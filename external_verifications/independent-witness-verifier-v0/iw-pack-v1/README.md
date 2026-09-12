# iw-pack-v1

Frozen Independent Witness pack for CAW BOUNDED_D scope.

## Scope

- Static: `wrps-v0-p0014`, `wrps-v0-p0030`
- Runtime: Marketplace `createListing` + MintableCaw `mint`
- Authority: AUTH-005 `CawProfile.owner()` read-only subset

## Frozen pins

- CAW commit: `e2074718bcea293726ddfcf8764e1499e7b9217c`
- Pack format: `iw-pack-v1`
- IW verifier: `v0`

## Nonclaims

Accepted IW reproduction (when performed by an external witness under separate authorization) does **not** imply CAW certified, trustless/decentralized verified, live tx verified, authority execution verified, system permissionless, security audit complete, or production safe.

## Safety

- REAL WALLET: NO
- REAL PRIVATE KEY: NO
- REAL CREDENTIAL: NO
- LIVE BROADCAST: NO
- LIVE MUTATION: NO

## Independence

Self-check ≠ Independent Verification. Maintainer dry-run ≠ Independent Witness.

## How to run

1. Read `instructions/PROCEDURE.md`
2. Verify `frozen-inputs/` digests
3. Produce outputs into a copy of `witness-output-template/`
4. Do **not** open `reference-disclosure/` until your output pack is frozen
5. Submit pack for IW verifier adjudication

Do not force a PASS. Record failures honestly.
