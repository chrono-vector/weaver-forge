from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_ci_supply_chain import validate_repository


FULL_SHA = "1" * 40


class SupplyChainPolicyTests(unittest.TestCase):
    def make_repository(self, action_ref: str = FULL_SHA, *, permissions: bool = True) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        permission_block = "permissions:\n  contents: read\n\n" if permissions else ""
        (workflows / "test.yml").write_text(
            "name: Test\n"
            "on: push\n"
            f"{permission_block}"
            "jobs:\n"
            "  test:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            f"      - uses: actions/checkout@{action_ref}\n",
            encoding="utf-8",
        )
        (root / ".github" / "dependabot.yml").write_text(
            "version: 2\n"
            "updates:\n"
            "  - package-ecosystem: github-actions\n"
            "    directory: \"/\"\n"
            "    schedule:\n"
            "      interval: weekly\n",
            encoding="utf-8",
        )
        return root

    def assert_policy_fails(self, action_ref: str = FULL_SHA, *, permissions: bool = True) -> None:
        errors, _ = validate_repository(
            self.make_repository(action_ref, permissions=permissions)
        )
        self.assertTrue(errors)

    def test_full_sha_passes(self) -> None:
        errors, count = validate_repository(self.make_repository())
        self.assertEqual([], errors)
        self.assertEqual(1, count)

    def test_mutable_major_tag_is_rejected(self) -> None:
        self.assert_policy_fails("v4")

    def test_branch_ref_is_rejected(self) -> None:
        self.assert_policy_fails("main")

    def test_short_sha_is_rejected(self) -> None:
        self.assert_policy_fails("1a2b3c4")

    def test_missing_permissions_is_rejected(self) -> None:
        self.assert_policy_fails(permissions=False)


if __name__ == "__main__":
    unittest.main()
