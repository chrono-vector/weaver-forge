# Root-cause assessment — C2D-2 (wording-precision correction)

## Confidence classification

**ROOT_CAUSE_LIKELY** — with the following precise meaning only:

- At least one contributor is directly supported: **distinct absolute `CARGO_TARGET_DIR` paths** are embedded in the artifacts.
- Widespread debug, string, symbol, and linked-output differences are documented.
- These findings **likely explain part of the variance**.
- **No unique or complete cause** has been established for all differing bytes.

A single exclusive root cause for every differing byte is **not** established.

---

## PROVEN OBSERVATIONS

These are measured static facts (not causal attributions):

1. **Embedded absolute target paths differ**
   - Old-only strings under `/work/cargo-target/debug/...`
   - New-only strings under `/work/cargo-target-c2d1/debug/...`
   - Matches the documented C2B-4 vs C2D-1 `CARGO_TARGET_DIR` difference

2. **GNU Build IDs differ**
   - Old: `29e028f32f8573ecc505d459d7d8a8e0341a361f`
   - New: `989dd4bee3b9523fc82343293cbf0d3b0ad6fe89`
   - `.note.gnu.build-id` content hashes differ (section size equal)
   - **Interpretation:** The Build IDs differ, confirming that the linked ELF outputs are distinct. This is an observed consequence or identifier of the variance, **not** an independently established root cause.

3. **Debug metadata differs** (multiple `.debug_*` sections; sizes and/or hashes)

4. **Symbol inventories differ** (`nm` name sets and counts; `.symtab`/`.strtab` hashes)

5. **`.text` differs** in both size and content hash (not executable-text-identical)

6. **Relocation and linked-layout sections differ** (including `.rela.dyn`, `.rela.plt`, `.plt`, `.got`, `.got.plt`, related layout metadata)

7. **NEEDED libraries match** (static dynamic section); no RPATH/RUNPATH either side

8. **Documented build contexts differ**
   - Old (C2B-4): prior/incremental build state in shared cargo target
   - New (C2D-1): empty target directory with `CARGO_INCREMENTAL=0`

---

## SUPPORTED LIKELY CONTRIBUTOR

- **Differing absolute target-directory paths** contributed to at least some **debug/string metadata** variance (directly evidenced by path inventories).

---

## UNRESOLVED POSSIBLE CONTRIBUTORS

The analysis does **not** isolate whether executable-text, relocation, or full-file differences resulted from any one of the following, or from a combination:

- incremental build state
- cached dependency artifacts
- link ordering
- environment variables
- bootstrap/package state
- dependency build outputs
- other nondeterministic code-generation or link inputs

Timestamps are **not** listed as contributors (timestamps were not specifically demonstrated as embedded causal fields).

---

## Executable code and build-mode wording

The executable text, relocation, and layout metadata differ across the two documented build contexts. The analysis does **not** isolate whether this resulted from incremental state, cached dependency artifacts, absolute paths, link ordering, build-environment variation, or a combination of these factors.

**Do not read as proven:** “codegen/layout nondeterminism between incremental vs clean rebuild” as a sole or established cause of `.text` differences.

---

## Interpretation

Owner-side clean rebuild produced a non-bit-identical ELF. Static comparison documents path embedding differences, widespread metadata variance, and non-identical `.text`/relocations. **ROOT_CAUSE_ESTABLISHED** is rejected: differences are not confined to a single proven mechanism, and Build ID difference is treated as an **identifier of distinct linked outputs**, not a root cause.

**ROOT_CAUSE_LIKELY** remains only as: path-related metadata contribution is supported; full accounting of all differing bytes remains open.
