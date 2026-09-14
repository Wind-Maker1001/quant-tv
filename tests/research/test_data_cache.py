import json

import pandas as pd

from qbot.research.data.cache import ParquetBarCache
from qbot.research.data.schema import canonicalize_bars, empty_bars


def _bars(dates, closes=None):
    closes = closes or [10.0 + offset for offset in range(len(dates))]
    frame = pd.DataFrame(
        {
            "date": dates,
            "symbol": "600000.SH",
            "open": closes,
            "high": [value + 1 for value in closes],
            "low": [value - 1 for value in closes],
            "close": closes,
            "volume": 1000.0,
            "amount": 10_000.0,
            "turnover": 0.01,
        }
    )
    return canonicalize_bars(frame)


def test_cache_tracks_covered_ranges_and_incremental_gaps(tmp_path):
    cache = ParquetBarCache(tmp_path)
    cache.update(
        "600000.SH",
        _bars(["2024-01-02", "2024-01-03"]),
        "2024-01-01",
        "2024-01-05",
        source="fixture",
    )
    assert cache.missing_ranges("600000.SH", "2024-01-01", "2024-01-10") == [
        (pd.Timestamp("2024-01-06"), pd.Timestamp("2024-01-10"))
    ]
    cache.update(
        "600000.SH",
        _bars(["2024-01-08", "2024-01-09"]),
        "2024-01-08",
        "2024-01-10",
        source="fixture",
    )
    assert cache.missing_ranges("600000.SH", "2024-01-01", "2024-01-10") == [
        (pd.Timestamp("2024-01-06"), pd.Timestamp("2024-01-07"))
    ]
    metadata = json.loads(cache.metadata_path("600000.SH").read_text("utf-8"))
    assert metadata["row_count"] == 4
    assert len(metadata["content_sha256"]) == 64
    assert not list(tmp_path.glob("*.tmp-*"))


def test_later_cache_update_replaces_an_overlapping_observation(tmp_path):
    cache = ParquetBarCache(tmp_path)
    cache.update(
        "600000.SH",
        _bars(["2024-01-02"], closes=[10.0]),
        "2024-01-02",
        "2024-01-02",
        source="fixture",
    )
    cache.update(
        "600000.SH",
        _bars(["2024-01-02"], closes=[12.0]),
        "2024-01-02",
        "2024-01-02",
        source="fixture",
    )
    loaded = cache.load("600000.SH")
    assert len(loaded) == 1
    assert loaded.loc[0, "close"] == 12.0


def test_empty_successful_response_still_marks_range_covered(tmp_path):
    cache = ParquetBarCache(tmp_path)
    cache.update(
        "600000.SH",
        empty_bars(),
        "2024-01-06",
        "2024-01-07",
        source="fixture",
    )
    assert cache.missing_ranges("600000.SH", "2024-01-06", "2024-01-07") == []
    assert cache.load("600000.SH").empty


def test_update_from_provider_only_fetches_uncovered_ranges(tmp_path):
    cache = ParquetBarCache(tmp_path)

    class Provider:
        source_version = "fixture"

        def __init__(self):
            self.calls = []

        def get_daily_bars(self, symbol, start, end):
            self.calls.append((symbol, pd.Timestamp(start), pd.Timestamp(end)))
            return _bars([pd.Timestamp(start)])

    provider = Provider()
    cache.update_from_provider(
        provider, "600000.SH", "2024-01-01", "2024-01-05"
    )
    cache.update_from_provider(
        provider, "600000.SH", "2024-01-01", "2024-01-08"
    )
    assert provider.calls == [
        (
            "600000.SH",
            pd.Timestamp("2024-01-01"),
            pd.Timestamp("2024-01-05"),
        ),
        (
            "600000.SH",
            pd.Timestamp("2024-01-06"),
            pd.Timestamp("2024-01-08"),
        ),
    ]
