# OAP Work Order — 073-a

## Objective

Wire accept and discard flows to the real `asyncpg_cow_reviewer` promotion
service so accepted workspace changes atomically merge to canonical, and
discarded sessions cleanly roll back.

## GitHub objective state

- Numeric objective: `073`; round: `073-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR

## Verified current state

- Accept route updates workspace status only.
- Discard route updates status only.
- `agent_state/promotion.py` wraps reviewer but never invoked from HTTP.
- Requires snapshot from 072-a.

## Required changes

1. Accept flow (review worker):
   - load latest review_snapshot for workspace;
   - call promotion service commit within reviewer transaction;
   - on success: increment canonical_site_revision, append promotion audit,
     mark workspace ACCEPTED, emit cache invalidation outbox.
   - on conflict (`CowConflictError`): set CONFLICTED/REVIEW, return
     structured error, leave canonical unchanged.
   - on validation failure: keep REVIEW, return structured errors.
2. Discard flow:
   - call foundation discard/cleanup within transaction;
   - remove pending COW overlay rows;
   - mark workspace DISCARDED;
   - retain audit trail.
3. Wire both HTTP routes to enqueue jobs; status polling reflects outcome.
4. Integration tests with real PostgreSQL:
   - create workspace, make COW writes, accept → canonical now contains
     changes, workspace ACCEPTED;
   - separate workspace B edits same row concurrently → B accept raises
     conflict, canonical unchanged, B CONFLICTED;
   - discard removes overlay rows, canonical unchanged, workspace DISCARDED.

## Explicit non-goals

- Do NOT implement selective acceptance (separate).
- Do NOT implement conflict resolution UI.
- Do NOT implement field-level merge/rebase.

## Acceptance criteria

- Real PostgreSQL promotion works end-to-end.
- Conflict preserves canonical integrity.
- Discard leaves no residual overlay data.
- Audit events recorded for both outcomes.
- All tests pass.

## Report

Publish `oap/reports/073-a-accept-discard-real-cow-promotion.md` with SELF
report commit parenting implementation SHA.
