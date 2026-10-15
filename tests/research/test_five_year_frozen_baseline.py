"""Offline safeguard: this data audit must not rewrite prior research evidence."""

import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "docs/research/evidence/five-year-data-feasibility-v1/frozen-baseline.json"


def test_original_research_evidence_and_factor_parameters_are_frozen():
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    baseline = frozen["baseline_commit"]
    assert baseline == "6864315bc8eeaf96356d6822d12f431ec485a94e"
    assert len(frozen["factors"]) == 14 and frozen["unique_candidate_expressions"] == 39
    assert frozen["candidate_configuration"]["max_panel_rows"] == 250000
    entries = frozen["files"]
    assert len(entries) == frozen["frozen_file_count"] == 470
    protected = {item["path"] for item in entries}
    tree = subprocess.check_output(["git", "ls-tree", "-r", baseline], cwd=ROOT, encoding="utf-8")
    blobs = {line.split("\t", 1)[1]: line.split("\t", 1)[0].split()[2] for line in tree.splitlines()}
    for item in entries:
        assert blobs[item["path"]] == item["baseline_git_blob_sha1"]
    changed = subprocess.check_output(["git", "-c", "core.quotepath=false", "diff", "--name-only", baseline],
                                      cwd=ROOT, encoding="utf-8").splitlines()
    assert not protected.intersection(changed), "prior research/Gates/Golden evidence changed"
