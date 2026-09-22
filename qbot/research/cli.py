"""Command-line interface for the isolated FactorLab research pipeline."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from qbot.research.backtest import FastBacktestConfig, FeeSchedule, run_fast_backtest
from qbot.research.config import ResearchConfig, load_config
from qbot.research.data import AKShareProvider, ParquetBarCache, TradingCalendar
from qbot.research.dataset import DatasetBuildOptions, DatasetBuilder
from qbot.research.errors import FactorLabError, PointInTimeUniverseRequiredError
from qbot.research.metrics import (
    calculate_portfolio_metrics,
    evaluate_factors,
    evaluate_predictions,
)
from qbot.research.reports import (
    write_factor_report,
    write_model_comparison_report,
    write_model_report,
)
from qbot.research.reproducibility import (
    PROVENANCE_FIELDS,
    RunManifest,
    set_random_seed,
    validate_provenance,
)
from qbot.research.universe.csi500 import (
    BaoStockPointInTimeProvider,
    collect_point_in_time_universe,
    dataframe_sha256,
    import_point_in_time_universe,
    validate_daily_membership,
)
from qbot.research.universe.filters import UniverseFilterConfig
from qbot.research.validation import ExpandingWalkForwardSplitter, WalkForwardRunner


LOGGER = logging.getLogger("qbot.research")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m qbot.research.cli",
        description="Qbot FactorLab research pipeline (NO LIVE MONEY)",
    )
    parser.add_argument("--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("audit", "download-data", "build-dataset", "evaluate-factors"):
        command = subparsers.add_parser(name)
        command.add_argument("--config", required=True)
    importer = subparsers.add_parser("import-universe")
    importer.add_argument("--config", required=True)
    importer.add_argument("--input", required=True, dest="input_path")
    walk_forward = subparsers.add_parser("walk-forward")
    walk_forward.add_argument("--config", required=True)
    walk_forward.add_argument(
        "--model", required=True, choices=("factor_score", "ridge")
    )
    comparison = subparsers.add_parser("compare-models")
    comparison.add_argument("--config", required=True)
    return parser


def _atomic_parquet(frame: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(".%s.tmp" % destination.name)
    frame.to_parquet(temporary, index=False)
    os.replace(str(temporary), str(destination))


def _atomic_json(payload: Any, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(".%s.tmp" % destination.name)
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(str(temporary), str(destination))


def _atomic_csv(frame: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(".%s.tmp" % destination.name)
    frame.to_csv(temporary, index=False)
    os.replace(str(temporary), str(destination))


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdefABCDEF" for character in value)
    )


def _artifact_sha256(directory: Path) -> Dict[str, str]:
    """Hash every regular report artifact using stable POSIX-relative names."""

    root = Path(directory)
    return {
        path.relative_to(root).as_posix(): _file_sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _dataset_contract(config: ResearchConfig) -> Dict[str, Any]:
    """Return only configuration fields that determine dataset contents."""

    return _dataset_contract_from_snapshot(config.to_dict())


def _dataset_contract_from_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the dataset-relevant subset from a serialized full config."""

    if not isinstance(snapshot, dict):
        raise FactorLabError("serialized config is not a mapping")
    try:
        minimum_cross_section = snapshot["evaluation"]["min_cross_section"]
        factor_list = snapshot["factors"]
        data = snapshot["data"]
        universe = snapshot["universe"]
        label = snapshot["label"]
        preprocessing = snapshot["preprocessing"]
    except (KeyError, TypeError) as exc:
        raise FactorLabError(
            "serialized config is missing dataset-contract fields"
        ) from exc
    return {
        "data": data,
        "universe": universe,
        "label": label,
        "preprocessing": preprocessing,
        "minimum_cross_section": minimum_cross_section,
        "factor_list": factor_list,
    }


def _provider(config: ResearchConfig) -> AKShareProvider:
    if config.data.provider.lower() != "akshare":
        raise FactorLabError("Phase 1 only implements data.provider=akshare")
    return AKShareProvider(
        benchmark_symbol=config.data.benchmark,
        adjustment=config.data.adjustment,
        retry_count=config.network.max_retries,
        backoff_seconds=config.network.backoff_seconds,
        request_interval=config.network.request_interval_seconds,
    )


def _benchmark_cache(config: ResearchConfig) -> ParquetBarCache:
    return ParquetBarCache(config.paths.benchmark_dir)


def _stock_cache(config: ResearchConfig) -> ParquetBarCache:
    return ParquetBarCache(config.paths.raw_dir / "akshare" / "daily")


def _benchmark_request_start(config: ResearchConfig) -> pd.Timestamp:
    """Return a conservative civil date used to discover exact warm-up sessions."""

    research_start = pd.Timestamp(config.data.start)
    warmup = int(config.data.warmup_trading_days)
    if warmup == 0:
        return research_start
    # Fetch more civil days than requested market sessions, then select the
    # exact final N sessions from the returned benchmark calendar.
    estimated_days = (warmup * 365 + 239) // 240 + 60
    return research_start - pd.Timedelta(days=max(366, estimated_days))


def _select_benchmark_with_warmup(
    config: ResearchConfig, bars: pd.DataFrame
) -> pd.DataFrame:
    """Select exactly N pre-start sessions plus the configured research range."""

    start = pd.Timestamp(config.data.start)
    end = pd.Timestamp(config.data.end)
    available = bars.loc[bars["date"] <= end].sort_values("date", kind="mergesort")
    research = available.loc[available["date"].between(start, end)]
    if research.empty:
        raise FactorLabError(
            "Benchmark cache has no bars in the configured research interval"
        )
    prior = available.loc[available["date"] < start]
    warmup = int(config.data.warmup_trading_days)
    if len(prior) < warmup:
        raise FactorLabError(
            "Benchmark cache has only %d/%d required warm-up trading sessions"
            % (len(prior), warmup)
        )
    selected_dates = pd.DatetimeIndex(prior["date"].tail(warmup)).append(
        pd.DatetimeIndex(research["date"])
    )
    return available.loc[available["date"].isin(selected_dates)].reset_index(drop=True)


