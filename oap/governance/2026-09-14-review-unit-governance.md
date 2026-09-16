# Prospective governance refinement: review-unit governance

Effective 2026-09-14, approved by the human project owner. This is a
prospective refinement of OAP review practice. The 2026-09-09
bounded-semantic-PR amendment remains in force and is not rewritten by this
document. All unchanged OAP laws continue. These rules bind from this
amendment onward for every new or continuing OAP execution increment.

## 1. Predeclared review budget

Every `CREATE_NEW_PR` semantic increment declares, before coding, its expected
review budget: production/config file count, migration count, test/evidence
footprint, generated-contract footprint, docs footprint, OAP transcript
footprint, and expected substantive implementation-line scale. The existing
20–30 implementation-file / several-thousand-substantive-line threshold
remains a review trigger, not a mechanical quota. Gaming the threshold by
moving code between boundaries, excluding meaningful tests, or ignoring
generated/OAP files is prohibited.

## 2. Cumulative review size

Every strategic review of a continuation calculates the base-to-current-head
cumulative PR size and records it separately for production/config,
migrations, tests/evidence, generated artifacts, docs, and OAP transcript.

## 3. CLOSURE_ONLY mode

Strategy enters CLOSURE_ONLY when it rejects a completion claim after
substantive implementation, or when the cumulative review trigger is crossed.
Once entered: no new semantic family, no adjacent feature, no opportunistic
scope, and no next-objective work in that PR. Only finite defects and evidence
that make already-added behavior safe, correct, and reviewable are permitted.
Separable functionality starts from verified merged `main` in another PR.

## 4. Finite rejection checklist

When Strategy rejects `COMPLETE`, it publishes one finite list of unresolved
criteria and the executable evidence required for each. A later report may
claim `COMPLETE` only if every named criterion was actually executed. Omitted
required browser, PostgreSQL, migration, concurrency, or public-boundary proof
requires `PARTIAL`/`BLOCKED`, never `COMPLETE`.

## 5. Early split decision

Semantically separable remaining work is split before being added to the
current PR. Tiny rounds do not justify a huge cumulative PR.

## 6. Final strategic acceptance record

Every acceptance record states: the verified base; the accepted exact head;
the cumulative base-to-head diff; grouped size per category; whether review
triggers fired; why the unit remains reviewable; whether and when CLOSURE_ONLY
began; and explicit confirmation that no new semantic family entered after
CLOSURE_ONLY began.
