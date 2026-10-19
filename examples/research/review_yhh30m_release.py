"""Inspect the full release diff for raw artifacts, secrets and machine paths."""

import argparse
import ast
from collections import Counter
import csv
import io
import json
from pathlib import Path
import re
import subprocess


URL = re.compile(r"\b(?!file:)[A-Za-z][A-Za-z0-9+.-]*:\x2f\x2f[^\s<>\"'`]*", re.I)
ABS = re.compile(r"(?<![\w])[A-Za-z]:[\\/][^\s\"'<>\[\](){}]+|(?<![\w\\])\\\\[\w.-]+\\[^\s\"'<>\[\](){}]+"
                 r"|(?<![\w.\x2f\\~>*%}-])\x2f[^\s\"'<>\[\](){}|,;]+")
SECRET = re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
GATES = ("qbot/research/data/schema.py", "qbot/research/data/providers/local.py",
         "qbot/research/data/market_qualification.py", "qbot/research/forward/", "qbot/research/config/",
         ".github/workflows/research-tests.yml")


def strings(value, context=""):
    if isinstance(value, str):
        yield context, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield context + "|KEY", key
            yield from strings(item, context + "|" + key)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item, context)


def review(repo, base):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, text=True).splitlines()
    files = sorted(set(git("diff", "--name-only", base)) | set(git("ls-files", "--others", "--exclude-standard")))
    blocked, fixture_vectors = [], Counter()
    prefixes = [str(Path.home()).replace(chr(92), chr(47)).lower(),
                str(repo.parent).replace(chr(92), chr(47)).lower()]
    sizes = {}
    literal_cache = {}
    for name in files:
        path = repo / name
        if not path.exists():
            continue
        sizes[name] = path.stat().st_size
        if path.suffix.lower() in {".parquet", ".zip", ".xlsx", ".bin", ".pkl", ".pyc"} or sizes[name] > 2_000_000:
            blocked.append({"file": name, "reason": "RAW_OR_LARGE_ARTIFACT"})
            continue
        text = path.read_text(encoding="utf-8-sig")
        if SECRET.search(text):
            blocked.append({"file": name, "reason": "SECRET_SHAPED_VALUE"})
        if path.suffix == ".csv":
            header = next(csv.reader(io.StringIO(text)))
            if any(c in header for c in ("open", "close", "volume_vendor", "开盘价（元）", "分钟时间")):
                blocked.append({"file": name, "reason": "RAW_MARKET_CSV_COLUMNS"})
        if path.suffix == ".json":
            entries = list(strings(json.loads(text)))
        elif path.suffix == ".py":
            tree = ast.parse(text)
            suffixes = set()
            # A single filename appended to the explicit relative evidence/
            # prefix and a Path.name is a relative fragment, not a local root.
            for node in ast.walk(tree):
                if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add) and
                        isinstance(node.right, ast.Constant) and isinstance(node.right.value, str) and
                        re.fullmatch(chr(47) + r"[A-Za-z0-9_.-]+", node.right.value) and
                        isinstance(node.left, ast.BinOp) and isinstance(node.left.op, ast.Add) and
                        isinstance(node.left.left, ast.Constant) and node.left.left.value == "evidence" + chr(47) and
                        isinstance(node.left.right, ast.Attribute) and node.left.right.attr == "name"):
                    suffixes.add(id(node.right))
            entries = [("PYTHON_STRING", n.value) for n in ast.walk(tree)
                       if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in suffixes]
        else:
            entries = [("TEXT", text)]
        for context, value in entries:
            value = URL.sub("REMOTE_URL", value)
            for match in ABS.finditer(value):
                token = match.group()
                if token == chr(47):
                    continue
                normalized = token.replace(chr(92), chr(47)).lower()
                if any(normalized.startswith(prefix) for prefix in prefixes):
                    blocked.append({"file": name, "reason": "MACHINE_PATH"})
                    continue
                historical_case = (name.endswith("yhh30m-conversion-v1/verification.json") and
                                   context.endswith("|KEY") and "resolved_case_statuses" in context and
                                   value.startswith("tests.research."))
                if historical_case:
                    if token not in literal_cache:
                        result = subprocess.run(["git", "grep", "-F", "-e", token, base, "--", "tests", "qbot", "examples"],
                                                cwd=repo, capture_output=True, text=True)
                        literal_cache[token] = result.returncode == 0
                    if literal_cache[token]:
                        fixture_vectors[name] += 1
                        continue
                blocked.append({"file": name, "reason": "UNEXPLAINED_ABSOLUTE_PATH", "context": context.split("|")[0]})
    gate_changes = [name for name in files if any(name == gate or name.startswith(gate) for gate in GATES)]
    return {"schema": "YHH_RELEASE_DIFF_REVIEW_V1", "base_commit": git("rev-parse", base)[0],
            "head_commit": git("rev-parse", "HEAD")[0], "changed_files": files, "file_bytes": sizes,
            "total_bytes": sum(sizes.values()), "blocked_findings": blocked, "protected_gate_changes": gate_changes,
            "historical_test_vectors_defined_in_main": dict(fixture_vectors),
            "status": "PASS" if not blocked and not gate_changes else "FAIL"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="origin/main")
    args = parser.parse_args()
    result = review(args.repo.resolve(), args.base)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
