"""Read-only adapter for the one previously authorized frozen 50-stock dataset."""

from pathlib import Path

import pandas as pd

from qbot.research.exploratory.contract import ExploratoryContractError, load_dataset
from qbot.research.exploratory.runner import verify_receipt as verify_previous_receipt

from .receipts import file_sha256

DATA_VERSION = "2f145d173f5ddc79d303f580bc4485241023ae3971d3b40a2e8fa6e3de2e3f5f"
MANIFEST_SHA256 = "c1aef73620bb34f43e1553aa196dcd35fd11eb2abfb34c842b7ff59c5a9b8ced"


def load_private_inputs(manifest_path=None, frozen_receipt_path=None):
    """Return status plus inputs; absent real evidence is never synthetic success."""
    if manifest_path is None or not Path(manifest_path).is_file():
        return "NOT_RUN", None, "authorized frozen private manifest absent"
    if frozen_receipt_path is None or not Path(frozen_receipt_path).is_file():
        return "BLOCKED", None, "frozen label receipt absent"
    try:
        if file_sha256(manifest_path) != MANIFEST_SHA256:
            raise ExploratoryContractError("frozen manifest byte hash mismatch")
        bars, benchmark, calendar, manifest = load_dataset(
            manifest_path, allow_synthetic=False
        )
        if (
            manifest["data_version"] != DATA_VERSION
            or len(manifest["sample"]["symbols"]) != 50
        ):
            raise ExploratoryContractError("frozen version/sample contract mismatch")
        previous = verify_previous_receipt(frozen_receipt_path)
        if (
            previous.get("status") != "SUCCESS"
            or previous.get("data_version") != DATA_VERSION
            or previous.get("data_files") != manifest["files"]
        ):
            raise ExploratoryContractError("frozen receipt input binding mismatch")
        derived = Path(frozen_receipt_path).parent / "derived_factor_labels.parquet"
        if previous["artifacts"].get(derived.name) != file_sha256(derived):
            raise ExploratoryContractError("frozen historical labels hash mismatch")
        frozen = pd.read_parquet(derived)
        required = ["date", "symbol", "entry_date", "exit_date", "EXCESS_RET5"]
        if not set(required).issubset(frozen):
            raise ExploratoryContractError("frozen labels lack explicit dates")
        labels = frozen[required].copy()
        evidence = {
            "classification": "EXPLORATORY / UNVERIFIED / NON_PIT_CONVENIENCE",
            "synthetic_only": False,
            "data_version": DATA_VERSION,
            "manifest_sha256": MANIFEST_SHA256,
            "source_version": manifest["source_version"],
            "verified_source_artifacts": len(manifest["sources"]),
            "input_sha256": {
                key: item["sha256"] for key, item in manifest["files"].items()
            },
            "frozen_label_file_sha256": file_sha256(derived),
            "previously_observed_sample": True,
            "formal_admission": False,
        }
        return (
            "SUCCESS",
            (
                bars,
                benchmark,
                calendar,
                labels,
                evidence,
                manifest["sample"]["symbols"],
            ),
            "all frozen private hashes/contracts verified",
        )
    except (ExploratoryContractError, OSError, ValueError, KeyError) as exc:
        return "BLOCKED", None, "private frozen contract failed: " + str(exc)
