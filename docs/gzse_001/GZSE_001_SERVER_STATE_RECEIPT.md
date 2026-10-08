# GZSE-001 Server State Receipt

Status: SERVER_STATE_RECEIPT_ONLY

Scope: GZSE-001 Phase A Gate Zero server-side enforcement for the default branch `main` of `chrono-vector/weaver-forge`.

This receipt preserves observed GitHub server configuration. It is documentation evidence of the observed configuration. It is not the enforcement itself; the actual GitHub server ruleset is the enforcement.

## Repository identity

| Field | Value |
|---|---|
| Repository | `chrono-vector/weaver-forge` |
| Branch | `main` |
| GitHub ruleset ID | `24696118` |
| GitHub ruleset name | `GZSE-001 Phase A main protection` |
| Ruleset target | `branch` |
| Ruleset enforcement | `active` |
| Target selector include | `refs/heads/main` |
| Target selector exclude | `[]` |

## Observation timestamps

| Event | Timestamp |
|---|---|
| Ruleset creation response | `2026-10-08T12:44:35.104+09:00` |
| Ruleset update timestamp returned by GitHub | `2026-10-08T12:44:35.174+09:00` |
| Preservation read-back | Performed immediately before this receipt was committed on the GZSE-001 isolated worktree |

## Before state

Read-only preflight before GZSE-001 Phase A configuration observed:

- branch protection: none
- repository rulesets: none
- `main` branch `protected`: `false`

## After state read-back

GitHub API read-back after server configuration and again at preservation time observed:

- ruleset exists: `yes`
- ruleset ID: `24696118`
- ruleset name: `GZSE-001 Phase A main protection`
- enforcement: `active`
- target selector include: `refs/heads/main`
- target selector exclude: `[]`
- bypass actors: `[]`
- `current_user_can_bypass`: `never`
- branch `main` protected: `true`
- classic branch protection `enabled`: `false` / ruleset-based protection is active

## Rules accepted by GitHub

### Pull request rule

| Parameter | Value |
|---|---|
| `required_approving_review_count` | `0` |
| `dismiss_stale_reviews_on_push` | `false` |
| `required_reviewers` | `[]` |
| `require_code_owner_review` | `false` |
| `require_last_push_approval` | `false` |
| `required_review_thread_resolution` | `true` |
| `require_extra_approval_for_unattributed_changes` | `true` — GitHub default/normalization |
| `allowed_merge_methods` | `merge`, `squash`, `rebase` — GitHub default/normalization; `required_linear_history` is also active |

### Required status checks rule

| Parameter | Value |
|---|---|
| `strict_required_status_checks_policy` | `true` |
| `do_not_enforce_on_create` | `false` — GitHub default/normalization |
| `required_status_checks` | `[{"context": "validate"}]` |

Required check evidence basis from design freeze:

- workflow name: `Validate Receipts`
- workflow file: `.github/workflows/validate-receipts.yml`
- stable job/check context: `validate`
- selected required check: `validate`

### Additional active rules

- `required_linear_history`
- `deletion`
- `non_fast_forward`

## Phase A assertions preserved

| Assertion | Preserved state |
|---|---|
| PR required | `ENFORCED` |
| Required check `validate` | `ENFORCED` |
| Branch up-to-date required | `ENFORCED` |
| Resolved conversations required | `ENFORCED` |
| Linear history required | `ENFORCED` |
| Force pushes blocked | `ENFORCED` via `non_fast_forward` |
| Branch deletion blocked | `ENFORCED` via `deletion` |
| Required approvals | `0` |
| CODEOWNER review | `DISABLED` |
| Stale approval dismissal | `DISABLED` |
| Latest-push approval | `DISABLED` |
| Routine bypass actors | `NONE` / `[]` |

## Server state receipt source

Temporary source receipt used for preservation:

`C:/dev/_tmp/GZSE_001_SERVER_STATE_RECEIPT_20261008T124435_JST.md`

The temporary receipt was validated against live GitHub API read-back before this repository receipt was created.

## Nonclaims

GitHub server enforcement != code correctness.

GitHub server enforcement != evidence correctness.

GitHub server enforcement != Independent Witness.

GitHub server enforcement != independent reproduction.

GitHub server enforcement != Human Final.

GitHub server enforcement != E4.

GitHub server enforcement != W1.

GitHub server enforcement != production readiness.

GitHub server enforcement != production permission.

Receipt != enforcement itself.

The actual GitHub server ruleset is the enforcement.

This receipt also does not prove protection of branches other than `main` and does not prove absence of GitHub platform-level administrator powers.
