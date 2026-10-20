"""Exact authorized P0 postimages; historical freezes remain immutable.

This revision changes financial admission, not factor/model/statistical logic.
Any further source change requires a new reviewed receipt rather than growing
an exception based on whatever happens to be in the working tree.
"""

import copy
import hashlib
import json
from pathlib import Path
import subprocess


BASE = "657486f8ca928c1e66b430f471cfe5ce96a613ab"
RECEIPT = "docs/research/evidence/unified-market-admission-v1/security-revision.json"
RECEIPT_SHA256 = "4c7ce29bfab736b953470dd2b9ffe5e49c3abcbb2189486ec03208fbabc93b34"
FILES = frozenset(
    (
        "qbot/research/cli.py",
        "qbot/research/data/providers/base.py",
        "qbot/research/data/providers/local.py",
        "qbot/research/data/admission.py",
        "tests/conftest.py",
        "tests/research/test_cli_phase2.py",
        "tests/research/test_cli_forward_evaluation.py",
        "tests/model_readiness/test_comparison_contract.py",
        "tests/market_admission/test_admission.py",
        ".github/scripts/ci/frozen_engineering_migration.py",
        ".github/scripts/ci/validate_execution.py",
        "tests/research/test_five_year_frozen_baseline.py",
        "tests/market_structure/test_delivery.py",
        "examples/research/review_yhh30m_release.py",
        "tests/market_admission/test_revision_contract.py",
    )
)
COVERAGE_FILES = frozenset(
    name.removeprefix("qbot/research/")
    for name in FILES
    if name.startswith("qbot/research/")
)


def blob(root, name):
    return subprocess.check_output(
        ["git", "hash-object", "--path=" + name, name], cwd=root, text=True
    ).strip()


def load_revision(root):
    root = Path(root)
    receipt = root / RECEIPT
    if not receipt.exists():
        return None
    content = receipt.read_bytes()
    if hashlib.sha256(content).hexdigest() != RECEIPT_SHA256:
        raise ValueError("Security admission receipt digest changed")
    revision = json.loads(content)
    if (
        set(revision) != {"schema", "base_commit", "files", "coverage_valid_lines"}
        or revision["schema"] != "FACTORLAB_SECURITY_ADMISSION_REVISION_V1"
        or revision["base_commit"] != BASE
        or set(revision["files"]) != FILES
        or set(revision["coverage_valid_lines"]) != COVERAGE_FILES
    ):
        raise ValueError("Security admission revision scope changed")
    for name, item in revision["files"].items():
        original = subprocess.run(
            ["git", "rev-parse", "--verify", BASE + ":" + name],
            cwd=root,
            text=True,
            capture_output=True,
        )
        before = original.stdout.strip() if original.returncode == 0 else None
        if (
            set(item) != {"before_blob", "approved_blob"}
            or item["before_blob"] != before
        ):
            raise ValueError("Security admission preimage changed: " + name)
        if blob(root, name) != item["approved_blob"]:
            raise ValueError("Unregistered security admission bytes: " + name)
    return revision


def coverage_contract(root, expected):
    """Replace only exact approved executable-line inventories, never outcomes."""
    revision = load_revision(root)
    if revision is None:
        return expected
    result = copy.deepcopy(expected)
    for contract in result["execution_by_platform"].values():
        contract["coverage_valid_lines"].update(revision["coverage_valid_lines"])
    return result
