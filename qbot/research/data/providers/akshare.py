"""AKShare-backed implementation of the FactorLab market-data interface."""

import importlib
import logging
import time
from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

try:
    from qbot.research.errors import ProviderError
except ImportError:  # pragma: no cover - isolated bootstrapping only
    class ProviderError(RuntimeError):
        """Fallback used only when the package foundation is unavailable."""

from qbot.research.data.providers.base import DateLike, MarketDataProvider
from qbot.research.data.schema import (
    canonicalize_bars,
    normalize_symbol,
    vendor_code,
)


LOGGER = logging.getLogger(__name__)

_COLUMN_ALIASES: Dict[str, Tuple[str, ...]] = {
    "date": ("date", "日期", "交易日期"),
    "open": ("open", "开盘"),
    "high": ("high", "最高"),
    "low": ("low", "最低"),
    "close": ("close", "收盘"),
    "volume": ("volume", "成交量"),
    "amount": ("amount", "成交额"),
    "turnover": ("turnover", "换手率"),
}


def _timestamp(value: DateLike, label: str) -> pd.Timestamp:
    try:
        result = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ProviderError("invalid %s date: %r" % (label, value)) from exc
    if result.tzinfo is not None:
        result = result.tz_localize(None)
    return result.normalize()


def _format_api_date(value: pd.Timestamp) -> str:
    return value.strftime("%Y%m%d")


def _find_column(frame: pd.DataFrame, logical_name: str) -> Optional[str]:
    for candidate in _COLUMN_ALIASES[logical_name]:
        if candidate in frame.columns:
            return candidate
    return None


def _extract_series(
    frame: pd.DataFrame,
    logical_name: str,
    required: bool = True,
) -> pd.Series:
    column = _find_column(frame, logical_name)
    if column is None:
        if required:
            raise ProviderError(
                "AKShare response is missing %s (columns=%s)"
                % (logical_name, list(frame.columns))
            )
        return pd.Series(np.nan, index=frame.index, dtype="float64")
    return frame[column]


