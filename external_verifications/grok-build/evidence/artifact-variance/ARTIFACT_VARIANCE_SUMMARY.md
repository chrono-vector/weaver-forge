# Artifact Variance Summary — Phase C2D-2

| Field | Value |
|-------|-------|
| Classification | **ARTIFACT VARIANCE ANALYSIS PASS** |
| Root-cause confidence | **ROOT_CAUSE_LIKELY** (partial contribution supported; unique full cause not established) |
| Old SHA-256 | `1efcd864606d3894b685ed3ec8c6b23e7e0aceeabdc04c4c8fc991c65df4389b` |
| New SHA-256 | `eebdbe81a8fc34645a2f3c72aad36825d692fbef594a6c540f77ffaa42c18dad` |
| Product executed | **No** |
| ldd used | **No** |

## Headline findings (observations)

1. Both artifacts authenticated by expected size and SHA-256.
2. Section hashes: **15 identical**, **30 differing** (of 45).
3. **`.text` differs** (size and hash) → not metadata-only variance; not executable-code equivalence.
4. GNU Build IDs differ — an observed identifier that the linked outputs are distinct, **not** a standalone root cause.
5. NEEDED libraries match.
6. Embedded paths show old `/work/cargo-target/...` vs new `/work/cargo-target-c2d1/...` (supported likely contributor to some metadata variance).
7. Debug/string/symbol tables differ substantially.
8. File size delta: **-132616** bytes.

## Causal stance (precision)

- **Supported likely contributor:** distinct absolute `CARGO_TARGET_DIR` paths in debug/string metadata.
- **Unresolved:** whether `.text`/relocation differences stem from incremental state, caches, paths, link ordering, environment, or a combination.
- **Not claimed:** unique root cause for all differing bytes; functional equivalence; executable-code equivalence.

## Multi-axis impact

- Does **not** upgrade Independent Witness, Functional, Security, Ops, or Windows readiness.
- Build reproducibility overall remains **PARTIAL**.
- Overall remains **PARTIAL**.

## Claim C-021

**PASS** (analysis completeness): static comparison completed; supported contributors and unresolved factors documented; does **not** establish bit-identical reproducibility or functional equivalence.