def _download_benchmark_with_warmup(
    config: ResearchConfig, provider: AKShareProvider
) -> pd.DataFrame:
    cache = _benchmark_cache(config)
    bars = cache.update_from_provider(
        provider,
        config.data.benchmark,
        _benchmark_request_start(config),
        config.data.end,
        is_index=True,
    )
    return _select_benchmark_with_warmup(config, bars)


def _load_benchmark_with_warmup(config: ResearchConfig) -> pd.DataFrame:
    bars = _benchmark_cache(config).load(config.data.benchmark)
    if bars.empty:
        raise FactorLabError(
            "Benchmark cache is empty; run download-data before this command"
        )
    return _select_benchmark_with_warmup(config, bars)


def _research_calendar(
    config: ResearchConfig, full_calendar: pd.DatetimeIndex
) -> pd.DatetimeIndex:
    start = pd.Timestamp(config.data.start)
    end = pd.Timestamp(config.data.end)
    result = full_calendar[(full_calendar >= start) & (full_calendar <= end)]
    if result.empty:
        raise FactorLabError("Benchmark research calendar is empty")
    return result


def _load_verified_membership(
    config: ResearchConfig, calendar: pd.DatetimeIndex
) -> pd.DataFrame:
    path = config.paths.universe_dir / "csi500_daily.parquet"
    manifest_path = config.paths.universe_dir / "manifest.json"
    if not path.exists() or not manifest_path.exists():
        raise PointInTimeUniverseRequiredError(
            "validated daily files are missing; run download-data or import-universe"
        )
    membership = validate_daily_membership(
        pd.read_parquet(path), calendar, config.universe.expected_member_count
    )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, AttributeError) as exc:
        raise PointInTimeUniverseRequiredError("universe manifest is unreadable") from exc
    if not isinstance(manifest, dict):
        raise PointInTimeUniverseRequiredError("universe manifest must be a mapping")
    dates = pd.DatetimeIndex(pd.to_datetime(calendar, errors="raise")).normalize()
    source = config.universe.provider.lower()
    if source == "baostock":
        expected_source = "BaoStockPointInTimeProvider"
        expected_source_version = "baostock-query_zz500_stocks-daily-v1"
    elif source == "local":
        expected_source = "local-import"
        expected_source_version = "user-pit-daily-import-v1"
    else:
        raise PointInTimeUniverseRequiredError(
            "universe.provider must be baostock or local"
        )
    expected = {
        "schema_version": 1,
        "source": expected_source,
        "source_version": expected_source_version,
        "index_symbol": config.universe.index_symbol,
        "start": dates.min().strftime("%Y-%m-%d"),
        "end": dates.max().strftime("%Y-%m-%d"),
        "trading_dates": int(dates.nunique()),
        "expected_member_count": int(config.universe.expected_member_count),
    }
    mismatches = [
        name for name, expected_value in expected.items()
        if manifest.get(name) != expected_value
    ]
    if mismatches:
        raise PointInTimeUniverseRequiredError(
            "universe manifest mismatch (%s); rebuild the PIT universe"
            % ", ".join(mismatches)
        )
    if source == "local":
        source_file = manifest.get("source_file")
        if not isinstance(source_file, str) or not source_file.strip():
            raise PointInTimeUniverseRequiredError(
                "local universe manifest source_file is missing"
            )
        if not _is_sha256(manifest.get("source_file_sha256")):
            raise PointInTimeUniverseRequiredError(
                "local universe manifest source_file_sha256 is invalid"
            )
    try:
        generated_at = pd.Timestamp(manifest.get("generated_at"))
    except (TypeError, ValueError) as exc:
        raise PointInTimeUniverseRequiredError(
            "universe manifest generated_at is invalid"
        ) from exc
    if pd.isna(generated_at):
        raise PointInTimeUniverseRequiredError(
            "universe manifest generated_at is invalid"
        )
    digest = manifest.get("sha256")
    if not _is_sha256(digest) or digest.lower() != dataframe_sha256(membership):
        raise PointInTimeUniverseRequiredError("universe content hash mismatch")
    return membership


def command_audit(config: ResearchConfig, run: RunManifest) -> None:
    required = [
        "ARCHITECTURE_AUDIT.md",
        "KNOWN_LEGACY_ISSUES.md",
    ]
    docs_dir = (config.repo_root or Path.cwd()) / "docs" / "research"
    missing = [name for name in required if not (docs_dir / name).is_file()]
    if missing:
        raise FactorLabError("Architecture audit artifacts missing: %s" % missing)
    run.add_output("architecture_audit", docs_dir / required[0])
    LOGGER.info("Architecture audit available at %s", docs_dir / required[0])


