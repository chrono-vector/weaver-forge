# SEIC-001 Design Boundary

SEIC-001 is an additive, non-authoritative hardening layer in the existing
`audit_lifecycle.epistemic` scope. It does not replace or reinterpret any CLOSED
Weaver contract.

## Epoch Model

An `evaluator_epoch.v0` record identifies one immutable accepted base commit,
`c_E`. It pins the exact checker bytes, evaluator entrypoints, evaluator semantic
surface (ESS), non-semantic external imports, and closure policy. The record is
canonical JSON loaded from a regular, non-symlink epoch file outside the
proposal repository. Direct bytes and proposal-local epoch paths are rejected.
It never selects `HEAD`, and the implementation does not derive `c_E` from the
current branch.

## Epoch Trust Binding (R1)

External location and non-symlink checks establish location only; they do not
establish Human approval. The epoch record therefore never authenticates
itself. `evaluate_closure` requires an independent trust input,
`trusted_epoch_sha256`: the plain SHA-256 of the exact approved epoch record
bytes, supplied by the caller from the Human approval record kept outside the
proposal tree and outside the epoch file.

Human approval is represented by the independently protected binding,
not by a string inside the epoch file.

The binding is verified before the record is interpreted. A missing binding
yields `REQUIRE_HUMAN_REVIEW`; a malformed binding yields `INVALID`; any byte
substitution, edit, or re-serialization yields `EPOCH_MISMATCH`. The fields
`approval_status` and `human_approval_ref` are descriptive only: an epoch that
self-declares `HUMAN_APPROVED`, carries an arbitrary approval reference, or
selects its own entrypoints and ESS cannot reach `PASS` without the binding. A
bound record describing itself as `UNAPPROVED` still yields
`REQUIRE_HUMAN_REVIEW` (descriptive fields may withhold trust, never create it).
The binding reuses generic SHA-256 over exact bytes; it is not a new digest
domain, authority, or registry.

The executing checker must have the same SHA-256 as the checker blob stored at
`c_E` and pinned by the epoch record. A mismatch yields `EPOCH_MISMATCH`.

Proposal content is read from Git objects. The changed-path set `M(P)` is always
the cumulative tree difference from `c_E` to the proposal commit. Proposal-local
commit boundaries do not change that comparison.

## ESS Model

Every ESS entry has exactly:

```json
{"relative_path":"...","sha256":"..."}
```

Paths are normalized repository-relative UTF-8 paths with `/` separators. They
cannot be absolute, contain `.` or `..` components, repeat after normalization,
or resolve to a symlink. Entries are unique and sorted by UTF-8 bytes. Digests
are lowercase SHA-256 over exact Git blob bytes.

The checker, evaluator entrypoints, epoch declaration paths, repo-local imported
helpers (including executed parent packages and submodules imported with
`from package import name`), and statically identified semantic data files must
be covered by ESS. External imports may be listed only when the trusted epoch
explicitly classifies them as non-semantic, and never for reserved semantic
machinery (below). Unlisted, unresolved, dynamic, generated, or shadow reach
cannot produce `PASS`.

## Closed SEIC-v0 Evaluator Syntax Profile (R1)

Reach analysis applies only to Python files reachable from the trusted
evaluator entrypoints inside ESS; unrelated repository code is not inspected
for these constructs. The profile is closed and conservative:

- Known-safe supported syntax is analyzed.
- Known semantic dependencies require ESS coverage.
- Unknown, potentially semantic syntax is `UNKNOWN_REACH`.

Supported (statically understood):

- `import m`, `import m as a`, `from m import n`, `from m import n as a`, and
  relative imports. Every binding is resolved to its canonical target, so
  aliases are analyzed exactly like unaliased names.
- Data reads only through `open(<literal>)`, `io.open(<literal>)`, or
  `pathlib.Path(<literal>).read_bytes() | read_text() | open()` (also through
  import aliases), where the literal is a normalized ESS path.
- Ordinary computation, plus the code-owned safe builtin allowlist (container,
  numeric, string, iteration, type-check, and exception builtins).

`UNKNOWN_REACH` (fail closed):

