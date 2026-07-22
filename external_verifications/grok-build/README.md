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
| Package status | **RC3 INTEGRATED STATIC BLIND-AUDIT RECORDED — RC4 PACKAGE CONTENT UNDER PREPARATION — NOT READY PENDING RC4 COMMIT, TAG AND RE-AUDIT** |
| Package version | `1.0.0-rc4` |
| Canonical package tag | `grok-build-witness-v1.0.0-rc4` (availability verified by annotated-tag resolution; canonical execution requires successful resolution; if resolution fails, canonical execution stops) |
| Package commit authority | `annotated_tag_resolution` (no embedded future rc4 commit) |
| Independent Witness (C-014) | **`NOT_STARTED`** |
| Overall | **`PARTIAL`** |

C2E-1 historically classified the package **READY WITH LIMITATIONS** (C-022); this was superseded. **rc1** (immutable tag `grok-build-witness-v1.0.0-rc1`) received a repeat blind audit verdict of **NOT READY** (C-024). **rc2** (immutable tag `grok-build-witness-v1.0.0-rc2`) received an integrated four-batch static blind audit verdict of **NOT READY** (C-025). **rc3** (immutable tag `grok-build-witness-v1.0.0-rc3`, commit `77221a224bbd6194cfafb81f6ecb58c800e5bc13`) received an integrated four-batch static audit verdict of **NOT READY** (C-026); that audit is preserved under `evidence/rc3-static-blind-audit/`. rc1, rc2, and rc3 all remain immutable historical releases. **rc4** package content is under preparation under canonical tag name `grok-build-witness-v1.0.0-rc4` and remains **NOT READY** until rc4 is committed, tagged, and repeat-audited.

### HISTORICAL PRE-TAG STATE

Before the rc3 tag existed, this document described rc3 package content as prepared-but-unaudited. That state is superseded: rc3 has since been tagged and audited (NOT READY, C-026), and rc4 is now the package content under preparation.

## Start here (owner evidence)

- [WITNESS_HANDOFF.md](WITNESS_HANDOFF.md)
- [REPRODUCTION.md](REPRODUCTION.md) (owner-side historical)

Witnesses must use [witness-package/WITNESS_RUNBOOK.md](witness-package/WITNESS_RUNBOOK.md), not owner path literals.
