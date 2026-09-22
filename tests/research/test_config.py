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
    assert formal.validation.initial_train_months == 24
    assert formal.validation.purge_days == 5
    assert formal.portfolio.top_k == 20
    assert formal.models.ridge.alphas == (0.1, 1.0, 10.0, 100.0)
    assert set(formal.models.factor_score.weights) == set(formal.factors)
    assert formal.fees.stamp_duty[0].sell_bps == 10.0
    assert formal.fees.stamp_duty[1].sell_bps == 5.0
    assert smoke.project.name.endswith("smoke-test-only")
    assert smoke.data.end < formal.data.end
    assert smoke.data.end.isoformat() == "2024-05-17"
    assert smoke.validation.initial_train_months == 2


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


def test_phase2_nested_unknown_field_is_rejected(tmp_path):
    document = _valid_document()
    document["models"] = {"ridge": {"alphas": [1.0], "future_hint": True}}
    path = _write_config(tmp_path, document)

    with pytest.raises(ConfigurationError, match="future_hint"):
        load_config(path, repo_root=tmp_path)


@pytest.mark.parametrize(
    "section,field,bad_symbol",
    [
        ("data", "benchmark", "000300.SH"),
        ("universe", "index_symbol", "000300.SH"),
        ("data", "benchmark", "sh000905"),
    ],
)
def test_csi500_benchmark_and_universe_symbol_are_fixed(
    tmp_path, section, field, bad_symbol
):
    document = _valid_document()
    document[section][field] = bad_symbol
    path = _write_config(tmp_path, document)

    with pytest.raises(ConfigurationError, match="both be canonical 000905.SH"):
        load_config(path, repo_root=tmp_path)


def test_factor_score_weights_must_match_enabled_factors(tmp_path):
    document = _valid_document()
    document["models"] = {
        "factor_score": {"weights": {"REV1": 1.0}},
    }
    path = _write_config(tmp_path, document)

    with pytest.raises(ConfigurationError, match="must match the enabled factor list"):
        load_config(path, repo_root=tmp_path)


def test_unregistered_factor_is_rejected_before_pipeline_execution(tmp_path):
    document = _valid_document()
    document["factors"] = ["REV1", "NOT_A_REAL_FACTOR"]
    path = _write_config(tmp_path, document)

    with pytest.raises(ConfigurationError, match="unregistered names"):
        load_config(path, repo_root=tmp_path)


def test_purge_must_cover_forward_label_horizon(tmp_path):
    document = _valid_document()
    document["validation"] = {"purge_days": 4}
    path = _write_config(tmp_path, document)

    with pytest.raises(ConfigurationError, match="purge_days must be at least"):
        load_config(path, repo_root=tmp_path)


def test_stamp_duty_schedule_must_be_contiguous(tmp_path):
    document = _valid_document()
    document["fees"] = {
        "stamp_duty": [
            {"start": "2021-01-01", "end": "2023-08-27", "sell_bps": 10},
            {"start": "2023-08-29", "end": None, "sell_bps": 5},
        ]
    }
    path = _write_config(tmp_path, document)

    with pytest.raises(ConfigurationError, match="contiguous"):
        load_config(path, repo_root=tmp_path)
