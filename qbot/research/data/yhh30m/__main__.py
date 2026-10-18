"""Run with python -m qbot.research.data.yhh30m convert/verify."""

import argparse
import json
from pathlib import Path

from .conversion import convert
from .provider import IntradayParquetProvider
from .storage import verify_partition


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    command = subs.add_parser("convert", help="Read audited ZIP/CSV into an isolated monthly dataset")
    command.add_argument("--source", required=True, type=Path)
    command.add_argument("--audit", required=True, type=Path)
    command.add_argument("--output", required=True, type=Path)
    command.add_argument("--start")
    command.add_argument("--end")
    command.add_argument("--block-bytes", type=int, default=1024 * 1024)
    verify = subs.add_parser("verify", help="Verify published bytes, row counts and source samples")
    verify.add_argument("--dataset", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.command == "convert":
        result = convert(args.source, args.audit, args.output, args.start, args.end, args.block_bytes,
                         progress=lambda value: print(json.dumps(value, ensure_ascii=False), flush=True))
    else:
        provider = IntradayParquetProvider(args.dataset, purpose="engineering")
        for partition in provider.catalog["partitions"]:
            receipt_path = provider._path(partition["receipt"])
            from .source import file_sha
            if file_sha(receipt_path) != partition["receipt_sha256"]:
                raise ValueError("RECEIPT_HASH_MISMATCH")
            verify_partition(receipt_path.parent)
        result = {"status": "VERIFIED", "rows": provider.catalog["rows"],
                  "partitions": len(provider.catalog["partitions"]), "formal_admission": False}
    print(json.dumps({key: value for key, value in result.items() if key != "source_containers"}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
