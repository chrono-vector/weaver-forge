"""Structural-validator test suite (1.0.0-rc5).

Covers:
  * schema-block CONTRACT tests (validator FILE_REQUIRED_FIELDS vs the exact
    BEGIN_SCHEMA_BLOCK / writer sections of the host and container scripts),
  * duplicate-key rejection,
  * outcome consistency across the outcome-bearing files,
  * golden-fixture validation (both the committed tests/fixtures/ trees and
    freshly built temp trees) for every required outcome / failure mode,
  * host-safety static assertions (canonical constants, readonly, overrides,
    WORK_ROOT guards) read from the shell script text,
  * manifest grammar / inventory,
  * machine verdict-ceiling enforcement,
  * redaction rules, and
  * upstream_product_commands_not_run enforcement.

Nothing here executes Docker/Cargo/Witness scripts.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
for p in (SCRIPTS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import validate_witness_evidence as v  # noqa: E402
import fixtures_lib as fx  # noqa: E402

HOST_SCRIPT = Path(SCRIPTS) / "run_witness_narrow_build.sh"
CONTAINER_SCRIPT = Path(SCRIPTS) / "container_narrow_build.sh"
FIXTURES = Path(HERE) / "fixtures"

# Fixed input identities only; no checkout/filter/fetch or historical builder upgrade.
_REGRESSION_COMMIT = "319c6dcb92c5152225076b99a465436ba55924b3"
_REGRESSION_TREES = {
    "success-artifact-present": "97bc2b000f5cda1566aab656047bdd8e34f08d3c",
    "build-not-started": "d2022a65e4a092e9056dae0d0d1d6a4867d98488",
    "cargo-failed": "f532c423d92c20cdf01d5955103a8b6df577a345",
    "artifact-missing": "761fdb4e47d828717a474907428b3438b5f0177a",
    "infrastructure-failure": "2147d9b8c585aa991396794d4372855359b593dd",
    "static-inspection-incomplete": "581a98ff716915d40a70a214027c5205b47acdd6",
    "image-pull-failure": "9dcb910bf671fcfb869bfef83e3fded8a4d2c6bb",
    "image-inspect-failure": "a9a4a8f92ff800ae49415c6688e48debea3eff90",
    "digest-mismatch": "c7d263a6bed273263ea959b81f97f1c1b58f4131",
    "platform-mismatch": "f6c1bfd1c1303afa7575fbdd8036f0056a11eeca",
    "rc5-preliminary-success": "2bc64e1f814d7ebf2707f4958ed74061dd04ff5d",
    "rc5-synthetic-final-success": "6858b3aa87d133664aa3667e570f5ad3a7105920",
    "rc6-r6-synthetic-final": "670f818ae0ff0efbfb8ab95d206163eba6883252",
}
_REGRESSION_MANIFEST = "EVIDENCE_MANIFEST.sha256"
_REGRESSION_BINDING = "WEAVER_FORGE_FINAL_BINDING.txt"


def _regression_git(*args: str, data: bytes | None = None) -> bytes:
    assert args[0] in {"rev-parse", "ls-tree", "cat-file"}
    return subprocess.run(
        ["git", "--no-optional-locks", "-C", str(Path(SCRIPTS).parents[3]), *args],
        input=data, capture_output=True, check=True, timeout=30,
    ).stdout


def _regression_snapshot(tree: Path) -> dict[str, bytes]:
    assert not any(p.is_symlink() for p in tree.rglob("*"))
    return {p.relative_to(tree).as_posix(): p.read_bytes()
            for p in tree.rglob("*") if p.is_file()}


def _regression_hashes(files: dict[str, bytes]) -> dict:
    return {name: {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
            for name, raw in sorted(files.items())}


def _regression_record(name: str, record: dict) -> None:
    destination = os.environ.get("WF_STAGE2A_ORACLE_DIR")
    if destination:
        directory = Path(destination)
        assert directory.is_dir() and not directory.is_symlink()
        with (directory / (name + ".json")).open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(record, handle, indent=2)
            handle.write("\n")


def _check_regression_manifest(tree: Path, payload: dict[str, bytes]) -> None:
    # Independent source-set/hashlib oracle, not inventory helper enumeration/hash.
    lines = [hashlib.sha256(payload[n]).hexdigest() + "  ./" + n for n in sorted(payload)]
    expected = ("\n".join(lines) + "\n").encode("ascii")
    assert (tree / _REGRESSION_MANIFEST).read_bytes() == expected


def _check_regression_binding(tree: Path, template: bytes) -> None:
    before = template.splitlines(keepends=True)
    after = (tree / _REGRESSION_BINDING).read_bytes().splitlines(keepends=True)
    assert len(before) == len(after)
    digest = hashlib.sha256((tree / _REGRESSION_MANIFEST).read_bytes()).hexdigest()
    count = 0
    for old, new in zip(before, after):
        if old.startswith(b"final_manifest_sha256="):
            count += 1
            assert new == b"final_manifest_sha256=" + digest.encode("ascii") + bytes([10])
        else:
            assert old == new
    assert count == 1


@contextmanager
def _pinned_regression_fixture(name: str, *, mode: str = "final-submission", mutable: bool = False):
    """Bounded Stage 2A acquisition; historical seals stay byte-identical.

    Current rc6-r6 uses the already verified payload -> Manifest -> Binding
    recipe. This does not generate/upgrade historical facts or source fixtures.
    """
    current = name == "rc6-r6-synthetic-final"
    oid = _REGRESSION_TREES[name]
    audit = {"recipe": "validator-regression-fixed-blob-v1", "fixture": name,
             "commit": _REGRESSION_COMMIT, "tree_oid": oid, "mode": mode,
             "schema": "rc6.5" if current else "rc6.1", "mutable_negative": mutable,
             "sources": {}, "construction_status": "INCOMPLETE"}
    with tempfile.TemporaryDirectory(prefix="validator_pinned_") as temporary:
        tree = Path(temporary)
        try:
            assert _regression_git("cat-file", "-t", _REGRESSION_COMMIT).strip() == b"commit"
            relative = "external_verifications/grok-build/witness-package/scripts/tests/fixtures/" + name
            assert _regression_git("rev-parse", _REGRESSION_COMMIT + ":" + relative).decode().strip() == oid
            entries = []
            folded = set()

            def checked_path(root: Path, relative: str, known: set) -> Path:
                # Keep Git's exact POSIX spelling: reject, never repair, unsafe input.
                parts = relative.split("/")
                assert all(re.fullmatch(r"[A-Za-z0-9_.-]+", part)
                           and part not in {"", ".", ".."} for part in parts), repr(relative)
                for part in parts:
                    assert part == part.rstrip(" .") and part.casefold() != ".git", repr(relative)
                    assert part.split(".", 1)[0].upper() not in {
                        "CON", "PRN", "AUX", "NUL", *["COM" + str(i) for i in range(1, 10)],
                        *["LPT" + str(i) for i in range(1, 10)],
                    }, repr(relative)
                assert root.is_dir() and not root.is_symlink()
                assert not getattr(root, "is_junction", lambda: False)()
                destination = root.joinpath(*parts)
                assert destination.relative_to(root).as_posix() == relative, repr(relative)
                cursor_path = root
                for index, part in enumerate(parts):
                    cursor_path = cursor_path / part
                    assert not cursor_path.is_symlink(), repr(relative)
                    assert not getattr(cursor_path, "is_junction", lambda: False)(), repr(relative)
                    if index < len(parts) - 1 and cursor_path.exists():
                        assert cursor_path.is_dir(), repr(relative)
                assert destination.resolve().is_relative_to(root.resolve()), repr(relative)
                assert not destination.exists(), repr(relative)
                # Track every prefix, not only leaves, for file/dir and case aliases.
                pending = set()
                for index in range(len(parts)):
                    prefix = "/".join(parts[:index + 1])
                    kind = "file" if index == len(parts) - 1 else "dir"
                    for prior, prior_kind in known:
                        if prior.casefold() == prefix.casefold():
                            assert prior == prefix and prior_kind == kind == "dir", repr(relative)
                    pending.add((prefix, kind))
                known.update(pending)
                return destination

            for item in _regression_git("ls-tree", "-r", "-z", oid).split(bytes([0])):
                if not item:
                    continue
                meta, raw_path = item.split(bytes([9]), 1)
                permissions, kind, blob = meta.split()
                assert (permissions, kind) == (b"100644", b"blob")
                path = raw_path.decode("ascii")
                checked_path(tree, path, folded)
                entries.append((path, blob.decode("ascii")))
            request = ("\n".join(blob for _, blob in entries) + "\n").encode("ascii")
            stream = _regression_git("cat-file", "--batch", data=request)
            cursor = 0
            source = {}
            for path, blob in entries:
                end = stream.index(bytes([10]), cursor)
                header = stream[cursor:end].split()
                assert header[0].decode("ascii") == blob and header[1] == b"blob"
                size = int(header[2])
                raw = stream[end + 1:end + 1 + size]
                assert stream[end + 1 + size:end + 2 + size] == bytes([10])
                cursor = end + 2 + size
                git_header = b"blob " + str(size).encode("ascii") + bytes([0])
                assert hashlib.sha1(git_header + raw).hexdigest() == blob
                source[path] = raw
                audit["sources"][path] = {"blob_oid": blob, **_regression_hashes({path: raw})[path]}
            assert cursor == len(stream)
            assert len(source) == (30 if current else 23 if name == "rc5-preliminary-success"
                                   else 26 if name == "rc5-synthetic-final-success" else 25)
            excluded = {_REGRESSION_MANIFEST, _REGRESSION_BINDING} if current else {_REGRESSION_MANIFEST}
            payload = {n: raw for n, raw in source.items() if n not in excluded}
            for n in ("BOOTSTRAP.txt", "STATIC_ARTIFACT_INSPECTION.txt"):
                assert bytes([13]) not in payload[n]
            for n, raw in source.items():
                if current and n in excluded:
                    continue
                destination = checked_path(tree, n, set())
                destination.parent.mkdir(parents=True, exist_ok=True)
                # Recheck resolved containment/links after parent creation, before xb.
                destination = checked_path(tree, n, set())
                with destination.open("xb") as handle:
                    handle.write(raw)
            if current:
                import evidence_inventory as ei
                from schema_register_loader import load_active_register

                assert v.SCHEMA_REGISTER_VERSION == "rc6.5"
                schema_oid = "3db5051448b667d7c40e02f1813da9f622829314"
                assert _regression_git("rev-parse", _REGRESSION_COMMIT + ":external_verifications/grok-build/witness-package/schemas/canonical_schema_register_rc6.json").decode().strip() == schema_oid
                assert hashlib.sha256(payload["DEVIATIONS.txt"]).hexdigest() == "dd293b6e000cdbcbc3ba9f2d23f9f2f3b3dd60b55283b48adc1e78139ffaca03"
                ei.write_evidence_manifest(tree, nested_classes=load_active_register().nested_class_records())
                digest = hashlib.sha256((tree / _REGRESSION_MANIFEST).read_bytes()).hexdigest()
                binding, count = re.subn(
                    b"^final_manifest_sha256=[0-9a-f]{64}$",
                    b"final_manifest_sha256=" + digest.encode("ascii"),
                    source[_REGRESSION_BINDING], flags=re.MULTILINE,
                )
                assert count == 1
                with (tree / _REGRESSION_BINDING).open("xb") as handle:
                    handle.write(binding)
                _check_regression_binding(tree, source[_REGRESSION_BINDING])
                audit["schema_blob_oid"] = schema_oid
            else:
                assert (tree / _REGRESSION_MANIFEST).read_bytes() == source[_REGRESSION_MANIFEST]
                audit["original_manifest_unchanged"] = True
            _check_regression_manifest(tree, payload)
            sealed = _regression_snapshot(tree)
            assert set(sealed) == set(source)
            for n, raw in payload.items():
                assert sealed[n] == raw == source[n]
            audit["sealed_files"] = _regression_hashes(sealed)
            audit["independent_source_set_raw_hash_payload_and_seal_checks"] = True
            audit["construction_status"] = "PASS"
            before_times = {n: (tree / n).stat().st_mtime_ns for n in sealed}
            yield tree
            if not mutable:
                assert _regression_snapshot(tree) == sealed, "consumer changed input bytes"
                assert {n: (tree / n).stat().st_mtime_ns for n in sealed} == before_times
                audit["consumer_no_write"] = True
        except BaseException as exc:
            audit["context_error"] = repr(exc)
            raise
        finally:
            audit["files_at_exit"] = _regression_hashes(_regression_snapshot(tree))
            _regression_record("regression-fixture-" + tree.name, audit)


def _record_tag_causality(base: dict[str, bytes], tree: Path, filename: str,
                          old: bytes, new: bytes, errors: list[str], allowed: tuple[str, ...]) -> None:
    audit = {"fixture": tree.name, "mutated_file": filename,
             "old_field": old.decode().strip(), "new_field": new.decode().strip(),
             "positive_accepted": True, "errors": errors, "allowed_diagnostics": allowed,
             "status": "INCOMPLETE"}
    try:
        expected = dict(base)
        assert expected[filename].count(old) == 1
        expected[filename] = expected[filename].replace(old, new, 1)
        actual = _regression_snapshot(tree)
        assert set(actual) == set(base)
        for n in base:
            if n not in {_REGRESSION_MANIFEST, _REGRESSION_BINDING}:
                assert actual[n] == expected[n], n
        payload = {n: raw for n, raw in expected.items()
                   if n not in {_REGRESSION_MANIFEST, _REGRESSION_BINDING}}
        _check_regression_manifest(tree, payload)
        _check_regression_binding(tree, expected[_REGRESSION_BINDING])
        # Only these two single-tag mutations have this six-diagnostic contract.
        rc8 = "grok-build-witness-v1.0.0-rc8"
        cross_reason = (
            "cross-file package identity tag mismatch among "
            "weaver_forge_tag_requested / package_tag / canonical_tag"
        )
        cases = {
            (_REGRESSION_BINDING,
             b"canonical_tag=grok-build-witness-v1.0.0-rc8\n",
             b"canonical_tag=grok-build-witness-v1.0.0-rc5\n"): (
                "WEAVER_FORGE_FINAL_BINDING.txt: canonical_tag != expected tag for "
                "package_version='1.0.0-rc8' (expected grok-build-witness-v1.0.0-rc8)",
                (rc8, rc8, "grok-build-witness-v1.0.0-rc5"),
                [
                    "WITNESS_VERDICT.md: package_tag must equal WEAVER_FORGE_FINAL_BINDING.txt canonical_tag",
                    "WEAVER_FORGE_FINAL_BINDING.txt: canonical_tag must equal WEAVER_FORGE_PACKAGE_IDENTITY.txt weaver_forge_tag_requested",
                    "WEAVER_FORGE_FINAL_BINDING.txt: canonical_tag must equal expected tag for package_version='1.0.0-rc8' (expected grok-build-witness-v1.0.0-rc8, found 'grok-build-witness-v1.0.0-rc5')",
                ],
            ),
            ("WITNESS_VERDICT.md",
             b"package_tag=grok-build-witness-v1.0.0-rc8\n",
             b"package_tag=grok-build-witness-v1.0.0-rc4\n"): (
                "WITNESS_VERDICT.md: package_tag != expected tag for "
                "package_version='1.0.0-rc8' (expected grok-build-witness-v1.0.0-rc8)",
                (rc8, "grok-build-witness-v1.0.0-rc4", rc8),
                [
                    "WITNESS_VERDICT.md: package_tag must equal expected tag for package_version='1.0.0-rc8' (expected grok-build-witness-v1.0.0-rc8, found 'grok-build-witness-v1.0.0-rc4')",
                    "WITNESS_VERDICT.md: package_tag must equal WEAVER_FORGE_PACKAGE_IDENTITY.txt weaver_forge_tag_requested",
                    "WITNESS_VERDICT.md: package_tag must equal WEAVER_FORGE_FINAL_BINDING.txt canonical_tag",
                ],
            ),
        }
        assert (filename, old, new) in cases, "unapproved tag mutation"
        identity_reason, expected_tags, tag_errors = cases[(filename, old, new)]

        def causal_fields(files: dict[str, bytes]) -> dict[str, dict[str, str]]:
            # Independent simple key extraction from the already byte-checked peers.
            peers = (
                "WEAVER_FORGE_PACKAGE_IDENTITY.txt", "WITNESS_VERDICT.md", _REGRESSION_BINDING,
                "SOURCE_IDENTITY.txt", "IMAGE_IDENTITY.txt", "POST_BUILD_INTEGRITY.txt",
                "WITNESS_STATEMENT.md", "BUILD_EXIT_CODE.txt", "STATIC_ARTIFACT_INSPECTION.txt",
                "DEVIATIONS.txt",
            )
            result = {}
            for peer in peers:
                pairs = re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$",
                                   files[peer].decode("utf-8"), flags=re.MULTILINE)
                assert len({key for key, _ in pairs}) == len(pairs), peer
                result[peer] = dict(pairs)
            return result

        before_fields, after_fields = causal_fields(base), causal_fields(actual)
        for fields in (before_fields, after_fields):
            assert fields["WEAVER_FORGE_PACKAGE_IDENTITY.txt"]["package_version"] == "1.0.0-rc8"
            for peer in ("WITNESS_STATEMENT.md", "WITNESS_VERDICT.md", "DEVIATIONS.txt"):
                assert fields[peer]["final_machine_ceiling"] == "PASS", peer
            assert fields["WITNESS_VERDICT.md"]["verdict_ceiling"] == "PASS"
            assert fields["BUILD_EXIT_CODE.txt"]["outcome"] == "CARGO_SUCCEEDED_ARTIFACT_PRESENT"
            assert fields["STATIC_ARTIFACT_INSPECTION.txt"]["inspection_complete"] == "yes"
            assert not v.detect_prohibited_violation(fields)
        for files in (base, actual):
            assert files["WITNESS_VERDICT.md"].count(b"Witness proposed verdict: PASS\n") == 1

        def tags(fields: dict[str, dict[str, str]]) -> tuple[str, str, str]:
            return (fields["WEAVER_FORGE_PACKAGE_IDENTITY.txt"]["weaver_forge_tag_requested"],
                    fields["WITNESS_VERDICT.md"]["package_tag"],
                    fields[_REGRESSION_BINDING]["canonical_tag"])

        assert tags(before_fields) == (rc8, rc8, rc8)
        assert tags(after_fields) == expected_tags
        before_reasons = v.detect_identity_mismatch(before_fields)
        after_reasons = v.detect_identity_mismatch(after_fields)
        assert before_reasons == []
        assert sorted(after_reasons) == sorted([identity_reason, cross_reason]), after_reasons
        ceilings = []
        for fields, reasons in ((before_fields, before_reasons), (after_fields, after_reasons)):
            ceilings.append(v.compute_verdict_ceiling(
                fields["BUILD_EXIT_CODE.txt"]["outcome"],
                bool(v.detect_prohibited_violation(fields)), bool(reasons),
                fields["STATIC_ARTIFACT_INSPECTION.txt"]["inspection_complete"] != "yes",
                deviation_final_ceiling=fields["DEVIATIONS.txt"]["final_machine_ceiling"],
            ))
        assert ceilings == ["PASS", "FAIL"], ceilings
        ceiling_errors = [
            "WITNESS_STATEMENT.md: final_machine_ceiling must equal validator-authoritative recomputed ceiling 'FAIL' (found 'PASS')",
            "WITNESS_VERDICT.md: proposed verdict PASS exceeds the machine-computed verdict ceiling FAIL for this run's evidence — a verdict may never be recorded above its ceiling",
            "WITNESS_VERDICT.md: final_machine_ceiling must equal validator-authoritative recomputed ceiling 'FAIL' (found 'PASS')",
        ]
        assert all(any(token in error for token in allowed) for error in tag_errors)
        expected_errors = tag_errors + ceiling_errors
        # Sorted-list equality is multiset equality: duplicates/omissions/extras fail.
        assert len(errors) == 6 and sorted(errors) == sorted(expected_errors), errors
        audit.update({"status": "PASS", "only_intended_payload_or_binding_field_plus_seal_changed": True,
                      "unrelated_errors_absent": True, "negative_files": _regression_hashes(actual),
                      "identity_reasons_before": before_reasons, "identity_reasons_after": after_reasons,
                      "machine_ceilings": ceilings, "recorded_PASS_values_unchanged": True,
                      "expected_diagnostic_multiset": expected_errors, "exact_multiset_matched": True})
    finally:
        _regression_record("regression-causality-" + tree.name, audit)


# ---------------------------------------------------------------------------
# Shell schema-block extraction helpers
# ---------------------------------------------------------------------------

_KEY_RE = re.compile(r'echo\s+"([A-Za-z_][A-Za-z0-9_]*)=')
_BARE_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=")


def schema_block_keys(text: str, name: str) -> set[str]:
    """Union of all `key=` names inside every
    `BEGIN_SCHEMA_BLOCK <name> ... END_SCHEMA_BLOCK` region.

    Supports both host ``echo "key=..."`` writers and container heredoc
    ``key=${var}`` schema blocks.
    """
    start_re = re.compile(r"BEGIN_SCHEMA_BLOCK\s+" + re.escape(name) + r"\b")
    keys: set[str] = set()
    inside = False
    for line in text.splitlines():
        if "END_SCHEMA_BLOCK" in line:
            inside = False
            continue
        if start_re.search(line):
            inside = True
            continue
        if inside:
            m = _KEY_RE.search(line)
            if m:
                keys.add(m.group(1))
                continue
            m = _BARE_KEY_RE.match(line.strip())
            if m:
                keys.add(m.group(1))
    return keys


def writer_block_keys(text: str, filename: str) -> set[str]:
    """Keys echoed in host writer blocks for ``filename``.

    Supports both classic ``{ ... } > "${EVIDENCE_DIR}/<filename>"`` redirects and
    RC6 atomic writers of the form ``{ ... } | write_evidence_file_atomic "${dest}"``
    where ``dest`` is assigned to the target filename in the surrounding function.
    """
    lines = text.splitlines()
    redirect_re = re.compile(r"\}\s*>\s*\"?\$\{EVIDENCE_DIR\}/" + re.escape(filename))
    atomic_re = re.compile(r"\}\s*\|\s*write_evidence_file_atomic\s+\"\$\{dest\}\"")
    best: set[str] = set()
    for idx, line in enumerate(lines):
        is_redirect = bool(redirect_re.search(line))
        is_atomic = bool(atomic_re.search(line))
        if not is_redirect and not is_atomic:
            continue
        if is_atomic:
            window = "\n".join(lines[max(0, idx - 120) : idx])
            if filename not in window:
                continue
        keys: set[str] = set()
        j = idx - 1
        while j >= 0:
            m = _KEY_RE.search(lines[j])
            if m:
                keys.add(m.group(1))
            if lines[j].strip() in ("{", "if ! {"):
                break
            j -= 1
        if len(keys) > len(best):
            best = keys
    return best


# ---------------------------------------------------------------------------
# Tree helpers
# ---------------------------------------------------------------------------


def _mktree(scenario: str, overrides: "dict[str, str] | None" = None) -> Path:
    files = fx.build_scenario(scenario)
    if overrides:
        for k, val in overrides.items():
            if val is None:
                files.pop(k, None)
            else:
                files[k] = val
    tmp = Path(tempfile.mkdtemp())
    fx.write_tree(tmp, files)
    return tmp


def _witness_verdict(outcome: str, ceiling: str, proposed: str) -> str:
    return (
        "evidence_schema_version=1\n"
        "run_id=run-2026-07-22-001\n"
        f"package_tag={fx.TAG}\n"
        f"weaver_forge_commit={fx.WEAVER}\n"
        f"grok_build_commit={fx.GROK}\n"
        f"outcome={outcome}\n"
        f"verdict_ceiling={ceiling}\n"
        "product_executed=NO\n"
        "ldd_used=NO\n"
        "maintainer_intake_verdict=pending\n"
        f"\nWitness proposed verdict: {proposed}\n"
    )


# ---------------------------------------------------------------------------
# Contract tests (validator schema <-> shell script schema blocks)
# ---------------------------------------------------------------------------


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = HOST_SCRIPT.read_text(encoding="utf-8")
        cls.container = CONTAINER_SCRIPT.read_text(encoding="utf-8")

    def test_container_generated_clean_target_keys_match_schema(self):
        self.assertEqual(
            schema_block_keys(self.container, "CLEAN_TARGET"),
            set(v.FILE_REQUIRED_FIELDS["CLEAN_TARGET_PROOF.txt"]),
        )

    def test_container_generated_build_environment_keys_match_schema(self):
        self.assertEqual(
            schema_block_keys(self.container, "BUILD_ENVIRONMENT"),
            set(v.FILE_REQUIRED_FIELDS["BUILD_ENVIRONMENT.txt"]),
        )

    def test_container_generated_timing_keys_match_schema(self):
        self.assertEqual(
            schema_block_keys(self.container, "BUILD_TIMING"),
            set(v.FILE_REQUIRED_FIELDS["BUILD_TIMING.txt"]),
        )

    def test_container_generated_build_exit_code_keys_match_schema(self):
        self.assertEqual(
            schema_block_keys(self.container, "BUILD_EXIT_CODE"),
            set(v.FILE_REQUIRED_FIELDS["BUILD_EXIT_CODE.txt"]),
        )

    def test_container_generated_static_inspection_keys_match_schema(self):
        # The validator splits STATIC's schema between FILE_REQUIRED_FIELDS
        # (always non-empty) and STATIC_ARTIFACT_INSPECTION_ALWAYS_PRESENT_KEYS
        # (present but legitimately empty when applicable=no). Their union is
        # the full container schema block.
        validator_keys = set(v.FILE_REQUIRED_FIELDS["STATIC_ARTIFACT_INSPECTION.txt"]) | set(
            v.STATIC_ARTIFACT_INSPECTION_ALWAYS_PRESENT_KEYS
        )
        self.assertEqual(
            schema_block_keys(self.container, "STATIC_ARTIFACT_INSPECTION"),
            validator_keys,
        )

    def test_host_generated_image_identity_keys_match_schema(self):
        self.assertEqual(
            schema_block_keys(self.host, "IMAGE_IDENTITY"),
            set(v.FILE_REQUIRED_FIELDS["IMAGE_IDENTITY.txt"]),
        )

    def test_host_generated_environment_keys_match_schema(self):
        # ENVIRONMENT is dual-owned: host writes one block, the container
        # appends a second. The union must exactly cover the required set.
        union = schema_block_keys(self.host, "ENVIRONMENT") | schema_block_keys(
            self.container, "ENVIRONMENT"
        )
        self.assertEqual(union, set(v.FILE_REQUIRED_FIELDS["ENVIRONMENT.txt"]))

    def test_host_generated_post_build_integrity_keys_match_schema(self):
        emitted = writer_block_keys(self.host, "POST_BUILD_INTEGRITY.txt")
        required = set(v.FILE_REQUIRED_FIELDS["POST_BUILD_INTEGRITY.txt"])
        # Phase 3E: exact equality (not one-way required-subset inclusion).
        self.assertEqual(emitted, required, f"host writer keys {emitted} != schema {required}")

    def test_image_identity_uses_rc4_key_names(self):
        keys = schema_block_keys(self.host, "IMAGE_IDENTITY")
        self.assertIn("inspect_image_id_command", keys)
        self.assertNotIn("inspect_id_command", keys)
        self.assertIn("inspect_repo_digests_command", keys)
        self.assertNotIn("inspect_repodigests_command", keys)


# ---------------------------------------------------------------------------
# parse_kv / duplicate-key tests
# ---------------------------------------------------------------------------


class ParseKvTests(unittest.TestCase):
    def test_duplicate_key_same_value_rejected(self):
        fields, errors = v.parse_kv("a=1\na=1\n", "F")
        self.assertEqual(fields.get("a"), "1")
        self.assertTrue(any("duplicate key 'a'" in e for e in errors))

    def test_duplicate_key_conflicting_value_rejected(self):
        fields, errors = v.parse_kv("a=1\na=2\n", "F")
        self.assertTrue(any("duplicate key 'a'" in e for e in errors))
        self.assertTrue(any("conflicting" in e for e in errors))

    def test_no_last_value_wins(self):
        fields, _ = v.parse_kv("a=1\na=2\n", "F")
        self.assertEqual(fields.get("a"), "1")

    def test_duplicate_key_in_evidence_file_fails_validation(self):
        # Append a duplicate cargo_incremental line to BUILD_COMMAND.txt.
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_COMMAND.txt"] = files["BUILD_COMMAND.txt"] + "cargo_incremental=0\n"
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("duplicate key 'cargo_incremental'" in e for e in errors), errors)


# ---------------------------------------------------------------------------
# Golden fixtures
# ---------------------------------------------------------------------------


class GoldenFixtureTests(unittest.TestCase):
    def test_all_committed_fixtures_pass(self):
        for scenario in fx.ALL_SCENARIOS:
            with self.subTest(scenario=scenario):
                with _pinned_regression_fixture(scenario) as d:
                    self.assertTrue(d.is_dir(), f"missing committed fixture: {d}")
                    errors = v.validate_dir(d, schema_register_version="rc6.1")
                    self.assertEqual(errors, [], f"{scenario}: {errors}")

    def test_all_scenarios_build_and_pass(self):
        for scenario in fx.ALL_SCENARIOS:
            with self.subTest(scenario=scenario):
                tmp = _mktree(scenario)
                errors = v.validate_dir(tmp, schema_register_version="rc6.1")
                self.assertEqual(errors, [], f"{scenario}: {errors}")

    def test_main_entrypoint_returns_zero_on_success_fixture(self):
        with _pinned_regression_fixture("success-artifact-present") as tree:
            rc = v.main(
                [
                    str(tree),
                    "--schema-register-version",
                    "rc6.1",
                ]
            )
            self.assertEqual(rc, 0)


# ---------------------------------------------------------------------------
# Outcome consistency
# ---------------------------------------------------------------------------


class OutcomeConsistencyTests(unittest.TestCase):
    def test_docker_outcome_disagreement_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["DOCKER_EXIT_CODE.txt"] = files["DOCKER_EXIT_CODE.txt"].replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=CARGO_FAILED"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("DOCKER_EXIT_CODE.txt: outcome" in e for e in errors), errors)

    def test_timing_outcome_disagreement_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_TIMING.txt"] = files["BUILD_TIMING.txt"].replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=BUILD_NOT_STARTED"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("BUILD_TIMING.txt: outcome" in e for e in errors), errors)

    def test_missing_outcome_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_EXIT_CODE.txt"] = "\n".join(
            l for l in files["BUILD_EXIT_CODE.txt"].splitlines() if not l.startswith("outcome=")
        ) + "\n"
        # Phase 3F-A: secondary cargo_started/build_status must not produce an
        # outcome when explicit outcome= is absent (inference removed).
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("explicit 'outcome'" in e or "outcome" in e.lower() for e in errors), errors)
        self.assertTrue(
            any("inference" in e.lower() or "explicit" in e.lower() for e in errors),
            errors,
        )

    def test_invalid_outcome_value_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_EXIT_CODE.txt"] = files["BUILD_EXIT_CODE.txt"].replace(
            "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT", "outcome=BANANA"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(errors)

    def test_duplicate_outcome_line_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["BUILD_EXIT_CODE.txt"] = (
            files["BUILD_EXIT_CODE.txt"] + "outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT\n"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("duplicate key 'outcome'" in e for e in errors), errors)

    def test_witness_verdict_outcome_mismatch_fails(self):
        files = fx.build_scenario("success-artifact-present")
        files["WITNESS_VERDICT.md"] = _witness_verdict(
            "CARGO_FAILED", "FAIL", "FAIL"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("WITNESS_VERDICT.md: outcome" in e for e in errors), errors)


# ---------------------------------------------------------------------------
# Verdict ceiling
# ---------------------------------------------------------------------------


class VerdictCeilingTests(unittest.TestCase):
    def test_compute_ceiling_success(self):
        self.assertEqual(
            v.compute_verdict_ceiling("CARGO_SUCCEEDED_ARTIFACT_PRESENT", False, False, False),
            "PASS",
        )

    def test_compute_ceiling_static_incomplete_partial(self):
        self.assertEqual(
            v.compute_verdict_ceiling("CARGO_SUCCEEDED_ARTIFACT_PRESENT", False, False, True),
            "PARTIAL",
        )

    def test_compute_ceiling_cargo_failed_fail(self):
        self.assertEqual(v.compute_verdict_ceiling("CARGO_FAILED", False, False, False), "FAIL")

    def test_compute_ceiling_missing_artifact_fail(self):
        self.assertEqual(
            v.compute_verdict_ceiling("CARGO_SUCCEEDED_ARTIFACT_MISSING", False, False, False),
            "FAIL",
        )

    def test_compute_ceiling_not_started_indeterminate(self):
        self.assertEqual(
            v.compute_verdict_ceiling("BUILD_NOT_STARTED", False, False, False), "INDETERMINATE"
        )
        self.assertEqual(
            v.compute_verdict_ceiling("INFRASTRUCTURE_FAILURE", False, False, False),
            "INDETERMINATE",
        )

    def test_compute_ceiling_prohibited_fail(self):
        self.assertEqual(
            v.compute_verdict_ceiling("CARGO_SUCCEEDED_ARTIFACT_PRESENT", True, False, False),
            "FAIL",
        )

    def test_compute_ceiling_identity_mismatch_fail(self):
        self.assertEqual(
            v.compute_verdict_ceiling("CARGO_SUCCEEDED_ARTIFACT_PRESENT", False, True, False),
            "FAIL",
        )

    def test_proposed_verdict_above_ceiling_rejected(self):
        # static-inspection-incomplete has ceiling PARTIAL; proposing PASS fails.
        files = fx.build_scenario("static-inspection-incomplete")
        files["WITNESS_VERDICT.md"] = _witness_verdict(
            "CARGO_SUCCEEDED_ARTIFACT_PRESENT", "PASS", "PASS"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("exceeds the machine-computed verdict" in e for e in errors), errors)

    def test_proposed_pass_on_cargo_failed_rejected(self):
        files = fx.build_scenario("cargo-failed")
        files["WITNESS_VERDICT.md"] = _witness_verdict("CARGO_FAILED", "PASS", "PASS")
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("exceeds" in e for e in errors), errors)


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class ManifestTests(unittest.TestCase):
    def _tree(self, scenario="success-artifact-present"):
        tmp = _mktree(scenario)
        return tmp

    def test_single_space_manifest_line_rejected(self):
        tmp = self._tree()
        mpath = tmp / v.MANIFEST_NAME
        text = mpath.read_text(encoding="utf-8")
        # collapse the mandatory two-space separator to one on the first line.
        first, _, rest = text.partition("\n")
        first_bad = first.replace("  ./", " ./", 1)
        mpath.write_text(first_bad + "\n" + rest, encoding="utf-8")
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("malformed line" in e for e in errors), errors)

    def test_hash_mismatch_rejected(self):
        tmp = self._tree()
        (tmp / "DEVIATIONS.txt").write_text(
            "evidence_schema_version=1\ndeviation_state=NONE\n# tampered\n", encoding="utf-8"
        )
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("hash mismatch" in e for e in errors), errors)

    def test_missing_manifest_entry_rejected(self):
        tmp = self._tree()
        mpath = tmp / v.MANIFEST_NAME
        lines = [l for l in mpath.read_text(encoding="utf-8").splitlines() if "DEVIATIONS.txt" not in l]
        mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("missing mandatory entry for DEVIATIONS.txt" in e for e in errors), errors)

    def test_prohibited_aux_file_rejected(self):
        tmp = self._tree()
        (tmp / "BOOTSTRAP_PROTOC_VERSION.txt").write_text("libprotoc 29.3\n", encoding="utf-8")
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(
            any("BOOTSTRAP_PROTOC_VERSION.txt must never appear" in e for e in errors), errors
        )

    def test_undeclared_aux_in_manifest_rejected(self):
        tmp = self._tree()
        extra = tmp / "SOMETHING_ELSE.txt"
        extra.write_text("hello\n", encoding="utf-8")
        digest = v.sha256_file(extra)
        mpath = tmp / v.MANIFEST_NAME
        mpath.write_text(
            mpath.read_text(encoding="utf-8") + f"{digest}  ./SOMETHING_ELSE.txt\n", encoding="utf-8"
        )
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("outside the closed" in e for e in errors), errors)

    def test_allowed_aux_file_accepted(self):
        tmp = self._tree()
        (tmp / "HOST_RUN_METADATA.txt").write_text("run metadata\n", encoding="utf-8")
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)


# ---------------------------------------------------------------------------
# Redactions
# ---------------------------------------------------------------------------


class RedactionTests(unittest.TestCase):
    def test_unlogged_redaction_marker_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["ARTIFACT_IDENTITY.txt"] = files["ARTIFACT_IDENTITY.txt"].replace(
            "gnu_build_id=abcdef0123456789", "gnu_build_id=[REDACTED: build id]"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("[REDACTED" in e for e in errors), errors)

    def test_prohibited_category_redaction_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["REDACTIONS.md"] = (
            "evidence_schema_version=1\n"
            "redaction_state=PRESENT\n"
            "semantic_integrity_declaration=yes\n"
            "redaction_1_file=ARTIFACT_IDENTITY.txt\n"
            "redaction_1_field=artifact_sha256\n"
            "redaction_1_reason=privacy\n"
            "redaction_1_replacement_marker=[REDACTED: sha]\n"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("prohibited category" in e for e in errors), errors)

    def test_valid_present_redaction_accepted(self):
        files = fx.build_scenario("success-artifact-present")
        files["ENVIRONMENT.txt"] = files["ENVIRONMENT.txt"].replace(
            "host_cpu=AMD Ryzen 9 7950X 16-Core Processor",
            "host_cpu=[REDACTED: cpu model]",
        )
        files["REDACTIONS.md"] = (
            "evidence_schema_version=1\n"
            "redaction_state=PRESENT\n"
            "semantic_integrity_declaration=yes\n"
            "redaction_1_file=ENVIRONMENT.txt\n"
            "redaction_1_field=host_cpu\n"
            "redaction_1_reason=host hardware privacy\n"
            "redaction_1_replacement_marker=[REDACTED: cpu model]\n"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertEqual(errors, [], errors)


# ---------------------------------------------------------------------------
# upstream_product_commands_not_run
# ---------------------------------------------------------------------------


class UpstreamProductCommandsTests(unittest.TestCase):
    def test_statement_upstream_not_yes_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["WITNESS_STATEMENT.md"] = files["WITNESS_STATEMENT.md"].replace(
            "upstream_product_commands_not_run=yes", "upstream_product_commands_not_run=no"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(
            any("upstream_product_commands_not_run must be yes" in e for e in errors), errors
        )

    def test_environment_upstream_not_yes_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["ENVIRONMENT.txt"] = files["ENVIRONMENT.txt"].replace(
            "upstream_product_commands_not_run=yes", "upstream_product_commands_not_run=no"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(
            any("upstream_product_commands_not_run must be yes" in e for e in errors), errors
        )

    def test_statement_upstream_no_flags_ceiling_fail(self):
        # upstream=no on the statement drives the machine ceiling to FAIL, so a
        # proposed PASS is rejected.
        files = fx.build_scenario("success-artifact-present")
        files["WITNESS_STATEMENT.md"] = files["WITNESS_STATEMENT.md"].replace(
            "upstream_product_commands_not_run=yes", "upstream_product_commands_not_run=no"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("exceeds" in e for e in errors), errors)


# ---------------------------------------------------------------------------
# product_executed / ldd enforcement
# ---------------------------------------------------------------------------


class ProductLddTests(unittest.TestCase):
    def test_product_executed_yes_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["ARTIFACT_IDENTITY.txt"] = files["ARTIFACT_IDENTITY.txt"].replace(
            "product_executed=NO", "product_executed=YES"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(errors)

    def test_ldd_used_yes_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["DOCKER_EXIT_CODE.txt"] = files["DOCKER_EXIT_CODE.txt"].replace(
            "ldd_used=NO", "ldd_used=YES"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(errors)


# ---------------------------------------------------------------------------
# Missing-file / structural
# ---------------------------------------------------------------------------


class StructuralTests(unittest.TestCase):
    def test_missing_required_file_rejected(self):
        tmp = _mktree("success-artifact-present")
        (tmp / "SOURCE_IDENTITY.txt").unlink()
        # keep manifest consistent so we exercise the required-file check
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("SOURCE_IDENTITY.txt" in e for e in errors), errors)

    def test_cargo_exit_code_na_alias_rejected(self):
        files = fx.build_scenario("build-not-started")
        files["BUILD_EXIT_CODE.txt"] = files["BUILD_EXIT_CODE.txt"].replace(
            "cargo_exit_code=NOT_APPLICABLE", "cargo_exit_code=N/A"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(any("cargo_exit_code" in e for e in errors), errors)


# ---------------------------------------------------------------------------
# Host-safety static assertions (read from the shell scripts, never executed)
# ---------------------------------------------------------------------------


class HostSafetyStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = HOST_SCRIPT.read_text(encoding="utf-8")
        cls.container = CONTAINER_SCRIPT.read_text(encoding="utf-8")

    def test_strict_bash_mode(self):
        self.assertIn("set -Eeuo pipefail", self.host)

    def test_canonical_constants_present_and_readonly(self):
        self.assertIn('readonly PACKAGE_VERSION="1.0.0-rc8"', self.host)
        self.assertIn('readonly CANONICAL_WEAVER_FORGE_TAG="grok-build-witness-v1.0.0-rc8"', self.host)
        self.assertIn(f'readonly CANONICAL_GROK_BUILD_COMMIT="{fx.GROK}"', self.host)
        self.assertIn(f'readonly CANONICAL_CARGO_LOCK_SHA256="{fx.LOCK}"', self.host)
        self.assertIn(f'readonly CANONICAL_BUILD_CMD="{fx.BUILD_CMD}"', self.host)
        self.assertIn(fx.IMG, self.host)

    def test_constants_self_check_present(self):
        self.assertIn("CANONICAL_IMAGE_DIGEST is not embedded in CANONICAL_RUST_IMAGE", self.host)

    def test_override_requires_noncanonical_flag(self):
        self.assertIn("overridden without --noncanonical-deviation", self.host)

    def test_noncanonical_pass_prohibition_and_url_fail_severity(self):
        self.assertIn("Witness proposed verdict PASS is PREVENTED", self.host)
        self.assertIn("WEAVER_FORGE_URL", self.host)
        self.assertIn('VERDICT_CEILING="FAIL"', self.host)
        self.assertIn("compute_verdict_ceiling", self.host)

    def test_work_root_guards_present(self):
        for needle in (
            "WORK_ROOT must not resolve to /",
            "WORK_ROOT must not be the package repository",
            "WORK_ROOT must be an absolute path",
            "WORK_ROOT must not resolve to the home directory",
            "WORK_ROOT must not resolve to a WSL drive-root mount",
            "WORK_ROOT must not resolve within a system prefix",
            "WORK_ROOT must not be an ancestor of the package repository",
            "WORK_ROOT must not be located inside the package repository",
        ):
            self.assertIn(needle, self.host, needle)

    def test_witness_id_validation_present(self):
        self.assertIn("validate_witness_id", self.host)
        self.assertIn("witness-id must not contain path separators", self.host)
        self.assertIn("witness-id must not contain '..'", self.host)
        self.assertIn("witness-id must not contain whitespace", self.host)

    def test_managed_child_symlink_policy_present(self):
        self.assertIn("safe_reset_managed_path", self.host)
        self.assertIn("NEVER followed", self.host)
        self.assertIn('[[ -L "${p}" ]]', self.host)
        self.assertIn('rm -f -- "${p}"', self.host)

    def test_missing_tag_and_tag_head_mismatch_finalizers_present(self):
        self.assertIn('finalize_pre_docker_infrastructure_failure "weaver_forge_tag_resolution"', self.host)
        self.assertIn('finalize_pre_docker_infrastructure_failure "weaver_forge_tag_head_mismatch"', self.host)

    def test_dirty_package_and_grok_clone_finalizers_present(self):
        self.assertIn('finalize_pre_docker_infrastructure_failure "weaver_forge_dirty_clone"', self.host)
        self.assertIn('finalize_pre_docker_infrastructure_failure "grok_build_dirty_clone"', self.host)

    def test_wrong_grok_commit_and_cargo_lock_finalizers_present(self):
        self.assertIn('finalize_pre_docker_infrastructure_failure "grok_build_commit_mismatch"', self.host)
        self.assertIn('finalize_pre_docker_infrastructure_failure "cargo_lock_pre_docker_mismatch"', self.host)
        self.assertIn("cargo_lock_post_matches_expected", self.host)
        self.assertIn("CARGO_LOCK_AFTER", self.host)

    def test_grok_detached_probe_present(self):
        self.assertIn('git -C "${SRC_DIR}" symbolic-ref -q HEAD', self.host)
        self.assertIn("grok_build_detached_head", self.host)
        self.assertIn('finalize_pre_docker_infrastructure_failure "grok_build_detached_head_check"', self.host)

    def test_host_preserves_container_outcome_authority(self):
        # Phase 3D: parse_container_result_tuple supersedes parse_container_outcome.
        self.assertIn("parse_container_result_tuple", self.host)
        self.assertIn("invalid_or_missing_container_outcome", self.host)
        self.assertIn("outcome_field_missing", self.host)
        self.assertIn("outcome_field_duplicated", self.host)
        self.assertIn("unsupported_outcome_", self.host)
        self.assertIn(
            "ordinary outcome from cargo_started/artifact-presence/raw Docker exit code alone",
            self.host,
        )

    def test_no_cached_image_fallback(self):
        self.assertIn("cached_image_fallback_used=NO", self.host)

    def test_image_pull_and_identity_failure_finalizers_present(self):
        self.assertIn('finalize_pre_docker_infrastructure_failure "image_pull"', self.host)
        self.assertIn('finalize_pre_docker_infrastructure_failure "image_identity_enforcement"', self.host)

    def test_no_embedded_future_rc4_commit(self):
        self.assertNotIn("PLACEHOLDER_UNTIL_RC4_TAGGED", self.host)
        self.assertNotIn("CANONICAL_WEAVER_FORGE_EXPECTED_COMMIT=", self.host)

    def test_container_uses_pipefail(self):
        self.assertIn("pipefail", self.container)


class DeviationCeilingTests(unittest.TestCase):
    def test_verdict_above_deviation_ceiling_rejected(self):
        files = fx.build_scenario("success-artifact-present")
        files["DEVIATIONS.txt"] = (
            "evidence_schema_version=1\n"
            "deviation_state=PRESENT\n"
            "deviation_1_description=noncanonical identity override accepted with flag\n"
            "deviation_1_severity=MATERIAL_NONCANONICAL\n"
            "deviation_1_canonical_identity_impact=yes\n"
            "deviation_1_verdict_ceiling=PARTIAL\n"
        )
        # Proposed PASS with recorded ceiling PARTIAL must fail (above deviation ceiling).
        # _witness_verdict(outcome, ceiling, proposed)
        files["WITNESS_VERDICT.md"] = _witness_verdict(
            "CARGO_SUCCEEDED_ARTIFACT_PRESENT", "PARTIAL", "PASS"
        )
        tmp = Path(tempfile.mkdtemp())
        fx.write_tree(tmp, files)
        errors = v.validate_dir(tmp, schema_register_version="rc6.1")
        self.assertTrue(
            any("exceeds the recorded verdict_ceiling" in e or "PARTIAL" in e for e in errors),
            errors,
        )


class Phase4S2CompatibilityNarrowTests(unittest.TestCase):
    """Narrow Phase 4-S2 compatibility / selection assertions only."""

    def test_active_register_loads_and_historical_fixtures_still_pass(self):
        import schema_register_loader as srl

        self.assertEqual(v.SCHEMA_REGISTER_VERSION, srl.ACTIVE_REGISTER_VERSION)
        self.assertEqual(v.SCHEMA_REGISTER_VERSION, "rc6.5")
        with _pinned_regression_fixture("success-artifact-present") as tree:
            errors = v.validate_dir(tree, schema_register_version="rc6.1")
            self.assertEqual(errors, [], errors)
        # Historical NOT_REACHED fixtures remain accepted via historical compatibility.
        with _pinned_regression_fixture("image-pull-failure") as tree:
            errors2 = v.validate_dir(tree, schema_register_version="rc6.1")
            self.assertEqual(errors2, [], errors2)

    def test_s2_shaped_package_identity_enforced_and_no_write(self):
        import schema_register_loader as srl
        import shutil

        tmp = Path(tempfile.mkdtemp(prefix="phase4_s2_val_", dir=HERE))
        try:
            files = fx.build_scenario("success-artifact-present")
            pkg = files["WEAVER_FORGE_PACKAGE_IDENTITY.txt"]
            pkg = pkg.replace(
                "weaver_forge_tag_requested=",
                "weaver_forge_tag_ref=refs/tags/grok-build-witness-v1.0.0-rc4\nweaver_forge_tag_requested=",
            )
            files["WEAVER_FORGE_PACKAGE_IDENTITY.txt"] = pkg
            fx.write_tree(tmp, files)
            before = {
                p.name: (p.stat().st_mtime_ns, p.read_bytes())
                for p in tmp.iterdir()
                if p.is_file()
            }
            errors = v.validate_dir(tmp, schema_register_version="rc6.1")
            after_names = {p.name for p in tmp.iterdir() if p.is_file()}
            self.assertEqual(after_names, set(before))
            for name, (mtime, data) in before.items():
                p = tmp / name
                self.assertEqual(p.read_bytes(), data)
                self.assertEqual(p.stat().st_mtime_ns, mtime)
            self.assertTrue(errors, "expected S2 exact-field rejection")
            self.assertTrue(
                any(
                    "weaver_forge_tag_raw_object_type" in e or "missing required field" in e
                    for e in errors
                ),
                errors,
            )
            self.assertTrue(srl.is_s2_shaped_package_identity(v.parse_kv(pkg, "x")[0]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_host_preliminary_mode_still_explicit(self):
        with _pinned_regression_fixture("success-artifact-present", mode=v.MODE_HOST_PRELIMINARY) as tree:
            errors = v.validate_dir(
                tree,
                mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1")
            self.assertEqual(errors, [], errors)


class PackageVersionAwareExpectedTagTests(unittest.TestCase):
    """Pi-approved package-version-aware expected-tag resolution.

    Slice / RC4B-002/003/012/026: RC8 active mapping with RC7 historical
    support and cross-file tag equality among package_tag /
    weaver_forge_tag_requested / canonical_tag / expected.
    """

    def test_resolver_mapping_and_unknown_fail_closed(self):
        self.assertEqual(
            v.expected_package_tag_for_version("1.0.0-rc4"),
            v.PACKAGE_TAG_HISTORICAL_RC4,
        )
        self.assertEqual(
            v.expected_package_tag_for_version("1.0.0-rc5"),
            v.PACKAGE_TAG_ACTIVE_RC5,
        )
        self.assertEqual(
            v.expected_package_tag_for_version("1.0.0-rc5-phase4-s3-fixture"),
            v.PACKAGE_TAG_ACTIVE_RC5,
        )
        self.assertEqual(
            v.expected_package_tag_for_version("1.0.0-rc7"),
            v.PACKAGE_TAG_HISTORICAL_RC7,
        )
        self.assertEqual(
            v.expected_package_tag_for_version("1.0.0-rc8"),
            v.PACKAGE_TAG_ACTIVE_RC8,
        )
        self.assertEqual(v.PACKAGE_TAG_EXPECTED, v.PACKAGE_TAG_ACTIVE_RC8)
        self.assertIsNone(v.expected_package_tag_for_version("1.0.0-rc3"))
        self.assertIsNone(v.expected_package_tag_for_version("1.0.0-rc6"))
        self.assertIsNone(v.expected_package_tag_for_version("1.0.0-rc99"))
        self.assertIsNone(v.expected_package_tag_for_version(""))

    def _mutate_kv_file(
        self, files: dict[str, str], filename: str, **replacements: str
    ) -> dict[str, str]:
        text = files[filename]
        for key, value in replacements.items():
            needle = f"{key}="
            lines = []
            for line in text.splitlines():
                if line.startswith(needle):
                    lines.append(f"{key}={value}")
                else:
                    lines.append(line)
            text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
        files = dict(files)
        files[filename] = text
        return files

    def _mutate_identity(self, files: dict[str, str], **replacements: str) -> dict[str, str]:
        return self._mutate_kv_file(files, "WEAVER_FORGE_PACKAGE_IDENTITY.txt", **replacements)

    def _align_tags_in_tree(self, tree: Path, old_tag: str, new_tag: str) -> None:
        for name in (
            "SOURCE_ACQUISITION.txt",
            "WITNESS_VERDICT.md",
            "WEAVER_FORGE_FINAL_BINDING.txt",
            "WEAVER_FORGE_PACKAGE_IDENTITY.txt",
        ):
            path = tree / name
            if not path.is_file():
                continue
            path.write_text(
                path.read_text(encoding="utf-8").replace(old_tag, new_tag),
                encoding="utf-8",
                newline="\n",
            )

    def _rewrite_manifest_and_seal(self, tree: Path) -> None:
        import hashlib

        import evidence_inventory as ei

        binding_path = tree / "WEAVER_FORGE_FINAL_BINDING.txt"
        binding_text = binding_path.read_text(encoding="utf-8") if binding_path.is_file() else ""
        if binding_path.is_file():
            binding_path.unlink()
        ei.write_evidence_manifest(tree)
        if not binding_text:
            return
        digest = hashlib.sha256((tree / "EVIDENCE_MANIFEST.sha256").read_bytes()).hexdigest()
        binding_path.write_text(
            "\n".join(
                f"final_manifest_sha256={digest}"
                if line.startswith("final_manifest_sha256=")
                else line
                for line in binding_text.splitlines()
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def test_rc4_package_rc4_tag_passes_and_rc5_tag_fails(self):
        base = fx.build_scenario("success-artifact-present")
        tmp_ok = Path(tempfile.mkdtemp(prefix="pv_ok_", dir=HERE))
        tmp_bad = Path(tempfile.mkdtemp(prefix="pv_bad_", dir=HERE))
        try:
            fx.write_tree(tmp_ok, base)
            self.assertEqual(v.validate_dir(tmp_ok, schema_register_version="rc6.1"), [])

            bad = self._mutate_identity(
                base,
                weaver_forge_tag_requested=v.PACKAGE_TAG_ACTIVE_RC5,
            )
            fx.write_tree(tmp_bad, bad)
            errors = v.validate_dir(tmp_bad, schema_register_version="rc6.1")
            self.assertTrue(
                any("canonical_run=yes requires weaver_forge_tag_requested=" in e for e in errors),
                errors,
            )
            self.assertTrue(
                any(v.PACKAGE_TAG_HISTORICAL_RC4 in e for e in errors),
                errors,
            )
        finally:
            import shutil

            shutil.rmtree(tmp_ok, ignore_errors=True)
            shutil.rmtree(tmp_bad, ignore_errors=True)

    def test_rc5_package_requires_rc5_tag_not_rc4(self):
        base = fx.build_scenario("success-artifact-present")
        # Promote historical builder output to active rc5 identity with matching tag.
        good = self._mutate_identity(
            base,
            package_version="1.0.0-rc5",
            weaver_forge_tag_requested=v.PACKAGE_TAG_ACTIVE_RC5,
        )
        bad = self._mutate_identity(
            base,
            package_version="1.0.0-rc5",
            weaver_forge_tag_requested=v.PACKAGE_TAG_HISTORICAL_RC4,
        )
        tmp_ok = Path(tempfile.mkdtemp(prefix="pv_rc5ok_", dir=HERE))
        tmp_bad = Path(tempfile.mkdtemp(prefix="pv_rc5bad_", dir=HERE))
        try:
            fx.write_tree(tmp_ok, good)
            # Also align SOURCE_ACQUISITION / WITNESS_VERDICT tags for internal consistency.
            (tmp_ok / "SOURCE_ACQUISITION.txt").write_text(
                (tmp_ok / "SOURCE_ACQUISITION.txt")
                .read_text(encoding="utf-8")
                .replace(v.PACKAGE_TAG_HISTORICAL_RC4, v.PACKAGE_TAG_ACTIVE_RC5),
                encoding="utf-8",
                newline="\n",
            )
            (tmp_ok / "WITNESS_VERDICT.md").write_text(
                (tmp_ok / "WITNESS_VERDICT.md")
                .read_text(encoding="utf-8")
                .replace(v.PACKAGE_TAG_HISTORICAL_RC4, v.PACKAGE_TAG_ACTIVE_RC5),
                encoding="utf-8",
                newline="\n",
            )
            import evidence_inventory as ei

            ei.write_evidence_manifest(tmp_ok)
            self.assertEqual(v.validate_dir(tmp_ok, schema_register_version="rc6.1"), [])

            fx.write_tree(tmp_bad, bad)
            errors = v.validate_dir(tmp_bad, schema_register_version="rc6.1")
            self.assertTrue(
                any("canonical_run=yes requires weaver_forge_tag_requested=" in e for e in errors),
                errors,
            )
            self.assertTrue(any(v.PACKAGE_TAG_ACTIVE_RC5 in e for e in errors), errors)
        finally:
            import shutil

            shutil.rmtree(tmp_ok, ignore_errors=True)
            shutil.rmtree(tmp_bad, ignore_errors=True)

    def test_rc7_coherent_tuple_accepted(self):
        base = fx.build_scenario("success-artifact-present")
        good = self._mutate_identity(
            base,
            package_version="1.0.0-rc7",
            weaver_forge_tag_requested=v.PACKAGE_TAG_HISTORICAL_RC7,
        )
        tmp = Path(tempfile.mkdtemp(prefix="pv_rc7ok_", dir=HERE))
        try:
            fx.write_tree(tmp, good)
            self._align_tags_in_tree(tmp, v.PACKAGE_TAG_HISTORICAL_RC4, v.PACKAGE_TAG_HISTORICAL_RC7)
            import evidence_inventory as ei

            ei.write_evidence_manifest(tmp)
            self.assertEqual(v.validate_dir(tmp, schema_register_version="rc6.1"), [])
            self.assertEqual(
                v.expected_package_tag_for_version("1.0.0-rc7"),
                v.PACKAGE_TAG_HISTORICAL_RC7,
            )
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)

    def test_rc7_unsupported_when_mapping_absent_is_fail_closed_for_unknown(self):
        # Sanity: unknown versions still fail closed; RC7 itself is mapped.
        self.assertIsNotNone(v.expected_package_tag_for_version("1.0.0-rc7"))
        base = fx.build_scenario("success-artifact-present")
        unknown = self._mutate_identity(base, package_version="1.0.0-rc7-unknown")
        tmp = Path(tempfile.mkdtemp(prefix="pv_rc7unk_", dir=HERE))
        try:
            fx.write_tree(tmp, unknown)
            errors = v.validate_dir(tmp, schema_register_version="rc6.1")
            self.assertTrue(
                any("unsupported package_version=" in e for e in errors),
                errors,
            )
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)

    def test_rc7_verdict_package_tag_mismatch_rejected(self):
        base = fx.build_scenario("success-artifact-present")
        good = self._mutate_identity(
            base,
            package_version="1.0.0-rc7",
            weaver_forge_tag_requested=v.PACKAGE_TAG_HISTORICAL_RC7,
        )
        tmp = Path(tempfile.mkdtemp(prefix="pv_rc7verdict_", dir=HERE))
        try:
            fx.write_tree(tmp, good)
            self._align_tags_in_tree(tmp, v.PACKAGE_TAG_HISTORICAL_RC4, v.PACKAGE_TAG_HISTORICAL_RC7)
            (tmp / "WITNESS_VERDICT.md").write_text(
                (tmp / "WITNESS_VERDICT.md")
                .read_text(encoding="utf-8")
                .replace(v.PACKAGE_TAG_HISTORICAL_RC7, v.PACKAGE_TAG_ACTIVE_RC5),
                encoding="utf-8",
                newline="\n",
            )
            import evidence_inventory as ei

            ei.write_evidence_manifest(tmp)
            errors = v.validate_dir(tmp, schema_register_version="rc6.1")
            self.assertTrue(
                any("package_tag must equal expected tag" in e for e in errors),
                errors,
            )
            self.assertTrue(any(v.PACKAGE_TAG_HISTORICAL_RC7 in e for e in errors), errors)
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)

    def test_rc7_identity_requested_tag_mismatch_rejected(self):
        base = fx.build_scenario("success-artifact-present")
        bad = self._mutate_identity(
            base,
            package_version="1.0.0-rc7",
            weaver_forge_tag_requested=v.PACKAGE_TAG_ACTIVE_RC5,
        )
        tmp = Path(tempfile.mkdtemp(prefix="pv_rc7id_", dir=HERE))
        try:
            fx.write_tree(tmp, bad)
            (tmp / "WITNESS_VERDICT.md").write_text(
                (tmp / "WITNESS_VERDICT.md")
                .read_text(encoding="utf-8")
                .replace(v.PACKAGE_TAG_HISTORICAL_RC4, v.PACKAGE_TAG_HISTORICAL_RC7),
                encoding="utf-8",
                newline="\n",
            )
            import evidence_inventory as ei

            ei.write_evidence_manifest(tmp)
            errors = v.validate_dir(tmp, schema_register_version="rc6.1")
            self.assertTrue(
                any("canonical_run=yes requires weaver_forge_tag_requested=" in e for e in errors),
                errors,
            )
            self.assertTrue(any(v.PACKAGE_TAG_HISTORICAL_RC7 in e for e in errors), errors)
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)

    def test_rc8_final_binding_canonical_tag_mismatch_rejected(self):
        with _pinned_regression_fixture("rc6-r6-synthetic-final") as positive:
            self.assertEqual(v.validate_dir(positive), [])
            base = _regression_snapshot(positive)
            with _pinned_regression_fixture("rc6-r6-synthetic-final", mutable=True) as tmp:
                self.assertEqual(_regression_snapshot(tmp), base)
                old = b"canonical_tag=grok-build-witness-v1.0.0-rc8\n"
                new = b"canonical_tag=grok-build-witness-v1.0.0-rc5\n"
                path = tmp / "WEAVER_FORGE_FINAL_BINDING.txt"
                self.assertEqual(path.read_bytes().count(old), 1)
                path.write_bytes(path.read_bytes().replace(old, new, 1))
                self._rewrite_manifest_and_seal(tmp)
                errors = v.validate_dir(tmp)
                self.assertTrue(
                    any(
                        "canonical_tag must equal expected tag" in e
                        or "canonical_tag must equal WEAVER_FORGE_PACKAGE_IDENTITY.txt"
                        in e
                        or "package_tag must equal WEAVER_FORGE_FINAL_BINDING.txt canonical_tag"
                        in e
                        for e in errors
                    ),
                    errors,
                )
                _record_tag_causality(base, tmp, path.name, old, new, errors, (
                    "canonical_tag must equal expected tag",
                    "canonical_tag must equal WEAVER_FORGE_PACKAGE_IDENTITY.txt",
                    "package_tag must equal WEAVER_FORGE_FINAL_BINDING.txt canonical_tag",
                ))
            self.assertEqual(_regression_snapshot(positive), base)

    def test_rc8_cross_file_identity_mismatch_rejected(self):
        with _pinned_regression_fixture("rc6-r6-synthetic-final") as positive:
            self.assertEqual(v.validate_dir(positive), [])
            base = _regression_snapshot(positive)
            with _pinned_regression_fixture("rc6-r6-synthetic-final", mutable=True) as tmp:
                self.assertEqual(_regression_snapshot(tmp), base)
                old = b"package_tag=grok-build-witness-v1.0.0-rc8\n"
                new = b"package_tag=grok-build-witness-v1.0.0-rc4\n"
                path = tmp / "WITNESS_VERDICT.md"
                self.assertEqual(path.read_bytes().count(old), 1)
                path.write_bytes(path.read_bytes().replace(old, new, 1))
                self._rewrite_manifest_and_seal(tmp)
                errors = v.validate_dir(tmp)
                self.assertTrue(
                    any(
                        "package_tag must equal expected tag" in e
                        or "package_tag must equal WEAVER_FORGE_PACKAGE_IDENTITY.txt" in e
                        or "package_tag must equal WEAVER_FORGE_FINAL_BINDING.txt" in e
                        for e in errors
                    ),
                    errors,
                )
                _record_tag_causality(base, tmp, path.name, old, new, errors, (
                    "package_tag must equal expected tag",
                    "package_tag must equal WEAVER_FORGE_PACKAGE_IDENTITY.txt",
                    "package_tag must equal WEAVER_FORGE_FINAL_BINDING.txt",
                ))
            self.assertEqual(_regression_snapshot(positive), base)

    def test_rc8_coherent_tuple_with_final_binding_accepted(self):
        with _pinned_regression_fixture("rc6-r6-synthetic-final") as tmp:
            self.assertEqual(v.validate_dir(tmp), [])
            self.assertEqual(
                v.expected_package_tag_for_version("1.0.0-rc8"),
                v.PACKAGE_TAG_ACTIVE_RC8,
            )

    def test_rc8_coherent_tuple_accepted(self):
        base = fx.build_scenario("success-artifact-present")
        good = self._mutate_identity(
            base,
            package_version="1.0.0-rc8",
            weaver_forge_tag_requested=v.PACKAGE_TAG_ACTIVE_RC8,
        )
        tmp = Path(tempfile.mkdtemp(prefix="pv_rc8ok_", dir=HERE))
        try:
            fx.write_tree(tmp, good)
            self._align_tags_in_tree(tmp, v.PACKAGE_TAG_HISTORICAL_RC4, v.PACKAGE_TAG_ACTIVE_RC8)
            import evidence_inventory as ei

            ei.write_evidence_manifest(tmp)
            self.assertEqual(v.validate_dir(tmp, schema_register_version="rc6.1"), [])
            self.assertEqual(
                v.expected_package_tag_for_version("1.0.0-rc8"),
                v.PACKAGE_TAG_ACTIVE_RC8,
            )
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)

    def test_unknown_package_version_fails_closed(self):
        base = fx.build_scenario("success-artifact-present")
        unknown = self._mutate_identity(base, package_version="1.0.0-rc99")
        tmp = Path(tempfile.mkdtemp(prefix="pv_unk_", dir=HERE))
        try:
            fx.write_tree(tmp, unknown)
            errors = v.validate_dir(tmp, schema_register_version="rc6.1")
            self.assertTrue(
                any("unsupported package_version=" in e for e in errors),
                errors,
            )
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)

    def test_active_rc5_and_historical_rc4_fixtures_pass(self):
        with _pinned_regression_fixture("rc5-preliminary-success", mode=v.MODE_HOST_PRELIMINARY) as tree:
            self.assertEqual(
                v.validate_dir(tree, mode=v.MODE_HOST_PRELIMINARY, schema_register_version="rc6.1"),
                [],
            )
            pkg = (tree / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8")
            self.assertIn(f"weaver_forge_tag_requested={v.PACKAGE_TAG_ACTIVE_RC5}", pkg)
        with _pinned_regression_fixture("rc5-synthetic-final-success") as tree:
            self.assertEqual(
                v.validate_dir(tree, mode=v.MODE_FINAL_SUBMISSION, schema_register_version="rc6.1"),
                [],
            )
        with _pinned_regression_fixture("success-artifact-present") as tree:
            self.assertEqual(v.validate_dir(tree, schema_register_version="rc6.1"), [])
            hist = (tree / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8")
            self.assertIn(f"weaver_forge_tag_requested={v.PACKAGE_TAG_HISTORICAL_RC4}", hist)
        # Current payload is fixed Git material; only its two derived seal files differ.
        with _pinned_regression_fixture("rc6-r6-synthetic-final") as tree:
            identity = (tree / "WEAVER_FORGE_PACKAGE_IDENTITY.txt").read_text(encoding="utf-8")
            self.assertIn("package_version=1.0.0-rc8", identity)
            self.assertIn(f"weaver_forge_tag_requested={v.PACKAGE_TAG_ACTIVE_RC8}", identity)
            self.assertEqual(v.validate_dir(tree), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
