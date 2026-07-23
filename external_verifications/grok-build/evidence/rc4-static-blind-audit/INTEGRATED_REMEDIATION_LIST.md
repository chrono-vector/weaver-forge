# RC4 static blind audit — integrated remediation list

Preserved from `RC4_BATCH_4_FINAL_INTEGRATED.md` sections 14–15. This is a remediation **plan** derived from the static audit. **No remediation implementation has begun.** Every item maps to one or more `RC4B` IDs. Status of every remediation item below: **NOT_STARTED**.

No new candidate tag should be created before the mandatory sequence is complete.

---

## Minimal mandatory remediation sequence

### 1. Correct release and status truthfulness

| Field | Value |
|-------|-------|
| Actions | update all current banners; record rc4 as fixed immutable history; narrow closure claims; correct claim-register and rollup semantics |
| Maps to RC4B IDs | `RC4B-001`, `RC4B-002`, `RC4B-003` |
| Status | NOT_STARTED |

### 2. Correct host filesystem and source-mount safety

| Field | Value |
|-------|-------|
| Actions | remove the `/work/grok-build` writable source alias; mount only narrow writable directories; move every Docker call after identity closure; enforce raw annotated-tag type |
| Maps to RC4B IDs | `RC4B-004`, `RC4B-005`, `RC4B-010`, `RC4B-019` |
| Status | NOT_STARTED |

### 3. Correct evidence-directory atomicity and run provenance

| Field | Value |
|-------|-------|
| Actions | atomically create an absent `EVIDENCE_DIR`; reject collisions; introduce one immutable run ID across all evidence; reject mixed-run content |
| Maps to RC4B IDs | `RC4B-008`, `RC4B-025` |
| Status | NOT_STARTED |

### 4. Make every failure path generator-complete

| Field | Value |
|-------|-------|
| Actions | one common host finalizer; one common container finalizer; all mandatory files receive exact final schemas; no final `NOT_REACHED` |
| Maps to RC4B IDs | `RC4B-011`, `RC4B-012`, `RC4B-024`, `RC4B-029` |
| Status | NOT_STARTED |

### 5. Establish exact generator/template/validator equality

| Field | Value |
|-------|-------|
| Actions | exact allowed keys; conditional schemas; no unknown keys; align post-build, deviation, host metadata, Docker exit, timing, and every other writer |
| Maps to RC4B IDs | `RC4B-006`, `RC4B-016`, `RC4B-021` |
| Status | NOT_STARTED |

### 6. Make outcome authority and post-build integrity fail-closed

| Field | Value |
|-------|-------|
| Actions | remove outcome inference; enforce one full cross-file tuple; require all post-build integrity fields; write truthful status; gate host zero on complete structural validity |
| Maps to RC4B IDs | `RC4B-013`, `RC4B-014`, `RC4B-015`, `RC4B-017`, `RC4B-022`, `RC4B-023`, `RC4B-019` |
| Status | NOT_STARTED |

### 7. Cryptographically close the full object inventory

| Field | Value |
|-------|-------|
| Actions | manifest every regular file; reject nested files, directories, symlinks, FIFOs, sockets, devices, and unknown objects; eliminate auxiliary exemptions |
| Maps to RC4B IDs | `RC4B-020`, `RC4B-026`, `RC4B-027`, `RC4B-028` |
| Status | NOT_STARTED |

### 8. Bind manual forms, deviations, verdict, and redaction

| Field | Value |
|-------|-------|
| Actions | add run/tag/commit/outcome identity to statement and verdict; enforce pending initial intake; align deviations; require numeric contiguous indices; aggregate ceilings; categorically bar noncanonical/deviation-present PASS; bind redactions to exact keys and markers |
| Maps to RC4B IDs | `RC4B-007`, `RC4B-030`, `RC4B-031`, `RC4B-032`, `RC4B-033`, `RC4B-034`, `RC4B-035`, `RC4B-036`, `RC4B-037` |
| Status | NOT_STARTED |

### 9. Make correction and intake immutable

| Field | Value |
|-------|-------|
| Actions | never mutate original Witness evidence; move maintainer intake to a separate append-only record; create complete superseding packages; preserve original and corrected manifests |
| Maps to RC4B IDs | `RC4B-038`, `RC4B-039` |
| Status | NOT_STARTED |

### 10. Add behavioral generator-backed tests

| Field | Value |
|-------|-------|
| Actions | Test: every supported outcome; all failure finalizers; exact schema output; mount isolation; run provenance; mixed-run rejection; full manifest closure; PASS prevention; correction/intake lifecycle |
| Maps to RC4B IDs | `RC4B-009`, `RC4B-018`, `RC4B-040`, `RC4B-019` |
| Status | NOT_STARTED |

### 11. Correct all public claims and rollups

| Field | Value |
|-------|-------|
| Actions | distinguish audit completion from readiness; distinguish readiness from Independent Witness reproduction; keep C-014 unchanged; record this rc4 static disposition as NOT READY |
| Maps to RC4B IDs | `RC4B-001`, `RC4B-002`, `RC4B-003` (claim/rollup truthfulness); Phase 0 intake records disposition without claiming readiness |
| Status | Phase 0 audit-recording portion in progress via claim intake only; underlying wording remediation **NOT_STARTED** |

### 12. Create and re-audit a new fixed candidate

| Field | Value |
|-------|-------|
| Actions | Only after all above: commit remediation; create a new annotated candidate tag; archive it; repeat static blind audit from the fixed snapshot; consider Independent Witness handoff only after a READY or qualifying READY WITH LIMITATIONS static result |
| Maps to RC4B IDs | All (`RC4B-001`–`RC4B-040`) as precondition for successor candidacy |
| Status | NOT_STARTED |

---

## Recommended hardening after mandatory remediation

(From Batch 4 section 15; not blockers; recommended after mandatory items.)

- Publish machine-readable schemas for every evidence file.
- Normalize boolean and status vocabularies.
- use cryptographically random run IDs or `mktemp -d`.
- separate automated staging from immutable final submission directories.
- record full Rust/Cargo version provenance.
- define exact protoc identity policy.
- capture or hash apt and DotSlash logs.
- use exact normalized RepoDigest matching.
- capture Docker inspect stderr and direct exits.
- execute Cargo through a direct argument vector rather than `bash -c`.
- add detached signed final-submission metadata.
- add distinct validator modes for: initial Witness submission; maintainer intake; corrected/superseding package.
- add explicit conflict-of-interest and public identity metadata for Witnesses.
- add filesystem-level read-only sealing after final manifest creation.

Related RC4B themes (hardening supports, does not close): `RC4B-005`, `RC4B-007`, `RC4B-009`, `RC4B-016`, `RC4B-018`, `RC4B-021`, `RC4B-025`, `RC4B-033`, `RC4B-038`, `RC4B-039`, `RC4B-040`.

---

## Coverage check

| Check | Result |
|-------|--------|
| Every RC4B ID appears in at least one mandatory item | Yes (`RC4B-001`–`RC4B-040`) |
| Remediation implementation begun | **No** |
| Blockers closed by this list | **0** |
| Independent Witness / C-014 advanced | **No** / `NOT_STARTED` |
