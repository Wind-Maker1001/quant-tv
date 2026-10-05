"""Generation publication, pinned readers, migration, and process locks."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pandas as pd
import pytest

from qbot.research.data.cache import ParquetBarCache
from qbot.research.data.schema import canonicalize_bars
from qbot.research.errors import CacheError


SYMBOL = "600000.SH"
SOURCE = "fixture"
SOURCE_VERSION = "raw-hfq-v1"


def _bars(date="2024-01-02", close=10.0):
    return canonicalize_bars(
        pd.DataFrame(
            {
                "date": [date],
                "symbol": [SYMBOL],
                "open": [close],
                "high": [close + 1.0],
                "low": [close - 1.0],
                "close": [close],
                "volume": [1000.0],
                "amount": [10000.0],
                "turnover": [0.01],
            }
        )
    )


def _update(cache, date="2024-01-02", close=10.0):
    return cache.update(
        SYMBOL,
        _bars(date, close),
        date,
        date,
        source=SOURCE,
        source_version=SOURCE_VERSION,
    )


def _snapshot(cache):
    return cache.load_snapshot(
        SYMBOL,
        expected_source=SOURCE,
        expected_source_version=SOURCE_VERSION,
    )


def _legacy_v2(cache):
    """Make a valid v2 artifact from a genuine serialized canonical frame."""
    _update(cache)
    generation_bytes = cache.data_path(SYMBOL).read_bytes()
    legacy = cache.root / (SYMBOL + ".parquet")
    legacy.write_bytes(generation_bytes)
    metadata = cache.read_metadata(SYMBOL)
    metadata["metadata_version"] = 2
    metadata.pop("generation_id")
    metadata.pop("data_file")
    cache.metadata_path(SYMBOL).write_text(
        json.dumps(metadata), encoding="utf-8"
    )
    return legacy, generation_bytes


@pytest.mark.parametrize("has_previous", [False, True])
@pytest.mark.parametrize("failure_point", ["before_generation", "after_generation", "pointer"])
def test_interrupted_publication_keeps_previous_commit_or_no_commit(
    tmp_path, monkeypatch, has_previous, failure_point
):
    cache = ParquetBarCache(tmp_path)
    if has_previous:
        _update(cache)
        old_path = cache.data_path(SYMBOL)
        old_data = old_path.read_bytes()
        old_metadata = cache.metadata_path(SYMBOL).read_bytes()
        old_frame = _snapshot(cache).frame
    original_write = cache._atomic_parquet

    def fail_generation(frame, target):
        if failure_point == "after_generation":
            original_write(frame, target)
        raise OSError("injected generation failure")

    def fail_pointer(value, target):
        raise OSError("injected pointer failure")

    with monkeypatch.context() as patch:
        if failure_point == "pointer":
            patch.setattr(cache, "_atomic_json", fail_pointer)
        else:
            patch.setattr(cache, "_atomic_parquet", fail_generation)
        with pytest.raises(CacheError, match="failed to atomically update"):
            _update(cache, "2024-01-03", 11.0)

    if has_previous:
        assert cache.metadata_path(SYMBOL).read_bytes() == old_metadata
        assert cache.data_path(SYMBOL) == old_path
        assert old_path.read_bytes() == old_data
        pd.testing.assert_frame_equal(_snapshot(cache).frame, old_frame)
    else:
        assert not cache.metadata_path(SYMBOL).exists()
        assert _snapshot(cache).metadata == {}
        assert _snapshot(cache).metadata_sha256 is None
        assert _snapshot(cache).frame.empty
    assert cache.missing_ranges(SYMBOL, "2024-01-03", "2024-01-03") == [
        (pd.Timestamp("2024-01-03"), pd.Timestamp("2024-01-03"))
    ]
    generations_before_retry = set(tmp_path.glob(SYMBOL + ".*.parquet"))
    if failure_point != "before_generation":
        assert len(generations_before_retry) == 1 + int(has_previous)
    _update(cache, "2024-01-03", 11.0)
    assert cache.missing_ranges(SYMBOL, "2024-01-03", "2024-01-03") == []
    assert set(tmp_path.glob(SYMBOL + ".*.parquet")).issuperset(
        generations_before_retry
    )
    assert _snapshot(cache).frame["date"].tolist() == (
        [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")]
        if has_previous
        else [pd.Timestamp("2024-01-03")]
    )


def test_reader_pins_one_metadata_generation_during_pointer_switch(tmp_path, monkeypatch):
    reader = ParquetBarCache(tmp_path)
    writer = ParquetBarCache(tmp_path)
    _update(writer)
    before = _snapshot(reader)
    old_pointer_bytes = reader.metadata_path(SYMBOL).read_bytes()
    original_validate = reader._validated_metadata_snapshot
    calls = []

    def switch_after_read(symbol):
        value = original_validate(symbol)
        calls.append(symbol)
        _update(writer, "2024-01-03", 12.0)
        return value

    with monkeypatch.context() as patch:
        patch.setattr(reader, "_validated_metadata_snapshot", switch_after_read)
        during = _snapshot(reader)
    assert calls == [SYMBOL]
    pd.testing.assert_frame_equal(during.frame, before.frame)
    assert during.metadata == before.metadata
    assert during.metadata_sha256 == hashlib.sha256(old_pointer_bytes).hexdigest()
    assert during.metadata["generation_id"] != writer.read_metadata(SYMBOL)["generation_id"]
    assert len(_snapshot(reader).frame) == 2


@pytest.mark.parametrize("has_previous", [False, True])
@pytest.mark.parametrize("failure_target", ["generation", "pointer"])
def test_real_atomic_replace_failure_cleans_temporary_files_and_preserves_commit(
    tmp_path, monkeypatch, has_previous, failure_target
):
    cache = ParquetBarCache(tmp_path)
    if has_previous:
        _update(cache)
        before = _snapshot(cache)
        pointer_bytes = cache.metadata_path(SYMBOL).read_bytes()
    replace = os.replace

    def fail_selected_replace(source, target):
        name = Path(target).name
        if (
            failure_target == "generation" and name.endswith(".parquet")
        ) or (
            failure_target == "pointer" and name.endswith(".metadata.json")
        ):
            raise OSError("injected atomic replace failure")
        return replace(source, target)

    with monkeypatch.context() as patch:
        patch.setattr(os, "replace", fail_selected_replace)
        with pytest.raises(CacheError, match="failed to atomically update"):
            _update(cache, "2024-01-03", 12.0)
    assert not list(tmp_path.glob("*.tmp-*"))
    if has_previous:
        assert cache.metadata_path(SYMBOL).read_bytes() == pointer_bytes
        after = _snapshot(cache)
        assert after.metadata == before.metadata
        pd.testing.assert_frame_equal(after.frame, before.frame)
    else:
        assert not cache.metadata_path(SYMBOL).exists()
        assert _snapshot(cache).frame.empty
    _update(cache, "2024-01-03", 12.0)
    assert cache.missing_ranges(SYMBOL, "2024-01-03", "2024-01-03") == []


def test_reader_hashes_and_decodes_the_same_in_memory_bytes(tmp_path, monkeypatch):
    cache = ParquetBarCache(tmp_path)
    _update(cache)
    old = _snapshot(cache)
    active = cache.data_path(SYMBOL)
    original_read = pd.read_parquet

    def tamper_after_bytes_were_captured(source, *args, **kwargs):
        assert hasattr(source, "read")
        active.write_bytes(b"tampered after snapshot read")
        return original_read(source, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(pd, "read_parquet", tamper_after_bytes_were_captured)
        pinned = _snapshot(cache)
    pd.testing.assert_frame_equal(pinned.frame, old.frame)
    assert pinned.metadata == old.metadata
    with pytest.raises(CacheError, match="content hash mismatch"):
        _snapshot(cache)


@pytest.mark.parametrize("mutation", ["tamper", "missing"])
def test_committed_generation_corruption_never_reads_another_file(tmp_path, mutation):
    cache = ParquetBarCache(tmp_path)
    _update(cache)
    first = cache.data_path(SYMBOL)
    _update(cache, "2024-01-03", 11.0)
    active = cache.data_path(SYMBOL)
    assert first.exists()
    if mutation == "tamper":
        active.write_bytes(active.read_bytes() + b"corruption")
        message = "content hash mismatch"
    else:
        active.unlink()
        message = "incomplete cache artifact"
    with pytest.raises(CacheError, match=message):
        _snapshot(cache)


@pytest.mark.parametrize(
    "field,value",
    [
        ("data_file", "../outside.parquet"),
        ("data_file", "000001.SZ." + "a" * 32 + ".parquet"),
        ("generation_id", "not-a-generation"),
        ("generation_id", "A" * 32),
        ("generation_id", "a" * 32),
    ],
)
def test_generation_pointer_rejects_unsafe_or_mismatched_names(tmp_path, field, value):
    cache = ParquetBarCache(tmp_path)
    _update(cache)
    metadata = cache.read_metadata(SYMBOL)
    metadata[field] = value
    cache.metadata_path(SYMBOL).write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(CacheError, match="invalid cache generation pointer"):
        _snapshot(cache)


def test_generation_updates_retain_immutable_previous_bytes(tmp_path):
    cache = ParquetBarCache(tmp_path)
    _update(cache)
    first = cache.data_path(SYMBOL)
    original = first.read_bytes()
    _update(cache, "2024-01-02", 15.0)
    second = cache.data_path(SYMBOL)
    assert first != second
    assert first.read_bytes() == original
    assert pd.read_parquet(first).loc[0, "close"] == 10.0
    assert _snapshot(cache).frame.loc[0, "close"] == 15.0
    assert not (tmp_path / (SYMBOL + ".parquet")).exists()


def test_strict_v2_reads_and_migration_preserve_legacy_bytes(tmp_path):
    cache = ParquetBarCache(tmp_path)
    legacy, original = _legacy_v2(cache)
    before = _snapshot(cache)
    assert before.metadata["metadata_version"] == 2
    assert cache.data_path(SYMBOL) == legacy
    assert before.frame.loc[0, "close"] == 10.0
    _update(cache, "2024-01-03", 11.0)
    assert legacy.read_bytes() == original
    assert cache.data_path(SYMBOL) != legacy
    assert _snapshot(cache).metadata["metadata_version"] == 3
    assert len(_snapshot(cache).frame) == 2


def test_failed_v2_migration_keeps_legacy_pair_committed(tmp_path, monkeypatch):
    cache = ParquetBarCache(tmp_path)
    legacy, original = _legacy_v2(cache)
    pointer = cache.metadata_path(SYMBOL).read_bytes()

    def fail_pointer(value, target):
        raise OSError("injected migration pointer failure")

    with monkeypatch.context() as patch:
        patch.setattr(cache, "_atomic_json", fail_pointer)
        with pytest.raises(CacheError, match="failed to atomically update"):
            _update(cache, "2024-01-03", 11.0)
    assert legacy.read_bytes() == original
    assert cache.metadata_path(SYMBOL).read_bytes() == pointer
    assert _snapshot(cache).metadata["metadata_version"] == 2
    assert len(_snapshot(cache).frame) == 1


@pytest.mark.parametrize("mutation", ["content", "source", "version"])
def test_v2_compatibility_does_not_relax_integrity_or_provider_contract(tmp_path, mutation):
    cache = ParquetBarCache(tmp_path)
    legacy, _ = _legacy_v2(cache)
    if mutation == "content":
        legacy.write_bytes(legacy.read_bytes() + b"corruption")
        message = "content hash mismatch"
    else:
        metadata = cache.read_metadata(SYMBOL)
        if mutation == "source":
            metadata["source_version"] = "different-adjustment"
            message = "source identity mismatch"
        else:
            metadata["metadata_version"] = 1
            message = "unsupported cache metadata version"
        cache.metadata_path(SYMBOL).write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(CacheError, match=message):
        _snapshot(cache)
    with pytest.raises(CacheError, match=message):
        _update(cache, "2024-01-03", 11.0)


def test_independent_instances_serialize_concurrent_merges(tmp_path):
    first = ParquetBarCache(tmp_path)
    second = ParquetBarCache(tmp_path)
    barrier = threading.Barrier(2)

    def write(cache, date, close):
        barrier.wait(timeout=5)
        return _update(cache, date, close)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(write, first, "2024-01-02", 10.0),
            executor.submit(write, second, "2024-01-03", 11.0),
        ]
        for future in futures:
            future.result(timeout=15)
    result = _snapshot(first)
    assert result.frame["date"].tolist() == [
        pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")
    ]
    assert result.frame["close"].tolist() == [10.0, 11.0]
    assert first.missing_ranges(SYMBOL, "2024-01-02", "2024-01-03") == []
    assert len(list(tmp_path.glob(SYMBOL + ".*.parquet"))) == 2


def test_lock_timeout_and_release_after_exception(tmp_path):
    holder = ParquetBarCache(tmp_path)
    contender = ParquetBarCache(tmp_path, lock_timeout_seconds=0.05)
    with pytest.raises(RuntimeError, match="injected protected-body failure"):
        with holder._writer_lock(SYMBOL):
            with pytest.raises(CacheError, match="writer lock timeout"):
                with contender._writer_lock(SYMBOL):
                    pytest.fail("another writer entered while the lock was held")
            raise RuntimeError("injected protected-body failure")
    _update(contender)
    assert len(_snapshot(contender).frame) == 1
    assert (tmp_path / ("." + SYMBOL + ".write.lock")).is_file()


@contextmanager
def _child_holding_lock(root, ready):
    script = (
        "import sys\n"
        "from pathlib import Path\n"
        "from qbot.research.data.cache import ParquetBarCache\n"
        "cache = ParquetBarCache(Path(sys.argv[1]))\n"
        "with cache._writer_lock('600000.SH'):\n"
        "    Path(sys.argv[2]).write_text('locked', encoding='utf-8')\n"
        "    sys.stdin.read()\n"
    )
    kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    child = subprocess.Popen(
        [sys.executable, "-c", script, str(root), str(ready)],
        cwd=str(Path(__file__).resolve().parents[2]),
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        **kwargs
    )
    try:
        deadline = time.monotonic() + 15.0
        while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        if not ready.exists():
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)
            pytest.fail("child did not acquire lock: %r" % child.stderr.read())
        yield child
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=5)
        child.stdin.close()
        child.stderr.close()


def test_abrupt_child_exit_releases_os_lock_without_removing_lock_file(tmp_path):
    cache = ParquetBarCache(tmp_path, lock_timeout_seconds=0.05)
    ready = tmp_path / "child-is-locked.txt"
    with _child_holding_lock(tmp_path, ready) as child:
        with pytest.raises(CacheError, match="writer lock timeout"):
            _update(cache)
        lock_file = tmp_path / ("." + SYMBOL + ".write.lock")
        assert lock_file.is_file()
        child.kill()
        child.wait(timeout=5)
        assert lock_file.is_file()
        _update(cache)
        assert len(_snapshot(cache).frame) == 1
        assert lock_file.is_file()
