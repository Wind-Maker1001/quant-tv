# ADR C01: Solo Maintainer versioned preservation

Date: 2026-10-21 (Asia/Shanghai)

Status: accepted for this migration by the repository owner's explicit task
instruction. This records a new governance decision, not an independent approval
of an earlier proposal. NO LIVE MONEY.

FactorLab is a personal quantitative research project with one actual maintainer.
The repository administrator has final authority over code and governance.
The proposed C01 requirements for a separate human issuer, multiple approvals,
an independent signature server, an external approval ledger, and implementation
permission separated from the developer do not fit this organization.

We replace those proposed organizational controls with a finite Git version
registry, exact source and control hashes, an explicit change inventory,
preservation of historical evidence, and automated regression and rejection
tests. Existing GitHub Ruleset 25464199, all six Required Check names, and CodeQL
remain in force. A JSON claim such as approved=true grants no authority.

The original main implementation is fixed at
cc13795d144592b360e560a9b979e183d6b01907. The reviewed CSMAR RAW source is fixed at
2198d393b75fbccfa05d49ada57cdf6703c12bb8. Implementation code remains at that
reviewed source; the new control version binds its exact preservation changes.
The registry does not accept refs, unknown versions, fallback versions, or a
version selected by an input qualification package. Original freezes, Golden,
PIT receipts, and control anchors are retained. Legacy tests run in a complete
isolated original environment. A historical text view is only for archival
verification and cannot issue or upgrade financial evidence.

The administrator accepts the organizational risk from the absence of separation
of duties. These repository controls detect unregistered content under the
reviewed policy; they do not claim to resist a malicious repository administrator
who changes that policy and its checks. B03 retains its trusted, clean Python
process boundary. Git author strings are not independent signatures.

External-human-authorization attacks from the earlier proposal have status
SUPERSEDED_BY_SOLO_GOVERNANCE_DECISION. Their replacement controls are exact Git
objects, the workflow-pinned control anchor, finite postimages and executable
tests. No historical approval, second maintainer, signature, or approval time is
invented. The old unsigned preparation and failed initializer evidence remain
historical records.

PIT, HFQ, identity, vintage, status, formal research admission and execution
requirements are unchanged. CSMAR RAW technical replay is not financial
certification. The financial status remains PIT_UNVERIFIED,
FORMAL_ADMISSION_BLOCKED, execution_admission=false, NO LIVE MONEY.

A future independent maintenance team can supersede this ADR and restore
mandatory independent approval through another explicit, reviewed decision.

The registry schema is FACTORLAB_C01_SOLO_REGISTRY_V1. It binds the two exact
commits, 29 reviewed source postimages, 34 executable sources plus one config,
four finite migration test postimages, two exact checkout-rendering files, added
collected node IDs, and executable
coverage line inventories. Its legacy identity is a reproduction identity,
not a claim about an original financial receipt. Windows runtime bytes and Linux
Git bytes are distinguished; Windows evidence does not certify Linux execution.
The workflow pins a new anchor covering the unchanged legacy checker, current
loader, C01 verifier and registry. The predecessor anchor, workflow Git object,
470-object manifest, collection and all receipts remain intact. Schema, exact
commits, file contents, original nodes, skip identities and postimages are
validated; an unknown version or arbitrary ref is an error.

The rendering file fixes LF for exactly five CSMAR files that were LF in the
reviewed Windows source. It does not change their Git blobs or the 470-object
freeze. Other Windows closure files retain their reviewed CRLF bytes. A checkout
whose runtime bytes differ is refused, even if Git's text filtering would hide
the difference. No historical receipt is rewritten to fix checkout rendering.
The second rendering file preserves the exact registry and anchor JSON bytes
for the workflow pin, following the existing evidence directory convention.

Publication preparation on 2026-10-22 separates the 17 historical CSMAR audit
files from public derivatives. Original objects and the accepted C01 candidate
are retained in a private bundle; they are excluded from the publication
ancestry. The safe source snapshot dabdc87b80d3c88ccf56034981a3c5cf0710ed63
has original main as its parent, the same 35 source/config identities and the
complete reviewed implementation. Its audit derivatives have new paths and
hashes. The registry records the original commit, original blob and SHA256,
and each public derivative SHA256. Historical JUnit projections retain failure
and error outcomes; they are explicitly historical, not current test results.
This changes publication packaging only. The original 470-object freeze,
Golden, PIT receipts, predecessor anchors, financial policy and source runtime
identities remain unchanged. The exact publication scanner and its targeted
negative tests are finite migration postimages under the same workflow anchor.

P1 source reachability update (2026-10-22): registry V2 reconstructs the
source-stage inventory from independently read LEGACY Git objects and exactly
29 workflow-authenticated postimages. Each entry binds its complete path,
regular-file mode, Git blob identity and normalized SHA256. Current files,
tracked modes, migration postimages and the unchanged 35 exact runtime-byte
identities are checked again. The original 470-object freeze and predecessor
receipts remain immutable. The publication scanner uses authenticated content
instead of requiring the historical source commit to be present.

The source commit SHA remains a provenance claim. When that commit is absent,
V2 does not claim to replay its original tree or independently re-prove its
ancestry. Authority for the registered content now comes from the reviewed CI
workflow pin, which authenticates the control anchor, controller and registry;
the registry's inventory digest is a consistency check, not self-approval.
Rehashing a candidate registry and anchor does not replace the trusted workflow
pin. A maintainer who can change that trusted policy remains within the Solo
governance trust boundary. This migration adds no financial certification.

A regression transfers only a synthetic squash main with LEGACY ancestry to
a separate bare repository, then makes a fresh clone without alternates or
development refs. It requires the source commit object to be absent while
controller initialization, historical preservation, publication safety and
real qualification replay pass; incomplete PIT still refuses formal admission.
