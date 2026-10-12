"""Logical fail-closed fixture for the frozen EB-14 J0+J1 sequence and accepted F5 contract.

This is a logical fixture model of one recorded call sequence. It is not a full two-process host proof, not a Supervisor process and a controller process, and not a Windows Job implementation. A recorded mock resume stays UNEXECUTED.
Owned-Job membership confirmation is not descendant cleanup and is not a host PASS.

The exact-type port check and the forbidden-name check are fixture guards.
This module does not sandbox arbitrary Python mutation, monkeypatching, or a
hostile interpreter.

Closed-stdin Win32 encoding stays unresolved. The fixture carries one explicit
hypothetical token for the preserved EB-5 closed-stdin rule. That token is not
a HANDLE value, and HANDLE_LIST is not used to encode it.
"""

from __future__ import annotations

DISPOSITIONS = frozenset({"REFUSED", "UNEXECUTED", "UNCONFIRMED"})
CLEANUP = frozenset({"NOT_APPLICABLE", "UNCONFIRMED", "OWNED_JOB_MEMBERSHIP_EMPTY"})
UNBOUND = "UNBOUND_AT_LAUNCH"
MOCK_ONLY_NON_IDENTITY_SCOPE = "MOCK_ONLY_NON_IDENTITY"
HYPOTHETICAL_CLOSED_STDIN_FIXTURE = "HYPOTHETICAL_CLOSED_STDIN_FIXTURE_TOKEN"
HANDLE_LIST_WIN32_ENCODING = "UNRESOLVED"
CLOSED_STDIN_WIN32_ENCODING = "UNRESOLVED"
FORBIDDEN_PORT_NAMES = frozenset({
    "AssignProcessToJobObject",
    "assign_process_to_job_object",
    "Popen",
    "popen",
    "CreateProcessW",
    "ctypes",
    "cffi",
    "subprocess",
    "system",
    "LoadLibrary",
    "WinDLL",
    "CDLL",
})
_NOT_OWNERSHIP_PROOF = frozenset({"DACL", "UNNAMED_HANDLE", "NON_INHERITABLE"})
_CREATION_FLAGS = frozenset({
    "EXTENDED_STARTUPINFO_PRESENT",
    "CREATE_SUSPENDED",
    "CREATE_UNICODE_ENVIRONMENT",
})
_PROHIBITED_FLAGS = frozenset({
    "CREATE_BREAKAWAY_FROM_JOB",
    "SHELL",
    "PARENT_PROCESS_OVERRIDE",
    "DEBUGGER",
    "CALLER_CREATION_FLAGS",
})
_JOB_CONFIGURATION = {
    "kill_on_job_close": True,
    "breakaway_ok": False,
    "silent_breakaway_ok": False,
}
_UNKNOWN = "UNKNOWN"
_SCOPE_ABSENT = object()
_CALL_EXCEPTION = object()


