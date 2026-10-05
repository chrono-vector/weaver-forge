# Official CPython 3.14.3 amd64 EXE Evidence Preparation v0 - D0-R1

## 1. Status

`READY_FOR_TARGETED_CLOSURE_REVIEW`

This additive documentation-only remediation closes only Pi findings M1 and M2
by design. It does not collect evidence, install or execute Python, establish a
pin, implement the frozen amendment, or authorize any later operation.

## 2. Binding and Scope

This R1 supplements without modifying:

- original D0 commit:
  `7b77fb3454d7cc7582bfe7a7a9a692f37127c9e4`;
- original D0 SHA-256:
  `5f9ba780b2719d46f4a7120b79699ca8bf846593038a9d9b436e1c8b261f31e6`;
- original D0 Git blob:
  `b05e99ba96d25bbb7cab3f1daaed7ed78287819f`;
- frozen interpreter-provenance amendment D1 commit:
  `f392778c644803791310c722af373e3ec0981885`;
- frozen D1 SHA-256:
  `571acef37b2c0aae652225ee7e21242427e9b2f2997f363811b7e267bfcfb9bf`;
- frozen D1 Git blob:
  `0bae82c83cfa846c625919f5608b6487f1c0e84d`.

If this R1 conflicts with the frozen D1, the frozen D1 controls and the affected
R1 predicate is `NOT_ESTABLISHED`. All original D0 schemas, boundaries, negative
state, and Pi N1 staging remain unchanged except for the two targeted closures
below.

## 3. M1 Closure: Pristine Root and Clean Baseline

### 3.1 Pre-install target-root state

Before installer execution, the exact intended target root
`C:\Program Files\WeaverForge\Python314` must satisfy exactly one of these
conditions:

1. **Absent:** the lexical target does not exist, its resolved target does not
   exist, and no ancestor reparse or mount behavior redirects it to existing
   content; or
2. **Fresh and empty:** a separately authorized preparation step created the
   exact root for this evidence session, the root contains zero entries and no
   alternate data streams or reparse content, and its creation event, owner,
   DACL, volume identity, directory identity, and empty enumeration are
   independently recorded before installer execution.

A pre-existing root is not made clean by deleting selected files, relying on an
installer repair/overwrite, or observing that expected files are absent. Any
unexplained prior existence, content, alternate stream, link, redirection,
identity discontinuity, incomplete enumeration, or inability to prove one of
the two conditions yields `NOT_ESTABLISHED`. Recovery requires a new evidence
session and a fresh target root; a deterministic manifest of a polluted tree is
not a clean baseline.

The before-install record must contain:

- evidence-session identifier and UTC observation interval;
- lexical target, resolved target or confirmed absence, volume identity, and
  relevant ancestor identities;
- existence mode (`absent` or `fresh-empty`);
- creation provenance when `fresh-empty`;
- owner, DACL, reparse/mount/link, alternate-stream, and entry-count results;
- exact tools, versions, commands, operator, raw-output digests, and independent
  recomputation disposition.

### 3.2 Installer-to-baseline closed interval

The installer completion event opens a closed evidence interval that ends only
after the clean baseline rows, entry count, and digest have been captured and
independently recomputed. During that interval:

- no non-installer `python.exe`, `pythonw.exe`, launcher, module, script, import,
  package tool, or other interpreter execution is permitted;
- no venv creation, pip invocation, third-party package operation, custody use,
  general use, repair, update, manual file operation, or other base-prefix
  mutation is permitted;
- only read-only collection needed to establish installer output, path/ACL
  facts, and baseline bytes is permitted;
- collection tooling must not import from, execute, compile, normalize, repair,
  quarantine, index, or otherwise write into the base prefix.

The after-install/pre-baseline record must bind the installer process completion
and exit result to the same evidence session, target directory identity, host,
and observation interval. It must record the process and file-activity evidence
used to exclude non-installer interpreter execution and intervening writes. A
mere Human assertion, lack of a visible console window, or final tree digest is
not sufficient proof of the closed interval.

If non-installer interpreter execution or another write occurs, or if the
collector cannot exclude it and demonstrate that all permitted collection was
non-writing, the result is `NOT_ESTABLISHED`. Collection must restart with a new
session and fresh installation/root; later deletion or a second manifest cannot
repair the failed clean-baseline claim.

### 3.3 Startup and import customization surfaces

Before accepting the baseline, the collector must explicitly enumerate and
classify every startup or import customization surface covered by the frozen D1,
including at least:

- every `sitecustomize.py` and `usercustomize.py` under the base prefix;
- every `.pth` and `._pth` file under the base prefix;
- base `Lib\site-packages`, import machinery, startup configuration, and any
  equivalent installer-created surface capable of changing startup, module
  search, or imported code.

Each such artifact must be included in the complete manifest and must be either
absent or proven to be an output of the exact accepted official installation,
bound to installed-state evidence, and explicitly accepted under the frozen
evidence rule. Presence in a deterministic manifest alone is insufficient.
Unknown, unexplained, pre-existing, externally created, or unreviewed
customization yields `NOT_ESTABLISHED` and requires a fresh installation/root.

### 3.4 Required M1 evidence binding

The later handoff must bind, in order:

