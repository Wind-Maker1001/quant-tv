"""Append actual V7 execution evidence, preserving every earlier Git byte."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path.cwd()))
import pandas as pd
from qbot.research.exploratory.market_structure.runner import verify_receipt

ROOT = Path.cwd()
EXTERNAL = Path(__file__).parent
PREFIX = Path('docs/research/market_structure/evidence')
TARGET = PREFIX / 'v7'
FINAL = EXTERNAL / 'v7/final'
UPSTREAM = 'f1ad2d4f05d7676f9d49e23af9a8e0ec0615e19e'
PREVIOUS = '7df99915738c455abd8782bb0aaaa91fa0ede4e6'
EXCEPTIONS = ['.github/workflows/minute-data-evidence.yml', 'examples/research/review_yhh30m_release.py']

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')

def git(*args):
    return subprocess.check_output(['git', *args], text=True).splitlines()

def junit(path):
    tree = ET.parse(path).getroot()
    counts = {key: sum(int(s.get(key, '0')) for s in tree.iter('testsuite'))
              for key in ('tests', 'failures', 'errors', 'skipped')}
    cases = {(row.get('classname'), row.get('name')) for row in tree.iter('testcase')}
    return counts, cases

assert not TARGET.exists(), 'never overwrite evidence'
head = git('rev-parse', 'HEAD')[0]
counts, cases = junit(FINAL / 'new-tests.xml')
assert counts == dict(tests=221, failures=0, errors=0, skipped=0), counts
assert junit(PREFIX / 'v1/new-tests.xml')[1] <= cases
assert junit(PREFIX / 'v6/new-tests.xml')[1] <= cases
targeted, _ = junit(FINAL / 'targeted-tests.xml')
assert targeted == dict(tests=159, failures=0, errors=0, skipped=0)
red, _ = junit(EXTERNAL / 'v7/red/red-tests.xml')
assert red == dict(tests=2, failures=2, errors=0, skipped=0)
red_receipt = read(EXTERNAL / 'v7/red/red-receipt.json')
assert sha('tests/market_structure/test_review_calendar_red.py') == red_receipt['test_sha256']
for name, expected in red_receipt['product_source_sha256'].items():
    original = subprocess.check_output(['git', 'show', PREVIOUS+':'+name])
    assert hashlib.sha256(original).hexdigest() == expected
for name in ('new-tests-command.json', 'static.json', 'source-cli.json'):
    assert read(FINAL / name)['implementation_commit'] == head
    assert read(FINAL / name)['exit_code'] == 0

preserved = {}
for version in range(1, 7):
    for name in git('ls-tree', '-r', '--name-only', PREVIOUS, '--', str(PREFIX/('v'+str(version))).replace('\\','/'), *([str(PREFIX/'v5-git-portability').replace('\\','/')] if version == 5 else [])):
        original = subprocess.check_output(['git', 'show', PREVIOUS+':'+name])
        expected = hashlib.sha256(original).hexdigest()
        assert sha(name) == expected, name
        preserved[name] = expected
original_modified = git('diff', '39eecf869c9c2075ba3f6e3c76aeba3338c63432', '--diff-filter=MDR', '--name-only')
assert not original_modified
changed = git('diff', UPSTREAM, '--name-only')
prefixes = ('qbot/research/exploratory/market_structure/', 'tests/market_structure/', 'docs/research/market_structure/')
assert all(p.startswith(prefixes) or p in EXCEPTIONS for p in changed)
assert sorted(git('diff', UPSTREAM, '--diff-filter=MDR', '--name-only')) == sorted(EXCEPTIONS)
assert not git('diff', UPSTREAM, '--name-only', '--', 'qbot/engineering/yhh30m', 'tests/minute_data', 'docs/research/evidence/yhh30m-independent-20261019-v1')

coverage = read(FINAL/'coverage.json')
source = {p.as_posix(): sha(p) for p in Path('qbot/research/exploratory/market_structure').glob('*.py')}
covered = {key.replace('\\','/'): row for key,row in coverage['files'].items()}
assert set(covered) == set(source) and len(source) == 10
xml_names = [Path(row.get('filename').replace('\\','/')).name for row in ET.parse(FINAL/'coverage.xml').getroot().iter('class')]
assert sorted(xml_names) == sorted(Path(p).name for p in source)
inventory = {p: dict(source_sha256=source[p], **covered[p]['summary']) for p in source}
receipt = verify_receipt(FINAL/'synthetic')
assert receipt['tested_commit'] == head
assert receipt['source_sha256'] == source
assert receipt['candidate_count'] == 32 and receipt['implemented_count'] == 14 and receipt['frequencies'] == [5,15,30]
states = pd.read_csv(FINAL/'synthetic/contract_status.csv')
assert len(states) == 32 and (states.implementation_status=='IMPLEMENTED_SYNTHETIC').sum()==14
previous = read(PREFIX/'v6/synthetic/receipt.json')
assert receipt['output_value_sha256'] != previous['output_value_sha256']
assert receipt['numeric_value_sha256'] == previous['numeric_value_sha256']
assert receipt['input_sha256'] == previous['input_sha256']
assert receipt['catalog_sha256'] == previous['catalog_sha256']
old_corr = pd.read_csv(PREFIX/'v6/synthetic/redundancy_windows.csv')
new_corr = pd.read_csv(FINAL/'synthetic/redundancy_windows.csv')
pd.testing.assert_frame_equal(old_corr, new_corr, check_exact=True)
minute_counts, minute_cases = junit(EXTERNAL/'main-sync/minute-tests.xml')
minute_contract = read('docs/research/evidence/yhh30m-independent-20261019-v1/minute-ci-contract.json')
assert minute_counts == dict(tests=42,failures=0,errors=0,skipped=0)
assert minute_cases == {tuple(row) for row in minute_contract['junit_addresses']}

old_snap = pd.read_csv(PREFIX/'v6/synthetic/snapshots.csv')
new_snap = pd.read_csv(FINAL/'synthetic/snapshots.csv')
pd.testing.assert_frame_equal(old_snap.drop(columns=['snapshot_id','context_input_sha256']), new_snap.drop(columns=['snapshot_id','context_input_sha256']), check_exact=True)
old_context = pd.read_csv(PREFIX/'v6/synthetic/market_context.csv')
new_context = pd.read_csv(FINAL/'synthetic/market_context.csv')
pd.testing.assert_frame_equal(old_context,new_context.drop(columns=['calendar_sha256']),check_exact=True)
TARGET.mkdir(parents=True)
shutil.copytree(EXTERNAL/'v7/red', TARGET/'red')
shutil.copytree(FINAL/'synthetic', TARGET/'synthetic')
for name in ('new-tests.xml','new-tests.log','new-tests-command.json','coverage.xml','coverage.json',
             'targeted-tests.xml','static.json','static.log','source-cli.json','source-cli.log'):
    shutil.copyfile(FINAL/name, TARGET/name)
integration = TARGET/'main-sync'
integration.mkdir()
for name in ('gate-red.xml','gate-red.log','gate-green.xml','minute-tests.xml','minute-tests.log',
             'compatibility-commands.json','compatibility-0.log','compatibility-1.log','compatibility-2.log'):
    shutil.copyfile(EXTERNAL/'main-sync'/name, integration/name)
for stage in ('final','post-gate'):
    shutil.copyfile(EXTERNAL/'main-sync'/stage/'new-tests-command.json', integration/(stage+'-command.json'))
    shutil.copyfile(EXTERNAL/'main-sync'/stage/'new-tests.xml', integration/(stage+'-tests.xml'))
shutil.copyfile(EXTERNAL/'main-sync/final/source-cli.json', integration/'pre-gate-source-cli.json')
shutil.copyfile(EXTERNAL/'run_acceptance_v7.py', TARGET/'actual-execution-driver.py')
shutil.copyfile(__file__, TARGET/'seal-evidence.py')
write(TARGET/'prior-preservation.json',preserved)
write(TARGET/'coverage-source-inventory.json',inventory)
write(TARGET/'integration-scope.json',dict(initial_baseline='39eecf869c9c2075ba3f6e3c76aeba3338c63432',
    authorized_upstream=UPSTREAM,merge_commit='7fb1f1e53755f5655c19d31f3aa0697c8cdd0b74',
    compatibility_commit='5db02fb6ae9c53007f61b1723d1a9a39e1bf1af4',
    authorized_gate_exceptions=EXCEPTIONS,original_baseline_modified_paths=original_modified,
    changes_relative_to_upstream=changed,minute_implementation_and_original_test_contract_unchanged=True,
    minute_tests=minute_counts,unscoped_decode_failure_path='docs/research/market_structure/evidence/v2/red/red-tests.log',
    red_gate_tests=junit(EXTERNAL/'main-sync/gate-red.xml')[0],
    green_gate_and_original_release_tests=junit(EXTERNAL/'main-sync/gate-green.xml')[0]))
write(TARGET/'comparison.json',dict(v6_output_value_sha256=previous['output_value_sha256'],
    v7_output_value_sha256=receipt['output_value_sha256'],numeric_value_sha256=receipt['numeric_value_sha256'],
    catalog_sha256=receipt['catalog_sha256'],default_values_reasons_coverage_equal=True, default_snapshots_equal=False,
    diagnostic_windows=len(new_corr),changed_diagnostic_windows=0,
    changed_artifacts={name:dict(v6=old,v7=receipt['artifacts'][name]) for name,old in previous['artifacts'].items()
                       if old != receipt['artifacts'][name]},
    reason='V7 validates taxonomy group IDs and binds context identity to the actually used canonical calendar. Feature values, missing reasons, coverage, feature-input hashes and diagnostic correlations remain identical. Full output and context/snapshot artifact hashes change because calendar identity is now bound; previous hashes remain immutable.',
    source_receipt_revision_note='Runner retains its legacy V4 evidence_revision annotation; this new acceptance and directory explicitly bind the V7 execution and current source hashes. No previous receipt rewritten.'))
write(TARGET/'acceptance.json',dict(evidence_revision='V7',implementation_commit=head,python=sys.version,
    independent_tests=counts,original_tests_preserved=55,prior_v6_tests_preserved=191,targeted_tests=targeted,
    red_tests=red,coverage=coverage['totals'],coverage_source_count=10,candidate_count=32,implemented_count=14,
    frequencies=[5,15,30],prior_evidence_preserved=True,software_status='SOFTWARE_MVP_SUCCESS',
    real_research_status='REAL_RESEARCH_BLOCKED',formal_status='BLOCKED',forward_status='BLOCKED',
    no_live_money=True,installation_package_status='NOT_VALIDATED',
    external_ci_and_review='PENDING_FINAL_HEAD; actual remote records to be checked separately',
    new_review_findings=[4313525755,4313525762]))
manifest = {}
for prefix in prefixes:
    for path in Path(prefix).rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            manifest[path.as_posix()] = sha(path)
for name in EXCEPTIONS:
    manifest[name]=sha(name)
published = dict(manifest)
normalization = {}
for name in EXCEPTIONS:
    blob = subprocess.check_output(['git', 'show', 'HEAD:'+name])
    expected = hashlib.sha256(blob).hexdigest()
    if expected != manifest[name]:
        assert Path(name).read_bytes().replace(b'\r\n', b'\n') == blob
        normalization[name] = dict(tested_worktree_sha256=manifest[name], published_git_blob_sha256=expected)
    published[name] = expected
write(TARGET/'delivery-manifest.json',dict(files=manifest, files_hash_scope='actual tested Windows worktree bytes',
    git_blob_files=published, git_blob_hash_scope='published Git blob bytes; evidence attributes preserve raw bytes',
    line_ending_normalization=normalization, self_hash_policy='Manifest excludes itself from both maps; its SHA-256 is reported separately'))
print(json.dumps(dict(tests=counts,coverage=coverage['totals'],manifest_sha256=sha(TARGET/'delivery-manifest.json'))))