class MockWin32Port:
    """Fixture port. Methods record logical hops and never start a process."""

    def __init__(
        self,
        *,
        controller_create: object = True,
        target_create: object = True,
        creation_time_member: object = True,
        configuration_ok: object = True,
        terminate_return: object = True,
        signalled: object = _UNKNOWN,
        remaining_members: object = _UNKNOWN,
    ) -> None:
        self.controller_create = controller_create
        self.target_create = target_create
        self.creation_time_member = creation_time_member
        self.configuration_ok = configuration_ok
        self.terminate_return = terminate_return
        self.signalled = signalled
        self.remaining_members = remaining_members
        self.calls: list[str] = []
        self.resume_calls = 0
        self.real_process_launched = False
        self.assigned_after_create = False
        self.jobs: dict[str, dict[str, object]] = {}
        self.breakaway_jobs: set[str] = set()
        self.errors: dict[str, BaseException] = {}
        self.results: dict[str, object] = {}
        self.observers: dict[str, object] = {}

    def prepare_job(self, name: str) -> object:
        self.calls.append("prepare_job:" + name)
        observer = self.observers.get("prepare")
        if observer is not None:
            observer(self, name)
        error = self.errors.get("prepare:" + name)
        if error is not None:
            raise error
        if "prepare:" + name in self.results:
            return self.results["prepare:" + name]
        self.jobs[name] = {
            "kill_on_job_close": True,
            "breakaway_ok": name in self.breakaway_jobs,
            "silent_breakaway_ok": False,
            "members": [],
        }
        return True

    def create_suspended_with_job_list(self, hop: str, job_name: str) -> object:
        self.calls.append("create_suspended_with_job_list:" + hop + ":" + job_name)
        observer = self.observers.get("create")
        if observer is not None:
            observer(self, hop, job_name)
        error = self.errors.get("create:" + hop)
        if error is not None:
            raise error
        if "create:" + hop in self.results:
            return self.results["create:" + hop]
        created = self.controller_create if hop == "J0" else self.target_create
        if created is not True:
            return False
        job = self.jobs.get(job_name)
        if type(job) is not dict:
            return False
        members = job.get("members")
        if type(members) is not list:
            return False
        members.append(hop)
        return True

    def query_membership(self, job_name: str) -> object:
        self.calls.append("query_membership:" + job_name)
        error = self.errors.get("membership:" + job_name)
        if error is not None:
            raise error
        if "membership:" + job_name in self.results:
            return self.results["membership:" + job_name]
        job = self.jobs.get(job_name)
        members: object = []
        if type(job) is dict:
            members = job.get("members", [])
        return {
            "creation_time_member": self.creation_time_member is True and bool(members),
            "configuration_ok": self.configuration_ok is True and _job_record_supported(job),
        }

    def terminate_job(self, job_name: str) -> object:
        self.calls.append("terminate_job:" + job_name)
        error = self.errors.get("terminate:" + job_name)
        if error is not None:
            raise error
        if "terminate:" + job_name in self.results:
            return self.results["terminate:" + job_name]
        return self.terminate_return

    def confirm_owned_membership(self, job_name: str) -> object:
        self.calls.append("confirm_owned_membership:" + job_name)
        error = self.errors.get("confirm:" + job_name)
        if error is not None:
            raise error
        if "confirm:" + job_name in self.results:
            return self.results["confirm:" + job_name]
        return {
            "signalled": self.signalled,
            "remaining": self.remaining_members,
            "scope": "OWNED_JOB_MEMBERS_ONLY",
        }

    def close_owner_handles(self, job_name: str) -> object:
        self.calls.append("close_owner_handles:" + job_name)
        error = self.errors.get("close:" + job_name)
        if error is not None:
            raise error
        if "close:" + job_name in self.results:
            return self.results["close:" + job_name]
        return None

    def resume_primary_thread(self) -> object:
        self.calls.append("resume_primary_thread")
        self.resume_calls += 1
        error = self.errors.get("resume")
        if error is not None:
            raise error
        observer = self.observers.get("resume")
        if observer is not None:
            return observer(self)
        if "resume" in self.results:
            return self.results["resume"]
        return True


