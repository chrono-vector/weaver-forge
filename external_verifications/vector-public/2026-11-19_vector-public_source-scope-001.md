# VECTOR Public Reference v0 — pinned source-scope record 001

**Date:** 2026-11-19 JST
**Status:** **NOT VERIFIED** pending actual GitHub Actions run and complete evidence-archive inspection.

## Exact reviewed references

- Weaver Forge public repository: `chrono-vector/weaver-forge`, development branch `development/independent-verification-v2`.
- VECTOR public repository: `chrono-vector/vector-core@d0db1d8bfa38ae4d54f54ae3153f98f87ab2f776` (resolved from `main` on review date; pinned full SHA in the workflow).
- VECTOR `README.md` explicitly says the repository is a **sanitized Public VECTOR v0 reference**, not operational authorization, Evidence admission, Owner acceptance, IW PASS, or a current private implementation.
- Public `README.md` documents `python -m pip install -r requirements-dev.txt` and `python -m pytest`, with synthetic CAD/Decision Trace/schema/import tests only.
- Public requirements are `pytest>=8.0` and `jsonschema>=4.18`. These are **unlocked ranges**; the created workflow does not establish bit-for-bit dependency repeatability.
- Weaver Forge's pre-existing `.github/workflows/independent-verification-v2.yml` runs its own baseline lifecycle unittest and receipt checks on Ubuntu and Windows. This is a **separate workflow** and its historical successful runs are not automatically fresh evidence for this specific VECTOR commit.
- Weaver Forge's public `audit_lifecycle/tests/test_lifecycle.py` includes boundary enforcement, tampering, digest recomputation, freeze and human-review synthetic tests. These do not by themselves qualify a private Job Agent or a private Integration Harness.

## New bounded workflow

- New path: `.github/workflows/vector-public-reference.yml`.
- Runs on changes to its own file (and manual dispatch), on development branch only.
- Checks out full immutable public VECTOR commit and verifies checkout HEAD.
- Installs the **documented**, unlocked development dependencies for Python 3.11, runs `python -m pytest -q` on the public VECTOR checkout, retains JUnit XML, stdout and source-commit metadata.
- A separate dependent job retrieves completed test-job logs and output ZIP, checks ZIP integrity, computes `SHA256SUMS.txt`, uploads a temporary artifact for 90 days.
- The workflow includes **no private repositories, secrets, Owner records, real handoff ZIPs, CAD/ERA operational dumps, Chronicle `signals/`, Job Agent source, integration Harness content, execution permissions or publication actions**.

## Separate private-boundary assessment

- `chrono-vector/world-third-private-job-agent` describes the implemented lanes FIND → AUTHORIZE → ENFORCE → EXECUTE → VERIFY → HUMAN FINAL → LEARN and distinct IW/Canonical/Publication controls. Its private README states **Work Trace validity ≠ authority**; no private source is replicated into this public receipt.
- `chrono-vector/world-third-private-integration-harness` describes a sibling-checkout integration requiring private EIG/Job Agent/VECTOR/Weaver pieces and local-only `evidence/`. It explicitly forbids publishing private backup as-is. Public Weaver GitHub Actions must not clone or upload its content.
- We have not executed new cross-component Job Agent / EIG / VECTOR / Weaver integrated tests in this phase. This is NOT VERIFIED, not PASS.

## Evidence gate

After actual execution, record GitHub Actions run ID, exact job conclusions, source SHA, dependency versions from logs where available, JUnit counts, artifact ZIP SHA-256 and SHA256SUMS verification. Result may be PASS only for **public synthetic VECTOR tests**, not private WORLD THIRD integration or operational authority.

**No changes to main, immutable RC8, Ryan's files, public VECTOR repo, or private Job Agent / integration Harness repos.**
