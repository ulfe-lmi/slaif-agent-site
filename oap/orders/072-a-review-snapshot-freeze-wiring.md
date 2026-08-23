# OAP Work Order — 072-a

## Objective

Implement workspace freeze: drain pending writes, revoke capability tokens,
create immutable review snapshot with digest and operation closure, and
transition workspace to REVIEW state.

## GitHub objective state

- Numeric objective: `072`; round: `072-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR

## Verified current state

- Workspace lifecycle routes exist (create/freeze/accept/discard).
- Freeze currently updates status only; no snapshot created.
- `review_snapshot` table exists but unused.
- Promotion service wraps `asyncpg_cow_reviewer` but is not called.

## Required changes

1. Implement freeze flow in review worker:
   - claim FREEZE_FINALIZE job,
   - obtain exclusive product lock,
   - verify no in-flight mutation transactions,
   - collect operation IDs and compute watermark,
   - serialize normalized site projection to JSON,
   - compute SHA-256 digest,
   - insert immutable `review_snapshot` row with digest, versions,
     operation_ids, watermark, validation_report placeholder,
   - mark workspace REVIEW, set frozen_at.
2. Revoke all active capability tokens for this workspace atomically.
3. Snapshot row immutable (no UPDATE path; enforced by role permissions).
4. Wire `POST /api/control/v1/workspaces/{id}:freeze` to enqueue job and
   return job ID; poll/status endpoint reports completion.
5. Integration tests:
   - freeze creates snapshot with correct operation count/digest;
   - post-freeze agent mutation attempt returns 409;
   - capabilities revoked immediately;
   - snapshot row cannot be updated even by owner role;
   - double freeze idempotent or explicit error (documented choice).

## Explicit non-goals

- Do NOT implement accept/promotion (separate objective).
- Do NOT implement discard cleanup (separate).
- Do NOT generate browser evidence during freeze.
- Do NOT alter canonical content.

## Acceptance criteria

- Freeze produces verifiable immutable snapshot.
- Agent writes blocked after freeze.
- Capability tokens invalidated.
- All tests pass including negative paths.

## Report

Publish `oap/reports/072-a-review-snapshot-freeze-wiring.md` with SELF report
commit parenting implementation SHA.
