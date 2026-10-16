"""Run the complete offline suite and retain timings, exit status and evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import time


def canonical_ids(values):
    return ("\n".join(sorted(values)) + "\n").encode("utf-8")


def write_json(path, value):
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def process_tree_rss(pid):
    """Sample aggregate Linux process-tree RSS; shared pages may be counted twice."""
    processes = {}
    try:
        for entry in Path("/proc").iterdir():
            if entry.name.isdigit():
                try:
                    fields = {}
                    for line in (entry / "status").read_text().splitlines():
                        if line.startswith(("PPid:", "VmRSS:")):
                            key, value = line.split(":", 1)
                            fields[key] = int(value.split()[0])
                    processes[int(entry.name)] = (
                        fields.get("PPid", 0),
                        fields.get("VmRSS", 0) * 1024,
                    )
                except (OSError, ValueError):
                    continue
    except OSError:
        return None
    selected = {pid}
    while True:
        expanded = selected | {
            key for key, (parent, _) in processes.items() if parent in selected
        }
        if expanded == selected:
            break
        selected = expanded
    return sum(processes.get(key, (0, 0))[1] for key in selected)


def usage():
    try:
        import resource

        result = resource.getrusage(resource.RUSAGE_CHILDREN)
        return result.ru_utime, result.ru_stime
    except ImportError:
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=(0, 2, 3), default=0)
    parser.add_argument("--no-coverage", action="store_true")
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    scripts = Path(__file__).resolve().parent
    environment = os.environ.copy()
    environment["PYTHONPATH"] = (
        str(scripts) + os.pathsep + environment.get("PYTHONPATH", "")
    )
    environment["MPLBACKEND"] = "Agg"
    environment["PYTHONUTF8"] = "1"
    command = [sys.executable]
    if args.profile:
        command.extend(
            ["-m", "cProfile", "-o", str(output / "profile.pstats"), "-m", "pytest"]
        )
    else:
        command.extend(["-m", "pytest"])
    command.extend(
        [
            "tests/research",
            "-q",
            "-m",
            "not network",
            "--durations=40",
            "--durations-min=0",
            "-p",
            "ci_profile",
            "--ci-evidence-dir",
            str(output),
        ]
    )
    if args.collect_only:
        command.append("--collect-only")
    else:
        command.append("--junitxml=" + str(output / "research.xml"))
        if not args.no_coverage:
            command.extend(
                [
                    "--cov=qbot.research",
                    "--cov-report=term",
                    "--cov-report=xml:" + str(output / "coverage.xml"),
                ]
            )
        if args.workers:
            command.extend(
                ["-n", str(args.workers), "--dist=loadfile", "--max-worker-restart=0"]
            )
    package_versions = json.loads(
        subprocess.check_output(
            [sys.executable, "-m", "pip", "list", "--format=json"], text=True
        )
    )
    metadata = {
        "kind": "actual_ci_measurement_not_financial_certification",
        "subject_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "subject_tree": subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], text=True
        ).strip(),
        "subject_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        ),
        "controller_sha": os.environ.get("CI_CONTROLLER_SHA", "UNKNOWN"),
        "python": sys.version,
        "platform": platform.platform(),
        "packages": package_versions,
        "command": command,
        "utc_started": datetime.now(timezone.utc).isoformat(),
        "workers": args.workers,
        "coverage": not args.no_coverage and not args.collect_only,
        "collect_only": args.collect_only,
        "profiled": args.profile,
        "environment": {
            key: environment.get(key, "UNSET")
            for key in (
                "ImageOS",
                "ImageVersion",
                "RUNNER_ARCH",
                "GITHUB_RUN_ID",
                "GITHUB_RUN_ATTEMPT",
                "CI_PIP_CACHE",
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
        "observer_sha256": hashlib.sha256(
            (scripts / "ci_profile.py").read_bytes()
        ).hexdigest(),
    }
    write_json(output / "environment.json", metadata)
    before = usage()
    started = time.perf_counter()
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=environment
    )
    peak = [None]
    stopped = threading.Event()

    def sample():
        while not stopped.is_set():
            current = process_tree_rss(process.pid)
            if current is not None:
                peak[0] = max(peak[0] or 0, current)
            stopped.wait(0.25)

    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    try:
        with (output / "pytest.log").open("wb") as logfile:
            for line in iter(process.stdout.readline, b""):
                logfile.write(line)
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
        exit_code = process.wait()
    finally:
        stopped.set()
        sampler.join()
    elapsed = time.perf_counter() - started
    after = usage()
    result = {
        "exit_code": exit_code,
        "wall_seconds": elapsed,
        "cpu_user_seconds": after[0] - before[0] if before and after else "UNKNOWN",
        "cpu_system_seconds": after[1] - before[1] if before and after else "UNKNOWN",
        "sampled_process_tree_rss_peak_bytes": (
            peak[0] if peak[0] is not None else "UNKNOWN"
        ),
        "rss_sampling_seconds": 0.25,
        "rss_shared_pages_may_be_double_counted": True,
    }
    write_json(output / "result.json", result)
    observations = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(output.glob("pytest-*.json"))
    ]
    collector = next((row for row in observations if row["all_ids"]), None)
    if collector:
        for key in ("all_ids", "selected_ids", "deselected_ids"):
            data = canonical_ids(collector[key])
            (output / (key + ".txt")).write_bytes(data)
            result[key + "_count"] = len(collector[key])
            result[key + "_sha256"] = hashlib.sha256(data).hexdigest()
        write_json(output / "result.json", result)
    print(json.dumps(result, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
