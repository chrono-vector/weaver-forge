# INR-HER MinGit distribution digest human ratification

VERDICT:
HUMAN_DISTRIBUTION_DIGEST_RATIFIED

HUMAN_APPROVAL:
GRANTED

SCOPE:
ZIP distribution digest ratification record only.

ACCEPTED_BASELINE:
71ac6d5c6d304cf433868d9d38dc563516eea61b

## Approved artifact

REPOSITORY:
git-for-windows/git

TAG:
v2.56.0.windows.2

RELEASE_ID:
404111703

ASSET_ID:
613673731

FILENAME:
MinGit-2.56.0.2-64-bit.zip

SIZE:
39806486

SHA-256:
da35e72aa21c005a5a0d298cfbae110bc1609a815730ea0dde84b01a1b3cd3be

## Evidence

- The Git for Windows release-notes filename table and the GitHub asset digest for asset 613673731 both state that SHA-256.
- One authenticated HTTPS download of asset 613673731 returned 302 from the asset API to release-assets.githubusercontent.com, then 200, with Content-Length 39806486.
- The retained local file is C:\Users\mine0\AppData\Local\Temp\weaver-forge-mingit-evidence\613673731\MinGit-2.56.0.2-64-bit.zip.
- The local SHA-256 equals the published SHA-256.
- git-for-windows/git-snapshots release 404117721 asset 613692734 has the same filename and size and the different digest ab2543fea7eebdc8476b63af2ff8acec10fce72fc9f72a40c9123df94c6ac1ae. That snapshot digest is excluded.

## Review

Grok Bot review:
Material findings 0. Same-model-family review.

## Recorded limits

- Sigstore and PGP bundles were not independently cryptographically verified.
- ZIP distribution digest only, NOT extracted executable or DLL identity.
- Existing Phase 2A contract step 5 (execution-tree binding) is UNEXECUTED.
- RATIFIED_GIT_SHA256 remains None in accepted code.
- The MinGit operational pin remains UNRATIFIED.
- No execution, extraction, installation, or production authority is granted.
- FULL_INR_READY: NO

## Human ratification limit

This record ratifies the named ZIP distribution digest.
The accepted N2 Design Freeze remains unchanged.
Execution-tree binding and the operational MinGit pin remain outside this approval.

DISTRIBUTION_DIGEST_RATIFIED:
YES

EXECUTION_BINDING:
UNEXECUTED

OPERATIONAL_MINGIT_PIN:
UNRATIFIED

FULL_INR_READY:
NO
