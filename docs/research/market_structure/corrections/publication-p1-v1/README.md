# PR 13 publication authentication correction

NO LIVE MONEY. This correction addresses discussion_r4316272907. It changes the
publication auditor, its minute workflow assertions and regression tests. Market
structure behavior, formal admission and the original V1 through V9 evidence are
unchanged. The earlier FINAL_SCOPE_AUDIT describes the prior implementation;
this independent receipt supersedes its reliance on Git ancestry.

## Reproduction before the fix

The actual reviewed head was a80a50fe0a7f3f974fabccdaef1c4de3649a8121, whose
parent was the frozen identifier 7300afdb92127aec83f03a5f5fa91b7f71fe94bb.
The PR comparison base was main f1ad2d4f05d7676f9d49e23af9a8e0ec0615e19e.
The review's temporary efa0c53 object could not be retrieved. We reproduced its
reported topology by committing the actual reviewed tree directly on the PR
base. These are local acceptance commits, not claimed GitHub commits.

Using the workflow's exact fetch refspec and detached checkout, the original
475-file tree passed. The identical squashed tree failed with
PATH_AUDIT_MANIFEST_MISMATCH when the frozen commit was present but not an
ancestor. A second remote containing only main and the squash proved the old
commit was absent and baseline git show failed; that checkout also failed. The new
three-topology regression against the old auditor produced one pass and two
failures. The red receipts were saved before changing the auditor.

## Frozen authentication

The trust anchors remain the previously audited constants:

- V9 delivery manifest SHA-256:
  63144f07169740b78f33873947f28fa8294d856ea028c53e7785f12daea2165a.
- Exact path rules SHA-256:
  956cf7d1276857b9f65eeed2763c49bf02fab75efb09a12fb66aa672015db851.
- Historical baseline identifier:
  7300afdb92127aec83f03a5f5fa91b7f71fe94bb.

The fixed rules digest authenticates the schema, baseline identifier, V9 digest,
168 exact paths, encodings and expected match types and counts. The independently
pinned V9 manifest's git_blob_files inventory authenticates each rule's original
path membership and published byte hash. The current bytes must match that hash
and the observed match types and counts must match the rule. Neither a different
path nor a rewritten current hash can establish membership in that frozen
inventory. Changing either manifest without matching its fixed digest blocks
publication. The auditor no longer reads frozen Git objects or asks whether the
old commit is an ancestor. Its PR comparison remains main.

No directory exemption was added. The same 168 files account for the same 1045
historical path matches, including one strictly decoded CP936 log whose frozen
Git text attribute and roundtrip remain mandatory. Secrets, raw artifacts and
global protected gates still block even when a path rule is authenticated.

## Validation receipts

validation.json records the before and after topology results, source hashes,
actual exit codes, command-log digests, directed tests and frozen inventory
digest. The candidate used for green validation changed exactly the three
requested implementation files; its original 475-file PR diff passed in all
three clean checkouts. The additional three correction files are scanned as new
files without historical exceptions before submission. The committed PR head is
also checked using clean checkouts and the remote minute workflow artifacts.

The directed suite includes digest tampering, wrong baseline identifiers, changed
bytes, new paths copying historical bytes, inconsistent source hashes, wrong
match counts, non-UTF-8 and binary files, machine paths, secret shapes, raw data
and every global gate in both reporting modes. All 80 directed tests and all 42
minute application tests passed; static defects and workflow Python syntax were
checked. Unrelated large research tests were not repeated locally. The 417
original evidence files retain their exact bytes and hashes.

The private raw command transcripts and scanner JSON are retained locally under
results/diagnostics/pr13-p1-topology. Their digests are recorded here; transcripts
contain host paths and are not copied into the published evidence or exempted.
The first local test attempt encountered Windows sandbox temporary-directory
permissions; its failure remains in green-checks, with the successful rerun in
green-checks-unrestricted. A validation harness initially compared the newly
introduced market module against main instead of the reviewed head; the corrected
check freezes the market module against a80a50f and formal gates against both.

## Repeat the clean topology check

From a complete checkout, with the requested subject available locally:

```text
python -B -X utf8 docs/research/market_structure/corrections/publication-p1-v1/verify_topology.py --source . --subject HEAD --base f1ad2d4f05d7676f9d49e23af9a8e0ec0615e19e --workspace data/research/publication-p1-acceptance --output results/diagnostics/publication-p1-acceptance
```

Use a fresh workspace path. The driver makes local acceptance commits and three
separate repositories; it does not move the source branch or modify its working
tree. Pass the original reviewed commit and --expect-broken to reproduce red.
The driver records each real command, exit code and output digest. No scope flag
is passed to the publication auditor. Human merging remains conditional on the
new head's required CI and Codex Review; this correction never merges the PR.
