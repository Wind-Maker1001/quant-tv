"""Read-only public archive integrity; original financial certification NOT_RUN."""

import ast
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRIVATE_PATH = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/]+|(?<![A-Za-z0-9_])/(?:Users|home|mnt)/")
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"AKIA[A-Z0-9]{16}"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9_.-]{24,}"),
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local(name):
    path = (ROOT / name).resolve()
    path.relative_to(ROOT)
    return path


def load(name):
    return json.loads(local(name).read_text(encoding="utf-8"))


def verify():
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    require(manifest["schema"] == "PIT_PUBLICATION_REDACTION_V1", "Unknown public-copy schema")
    require(manifest["formal_admission"] is False and manifest["no_live_money"] is True,
            "Admission boundary changed")
    require(len(manifest["files"]) == 48, "Expected 43 original and 5 migration copies")
    scripts = 0
    for item in manifest["files"] + manifest["publication_artifacts"]:
        raw = local(item["path"]).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == item["public_sha256"]
                and len(raw) == item["public_bytes"], "Public-copy hash mismatch: " + item["path"])
        text = raw.decode("utf-8")
        require(not PRIVATE_PATH.search(text), "Absolute local path in: " + item["path"])
        require(not any(pattern.search(text) for pattern in SECRET_PATTERNS),
                "Credential pattern in: " + item["path"])
        if item["path"].endswith(".json"):
            json.loads(text)
        if item["path"].endswith(".py"):
            ast.parse(text, filename=item["path"])
            scripts += 1
    require(not PRIVATE_PATH.search(json.dumps(manifest)), "Private path in public manifest")

    prefix = "docs/research/evidence/"
    release = load(prefix + "audit-pit-release-20261018-v1/release-manifest.json")
    for item in release["protected_contracts"]:
        content = local(item["path"]).read_bytes().replace(b"\r\n", b"\n")
        require(hashlib.sha256(content).hexdigest() == item["normalized_text_sha256"],
                "Historical research text changed: " + item["path"])
    audit = prefix + "independent-data-review-20261017-v1/"
    summary = load(audit + "summary.json")
    with local(audit + "daily-counts.csv").open(encoding="utf-8", newline="") as stream:
        daily = list(csv.DictReader(stream))
    require(len(daily) == summary["csv_days"] == 1393, "Daily derivative count mismatch")
    require(sum(int(r["rows"]) for r in daily) == summary["total_rows"] == 64115523,
            "Historical derivative row total changed")
    years = defaultdict(list)
    for row in daily:
        years[row["date"][:4]].append(row)
    for annual in summary["year_summary"]:
        rows = years[str(annual["year"])]
        require(len(rows) == annual["csv_days"] and sum(int(r["rows"]) for r in rows) == annual["rows"],
                "Annual derivative reconciliation failed")
    phase = prefix + "pit-phase1-20261018-v1/"
    candidates = load(phase + "candidate-events.json")
    events = candidates["events"]
    require(len(events) == 14 and candidates["formal_admission"] is False
            and candidates["daily_members_generated"] is False
            and candidates["chain_completeness"] == "UNKNOWN", "Candidate scope changed")
    require(all(e["matrix"]["actual_effective_member_date"] == "UNKNOWN"
                and e["matrix"]["historical_known_at"] == "UNKNOWN"
                and e["matrix"]["formal_admission"] is False for e in events), "Unknowns promoted")
    require(sum(len(e["changes"]) for e in events) == 1008, "Candidate actions changed")
    event = next(e for e in events if e["matrix"]["notice_id"] == 13888)
    require(dict(Counter(c["action"] for c in event["changes"])) == {"ADD": 50, "REMOVE": 50},
            "13888 candidate counts changed")
    require(event["parser_details"]["reserves_excluded"] == 25, "Reserve treatment changed")
    baseline = load(phase + "baseline-result.json")
    require(baseline["verified_complete_baselines"] == 0
            and baseline["verified_members_from_authoritative_baseline"] == "UNKNOWN", "Baseline promoted")
    return {
        "public_copy_integrity": "PASS",
        "original_delivery_copies": 43,
        "migration_copies": 5,
        "publication_controls": len(manifest["publication_artifacts"]) + 1,
        "research_text_contracts_unchanged": len(release["protected_contracts"]),
        "python_syntax_checked": scripts,
        "absolute_local_path_scan": "NO_MATCHES",
        "limited_credential_patterns": "NO_MATCHES",
        "historical_statistical_reconciliation": "PASS_DERIVATIVES_ONLY",
        "private_original_byte_replay": "NOT_RUN_PRIVATE_ORIGINALS_NOT_PUBLISHED",
        "historical_actual_date_and_baseline_certification": "NOT_RUN_EVIDENCE_INCOMPLETE",
        "formal_admission": False,
        "no_live_money": True,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
