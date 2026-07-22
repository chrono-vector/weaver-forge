# Witness submission — Grok Build

## Primary method (preferred)

1. Fork `https://github.com/chrono-vector/weaver-forge`.
2. Create a branch named:
   `independent-witness/<witness-id>-<yyyy-mm-dd>`
   Example: `independent-witness/alice-2026-07-22`
3. Add **only** your evidence under:
   `external_verifications/grok-build/witness-submissions/<witness-id>-<yyyy-mm-dd>/`
4. Include completed templates / required files (see manifest).
5. Open a Pull Request. Do **not** edit owner `evidence/` logs or change owner verdicts to claim PASS on their behalf.

Witness may update a PR description; classification is assigned per [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md) after review.

## Fallback method

If a PR is impractical:

1. Produce a ZIP or tar archive of the evidence directory.
2. Compute a cryptographic hash of the archive (SHA-256).
3. Deliver via an agreed channel (documented by owner intake).
4. Owner must preserve the original archive before extraction.

A private fallback delivery is **not** automatically “public independent verification” until published in the repository.

## Must not modify

- Owner historical evidence trees
- Pinned source of Grok Build
- Claim IDs for owner-side results (add Witness results separately)

## Bit-identical note

Do not expect your artifact SHA-256 to match owner values. Record **your** hash.
