# RSH-001 Verification

- Starting HEAD: `34b401c965704f45160cfb538be66a50826c5893`
- Final candidate HEAD: the single commit containing this record; its exact SHA is reported in the final execution status because a Git commit cannot contain its own commit ID
- Branch: `hardening/rsh-001-supply-chain`
- Weaver runtime/source code changed: `NO`

## Files Changed

- `.github/workflows/validate-receipts.yml`
- `.github/dependabot.yml`
- `scripts/check_ci_supply_chain.py`
- `scripts/test_ci_supply_chain.py`
- `docs/rsh_001/RSH_001_BASELINE.md`
- `docs/rsh_001/ACTION_PIN_MAP.md`
- `docs/rsh_001/RSH_001_PERMISSIONS.md`
- `docs/rsh_001/SUPPLY_CHAIN_UPDATE_POLICY.md`
- `docs/rsh_001/RSH_001_VERIFICATION.md`

## Configuration Changes

| Action | Old ref | New SHA |
| --- | --- | --- |
| `actions/checkout` | `v4` | `11d5960a326750d5838078e36cf38b85af677262` |
| `actions/setup-python` | `v5` | `a26af69be951a213d495a4c3e4e4022e16d87065` |

- Permissions: explicit top-level `contents: read`; no write permissions.
- Checkout credentials: `persist-credentials: false`.
- Concurrency: workflow plus ref group; superseded runs are cancelled.
- Dependabot: weekly `github-actions` updates for repository root; no auto-merge.

## Validation

Commands and final results are recorded after candidate verification:

| Command | Result |
| --- | --- |
| `python -c "import yaml; ... yaml.safe_load(...)"` for both modified YAML files | PASS; 2 files parsed with PyYAML 6.0.3 |
| `python scripts/check_ci_supply_chain.py` | PASS; 2/2 external refs full-SHA pinned, explicit permissions and Dependabot present |
| `python -m unittest scripts.test_ci_supply_chain -v` | PASS; 5 tests |
| `python scripts/validate_receipts.py` | PASS; 15 receipt files |
| `python scripts/check_receipt_coverage.py` | PASS; advisory inventory reports 227 commits and 15 receipts; exact mapping remains not enforceable |

Mutation checks use temporary repositories and never modify candidate files:

| Mutation | Expected | Result |
| --- | --- | --- |
| Replace a full SHA with `@v4` | FAIL | KILLED |
| Replace a full SHA with a 7-character SHA | FAIL | KILLED |
| Remove explicit permissions | FAIL | KILLED |

## Remaining Limitations

- Pinning does not prove third-party action safety or protect against compromise of GitHub or upstream history before resolution.
- Dependabot proposals and passing CI still require human review.
- This change does not attest dependency completeness outside GitHub Actions.
- Local YAML parsing validates syntax, not GitHub-hosted execution semantics.
- Existing receipt coverage inventory drift remains advisory and is not changed or reinterpreted by RSH-001.

Exact evidence ceiling:
`CI_SUPPLY_CHAIN_HARDENED_AT_PINNED_REPOSITORY_STATE`.

This is not independent verification, production authorization, Human Final, a new witness
level, new operational authority, or evidence of improved Weaver semantic correctness.
