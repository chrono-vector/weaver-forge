# INR-HER MinGit SDK Nupkg Internal Header Comparison Evidence

Record date: 2026-10-12 (Asia/Tokyo)
Status: SDK_NUPKG_INTERNAL_HEADER_COMPARISON_TRANSFERRED_TEXT_REVIEWED_FULL_INR_NOT_READY
Scope: one documentation-only preservation of the transferred nupkg internal header comparison and of its text comparison with include_hashes.txt and header_rehash_verification_v2.txt
Decision source: the Human explicit approval to review this transferred comparison text and to preserve the review as documentation only.
Provenance split: the user ran a PowerShell ZipArchive read-only verification on a separate Windows 11 PC and transferred sdk_nupkg_internal_header_comparison.txt. Cursor reviewed that transferred text against include_hashes.txt and header_rehash_verification_v2.txt. Cursor did not run ZipArchive, did not open the SDK package, did not recompute entry digests from package bytes, and did not inspect the measuring PC.

This record preserves a text review of 151 selected SDK header archive entries. It covers those 151 entries only. The whole SDK package, runtime safety, and operational authorization remain outside this result. It does not copy an SDK package, a header, an executable, or an object file into Git. It does not edit a frozen document. It does not compile, download, extract, install, or launch an SDK or a compiler. It does not grant an operational SDK pin, an operational MinGit pin, production authority, or execution authority. FULL_INR_READY=NO.

## 1. Baseline

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: 45855b0941dcdd14fffef447355ff42b381f0ea6
Cursor-verified Git HEAD before this record: 45855b0941dcdd14fffef447355ff42b381f0ea6
HEAD comparison: MATCH.
HEAD subject: docs: record limited human acceptance of the SDK header rehash v2 evidence

Cursor-verified tracked status before this record: no tracked path differed from HEAD. git status --porcelain=v1 reported only the pre-existing untracked .wacp/ tree. This record does not read, stage, edit, or delete any .wacp/ path. Frozen documents at this HEAD stay unmodified.

## 2. Transferred file

Evidence directory: C:/dev/_tmp/weaver-abi-evidence-20261012/abi-followup-20261012
That directory contains six files. The five earlier follow-up files remain outside this review except as comparison inputs. These files stay outside Git.

| File | Size in bytes | SHA-256 | Role in this record |
| --- | ---: | --- | --- |
| sdk_nupkg_internal_header_comparison.txt | 19029 | a24c9a06261e8dd0692d48344a3ceca067673a37fae808c913a52c33989cf581 | Reviewed. Expected digest MATCH. |
| include_hashes.txt | 23426 | 99709fd72298e4cff9a66dffd9ad5fbb98677ccd7462af95c805ce6db1c7c37e | Cross-check manifest. MATCH with the digest already recorded. |
| header_rehash_verification_v2.txt | 26657 | 452963153d799315d2c8db07c1c0180740a1bb5f3b74837a63af0e013df2b32e | Prior on-disk rehash text. MATCH with the digest already recorded. |

sdk_nupkg_internal_header_comparison.txt is UTF-8 with a byte-order mark and CRLF, 164 lines: 12 metadata lines, one blank line, and 151 MATCH lines. It ends with CRLF. include_hashes.txt and header_rehash_verification_v2.txt keep the encodings and line counts already recorded for the header-rehash v2 evidence.

## 3. User-run ZipArchive comparison and Cursor review of transferred text

User-run PowerShell ZipArchive read-only verification on a separate Windows 11 PC. The transferred text states its method as .NET ZipArchive read-only and SHA256, with no extraction, installation, compilation, or target execution. It states SDK_HEADERS_EXPECTED: 151, SDK_HEADERS_MATCHED: 151, SDK_HEADERS_MISMATCHED_OR_MISSING: 0, MSVC_HEADERS_EXCLUDED: 8, and PACKAGE_HEADER_COMPARISON: PASS. Cursor did not run that verification and did not recompute any archive-entry digest from package bytes.

Cursor's review of transferred text only. Cursor hashed the transferred comparison file, parsed the 151 MATCH lines, and compared each archive path and digest with the SDK subset of include_hashes.txt. Cursor also compared each archive path, digest, and byte size with the SDK subset of header_rehash_verification_v2.txt. That comparison is a text comparison of transferred evidence. The ZipArchive measurement itself remains the user-run verification on the separate Windows 11 PC.

SDK package digest carried forward as text. The comparison field PACKAGE_SHA256 is A74CA8F9AF98BD61925D9E2932AD98F746306123167B8F0BBA99CD9EA9F03807. That 64-digit value equals the whole-package digest already recorded for Microsoft.Windows.SDK.CPP 10.0.28000.2705 and equals the v2 field SDK_PACKAGE_SHA256. Cursor did not rehash the nupkg.

Manifest digest matched as text. The comparison field MANIFEST_SHA256 is 99709FD72298E4CFF9A66DFFD9AD5FBB98677CCD7462AF95C805CE6DB1C7C37E. Cursor recomputed that digest from the bytes of include_hashes.txt. The two digests match.

No operational SDK PIN or execution authorization. The comparison field OPERATIONAL_SDK_PIN is UNRATIFIED. This record grants no operational SDK pin, no operational MinGit pin, and no execution authority. EXECUTION_BINDING_REAL remains UNEXECUTED.

