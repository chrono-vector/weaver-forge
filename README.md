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

## Public / private artifact routing
This repository is intended to function as `WEAVER_FORGE_PUBLIC_CORE`. Before adding operational artifacts, ZIPs, Ingress results, Witness submissions, or Owner evidence, read [PUBLIC_PRIVATE_ARTIFACT_ROUTING.md](PUBLIC_PRIVATE_ARTIFACT_ROUTING.md). Future real operational material must not be added here by default.

## License

Owner-controlled reusable Public Core material — architecture, protocols, schemas, validators, scripts, templates, synthetic fixtures/tests, Independent Witness protocol/tooling/templates, VECTOR Ingress v0 reference code/schema/tests, and public reproducibility/reference documentation — is licensed under Apache-2.0. See [LICENSE](LICENSE), [LICENSE_SCOPE.md](LICENSE_SCOPE.md), and [NOTICE](NOTICE).

This Apache grant does **not** license third-party quoted/copied material, historical evidence records, historical receipts as records, human witness submissions, identity/signature material, Owner operational authorization instances, or Grok Build / xAI / SpaceXAI source. Public visibility is not a license grant. Inclusion in Git history does not relicense excluded content.

## Use and feedback
Weaver Forge is open for research, evaluation, and reproducibility testing.
Users are welcome to try the documented workflows and report reproducible defects through GitHub Issues.
Reports should include:
- operating system
- tag or commit
- commands used
- expected result
- actual result
- relevant logs

## Validate Receipts

Check that every file in `receipts/` includes the required sections and a `Commit:` line:

```bash
python scripts/validate_receipts.py
```

Exit code `0` means all receipts passed; `1` means at least one receipt is missing required fields.

## Published External Verification Packages

| Package | Status |
|---------|--------|
| [VECTOR Package Ingress v0](external_verifications/vector-handoff/README.md) | Separate VECTOR surface from RC8. Read-only package intake/checking boundary under v0 only. **Not** RC8 READY. **Not** Independent Witness. **Not** Evidence admission. **Not** truth verification. **Not** Weaver downstream execution. **Not** Owner approval. **Not** Stage 6. |
| [Grok Build narrow clean rebuild Witness package](external_verifications/grok-build/witness-package/README.md) | **NOT READY** — RC6 immutable historical **NOT READY** — RC7 immutable historical **NOT READY** after completed Source Weaver audit — RC7 not eligible for Independent Witness handoff — Independent Witness handoff not authorized — C-014 **NOT_STARTED** — no finding or blocker CLEAR/CLOSED — RC8 immutable static-audit candidate (`1.0.0-rc8` / `grok-build-witness-v1.0.0-rc8`) — RC8 artifact generation and verification passed — accepted non-authoritative advisory technical evaluation — RC8 Formal Source Evaluation is complete under accepted GOV-004 — final controlling disposition **NOT READY** — F-01–F-04 and B-01–B-05 remain open — Independent Witness reproduction NOT PERFORMED — Independent Witness PASS NONE — no release, production readiness, Independent Witness PASS, or C-014 completion claimed; overall **PARTIAL** |

## VECTOR Package Ingress v0

This repository also hosts a **read-only VECTOR package intake/checking boundary**: [VECTOR Package Ingress v0](external_verifications/vector-handoff/README.md).

It checks package/container/digest/binding/boundary conditions under v0 only. `INGRESS_READY` means those v0 checks passed. It is **not** a truth verifier, Evidence admission, Independent Witness, Weaver downstream execution, Owner approval, or Stage 6.

```text
Observation ≠ Interpretation ≠ Verification ≠ Execution
Schema-valid ≠ True
Replayable ≠ Externally True
REPLAY_ELIGIBLE_BY_CONTRACT ≠ Replay Authorized
Ingress Ready ≠ Evidence Admitted
Ingress Ready ≠ Weaver Execution Authorized
Ingress Ready ≠ Stage 6
Ingress Ready ≠ Independent Witness PASS
```

Public input is a ZIP path only. Do not treat this lab, RC8, or Ingress as VECTOR-the-product.

## RC8 current lifecycle status
RC8 exists as an immutable static-audit candidate.
RC8 artifact generation and verification passed.
RC8 Formal Source Evaluation is complete under accepted GOV-004.
Final controlling disposition: NOT READY.
No formal Source Weaver READY decision exists.
F-01–F-04 and B-01–B-05 remain open.
Independent Witness was not authorized and was not performed.
C-014 is NOT_STARTED.
No finding or blocker is CLEAR or CLOSED.
No release-readiness or production-readiness claim is made.
The README preserved inside the immutable RC8 tag and artifacts may still contain pre-tag wording because it is a preserved historical snapshot. The immutable RC8 tag and artifact contents have not been changed.

## Independent reproduction

See [REPRODUCE.md](REPRODUCE.md) for clone prerequisites, validation commands, GitHub Actions checks, and witness review steps.