"""Independent Git-object V2 calculator. Imports no FactorLab implementation.

python recompute_canonical.py --repository <repo> --revision 4bec2ef --output <json>
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    def git(*parts):
        return subprocess.check_output(["git", "-C", str(args.repository), *parts])

    revision = git("rev-parse", args.revision + "^{commit}").decode("ascii").strip()
    records = []
    for entry in git("ls-tree", "-rz", revision, "--", "qbot/research").split(b"\0"):
        if not entry:
            continue
        header, path = entry.split(b"\t", 1)
        if not path.lower().endswith(b".py"):
            continue
        mode, kind, oid = header.split()
        if mode not in (b"100644", b"100755") or kind != b"blob":
            raise ValueError("non-regular Python source")
        raw = git("cat-file", "blob", oid.decode("ascii"))
        raw.decode("utf-8")
        content = raw.replace(b"\r\n", b"\n")
        if b"\r" in content:
            raise ValueError("lone CR")
        records.append({"path": path.decode("utf-8"), "bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest()})
    payload = {
        "protocol": "factorlab-model-readiness-source-v2",
        "scope": "Git-tracked regular Python files (*.py, ASCII case-insensitive) recursively under qbot/research",
        "normalization": "UTF-8 bytes; CRLF -> LF only; reject lone CR; preserve all other bytes",
        "files": sorted(records, key=lambda item: item["path"].encode("utf-8")),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    result = {"classification": "INDEPENDENT_GIT_OBJECT_REFERENCE_NOT_A_MODEL_RUN",
              "source_commit": revision, "canonical_sha256": hashlib.sha256(encoded).hexdigest(),
              "canonical_payload": payload}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(result["source_commit"], len(records), result["canonical_sha256"])


if __name__ == "__main__":
    main()
