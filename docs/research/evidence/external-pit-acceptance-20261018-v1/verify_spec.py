"""Read-only delivery consistency checks, never a PIT admission validator.

No network, market-row decoding, research imports, publication or file writes.
Preservation hashing includes an existing 52 KB archived DAY and test fixtures.
Future real-evidence test cases in the accompanying plan remain NOT_RUN.
"""

import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def local_path(relative):
    path = (ROOT / relative).resolve()
    path.relative_to(ROOT)
    return path


def check_artifact(item):
    content = local_path(item["path"]).read_bytes()
    if hashlib.sha256(content).hexdigest() != item["sha256"]:
        raise ValueError("SHA-256 mismatch: " + item["path"])
    if len(content) != item["bytes"]:
        raise ValueError("Byte count mismatch: " + item["path"])


def find_function(tree, name):
    return next(node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == name)


def assigned_literal(function, name):
    for node in ast.walk(function):
        if (isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)):
            return ast.literal_eval(node.value)
    raise ValueError("Missing literal assignment: " + name)


def verify():
    manifest = read_json(HERE / "delivery-manifest.json")
    if manifest["schema"] != "EXTERNAL_PIT_SPEC_DELIVERY_V1":
        raise ValueError("Unexpected delivery schema")
    for item in manifest["artifacts"] + manifest["existing_evidence"]:
        check_artifact(item)
    before = read_json(HERE / "preservation-before.json")
    for item in before["files"]:
        check_artifact(item)

    shapes = manifest["contract_shapes"]
    for item in shapes["dataclasses"]:
        tree = ast.parse(local_path(item["path"]).read_text(encoding="utf-8"))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == item["name"])
        actual = [n.target.id for n in cls.body if isinstance(n, ast.AnnAssign)]
        if actual != item["fields"]:
            raise ValueError("Contract shape mismatch: " + item["name"])
    tree = ast.parse(local_path("qbot/research/data/market_qualification.py").read_text(encoding="utf-8"))
    roles = assigned_literal(find_function(tree, "_unbound_real_roles"), "roles")
    if list(roles) != shapes["unbound_real_roles"]:
        raise ValueError("Real source binding roles changed")
    review = assigned_literal(find_function(tree, "_reviews"), "required")
    if sorted(review) != shapes["independent_review_fields"]:
        raise ValueError("Independent review schema changed")

    phase1 = ROOT / "docs/research/evidence/pit-phase1-20261018-v1"
    candidates = read_json(phase1 / "candidate-events.json")
    events = candidates["events"]
    if (len(events) != 14 or candidates["formal_admission"] is not False
            or candidates["daily_members_generated"] is not False
            or candidates["chain_completeness"] != "UNKNOWN"):
        raise ValueError("Candidate scope differs from specification")
    for event in events:
        matrix = event["matrix"]
        if (matrix["actual_effective_member_date"] != "UNKNOWN"
                or matrix["historical_known_at"] != "UNKNOWN"
                or matrix["formal_admission"] is not False):
            raise ValueError("Candidate uncertainty changed; re-review the specification")
    event = next(e for e in events if e["matrix"]["notice_id"] == 13888)
    matrix = event["matrix"]
    expected = manifest["event_13888_expected"]
    for field, value in expected.items():
        if matrix[field] != value:
            raise ValueError("13888 metadata differs: " + field)
    actions = Counter(row["action"] for row in event["changes"])
    if dict(actions) != {"ADD": 50, "REMOVE": 50}:
        raise ValueError("13888 candidate action counts differ")
    adds = {r["symbol"] for r in event["changes"] if r["action"] == "ADD"}
    removes = {r["symbol"] for r in event["changes"] if r["action"] == "REMOVE"}
    if len(adds) != 50 or len(removes) != 50 or adds.intersection(removes):
        raise ValueError("13888 candidate actions overlap or duplicate")
    if event["parser_details"]["reserves_excluded"] != 25:
        raise ValueError("Reserve exclusion differs")
    identity = read_json(phase1 / "identity-mapping-proposal.json")
    if (identity["formal_identity_snapshot_eligible"] is not False
            or identity["transition"]["first_historically_known_at"] != "UNKNOWN"
            or identity["transition"]["source_stated_code_change_date"] != "2025-02-17"):
        raise ValueError("Identity proposal scope changed")

    local_links = 0
    for relative in manifest["documents"]:
        path = local_path(relative)
        content = path.read_text(encoding="utf-8")
        for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", content):
            if target.startswith(("https://", "http://", "#")):
                continue
            target = target.split("#", 1)[0]
            resolved = (path.parent / target).resolve()
            resolved.relative_to(ROOT)
            if not resolved.exists():
                raise ValueError("Broken local document reference: " + target)
            local_links += 1

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True).strip()
    diff = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=str(ROOT), text=True)
    if head != before["head"] or diff != before["tracked_diff_before"] or diff:
        raise ValueError("Repository head or tracked files changed")
    return {
        "schema": "EXTERNAL_PIT_SPEC_VERIFICATION_V1",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "protected_existing_files_unchanged": len(before["files"]),
        "delivery_artifacts_checked": len(manifest["artifacts"]),
        "reused_original_evidence_checked": len(manifest["existing_evidence"]),
        "contract_shapes_checked": len(shapes["dataclasses"]),
        "source_binding_roles_unchanged": list(roles),
        "local_document_links_checked": local_links,
        "candidate_events_still_unverified": 14,
        "event_13888_candidate_actions": dict(actions),
        "event_13888_reserves_excluded": 25,
        "event_13888_actual_boundary_and_vintage": "UNKNOWN",
        "real_baseline_acceptance": "NOT_RUN_BASELINE_NOT_OBTAINED",
        "real_before_after_set_difference": "NOT_RUN_INDEPENDENT_SNAPSHOTS_NOT_OBTAINED",
        "real_identity_sample_acceptance": "NOT_RUN_IDENTITY_CONTRACT_INCOMPLETE",
        "planned_negative_cases_execution": "NOT_RUN_DESIGN_ONLY",
        "tracked_diff_empty": True,
        "no_live_money": True,
        "financial_certification": False,
        "formal_admission": False,
        "scope": "Read-only document, contract-shape, candidate metadata and byte-binding consistency only",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
