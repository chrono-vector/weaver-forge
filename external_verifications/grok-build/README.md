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
| Package status | **RC6 FIXED IMMUTABLE — NOT READY — Independent Witness handoff not authorized — C-014 NOT_STARTED — no finding CLEAR/CLOSED — next-candidate identity RC7 (`1.0.0-rc7` / `grok-build-witness-v1.0.0-rc7`) fixed in active Host/templates and validator mapping — RC7 tag/archive/bundle do not yet exist — RC7 Source Weaver audit has not occurred — NOT READY — Independent Witness reproduction NOT PERFORMED — Independent Witness PASS NONE** |
| Last immutable package version | `1.0.0-rc6` |
| Last immutable canonical package tag | `grok-build-witness-v1.0.0-rc6` (annotated tag object `c9ce879bb25db54e3d8520f297a8f5d4035ac9a8`; peeled commit `7b76842bfa1adcedf0c00221cb574d9c3175b7e7`; tree `77369ab099414167df658b25eac3adcb4f264eb3`; archive SHA-256 `1f411f65735d6e2f8aeb0cb968d0e6b2108af00ef0a0264dc15daed114da0fee`; transfer-bundle SHA-256 `ed23824246563db17d9adb7e5b5c95b633077b79b2681c04c46d8de544de6d26`) |
| Package commit authority | `annotated_tag_resolution` (peeled commit is the fixed RC6 release identity; distinct from annotated tag object, archive, and transfer-bundle identities) |
| RC6 static disposition | **NOT READY**; Independent Witness handoff **not authorized** |
| Historical rc5 static disposition | **NOT READY** (Source Weaver); Independent Witness handoff **not authorized** |
| Historical rc4 static audit | COMPLETE (C-027; `evidence/rc4-static-blind-audit/`); disposition **NOT READY**; 40 integrated blockers |
| Current `main` | Pre-tag / prospective RC7 next-candidate only; RC7 tag/archive/bundle **absent**; RC7 Source Weaver audit has not occurred |
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
| `1.0.0-rc6` | `grok-build-witness-v1.0.0-rc6` | `7b76842bfa1adcedf0c00221cb574d9c3175b7e7` | FIXED_IMMUTABLE | COMPLETE (immutable candidate published) | **NOT READY** |

Independent Witness reproduction remains **NOT PERFORMED** for every row; C-014 remains **`NOT_STARTED`**. No readiness PASS is assigned. **RC7 tag does not yet exist.**

### HISTORICAL PRE-TAG / PRE-RC6 STATE

Earlier wording described rc3/rc4/rc5/rc6 prospectively (“package content under preparation,” “rc5/rc6 tag does not exist,” “technical remediation not yet begun,” “prospective RC6”). Those states are superseded: rc1–rc6 are immutable **NOT READY** history; RC6 Independent Witness handoff is not authorized; current `main` is pre-tag / prospective RC7 next-candidate only.

## Start here (owner evidence)

- [WITNESS_HANDOFF.md](WITNESS_HANDOFF.md)
- [REPRODUCTION.md](REPRODUCTION.md) (owner-side historical)

Witnesses must use [witness-package/WITNESS_RUNBOOK.md](witness-package/WITNESS_RUNBOOK.md), not owner path literals.
