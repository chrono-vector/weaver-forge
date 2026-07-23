#!/usr/bin/env python3
"""Phase 2B source-mount isolation behavioral tests (RC4B-010 / RC4B-009 subset).

Safety contract:
- Temporary workspaces are children of scripts/tests/ (never the OS default temp root)
- Every Bash subprocess uses cwd=SCRIPTS_DIR and repository-local relative paths
- Host script is sourced only as ./run_witness_narrow_build.sh
- Mock Docker executable first on PATH (never delegates to real docker; no exec)
- Mock proof is unique marker + length-prefixed argv log (argument boundaries preserved)
- No remote clones / no network
- No Cargo, rustc, rustup, DotSlash, protoc, ldd, or product execution
- No Windows absolute workspace paths passed into Bash
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
HOST_SCRIPT_NAME = "run_witness_narrow_build.sh"
HOST_SCRIPT = SCRIPTS_DIR / HOST_SCRIPT_NAME
MOCK_DOCKER_MARKER = "MOCK_DOCKER_PHASE2B"
DOCKER_LOG_ENV = "PHASE2B_DOCKER_INVOCATION_LOG"
TEMP_PREFIX = "phase2b_test_"

_STRIP_ENV_KEYS = (
    "IDENTITY_GATE_CLOSED",
    "DOCKER_HOST",
    "DOCKER_CONTEXT",
    "CARGO_HOME",
    "RUSTUP_HOME",
    "CARGO_TARGET_DIR",
    DOCKER_LOG_ENV,
)


def _find_bash() -> str:
    candidates: list[str] = []
    for key in ("ProgramFiles", "ProgramFiles(x86)"):
        root = os.environ.get(key)
        if root:
            candidates.append(str(Path(root) / "Git" / "bin" / "bash.exe"))
            candidates.append(str(Path(root) / "Git" / "usr" / "bin" / "bash.exe"))
    which = shutil.which("bash")
    if which:
        candidates.append(which)
    for c in candidates:
        if c and Path(c).is_file():
            return c
    raise unittest.SkipTest("bash not available for Phase 2B mount isolation tests")


def _bash(args: list[str], *, env: dict[str, str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_find_bash(), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=env,
        cwd=str(cwd) if cwd is not None else None,
    )


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8", newline="\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _is_dir_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        os.readlink(path)
        return True
    except OSError:
        return False


def _create_dir_link(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
        return
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":
        cp = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if cp.returncode == 0 and _is_dir_link(link):
            return
        raise unittest.SkipTest(
            f"symlink/junction creation unavailable (privilege): mklink exit {cp.returncode}"
        )
    raise unittest.SkipTest("directory symlink creation unavailable on this platform")


def _remaining_phase2b_temps() -> list[Path]:
    if not TESTS_DIR.is_dir():
        return []
    return sorted(
        p for p in TESTS_DIR.iterdir() if p.is_dir() and p.name.startswith(TEMP_PREFIX)
    )


def _parse_argv_log(text: str) -> list[list[str]]:
    """Parse length-prefixed mock Docker argv log into invocations."""
    invocations: list[list[str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i] != MOCK_DOCKER_MARKER:
            i += 1
            continue
        i += 1
        if i >= len(lines) or not lines[i].startswith("ARGC="):
            raise AssertionError(f"malformed docker log near line {i}: {lines[i:i+3]}")
        argc = int(lines[i].split("=", 1)[1])
        i += 1
        args: list[str] = []
        for _ in range(argc):
            if i >= len(lines) or ":" not in lines[i]:
                raise AssertionError(f"missing ARGV length line at {i}")
            length_s, payload = lines[i].split(":", 1)
            length = int(length_s)
            if len(payload) != length:
                raise AssertionError(
                    f"argv boundary corruption: declared len={length} actual={len(payload)} payload={payload!r}"
                )
            args.append(payload)
            i += 1
        if i >= len(lines) or lines[i] != "END_INVOCATION":
            raise AssertionError("missing END_INVOCATION")
        i += 1
        invocations.append(args)
    return invocations


class Phase2BMountIsolationTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        leftovers = _remaining_phase2b_temps()
        assert not leftovers, (
            f"Phase 2B temporary directories remain under {TESTS_DIR}: "
            f"{[p.name for p in leftovers]}"
        )

    def setUp(self) -> None:
        self.assertTrue(HOST_SCRIPT.is_file(), f"missing host script: {HOST_SCRIPT}")
        self._tmpdir = tempfile.TemporaryDirectory(prefix=TEMP_PREFIX, dir=str(TESTS_DIR))
        self.workspace = Path(self._tmpdir.name).resolve()
        self.assertEqual(self.workspace.parent, TESTS_DIR)
        self.ws_basename = self.workspace.name
        self.ws_rel = f"tests/{self.ws_basename}"
        self.assertFalse(Path(self.ws_rel).is_absolute())
        self.assertTrue(self.ws_rel.startswith("tests/"))

        self.mock_bin = self.workspace / "mock-bin"
        self.mock_bin.mkdir()
        self.docker_log = self.workspace / "docker_invocations.log"
        self.docker_log.write_text("", encoding="utf-8")
        self.mock_bin_rel = f"{self.ws_rel}/mock-bin"
        self.docker_log_rel = f"{self.ws_rel}/docker_invocations.log"

        _write_executable(
            self.mock_bin / "docker",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                if [[ -z "${{{DOCKER_LOG_ENV}:-}}" ]]; then
                  echo "mock-docker: {DOCKER_LOG_ENV} is unset" >&2
                  exit 96
                fi
                {{
                  echo "{MOCK_DOCKER_MARKER}"
                  printf 'ARGC=%s\\n' "$#"
                  for _arg in "$@"; do
                    printf '%s:%s\\n' "${{#_arg}}" "${{_arg}}"
                  done
                  echo "END_INVOCATION"
                }} >> "${{{DOCKER_LOG_ENV}}}"
                case "${{1:-}}" in
                  version)
                    if [[ "${{2:-}}" == "--format" ]]; then
                      echo "0.0.0-mock-phase2b"
                    else
                      echo "Client: 0.0.0-mock-phase2b"
                    fi
                    ;;
                  context)
                    echo "mock-context-phase2b"
                    ;;
                  run)
                    exit 0
                    ;;
                  pull|inspect)
                    exit 0
                    ;;
                  *)
                    echo "mock-docker: unexpected command: $*" >&2
                    exit 97
                    ;;
                esac
                """
            ),
        )
        mock_body = (self.mock_bin / "docker").read_text(encoding="utf-8")
        self.assertNotRegex(mock_body, r"(?m)^\s*exec\s+")
        self.assertNotIn("command -v docker", mock_body)
        self.assertNotIn("/usr/bin/docker", mock_body)
        self.assertNotIn("docker.io", mock_body)

        self.env: dict[str, str] = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.workspace / "home"),
            "TMPDIR": str(self.workspace / "tmp"),
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
            DOCKER_LOG_ENV: self.docker_log_rel,
        }
        (self.workspace / "home").mkdir()
        (self.workspace / "tmp").mkdir()
        for k in _STRIP_ENV_KEYS:
            if k == DOCKER_LOG_ENV:
                continue
            self.env.pop(k, None)
        for k in ("SYSTEMROOT", "WINDIR", "SystemRoot", "COMSPEC"):
            if k in os.environ:
                self.env[k] = os.environ[k]

        self._run_setup_probe()
        self.docker_log.write_text("", encoding="utf-8")
        probe = self._bash_in_scripts("docker version --format '{{.Client.Version}}'")
        self.assertEqual(probe.returncode, 0, probe.stderr + probe.stdout)
        self.assertEqual(probe.stdout.strip(), "0.0.0-mock-phase2b")
        self.assertIn(MOCK_DOCKER_MARKER, self.docker_log.read_text(encoding="utf-8"))
        self.assertEqual(self._docker_invocation_count(), 1)
        self.docker_log.write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        workspace = getattr(self, "workspace", None)
        self._tmpdir.cleanup()
        if workspace is not None:
            self.assertFalse(
                workspace.exists(),
                f"TemporaryDirectory failed to remove repository-local workspace: {workspace}",
            )

    def _bash_env(self) -> dict[str, str]:
        env = dict(self.env)
        env["HOME"] = self.ws_rel + "/home"
        env["TMPDIR"] = self.ws_rel + "/tmp"
        env[DOCKER_LOG_ENV] = self.docker_log_rel
        env["PATH"] = self.mock_bin_rel + os.pathsep + env.get("PATH", "")
        return env

    def _bash_in_scripts(self, body: str) -> subprocess.CompletedProcess[str]:
        return _bash(["-c", body], env=self._bash_env(), cwd=SCRIPTS_DIR)

    def _run_setup_probe(self) -> None:
        probe_rel = f"{self.ws_rel}/setup_probe.txt"
        script = textwrap.dedent(
            f"""\
            set -Eeuo pipefail
            test -r ./run_witness_narrow_build.sh
            test -d {shlex.quote(self.ws_rel)}
            echo ok > {shlex.quote(probe_rel)}
            """
        )
        cp = self._bash_in_scripts(script)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertTrue((self.workspace / "setup_probe.txt").is_file())

    def _source_helpers_snippet(self) -> str:
        return textwrap.dedent(
            f"""\
            set -Eeuo pipefail
            export PATH={shlex.quote(self.mock_bin_rel)}:${{PATH:-}}
            export {DOCKER_LOG_ENV}={shlex.quote(self.docker_log_rel)}
            source ./run_witness_narrow_build.sh
            """
        )

    def _run_sourced(self, body: str) -> subprocess.CompletedProcess[str]:
        script = self._source_helpers_snippet() + "\n" + body
        return _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)

    def _ws(self, *parts: str) -> str:
        return "/".join((self.ws_rel, *parts))

    def _py_to_bash_rel(self, path: Path) -> str:
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(SCRIPTS_DIR.resolve())
        except ValueError as exc:
            raise AssertionError(f"path not under SCRIPTS_DIR: {resolved}") from exc
        return rel.as_posix()

    def _docker_invocation_count(self) -> int:
        return len(_parse_argv_log(self.docker_log.read_text(encoding="utf-8")))

    def _docker_run_argv(self) -> list[str]:
        inv = _parse_argv_log(self.docker_log.read_text(encoding="utf-8"))
        runs = [a for a in inv if a and a[0] == "run"]
        self.assertTrue(runs, "expected at least one docker run invocation")
        return runs[-1]

    def _layout_snippet(self, work_rel: str) -> str:
        """Create a production-like directory layout under work_rel (Bash-relative)."""
        return textwrap.dedent(
            f"""\
            mkdir -p {shlex.quote(work_rel)}
            WORK_ROOT={shlex.quote(work_rel)}
            WORK_ROOT="$(cd "$WORK_ROOT" && pwd)"
            WF_DIR="$WORK_ROOT/weaver-forge"
            SRC_DIR="$WORK_ROOT/grok-build-src"
            CARGO_HOME_DIR="$WORK_ROOT/cargo-home"
            CARGO_TARGET_DIR="$WORK_ROOT/cargo-target"
            BOOTSTRAP_CARGO_TARGET_DIR="$WORK_ROOT/bootstrap-cargo-target"
            DOTSLASH_CACHE_DIR="$WORK_ROOT/dotslash-cache"
            HOME_DIR="$WORK_ROOT/home"
            BOOTSTRAP_DIR="$WORK_ROOT/bootstrap"
            TMP_DIR="$WORK_ROOT/tmp"
            EVIDENCE_DIR="$WORK_ROOT/evidence/run1"
            mkdir -p "$WF_DIR/external_verifications/grok-build/witness-package/scripts"
            mkdir -p "$SRC_DIR" "$CARGO_HOME_DIR" "$CARGO_TARGET_DIR" \\
              "$BOOTSTRAP_CARGO_TARGET_DIR" "$DOTSLASH_CACHE_DIR" "$HOME_DIR" \\
              "$BOOTSTRAP_DIR" "$TMP_DIR" "$EVIDENCE_DIR"
            HOST_CONTAINER_SCRIPT="$WF_DIR/external_verifications/grok-build/witness-package/scripts/container_narrow_build.sh"
            printf '%s\\n' '#!/usr/bin/env bash' 'echo container-mock' > "$HOST_CONTAINER_SCRIPT"
            # Minimal git metadata so canonicalize/path checks have real trees.
            (cd "$SRC_DIR" && git init -q && git config user.email t@t && git config user.name t \\
              && echo x > f && git add f && git commit -q -m i)
            (cd "$WF_DIR" && git init -q && git config user.email t@t && git config user.name t \\
              && echo y > f && git add f && git commit -q -m i)
            SRC_HEAD="$(git -C "$SRC_DIR" rev-parse HEAD)"
            SRC_STATUS=""
            CURRENT_STAGE="phase2b_test"
            """
        )

    def _build_and_emit_argv(self) -> str:
        return textwrap.dedent(
            """\
            build_canonical_mount_plan
            validate_mount_plan
            build_docker_mount_argv
            declare -a DOCKER_RUN_ARGV=(run --rm --platform linux/amd64 --network bridge)
            DOCKER_RUN_ARGV+=("${DOCKER_MOUNT_ARGV[@]}")
            DOCKER_RUN_ARGV+=(-e HOME=/work/home -e CARGO_HOME=/work/cargo-home
              -e CARGO_TARGET_DIR=/work/cargo-target -e TMPDIR=/work/tmp -w /src
              docker.io/library/rust@sha256:dead
              bash /witness/container_narrow_build.sh)
            docker "${DOCKER_RUN_ARGV[@]}"
            """
        )

    def _mount_specs(self, argv: list[str]) -> list[str]:
        specs: list[str] = []
        i = 0
        while i < len(argv):
            if argv[i] == "--mount" and i + 1 < len(argv):
                specs.append(argv[i + 1])
                i += 2
                continue
            i += 1
        return specs

    # ------------------------------------------------------------------
    # Successful canonical plan
    # ------------------------------------------------------------------
    def test_canonical_mount_plan_reaches_mock_docker(self) -> None:
        work_rel = self._ws("work-ok")
        body = self._layout_snippet(work_rel) + self._build_and_emit_argv()
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(self._docker_invocation_count(), 1)
        argv = self._docker_run_argv()
        specs = self._mount_specs(argv)

        # 1: source /src readonly exactly once
        src_specs = [s for s in specs if re.search(r"(^|,)dst=/src(,|$)", s)]
        self.assertEqual(len(src_specs), 1, specs)
        self.assertIn("readonly", src_specs[0])
        self.assertRegex(src_specs[0], r"type=bind,src=.+,dst=/src,readonly")

        # 2: no broad WORK_ROOT -> /work
        for s in specs:
            self.assertNotRegex(s, r"(^|,)dst=/work(,|$)")

        # 3: no /work/grok-build alias (audit name or code name)
        joined = "\n".join(argv)
        self.assertNotIn("/work/grok-build", joined)
        for s in specs:
            self.assertNotRegex(s, r"dst=/work/grok-build(-src)?(,|$)")

        # 4–8: dedicated writable mounts
        for dst in (
            "/work/cargo-target",
            "/work/bootstrap-cargo-target",
            "/work/home",
            "/work/tmp",
            "/evidence",
        ):
            hits = [s for s in specs if f"dst={dst}" in s or f"dst={dst}," in s]
            self.assertEqual(len(hits), 1, f"missing {dst}: {specs}")
            self.assertNotIn("readonly", hits[0])

        # HOME/CARGO_HOME mount (cargo-home)
        cargo_home = [s for s in specs if "dst=/work/cargo-home" in s]
        self.assertEqual(len(cargo_home), 1)

        # 22: exact argument boundaries — --mount and its value are separate argv elems
        for i, a in enumerate(argv):
            if a == "--mount":
                self.assertLess(i + 1, len(argv))
                self.assertTrue(argv[i + 1].startswith("type=bind,"))

    def test_path_with_spaces_preserved_in_docker_argv(self) -> None:
        work_rel = self._ws("work with spaces")
        body = self._layout_snippet(work_rel) + self._build_and_emit_argv()
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        argv = self._docker_run_argv()
        specs = self._mount_specs(argv)
        self.assertTrue(any("work with spaces" in s for s in specs), specs)
        # Must be one argv element containing spaces, not split fragments.
        space_args = [a for a in argv if "work with spaces" in a]
        self.assertTrue(space_args)
        for a in space_args:
            self.assertIn("type=bind,src=", a)

    # ------------------------------------------------------------------
    # Validator rejections (docker count must stay 0)
    # ------------------------------------------------------------------
    def _reject_case(self, mutate: str, expect_substr: str) -> None:
        work_rel = self._ws("work-rej")
        body = (
            self._layout_snippet(work_rel)
            + textwrap.dedent(
                f"""\
                finalize_pre_docker_infrastructure_failure() {{
                  echo "FINALIZE:$1" >&2
                  exit 7
                }}
                build_canonical_mount_plan
                {mutate}
                set +e
                validate_mount_plan
                ec=$?
                set -e
                echo "VALIDATE_EC=$ec"
                exit "$ec"
                """
            )
        )
        before = self._docker_invocation_count()
        cp = self._run_sourced(body)
        self.assertNotEqual(cp.returncode, 0, cp.stdout + cp.stderr)
        self.assertIn(expect_substr, (cp.stderr or "") + (cp.stdout or ""))
        self.assertEqual(self._docker_invocation_count(), before)

    def test_reject_writable_equal_grok_build(self) -> None:
        self._reject_case(
            'append_mount_plan "rw" "$SRC_DIR" "/work/evil-src"',
            "aliases GROK_BUILD_DIR",
        )

    def test_reject_writable_inside_grok_build(self) -> None:
        self._reject_case(
            'mkdir -p "$SRC_DIR/nested" && append_mount_plan "rw" "$SRC_DIR/nested" "/work/evil-nested"',
            "aliases GROK_BUILD_DIR",
        )

    def test_reject_writable_ancestor_of_grok_build(self) -> None:
        # WORK_ROOT is the ancestor; also covered by WORK_ROOT writable ban.
        self._reject_case(
            'append_mount_plan "rw" "$WORK_ROOT" "/work"',
            "WORK_ROOT",
        )

    def test_reject_writable_equal_wf_dir(self) -> None:
        self._reject_case(
            'append_mount_plan "rw" "$WF_DIR" "/work/evil-wf"',
            "aliases WF_DIR",
        )

    def test_reject_writable_ancestor_of_wf_dir(self) -> None:
        self._reject_case(
            'append_mount_plan "rw" "$WORK_ROOT" "/work"',
            "WORK_ROOT",
        )

    def test_reject_writable_target_equals_src(self) -> None:
        self._reject_case(
            'append_mount_plan "rw" "$CARGO_TARGET_DIR" "/src"',
            "overlaps /src",
        )

    def test_reject_writable_target_below_src(self) -> None:
        self._reject_case(
            'append_mount_plan "rw" "$CARGO_TARGET_DIR" "/src/nested"',
            "overlaps /src",
        )

    def test_reject_writable_target_above_src(self) -> None:
        self._reject_case(
            'append_mount_plan "rw" "$CARGO_TARGET_DIR" "/"',
            "overlaps /src",
        )

    def test_reject_duplicate_container_target(self) -> None:
        self._reject_case(
            'append_mount_plan "rw" "$HOME_DIR" "/work/cargo-target"',
            "duplicate container target",
        )

    def test_reject_same_source_ro_and_rw(self) -> None:
        self._reject_case(
            'append_mount_plan "ro" "$CARGO_TARGET_DIR" "/work/cargo-target-ro-alias"',
            "mounted both",
        )

    def test_path_prefix_false_positive_avoided(self) -> None:
        """/source vs /source-other must not be treated as parent/child."""
        work_rel = self._ws("work-prefix")
        body = (
            self._layout_snippet(work_rel)
            + textwrap.dedent(
                """\
                mkdir -p "$WORK_ROOT/source" "$WORK_ROOT/source-other"
                # Point SRC_DIR at .../source (not source-other).
                SRC_DIR="$WORK_ROOT/source"
                (cd "$SRC_DIR" && git init -q && git config user.email t@t && git config user.name t \\
                  && echo z > f && git add f && git commit -q -m i)
                clear_mount_plan
                append_mount_plan "ro" "$SRC_DIR" "/src"
                append_mount_plan "ro" "$HOST_CONTAINER_SCRIPT" "/witness/container_narrow_build.sh"
                append_mount_plan "rw" "$WORK_ROOT/source-other" "/work/source-other"
                append_mount_plan "rw" "$CARGO_TARGET_DIR" "/work/cargo-target"
                append_mount_plan "rw" "$BOOTSTRAP_CARGO_TARGET_DIR" "/work/bootstrap-cargo-target"
                append_mount_plan "rw" "$CARGO_HOME_DIR" "/work/cargo-home"
                append_mount_plan "rw" "$HOME_DIR" "/work/home"
                append_mount_plan "rw" "$DOTSLASH_CACHE_DIR" "/work/dotslash-cache"
                append_mount_plan "rw" "$BOOTSTRAP_DIR" "/work/bootstrap"
                append_mount_plan "rw" "$TMP_DIR" "/work/tmp"
                append_mount_plan "rw" "$EVIDENCE_DIR" "/evidence"
                validate_mount_plan
                echo PREFIX_OK
                """
            )
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("PREFIX_OK", cp.stdout)

    def test_validation_failure_docker_count_zero(self) -> None:
        before = self._docker_invocation_count()
        self.assertEqual(before, 0)
        self._reject_case(
            'append_mount_plan "rw" "$SRC_DIR" "/work/evil"',
            "aliases GROK_BUILD_DIR",
        )
        self.assertEqual(self._docker_invocation_count(), 0)

    def test_reject_comma_in_mount_fields(self) -> None:
        """Comma in src or dst must fail closed before Docker argv construction."""
        cases = (
            (
                "comma_in_source",
                textwrap.dedent(
                    """\
                    mkdir -p "$WORK_ROOT/src,with,comma"
                    append_mount_plan "rw" "$WORK_ROOT/src,with,comma" "/work/comma-src"
                    """
                ),
                "must not contain comma",
            ),
            (
                "comma_in_destination",
                'append_mount_plan "rw" "$CARGO_TARGET_DIR" "/work/dst,with,comma"',
                "must not contain comma",
            ),
        )
        for name, mutate, expect in cases:
            with self.subTest(case=name):
                self.docker_log.write_text("", encoding="utf-8")
                work_rel = self._ws(f"work-comma-{name}")
                body = (
                    self._layout_snippet(work_rel)
                    + textwrap.dedent(
                        f"""\
                        finalize_pre_docker_infrastructure_failure() {{
                          echo "FINALIZE:$1" >&2
                          exit 7
                        }}
                        build_canonical_mount_plan
                        {mutate}
                        set +e
                        validate_mount_plan
                        ec=$?
                        set -e
                        echo "VALIDATE_EC=$ec"
                        # Must never reach structured argv construction / docker.
                        build_docker_mount_argv
                        docker run --rm should-not-run
                        exit "$ec"
                        """
                    )
                )
                cp = self._run_sourced(body)
                combined = (cp.stderr or "") + (cp.stdout or "")
                self.assertNotEqual(cp.returncode, 0, combined)
                self.assertIn(expect, combined)
                self.assertIn("FINALIZE:mount_plan_field_syntax_", combined)
                self.assertEqual(self._docker_invocation_count(), 0)
                # Comma must not have been split into multiple Docker --mount fields.
                log = self.docker_log.read_text(encoding="utf-8")
                self.assertNotIn("--mount", log)
                self.assertNotIn("type=bind", log)

    def test_reject_writable_source_inside_wf_dir(self) -> None:
        """Writable child directory beneath WF_DIR must be rejected behaviorally."""
        work_rel = self._ws("work-wf-child")
        body = (
            self._layout_snippet(work_rel)
            + textwrap.dedent(
                """\
                finalize_pre_docker_infrastructure_failure() {
                  echo "FINALIZE:$1" >&2
                  # Return (do not exit) so the harness can verify sentinel survival.
                }
                mkdir -p "$WF_DIR/child-writable"
                echo sentinel-v1 > "$WF_DIR/child-writable/sentinel.txt"
                build_canonical_mount_plan
                append_mount_plan "rw" "$WF_DIR/child-writable" "/work/evil-wf-child"
                set +e
                validate_mount_plan
                ec=$?
                set -e
                echo "VALIDATE_EC=$ec"
                test -d "$WF_DIR/child-writable"
                test -f "$WF_DIR/child-writable/sentinel.txt"
                grep -qx 'sentinel-v1' "$WF_DIR/child-writable/sentinel.txt"
                echo "SENTINEL_OK"
                exit "$ec"
                """
            )
        )
        before = self._docker_invocation_count()
        cp = self._run_sourced(body)
        combined = (cp.stderr or "") + (cp.stdout or "")
        self.assertNotEqual(cp.returncode, 0, combined)
        self.assertIn("aliases WF_DIR", combined)
        self.assertIn("FINALIZE:mount_plan_writable_aliases_wf", combined)
        self.assertIn("SENTINEL_OK", combined)
        self.assertEqual(self._docker_invocation_count(), before)
        self.assertEqual(self._docker_invocation_count(), 0)

    def test_reject_missing_required_mount_source(self) -> None:
        """Genuinely absent required mount source fails before Docker / without creation."""
        work_rel = self._ws("work-missing-src")
        body = (
            self._layout_snippet(work_rel)
            + textwrap.dedent(
                """\
                finalize_pre_docker_infrastructure_failure() {
                  echo "FINALIZE:$1" >&2
                  # Return (do not exit) so the harness can verify the source stays absent.
                }
                MISSING="$WORK_ROOT/does-not-exist-mount-source"
                test ! -e "$MISSING"
                build_canonical_mount_plan
                append_mount_plan "rw" "$MISSING" "/work/missing-src"
                set +e
                validate_mount_plan
                ec=$?
                set -e
                echo "VALIDATE_EC=$ec"
                # Validator must not create the missing source.
                test ! -e "$MISSING"
                echo "STILL_ABSENT"
                exit "$ec"
                """
            )
        )
        cp = self._run_sourced(body)
        combined = (cp.stderr or "") + (cp.stdout or "")
        self.assertNotEqual(cp.returncode, 0, combined)
        self.assertIn("required mount source does not exist", combined)
        self.assertIn("FINALIZE:mount_plan_source_missing", combined)
        self.assertNotIn("cannot canonicalize mount source", combined)
        self.assertIn("STILL_ABSENT", combined)
        self.assertEqual(self._docker_invocation_count(), 0)

    def test_reject_mount_source_canonicalization_failure(self) -> None:
        """Canonicalization failure for an existing required source fails closed.

        Prefers a real broken-symlink filesystem case. If link creation is
        unavailable (e.g. Windows privilege), uses a tightly scoped harness
        override of canonicalize_existing_path only inside this sourced
        subprocess (not activatable via production args/env).
        """
        work_rel = self._ws("work-canon-fail")
        # Attempt real broken symlink first via Bash ln -s.
        probe = self._bash_in_scripts(
            textwrap.dedent(
                f"""\
                set -Eeuo pipefail
                base={shlex.quote(work_rel + "/probe")}
                mkdir -p "$base"
                if ln -s "$base/missing-target" "$base/broken-link" 2>/dev/null \\
                  && [[ -L "$base/broken-link" ]] && [[ ! -e "$base/broken-link" ]]; then
                  echo BROKEN_SYMLINK_OK
                else
                  echo BROKEN_SYMLINK_UNAVAILABLE
                fi
                """
            )
        )
        use_real_broken = "BROKEN_SYMLINK_OK" in (probe.stdout or "")

        if use_real_broken:
            mutate = textwrap.dedent(
                """\
                BROKEN="$WORK_ROOT/canon-broken"
                rm -rf "$BROKEN"
                ln -s "$WORK_ROOT/missing-canon-target" "$BROKEN"
                test -L "$BROKEN"
                test ! -e "$BROKEN"
                append_mount_plan "rw" "$BROKEN" "/work/canon-broken"
                """
            )
            expect_finalize = "FINALIZE:mount_plan_canonicalize_mount_source"
            expect_msg = "cannot canonicalize mount source"
            injection_note = ""
        else:
            # canonicalization-failure injection (test harness only)
            mutate = textwrap.dedent(
                """\
                echo "CANONICALIZATION_FAILURE_INJECTION=yes"
                DESIGNATED="$WORK_ROOT/canon-inject-src"
                mkdir -p "$DESIGNATED"
                echo keep > "$DESIGNATED/sentinel.txt"
                # Save production helper, then override only for the designated source.
                eval "$(declare -f canonicalize_existing_path | sed '1s/canonicalize_existing_path/canonicalize_existing_path__prod/')"
                canonicalize_existing_path() {
                  local p="$1"
                  if [[ "$p" == "$DESIGNATED" ]]; then
                    return 1
                  fi
                  canonicalize_existing_path__prod "$p"
                }
                append_mount_plan "rw" "$DESIGNATED" "/work/canon-inject"
                """
            )
            expect_finalize = "FINALIZE:mount_plan_canonicalize_mount_source"
            expect_msg = "cannot canonicalize mount source"
            injection_note = "CANONICALIZATION_FAILURE_INJECTION=yes"

        body = (
            self._layout_snippet(work_rel)
            + textwrap.dedent(
                f"""\
                finalize_pre_docker_infrastructure_failure() {{
                  echo "FINALIZE:$1" >&2
                  exit 7
                }}
                build_canonical_mount_plan
                {mutate}
                set +e
                validate_mount_plan
                ec=$?
                set -e
                echo "VALIDATE_EC=$ec"
                exit "$ec"
                """
            )
        )
        cp = self._run_sourced(body)
        combined = (cp.stderr or "") + (cp.stdout or "")
        self.assertNotEqual(cp.returncode, 0, combined)
        self.assertIn(expect_msg, combined)
        self.assertIn(expect_finalize, combined)
        self.assertNotIn("required mount source does not exist", combined)
        if injection_note:
            self.assertIn(injection_note, combined)
        self.assertEqual(self._docker_invocation_count(), 0)

    # ------------------------------------------------------------------
    # Pre/post source integrity
    # ------------------------------------------------------------------
    def test_post_head_mismatch_prevents_success(self) -> None:
        work_rel = self._ws("work-head")
        body = (
            self._layout_snippet(work_rel)
            + textwrap.dedent(
                """\
                EVIDENCE_DIR="$WORK_ROOT/evidence/run1"
                mkdir -p "$EVIDENCE_DIR"
                : > "$EVIDENCE_DIR/HOST_RUN_METADATA.txt"
                CARGO_STARTED=NO
                OUTCOME=CARGO_SUCCEEDED_ARTIFACT_PRESENT
                POST_BUILD_INTEGRITY_OK=yes
                enforce_post_docker_source_integrity_boundary "no" "yes"
                echo "OUTCOME=$OUTCOME"
                echo "POST=$POST_BUILD_INTEGRITY_OK"
                grep -q 'outcome=INFRASTRUCTURE_FAILURE' "$EVIDENCE_DIR/BUILD_EXIT_CODE.txt"
                grep -q 'failure_stage=post_docker_source_integrity' "$EVIDENCE_DIR/BUILD_EXIT_CODE.txt"
                """
            )
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("OUTCOME=INFRASTRUCTURE_FAILURE", cp.stdout)
        self.assertIn("POST=no", cp.stdout)

    def test_post_dirty_tree_prevents_success(self) -> None:
        work_rel = self._ws("work-dirty")
        body = (
            self._layout_snippet(work_rel)
            + textwrap.dedent(
                """\
                EVIDENCE_DIR="$WORK_ROOT/evidence/run1"
                mkdir -p "$EVIDENCE_DIR"
                : > "$EVIDENCE_DIR/HOST_RUN_METADATA.txt"
                CARGO_STARTED=YES
                OUTCOME=CARGO_SUCCEEDED_ARTIFACT_PRESENT
                POST_BUILD_INTEGRITY_OK=yes
                enforce_post_docker_source_integrity_boundary "yes" "no"
                echo "OUTCOME=$OUTCOME"
                grep -q 'reason=post_docker_source_head_or_clean_tree_mismatch' "$EVIDENCE_DIR/BUILD_EXIT_CODE.txt"
                """
            )
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("OUTCOME=INFRASTRUCTURE_FAILURE", cp.stdout)

    def test_symlink_safe_source_canonicalization(self) -> None:
        work = self.workspace / "work-sym"
        work.mkdir()
        real_src = work / "real-grok"
        real_src.mkdir()
        link_src = work / "grok-build-src"
        try:
            _create_dir_link(link_src, real_src)
        except unittest.SkipTest as e:
            self.skipTest(str(e))
        work_rel = self._py_to_bash_rel(work)
        body = textwrap.dedent(
            f"""\
            WORK_ROOT={shlex.quote(work_rel)}
            WORK_ROOT="$(cd "$WORK_ROOT" && pwd)"
            WF_DIR="$WORK_ROOT/weaver-forge"
            SRC_DIR="$WORK_ROOT/grok-build-src"
            CARGO_HOME_DIR="$WORK_ROOT/cargo-home"
            CARGO_TARGET_DIR="$WORK_ROOT/cargo-target"
            BOOTSTRAP_CARGO_TARGET_DIR="$WORK_ROOT/bootstrap-cargo-target"
            DOTSLASH_CACHE_DIR="$WORK_ROOT/dotslash-cache"
            HOME_DIR="$WORK_ROOT/home"
            BOOTSTRAP_DIR="$WORK_ROOT/bootstrap"
            TMP_DIR="$WORK_ROOT/tmp"
            EVIDENCE_DIR="$WORK_ROOT/evidence/run1"
            mkdir -p "$WF_DIR/external_verifications/grok-build/witness-package/scripts"
            mkdir -p "$CARGO_HOME_DIR" "$CARGO_TARGET_DIR" "$BOOTSTRAP_CARGO_TARGET_DIR" \\
              "$DOTSLASH_CACHE_DIR" "$HOME_DIR" "$BOOTSTRAP_DIR" "$TMP_DIR" "$EVIDENCE_DIR"
            # real_src already exists via link target
            HOST_CONTAINER_SCRIPT="$WF_DIR/external_verifications/grok-build/witness-package/scripts/container_narrow_build.sh"
            echo '#!/bin/bash' > "$HOST_CONTAINER_SCRIPT"
            (cd "$SRC_DIR" && git init -q && git config user.email t@t && git config user.name t \\
              && echo x > f && git add f && git commit -q -m i)
            (cd "$WF_DIR" && git init -q && git config user.email t@t && git config user.name t \\
              && echo y > f && git add f && git commit -q -m i)
            build_canonical_mount_plan
            validate_mount_plan
            echo SYMLINK_OK
            # Writable mount through a path that canonicalizes into SRC must fail.
            finalize_pre_docker_infrastructure_failure() {{ echo "FINALIZE:$1" >&2; exit 7; }}
            append_mount_plan "rw" "$WORK_ROOT/real-grok" "/work/via-real"
            set +e
            validate_mount_plan
            ec=$?
            set -e
            exit "$ec"
            """
        )
        cp = self._run_sourced(body)
        # First validate should succeed (printed SYMLINK_OK) then second fails.
        self.assertIn("SYMLINK_OK", cp.stdout + cp.stderr)
        self.assertNotEqual(cp.returncode, 0)
        combined = cp.stderr + cp.stdout
        # Symlink resolution must fail-closed: either mode conflict on the same
        # canonical source, or explicit GROK_BUILD_DIR alias rejection.
        self.assertTrue(
            ("aliases GROK_BUILD_DIR" in combined) or ("mounted both" in combined),
            combined,
        )
        self.assertEqual(self._docker_invocation_count(), 0)

    def test_host_script_has_no_broad_work_mount(self) -> None:
        text = HOST_SCRIPT.read_text(encoding="utf-8")
        self.assertNotRegex(text, r'-v\s+"\$\{WORK_ROOT\}:/work')
        self.assertNotIn("/work/grok-build", text)
        self.assertIn("build_canonical_mount_plan", text)
        self.assertIn("validate_mount_plan", text)
        self.assertIn("readonly", text)
        self.assertIn("enforce_post_docker_source_integrity_boundary", text)
        # validate before docker run array expansion
        idx_val = text.index("validate_mount_plan")
        idx_run = text.index('docker "${DOCKER_RUN_ARGV[@]}"')
        self.assertLess(idx_val, idx_run)


if __name__ == "__main__":
    unittest.main()