class FailClosedMockMachine:
    """One-shot logical sequence. Failure locks the machine. No retry."""

    def __init__(self, port: object, *, controller_scope: object = _SCOPE_ABSENT) -> None:
        self._port = port
        self._controller_scope = controller_scope
        self._locked = False
        self._resumes = 0
        self._logical_jobs: list[str] = []
        self._create_attempted: set[str] = set()
        self._cleanup_target: str | None = None

    def run(self, fixture: object) -> dict[str, object]:
        if self._locked or self._resumes:
            return _emit("REFUSED", "RETRY_PROHIBITED", self._resumes, "NOT_APPLICABLE")
        port_reason = _accept_port(self._port)
        if port_reason is not None:
            self._locked = True
            return _emit("REFUSED", port_reason, 0, "NOT_APPLICABLE")
        if type(fixture) is not dict:
            self._locked = True
            return _emit("REFUSED", "FIXTURE_REJECTED", 0, "NOT_APPLICABLE")
        refusal = _prelaunch(fixture)
        if refusal is not None:
            self._locked = True
            return _emit("REFUSED", refusal, 0, "NOT_APPLICABLE")
        if _controller_scope_gate(self._controller_scope) is not None:
            self._locked = True
            return _emit("REFUSED", "LAUNCH_IDENTITY_REQUIRED_UNPROVEN", 0, "NOT_APPLICABLE")
        self._locked = True
        try:
            return self._after_prelaunch(fixture)
        except BaseException:
            if self._cleanup_target is not None:
                self._cleanup_job(self._cleanup_target)
            raise

    def request_resume(self) -> dict[str, object]:
        """Second resume is refused. The port is not called again."""
        self._locked = True
        return _emit("REFUSED", "DOUBLE_RESUME", self._resumes, "NOT_APPLICABLE")

    def _after_prelaunch(self, fixture: dict[str, object]) -> dict[str, object]:
        self._cleanup_target = "J0"
        prepared = self._call(lambda: self._port.prepare_job("J0"))
        if prepared is _CALL_EXCEPTION:
            return self._fail("J0", "J0_PREPARATION_FAILED", uncertain=True)
        if prepared is not True:
            if prepared is False:
                return self._fail(None, "J0_PREPARATION_FAILED")
            return self._fail("J0", "J0_PREPARATION_FAILED", uncertain=True)
        if _known_bad_configuration(self._port, "J0"):
            return self._fail("J0", "JOB_CONFIGURATION")
        refusal = self._create_once("J0", "J0")
        if refusal is not None:
            return refusal
        self._cleanup_target = "J1"
        prepared = self._call(lambda: self._port.prepare_job("J1"))
        if prepared is _CALL_EXCEPTION:
            return self._fail("J0", "J1_PREPARATION_FAILED", uncertain=True)
        if prepared is not True:
            if prepared is False:
                return self._fail("J0", "J1_PREPARATION_FAILED")
            return self._fail("J0", "J1_PREPARATION_FAILED", uncertain=True)
        if _known_bad_configuration(self._port, "J1"):
            return self._fail("J1", "JOB_CONFIGURATION")
        refusal = self._create_once("J1", "J1")
        if refusal is not None:
            return refusal
        membership = self._call(lambda: self._port.query_membership("J1"))
        if membership is _CALL_EXCEPTION or not _membership_verified(membership):
            return self._fail(
                "J1",
                "MEMBERSHIP_UNVERIFIED",
                uncertain=membership is _CALL_EXCEPTION,
            )
        gate = _resume_gate(fixture)
        if gate is not None:
            return self._fail("J1", gate)
        if self._logical_jobs != ["J0", "J1"]:
            return self._fail("J1", "MEMBERSHIP_UNVERIFIED", uncertain=True)
        if self._resumes >= 1:
            return self._fail("J1", "DOUBLE_RESUME")
        self._resumes = 1
        resumed = self._call(lambda: self._port.resume_primary_thread())
        if resumed is _CALL_EXCEPTION or resumed is not True:
            return self._fail("J1", "RESUME_FAILED", uncertain=resumed is not False)
        return _emit(
            "UNEXECUTED",
            "MOCK_RESUME_RECORDED_REAL_BINDING_UNEXECUTED",
            1,
            "NOT_APPLICABLE",
        )

    def _create_once(self, hop: str, job_name: str) -> dict[str, object] | None:
        if hop in self._create_attempted or job_name in self._logical_jobs:
            return self._fail(job_name, "RETRY_PROHIBITED")
        self._create_attempted.add(hop)
        created = self._call(
            lambda: self._port.create_suspended_with_job_list(hop, job_name)
        )
        reason = hop + "_CREATION_FAILED"
        if created is _CALL_EXCEPTION:
            return self._fail(job_name, reason, uncertain=True)
        if created is True:
            self._logical_jobs.append(job_name)
            return None
        return self._fail(job_name, reason, uncertain=created is not False)

    def _call(self, func: object) -> object:
        try:
            return func()
        except Exception:
            return _CALL_EXCEPTION

    def _fail(self, job_name: str | None, reason: str, *, uncertain: bool = False) -> dict[str, object]:
        self._locked = True
        if job_name is None:
            if uncertain:
                return _emit("UNCONFIRMED", reason, self._resumes, "UNCONFIRMED")
            return _emit("REFUSED", reason, self._resumes, "NOT_APPLICABLE")
        status = self._cleanup_job(job_name)
        if uncertain or status != "OWNED_JOB_MEMBERSHIP_EMPTY":
            return _emit("UNCONFIRMED", reason, self._resumes, "UNCONFIRMED")
        return _emit("REFUSED", reason, self._resumes, "OWNED_JOB_MEMBERSHIP_EMPTY")

    def _cleanup_job(self, job_name: str) -> str:
        terminate_uncertain = False
        close_uncertain = False
        confirmation: object = None
        try:
            terminated = self._port.terminate_job(job_name)
        except Exception:
            terminate_uncertain = True
        else:
            if terminated is not True and terminated is not False:
                terminate_uncertain = True
        try:
            confirmation = self._port.confirm_owned_membership(job_name)
        except Exception:
            confirmation = None
        try:
            self._port.close_owner_handles(job_name)
        except Exception:
            close_uncertain = True
        if terminate_uncertain or close_uncertain:
            return "UNCONFIRMED"
        if _owned_membership_empty(confirmation):
            return "OWNED_JOB_MEMBERSHIP_EMPTY"
        return "UNCONFIRMED"


