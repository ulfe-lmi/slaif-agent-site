# OAP Work Order — 074-e

## Objective and verified state

Amend only PR #70 / `oap/074-human-agent-session-control-plane`; no new PR or
merge. Required starting report head
`6897d5b46dc7865342786226032443f3e715ba4d`, sole parent
`4b508c0ab39971077d0e45f16ac5a6710f975adb`; `main` remains
`74d9c189fe241356fbe03f2632197ecbb1ce53a3`; all 20 checks are green.
Product and authority logic is accepted. Close one evidence gap only: 074-d
claims dynamic Agent-session restart recovery, but current `e2e.sh` merely runs
the same Agent projects twice before `smoke.sh` later restarts the stack.

## Required proof-only change

Add a deterministic clean-Compose public-boundary proof that:

1. logs in through NGINX as an authorized human using disposable fixture
   credentials and CSRF;
2. creates one bounded Agent workspace and one capability through the real
   Control endpoints with idempotency keys;
3. keeps the plaintext token only in process memory (never stdout/stderr, shell
   trace, file, environment, URL, artifact or retained log), uses it on the
   public Agent `/session`, and records only safe IDs/status;
4. actually restarts/recreates both `control-api` and `agent-api`, waits for
   public readiness, then uses the same in-memory token successfully and lists
   the persisted workspace/capability metadata through Control;
5. revokes through public Control, verifies Agent 401, confirms later metadata
   contains no token, and clears all in-memory secret references;
6. checks missing-CSRF denial through the same public edge and confirms no
   duplicate workspace/capability/audit from idempotent retry.

Use a bounded helper inside the smoke orchestration if needed, but it may not
write or print the token and may not access DB/service/internal APIs for the
claimed behavior. Docker restart orchestration is test infrastructure only.
Remove the redundant pre-restart duplicate Agent Playwright run unless it adds
distinct evidence; retain desktop+phone L1/L4 browser contracts once.

Add focused contract/unit coverage proving the restart helper's redaction,
public-path-only calls, exact restart targets, failure handling and cleanup.
Run the helper in exactly one clean local Compose smoke and require the final
GitHub Compose job plus all other current checks green. Run only focused local
lint/tests plus the clean smoke proportional to this proof-only change; report
all exact commands/counts/skips. No product/migration/grant/UI/authorization/
dependency/supply-chain behavior change.

## Report

Do not edit earlier reports. Publish exactly
`oap/reports/074-e-public-restart-capability-proof.md` as immutable report-only
child of literal implementation SHA. Correct the 074-d restart overstatement;
record exact safe evidence/commands/files/checks, secret nonretention, no extra
PR/merge/release and SELF.
