# RSH-001 Baseline

- Scope: repository CI supply-chain hardening only
- Repository: `C:\dev\Weaver\weaver-forge-r4`
- Starting HEAD: `34b401c965704f45160cfb538be66a50826c5893`
- Starting branch: `r4/epistemic-contract-v1`
- Starting worktree: clean
- Workflow inventory: `.github/workflows/validate-receipts.yml`
- Existing Dependabot configuration: absent

## Workflow Inventory

| Workflow | Job | External action | Original ref | Credentials persisted | Events | Required permissions | Mutates repository | Cancellation safe |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `validate-receipts.yml` | `validate` | `actions/checkout` | `v4` | Yes, by checkout default | `push`, `pull_request` | Repository contents read | No | Yes |
| `validate-receipts.yml` | `validate` | `actions/setup-python` | `v5` | Not applicable | `push`, `pull_request` | None beyond job contents read | No | Yes |

The workflow has no schedule, `workflow_dispatch`, release, or explicit tag-only trigger.
The unfiltered `push` trigger can run for pushed branches and tags. The validation job reads
repository history and receipts, installs the selected Python toolcache version, and emits
validation output. It does not publish, write repository contents, or modify external state.

RSH-001 disables checkout credential persistence because no later step performs an
authenticated Git operation. Superseded runs can be cancelled without leaving partial
published state.