def _accept_port(port: object) -> str | None:
    if type(port) is not MockWin32Port:
        return "PORT_REJECTED"
    names = set(dir(port))
    if names & FORBIDDEN_PORT_NAMES:
        return "FORBIDDEN_API_PRESENT"
    required = (
        "prepare_job",
        "create_suspended_with_job_list",
        "query_membership",
        "terminate_job",
        "confirm_owned_membership",
        "close_owner_handles",
        "resume_primary_thread",
    )
    if any(not callable(getattr(port, name, None)) for name in required):
        return "PORT_REJECTED"
    return None


def _controller_scope_gate(scope: object) -> str | None:
    """Controller-owned mock gate. It is not operational authority.

    The frozen contract treats missing or unknown scope as identity-required and
    refuses before spawn while launch identity is unbound. The only scope that
    passes is the controller constant for this mock, and only as a non-identity
    fixture gate.
    """
    if type(scope) is str and scope == MOCK_ONLY_NON_IDENTITY_SCOPE:
        return None
    return "LAUNCH_IDENTITY_REQUIRED_UNPROVEN"


def _prelaunch(fixture: dict[str, object]) -> str | None:
    if fixture.get("selected_approach") != "J0+J1":
        return "APPROACH_NOT_SELECTED"
    proof = fixture.get("ownership_proof")
    if fixture.get("ownership_proven") is not True or proof in _NOT_OWNERSHIP_PROOF:
        return "UNPROVEN_OWNERSHIP"
    if fixture.get("job_list_supported") is not True or fixture.get("job_compatible") is not True:
        return "JOB_COMPATIBILITY"
    if not _fixture_job_configuration_supported(fixture.get("job_configuration")):
        return "JOB_CONFIGURATION"
    if fixture.get("supervisor_independence_guaranteed") is not True:
        return "SUPERVISOR_INDEPENDENCE"
    if fixture.get("cpu_time_backstop_is_monitor") is True:
        return "SUPERVISOR_INDEPENDENCE"
    if fixture.get("pin_approved") is not True:
        return "UNAPPROVED_PIN"
    if fixture.get("approved_limit_tokens_present") is not True:
        return "ABSENT_APPROVED_LIMIT_TOKENS"
    if fixture.get("closed_stdin") != HYPOTHETICAL_CLOSED_STDIN_FIXTURE:
        return "ABSENT_CLOSED_STDIN"
    if "creation_flags" not in fixture:
        return "CREATION_FLAGS_REJECTED"
    flags = fixture.get("creation_flags")
    if type(flags) is not frozenset and type(flags) is not set:
        return "CREATION_FLAGS_REJECTED"
    if flags != _CREATION_FLAGS or flags & _PROHIBITED_FLAGS:
        return "CREATION_FLAGS_REJECTED"
    if "handle_list" not in fixture:
        return "HANDLE_LIST_REJECTED"
    if fixture.get("handle_list") != HANDLE_LIST_WIN32_ENCODING or type(fixture.get("handle_list")) is not str:
        return "HANDLE_LIST_REJECTED"
    return None


