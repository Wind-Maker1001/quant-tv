"""Run explicitly; preserve the historical tests/research Git tree."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
PUB = "docs/research/evidence/pit-publication-20261018-v1/"
MIG = "docs/research/evidence/pit-release-migration-20261018-v1/"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def publication():
    return load_module("pit_publication", ROOT / PUB / "verify_publication.py")


@pytest.fixture
def migration():
    return load_module("pit_migration", ROOT / MIG / "verify_migration.py")


def inject(publication, monkeypatch, tmp_path, payload, kind="md", escape=""):
    manifest = json.loads((ROOT / PUB / "manifest.json").read_text(encoding="utf-8"))
    name = MIG + {"md": "PR_DESCRIPTION.md", "json": "validation.json",
                  "py": "verify_migration.py"}[kind]
    text = (ROOT / name).read_text(encoding="utf-8")
    if kind == "json":
        value = json.loads(text)
        value["test_probe"] = payload
        text = json.dumps(value, ensure_ascii=False)
        if escape:
            text = text.replace("/", escape)
    elif kind == "py":
        text += "\nTEST_PROBE = " + repr(payload) + "\n"
    else:
        text += "\nProbe: '" + payload + "'\n"
    raw = text.encode("utf-8")
    target = tmp_path / ("injected." + kind)
    target.write_bytes(raw)
    item = next(item for item in manifest["files"] if item["path"] == name)
    item.update(public_sha256=hashlib.sha256(raw).hexdigest(), public_bytes=len(raw))
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(publication, "HERE", tmp_path)
    original_local = publication.local
    monkeypatch.setattr(publication, "local",
                        lambda path: target if path == name else original_local(path))


@pytest.mark.parametrize("kind", ["md", "json", "py"])
@pytest.mark.parametrize("payload", [
    "/workspace/alice/repo", "/root/secret", "/tmp/build", "/var/cache/private",
    "/opt/research", "/srv/evidence", "/Volumes/alice/archive", "/data/research",
    "/unlisted_mount_928/alice", "/私有挂载/研究", "/secret", "/.hidden",
    "/2026/10/18", "C:/Users/alice/repo", r"D:\private\receipt.json",
    r"\\server\share\private",
])
def test_rehashed_public_file_rejects_paths(publication, monkeypatch, tmp_path, payload, kind):
    inject(publication, monkeypatch, tmp_path, payload, kind)
    with pytest.raises(ValueError, match="Absolute local path"):
        publication.verify()


@pytest.mark.parametrize("escape", [r"\/", r"\u002f"])
@pytest.mark.parametrize("payload", ["/new_volume/private", "/root/secret", "/"])
def test_json_escapes_cannot_hide_paths(publication, monkeypatch, tmp_path, payload, escape):
    inject(publication, monkeypatch, tmp_path, payload, "json", escape)
    with pytest.raises(ValueError, match="Absolute local path"):
        publication.verify()


@pytest.mark.parametrize("payload", [
    "https://example.org/workspace/alice?date=2026/10/18",
    "http://example.org:8080/tmp/build", "ftp://example.org/root/archive",
    "wss://example.org/unknown/mount", "custom+v2://example.org/root/resource",
    "s3://research-bucket/2026/10/18", "ssh://git@example.org/workspace/repo",
    "docs/research/evidence.json", "./tmp/build", "../root/secret",
    "<REPO>/data/research", "$" + "{QBOT_DATA_DIR}/tdx", "**/__pycache__/",
    "2026/10/18", "2026-10-18", "2021/01/01–2026/10/18",
    "Formal/Forward BLOCKED; NO LIVE MONEY",
])
def test_urls_relative_paths_and_dates_pass(publication, monkeypatch, tmp_path, payload):
    inject(publication, monkeypatch, tmp_path, payload)
    result = publication.verify()
    assert result["public_copy_integrity"] == "PASS"
    assert result["formal_admission"] is False and result["no_live_money"] is True


def test_manifest_strings_are_scanned(publication, monkeypatch, tmp_path):
    inject(publication, monkeypatch, tmp_path, "safe")
    path = tmp_path / "manifest.json"
    value = json.loads(path.read_text())
    value["private_comment"] = "/unlisted_mount/private"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Private path in public manifest"):
        publication.verify()


def test_python_suffix_requires_relative_expression(publication):
    unsafe = 'prefix = "note"; output = prefix + "/root/secret"'
    assert publication.has_local_path(publication.python_path_text(unsafe))
    relative = 'output = str(path.relative_to(ROOT)).replace("\\\\", "/") + "/image.png"'
    assert not publication.has_local_path(publication.python_path_text(relative))
    assert publication.has_local_path(publication.python_path_text(relative + '\nx = "/image.png"'))


def test_python_string_escapes_are_decoded(publication):
    source = r'output = "\u002funknown_mount\u002fprivate"'
    assert publication.has_local_path(publication.python_path_text(source))


def test_decoded_json_keys_are_scanned(publication, monkeypatch, tmp_path):
    inject(publication, monkeypatch, tmp_path, {"/unknown_mount/private": "value"},
           "json", r"\u002f")
    with pytest.raises(ValueError, match="decoded JSON"):
        publication.verify()


def git(root, *args):
    env = os.environ.copy()
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.check_output(
        ["git", "-c", "user.name=Archive Test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", "-c", "core.eol=lf",
         "-c", "core.hooksPath=" + os.devnull, *args],
        cwd=root, env=env, stderr=subprocess.PIPE,
    )


def write(root, name, raw):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def commit(root, message):
    git(root, "add", ".")
    git(root, "commit", "-m", message)
    return git(root, "rev-parse", "HEAD").decode().strip()


@pytest.fixture(scope="module")
def historical_repository(tmp_path_factory):
    root = tmp_path_factory.mktemp("historical-git")
    git(root, "init", "-b", "main")
    protected = {".github/scripts", ".github/workflows", "qbot/research",
                 "configs/research", "tests/research"}
    for path in protected:
        write(root, path + "/frozen.txt", b"frozen main\n")
    write(root, ".gitattributes", b"* text=auto eol=lf\n")
    base = commit(root, "main")
    trees = {name: git(root, "rev-parse", base + ":" + name).decode().strip()
             for name in protected}
    for index in range(42):
        write(root, "archive/file-%02d.txt" % index, ("original %d\n" % index).encode())
    source = commit(root, "original archive")
    paths = [".gitattributes"] + ["archive/file-%02d.txt" % i for i in range(42)]
    delivery = []
    for name in paths:
        raw = (root / name).read_bytes()
        delivery.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                         "git_blob": git(root, "rev-parse", source + ":" + name).decode().strip()})
    git(root, "checkout", "-b", "migration", base)
    git(root, "cherry-pick", "-x", source)
    cherry_pick = git(root, "rev-parse", "HEAD").decode().strip()
    verifier = b'print("historical verifier")\n'
    extras = ["docs/research/PIT_EVIDENCE_RELEASE_MIGRATION_2026-10-18.md",
              MIG + ".gitattributes", MIG + "PR_DESCRIPTION.md",
              MIG + "validation.json", MIG + "verify_migration.py"]
    receipt = {
        "schema": "PIT_EVIDENCE_MAIN_MIGRATION_V1", "formal_admission": False,
        "no_live_money": True, "main_base_commit": base, "source_commit": source,
        "cherry_pick_commit": cherry_pick, "delivery_files": delivery,
        "protected_main_trees": trees, "migration_files": extras,
        "migration_verifier_sha256": hashlib.sha256(verifier).hexdigest(),
    }
    for name in extras:
        write(root, name, b"historical migration note\n")
    write(root, MIG + "verify_migration.py", verifier)
    write(root, MIG + "validation.json", json.dumps(receipt).encode())
    private = commit(root, "private publication source")
    manifest = {"main_base_commit": base, "private_source_commit": private, "files": []}
    for name in paths + extras:
        raw = (root / name).read_bytes()
        manifest["files"].append({"path": name, "original_bytes": len(raw),
                                  "original_sha256": hashlib.sha256(raw).hexdigest()})
    write(root, PUB + "manifest.json", json.dumps(manifest).encode())
    write(root, PUB + "verify_publication.py",
          b'def verify():\n    return {"public_copy_integrity": "PASS", '
          b'"formal_admission": False, "no_live_money": True}\n')
    return root, receipt, manifest


@pytest.fixture
def history(tmp_path, historical_repository, migration, monkeypatch):
    original, receipt, manifest = historical_repository
    root = tmp_path / "checkout"
    shutil.copytree(original, root)
    monkeypatch.setattr(migration, "ROOT", root)
    return root, copy.deepcopy(receipt), copy.deepcopy(manifest)


def test_real_objects_validate_only_recorded_scope(migration, history, capsys):
    _, receipt, manifest = history
    migration.verify_recorded_migration(receipt, manifest)
    assert migration.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["migration_consistency"] == "PASS_RECORDED_GIT_OBJECTS_ONLY"
    assert result["historical_delivery_objects_checked"] == 43
    assert result["full_migration_verification"].startswith("NOT_RUN")


@pytest.mark.parametrize("field", ["main_base_commit", "source_commit", "cherry_pick_commit"])
def test_missing_commit_is_not_success(migration, history, field, capsys):
    root, receipt, manifest = history
    receipt[field] = "0" * 40
    if field == "main_base_commit":
        manifest[field] = receipt[field]
    write(root, migration.RECEIPT, json.dumps(receipt).encode())
    write(root, PUB + "manifest.json", json.dumps(manifest).encode())
    assert migration.main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["migration_consistency"].startswith("NOT_RUN")
    assert result["full_migration_verification"].startswith("NOT_RUN")


@pytest.mark.parametrize("missing", ["private_commit", "delivery_blob", "original_verifier"])
def test_missing_original_objects_are_not_success(migration, history, missing):
    root, receipt, manifest = history
    if missing == "private_commit":
        manifest["private_source_commit"] = "0" * 40
    else:
        blob = receipt["delivery_files"][-1]["git_blob"]
        if missing == "original_verifier":
            blob = git(root, "rev-parse", manifest["private_source_commit"] + ":" +
                       migration.VERIFIER).decode().strip()
        # Only this test's synthetic repository is modified.
        target = root / ".git" / "objects" / blob[:2] / blob[2:]
        target.chmod(stat.S_IWRITE | stat.S_IREAD)
        target.unlink()
    with pytest.raises(migration.MissingGitObjects):
        migration.verify_recorded_migration(receipt, manifest)


def test_shallow_checkout_is_not_success(migration, history, tmp_path, monkeypatch):
    root, receipt, manifest = history
    shallow = tmp_path / "shallow"
    git(tmp_path, "clone", "--depth=1", "--no-local", root.as_uri(), str(shallow))
    monkeypatch.setattr(migration, "ROOT", shallow)
    with pytest.raises(migration.MissingGitObjects):
        migration.verify_recorded_migration(receipt, manifest)


@pytest.mark.parametrize("mutation", ["schema", "boundary", "duplicate", "hash", "blob",
                                    "protected_inventory", "unsafe_path", "parent"])
def test_inconsistent_receipt_fails(migration, history, mutation):
    _, receipt, manifest = history
    if mutation == "schema":
        receipt["schema"] = "UNKNOWN"
    elif mutation == "boundary":
        receipt["formal_admission"] = True
    elif mutation == "duplicate":
        receipt["delivery_files"][-1] = receipt["delivery_files"][0]
    elif mutation == "hash":
        item = receipt["delivery_files"][-1]
        item["sha256"] = "0" * 64
        next(p for p in manifest["files"] if p["path"] == item["path"])["original_sha256"] = item["sha256"]
    elif mutation == "blob":
        receipt["delivery_files"][-1]["git_blob"] = receipt["delivery_files"][0]["git_blob"]
    elif mutation == "protected_inventory":
        receipt["protected_main_trees"].pop("qbot/research")
    elif mutation == "unsafe_path":
        receipt["delivery_files"][-1]["path"] = "../outside"
    elif mutation == "parent":
        receipt["cherry_pick_commit"] = manifest["private_source_commit"]
    with pytest.raises(ValueError):
        migration.verify_recorded_migration(receipt, manifest)


@pytest.mark.parametrize("committed", [False, True])
def test_protected_tree_change_is_rejected(migration, history, committed):
    root, receipt, manifest = history
    write(root, "qbot/research/frozen.txt", b"changed research\n")
    if committed:
        commit(root, "unauthorized research change")
    with pytest.raises(ValueError, match="protected main|Git entry mismatch"):
        migration.verify_recorded_migration(receipt, manifest)


def test_bad_receipt_cli_reports_fail(migration, history, capsys):
    root, receipt, _ = history
    receipt["no_live_money"] = False
    write(root, migration.RECEIPT, json.dumps(receipt).encode())
    assert migration.main() == 1
    assert json.loads(capsys.readouterr().out)["migration_consistency"] == "FAIL"


def test_missing_git_is_not_run(migration, history, monkeypatch, capsys):
    monkeypatch.setenv("PATH", "")
    assert migration.main() == 1
    assert json.loads(capsys.readouterr().out)["migration_consistency"].startswith("NOT_RUN")
