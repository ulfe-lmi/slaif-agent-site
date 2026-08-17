# OAP Work Order — 008-b

## Objective

Amend existing PR `#11` with one narrowly bounded result: prove whether the
persistent PostgreSQL data volume created by the accepted objective-007 image
can be started and validated safely by the Alpine PostgreSQL image proposed in
008-a.

The exact transition is:

```text
from postgres:18.6-trixie
sha256:06cad38a5d9f5d24b4d83d86def30795d5e4b757fedbf5281172b576dedcd941

to postgres:18.6-alpine3.23
sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f
```

If the transition is not demonstrably safe, stop and report `PARTIAL`. Do not
redesign the image family, add an exception, dump/restore automatically,
discard a volume, or launch another broad remediation campaign.

## Hard execution budget

This continuation is intentionally capped.

- Target executor duration: at most 60 minutes.
- Maximum targeted transition-test attempts: 3.
- Maximum implementation commits/check generations: 2.
- Local complete `tools/supply_chain/run.sh` executions authorized: 0.
- Full six-image local rebuild/SBOM/Grype cycles authorized: 0.
- GitHub's existing supply-chain job will provide the one authoritative full
  regression after push.

If the cap is reached, publish a truthful `PARTIAL` report. Do not continue
retrying.

## GitHub objective state

- Numeric objective: `008`
- Execution round: `008-b`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#11`
- Existing PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/11>
- Required head branch: `oap/008-supply-chain-build-gates`
- Base branch: `main`
- Required PR title:
  `[OAP 008] Add reproducible supply-chain and SBOM gates`
- Current remote PR head:
  `f83c13243694b990231936bfec77dd0b7569c554`
- Previous implementation head:
  `9c732921e6c04eb21bf385cdd5964055bd8ed3eb`
- Repository: `ulfe-lmi/slaif-agent-site`
- Required delivery: amend PR `#11`; no new PR.

All 20 checks on the 008-a report head are currently successful and open
CodeQL alerts are zero. Preserve the 008-a order/report exactly.

## Strategic finding

008-a changed the persistent database runtime from Debian/glibc
`postgres:18.6-trixie` to Alpine/musl `postgres:18.6-alpine3.23` to satisfy the
zero-Critical policy. The PostgreSQL major and patch version stayed at 18.6,
but libc, locale, collation, OS packages, and entrypoint environment changed.

Objective 007 had already established a named persistent `postgres-data`
volume. The 008-a clean-start tests create only new Alpine volumes; they do not
prove that a volume initialized by the previously accepted Trixie image starts
cleanly, preserves data and role/bootstrap state, or has compatible
locale/collation metadata. This is a merge blocker until tested or explicitly
accepted by the human.

The postmortem also found that container OS/runtime license evidence is
retained in a 14-day CI artifact rather than the committed Python/npm notice.
Do not expand this continuation to solve release-notice packaging. Add/retain
an explicit documentation gate that image publication requires durable OS
license/source-offer review; actual release packaging belongs to a later
release objective.

## Allowed path scope

Only these paths may change, plus the new order/report and active pointer:

```text
.github/workflows/ci.yml
README.md
docs/DEPLOYMENT.md
docs/OPERATIONS.md
docs/SUPPLY_CHAIN.md
supply-chain/policy.json
tests/packaging/postgres-base-transition.sh
tests/packaging/test_postgres_base_transition.py
tests/packaging/test_oci_contract.py
tests/supply_chain/test_policy.py
tools/compose/verify.py
tools/supply_chain/policy.py
oap/active
oap/orders/008-b-prove-postgres-base-transition.md
oap/reports/008-b-prove-postgres-base-transition.md
```

Prefer fewer paths. Do not change `compose.yaml`, a Dockerfile, either lock,
application code, database migration/bootstrap semantics, vulnerability/
license exception files, scanner scripts, notices, service topology, action
pins, or prior OAP artifacts.

## Required transition test

Create one exact, bounded, disposable integration test using a unique validated
Docker project/container/network/volume prefix. It must:

1. Pull/verify both exact readable-tag-plus-digest PostgreSQL references.
2. Initialize a fresh named data volume with the old Trixie image using fake
   generated local credentials and its actual default locale/init behavior.
3. Run the current one-shot role/migration/COW bootstrap against that old
   server so the volume contains the exact accepted `006_001`, ten privilege
   roles, ten login principals, and `EMPTY_SAFE safe=true` state.
4. Add test-only representative persistent data outside the protected empty
   `content` schema: Unicode text, ordered text/index behavior, numeric,
   timestamp, JSONB, primary/foreign-key rows, and a deterministic digest.
5. Record non-secret pre-transition facts:
   - PostgreSQL version and control-data compatibility fields;
   - database encoding, locale provider, collation/ctype, stored collation
     version, and actual collation version where supported;
   - schema/migration/bootstrap marker;
   - role/login membership and privilege validation result;
   - representative row/index/query digest.
6. Stop the old server cleanly without removing or modifying the named data
   volume.