1. pre-install target-root record;
2. exact accepted installer and invocation record;
3. installer completion record;
4. installer-to-baseline closed-interval record;
5. after-install/pre-baseline root and ACL record;
6. startup/import customization classification;
7. complete baseline rows, count, and digest;
8. independent recomputation of these records and bindings.

An omitted, stale, cross-session, cross-root, or ambiguous predecessor makes the
whole clean-baseline claim `NOT_ESTABLISHED`.

`M1_CLOSED_BY_DESIGN: YES`

## 4. M2 Closure: Exact Path Canonicalization

The baseline uses only the frozen D1 schema
`cp314-base-prefix-manifest-v0`. For every regular file, the collector must apply
this exact ordered pipeline without alternate normalization or discretion:

1. Derive the source path relative to the exact resolved frozen base-prefix
   root.
2. Reject an absolute, parent-bearing, escaping, empty, invalid, or
   non-relativizable result.
3. Replace every ASCII backslash byte `0x5c` (`\`) with ASCII slash byte `0x2f`
   (`/`).
4. Require every resulting path character to be ASCII (`0x00` through `0x7f`),
   while rejecting NUL, CR, LF, and any path form invalid under the frozen
   schema.
5. Lowercase only ASCII `A` through `Z` by adding `0x20`; leave all other
   permitted ASCII bytes unchanged. Locale-sensitive mapping, Unicode case
   folding, Unicode normalization, and filesystem-supplied display casing are
   forbidden substitutes.
6. Reject duplicate normalized paths. Also reject distinct source paths that
   become identical after slash replacement and ASCII lowercasing; this is an
   ASCII case collision and is never resolved by traversal order.
7. For each accepted normalized path, compute exact raw-file decimal byte size
   and exact raw-file lowercase SHA-256, then serialize one row as:
   `<normalized-relative-path> NUL <decimal-size> NUL <lowercase-file-sha256> LF`.
8. Sort complete rows by their normalized canonical ASCII path bytes using
   unsigned bytewise ascending order. No locale, Unicode, natural, filesystem,
   or case-preserving sort is allowed.
9. Serialize the manifest as the exact concatenation of those sorted ASCII rows,
   with no header, BOM, separator change, terminal transformation, or platform
   newline conversion.
10. Hash the exact manifest bytes with SHA-256 and represent the result as
    exactly 64 lowercase ASCII hexadecimal characters. Record the exact entry
    count and final digest.

The serialization in step 7 and concatenation in step 9 are exactly the frozen
D1 wording and semantics. ASCII rows are also valid UTF-8 bytes, so no separate
encoding transformation occurs. The full ordered rows must be retained for
independent byte-for-byte recomputation.

Normal mixed-case CPython source paths such as `DLLs` and `Lib` are accepted
only by deterministic ASCII lowercasing to `dlls` and `lib` within their full
relative paths. This does not permit two source paths that differ only by ASCII
case: such paths collide at step 6 and fail closed.

Any pipeline reordering, omitted check, collector-selected alternative,
case-preserving output, locale/Unicode lowercasing, path cleanup after an escape,
or digest over a rendered text form yields `NOT_ESTABLISHED`.

`M2_CLOSED_BY_DESIGN: YES`

## 5. Targeted Adversarial Self-Review

| Case | Required disposition |
| --- | --- |
| Pre-existing target root containing any unexplained file | `NOT_ESTABLISHED`; restart from a fresh installation/root |
| Unexplained `sitecustomize.py`, `usercustomize.py`, `.pth`, or `._pth` | `NOT_ESTABLISHED`; manifest inclusion does not cure it |
| Any non-installer interpreter execution before baseline capture | `NOT_ESTABLISHED`; restart from a fresh installation/root |
| Inability to exclude a write between installer completion and baseline capture | `NOT_ESTABLISHED`; restart from a fresh installation/root |
| Normal source path `DLLs\_ssl.pyd` or `Lib\encodings\__init__.py` | Accept only after exact slash replacement and ASCII lowercasing |
| Two source paths differing only by ASCII case | `NOT_ESTABLISHED` at duplicate/collision check |
| Absolute, parent-bearing, empty, or escaping relative path | `NOT_ESTABLISHED` before serialization |
| Locale-sensitive or Unicode lowercasing substituted for ASCII mapping | `NOT_ESTABLISHED` |

All eight cases have deterministic fail-closed dispositions. None depends on
collector choice, traversal order, or a later successful digest.

## 6. Preserved Boundaries and Negative State

This R1 preserves the original D0's official python.org CPython 3.14.3 amd64 EXE
restriction, evidence schemas, freshness rules, Pi N1 clarification, handoff
boundary, authority inequalities, and stop/go gates. It does not reinterpret the
frozen D1 or any CLOSED or Human Final scope.

`FINAL_PIN_VALUES_ESTABLISHED: NO`

`ARTIFACT_DOWNLOADED: NO`

`PYTHON_INSTALLED: NO`

`IMPLEMENTATION_PERFORMED: NO`

`PRE_REAL_ENVIRONMENT_ESTABLISHED: NO`

`REAL_KEY_GENERATION_AUTHORIZED: NO`

`REAL_KEY_GENERATED: NO`

`ADMISSION_PERFORMED: NO`

## 7. Next Gate

The only next step authorized by this status is one targeted closure review of
M1 and M2. Evidence collection, download, installation, account or ACL changes,
venv or pip use, implementation, key operations, Admission, and push remain
outside this batch.
