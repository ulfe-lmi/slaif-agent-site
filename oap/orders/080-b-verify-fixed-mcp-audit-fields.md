# 080-b — remove the MCP log-injection data flow

## Identity and finding

Objective 080, increment 080/1, round `080-b`, `AMEND_EXISTING_PR`.
Amend [PR #125](https://github.com/ulfe-lmi/slaif-agent-site/pull/125)
on `oap/080-a-capability-bound-mcp-discovery` in the existing isolated
`/home/janezp/codex-work/slaif-agent-site-080-a` checkout. Verified
main is `f370c647fcca3e4a027b96dbb6d82575d817cbe5`. The required
a report-only head is `f18d7d42cf623e08db390d0d9dd5dc7f1980760b`
with sole implementation parent `850f98793058352ffffa87d0ac363a1941705a21`.
The a response closed. Preserve the a order, report and pushed
history. This is the single permitted same-PR repair.

The a round proves all three public MCP browser contracts, the
official current-client smoke, 475 native PG18 tests, and the exact
final-head required checks, ten PostgreSQL jobs and six-image gates.
Review withheld acceptance for CodeQL rule `py/log-injection`.
[Alert #13](https://github.com/ulfe-lmi/slaif-agent-site/security/code-scanning/13)
is open on the exact a synthetic merge
`1de69cef0b2b78b3d89bf286113c1dc5af8f4597`. The sink is
`mcp_adapter/mcp_http.py:391`. The prior instance
[Alert #12](https://github.com/ulfe-lmi/slaif-agent-site/security/code-scanning/12)
is already fixed in a superseded analysis. Review the actual current
analysis data flow and close the live cause in source.

## Finite repair

- The successful dispatch currently selects `mcp_operation` from the
  caller's validated RPC method for two branches. Construct the
  logged operation using fixed server literals in the recognized
  result branches. Keep the existing request identity and the
  canonical authenticated site and workspace identity. Use typed
  normalization for any additional flow identified in the exact
  current analysis. No raw caller text, client RPC ID, capability,
  source URL, raw upstream body, or caller-provided destination may
  reach audit or diagnostic logging.
- Preserve the public MCP wire contract, tools set, authorization,
  same one fixed Agent API GET, quota, transport bounds, HTTP status
  behavior, and approved site/workspace evidence. Keep the safe
  structured logs. The fix may touch the scoped MCP logger, its
  focused unit tests and the b transcript. Preserve the a tests.
  Show successful discover, list, and call each emit only the
  expected fixed operation and validated IDs. Use a synthetic
  ordinary caller marker to verify that external identifiers do
  not enter log output.
- Establish causality with the exact CodeQL Python analysis and
  its current synthetic subject. The active `py/log-injection`
  instance must be absent or fixed by the source correction. Record
  the relevant alert identities and query state. Preserve CodeQL
  workflow, query selection, severity, reporting, checks, and
  policies. No dismissal, suppression, exclude rule, disabled check,
  token, or dependency workaround. If another source still reaches
  this log sink, resolve it in the same bounded repair before
  publishing its report.

## Verification and delivery

Run the full MCP unit module, unit and repository suite, relevant
quality, package and process checks, and exact Markdown lint on this
bounded change. Retain the exact a native PG18 and official-client
subjects and evidence. The b change is confined to logging and tests.
Verify current GitHub CI on this implementation head including all
20 required check bindings, ten actual PG14–18 matrix jobs, the three
MCP NGINX contracts, all 19 projects, six profiles, overlapping review,
retained Heading reads, real media acceptance, two isolated runs and
Apache syntax, CodeQL including the live alert outcome, and fresh
six-image supply evidence. Treat missing, pending, or failed as such.
Preserve fixture credential hygiene and operator authority. Stop for
a real policy, secret or infrastructure boundary.

Receive one exact ASCII `OK` with EOF and resolve the selected
immutable order. Commit the exact b order and active bytes with the
bounded fix. Push only new commits to the same branch. No force-push,
history rewrite, new PR, merge, or later activation.

Publish one `oap/reports/080-b-verify-fixed-mcp-audit-fields.md` after
the exact implementation head and its evidence are remote. Record
the complete source and evidence findings, PR identity, and the
following standalone lines, using the actual lowercase hexadecimal
implementation SHA and no list prefix.

```text
Implementation head SHA: <forty-hexadecimal-character SHA>
Report publication commit: SELF
```

Lint the complete temporary report with the repository configuration.
Publish byte-identical canonical and branch report copies. The remote
PR head must be a report-only commit with the literal implementation
SHA as its sole parent. Verify that head, send exact `OK` once to the
verified response FIFO and close. ROOT alone reviews, accepts, or merges.