FULL_INR_READY=NO. The comparison text states FULL_INR_READY: NO. This record keeps that result.

## 4. Cross-check of 151 MATCH records

Cursor parsed every comparison MATCH line as MATCH, one decimal size, one uppercase 64-digit digest, and one archive-relative path, separated by space-pipe-space. All 151 lines matched that shape. The file contains no MISMATCH line and no MISSING line.

include_hashes.txt has 159 lines. Every line is an uppercase 64-digit digest, two spaces, and one path. Of those 159 paths, 151 sit under C:\ABI-Verification\SDK-10.0.28000.2705\c\Include\10.0.28000.0\ and 8 sit under the MSVC toolset include root. header_rehash_verification_v2.txt has 159 MATCH lines with the same 159 paths, the same 159 digests, and one byte size on each line.

Archive paths use forward slashes and begin at c/Include/10.0.28000.0/. Cursor mapped each archive path to the on-disk path with the same suffix under C:\ABI-Verification\SDK-10.0.28000.2705\.

Comparison result:

- MATCH records: 151
- MISMATCH records: 0
- MISSING records: 0
- Unique archive paths: 151
- Unique digests: 151
- SDK paths in include_hashes.txt: 151
- SDK paths in header_rehash_verification_v2.txt: 151
- Archive paths absent from the include_hashes.txt SDK subset: 0
- include_hashes.txt SDK paths absent from the archive comparison: 0
- Path-and-digest mismatches against include_hashes.txt: 0
- Path, digest, and byte-size mismatches against header_rehash_verification_v2.txt: 0
- include_hashes.txt has no byte size, so byte size is independently comparable against header_rehash_verification_v2.txt only. All 151 sizes matched that v2 SDK subset.
- Row order follows ascending byte size. That order differs from the order of include_hashes.txt and from the order of header_rehash_verification_v2.txt. The path, digest, and size sets still match.

Permitted SDK archive paths, matching the 151-path SDK subset already recorded for include_hashes.txt:

- shared: 38
- ucrt: 13
- um: 100

Each archive path has exactly one directory under c/Include/10.0.28000.0/. No archive path leaves that root.

Eight MSVC headers were excluded. They remain in include_hashes.txt and in header_rehash_verification_v2.txt, and they are absent from sdk_nupkg_internal_header_comparison.txt. Their basenames are concurrencysal.h, excpt.h, limits.h, sal.h, stdarg.h, vadefs.h, vcruntime.h, and vcruntime_string.h. Their on-disk root in the earlier rehash text is C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.50.35717\include\. MSVC_HEADERS_EXCLUDED: 8 agrees with that excluded set.

Each MATCH line carries one header size in bytes. The 151 sizes run from 554 to 1636141. Three lengths are shared by distinct SDK headers with distinct digests: 11292 appears twice, 1413 appears twice, and 918 appears four times. The size set therefore has 146 distinct values. Path identity and digest identity remain one-to-one. The second 554-byte header in the 159-row rehash is MSVC stdarg.h, and that header is outside this 151-row comparison. The SDK header sdv_driverspecs.h remains the only 554-byte row here.

## 5. What this result covers

The transferred comparison marks 151 unique SDK archive header entries MATCH, with zero MISMATCH and zero MISSING. For those 151 entries, the archive path and digest agree with include_hashes.txt, and the archive path, digest, and byte size agree with header_rehash_verification_v2.txt.

The result covers only those selected 151 SDK header entries. It leaves the rest of the SDK package unchecked. It establishes no runtime safety. It grants no operational authorization. PACKAGE_HEADER_COMPARISON: PASS in the transferred text is a pass for this 151-entry selection. FULL_INR_READY stays NO. The operational SDK pin and the operational MinGit pin stay UNRATIFIED.

## 6. What remains open

The following stay OPEN. This record does not close them.

- SDK package contents beyond the selected 151 header entries: NOT CHECKED. A 151-entry header comparison leaves every other nupkg entry unreviewed.
- Header bytes inside the nupkg: NOT REHASHED BY CURSOR. The 151 MATCH rows are transferred text from the user-run PowerShell ZipArchive verification on a separate Windows 11 PC.
- Eight MSVC headers: EXCLUDED from this comparison. Their on-disk rehash rows remain in the earlier 159-row text. This record does not turn those eight rows into nupkg evidence.
- Operational SDK pin: UNRATIFIED. OPERATIONAL_SDK_PIN remains UNRATIFIED.
- MinGit operational PIN: OPEN. OPERATIONAL_MINGIT_PIN remains UNRATIFIED.
- Real execution binding: OPEN. EXECUTION_BINDING_REAL remains UNEXECUTED. This record authorizes no execution.
- Runtime safety: NOT ESTABLISHED.
- Operational authorization: NOT GRANTED.
- Independent third-party verification: NONE. No second provider remeasured the nupkg entries.
- Full ABI ratification: not granted.
- Production authority: not granted.
- FULL INR readiness: NO. FULL_INR_READY=NO.

## 7. Batch boundary

This batch adds one documentation path and edits nothing else. It does not stage, commit, or push. .wacp/ remains untracked and excluded. No frozen document is edited. No SDK package, header, executable, or object file is added to Git.

COMMITTED: NO
PUSHED: NO
FULL_INR_READY: NO
