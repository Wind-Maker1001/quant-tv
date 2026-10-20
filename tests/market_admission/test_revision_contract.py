"""P0 authorization changes exact bytes, never the historical test outcomes."""

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "security_admission_contract", ROOT / ".github/scripts/ci/security_admission_revision.py"
)
security = importlib.util.module_from_spec(spec)
spec.loader.exec_module(security)


@pytest.fixture
def revision_clone(tmp_path):
    root = tmp_path / "clone"
    subprocess.check_call(
        ["git", "clone", "--shared", "--no-checkout", str(ROOT), str(root)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for name in security.FILES | {security.RECEIPT, ".gitattributes"}:
        source = ROOT / name
        if source.is_file():
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    return root


def test_revision_preserves_all_legacy_collection_and_outcome_requirements():
    expected = json.loads((ROOT / "docs/research/evidence/ci-runtime-optimization-v1/baseline-collection.json").read_text())
    original = copy.deepcopy(expected)
    adjusted = security.coverage_contract(ROOT, expected)
    assert expected == original
    assert adjusted.keys() == expected.keys()
    for key in expected.keys() - {"execution_by_platform"}:
        assert adjusted[key] == expected[key]
    for family, contract in expected["execution_by_platform"].items():
        for key in contract.keys() - {"coverage_valid_lines"}:
            assert adjusted["execution_by_platform"][family][key] == contract[key]
        current = adjusted["execution_by_platform"][family]["coverage_valid_lines"]
        for name in set(contract["coverage_valid_lines"]) - security.COVERAGE_FILES:
            assert current[name] == contract["coverage_valid_lines"][name]
    assert security.load_revision(ROOT)["base_commit"] == security.BASE


@pytest.mark.parametrize("name", sorted(security.FILES))
def test_every_authorized_file_still_rejects_unregistered_bytes(revision_clone, name):
    path = revision_clone / name
    path.write_bytes(path.read_bytes() + b"\n# unregistered security change\n")
    with pytest.raises(ValueError, match="Unregistered security admission bytes"):
        security.load_revision(revision_clone)


@pytest.mark.parametrize("mutation", ["source_scope", "coverage", "base", "postimage"])
def test_rewriting_the_receipt_cannot_self_authorize_changes(revision_clone, mutation):
    path = revision_clone / security.RECEIPT
    payload = json.loads(path.read_bytes())
    if mutation == "source_scope":
        payload["files"]["qbot/research/factors/registry.py"] = {}
    elif mutation == "coverage":
        payload["coverage_valid_lines"] = {}
    elif mutation == "base":
        payload["base_commit"] = "0" * 40
    else:
        payload["files"]["qbot/research/cli.py"]["approved_blob"] = "0" * 40
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="receipt digest changed"):
        security.load_revision(revision_clone)
