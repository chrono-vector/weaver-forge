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
| Package status | **RC4 FIXED IMMUTABLE — STATIC BLIND AUDIT COMPLETE — FINAL DISPOSITION NOT READY (40 BLOCKERS) — PHASE 1 DOCUMENTATION REMEDIATION ON MAIN — TECHNICAL IMPLEMENTATION REMEDIATION NOT YET BEGUN — RC5 TAG DOES NOT EXIST — C-014 NOT_STARTED** |
| Package version | `1.0.0-rc4` |
| Canonical package tag | `grok-build-witness-v1.0.0-rc4` (fixed immutable annotated tag; commit `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`) |
| Package commit authority | `annotated_tag_resolution` (resolved commit is the fixed rc4 release identity) |
| Static audit | COMPLETE (C-027; `evidence/rc4-static-blind-audit/`) |
| Static disposition | **NOT READY** |
| Integrated blockers | 40 (`RC4B-001`–`RC4B-040`) |
| Remediation state | Phase 0 audit intake COMPLETE; Phase 1 documentation/status-truthfulness remediation on `main`; technical implementation remediation **NOT YET BEGUN** |
| Successor state | Phase 1 documentation remediation on `main`; technical implementation remediation NOT YET BEGUN; `main` prepared toward possible future rc5 candidate; **rc5 tag does not exist** |
| Independent Witness reproduction | **NOT PERFORMED** |
| Independent Witness PASS | **NONE** |
| Independent Witness (C-014) | **`NOT_STARTED`** |
| Overall | **`PARTIAL`** |

C2E-1 historically classified the package **READY WITH LIMITATIONS** (C-022); this was superseded. Immutable release history:

| Version | Tag | Commit | Release state | Static audit | Static disposition |
|---------|-----|--------|---------------|--------------|--------------------|
| `1.0.0-rc1` | `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | FIXED_IMMUTABLE | COMPLETE (C-024) | **NOT READY** |
| `1.0.0-rc2` | `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | FIXED_IMMUTABLE | COMPLETE (C-025) | **NOT READY** |
| `1.0.0-rc3` | `grok-build-witness-v1.0.0-rc3` | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` | FIXED_IMMUTABLE | COMPLETE (C-026; `evidence/rc3-static-blind-audit/`) | **NOT READY** |
| `1.0.0-rc4` | `grok-build-witness-v1.0.0-rc4` | `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` | FIXED_IMMUTABLE | COMPLETE (C-027; `evidence/rc4-static-blind-audit/`) | **NOT READY** |

Independent Witness reproduction remains **NOT PERFORMED** for every row; C-014 remains **`NOT_STARTED`**. No readiness PASS is assigned.

### HISTORICAL PRE-TAG STATE

Before the rc3 tag existed, this document described rc3 package content as prepared-but-unaudited. That state is superseded: rc3 was tagged and audited (**NOT READY**, C-026). Later, pre-rc4-publication wording described rc4 as “package content under preparation” / “pending commit, tag, and re-audit.” That prospective wording is superseded: rc4 is now the fixed immutable release at the tag/commit above, statically audited **NOT READY** (C-027). Phase 0 audit intake is complete. Phase 1 documentation and release/status remediation is being performed on `main`. Technical implementation remediation of scripts, schemas, validators, tests, and execution controls has not begun. `main` is being prepared toward a possible future rc5 candidate; **no rc5 tag exists**.

## Start here (owner evidence)

- [WITNESS_HANDOFF.md](WITNESS_HANDOFF.md)
- [REPRODUCTION.md](REPRODUCTION.md) (owner-side historical)

Witnesses must use [witness-package/WITNESS_RUNBOOK.md](witness-package/WITNESS_RUNBOOK.md), not owner path literals.
