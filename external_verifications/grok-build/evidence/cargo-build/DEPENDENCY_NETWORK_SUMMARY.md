# Dependency / network summary — C2B-4

| Field | Value |
|-------|-------|
| Network authorized | Yes (limited) |
| Project crate re-download | **No** (`Downloaded` = 0) |
| New git objects for project deps | Not observed in cargo log |

## Network categories used

| Category | Used? |
|----------|-------|
| apt (bootstrap packages) | **Yes** |
| crates.io registry | **No new downloads** (cache hit) |
| git deps (nucleo etc.) | Cache hit expected |
| DotSlash protoc | Cache hit (existing digest) |
| xAI product/API | **No** |

## Lockfile

Cargo.lock **unchanged** (Phase B SHA-256 match).
