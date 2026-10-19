"""Actual independent execution driver; no market-data or trading actions."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).parent / "v9/final"
kind = sys.argv[1]
head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
start = datetime.datetime.now(datetime.timezone.utc).isoformat()
if kind == "tests":
    cmd = [sys.executable, "-X", "utf8", "-m", "pytest", "tests/market_structure", "-q",
           "--basetemp="+str(root/"test-temp"), "--junitxml="+str(root/"new-tests.xml"),
           "--cov=qbot/research/exploratory/market_structure", "--cov-branch",
           "--cov-report=term-missing", "--cov-report=xml:"+str(root/"coverage.xml"),
           "--cov-report=json:"+str(root/"coverage.json")]
    env = dict(os.environ, COVERAGE_FILE=str(root/".coverage"))
    with (root/"new-tests.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
    name = "new-tests-command"
elif kind == "cli":
    cmd = [sys.executable, "-X", "utf8", "-m", "qbot.research.exploratory.market_structure",
           "--output", str(root/"synthetic"), "--frequencies", "5", "15", "30"]
    with (root/"source-cli.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    name = "source-cli"
else:
    scopes = ["qbot/research/exploratory/market_structure", "tests/market_structure"]
    files = sorted(p.as_posix() for scope in scopes for p in Path(scope).rglob("*.py"))
    for path in files:
        compile(Path(path).read_bytes(), path, "exec")
    commands = [[sys.executable, "-X", "utf8", "-m", "flake8", "--select=E9,F63,F7,F82"]+scopes,
                ["git", "-c", "core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol", "diff", "--check", "b30256d", "HEAD", "--"]+scopes,
                [sys.executable, "-X", "utf8", ".github/scripts/ci/research_checks.py"],
                [sys.executable, "-X", "utf8", "-m", "pytest", "tests/market_structure/test_review_red_cases.py", "tests/market_structure/test_review_spearman.py", "tests/market_structure/test_review_dependencies.py", "tests/market_structure/test_review_broadcast.py", "tests/market_structure/test_review_followup.py", "tests/market_structure/test_review_source_policy.py", "tests/market_structure/test_review_amount_red.py", "tests/market_structure/test_review_amount_fields.py", "tests/market_structure/test_review_scope_red.py", "tests/market_structure/test_review_scope.py", "tests/market_structure/test_review_taxonomy_red.py", "tests/market_structure/test_review_taxonomy.py", "tests/market_structure/test_review_calendar_red.py", "tests/market_structure/test_review_calendar.py", "tests/market_structure/test_review_identifiers_red.py", "tests/market_structure/test_review_identifiers.py", "tests/market_structure/test_review_provenance_red.py", "tests/market_structure/test_review_provenance.py", "-q", "--basetemp="+str(root/"targeted-temp"), "--junitxml="+str(root/"targeted-tests.xml")]]
    results=[]
    with (root/"static.log").open("w", encoding="utf-8") as log:
        for command in commands:
            log.write(json.dumps(command)+"\n"); log.flush()
            r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
            results.append(dict(argv=command,exit_code=r.returncode))
    data=dict(implementation_commit=head,python=sys.version,started_at=start,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=int(any(r["exit_code"] for r in results)),compiled_sources=files,commands=results)
    (root/"static.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
    print(json.dumps(data),flush=True)
    raise SystemExit(data["exit_code"])
data=dict(argv=cmd,implementation_commit=head,python=sys.version,started_at=start,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=result.returncode)
(root/(name+".json")).write_text(json.dumps(data,indent=2),encoding="utf-8")
print(json.dumps(data),flush=True)
raise SystemExit(result.returncode)
