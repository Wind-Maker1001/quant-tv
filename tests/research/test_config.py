from pathlib import Path

import pytest
import yaml

from qbot.research.config import load_config
from qbot.research.errors import (
    ConfigurationError,
    POINT_IN_TIME_UNIVERSE_REQUIRED,
    PointInTimeUniverseRequiredError,
)


def _valid_document():
    return {
        "project": {"name": "test-factorlab"},
        "data": {
            "start": "2024-01-02",
            "end": "2024-04-30",
            "provider": "akshare",
            "benchmark": "000905.SH",
            "adjustment": "hfq",
            "calendar_source": "benchmark",
        },
        "universe": {
            "name": "CSI500",
            "index_symbol": "000905.SH",
            "provider": "baostock",
            "point_in_time": True,
            "expected_member_count": 500,
        },
        "factors": ["REV1", "MOM20"],
    }


def _write_config(root: Path, document) -> Path:
    config_dir = root / "configs" / "research"
    config_dir.mkdir(parents=True)
    path = config_dir / "test.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def test_load_config_is_strict_and_resolves_paths_from_repo_root(tmp_path):
    document = _valid_document()
    document["paths"] = {
        "data_root": "var/research-data",
        "results_root": "var/results",
    }
    path = _write_config(tmp_path, document)

    config = load_config(path.relative_to(tmp_path), repo_root=tmp_path)

    assert config.paths.data_root == (tmp_path / "var/research-data").resolve()
    assert config.paths.results_root == (tmp_path / "var/results").resolve()
    assert config.config_path == path.resolve()
    assert config.repo_root == tmp_path.resolve()
    assert config.factors == ("REV1", "MOM20")
    assert config.data.start.isoformat() == "2024-01-02"


@pytest.mark.parametrize(
    "mutate,unknown_name",
    [
        (lambda value: value.update({"surprise": True}), "surprise"),
        (
            lambda value: value["data"].update({"future_fill": "bfill"}),
            "future_fill",
        ),
    ],
)
def test_unknown_fields_are_rejected(tmp_path, mutate, unknown_name):
    document = _valid_document()
    mutate(document)
    path = _write_config(tmp_path, document)

    with pytest.raises(ConfigurationError, match=unknown_name):
        load_config(path, repo_root=tmp_path)


def test_missing_required_field_is_rejected(tmp_path):
    document = _valid_document()
    document.pop("data")
    path = _write_config(tmp_path, document)

    with pytest.raises(ConfigurationError, match="missing required field.*data"):
        load_config(path, repo_root=tmp_path)


def test_non_boolean_is_not_coerced(tmp_path):
    document = _valid_document()
    document["live_trading"] = "false"
    path = _write_config(tmp_path, document)

    with pytest.raises(ConfigurationError, match="live_trading must be a boolean"):
        load_config(path, repo_root=tmp_path)


def test_point_in_time_universe_cannot_be_disabled(tmp_path):
    document = _valid_document()
    document["universe"]["point_in_time"] = False
    path = _write_config(tmp_path, document)

    with pytest.raises(PointInTimeUniverseRequiredError) as caught:
        load_config(path, repo_root=tmp_path)

    assert POINT_IN_TIME_UNIVERSE_REQUIRED in str(caught.value)


def test_formal_and_smoke_configs_load():
    repository = Path(__file__).resolve().parents[2]

    formal = load_config("configs/research/csi500_5y.yaml", repo_root=repository)
    smoke = load_config("configs/research/csi500_smoke.yaml", repo_root=repository)

    assert formal.data.start.isoformat() == "2021-09-13"
    assert formal.data.end.isoformat() == "2026-09-11"
    assert formal.data.warmup_trading_days == 130
    assert formal.live_trading is False
    assert smoke.project.name.endswith("smoke-test-only")
    assert smoke.data.end < formal.data.end


def test_warmup_must_cover_listing_and_quality_windows(tmp_path):
    document = _valid_document()
    document["data"]["warmup_trading_days"] = 10
    path = _write_config(tmp_path, document)

    with pytest.raises(ConfigurationError, match="warmup_trading_days must cover"):
        load_config(path, repo_root=tmp_path)


def test_manifest_snapshot_is_json_serializable(tmp_path):
    config = load_config(_write_config(tmp_path, _valid_document()), repo_root=tmp_path)

    snapshot = config.to_dict()

    assert snapshot["data"]["start"] == "2024-01-02"
    assert snapshot["factors"] == ["REV1", "MOM20"]
    assert "repo_root" not in snapshot
    assert "config_path" not in snapshot
