"""Append-only attempt storage, status-last transaction, and state derivation."""

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from wvma_v1.canonical import (
    canonical_bytes,
    canonical_digest,
    digest_excluding_field,
    sha256_file,
)
from wvma_v1.models import (
    ABSENT,
    AttemptState,
    AttemptVerdict,
    CaseResult,
    Catalog,
    CatalogError,
    ResultClass,
    SchemaError,
    WVMAStatus,
    build_status,
    critical_acceptance_blocks,
    strict_parse_case_result,
    strict_parse_catalog,
    strict_parse_status,
)

ATTEMPT_INTENT_SCHEMA_VERSION = "wvma_v1.attempt_intent.v1"
FINALIZE_INTENT_SCHEMA_VERSION = "wvma_v1.finalize_intent.v1"


class StateError(ValueError):
    """Invalid attempt/state transition or storage error."""


class ReplayError(StateError):
    """Duplicate attempt/result/replay rejection."""


def _utc_now_basic() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def make_attempt_id(*, when: datetime | None = None, nonce: str | None = None) -> str:
    ts = (when or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    token = nonce or secrets.token_hex(4)
    if len(token) != 8 or any(c not in "0123456789abcdef" for c in token):
        raise StateError("nonce must be 8 lowercase hex characters")
    return f"WVMA-{ts}-{token}"


def _write_exclusive_bytes(path: Path, data: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ReplayError(f"destination exists; exclusive create rejected: {path}")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        fd = os.open(str(path), flags, 0o644)
    except FileExistsError as exc:
        raise ReplayError(
            f"destination exists; exclusive create rejected: {path}"
        ) from exc
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    # Best-effort directory durability after exclusive create.
    try:
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def write_exclusive_json(path: Path, obj: Mapping[str, Any]) -> None:
    _write_exclusive_bytes(Path(path), canonical_bytes(obj))


def _mkdir_exclusive(path: Path) -> None:
    path = Path(path)
    try:
        path.mkdir(parents=False, exist_ok=False)
    except FileExistsError as exc:
        raise ReplayError(
            f"attempt directory exists; exclusive create rejected: {path}"
        ) from exc
    except FileNotFoundError:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.mkdir(parents=False, exist_ok=False)
        except FileExistsError as exc:
            raise ReplayError(
                f"attempt directory exists; exclusive create rejected: {path}"
            ) from exc


def catalogs_dir(out_root: Path) -> Path:
    return Path(out_root) / "catalogs"


def attempts_dir(out_root: Path) -> Path:
    return Path(out_root) / "attempts"


def attempt_dir(out_root: Path, attempt_id: str) -> Path:
    return attempts_dir(out_root) / attempt_id


def catalog_path(out_root: Path, catalog_digest: str) -> Path:
    return catalogs_dir(out_root) / f"{catalog_digest}.json"


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def sealed_catalog_digests(out_root: Path) -> list[str]:
    root = catalogs_dir(out_root)
    if not root.is_dir():
        return []
    digests = []
    for path in sorted(root.glob("*.json")):
        digests.append(path.stem)
    return digests


def seal_catalog(out_root: Path, catalog: Catalog | Mapping[str, Any] | Path) -> Catalog:
    """Seal catalog bytes under <out>/catalogs/<catalog_digest>.json."""
    if isinstance(catalog, Path):
        raw = load_json(catalog)
        parsed = strict_parse_catalog(raw)
    elif isinstance(catalog, Catalog):
        parsed = catalog
    else:
        parsed = strict_parse_catalog(catalog)

    out_root = Path(out_root)
    dest = catalog_path(out_root, parsed.catalog_digest)
    write_exclusive_json(dest, parsed.to_dict())
    # Re-read to ensure sealed bytes parse and digest-match path name.
    sealed = strict_parse_catalog(load_json(dest))
    if sealed.catalog_digest != dest.stem:
        raise CatalogError("sealed catalog path digest mismatch")
    return sealed


def load_sealed_catalog(out_root: Path, catalog_digest: str) -> Catalog:
    path = catalog_path(out_root, catalog_digest)
    if not path.is_file():
        raise StateError(f"catalog not sealed: {catalog_digest}")
    catalog = strict_parse_catalog(load_json(path))
    if catalog.catalog_digest != catalog_digest:
        raise CatalogError("sealed catalog digest mismatch")
    file_digest = sha256_file(path)
    # Path is content-addressed by catalog_digest (self-digest), not raw file hash.
    if catalog.catalog_digest != digest_excluding_field(
        catalog.to_dict(), "catalog_digest"
    ):
        raise CatalogError("sealed catalog self-digest invalid")
    _ = file_digest
    return catalog


def _attempt_intent_body(
    *,
    attempt_id: str,
    catalog: Catalog,
    source_revision: str,
    runner_digest: str,
    oracle_digest: str,
    baseline_receipt_digest: str,
    protected_path_inventory_digest: str,
    started_at: str,
    prior_attempt_id: str | None = ABSENT,
    prior_attempt_root_digest: str | None = ABSENT,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": ATTEMPT_INTENT_SCHEMA_VERSION,
        "authority": False,
        "attempt_id": attempt_id,
        "catalog_id": catalog.catalog_id,
        "catalog_digest": catalog.catalog_digest,
        "product_base_sha": catalog.product_base_sha,
        "source_revision": source_revision,
        "runner_digest": runner_digest,
        "oracle_digest": oracle_digest,
        "baseline_receipt_digest": baseline_receipt_digest,
        "protected_path_inventory_digest": protected_path_inventory_digest,
        "started_at": started_at,
    }
    if prior_attempt_id is not ABSENT:
        if not isinstance(prior_attempt_id, str) or not prior_attempt_id:
            raise StateError("prior_attempt_id PRESENT-invalid")
        body["prior_attempt_id"] = prior_attempt_id
    if prior_attempt_root_digest is not ABSENT:
        if (
            not isinstance(prior_attempt_root_digest, str)
            or len(prior_attempt_root_digest) != 64
        ):
            raise StateError("prior_attempt_root_digest PRESENT-invalid")
        body["prior_attempt_root_digest"] = prior_attempt_root_digest
    return body


def create_attempt(
    out_root: Path,
    *,
    catalog_digest: str,
    source_revision: str,
    runner_digest: str,
    oracle_digest: str,
    baseline_receipt_digest: str,
    protected_path_inventory_digest: str,
    attempt_id: str | None = None,
    prior_attempt_id: str | None = ABSENT,
    prior_attempt_root_digest: str | None = ABSENT,
) -> dict[str, Any]:
    out_root = Path(out_root)
    catalog = load_sealed_catalog(out_root, catalog_digest)
    aid = attempt_id or make_attempt_id()
    if not aid.startswith("WVMA-"):
        raise StateError("attempt_id must use WVMA-<UTC_BASIC>-<8_HEX_NONCE>")
    root = attempt_dir(out_root, aid)
    _mkdir_exclusive(root)
    (root / "results").mkdir(parents=False, exist_ok=False)
    intent = _attempt_intent_body(
        attempt_id=aid,
        catalog=catalog,
        source_revision=source_revision,
        runner_digest=runner_digest,
        oracle_digest=oracle_digest,
        baseline_receipt_digest=baseline_receipt_digest,
        protected_path_inventory_digest=protected_path_inventory_digest,
        started_at=_utc_now_iso(),
        prior_attempt_id=prior_attempt_id,
        prior_attempt_root_digest=prior_attempt_root_digest,
    )
    write_exclusive_json(root / "ATTEMPT_INTENT.json", intent)
    return intent


def _read_attempt_intent(out_root: Path, attempt_id: str) -> dict[str, Any]:
    path = attempt_dir(out_root, attempt_id) / "ATTEMPT_INTENT.json"
    if not path.is_file():
        raise StateError(f"ATTEMPT_INTENT missing for {attempt_id}")
    data = load_json(path)
    if not isinstance(data, Mapping):
        raise StateError("ATTEMPT_INTENT PRESENT-invalid")
    if data.get("attempt_id") != attempt_id:
        raise StateError("ATTEMPT_INTENT attempt_id mismatch")
    if data.get("authority") is not False:
        raise StateError("ATTEMPT_INTENT authority must be false")
    if data.get("schema_version") != ATTEMPT_INTENT_SCHEMA_VERSION:
        raise StateError("ATTEMPT_INTENT schema_version invalid")
    return dict(data)


def list_published_results(out_root: Path, attempt_id: str) -> dict[str, CaseResult]:
    root = attempt_dir(out_root, attempt_id) / "results"
    published: dict[str, CaseResult] = {}
    if not root.is_dir():
        return published
    for case_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        files = sorted(case_dir.glob("*.json"))
        if len(files) != 1:
            raise StateError(
                f"case result directory must contain exactly one file: {case_dir}"
            )
        result = strict_parse_case_result(load_json(files[0]))
        if result.case_id != case_dir.name:
            raise StateError("result case_id does not match directory")
        if result.result_digest != files[0].stem:
            raise StateError("result digest does not match filename")
        if result.attempt_id != attempt_id:
            raise StateError("result attempt_id mismatch")
        published[result.case_id] = result
    return published


def compute_attempt_root_digest(out_root: Path, attempt_id: str) -> str:
    """Digest over ATTEMPT_INTENT and immutable case-result files only."""
    root = attempt_dir(out_root, attempt_id)
    intent_path = root / "ATTEMPT_INTENT.json"
    if not intent_path.is_file():
        raise StateError("cannot compute attempt-root digest without ATTEMPT_INTENT")
    entries: dict[str, str] = {
        "ATTEMPT_INTENT.json": sha256_file(intent_path),
    }
    results_root = root / "results"
    if results_root.is_dir():
        for path in sorted(results_root.rglob("*.json")):
            rel = path.relative_to(root).as_posix()
            entries[rel] = sha256_file(path)
    # Explicitly exclude finalize/status even if present.
    return canonical_digest(entries)


def publish_case_result(
    out_root: Path,
    attempt_id: str,
    result: CaseResult | Mapping[str, Any],
) -> CaseResult:
    out_root = Path(out_root)
    intent = _read_attempt_intent(out_root, attempt_id)
    if (attempt_dir(out_root, attempt_id) / "FINALIZE_INTENT.json").exists():
        raise StateError("cannot publish results after FINALIZE_INTENT")
    parsed = (
        result
        if isinstance(result, CaseResult)
        else strict_parse_case_result(result)
    )
    if parsed.attempt_id != attempt_id:
        raise StateError("result attempt_id mismatch")
    if parsed.catalog_digest != intent["catalog_digest"]:
        raise ReplayError("foreign catalog case rejected")
    catalog = load_sealed_catalog(out_root, intent["catalog_digest"])
    try:
        mutation = catalog.mutation_by_case_id(parsed.case_id)
    except CatalogError as exc:
        raise ReplayError("foreign catalog case rejected") from exc
    if parsed.property_id != mutation.property_id:
        raise StateError("result property_id does not match catalog mutation")

    case_dir = attempt_dir(out_root, attempt_id) / "results" / parsed.case_id
    try:
        case_dir.mkdir(parents=False, exist_ok=False)
    except FileExistsError as exc:
        raise ReplayError(
            f"duplicate case publication rejected: {parsed.case_id}"
        ) from exc
    dest = case_dir / f"{parsed.result_digest}.json"
    write_exclusive_json(dest, parsed.to_dict())
    return parsed


def write_finalize_intent(
    out_root: Path,
    attempt_id: str,
    *,
    intended_status_digest: str,
    result_references: list[dict[str, str]],
    attempt_root_digest: str,
) -> dict[str, Any]:
    root = attempt_dir(out_root, attempt_id)
    if not (root / "ATTEMPT_INTENT.json").is_file():
        raise StateError("FINALIZE_INTENT requires ATTEMPT_INTENT")
    if (root / "WVMA_STATUS.json").exists():
        raise StateError("cannot write FINALIZE_INTENT after WVMA_STATUS")
    refs = sorted(
        [{"case_id": r["case_id"], "result_digest": r["result_digest"]} for r in result_references],
        key=lambda x: x["case_id"],
    )
    body = {
        "schema_version": FINALIZE_INTENT_SCHEMA_VERSION,
        "authority": False,
        "attempt_id": attempt_id,
        "attempt_root_digest": attempt_root_digest,
        "intended_status_digest": intended_status_digest,
        "result_references": refs,
    }
    write_exclusive_json(root / "FINALIZE_INTENT.json", body)
    return body


def _compute_verdict_and_blockers(
    catalog: Catalog,
    results: Mapping[str, CaseResult],
) -> tuple[AttemptState, AttemptVerdict | None, list[str], dict[str, int]]:
    counts = {cls.value: 0 for cls in ResultClass}
    blockers: list[str] = []
    missing_critical: list[str] = []

    for case_id in catalog.critical_case_ids:
        result = results.get(case_id)
        if result is None:
            missing_critical.append(case_id)
            counts[ResultClass.MISSING_RESULT.value] += 1
            blockers.append(case_id)
            continue
        counts[result.result_class.value] += 1
        if critical_acceptance_blocks(result.result_class):
            blockers.append(case_id)

    # Non-critical published results still counted.
    for case_id, result in results.items():
        if case_id in catalog.critical_case_ids:
            continue
        counts[result.result_class.value] += 1

    if missing_critical:
        # Incomplete critical coverage cannot be COMPLETE.
        return AttemptState.RUN_INCOMPLETE, None, sorted(set(blockers)), counts

    if blockers:
        return (
            AttemptState.RUN_COMPLETE,
            AttemptVerdict.CRITICAL_SURVIVOR,
            sorted(set(blockers)),
            counts,
        )
    return (
        AttemptState.RUN_COMPLETE,
        AttemptVerdict.ALL_CRITICAL_DETECTED,
        [],
        counts,
    )


def finalize_attempt(
    out_root: Path,
    attempt_id: str,
    *,
    completed_at: str | None = None,
    force_state: AttemptState | None = None,
) -> WVMAStatus:
    """Status-last transaction: FINALIZE_INTENT then WVMA_STATUS."""
    out_root = Path(out_root)
    intent = _read_attempt_intent(out_root, attempt_id)
    root = attempt_dir(out_root, attempt_id)
    if (root / "FINALIZE_INTENT.json").exists() or (root / "WVMA_STATUS.json").exists():
        raise ReplayError("finalize already started or completed")

    catalog = load_sealed_catalog(out_root, intent["catalog_digest"])
    results = list_published_results(out_root, attempt_id)
    attempt_root = compute_attempt_root_digest(out_root, attempt_id)
    state, verdict, blockers, counts = _compute_verdict_and_blockers(catalog, results)
    if force_state is not None:
        state = force_state
        if state != AttemptState.RUN_COMPLETE:
            verdict = None
    refs = [
        {"case_id": case_id, "result_digest": result.result_digest}
        for case_id, result in sorted(results.items())
    ]
    status = build_status(
        attempt_id=attempt_id,
        catalog_digest=intent["catalog_digest"],
        source_revision=intent["source_revision"],
        runner_digest=intent["runner_digest"],
        oracle_digest=intent["oracle_digest"],
        state=state,
        verdict=verdict if verdict is not None else ABSENT,
        baseline_receipt_digest=intent["baseline_receipt_digest"],
        case_result_digests=refs,
        result_counts={k: v for k, v in counts.items() if v},
        blocking_case_ids=blockers,
        attempt_root_digest=attempt_root,
        completed_at=completed_at or _utc_now_iso(),
    )
    write_finalize_intent(
        out_root,
        attempt_id,
        intended_status_digest=status.status_digest,
        result_references=refs,
        attempt_root_digest=attempt_root,
    )
    write_exclusive_json(root / "WVMA_STATUS.json", status.to_dict())
    return status


def _status_matches_finalize(
    status: WVMAStatus,
    finalize: Mapping[str, Any],
    attempt_root: str,
) -> bool:
    if status.status_digest != finalize.get("intended_status_digest"):
        return False
    if status.attempt_root_digest != finalize.get("attempt_root_digest"):
        return False
    if attempt_root != status.attempt_root_digest:
        return False
    refs = [
        {"case_id": x["case_id"], "result_digest": x["result_digest"]}
        for x in status.case_result_digests
    ]
    intent_refs = list(finalize.get("result_references") or [])
    return refs == intent_refs


def derive_attempt_state(
    out_root: Path,
    attempt_id: str | None = None,
) -> AttemptState:
    out_root = Path(out_root)
    sealed = sealed_catalog_digests(out_root)
    if not sealed:
        return AttemptState.NOT_CONFIGURED
    if attempt_id is None:
        return AttemptState.CATALOG_SEALED

    root = attempt_dir(out_root, attempt_id)
    if not root.exists():
        return AttemptState.CATALOG_SEALED

    intent_path = root / "ATTEMPT_INTENT.json"
    finalize_path = root / "FINALIZE_INTENT.json"
    status_path = root / "WVMA_STATUS.json"

    if not intent_path.is_file():
        return AttemptState.RUN_INVALID

    try:
        _read_attempt_intent(out_root, attempt_id)
    except (StateError, SchemaError, json.JSONDecodeError, OSError):
        return AttemptState.RUN_INVALID

    if status_path.is_file() and not finalize_path.is_file():
        return AttemptState.RUN_INVALID

    if finalize_path.is_file():
        try:
            finalize = load_json(finalize_path)
            if not isinstance(finalize, Mapping):
                return AttemptState.RUN_INVALID
            attempt_root = compute_attempt_root_digest(out_root, attempt_id)
        except (StateError, SchemaError, json.JSONDecodeError, OSError):
            return AttemptState.RUN_INVALID

        if not status_path.is_file():
            # Status-last: deleted/missing status after finalize is INCOMPLETE,
            # never a downgrade to RUN_IN_PROGRESS.
            return AttemptState.RUN_INCOMPLETE

        try:
            status = strict_parse_status(load_json(status_path))
            list_published_results(out_root, attempt_id)
        except (StateError, SchemaError, json.JSONDecodeError, OSError):
            return AttemptState.RUN_INCOMPLETE

        if status.attempt_id != attempt_id:
            return AttemptState.RUN_INVALID
        if not _status_matches_finalize(status, finalize, attempt_root):
            return AttemptState.RUN_INCOMPLETE
        return status.state

    # Intent present, no finalize.
    try:
        list_published_results(out_root, attempt_id)
    except (StateError, SchemaError, json.JSONDecodeError, OSError):
        return AttemptState.RUN_INVALID
    return AttemptState.RUN_IN_PROGRESS


def verify_attempt(out_root: Path, attempt_id: str) -> AttemptState:
    state = derive_attempt_state(out_root, attempt_id)
    if state == AttemptState.RUN_INVALID:
        raise StateError(f"attempt {attempt_id} is RUN_INVALID")
    if state == AttemptState.RUN_INCOMPLETE:
        raise StateError(f"attempt {attempt_id} is RUN_INCOMPLETE")
    if state == AttemptState.RUN_IN_PROGRESS:
        raise StateError(f"attempt {attempt_id} is still RUN_IN_PROGRESS")
    if state != AttemptState.RUN_COMPLETE:
        raise StateError(f"attempt {attempt_id} state={state.value}")
    root = attempt_dir(out_root, attempt_id)
    status = strict_parse_status(load_json(root / "WVMA_STATUS.json"))
    if status.verdict not in {
        AttemptVerdict.ALL_CRITICAL_DETECTED,
        AttemptVerdict.CRITICAL_SURVIVOR,
    }:
        raise StateError("RUN_COMPLETE requires valid verdict")
    return state


def create_recovery_attempt(
    out_root: Path,
    prior_attempt_id: str,
    *,
    attempt_id: str | None = None,
) -> dict[str, Any]:
    """Create a NEW attempt bound to the prior attempt's immutable root digest."""
    out_root = Path(out_root)
    prior_root = attempt_dir(out_root, prior_attempt_id)
    if not prior_root.is_dir():
        raise StateError(f"prior attempt missing: {prior_attempt_id}")

    # Snapshot prior bytes before recovery; recovery must not mutate them.
    prior_files = {
        p.relative_to(prior_root).as_posix(): sha256_file(p)
        for p in sorted(prior_root.rglob("*"))
        if p.is_file()
    }
    prior_intent = _read_attempt_intent(out_root, prior_attempt_id)
    prior_attempt_root = compute_attempt_root_digest(out_root, prior_attempt_id)

    new_intent = create_attempt(
        out_root,
        catalog_digest=prior_intent["catalog_digest"],
        source_revision=prior_intent["source_revision"],
        runner_digest=prior_intent["runner_digest"],
        oracle_digest=prior_intent["oracle_digest"],
        baseline_receipt_digest=prior_intent["baseline_receipt_digest"],
        protected_path_inventory_digest=prior_intent[
            "protected_path_inventory_digest"
        ],
        attempt_id=attempt_id,
        prior_attempt_id=prior_attempt_id,
        prior_attempt_root_digest=prior_attempt_root,
    )

    after_files = {
        p.relative_to(prior_root).as_posix(): sha256_file(p)
        for p in sorted(prior_root.rglob("*"))
        if p.is_file()
    }
    if after_files != prior_files:
        raise StateError("recovery mutated prior attempt bytes")
    return new_intent
