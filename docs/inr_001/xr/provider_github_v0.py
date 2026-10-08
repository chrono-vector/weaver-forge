"""INR-XR-001 v0 provider trust anchor: GitHub Actions only.

This is the single provider-verification boundary for XR v0.

* The transport (``GitHubProvider``) issues HTTPS GET requests to the fixed origin
  ``https://api.github.com`` only. It uses a token read from the environment
  variable named by ``TOKEN_ENV`` and refuses redirects. Without a token it raises
  ``ProviderUnavailable`` BEFORE any network call is made. No mock or offline mode
  exists in this module, and no argv, environment or file switch selects one. Unit
  tests pass their own trust-substitute object to ``verify_provider`` in-process.
  That object is never reachable from the CLI or from the verifier process, which
  always construct ``GitHubProvider.from_environment()``.
* The verification (``verify_provider``) treats every provider field in the bundle
  as a CLAIM. Authority comes from three provider responses: the workflow run
  attempt, the job, and the run's artifact list.

Bundle-to-run binding (the ONE v0 mechanism): the workflow job uploads the bundle as
a GitHub Actions artifact named ``inr-xr-bundle-<bundle_digest>``, where
``bundle_digest`` is the SHA-256 of ``external_run_manifest.json``. The manifest
binds every raw file by SHA-256. The verifier lists the verified run's artifacts
through the provider API and requires exactly one such artifact. That artifact must
belong to the verified run and head SHA, must not be expired or empty, and must have
been created inside the verified job's time window. Only a job of that run can
create artifacts in it, and the artifact name is computed by the workflow code at
the verified head SHA.

This proves provenance only as far as GitHub and the reviewed workflow code at the
expected head SHA are trusted. It claims no hostile-host resistance.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

API_ORIGIN = "https://api.github.com"
API_HOST = "api.github.com"
TOKEN_ENV = "INR_XR_GITHUB_TOKEN"
API_VERSION = "2022-11-28"
WORKFLOW_PATH = ".github/workflows/inr-xr-external-run.yml"
ARTIFACT_PREFIX = "inr-xr-bundle-"
HOSTED_RUNNER_GROUP = "GitHub Actions"
CLAIM_CLOCK_SKEW_SECONDS = 120
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
_PATH = re.compile(r"/repos/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/"
                   r"(?:runs/[0-9]+/attempts/[0-9]+|jobs/[0-9]+|runs/[0-9]+/artifacts\?name=[A-Za-z0-9_.-]+)")
_SHA = re.compile(r"[0-9a-f]{40}")


class ProviderUnavailable(Exception):
    """Trusted provider data could not be obtained (no credential, network or response)."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderUnavailable("provider redirect refused")


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


def verify_provider(provider, claims, *, repository, bundle_digest, expected_head_sha, not_before,
                    event_window):
    """Verify the bundle's GitHub claims against authoritative provider data.

    The arguments are:

    * ``claims``: the bundle's runner identity (claims only).
    * ``repository``: the trusted repository from the committed origin set.
    * ``bundle_digest``: computed by the adapter from the submitted manifest.
    * ``expected_head_sha`` and ``not_before``: operator parameters.
    * ``event_window``: the bundle's event start/complete times (seconds).

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
    if listed is None:
        _issue(binding, "unconfirmed", "provider artifact list unavailable")
    elif len(matching) != 1:
        _issue(binding, "unconfirmed", "no unique provider artifact carries the submitted bundle digest")
    else:
        artifact = matching[0]
        origin = artifact.get("workflow_run") if type(artifact.get("workflow_run")) is dict else {}
        created = _time(artifact.get("created_at"))
        if origin.get("id") != run.get("id") or origin.get("head_sha") != head:
            _issue(binding, "fail", "bundle artifact belongs to another run/commit")
        if artifact.get("expired") is not False or type(artifact.get("size_in_bytes")) is not int \
                or artifact["size_in_bytes"] <= 0:
            _issue(binding, "unconfirmed", "bundle artifact expired or empty")
        if created is None or job_started is None or job_completed is None \
                or not (job_started <= created <= job_completed):
            _issue(binding, "fail", "bundle artifact not created inside the verified job window")
    if provenance["fail"] or provenance["blocked"]:
        if not binding["fail"] and not binding["blocked"]:
            _issue(binding, "unconfirmed", "binding refers to an unverified run")
    out["run"] = {"repository": repo.get("full_name"), "run_id": run.get("id"), "run_attempt": run.get("run_attempt"),
                  "job_id": job.get("id"), "head_sha": head, "workflow_path": run.get("path"),
                  "run_created_at": run.get("created_at"), "job_started_at": job.get("started_at"),
                  "job_completed_at": job.get("completed_at"), "runner_name": job.get("runner_name"),
                  "runner_group_name": job.get("runner_group_name"), "labels": job.get("labels"),
                  "status": job.get("status"), "conclusion": job.get("conclusion"),
                  "artifact_name": name if len(matching) == 1 else None}
    return out
