# Witness classification — precedence (1.0.0-rc3)

Applies to package version **1.0.0-rc3** (canonical package tag
`grok-build-witness-v1.0.0-rc3`; package commit authority =
`annotated_tag_resolution`).
Superseded rc2 text (tag `grok-build-witness-v1.0.0-rc2`, commit
`255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`) and rc1 text (tag `grok-build-witness-v1.0.0-rc1`,
commit `89127c78c3a11492892de7e3b5f0dee18d71775a`) remain visible only through immutable git
history at those tags; this file states **current** policy only.

Apply rules **in order**; the first matching row governs the **proposed Witness verdict**
recorded in `WITNESS_VERDICT.md`. Maintainers assign an **intake verdict** separately, using
[MAINTAINER_INTAKE_POLICY.md](MAINTAINER_INTAKE_POLICY.md); the two are never merged into one
field, and disagreements between them stay visible rather than being silently resolved.

## Deviation severity (authoritative definitions)

Every deviation recorded in `DEVIATIONS.txt` (see [templates/DEVIATIONS.txt](templates/DEVIATIONS.txt))
must be assigned exactly one of the following four severities. Each severity ties to an exact
verdict-ceiling constraint — the **highest** (best) proposed verdict the Witness is permitted to
select in `WITNESS_VERDICT.md`, given that deviation:

| Severity | Meaning | Verdict ceiling |
|----------|---------|------------------|
| `NONE` | No deviation from the canonical published procedure/identity occurred. | No restriction imposed by this deviation. |
| `NONMATERIAL_DISCLOSED` | A disclosed deviation that does not touch canonical identity fields (`WEAVER_FORGE_URL`, `WEAVER_FORGE_TAG`, `GROK_BUILD_URL`, `GROK_BUILD_COMMIT`, `RUST_IMAGE`, `EXPECTED_CARGO_LOCK_SHA256`, `BUILD_CMD`) and does not alter the meaning of any mandatory evidence field (e.g. optional parallelism flags, cosmetic path differences, non-mandatory apt package version drift). | Ceiling **PARTIAL**. Never PASS: a canonical run with zero accepted deviations is required for PASS (see the PASS checklist below). |
| `MATERIAL_NONCANONICAL` | A disclosed deviation that changes procedure in a way that could plausibly affect what was actually built or verified, but is not itself an identity mismatch against a canonical pinned value (e.g. running on an unsupported host route, using `--allow-nonempty-work-root`, omitting a mandatory static-inspection command). | Ceiling **must not be `PASS`** (validator-enforced). Default: **PARTIAL**; escalate to **FAIL** or **INDETERMINATE** per the precedence table below when the deviation coincides with a listed FAIL/INDETERMINATE condition. |
| `PROHIBITED` | A deviation that is forbidden outright regardless of disclosure (product execution, `ldd` use, running against a non-canonical Grok Build commit/image/`Cargo.lock`/build command without going through the identity-mismatch path, deliberate falsification, or material evidence manipulation). | Ceiling **must be exactly `FAIL`** (validator-enforced; no other value is accepted). |

`--noncanonical-deviation` accepted by the host orchestrator is a **disclosure mechanism**, not
an approval mechanism: accepting the flag never raises a ceiling, it only permits the run to
proceed instead of aborting, and every accepted deviation must still be recorded and classified
using this table.

## Precedence table

Apply **in order**; the first matching row governs. Rows are intentionally more specific than a
single generic "mismatch" bucket so that overlapping-defect cases (e.g. identity mismatch
*combined with* a missing artifact) resolve deterministically to the earliest-listed, most severe
applicable row.

