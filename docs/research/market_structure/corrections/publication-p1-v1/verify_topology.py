"""Verify exact publication trees through fresh Actions-style Git checkouts."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASELINE = "7300afdb92127aec83f03a5f5fa91b7f71fe94bb"
MANIFEST = "docs/research/market_structure/evidence/v9/delivery-manifest.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-broken", action="store_true")
    args = parser.parse_args()
    args.source = args.source.resolve()
    args.workspace = args.workspace.resolve()
    args.output = args.output.resolve()
    assert not args.workspace.exists(), "fresh workspace required"
    args.workspace.mkdir(parents=True)
    args.output.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_LFS_SKIP_SMUDGE="1", GIT_CONFIG_NOSYSTEM="1",
               GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_LAZY_FETCH="1",
               GIT_AUTHOR_NAME="Publication topology acceptance",
               GIT_AUTHOR_EMAIL="acceptance@example.invalid",
               GIT_COMMITTER_NAME="Publication topology acceptance",
               GIT_COMMITTER_EMAIL="acceptance@example.invalid")
    commands = []

    def run(cwd, argv, allowed=(0,)):
        result = subprocess.run(argv, cwd=cwd, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        commands.append(dict(cwd=str(cwd), argv=argv, exit_code=result.returncode,
                             stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
                             stderr=result.stderr.decode("utf-8", errors="replace")))
        (args.output / "commands.json").write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
        assert result.returncode in allowed, commands[-1]
        return result

    def git(cwd, *argv, allowed=(0,)):
        return run(cwd, ["git", *argv], allowed)

    args.subject = git(args.source, "rev-parse", args.subject + "^{commit}").stdout.decode().strip()
    args.base = git(args.source, "rev-parse", args.base + "^{commit}").stdout.decode().strip()
    common = Path(git(args.source, "rev-parse", "--git-common-dir").stdout.decode().strip())
    if not common.is_absolute():
        common = (args.source / common).resolve()
    seed = args.workspace / "retained.git"
    git(args.workspace, "init", "--bare", str(seed))
    (seed / "objects/info/alternates").write_bytes(((common / "objects").as_posix() + "\n").encode("utf-8"))
    git(seed, "update-ref", "refs/heads/main", args.base)
    git(seed, "update-ref", "refs/heads/feature", args.subject)
    tree = git(seed, "rev-parse", args.subject + "^{tree}").stdout.decode().strip()
    squash = git(seed, "commit-tree", tree, "-p", args.base, "-m", "Acceptance squash of exact publication tree").stdout.decode().strip()
    git(seed, "update-ref", "refs/heads/squashed", squash)
    discarded = args.workspace / "discarded.git"
    git(args.workspace, "init", "--bare", str(discarded))
    git(discarded, "fetch", "--no-tags", "--no-recurse-submodules", str(seed),
        "refs/heads/main:refs/heads/main", "refs/heads/squashed:refs/heads/squashed")
    cases = []
    for name, remote, subject in (("original", seed, args.subject),
                                  ("squashed-retained", seed, squash),
                                  ("squashed-discarded", discarded, squash)):
        checkout = args.workspace / name
        git(args.workspace, "init", str(checkout))
        git(checkout, "config", "core.longpaths", "true")
        git(checkout, "remote", "add", "origin", str(remote))
        git(checkout, "fetch", "--no-tags", "--no-recurse-submodules", "origin",
            "+refs/heads/*:refs/remotes/origin/*", subject)
        git(checkout, "checkout", "--detach", subject)
        assert git(checkout, "status", "--porcelain").stdout == b""
        assert git(checkout, "rev-parse", "HEAD").stdout.decode().strip() == subject
        assert git(checkout, "rev-parse", "HEAD^{tree}").stdout.decode().strip() == tree
        ancestor = git(checkout, "merge-base", "--is-ancestor", BASELINE, "HEAD", allowed=(0, 1, 128)).returncode
        exists = git(checkout, "cat-file", "-e", BASELINE + "^{commit}", allowed=(0, 1, 128)).returncode
        show = git(checkout, "show", BASELINE + ":" + MANIFEST, allowed=(0, 1, 128)).returncode
        result = run(checkout, [sys.executable, "-B", "-X", "utf8", "-m",
                               "examples.research.review_yhh30m_release", "--repo", ".", "--base", args.base], (0, 1))
        (args.output / (name + "-publication.json")).write_bytes(result.stdout)
        (args.output / (name + ".stderr.log")).write_bytes(result.stderr)
        report = json.loads(result.stdout)
        assert git(checkout, "status", "--porcelain").stdout == b""
        cases.append(dict(case=name, subject=subject, tree=tree,
                          parents=git(checkout, "show", "-s", "--format=%P", "HEAD").stdout.decode().strip().split(),
                          ancestor_exit=ancestor, frozen_object_exit=exists, frozen_show_exit=show,
                          scanner_exit=result.returncode, status=report["status"],
                          changed_files=len(report["changed_files"]),
                          checked_files=len(report["safety_checked_files"]),
                          out_of_scope_files=len(report["out_of_scope_files"]),
                          reason_counts=dict(Counter(x["reason"] for x in report["blocked_findings"])),
                          source_sha256=hashlib.sha256((checkout / "examples/research/review_yhh30m_release.py").read_bytes()).hexdigest(),
                          output_sha256=hashlib.sha256(result.stdout).hexdigest(), clean=True))
        (args.output / "receipt.json").write_text(json.dumps(dict(subject=args.subject, base=args.base,
            frozen_baseline=BASELINE, python=sys.version, cases=cases), indent=2) + "\n", encoding="utf-8")
        print(json.dumps(cases[-1]), flush=True)
    assert cases[0]["ancestor_exit"] == 0
    assert cases[1]["ancestor_exit"] == 1 and cases[1]["frozen_object_exit"] == 0
    assert cases[2]["frozen_object_exit"] != 0 and cases[2]["frozen_show_exit"] != 0
    assert [c["status"] for c in cases] == (["PASS", "FAIL", "FAIL"] if args.expect_broken else ["PASS"] * 3)


if __name__ == "__main__":
    main()
