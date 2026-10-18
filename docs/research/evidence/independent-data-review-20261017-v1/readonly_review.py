"""Independent, offline audit. Reads inputs; writes only new review evidence.

This is an audit companion, never a financial qualification or research entrypoint.
Run with Python -B. No original audit script or qbot pipeline is executed.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import time
import zipfile

import numpy as np
import pandas as pd


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo, source, output = [Path(v).resolve() for v in (args.repo, args.source, args.output)]
    if repo not in output.parents or source == output or source in output.parents:
        raise ValueError("review outputs must be separate and inside the repository")
    output.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    tick = time.perf_counter()
    tracked = subprocess.check_output(["git", "ls-files", "-z", "qbot/research", "configs/research", "docs/research", "tests/research", "dev"], cwd=repo).decode("utf-8").split("\0")
    protected = [repo / p for p in tracked if p and (repo / p).is_file()]
    protected += sorted(repo.glob("*AUDIT*.md"))
    protected += [source / n for n in ("AUDIT_SUMMARY.md", "audit_report.txt", "deep_audit_report.txt", "audit_stock_data.py", "deep_audit.py")]
    original_hashes = {str(p): digest(p) for p in protected}
    archives = sorted(source.glob("202*.zip"))
    loose = sorted(source.glob("202*.csv"))
    containers = archives + loose
    container_hashes = {str(p): digest(p) for p in containers}
    container_stats = {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in containers}
    print(json.dumps({"event": "baseline", "protected_files": len(protected), "archives": len(archives), "loose_csv": len(loose)}, ensure_ascii=False), flush=True)

    expected = ["证券代码", "证券名称", "交易日期", "分钟时间", "开盘价（元）", "最高价（元）", "最低价（元）", "收盘价（元）", "成交量", "成交额", "复权因子"]
    code, name, day, stamp = expected[:4]
    numeric = expected[4:]
    daily, members, errors = [], [], []
    years = defaultdict(lambda: {"dates": set(), "codes": set(), "rows": 0})
    securities = defaultdict(lambda: {"dates": set(), "names": set()})
    slots = Counter()
    totals = Counter()
    examples = defaultdict(list)
    targets = {"600000.SH", "000001.SZ", "600519.SH", "000002.SZ", "300750.SZ", "688981.SH", "601059.SH", "001289.SZ", "600112.SH", "000961.SZ", "300114.SZ", "302132.SZ", "000780.SZ"}
    target_rows = []

    def inspect(content, locator, declared, container):
        frame = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig", dtype={c: str for c in expected[:4]}, low_memory=False)
        n = len(frame)
        if list(frame.columns) != expected:
            raise ValueError("11-column source schema mismatch")
        counts = frame.groupby(code, dropna=False).size()
        times = frame[stamp].str[11:19]
        time_counts = times.value_counts(dropna=False)
        unique_times = sorted(str(t) for t in time_counts.index)
        timestamp_valid = frame[stamp].str.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}").fillna(False)
        timestamp_parse = pd.to_datetime(frame[stamp], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        expected_date = pd.Timestamp(declared).strftime("%Y%m%d")
        mismatch = frame[day].ne(expected_date) | frame[stamp].str[:10].ne(declared)
        values = frame[numeric].apply(pd.to_numeric, errors="coerce")
        o, h, l, c = [values[x] for x in expected[4:8]]
        bad_ohlc = h.lt(l) | o.lt(l) | o.gt(h) | c.lt(l) | c.gt(h)
        duplicates = frame.duplicated([code, stamp])
        factors = values.groupby(frame[code])["复权因子"].nunique(dropna=False)
        expected_slots = {"09:30:00", "10:00:00", "10:30:00", "11:00:00", "11:30:00", "13:30:00", "14:00:00", "14:30:00", "15:00:00"}
        pair_unique = frame.assign(_time=times).groupby(code)["_time"].nunique()
        hist = Counter(int(v) for v in counts)
        row = {
            "date": declared, "container": container, "locator": locator, "rows": n,
            "securities": int(frame[code].nunique()), "SH": int(frame.loc[frame[code].str.endswith(".SH", na=False), code].nunique()),
            "SZ": int(frame.loc[frame[code].str.endswith(".SZ", na=False), code].nunique()), "BJ": int(frame.loc[frame[code].str.endswith(".BJ", na=False), code].nunique()),
            "first_1000_securities": int(frame.head(1000)[code].nunique()),
            "bars_min": int(counts.min()), "bars_max": int(counts.max()), "bars_histogram": json.dumps(dict(sorted(hist.items()))),
            "not_nine_rows_securities": int(counts.ne(9).sum()), "not_nine_unique_slots_securities": int(pair_unique.ne(9).sum()),
            "duplicate_keys": int(duplicates.sum()), "date_mismatch_rows": int(mismatch.sum()),
            "invalid_timestamp_rows": int((~timestamp_valid | timestamp_parse.isna()).sum()),
            "null_cells": int(frame.isna().sum().sum()), "nonfinite_numeric_cells": int((~np.isfinite(values.to_numpy())).sum()),
            "ohlc_logic_rows": int(bad_ohlc.sum()), "nonpositive_price_rows": int(values.iloc[:, :4].le(0).any(axis=1).sum()),
            "negative_volume_rows": int(values["成交量"].lt(0).sum()), "negative_amount_rows": int(values["成交额"].lt(0).sum()),
            "zero_volume_rows": int(values["成交量"].eq(0).sum()), "zero_amount_rows": int(values["成交额"].eq(0).sum()),
            "nonpositive_factor_rows": int(values["复权因子"].le(0).sum()), "intraday_factor_change_securities": int(factors.gt(1).sum()),
            "factor_min": float(values["复权因子"].min()), "factor_max": float(values["复权因子"].max()),
            "time_labels": "|".join(unique_times), "outside_nine_label_rows": int((~times.isin(expected_slots)).sum()),
            "content_sha256": hashlib.sha256(content).hexdigest(),
        }
        for k in ("duplicate_keys", "date_mismatch_rows", "invalid_timestamp_rows", "null_cells", "nonfinite_numeric_cells", "ohlc_logic_rows", "nonpositive_price_rows", "negative_volume_rows", "negative_amount_rows", "zero_volume_rows", "zero_amount_rows", "nonpositive_factor_rows", "intraday_factor_change_securities", "outside_nine_label_rows"):
            totals[k] += row[k]
        for k, mask in (("bad_ohlc", bad_ohlc), ("zero_volume", values["成交量"].eq(0)), ("zero_price", values.iloc[:, :4].le(0).any(axis=1))):
            if mask.any() and len(examples[k]) < 10:
                examples[k].extend(frame.loc[mask, [code, day, stamp]].head(3).to_dict("records"))
        yr = declared[:4]
        years[yr]["dates"].add(declared)
        years[yr]["codes"].update(frame[code].dropna())
        years[yr]["rows"] += n
        for ticker, title in frame[[code, name]].drop_duplicates().itertuples(index=False, name=None):
            securities[ticker]["dates"].add(declared)
            if pd.notna(title):
                securities[ticker]["names"].add(title)
        for ticker, group in frame.loc[frame[code].isin(targets)].groupby(code, sort=False):
            target_rows.append({"date": declared, "symbol": ticker, "rows": len(group), "names": "|".join(sorted(set(group[name].dropna())))})
        slots.update({str(k): int(v) for k, v in time_counts.items()})
        daily.append(row)
        if len(daily) % 100 == 0:
            print(json.dumps({"event": "progress", "days": len(daily), "elapsed_seconds": round(time.perf_counter()-tick, 1)}, ensure_ascii=False), flush=True)

    for archive in archives:
        try:
            with zipfile.ZipFile(archive) as z:
                infos = [i for i in z.infolist() if not i.is_dir()]
                for info in infos:
                    match = re.search(r"(?:^|/)(\d{8})_.*\.csv$", info.filename)
                    if not match:
                        errors.append({"source": archive.name, "member": info.filename, "error": "unexpected non-daily-CSV member"})
                        continue
                    declared = pd.Timestamp(match.group(1)).strftime("%Y-%m-%d")
                    try:
                        content = z.read(info)  # Full member read also verifies ZIP CRC.
                        inspect(content, info.filename, declared, archive.name)
                        members.append({"archive": archive.name, "member": info.filename, "bytes": info.file_size, "crc32": "%08x" % info.CRC, "sha256": hashlib.sha256(content).hexdigest()})
                    except Exception as exc:
                        errors.append({"source": archive.name, "member": info.filename, "error": repr(exc)})
        except Exception as exc:
            errors.append({"source": archive.name, "error": repr(exc)})
        print(json.dumps({"event": "archive_done", "archive": archive.name, "days_done": len(daily), "elapsed_seconds": round(time.perf_counter()-tick, 1), "errors": len(errors)}, ensure_ascii=False), flush=True)
    for p in loose:
        try:
            declared = pd.Timestamp(p.name[:8]).strftime("%Y-%m-%d")
            inspect(p.read_bytes(), p.name, declared, "loose_2026_csv")
        except Exception as exc:
            errors.append({"source": p.name, "error": repr(exc)})

    daily_frame = pd.DataFrame(daily).sort_values(["date", "container", "locator"])
    calendar_path = repo / "data/research/five-year-pilot/20261015-native-calendar-v1/runs/20261015T111701027971Z-d51bb4d1/calendar.csv"
    calendar = pd.read_csv(calendar_path).date.astype(str).str[:10]
    research = set(calendar[(calendar >= "2021-09-13") & (calendar <= "2026-09-11")])
    present = set(daily_frame.date)
    research_frame = daily_frame[daily_frame.date.isin(research)]
    all_calendar = set(calendar)
    calendar_evidence = {"path": str(calendar_path.relative_to(repo)), "sha256": digest(calendar_path), "days": len(calendar), "research_days": len(research), "missing_research_dates": sorted(research-present), "missing_warmup_dates": sorted((all_calendar-research)-present), "extra_dates_within_calendar_bounds": sorted({d for d in present if min(all_calendar) <= d <= max(all_calendar)}-all_calendar), "research_daily_securities_min": int(research_frame.securities.min()), "research_daily_securities_max": int(research_frame.securities.max())}
    year_summary = []
    for yr, state in sorted(years.items()):
        subset = daily_frame[daily_frame.date.str.startswith(yr)]
        year_summary.append({"year": yr, "csv_days": len(subset), "first": min(state["dates"]), "last": max(state["dates"]), "rows": state["rows"], "unique_codes": len(state["codes"]), "daily_securities_min": int(subset.securities.min()), "daily_securities_max": int(subset.securities.max()), "daily_securities_median": float(subset.securities.median()), "daily_securities_mean": float(subset.securities.mean()), "bars_min": int(subset.bars_min.min()), "bars_max": int(subset.bars_max.max()), "zero_volume_rows": int(subset.zero_volume_rows.sum())})
    security_summary = [{"symbol": ticker, "observed_days": len(v["dates"]), "first_observation": min(v["dates"]), "last_observation": max(v["dates"]), "research_observed_days": len(v["dates"] & research), "research_missing_grid_days": len(research-v["dates"]), "names": "|".join(sorted(v["names"]))} for ticker, v in sorted(securities.items())]
    changed_protected = [p for p, before in original_hashes.items() if digest(Path(p)) != before]
    changed_containers = [p for p, before in container_hashes.items() if digest(Path(p)) != before]
    changed_stats = [p for p, before in container_stats.items() if (Path(p).stat().st_size, Path(p).stat().st_mtime_ns) != before]
    summary = {"schema": "INDEPENDENT_READONLY_REVIEW_V1", "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(), "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip(), "source": str(source), "python": __import__("sys").version, "pandas": pd.__version__, "numpy": np.__version__, "elapsed_seconds": time.perf_counter()-tick, "formal_admission": False, "no_live_money": True, "network_requests_by_checker": 0, "csv_days": len(daily), "total_rows": int(daily_frame.rows.sum()), "unique_codes": len(securities), "duplicate_file_dates": int(daily_frame.date.duplicated().sum()), "year_summary": year_summary, "time_label_row_counts": dict(slots), "aggregate_checks": dict(totals), "examples_key_only": dict(examples), "calendar_comparison": calendar_evidence, "targets": [s for s in security_summary if s["symbol"] in targets], "errors": errors, "preservation": {"protected_files": len(original_hashes), "containers": len(container_hashes), "changed_protected_sha256": changed_protected, "changed_container_sha256": changed_containers, "changed_container_size_mtime": changed_stats}}
    artifacts = {
        "summary.json": json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        "input-hashes.json": json.dumps({"protected_files": original_hashes, "containers": container_hashes, "archive_members": members}, ensure_ascii=False, indent=2) + "\n",
        "daily-counts.csv": daily_frame.to_csv(index=False),
        "security-observations.csv": pd.DataFrame(security_summary).to_csv(index=False),
        "target-observations.csv": pd.DataFrame(target_rows).sort_values(["symbol", "date"]).to_csv(index=False),
    }
    for filename, content in artifacts.items():
        with (output / filename).open("x", encoding="utf-8", newline="") as stream:
            stream.write(content)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
