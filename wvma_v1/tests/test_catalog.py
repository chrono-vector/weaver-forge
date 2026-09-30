"""Sealed synthetic catalog parser tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from wvma_v1.canonical import digest_excluding_field
from wvma_v1.models import (
    AttemptState,
    CatalogError,
    SchemaError,
    strict_parse_catalog,
)
from wvma_v1.state import ReplayError, derive_attempt_state, seal_catalog

FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "SYNTHETIC_CATALOG.json"
)


class CatalogTests(unittest.TestCase):
    def test_seal_catalog_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            self.assertEqual(
                derive_attempt_state(out), AttemptState.NOT_CONFIGURED
            )
            catalog = seal_catalog(out, FIXTURE)
            self.assertEqual(
                derive_attempt_state(out), AttemptState.CATALOG_SEALED
            )
            with self.assertRaises(ReplayError):
                seal_catalog(out, catalog)

    def test_foreign_property_reference_rejects(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        data["mutations"][0]["property_id"] = "WVMA-UNKNOWN"
        data["catalog_digest"] = digest_excluding_field(data, "catalog_digest")
        with self.assertRaises(CatalogError):
            strict_parse_catalog(data)

    def test_critical_false_for_listed_critical_rejects(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        data["mutations"][0]["critical"] = False
        data["catalog_digest"] = digest_excluding_field(data, "catalog_digest")
        with self.assertRaises(CatalogError):
            strict_parse_catalog(data)

    def test_unknown_critical_case_id_rejects(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        data["critical_case_ids"].append("WVMA-MISSING")
        data["catalog_digest"] = digest_excluding_field(data, "catalog_digest")
        with self.assertRaises(CatalogError):
            strict_parse_catalog(data)

    def test_digest_mismatch_on_fixture_tamper(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        data["catalog_version"] = "tampered"
        with self.assertRaises((CatalogError, SchemaError)):
            strict_parse_catalog(data)

    def test_typed_catalog_malicious_digest_rejects_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            sealed = seal_catalog(out, FIXTURE)
            evil = replace(sealed, catalog_digest="../evil_digest")
            catalogs = out / "catalogs"
            before = set(catalogs.rglob("*")) if catalogs.exists() else set()
            with self.assertRaises((CatalogError, SchemaError, ValueError)):
                seal_catalog(out, evil)
            after = set(catalogs.rglob("*")) if catalogs.exists() else set()
            self.assertEqual(before, after)
            self.assertFalse(any("evil" in str(p) for p in out.rglob("*")))

    def test_typed_catalog_invalid_authority_rejects_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            sealed = seal_catalog(out, FIXTURE)
            evil = replace(sealed, authority=True)
            catalogs = out / "catalogs"
            before = set(catalogs.rglob("*"))
            with self.assertRaises((CatalogError, SchemaError)):
                seal_catalog(out, evil)
            self.assertEqual(before, set(catalogs.rglob("*")))

    def test_bogus_json_filename_does_not_imply_catalog_sealed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            catalogs = out / "catalogs"
            catalogs.mkdir(parents=True)
            (catalogs / "not-a-digest.json").write_text("{}", encoding="utf-8")
            self.assertEqual(
                derive_attempt_state(out), AttemptState.NOT_CONFIGURED
            )


if __name__ == "__main__":
    unittest.main()
