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
# Recognize roots independently of mount names; URLs and relative components
# (including globs, environment variables and redaction markers) are not roots.
NETWORK_URL = re.compile(
    r"\b(?!file:)[A-Za-z][A-Za-z0-9+.-]+:\x2f\x2f[^\s<>\"'`]*", re.I,
)
PRIVATE_PATH = re.compile(
    r"(?<![\w])[A-Za-z]:[\\/]+|(?<![\w\\])\\\\[\w.-]+\\"
    r"|(?<![\w.\x2f\\~>*%}-])\x2f[^\s<>\"'`|,;()\[\]{}]*"
)
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


def relative_expression(node):
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name) and node.func.id == "str" and len(node.args) == 1:
        return relative_expression(node.args[0])
    if isinstance(node.func, ast.Attribute):
        if node.func.attr == "relative_to":
            return True
        if node.func.attr == "replace" and len(node.args) == 2:
            if all(isinstance(arg, ast.Constant) for arg in node.args):
                if [arg.value for arg in node.args] == [chr(92), chr(47)]:
                    return relative_expression(node.func.value)
    return False


def python_path_text(text):
    # The historical assembler adds a slash-prefixed filename to a proven
    # relative_to(...) expression. Mask only that suffix's AST span; a generic
    # prefix + absolute_literal must still be rejected.
    spans = []
    relative_suffixes = set()
    tree = ast.parse(text)
    raw = text.encode("utf-8")
    starts = [0]
    for line in raw.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    for node in ast.walk(tree):
        if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
                and relative_expression(node.left) and isinstance(node.right, ast.Constant)
                and isinstance(node.right.value, str) and node.right.value.startswith(chr(47))):
            suffix = node.right
            relative_suffixes.add(id(suffix))
            spans.append((starts[suffix.lineno - 1] + suffix.col_offset,
                          starts[suffix.end_lineno - 1] + suffix.end_col_offset))
    for start, end in sorted(spans, reverse=True):
        raw = raw[:start] + b" " * (end - start) + raw[end:]
    # Decode Python string escapes as well, including escaped UNC paths. The
    # single slash used as a separator is not a machine path in source code.
    decoded = [node.value for node in ast.walk(tree)
               if isinstance(node, ast.Constant) and isinstance(node.value, str)
               and id(node) not in relative_suffixes and node.value != chr(47)]
    return raw.decode("utf-8") + "\n" + "\n".join(decoded)


def has_local_path(text):
    text = NETWORK_URL.sub("URL", text)
    for match in PRIVATE_PATH.finditer(text):
        if match.group() == chr(47):
            continue
        return True
    return text.strip(" \t\r\n\"'`") == chr(47)


def json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from json_strings(item)


def verify():
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    require(manifest["schema"] == "PIT_PUBLICATION_REDACTION_V1", "Unknown public-copy schema")
    require(manifest["formal_admission"] is False and manifest["no_live_money"] is True,
            "Admission boundary changed")
    require(len(manifest["files"]) == 48, "Expected 43 original and 5 migration copies")
    scripts = 0
    for item in manifest["files"] + manifest["publication_artifacts"]:
        raw = local(item["path"]).read_bytes()
        if item.get("public_hash_mode") == "LF_CANONICAL_TEXT":
            raw = raw.replace(b"\r\n", b"\n")
        require(hashlib.sha256(raw).hexdigest() == item["public_sha256"]
                and len(raw) == item["public_bytes"], "Public-copy hash mismatch: " + item["path"])
        text = raw.decode("utf-8")
        scan_text = python_path_text(text) if item["path"].endswith(".py") else text
        require(not has_local_path(scan_text),
                "Absolute local path in: " + item["path"])
        require(not any(pattern.search(text) for pattern in SECRET_PATTERNS),
                "Credential pattern in: " + item["path"])
        if item["path"].endswith(".json"):
            # JSON can escape both slashes and letters in a machine path.
            require(not any(has_local_path(value) for value in json_strings(json.loads(text))),
                    "Absolute local path in decoded JSON: " + item["path"])
        if item["path"].endswith(".py"):
            ast.parse(text, filename=item["path"])
            scripts += 1
    require(not any(has_local_path(value) for value in json_strings(manifest)),
            "Private path in public manifest")

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
