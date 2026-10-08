"""INR-XR-001 v0 provider trust anchor: GitHub Actions only (R3: artifact CONTENT binding).

This is the single provider-verification boundary for XR v0.

* The transport (``GitHubProvider``) issues HTTPS GET requests to the fixed origin
  ``https://api.github.com`` only, using a token read from the environment variable
  named by ``TOKEN_ENV``. Without a token it raises ``ProviderUnavailable`` BEFORE
  any network call is made. JSON endpoints refuse every redirect. The single
  artifact download endpoint follows exactly ONE redirect, as GitHub documents for
  ``GET /repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip`` (302 with a
  ``Location`` header to a short-lived signed storage URL). That redirect target
  must be HTTPS, on port 443, with no userinfo, on a host matching
  ``ARTIFACT_STORAGE_HOST`` (GitHub Actions artifact storage on Azure Blob,
  ``productionresultssa<N>.blob.core.windows.net``) and a path under
  ``/actions-results/``. The redirected request carries NO Authorization header,
  follows no further redirect, and is size-capped. No bundle-controlled URL and no
  generic URL fetching exist. No mock or offline mode exists in this module, and no
  argv, environment or file switch selects one. Unit tests pass their own
  trust-substitute object to ``verify_provider`` in-process. That object is never
  reachable from the CLI or from the verifier process, which always construct
  ``GitHubProvider.from_environment()``.
* The verification (``verify_provider``) treats every provider field in the bundle
  as a CLAIM. Authority comes from provider responses: the workflow run attempt,
  the claimed job, the run's artifact list, the artifact's own metadata, and the
  artifact's ZIP content.

BUNDLE-TO-RUN BINDING (the ONE v0 mechanism: GitHub artifact CONTENT verification):

1. The verified run's artifact list, queried by name ``inr-xr-bundle-<bundle_digest>``,
   must contain exactly one artifact of that name. ``bundle_digest`` is the SHA-256
   of the submitted ``external_run_manifest.json``.
2. The artifact ID comes only from that provider listing. The artifact metadata
   (``/actions/artifacts/{id}``) must repeat the same ID and name, name the verified
   run and head SHA, be unexpired and have a positive size, and have been created in
   the verified job window.
3. The ZIP is downloaded from the fixed endpoint for that ID. Its size must equal
   the provider ``size_in_bytes``. When the provider metadata carries
   ``digest: "sha256:<hex>"``, the ZIP SHA-256 must equal it.
4. The frozen content rule (``ARTIFACT_CONTENT_RULE``) is applied: the ZIP holds
   exactly ``external_run_manifest.json`` plus every path bound by its
   ``evidence_files``, as regular, unencrypted, stored/deflated file entries.
   Directory entries are allowed only for ancestors of those files. Anything else
   is FAIL: an extra, missing, duplicate (also case-folded), traversing, absolute,
   backslash or colon path, a symlink entry, an encrypted entry, or a size-cap
   breach. Every entry's bytes must equal the submitted bundle file byte for byte,
   so the manifest bytes, the raw file inventory and SHA-256 values, the event ID,
   the target SHA and the profile/origin digests are all bound.

PROVENANCE SCOPE: GitHub artifacts are RUN-scoped. The REST metadata names the
workflow run, not the producing job. The binding is therefore RUN-LEVEL. The
claimed job is compared with the provider's job record for consistency (same run,
attempt and head; runner name; hosted runner group; artifact and event times inside
that job's window), but the producing job is NOT authenticated: JOB_LEVEL provenance
is NOT_CLAIMED. Downstream predicates rely on the reviewed workflow at the expected
head SHA for which jobs exist.

This proves provenance only as far as GitHub and the reviewed workflow code at the
expected head SHA are trusted. It claims no hostile-host resistance.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import io
import json
import os
import re
import stat
import urllib.error
import urllib.parse
import urllib.request
import zipfile

API_ORIGIN = "https://api.github.com"
API_HOST = "api.github.com"
TOKEN_ENV = "INR_XR_GITHUB_TOKEN"
API_VERSION = "2022-11-28"
WORKFLOW_PATH = ".github/workflows/inr-xr-external-run.yml"
ARTIFACT_PREFIX = "inr-xr-bundle-"
HOSTED_RUNNER_GROUP = "GitHub Actions"
CLAIM_CLOCK_SKEW_SECONDS = 120
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_ARTIFACT_ENTRIES = 256
MAX_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
JOB_LEVEL_PROVENANCE = "NOT_CLAIMED"
ARTIFACT_STORAGE_HOST = re.compile(r"productionresultssa[0-9]{1,3}\.blob\.core\.windows\.net")
ARTIFACT_STORAGE_PATH_PREFIX = "/actions-results/"
MANIFEST_NAME = "external_run_manifest.json"
ARTIFACT_CONTENT_RULE = (
    "artifact ZIP = exactly external_run_manifest.json + every evidence_files path of that manifest; regular, "
    "unencrypted, stored/deflated file entries; ancestor directory entries only; each entry byte-identical to "
    "the submitted bundle file")
_REPO = r"/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/"
_PATH = re.compile(_REPO + r"(?:runs/[0-9]+/attempts/[0-9]+|jobs/[0-9]+|artifacts/[0-9]+|"
                           r"runs/[0-9]+/artifacts\?name=[A-Za-z0-9_.-]+)")
_ZIP_PATH = re.compile(_REPO + r"artifacts/[0-9]+/zip")
_SHA = re.compile(r"[0-9a-f]{40}")


class ProviderUnavailable(Exception):
    """Trusted provider data could not be obtained (no credential, network or response)."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderUnavailable("provider redirect refused")


