# RC4 static blind audit — integrated remediation list

Preserved from `RC4_BATCH_4_FINAL_INTEGRATED.md` sections 14–15. This is a remediation **plan** derived from the static audit. Unless explicitly marked otherwise, remediation items remain **NOT_STARTED**. Documentation-only remediation associated with RC4B-001, RC4B-002, and RC4B-003 is **REMEDIATED_ON_MAIN_PENDING_REAUDIT**. Phase 2A host preflight work on `main` advances RC4B-004 and RC4B-008 to **REMEDIATED_ON_MAIN_PENDING_REAUDIT** after Cursor and Pi both executed the 18-test suite successfully (Pi fourth limited read-only recheck PASS); that status is **not** final closure. Phase 2B source-mount isolation on `main` advances RC4B-010 to **REMEDIATED_ON_MAIN_PENDING_REAUDIT** after Pi corrected-suite read-only recheck PASS (22/22 Phase 2B + 18/18 Phase 2A; prior Pi first corroboration PASS WITH CORRECTIONS REQUIRED BEFORE COMMIT preserved; **not CLOSED**). **REMEDIATED_ON_MAIN_PENDING_REAUDIT is not final closure**; final closure requires a future fixed candidate and repeat static audit. RC4B-005 and RC4B-009 remain **OPEN** with implementation notes (Phase 2B adds only a mount-plan behavioral subset for RC4B-009). **No blocker is CLOSED.** Every item maps to one or more `RC4B` IDs.

No new candidate tag should be created before the mandatory sequence is complete.

---

## Minimal mandatory remediation sequence

### 1. Correct release and status truthfulness

| Field | Value |
|-------|-------|
| Actions | update all current banners; record rc4 as fixed immutable history; narrow closure claims; correct claim-register and rollup semantics |
| Maps to RC4B IDs | `RC4B-001`, `RC4B-002`, `RC4B-003` |
| Status | REMEDIATED_ON_MAIN_PENDING_REAUDIT (Phase 1 documentation/status-truthfulness on `main`; **not CLOSED**; final closure requires future fixed candidate + repeat static audit) |

### 2. Correct host filesystem and source-mount safety

| Field | Value |
|-------|-------|
| Actions | remove the `/work/grok-build` writable source alias; mount only narrow writable directories; move every Docker call after identity closure; enforce raw annotated-tag type |
| Maps to RC4B IDs | `RC4B-004`, `RC4B-005`, `RC4B-010`, `RC4B-019` |
| Status | **PARTIAL (Phase 2A + Phase 2B staged on main):** `RC4B-004` → **REMEDIATED_ON_MAIN_PENDING_REAUDIT** — every Docker CLI is structurally after complete identity closure; pre-gate failure evidence is truthful; Cursor and Pi both executed the 18-test suite successfully in their respective environments. **REMEDIATED_ON_MAIN_PENDING_REAUDIT is not final closure**; final closure requires a future fixed candidate and repeat static audit. `RC4B-005` → **OPEN** (raw `git cat-file -t` equals `tag` enforced; normative exact evidence-schema field integration deferred to Phase 4). `RC4B-010` → **REMEDIATED_ON_MAIN_PENDING_REAUDIT** (Phase 2B): broad `WORK_ROOT`→`/work` writable mount removed; Grok Build source mounted exactly once at `/src` read-only; no writable source alias remains; mount validator is load-bearing; comma/CR/LF mount fields fail closed; missing/canonicalization/overlap failures fail before Docker; pre/post source HEAD and clean-tree checks prevent successful acceptance after mutation; corrected Phase 2B suite passed in Cursor and Pi environments (Pi corrected-suite read-only recheck PASS; prior Pi first corroboration PASS WITH CORRECTIONS REQUIRED BEFORE COMMIT preserved). **REMEDIATED_ON_MAIN_PENDING_REAUDIT is not final closure**; final closure requires a future fixed candidate and repeat static audit; not CLOSED. `RC4B-019` unchanged. **None CLOSED.** |

