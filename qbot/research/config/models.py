"""Typed configuration model for reproducible FactorLab experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
import math
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from qbot.research.errors import ConfigurationError, PointInTimeUniverseRequiredError


@dataclass(frozen=True)
class ProjectConfig:
    name: str = "qbot-factorlab"


@dataclass(frozen=True)
class PathsConfig:
    """Artifact roots, resolved against the repository root by the loader."""

    data_root: Path = Path("data/research")
    results_root: Path = Path("results")

    @property
    def raw_dir(self) -> Path:
        return self.data_root / "raw"

    @property
    def benchmark_dir(self) -> Path:
        return self.data_root / "benchmark"

    @property
    def universe_dir(self) -> Path:
        return self.data_root / "universe"

    @property
    def processed_dir(self) -> Path:
        return self.data_root / "processed"

    @property
    def features_dir(self) -> Path:
        return self.data_root / "features"

    @property
    def factor_results_dir(self) -> Path:
        return self.results_root / "factors"

    @property
    def runs_dir(self) -> Path:
        return self.results_root / "runs"

    @property
    def model_results_dir(self) -> Path:
        return self.results_root / "models"

    @property
    def report_dir(self) -> Path:
        return self.results_root / "report"


@dataclass(frozen=True)
class DataConfig:
    start: date
    end: date
    provider: str = "akshare"
    benchmark: str = "000905.SH"
    adjustment: str = "hfq"
    calendar_source: str = "benchmark"
    warmup_trading_days: int = 130


@dataclass(frozen=True)
class UniverseConfig:
    name: str = "CSI500"
    index_symbol: str = "000905.SH"
    provider: str = "baostock"
    point_in_time: bool = True
    expected_member_count: int = 500
    min_listed_days: int = 120
    exclude_st: bool = True
    exclude_suspended: bool = True
    zero_volume_window_days: int = 20
    data_quality_window_days: int = 60
    min_valid_ohlcv_ratio: float = 0.8


@dataclass(frozen=True)
class CacheConfig:
    format: str = "parquet"
    per_symbol: bool = True
    skip_existing: bool = True
    atomic_writes: bool = True


@dataclass(frozen=True)
class NetworkConfig:
    max_retries: int = 3
    backoff_seconds: Tuple[float, ...] = (1.0, 2.0, 4.0)
    request_interval_seconds: float = 0.25
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class LabelConfig:
    holding_days: int = 5
    entry_price: str = "next_open"
    target: str = "excess_return"


@dataclass(frozen=True)
class PreprocessingConfig:
    winsorization: str = "mad"
    mad_multiplier: float = 5.0
    zscore_ddof: int = 0


@dataclass(frozen=True)
class EvaluationConfig:
    quantiles: int = 5
    min_cross_section: int = 20


@dataclass(frozen=True)
class FactorScoreConfig:
    """Fixed, interpretable baseline weights for enabled factors."""

    weights: Dict[str, float] = field(default_factory=dict)
    normalize_by_absolute_weight: bool = True


@dataclass(frozen=True)
class RidgeConfig:
    """Small validation-only candidate set for the Ridge baseline."""

    alphas: Tuple[float, ...] = (0.1, 1.0, 10.0, 100.0)
    fit_intercept: bool = True
    max_iter: int = 10000
    tolerance: float = 0.0001


@dataclass(frozen=True)
class ModelsConfig:
    factor_score: FactorScoreConfig = field(default_factory=FactorScoreConfig)
    ridge: RidgeConfig = field(default_factory=RidgeConfig)


@dataclass(frozen=True)
class ValidationConfig:
    initial_train_months: int = 24
    validation_months: int = 3
    test_months: int = 3
    step_months: int = 3
    purge_days: int = 5
    embargo_days: int = 5


@dataclass(frozen=True)
class PortfolioConfig:
    top_k: int = 20
    rebalance_days: int = 5
    weighting: str = "equal"


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 1_000_000.0
    board_lot: int = 100
    annualization_days: int = 252
    risk_free_rate: float = 0.0


@dataclass(frozen=True)
class StampDutyPeriod:
    start: date
    end: Optional[date]
    sell_bps: float


def _default_stamp_duty() -> Tuple[StampDutyPeriod, ...]:
    return (
        StampDutyPeriod(date(1900, 1, 1), date(2023, 8, 27), 10.0),
        StampDutyPeriod(date(2023, 8, 28), None, 5.0),
    )


@dataclass(frozen=True)
class FeesConfig:
    commission_bps: float = 3.0
    minimum_commission_cny: float = 5.0
    slippage_bps: float = 5.0
    transfer_fee_bps: float = 0.0
    buy_fee_bps: float = 0.0
    sell_fee_bps: float = 0.0
    stamp_duty: Tuple[StampDutyPeriod, ...] = field(
        default_factory=_default_stamp_duty
    )


@dataclass(frozen=True)
class ResearchConfig:
    project: ProjectConfig
    data: DataConfig
    universe: UniverseConfig
    factors: Tuple[str, ...]
    seed: int = 42
    live_trading: bool = False
    paths: PathsConfig = field(default_factory=PathsConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    label: LabelConfig = field(default_factory=LabelConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    portfolio: PortfolioConfig = field(default_factory=PortfolioConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    fees: FeesConfig = field(default_factory=FeesConfig)
    config_path: Optional[Path] = field(default=None, init=False, repr=False)
    repo_root: Optional[Path] = field(default=None, init=False, repr=False)

    @property
    def random_seed(self) -> int:
        """Explicit alias used by experiment-manifest code."""

        return self.seed

    def validate(self) -> None:
        """Enforce correctness constraints before any network or disk work."""

        if not self.project.name.strip():
            raise ConfigurationError("project.name must not be empty")
        if self.live_trading:
            raise ConfigurationError(
                "FactorLab is research-only; live_trading must be false"
            )
        if self.seed < 0:
            raise ConfigurationError("seed must be non-negative")
        if self.data.start > self.data.end:
            raise ConfigurationError("data.start must be on or before data.end")
        if self.data.adjustment not in {"hfq", "qfq"}:
            raise ConfigurationError("data.adjustment must be hfq or qfq")
        if self.data.calendar_source != "benchmark":
            raise ConfigurationError(
                "data.calendar_source must be benchmark in FactorLab Phase 1"
            )
        benchmark_symbol = str(self.data.benchmark).strip().upper()
        universe_symbol = str(self.universe.index_symbol).strip().upper()
        if benchmark_symbol != "000905.SH" or universe_symbol != "000905.SH":
            raise ConfigurationError(
                "FactorLab CSI500 research requires data.benchmark and "
                "universe.index_symbol to both be canonical 000905.SH"
            )
        if self.data.warmup_trading_days < 0:
            raise ConfigurationError("data.warmup_trading_days must be non-negative")
        if self.data.warmup_trading_days < max(
            self.universe.min_listed_days,
            self.universe.data_quality_window_days,
        ):
            raise ConfigurationError(
                "data.warmup_trading_days must cover universe listing/data-quality windows"
            )
        if not self.universe.point_in_time:
            raise PointInTimeUniverseRequiredError(
                "universe.point_in_time must be true"
            )
        if self.universe.provider.lower() not in {"baostock", "local"}:
            raise ConfigurationError(
                "universe.provider must be baostock or local in FactorLab Phase 1"
            )
        if self.universe.expected_member_count <= 0:
            raise ConfigurationError("universe.expected_member_count must be positive")
        if self.universe.min_listed_days < 0:
            raise ConfigurationError("universe.min_listed_days must be non-negative")
        if self.universe.zero_volume_window_days <= 0:
            raise ConfigurationError(
                "universe.zero_volume_window_days must be positive"
            )
        if self.universe.data_quality_window_days <= 0:
            raise ConfigurationError(
                "universe.data_quality_window_days must be positive"
            )
        if not 0.0 < self.universe.min_valid_ohlcv_ratio <= 1.0:
            raise ConfigurationError(
                "universe.min_valid_ohlcv_ratio must be in (0, 1]"
            )
        if self.cache.format != "parquet":
            raise ConfigurationError("cache.format must be parquet")
        if self.network.max_retries < 1:
            raise ConfigurationError("network.max_retries must be at least 1")
        if len(self.network.backoff_seconds) < self.network.max_retries:
            raise ConfigurationError(
                "network.backoff_seconds must contain at least max_retries values"
            )
        if any(value < 0 for value in self.network.backoff_seconds):
            raise ConfigurationError("network.backoff_seconds cannot be negative")
        if self.network.request_interval_seconds < 0:
            raise ConfigurationError(
                "network.request_interval_seconds cannot be negative"
            )
        if self.network.timeout_seconds <= 0:
            raise ConfigurationError("network.timeout_seconds must be positive")
        if self.label.holding_days <= 0:
            raise ConfigurationError("label.holding_days must be positive")
        if self.label.entry_price != "next_open":
            raise ConfigurationError(
                "label.entry_price must be next_open to preserve signal timing"
            )
        if self.label.target != "excess_return":
            raise ConfigurationError("label.target must be excess_return")
        if self.preprocessing.winsorization != "mad":
            raise ConfigurationError(
                "preprocessing.winsorization must be mad in FactorLab Phase 1"
            )
        if self.preprocessing.mad_multiplier <= 0:
            raise ConfigurationError(
                "preprocessing.mad_multiplier must be positive"
            )
        if self.preprocessing.zscore_ddof != 0:
            raise ConfigurationError(
                "preprocessing.zscore_ddof must be 0 in FactorLab Phase 1"
            )
        if self.evaluation.quantiles < 2:
            raise ConfigurationError("evaluation.quantiles must be at least 2")
        if self.evaluation.min_cross_section < self.evaluation.quantiles:
            raise ConfigurationError(
                "evaluation.min_cross_section must be at least evaluation.quantiles"
            )
        if not self.factors:
            raise ConfigurationError("factors must contain at least one factor")
        if len(set(self.factors)) != len(self.factors):
            raise ConfigurationError("factors must not contain duplicates")
        if any(not factor.strip() for factor in self.factors):
            raise ConfigurationError("factor names must not be empty")
        # Import lazily so the typed configuration layer remains cheap to
        # import while still making an unknown YAML factor a fail-fast error.
        from qbot.research.factors.registry import FACTOR_REGISTRY

        unknown_factors = sorted(set(self.factors).difference(FACTOR_REGISTRY))
        if unknown_factors:
            raise ConfigurationError(
                "factors contain unregistered names: %s; available factors: %s"
                % (
                    ", ".join(unknown_factors),
                    ", ".join(sorted(FACTOR_REGISTRY)),
                )
            )
        weights = self.models.factor_score.weights
        if weights:
            if set(weights) != set(self.factors):
                raise ConfigurationError(
                    "models.factor_score.weights must match the enabled factor list"
                )
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in weights.values()
            ):
                raise ConfigurationError(
                    "models.factor_score.weights must contain finite numbers"
                )
            if not any(float(value) != 0.0 for value in weights.values()):
                raise ConfigurationError(
                    "models.factor_score.weights must not all be zero"
                )
        ridge = self.models.ridge
        if not ridge.alphas or any(
            not math.isfinite(value) or value <= 0 for value in ridge.alphas
        ):
            raise ConfigurationError("models.ridge.alphas must be finite and positive")
        if ridge.max_iter <= 0:
            raise ConfigurationError("models.ridge.max_iter must be positive")
        if not math.isfinite(ridge.tolerance) or ridge.tolerance <= 0:
            raise ConfigurationError("models.ridge.tolerance must be positive")
        validation_values = {
            "initial_train_months": self.validation.initial_train_months,
            "validation_months": self.validation.validation_months,
            "test_months": self.validation.test_months,
            "step_months": self.validation.step_months,
        }
        for name, value in validation_values.items():
            if value <= 0:
                raise ConfigurationError("validation.%s must be positive" % name)
        if self.validation.step_months < self.validation.test_months:
            raise ConfigurationError(
                "validation.step_months must be at least validation.test_months "
                "to prevent overlapping test windows"
            )
        if self.validation.purge_days < self.label.holding_days:
            raise ConfigurationError(
                "validation.purge_days must be at least label.holding_days"
            )
        if self.validation.embargo_days < 0:
            raise ConfigurationError("validation.embargo_days must be non-negative")
        if self.portfolio.top_k <= 0:
            raise ConfigurationError("portfolio.top_k must be positive")
        if self.portfolio.rebalance_days <= 0:
            raise ConfigurationError("portfolio.rebalance_days must be positive")
        if self.portfolio.weighting != "equal":
            raise ConfigurationError(
                "portfolio.weighting must be equal in FactorLab Phase 2"
            )
        if not math.isfinite(self.backtest.initial_cash) or self.backtest.initial_cash <= 0:
            raise ConfigurationError("backtest.initial_cash must be positive")
        if self.backtest.board_lot <= 0:
            raise ConfigurationError("backtest.board_lot must be positive")
        if self.backtest.annualization_days <= 0:
            raise ConfigurationError("backtest.annualization_days must be positive")
        if not math.isfinite(self.backtest.risk_free_rate):
            raise ConfigurationError("backtest.risk_free_rate must be finite")
        fee_values = {
            "commission_bps": self.fees.commission_bps,
            "minimum_commission_cny": self.fees.minimum_commission_cny,
            "slippage_bps": self.fees.slippage_bps,
            "transfer_fee_bps": self.fees.transfer_fee_bps,
            "buy_fee_bps": self.fees.buy_fee_bps,
            "sell_fee_bps": self.fees.sell_fee_bps,
        }
        if any(not math.isfinite(value) or value < 0 for value in fee_values.values()):
            raise ConfigurationError("fees values must be finite and non-negative")
        periods = self.fees.stamp_duty
        if not periods:
            raise ConfigurationError("fees.stamp_duty must not be empty")
        if tuple(sorted(periods, key=lambda period: period.start)) != periods:
            raise ConfigurationError("fees.stamp_duty must be sorted by start date")
        for number, period in enumerate(periods):
            if not math.isfinite(period.sell_bps) or period.sell_bps < 0:
                raise ConfigurationError(
                    "fees.stamp_duty sell_bps must be finite and non-negative"
                )
            if period.end is not None and period.end < period.start:
                raise ConfigurationError(
                    "fees.stamp_duty end must be on or after start"
                )
            if period.end is None and number != len(periods) - 1:
                raise ConfigurationError(
                    "only the final fees.stamp_duty period may have a null end"
                )
            if number:
                previous = periods[number - 1]
                if previous.end is None or period.start != previous.end + timedelta(days=1):
                    raise ConfigurationError(
                        "fees.stamp_duty periods must be contiguous and non-overlapping"
                    )
        if periods[0].start > self.data.start:
            raise ConfigurationError("fees.stamp_duty does not cover data.start")
        final_end = periods[-1].end
        if final_end is not None and final_end < self.data.end:
            raise ConfigurationError("fees.stamp_duty does not cover data.end")

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable snapshot suitable for run manifests."""

        value = asdict(self)
        value.pop("config_path", None)
        value.pop("repo_root", None)
        return _serialize(value)


def _serialize(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value


__all__ = [
    "CacheConfig",
    "DataConfig",
    "EvaluationConfig",
    "BacktestConfig",
    "FactorScoreConfig",
    "FeesConfig",
    "LabelConfig",
    "ModelsConfig",
    "NetworkConfig",
    "PathsConfig",
    "PortfolioConfig",
    "PreprocessingConfig",
    "ProjectConfig",
    "ResearchConfig",
    "RidgeConfig",
    "StampDutyPeriod",
    "UniverseConfig",
    "ValidationConfig",
]
