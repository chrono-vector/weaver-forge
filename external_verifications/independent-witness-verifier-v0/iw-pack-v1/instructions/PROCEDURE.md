# IW v1 Procedure (BOUNDED_D)

Bias rule: Do **not** force a PASS. Record honest observations.

## A. STATIC p0014

- **INPUT**: `frozen-inputs/path-sot/wrps-v0-p0014.json` + CAW checkout at frozen commit
- **ACTION**: Independently re-derive/verify static path binding for `CawProfileMarketplace.createListing`
- **OUTPUT**: `static-reproduction-results.json` entry for `wrps-v0-p0014`
- **PASS CONDITION**: Binding reconstructible; `REPRODUCTION_PASS` or explicit mismatch recorded
- **FAIL CONDITION**: Missing frozen source → `DEPENDENCY_BLOCKED` / `SOURCE_MISMATCH`
- **SAFETY BOUNDARY**: `NO_NETWORK`

## B. STATIC p0030

- **INPUT**: `frozen-inputs/path-sot/wrps-v0-p0030.json` + CAW checkout
- **ACTION**: Independently re-derive/verify static binding for `MintableCaw.mint`
- **OUTPUT**: `static-reproduction-results.json` entry for `wrps-v0-p0030`
- **PASS CONDITION**: Binding reconstructible
- **FAIL CONDITION**: `DEPENDENCY_BLOCKED` / `SOURCE_MISMATCH`
- **SAFETY BOUNDARY**: `NO_NETWORK`

## C. p0014 runtime input / dispatch / bounded local execution shape

- **INPUT**: fixture spec `p0014-createListing.json` + ABI from frozen CAW
- **ACTION**: Encode calldata locally; construct dispatch envelope; optional bounded local-fork simulation per published policy — **no broadcast**
- **OUTPUT**: `runtime-input-results.json`, `runtime-dispatch-results.json`, `runtime-execution-results.json` for p0014
- **PASS CONDITION**: Witness-produced artifacts present; honest observation of success/revert/block
- **FAIL CONDITION**: `RUNTIME_MISMATCH` / `RPC_BLOCKED` / `ENVIRONMENT_BLOCKED`
- **SAFETY BOUNDARY**: `NO_NETWORK` for encoding; `LOCAL_FORK_BOUNDED_MUTATION` only if required and local-only

## D. p0030 runtime input / read-only eth_call success shape

- **INPUT**: fixture spec `p0030-mint.json`
- **ACTION**: Encode `mint(address,uint256)` locally; ephemeral local fork `eth_call` — **no broadcast**
- **OUTPUT**: runtime input/dispatch/execution results for p0030
- **PASS CONDITION**: Selector/encoding + call observation recorded; `LIVE_MUTATION=false`
- **FAIL CONDITION**: `RPC_BLOCKED` / `RUNTIME_MISMATCH` / `UNEXPECTED_RESULT`
- **SAFETY BOUNDARY**: `LOCAL_FORK_READ_ONLY` or `NO_NETWORK` for encoding-only

## E. Authority read-only subset

- **INPUT**: `frozen-inputs/authority-subset-targets.json` (AUTH-005 `owner()`)
- **ACTION**: Read-only `eth_call` of `owner()`; record 20-byte address; **do not** claim holder identity
- **OUTPUT**: `authority-read-results.json`
- **PASS CONDITION**: Read attempt recorded under `READ_ONLY_NETWORK` / `LOCAL_FORK_READ_ONLY`
- **FAIL CONDITION**: `RPC_BLOCKED` / `SOURCE_MISMATCH`
- **SAFETY BOUNDARY**: Read-only; no privileged execution

## Finalization

Capture environment, failure-log, retry-log, digests, attestation, receipt, manifest.
Compare to `reference-disclosure/` **only after** output pack is frozen.
