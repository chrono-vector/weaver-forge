RC4 BATCH 1 — PART 1 OF 4
Part-1 scope

This part covers the documentation-facing portion of RC4 Batch 1:

rc1–rc4 release-history representation;
rc4 package version and canonical tag;
annotated-tag authority;
detached package identity requirements at the normative-document level;
absence of a self-referential rc4 commit placeholder;
time-stable tag wording;
public discoverability;
canonical platform boundaries.
The already completed bundle/archive verification and isolated extraction were not repeated.
No executable, validator, test, build tool, or Witness script was run.
1. RC1–RC4 immutable-history representation
Finding 1.1 — rc1, rc2, and rc3 identities and audit results are consistently preserved

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/README.md
Heading/table: package identity and Historical immutable releases
Lines: 10–12, 70–78
The package records:
rc1 → 89127c78c3a11492892de7e3b5f0dee18d71775a → NOT READY
rc2 → 255b357c9ee33c4a9e34b5d9b6e396c53cfe494e → NOT READY
rc3 → 77221a224bbd6194cfafb81f6ecb58c800e5bc13 → NOT READY

It also states that these tags must not be moved, deleted, or force-updated.

Finding 1.2 — The dedicated release-identity document preserves the same history

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
Heading: Immutable historical releases
Lines: 24–32
The same three tag/commit pairs and audit outcomes are recorded without retroactively upgrading their readiness.
Finding 1.3 — rc4 immutability is described as applying after publication

Classification: CLEAR WITH LIMITATIONS

Path: external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
Heading: Canonical package identity model and release policy
Lines: 49, 59–64, 84
The document says the rc4 tag becomes immutable after successful publication and must not be moved, recreated, or force-updated.
The fixed rc4 tag now exists and resolves to:
039b46737c5968a81fb756d7a6d1d0dd57b6ad96

but the tagged documentation still describes rc4 publication as a future state. The immutability rule is sound, but the snapshot does not record rc4 itself in the historical-release table.

Finding 1.4 — Public rollups preserve rc1–rc3 as historical NOT READY releases

Classification: CLEAR

Path: external_verifications/grok-build/README.md
Lines: 22–26
Path: external_verifications/grok-build/WITNESS_HANDOFF.md
Lines: 6–12
Path: external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md
Lines: 81–90
All three prior release identities are consistently retained.
Part-1 limitation carried forward

The requested scope refers to rc1–rc4 immutable history, but rc4 is represented as a package candidate that will become immutable rather than as the already-existing fixed tag being audited. The actual archive identity proves rc4 exists, but the tagged documentation itself does not yet record rc4 as a published immutable release.

2. RC4 package version and canonical tag
Finding 2.1 — Package version is consistently 1.0.0-rc4

Classification: CLEAR
Representative paths:

README.md:56
external_verifications/grok-build/README.md:15–18
external_verifications/grok-build/VERDICT.md:6, 25, 56–58
external_verifications/grok-build/RESULTS.md:6, 44
external_verifications/grok-build/WITNESS_HANDOFF.md:6, 11
external_verifications/grok-build/witness-package/README.md:5–9
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md:5–8
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md:1–8
The inspected current-facing package documents consistently use:
1.0.0-rc4
Finding 2.2 — Canonical tag is consistently exact

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/README.md
Lines: 5–9, 30–36
Path: external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
Lines: 5–7, 38–47
Path: external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
Lines: 1–8, 48, 57–60
The exact canonical tag is:
grok-build-witness-v1.0.0-rc4

No inspected current package document designates another rc4 tag as canonical.

Finding 2.3 — Public root entry names the same package/tag pair

Classification: CLEAR

Path: README.md
Heading: Published External Verification Packages
Lines: 52–56
The root repository directly links the package and displays its rc4 version/tag.
3. Annotated-tag resolution authority
Finding 3.1 — Package authority is explicitly annotated_tag_resolution

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/README.md
Lines: 5–9
Path: external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
Lines: 5–7, 34–49
Path: external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
Lines: 5–8, 57–66
The package consistently states:
package_commit_authority=annotated_tag_resolution
Finding 3.2 — Exact annotated-tag commit dereference is normative

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
Heading: Canonical package identity model
Lines: 38–47
The required reference is:
refs/tags/grok-build-witness-v1.0.0-rc4^{commit}

