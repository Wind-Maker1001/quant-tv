"""CSI500 point-in-time membership backed by BaoStock or local files.

Current constituents are deliberately never used as a historical fallback.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
from numbers import Real
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from qbot.research.errors import PointInTimeUniverseError, ProviderError

from .base import PointInTimeUniverse, PointInTimeUniverseProvider

LOGGER = logging.getLogger(__name__)
CANONICAL_SYMBOL = re.compile(r"^(?:60|68|00|30|83|87|43)\d{4}\.(?:SH|SZ|BJ)$")
PIT_REQUIRED = "POINT-IN-TIME UNIVERSE REQUIRED"
_BAOSTOCK_PIT_SOURCE_VERSION = "baostock-query_zz500_stocks-daily-v1"


def canonical_symbol(value: Any) -> str:
    """Convert BaoStock/Chinese exchange symbols to the project convention."""

    raw = str(value).strip().upper()
    if CANONICAL_SYMBOL.match(raw):
        return raw
    if raw.startswith(("SH.", "SZ.", "BJ.")):
        exchange, code = raw.split(".", 1)
        result = "%s.%s" % (code, exchange)
    elif raw.endswith((".SH", ".SZ", ".BJ")):
        result = raw
    elif raw.isdigit() and len(raw) == 6:
        if raw.startswith(("6", "9")):
            exchange = "SH"
        elif raw.startswith(("4", "8")):
            exchange = "BJ"
        else:
            exchange = "SZ"
        result = "%s.%s" % (raw, exchange)
    else:
        raise PointInTimeUniverseError(
            "%s: invalid constituent symbol %r" % (PIT_REQUIRED, value)
        )
    if not CANONICAL_SYMBOL.match(result):
        raise PointInTimeUniverseError(
            "%s: invalid canonical symbol %r" % (PIT_REQUIRED, result)
        )
    return result


def _normalise_dates(values: Iterable[Any]) -> pd.DatetimeIndex:
    dates = pd.to_datetime(list(values), errors="raise")
    if getattr(dates, "tz", None) is not None:
        dates = dates.tz_localize(None)
    return pd.DatetimeIndex(dates).normalize()


def _membership_flag(value: Any) -> bool:
    """Parse an explicit membership flag without truthiness coercion.

    In particular, ``bool("false")`` and ``bool("0")`` are both true in
    Python.  Accepting those values silently would add non-members to a PIT
    universe, so imported flags are restricted to unambiguous encodings.
    """

    if value is True or value is False:
        return bool(value)
    if pd.isna(value):
        raise PointInTimeUniverseError(
            "%s: is_member must not be null" % PIT_REQUIRED
        )
    if isinstance(value, Real) and float(value) in {0.0, 1.0}:
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1"}:
        return True
    if text in {"false", "0"}:
        return False
    raise PointInTimeUniverseError(
        "%s: invalid is_member value %r" % (PIT_REQUIRED, value)
    )


def validate_daily_membership(
    frame: pd.DataFrame,
    requested_dates: Optional[Iterable[Any]] = None,
    expected_member_count: Optional[int] = 500,
) -> pd.DataFrame:
    """Validate exact daily PIT snapshots and return a canonical copy."""

    required = {"date", "symbol"}
    missing = required.difference(frame.columns)
    if missing:
        raise PointInTimeUniverseError(
            "%s: missing columns %s" % (PIT_REQUIRED, sorted(missing))
        )
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"], errors="raise").dt.tz_localize(None).dt.normalize()
    result["symbol"] = result["symbol"].map(canonical_symbol)
    if "is_member" not in result:
        result["is_member"] = True
    result["is_member"] = result["is_member"].map(_membership_flag).astype(bool)
    result = result.loc[result["is_member"], ["date", "symbol", "is_member"]]
    if result.duplicated(["date", "symbol"]).any():
        dupes = result.loc[result.duplicated(["date", "symbol"], keep=False), ["date", "symbol"]]
        raise PointInTimeUniverseError(
            "%s: duplicate memberships: %s" % (PIT_REQUIRED, dupes.head().to_dict("records"))
        )
    if requested_dates is not None:
        expected_dates = _normalise_dates(requested_dates).unique().sort_values()
        actual_dates = pd.DatetimeIndex(result["date"].unique()).sort_values()
        missing_dates = expected_dates.difference(actual_dates)
        extra_dates = actual_dates.difference(expected_dates)
        if len(missing_dates) or len(extra_dates):
            raise PointInTimeUniverseError(
                "%s: snapshot coverage mismatch; missing=%s extra=%s"
                % (
                    PIT_REQUIRED,
                    [d.strftime("%Y-%m-%d") for d in missing_dates[:10]],
                    [d.strftime("%Y-%m-%d") for d in extra_dates[:10]],
                )
            )
    if expected_member_count is not None:
        counts = result.groupby("date", sort=True)["symbol"].nunique()
        invalid = counts[counts != int(expected_member_count)]
        if not invalid.empty:
            details = {d.strftime("%Y-%m-%d"): int(v) for d, v in invalid.head(10).items()}
            raise PointInTimeUniverseError(
                "%s: expected %d unique members per date, got %s"
                % (PIT_REQUIRED, expected_member_count, details)
            )
    return result.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)


def compress_membership_intervals(daily: pd.DataFrame) -> pd.DataFrame:
    """Compress consecutive observed membership dates into inclusive intervals.

    Consecutive means consecutive dates in the supplied market calendar, not
    consecutive civil days. Re-entry creates another interval for the symbol.
    """

    clean = validate_daily_membership(daily, expected_member_count=None)
    calendar = pd.DatetimeIndex(clean["date"].drop_duplicates().sort_values())
    date_position = pd.Series(range(len(calendar)), index=calendar)
    rows: List[Dict[str, Any]] = []
    for symbol, group in clean.groupby("symbol", sort=True):
        dates = pd.DatetimeIndex(group["date"].sort_values().unique())
        positions = date_position.loc[dates].to_numpy()
        starts = [0]
        starts.extend(((positions[1:] - positions[:-1] != 1).nonzero()[0] + 1).tolist())
        ends = [value - 1 for value in starts[1:]] + [len(dates) - 1]
        for interval_number, (start_idx, end_idx) in enumerate(zip(starts, ends), start=1):
            rows.append(
                {
                    "symbol": symbol,
                    "entry_date": dates[start_idx],
                    "exit_date": dates[end_idx],
                    "interval": interval_number,
                }
            )
    columns = ["symbol", "entry_date", "exit_date", "interval"]
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["symbol", "entry_date"], kind="mergesort"
    ).reset_index(drop=True)


class DataFramePointInTimeUniverse(PointInTimeUniverse):
    """Exact-date universe backed by validated daily snapshots."""

    def __init__(self, daily: pd.DataFrame, version: Optional[str] = None) -> None:
        self._daily = validate_daily_membership(daily, expected_member_count=None)
        self._version = version or dataframe_sha256(self._daily)

    def get_members(self, date: pd.Timestamp) -> List[str]:
        as_of = pd.Timestamp(date)
        if as_of.tzinfo is not None:
            as_of = as_of.tz_localize(None)
        as_of = as_of.normalize()
        selected = self._daily.loc[self._daily["date"] == as_of, "symbol"]
        if selected.empty:
            raise PointInTimeUniverseError(
                "%s: no snapshot for %s" % (PIT_REQUIRED, as_of.strftime("%Y-%m-%d"))
            )
        return selected.sort_values().tolist()

    def version(self) -> Optional[str]:
        return self._version

    @property
    def daily(self) -> pd.DataFrame:
        return self._daily.copy()


class BaoStockPointInTimeProvider(PointInTimeUniverseProvider):
    """Historical CSI500 snapshots using BaoStock's date-aware endpoint."""

    SUPPORTED_INDEXES = {"000905.SH", "CSI500", "ZZ500"}

    def __init__(
        self,
        client: Any = None,
        retry_count: int = 3,
        backoff_seconds: Sequence[float] = (1.0, 2.0, 4.0),
        request_interval: float = 0.25,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        if retry_count < 0:
            raise ProviderError("retry_count must be non-negative")
        if retry_count and not backoff_seconds:
            raise ProviderError("backoff_seconds must not be empty when retries are enabled")
        if any(float(value) < 0 for value in backoff_seconds):
            raise ProviderError("backoff_seconds values must be non-negative")
        if request_interval < 0:
            raise ProviderError("request_interval must be non-negative")
        self._client = client
        self._owns_session = False
        self.retry_count = int(retry_count)
        self.backoff_seconds = tuple(float(value) for value in backoff_seconds)
        self.request_interval = float(request_interval)
        self._sleep = sleep_fn
        self._monotonic = monotonic_fn
        self._last_request_at: Optional[float] = None

    def __enter__(self) -> "BaoStockPointInTimeProvider":
        client = self._get_client()

        def login() -> Any:
            result = client.login()
            if getattr(result, "error_code", "0") != "0":
                raise ProviderError(
                    "BaoStock login failed: %s"
                    % getattr(result, "error_msg", "unknown")
                )
            return result

        self._with_retry(login, "login")
        self._owns_session = True
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self._owns_session:
            self._client.logout()
            self._owns_session = False

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import baostock as bs
            except ImportError as exc:
                raise ProviderError(
                    "BaoStock is required for PIT CSI500 data; install dev/requirements-research.txt"
                ) from exc
            self._client = bs
        return self._client

    def _throttle(self) -> None:
        now = self._monotonic()
        if self._last_request_at is not None:
            remaining = self.request_interval - (now - self._last_request_at)
            if remaining > 0:
                self._sleep(remaining)
                now = self._monotonic()
        self._last_request_at = now

    def _with_retry(self, operation: Callable[[], Any], description: str) -> Any:
        last_error: Optional[BaseException] = None
        for attempt in range(self.retry_count + 1):
            self._throttle()
            try:
                return operation()
            except Exception as exc:  # BaoStock exposes several exception types
                last_error = exc
                if attempt >= self.retry_count:
                    break
                delay = self.backoff_seconds[
                    min(attempt, len(self.backoff_seconds) - 1)
                ]
                LOGGER.warning(
                    "BaoStock %s failed (attempt %d/%d): %s; retrying in %.2fs",
                    description,
                    attempt + 1,
                    self.retry_count + 1,
                    exc,
                    delay,
                )
                if delay:
                    self._sleep(delay)
        raise ProviderError(
            "BaoStock %s failed after %d attempt(s): %s"
            % (description, self.retry_count + 1, last_error)
        ) from last_error

    def _query_rows(
        self,
        method_name: str,
        description: str,
        *args: Any,
        required_fields: Sequence[str] = (),
        require_rows: bool = True,
        **kwargs: Any
    ) -> Tuple[List[str], List[List[str]]]:
        """Run and fully consume one BaoStock result inside the retry boundary."""

        client = self._get_client()

        def operation() -> Tuple[List[str], List[List[str]]]:
            query = getattr(client, method_name)(*args, **kwargs)
            if getattr(query, "error_code", "0") != "0":
                raise ProviderError(
                    "%s: %s"
                    % (description, getattr(query, "error_msg", "unknown error"))
                )
            fields = list(getattr(query, "fields", []))
            missing = sorted(set(required_fields).difference(fields))
            if missing:
                raise ProviderError(
                    "%s response missing fields %s" % (description, missing)
                )
            rows: List[List[str]] = []
            while query.next():
                rows.append(query.get_row_data())
            if getattr(query, "error_code", "0") != "0":
                raise ProviderError(
                    "%s iteration: %s"
                    % (description, getattr(query, "error_msg", "unknown error"))
                )
            if require_rows and not rows:
                raise ProviderError("%s returned no rows" % description)
            return fields, rows

        return self._with_retry(operation, description)

    def get_constituents(
        self, index_symbol: str, date: pd.Timestamp
    ) -> pd.DataFrame:
        if str(index_symbol).upper() not in self.SUPPORTED_INDEXES:
            raise ProviderError("BaoStock provider only supports CSI500/000905.SH")
        client = self._get_client()
        as_of = pd.Timestamp(date).strftime("%Y-%m-%d")
        query = client.query_zz500_stocks(date=as_of)
        if getattr(query, "error_code", "0") != "0":
            raise ProviderError(
                "BaoStock CSI500 query failed for %s: %s"
                % (as_of, getattr(query, "error_msg", "unknown"))
            )
        rows: List[List[str]] = []
        while query.next():
            rows.append(query.get_row_data())
        fields = list(getattr(query, "fields", []))
        data = pd.DataFrame(rows, columns=fields or None)
        if data.empty:
            raise ProviderError("BaoStock returned no CSI500 members for %s" % as_of)
        code_column = "code" if "code" in data.columns else data.columns[1]
        result = pd.DataFrame(
            {
                "date": pd.Timestamp(as_of),
                "symbol": data[code_column].map(canonical_symbol),
                "is_member": True,
            }
        )
        return result.sort_values("symbol").reset_index(drop=True)

    def get_security_history(
        self, symbols: Sequence[str], start: Any, end: Any
    ) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
        """Download daily ST/trading status and point-in-time listing dates."""

        status_parts: List[pd.DataFrame] = []
        listing_rows: List[Dict[str, Any]] = []
        failures: List[str] = []
        for symbol in sorted(set(symbols)):
            bs_symbol = "%s.%s" % (symbol[-2:].lower(), symbol[:6])
            try:
                basic_fields, basic_rows = self._query_rows(
                    "query_stock_basic",
                    "stock basic %s" % symbol,
                    code=bs_symbol,
                    required_fields=("ipoDate",),
                )
                basic_data = pd.DataFrame(basic_rows, columns=basic_fields)
                listing_date = pd.Timestamp(basic_data.iloc[0]["ipoDate"])
                history_fields, rows = self._query_rows(
                    "query_history_k_data_plus",
                    "security status %s" % symbol,
                    bs_symbol,
                    "date,code,tradestatus,isST",
                    start_date=pd.Timestamp(start).strftime("%Y-%m-%d"),
                    end_date=pd.Timestamp(end).strftime("%Y-%m-%d"),
                    frequency="d",
                    adjustflag="3",
                    required_fields=("date", "code", "tradestatus", "isST"),
                )
                part = pd.DataFrame(rows, columns=history_fields)
                status_parts.append(
                    pd.DataFrame(
                        {
                            "date": pd.to_datetime(part["date"]),
                            "symbol": symbol,
                            "trade_status": pd.to_numeric(
                                part["tradestatus"], errors="coerce"
                            ),
                            "is_st": pd.to_numeric(
                                part["isST"], errors="coerce"
                            ).astype("boolean"),
                        }
                    )
                )
                listing_rows.append(
                    {"symbol": symbol, "listing_date": listing_date}
                )
            except Exception as exc:  # one security must not abort a batch
                LOGGER.warning("BaoStock status failed for %s: %s", symbol, exc)
                failures.append(symbol)
        status = pd.concat(status_parts, ignore_index=True) if status_parts else pd.DataFrame(
            columns=["date", "symbol", "trade_status", "is_st"]
        )
        listings = pd.DataFrame(listing_rows, columns=["symbol", "listing_date"])
        return status, listings, failures


def dataframe_sha256(frame: pd.DataFrame) -> str:
    """Stable content hash independent of Parquet metadata."""

    ordered = frame.sort_values(list(frame.columns), kind="mergesort").reset_index(drop=True)
    values = ordered.to_csv(index=False, date_format="%Y-%m-%d", lineterminator="\n")
    return hashlib.sha256(values.encode("utf-8")).hexdigest()


def _atomic_parquet(frame: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    frame.to_parquet(temporary, index=False)
    os.replace(str(temporary), str(destination))


def _atomic_json(payload: Dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(str(temporary), str(destination))


def _snapshot_metadata(
    provider: PointInTimeUniverseProvider,
    index_symbol: str,
    date: pd.Timestamp,
    expected_member_count: int,
    snapshot: pd.DataFrame,
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "source": provider.__class__.__name__,
        "source_version": _BAOSTOCK_PIT_SOURCE_VERSION,
        "index_symbol": index_symbol,
        "date": pd.Timestamp(date).strftime("%Y-%m-%d"),
        "expected_member_count": int(expected_member_count),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sha256": dataframe_sha256(snapshot),
    }


def _load_cached_snapshot(
    snapshot_path: Path,
    metadata_path: Path,
    provider: PointInTimeUniverseProvider,
    index_symbol: str,
    date: pd.Timestamp,
    expected_member_count: int,
) -> pd.DataFrame:
    """Load only a snapshot whose source contract and content are auditable."""

    if not snapshot_path.exists() or not metadata_path.exists():
        raise PointInTimeUniverseError("cached snapshot provenance is missing")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise PointInTimeUniverseError("cached snapshot metadata is not a mapping")
    expected = {
        "schema_version": 1,
        "source": provider.__class__.__name__,
        "source_version": _BAOSTOCK_PIT_SOURCE_VERSION,
        "index_symbol": index_symbol,
        "date": pd.Timestamp(date).strftime("%Y-%m-%d"),
        "expected_member_count": int(expected_member_count),
    }
    mismatches = [
        name for name, value in expected.items() if metadata.get(name) != value
    ]
    if mismatches:
        raise PointInTimeUniverseError(
            "cached snapshot metadata mismatch: %s" % ", ".join(mismatches)
        )
    snapshot = validate_daily_membership(
        pd.read_parquet(snapshot_path), [date], expected_member_count
    )
    digest = metadata.get("sha256")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in digest)
        or digest.lower() != dataframe_sha256(snapshot)
    ):
        raise PointInTimeUniverseError("cached snapshot content hash mismatch")
    return snapshot


def collect_point_in_time_universe(
    provider: PointInTimeUniverseProvider,
    index_symbol: str,
    calendar: Iterable[Any],
    output_dir: Path,
    expected_member_count: int = 500,
    retries: int = 3,
    backoff_seconds: Sequence[float] = (1.0, 2.0, 4.0),
    request_interval_seconds: float = 0.25,
) -> Dict[str, Any]:
    """Collect resumable daily snapshots and materialise validated PIT files.

    Individual failures are recorded and collection continues. Materialisation
    fails after the loop unless every requested market date is valid.
    """

    output = Path(output_dir)
    if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
        raise PointInTimeUniverseError("retries must be a non-negative integer")
    if retries and not backoff_seconds:
        raise PointInTimeUniverseError(
            "backoff_seconds must not be empty when retries are enabled"
        )
    snapshots_dir = output / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    dates = _normalise_dates(calendar).unique().sort_values()
    failures: Dict[str, str] = {}
    parts: List[pd.DataFrame] = []
    for number, date in enumerate(dates):
        snapshot_path = snapshots_dir / (date.strftime("%Y-%m-%d") + ".parquet")
        metadata_path = snapshots_dir / (date.strftime("%Y-%m-%d") + ".json")
        snapshot: Optional[pd.DataFrame] = None
        if snapshot_path.exists() or metadata_path.exists():
            try:
                snapshot = _load_cached_snapshot(
                    snapshot_path,
                    metadata_path,
                    provider,
                    index_symbol,
                    date,
                    expected_member_count,
                )
            except Exception as exc:
                LOGGER.warning("Ignoring invalid cached PIT snapshot %s: %s", snapshot_path, exc)
        if snapshot is None:
            last_error: Optional[Exception] = None
            for attempt in range(retries + 1):
                try:
                    candidate = provider.get_constituents(index_symbol, date)
                    snapshot = validate_daily_membership(
                        candidate, [date], expected_member_count
                    )
                    _atomic_parquet(snapshot, snapshot_path)
                    _atomic_json(
                        _snapshot_metadata(
                            provider,
                            index_symbol,
                            date,
                            expected_member_count,
                            snapshot,
                        ),
                        metadata_path,
                    )
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt < retries:
                        delay = backoff_seconds[min(attempt, len(backoff_seconds) - 1)] if backoff_seconds else 0
                        time.sleep(max(0.0, float(delay)))
            if snapshot is None:
                failures[date.strftime("%Y-%m-%d")] = str(last_error)
                LOGGER.error("PIT snapshot failed for %s: %s", date.date(), last_error)
            if request_interval_seconds > 0 and number + 1 < len(dates):
                time.sleep(request_interval_seconds)
        if snapshot is not None:
            parts.append(snapshot)
    if failures or len(parts) != len(dates):
        failure_path = output / "failures.json"
        _atomic_json({"failed_dates": failures}, failure_path)
        raise PointInTimeUniverseError(
            "%s: %d/%d daily snapshots unavailable; see %s"
            % (PIT_REQUIRED, len(failures), len(dates), failure_path)
        )
    daily = validate_daily_membership(
        pd.concat(parts, ignore_index=True), dates, expected_member_count
    )
    intervals = compress_membership_intervals(daily)
    daily_path = output / "csi500_daily.parquet"
    interval_path = output / "csi500_intervals.parquet"
    _atomic_parquet(daily, daily_path)
    _atomic_parquet(intervals, interval_path)
    content_hash = dataframe_sha256(daily)
    manifest = {
        "schema_version": 1,
        "source": provider.__class__.__name__,
        "index_symbol": index_symbol,
        "source_version": _BAOSTOCK_PIT_SOURCE_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "start": dates.min().strftime("%Y-%m-%d"),
        "end": dates.max().strftime("%Y-%m-%d"),
        "trading_dates": int(len(dates)),
        "expected_member_count": int(expected_member_count),
        "sha256": content_hash,
    }
    _atomic_json(manifest, output / "manifest.json")
    return manifest


def import_point_in_time_universe(
    source: Path,
    output_dir: Path,
    calendar: Iterable[Any],
    expected_member_count: int = 500,
    index_symbol: str = "000905.SH",
) -> Dict[str, Any]:
    """Validate and materialise user-supplied daily CSV/Parquet membership."""

    path = Path(source)
    try:
        source_bytes = path.read_bytes()
    except OSError as exc:
        raise PointInTimeUniverseError(
            "%s: cannot read import file %s: %s" % (PIT_REQUIRED, path, exc)
        ) from exc
    source_file_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if path.suffix.lower() in {".parquet", ".pq"}:
        frame = pd.read_parquet(io.BytesIO(source_bytes))
    elif path.suffix.lower() == ".csv":
        frame = pd.read_csv(io.BytesIO(source_bytes))
    else:
        raise PointInTimeUniverseError(
            "%s: import must be CSV or Parquet" % PIT_REQUIRED
        )
    daily = validate_daily_membership(frame, calendar, expected_member_count)
    output = Path(output_dir)
    _atomic_parquet(daily, output / "csi500_daily.parquet")
    intervals = compress_membership_intervals(daily)
    _atomic_parquet(intervals, output / "csi500_intervals.parquet")
    digest = dataframe_sha256(daily)
    dates = _normalise_dates(calendar)
    manifest = {
        "schema_version": 1,
        "source": "local-import",
        "source_version": "user-pit-daily-import-v1",
        "source_file": str(path.resolve()),
        "source_file_sha256": source_file_sha256,
        "index_symbol": index_symbol,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "start": dates.min().strftime("%Y-%m-%d"),
        "end": dates.max().strftime("%Y-%m-%d"),
        "trading_dates": int(len(dates.unique())),
        "expected_member_count": int(expected_member_count),
        "sha256": digest,
    }
    _atomic_json(manifest, output / "manifest.json")
    return manifest
