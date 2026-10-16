# PR #8 P2 correction — V2

NO LIVE MONEY. V1 is retained byte for byte as historical evidence. Its
`worktree_sha256` field describes one Windows checkout, not a portable delivery
contract. Its private-preservation claim also excluded existing siblings in the
current run directory. Those two claims must be read with this correction.

The corrected audit excludes only its newly created output directory. Existing
sibling review/supplement files remain in both metadata snapshots; modification
or deletion produces `FAIL`, a nonempty change list and a nonzero audit exit.
DAY, Parquet, GBBQ, coverage, comparisons and financial admission logic are unchanged.

V2's `delivery-files.json` is generated **after committing** its payload. Every
SHA256/length is independently computed from `git cat-file blob
<source_commit>:<path>`. It retains no authoritative `worktree_sha256` field.
Verification separately reads each filesystem file and asks Git's clean filters
to reproduce the committed blob OID. Raw filesystem SHA256 is diagnostic only:
CRLF and LF checkouts can legitimately differ. Substantive edits still fail.
The sealer refuses an existing output, and verifies the checkout before writing.

Reproduce verification from a checkout containing the referenced commit:

```powershell
python -B examples/research/seal_tdx_delivery.py verify --index docs/research/evidence/tdx-data-quality-v2/delivery-files.json
```

The sealed payload includes all V1 public files (including the old index), the
corrected audit, sealer, regression tests and this correction. The V2 index
excludes itself and the later validation envelope to avoid cyclic hashes.
`validation.json` binds the index, subsequent aggregate recheck and all local
test receipts by SHA256. The envelope itself is bound by the final Git commit;
its local verification receipt is retained privately. No claim of self-hashing
or a precomputed final commit SHA is made.

`hash-root-cause.json` records independent Git-object and filesystem reads.
`regression-reproduction.json` records failures against the old implementation
and contract, followed by passing software counterexamples. Full offline
regression and real-asset preservation results are in `validation.json`.
These software tests do not authenticate units, identity, PIT or HFQ.
