"""FactorLab engineering adapter. It cannot satisfy MarketDataProvider."""

import json
import hashlib
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from qbot.research.forward.integrity import assert_no_link_components
from .contract import CONTRACT, SCHEMA, IntradayDataError, json_bytes
from .source import file_sha


class IntradayParquetProvider:
    frequency = "VENDOR_30M_LABELS"
    financial_research_eligible = False

    def __init__(self, root, *, purpose):
        if purpose not in {"engineering", "exploratory"}:
            raise IntradayDataError("MINUTE_OBSERVATIONS_NOT_FORMALLY_RESEARCH_ELIGIBLE")
        self.root = assert_no_link_components(Path(root))
        self.catalog = json.loads((self.root / "dataset.json").read_text(encoding="utf-8"))
        if (self.catalog["contract"] != json.loads(json_bytes(CONTRACT)) or not self.catalog["complete"] or
                self.catalog["schema"] != CONTRACT["schema"]):
            raise IntradayDataError("INVALID_OR_INCOMPLETE_INTRADAY_DATASET")
        dates = [d for p in self.catalog["partitions"] for d in p["dates"]]
        if len(dates) != len(set(dates)) or sorted(dates) != self.catalog["selection"]["dates"]:
            raise IntradayDataError("INTRADAY_PARTITION_COVERAGE_MISMATCH")
        if sum(p["rows"] for p in self.catalog["partitions"]) != self.catalog["rows"]:
            raise IntradayDataError("INTRADAY_CATALOG_COUNTS_MISMATCH")
        if hashlib.sha256(json_bytes(self.catalog["selection"])).hexdigest() != self.catalog["selection_id"]:
            raise IntradayDataError("INTRADAY_SELECTION_ID_MISMATCH")

    def _path(self, relative):
        relative = Path(relative)
        if relative.is_absolute() or ".." in relative.parts:
            raise IntradayDataError("UNSAFE_DATASET_PATH")
        return assert_no_link_components(self.root / relative)

    def iter_batches(self, *, start=None, end=None, symbols=None, columns=None, batch_size=65536):
        if batch_size < 1:
            raise IntradayDataError("POSITIVE_BATCH_SIZE_REQUIRED")
        for partition in self.catalog["partitions"]:
            if (start and max(partition["dates"]) < start) or (end and min(partition["dates"]) > end):
                continue
            receipt_path, path = self._path(partition["receipt"]), self._path(partition["parquet"])
            if file_sha(receipt_path) != partition["receipt_sha256"] or file_sha(path) != partition["parquet_sha256"]:
                raise IntradayDataError("INTRADAY_ARTIFACT_HASH_MISMATCH")
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if (receipt["contract"] != self.catalog["contract"] or receipt["rows"] != partition["rows"] or
                    receipt["identity"] != partition["identity"] or receipt["parquet_sha256"] != partition["parquet_sha256"] or
                    receipt["implementation_sha256"] != self.catalog["selection"]["implementation_sha256"] or
                    [d["date"] for d in receipt["days"]] != partition["dates"]):
                raise IntradayDataError("INTRADAY_RECEIPT_MISMATCH")
            parquet = pq.ParquetFile(path)
            if not parquet.schema_arrow.equals(SCHEMA, check_metadata=True):
                raise IntradayDataError("INTRADAY_SCHEMA_MISMATCH")
            for batch in parquet.iter_batches(batch_size=batch_size):
                table = pa.Table.from_batches([batch], schema=SCHEMA)
                mask = pa.array([True] * len(table))
                if start:
                    mask = pc.and_(mask, pc.greater_equal(table["trade_date"], pa.scalar(date.fromisoformat(start))))
                if end:
                    mask = pc.and_(mask, pc.less_equal(table["trade_date"], pa.scalar(date.fromisoformat(end))))
                if symbols is not None:
                    mask = pc.and_(mask, pc.is_in(table["symbol"], value_set=pa.array(list(symbols), type=pa.string())))
                table = table.filter(mask)
                if columns is not None:
                    table = table.select(columns)
                yield from table.to_batches(max_chunksize=batch_size)

    def daily_bars(self, *args, **kwargs):
        raise IntradayDataError("DAILY_AGGREGATION_DISABLED_UNKNOWN_INTERVAL_AND_UNIT_SEMANTICS")