def command_download(config: ResearchConfig, run: RunManifest) -> None:
    provider = _provider(config)
    benchmark_cache = _benchmark_cache(config)
    benchmark = _download_benchmark_with_warmup(config, provider)
    full_calendar = TradingCalendar.from_benchmark_bars(benchmark).dates
    calendar = _research_calendar(config, full_calendar)
    run.add_output("benchmark", benchmark_cache.data_path(config.data.benchmark))
    LOGGER.info(
        "Benchmark calendar contains %d research and %d warm-up sessions",
        len(calendar),
        len(full_calendar) - len(calendar),
    )

    universe_provider = config.universe.provider.lower()
    if universe_provider not in {"baostock", "local"}:
        raise PointInTimeUniverseRequiredError(
            "Phase 1 requires universe.provider=baostock or local"
        )
    manifest_path = config.paths.universe_dir / "manifest.json"
    existing_manifest: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            existing_manifest = {}
    if universe_provider == "local" and existing_manifest.get("source") != "local-import":
        raise PointInTimeUniverseRequiredError(
            "universe.provider=local requires a validated import-universe artifact"
        )
    with BaoStockPointInTimeProvider(
        retry_count=config.network.max_retries,
        backoff_seconds=config.network.backoff_seconds,
        request_interval=config.network.request_interval_seconds,
    ) as pit_provider:
        if universe_provider == "local":
            membership = _load_verified_membership(config, calendar)
            universe_manifest = existing_manifest
            LOGGER.info("Reusing validated local-import PIT universe")
        else:
            universe_manifest = collect_point_in_time_universe(
                pit_provider,
                config.universe.index_symbol,
                calendar,
                config.paths.universe_dir,
                expected_member_count=config.universe.expected_member_count,
                retries=config.network.max_retries,
                backoff_seconds=config.network.backoff_seconds,
                request_interval_seconds=config.network.request_interval_seconds,
            )
            membership = _load_verified_membership(config, calendar)
        symbols = membership["symbol"].drop_duplicates().sort_values().tolist()
        status, listings, status_failures = pit_provider.get_security_history(
            symbols, full_calendar.min(), full_calendar.max()
        )
    _atomic_parquet(status, config.paths.universe_dir / "security_status.parquet")
    _atomic_parquet(listings, config.paths.universe_dir / "listing_dates.parquet")
    _atomic_json(status_failures, config.paths.universe_dir / "status_failures.json")
    run.payload["universe_version"] = universe_manifest["sha256"]
    run.add_output("universe", config.paths.universe_dir / "csi500_daily.parquet")
    if status_failures:
        run.add_failures("security_status", status_failures)

    cache = _stock_cache(config)
    failures: Dict[str, str] = {}
    for number, symbol in enumerate(symbols, start=1):
        try:
            cache.update_from_provider(
                provider,
                symbol,
                full_calendar.min(),
                full_calendar.max(),
                is_index=False,
            )
        except Exception as exc:
            failures[symbol] = str(exc)
            LOGGER.warning("Market data failed for %s: %s", symbol, exc)
        if number % 25 == 0 or number == len(symbols):
            LOGGER.info("Downloaded/checked %d/%d securities", number, len(symbols))
    failure_path = config.paths.raw_dir / "akshare" / "failed_symbols.json"
    _atomic_json(failures, failure_path)
    run.add_failures("market_data", failures)
    run.add_output("failed_symbols", failure_path)
    LOGGER.info("Market data completed with %d failed symbols", len(failures))


def command_import_universe(
    config: ResearchConfig, run: RunManifest, input_path: str
) -> None:
    if config.universe.provider.lower() != "local":
        raise PointInTimeUniverseRequiredError(
            "import-universe requires universe.provider=local"
        )
    try:
        benchmark = _load_benchmark_with_warmup(config)
    except FactorLabError:
        provider = _provider(config)
        benchmark = _download_benchmark_with_warmup(config, provider)
    full_calendar = TradingCalendar.from_benchmark_bars(benchmark).dates
    calendar = _research_calendar(config, full_calendar)
    manifest = import_point_in_time_universe(
        Path(input_path),
        config.paths.universe_dir,
        calendar,
        expected_member_count=config.universe.expected_member_count,
        index_symbol=config.universe.index_symbol,
    )
    run.payload["universe_version"] = manifest["sha256"]
    run.add_output("universe", config.paths.universe_dir / "csi500_daily.parquet")
    LOGGER.info("Imported and validated %d PIT sessions", manifest["trading_dates"])


def _load_stock_bars(config: ResearchConfig, symbols: Iterable[str]) -> pd.DataFrame:
    cache = _stock_cache(config)
    parts: List[pd.DataFrame] = []
    missing: List[str] = []
    for symbol in symbols:
        bars = cache.load(symbol)
        if bars.empty:
            missing.append(symbol)
        else:
            parts.append(bars)
    if missing:
        LOGGER.warning("No cached bars for %d member securities", len(missing))
    if not parts:
        raise FactorLabError("No stock bars are available; run download-data first")
    return pd.concat(parts, ignore_index=True)


