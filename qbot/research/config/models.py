"""Typed configuration model for reproducible FactorLab experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
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
                "FactorLab Phase 1 is research-only; live_trading must be false"
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
    "LabelConfig",
    "NetworkConfig",
    "PathsConfig",
    "PreprocessingConfig",
    "ProjectConfig",
    "ResearchConfig",
    "UniverseConfig",
]
