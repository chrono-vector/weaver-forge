# Witness classification rules — Grok Build narrow rebuild

Bit-identical equality with owner SHA-256 values is **not** required for PASS.

---

## INDEPENDENT NARROW REBUILD PASS

All of the following:

1. Witness is a person **other than** the owner/package author.
2. Run occurred on the Witness’s **own** host, VM, or cloud environment.
3. Public instructions (this package) were sufficient to start (no owner private assistance required for the core path).
4. Exact pinned source commit matched.
5. Exact pinned Rust image digest matched.
6. Source tree was clean before and after build.
7. `Cargo.lock` remained unchanged.
8. New **empty** `CARGO_TARGET_DIR` documented.
9. `CARGO_INCREMENTAL=0` documented.
10. `cargo build -p xai-grok-pager-bin --locked` exited **0**.
11. Expected artifact `xai-grok-pager` was produced.
12. Artifact size and SHA-256 (and recommended Build ID / `file` output) were recorded.
13. Post-build source integrity passed.
14. Required evidence files were supplied (see manifest).

A **different** SHA-256 than owner C2B-4 or C2D-1 is **not** FAIL by itself.

---

## INDEPENDENT NARROW REBUILD PARTIAL

Use when the binary was produced but one or more of independence, pinning, clean-target, bootstrap disclosure, cache provenance, or evidence completeness conditions failed, or the procedure was materially modified without full disclosure.

---

## INDEPENDENT NARROW REBUILD FAIL

Use when:

- source commit or image digest did not match
- build failed or expected artifact missing
- source or `Cargo.lock` changed
- evidence contradicts the claimed result

---

## INDETERMINATE

Evidence is insufficient to determine whether the claimed run occurred as stated.

---

## Explicit non-upgrades

A Witness PASS on narrow rebuild does **not** automatically establish:

- overall Weaver package PASS
- functional product verification
- security review
- production readiness
- Windows-native readiness
- bit-identical reproducibility across environments