def command_build_dataset(config: ResearchConfig, run: RunManifest) -> None:
    benchmark = _load_benchmark_with_warmup(config)
    calendar = TradingCalendar.from_benchmark_bars(benchmark).dates
    research_calendar = _research_calendar(config, calendar)
    membership = _load_verified_membership(config, research_calendar)
    symbols = membership["symbol"].drop_duplicates().sort_values().tolist()
    bars = _load_stock_bars(config, symbols)
    status_path = config.paths.universe_dir / "security_status.parquet"
    listing_path = config.paths.universe_dir / "listing_dates.parquet"
    if not status_path.exists() or not listing_path.exists():
        raise FactorLabError("BaoStock status/listing cache is missing; run download-data")
    status = pd.read_parquet(status_path)
    listings = pd.read_parquet(listing_path)
    filter_config = UniverseFilterConfig(
        min_listed_days=config.universe.min_listed_days,
        exclude_st=config.universe.exclude_st,
        exclude_suspended=config.universe.exclude_suspended,
        zero_volume_window=config.universe.zero_volume_window_days,
        quality_window=config.universe.data_quality_window_days,
        min_quality_ratio=config.universe.min_valid_ohlcv_ratio,
    )
    options = DatasetBuildOptions(
        factor_names=config.factors,
        holding_days=config.label.holding_days,
        entry_price=config.label.entry_price,
        expected_member_count=config.universe.expected_member_count,
        winsorization=config.preprocessing.winsorization,
        mad_multiplier=config.preprocessing.mad_multiplier,
        minimum_cross_section=config.evaluation.min_cross_section,
        filter_config=filter_config,
    )
    builder = DatasetBuilder(options)
    dataset = builder.build(bars, benchmark, membership, status, listings, calendar)
    destination = config.paths.processed_dir / "dataset.parquet"
    builder.write_artifacts(dataset, destination, config.paths.features_dir)
    dataset_manifest_path = config.paths.processed_dir / "dataset_manifest.json"
    dataset_sha256 = _file_sha256(destination)
    universe_version = dataframe_sha256(membership)
    _atomic_json(
        {
            "schema_version": 2,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dataset_path": str(destination),
            "dataset_sha256": dataset_sha256,
            "universe_version": universe_version,
            "factor_list": list(config.factors),
            "target": _target_column(config),
            "rows": int(len(dataset)),
            "dates": int(dataset["date"].nunique()),
            "data_start": config.data.start.isoformat(),
            "data_end": config.data.end.isoformat(),
            "dataset_contract": _dataset_contract(config),
            "producer_run_id": run.run_id,
            "producer_provenance": validate_provenance(run.payload),
        },
        dataset_manifest_path,
    )
    run.add_output("dataset", destination)
    run.add_output("dataset_manifest", dataset_manifest_path)
    run.payload["dataset_rows"] = int(len(dataset))
    run.payload["dataset_dates"] = int(dataset["date"].nunique())
    run.payload["dataset_sha256"] = dataset_sha256
    run.payload["universe_version"] = universe_version
    LOGGER.info("Dataset written: %d rows across %d dates", len(dataset), dataset["date"].nunique())


def command_evaluate(config: ResearchConfig, run: RunManifest) -> None:
    benchmark = _load_benchmark_with_warmup(config)
    full_calendar = TradingCalendar.from_benchmark_bars(benchmark).dates
    research_calendar = _research_calendar(config, full_calendar)
    dataset, dataset_sha256, universe_version = _load_verified_dataset(
        config, research_calendar, run
    )
    run.payload["dataset_sha256"] = dataset_sha256
    run.payload["universe_version"] = universe_version
    target = _target_column(config)
    evaluation = evaluate_factors(
        dataset,
        config.factors,
        target=target,
        quantiles=config.evaluation.quantiles,
        minimum_cross_section=config.evaluation.min_cross_section,
    )
    summary = write_factor_report(evaluation, config.paths.factor_results_dir)
    run.add_output("factor_report", summary)
    valid_rank_ic = int(evaluation.daily_ic["RankIC"].notna().sum())
    run.payload["valid_rank_ic_observations"] = valid_rank_ic
    if valid_rank_ic == 0:
        raise FactorLabError("Factor evaluation produced no valid RankIC observations")
    LOGGER.info("Factor report written with %d valid daily RankIC values", valid_rank_ic)


def _target_column(config: ResearchConfig) -> str:
    return "EXCESS_RET%d" % config.label.holding_days


def _load_verified_dataset(
    config: ResearchConfig,
    research_calendar: pd.DatetimeIndex,
    run: Optional[RunManifest] = None,
) -> tuple:
    membership = _load_verified_membership(config, research_calendar)
    universe_version = dataframe_sha256(membership)
    dataset_path = config.paths.processed_dir / "dataset.parquet"
    manifest_path = config.paths.processed_dir / "dataset_manifest.json"
    if not dataset_path.exists():
        raise FactorLabError("Dataset is missing; run build-dataset first")
    if not manifest_path.exists():
        raise FactorLabError(
            "Dataset manifest is missing; rebuild the dataset before evaluation"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, AttributeError) as exc:
        raise FactorLabError("Dataset manifest is unreadable") from exc
    dataset_sha256 = _file_sha256(dataset_path)
    expected = {
        "schema_version": 2,
        "dataset_sha256": dataset_sha256,
        "universe_version": universe_version,
        "factor_list": list(config.factors),
        "target": _target_column(config),
        "data_start": config.data.start.isoformat(),
        "data_end": config.data.end.isoformat(),
        "dataset_contract": _dataset_contract(config),
    }
    mismatches = [name for name, value in expected.items() if manifest.get(name) != value]
    if mismatches:
        raise FactorLabError(
            "Dataset manifest mismatch (%s); rebuild before evaluation"
            % ", ".join(mismatches)
        )
    try:
        producer_provenance = validate_provenance(
            manifest.get("producer_provenance", {})
        )
    except ValueError as exc:
        raise FactorLabError(
            "Dataset manifest has missing or unknown producer provenance: %s"
            % exc
        ) from exc
    producer_run_id = manifest.get("producer_run_id")
    if (
        not isinstance(producer_run_id, str)
        or not producer_run_id.strip()
        or Path(producer_run_id).name != producer_run_id
    ):
        raise FactorLabError("Dataset manifest producer_run_id is missing")
    producer_manifest_path = (
        config.paths.runs_dir / producer_run_id / "manifest.json"
    )
    try:
        producer_manifest = json.loads(
            producer_manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError, AttributeError) as exc:
        raise FactorLabError(
            "Dataset producer run manifest is missing or unreadable"
        ) from exc
    producer_expected = {
        "run_id": producer_run_id,
        "command": "build-dataset",
        "status": "success",
        "dataset_sha256": dataset_sha256,
        "universe_version": universe_version,
    }
    producer_mismatches = [
        name
        for name, expected_value in producer_expected.items()
        if producer_manifest.get(name) != expected_value
    ]
    if producer_mismatches:
        raise FactorLabError(
            "Dataset producer run manifest mismatch (%s)"
            % ", ".join(producer_mismatches)
        )
    try:
        producer_contract = _dataset_contract_from_snapshot(
            producer_manifest.get("config")
        )
    except FactorLabError as exc:
        raise FactorLabError(
            "Dataset producer run config is invalid: %s" % exc
        ) from exc
    if producer_contract != manifest.get("dataset_contract"):
        raise FactorLabError(
            "Dataset producer run config does not match the dataset contract"
        )
    try:
        recorded_producer_provenance = validate_provenance(producer_manifest)
    except ValueError as exc:
        raise FactorLabError(
            "Dataset producer run has missing or unknown provenance: %s" % exc
        ) from exc
    if recorded_producer_provenance != producer_provenance:
        raise FactorLabError(
            "Dataset manifest producer provenance differs from its build run"
        )
    if run is not None:
        current_provenance = _comparison_provenance(
            run.payload, "Current dataset consumer run"
        )
        mismatched_provenance = [
            field
            for field in PROVENANCE_FIELDS
            if producer_provenance[field] != current_provenance[field]
        ]
        if mismatched_provenance:
            raise FactorLabError(
                "Dataset producer provenance differs from the current environment (%s); "
                "rebuild the dataset"
                % ", ".join(mismatched_provenance)
            )
        run.payload["dataset_producer_run_id"] = producer_run_id
        run.payload["dataset_producer_provenance"] = producer_provenance
    dataset = pd.read_parquet(dataset_path)
    required = {
        "date",
        "symbol",
        "entry_date",
        "exit_date",
        _target_column(config),
    }.union(config.factors)
    missing = sorted(required.difference(dataset.columns))
    if missing:
        raise FactorLabError(
            "Dataset is missing model/audit columns: %s" % ", ".join(missing)
        )
    if dataset.empty:
        raise FactorLabError("Dataset is empty")
    result = dataset.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise").dt.normalize()
    result.sort_values(["date", "symbol"], kind="mergesort", inplace=True)
    result.reset_index(drop=True, inplace=True)
    if result.duplicated(["date", "symbol"]).any():
        raise FactorLabError("Dataset contains duplicate (date, symbol) rows")
    if manifest.get("rows") != len(result) or manifest.get("dates") != result["date"].nunique():
        raise FactorLabError("Dataset manifest row/date counts do not match the data")
    return result, dataset_sha256, universe_version


