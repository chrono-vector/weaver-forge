# INR-001 Target Profile Re-freeze Record (r3)

Status: IMPLEMENTER RECORD — not independently reviewed, not a Human acceptance of
the profile. Prior re-freeze record: `INR_001_PROFILE_REFREEZE_R2.md` (kept unchanged).

Profile: `profiles/psm_001_inr_target_profile_v0.json`
(`target_profile_id`: `INR_TARGET_PROFILE_PSM_001_V0`, `target_sha`:
`c5e1cfa2fb52874fe9c97e0eade6a120c12cb27b`, unchanged)

Digest rule (unchanged): SHA-256 of the canonical JSON (sorted keys, compact
separators, ASCII) of the profile without `target_profile_digest`. The pinned
constant `PROFILE_DIGEST` now lives in `supervisor_inr_v0.py` (the r2 module
`trusted_capture.py` was removed) and must equal the digest of the committed profile
(checked by `configuration()` inside every supervised run and by
`test_profile_origin_conform_and_digest_is_pinned`).

OLD_PROFILE_DIGEST: `bae309aa9a8f04f64990359d75f1e262945b8bf68149229f1a3023de207dc4ca` (r2, commit 1ce1651)

NEW_PROFILE_DIGEST: `25fa116108c8014904b52302e8f5f583d332bf5de72583551494119b863ae4bb` (r3)

## Reasons

1. Remove an overclaim. The r2 case `PSM_NEG_HUMAN_FINAL_PRODUCTION_INFERENCE`
   ("Human Final / production inference refused by its dedicated rules") claimed a
   production property that the pinned validator does not enforce. The pinned
   validator refuses Human Final inference through the `_HUMAN_ACCEPTANCE` source
   rule and touches production only through the required-nonclaims rule. It has no
   rule that rejects a positive "production permission granted" assertion.
2. Bind only properties the pinned PSM validator actually enforces
   (P_verified = P_executed).
3. Keep exact refusal semantics: each case still binds the exact, ordered error
   list the pinned validator returns.

## Evidence from the pinned source (`git show c5e1cfa:docs/portfolio_state/validate_psm_v0.py`, sha256 `a2aff1e6...b51e`)

```
24: _HUMAN_ACCEPTANCE = re.compile(
25:     r"Decision:\s*\r?\nHUMAN_REVIEW_ACCEPTED(?:_WITH_NONMATERIAL_LIMITATIONS)?(?:\s|\Z)"
26: )
63: _REQUIRED_NONCLAIMS = frozenset(
71:         "does_not_create_human_final",
72:         "does_not_grant_production_permission",
242:     if kind == "human_final" and _HUMAN_ACCEPTANCE.search(
243:         content.stdout.decode("utf-8", "replace")
244:     ) is None:
245:         errors.append(f"{field} does not resolve to an accepted Human Final record")
251:     if type(record) is not dict or set(record) != _TOP_LEVEL:
252:         return ("top-level fields do not match the closed PSM-v0 schema",)
492:     nonclaims = _string_list(record.get("nonclaims"), "nonclaims", errors, nonempty=True)
493:     missing_nonclaims = _REQUIRED_NONCLAIMS - set(nonclaims)
494:     if missing_nonclaims:
495:         errors.append(f"required nonclaims are missing: {', '.join(sorted(missing_nonclaims))}")
```

The word "production" appears in the pinned source only on line 6 (module docstring:
"Final, witness status, or production permission.") and line 72 (the required
nonclaim token). No rule reads or rejects a production-permission value. A record
that keeps every nonclaim and adds the free-text limitation "production permission
granted" is accepted with no errors (`test_pinned_validator_accepts_a_positive_production_statement`).
A top-level `production_permission` key is refused only by the generic closed-schema
rule on line 252, which is not a production rule (`test_old_top_level_human_final_input_is_wrong_reason`).

POSITIVE_PRODUCTION_PERMISSION_GRANT_REFUSAL: NOT_CLAIMED

No case for a positive production-permission grant was created.

## Every change from the r2 profile

Unchanged: `schema_version`, `target_profile_id`, `target_sha`, `profile_purpose`,
`python_policy`, `target_file_digests`, the argv template, and cases 1–8 and the
mutated-input case (ids, digests, expected errors, return codes, properties).

1. Case `PSM_NEG_HUMAN_FINAL_PRODUCTION_INFERENCE` (sequence 9) was removed and split into:
   - `PSM_NEG_HUMAN_FINAL_INFERENCE` (sequence 9). Input: the accepted record with
     `source_records[1].record_kind` (the SEIC verification record) changed from
     `verification` to `human_final`. Nonclaims are left intact. Expected errors:
     `["source_records[1] does not resolve to an accepted Human Final record"]`.
     Input digest `91aa664cea7cfecc47f0034c01c7f7f25eec1b32c31e663131e4b5d72eebe771`.
     Property: Human Final is not inferred from a non-Human-Final source (lines 24–26, 242–245).
   - `PSM_REQUIRED_PRODUCTION_NONCLAIM` (sequence 10). Input: the accepted record
     with exactly the nonclaim `does_not_grant_production_permission` removed.
     Expected errors: `["required nonclaims are missing: does_not_grant_production_permission"]`.
     Input digest `9ec5a07d5d8b69bffcc4d7437b1a968236f3f0bdb77cba01408085ba4c9f15ca`.
     Property: a record that omits that required nonclaim is refused (lines 63–72, 492–495).
     This is not a positive production grant and is not described as one.
2. `PSM_NEG_MUTATED_ARCHIVE_OR_INPUT` moved from sequence 10 to 11 (same input, digest and expected error).
3. `command_inventory` was rebuilt in the same order (`CMD_<case_id>`, the same argv template, `required: true`).
4. `nonclaims` gained "profile does not claim that the pinned validator rejects a
   positive production-permission assertion".

The removed r2 input (`fee9f7b9...88cb`) mixed two rules. Its first error came from
the Human Final rule and its second ("required nonclaims are missing:
does_not_create_human_final, does_not_grant_production_permission") came from the
nonclaims rule. Neither error showed that a production grant is refused.

Expected errors come from reading the pinned source above. The live tests
(`test_every_negative_control_hits_its_exact_refusal`,
`test_split_human_final_and_production_nonclaim_cases`,
`test_every_case_executes_exactly_its_frozen_refusal`) confirmed them by running
the pinned validator through the runtime probe on this machine (Python 3.14.3; the
frozen policy is 3.11.x, so any difference there would show up as a refusal
mismatch and never as PASS).

INR_PASS_CLAIMED: NO. HUMAN_FINAL_CREATED: NO. PSM_CHANGED: NO.
