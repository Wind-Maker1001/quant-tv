"""Synthetic contract failures are isolated from real research CI evidence."""

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from benchmark import write_json
from validate_execution import load, validate


class ExecutionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sandbox = tempfile.TemporaryDirectory()
        cls.root = Path(cls.sandbox.name)
        subject = cls.root / "subject"
        (subject / "tests/research").mkdir(parents=True)
        (subject / "tests/research/test_synthetic_contract.py").write_text(
            "import pytest\n"
            '@pytest.mark.parametrize("value", [1], ids=["nested::[id]"])\n'
            "def test_actual_call(value):\n    assert value == 1\n"
            '@pytest.mark.skip(reason="synthetic contract skip")\n'
            "def test_actual_skip():\n    raise AssertionError\n"
            "@pytest.mark.network\n"
            "def test_deselected_network():\n    raise AssertionError\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "init", "-q", str(subject)], check=True)
        subprocess.run(["git", "add", "."], cwd=subject, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Synthetic CI contract",
                "-c",
                "user.email=ci@example.invalid",
                "commit",
                "-qm",
                "synthetic fixture",
            ],
            cwd=subject,
            check=True,
            stdout=subprocess.PIPE,
        )
        cls.original = cls.root / "actual-synthetic-execution"
        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("benchmark.py")),
                "--no-coverage",
                "--output",
                str(cls.original),
            ],
            cwd=subject,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        result = load(cls.original / "result.json")
        cls.expected = {key: value for key, value in result.items() if "_ids_" in key}

    @classmethod
    def tearDownClass(cls):
        cls.sandbox.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name) / "copied-synthetic-evidence"
        shutil.copytree(self.original, self.directory)

    def tearDown(self):
        self.temporary.cleanup()

    def mutate(self, filename, mutation):
        path = self.directory / filename
        value = load(path)
        mutation(value)
        write_json(path, value)

    def reject(self):
        with self.assertRaises((ValueError, FileNotFoundError, ET.ParseError)):
            validate(self.directory, self.expected)

    def test_real_observer_and_junit_agree_on_nested_parameter_ids(self):
        result = validate(self.directory, self.expected)
        self.assertEqual(
            (result["passed"], result["skipped"], result["deselected"]), (1, 1, 1)
        )

    def test_pytest_failure_cannot_be_relabelled(self):
        self.mutate("result.json", lambda value: value.update(exit_code=1))
        self.reject()

    def test_worker_crash_is_a_failure(self):
        self.mutate(
            "pytest-controller.json",
            lambda value: value["worker_errors"].append(
                {"worker": "gw0", "error": "crashed"}
            ),
        )
        self.reject()

    def test_missing_worker_evidence_fails(self):
        self.mutate("environment.json", lambda value: value.update(workers=2))
        self.reject()

    def test_different_frozen_collection_fails(self):
        self.mutate(
            "pytest-controller.json",
            lambda value: value["all_ids"].append(
                "tests/research/test_omitted.py::test_missing"
            ),
        )
        self.reject()

    def test_missing_execution_fails(self):
        def remove(value):
            nodeid = value["reports"][0]["nodeid"]
            value["reports"] = [
                row for row in value["reports"] if row["nodeid"] != nodeid
            ]

        self.mutate("pytest-controller.json", remove)
        self.reject()

    def test_duplicate_execution_fails(self):
        self.mutate(
            "pytest-controller.json",
            lambda value: value["reports"].append(copy.deepcopy(value["reports"][0])),
        )
        self.reject()

    def test_a_failed_test_phase_fails(self):
        self.mutate(
            "pytest-controller.json",
            lambda value: value["reports"][0].update(outcome="failed"),
        )
        self.reject()

    def test_missing_junit_fails(self):
        (self.directory / "research.xml").unlink()
        self.reject()

    def test_damaged_junit_fails(self):
        (self.directory / "research.xml").write_text("<broken", encoding="utf-8")
        self.reject()

    def test_duplicate_junit_case_fails(self):
        path = self.directory / "research.xml"
        root = ET.parse(path)
        suite = root.getroot().find("testsuite")
        suite.append(copy.deepcopy(suite.find("testcase")))
        root.write(path)
        self.reject()

    def test_false_junit_totals_fail(self):
        path = self.directory / "research.xml"
        root = ET.parse(path)
        root.getroot().find("testsuite").set("tests", "9000")
        root.write(path)
        self.reject()

    def test_collection_receipt_tampering_fails(self):
        (self.directory / "selected_ids.txt").write_bytes(b"placeholder\n")
        self.reject()

    def test_collection_only_is_not_acceptance(self):
        self.mutate("environment.json", lambda value: value.update(collect_only=True))
        self.reject()

    def test_missing_coverage_fails(self):
        self.mutate("environment.json", lambda value: value.update(coverage=True))
        self.reject()


if __name__ == "__main__":
    unittest.main()