def _resume_gate(fixture: dict[str, object]) -> str | None:
    """Accepted F5 gate: all four conditions, otherwise no Resume.

    Membership and configuration were already checked from the fixture port.
    That check is defense in depth and does not replace creation-time membership.
    """
    if fixture.get("stdout_reader_started") is not True or fixture.get("stderr_reader_started") is not True:
        return "READERS_NOT_STARTED"
    if fixture.get("controller_deadline_armed") is not True:
        return "CONTROLLER_DEADLINE_UNARMED"
    source = fixture.get("supervisor_readiness_source")
    armed = fixture.get("supervisor_monitor_armed") is True
    if source == "CONTROLLER":
        return "SUPERVISOR_SELF_ATTESTATION_INSUFFICIENT"
    if not armed or source != "SUPERVISOR":
        return "SUPERVISOR_NOT_READY"
    return None


def _membership_verified(membership: object) -> bool:
    if type(membership) is not dict:
        return False
    return (
        membership.get("creation_time_member") is True
        and membership.get("configuration_ok") is True
    )


def _fixture_job_configuration_supported(config: object) -> bool:
    if type(config) is not dict or set(config) != set(_JOB_CONFIGURATION):
        return False
    return (
        config.get("kill_on_job_close") is True
        and config.get("breakaway_ok") is False
        and config.get("silent_breakaway_ok") is False
    )


def _job_record_supported(job: object) -> bool:
    if type(job) is not dict:
        return False
    return (
        job.get("kill_on_job_close") is True
        and job.get("breakaway_ok") is False
        and job.get("silent_breakaway_ok") is False
    )


def _known_bad_configuration(port: object, job_name: str) -> bool:
    flag = getattr(port, "configuration_ok", True)
    if flag is not True:
        return True
    jobs = getattr(port, "jobs", None)
    if type(jobs) is not dict:
        return True
    return not _job_record_supported(jobs.get(job_name))


def _owned_membership_empty(confirmation: object) -> bool:
    if type(confirmation) is not dict:
        return False
    remaining = confirmation.get("remaining", _UNKNOWN)
    return confirmation.get("signalled", _UNKNOWN) is True and type(remaining) is int and remaining == 0


def _emit(disposition: str, reason: str, resume_count: int, cleanup: str) -> dict[str, object]:
    if disposition not in DISPOSITIONS or cleanup not in CLEANUP:
        raise RuntimeError("disposition outside the fail-closed vocabulary")
    return {
        "disposition": disposition,
        "reason": reason,
        "resume_count": resume_count,
        "cleanup": cleanup,
        "cleanup_scope": "OWNED_JOB_MEMBERS_ONLY",
        "terminate_return_is_cleanup_success": False,
        "launch_identity": UNBOUND,
        "scope_gate_is_operational_authority": False,
        "closed_stdin_win32_encoding": CLOSED_STDIN_WIN32_ENCODING,
        "handle_list_win32_encoding": HANDLE_LIST_WIN32_ENCODING,
        "host_model": "LOGICAL_FIXTURE_NOT_TWO_PROCESS_HOST_PROOF",
        "execution_binding_real": "UNEXECUTED",
        "operational_mingit_pin": "UNRATIFIED",
        "full_inr_ready": "NO",
        "numeric_limits": "UNSET",
        "real_process_launched": False,
        "host_qualification": "OPEN",
    }