The resulting value must be one full 40-character commit.

Finding 3.3 — Runbook requires the same exact dereference

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
Heading: package commit authority
Lines: 57–66
It requires the annotated tag to be resolved, checked out detached, and compared to HEAD.
Finding 3.4 — Resolution failure is consistently fatal for canonical execution

Classification: CLEAR

README.md:56
external_verifications/grok-build/README.md:17–18
external_verifications/grok-build/witness-package/README.md:9, 36
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md:18–20, 49
The normative identity model does not permit floating main to silently substitute for a missing tag.
4. Detached package HEAD and clean clone requirements
Finding 4.1 — Detached checkout is explicitly required

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
Lines: 40–47
The canonical procedure:
fresh-clones Weaver Forge;
fetches tags;
resolves the annotated rc4 tag;
checks out the resolved commit detached.
Finding 4.2 — Detached HEAD must equal the resolved tag commit

Classification: CLEAR

Path: same
Lines: 42–46
The normative comparison is explicit.
Finding 4.3 — Package clone must be clean

Classification: CLEAR

Path: same
Lines: 45–47
The clean-state requirement is part of the recorded package identity evidence.
Finding 4.4 — Requirements document agrees with the identity model

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md
Fields: package revision and Weaver Forge package commit
Lines: 77, 92–104
It requires:
the exact annotated tag;
detached HEAD;
HEAD equality with the resolved commit;
clean package clone;
no embedded expected-commit placeholder.
The executable enforcement inside run_witness_narrow_build.sh will be traced in a later Batch-1 part.
5. Absence of a self-referential rc4 commit placeholder
Finding 5.1 — Self-reference is explicitly rejected by design

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md
Lines: 49–55
The package explains that embedding its own future commit would create circular identity because modifying the tree changes the commit.
Finding 5.2 — Optional external expected commit is additional only

Classification: CLEAR

Path: same
Lines: 55–56
Path: external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md
Line: 104
WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT:
is optional;
must not be stored as a placeholder;
cannot replace annotated-tag authority;
must match the resolved tag commit and detached HEAD when supplied.
Finding 5.3 — Current documents consistently state “no embedded future rc4 commit”

Classification: CLEAR
Representative paths:

external_verifications/grok-build/README.md:18
external_verifications/grok-build/VERDICT.md:58
external_verifications/grok-build/WITNESS_HANDOFF.md:11
external_verifications/grok-build/witness-package/README.md:7, 68
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md:8, 60
No inspected normative file requires the package to contain:
039b46737c5968a81fb756d7a6d1d0dd57b6ad96

inside its own tagged tree.

6. Time-stable tag wording
Finding 6.1 — Annotated-tag resolution wording itself is time-stable

Classification: CLEAR
The following rule remains valid before and after publication:

Canonical execution requires successful resolution of
refs/tags/grok-build-witness-v1.0.0-rc4^{commit}.
If resolution fails, canonical execution stops.

Representative paths:

external_verifications/grok-build/witness-package/README.md:9, 36
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md:38–49
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md:57–66
Finding 6.2 — Current status banners still say rc4 is pending, under preparation, or not yet tagged

Classification: BLOCKED
Exact examples:

README.md:56

rc4 package content under preparation

external_verifications/grok-build/README.md:15

RC4 PACKAGE CONTENT UNDER PREPARATION — NOT READY PENDING RC4 COMMIT, TAG AND RE-AUDIT

external_verifications/grok-build/README.md:22

remains NOT READY until rc4 is committed, tagged, and repeat-audited

external_verifications/grok-build/VERDICT.md:56

NOT READY PENDING RC4 COMMIT, TAG AND RE-AUDIT

external_verifications/grok-build/VERDICT.md:66