def _walk_forward_splitter(config: ResearchConfig) -> ExpandingWalkForwardSplitter:
    values = config.validation
    return ExpandingWalkForwardSplitter(
        initial_train_months=values.initial_train_months,
        validation_months=values.validation_months,
        test_months=values.test_months,
        step_months=values.step_months,
        purge_days=values.purge_days,
        embargo_days=values.embargo_days,
    )


def _model_hyperparameters(config: ResearchConfig, model_name: str) -> Dict[str, Any]:
    if model_name == "factor_score":
        return {
            "weights": dict(config.models.factor_score.weights),
            "normalize_by_absolute_weight": (
                config.models.factor_score.normalize_by_absolute_weight
            ),
        }
    return {
        "alphas": list(config.models.ridge.alphas),
        "fit_intercept": config.models.ridge.fit_intercept,
        "max_iter": config.models.ridge.max_iter,
        "tolerance": config.models.ridge.tolerance,
    }


def _json_metrics(values: Dict[str, float]) -> Dict[str, Optional[float]]:
    result: Dict[str, Optional[float]] = {}
    for name, value in values.items():
        numeric = float(value)
        result[name] = numeric if math.isfinite(numeric) else None
    return result


def _backtest_window(
    predictions: pd.DataFrame,
    bars: pd.DataFrame,
    benchmark: pd.DataFrame,
) -> tuple:
    start = pd.Timestamp(predictions["date"].min()).normalize()
    if "exit_date" not in predictions or predictions["exit_date"].dropna().empty:
        raise FactorLabError(
            "Out-of-sample predictions require exit_date for backtest horizon audit"
        )
    end = pd.to_datetime(predictions["exit_date"], errors="raise").max().normalize()
    benchmark_dates = pd.to_datetime(benchmark["date"], errors="raise").dt.normalize()
    selected_benchmark = benchmark.loc[benchmark_dates.between(start, end)].copy()
    bar_dates = pd.to_datetime(bars["date"], errors="raise").dt.normalize()
    selected_bars = bars.loc[bar_dates.between(start, end)].copy()
    if selected_benchmark.empty or selected_bars.empty:
        raise FactorLabError("Backtest price window is empty")
    return selected_bars, selected_benchmark


