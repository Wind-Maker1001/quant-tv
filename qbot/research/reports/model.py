"""Deterministic, headless reporting for FactorLab model experiments.

The writer consumes only already-produced out-of-sample predictions and
backtest results. It does not fit a model, select hyperparameters, or infer a
"winner" from test performance.  Every tabular artifact is written both as
CSV (easy to inspect) and Parquet (lossless and efficient to reload).
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from collections.abc import Iterable
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from qbot.research.backtest.fast import FastBacktestResult
from qbot.research.backtest.execution import ExecutionBacktestResult
from qbot.research.metrics.prediction import PredictionEvaluation
from qbot.research.validation.walk_forward import WalkForwardResult


class ModelReportError(ValueError):
    """Raised when model-report inputs are structurally invalid."""


_TABLE_NAMES = (
    "predictions",
    "walk_forward_results",
    "validation_results",
    "prediction_daily",
    "prediction_summary",
    "nav",
    "trades",
    "positions",
    "signals",
    "portfolio_metrics",
)


def _temporary_path(destination: Path) -> Path:
    """Return a same-directory temporary path with a useful final suffix."""

    token = uuid.uuid4().hex
    return destination.with_name(
        ".%s.%s.tmp%s" % (destination.stem, token, destination.suffix)
    )


def _atomic_write(destination: Path, writer: Callable[[Path], None]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_path(destination)
    try:
        writer(temporary)
        os.replace(str(temporary), str(destination))
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _atomic_text(text: str, destination: Path) -> None:
    def write(path: Path) -> None:
        # ``Path.write_text(newline=...)`` is unavailable on Python 3.9.
        # Report text is constructed with explicit ``\n`` separators already.
        path.write_text(text, encoding="utf-8")

    _atomic_write(destination, write)


def _atomic_csv(frame: pd.DataFrame, destination: Path) -> None:
    _atomic_write(destination, lambda path: frame.to_csv(path, index=False))


def _atomic_parquet(frame: pd.DataFrame, destination: Path) -> None:
    _atomic_write(destination, lambda path: frame.to_parquet(path, index=False))


def _write_table(frame: pd.DataFrame, name: str, destination: Path) -> Tuple[Path, Path]:
    csv_path = destination / (name + ".csv")
    parquet_path = destination / (name + ".parquet")
    _atomic_csv(frame, csv_path)
    _atomic_parquet(frame, parquet_path)
    return csv_path, parquet_path


def _save_figure(figure: plt.Figure, destination: Path) -> None:
    try:
        _atomic_write(
            destination,
            lambda path: figure.savefig(
                path,
                format="png",
                dpi=150,
                bbox_inches="tight",
            ),
        )
    finally:
        plt.close(figure)


def _placeholder(axis: plt.Axes, title: str) -> None:
    axis.set_title(title)
    axis.text(
        0.5,
        0.5,
        "No data available",
        ha="center",
        va="center",
        transform=axis.transAxes,
        color="#666666",
    )
    axis.set_xticks([])
    axis.set_yticks([])


def _x_axis(frame: pd.DataFrame) -> pd.Series:
    if "date" not in frame:
        return pd.Series(np.arange(len(frame)), index=frame.index)
    dates = pd.to_datetime(frame["date"], errors="coerce")
    if dates.notna().any():
        return dates
    return pd.Series(np.arange(len(frame)), index=frame.index)


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame:
        return pd.Series(dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _plot_nav(nav: pd.DataFrame, destination: Path) -> None:
    figure, axis = plt.subplots(figsize=(11, 5.5))
    plotted = False
    if not nav.empty:
        x_values = _x_axis(nav)
        for column, label in (
            ("strategy_nav", "Strategy"),
            ("benchmark_nav", "CSI500"),
            ("excess_nav", "Excess NAV"),
        ):
            values = _numeric(nav, column)
            if len(values) and values.notna().any():
                axis.plot(x_values, values, label=label, linewidth=1.4)
                plotted = True
    if plotted:
        axis.set_title("Out-of-sample NAV")
        axis.set_ylabel("NAV")
        axis.grid(alpha=0.2)
        axis.legend()
    else:
        _placeholder(axis, "Out-of-sample NAV")
    _save_figure(figure, destination)


def _drawdowns(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.where(np.isfinite(numeric) & (numeric > 0))
    return valid / valid.cummax().clip(lower=1.0) - 1.0


def _plot_drawdown(nav: pd.DataFrame, destination: Path) -> None:
    figure, axis = plt.subplots(figsize=(11, 4.5))
    plotted = False
    if not nav.empty:
        x_values = _x_axis(nav)
        for column, label in (
            ("strategy_nav", "Strategy"),
            ("benchmark_nav", "CSI500"),
            ("excess_nav", "Excess NAV"),
        ):
            if column in nav:
                values = _drawdowns(nav[column])
                if values.notna().any():
                    axis.plot(x_values, values, label=label, linewidth=1.3)
                    plotted = True
    if plotted:
        axis.axhline(0.0, color="black", linewidth=0.8)
        axis.set_title("Drawdown")
        axis.set_ylabel("Drawdown")
        axis.grid(alpha=0.2)
        axis.legend()
    else:
        _placeholder(axis, "Drawdown")
    _save_figure(figure, destination)


def _plot_prediction_ic(daily: pd.DataFrame, destination: Path) -> None:
    figure, axis = plt.subplots(figsize=(11, 5))
    plotted = False
    if not daily.empty:
        x_values = _x_axis(daily)
        for column, label in (
            ("prediction_ic", "Prediction IC"),
            ("prediction_rank_ic", "Prediction RankIC"),
        ):
            values = _numeric(daily, column)
            if len(values) and values.notna().any():
                axis.plot(x_values, values, label=label, alpha=0.75, linewidth=1.0)
                plotted = True
    if plotted:
        axis.axhline(0.0, color="black", linewidth=0.8)
        axis.set_title("Daily out-of-sample prediction IC")
        axis.set_ylabel("Correlation")
        axis.grid(alpha=0.2)
        axis.legend()
    else:
        _placeholder(axis, "Daily out-of-sample prediction IC")
    _save_figure(figure, destination)


def _plot_daily_bar(
    nav: pd.DataFrame,
    column: str,
    title: str,
    ylabel: str,
    destination: Path,
) -> None:
    figure, axis = plt.subplots(figsize=(11, 4.5))
    values = _numeric(nav, column)
    if not nav.empty and len(values) and values.notna().any():
        axis.bar(_x_axis(nav), values.fillna(0.0), width=1.0, color="#35618f")
        axis.set_title(title)
        axis.set_ylabel(ylabel)
        axis.grid(axis="y", alpha=0.2)
    else:
        _placeholder(axis, title)
    _save_figure(figure, destination)


def _plot_coefficients(coefficients: pd.DataFrame, destination: Path) -> None:
    figure, axis = plt.subplots(figsize=(11, 6))
    required = {"fold", "feature", "coefficient"}
    if coefficients.empty or not required.issubset(coefficients.columns):
        _placeholder(axis, "Ridge coefficient stability")
        _save_figure(figure, destination)
        return
    table = coefficients.copy()
    table["coefficient"] = pd.to_numeric(table["coefficient"], errors="coerce")
    pivot = table.pivot_table(
        index="fold",
        columns="feature",
        values="coefficient",
        aggfunc="first",
    ).sort_index()
    if pivot.empty or not pivot.notna().any().any():
        _placeholder(axis, "Ridge coefficient stability")
    else:
        for feature in pivot.columns:
            axis.plot(
                pivot.index,
                pivot[feature],
                marker="o",
                markersize=3,
                linewidth=1.0,
                label=str(feature),
            )
        axis.axhline(0.0, color="black", linewidth=0.8)
        axis.set_title("Ridge coefficient stability by walk-forward fold")
        axis.set_xlabel("Fold")
        axis.set_ylabel("Coefficient")
        axis.grid(alpha=0.2)
        axis.legend(bbox_to_anchor=(1.02, 1.0), loc="upper left", fontsize=8)
    _save_figure(figure, destination)


def _plot_feature_importance(
    importance: pd.DataFrame, destination: Path
) -> None:
    figure, axis = plt.subplots(figsize=(10, 6))
    required = {"feature", "normalized_importance"}
    if importance.empty or not required.issubset(importance.columns):
        _placeholder(axis, "Mean tree feature importance")
        _save_figure(figure, destination)
        return
    table = importance.copy()
    table["normalized_importance"] = pd.to_numeric(
        table["normalized_importance"], errors="coerce"
    )
    values = (
        table.groupby("feature", sort=True)["normalized_importance"]
        .mean()
        .dropna()
        .sort_values()
    )
    if values.empty:
        _placeholder(axis, "Mean tree feature importance")
    else:
        values.plot(kind="barh", ax=axis, color="#35618f")
        axis.set_xlabel("Mean normalized gain importance")
        axis.set_title("Mean tree feature importance across walk-forward folds")
        axis.grid(axis="x", alpha=0.2)
    _save_figure(figure, destination)


def _plot_regime_performance(summary: pd.DataFrame, destination: Path) -> None:
    figure, axis = plt.subplots(figsize=(9, 5.5))
    required = {"scope", "period", "prediction_rank_ic_mean"}
    if summary.empty or not required.issubset(summary.columns):
        _placeholder(axis, "Prediction RankIC by market regime")
        _save_figure(figure, destination)
        return
    regimes = summary.loc[summary["scope"] == "REGIME"].copy()
    regimes["prediction_rank_ic_mean"] = pd.to_numeric(
        regimes["prediction_rank_ic_mean"], errors="coerce"
    )
    regimes.dropna(subset=["prediction_rank_ic_mean"], inplace=True)
    if regimes.empty:
        _placeholder(axis, "Prediction RankIC by market regime")
    else:
        regimes.sort_values("period", kind="mergesort", inplace=True)
        axis.bar(
            regimes["period"].astype(str),
            regimes["prediction_rank_ic_mean"],
            color="#527a5a",
        )
        axis.axhline(0.0, color="black", linewidth=0.8)
        axis.set_ylabel("Mean daily RankIC")
        axis.set_title("Prediction RankIC by market regime")
        axis.grid(axis="y", alpha=0.2)
    _save_figure(figure, destination)


def _metric_frame(metrics: Mapping[str, Any]) -> pd.DataFrame:
    if not isinstance(metrics, Mapping):
        raise ModelReportError("portfolio_metrics must be a mapping")
    rows = [{"metric": str(name), "value": value} for name, value in metrics.items()]
    return pd.DataFrame(rows, columns=["metric", "value"])


def _format_value(value: Any) -> str:
    if value is None or value is pd.NA:
        return "NA"
    try:
        if pd.isna(value):
            return "NA"
    except (TypeError, ValueError):
        pass
    if isinstance(value, (float, np.floating)):
        return "%.6f" % float(value)
    return str(value).replace("|", "\\|")


def _overall_prediction(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty or "scope" not in summary:
        return pd.DataFrame()
    return summary.loc[summary["scope"].astype(str).str.upper() == "OVERALL"]


def _mapping_from_metrics(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    if isinstance(value, pd.Series):
        return {str(key): item for key, item in value.items()}
    if isinstance(value, pd.DataFrame):
        if value.empty:
            return {}
        if {"metric", "value"}.issubset(value.columns):
            return {
                str(row.metric): row.value
                for row in value.loc[:, ["metric", "value"]].itertuples(index=False)
            }
        if len(value) == 1:
            return {str(key): item for key, item in value.iloc[0].items()}
    raise ModelReportError(
        "portfolio_metrics must be a mapping, Series, or metric/value DataFrame"
    )


def _mapping_from_prediction(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, PredictionEvaluation):
        value = value.summary
    if isinstance(value, pd.Series):
        return {
            str(key): item
            for key, item in value.items()
            if str(key) not in {"scope", "period"}
        }
    if isinstance(value, pd.DataFrame):
        overall = _overall_prediction(value)
        if overall.empty and len(value) == 1:
            overall = value
        if overall.empty:
            return {}
        row = overall.iloc[0]
        return {
            str(key): item
            for key, item in row.items()
            if str(key) not in {"scope", "period"}
        }
    raise ModelReportError(
        "prediction_summary must be a PredictionEvaluation, Series, or DataFrame"
    )


def _comparison_record(value: Mapping[str, Any], model_name: Optional[str] = None) -> dict:
    record = dict(value)
    name = record.pop("model_name", model_name)
    if not isinstance(name, str) or not name.strip():
        raise ModelReportError("each model comparison record requires model_name")
    prediction_value = record.pop("prediction", None)
    if prediction_value is None:
        prediction_value = record.pop("prediction_summary", None)
    metrics_value = record.pop("portfolio_metrics", None)
    result = {"model_name": name.strip()}
    result.update(_mapping_from_prediction(prediction_value))
    result.update(_mapping_from_metrics(metrics_value))
    result.update(record)
    return result


def _comparison_frame(records_or_frame: Any) -> pd.DataFrame:
    if isinstance(records_or_frame, pd.DataFrame):
        frame = records_or_frame.copy()
    elif isinstance(records_or_frame, Mapping):
        if "model_name" in records_or_frame:
            frame = pd.DataFrame([_comparison_record(records_or_frame)])
        else:
            rows = []
            for model_name, value in records_or_frame.items():
                if isinstance(value, PredictionEvaluation):
                    value = {"prediction": value}
                if not isinstance(value, Mapping):
                    raise ModelReportError(
                        "model comparison mapping values must be mappings or PredictionEvaluation"
                    )
                rows.append(_comparison_record(value, model_name=str(model_name)))
            frame = pd.DataFrame(rows)
    elif isinstance(records_or_frame, Iterable) and not isinstance(
        records_or_frame, (str, bytes)
    ):
        rows = []
        for value in records_or_frame:
            if not isinstance(value, Mapping):
                raise ModelReportError("model comparison records must be mappings")
            rows.append(_comparison_record(value))
        frame = pd.DataFrame(rows)
    else:
        raise ModelReportError(
            "records_or_frame must be a DataFrame, mapping, or iterable of mappings"
        )
    if frame.empty:
        if "model_name" not in frame:
            frame = pd.DataFrame(columns=["model_name"])
        return frame
    if "model_name" not in frame:
        raise ModelReportError("model comparison data requires model_name")
    if frame["model_name"].isna().any() or frame["model_name"].astype(str).str.strip().eq("").any():
        raise ModelReportError("model_name must not contain missing or empty values")
    frame["model_name"] = frame["model_name"].astype(str).str.strip()
    if frame["model_name"].duplicated().any():
        raise ModelReportError("model comparison contains duplicate model_name values")
    return frame.sort_values("model_name", kind="mergesort").reset_index(drop=True)


def _plot_model_ic(comparison: pd.DataFrame, destination: Path) -> None:
    figure, axis = plt.subplots(figsize=(10, 5.5))
    metrics = [
        ("prediction_ic_mean", "Prediction IC"),
        ("prediction_rank_ic_mean", "Prediction RankIC"),
    ]
    available = [item for item in metrics if item[0] in comparison]
    if comparison.empty or not available:
        _placeholder(axis, "Out-of-sample model IC comparison")
        _save_figure(figure, destination)
        return
    x_values = np.arange(len(comparison))
    width = 0.34 if len(available) > 1 else 0.55
    plotted = False
    for index, (column, label) in enumerate(available):
        values = pd.to_numeric(comparison[column], errors="coerce")
        if not values.notna().any():
            continue
        offset = (index - (len(available) - 1) / 2.0) * width
        axis.bar(x_values + offset, values, width=width, label=label)
        plotted = True
    if plotted:
        axis.axhline(0.0, color="black", linewidth=0.8)
        axis.set_xticks(x_values, comparison["model_name"].astype(str), rotation=20)
        axis.set_ylabel("Mean daily correlation")
        axis.set_title("Out-of-sample model IC comparison")
        axis.grid(axis="y", alpha=0.2)
        axis.legend()
    else:
        _placeholder(axis, "Out-of-sample model IC comparison")
    _save_figure(figure, destination)


def _plot_comparison_nav(nav: pd.DataFrame, destination: Path) -> None:
    figure, axis = plt.subplots(figsize=(11, 5.5))
    required = {"date", "model_name", "strategy_nav", "benchmark_nav"}
    if nav.empty or not required.issubset(nav.columns):
        _placeholder(axis, "Out-of-sample NAV comparison")
        _save_figure(figure, destination)
        return
    table = nav.copy()
    table["date"] = pd.to_datetime(table["date"], errors="coerce")
    for model_name, values in table.groupby("model_name", sort=True):
        values = values.sort_values("date", kind="mergesort")
        axis.plot(values["date"], values["strategy_nav"], label=str(model_name))
    benchmark = table.sort_values("date", kind="mergesort").drop_duplicates("date")
    axis.plot(
        benchmark["date"],
        benchmark["benchmark_nav"],
        label="CSI500",
        color="black",
        linestyle="--",
        linewidth=1.2,
    )
    axis.set_title("Out-of-sample NAV comparison")
    axis.set_ylabel("NAV")
    axis.grid(alpha=0.2)
    axis.legend()
    _save_figure(figure, destination)


def _plot_comparison_drawdown(nav: pd.DataFrame, destination: Path) -> None:
    figure, axis = plt.subplots(figsize=(11, 5.0))
    required = {"date", "model_name", "strategy_nav"}
    if nav.empty or not required.issubset(nav.columns):
        _placeholder(axis, "Out-of-sample drawdown comparison")
        _save_figure(figure, destination)
        return
    for model_name, values in nav.groupby("model_name", sort=True):
        values = values.copy()
        values["date"] = pd.to_datetime(values["date"], errors="coerce")
        values.sort_values("date", kind="mergesort", inplace=True)
        series = pd.to_numeric(values["strategy_nav"], errors="coerce")
        drawdown = series / series.cummax() - 1.0
        axis.plot(values["date"], drawdown, label=str(model_name))
    axis.set_title("Out-of-sample drawdown comparison")
    axis.set_ylabel("Drawdown")
    axis.grid(alpha=0.2)
    axis.legend()
    _save_figure(figure, destination)


def _plot_comparison_daily_metric(
    nav: pd.DataFrame,
    column: str,
    title: str,
    ylabel: str,
    destination: Path,
) -> None:
    figure, axis = plt.subplots(figsize=(11, 5.0))
    required = {"date", "model_name", column}
    if nav.empty or not required.issubset(nav.columns):
        _placeholder(axis, title)
        _save_figure(figure, destination)
        return
    for model_name, values in nav.groupby("model_name", sort=True):
        values = values.copy()
        values["date"] = pd.to_datetime(values["date"], errors="coerce")
        values.sort_values("date", kind="mergesort", inplace=True)
        axis.plot(
            values["date"],
            pd.to_numeric(values[column], errors="coerce").fillna(0.0),
            label=str(model_name),
            linewidth=0.9,
        )
    axis.set_title(title)
    axis.set_ylabel(ylabel)
    axis.grid(alpha=0.2)
    axis.legend()
    _save_figure(figure, destination)


def _plot_comparison_feature_importance(
    importance: pd.DataFrame, destination: Path
) -> None:
    figure, axis = plt.subplots(figsize=(12, 6))
    required = {"model_name", "feature", "normalized_importance"}
    if importance.empty or not required.issubset(importance.columns):
        _placeholder(axis, "Tree feature importance comparison")
        _save_figure(figure, destination)
        return
    table = importance.pivot_table(
        index="feature",
        columns="model_name",
        values="normalized_importance",
        aggfunc="mean",
    ).fillna(0.0)
    table.plot(kind="bar", ax=axis)
    axis.set_title("Mean feature importance across walk-forward folds")
    axis.set_ylabel("Normalized gain importance")
    axis.grid(axis="y", alpha=0.2)
    _save_figure(figure, destination)


def _plot_comparison_regime(
    prediction_summary: pd.DataFrame, destination: Path
) -> None:
    figure, axis = plt.subplots(figsize=(10, 5.5))
    required = {
        "model_name",
        "scope",
        "period",
        "prediction_rank_ic_mean",
    }
    if prediction_summary.empty or not required.issubset(prediction_summary.columns):
        _placeholder(axis, "Prediction RankIC by model and regime")
        _save_figure(figure, destination)
        return
    regimes = prediction_summary.loc[
        prediction_summary["scope"] == "REGIME"
    ]
    table = regimes.pivot_table(
        index="period",
        columns="model_name",
        values="prediction_rank_ic_mean",
        aggfunc="first",
    )
    if table.empty:
        _placeholder(axis, "Prediction RankIC by model and regime")
    else:
        table.plot(kind="bar", ax=axis)
        axis.axhline(0.0, color="black", linewidth=0.8)
        axis.set_title("Prediction RankIC by model and market regime")
        axis.set_ylabel("Mean daily RankIC")
        axis.grid(axis="y", alpha=0.2)
    _save_figure(figure, destination)


def _comparison_markdown(
    comparison: pd.DataFrame, disclaimer: Optional[str] = None
) -> str:
    lines = [
        "# FactorLab Phase 3 模型比较",
        "",
    ]
    if disclaimer:
        lines.extend(["> **%s**" % disclaimer.strip(), ""])
    lines.extend(
        [
            "本表仅客观并列各模型已完成的 Walk-Forward 样本外指标，不自动评选最佳模型，"
            "也不使用最终测试结果重新选择参数。",
            "",
        ]
    )
    if comparison.empty:
        lines.append("No completed model records are available.")
        lines.append("")
        return "\n".join(lines)
    preferred = [
        "model_name",
        "prediction_ic_mean",
        "prediction_rank_ic_mean",
        "prediction_icir",
        "prediction_rank_icir",
        "top_bottom_spread",
        "cumulative_return",
        "annualized_return",
        "sharpe_ratio",
        "maximum_drawdown",
        "information_ratio",
        "portfolio_turnover",
        "total_transaction_cost",
        "execution_cumulative_return",
        "execution_excess_return",
        "execution_sharpe_ratio",
        "execution_maximum_drawdown",
        "execution_total_transaction_cost",
    ]
    columns = [name for name in preferred if name in comparison.columns]
    if "model_name" not in columns:
        columns.insert(0, "model_name")
    lines.append("| %s |" % " | ".join(columns))
    lines.append("|%s|" % "|".join("---" if name == "model_name" else "---:" for name in columns))
    for row in comparison.loc[:, columns].itertuples(index=False, name=None):
        lines.append("| %s |" % " | ".join(_format_value(value) for value in row))
    lines.append("")
    return "\n".join(lines)


def _summary_markdown(
    model_name: str,
    walk_forward: WalkForwardResult,
    prediction: PredictionEvaluation,
    backtest: FastBacktestResult,
    metrics: pd.DataFrame,
    disclaimer: Optional[str] = None,
    execution_backtest: Optional[ExecutionBacktestResult] = None,
    execution_metrics: Optional[pd.DataFrame] = None,
) -> str:
    fold_count = (
        int(walk_forward.fold_summary["fold"].nunique())
        if "fold" in walk_forward.fold_summary and not walk_forward.fold_summary.empty
        else 0
    )
    prediction_rows = len(walk_forward.predictions)
    nav_rows = len(backtest.nav)
    trade_rows = len(backtest.trades)
    lines = [
        "# FactorLab Phase 3 模型报告",
        "",
    ]
    if disclaimer:
        lines.extend(["> **%s**" % disclaimer.strip(), ""])
    lines.extend(
        [
            "- Model: `%s`" % model_name,
            "- Walk-forward folds: %d" % fold_count,
            "- Out-of-sample prediction rows: %d" % prediction_rows,
            "- Backtest trading dates: %d" % nav_rows,
            "- Recorded trades: %d" % trade_rows,
            "",
            "所有预测指标均来自 Walk-Forward 的测试区间；验证区间仅用于已配置候选参数的选择。"
            "本报告不依据最终测试收益重新选择因子、模型、Top-K 或交易成本。",
            "",
            "## Prediction quality",
            "",
        ]
    )
    overall = _overall_prediction(prediction.summary)
    if overall.empty:
        lines.append("No realised out-of-sample prediction metrics are available.")
    else:
        selected = (
            "prediction_ic_mean",
            "prediction_icir",
            "prediction_rank_ic_mean",
            "prediction_rank_icir",
            "top_k_future_return",
            "bottom_k_future_return",
            "top_bottom_spread",
            "score_coverage",
            "coverage",
            "top_label_coverage",
            "bottom_label_coverage",
            "valid_dates",
            "rank_ic_valid_dates",
        )
        row = overall.iloc[0]
        lines.extend(["| Metric | Value |", "|---|---:|"])
        for metric in selected:
            if metric in overall.columns:
                lines.append("| %s | %s |" % (metric, _format_value(row[metric])))
    lines.extend(["", "## Portfolio performance", ""])
    if metrics.empty:
        lines.append("No portfolio metrics are available.")
    else:
        lines.extend(["| Metric | Value |", "|---|---:|"])
        for row in metrics.itertuples(index=False):
            lines.append("| %s | %s |" % (row.metric, _format_value(row.value)))
    if execution_backtest is not None:
        lines.extend(
            [
                "",
                "## Rule-aware execution performance",
                "",
                "该层使用次日开盘、T+1、100股整数手、现金约束、停牌和涨跌停日线近似。"
                "日线无法重建盘口队列，拒单记录见 `execution_rejections.csv`。",
                "",
                "- Executed trades: %d" % len(execution_backtest.trades),
                "- Rejected order fragments: %d"
                % len(execution_backtest.rejections),
                "",
            ]
        )
        if execution_metrics is None or execution_metrics.empty:
            lines.append("No execution metrics are available.")
        else:
            lines.extend(["| Metric | Value |", "|---|---:|"])
            for row in execution_metrics.itertuples(index=False):
                lines.append(
                    "| %s | %s |" % (row.metric, _format_value(row.value))
                )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            "CSV files are intended for review and course-report tables; matching Parquet files "
            "preserve data types for reproducible analysis. Daily-bar execution is an approximation "
            "and cannot reconstruct order-book liquidity or limit-order queues.",
            "",
        ]
    )
    return "\n".join(lines)


def write_model_report(
    model_name: str,
    walk_forward: WalkForwardResult,
    prediction_evaluation: PredictionEvaluation,
    backtest: FastBacktestResult,
    portfolio_metrics: Mapping[str, Any],
    output_dir: Path,
    disclaimer: Optional[str] = None,
    execution_backtest: Optional[ExecutionBacktestResult] = None,
    execution_metrics: Optional[Mapping[str, Any]] = None,
) -> Path:
    """Write one model's complete Phase-3 artifact directory.

    Returns the path to ``summary.md``.  Mandatory plots are still created for
    empty inputs, using an explicit ``No data available`` marker.  Ridge
    coefficient artifacts are emitted only when coefficients are present.
    """

    if not isinstance(model_name, str) or not model_name.strip():
        raise ModelReportError("model_name must be a non-empty string")
    if not isinstance(walk_forward, WalkForwardResult):
        raise ModelReportError("walk_forward must be a WalkForwardResult")
    if not isinstance(prediction_evaluation, PredictionEvaluation):
        raise ModelReportError(
            "prediction_evaluation must be a PredictionEvaluation"
        )
    if not isinstance(backtest, FastBacktestResult):
        raise ModelReportError("backtest must be a FastBacktestResult")
    if execution_backtest is not None and not isinstance(
        execution_backtest, ExecutionBacktestResult
    ):
        raise ModelReportError(
            "execution_backtest must be an ExecutionBacktestResult"
        )
    if execution_backtest is None and execution_metrics is not None:
        raise ModelReportError(
            "execution_metrics require execution_backtest"
        )

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    metric_table = _metric_frame(portfolio_metrics)
    tables: Dict[str, pd.DataFrame] = {
        "predictions": walk_forward.predictions,
        "walk_forward_results": walk_forward.fold_summary,
        "validation_results": walk_forward.validation_metrics,
        "prediction_daily": prediction_evaluation.daily,
        "prediction_summary": prediction_evaluation.summary,
        "nav": backtest.nav,
        "trades": backtest.trades,
        "positions": backtest.positions,
        "signals": backtest.signals,
        "portfolio_metrics": metric_table,
    }
    for name in _TABLE_NAMES:
        _write_table(tables[name].copy(), name, destination)

    execution_metric_table = pd.DataFrame(columns=["metric", "value"])
    if execution_backtest is not None:
        execution_metric_table = _metric_frame(execution_metrics or {})
        execution_tables = {
            "execution_nav": execution_backtest.nav,
            "execution_trades": execution_backtest.trades,
            "execution_positions": execution_backtest.positions,
            "execution_rejections": execution_backtest.rejections,
            "execution_signals": execution_backtest.signals,
            "execution_portfolio_metrics": execution_metric_table,
        }
        for name, table in execution_tables.items():
            _write_table(table.copy(), name, destination)
        _plot_nav(
            execution_backtest.nav,
            destination / "execution_nav_curve.png",
        )
        _plot_drawdown(
            execution_backtest.nav,
            destination / "execution_drawdown.png",
        )

    if not walk_forward.coefficients.empty:
        _write_table(
            walk_forward.coefficients.copy(),
            "ridge_coefficients",
            destination,
        )
        _plot_coefficients(
            walk_forward.coefficients,
            destination / "ridge_coefficients.png",
        )

    if not walk_forward.feature_importance.empty:
        _write_table(
            walk_forward.feature_importance.copy(),
            "feature_importance",
            destination,
        )
        _plot_feature_importance(
            walk_forward.feature_importance,
            destination / "feature_importance.png",
        )

    _plot_nav(backtest.nav, destination / "nav_curve.png")
    _plot_drawdown(backtest.nav, destination / "drawdown.png")
    _plot_prediction_ic(
        prediction_evaluation.daily,
        destination / "prediction_ic.png",
    )
    _plot_regime_performance(
        prediction_evaluation.summary,
        destination / "regime_performance.png",
    )
    _plot_daily_bar(
        backtest.nav,
        "turnover",
        "Daily portfolio turnover",
        "Turnover",
        destination / "turnover.png",
    )
    _plot_daily_bar(
        backtest.nav,
        "transaction_cost",
        "Daily transaction cost",
        "CNY",
        destination / "transaction_cost.png",
    )

    summary_path = destination / "summary.md"
    _atomic_text(
        _summary_markdown(
            model_name.strip(),
            walk_forward,
            prediction_evaluation,
            backtest,
            metric_table,
            disclaimer,
            execution_backtest,
            execution_metric_table,
        ),
        summary_path,
    )
    return summary_path


def write_model_comparison_report(
    comparison: Any,
    output_dir: Path,
    disclaimer: Optional[str] = None,
    details: Optional[Mapping[str, pd.DataFrame]] = None,
) -> Path:
    """Write an objective, non-selecting comparison of completed model runs.

    ``comparison`` may be an already-flat DataFrame, an iterable of flat
    mappings, or a mapping keyed by model name.  Structured records can supply
    ``prediction``/``prediction_summary`` and ``portfolio_metrics``; their
    overall values are merged into one row per model.  The function never
    ranks models or recommends one from final-test performance.
    """

    comparison = _comparison_frame(comparison)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    _atomic_csv(comparison, destination / "model_comparison.csv")
    _plot_model_ic(comparison, destination / "model_ic_comparison.png")
    detail_tables: Dict[str, pd.DataFrame] = {}
    if details is not None:
        if not isinstance(details, Mapping):
            raise ModelReportError("details must be a mapping of DataFrames")
        for raw_name, table in details.items():
            name = str(raw_name)
            if (
                not name
                or Path(name).name != name
                or not name.replace("_", "").isalnum()
            ):
                raise ModelReportError("detail table name is unsafe: %r" % raw_name)
            if not isinstance(table, pd.DataFrame):
                raise ModelReportError("detail table %s must be a DataFrame" % name)
            detail_tables[name] = table.copy()
            _write_table(detail_tables[name], name, destination)
    nav = detail_tables.get("nav", pd.DataFrame())
    _plot_comparison_nav(nav, destination / "nav_curve.png")
    _plot_comparison_drawdown(nav, destination / "drawdown.png")
    _plot_comparison_daily_metric(
        nav,
        "turnover",
        "Daily portfolio turnover by model",
        "Turnover",
        destination / "turnover.png",
    )
    _plot_comparison_daily_metric(
        nav,
        "transaction_cost",
        "Daily transaction cost by model",
        "CNY",
        destination / "transaction_cost.png",
    )
    _plot_comparison_feature_importance(
        detail_tables.get("feature_importance", pd.DataFrame()),
        destination / "feature_importance.png",
    )
    _plot_comparison_regime(
        detail_tables.get("prediction_summary", pd.DataFrame()),
        destination / "regime_performance.png",
    )
    summary_path = destination / "summary.md"
    _atomic_text(_comparison_markdown(comparison, disclaimer), summary_path)
    return summary_path


__all__ = [
    "ModelReportError",
    "write_model_comparison_report",
    "write_model_report",
]
