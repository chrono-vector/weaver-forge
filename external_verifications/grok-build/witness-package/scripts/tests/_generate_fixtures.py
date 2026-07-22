"""Materialize the on-disk golden fixtures under tests/fixtures/.

Run:  python external_verifications/grok-build/witness-package/scripts/tests/_generate_fixtures.py

This is a helper (not a test module — its name does not match test_*.py so
unittest discovery ignores it). The unit tests build the same trees in temp
directories via fixtures_lib, and additionally validate these committed
fixtures, so the two stay consistent.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import fixtures_lib

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"


def main() -> None:
    for scenario in fixtures_lib.ALL_SCENARIOS:
        dest = FIXTURES / scenario
        if dest.exists():
            shutil.rmtree(dest)
        fixtures_lib.build_and_write(dest, scenario)
        print(f"wrote {dest}")


if __name__ == "__main__":
    main()