def command_walk_forward(
    config: ResearchConfig,
    run: RunManifest,
    model_name: str,
) -> None:
    """Run a leakage-audited Phase-2 model and its fast OOS backtest."""

    benchmark = _load_benchmark_with_warmup(config)
    full_calendar = TradingCalendar.from_benchmark_bars(benchmark).dates
    research_calendar = _research_calendar(config, full_calendar)
    dataset, dataset_sha256, universe_version = _load_verified_dataset(
        config, research_calendar, run
    )
    output_dir = config.paths.model_results_dir / model_name / run.run_id
    model_dir = output_dir / "fold_models"

    runner_options: Dict[str, Any] = {
        "model_name": model_name,
        "feature_names": config.factors,
        "target_col": _target_column(config),
        "top_k": config.portfolio.top_k,
        "minimum_cross_section": config.evaluation.min_cross_section,
        "random_seed": config.seed,
        "model_directory": model_dir,
    }
    if model_name == "factor_score":
        weights = config.models.factor_score.weights
        if not weights:
            raise FactorLabError(
                "models.factor_score.weights are required for factor_score"
            )
        runner_options.update(
            factor_weights=weights,
            normalize_by_absolute_weight=(
                config.models.factor_score.normalize_by_absolute_weight
            ),
        )
    elif model_name == "ridge":
        runner_options.update(
            ridge_alphas=config.models.ridge.alphas,
            ridge_fit_intercept=config.models.ridge.fit_intercept,
            ridge_max_iter=config.models.ridge.max_iter,
            ridge_tolerance=config.models.ridge.tolerance,
        )
    else:
        raise FactorLabError("Phase 2 implements factor_score and ridge only")

    walk_forward = WalkForwardRunner(
        _walk_forward_splitter(config), **runner_options
    ).run(dataset, calendar=research_calendar)
    prediction = evaluate_predictions(
        walk_forward.predictions,
        target_col=_target_column(config),
        top_k=config.portfolio.top_k,
        minimum_cross_section=config.evaluation.min_cross_section,
        fold_col="fold",
    )
    overall = prediction.overall
    if overall.empty or int(overall.iloc[0]["rank_ic_valid_dates"]) == 0:
        raise FactorLabError("Walk-forward produced no valid out-of-sample RankIC")

    symbols = walk_forward.predictions["symbol"].drop_duplicates().sort_values()
    bars = _load_stock_bars(config, symbols)
    bars, backtest_benchmark = _backtest_window(
        walk_forward.predictions, bars, benchmark
    )
    backtest_stock_bars_sha256 = dataframe_sha256(bars)
    backtest_benchmark_sha256 = dataframe_sha256(backtest_benchmark)
    backtest = run_fast_backtest(
        walk_forward.predictions[["date", "symbol", "score"]],
        bars,
        backtest_benchmark,
        config=FastBacktestConfig(
            top_k=config.portfolio.top_k,
            rebalance_days=config.portfolio.rebalance_days,
            minimum_cross_section=config.evaluation.min_cross_section,
            initial_cash=config.backtest.initial_cash,
            price_column="adj_open",
            benchmark_price_column="adj_open",
        ),
        fee_schedule=FeeSchedule.from_config(config.fees),
    )
    portfolio_metrics = calculate_portfolio_metrics(
        backtest.nav,
        backtest.trades,
        backtest.positions,
        periods_per_year=config.backtest.annualization_days,
        risk_free_rate=config.backtest.risk_free_rate,
    )
    summary_path = write_model_report(
        model_name,
        walk_forward,
        prediction,
        backtest,
        portfolio_metrics,
        output_dir,
    )

    run.payload["model"] = model_name
    run.payload["dataset_sha256"] = dataset_sha256
    run.payload["universe_version"] = universe_version
    run.payload["backtest_stock_bars_sha256"] = backtest_stock_bars_sha256
    run.payload["backtest_benchmark_sha256"] = backtest_benchmark_sha256
    run.payload["hyperparameters"] = _model_hyperparameters(config, model_name)
    run.payload["walk_forward_folds"] = int(len(walk_forward.fold_summary))
    run.payload["out_of_sample_prediction_rows"] = int(
        len(walk_forward.predictions)
    )
    run.payload["prediction_metrics"] = {
        key: (None if pd.isna(value) else float(value))
        for key, value in overall.iloc[0].items()
        if key not in {"scope", "period"}
    }
    run.payload["portfolio_metrics"] = _json_metrics(portfolio_metrics)
    prediction_path = output_dir / "predictions.parquet"
    run.payload["predictions_sha256"] = _file_sha256(prediction_path)
    run.payload["model_artifact_sha256"] = _artifact_sha256(output_dir)
    run.add_output("model_report", summary_path)
    run.add_output("predictions", prediction_path)
    run.add_output("walk_forward_results", output_dir / "walk_forward_results.csv")
    run.add_output("nav", output_dir / "nav.csv")
    LOGGER.info(
        "%s completed: %d folds, %d OOS predictions",
        model_name,
        len(walk_forward.fold_summary),
        len(walk_forward.predictions),
    )


def _latest_model_output(config: ResearchConfig, model_name: str) -> Path:
    root = config.paths.model_results_dir / model_name
    required = (
        "predictions.parquet",
        "prediction_summary.csv",
        "portfolio_metrics.csv",
        "walk_forward_results.csv",
        "summary.md",
    )
    candidates = []
    if root.exists():
        for path in root.iterdir():
            if not path.is_dir() or not all(
                (path / name).is_file() for name in required
            ):
                continue
            manifest_path = config.paths.runs_dir / path.name / "manifest.json"
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, AttributeError):
                continue
            if manifest.get("status") != "success":
                continue
            if manifest.get("run_id") != path.name:
                continue
            if manifest.get("command") != "walk-forward":
                continue
            if manifest.get("model") != model_name:
                continue
            candidates.append(path)
    if not candidates:
        raise FactorLabError(
            "No completed %s report; run walk-forward --model %s first"
            % (model_name, model_name)
        )
    return sorted(candidates, key=lambda path: path.name)[-1]


def _comparison_provenance(
    payload: Dict[str, Any], description: str
) -> Dict[str, Any]:
    try:
        return validate_provenance(payload)
    except ValueError as exc:
        raise FactorLabError(
            "%s has missing or unknown provenance: %s" % (description, exc)
        ) from exc


