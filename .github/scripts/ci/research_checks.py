"""Read-only Python 3.9 research checks; not a full Pylint analysis."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SCOPES = ("qbot/research", "tests/research", "examples/research", ".github/scripts/ci")


def git(root, *arguments):
    return subprocess.check_output(
        ["git", *arguments], cwd=root, text=True, encoding="utf-8"
    ).strip()


def resolve_base(root, event_name, pr_base="", push_before=""):
    """Use the event's advertised baseline, with an explicit first-push fallback."""
    candidate = pr_base if event_name == "pull_request" else push_before
    if candidate and candidate != "0" * 40:
        if not re.fullmatch(r"[0-9a-f]{40}", candidate):
            raise ValueError("Event baseline must be a full commit SHA")
        git(root, "rev-parse", "--verify", candidate + "^{commit}")
    else:
        candidate = "origin/main"
        git(root, "rev-parse", "--verify", candidate + "^{commit}")
    return git(root, "merge-base", candidate, "HEAD")


def check_whitespace(root, base, scopes):
    # Frozen references deliberately retain CRLF bytes. Recognize the line
    # ending while still rejecting trailing spaces and the other default rules.
    subprocess.run(
        [
            "git",
            "-c",
            "core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol",
            "diff",
            "--check",
            "--ignore-submodules",
            base,
            "HEAD",
            "--",
            *scopes,
        ],
        cwd=root,
        check=True,
    )


def main():
    if sys.version_info[:2] != (3, 9):
        raise RuntimeError("Research syntax checks require Python 3.9")
    base = resolve_base(
        ROOT,
        os.environ.get("GITHUB_EVENT_NAME", "workflow_dispatch"),
        os.environ.get("PR_BASE_SHA", ""),
        os.environ.get("PUSH_BEFORE_SHA", ""),
    )
    files = sorted(path for scope in SCOPES for path in (ROOT / scope).rglob("*.py"))
    for path in files:
        compile(path.read_bytes(), str(path), "exec")
    subprocess.run(
        [sys.executable, "-m", "flake8", "--select=E9,F63,F7,F82", *SCOPES],
        cwd=ROOT,
        check=True,
    )
    check_whitespace(ROOT, base, SCOPES)
    print(
        json.dumps(
            {
                "base": base,
                "compiled_python_files": len(files),
                "static_rules": "flake8 E9,F63,F7,F82",
                "scopes": SCOPES,
                "modifies_source": False,
                "full_pylint_analysis": False,
            }
        )
    )


if __name__ == "__main__":
    main()
