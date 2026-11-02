"""Regression tests for the bounded Compose smoke project selector and the
opt-in lifecycle evidence contract. The lifecycle tests exercise the real
verify.py producer/reader/auditor functions, the real smoke.sh helper with
only the external Docker boundary mocked, and the real CLI parser/dispatch.
No product runtime run is executed by this module; nothing here is an
acceptance or a future PASS claim."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[2]
SMOKE = ROOT / "tools" / "compose" / "smoke.sh"
VERIFY = ROOT / "tools" / "compose" / "verify.py"

SEP = "\x1f"
TEMPLATE_SENTINEL = "<no value>"
IMAGE_DIGEST = "sha256:" + "ab" * 32
IMAGE_REF = "slaif-agent-site-backend:local"
FOREIGN_ID = "f" * 64
CREATED_AT = "2026-11-02T00:00:00.000000000Z"
STARTED_AT = "2026-11-02T00:00:01.000000000Z"
FINISHED_AT = "2026-11-02T00:00:02.000000000Z"
ZERO_TIME = "0001-01-01T00:00:00Z"
PROJECT = "slaif007ktest"
SCOPE = "slaif007ktest"
MOUNTS_LINE = SEP + "/src/secrets" + SEP + "/secrets" + SEP + "bind" + SEP + "true\n"


def _load_verify():
    spec = importlib.util.spec_from_file_location("compose_verify", VERIFY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = _load_verify()


class ComposeSmokeContractTests(unittest.TestCase):
    def validate(self, project: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", str(SMOKE), project, "--validate-project"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_established_safe_project_families_are_accepted(self) -> None:
        for project in (
            "slaif007ci",
            "slaif009fixture",
            "slaif010rsmoke",
            "slaif071a",
        ):
            with self.subTest(project=project):
                result = self.validate(project)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")

    def test_unsafe_project_names_are_rejected(self) -> None:
        for project in (
            "",
            "SLAIF007CI",
            "slaif007-ci",
            "slaif007_ci",
            "slaif007*",
            "slaif007;true",
            "slaif",
            "unrelated007ci",
        ):
            with self.subTest(project=project):
                result = self.validate(project)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "compose-smoke: unsafe project name\n")

    def test_render_recovery_is_bounded_ordered_and_stable(self) -> None:
        source = SMOKE.read_text(encoding="utf-8")
        self.assertIn('while test "$attempt" -lt 40', source)
        self.assertIn("render-locator-recovery: failed service=", source)
        marker = (
            "render-locator-recovery: restored render=healthy web=healthy nginx=healthy"
        )
        self.assertEqual(source.count(marker), 1)
        render = source.index("wait_healthy render-api")
        web = source.index("wait_healthy web", render)
        nginx = source.index("wait_healthy nginx", web)
        global_wait = source.index("up --wait >/dev/null", nginx)
        self.assertLess(render, web)
        self.assertLess(web, nginx)
        self.assertLess(nginx, global_wait)
        self.assertGreaterEqual(
            source.count("--force-recreate --no-deps render-api"), 2
        )
        # The render fingerprint is a guarded command-substitution
        # assignment followed by a variable comparison; the unguarded
        # substitution-inside-test form was deliberately removed.
        self.assertIn(
            "render_before=$(render_fingerprint h-render-fingerprint-before)",
            source,
        )
        self.assertIn('test "$check1_render" = "$render_before"', source)
        self.assertNotIn('test "$(render_fingerprint)"', source)
        self.assertIn('test "$(site_fingerprint)" = "$sites_before"', source)

    def test_membership_fixtures_are_bounded_to_smoke_and_fail_on_collision(
        self,
    ) -> None:
        source = SMOKE.read_text(encoding="utf-8")
        first = "12000000-0000-4000-8000-000000000001"
        second = "12000000-0000-4000-8000-000000000002"
        precondition, _insert = source.split(
            "INSERT INTO control.user_account", maxsplit=1
        )
        self.assertEqual(source.count("INSERT INTO control.user_account"), 2)
        self.assertIn("agent-browser-http: OK", source)
        self.assertIn("14000000-0000-4000-8000-000000000004", source)
        self.assertIn("unexpected fixture precondition", source)
        self.assertIn("OR EXISTS (SELECT 1 FROM control.user_account)", precondition)
        self.assertNotIn(
            "FROM control.user_account\n          WHERE id IN", precondition
        )
        self.assertIn("https://fixture.invalid", source)
        self.assertIn("identity_kind = 'OIDC'", source)
        self.assertIn("identity_kind = 'LOCAL'", source)
        self.assertIn("password_hash IS NULL", source)
        self.assertIn("password_hash IS NOT NULL", source)
        self.assertIn("SELECT count(*) = 4", source)
        self.assertIn("AND id = '12000000-0000-4000-8000-000000000309'::uuid", source)
        self.assertIn("AND local_username = 'oap079a.denied'", source)
        self.assertIn(
            "(SELECT count(*) FROM control.platform_administrator) = 1", source
        )
        self.assertIn("SET ROLE slaif_owner", source)
        self.assertIn("membership_fingerprint", source)
        self.assertGreaterEqual(source.count(first), 4)
        self.assertGreaterEqual(source.count(second), 4)
        for path in (
            ROOT / "compose.yaml",
            ROOT / "services" / "backend" / "src",
            ROOT / "migrations",
        ):
            files = [path] if path.is_file() else list(path.rglob("*"))
            for candidate in files:
                if candidate.is_file():
                    text = candidate.read_text(encoding="utf-8", errors="ignore")
                    self.assertNotIn(first, text, str(candidate))
                    self.assertNotIn(second, text, str(candidate))

    def test_governance_project_orders_all_six_stable_devices(self) -> None:
        config = (ROOT / "playwright.config.ts").read_text(encoding="utf-8")
        self.assertEqual(config.count('name: "governance"'), 1)
        self.assertIn('dependencies: ["setup"]', config)
        self.assertEqual(config.count('dependencies: ["governance"]'), 14)
        for project in (
            "desktop-chromium",
            "desktop-firefox",
            "desktop-webkit",
            "tablet",
            "mobile-chromium",
            "mobile-webkit",
        ):
            self.assertIn(f'name: "{project}"', config)
        for project in (
            "agent-desktop-chromium",
            "agent-mobile-chromium",
            "agent-workspace-puck-desktop",
            "agent-workspace-puck-tablet",
            "freeze-review-snapshot",
            "review-surface",
            "accept-lifecycle",
            "discard-lifecycle",
        ):
            self.assertIn(f'name: "{project}"', config)
        governance = (ROOT / "tests/e2e/governance.spec.ts").read_text(encoding="utf-8")
        for marker in (
            "site-create-visible",
            "domain-primary-replace-visible",
            "membership-add-visible",
            "stale-ui-conflict-recovery",
            "crafted-membership-negatives",
            "archive-dialog-keyboard-visible",
            "privacy-csp-edge",
        ):
            self.assertIn(marker, governance)
        smoke = SMOKE.read_text(encoding="utf-8")
        self.assertIn("governance-restart: OK", smoke)
        self.assertIn("domain_fingerprint", smoke)

    def test_browser_worker_proof_is_durable_and_private(self) -> None:
        source = SMOKE.read_text(encoding="utf-8")
        for marker in (
            "browser-worker-runtime-policy: OK",
            "browser-worker-image-policy: OK",
            "browser-worker-dispatch: OK durable-runs=2 artifacts=agent-owned",
            "browser-worker-restart: OK durable-dispatch-artifacts=retained",
            "browser-worker-public-separation: OK durable-runs=2 completed=2",
            "browser-artifact-runtime-policy: OK files=",
            "browser-worker-cleanup: OK chromium-children=0",
            "browser-worker-secret-recovery: OK",
        ):
            self.assertEqual(source.count(marker), 1, marker)
        self.assertIn("baseline=int(sys.argv[1])", source)
        self.assertNotIn("slaif_agent_browser_run_claim", source)
        self.assertNotIn("slaif_agent_browser_run_complete", source)
        self.assertNotIn("slaif_agent_browser_artifact_register", source)

    def test_dispatch_fixture_uses_seeded_route_and_reports_terminal_failures(
        self,
    ) -> None:
        source = SMOKE.read_text(encoding="utf-8")
        self.assertIn('"route":"/s/parity/"', source)
        self.assertIn('ROUTE = "/s/parity/"', source)
        self.assertNotIn('"route":"/s/demo/home"', source)
        self.assertNotIn('ROUTE = "/s/demo/home"', source)
        self.assertIn("agent-browser-dispatch: terminal run=", source)
        self.assertIn('state in {"FAILED", "TIMED_OUT", "CANCELLED"}', source)


# ---------------------------------------------------------------------------
# External Docker boundary mock. The shim is a disposable shell script that
# emulates the exact docker CLI verbs the smoke.sh helper and the verify.py
# lifecycle operations invoke; its state lives in a private test directory.
# It is the only mocked boundary: verify.py, smoke.sh and the CLI run real.
# ---------------------------------------------------------------------------

SHIM = r"""#!/bin/sh
# External Docker boundary mock for the lifecycle evidence contract tests.
state=$LIFECYCLE_SHIM_STATE
cmd=$1
shift
case "$cmd" in
version)
    printf '28.0.0\n'
    exit 0
    ;;
