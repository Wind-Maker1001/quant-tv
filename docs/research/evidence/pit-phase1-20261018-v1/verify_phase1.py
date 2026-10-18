"""Read-only integrity/completeness checks for the delivered phase-one evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", help="Optional NEW receipt path; existing files are never overwritten")
    args = ap.parse_args()
    repo = Path.cwd().resolve()
    public = repo / "docs/research/evidence/pit-phase1-20261018-v1"
    private = repo / "data/research/diagnostics/pit-phase1/20261018-v1"
    load = lambda p: json.loads(p.read_text(encoding="utf-8"))
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    initial = load(private / "start-preservation.json")
    offline = load(public / "offline-check-receipt.json")
    baseline = load(public / "baseline-result.json")
    assembly = load(public / "delivery-assembly-receipt.json")
    evidence = load(public / "evidence-register.json")["evidence"]
    candidates = load(public / "candidate-events.json")
    mapping = load(public / "identity-mapping-proposal.json")
    matrix = pd.read_csv(public / "pit-evidence-matrix.csv", keep_default_na=False)
    gaps = pd.read_csv(public / "actual-effective-gaps.csv", keep_default_na=False)
    expected = dict(initial["protected_sha256"])
    expected.update(offline["original_file_sha256_at_read"])
    for row in baseline["reused_prior_inputs"]:
        expected[row["path"]] = row["sha256"]
    for row in evidence:
        expected[row["local_path"]] = row["local_file_sha256"]
    changed = [name for name, before in expected.items() if digest(repo / name) != before]
    assert not changed, changed
    assert digest(public / "review_pit_evidence.py") == offline["script_sha256"]
    assert digest(public / "assemble_phase1_delivery.py") == assembly["script_sha256"]
    assert digest(repo / baseline["search_archive"]) == baseline["search_archive_sha256"]
    assert len(matrix) == len(gaps) == len(candidates["events"]) == 14
    assert matrix.notice_id.nunique() == 14 and set(matrix.notice_id) == set(gaps.notice_id)
    assert matrix.actual_effective_member_date.eq("UNKNOWN").all()
    assert matrix.historical_known_at.eq("UNKNOWN").all() and gaps.actual_effective_date.eq("UNKNOWN").all()
    assert len(evidence) == 30
    for row in evidence:
        assert row["source_url"].startswith("https://")
        assert row["publication_date"] and row["actual_effective_date"] and row["historical_known_at"]
        assert len(row["local_file_sha256"]) == 64
        assert row["formal_admission"] is False
        if "browser" in row["representation"]:
            assert row["publisher_original_response_sha256"] == "UNKNOWN"
    regular = [e for e in candidates["events"] if e["matrix"]["event_kind"] == "REGULAR"]
    assert len(regular) == 10 and all(e["matrix"]["candidate_add"] == e["matrix"]["candidate_remove"] == 50 for e in regular)
    changes = [c for e in candidates["events"] for c in e["changes"]]
    assert len(changes) == 1008
    unknown = [c for c in changes if c.get("symbol") is None]
    assert len(unknown) == 1 and unknown[0]["raw_code"] == "-"
    target = next(e for e in candidates["events"] if e["matrix"]["notice_id"] == 3006227)
    assert {(c["action"], c["symbol"]) for c in target["changes"]} == {("REMOVE", "601198.SH"), ("ADD", "603083.SH")}
    assert baseline["verified_complete_baselines"] == 0 and baseline["verified_members_from_authoritative_baseline"] == "UNKNOWN"
    assert baseline["no_member_list_generated"] and not candidates["daily_members_generated"]
    assert not candidates["formal_admission"] and not mapping["formal_admission"]
    assert not mapping["formal_identity_snapshot_eligible"] and mapping["transition"]["first_historically_known_at"] == "UNKNOWN"
    assert mapping["transition"]["source_stated_code_change_date"] == "2025-02-17"
    assert offline["network_requests"] == offline["market_price_files_opened"] == 0
    assert baseline["csi_notice_body_requests"] == 0 and not baseline["csi_denied_workflow_reopened"]
    assert digest(repo / assembly["new_original_path"]) == assembly["new_original_sha256"]
    report = repo / "docs/research/PIT_PHASE1_EVIDENCE_2026-10-18.md"
    links = re.findall(r"\]\(([^)]+)\)", report.read_text(encoding="utf-8"))
    planned_receipt = (repo / args.receipt).resolve() if args.receipt else None
    broken = [t for t in links if not t.startswith(("http://", "https://", "#")) and not (report.parent / t).exists()
              and (report.parent / t).resolve() != planned_receipt]
    assert not broken, broken
    assert subprocess.run(["git", "diff", "--quiet"], cwd=repo).returncode == 0
    artifacts = {str(p.relative_to(repo)).replace("\\", "/"): digest(p) for p in public.iterdir() if p.is_file()}
    artifacts[str(report.relative_to(repo)).replace("\\", "/")] = digest(report)
    receipt = {"schema": "PIT_PHASE1_FINAL_VERIFICATION_V1", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
               "original_protected_files": len(initial["protected_sha256"]), "existing_event_inputs": len(offline["original_file_sha256_at_read"]),
               "total_distinct_bound_files_rechecked": len(expected), "changed_files": changed, "tracked_diff_empty": True,
               "candidate_events_checked": 14, "evidence_records_checked": 30, "candidate_actions_checked": 1008,
               "actual_index_effective_dates_certified": 0, "authority_baselines_obtained": 0, "unknowns_preserved": True,
               "new_original_sha256": assembly["new_original_sha256"], "output_sha256": artifacts,
               "formal_admission": False, "forward_activated": False, "no_live_money": True,
               "scope": "Integrity and evidence-contract review only; neither hashes nor this receipt authenticate historical truth or qualify financial inputs"}
    if planned_receipt:
        if repo not in planned_receipt.parents:
            raise ValueError("new receipt must remain inside the repository")
        with planned_receipt.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(receipt, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "output_sha256"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
