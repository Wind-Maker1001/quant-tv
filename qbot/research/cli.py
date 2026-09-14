"""Command-line interface for the isolated FactorLab Phase-1 pipeline."""

import argparse
import json
import logging
import os
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from qbot.research.config import ResearchConfig, load_config
from qbot.research.data import AKShareProvider, ParquetBarCache, TradingCalendar
from qbot.research.dataset import DatasetBuildOptions, DatasetBuilder
from qbot.research.errors import FactorLabError, PointInTimeUniverseRequiredError
from qbot.research.metrics import evaluate_factors
from qbot.research.reports import write_factor_report
from qbot.research.reproducibility import RunManifest, set_random_seed
from qbot.research.universe.csi500 import (
    BaoStockPointInTimeProvider,
    collect_point_in_time_universe,
    dataframe_sha256,
    import_point_in_time_universe,
    validate_daily_membership,
)
from qbot.research.universe.filters import UniverseFilterConfig


LOGGER = logging.getLogger("qbot.research")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m qbot.research.cli",
        description="Qbot FactorLab Phase-1 research pipeline (NO LIVE MONEY)",
    )
    parser.add_argument("--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("audit", "download-data", "build-dataset", "evaluate-factors"):
        command = subparsers.add_parser(name)
        command.add_argument("--config", required=True)
    importer = subparsers.add_parser("import-universe")
    importer.add_argument("--config", required=True)
    importer.add_argument("--input", required=True, dest="input_path")
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
    except (OSError, ValueError) as exc:
        raise PointInTimeUniverseRequiredError("universe manifest is unreadable") from exc
    if manifest.get("sha256") != dataframe_sha256(membership):
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
        if existing_manifest.get("source") == "local-import":
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
    run.add_output("dataset", destination)
    run.payload["dataset_rows"] = int(len(dataset))
    run.payload["dataset_dates"] = int(dataset["date"].nunique())
    LOGGER.info("Dataset written: %d rows across %d dates", len(dataset), dataset["date"].nunique())


def command_evaluate(config: ResearchConfig, run: RunManifest) -> None:
    dataset_path = config.paths.processed_dir / "dataset.parquet"
    if not dataset_path.exists():
        raise FactorLabError("Dataset is missing; run build-dataset first")
    dataset = pd.read_parquet(dataset_path)
    target = "EXCESS_RET%d" % config.label.holding_days
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
    set_random_seed(config.seed)
    run = RunManifest(config, arguments.command, vars(arguments))
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
        else:  # argparse prevents this branch
            raise FactorLabError("Unsupported command %s" % arguments.command)
    except (FactorLabError, OSError, ValueError) as exc:
        run.finish("failed", str(exc))
        LOGGER.error("%s", exc)
        return 1
    except Exception as exc:
        run.finish("failed", "%s: %s" % (type(exc).__name__, exc))
        LOGGER.exception("Unexpected failure")
        return 1
    run.finish("success")
    LOGGER.info("Manifest: %s", run.path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
