# INR-HER MinGit SDK Header Rehash V2 Evidence

Record date: 2026-10-12 (Asia/Tokyo)
Status: HEADER_REHASH_V2_TRANSFERRED_TEXT_REVIEWED_FULL_INR_NOT_READY
Scope: one documentation-only preservation of the transferred header-rehash v2 text and of its comparison with include_hashes.txt
Decision source: the Human explicit approval to review this transferred rehash text and to preserve the review as documentation only.
Provenance split: a separate user-run PowerShell rehash produced header_rehash_verification_v2.txt. Cursor reviewed that transferred text and include_hashes.txt. Cursor did not rehash header bytes, did not open the SDK package, and did not inspect the measuring PC.

This record does not copy an SDK package, a header, an executable, or an object file into Git. It does not edit a frozen document. It does not compile, download, extract, install, or launch an SDK or a compiler. It does not grant an operational SDK pin, an operational MinGit pin, production authority, or execution authority. FULL_INR_READY=NO.

## 1. Baseline

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: 470c0ba267aa5e19a3a624c81fcf4cde109764ec
Cursor-verified Git HEAD before this record: 470c0ba267aa5e19a3a624c81fcf4cde109764ec
HEAD comparison: MATCH.
HEAD subject: docs: record limited human acceptance of the ABI offset follow-up evidence

Cursor-verified tracked status before this record: no tracked path differed from HEAD. git status --porcelain=v1 reported only the pre-existing untracked .wacp/ tree. This record does not read, stage, edit, or delete any .wacp/ path. Frozen documents at this HEAD stay unmodified.

## 2. Transferred files

Evidence directory: C:/dev/_tmp/weaver-abi-evidence-20261012/abi-followup-20261012
That directory contains five files. The three earlier follow-up files remain at the sizes and SHA-256 values already recorded. This record reviews the two rehash texts and remeasures include_hashes.txt for the cross-check. These files stay outside Git.

| File | Size in bytes | SHA-256 | Role in this record |
| --- | ---: | --- | --- |
| header_rehash_verification_v2.txt | 26657 | 452963153d799315d2c8db07c1c0180740a1bb5f3b74837a63af0e013df2b32e | Reviewed. Expected digest MATCH. |
| include_hashes.txt | 23426 | 99709fd72298e4cff9a66dffd9ad5fbb98677ccd7462af95c805ce6db1c7c37e | Cross-check manifest. MATCH with the digest already recorded. |
| header_rehash_verification.txt | 544 | 758f23a8f8c4e7e12e3b71bae022e28de54f9584ca9b0626b098287084165059 | v1 summary only. Incomplete. |
| abi_offsets.cpp | 1390 | f1955ed33ca81eaad2cfd99fd6d50f2791ba422f165e3c4f54a799662dcfa514 | Unchanged earlier file. Not re-reviewed for offsets. |
| abi_offsets.log | 32547 | 1e5632f54348683c2b2f14733cec7ce94a60d57e1903178fa55a50f258f9f000 | Unchanged earlier file. Not re-reviewed for offsets. |

header_rehash_verification_v2.txt is UTF-8 with a byte-order mark and CRLF, 173 lines: 13 metadata lines, one blank line, and 159 MATCH lines. It ends with CRLF. include_hashes.txt is CRLF, with no byte-order mark, 159 lines. header_rehash_verification.txt is CRLF, with no byte-order mark, 544 bytes: 12 content lines and one trailing blank line. It contains no per-header MATCH line.

## 3. User-run rehash and Cursor review of transferred text

User-run PowerShell rehash of 159 existing headers. The v2 text states its method as PowerShell Get-FileHash SHA256, scoped to existing files, with no compile, extraction, or execution. It states HEADERS_EXPECTED: 159, HEADERS_MATCHED: 159, HEADERS_MISMATCHED_OR_MISSING: 0, and HEADER_REHASH_RESULT: PASS. Cursor did not run that PowerShell rehash and did not recompute any header digest from header bytes.

Cursor's review of transferred text only. Cursor hashed the transferred text files, parsed the 159 MATCH lines, and compared each path and digest with include_hashes.txt. That comparison is a text comparison. It is not a new measurement of header bytes.

SDK nupkg digest matched as a whole. The v2 field SDK_PACKAGE_SHA256 is A74CA8F9AF98BD61925D9E2932AD98F746306123167B8F0BBA99CD9EA9F03807. That 64-digit value equals the whole-package digest already recorded for Microsoft.Windows.SDK.CPP 10.0.28000.2705. The v2 text presents that equality as a whole-package digest match from the user-run rehash.