- any import binding whose target is in the code-owned reserved semantic
  machinery set, regardless of aliasing or epoch classification: import
  machinery and dynamic loading (`importlib`, `imp`, `_imp`, `runpy`,
  `zipimport`, `pkgutil`, `builtins`, `__main__`, `marshal`, `pickle`,
  `shelve`, `code`, `codeop`, `ctypes`, `inspect`), plugin discovery
  (`importlib.metadata`, `pkg_resources`, `setuptools`, `distutils`,
  `stevedore`, `pluggy`, `importlib_metadata`, `importlib_resources`), and
  process/environment/filesystem-discovery configuration (`os`, `sys`, `nt`,
  `posix`, `site`, `sitecustomize`, `usercustomize`, `sysconfig`, `platform`,
  `locale`, `getpass`, `argparse`, `getopt`, `optparse`, `fileinput`,
  `configparser`, `dotenv`, `glob`, `shutil`, `tempfile`, `socket`,
  `subprocess`, `multiprocessing`, `_io`). This covers aliased or unaliased
  `sys.path` mutation, `os.environ`/`os.getenv`, `sys.argv`, and import-machinery
  aliases such as `import importlib as il` or
  `from importlib import import_module as im`;
- star imports and ambiguous import bindings;
- builtins outside the safe allowlist (for example `__import__`, `eval`,
  `exec`, `compile`, `globals`, `locals`, `vars`, `input`, `breakpoint`), and
  any non-call reference to `open`/`io.open` (aliasing a reader);
- every `getattr`/`hasattr`/`setattr`/`delattr` use (R2: calls and bare
  references, literal names included; no safe-receiver exemption),
  `operator.attrgetter`/`operator.methodcaller`, and introspection escapes
  (`__dict__`, `__getattr__`, `__subclasses__`, `__globals__`, `__builtins__`,
  frame attributes, and similar);
- non-literal or non-ESS reads, `pathlib` use outside the recognized literal
  read form, `codecs.open`, `io.FileIO`, `io.open_code`, and resource or
  plugin-discovery method calls on unknown receivers (`read_text`,
  `read_bytes`, `open`, `iterdir`, `glob`, `rglob`, `listdir`, `scandir`,
  `entry_points`, `iter_entry_points`, `get_data`, `find_spec`,
  `load_module`, `exec_module`, `resource_*`);
- unresolved repo-local imports, repo-local imports outside ESS, shadow
  ambiguity, unparseable semantic Python, and generated inputs outside ESS.

## Caller Semantic Input (R1)

Any caller-supplied semantic input other than `None` or an exact empty mapping
is `CALLER_SEMANTIC_INPUT`, independent of nesting depth, field naming
(aliased fields), file/path references, or mapping type (for example a process
environment mapping). Inside the trusted evaluator, caller-controlled values
cannot silently change evaluator meaning: reading semantic configuration from a
caller-derived path is a non-literal read, caller-chosen attribute access is
dynamic attribute access, and environment/process-derived values require
reserved modules or builtins. Each is `UNKNOWN_REACH`.

## Evaluation Boundary

SEIC-v0:

- verifies the independent approval binding, the canonical epoch, and ESS
  against `c_E`;
- rejects checker, epoch declaration, evaluator, config, schema, table, helper,
  and other ESS changes with `CLOSURE_HIT`;
- rejects caller semantic input;
- resolves bounded static Python imports and direct semantic reads from trusted
  evaluator entrypoints under the closed SEIC-v0 syntax profile;
- returns `UNKNOWN_REACH` for anything outside that profile, dynamic loading,
  path manipulation, unresolved imports, shadow ambiguity, or unbound semantic
  reads;
- emits one canonical `evaluator_closure.v0` receipt;
- performs only read-only Git object inspection and file reads.

The implementation does not execute proposal code, write protected state,
provide a service, use a database, or require network access.

## Nonclaims

No disposition grants authorization, correctness, merge approval, policy
approval, Human Final, independent reproduction, production authorization, new
Weaver authority, or a higher evidence level. `PASS` means only that this bounded
v0 checker detected no closure violation under the pinned, Human-bound epoch.

No new digest domain is introduced. The receipt, approval binding, and
epoch/ESS bindings reuse the repository's existing canonical JSON and generic
SHA-256 mechanisms.

Exact evidence ceiling:
`LOCAL_SEIC_V0_IMPLEMENTATION_AND_SYNTHETIC_VALIDATION_AT_PINNED_REPOSITORY_STATE`.
