# IW v1 Procedure (BOUNDED_D)

Bias rule: Do **not** force a PASS. Record honest observations.
Do **not** open `reference-disclosure/` until your witness output pack is frozen.

## STATIC common labels (anti-circularity)

For both static paths:

- **INPUT SOURCE**: CAW frozen commit `e2074718bcea293726ddfcf8764e1499e7b9217c` (+ Weaver pin in `frozen-inputs/weaver-pin.json`)
- **DERIVED BY WITNESS**: callsite / method / target / ABI / args reconstructed from CAW + fixture-spec
- **POST-RUN COMPARISON**: `frozen-inputs/path-sot/*.json` is a reference-only comparison aid AFTER derivation — **not** a sole proof source and **not** a substitute for witness-derived static results

Path-sot uses `ROLE: POST_RUN_COMPARISON_REFERENCE_ONLY` / `STATIC_STATUS_REFERENCE: COMPARISON_ONLY`.

---

## A. STATIC p0014

- **INPUT SOURCE**: CAW source commit `e2074718bcea293726ddfcf8764e1499e7b9217c`; Weaver pin; path-id `wrps-v0-p0014`
- **DERIVED BY WITNESS**: verify `CawProfileMarketplace.createListing` binding (target `0x6404d1d3d878407a0977d99c832453f235da67c3`, method `createListing(uint32,uint8,address,uint256,uint256,uint64)`, ABI from CAW)
- **OUTPUT**: `static-reproduction-results.json` entry for `wrps-v0-p0014`
- **POST-RUN COMPARISON**: path-sot reference only after derivation
- **SAFETY BOUNDARY**: `NO_NETWORK`

## B. STATIC p0030

- **INPUT SOURCE**: same CAW commit / Weaver pin; path-id `wrps-v0-p0030`
- **DERIVED BY WITNESS**: verify `MintableCaw.mint` binding (target `0x56817dc696448135203c0556f702c6a953260411`, selector `0x40c10f19`, ABI from CAW)
- **OUTPUT**: `static-reproduction-results.json` entry for `wrps-v0-p0030`
- **POST-RUN COMPARISON**: path-sot reference only after derivation
- **SAFETY BOUNDARY**: `NO_NETWORK`

---

## C. p0014 runtime (createListing) — full explicit procedure

Operational constants (encoding / fork pins — **not** a pre-declared must-PASS verdict):

- CAW source commit: `e2074718bcea293726ddfcf8764e1499e7b9217c`
- Weaver pin: see `frozen-inputs/weaver-pin.json`
- Chain: `11155111` (Sepolia)
- Fixed fork block: `11685854`
- Target address: `0x6404d1d3d878407a0977d99c832453f235da67c3`
- Method / ABI: `createListing(uint32,uint8,address,uint256,uint256,uint64)` from CAW artifacts
- Deterministic fixture: `frozen-inputs/fixture-specs/p0014-createListing.json` (profileId=42, listingType=0, ETH paymentToken, price=1e18, duration=86400)
- Tooling: **Foundry anvil preferred** (Foundry stable) **OR** Hardhat from CAW lock; document tool + version in environment.json

Steps:

1. Checkout CAW at frozen commit; confirm Weaver pin recorded
2. Load ABI + deterministic fixture; encode calldata locally; record calldata hash (calldata_sha256)
3. Start local fork at fixed block `11685854` (read-only RPC allowed for fork source)
4. Owner resolution for the profile/token under test
5. Impersonation of resolved owner (local only — no real wallet / key / credential)
6. Ownership verification before mutation
7. Approval setup; local approval tx to marketplace (LOCAL_FORK_BOUNDED_MUTATION only)
8. Take snapshot
9. Execute `createListing(...)` on local fork
10. Capture return / event / state observations (honest success OR revert)
11. Snapshot revert; post-revert verification that fork state restored
12. Write raw evidence outputs (runtime-input / dispatch / execution results + evidence digests)
13. Failure recording: append failure-log / retry-log with ATTEMPT_ID / PRIOR_ATTEMPT_ID policy — never delete prior failures

Expected success/revert classification comparison is sealed in `reference-disclosure/` — do not treat fixture-spec as a must-PASS oracle.

**SAFETY**: no live broadcast; REAL_WALLET=NO; REAL_PRIVATE_KEY=NO; LIVE_MUTATION=NO outside local fork.

---

## D. p0030 runtime (mint) — eth_call success shape

Operational constants:

- Target: `0x56817dc696448135203c0556f702c6a953260411`
- ABI: `mint(address,uint256)` / selector `0x40c10f19`
- `parseUnits(amount, 18)` — fixture amount_human `10000000000` → wei in fixture-spec
- Deterministic fixture: `frozen-inputs/fixture-specs/p0030-mint.json`
- Fixed block: `11686270` (from p0030 evidence; authority subset uses `11686511`)
- Fork source: local fork RPC read-only allowed

Steps:

1. Encode mint calldata from fixture; record calldata hash
2. Local fork at fixed block; `eth_call` (LOCAL_FORK_READ_ONLY)
3. Capture raw return / returndata
4. Record runtime input/dispatch/execution results
5. Failure recording as above

Do **not** expose or assume expected PASS verdict before freeze.

---

## E. Authority read-only subset (AUTH-005)

- Visible pre-run: target `0x9fcbb3d6880cd3293f1a731fe6c958a6621a74bf`, method `owner()`, chain `11155111`, block `11686511`, ABI/source from CAW Ownable
- Action: read-only `eth_call` of `owner()`; record 20-byte address; **do not** claim holder identity
- Expected owner reveal: **only** in `reference-disclosure/` after freeze
- OUTPUT: `authority-read-results.json`
- SAFETY: read-only; no privileged execution

---

## Finalization

Capture environment, failure-log, retry-log, digests, attestation, **external submission receipt**, manifest.
`FAILURE_HISTORY_ASSURANCE` = `SUBMITTED_HISTORY_PRESERVED` (never claim `COMPLETE_HISTORY_CRYPTOGRAPHICALLY_PROVEN`).
Compare to `reference-disclosure/` **only after** output pack is frozen.
