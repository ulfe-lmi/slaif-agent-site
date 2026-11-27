# 083-14-b — enforce the retained Heading byte limit before aggregation

## Identity and authority

Objective 083, increment 083/14, round `083-14-b`,
`AMEND_EXISTING_PR`. Amend [PR #123](https://github.com/ulfe-lmi/slaif-agent-site/pull/123)
on `oap/083-14-a-retained-heading-review-facts` against `main`
`1a633f57d828b099111b7b3dc3dc4ceafb9982b0`. The verified a report-only head
`8fbfc236be77a7057618ddbb794971a1f59765d7`
has sole implementation parent `f4e1a7109c8db5dd6cb1cf23cd5e6f045ca8141f`.
Use the existing isolated 083/14 checkout. No new PR. This is the
only same-PR repair permitted by the operating rhythm. The a response
is closed and the a order and report remain immutable.

## Findings and finite repair

1. **Enforce the actual byte budget before building the array.**
   The a capture compares the 1 MiB ceiling with a sum of the
   codepoint counts of the two props JSON texts. A selected set
   can pass that estimate and then exceed the encoded array limit
   because the input omits all retained-record fields and their
   syntax and does not measure canonical escaping. The first
   authoritative encoded-byte check follows `jsonb_agg`. The
   count and per-value limits bound each row and the wider work,
   but the order requires the retained payload ceiling before
   array materialization. Enforce the exact canonical UTF-8 byte
   limit of the selected record array before aggregation, including
   canonical per-record bytes, separators, and array delimiters.
   Reuse the same record shape and canonical serialization contract,
   preserve stable ordering and existing output, and keep the
   definitive post-assembly invariant. Avoid rejecting supported
   in-budget records because of a loose upper estimate. Verify a
   bounded new native case below the count and value caps with
   encoded total over the ceiling, plus a legal under-limit case.
   The test must establish refusal at the pre-assembly check and no
   partial freeze state. Keep the phase-aware grants, compact
   error behavior and full rollback.
2. **Provide the claimed read-time negative evidence.** Report a
   names a read-time identity divergence test that is absent at its
   literal implementation head. The existing fixture only checks the
   capture definer's refusal and the unchanged retained row. Add a
   narrow native check through the authorized human read of the same
   bounded fixture showing uniform unavailable on the mismatched
   persisted identity, while an otherwise matching exact snapshot
   read succeeds. Preserve immutable production data and keep any
   fixture instrumentation disposable and owner-only. Report the actual
   test identifiers and scopes. The existing atomic late-failure test
   is `test_freeze_fault_after_manifest_staging_rolls_back_atomically`.
   Verify all retained lifecycle and read criteria from a remain met.

## Scope and verification

Only the unmerged 081 migration, relevant focused tests, matching
security/testing docs, and the b transcript may change. Preserve all
merged migrations, prior round bytes, existing approved snapshot and
acceptance semantics, exact authorized read, and all security and
supply policies. No new API, dependencies, maintenance, generalized
history, conflict lifecycle, foundation changes, or release claims.
Review any overall size changes against the bounded contract. Routine
test setup uses only owned disposable resources. No new human secrets
or infrastructure. Use test voice and protect fixture credentials.
Do not record process IDs, handles, FIFO or lock inodes, or prompt
digests in durable files.

Run focused PG18 regressions then the full owned frozen integration,
unit/repository, code quality, package, process, Markdown and all
frozen Node gates at the final implementation subject. Identify each
actual command and outcome rather than citing a different subject.
Use the real PG14–18 jobs and public NGINX Compose proof of the
existing Heading read, all 19 projects, six profiles, real media and
isolated worker runs, plus Apache syntax. Verify the same existing
20 matching-app required checks, ten actual matrix children, CodeQL,
and fresh six-image evidence. Stop and report any actual policy
gate that cannot pass without weakening it.

## Delivery

Receive one fresh ASCII `OK` and EOF, resolve the unique selected order,
and reconcile the exact PR/base/head before mutation. Commit the exact
b order and active bytes with scoped implementation. Preserve the a
report. Publish exactly one
`oap/reports/083-14-b-enforce-retained-heading-byte-limit.md` with the
actual bounded correction evidence and existing a criteria, precise
local and GitHub subjects, literal
`Implementation head SHA: <40-hex>` and
`Report publication commit: SELF`. Exact Markdownlint of the complete
temporary report must pass before atomic publication. The byte-identical
canonical and branch report is the sole path in the final report commit
and its only parent is the reported implementation SHA. Verify it as
the remote PR head and send `printf '%s' OK` to the verified response
FIFO once, then close and stop. No force push, merge, or later round.
ROOT alone reviews, accepts and merges.