### 3. Correct evidence-directory atomicity and run provenance

| Field | Value |
|-------|-------|
| Actions | atomically create an absent `EVIDENCE_DIR`; reject collisions; introduce one immutable run ID across all evidence; reject mixed-run content |
| Maps to RC4B IDs | `RC4B-008`, `RC4B-025` |
| Status | **PARTIAL (Phase 2A + Pi fourth limited read-only recheck PASS):** `RC4B-008` → **REMEDIATED_ON_MAIN_PENDING_REAUDIT** — final `EVIDENCE_DIR` uses atomic plain `mkdir`; collisions do not merge or overwrite previous evidence; ordinary collision and link/junction target-survival tests pass; Cursor and Pi both executed the 18-test suite successfully. **REMEDIATED_ON_MAIN_PENDING_REAUDIT is not final closure**; final closure requires a future fixed candidate and repeat static audit. Full run-ID propagation across every evidence file (`RC4B-025`) → **not addressed** (later Phase 2/4). **None CLOSED.** |

### 4. Make every failure path generator-complete

| Field | Value |
|-------|-------|
| Actions | one common host finalizer; one common container finalizer; all mandatory files receive exact final schemas; no final `NOT_REACHED` |
| Maps to RC4B IDs | `RC4B-011`, `RC4B-012`, `RC4B-024`, `RC4B-029` |
| Status | **PARTIAL (Phase 3C container-side + Phase 3D host-side + Phase 3E POST_BUILD):** `RC4B-011` and `RC4B-024` remain **OPEN** (container-side implementation recorded on main; schema/validator alignment incomplete). `RC4B-012` remains **OPEN** — Phase 3D host invalid/missing-result finalization plus Phase 3E complete host-owned FAILED `POST_BUILD` on those paths are recorded on `main`; retains **OPEN** pending validator-gated success (Phase 3F), fixed candidate, and repeat audit. `RC4B-029` remains **OPEN** — host-side truthful failure finalization (Phase 3D) and complete FAILED POST_BUILD finalization (Phase 3E) recorded on main; container-side recorded in Phase 3C; full integration / fixed candidate / repeat audit still required. **Not CLOSED.** |

### 5. Establish exact generator/template/validator equality

| Field | Value |
|-------|-------|
| Actions | exact allowed keys; conditional schemas; no unknown keys; align post-build, deviation, host metadata, Docker exit, timing, and every other writer |
| Maps to RC4B IDs | `RC4B-006`, `RC4B-016`, `RC4B-021` |
| Status | **PARTIAL (Phase 3E POST_BUILD field-set subset only):** `RC4B-016` — the exact POST_BUILD field set is aligned across the centralized host writer, template, validator required-field/schema definition, fixtures_lib, and POST_BUILD fixtures on `main` (**POST_BUILD subset implemented on main pending integration and reaudit**). Broader exact-field-set equality across all writers / all evidence files remains incomplete. `RC4B-006` and `RC4B-021` remain unaddressed by Phase 3E. **RC4B-016 is not CLOSED and is not claimed fully remediated.** |

### 6. Make outcome authority and post-build integrity fail-closed

