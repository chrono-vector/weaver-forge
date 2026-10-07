"""Fail-closed validator for Portfolio State Metadata v0.

PSM describes accepted state by reference. Validation establishes only that a
record conforms to this closed metadata profile and that its declared source
records resolve in Git. It creates no authority, evidence promotion, Human
Final, witness status, or production permission.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = "weaver.portfolio_state_metadata.v0"
VALID = "VALID"
INVALID = "INVALID"

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_HUMAN_ACCEPTANCE = re.compile(
    r"Decision:\s*\r?\nHUMAN_REVIEW_ACCEPTED(?:_WITH_NONMATERIAL_LIMITATIONS)?(?:\s|\Z)"
)
_TOP_LEVEL = frozenset(
    {
        "schema_version",
        "portfolio_state_id",
        "subject_scope_id",
        "source_records",
        "earned",
        "not_yet_earned",
        "validation_debt",
        "epistemic_ceiling",
        "counterexamples",
        "assumptions",
        "replayability",
        "revision_provenance",
        "limitations",
        "nonclaims",
    }
)
_SOURCE_KEYS = frozenset({"source_record_id", "path", "git_commit", "record_kind"})
_SOURCE_KINDS = frozenset(
    {"human_final", "verification", "wacp_binding", "ecp_record", "counterexample", "remediation"}
)
_EARNED_KEYS = frozenset({"claim_id", "description", "status", "source_claim_refs"})
_NOT_YET_KEYS = frozenset(
    {"claim_id", "description", "status", "source_record_ids", "blocking_debt_ids"}
)
_DEBT_KEYS = frozenset(
    {"debt_id", "description", "source_reference", "status", "blocked_claims", "closure_condition"}
)
_CEILING_KEYS = frozenset({"ceiling_id", "description", "source_record_id", "verbatim"})
_COUNTEREXAMPLE_KEYS = frozenset(
    {"counterexample_id", "description", "status", "source_record_ids", "outcome_history"}
)
_ASSUMPTION_KEYS = frozenset({"assumption_id", "description", "status", "source_record_ids"})
_REPLAY_KEYS = frozenset({"status", "source_record_ids", "independent_reproduction"})
_REVISION_KEYS = frozenset({"revision_id", "git_commit", "source_record_ids"})
_REQUIRED_NONCLAIMS = frozenset(
    {
        "does_not_create_authority",
        "does_not_establish_truth",
        "does_not_establish_correctness",
        "does_not_establish_safety",
        "does_not_promote_evidence",
        "does_not_promote_claims",
        "does_not_create_human_final",
        "does_not_grant_production_permission",
        "does_not_create_witness_status",
        "does_not_establish_independent_reproduction",
        "does_not_replace_authoritative_records",
        "does_not_prove_completeness",
    }
)

# Closed PSM-v0 interpretation pins. They bind a bounded claim key to one exact
# accepted source identity and statement; they do not grant authority or infer
# stronger claims from generic acceptance, tests, replay, or verification.
_CLAIM_BINDINGS = {
    "seic-001:closed-bounded-v0": {
        "claim_id": "seic-001-closed-bounded-v0",
        "description": "SEIC-001 is closed within its accepted bounded v0 scope and limitations.",
        "git_commit": "9d2e0f85c719307ba12e1ff6fb8b2e8f3ca833d8",
        "path": "docs/seic_001/SEIC_001_HUMAN_FINAL.md",
        "exact_text": "Final status:\nSEIC-001 CLOSED WITH NONMATERIAL LIMITATIONS",
    },
    "wacp-001:closed-bounded-v0": {
        "claim_id": "wacp-001-closed-bounded-v0",
        "description": "WACP-001 is closed within its accepted bounded v0 scope and limitations.",
        "git_commit": "ae2050629f2a6586a272afbacb2130affc2ce279",
        "path": "docs/wacp_001/WACP_001_HUMAN_FINAL.md",
        "exact_text": "Final status:\nWACP-001 CLOSED WITH NONMATERIAL LIMITATIONS",
    },
    "ecp-001:closed-bounded-v0": {
        "claim_id": "ecp-001-closed-bounded-v0",
        "description": "ECP-001 is closed within its accepted bounded v0 scope and limitations.",
        "git_commit": "374ff5d9ceecc92cccb6ea7c450e34c3787bb80a",
        "path": "docs/ecp_001/ECP_001_HUMAN_FINAL.md",
        "exact_text": "Final status:\nECP-001 CLOSED WITH NONMATERIAL LIMITATIONS",
    },
}
_COUNTEREXAMPLE_BINDINGS = {
    "seic-indirect-attribute-reach": {
        "trigger_source": (
            "9d2e0f85c719307ba12e1ff6fb8b2e8f3ca833d8",
            "docs/seic_001/SEIC_001_HUMAN_FINAL.md",
        ),
        "required_sources": frozenset(
            {
                (
                    "9d2e0f85c719307ba12e1ff6fb8b2e8f3ca833d8",
                    "docs/seic_001/SEIC_001_HUMAN_FINAL.md",
                ),
                (
                    "9d2e0f85c719307ba12e1ff6fb8b2e8f3ca833d8",
                    "docs/seic_001/SEIC_001_VERIFICATION.md",
                ),
            }
        ),
        "status": "REMEDIATED",
        "outcome_history": ("FAIL", "REMEDIATION", "PASS"),
    }
}


class DuplicateKeyError(ValueError):
    pass


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_record(path: str | Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(
        raw.decode("utf-8", "strict"), object_pairs_hook=_object_without_duplicates
    )
    if type(value) is not dict:
        raise ValueError("PSM record must be an object")
    return value


def canonical_bytes(record: dict[str, Any]) -> bytes:
    return (
        json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _string(value: Any, field: str, errors: list[str]) -> str | None:
    if type(value) is not str or not value.strip():
        errors.append(f"{field} must be a non-empty string")
        return None
    return value


def _string_list(
    value: Any, field: str, errors: list[str], *, nonempty: bool = False
) -> list[str]:
    if type(value) is not list:
        errors.append(f"{field} must be a list")
        return []
    if nonempty and not value:
        errors.append(f"{field} must not be empty")
    if any(type(item) is not str or not item.strip() for item in value):
        errors.append(f"{field} entries must be non-empty strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{field} must not contain duplicates")
    return value


def _exact_object(value: Any, keys: frozenset[str], field: str, errors: list[str]) -> dict[str, Any] | None:
    if type(value) is not dict or set(value) != keys:
        errors.append(f"{field} must contain exactly: {', '.join(sorted(keys))}")
        return None
    return value


def _exact_list(value: Any, field: str, errors: list[str], *, nonempty: bool = False) -> list[Any]:
    if type(value) is not list:
        errors.append(f"{field} must be a list")
        return []
    if nonempty and not value:
        errors.append(f"{field} must not be empty")
    return value


def _normalized_path(value: Any, field: str, errors: list[str]) -> str | None:
    path = _string(value, field, errors)
    if path is None:
        return None
    candidate = PurePosixPath(path)
    if "\\" in path or path.startswith("/") or any(part in {"", ".", ".."} for part in candidate.parts):
        errors.append(f"{field} must be a normalized repository-relative POSIX path")
        return None
    return path


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments], cwd=root, capture_output=True, check=False
    )


def _resolve_source(root: Path, source: dict[str, Any], field: str, errors: list[str]) -> None:
    path = _normalized_path(source.get("path"), f"{field}.path", errors)
    commit = _string(source.get("git_commit"), f"{field}.git_commit", errors)
    kind = source.get("record_kind")
    if kind not in _SOURCE_KINDS:
        errors.append(f"{field}.record_kind is not in the closed v0 set")
    if commit is None or _SHA.fullmatch(commit) is None:
        errors.append(f"{field}.git_commit must be a full lowercase commit SHA")
        return
    if path is None:
        return
    if _git(root, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
        errors.append(f"{field} commit is unresolved")
        return
    tree = _git(root, "ls-tree", commit, "--", path)
    if tree.returncode != 0 or not tree.stdout:
        errors.append(f"{field} path is missing at the declared commit")
        return
    metadata = tree.stdout.decode("utf-8", "replace").split("\t", 1)[0].split()
    if len(metadata) < 2 or metadata[0] not in {"100644", "100755"} or metadata[1] != "blob":
        errors.append(f"{field} path must resolve to a regular non-symlink blob")
        return
    content = _git(root, "show", f"{commit}:{path}")
    if content.returncode != 0:
        errors.append(f"{field} content is unresolved")
        return
    if kind == "human_final" and _HUMAN_ACCEPTANCE.search(
        content.stdout.decode("utf-8", "replace")
    ) is None:
        errors.append(f"{field} does not resolve to an accepted Human Final record")


def validate_record(record: Any, repository: str | Path) -> tuple[str, ...]:
    errors: list[str] = []
    root = Path(repository).resolve()
    if type(record) is not dict or set(record) != _TOP_LEVEL:
        return ("top-level fields do not match the closed PSM-v0 schema",)
    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version mismatch")
    _string(record.get("portfolio_state_id"), "portfolio_state_id", errors)
    _string(record.get("subject_scope_id"), "subject_scope_id", errors)

    sources = _exact_list(record.get("source_records"), "source_records", errors, nonempty=True)
    source_by_id: dict[str, dict[str, Any]] = {}
    source_content: dict[str, str] = {}
    for index, raw in enumerate(sources):
        field = f"source_records[{index}]"
        source = _exact_object(raw, _SOURCE_KEYS, field, errors)
        if source is None:
            continue
        source_id = _string(source.get("source_record_id"), f"{field}.source_record_id", errors)
        if source_id is not None:
            if source_id in source_by_id:
                errors.append(f"duplicate source_record_id: {source_id}")
            source_by_id[source_id] = source
        _resolve_source(root, source, field, errors)
        if source_id is not None:
            path, commit = source.get("path"), source.get("git_commit")
            if type(path) is str and type(commit) is str and _SHA.fullmatch(commit):
                content = _git(root, "show", f"{commit}:{path}")
                if content.returncode == 0:
                    source_content[source_id] = content.stdout.decode("utf-8", "replace")

    def source_refs(value: Any, field: str, *, nonempty: bool = True) -> list[str]:
        refs = _string_list(value, field, errors, nonempty=nonempty)
        for ref in refs:
            if ref not in source_by_id:
                errors.append(f"{field} references missing source record: {ref}")
        return refs

    earned = _exact_list(record.get("earned"), "earned", errors)
    earned_ids: set[str] = set()
    for index, raw in enumerate(earned):
        field = f"earned[{index}]"
        entry = _exact_object(raw, _EARNED_KEYS, field, errors)
        if entry is None:
            continue
        claim_id = _string(entry.get("claim_id"), f"{field}.claim_id", errors)
        description = _string(entry.get("description"), f"{field}.description", errors)
        if entry.get("status") != "EARNED":
            errors.append(f"{field}.status must be EARNED")
        claim_refs = _string_list(
            entry.get("source_claim_refs"), f"{field}.source_claim_refs", errors, nonempty=True
        )
        for claim_ref in claim_refs:
            binding = _CLAIM_BINDINGS.get(claim_ref)
            if binding is None:
                errors.append(f"{field} source claim ref is not in the closed PSM-v0 table: {claim_ref}")
                continue
            if claim_id != binding["claim_id"]:
                errors.append(f"{field} claim_id does not match source claim ref: {claim_ref}")
            if description != binding["description"]:
                errors.append(f"{field} description does not match source claim ref: {claim_ref}")
            matched_sources = [
                source_id
                for source_id, source in source_by_id.items()
                if source.get("git_commit") == binding["git_commit"]
                and source.get("path") == binding["path"]
                and source.get("record_kind") == "human_final"
            ]
            if not matched_sources:
                errors.append(f"{field} source claim ref has no matching accepted source identity: {claim_ref}")
            elif not any(
                binding["exact_text"] in source_content.get(source_id, "")
                for source_id in matched_sources
            ):
                errors.append(f"{field} source claim ref statement is absent: {claim_ref}")
        if claim_id is not None:
            if claim_id in earned_ids:
                errors.append(f"duplicate earned claim_id: {claim_id}")
            earned_ids.add(claim_id)

    not_yet = _exact_list(record.get("not_yet_earned"), "not_yet_earned", errors)
    not_yet_ids: set[str] = set()
    not_yet_debts: dict[str, list[str]] = {}
    for index, raw in enumerate(not_yet):
        field = f"not_yet_earned[{index}]"
        entry = _exact_object(raw, _NOT_YET_KEYS, field, errors)
        if entry is None:
            continue
        claim_id = _string(entry.get("claim_id"), f"{field}.claim_id", errors)
        _string(entry.get("description"), f"{field}.description", errors)
        if entry.get("status") != "NOT_YET_EARNED":
            errors.append(f"{field}.status must be NOT_YET_EARNED")
        refs = source_refs(entry.get("source_record_ids"), f"{field}.source_record_ids", nonempty=False)
        debt_refs = _string_list(entry.get("blocking_debt_ids"), f"{field}.blocking_debt_ids", errors)
        if not refs and not debt_refs:
            errors.append(f"{field} must retain a source or blocking debt reference")
        if claim_id is not None:
            if claim_id in not_yet_ids:
                errors.append(f"duplicate not_yet_earned claim_id: {claim_id}")
            not_yet_ids.add(claim_id)
            not_yet_debts[claim_id] = debt_refs

    conflicts = earned_ids & not_yet_ids
    if conflicts:
        errors.append(f"claims cannot be both Earned and NotYetEarned: {', '.join(sorted(conflicts))}")

    debts = _exact_list(record.get("validation_debt"), "validation_debt", errors)
    debt_ids: set[str] = set()
    blocked_by_debt: dict[str, set[str]] = {}
    for index, raw in enumerate(debts):
        field = f"validation_debt[{index}]"
        debt = _exact_object(raw, _DEBT_KEYS, field, errors)
        if debt is None:
            continue
        debt_id = _string(debt.get("debt_id"), f"{field}.debt_id", errors)
        _string(debt.get("description"), f"{field}.description", errors)
        ref = _string(debt.get("source_reference"), f"{field}.source_reference", errors)
        if ref is not None and ref not in source_by_id:
            errors.append(f"{field}.source_reference is unresolved")
        if debt.get("status") not in {"OPEN", "CLOSED"}:
            errors.append(f"{field}.status is not in the closed v0 set")
        blocked = _string_list(debt.get("blocked_claims"), f"{field}.blocked_claims", errors, nonempty=True)
        _string(debt.get("closure_condition"), f"{field}.closure_condition", errors)
        for claim in blocked:
            if claim not in not_yet_ids:
                errors.append(f"{field} blocked claim must remain NotYetEarned: {claim}")
        if debt_id is not None:
            if debt_id in debt_ids:
                errors.append(f"duplicate debt_id: {debt_id}")
            debt_ids.add(debt_id)
            blocked_by_debt[debt_id] = set(blocked)
    for claim, refs in not_yet_debts.items():
        for ref in refs:
            if ref not in debt_ids:
                errors.append(f"NotYetEarned claim {claim} references missing debt: {ref}")
            elif claim not in blocked_by_debt.get(ref, set()):
                errors.append(f"debt {ref} does not block referenced claim: {claim}")

    ceiling = _exact_object(record.get("epistemic_ceiling"), _CEILING_KEYS, "epistemic_ceiling", errors)
    if ceiling is not None:
        _string(ceiling.get("ceiling_id"), "epistemic_ceiling.ceiling_id", errors)
        _string(ceiling.get("description"), "epistemic_ceiling.description", errors)
        ceiling_ref = _string(ceiling.get("source_record_id"), "epistemic_ceiling.source_record_id", errors)
        verbatim = _string(ceiling.get("verbatim"), "epistemic_ceiling.verbatim", errors)
        if ceiling_ref is not None and ceiling_ref not in source_by_id:
            errors.append("epistemic_ceiling source is unresolved")
        elif ceiling_ref is not None and verbatim is not None and verbatim not in source_content.get(ceiling_ref, ""):
            errors.append("epistemic_ceiling.verbatim is absent from the source record")

    counterexamples = _exact_list(record.get("counterexamples"), "counterexamples", errors)
    seen_counterexamples: set[str] = set()
    counterexample_by_id: dict[str, tuple[dict[str, Any], list[str]]] = {}
    for index, raw in enumerate(counterexamples):
        field = f"counterexamples[{index}]"
        item = _exact_object(raw, _COUNTEREXAMPLE_KEYS, field, errors)
        if item is None:
            continue
        item_id = _string(item.get("counterexample_id"), f"{field}.counterexample_id", errors)
        _string(item.get("description"), f"{field}.description", errors)
        refs = source_refs(item.get("source_record_ids"), f"{field}.source_record_ids")
        status = item.get("status")
        history = _string_list(item.get("outcome_history"), f"{field}.outcome_history", errors, nonempty=True)
        if status == "OPEN":
            if history != ["FAIL"]:
                errors.append(f"{field} OPEN history must be exactly FAIL")
        elif status == "REMEDIATED":
            if history != ["FAIL", "REMEDIATION", "PASS"] or len(refs) < 2:
                errors.append(f"{field} must preserve FAIL/remediation/PASS and at least two sources")
        else:
            errors.append(f"{field}.status is not in the closed v0 set")
        if item_id is not None:
            if item_id in seen_counterexamples:
                errors.append(f"duplicate counterexample_id: {item_id}")
            seen_counterexamples.add(item_id)
            counterexample_by_id[item_id] = (item, refs)

    source_identities = {
        (source.get("git_commit"), source.get("path")) for source in source_by_id.values()
    }
    for counterexample_id, binding in _COUNTEREXAMPLE_BINDINGS.items():
        if binding["trigger_source"] not in source_identities:
            continue
        preserved = counterexample_by_id.get(counterexample_id)
        if preserved is None:
            errors.append(f"required counterexample is missing: {counterexample_id}")
            continue
        item, refs = preserved
        linked_identities = {
            (
                source_by_id.get(ref, {}).get("git_commit"),
                source_by_id.get(ref, {}).get("path"),
            )
            for ref in refs
        }
        if item.get("status") != binding["status"]:
            errors.append(f"required counterexample status changed: {counterexample_id}")
        if tuple(item.get("outcome_history", ())) != binding["outcome_history"]:
            errors.append(f"required counterexample history changed: {counterexample_id}")
        if not binding["required_sources"] <= linked_identities:
            errors.append(f"required counterexample provenance is incomplete: {counterexample_id}")

    assumptions = _exact_list(record.get("assumptions"), "assumptions", errors)
    seen_assumptions: set[str] = set()
    for index, raw in enumerate(assumptions):
        field = f"assumptions[{index}]"
        item = _exact_object(raw, _ASSUMPTION_KEYS, field, errors)
        if item is None:
            continue
        assumption_id = _string(item.get("assumption_id"), f"{field}.assumption_id", errors)
        _string(item.get("description"), f"{field}.description", errors)
        if item.get("status") not in {"UNKNOWN", "VERIFIED", "DISCHARGED"}:
            errors.append(f"{field}.status is not in the closed v0 set; UNKNOWN is not PASS")
        source_refs(item.get("source_record_ids"), f"{field}.source_record_ids")
        if assumption_id is not None:
            if assumption_id in seen_assumptions:
                errors.append(f"duplicate assumption_id: {assumption_id}")
            seen_assumptions.add(assumption_id)

    replay = _exact_object(record.get("replayability"), _REPLAY_KEYS, "replayability", errors)
    if replay is not None:
        if replay.get("status") not in {"UNKNOWN", "RECORDED", "REPLAYABLE", "NOT_REPLAYABLE"}:
            errors.append("replayability.status is not in the closed v0 set")
        source_refs(replay.get("source_record_ids"), "replayability.source_record_ids")
        if replay.get("independent_reproduction") != "NOT_CLAIMED":
            errors.append("replayability cannot establish independent reproduction")

    revisions = _exact_list(record.get("revision_provenance"), "revision_provenance", errors, nonempty=True)
    revision_ids: set[str] = set()
    for index, raw in enumerate(revisions):
        field = f"revision_provenance[{index}]"
        item = _exact_object(raw, _REVISION_KEYS, field, errors)
        if item is None:
            continue
        revision_id = _string(item.get("revision_id"), f"{field}.revision_id", errors)
        commit = _string(item.get("git_commit"), f"{field}.git_commit", errors)
        source_refs(item.get("source_record_ids"), f"{field}.source_record_ids")
        if commit is None or _SHA.fullmatch(commit) is None or _git(root, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            errors.append(f"{field}.git_commit is unresolved")
        if revision_id is not None:
            if revision_id in revision_ids:
                errors.append(f"duplicate revision_id: {revision_id}")
            revision_ids.add(revision_id)

    _string_list(record.get("limitations"), "limitations", errors, nonempty=True)
    nonclaims = _string_list(record.get("nonclaims"), "nonclaims", errors, nonempty=True)
    missing_nonclaims = _REQUIRED_NONCLAIMS - set(nonclaims)
    if missing_nonclaims:
        errors.append(f"required nonclaims are missing: {', '.join(sorted(missing_nonclaims))}")
    return tuple(errors)


def validation_status(record: Any, repository: str | Path) -> str:
    return VALID if not validate_record(record, repository) else INVALID


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate one PSM-v0 metadata record")
    parser.add_argument("record", type=Path)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    try:
        record = load_record(arguments.record)
        errors = validate_record(record, arguments.repository)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        errors = (str(exc),)
    print(json.dumps({"status": VALID if not errors else INVALID, "errors": list(errors)}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
