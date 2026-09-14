"""Reproducible run manifests for every FactorLab CLI invocation."""

import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional
import uuid

import numpy as np

from qbot.research.config import ResearchConfig


TRACKED_PACKAGES = (
    "numpy",
    "pandas",
    "pyarrow",
    "scipy",
    "scikit-learn",
    "matplotlib",
    "akshare",
    "baostock",
    "PyYAML",
    "pytest",
)


def set_random_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def git_commit(repo_root: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


def package_versions(names: Iterable[str] = TRACKED_PACKAGES) -> Dict[str, Optional[str]]:
    versions: Dict[str, Optional[str]] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def _atomic_json(payload: Dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(".%s.tmp-%s" % (destination.name, uuid.uuid4().hex))
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(str(temporary), str(destination))


class RunManifest:
    """Mutable-in-memory, atomic-on-disk lifecycle record."""

    def __init__(
        self,
        config: ResearchConfig,
        command: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        self.run_id = "%s-%s-%s" % (
            now.strftime("%Y%m%dT%H%M%S.%fZ"),
            command.replace("_", "-"),
            uuid.uuid4().hex[:8],
        )
        self.path = config.paths.runs_dir / self.run_id / "manifest.json"
        universe_manifest = config.paths.universe_dir / "manifest.json"
        universe_version = None
        if universe_manifest.exists():
            try:
                universe_version = json.loads(
                    universe_manifest.read_text(encoding="utf-8")
                ).get("sha256")
            except (OSError, ValueError, AttributeError):
                universe_version = None
        self.payload: Dict[str, Any] = {
            "run_id": self.run_id,
            "timestamp": now.isoformat(),
            "completed_at": None,
            "command": command,
            "arguments": arguments or {},
            "status": "running",
            "git_commit": git_commit(config.repo_root or Path.cwd()),
            "upstream_audit_commit": "f0425ae4ae8bd02b79656b8f7039f4cd6874095e",
            "config_path": str(config.config_path) if config.config_path else None,
            "config": config.to_dict(),
            "random_seed": config.seed,
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "package_versions": package_versions(),
            "data_start": config.data.start.isoformat(),
            "data_end": config.data.end.isoformat(),
            "universe_version": universe_version,
            "factor_list": list(config.factors),
            "failures": {},
            "outputs": {},
        }
        _atomic_json(self.payload, self.path)

    def add_output(self, name: str, value: Any) -> None:
        self.payload["outputs"][name] = str(value)
        _atomic_json(self.payload, self.path)

    def add_failures(self, name: str, values: Any) -> None:
        self.payload["failures"][name] = values
        _atomic_json(self.payload, self.path)

    def finish(self, status: str = "success", error: Optional[str] = None) -> None:
        self.payload["status"] = status
        self.payload["completed_at"] = datetime.now(timezone.utc).isoformat()
        if error is not None:
            self.payload["error"] = error
        _atomic_json(self.payload, self.path)


__all__ = ["RunManifest", "git_commit", "package_versions", "set_random_seed"]