def _prediction_oos_keys(
    model_name: str,
    output_dir: Path,
    manifest: Dict[str, Any],
    target_col: str,
) -> pd.DataFrame:
    prediction_path = output_dir / "predictions.parquet"
    expected_sha256 = manifest.get("predictions_sha256")
    if (
        not isinstance(expected_sha256, str)
        or len(expected_sha256) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in expected_sha256)
    ):
        raise FactorLabError(
            "%s run has missing or unknown predictions_sha256 provenance"
            % model_name
        )
    actual_sha256 = _file_sha256(prediction_path)
    if expected_sha256.lower() != actual_sha256:
        raise FactorLabError(
            "%s predictions.parquet SHA-256 mismatch" % model_name
        )
    try:
        predictions = pd.read_parquet(prediction_path)
    except Exception as exc:
        raise FactorLabError(
            "%s predictions.parquet is unreadable" % model_name
        ) from exc
    key_columns = ["date", "symbol", "fold"]
    audit_columns = ["entry_date", "exit_date", target_col]
    comparison_columns = key_columns + audit_columns
    missing = [name for name in comparison_columns if name not in predictions]
    if missing:
        raise FactorLabError(
            "%s predictions are missing OOS identity/audit columns: %s"
            % (model_name, ", ".join(missing))
        )
    keys = predictions.loc[:, comparison_columns].copy()
    required_non_null = key_columns + ["entry_date", "exit_date"]
    if keys.empty or keys[required_non_null].isna().any().any():
        raise FactorLabError(
            "%s predictions contain empty or null OOS keys" % model_name
        )
    if keys["symbol"].map(lambda value: not str(value).strip()).any():
        raise FactorLabError("%s predictions contain blank symbols" % model_name)
    try:
        keys["date"] = pd.to_datetime(keys["date"], errors="raise").dt.normalize()
        keys["entry_date"] = pd.to_datetime(
            keys["entry_date"], errors="raise"
        ).dt.normalize()
        keys["exit_date"] = pd.to_datetime(
            keys["exit_date"], errors="raise"
        ).dt.normalize()
        keys[target_col] = pd.to_numeric(keys[target_col], errors="raise")
        keys.sort_values(key_columns, kind="mergesort", inplace=True)
    except (TypeError, ValueError) as exc:
        raise FactorLabError(
            "%s predictions contain invalid OOS keys" % model_name
        ) from exc
    if keys.duplicated(key_columns).any():
        raise FactorLabError(
            "%s predictions contain duplicate (date, symbol, fold) OOS keys"
            % model_name
        )
    invalid_windows = ~(
        (keys["date"] < keys["entry_date"])
        & (keys["entry_date"] < keys["exit_date"])
    )
    if invalid_windows.any():
        raise FactorLabError(
            "%s predictions contain invalid label audit windows" % model_name
        )
    return keys.reset_index(drop=True)


def _verify_model_artifacts(
    model_name: str,
    output_dir: Path,
    manifest: Dict[str, Any],
) -> None:
    """Reject incomplete, missing, extra, or modified model report files."""

    expected = manifest.get("model_artifact_sha256")
    if not isinstance(expected, dict) or not expected:
        raise FactorLabError(
            "%s run has missing model artifact hash inventory" % model_name
        )
    required = {
        "predictions.parquet",
        "prediction_summary.csv",
        "portfolio_metrics.csv",
        "walk_forward_results.csv",
        "summary.md",
    }
    if not required.issubset(expected):
        missing = sorted(required.difference(expected))
        raise FactorLabError(
            "%s artifact hash inventory is missing: %s"
            % (model_name, ", ".join(missing))
        )
    actual = _artifact_sha256(output_dir)
    if set(actual) != set(expected):
        raise FactorLabError(
            "%s model artifact inventory differs from its manifest" % model_name
        )
    modified = [
        name
        for name in sorted(actual)
        if not _is_sha256(expected.get(name))
        or actual[name].lower() != str(expected[name]).lower()
    ]
    if modified:
        raise FactorLabError(
            "%s model artifact SHA-256 mismatch (%s)"
            % (model_name, ", ".join(modified))
        )


def _comparison_record(model_name: str, output_dir: Path) -> Dict[str, Any]:
    prediction = pd.read_csv(output_dir / "prediction_summary.csv")
    overall = prediction.loc[
        prediction["scope"].astype(str).str.upper() == "OVERALL"
    ]
    if len(overall) != 1:
        raise FactorLabError("%s report has no unique OVERALL row" % model_name)
    metrics = pd.read_csv(output_dir / "portfolio_metrics.csv")
    if not {"metric", "value"}.issubset(metrics.columns):
        raise FactorLabError("%s portfolio metrics are malformed" % model_name)
    record: Dict[str, Any] = {
        "model_name": model_name,
        "run_id": output_dir.name,
    }
    record.update(
        {
            name: value
            for name, value in overall.iloc[0].items()
            if name not in {"scope", "period"}
        }
    )
    record.update(dict(zip(metrics["metric"], metrics["value"])))
    return record


