# Grok Build external verification (Weaver Forge)

| Field | Value |
|-------|-------|
| Target | [xai-org/grok-build](https://github.com/xai-org/grok-build) @ `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Owner-side status | Documented in `VERDICT.md`, `RESULTS.md`, `CLAIM_REGISTER.md` |
| Independent Witness (C-014) | **`NOT_STARTED`** |

## Published Witness package

**Grok Build narrow clean rebuild Witness package** — [witness-package/README.md](witness-package/README.md)

| Banner | Value |
|--------|-------|
| Package status | **RC5 FIXED IMMUTABLE — NOT READY — Independent Witness handoff not authorized — C-014 NOT_STARTED — RC6-R1–R7 remediation implemented on `main` (pre-tag / prospective RC6 fixed candidate only) — RC6 tag/archive/bundle do not yet exist — NOT READY — Independent Witness reproduction NOT PERFORMED — Independent Witness PASS NONE** |
| Last immutable package version | `1.0.0-rc5` |
| Last immutable canonical package tag | `grok-build-witness-v1.0.0-rc5` (tag `grok-build-witness-v1.0.0-rc5`; annotated tag object `9c01e314249f59945e93597af6ece2e3fb33e6cd`; peeled commit `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07`; tree `97ad93d80480b23a49f1636ff55dae449202aa3c`; archive SHA-256 `5bf6e8f66795ba310ad5b149b721ca1930b5729ab3c568a20559d8dda40e0435`; transfer-bundle SHA-256 `5581b10788f0a3ee7a36982ac1b2468c658afc353fe88da3423298b60344bb2b`) |
| Package commit authority | `annotated_tag_resolution` (peeled commit is the fixed RC5 release identity; distinct from annotated tag object, archive, and transfer-bundle identities) |
| RC5 static disposition | **NOT READY** (Source Weaver); Independent Witness handoff **not authorized** |
| Historical rc4 static audit | COMPLETE (C-027; `evidence/rc4-static-blind-audit/`); disposition **NOT READY**; 40 integrated blockers |
| Current `main` | RC6-R1–R7 remediation implemented (pre-tag / prospective RC6 fixed candidate only); RC6 tag/archive/bundle **absent** |
| Independent Witness reproduction | **NOT PERFORMED** |
| Independent Witness PASS | **NONE** |
| Independent Witness (C-014) | **`NOT_STARTED`** |
| Overall | **`PARTIAL`** |

C2E-1 historically classified the package **READY WITH LIMITATIONS** (C-022); this was superseded. Immutable release history:

| Version | Tag | Peeled commit | Release state | Static audit | Static disposition |
|---------|-----|---------------|---------------|--------------|--------------------|
| `1.0.0-rc1` | `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | FIXED_IMMUTABLE | COMPLETE (C-024) | **NOT READY** |
| `1.0.0-rc2` | `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | FIXED_IMMUTABLE | COMPLETE (C-025) | **NOT READY** |
| `1.0.0-rc3` | `grok-build-witness-v1.0.0-rc3` | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` | FIXED_IMMUTABLE | COMPLETE (C-026; `evidence/rc3-static-blind-audit/`) | **NOT READY** |
| `1.0.0-rc4` | `grok-build-witness-v1.0.0-rc4` | `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` | FIXED_IMMUTABLE | COMPLETE (C-027; `evidence/rc4-static-blind-audit/`) | **NOT READY** |
| `1.0.0-rc5` | `grok-build-witness-v1.0.0-rc5` | `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07` | FIXED_IMMUTABLE | COMPLETE (Source Weaver) | **NOT READY** |

Independent Witness reproduction remains **NOT PERFORMED** for every row; C-014 remains **`NOT_STARTED`**. No readiness PASS is assigned. **RC6 tag does not yet exist.**

### HISTORICAL PRE-TAG / PRE-RC5 STATE

Earlier wording described rc3/rc4/rc5 prospectively (“package content under preparation,” “rc5 tag does not exist,” “technical remediation not yet begun”). Those states are superseded: rc1–rc5 are immutable **NOT READY** history; RC5 Independent Witness handoff is not authorized; current `main` is pre-tag RC6-R1–R7 remediation only.

## Start here (owner evidence)

- [WITNESS_HANDOFF.md](WITNESS_HANDOFF.md)
- [REPRODUCTION.md](REPRODUCTION.md) (owner-side historical)

Witnesses must use [witness-package/WITNESS_RUNBOOK.md](witness-package/WITNESS_RUNBOOK.md), not owner path literals.
