# OAP Work Order — 072-t

## Objective

Continue Objective 072 on PR #66. Close the two public retrieval E2E proofs
removed from the final 072-s harness: deterministic worker-outage 503/recovery
and revoked-capability denial. Change only the Compose proof/tests/docs if
needed, run exactly one sudo-backed clean local Compose and fresh CI, then report
whether the full Objective 072 contract is complete. Do not merge.

## Verified state

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at green report-only head `8fa508daf5d71ed6edbc4a82d5c04432c4d57a5b`;
  its sole parent is implementation `4d4c8b63e0133c415b552ddc20c76d8b04a1d78f`.
  Main remains `082f2359b0c4d59b692580d17992c35d46183b12`;
  all 20 required checks pass.
- Public retrieval of six byte/digest/MIME-verified artifacts through NGINX,
  random/foreign 404s, Agent restart, browser-worker restart, canonical
  separation, private file policy and Chromium cleanup pass.
- The final 072-s change deleted its credential-volume outage/503/recovery block;
  report admits the final local run was not completed. No Compose step proves a
  previously authorized token is denied after revocation. Focused tests cover
  mappings, but the 072-s order required these public-path E2E behaviors.
- Preserve the exact 41-entry Chrome `.64` exception and issue #67 through
  `2026-09-04`; any new unexcepted finding fails closed.

## Requirements and binary acceptance

1. After successful byte retrieval and restart identity proof, deterministically
   stop only the `browser-worker` service with Compose. Through public NGINX,
   retrieve a known retained artifact using the valid bound capability and a
   bounded client timeout greater than the Agent's 10-second internal timeout;
   require exact 503 with the stable safe error envelope and no partial bytes or
   internal binding details. In the same outage, canonical public site remains
   200 and contains no workspace overlay.
2. Start only `browser-worker`, wait for real readiness, retrieve the same
   artifact again through public NGINX, and prove byte count/SHA/MIME and content
   are identical to the pre-outage retrieval. Do not modify/move credentials,
   volumes, DB rows or artifact files to create the outage.
3. At the end of the fixture, revoke the formerly authorized test capability
   using an existing product control surface where available; fixture-level DB
   authority transition is acceptable only if the product revoke surface cannot
   be used without unrelated setup. The same bearer token retrieving its own
   known artifact must then receive existing stable 401 authentication denial,
   with no bytes/metadata leakage. A separate valid foreign capability remains
   a non-leaking 404.
4. Add focused static/harness tests proving exactly one stop/start outage block,
   bounded timeouts, canonical availability, post-recovery byte comparison and
   revocation denial. Retain all existing public retrieval, hostile-network,
   token-binding, privacy, restart and cleanup assertions.
5. Run exactly one fresh full local Compose smoke using passwordless sudo and a
   new project name after focused checks. Do not call Docker permission a blocker
   and do not launch another local broad run; if it fails, report the exact stage.
6. Run directly affected tests, full repository/packaging policy, current
   supply-chain and all fresh GitHub checks. Every required check must pass;
   no rerun unless an evidenced external infrastructure failure occurs.

## Scope and workflow

No Agent/worker/Web/Render/database product code, migration/grant, contract,
exception, dependency, GC/source/review/promotion, second PR, merge, auto-merge
or release. Only proof harness/tests/accurate docs/transcript.

Commit/push unchanged order and `oap/active`, then proof repair. Publish exactly
`oap/reports/072-t-final-public-retrieval-proof.md` as report-only child with
literal implementation parent and `Report publication commit: SELF`; signal
exact FIFO `OK`.

Report exact pre-outage/503/canonical/recovery/revocation/foreign results and
byte hashes; one local Compose command/result/timing; all tests/current CI;
exception status; files/SHAs; no extra PR and no merge. Mark Objective 072
`COMPLETE` only if every original 072 order plus this proof is satisfied and
all current checks are green; otherwise `PARTIAL` with exact remaining gap.
