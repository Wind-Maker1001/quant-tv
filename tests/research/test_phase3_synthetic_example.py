"""The public Phase-3 example must be offline, small, and complete."""

import json

import pandas as pd

from examples.research.phase3_synthetic_demo import (
    MODEL_NAMES,
    WARNING,
    run_demo,
)


def test_phase3_synthetic_demo_runs_complete_offline_path(tmp_path):
    destination = tmp_path / "synthetic"
    manifest = run_demo(destination, seed=42)

    stored = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["synthetic"] is True
    assert stored["network_used"] is False
    assert stored["warning"] == WARNING
    assert set(stored["models"]) == set(MODEL_NAMES)
    assert set(stored["market_regime_counts"]) == {"BULL", "BEAR", "SIDEWAYS"}
    assert all(value > 0 for value in stored["market_regime_counts"].values())

    for model_name in MODEL_NAMES:
        model_dir = destination / model_name
        predictions = pd.read_parquet(model_dir / "predictions.parquet")
        fast_trades = pd.read_csv(
            model_dir / "trades.csv",
            parse_dates=["signal_date", "execution_date"],
        )
        execution_trades = pd.read_csv(
            model_dir / "execution_trades.csv",
            parse_dates=["signal_date", "execution_date"],
        )
        prediction_summary = pd.read_csv(model_dir / "prediction_summary.csv")

        assert not predictions.empty
        assert set(predictions["MARKET_REGIME"]) == {"BULL", "BEAR", "SIDEWAYS"}
        assert not fast_trades.empty
        assert not execution_trades.empty
        assert (fast_trades["execution_date"] > fast_trades["signal_date"]).all()
        assert (
            execution_trades["execution_date"] > execution_trades["signal_date"]
        ).all()
        assert (execution_trades["executed_shares"] % 100 == 0).all()
        assert "REGIME" in set(prediction_summary["scope"])
        assert (model_dir / "execution_rejections.parquet").is_file()
        assert WARNING in (model_dir / "summary.md").read_text(encoding="utf-8")

    assert (destination / "ridge" / "ridge_coefficients.parquet").is_file()
    for model_name in ("lightgbm", "xgboost"):
        assert (destination / model_name / "feature_importance.parquet").is_file()

    comparison = pd.read_csv(destination / "comparison" / "model_comparison.csv")
    assert set(comparison["model_name"]) == set(MODEL_NAMES)
    assert (destination / "comparison" / "execution_nav.parquet").is_file()
    assert WARNING in (destination / "comparison" / "summary.md").read_text(
        encoding="utf-8"
    )
    assert WARNING in (destination / "README.md").read_text(encoding="utf-8")
