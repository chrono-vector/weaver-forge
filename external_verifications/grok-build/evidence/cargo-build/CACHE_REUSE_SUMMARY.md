# Cache reuse summary — C2B-4

| Field | Value |
|-------|-------|
| Classification | **owner-side isolated incremental build reproduction** |
| Clean-room from empty caches | **No** |

## Reused paths

| Path | Reused? | Before bytes | After bytes |
|------|---------|-------------:|------------:|
| cargo-home | **Yes** | 779543568 | 779543568 |
| cargo-target | **Yes** | 5260310538 | debug ≈14991381975 |
| dotslash-cache | **Yes** | 13033306 | 13033306 |

## Incremental character

| Observation | Value |
|-------------|-------|
| `Downloaded` lines | **0** (registry already populated) |
| `Fresh` lines | **0** |
| `Compiling` lines | **969** |
| `Checking` lines | **0** |

Interpretation: dependency sources/registry from C2B-3 were reused (no re-download), but the build still performed full **compile+link** work for the `dev` profile binary (cargo check artifacts are not a complete substitute for `cargo build` objects). Not a clean-build claim.

## Preconditions for reuse (met)

- Caches outside Grok Build source tree
- No credentials in work root
- Source pin and Cargo.lock unchanged
- Same pinned image digest and Rust 1.92.0
