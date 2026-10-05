# Dedicated Local Software Ed25519 Generation and Custody Profile v0 - Human Design Freeze

Date:
2026-10-05

`HUMAN_DESIGN_FREEZE_STATUS: ACCEPTED`

Human decision:
`HUMAN_DESIGN_FREEZE_ACCEPTED`

This record saves a Human Design Freeze decision explicitly made by the Human authority. It does not record an AI acceptance decision. It does not amend the frozen D1-R1 design, generate or select a real key, create or request private or recovery material, perform Admission PREPARE or CONFIRM, authorize implementation, authorize key generation, or create identity, role, authorization, trust, provenance, evidence, truth, currentness, revocation, or Human Final semantics.

Repository:
`C:\dev\Weaver\weaver-forge-r4`

Scope name:
`Dedicated Local Software Ed25519 Generation and Custody Profile v0`

Design revision:
D1-R1, the minimal remediation of material findings MF-1 through MF-8 raised by the independent adversarial review of commit `4cac108eb6a7c0454433d8a191264517c0fa29a9`.

D1-R1 status:
The frozen file states `Design status: READY_FOR_INDEPENDENT_REREVIEW`. That precondition was satisfied by the independent targeted review recorded below. The frozen bytes are not edited to reflect it.

## Frozen design

Frozen design commit:
`73942f18b5089c48795039d2fe8f24bf01b0c2f7`

Parent of the frozen design commit:
`4cac108eb6a7c0454433d8a191264517c0fa29a9`

Frozen design file:
`docs/next/DEDICATED_LOCAL_SOFTWARE_ED25519_GENERATION_AND_CUSTODY_PROFILE_V0_D1_20261005.md`

Frozen file SHA-256:
`B788A240989F00A01844692C6B714E1106F936D1220C9E79AB67173DDEB01791`

Frozen file size:
46640 bytes

Frozen file line endings:
LF only; the file contains 0 CR bytes.

Frozen Git blob id:
`c02baa04ae984c1ee8601b9b552b93ca87a34aad`

The committed blob bytes were extracted after commit and their SHA-256 equals the reviewed working-tree SHA-256 above. The exact reviewed bytes are the committed bytes.

## Independent targeted review

Prior independent adversarial review of commit `4cac108eb6a7c0454433d8a191264517c0fa29a9`:
`REVISE_BEFORE_HUMAN_DESIGN_FREEZE`, material findings MF-1 through MF-8.

Independent targeted closure review of the D1-R1 working-tree bytes with the SHA-256 above:
`ACCEPT_D1_R1_FOR_HUMAN_DESIGN_FREEZE`

Reviewed D1-R1 diff size against `4cac108eb6a7c0454433d8a191264517c0fa29a9`:
+176 / -52. The edit had been reported as +174 / -50 before review. The review bound its verdict to the exact file SHA-256 above, not to the reported count.

`MF_1_TO_MF_8: CLOSED_8_OF_8`

`NEW_MATERIAL_FINDINGS: 0`

`SELF_RATIFICATION_PATH_FOUND: NO`

`WRONG_KEY_ADMISSION_PATH_REMAINS: NO`

`PRIVATE_KEY_AI_EXPOSURE_PATH_REMAINS: NO`

`HISTORICAL_SNAPSHOT_SEMANTICS_PRESERVED: YES`

`SAFE_FOR_HUMAN_DESIGN_FREEZE: YES`

## Known nonmaterial limitations

The targeted review recorded eight nonmaterial findings. They remain nonmaterial limitations. They were not applied after review, because any text edit would invalidate the exact-byte review. They may be resolved later only within the frozen semantics by implementation or runbook work, or by a separately authorized additive revision.

