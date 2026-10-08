# INR-001 Target Profile Re-freeze Record (r2)

Profile: `profiles/psm_001_inr_target_profile_v0.json`
(`target_profile_id`: `INR_TARGET_PROFILE_PSM_001_V0`, `target_sha`:
`c5e1cfa2fb52874fe9c97e0eade6a120c12cb27b`, unchanged)

Digest rule (unchanged): SHA-256 of the canonical JSON (sorted keys, compact
separators, ASCII) of the profile without `target_profile_digest`. The pinned
constant `PROFILE_DIGEST` in `trusted_capture.py` equals the digest of the committed
profile bytes (checked by `configuration()` on every run and by
`test_profile_origin_conform_and_digest_is_pinned`).

| state | digest |
|---|---|
| old (committed in c0747cc / 99418b4) | `2e2e75e246694fdd4d39d52bf3d5f6f65642dcbb3ef4621f258aed7724537634` |
| intermediate (Codex uncommitted, never committed) | `512a1f278306b5d87d245c027e3f7eaf14f2dae0824ff527182f9ba03d303916` |
| **new (r2)** | `bae309aa9a8f04f64990359d75f1e262945b8bf68149229f1a3023de207dc4ca` |

## Every change from the old committed profile, and why

Unchanged: `schema_version`, `target_profile_id`, `target_sha`, `profile_purpose`,
`nonclaims`, all 10 `case_id`s, all `command_id`s, `sequence`, `required`,
`mandatory_execution`, `expected_classification`, `python_policy.version` (3.11.x)
and the other existing `python_policy` entries.

1. `command_inventory[*].argv` added:
   `["{python}", "-I", "-S", "-B", "{probe}", "{source}", "{input}", "{repository}"]`.
   Why: the executed command must come from frozen configuration, and the verifier
   compares the actual Popen argv to its own template (`validate_inr_v0.ARGV_TEMPLATE`,
   which must equal this). `-S` (no `site`, no `.pth`) was added in r2 because the
   target is stdlib-only; `-I -B` were in the intermediate profile.
2. `python_policy.child_interpreter_flags = ["-I", "-S", "-B"]` and
   `python_policy.site = "DISABLED"` added. Why: record the child interpreter policy.
3. `required_cases[1..9].accepted_return_codes`: `[1, 2]` -> `[2]`. Why: rc 1 is an
   uncaught exception/traceback, not a refusal; the probe returns 2 only for
   reported validator errors.
4. `required_cases[*].input_digest`: all 10 changed. Why: the old values were not
   produced by any committed input generator (C1 had none; even the fixed bytes of
   `PSM_NEG_MUTATED_ARCHIVE_OR_INPUT` do not hash to the old value). The new values are
   the SHA-256 of `input_cases.case_bytes(...)` applied to the pinned
   `portfolio_state_v0.example.json` at TARGET_SHA; capture refuses to run if they differ.
   `PSM_NEG_HUMAN_FINAL_PRODUCTION_INFERENCE` changed again in r2
   (`b4d0ddc2a0bd9ecb7d1efc6748d4490617f5249ae5aa33ca7dd9dadf54306b2f` in the
   intermediate profile -> `fee9f7b995b89288533d643b30d9d50c519193ccae1412997be608e4608b88cb`)
   because the old mutation added top-level keys and was refused only by the generic
   "top-level fields do not match the closed PSM-v0 schema" rule (finding M3). The
   r2 mutation keeps the closed key set: it marks the SEIC verification source record
   as `human_final` and drops the `does_not_create_human_final` /
   `does_not_grant_production_permission` nonclaims.
5. `required_cases[*].expected_errors` added: the exact, ordered error list the
   pinned `validate_psm_v0.py` must return (empty for the positive case). Why: M3 —
   a negative control counts only if refused by its intended rule. The values were
   obtained by running the pinned validator on the closed inputs.
6. `required_cases[*].intended_refusal` added: the rule in `validate_psm_v0.py` that
   produces the expected errors (documentation; the binding is `expected_errors`).
7. `required_cases[1..9].required_property` text changed from "negative control
   refuses/fails as frozen" to "negative control refused by its intended rule (exact
   errors)" (HUMAN_FINAL: "Human Final / production inference refused by its
   dedicated rules"). Why: wording matches the new exact binding.
8. `target_file_digests` added (six files under `docs/portfolio_state/` at TARGET_SHA,
   as introduced by the intermediate profile). Why: capture verifies Git blob bytes
   against these before staging; the verifier compares the measured digests to them.

Notes:
- `PSM_NEG_MUTATED_ARCHIVE_OR_INPUT` expects the CPython message
  `'utf-8' codec can't decode byte 0xff in position 21: invalid start byte`. It was
  observed on Python 3.14.3. The frozen policy is 3.11.x, where the same message is
  expected but has not been observed on this machine (no 3.11 is installed). Any
  difference is reported as a refusal mismatch (non-PASS), never as PASS.
- This re-freeze is an implementer record. It is not a Human acceptance of the profile.
