"""Isolated tests for the ASCII environment and argv proposals.

These tests call pure functions only. They do not launch a process.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.inr_her_mingit.ascii_env_argv_v0 import (
    EXECUTION_AUTHORIZED,
    MINGIT_CRT_COMPATIBLE,
    WINDOWS_ENVIRONMENT_SORT_CLOSED,
    propose_ascii_command_line,
    propose_utf16le_environment_block,
)

_MODULE = Path(__file__).resolve().parents[1] / "ascii_env_argv_v0.py"
_ASCII_UPPER = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
)


def _snapshot() -> dict[str, str]:
    return {
        "WINDIR": r"C:\Windows",
        "SystemRoot": r"C:\Windows",
        "XDG_CONFIG_HOME": r"C:\xdg",
        "USERPROFILE": r"C:\home",
        "HOME": r"C:\home",
        "GIT_CONFIG_GLOBAL": r"C:\cfg\empty",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "PATH": r"C:\tree\ucrt64\bin",
    }


_LITERAL_UTF16LE = bytes.fromhex(
    "4700490054005f0043004f004e004600490047005f0047004c004f00420041004c00"
    "3d0043003a005c006300660067005c0065006d007000740079000000"
    "4700490054005f0043004f004e004600490047005f004e004f005300590053005400"
    "45004d003d0031000000"
    "4700490054005f004e004f005f005200450050004c004100430045005f004f004200"
    "4a0045004300540053003d0031000000"
    "4700490054005f004f005000540049004f004e0041004c005f004c004f0043004b00"
    "53003d0030000000"
    "4700490054005f005400450052004d0049004e0041004c005f00500052004f004d00"
    "500054003d0030000000"
    "48004f004d0045003d0043003a005c0068006f006d0065000000"
    "50004100540048003d0043003a005c0074007200650065005c007500630072007400"
    "360034005c00620069006e000000"
    "530079007300740065006d0052006f006f0074003d0043003a005c00570069006e00"
    "64006f00770073000000"
    "5500530045005200500052004f00460049004c0045003d0043003a005c0068006f00"
    "6d0065000000"
    "570049004e004400490052003d0043003a005c00570069006e0064006f0077007300"
    "0000"
    "5800440047005f0043004f004e004600490047005f0048004f004d0045003d004300"
    "3a005c007800640067000000"
    "0000"
)


def _block(pairs: list[tuple[str, str]]) -> bytes:
    ordered = sorted(pairs, key=lambda item: item[0].translate(_ASCII_UPPER))
    out = bytearray()
    for key, value in ordered:
        out += f"{key}={value}".encode("utf-16-le")
        out += b"\x00\x00"
    out += b"\x00\x00"
    return bytes(out)


class EnvironmentProposalTests(unittest.TestCase):
    def test_exact_utf16le_bytes_and_original_spelling(self) -> None:
        result = propose_utf16le_environment_block(_snapshot())
        expected = _block(list(_snapshot().items()))
        self.assertEqual(result.status, "PROPOSED")
        self.assertEqual(result.proposed, expected)
        self.assertIsInstance(result.proposed, bytes)
        self.assertFalse(result.proposed.startswith(b"\xff\xfe"))
        self.assertIn("SystemRoot=".encode("utf-16-le"), result.proposed)
        self.assertNotIn("SYSTEMROOT=".encode("utf-16-le"), result.proposed)
        decoded = result.proposed.decode("utf-16-le")
        parts = decoded.split("\x00")
        self.assertEqual(parts[-1], "")
        self.assertEqual(parts[-2], "")
        self.assertEqual(
            [part.split("=", 1)[0] for part in parts[:-2]],
            [
                "GIT_CONFIG_GLOBAL",
                "GIT_CONFIG_NOSYSTEM",
                "GIT_NO_REPLACE_OBJECTS",
                "GIT_OPTIONAL_LOCKS",
                "GIT_TERMINAL_PROMPT",
                "HOME",
                "PATH",
                "SystemRoot",
                "USERPROFILE",
                "WINDIR",
                "XDG_CONFIG_HOME",
            ],
        )

    def test_literal_utf16le_bytes_match_frozen_snapshot(self) -> None:
        result = propose_utf16le_environment_block(_snapshot())
        self.assertEqual(result.status, "PROPOSED")
        self.assertEqual(result.proposed, _LITERAL_UTF16LE)
        self.assertEqual(len(result.proposed), 484)
        self.assertTrue(result.proposed.endswith(b"\x00\x00\x00\x00"))

    def test_sort_is_independent_of_insertion_order(self) -> None:
        forward = _snapshot()
        reverse = {key: forward[key] for key in reversed(list(forward))}
        first = propose_utf16le_environment_block(forward)
        second = propose_utf16le_environment_block(reverse)
        self.assertEqual(first.proposed, second.proposed)
        self.assertEqual(first.proposed, _block(list(reverse.items())))

    def test_forward_slash_path_is_preserved(self) -> None:
        snapshot = _snapshot()
        snapshot["PATH"] = "C:/tree/ucrt64/bin"
        snapshot["GIT_CONFIG_GLOBAL"] = "C:/cfg/empty"
        result = propose_utf16le_environment_block(snapshot)
        self.assertEqual(result.status, "PROPOSED")
        self.assertIn("PATH=C:/tree/ucrt64/bin".encode("utf-16-le"), result.proposed)

    def test_case_insensitive_duplicate_is_refused(self) -> None:
        snapshot = _snapshot()
        snapshot["Path"] = r"D:\other\ucrt64\bin"
        result = propose_utf16le_environment_block(snapshot)
        self.assertEqual(result.reason, "DUPLICATE_KEY")
        self.assertIsNone(result.proposed)

    def test_forbidden_keys_are_refused(self) -> None:
        forbidden = (
            "TEMP",
            "tmp",
            "GIT_DIR",
            "GIT_WORK_TREE",
            "GIT_COMMON_DIR",
            "GIT_EXEC_PATH",
            "GIT_CONFIG",
            "GIT_CONFIG_SYSTEM",
            "GIT_CONFIG_COUNT",
            "GIT_CONFIG_PARAMETERS",
            "GIT_CONFIG_KEY_0",
            "GIT_CONFIG_VALUE_0",
            "GIT_ASKPASS",
            "GIT_SSH",
            "GIT_SSH_COMMAND",
            "PAGER",
            "GIT_PAGER",
            "less",
        )
        for key in forbidden:
            snapshot = _snapshot()
            snapshot[key] = "1"
            with self.subTest(key=key):
                result = propose_utf16le_environment_block(snapshot)
                self.assertEqual(result.reason, "FORBIDDEN_KEY")
                self.assertIsNone(result.proposed)

    def test_unauthorized_and_missing_keys_are_refused(self) -> None:
        extra = _snapshot()
        extra["GIT_CEILING_DIRECTORIES"] = r"C:\ceil"
        self.assertEqual(
            propose_utf16le_environment_block(extra).reason,
            "UNAUTHORIZED_KEY",
        )
        renamed = _snapshot()
        renamed["systemroot"] = renamed.pop("SystemRoot")
        self.assertEqual(
            propose_utf16le_environment_block(renamed).reason,
            "UNAUTHORIZED_KEY",
        )
        missing = _snapshot()
        del missing["PATH"]
        self.assertEqual(
            propose_utf16le_environment_block(missing).reason,
            "MISSING_REQUIRED_KEY",
        )

    def test_malformed_snapshot_is_refused(self) -> None:
        self.assertEqual(propose_utf16le_environment_block([]).reason, "INPUT_REJECTED")
        self.assertEqual(propose_utf16le_environment_block("PATH=1").reason, "INPUT_REJECTED")

        class Map(dict):
            pass

        class Text(str):
            pass

        self.assertEqual(
            propose_utf16le_environment_block(Map(_snapshot())).reason,
            "INPUT_REJECTED",
        )
        bad_key = _snapshot()
        bad_key[Text("FOO")] = "1"
        self.assertEqual(propose_utf16le_environment_block(bad_key).reason, "INPUT_REJECTED")
        bad_value = _snapshot()
        bad_value["HOME"] = Text(r"C:\home")
        self.assertEqual(
            propose_utf16le_environment_block(bad_value).reason,
            "INPUT_REJECTED",
        )
        numeric = _snapshot()
        numeric["HOME"] = 1
        self.assertEqual(propose_utf16le_environment_block(numeric).reason, "INPUT_REJECTED")
        self.assertEqual(
            propose_utf16le_environment_block({"": "1"}).reason,
            "INVALID_KEY",
        )
        self.assertEqual(
            propose_utf16le_environment_block({"1PATH": "1"}).reason,
            "INVALID_KEY",
        )
        self.assertEqual(
            propose_utf16le_environment_block({"A-B": "1"}).reason,
            "INVALID_KEY",
        )

    def test_nul_control_surrogate_and_invalid_values_are_refused(self) -> None:
        cases = (
            ("PATH", "C:\\tree\\ucrt64\\bin\x00", "NUL_REJECTED"),
            ("PATH", "C:\\tree\\ucrt64\\bin\x01", "CONTROL_CHARACTER"),
            ("PATH", "C:\\tree\\ucrt64\\bin\ud800", "ISOLATED_SURROGATE"),
            ("PATH", "C:\\tree\\ucrt64\\bin\u00e9", "NON_ASCII"),
            ("PATH", "C:\\tree\\ucrt64\\bin ", "WHITESPACE"),
            ("PATH", "C:\\tree\\ucrt64\\bin\"", "QUOTE"),
            ("PATH", "C:\\tree\\ucrt64\\bin*", "WILDCARD"),
            ("HOME", "C:\\home\\..\\other", "INVALID_VALUE"),
            ("PATH", r"C:\tree\ucrt64\bin\git.exe", "INVALID_VALUE"),
            ("PATH", r"C:\tree\cmd\git.exe", "INVALID_VALUE"),
            ("GIT_TERMINAL_PROMPT", "1", "INVALID_VALUE"),
            ("GIT_NO_REPLACE_OBJECTS", "0", "INVALID_VALUE"),
            ("SystemRoot", r"C:\Windows\other", "INCONSISTENT_VALUE"),
            ("USERPROFILE", r"C:\other", "INCONSISTENT_VALUE"),
        )
        for key, value, reason in cases:
            snapshot = _snapshot()
            snapshot[key] = value
            with self.subTest(key=key, reason=reason):
                result = propose_utf16le_environment_block(snapshot)
                self.assertEqual(result.status, "REFUSED")
                self.assertEqual(result.reason, reason)
                self.assertIsNone(result.proposed)
                self.assertFalse(result.execution_authorized)

    def test_malformed_paths_prefixes_ads_and_name_equals_are_refused(self) -> None:
        cases = (
            ("PATH", r"C:tree\ucrt64\bin", "INVALID_VALUE"),
            ("PATH", r"C\tree\ucrt64\bin", "INVALID_VALUE"),
            ("PATH", r"\\server\share\ucrt64\bin", "INVALID_VALUE"),
            ("PATH", r"\\?\C:\tree\ucrt64\bin", "WILDCARD"),
            ("PATH", r"\\.\C:\tree\ucrt64\bin", "INVALID_VALUE"),
            ("PATH", r"C:\tree\ucrt64\bin:Zone.Identifier", "INVALID_VALUE"),
            ("PATH", r"C:\tree\ucrt64\bin.", "INVALID_VALUE"),
            ("PATH", r"C:\tree\ucrt64\bin ", "WHITESPACE"),
            ("PATH", r"C:\a\ucrt64\bin;C:\b\ucrt64\bin", "INVALID_VALUE"),
        )
        for key, value, reason in cases:
            snapshot = _snapshot()
            snapshot[key] = value
            with self.subTest(value=value, reason=reason):
                result = propose_utf16le_environment_block(snapshot)
                self.assertEqual(result.status, "REFUSED")
                self.assertEqual(result.reason, reason)
                self.assertIsNone(result.proposed)
                self.assertFalse(result.execution_authorized)
        named = _snapshot()
        named["PATH=BIN"] = r"C:\tree\ucrt64\bin"
        result = propose_utf16le_environment_block(named)
        self.assertEqual(result.status, "REFUSED")
        self.assertEqual(result.reason, "INVALID_KEY")
        self.assertIsNone(result.proposed)
        self.assertFalse(result.execution_authorized)

    def test_proposal_does_not_authorize_execution(self) -> None:
        result = propose_utf16le_environment_block(_snapshot())
        self.assertFalse(EXECUTION_AUTHORIZED)
        self.assertFalse(WINDOWS_ENVIRONMENT_SORT_CLOSED)
        self.assertFalse(result.execution_authorized)


class ArgvProposalTests(unittest.TestCase):
    def test_three_fixed_shapes_have_exact_proposed_strings(self) -> None:
        image = r"C:\tree\ucrt64\bin\git.exe"
        cases = (
            [image, "--version"],
            [image, "--exec-path"],
            [image, "config", "--list", "--show-scope", "-z"],
        )
        for argv in cases:
            with self.subTest(argv=argv):
                result = propose_ascii_command_line(argv)
                self.assertEqual(result.status, "PROPOSED")
                self.assertEqual(result.proposed, " ".join(argv))
                self.assertNotIn('"', result.proposed)
                self.assertFalse(result.execution_authorized)
                self.assertFalse(MINGIT_CRT_COMPATIBLE)

    def test_tuple_and_forward_slash_image_are_accepted(self) -> None:
        argv = ("C:/tree/ucrt64/bin/git.exe", "--version")
        result = propose_ascii_command_line(argv)
        self.assertEqual(result.proposed, "C:/tree/ucrt64/bin/git.exe --version")

    def test_restricted_argv_refusals(self) -> None:
        image = r"C:\tree\ucrt64\bin\git.exe"
        cases = (
            ("RAW", "RAW_COMMAND_LINE"),
            (b"RAW", "RAW_COMMAND_LINE"),
            (None, "INPUT_REJECTED"),
            ([image, 1], "INPUT_REJECTED"),
            ([], "UNSUPPORTED_ARGV"),
            ([image], "UNSUPPORTED_ARGV"),
            ([image, "--version", "--extra"], "UNSUPPORTED_ARGV"),
            ([image, "--Version"], "UNSUPPORTED_ARGV"),
            ([image, "-C", "."], "UNSUPPORTED_ARGV"),
            ([image, "-c", "core.editor=ed"], "UNSUPPORTED_ARGV"),
            ([image, "--git-dir", r"C:\repo"], "UNSUPPORTED_ARGV"),
            ([image, "--work-tree", r"C:\wt"], "UNSUPPORTED_ARGV"),
            ([image, "--file", r"C:\cfg"], "UNSUPPORTED_ARGV"),
            ([r"C:\tree\cmd\git.exe", "--version"], "UNSUPPORTED_ARGV"),
            ([r"tree\ucrt64\bin\git.exe", "--version"], "UNSUPPORTED_ARGV"),
            ([r"\\server\ucrt64\bin\git.exe", "--version"], "UNSUPPORTED_ARGV"),
            ([r"C:\tree\ucrt64\bin\..\bin\git.exe", "--version"], "UNSUPPORTED_ARGV"),
            ([image + " ", "--version"], "WHITESPACE"),
            ([image + "\tbin", "--version"], "WHITESPACE"),
            ([image + '"', "--version"], "QUOTE"),
            ([image + "'", "--version"], "QUOTE"),
            ([image + "\x01", "--version"], "CONTROL_CHARACTER"),
            ([image + "\x00", "--version"], "NUL_REJECTED"),
            ([image + "\ud800", "--version"], "ISOLATED_SURROGATE"),
            ([image + "\u00e9", "--version"], "NON_ASCII"),
            ([image.replace("git.exe", "git*.exe"), "--version"], "WILDCARD"),
            ([image.replace("git.exe", "git?.exe"), "--version"], "WILDCARD"),
            ([image, "config", "--list", "--show-scope"], "UNSUPPORTED_ARGV"),
        )
        for argv, reason in cases:
            with self.subTest(reason=reason):
                result = propose_ascii_command_line(argv)
                self.assertEqual(result.status, "REFUSED")
                self.assertEqual(result.reason, reason)
                self.assertIsNone(result.proposed)
                self.assertFalse(result.execution_authorized)

    def test_malformed_drive_unc_extended_ads_and_trailing_dot_are_refused(self) -> None:
        cases = (
            ([r"C:tree\ucrt64\bin\git.exe", "--version"], "UNSUPPORTED_ARGV"),
            ([r"\\server\share\ucrt64\bin\git.exe", "--version"], "UNSUPPORTED_ARGV"),
            ([r"\\?\C:\tree\ucrt64\bin\git.exe", "--version"], "WILDCARD"),
            ([r"\\.\C:\tree\ucrt64\bin\git.exe", "--version"], "UNSUPPORTED_ARGV"),
            ([r"C:\tree\ucrt64\bin\git.exe:stream", "--version"], "UNSUPPORTED_ARGV"),
            ([r"C:\tree\ucrt64\bin\git.exe.", "--version"], "UNSUPPORTED_ARGV"),
            ([r"C:\tree\ucrt64\bin\git.exe ", "--version"], "WHITESPACE"),
        )
        for argv, reason in cases:
            with self.subTest(argv=argv[0], reason=reason):
                result = propose_ascii_command_line(argv)
                self.assertEqual(result.status, "REFUSED")
                self.assertEqual(result.reason, reason)
                self.assertIsNone(result.proposed)
                self.assertFalse(result.execution_authorized)

    def test_module_has_no_process_imports(self) -> None:
        tree = ast.parse(_MODULE.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        self.assertEqual(imported, {"__future__", "typing"})
        public = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ]
        self.assertEqual(
            public,
            ["propose_utf16le_environment_block", "propose_ascii_command_line"],
        )


if __name__ == "__main__":
    unittest.main()