create)
    printf '%s\n' "$@" >"$state/create-argv"
    name=
    while test $# -gt 0; do
        case "$1" in
        --name)
            name=$2
            shift 2
            ;;
        *)
            shift
            ;;
        esac
    done
    if test -f "$state/fail-create-$name"; then
        printf '%s\n' "$LIFECYCLE_SHIM_FOREIGN_ID"
        exit 1
    fi
    id=$(printf 'container:%s' "$name" | sha256sum | cut -d' ' -f1)
    mkdir -p "$state/containers"
    printf '%s\n' "$name" >"$state/containers/$id"
    printf '%s\n' "$id"
    exit 0
    ;;
start)
    id=$2
    if test ! -f "$state/containers/$id"; then
        exit 125
    fi
    if test -f "$state/start-fail-$id"; then
        exit 125
    fi
    printf 'started %s\n' "$id" >>"$state/events"
    rc=0
    if test -f "$state/body-rc"; then
        rc=$(cat "$state/body-rc")
    fi
    exit "$rc"
    ;;
rm)
    id=$1
    if test -f "$state/rm-fail-$id"; then
        exit 1
    fi
    if test ! -f "$state/containers/$id"; then
        exit 1
    fi
    rm -f "$state/containers/$id"
    printf 'removed %s\n' "$id" >>"$state/events"
    exit 0
    ;;
ps)
    filter=
    while test $# -gt 0; do
        case "$1" in
        --filter)
            filter=$2
            shift 2
            ;;
        --format)
            shift 2
            ;;
        *)
            shift
            ;;
        esac
    done
    case "$filter" in
    id=*)
        id=${filter#id=}
        if test -f "$state/ps-fail"; then
            exit 1
        fi
        if test -f "$state/containers/$id"; then
            printf '%s\n' "$id"
        fi
        exit 0
        ;;
    *)
        exit 0
        ;;
    esac
    ;;