class _CaptureRedirect(urllib.request.HTTPRedirectHandler):
    """Do not follow: the 302 surfaces as HTTPError so its Location can be vetted."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _storage_url(location):
    """The one accepted redirect target for an artifact ZIP, or ProviderUnavailable."""
    if type(location) is not str:
        raise ProviderUnavailable("artifact download redirect without Location")
    parts = urllib.parse.urlsplit(location)
    if (parts.scheme != "https" or parts.username is not None or parts.password is not None
            or parts.port not in (None, 443) or parts.hostname is None
            or ARTIFACT_STORAGE_HOST.fullmatch(parts.hostname) is None
            or not parts.path.startswith(ARTIFACT_STORAGE_PATH_PREFIX) or parts.fragment):
        raise ProviderUnavailable("artifact download redirect target outside the fixed storage allowlist")
    return location


def _read_capped(response, cap):
    data = response.read(cap + 1)
    if len(data) > cap:
        raise ProviderUnavailable("provider response too large")
    return data


class GitHubProvider:
    """Real provider boundary: HTTPS GET to the fixed api.github.com origin only."""

    def __init__(self, token):
        self._token = token if type(token) is str and token else None

    @classmethod
    def from_environment(cls):
        return cls(os.environ.get(TOKEN_ENV))

    def get_json(self, path):
        if self._token is None:
            raise ProviderUnavailable(f"no GitHub credential in {TOKEN_ENV}; provider not contacted")
        if type(path) is not str or _PATH.fullmatch(path) is None:
            raise ProviderUnavailable("provider path outside the fixed v0 endpoint set")
        request = urllib.request.Request(API_ORIGIN + path, method="GET", headers={
            "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": API_VERSION,
            "Authorization": "Bearer " + self._token, "User-Agent": "inr-xr-verifier-v0"})
        opener = urllib.request.build_opener(_NoRedirect())
        try:
            with opener.open(request, timeout=30) as response:
                final = urllib.parse.urlsplit(response.geturl())
                if response.status != 200 or final.scheme != "https" or final.hostname != API_HOST:
                    raise ProviderUnavailable("unexpected provider response origin/status")
                data = response.read(MAX_RESPONSE_BYTES + 1)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise ProviderUnavailable(f"provider request failed: {exc}") from None
        if len(data) > MAX_RESPONSE_BYTES:
            raise ProviderUnavailable("provider response too large")
        try:
            value = json.loads(data.decode("utf-8"))
        except (UnicodeError, ValueError):
            raise ProviderUnavailable("provider response is not JSON") from None
        if type(value) is not dict:
            raise ProviderUnavailable("provider response is not a JSON object")
        return value

    def get_artifact_zip(self, repository, artifact_id):
        """ZIP bytes of one artifact: fixed API endpoint, one vetted redirect, no token on the redirect."""
        if self._token is None:
            raise ProviderUnavailable(f"no GitHub credential in {TOKEN_ENV}; provider not contacted")
        path = f"/repos/{repository}/actions/artifacts/{artifact_id}/zip"
        if type(artifact_id) is not int or _ZIP_PATH.fullmatch(path) is None:
            raise ProviderUnavailable("artifact download path outside the fixed v0 endpoint")
        request = urllib.request.Request(API_ORIGIN + path, method="GET", headers={
            "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": API_VERSION,
            "Authorization": "Bearer " + self._token, "User-Agent": "inr-xr-verifier-v0"})
        try:
            with urllib.request.build_opener(_CaptureRedirect()).open(request, timeout=30) as response:
                raise ProviderUnavailable(f"artifact endpoint did not redirect (status {response.status})")
        except urllib.error.HTTPError as exc:
            if exc.code != 302:
                raise ProviderUnavailable(f"artifact download failed: HTTP {exc.code}") from None
            location = _storage_url(exc.headers.get("Location") if exc.headers is not None else None)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise ProviderUnavailable(f"artifact download failed: {exc}") from None
        storage = urllib.request.Request(location, method="GET", headers={"User-Agent": "inr-xr-verifier-v0"})
        try:
            with urllib.request.build_opener(_NoRedirect()).open(storage, timeout=60) as response:
                final = urllib.parse.urlsplit(response.geturl())
                if (response.status != 200 or final.scheme != "https" or final.hostname is None
                        or ARTIFACT_STORAGE_HOST.fullmatch(final.hostname) is None):
                    raise ProviderUnavailable("unexpected artifact storage response origin/status")
                return _read_capped(response, MAX_ARTIFACT_BYTES)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise ProviderUnavailable(f"artifact storage download failed: {exc}") from None


def _entry_problem(name):
    if not name or "\\" in name or "\0" in name or ":" in name or name.startswith("/"):
        return "absolute, drive, backslash or empty entry name"
    parts = name.rstrip("/").split("/") if name.endswith("/") else name.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return "path traversal or empty component"
    return None


def compare_artifact_content(zip_bytes, manifest_bytes, manifest, files):
    """Apply ARTIFACT_CONTENT_RULE. Returns {level: [messages]} (empty lists = bound)."""
    issues = {"blocked": [], "fail": [], "unconfirmed": []}
    expected = [MANIFEST_NAME] + [entry["path"] for entry in manifest["evidence_files"]]
    submitted = dict(files, **{MANIFEST_NAME: manifest_bytes})
    allowed_dirs = {"/".join(path.split("/")[:i]) + "/" for path in expected for i in range(1, path.count("/") + 1)}
    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
        infos = archive.infolist()
    except (zipfile.BadZipFile, ValueError, OSError) as exc:
        _issue(issues, "fail", f"artifact is not a readable ZIP archive: {exc}")
        return issues
    if len(infos) > MAX_ARTIFACT_ENTRIES or sum(i.file_size for i in infos) > MAX_UNCOMPRESSED_BYTES:
        _issue(issues, "fail", "artifact ZIP exceeds the entry/size cap")
        return issues
    seen, folded, content = set(), set(), {}
    for info in infos:
        name = info.filename
        problem = _entry_problem(name)
        if problem:
            _issue(issues, "fail", f"artifact entry rejected ({problem}): {name!r}")
            continue
        if name in seen or name.casefold() in folded:
            _issue(issues, "fail", f"duplicate artifact entry: {name}")
            continue
        seen.add(name)
        folded.add(name.casefold())
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            _issue(issues, "fail", f"symlink entry in artifact: {name}")
            continue
        if info.flag_bits & 0x1 or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
            _issue(issues, "fail", f"encrypted or unsupported artifact entry: {name}")
            continue
        if info.is_dir():
            if name not in allowed_dirs or info.file_size:
                _issue(issues, "fail", f"unexpected directory entry in artifact: {name}")
            continue
        if name not in expected:
            _issue(issues, "fail", f"extra artifact entry not bound by the manifest: {name}")
            continue
        try:
            with archive.open(info) as handle:
                data = handle.read(info.file_size + 1)
        except (zipfile.BadZipFile, ValueError, OSError, RuntimeError) as exc:
            _issue(issues, "fail", f"artifact entry unreadable: {name}: {exc}")
            continue
        if len(data) != info.file_size:
            _issue(issues, "fail", f"artifact entry size inconsistent: {name}")
            continue
        content[name] = data
    for name in expected:
        if name not in seen:
            _issue(issues, "fail", f"artifact lacks bundle file: {name}")
        elif name in content:
            local = submitted.get(name)
            if local is None:
                _issue(issues, "unconfirmed", f"submitted bundle lacks a file the artifact holds: {name}")
            elif hashlib.sha256(content[name]).digest() != hashlib.sha256(local).digest() or content[name] != local:
                _issue(issues, "fail", f"provider-held artifact content differs from the submitted bundle: {name}")
    return issues


def _time(value):
    if type(value) is not str:
        return None
    try:
        moment = _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        return None
    return moment.timestamp()


def _issue(issues, level, message):
    issues[level].append("provider: " + message)


def _bind_artifact(provider, binding, *, repository, artifact_id, name, run, head, listed, job_window,
                   bundle_content):
    """Artifact metadata + ZIP content binding (steps 2-4 of the binding). True only if bound."""
    job_started, job_completed = job_window
    try:
        meta = provider.get_json(f"/repos/{repository}/actions/artifacts/{artifact_id}")
    except ProviderUnavailable as exc:
        _issue(binding, "blocked", f"artifact metadata unavailable: {exc}")
        return False
    origin = meta.get("workflow_run") if type(meta.get("workflow_run")) is dict else {}
    listed_origin = listed.get("workflow_run") if type(listed.get("workflow_run")) is dict else {}
    created = _time(meta.get("created_at"))
    size = meta.get("size_in_bytes")
    for failed, message in (
            (meta.get("id") != artifact_id or meta.get("name") != name, "artifact metadata is not the listed artifact"),
            (origin.get("id") != run.get("id") or origin.get("head_sha") != head
             or listed_origin.get("id") != run.get("id") or listed_origin.get("head_sha") != head,
             "bundle artifact belongs to another run/commit"),
            (created is None or job_started is None or job_completed is None
             or not job_started <= created <= job_completed,
             "bundle artifact not created inside the claimed job window")):
        if failed:
            _issue(binding, "fail", message)
    if meta.get("expired") is not False or listed.get("expired") is not False or type(size) is not int or size <= 0:
        _issue(binding, "unconfirmed", "bundle artifact expired, deleted or empty")
    if binding["fail"] or binding["unconfirmed"]:
        return False
    if bundle_content is None:
        _issue(binding, "unconfirmed", "submitted bundle content not available for comparison")
        return False
    try:
        data = provider.get_artifact_zip(repository, artifact_id)
    except ProviderUnavailable as exc:
        _issue(binding, "blocked", f"provider-held artifact content unavailable: {exc}")
        return False
    if type(data) is not bytes or len(data) != size:
        _issue(binding, "fail", "downloaded artifact size differs from the provider metadata")
        return False
    provider_digest = meta.get("digest")
    if provider_digest is not None and provider_digest != "sha256:" + hashlib.sha256(data).hexdigest():
        _issue(binding, "fail", "downloaded artifact digest differs from the provider metadata")
        return False
    manifest_bytes, manifest, files = bundle_content
    issues = compare_artifact_content(data, manifest_bytes, manifest, files)
    for level in ("blocked", "fail", "unconfirmed"):
        binding[level].extend(issues[level])
    return not any(issues.values())


def verify_provider(provider, claims, *, repository, bundle_digest, expected_head_sha, not_before,
                    event_window, bundle_content=None):
    """Verify the bundle's GitHub claims against authoritative provider data.

    The arguments are:

    * ``claims``: the bundle's runner identity (claims only).
    * ``repository``: the trusted repository from the committed origin set.
    * ``bundle_digest``: computed by the adapter from the submitted manifest.
    * ``expected_head_sha`` and ``not_before``: operator parameters.
    * ``event_window``: the bundle's event start/complete times (seconds).
    * ``bundle_content``: ``(manifest_bytes, manifest, files)`` of the submitted bundle,
      as admitted by the adapter, compared with the provider-held artifact content.

    Returns ``{"provenance": {level: [...]}, "binding": {level: [...]}, "run": dict | None}``.
    An empty issue map with ``run`` set means the check is verified.
    """
    provenance = {"blocked": [], "fail": [], "unconfirmed": []}
    binding = {"blocked": [], "fail": [], "unconfirmed": []}
    out = {"provenance": provenance, "binding": binding, "run": None}
    if provider is None:
        _issue(provenance, "unconfirmed", "no trusted provider verification performed (bundle claims only)")
        _issue(binding, "unconfirmed", "bundle not bound to a provider-verified run")
        return out
    if claims is None:
        _issue(provenance, "unconfirmed", "runner identity claims not admitted; nothing to verify")
        _issue(binding, "unconfirmed", "bundle not bound to a provider-verified run")
        return out
    if expected_head_sha is None or _SHA.fullmatch(str(expected_head_sha)) is None:
        _issue(provenance, "unconfirmed", "no operator-designated workflow head SHA")
    if not_before is None:
        _issue(provenance, "unconfirmed", "no operator not-before time; provider run staleness not excluded")
    if claims.get("provider") != "github-actions":
        _issue(provenance, "unconfirmed", "only GitHub Actions is supported in v0")
        _issue(binding, "unconfirmed", "bundle not bound to a provider-verified run")
        return out
    run_id, attempt, job_id = claims["workflow_run_id"], claims["workflow_run_attempt"], claims["job_id"]
    if not re.fullmatch(r"[0-9]+", job_id):
        _issue(provenance, "unconfirmed", "job ID claim is not a GitHub job ID")
        _issue(binding, "unconfirmed", "bundle not bound to a provider-verified run")
        return out
    base = f"/repos/{repository}/actions"
    try:
        run = provider.get_json(f"{base}/runs/{run_id}/attempts/{attempt}")
        job = provider.get_json(f"{base}/jobs/{job_id}")
        artifacts = provider.get_json(f"{base}/runs/{run_id}/artifacts?name={ARTIFACT_PREFIX}{bundle_digest}")
    except ProviderUnavailable as exc:
        _issue(provenance, "blocked", f"trusted GitHub metadata unavailable: {exc}")
        _issue(binding, "blocked", "bundle-to-run binding not verifiable without provider data")
        return out
    repo = run.get("repository") if type(run.get("repository")) is dict else {}
    head = run.get("head_sha")
    run_created, run_started = _time(run.get("created_at")), _time(run.get("run_started_at"))
    job_started, job_completed = _time(job.get("started_at")), _time(job.get("completed_at"))
    checks_fail = (
        (repo.get("full_name") != repository, "run repository is not the trusted repository"),
        (claims["repository"] != repository, "claimed repository is not the trusted repository"),
        (str(run.get("id")) != run_id or run.get("run_attempt") != attempt,
         "provider run/attempt differs from the claimed run"),
        (head != claims["head_sha"], "provider head SHA differs from the claimed head SHA"),
        (expected_head_sha is not None and head != expected_head_sha,
         "provider head SHA differs from the operator-designated workflow commit"),
        (run.get("path") != WORKFLOW_PATH, "run workflow is not the INR-XR workflow"),
        (claims["workflow_path"] != WORKFLOW_PATH, "claimed workflow path is not the INR-XR workflow"),
        (str(job.get("id")) != job_id, "provider job differs from the claimed job"),
        (job.get("run_id") != run.get("id") or job.get("run_attempt") != attempt,
         "provider job belongs to another run/attempt"),
        (job.get("head_sha") != head, "provider job head SHA differs from the run"),
        (job.get("runner_name") != claims["runner_name"], "provider runner name differs from the claim"),
        (job.get("runner_group_name") != HOSTED_RUNNER_GROUP, "provider job did not run on a GitHub-hosted runner"),
    )
    for failed, message in checks_fail:
        if failed:
            _issue(provenance, "fail", message)
    if run.get("status") != "completed" or run.get("conclusion") != "success" \
            or job.get("status") != "completed" or job.get("conclusion") != "success":
        _issue(provenance, "unconfirmed", "provider run/job not completed successfully")
    if None in (run_created, run_started, job_started, job_completed):
        _issue(provenance, "unconfirmed", "provider timestamps missing")
    else:
        if not run_created <= run_started <= job_started <= job_completed:
            _issue(provenance, "fail", "provider timestamps out of order")
        if not_before is not None and run_created < not_before:
            _issue(provenance, "unconfirmed", "provider run predates the operator's run request (stale run)")
        claimed_start = _time(claims["job_started_at"])
        if claimed_start is None or not (job_started - CLAIM_CLOCK_SKEW_SECONDS <= claimed_start <= job_completed):
            _issue(provenance, "fail", "claimed job start contradicts the provider job window")
        started, completed = event_window
        if started is None or completed is None:
            _issue(provenance, "unconfirmed", "bundle event window not established; not placed in the job window")
        elif not job_started <= started <= completed <= job_completed:
            _issue(provenance, "fail", "event times lie outside the provider-verified job window")
    listed = artifacts.get("artifacts") if type(artifacts.get("artifacts")) is list else None
    name = ARTIFACT_PREFIX + str(bundle_digest)
    matching = [a for a in (listed or []) if type(a) is dict and a.get("name") == name]
    artifact_id = None
    if listed is None:
        _issue(binding, "unconfirmed", "provider artifact list unavailable")
    elif len(matching) != 1:
        _issue(binding, "unconfirmed", "no unique provider artifact carries the submitted bundle digest")
    else:
        artifact_id = matching[0].get("id")
        if type(artifact_id) is not int or artifact_id <= 0:
            _issue(binding, "fail", "provider artifact listing carries no artifact ID")
            artifact_id = None
    content_bound = False
    if artifact_id is not None:
        content_bound = _bind_artifact(provider, binding, repository=repository, artifact_id=artifact_id,
                                       name=name, run=run, head=head, listed=matching[0],
                                       job_window=(job_started, job_completed), bundle_content=bundle_content)
    if provenance["fail"] or provenance["blocked"]:
        if not binding["fail"] and not binding["blocked"]:
            _issue(binding, "unconfirmed", "binding refers to an unverified run")
    out["run"] = {"repository": repo.get("full_name"), "run_id": run.get("id"), "run_attempt": run.get("run_attempt"),
                  "head_sha": head, "workflow_path": run.get("path"), "run_created_at": run.get("created_at"),
                  "provenance_scope": "RUN_LEVEL", "job_level_provenance": JOB_LEVEL_PROVENANCE,
                  "claimed_job_id": job.get("id"), "claimed_job_started_at": job.get("started_at"),
                  "claimed_job_completed_at": job.get("completed_at"), "claimed_job_runner_name": job.get("runner_name"),
                  "claimed_job_runner_group_name": job.get("runner_group_name"), "claimed_job_labels": job.get("labels"),
                  "claimed_job_status": job.get("status"), "claimed_job_conclusion": job.get("conclusion"),
                  "artifact_id": artifact_id if content_bound else None,
                  "artifact_content_bound": content_bound,
                  "artifact_name": name if content_bound else None}
    return out