| Field | Value |
|-------|-------|
| Actions | remove outcome inference; enforce one full cross-file tuple; require all post-build integrity fields; write truthful status; gate host zero on complete structural validity |
| Maps to RC4B IDs | `RC4B-013`, `RC4B-014`, `RC4B-015`, `RC4B-017`, `RC4B-022`, `RC4B-023`, `RC4B-019` |
| Status | **PARTIAL (Phase 3B contract + Phase 3D host tuple ingestion + Phase 3E POST_BUILD):** `RC4B-014` and `RC4B-023` → **IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT** — Phase 3D host parses the complete required tuple (not only `outcome=`), preserves valid container outcomes, and records host-owned ingestion; Phase 3E adds host-owned complete truthful POST_BUILD. **Not CLOSED.** `RC4B-015` → **IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT** — Phase 3E centralizes host POST_BUILD finalization with `status=OK` iff `post_build_integrity_ok=yes` and complete FAILED records on finalized failure paths; pending integration, fixed candidate, and reaudit. **Not CLOSED.** `RC4B-022` remains **CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING** (validator inference unchanged). `RC4B-013` and `RC4B-017` remain **OPEN**. `RC4B-019` remains **OPEN** with Phase 3E host POST_BUILD progress recorded (schema-aligned POST_BUILD does not close broader behavioral/generator coverage). |

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
| Status | **PARTIAL (Phase 2A + Phase 2B):** `RC4B-009` remains **OPEN** — Phase 2A host-safety subset for RC4B-004/005/008 retained; Phase 2B adds a **subset** of required behavioral coverage (mount-plan isolation / writable-alias rejection / argv boundary / pre-post source integrity only). Broader generator-backed outcome/schema/manifest/PASS/correction tests remain outstanding. |

### 11. Correct all public claims and rollups

| Field | Value |
|-------|-------|
| Actions | distinguish audit completion from readiness; distinguish readiness from Independent Witness reproduction; keep C-014 unchanged; record this rc4 static disposition as NOT READY |
| Maps to RC4B IDs | `RC4B-001`, `RC4B-002`, `RC4B-003` (claim/rollup truthfulness); Phase 0 intake records disposition without claiming readiness |
| Status | REMEDIATED_ON_MAIN_PENDING_REAUDIT for public-claim/rollup wording associated with RC4B-001/002/003 (Phase 1); C-027 remains `AUDIT_RECORDING` only; underlying wording remediation for technical readiness remains outside this item |

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
| Remediation implementation begun | Phase 1 documentation/status-truthfulness (RC4B-001/002/003); Phase 2A host preflight (RC4B-004/008 REMEDIATED_ON_MAIN_PENDING_REAUDIT after Cursor + Pi 18/18; RC4B-005/009 remain OPEN with notes; **not CLOSED**); Phase 2B source-mount isolation (RC4B-010 REMEDIATED_ON_MAIN_PENDING_REAUDIT after Cursor + Pi corrected-suite PASS; **not CLOSED**); Phase 3B authoritative outcome ownership contract (RC4B-022 remains CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING; RC4B-014/023 advanced by Phase 3D); Phase 3C container terminal finalization (RC4B-011/024/029 remain OPEN with container-side implementation recorded); Phase 3D host outcome ingestion (RC4B-014/023 → IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT; RC4B-012/029 remain OPEN with host-side implementation recorded; **not CLOSED**); Phase 3E host POST_BUILD integrity (RC4B-015 → IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT; RC4B-016 POST_BUILD field-set subset only — not fully remediated / not CLOSED; RC4B-012/029/019 remain OPEN with Phase 3E progress recorded; RC4B-013/017 remain OPEN; RC4B-022 unchanged; validator-gated success remains Phase 3F; **not CLOSED**) |
| Technical implementation remediation (scripts/validator/tests/templates/execution controls) begun | **Yes — Phase 2A host preflight + Phase 2B mount isolation + Phase 3C container terminal finalization + Phase 3D host outcome ingestion + Phase 3E host POST_BUILD integrity / schema alignment** (Phase 3B is contract/docs/tests only; Phase 3E does not change container script, outcome-contract JSON, or historical Phase 3B/3C/3D notes) |
| Blockers CLOSED | **0** |
| Blockers REMEDIATED_ON_MAIN_PENDING_REAUDIT | RC4B-001, RC4B-002, RC4B-003, RC4B-004, RC4B-008, RC4B-010 |
| Blockers IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT | RC4B-014, RC4B-015, RC4B-023 |
| Blockers CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING | RC4B-022 |
| Blockers OPEN_PENDING_CROSS_ENV_CORROBORATION | *(none)* |
| Independent Witness / C-014 advanced | **No** / `NOT_STARTED` |