Package internal header-byte equivalence NOT checked. The v2 field PACKAGE_INTERNAL_ENTRIES_VERIFIED is NO. Cursor did not open the nupkg, did not list its entries, and did not compare header bytes inside the package with the 159 on-disk headers. A whole-package digest match does not establish that each package entry equals the corresponding hashed header.

No operational SDK PIN or execution authorization. The v2 field OPERATIONAL_SDK_PIN is UNRATIFIED. This record grants no operational SDK pin, no operational MinGit pin, and no execution authority. EXECUTION_BINDING_REAL remains UNEXECUTED.

FULL_INR_READY=NO. The v2 text states FULL_INR_READY: NO. This record keeps that result.

The v2 field MANIFEST_SHA256 is 99709FD72298E4CFF9A66DFFD9AD5FBB98677CCD7462AF95C805CE6DB1C7C37E. Cursor recomputed that digest from the bytes of include_hashes.txt. The two digests match.

## 4. v1 is incomplete

header_rehash_verification.txt is an incomplete v1 summary. Its own first body line in v2 says that v2 supersedes an incomplete v1 verification caused by a PowerShell variable collision. The v1 field HEADERS_MATCHED is the text System.Collections.Hashtable. That text is the PowerShell automatic $Matches variable rendered as a Hashtable, not a header count. v1 records HEADER_REHASH_RESULT: FAIL beside HEADERS_MISMATCHED_OR_MISSING: 0.

This record treats v1 as incomplete because of that $Matches collision. The v1 FAIL is a summary-field defect. It is not a header mismatch. v1 contains no per-header row that could support a mismatch finding. The 159-row comparison in section 5 uses v2 and include_hashes.txt.

## 5. Cross-check of 159 MATCH records

Cursor parsed every v2 MATCH line as MATCH, one decimal size, one uppercase 64-digit digest, and one path, separated by space-pipe-space. All 159 lines matched that shape. include_hashes.txt has 159 lines. Every line is an uppercase 64-digit digest, two spaces, and one path.

Comparison result:

- MATCH records: 159
- include_hashes.txt records: 159
- Unique paths: 159
- Unique digests: 159
- Paths present in v2 and absent from include_hashes.txt: 0
- Paths present in include_hashes.txt and absent from v2: 0
- Path-and-digest mismatches: 0
- Order: the 159 v2 paths and digests follow the same order as include_hashes.txt
- Paths outside the two permitted include roots: 0

Permitted paths, matching the unique-path set already recorded for include_hashes.txt:

- SDK include root, 151 unique paths: C:\ABI-Verification\SDK-10.0.28000.2705\c\Include\10.0.28000.0\ . Those 151 paths divide into shared 38, ucrt 13, and um 100. Each path has exactly one directory under that root.
- MSVC toolset include root, 8 unique paths: C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.50.35717\include\ . The eight basenames are concurrencysal.h, excpt.h, limits.h, sal.h, stdarg.h, vadefs.h, vcruntime.h, and vcruntime_string.h.

Each MATCH line carries one header size in bytes. The 159 sizes run from 554 to 1636141. Four lengths are shared by distinct headers with distinct digests: 554 appears twice, 918 appears four times, 1413 appears twice, and 11292 appears twice. The size set therefore has 153 distinct values. Path identity and digest identity remain one-to-one.

## 6. What remains open

The following stay OPEN. This record does not close them.

- Package-internal header-byte equivalence: NOT CHECKED. PACKAGE_INTERNAL_ENTRIES_VERIFIED remains NO. Cursor did not extract or compare nupkg entries.
- Header bytes on the measuring PC: NOT REHASHED BY CURSOR. The 159 MATCH rows are transferred text from the user-run PowerShell rehash.
- v1 rehash result: INCOMPLETE. The v1 FAIL stays a $Matches summary-field defect. It is not evidence of a header mismatch, and it is not a completed pass.
- Operational SDK pin: UNRATIFIED. OPERATIONAL_SDK_PIN remains UNRATIFIED.
- MinGit operational PIN: OPEN. OPERATIONAL_MINGIT_PIN remains UNRATIFIED.
- Real execution binding: OPEN. EXECUTION_BINDING_REAL remains UNEXECUTED. This record authorizes no execution.
- Independent third-party verification: NONE. No second provider remeasured the nupkg entries or the 159 header files.
- Full ABI ratification: not granted.
- Production authority: not granted. Runtime authority: not granted.
- FULL INR readiness: NO. FULL_INR_READY=NO.

## 7. Batch boundary

This batch adds one documentation path and edits nothing else. It does not stage, commit, or push. .wacp/ remains untracked and excluded. No frozen document is edited. No SDK package, header, executable, or object file is added to Git.

COMMITTED: NO
PUSHED: NO
FULL_INR_READY: NO
