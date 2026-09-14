"""Atomic per-symbol Parquet cache with explicit request coverage."""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

try:
    from qbot.research.errors import CacheError
except ImportError:  # pragma: no cover - isolated bootstrapping only
    class CacheError(RuntimeError):
        """Fallback used only when the package foundation is unavailable."""

from qbot.research.data.providers.base import DateLike, MarketDataProvider
from qbot.research.data.schema import canonicalize_bars, empty_bars, normalize_symbol


Range = Tuple[pd.Timestamp, pd.Timestamp]


def _normalise_date(value: DateLike) -> pd.Timestamp:
    try:
        result = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise CacheError("invalid cache coverage date: %r" % (value,)) from exc
    if result.tzinfo is not None:
        result = result.tz_localize(None)
    return result.normalize()


def _merge_ranges(ranges: Iterable[Range]) -> List[Range]:
    ordered = sorted(
        ((_normalise_date(start), _normalise_date(end)) for start, end in ranges),
        key=lambda item: item[0],
    )
    merged: List[Range] = []
    for start, end in ordered:
        if start > end:
            raise CacheError("coverage start must be on or before coverage end")
        if not merged or start > merged[-1][1] + pd.Timedelta(days=1):
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _subtract_ranges(requested: Range, covered: Sequence[Range]) -> List[Range]:
    start, end = requested
    cursor = start
    gaps: List[Range] = []
    for covered_start, covered_end in _merge_ranges(covered):
        if covered_end < cursor:
            continue
        if covered_start > end:
            break
        if covered_start > cursor:
            gaps.append((cursor, min(end, covered_start - pd.Timedelta(days=1))))
        cursor = max(cursor, covered_end + pd.Timedelta(days=1))
        if cursor > end:
            break
    if cursor <= end:
        gaps.append((cursor, end))
    return gaps


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class ParquetBarCache:
    """Cache canonical bars in one independently resumable file per symbol.

    ``covered_ranges`` records successful vendor requests, including requests
    that returned no rows.  Therefore incremental updates do not repeatedly
    fetch weekends, suspensions, or pre-listing days merely because no bar is
    stored for them.
    """

    metadata_version = 1

    def __init__(self, root: Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def data_path(self, symbol: str) -> Path:
        return self.root / (normalize_symbol(symbol) + ".parquet")

    def metadata_path(self, symbol: str) -> Path:
        return self.root / (normalize_symbol(symbol) + ".metadata.json")

    def read_metadata(self, symbol: str) -> Dict[str, Any]:
        path = self.metadata_path(symbol)
        if not path.exists():
            return {}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CacheError("cannot read cache metadata: %s" % path) from exc
        if not isinstance(value, dict):
            raise CacheError("cache metadata must be a JSON object: %s" % path)
        return value

    @staticmethod
    def _coverage_from_metadata(metadata: Dict[str, Any]) -> List[Range]:
        ranges: List[Range] = []
        for value in metadata.get("covered_ranges", []):
            if not isinstance(value, dict) or "start" not in value or "end" not in value:
                raise CacheError("invalid covered_ranges entry in cache metadata")
            ranges.append((_normalise_date(value["start"]), _normalise_date(value["end"])))
        return _merge_ranges(ranges)

    def missing_ranges(
        self,
        symbol: str,
        start: DateLike,
        end: DateLike,
    ) -> List[Range]:
        """Return uncovered inclusive calendar-date ranges for a request."""

        requested = (_normalise_date(start), _normalise_date(end))
        if requested[0] > requested[1]:
            raise CacheError("cache request start must be on or before end")
        covered = self._coverage_from_metadata(self.read_metadata(symbol))
        return _subtract_ranges(requested, covered)

    def load(self, symbol: str, verify_hash: bool = True) -> pd.DataFrame:
        """Load and validate a symbol cache, returning an empty canonical frame."""

        canonical_symbol = normalize_symbol(symbol)
        path = self.data_path(canonical_symbol)
        if not path.exists():
            return empty_bars()
        metadata = self.read_metadata(canonical_symbol)
        expected_hash = metadata.get("content_sha256")
        if verify_hash and expected_hash and _sha256(path) != expected_hash:
            raise CacheError("cache content hash mismatch: %s" % path)
        try:
            frame = pd.read_parquet(path)
        except Exception as exc:
            raise CacheError("cannot read cached Parquet: %s" % path) from exc
        try:
            return canonicalize_bars(
                frame, symbol=canonical_symbol, allow_missing_ohlc=True
            )
        except Exception as exc:
            raise CacheError("cached bars failed schema validation: %s" % path) from exc

    @staticmethod
    def _atomic_parquet(frame: pd.DataFrame, target: Path) -> None:
        temporary = target.with_name(".%s.tmp-%s" % (target.name, uuid.uuid4().hex))
        try:
            frame.to_parquet(temporary, index=False)
            os.replace(str(temporary), str(target))
        except Exception:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise

    @staticmethod
    def _atomic_json(value: Dict[str, Any], target: Path) -> None:
        temporary = target.with_name(".%s.tmp-%s" % (target.name, uuid.uuid4().hex))
        payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        try:
            temporary.write_text(payload, encoding="utf-8")
            os.replace(str(temporary), str(target))
        except Exception:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            raise

    def update(
        self,
        symbol: str,
        bars: pd.DataFrame,
        covered_start: DateLike,
        covered_end: DateLike,
        source: str,
        source_version: Optional[str] = None,
    ) -> pd.DataFrame:
        """Merge bars and atomically replace data and metadata files."""

        canonical_symbol = normalize_symbol(symbol)
        coverage = (_normalise_date(covered_start), _normalise_date(covered_end))
        if coverage[0] > coverage[1]:
            raise CacheError("covered_start must be on or before covered_end")
        try:
            incoming = canonicalize_bars(
                bars, symbol=canonical_symbol, allow_missing_ohlc=True
            )
        except Exception as exc:
            raise CacheError("incoming bars failed schema validation") from exc
        outside = ~incoming["date"].between(coverage[0], coverage[1])
        if outside.any():
            raise CacheError("incoming bars fall outside the declared coverage")

        current = self.load(canonical_symbol)
        if current.empty:
            merged = incoming
        elif incoming.empty:
            merged = current
        else:
            # A later successful request is authoritative for overlapping dates.
            merged = pd.concat([current, incoming], ignore_index=True)
            merged = merged.drop_duplicates(["date", "symbol"], keep="last")
            merged = canonicalize_bars(
                merged, symbol=canonical_symbol, allow_missing_ohlc=True
            )

        old_metadata = self.read_metadata(canonical_symbol)
        covered_ranges = self._coverage_from_metadata(old_metadata)
        covered_ranges = _merge_ranges(covered_ranges + [coverage])
        data_path = self.data_path(canonical_symbol)
        metadata_path = self.metadata_path(canonical_symbol)
        try:
            self._atomic_parquet(merged, data_path)
            metadata: Dict[str, Any] = {
                "metadata_version": self.metadata_version,
                "symbol": canonical_symbol,
                "source": source,
                "source_version": source_version or "unknown",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "row_count": int(len(merged)),
                "data_start": (
                    merged["date"].min().date().isoformat() if not merged.empty else None
                ),
                "data_end": (
                    merged["date"].max().date().isoformat() if not merged.empty else None
                ),
                "covered_ranges": [
                    {
                        "start": start.date().isoformat(),
                        "end": end.date().isoformat(),
                    }
                    for start, end in covered_ranges
                ],
                "content_sha256": _sha256(data_path),
            }
            self._atomic_json(metadata, metadata_path)
        except Exception as exc:
            raise CacheError("failed to atomically update cache for %s" % canonical_symbol) from exc
        return merged

    def update_from_provider(
        self,
        provider: MarketDataProvider,
        symbol: str,
        start: DateLike,
        end: DateLike,
        is_index: bool = False,
    ) -> pd.DataFrame:
        """Fetch only uncovered ranges and update the cache deterministically."""

        canonical_symbol = normalize_symbol(symbol)
        source = provider.__class__.__name__
        try:
            source_version = str(getattr(provider, "source_version", "unknown"))
        except Exception:
            source_version = "unknown"
        for gap_start, gap_end in self.missing_ranges(
            canonical_symbol, start, end
        ):
            if is_index:
                bars = provider.get_index_bars(
                    canonical_symbol, gap_start, gap_end
                )
            else:
                bars = provider.get_daily_bars(
                    canonical_symbol, gap_start, gap_end
                )
            self.update(
                canonical_symbol,
                bars,
                covered_start=gap_start,
                covered_end=gap_end,
                source=source,
                source_version=source_version,
            )
        return self.load(canonical_symbol)


__all__ = ["ParquetBarCache"]
