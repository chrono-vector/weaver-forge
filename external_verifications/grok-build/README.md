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
| Package status | **RC6 IMMUTABLE HISTORICAL — NOT READY — RC7 IMMUTABLE HISTORICAL — NOT READY AFTER COMPLETED SOURCE WEAVER AUDIT — RC7 NOT ELIGIBLE FOR INDEPENDENT WITNESS HANDOFF — Independent Witness handoff not authorized — C-014 NOT_STARTED — no finding CLEAR/CLOSED — RC8 IMMUTABLE STATIC-AUDIT CANDIDATE (`1.0.0-rc8` / `grok-build-witness-v1.0.0-rc8`) — RC8 artifact generation and verification passed — accepted non-authoritative advisory technical evaluation — formal Source Weaver audit not performed for RC8 — no formal Source Weaver READY/NOT READY decision for RC8 — NOT READY FOR INDEPENDENT WITNESS HANDOFF — Independent Witness reproduction NOT PERFORMED — Independent Witness PASS NONE — no release readiness or production readiness claimed** |
| Current immutable static-audit candidate | `1.0.0-rc8` / `grok-build-witness-v1.0.0-rc8` (annotated tag object `8113d952d3b127d32e138dbf804141f5d1dfb26f`; peeled commit `1de4b4d9523711418390f8331c95988523ef4481`; tree `87b40d8a32ca536a4cdba0eee474f6171c62f6bb`) |
| Last immutable historical NOT READY package version | `1.0.0-rc6` |
| Last immutable historical NOT READY canonical package tag | `grok-build-witness-v1.0.0-rc6` (annotated tag object `c9ce879bb25db54e3d8520f297a8f5d4035ac9a8`; peeled commit `7b76842bfa1adcedf0c00221cb574d9c3175b7e7`; tree `77369ab099414167df658b25eac3adcb4f264eb3`; archive SHA-256 `1f411f65735d6e2f8aeb0cb968d0e6b2108af00ef0a0264dc15daed114da0fee`; transfer-bundle SHA-256 `ed23824246563db17d9adb7e5b5c95b633077b79b2681c04c46d8de544de6d26`) |
| Package commit authority | `annotated_tag_resolution` for tagged package identities; peeled commits are distinct from annotated tag objects, archives, bundles, sidecars, and other artifact identities |
| RC6 static disposition | Immutable historical **NOT READY**; Independent Witness handoff **not authorized** |
| RC7 static disposition | Immutable historical **NOT READY** after completed Source Weaver audit; not eligible for Independent Witness handoff |
| RC8 lifecycle boundary | Immutable static-audit candidate; artifact generation and verification passed; accepted non-authoritative advisory technical evaluation; formal Source Weaver audit not performed for RC8; no formal Source Weaver READY/NOT READY decision exists for RC8 |
| Current `main` | Post-RC8 documentation/status surface; not a new RC, not RC9, not READY, not release-approved, and not authorized for Independent Witness handoff |
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
| `1.0.0-rc7` | `grok-build-witness-v1.0.0-rc7` | `4316b976b086cb7116cabe0c8deaa47159001c09` | FIXED_IMMUTABLE | COMPLETE (Source Weaver static audit of tagged RC7) | **NOT READY** |
| `1.0.0-rc8` | `grok-build-witness-v1.0.0-rc8` | `1de4b4d9523711418390f8331c95988523ef4481` | FIXED_IMMUTABLE static-audit candidate | Artifact generation/verification passed; accepted non-authoritative advisory technical evaluation; formal Source Weaver audit not performed | **No formal Source Weaver READY/NOT READY decision for RC8** |

Independent Witness reproduction remains **NOT PERFORMED** for every row; C-014 remains **`NOT_STARTED`**. No readiness PASS is assigned. RC6 and RC7 remain immutable historical **NOT READY** candidates. RC8 is an immutable static-audit candidate only; RC8 artifact generation and verification passed, but no formal Source Weaver READY/NOT READY decision exists for RC8.

### HISTORICAL PRE-TAG / PRE-RC6 STATE

Earlier wording described rc3/rc4/rc5/rc6 prospectively (“package content under preparation,” “rc5/rc6 tag does not exist,” “technical remediation not yet begun,” “prospective RC6”) and later described RC7/RC8 prospectively. Those states are superseded: rc1–rc6 are immutable **NOT READY** history; RC6 Independent Witness handoff is not authorized; RC7 is immutable historical **NOT READY** after completed Source Weaver audit and is not eligible for Independent Witness handoff; RC8 is an immutable static-audit candidate with passed artifact generation/verification, no formal Source Weaver audit, no formal Source Weaver READY/NOT READY decision, and no Independent Witness authorization.

## Start here (owner evidence)

- [WITNESS_HANDOFF.md](WITNESS_HANDOFF.md)
- [REPRODUCTION.md](REPRODUCTION.md) (owner-side historical)

If a future formal Independent Witness route is separately authorized, witnesses must use [witness-package/WITNESS_RUNBOOK.md](witness-package/WITNESS_RUNBOOK.md), not owner path literals. No Independent Witness handoff is authorized by this document.