inspect)
    fmt=
    id=
    while test $# -gt 0; do
        case "$1" in
        --format)
            fmt=$2
            shift 2
            ;;
        *)
            id=$1
            shift
            ;;
        esac
    done
    if test ! -f "$state/containers/$id"; then
        exit 1
    fi
    name=$(cat "$state/containers/$id")
    case "$fmt" in
    *"State.Status"*)
        if test -f "$state/events" && grep -q "^started $id$" "$state/events"; then
            rc=0
            if test -f "$state/body-rc"; then
                rc=$(cat "$state/body-rc")
            fi
            _fmt='%s\037/%s\037%s\037%s\037%s\037exited\037false\037%s\037%s\037%s\n'
            printf "$_fmt" \
                "$id" "$name" "$LIFECYCLE_SHIM_IMAGE" "$LIFECYCLE_SHIM_IMAGE_REF" \
                "$LIFECYCLE_SHIM_CREATED" "$rc" "$LIFECYCLE_SHIM_STARTED" \
                "$LIFECYCLE_SHIM_FINISHED"
        else
            _fmt='%s\037/%s\037%s\037%s\037%s\037created\037false\0370\037'
            _fmt="${_fmt}0001-01-01T00:00:00Z\0370001-01-01T00:00:00Z\n"
            printf "$_fmt" \
                "$id" "$name" "$LIFECYCLE_SHIM_IMAGE" "$LIFECYCLE_SHIM_IMAGE_REF" \
                "$LIFECYCLE_SHIM_CREATED"
        fi
        exit 0
        ;;
    *'range .Mounts'*)
        printf '\037/src/secrets\037/secrets\037bind\037true\n'
        exit 0
        ;;
    *com.docker.compose.project*)
        exit 0
        ;;
    *com.docker.compose.service*)
        exit 0
        ;;
    *)
        exit 1
        ;;
    esac
    ;;
run)
    printf '%s\n' "$@" >"$state/run-argv"
    rc=0
    if test -f "$state/body-rc"; then
        rc=$(cat "$state/body-rc")
    fi
    exit "$rc"
    ;;
*)
    printf 'shim: unsupported %s\n' "$cmd" >&2
    exit 64
    ;;