class AKShareProvider(MarketDataProvider):
    """Fetch raw and adjusted A-share bars through AKShare.

    Imports AKShare lazily so importing ``qbot.research`` never requires the
    optional network dependency.  Tests and offline callers may inject a small
    AKShare-compatible object through ``akshare_module``.
    """

    def __init__(
        self,
        benchmark_symbol: str = "000905.SH",
        adjustment: str = "hfq",
        retry_count: int = 3,
        backoff_seconds: Sequence[float] = (1.0, 2.0, 4.0),
        request_interval: float = 0.25,
        akshare_module: Optional[Any] = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        if adjustment not in {"hfq", "qfq"}:
            raise ProviderError("adjustment must be 'hfq' or 'qfq'")
        if retry_count < 0:
            raise ProviderError("retry_count must be non-negative")
        if request_interval < 0:
            raise ProviderError("request_interval must be non-negative")
        if not backoff_seconds:
            raise ProviderError("backoff_seconds must contain at least one value")
        if any(float(item) < 0 for item in backoff_seconds):
            raise ProviderError("backoff_seconds values must be non-negative")

        self.benchmark_symbol = normalize_symbol(benchmark_symbol)
        self.adjustment = adjustment
        self.retry_count = int(retry_count)
        self.backoff_seconds = tuple(float(item) for item in backoff_seconds)
        self.request_interval = float(request_interval)
        self._akshare = akshare_module
        self._sleep = sleep_fn
        self._monotonic = monotonic_fn
        self._last_request_at: Optional[float] = None

    @property
    def akshare(self) -> Any:
        if self._akshare is None:
            try:
                self._akshare = importlib.import_module("akshare")
            except ImportError as exc:
                raise ProviderError(
                    "AKShare is not installed; install dev/requirements-research.txt"
                ) from exc
        return self._akshare

    @property
    def source_version(self) -> str:
        return str(getattr(self.akshare, "__version__", "unknown"))

    def _throttle(self) -> None:
        now = self._monotonic()
        if self._last_request_at is not None:
            remaining = self.request_interval - (now - self._last_request_at)
            if remaining > 0:
                self._sleep(remaining)
                now = self._monotonic()
        self._last_request_at = now

    def _call(self, function: Callable[..., Any], **kwargs: Any) -> pd.DataFrame:
        last_error: Optional[BaseException] = None
        for attempt in range(self.retry_count + 1):
            self._throttle()
            try:
                result = function(**kwargs)
                if not isinstance(result, pd.DataFrame):
                    raise TypeError("provider returned %s" % type(result).__name__)
                return result
            except Exception as exc:  # vendor errors do not share one base class
                last_error = exc
                if attempt >= self.retry_count:
                    break
                delay = self.backoff_seconds[
                    min(attempt, len(self.backoff_seconds) - 1)
                ]
                LOGGER.warning(
                    "AKShare request failed (attempt %d/%d): %s; retrying in %.2fs",
                    attempt + 1,
                    self.retry_count + 1,
                    exc,
                    delay,
                )
                if delay:
                    self._sleep(delay)
        raise ProviderError("AKShare request failed after retries") from last_error

    @staticmethod
    def _date_range(start: DateLike, end: DateLike) -> Tuple[pd.Timestamp, pd.Timestamp]:
        start_ts = _timestamp(start, "start")
        end_ts = _timestamp(end, "end")
        if start_ts > end_ts:
            raise ProviderError("start date must be on or before end date")
        return start_ts, end_ts

    @staticmethod
    def _normalise_vendor_frame(
        frame: pd.DataFrame,
        start: pd.Timestamp,
        end: pd.Timestamp,
        require_turnover: bool,
    ) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(
                columns=["date", "open", "high", "low", "close", "volume", "amount", "turnover"]
            )
        result = pd.DataFrame(index=frame.index)
        result["date"] = pd.to_datetime(_extract_series(frame, "date"), errors="coerce")
        for field in ("open", "high", "low", "close", "volume"):
            result[field] = pd.to_numeric(
                _extract_series(frame, field), errors="coerce"
            )
        result["amount"] = pd.to_numeric(
            _extract_series(frame, "amount", required=False), errors="coerce"
        )
        result["turnover"] = pd.to_numeric(
            _extract_series(frame, "turnover", required=require_turnover),
            errors="coerce",
        )
        if result["date"].isna().any():
            raise ProviderError("AKShare response contains an invalid date")
        result["date"] = result["date"].dt.tz_localize(None).dt.normalize()
        result = result.loc[result["date"].between(start, end)].copy()
        if result["date"].duplicated().any():
            raise ProviderError("AKShare response contains duplicate dates")
        return result.sort_values("date", kind="mergesort").reset_index(drop=True)

    def get_daily_bars(
        self, symbol: str, start: DateLike, end: DateLike
    ) -> pd.DataFrame:
        canonical_symbol = normalize_symbol(symbol)
        start_ts, end_ts = self._date_range(start, end)
        kwargs = {
            "symbol": vendor_code(canonical_symbol),
            "period": "daily",
            "start_date": _format_api_date(start_ts),
            "end_date": _format_api_date(end_ts),
        }
        raw_vendor = self._call(
            self.akshare.stock_zh_a_hist, adjust="", **kwargs
        )
        adjusted_vendor = self._call(
            self.akshare.stock_zh_a_hist, adjust=self.adjustment, **kwargs
        )
        raw = self._normalise_vendor_frame(
            raw_vendor, start_ts, end_ts, require_turnover=True
        )
        adjusted = self._normalise_vendor_frame(
            adjusted_vendor, start_ts, end_ts, require_turnover=False
        )
        if raw.empty and adjusted.empty:
            from qbot.research.data.schema import empty_bars

            return empty_bars()
        raw_dates = pd.Index(raw["date"])
        adjusted_dates = pd.Index(adjusted["date"])
        if not raw_dates.equals(adjusted_dates):
            raise ProviderError(
                "raw and %s AKShare bars have different trading dates"
                % self.adjustment
            )

        result = pd.DataFrame(
            {
                "date": raw["date"],
                "symbol": canonical_symbol,
                "open": raw["open"],
                "high": raw["high"],
                "low": raw["low"],
                "close": raw["close"],
                # AKShare stock_zh_a_hist reports volume in hands.
                "volume": raw["volume"] * 100.0,
                "amount": raw["amount"],
                # AKShare reports turnover as percent; internal units are decimal.
                "turnover": raw["turnover"] / 100.0,
                "raw_open": raw["open"],
                "raw_high": raw["high"],
                "raw_low": raw["low"],
                "raw_close": raw["close"],
                "adj_open": adjusted["open"],
                "adj_high": adjusted["high"],
                "adj_low": adjusted["low"],
                "adj_close": adjusted["close"],
            }
        )
        result["adj_factor"] = result["adj_close"] / result["raw_close"].replace(
            0.0, np.nan
        )
        return canonicalize_bars(result, symbol=canonical_symbol)

    def get_index_bars(
        self, symbol: str, start: DateLike, end: DateLike
    ) -> pd.DataFrame:
        canonical_symbol = normalize_symbol(symbol)
        start_ts, end_ts = self._date_range(start, end)
        code = vendor_code(canonical_symbol)

        volume_multiplier = 100.0
        if hasattr(self.akshare, "index_zh_a_hist"):
            vendor_frame = self._call(
                self.akshare.index_zh_a_hist,
                symbol=code,
                period="daily",
                start_date=_format_api_date(start_ts),
                end_date=_format_api_date(end_ts),
            )
        elif hasattr(self.akshare, "stock_zh_index_daily"):
            exchange = canonical_symbol.split(".", 1)[1].lower()
            vendor_frame = self._call(
                self.akshare.stock_zh_index_daily,
                symbol="%s%s" % (exchange, code),
            )
            # The Sina fallback reports index volume in shares, whereas the
            # Eastmoney primary reports hands.
            volume_multiplier = 1.0
        else:
            raise ProviderError("AKShare has no supported mainland index endpoint")

        normalised = self._normalise_vendor_frame(
            vendor_frame, start_ts, end_ts, require_turnover=False
        )
        if normalised.empty:
            from qbot.research.data.schema import empty_bars

            return empty_bars()
        result = pd.DataFrame(
            {
                "date": normalised["date"],
                "symbol": canonical_symbol,
                "open": normalised["open"],
                "high": normalised["high"],
                "low": normalised["low"],
                "close": normalised["close"],
                "volume": normalised["volume"] * volume_multiplier,
                "amount": normalised["amount"],
                "turnover": normalised["turnover"],
            }
        )
        for field in ("open", "high", "low", "close"):
            result["raw_%s" % field] = result[field]
            result["adj_%s" % field] = result[field]
        result["adj_factor"] = 1.0
        return canonicalize_bars(
            result, symbol=canonical_symbol, allow_missing_ohlc=False
        )

    def get_trade_calendar(
        self, start: DateLike, end: DateLike
    ) -> pd.DatetimeIndex:
        bars = self.get_index_bars(self.benchmark_symbol, start, end)
        if bars.empty:
            raise ProviderError(
                "benchmark returned no dates; a trading calendar cannot be built"
            )
        return pd.DatetimeIndex(bars["date"].drop_duplicates().sort_values(), name="date")

    def get_index_constituents(
        self, symbol: str, as_of: Optional[DateLike] = None
    ) -> pd.DataFrame:
        if as_of is not None:
            raise ProviderError(
                "AKShare exposes only a current constituent snapshot; "
                "POINT-IN-TIME UNIVERSE REQUIRED for historical dates"
            )
        canonical_index = normalize_symbol(symbol)
        if not hasattr(self.akshare, "index_stock_cons"):
            raise ProviderError("AKShare has no supported constituent endpoint")
        vendor_frame = self._call(
            self.akshare.index_stock_cons, symbol=vendor_code(canonical_index)
        )
        symbol_column = next(
            (
                candidate
                for candidate in ("品种代码", "成分券代码", "股票代码", "代码", "symbol")
                if candidate in vendor_frame.columns
            ),
            None,
        )
        if symbol_column is None:
            raise ProviderError("AKShare constituent response has no symbol column")
        output = pd.DataFrame(
            {
                "index_symbol": canonical_index,
                "symbol": vendor_frame[symbol_column].map(normalize_symbol),
                "is_current_snapshot": True,
            }
        )
        return output.drop_duplicates("symbol").sort_values("symbol").reset_index(
            drop=True
        )


__all__ = ["AKShareProvider"]
