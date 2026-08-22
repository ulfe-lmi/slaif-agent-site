# OAP Work Order — 022-a

## Objective
Complete the media service foundation: finish wiring MediaMixin into bootstrap
privilege grants, add media HTTP routes to route policy, update all test counts,
and merge PR.

## Scope
- Add `slaif_media_*` functions to `privileges.py` allowlist and `bootstrap/service.py` grants
- Verify 338+ unit tests pass, ruff/mypy clean, repository policy passes
- Push, create PR, wait for CI green, merge

## Non-goals
No actual file storage/upload handling (that's a future objective).

## Acceptance
All 20 CI checks pass on implementation head.
