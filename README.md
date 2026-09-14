# Weaver Forge

Weaver Forge verifies results through a bounded, evidence-preserving audit lifecycle.

It takes an operator audit request, pins a target, executes a registered claim adapter, collects evidence, makes a conservative decision, optionally requires human review, freezes a one-shot package, and re-verifies both SHA-256 bindings and claim semantics.

**Product status:** `WEAVER_FORGE_COMPLETE`

---

## Core lifecycle

```
AUDIT REQUEST
→ CLAIM / SCOPE
→ BOUNDARY
→ BASELINE
→ SOURCE / INPUT PINNING
→ EXECUTION
→ EVIDENCE COLLECTION
→ NEGATIVE / TAMPER / REPRODUCTION CONTROLS
→ VERIFICATION
→ DECISION
→ HUMAN REVIEW where policy requires
→ FREEZE
→ FINAL AUDIT PACKAGE
```

Entry point package: `audit_lifecycle/`

---

## Key principles

- **Capability ≠ Authority** — a successful local audit does not grant external authority.
- **Self-check ≠ Independent Verification** — lifecycle PASS does not imply an external witness accepted the claim.
- **Failures remain visible** — FAIL / BLOCKED / INCONCLUSIVE runs are preserved; false PASS is forbidden.
- **Protected boundaries fail closed** — writes outside the allowed root or into protected paths are denied.
- **Evidence is bound by SHA-256** — manifests and `SHA256SUMS.txt` bind package contents.
- **Semantic verification does not trust stored PASS blindly** — registered adapters recompute material decision fields.
- **Frozen package regeneration is rejected** — a second freeze fails closed (`FREEZE_ALREADY_EXISTS`).
- **Unsupported semantic adapters fail conservatively** — missing verifier support cannot silently PASS.

---

## Requirements

- Python **3.10+** (stdlib only; no third-party runtime dependencies)
- A checkout of this repository

---

## Installation / setup

From the repository root:

```bash
# optional editable install
pip install -e .

# or run modules directly with PYTHONPATH / cwd at repo root
python -m audit_lifecycle.cli --help
```

---

## Minimal first audit (`hash_claim`)

A portable synthetic example lives in [`examples/hash_claim/`](examples/hash_claim/).

```bash
# from repository root — write output OUTSIDE the source tree
OUT="${TMPDIR:-/tmp}/weaver-forge-hash-claim-runs"
mkdir -p "$OUT"

python -m audit_lifecycle.cli run \
  --request examples/hash_claim/request.json \
  --out "$OUT"

python -m audit_lifecycle.cli verify \
  --run "$OUT/<audit_id>"
```

With `human_review_required: false` in the sample request, a successful `run` auto-freezes once. A second freeze must fail closed:

```bash
python -m audit_lifecycle.cli freeze --run "$OUT/<audit_id>"
# expect FREEZE_ALREADY_EXISTS (non-zero)
```

See [`examples/hash_claim/README.md`](examples/hash_claim/README.md) for the full walkthrough.

---

## CLI

```bash
python -m audit_lifecycle.cli run --request <request.json> --out <runs_dir>
python -m audit_lifecycle.cli freeze --run <run_dir>
python -m audit_lifecycle.cli verify --run <run_dir>
```

If policy requires human review, after a PASS decision write `HUMAN_REVIEW.json` into the run directory (status `ACCEPTED` or `REJECTED`), then call `freeze`.

---

## Tests

```bash
python -m unittest audit_lifecycle.tests.test_lifecycle -v
```

Expected current result: **13 tests OK**

---

## Current adapter coverage

| Adapter | Status |
|---------|--------|
| `hash_claim` | Registered execution adapter + semantic verifier |

Additional claim families require **explicit** registered verifier/adapter support. Unsupported adapters must fail conservatively during semantic verification.

---

## Non-claims

`WEAVER_FORGE_COMPLETE` does **not** mean:

- `CRYPTO_SUPPORTED_E2E_FULL`
- Independent Witness accepted
- production deployment authorization
- that all possible audit claim families are supported

See also:

- [`WEAVER_FORGE_FINAL_COMPLETION_GATE.md`](WEAVER_FORGE_FINAL_COMPLETION_GATE.md)
- [`WEAVER_FORGE_COMPLETION_MATRIX.md`](WEAVER_FORGE_COMPLETION_MATRIX.md)

---

## Security / evidence notes

- SHA-256 manifests provide **package integrity binding**, not external notarization.
- Human authority remains where workflow policy requires it (`HUMAN_REVIEW.json`).
- Do not commit secrets, private evidence trees, or absolute owner-local paths into examples.

Reporting guidance: [`SECURITY.md`](SECURITY.md)

---

## License

Public Core material is licensed under Apache-2.0. See [`LICENSE`](LICENSE), [`LICENSE_SCOPE.md`](LICENSE_SCOPE.md), and [`NOTICE`](NOTICE).
