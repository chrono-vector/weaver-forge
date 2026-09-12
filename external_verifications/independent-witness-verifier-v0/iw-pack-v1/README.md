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
- PACK_ROOT (relative): `iw-pack-v1`

## Seal model

- `CONTENT_MANIFEST`: hash of reproducibility payload files (HASHED_PAYLOAD)
- `PACK_SEAL`: binds content_manifest_digest + canonical git commit/tree + schema/version pins
- `PACK_ROOT_DIGEST`: digest of sealed metadata model (see PACK_FREEZE / PACK_SEAL)
- Dry-run result is HISTORICAL_RECORD / SEAL_METADATA annex — not hashed into CONTENT_MANIFEST payload

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
Self-declared independence alone is insufficient — external submission receipt required for IW_ACCEPTED.
MAINTAINER_ORIGIN must be != YES.

## How to run

1. Read `instructions/PROCEDURE.md`
2. Verify `frozen-inputs/` digests and toolchain profile
3. Produce outputs into a copy of `witness-output-template/`
4. Do **not** open `reference-disclosure/` until your output pack is frozen
5. Submit pack with external submission receipt for IW verifier adjudication

Do not force a PASS. Record failures honestly.
