# Semi-blind disclosure

**Visible before run**: frozen commit/version, PATH_IDs, targets/methods, fixture specs (encoding inputs), chain/block requirements, procedure, schema/output requirements, toolchain profile.

**Reveal after witness output frozen**: exact expected derived hashes/results and expected owner address in `reference-disclosure/`.

Protected pre-run (must NOT appear in fixture-specs / path-sot):

- Expected PASS / success verdict
- Expected owner address as comparison oracle
- `STATIC_STATUS_REFERENCE: COMPLETE` in path-sot (use COMPARISON_ONLY)

Do not make execution impossible merely to achieve blindness.

External submission: MAINTAINER_ORIGIN != YES; self-declared independence insufficient.
