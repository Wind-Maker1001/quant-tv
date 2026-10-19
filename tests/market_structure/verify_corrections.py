"""Seal V2 evidence without changing V1; run explicitly from a Python 3.9 worktree."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

from qbot.research.exploratory.market_structure.contracts import MARKERS, json_bytes
from qbot.research.exploratory.market_structure.runner import verify_receipt

ROOT = Path(__file__).resolve().parents[2]
REVIEWED = "b30256dd9e24c3db99be5d63d4b3b4d9113b0872"
PREFIXES = (
    "qbot/research/exploratory/market_structure/",
    "tests/market_structure/",
    "docs/research/market_structure/",
)
V1 = "docs/research/market_structure/evidence/v1/"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def junit(path):
    suites = list(ET.parse(path).getroot().iter("testsuite"))
    counts = {
        key: sum(int(s.attrib[key]) for s in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }
    cases = {
        (c.attrib["classname"], c.attrib["name"])
        for c in ET.parse(path).getroot().iter("testcase")
    }
    return counts, cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    artifacts = args.artifacts.resolve()
    target = ROOT / "docs/research/market_structure/evidence/v2"
    if target.exists():
        raise ValueError("fresh V2 directory required; never overwrite evidence")
    preserved = {}
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", REVIEWED, "--", V1],
        cwd=ROOT,
        text=True,
    ).splitlines()
    for name in paths:
        old = subprocess.check_output(["git", "show", REVIEWED + ":" + name], cwd=ROOT)
        expected = hashlib.sha256(old).hexdigest()
        if sha(ROOT / name) != expected:
            raise ValueError("V1 evidence changed: " + name)
        preserved[name] = expected
    changed = subprocess.check_output(
        ["git", "diff", REVIEWED, "--name-only"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    if any(not p.startswith(PREFIXES) or p.startswith(V1) for p in changed):
        raise ValueError("protected path changed")
    red, _ = junit(artifacts / "red/red-tests.xml")
    if red != dict(tests=3, failures=3, errors=0, skipped=0):
        raise ValueError("three independent red counterexamples required")
    red_receipt = read(artifacts / "red/red-receipt.json")
    if red_receipt["product_head"] != REVIEWED or red_receipt["exit_code"] != 1:
        raise ValueError("red execution subject/outcome mismatch")
    for name, expected in red_receipt["product_source_sha256"].items():
        old = subprocess.check_output(["git", "show", REVIEWED + ":" + name], cwd=ROOT)
        if hashlib.sha256(old).hexdigest() != expected:
            raise ValueError("red product source mismatch")
    if (
        sha(ROOT / "tests/market_structure/test_review_red_cases.py")
        != red_receipt["test_source_sha256"]
    ):
        raise ValueError("minimal red counterexamples changed")
    counts, cases = junit(artifacts / "new-tests.xml")
    _, old_cases = junit(ROOT / V1 / "new-tests.xml")
    if not old_cases.issubset(cases) or len(old_cases) != 55:
        raise ValueError("all original 55 independent tests must run")
    if counts["tests"] != len(cases) or any(
        counts[k] for k in ("failures", "errors", "skipped")
    ):
        raise ValueError("all independent tests must execute and pass")
    targeted, _ = junit(artifacts / "targeted-tests.xml")
    if targeted["tests"] < 3 or any(
        targeted[k] for k in ("failures", "errors", "skipped")
    ):
        raise ValueError("targeted regression execution did not pass")
    coverage = read(artifacts / "coverage.json")
    expected = {
        p.relative_to(ROOT).as_posix() for p in (ROOT / PREFIXES[0]).glob("*.py")
    }
    actual = {k.replace("\\", "/") for k in coverage["files"]}
    xml_files = {
        PREFIXES[0] + c.attrib["filename"].split("market_structure/")[-1]
        for c in ET.parse(artifacts / "coverage.xml").getroot().findall(".//class")
    }
    if actual != expected or xml_files != expected:
        raise ValueError("coverage XML/JSON must include every new source")
    for name in ("new-tests-command.json", "static.json", "source-cli.json"):
        if read(artifacts / name)["exit_code"] != 0:
            raise ValueError("failed explicit execution: " + name)
    receipt = verify_receipt(artifacts / "synthetic")
    if set(receipt["frequencies"]) != {5, 15, 30}:
        raise ValueError("three frequencies required")
    states = pd.read_csv(artifacts / "synthetic/contract_status.csv")
    if (
        len(states) != 32
        or states.implementation_status.eq("IMPLEMENTED_SYNTHETIC").sum() != 14
    ):
        raise ValueError("32 contracts and 14 implementations required")
    old_receipt = read(ROOT / V1 / "synthetic/receipt.json")
    replay = read(artifacts / "v1-replay.json")
    if (
        replay["status"] != "EXACT_V1_REPLAY_MATCH"
        or replay["source_commit"] != REVIEWED
        or replay["v1_receipt_sha256"] != sha(ROOT / V1 / "synthetic/receipt.json")
        or replay["full_value_sha256"] != old_receipt["output_value_sha256"]
        or replay["numeric_value_sha256"] != receipt["numeric_value_sha256"]
    ):
        raise ValueError("V1 replay / V2 numeric comparison mismatch")
    old = pd.read_csv(ROOT / V1 / "synthetic/redundancy_windows.csv")
    new = pd.read_csv(artifacts / "synthetic/redundancy_windows.csv")
    keys = [
        "scenario",
        "frequency",
        "grain",
        "namespace",
        "observation_end",
        "left",
        "right",
    ]
    pairs = old.merge(
        new,
        on=keys,
        suffixes=("_v1", "_v2"),
        validate="one_to_one",
        how="outer",
        indicator=True,
    )
    if not pairs._merge.eq("both").all():
        raise ValueError("diagnostic window inventory changed unexpectedly")
    difference = ~np.isclose(
        pairs.spearman_v1, pairs.spearman_v2, atol=1e-12, rtol=0, equal_nan=True
    )
    comparison = dict(
        v1_output_value_sha256=old_receipt["output_value_sha256"],
        v2_output_value_sha256=receipt["output_value_sha256"],
        numeric_values_equal=True,
        numeric_value_sha256=receipt["numeric_value_sha256"],
        v1_catalog_sha256=old_receipt["catalog_sha256"],
        v2_catalog_sha256=receipt["catalog_sha256"],
        diagnostic_windows=len(pairs),
        changed_spearman_windows=int(difference.sum()),
        reason="Pairwise-complete Spearman ranks; precise required_inputs; feature/context input hashes separated. V1 bytes retained.",
    )
    target.mkdir(parents=True)
    shutil.copytree(artifacts / "red", target / "red")
    shutil.copytree(artifacts / "synthetic", target / "synthetic")
    for name in (
        "new-tests.xml",
        "new-tests.log",
        "new-tests-command.json",
        "targeted-tests.xml",
        "coverage.json",
        "coverage.xml",
        "static.json",
        "static.log",
        "source-cli.json",
        "source-cli.log",
        "v1-replay.json",
        "comparison-command.json",
    ):
        shutil.copyfile(artifacts / name, target / name)
    (target / "v1-preservation.json").write_bytes(json_bytes(preserved))
    (target / "v1-v2-comparison.json").write_bytes(json_bytes(comparison))
    inventory = {
        k.replace("\\", "/"): dict(source_sha256=sha(ROOT / k), **v["summary"])
        for k, v in coverage["files"].items()
    }
    (target / "coverage-source-inventory.json").write_bytes(json_bytes(inventory))
    acceptance = dict(
        **MARKERS,
        software_status="SOFTWARE_MVP_SUCCESS",
        real_research_status="REAL_RESEARCH_BLOCKED",
        formal_status="BLOCKED",
        forward_status="BLOCKED",
        installation_package_status="NOT_VALIDATED",
        reviewed_commit=REVIEWED,
        implementation_commit=receipt["tested_commit"],
        python=sys.version,
        independent_tests=counts,
        original_tests_preserved=55,
        targeted_tests=targeted,
        red_tests=red,
        coverage=coverage["totals"],
        coverage_inventory_verified=True,
        candidate_count=32,
        implemented_count=14,
        frequencies=[5, 15, 30],
        v1_preserved=True,
        comparison=comparison,
        external_ci_and_review="PENDING_FINAL_HEAD; recorded separately on PR #13",
        corrections={"P2-1": 4310212806, "P2-2": 4310212810, "P2-3": 4310212817},
    )
    (target / "acceptance.json").write_bytes(json_bytes(acceptance))
    manifest = {}
    for prefix in PREFIXES:
        for path in sorted((ROOT / prefix).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                manifest[path.relative_to(ROOT).as_posix()] = sha(path)
    manifest_path = target / "delivery-manifest.json"
    manifest_path.write_bytes(
        json_bytes(
            dict(
                files=manifest,
                self_hash_policy="excludes itself; SHA256 reported separately",
            )
        )
    )
    print(
        json.dumps(
            dict(
                manifest_sha256=sha(manifest_path), tests=counts, comparison=comparison
            )
        )
    )


if __name__ == "__main__":
    main()
