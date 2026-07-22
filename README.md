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
| [Grok Build narrow clean rebuild Witness package](external_verifications/grok-build/witness-package/README.md) | **NOT READY** — package version `1.0.0-rc3`; canonical tag `grok-build-witness-v1.0.0-rc3` (availability verified by tag resolution); pending fixed-tag repeat blind audit; rc1 and rc2 are immutable historical releases each with a recorded NOT READY audit; Independent Witness (C-014) **NOT_STARTED**; overall **PARTIAL** |

## Independent reproduction

See [REPRODUCE.md](REPRODUCE.md) for clone prerequisites, validation commands, GitHub Actions checks, and witness review steps.