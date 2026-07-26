# Weaver Forge — Daily Commit Lab

**A proof-of-work builder community for ML, Deep Learning, DSA, MLOps, AI systems, replay/evidence systems, and AI governance.**

### Motto
**Build. Test. Commit. Receipt. Repeat.**

### Secondary Law
**No commit. No claim. No receipt. No authority.**

### Differentiator
Most groups reward talking. We require receipts.

---

## Our Loop
Learn → Build → Test → Commit → Receipt → Review → Improve

## Culture
- No fake progress
- No hype without evidence
- Claims require receipts
- Failed experiments are welcome when documented
- Builders only

## Tracks
- **ML Foundations**
- **Deep Learning**
- **DSA**
- **Weaver Systems** (receipt ledgers, claim registries, replay tools, governance systems)

## How to Participate
1. Join our [Discord](https://discord.gg/YOUR_INVITE) (replace with actual link)
2. Read the rules and templates in this repo
3. Introduce yourself and post your first receipt

## Repository Purpose
This GitHub repository is the **official evidence layer** for Weaver Forge.

**Build. Test. Commit. Receipt. Repeat.**

## Validate Receipts

Check that every file in `receipts/` includes the required sections and a `Commit:` line:

```bash
python scripts/validate_receipts.py
```

Exit code `0` means all receipts passed; `1` means at least one receipt is missing required fields.

## Published External Verification Packages

| Package | Status |
|---------|--------|
| [Grok Build narrow clean rebuild Witness package](external_verifications/grok-build/witness-package/README.md) | **NOT READY** — RC5 FIXED IMMUTABLE — NOT READY — Independent Witness handoff not authorized — C-014 NOT_STARTED — RC6-R1–R7 remediation implemented on `main` (pre-tag / prospective RC6 fixed candidate only) — RC6 tag/archive/bundle do not yet exist — NOT READY — Independent Witness reproduction NOT PERFORMED — Independent Witness PASS NONE; last immutable identity: tag `grok-build-witness-v1.0.0-rc5`; annotated tag object `9c01e314249f59945e93597af6ece2e3fb33e6cd`; peeled commit `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07`; tree `97ad93d80480b23a49f1636ff55dae449202aa3c`; archive SHA-256 `5bf6e8f66795ba310ad5b149b721ca1930b5729ab3c568a20559d8dda40e0435`; transfer-bundle SHA-256 `5581b10788f0a3ee7a36982ac1b2468c658afc353fe88da3423298b60344bb2b`; overall **PARTIAL** |

## Independent reproduction

See [REPRODUCE.md](REPRODUCE.md) for clone prerequisites, validation commands, GitHub Actions checks, and witness review steps.