7. Start the new exact Alpine image against that same volume and the same fake
   password file. Do not run `initdb`, `pg_upgrade`, dump/restore, reset,
   `REINDEX`, collation refresh, or any repair before validation.
8. Prove the new server reaches healthy/read-write state and preserves every
   recorded schema, role, marker, row, constraint, index/query, and digest.
9. Re-run current bootstrap `validate` and local-login validation without
   mutation; both must remain safe.
10. Compare the before/after locale/collation facts and inspect startup/server
    logs. Any version mismatch, incompatible locale/provider, collation warning,
    invalid index warning, data-directory warning, checksum/query difference,
    or required repair is a failed compatibility result.
11. Restart the Alpine server once more on the unchanged volume and repeat the
    essential health/data/marker checks.
12. Remove only the exact disposable containers/network/volume and temporary
    credential directory, even after failure.

The test must not print passwords, DSNs, or a digest derived from secret
values. It must never inspect or mutate the operator's normal Compose volumes.

## Policy and CI integration

- Record the old Trixie reference as immutable historical transition evidence
  in the machine policy without making it a current build input.
- Validate that current and historical references are exact full digests and
  that the transition pair cannot silently drift.
- Add the transition test to the existing Compose/packaging CI job. It must run
  once per relevant PR head and cannot be marked optional or skipped.
- Existing clean Compose, supply-chain, Python, PostgreSQL, Node, Markdown,
  Mermaid, dependency-review, and CodeQL gates remain unchanged.
- Do not rerun the full local supply-chain gate. Run only the focused transition
  test, its static/unit policy tests, and fast directly affected checks before
  pushing.

## Attempt ledger

The 008-b report must include every targeted attempt, including successful and
failed attempts:

```text
attempt number
start/end or duration
exact stage reached
PASS/FAIL
root cause
code/config change made afterward
whether any full image/SBOM/Grype runner ran (must be NO locally)
```

Do not omit exploratory failures. GitHub workflow generations and any failed
jobs must also be listed with head SHA and cause.

## Acceptance criteria

1. PR `#11` remains the unique objective-008 PR and is amended; no new PR,
   merge, auto-merge, force push, exception, or prior-report edit occurs.
2. The exact old-image-initialized volume starts on the exact new image without
   initialization, repair, dump/restore, or data loss.
3. Encoding/locale/provider/collation stored-versus-actual facts are compatible
   and produce no server warning or index/query drift.
4. `006_001`, `EMPTY_SAFE safe=true`, all product roles/logins, privilege
   validation, representative data/constraints/indexes, and deterministic
   query digest survive transition and Alpine restart.
5. The test is mandatory in CI, fully disposable, secret-safe, and cannot
   target ordinary project volumes.
6. The old/current image pair is immutable in policy, all directly affected
   tests pass, and existing 20-check regression remains green with zero open
   CodeQL alert.
7. Documentation states only the exact tested transition guarantee and keeps
   OS notice/source-offer review as a prerequisite before image publication.
8. Execution stays within the hard budget and the report includes the complete
   attempt ledger.
9. `oap/active` is `008-b`, both rounds correlate uniquely, and final report
   publication follows protocol 1.2.

If criteria 2–4 fail, status must be `PARTIAL` and the report must present the
exact incompatibility for human choice. Do not remediate beyond this order.

## Verification required

Run only:

- focused static/unit tests for the historical transition policy;
- shell/static safety checks for the exact transition script;
- the targeted old-volume-to-new-image test, within the three-attempt cap;
- repository policy, affected packaging tests, Ruff/format on changed Python,
  Markdown on changed docs, and `git diff --check`;
- one normal GitHub check generation for the implementation head, with at most
  one corrective implementation commit if a genuine in-scope CI defect exists;
- final report-only head verification according to the normal OAP protocol.

Explicitly do **not** run locally:

```text
tools/supply_chain/run.sh
two-build five-image reproducibility suite
six-image SBOM/Grype suite
full Python 3.12–14 local matrix
full PostgreSQL 14–18 local matrix
full clean/restart/failure Compose smoke
```

Those unchanged gates run once in GitHub CI.

## Safety / security constraints

Use exact disposable names and fake secrets. No broad Docker prune or unrelated
volume deletion. Never expose secret material. Treat a locale/collation warning
as failure rather than suppressing it. Do not change the image, database state,
or policy to manufacture compatibility.

## GitHub workflow

Fetch and verify open PR `#11`, check out
`oap/008-supply-chain-build-gates`, and amend that same branch/PR. Preserve all
008-a artifacts. Never create another PR or merge. Respect the attempt and
commit caps.

## Required report

Atomically publish exactly:

```text
oap/reports/008-b-prove-postgres-base-transition.md
```

Use protocol 1.2 in full. Include the exact transition facts, attempt ledger,
locale/collation/data/role/marker results, cleanup proof, local test restraint,
GitHub run history, unchanged supply-chain evidence, scope/security/no-merge
confirmations, literal implementation head, and
`Report publication commit: SELF`.