esac
"""

DRIVER_TEMPLATE = r"""#!/bin/sh
set -eu
ROOT=@ROOT@
PROJECT=slaif007ktest
NEGATIVE_PROJECT=slaif007ktestnegative
LIFECYCLE_DIR=@EVIDENCE@
LIFECYCLE_SCOPE=slaif007ktest
LIFECYCLE_ACTIVE=@ACTIVE@
@FUNCTIONS@
@SCENARIO@
"""


def docker_id_for(name):
    return hashlib.sha256(("container:" + name).encode()).hexdigest()


def extract_smoke_functions(names):
    source = SMOKE.read_text(encoding="utf-8")
    chunks = []
    for name in names:
        start = source.index(name + "() {")
        end = source.index("\n}\n", start) + 3
        chunks.append(source[start:end])
    return "\n".join(chunks)


def make_driver(tmp, scenario, active=1, functions=None):
    functions = functions or ("lifecycle", "helper_run")
    bin_dir = tmp / "bin"
    bin_dir.mkdir(mode=0o700)
    shim = bin_dir / "docker"
    shim.write_text(SHIM)
    shim.chmod(0o755)
    state = tmp / "state"
    state.mkdir(mode=0o700)
    evidence = tmp / "evidence"
    evidence.mkdir(mode=0o700)
    driver = tmp / "driver.sh"
    driver.write_text(
        DRIVER_TEMPLATE.replace("@ROOT@", str(ROOT))
        .replace("@EVIDENCE@", str(evidence))
        .replace("@ACTIVE@", str(active))
        .replace("@FUNCTIONS@", extract_smoke_functions(list(functions)))
        .replace("@SCENARIO@", scenario)
    )
    env = dict(os.environ)
    env["PATH"] = f"{Path(sys.executable).parent}:{bin_dir}:" + env.get("PATH", "")
    env["LIFECYCLE_SHIM_STATE"] = str(state)
    env["LIFECYCLE_SHIM_IMAGE"] = IMAGE_DIGEST
    env["LIFECYCLE_SHIM_IMAGE_REF"] = IMAGE_REF
    env["LIFECYCLE_SHIM_FOREIGN_ID"] = FOREIGN_ID
    env["LIFECYCLE_SHIM_CREATED"] = CREATED_AT
    env["LIFECYCLE_SHIM_STARTED"] = STARTED_AT
    env["LIFECYCLE_SHIM_FINISHED"] = FINISHED_AT
    return driver, state, evidence, env


def run_driver(tmp, scenario, active=1, functions=None):
    driver, state, evidence, env = make_driver(tmp, scenario, active, functions)
    proc = subprocess.run(
        ["sh", str(driver)],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    return proc, state, evidence


def helper_receipts(evidence, tag, cid):
    names = {
        "begin": V._lifecycle_helper_name(tag, "begin"),
        "created": V._lifecycle_helper_name(tag, "created", cid),
        "meta": V._lifecycle_helper_name(tag, "meta", cid),
        "start": V._lifecycle_helper_name(tag, "start", cid),
        "state": V._lifecycle_helper_name(tag, "state", cid),
        "removed": V._lifecycle_helper_name(tag, "removed", cid),
        "absent": V._lifecycle_helper_name(tag, "absent", cid),
        "complete": V._lifecycle_helper_name(tag, "complete"),
    }
    return {key: evidence / value for key, value in names.items()}


def extract_smoke_block(anchor: str, end_anchor: str) -> str:
    """Extract a verbatim production caller statement from the real source."""
    source = SMOKE.read_text(encoding="utf-8")
    start = source.index(anchor)
    end = source.index(end_anchor, start) + len(end_anchor)
    return source[start:end]


class LifecycleShellContractTests(unittest.TestCase):
    """The real smoke.sh helper and final callers run under the driver; only
    the external docker CLI is mocked. Incomplete capture must abort the
    driver before any denial or value branch can accept a result."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="lifecycle-shell-")
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def drive(self, scenario, active=1, functions=None, pre=None):
        driver, state, evidence, env = make_driver(
            self.tmp, scenario, active, functions
        )
        if pre is not None:
            pre(state)
        proc = subprocess.run(
            ["sh", str(driver)],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        return proc, state, evidence

    def flagset(self):
        return (
            "--network none --read-only --cap-drop ALL "
            "--cap-add DAC_READ_SEARCH --user 0:0 "
            "--entrypoint python slaif-agent-site-backend:local "
        )

    def test_genuine_body_exit_97_completes_and_audits(self) -> None:
        body = "import sys; sys.exit(97)"
        scenario = (
            'printf "97\\n" >"$LIFECYCLE_SHIM_STATE/body-rc"\n'
            "set +e\n"
            f'helper_run h-body97 "slaif007ktest-h-body97" '
            f"{self.flagset()}-c '{body}'\n"
            "rc=$?\n"
            "set -e\n"
            'test "$rc" = 97\n'
            "printf BODY97_OK\n"
        )
        proc, state, evidence = self.drive(scenario)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("BODY97_OK", proc.stdout)
        create_argv = (state / "create-argv").read_text().splitlines()
        self.assertEqual(
            create_argv,
            [
                "--name",
                "slaif007ktest-h-body97",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--cap-add",
                "DAC_READ_SEARCH",
                "--user",
                "0:0",
                "--entrypoint",
                "python",
                "slaif-agent-site-backend:local",
                "-c",
                body,
            ],
        )
        cid = docker_id_for("slaif007ktest-h-body97")
        names = helper_receipts(evidence, "h-body97", cid)
        for key, path in names.items():
            self.assertTrue(path.is_file(), key)
        complete = V._read_evidence_record(evidence, names["complete"].name)
        self.assertEqual(
            (
                complete["start_rc"],
                complete["body_exit"],
                complete["rm_rc"],
                complete["ps_rc"],
            ),
            (97, 97, 0, 0),
        )
        V._lifecycle_audit_helpers(PROJECT, SCOPE, evidence, ["h-body97"])

    def test_default_mode_preserves_exact_original_argv(self) -> None:
        body = "print(1)"
        scenario = (
            'helper_run h-argv "slaif007ktest-h-argv" --network none '
            "--read-only --cap-drop ALL --cap-add DAC_READ_SEARCH --user 0:0 "
            '--volume "slaif007ktest_local-secrets:/secrets:ro" '
            "--entrypoint python slaif-agent-site-backend:local "
            f"-c '{body}'\n"
        )
        proc, state, evidence = self.drive(scenario, active=0)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        argv = (state / "run-argv").read_text().splitlines()
        self.assertEqual(
            argv,
            [
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--cap-add",
                "DAC_READ_SEARCH",
                "--user",
                "0:0",
                "--volume",
                "slaif007ktest_local-secrets:/secrets:ro",
                "--entrypoint",
                "python",
                "slaif-agent-site-backend:local",
                "-c",
                body,
            ],
        )
        self.assertEqual(len(argv), 17)
        self.assertEqual(list(evidence.iterdir()), [])

    def test_failed_create_never_adopts_foreign_stdout(self) -> None:
        name = "slaif007ktest-h-createfail"
        scenario = (
            f'helper_run h-createfail "{name}" --network none --read-only '
            "--entrypoint python slaif-agent-site-backend:local -c 'print(1)'\n"
        )

        def pre(state):
            (state / f"fail-create-{name}").write_text("")

        proc, state, evidence = self.drive(scenario, pre=pre)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        failed = V._read_evidence_record(
            evidence, V._lifecycle_helper_name("h-createfail", "created-failed")
        )
        self.assertEqual(
            set(failed),
            {"project", "tag", "invocation", "source_point", "name", "create_rc"},
        )
        self.assertEqual(failed["create_rc"], 1)
        cid = docker_id_for(name)
        for point in ("created", "meta", "start", "state", "removed", "absent"):
            self.assertFalse(
                (
                    evidence / V._lifecycle_helper_name("h-createfail", point, cid)
                ).is_file()
            )
        self.assertFalse(
            (evidence / V._lifecycle_helper_name("h-createfail", "complete")).is_file()
        )
        self.assertFalse((state / "events").exists())
        self.assertFalse((state / "containers").exists())
        for path in evidence.iterdir():
            self.assertNotIn(FOREIGN_ID.encode(), path.read_bytes())

    def test_start_failure_with_created_terminal_is_infrastructure(self) -> None:
        name = "slaif007ktest-h-startfail"
        cid = docker_id_for(name)
        scenario = (
            f'helper_run h-startfail "{name}" --network none --read-only '
            "--entrypoint python slaif-agent-site-backend:local -c 'print(1)'\n"
        )

        def pre(state):
            (state / f"start-fail-{cid}").write_text("")

        proc, state, evidence = self.drive(scenario, pre=pre)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        names = helper_receipts(evidence, "h-startfail", cid)
        start = V._read_evidence_record(evidence, names["start"].name)
        self.assertEqual(start["start_rc"], 125)
        state_rec = V._read_evidence_record(evidence, names["state"].name)
        self.assertEqual(state_rec["state"]["status"], "created")
        self.assertEqual(state_rec["state"]["started_at"], ZERO_TIME)
        self.assertEqual(state_rec["state"]["finished_at"], ZERO_TIME)
        self.assertFalse(names["complete"].is_file())
        with self.assertRaises(ValueError):
            V._lifecycle_audit_helpers(PROJECT, SCOPE, evidence, ["h-startfail"])

    def test_genuine_body_exit_125_completes(self) -> None:
        name = "slaif007ktest-h-body125"
        scenario = (
            'printf "125\\n" >"$LIFECYCLE_SHIM_STATE/body-rc"\n'
            "set +e\n"
            f'helper_run h-body125 "{name}" --network none --read-only '
            "--entrypoint python slaif-agent-site-backend:local "
            "-c 'import sys; sys.exit(125)'\n"
            "rc=$?\n"
            "set -e\n"
            'test "$rc" = 125\n'
            "printf BODY125_OK\n"
        )
        proc, state, evidence = self.drive(scenario)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("BODY125_OK", proc.stdout)
        cid = docker_id_for(name)
        names = helper_receipts(evidence, "h-body125", cid)
        complete = V._read_evidence_record(evidence, names["complete"].name)
        self.assertEqual((complete["start_rc"], complete["body_exit"]), (125, 125))
        V._lifecycle_audit_helpers(PROJECT, SCOPE, evidence, ["h-body125"])

    def test_rm_failure_preserves_residual_and_blocks_completion(self) -> None:
        name = "slaif007ktest-h-rmfail"
        cid = docker_id_for(name)
        scenario = (
            f'helper_run h-rmfail "{name}" --network none --read-only '
            "--entrypoint python slaif-agent-site-backend:local -c 'print(1)'\n"
        )

        def pre(state):
            (state / f"rm-fail-{cid}").write_text("")

        proc, state, evidence = self.drive(scenario, pre=pre)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        names = helper_receipts(evidence, "h-rmfail", cid)
        removed = V._read_evidence_record(evidence, names["removed"].name)
        self.assertEqual(removed["rm_rc"], 1)
        self.assertFalse(names["absent"].is_file())
        self.assertFalse(names["complete"].is_file())
        self.assertTrue((state / "containers" / cid).is_file())
        with self.assertRaises(ValueError):
            V._lifecycle_audit_helpers(PROJECT, SCOPE, evidence, ["h-rmfail"])

    def test_failed_absence_query_is_not_absence(self) -> None:
        name = "slaif007ktest-h-psfail"
        cid = docker_id_for(name)
        scenario = (
            f'helper_run h-psfail "{name}" --network none --read-only '
            "--entrypoint python slaif-agent-site-backend:local -c 'print(1)'\n"
        )

        def pre(state):
            (state / "ps-fail").write_text("")

        proc, state, evidence = self.drive(scenario, pre=pre)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        names = helper_receipts(evidence, "h-psfail", cid)
        removed = V._read_evidence_record(evidence, names["removed"].name)
        self.assertEqual(removed["rm_rc"], 0)
        self.assertFalse(names["absent"].is_file())
        self.assertFalse(names["complete"].is_file())
        self.assertFalse((state / "containers" / cid).exists())
        with self.assertRaises(ValueError):
            V._lifecycle_audit_helpers(PROJECT, SCOPE, evidence, ["h-psfail"])

    def test_real_denial_caller_aborts_on_incomplete_capture(self) -> None:
        block = extract_smoke_block("if helper_run h-secret-neg ", "\nfi")
        cid = docker_id_for("slaif007ktest-h-secret-neg")

        def pre(state):
            (state / f"rm-fail-{cid}").write_text("")

        proc, state, evidence = self.drive(
            block + "\nprintf SECRET_NEG_REACHED\n", pre=pre
        )
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn("SECRET_NEG_REACHED", proc.stdout)
        self.assertNotIn(
            "unrelated uid unexpectedly read a secret",
            proc.stdout + proc.stderr,
        )
        names = helper_receipts(evidence, "h-secret-neg", cid)
        removed = V._read_evidence_record(evidence, names["removed"].name)
        self.assertEqual(removed["rm_rc"], 1)
        self.assertFalse(names["complete"].is_file())
        with self.assertRaises(ValueError):
            V._lifecycle_audit_helpers(PROJECT, SCOPE, evidence, ["h-secret-neg"])

    def test_real_value_caller_aborts_before_comparison(self) -> None:
        block = extract_smoke_block(
            "check1_render=$(render_fingerprint h-render-fingerprint-check1)",
            'test "$check1_secrets" = "$before"',
        )
        cid = docker_id_for("slaif007ktest-h-fingerprint-check1")

        def pre(state):
            (state / f"rm-fail-{cid}").write_text("")

        scenario = (
            "before=placeholder\nrender_before=placeholder\n"
            + block
            + "\nprintf CHECK1_REACHED\n"
        )
        proc, state, evidence = self.drive(
            scenario,
            functions=(
                "lifecycle",
                "helper_run",
                "fingerprint",
                "render_fingerprint",
            ),
            pre=pre,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn("CHECK1_REACHED", proc.stdout)
        names = helper_receipts(evidence, "h-fingerprint-check1", cid)
        removed = V._read_evidence_record(evidence, names["removed"].name)
        self.assertEqual(removed["rm_rc"], 1)
        self.assertFalse(names["complete"].is_file())
        with self.assertRaises(ValueError):
            V._lifecycle_audit_helpers(
                PROJECT, SCOPE, evidence, ["h-fingerprint-check1"]
            )


def _fake_docker(cid, name, body_rc):
    """Mock only the Docker boundary for in-process producer round-trips.

    A never-started container reports the zero time for BOTH StartedAt and
    FinishedAt, as the pinned engine does; an executed container reports the
    body's own 0..255 native.
    """
    state = {"started": False, "removed": False}

    def fake(argv, root):
        verb = argv[1]
        if verb == "inspect":
            template = argv[argv.index("--format") + 1]
            if template == V.CONTAINER_PROJECTION_TEMPLATE:
                if state["started"]:
                    fields = [
                        cid,
                        "/" + name,
                        IMAGE_DIGEST,
                        IMAGE_REF,
                        CREATED_AT,
                        "exited",
                        "false",
                        str(body_rc),
                        STARTED_AT,
                        FINISHED_AT,
                    ]
                else:
                    fields = [
                        cid,
                        "/" + name,
                        IMAGE_DIGEST,
                        IMAGE_REF,
                        CREATED_AT,
                        "created",
                        "false",
                        "0",
                        ZERO_TIME,
                        ZERO_TIME,
                    ]
                return 0, SEP.join(fields) + "\n"
            if template == V.CONTAINER_MOUNTS_TEMPLATE:
                return 0, MOUNTS_LINE
            return 0, "\n"
        if verb == "rm":
            if argv[2] != cid:
                raise AssertionError("rm target is not the owned id")
            state["removed"] = True
            return 0, ""
        if verb == "ps":
            want = argv[argv.index("--filter") + 1]
            if want != "id=" + cid:
                return 1, ""
            return 0, "" if state["removed"] else cid + "\n"
        raise AssertionError("unexpected docker verb")

    def mark_started():
        # The shell's `docker start -a` completed with the body's native.
        state["started"] = True

    return fake, mark_started


class LifecycleProducerContractTests(unittest.TestCase):
    """Real verify.py producers/readers/auditors; only _lifecycle_run, the
    Docker boundary, is mocked. No fabricated-receipt-only oracle."""

    def mk_evidence(self, base, name):
        ev = base / name
        ev.mkdir(mode=0o700)
        return ev

    def run_chain(self, ev, tag, name, cid, start_rc, body_rc=None, started=True):
        fake, mark_started = _fake_docker(
            cid, name, start_rc if body_rc is None else body_rc
        )
        with mock.patch.object(V, "_lifecycle_run", fake):
            V._lifecycle_helper_begin(ROOT, PROJECT, SCOPE, tag, name, ev)
            V._lifecycle_helper_created(ROOT, PROJECT, SCOPE, tag, name, cid, 0, ev)
            if started:
                mark_started()
            V._lifecycle_helper_start(ROOT, PROJECT, SCOPE, tag, cid, start_rc, ev)
            V._lifecycle_helper_terminal(ROOT, PROJECT, SCOPE, tag, cid, ev)
            V._lifecycle_helper_remove(ROOT, PROJECT, SCOPE, tag, cid, ev)

    def test_full_body_range_round_trips_through_real_producers(self) -> None:
        base = Path(tempfile.mkdtemp(prefix="lifecycle-rt-"))
        try:
            for code in range(256):
                with self.subTest(code=code):
                    tag = f"rt-{code:03d}"
                    name = f"slaif007ktest-{tag}"
                    cid = hashlib.sha256(f"roundtrip-{code}".encode()).hexdigest()
                    ev = self.mk_evidence(base, tag)
                    self.run_chain(ev, tag, name, cid, code)
                    V._lifecycle_helper_complete(
                        ROOT, PROJECT, SCOPE, tag, name, cid, code, code, ev
                    )
                    complete = V._read_evidence_record(
                        ev, V._lifecycle_helper_name(tag, "complete")
                    )
                    self.assertEqual(
                        (
                            complete["start_rc"],
                            complete["body_exit"],
                            complete["rm_rc"],
                            complete["ps_rc"],
                        ),
                        (code, code, 0, 0),
                    )
                    V._lifecycle_audit_helpers(PROJECT, SCOPE, ev, [tag])
        finally:
            shutil.rmtree(base)

    def test_start_failure_with_created_terminal_is_infrastructure(self) -> None:
        base = Path(tempfile.mkdtemp(prefix="lifecycle-rt-"))
        try:
            tag, name = "inf125", "slaif007ktest-inf125"
            cid = hashlib.sha256(b"roundtrip-inf125").hexdigest()
            ev = self.mk_evidence(base, tag)
            self.run_chain(ev, tag, name, cid, 125, started=False)
            with self.assertRaises(ValueError):
                V._lifecycle_helper_complete(
                    ROOT, PROJECT, SCOPE, tag, name, cid, 125, 125, ev
                )
            self.assertFalse((ev / V._lifecycle_helper_name(tag, "complete")).is_file())
            with self.assertRaises(ValueError):
                V._lifecycle_audit_helpers(PROJECT, SCOPE, ev, [tag])
        finally:
            shutil.rmtree(base)

    def test_terminal_native_mismatch_is_rejected(self) -> None:
        base = Path(tempfile.mkdtemp(prefix="lifecycle-rt-"))
        try:
            tag, name = "mis98", "slaif007ktest-mis98"
            cid = hashlib.sha256(b"roundtrip-mis98").hexdigest()
            ev = self.mk_evidence(base, tag)
            self.run_chain(ev, tag, name, cid, 97, body_rc=98)
            with self.assertRaises(ValueError):
                V._lifecycle_helper_complete(
                    ROOT, PROJECT, SCOPE, tag, name, cid, 97, 97, ev
                )
            self.assertFalse((ev / V._lifecycle_helper_name(tag, "complete")).is_file())
        finally:
            shutil.rmtree(base)

    def cli(self, evidence, *args):
        return subprocess.run(
            [
                sys.executable,
                str(VERIFY),
                "--root",
                str(ROOT),
                "--project",
                PROJECT,
                "--lifecycle-evidence",
                str(evidence),
                "--scope",
                SCOPE,
                *args,
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_cli_dispatch_and_arg_contract(self) -> None:
        base = Path(tempfile.mkdtemp(prefix="lifecycle-cli-"))
        try:
            ev = self.mk_evidence(base, "chain")
            tag, name = "cli-tag", "slaif007ktest-cli-tag"
            cid = hashlib.sha256(b"roundtrip-cli").hexdigest()
            self.run_chain(ev, tag, name, cid, 0)
            V._lifecycle_helper_complete(ROOT, PROJECT, SCOPE, tag, name, cid, 0, 0, ev)
            result = self.cli(
                ev, "--lifecycle-operation", "audit-helpers", "--tag", tag
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self.cli(
                ev,
                "--lifecycle-operation",
                "audit-helpers",
                "--tag",
                "cli-other",
            )
            self.assertEqual(result.returncode, 1)
            result = self.cli(
                ev,
                "--lifecycle-operation",
                "helper-begin",
                "--tag",
                tag,
                "--tag",
                tag,
                "--name",
                name,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("exactly once", result.stderr)
            result = self.cli(ev, "--lifecycle-operation", "bogus")
            self.assertEqual(result.returncode, 1)
            self.assertIn("unknown", result.stderr)
        finally:
            shutil.rmtree(base)

    def test_cli_requires_evidence_binding(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VERIFY),
                "--root",
                str(ROOT),
                "--project",
                PROJECT,
                "--lifecycle-operation",
                "audit-helpers",
                "--tag",
                "x",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("evidence binding is missing", result.stderr)

    def test_mount_projection_requires_real_values_but_allows_tmpfs(self) -> None:
        ok = V._lifecycle_project_mounts(
            SEP + SEP + "/dest" + SEP + "tmpfs" + SEP + "true\n"
        )
        self.assertEqual(ok[0]["source"], "")
        self.assertIsNone(ok[0]["name"])
        bad = (
            SEP + TEMPLATE_SENTINEL + SEP + "/dest" + SEP + "tmpfs" + SEP + "true\n",
            "/src" + SEP + SEP + SEP + "tmpfs" + SEP + "true\n",
            "/src" + SEP + "/dest" + SEP + TEMPLATE_SENTINEL + SEP + "true\n",
            "/src" + SEP + "/dest" + SEP + "tmpfs" + SEP + "maybe\n",
            "/src" + SEP + "/dest" + SEP + "tmpfs" + SEP + "true\n",
            "/src" + SEP + "/dest" + SEP + "tmpfs" + SEP + "true" + SEP + "x\n",
        )
        for line in bad:
            with self.subTest(line=line), self.assertRaises(ValueError):
                V._lifecycle_project_mounts(line)

    def test_container_and_state_projections_reject_unpinned_values(self) -> None:
        good = [
            "a" * 64,
            "/cli-name",
            IMAGE_DIGEST,
            IMAGE_REF,
            CREATED_AT,
            "exited",
            "false",
            "0",
            STARTED_AT,
            FINISHED_AT,
        ]
        record = V._lifecycle_container_record(
            list(good), [], None, None, "helper-created"
        )
        V._lifecycle_validate_flat_meta(record, "helper-created")
        bad = (
            ["b" * 63, *good[1:]],
            [good[0], "no-slash", *good[2:]],
            [good[0], "/a/b", *good[2:]],
            [good[0], good[1], "ab" * 32, *good[3:]],
            [good[0], good[1], good[2], TEMPLATE_SENTINEL, *good[4:]],
            [good[0], good[1], good[2], good[3], TEMPLATE_SENTINEL, *good[5:]],
            good[:9],
        )
        for fields in bad:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                V._lifecycle_container_record(
                    list(fields), [], None, None, "helper-created"
                )
        state_good = ["exited", "false", "0", STARTED_AT, FINISHED_AT]
        for fields in (
            ["stopped", *state_good[1:]],
            ["exited", "maybe", *state_good[2:]],
            ["exited", "false", "x", *state_good[3:]],
            ["exited", "false", "0", TEMPLATE_SENTINEL, FINISHED_AT],
            ["exited", "false", "0", STARTED_AT, TEMPLATE_SENTINEL],
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                V._lifecycle_project_state(fields)

    def test_volume_and_network_optional_fields_are_honest(self) -> None:
        record = V._lifecycle_volume_record(
            SEP.join(["vol-a", "local", "/mp", CREATED_AT]) + "\n", "capture"
        )
        self.assertEqual(record["created"], CREATED_AT)
        absent = V._lifecycle_volume_record(
            SEP.join(["vol-a", "local", TEMPLATE_SENTINEL, TEMPLATE_SENTINEL]) + "\n",
            "capture",
        )
        self.assertIsNone(absent["mountpoint"])
        self.assertIsNone(absent["created"])
        with self.assertRaises(ValueError):
            V._lifecycle_volume_record(
                SEP.join(["vol-a", TEMPLATE_SENTINEL, "/mp", CREATED_AT]) + "\n",
                "capture",
            )
        net = V._lifecycle_network_record(
            SEP.join(["c" * 64, "net-a", CREATED_AT]) + "\n", "capture"
        )
        self.assertEqual(net["id"], "c" * 64)
        with self.assertRaises(ValueError):
            V._lifecycle_network_record(
                SEP.join(["c" * 64, "net-a", TEMPLATE_SENTINEL]) + "\n",
                "capture",
            )

    def test_reader_rejects_mutated_flat_meta(self) -> None:
        good = [
            "a" * 64,
            "/cli-name",
            IMAGE_DIGEST,
            IMAGE_REF,
            CREATED_AT,
            "exited",
            "false",
            "0",
            STARTED_AT,
            FINISHED_AT,
        ]
        base = V._lifecycle_container_record(
            list(good), [], None, None, "helper-created"
        )
        base["mounts"] = [
            {
                "name": None,
                "source": "",
                "destination": "/d",
                "type": "tmpfs",
                "rw": True,
            }
        ]
        V._lifecycle_validate_flat_meta(base, "helper-created")

        def mutated():
            return json.loads(json.dumps(base))

        record = mutated()
        record["mounts"][0]["source"] = TEMPLATE_SENTINEL
        with self.assertRaises(ValueError):
            V._lifecycle_validate_flat_meta(record, "helper-created")
        record = mutated()
        record["mounts"][0]["destination"] = TEMPLATE_SENTINEL
        with self.assertRaises(ValueError):
            V._lifecycle_validate_flat_meta(record, "helper-created")
        record = mutated()
        record["state"]["started_at"] = TEMPLATE_SENTINEL
        with self.assertRaises(ValueError):
            V._lifecycle_validate_flat_meta(record, "helper-created")
        record = mutated()
        record["state"]["status"] = "stopped"
        with self.assertRaises(ValueError):
            V._lifecycle_validate_flat_meta(record, "helper-created")
        record = mutated()
        record["extra"] = 1
        with self.assertRaises(ValueError):
            V._lifecycle_validate_flat_meta(record, "helper-created")
        with self.assertRaises(ValueError):
            V._lifecycle_validate_flat_meta(mutated(), "helper-terminal")

    def test_writer_hostile_file_contract(self) -> None:
        base = Path(tempfile.mkdtemp(prefix="lifecycle-hostile-"))
        try:

            def priv(name, mode=0o700):
                path = base / name
                path.mkdir(mode=mode)
                path.chmod(mode)
                return path

            public = priv("public", 0o755)
            with self.assertRaises(ValueError):
                V._write_evidence_record(public, "helper-a.json", {"a": 1})
            self.assertFalse((public / "helper-a.json").exists())

            ev = priv("ev")
            target = base / "target.json"
            target.write_text("x")
            (ev / "helper-sym.json").symlink_to(target)
            with self.assertRaises(ValueError):
                V._write_evidence_record(ev, "helper-sym.json", {"a": 1})
            self.assertEqual(target.read_text(encoding="utf-8"), "x")

            (ev / "helper-collide.json").write_text("x")
            with self.assertRaises(ValueError):
                V._write_evidence_record(ev, "helper-collide.json", {"a": 1})

            for relpath in ("a/b.json", "../up.json", "bad name.json"):
                with self.subTest(relpath=relpath), self.assertRaises(ValueError):
                    V._write_evidence_record(ev, relpath, {"a": 1})
            with self.assertRaises(ValueError):
                V._write_evidence_record(ev, "helper-nondict.json", [1, 2])
            with self.assertRaises(ValueError):
                V._write_evidence_record(
                    ev, "helper-big.json", {"a": "x" * V.RECEIPT_MAX_BYTES}
                )
            self.assertFalse((ev / "helper-big.json").exists())

            close_ev = priv("close")
            real_close = os.close
            attempted = []
            refused = []

            def flaky_close(fd):
                attempted.append(fd)
                if len(attempted) == 1:
                    refused.append(fd)
                    raise OSError("simulated close failure")
                return real_close(fd)

            try:
                with mock.patch("os.close", side_effect=flaky_close):
                    with self.assertRaises(ValueError):
                        V._write_evidence_record(
                            close_ev, "helper-close.json", {"a": 1}
                        )
                # Every owned descriptor must be attempted after the first
                # close failure: the evidence-dir components plus the leaf.
                self.assertEqual(len(attempted), len(list(close_ev.parts)) + 1)
                self.assertEqual(refused, [attempted[0]])
                for fd in attempted[1:]:
                    with self.assertRaises(OSError):
                        os.fstat(fd)
                os.fstat(refused[0])  # the simulated failure left it open
                self.assertTrue((close_ev / "helper-close.json").is_file())
                record = V._read_evidence_record(close_ev, "helper-close.json")
                self.assertEqual(record, {"a": 1})
            finally:
                # Release the test-owned descriptor left open by the
                # simulated close failure, even if an assertion failed;
                # no production close is retried.
                if refused:
                    real_close(refused[0])
        finally:
            shutil.rmtree(base)

    def test_reader_hostile_file_contract(self) -> None:
        base = Path(tempfile.mkdtemp(prefix="lifecycle-hostile-"))
        try:
            ev = base / "ev"
            ev.mkdir(mode=0o700)

            def raw(name, payload: bytes):
                path = ev / name
                fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                try:
                    view = memoryview(payload)
                    while view:
                        written = os.write(fd, view)
                        view = view[written:]
                finally:
                    os.close(fd)
                return path

            path = raw(
                "helper-mode.json", b'{"record": {"a": 1}, "time_ns": 1, "utc": "x"}\n'
            )
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                V._read_evidence_record(ev, "helper-mode.json")

            (ev / "helper-dir.json").mkdir()
            with self.assertRaises(ValueError):
                V._read_evidence_record(ev, "helper-dir.json")

            cases = (
                (
                    "helper-dup.json",
                    b'{"record": {"a": 1, "a": 2}, "time_ns": 1, "utc": "x"}\n',
                ),
                (
                    "helper-nan.json",
                    b'{"record": {"a": NaN}, "time_ns": 1, "utc": "x"}\n',
                ),
                ("helper-utf8.json", b"\xff\xfe"),
                ("helper-envelope.json", b'{"record": {"a": 1}, "utc": "x"}\n'),
                (
                    "helper-booltime.json",
                    b'{"record": {"a": 1}, "time_ns": true, "utc": "x"}\n',
                ),
            )
            for name, payload in cases:
                raw(name, payload)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    V._read_evidence_record(ev, name)
        finally:
            shutil.rmtree(base)


class LifecycleSourceCoverageTests(unittest.TestCase):
    def test_every_helper_tag_is_on_the_static_audit_list(self) -> None:
        source = SMOKE.read_text(encoding="utf-8")
        used = set(re.findall(r"\bhelper_run\s+(h-[a-z0-9-]+)", source))
        used |= set(re.findall(r"\bfingerprint\s+(h-[a-z0-9-]+)", source))
        used |= set(re.findall(r"\brender_fingerprint\s+(h-[a-z0-9-]+)", source))
        start = source.index("lifecycle audit-helpers")
        end = source.index("\nLIFECYCLE_MAIN_DONE=1", start)
        listed = set(re.findall(r"--tag\s+(h-[a-z0-9-]+)", source[start:end]))
        self.assertEqual(used, listed)
        self.assertEqual(len(listed), 32)

    def test_default_mode_is_the_only_plain_docker_run(self) -> None:
        source = SMOKE.read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"(?m)^\s*docker run", source)), 1)
