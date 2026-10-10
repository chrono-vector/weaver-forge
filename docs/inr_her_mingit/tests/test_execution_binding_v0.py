"""Fixture tests for the EB-0 MinGit execution-binding decision.

These tests supply plain data only. They do not open the ratified ZIP,
hash its members, or launch Git.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.inr_her_001.supervisor_her_v1 import RATIFIED_GIT_SHA256, classify_git_pin
from docs.inr_her_mingit.execution_binding_v0 import (
    RATIFIED_DISTRIBUTION_SHA256,
    evaluate_execution_binding,
)

DIST = RATIFIED_DISTRIBUTION_SHA256
SNAP = "ab2543fea7eebdc8476b63af2ff8acec10fce72fc9f72a40c9123df94c6ac1ae"
CMD = "11" * 32
BIN = "22" * 32
DLL = "33" * 32
OTHER = "44" * 32
TREE = "C:/pinned/mingit"
_PASS_VALUES = {"PASS", "ISOLATION_PASS", "FULL_INR_PASS", "FRESH", "HASH_AGREEMENT_ONLY"}


def _valid() -> dict:
    return {
        "distribution_sha256": DIST,
        "tree_root": TREE,
        "candidate_path": TREE + "/mingw64/bin/git.exe",
        "manifest": [
            {"relative_path": "cmd/git.exe", "sha256": CMD, "role": "execution_image"},
            {"relative_path": "mingw64/bin/git.exe", "sha256": BIN, "role": "execution_image"},
            {"relative_path": "mingw64/bin/example.dll", "sha256": DLL, "role": "dependency"},
            {"relative_path": "etc/gitconfig", "sha256": OTHER, "role": "other"},
        ],
        "observed": [
            {"relative_path": "cmd/git.exe", "sha256": CMD},
            {"relative_path": "mingw64/bin/git.exe", "sha256": BIN},
            {"relative_path": "mingw64/bin/example.dll", "sha256": DLL},
            {"relative_path": "etc/gitconfig", "sha256": OTHER},
        ],
        "dependencies": [
            {"path": TREE + "/mingw64/bin/example.dll", "sha256": DLL},
        ],
        "environment": {
            "PATH": TREE + "/mingw64/bin",
            "GIT_NO_REPLACE_OBJECTS": "1",
        },
        "source": "BOUND_TREE",
        "reparse_escape": False,
        "mingit_sha256_authenticated": False,
    }


class ExecutionBindingV0Tests(unittest.TestCase):
    def assertClosed(self, result: dict) -> None:
        self.assertNotEqual("PASS", result["overall_status"])
        self.assertFalse(result["full_inr_ready"])
        self.assertFalse(result["isolation_pass"])
        self.assertFalse(result["freshness_pass"])
        self.assertEqual("UNEXECUTED", result["execution_binding_real"])
        self.assertEqual("UNRATIFIED", result["operational_mingit_pin"])
        self.assertEqual("UNVERIFIED", result["filesystem_verification"])
        self.assertEqual("UNVERIFIED", result["reparse_verification"])
        self.assertEqual("UNVERIFIED", result["loader_verification"])
        self.assertEqual("UNVERIFIED", result["acl_verification"])
        self.assertEqual("UNVERIFIED", result["process_isolation"])
        self.assertEqual(("BLOCKED", "HER_GIT_PIN_UNRATIFIED"), (
            result["operational_pin_status"],
            result["operational_pin_reason"],
        ))
        for value in result.values():
            if type(value) is str:
                self.assertNotIn(value, _PASS_VALUES)

    def test_fixture_match_stays_unpinned_and_blocked(self) -> None:
        result = evaluate_execution_binding(_valid())
        self.assertEqual("TREE_MATCH_UNPINNED", result["binding_result"])
        self.assertEqual("BLOCKED", result["overall_status"])
        self.assertEqual("HER_GIT_PIN_UNRATIFIED", result["overall_reason"])
        self.assertTrue(result["distribution_accepted"])
        self.assertClosed(result)

    def test_match_calls_classify_git_pin_with_image_digest(self) -> None:
        with mock.patch(
            "docs.inr_her_mingit.execution_binding_v0.classify_git_pin",
            wraps=classify_git_pin,
        ) as spy:
            evaluate_execution_binding(_valid())
        spy.assert_called_once_with(BIN)

    def test_pinned_source_label_does_not_ratify_pin(self) -> None:
        document = _valid()
        document["source"] = "MINGIT_PINNED"
        result = evaluate_execution_binding(document)
        self.assertEqual("TREE_MATCH_UNPINNED", result["binding_result"])
        self.assertEqual("HER_GIT_PIN_UNRATIFIED", result["operational_pin_reason"])
        self.assertClosed(result)

    def test_lexical_dot_segment_matches_selected_image(self) -> None:
        document = _valid()
        document["candidate_path"] = TREE + "/mingw64/bin/./git.exe"
        result = evaluate_execution_binding(document)
        self.assertEqual("TREE_MATCH_UNPINNED", result["binding_result"])
        self.assertClosed(result)

    def test_snapshot_distribution_is_excluded_before_tree_match(self) -> None:
        document = _valid()
        document["distribution_sha256"] = SNAP
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_DISTRIBUTION_EXCLUDED", result["overall_reason"])
        self.assertFalse(result["distribution_accepted"])
        self.assertEqual("REFUSED", result["binding_result"])
        self.assertClosed(result)

    def test_other_distribution_digest_is_rejected(self) -> None:
        document = _valid()
        document["distribution_sha256"] = "ab" * 32
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_DISTRIBUTION_REJECTED", result["overall_reason"])
        self.assertFalse(result["distribution_accepted"])
        self.assertClosed(result)

    def test_zip_digest_cannot_pose_as_executable(self) -> None:
        document = _valid()
        document["manifest"][1]["sha256"] = DIST
        document["observed"][1]["sha256"] = DIST
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_DIGEST_ROLE_MISMATCH", result["overall_reason"])
        self.assertClosed(result)

    def test_snapshot_digest_cannot_pose_as_executable(self) -> None:
        document = _valid()
        document["manifest"][1]["sha256"] = SNAP
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_DIGEST_ROLE_MISMATCH", result["overall_reason"])
        self.assertClosed(result)

    def test_forbidden_digests_are_refused_for_every_manifest_role(self) -> None:
        cases = (
            (DIST, 1, "execution_image"),
            (SNAP, 1, "execution_image"),
            (DIST, 2, "dependency"),
            (SNAP, 2, "dependency"),
            (DIST, 3, "other"),
            (SNAP, 3, "other"),
        )
        for digest, index, role in cases:
            with self.subTest(role=role, digest=digest[:8]):
                document = _valid()
                self.assertEqual(role, document["manifest"][index]["role"])
                document["manifest"][index]["sha256"] = digest
                document["observed"][index]["sha256"] = digest
                result = evaluate_execution_binding(document)
                self.assertEqual("BLOCKED", result["overall_status"])
                self.assertEqual("HER_GIT_DIGEST_ROLE_MISMATCH", result["overall_reason"])
                self.assertEqual("REFUSED", result["binding_result"])
                self.assertNotEqual("TREE_MATCH_UNPINNED", result["binding_result"])
                self.assertClosed(result)

    def test_path_outside_root_is_unexpected_source(self) -> None:
        document = _valid()
        document["candidate_path"] = "C:/Program Files/Git/cmd/git.exe"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", result["overall_reason"])
        self.assertClosed(result)

    def test_grok_git_path_is_unexpected_source(self) -> None:
        document = _valid()
        document["candidate_path"] = "C:/Users/mine0/AppData/Local/grok/git/cmd/git.exe"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", result["overall_reason"])
        self.assertClosed(result)

    def test_foreign_volume_is_unexpected_source(self) -> None:
        document = _valid()
        document["candidate_path"] = "D:/pinned/mingit/mingw64/bin/git.exe"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", result["overall_reason"])
        self.assertClosed(result)

    def test_prefix_boundary_is_not_containment(self) -> None:
        document = _valid()
        document["candidate_path"] = "C:/pinned/mingit-evil/mingw64/bin/git.exe"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", result["overall_reason"])
        self.assertClosed(result)

    def test_parent_escape_is_unexpected_source(self) -> None:
        document = _valid()
        document["candidate_path"] = TREE + "/mingw64/../../Windows/git.exe"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", result["overall_reason"])
        self.assertClosed(result)

    def test_manifest_parent_segment_is_unexpected_source(self) -> None:
        document = _valid()
        document["manifest"][1]["relative_path"] = "mingw64/../mingw64/bin/git.exe"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", result["overall_reason"])
        self.assertClosed(result)

    def test_reparse_flag_refuses_without_claiming_reparse_proof(self) -> None:
        document = _valid()
        document["reparse_escape"] = True
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", result["overall_reason"])
        self.assertEqual("UNVERIFIED", result["reparse_verification"])
        self.assertClosed(result)

    def test_unexpected_source_label_is_refused(self) -> None:
        document = _valid()
        document["source"] = "UNEXPECTED"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", result["overall_reason"])
        self.assertClosed(result)

    def test_live_checkout_source_is_refused(self) -> None:
        document = _valid()
        document["source"] = "LIVE_CHECKOUT"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", result["overall_reason"])
        self.assertClosed(result)

    def test_pinned_label_without_manifest_match_stays_unratified(self) -> None:
        document = _valid()
        document["source"] = "MINGIT_PINNED"
        document["observed"][1]["sha256"] = "55" * 32
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_TREE_INTEGRITY_REFUSED", result["overall_reason"])
        self.assertEqual("HER_GIT_PIN_UNRATIFIED", result["operational_pin_reason"])
        self.assertClosed(result)

    def test_extra_git_exe_is_refused(self) -> None:
        document = _valid()
        document["observed"].append({
            "relative_path": "mingw64/libexec/git-core/git.exe",
            "sha256": "66" * 32,
        })
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_TREE_INTEGRITY_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_shim_only_manifest_does_not_bind(self) -> None:
        document = _valid()
        document["manifest"] = [
            {"relative_path": "cmd/git.exe", "sha256": CMD, "role": "execution_image"},
            {"relative_path": "mingw64/bin/example.dll", "sha256": DLL, "role": "dependency"},
        ]
        document["observed"] = [
            {"relative_path": "cmd/git.exe", "sha256": CMD},
            {"relative_path": "mingw64/bin/example.dll", "sha256": DLL},
        ]
        document["candidate_path"] = TREE + "/cmd/git.exe"
        document["environment"]["PATH"] = TREE + "/cmd"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_TREE_INTEGRITY_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_cmd_shim_candidate_does_not_bind(self) -> None:
        document = _valid()
        document["candidate_path"] = TREE + "/cmd/git.exe"
        document["environment"]["PATH"] = TREE + "/cmd"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_TREE_INTEGRITY_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_missing_observed_member_is_refused(self) -> None:
        document = _valid()
        document["observed"].pop()
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_TREE_INTEGRITY_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_observed_hash_mismatch_is_refused(self) -> None:
        document = _valid()
        document["observed"][2]["sha256"] = "77" * 32
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_TREE_INTEGRITY_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_missing_dependency_is_refused(self) -> None:
        document = _valid()
        document["dependencies"] = []
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_DEPENDENCY_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_dependency_hash_mismatch_is_refused(self) -> None:
        document = _valid()
        document["dependencies"][0]["sha256"] = "88" * 32
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_DEPENDENCY_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_extra_dependency_is_refused(self) -> None:
        document = _valid()
        document["dependencies"].append({
            "path": TREE + "/mingw64/bin/extra.dll",
            "sha256": "99" * 32,
        })
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_DEPENDENCY_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_dependency_outside_root_is_refused(self) -> None:
        document = _valid()
        document["dependencies"][0]["path"] = "C:/Windows/System32/example.dll"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_DEPENDENCY_REFUSED", result["overall_reason"])
        self.assertEqual("UNVERIFIED", result["loader_verification"])
        self.assertClosed(result)

    def test_inherited_git_dir_is_refused(self) -> None:
        self._refuse_git_name("GIT_DIR")

    def test_inherited_git_exec_path_is_refused(self) -> None:
        self._refuse_git_name("GIT_EXEC_PATH")

    def test_inherited_git_config_global_is_refused(self) -> None:
        self._refuse_git_name("GIT_CONFIG_GLOBAL")

    def test_inherited_git_config_system_is_refused(self) -> None:
        self._refuse_git_name("GIT_CONFIG_SYSTEM")

    def test_second_path_entry_is_refused(self) -> None:
        document = _valid()
        document["environment"]["PATH"] = TREE + "/mingw64/bin;C:/Program Files/Git/cmd"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_PATH_CONTROL_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_path_must_be_the_selected_image_parent(self) -> None:
        document = _valid()
        document["environment"]["PATH"] = TREE + "/cmd"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_PATH_CONTROL_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_duplicate_path_keys_are_refused_in_both_orders(self) -> None:
        pairs = (
            ("PATH", "Path"),
            ("Path", "PATH"),
            ("PATH", "path"),
            ("path", "PATH"),
            ("Path", "path"),
            ("path", "Path"),
        )
        for first, second in pairs:
            with self.subTest(first=first, second=second):
                document = _valid()
                document["environment"] = {
                    first: TREE + "/mingw64/bin",
                    second: TREE + "/mingw64/bin",
                    "GIT_NO_REPLACE_OBJECTS": "1",
                }
                result = evaluate_execution_binding(document)
                self.assertEqual("BLOCKED", result["overall_status"])
                self.assertEqual("HER_GIT_PATH_CONTROL_REFUSED", result["overall_reason"])
                self.assertEqual("REFUSED", result["binding_result"])
                self.assertClosed(result)

    def test_all_three_path_spellings_are_refused(self) -> None:
        document = _valid()
        document["environment"] = {
            "PATH": TREE + "/mingw64/bin",
            "Path": TREE + "/mingw64/bin",
            "path": TREE + "/cmd",
            "GIT_NO_REPLACE_OBJECTS": "1",
        }
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_PATH_CONTROL_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_missing_path_key_is_refused(self) -> None:
        document = _valid()
        del document["environment"]["PATH"]
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_PATH_CONTROL_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_one_path_key_in_any_case_stays_unpinned(self) -> None:
        for name in ("PATH", "Path", "path"):
            with self.subTest(name=name):
                document = _valid()
                value = document["environment"].pop("PATH")
                document["environment"][name] = value
                result = evaluate_execution_binding(document)
                self.assertEqual("TREE_MATCH_UNPINNED", result["binding_result"])
                self.assertEqual("BLOCKED", result["overall_status"])
                self.assertEqual("HER_GIT_PIN_UNRATIFIED", result["overall_reason"])
                self.assertClosed(result)

    def test_missing_git_no_replace_objects_is_refused(self) -> None:
        document = _valid()
        del document["environment"]["GIT_NO_REPLACE_OBJECTS"]
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_PATH_CONTROL_REFUSED", result["overall_reason"])
        self.assertClosed(result)

    def test_authenticated_flag_is_contradiction(self) -> None:
        document = _valid()
        document["mingit_sha256_authenticated"] = True
        result = evaluate_execution_binding(document)
        self.assertEqual("FAIL", result["overall_status"])
        self.assertEqual("HER_CONTRADICTION", result["overall_reason"])
        self.assertClosed(result)

    def test_pass_claims_are_contradictions(self) -> None:
        for claim in ("PASS", "ISOLATION_PASS", "FRESH", "FULL_INR_PASS", "HASH_AGREEMENT_ONLY"):
            with self.subTest(claim=claim):
                document = _valid()
                document["claimed_status"] = claim
                result = evaluate_execution_binding(document)
                self.assertEqual("FAIL", result["overall_status"])
                self.assertEqual("HER_CONTRADICTION", result["overall_reason"])
                self.assertClosed(result)

    def test_authorization_flags_are_contradictions(self) -> None:
        for name in (
            "operational_pin_authorized",
            "execution_authorized",
            "full_inr_ready",
            "isolation_pass",
            "freshness_pass",
        ):
            with self.subTest(flag=name):
                document = _valid()
                document[name] = True
                result = evaluate_execution_binding(document)
                self.assertEqual("HER_CONTRADICTION", result["overall_reason"])
                self.assertFalse(result["full_inr_ready"])
                self.assertClosed(result)

    def test_empty_manifest_is_absent(self) -> None:
        document = _valid()
        document["manifest"] = []
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_MANIFEST_ABSENT", result["overall_reason"])
        self.assertClosed(result)

    def test_duplicate_manifest_entries_collide(self) -> None:
        document = _valid()
        document["manifest"].append(dict(document["manifest"][1]))
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_PATH_COLLISION", result["overall_reason"])
        self.assertClosed(result)

    def test_normalization_collision_is_refused(self) -> None:
        document = _valid()
        document["manifest"].append({
            "relative_path": "mingw64/bin/./git.exe",
            "sha256": "aa" * 32,
            "role": "execution_image",
        })
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_PATH_COLLISION", result["overall_reason"])
        self.assertClosed(result)

    def test_casefold_collision_is_refused(self) -> None:
        document = _valid()
        document["manifest"].append({
            "relative_path": "mingw64/bin/Git.exe",
            "sha256": "bb" * 32,
            "role": "execution_image",
        })
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_PATH_COLLISION", result["overall_reason"])
        self.assertClosed(result)

    def test_unexpected_role_is_rejected(self) -> None:
        document = _valid()
        document["manifest"][3]["role"] = "shim"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_BINDING_INPUT_REJECTED", result["overall_reason"])
        self.assertClosed(result)

    def test_git_exe_dependency_role_is_rejected(self) -> None:
        document = _valid()
        document["manifest"][0]["role"] = "dependency"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_BINDING_INPUT_REJECTED", result["overall_reason"])
        self.assertClosed(result)

    def test_dll_execution_role_is_rejected(self) -> None:
        document = _valid()
        document["manifest"][2]["role"] = "execution_image"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_BINDING_INPUT_REJECTED", result["overall_reason"])
        self.assertClosed(result)

    def test_malformed_document_is_rejected(self) -> None:
        for document in (None, [], "git", {"distribution_sha256": DIST}):
            with self.subTest(document=type(document).__name__):
                result = evaluate_execution_binding(document)
                self.assertEqual("HER_BINDING_INPUT_REJECTED", result["overall_reason"])
                self.assertClosed(result)

    def test_unc_candidate_is_rejected(self) -> None:
        document = _valid()
        document["candidate_path"] = "//server/share/git.exe"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_BINDING_INPUT_REJECTED", result["overall_reason"])
        self.assertClosed(result)

    def test_uppercase_digest_is_rejected(self) -> None:
        document = _valid()
        document["distribution_sha256"] = DIST.upper()
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_BINDING_INPUT_REJECTED", result["overall_reason"])
        self.assertClosed(result)

    def test_decision_does_not_launch_or_open_zip(self) -> None:
        source = Path(evaluate_execution_binding.__code__.co_filename).read_text(encoding="utf-8")
        for token in ("subprocess", "zipfile", "urllib", "shutil", "extractall"):
            self.assertNotIn(token, source)
        with mock.patch("subprocess.run", side_effect=AssertionError("git launched")):
            result = evaluate_execution_binding(_valid())
        self.assertEqual("TREE_MATCH_UNPINNED", result["binding_result"])

    def test_ratified_git_constant_remains_none(self) -> None:
        before = RATIFIED_GIT_SHA256
        evaluate_execution_binding(_valid())
        evaluate_execution_binding({"claimed_status": "FULL_INR_PASS", **_valid()})
        self.assertIsNone(before)
        self.assertIsNone(RATIFIED_GIT_SHA256)

    def _refuse_git_name(self, name: str) -> None:
        document = _valid()
        document["environment"][name] = "1"
        result = evaluate_execution_binding(document)
        self.assertEqual("HER_GIT_PATH_CONTROL_REFUSED", result["overall_reason"])
        self.assertClosed(result)


if __name__ == "__main__":
    unittest.main()
