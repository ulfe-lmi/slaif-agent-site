"""Static safety contract for the bounded PostgreSQL base transition test."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "tests/packaging/postgres-base-transition.sh"
OLD_IMAGE = (
    "docker.io/library/postgres:18.6-trixie@sha256:"
    "06cad38a5d9f5d24b4d83d86def30795d5e4b757fedbf5281172b576dedcd941"
)
NEW_IMAGE = (
    "docker.io/library/postgres:18.6-alpine3.23@sha256:"
    "697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f"
)


class PostgresBaseTransitionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.script = SCRIPT.read_text(encoding="utf-8")
        self.policy = json.loads(
            (ROOT / "supply-chain/policy.json").read_text(encoding="utf-8")
        )

    def test_exact_transition_is_shared_by_script_policy_and_compose(self) -> None:
        transition = self.policy["historical_oci_transitions"][
            "postgres-18.6-trixie-to-alpine3.23"
        ]
        self.assertEqual(transition["from"], OLD_IMAGE)
        self.assertEqual(transition["to"], NEW_IMAGE)
        self.assertEqual(self.policy["oci_sources"]["postgres"], NEW_IMAGE)
        self.assertIn(f"OLD_IMAGE='{OLD_IMAGE}'", self.script)
        self.assertIn(f"NEW_IMAGE='{NEW_IMAGE}'", self.script)
        compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn(NEW_IMAGE.removeprefix("docker.io/library/"), compose)
        self.assertNotIn(OLD_IMAGE, compose)

    def test_script_has_exact_cleanup_and_no_destructive_escape(self) -> None:
        self.assertIn("set -eu", self.script)
        self.assertIn("trap cleanup EXIT", self.script)
        self.assertIn('docker volume rm "$DATA_VOLUME"', self.script)
        self.assertIn('docker network rm "$NETWORK"', self.script)
        self.assertIn('rmdir "$CREDENTIAL_DIR"', self.script)
        self.assertIn("*[!a-z0-9]*", self.script)
        for forbidden in (
            "docker system prune",
            "docker volume prune",
            "docker container prune",
            "pg_upgrade",
            "pg_dump",
            "pg_restore",
            "POSTGRES_INITDB_ARGS",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.script)
        self.assertIsNone(re.search(r"(?im)^\s*reindex\b", self.script))
        self.assertIsNone(re.search(r"(?im)^\s*alter\s+database.*refresh", self.script))

    def test_transition_is_a_required_compose_job_step(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        invocation = (
            "sh tests/packaging/postgres-base-transition.sh slaif008transitionci"
        )
        self.assertIn(invocation, " ".join(workflow.split()))
        self.assertNotRegex(workflow, r"(?s)Prove PostgreSQL.*continue-on-error")


if __name__ == "__main__":
    unittest.main()