| Order | Condition | Proposed verdict |
|------:|-----------|-------------------|
| 1 | Proven **product execution** (any invocation of `xai-grok-pager` / `grok`, including `--version`, `--help`, `-h`, TUI, login, agents, OAuth, models, update) | **FAIL** |
| 2 | Proven **`ldd` use** against the built artifact or any other executable | **FAIL** |
| 3 | Deliberate falsification or material evidence manipulation (edited logs/hashes, backdated timestamps, fabricated command output) | **FAIL** |
| 4 | **Canonical package-tag mismatch** — the Weaver Forge tag actually resolved and used is not `grok-build-witness-v1.0.0-rc3`, or the tag could not be resolved on `origin` at all | **FAIL** |
| 5 | **Canonical Weaver Forge commit mismatch** — the commit resolved from the requested tag does not equal the pinned/expected Weaver Forge commit once one is recorded for rc3 | **FAIL** |
| 6 | **Canonical Grok Build commit mismatch** — observed Grok Build `HEAD` after clone/checkout ≠ `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` | **FAIL** |
| 7 | **Canonical Rust image mismatch** — pulled image digest, OS, or architecture does not match the pinned `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` / `linux/amd64` | **FAIL** |
| 8 | **`Cargo.lock` mismatch or change** — SHA-256 before build ≠ `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421`, or the before/after SHA-256 values differ from each other | **FAIL** |
| 9 | **Source change** — Grok Build source tree is not clean (non-empty `git status --porcelain`) at any checked point, or `HEAD` differs before vs. after the build | **FAIL** |
| 10 | **Build failure** — outcome is `CARGO_FAILED` (cargo started, nonzero exit) | **FAIL** |
| 11 | **Missing artifact** — outcome is `CARGO_SUCCEEDED_ARTIFACT_MISSING` (cargo reported success but the expected binary is absent) | **FAIL** |
| 12 | A `PROHIBITED`-severity deviation of any kind not already covered above | **FAIL** |
| 13 | **Insufficient proof** — evidence cannot establish what occurred: outcome is `BUILD_NOT_STARTED` or `INFRASTRUCTURE_FAILURE` for reasons that do not themselves prove a canonical-identity or `Cargo.lock`/source defect (e.g. image pull failure, bootstrap failure before cargo starts, unexplained gaps in mandatory evidence, missing proof of an expected commit) | **INDETERMINATE** |
| 14 | Outcome is `CARGO_SUCCEEDED_ARTIFACT_PRESENT`, all canonical identities matched, `Cargo.lock`/source unchanged, but independence, cache provenance, procedure, or any mandatory evidence file is incomplete, **or** any `MATERIAL_NONCANONICAL`/`NONMATERIAL_DISCLOSED` deviation was accepted for this run | **PARTIAL** (or the specific deviation's own ceiling from the table above, whichever is stricter) |
| 15 | Outcome is `CARGO_SUCCEEDED_ARTIFACT_PRESENT`, every mandatory condition in the PASS checklist below is affirmatively established, `canonical_run=yes` (zero accepted deviations of any severity) | **PASS** |

**Successful canonical run with a nonmaterial disclosed limitation** (row 14, `NONMATERIAL_DISCLOSED`
severity only) is capped at **PARTIAL** — never `INDETERMINATE` or `FAIL` on that basis alone, and
never `PASS`.

## Clarifications

| Topic | Rule |
|-------|------|
| Wrong commit/tag/image/lock observed (rows 4–8) | **FAIL** whenever proven, regardless of whether it was disclosed via `--noncanonical-deviation` |
| Missing proof of an expected commit (evidence gap, not a proven wrong value) | **INDETERMINATE** (row 13) |
| Different artifact SHA-256 vs. the owner's historical artifact alone | **Not FAIL** by itself — bit-identical reproducibility is never required |
| Witness role | Proposes a verdict in `WITNESS_VERDICT.md`; never assigns the maintainer intake value |
| Maintainer role | Assigns intake verdict per [MAINTAINER_INTAKE_POLICY.md](MAINTAINER_INTAKE_POLICY.md); may differ from the Witness proposal with documented rationale |
| Bit-identical reproducibility | **Not** required for narrow rebuild PASS |
| Failure submissions | A truthful `FAIL`, `INDETERMINATE`, or negative-outcome submission is a **valid, acceptable** Witness submission and must never be discouraged, hidden, or reclassified upward to obtain a nominally better status |
| Orchestrator `verdict_ceiling` vs. this document | The host orchestrator (`scripts/run_witness_narrow_build.sh`) computes an advisory `verdict_ceiling` for identity-override deviations. This document is authoritative. Where the orchestrator's computed ceiling is looser than the ceiling this table would assign to the same deviation (for example, an accepted `WEAVER_FORGE_TAG` override), the Witness **must** apply this document's stricter ceiling when completing `WITNESS_VERDICT.md`, and must record the discrepancy in `DEVIATIONS.txt`. Reconciling the orchestrator's computed value with this table is tracked as an open script-alignment item and is **not** performed as part of this documentation pass. |

## Narrow rebuild PASS checklist (row 15)

All of the following, affirmatively established, with matching evidence files:

- Independence (own host, not owner/package author, not an owner-side reproducer)
- Public pins only; no owner caches used as inputs
- Canonical package tag resolved with matching commit (once pinned)
- Clean source at the canonical Grok Build commit, before and after the build
- Digest-pinned Rust image, platform `linux/amd64` confirmed via `docker inspect`
- New empty `CARGO_TARGET_DIR`, confirmed empty on host **and** in-container before the build
- `CARGO_INCREMENTAL=0`
- Exact canonical build command, exit code `0`
- Outcome `CARGO_SUCCEEDED_ARTIFACT_PRESENT`; artifact present with recorded SHA-256/size
- Static metadata recorded (`file`, `readelf -h`/`-n`/`-d`, `objdump -f`); artifact never executed
- `product_executed=NO`, `ldd_used=NO` on every file that declares those fields
- Post-build integrity confirmed (source `HEAD` and `Cargo.lock` unchanged)
- All mandatory evidence files present, non-placeholder, and listed correctly in the **final**
  `EVIDENCE_MANIFEST.sha256` (structural validator PASS)
- `canonical_run=yes` — zero accepted deviations of any severity for this run
- `deviation_state=NONE` in `DEVIATIONS.txt`

## Explicit non-upgrades

A Witness narrow-rebuild `PASS` does **not** establish:

- Overall Weaver Forge / Grok Build package `PASS`
- Functional, security, or operational readiness of the product
- Windows-native build readiness (still `BLOCKED`)
- Independent Witness claim **C-014** completion by itself — C-014 transitions only per the
  maintainer intake rule in [MAINTAINER_INTAKE_POLICY.md](MAINTAINER_INTAKE_POLICY.md)
- Package readiness (`READY` / `READY WITH LIMITATIONS`) — see [PACKAGE_READINESS_POLICY.md](PACKAGE_READINESS_POLICY.md),
  which governs the package as a whole, not a single run's verdict

## Change log

| Version | Change |
|---------|--------|
| 1.0.0-rc1 | Initial precedence table (5 ordered rules) |
| 1.0.0-rc2 | Unchanged from rc1 at the tagged commit; found materially incomplete by the rc2 integrated four-batch static blind audit (`RB-025`: precedence table did not cover overlapping-defect cases) |
| 1.0.0-rc3 | Explicit per-condition FAIL/INDETERMINATE/PARTIAL mapping (product execution, `ldd` use, tag/commit/image/`Cargo.lock`/source mismatch, build failure, missing artifact, insufficient proof, nonmaterial-limitation ceiling); formal deviation-severity-to-ceiling table (`NONE`/`NONMATERIAL_DISCLOSED`/`MATERIAL_NONCANONICAL`/`PROHIBITED`); explicit Witness-proposed vs. maintainer-intake separation with a pointer to `MAINTAINER_INTAKE_POLICY.md`; orchestrator-ceiling reconciliation note added as a disclosed known gap (RB-025 remediation) |