Package remains NOT READY until rc4 is committed, tagged, and repeat-audited.
external_verifications/grok-build/witness-package/README.md:8, 64
external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md:8, 15, 64
external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md:394–403
external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md:61–73
These are normative current-state assertions inside the fixed rc4 tag, but the rc4 tag and commit already exist.
They directly fail the requested confirmation:
no normative statement says rc4 is pending or absent
Finding 6.3 — Some documents claim time-stable rc4 wording was applied

Classification: BLOCKED

Path: external_verifications/grok-build/RESULTS.md
Lines: 250–251
Path: external_verifications/grok-build/CLAIM_REGISTER.md
Change log: lines 511–512
Path: external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
Change log: line 418
These entries claim that normative “tag absent/pending” assertions were removed or that time-stable rc4 wording was applied.
That claim is contradicted by the current status banners and “until rc4 is committed, tagged” sentences listed above.
Finding 6.4 — Historical pre-tag language is clearly labelled for rc3

Classification: CLEAR

Path: external_verifications/grok-build/README.md
Lines: 24–26
Path: external_verifications/grok-build/witness-package/README.md
Lines: 80–82
Path: external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md
Lines: 407–410
The rc3 pre-tag wording is properly identified as historical and superseded.
The defect is not the quoted historical rc3 wording; it is the current normative rc4-pending wording.
7. Public discoverability
Finding 7.1 — Root repository exposes the Witness package directly

Classification: CLEAR

Path: README.md
Lines: 52–56
The package is linked from a top-level public entry point.
Finding 7.2 — Grok Build verification README links directly to the package

Classification: CLEAR

Path: external_verifications/grok-build/README.md
Heading: Published Witness package
Lines: 9–18, 28–33
A reader is directed to:
external_verifications/grok-build/witness-package/README.md

and then to the runbook.

Finding 7.3 — Owner-side documents identify the canonical Witness starting point

Classification: CLEAR

Path: external_verifications/grok-build/VERDICT.md
Lines: 50–52
Path: external_verifications/grok-build/WITNESS_HANDOFF.md
Lines: 13–17
The canonical package is discoverable without requiring private owner contact.
Finding 7.4 — Package README provides an ordered navigation path

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/README.md
Heading: Read next
Lines: 50–60
It links:
version identity;
requirements;
runbook;
classification;
submission;
redaction;
evidence manifest;
validator documentation;
templates.
Finding 7.5 — Discoverability is weakened by the stale “under preparation” status

Classification: CLEAR WITH LIMITATIONS
The package is easy to find, but a public reader who lands on the fixed tag is told that the same tag has not yet been committed or published. This does not hide the package, but it creates avoidable uncertainty about whether the fixed rc4 snapshot is actually the intended audit target.

8. Canonical platform boundaries
Finding 8.1 — Linux and WSL2 with linux/amd64 Docker are canonical

Classification: CLEAR

Path: external_verifications/grok-build/witness-package/README.md
Lines: 20–24
The intended Witness is an independent user operating:
Linux or WSL2 host
linux/amd64 Docker
Finding 8.2 — PowerShell-native execution is explicitly noncanonical

Classification: CLEAR

Path: same
Line: 24
Finding 8.3 — Windows-native Rust remains BLOCKED

Classification: CLEAR

Path: same
Line: 24
Finding 8.4 — macOS Docker is explicitly unvalidated/noncanonical

Classification: CLEAR

Path: same
Line: 24
Finding 8.5 — Platform boundary is visible before the runbook

Classification: CLEAR
The package does not bury the Linux/WSL2 restriction only in a later script; it appears in the first public package page.

Part-1 blockers carried forward
Current normative documents falsely describe the already-fixed rc4 tag as still under preparation, pending commit/tag, or not yet published.
Several change-log/status claims state that current tag-pending assertions were removed, but those assertions remain.
The tagged snapshot does not represent rc4 itself as an already-published immutable release, even though the fixed tag now exists.
Part-1 non-fatal limitations carried forward
Public discoverability is strong, but stale pre-publication status wording can make an external auditor unsure whether rc4 is the intended fixed target.
rc4 immutability is correctly defined prospectively, but its already-published state is not reflected inside the snapshot.
This part confirmed normative detached/clean package requirements; executable enforcement is deferred to a later Batch-1 part.
No final package-readiness verdict is issued in this part.