def command_compare_models(config: ResearchConfig, run: RunManifest) -> None:
    """Compare latest completed Phase-2 runs without selecting a winner."""

    model_names = ("factor_score", "ridge")
    outputs = {name: _latest_model_output(config, name) for name in model_names}
    manifests = {
        name: json.loads(
            (config.paths.runs_dir / path.name / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        for name, path in outputs.items()
    }
    current_provenance = _comparison_provenance(
        run.payload, "Current compare-models run"
    )
    for name, payload in manifests.items():
        source_provenance = _comparison_provenance(
            payload, "%s source run" % name
        )
        provenance_mismatches = [
            field
            for field in PROVENANCE_FIELDS
            if source_provenance[field] != current_provenance[field]
        ]
        if provenance_mismatches:
            raise FactorLabError(
                "%s source run provenance differs from the current environment (%s)"
                % (name, ", ".join(provenance_mismatches))
            )
        _verify_model_artifacts(name, outputs[name], payload)
    current_config = config.to_dict()
    if any(payload.get("config") != current_config for payload in manifests.values()):
        raise FactorLabError(
            "Model reports were not produced from the current identical config"
        )
    dataset_versions = {
        payload.get("dataset_sha256") for payload in manifests.values()
    }
    universe_versions = {
        payload.get("universe_version") for payload in manifests.values()
    }
    if (
        len(dataset_versions) != 1
        or not _is_sha256(next(iter(dataset_versions), None))
    ):
        raise FactorLabError("Model reports use different or unknown dataset versions")
    if (
        len(universe_versions) != 1
        or not _is_sha256(next(iter(universe_versions), None))
    ):
        raise FactorLabError("Model reports use different or unknown PIT universe versions")
    backtest_stock_versions = {
        payload.get("backtest_stock_bars_sha256") for payload in manifests.values()
    }
    backtest_benchmark_versions = {
        payload.get("backtest_benchmark_sha256") for payload in manifests.values()
    }
    if (
        len(backtest_stock_versions) != 1
        or not _is_sha256(next(iter(backtest_stock_versions), None))
    ):
        raise FactorLabError(
            "Model reports use different or unknown backtest stock-bar inputs"
        )
    if (
        len(backtest_benchmark_versions) != 1
        or not _is_sha256(next(iter(backtest_benchmark_versions), None))
    ):
        raise FactorLabError(
            "Model reports use different or unknown backtest benchmark inputs"
        )
    oos_keys = {
        name: _prediction_oos_keys(
            name,
            outputs[name],
            manifests[name],
            _target_column(config),
        )
        for name in model_names
    }
    if not oos_keys[model_names[0]].equals(oos_keys[model_names[1]]):
        raise FactorLabError(
            "Model reports do not use identical out-of-sample keys, label "
            "windows, and realised targets"
        )
    comparison = pd.DataFrame(
        [_comparison_record(name, outputs[name]) for name in model_names]
    )
    comparison_dir = config.paths.report_dir / run.run_id
    summary_path = write_model_comparison_report(comparison, comparison_dir)
    folds = []
    for name, path in outputs.items():
        table = pd.read_csv(path / "walk_forward_results.csv")
        table.insert(0, "source_run_id", path.name)
        if "model_name" not in table:
            table.insert(1, "model_name", name)
        folds.append(table)
    combined_folds = pd.concat(folds, ignore_index=True, sort=False)
    fold_path = comparison_dir / "walk_forward_results.csv"
    _atomic_csv(combined_folds, fold_path)
    run.payload["compared_models"] = list(model_names)
    run.payload["source_model_runs"] = {
        name: path.name for name, path in outputs.items()
    }
    run.payload["source_predictions_sha256"] = {
        name: manifests[name]["predictions_sha256"] for name in model_names
    }
    run.payload["source_model_artifact_sha256"] = {
        name: manifests[name]["model_artifact_sha256"] for name in model_names
    }
    run.payload["dataset_sha256"] = next(iter(dataset_versions))
    run.payload["universe_version"] = next(iter(universe_versions))
    run.payload["backtest_stock_bars_sha256"] = next(
        iter(backtest_stock_versions)
    )
    run.payload["backtest_benchmark_sha256"] = next(
        iter(backtest_benchmark_versions)
    )
    run.payload["comparison_artifact_sha256"] = _artifact_sha256(comparison_dir)
    run.add_output(
        "model_comparison", comparison_dir / "model_comparison.csv"
    )
    run.add_output("walk_forward_results", fold_path)
    run.add_output("summary", summary_path)
    LOGGER.info("Compared FactorScore and Ridge without automatic model selection")


def main(argv: Optional[List[str]] = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, arguments.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        config = load_config(arguments.config)
    except FactorLabError as exc:
        LOGGER.error("%s", exc)
        return 2
    try:
        set_random_seed(config.seed)
        run = RunManifest(config, arguments.command, vars(arguments))
    except Exception as exc:
        LOGGER.error(
            "Cannot initialise reproducible run manifest: %s: %s",
            type(exc).__name__,
            exc,
        )
        return 2
    LOGGER.info("Run ID: %s", run.run_id)
    try:
        if arguments.command == "audit":
            command_audit(config, run)
        elif arguments.command == "download-data":
            command_download(config, run)
        elif arguments.command == "import-universe":
            command_import_universe(config, run, arguments.input_path)
        elif arguments.command == "build-dataset":
            command_build_dataset(config, run)
        elif arguments.command == "evaluate-factors":
            command_evaluate(config, run)
        elif arguments.command == "walk-forward":
            command_walk_forward(config, run, arguments.model)
        elif arguments.command == "compare-models":
            command_compare_models(config, run)
        else:  # argparse prevents this branch
            raise FactorLabError("Unsupported command %s" % arguments.command)
    except (FactorLabError, OSError, ValueError) as exc:
        try:
            run.finish("failed", str(exc))
        except Exception as manifest_exc:
            LOGGER.error(
                "Cannot finalise failed run manifest (original error: %s): %s: %s",
                exc,
                type(manifest_exc).__name__,
                manifest_exc,
            )
        LOGGER.error("%s", exc)
        return 1
    except Exception as exc:
        try:
            run.finish("failed", "%s: %s" % (type(exc).__name__, exc))
        except Exception as manifest_exc:
            LOGGER.error(
                "Cannot finalise failed run manifest (original error: %s: %s): %s: %s",
                type(exc).__name__,
                exc,
                type(manifest_exc).__name__,
                manifest_exc,
            )
        LOGGER.exception("Unexpected failure")
        return 1
    try:
        run.finish("success")
    except Exception as exc:
        LOGGER.error(
            "Command completed but the success manifest could not be finalised: %s: %s",
            type(exc).__name__,
            exc,
        )
        return 1
    LOGGER.info("Manifest: %s", run.path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
