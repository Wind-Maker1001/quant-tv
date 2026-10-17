"""Public-copy adapter. Exact historical-byte replay is NOT_RUN.
See the publication manifest for the original implementation hash.
"""
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[4]
if __name__ == "__main__":
    checker = ROOT / "docs/research/evidence/pit-publication-20261018-v1/verify_publication.py"
    result = runpy.run_path(str(checker))["verify"]()
    result["historical_full_verifier"] = "NOT_RUN_PRIVATE_ORIGINAL_BYTES_AND_HISTORY_REQUIRED"
    print(json.dumps(result, ensure_ascii=False, indent=2))
