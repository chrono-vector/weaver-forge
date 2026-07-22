# Witness classification — precedence (1.0.0-rc2)

Apply rules **in order**; first matching row governs the **proposed Witness verdict**. Maintainers assign **intake verdict** separately; disagreements stay visible.

| Order | Condition | Proposed verdict |
|------:|-----------|------------------|
| 1 | Proven prohibited **product execution**, deliberate falsification, or material evidence manipulation | **FAIL** |
| 2 | Proven source **commit mismatch**, **image digest mismatch**, build failure, missing artifact, **source tree change**, or **`Cargo.lock` change** | **FAIL** |
| 3 | Evidence cannot establish what occurred (including **missing proof of commit** when required) | **INDETERMINATE** |
| 4 | Build succeeded but independence, cache provenance, procedure, or mandatory evidence is incomplete | **PARTIAL** |
| 5 | Every mandatory condition affirmatively established | **PASS** |

## Clarifications

| Topic | Rule |
|-------|------|
| Wrong commit observed | **FAIL** (when proven) |
| Missing proof of expected commit | **INDETERMINATE** |
| Different artifact SHA-256 vs owner alone | **Not FAIL** by itself |
| Witness role | Proposes verdict in `WITNESS_VERDICT.md` |
| Maintainer role | Assigns intake verdict; may differ with documented rationale |
| Bit-identical reproducibility | **Not** required for narrow rebuild PASS |

## Narrow rebuild PASS checklist (order 5)

Independence, own host, public pins, clean source, digest-pinned image, empty target, `CARGO_INCREMENTAL=0`, exact build command exit 0, artifact produced, static metadata recorded, `product_executed=NO`, `ldd_used=NO`, post-build integrity, required evidence files + manifest.

## Explicit non-upgrades

Witness narrow PASS does **not** establish overall Weaver PASS, functional/security/ops readiness, Windows-native readiness, or C-014 completion.