- N1: Negative check 10 says to reject inherited ACLs, while the ACL rule requires secret files to inherit the protected directory DACL. The intended reading is that only ACEs inherited from the protected custody or restore directory are allowed.
- N2: The `ABANDONED` scope is stated without an upper bound in two places and as "before READY" in another. No state after `READY_FOR_ADMISSION_HANDOFF` is defined. The custody helper cannot affect Admission.
- N3: The fixed quarantine location and DACL for abandoned artifacts, and the mechanism for retiring the old active directory, are not named.
- N4: The "expected restore state marker" is not defined in the custody state table. Byte equality with the medium is a runbook step because the restore check takes no media path.
- N5: Negative checks 30, 43, and 47 and mutation 30 cannot be runtime rejections by the helper. The frozen text already classifies the underlying facts as runbook or test-plan items.
- N6: The observed PBES2/PBKDF2-SHA256-2048/AES-256-CBC detail was source-observed at tag 50.0.2, not observed as emitted output. The OpenSSL 4.0.3 attribution belongs to the `cryptography` 50.0.2 changelog. `RECORD` verification should compare against the reviewed hash-locked wheel artifacts.
- N7: The frozen procedure lists independent rereview after Freeze, while the document requires it before Freeze. The independent targeted review occurred before this Freeze.
- N8: A single failed backup copy abandons the whole generation instead of permitting retry with new media. This is fail-closed.

## Freeze distinctions

DESIGN FREEZE ≠ IMPLEMENTATION ACCEPTANCE

DESIGN FREEZE ≠ HUMAN FINAL

DESIGN FREEZE ≠ KEY GENERATION AUTHORIZATION

DESIGN FREEZE ≠ ADMISSION

DESIGN FREEZE ≠ TRUST / IDENTITY / ROLE / AUTHORIZATION

## Frozen nonclaims

`REAL_KEY_GENERATED: NO`

`PRIVATE_KEY_CREATED: NO`

`PASSPHRASE_SEED_OR_RECOVERY_SECRET_CREATED: NO`

`ADMISSION_PREPARE_PERFORMED: NO`

`ADMISSION_CONFIRM_PERFORMED: NO`

`IMPLEMENTATION_AUTHORIZED_BY_FREEZE: NO`

`KEY_GENERATION_AUTHORIZED: NO`

`HUMAN_FINAL: NOT_PERFORMED`

`IDENTITY_SEMANTICS_ADDED: NO`

`ROLE_SEMANTICS_ADDED: NO`

`AUTHORIZATION_SEMANTICS_ADDED: NO`

`TRUST_SEMANTICS_ADDED: NO`

`HISTORICAL_ADMISSION_SEMANTICS_CHANGED: NO`

## Historical Admission

`EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0` remains immutable and historical. Exact Public-Key Admission Decision Semantics v0 and the Exact Public-Key Admission Act Template and Binding Handoff v0 remain as frozen. This Freeze creates no current, active, revoked, superseded, or replacement status. Any replacement key still requires a new additive snapshot and a new two-phase admission act.

## Next scope

The next proposed scope is `Dedicated Local Software Ed25519 Custody Helper and Runbook v0`. This record does not authorize it. Implementation, test-only key material, real execution environment preparation, real key generation, and Admission PREPARE or CONFIRM each require separate Human authorization.

## Closed-scope protection

This freeze record does not modify or reinterpret R3, R4, WVMA-V1, TE, RP, IVP, CR, RER, EBD, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, PSRD-v0, SUBP-v0, Exact-Bytes Witness v0, Exact Public-Key Admission Decision Semantics v0, Exact Public-Key Admission Act Template and Binding Handoff v0, or any other CLOSED scope.

It does not alter VECTOR, EIG, Canonical, Published, or Deployed state. It changes no production code, tests, requirements, dependency pins, installed packages, key material, admission state, signer-reference binding, or signing service.

## Change rule

The frozen D1-R1 bytes may not be edited in place. Any change, including resolution of N1 through N8 in the design text, requires a separately authorized additive revision, independent review, and a new Human Design Freeze.

## Push status

NO. No public or remote push is authorized by this Human Design Freeze save.
