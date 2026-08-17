# Versioned OAP transcript

This directory is the repository-visible transcript for Orchestrated Agentic
Programming (OAP). Full coding-agent behavior is defined by
[`OAP-COMMUNICATION-coding-agent.md`](../OAP-COMMUNICATION-coding-agent.md).

## Directory contract

- `active` is authored by the strategic model and is the sole selector of the
  executable order. The coding agent never infers work from filenames, mtimes,
  or numbering.
- `orders/` contains immutable, strategic-model-authored work orders.
- `reports/` contains immutable, coding-agent-authored execution reports.
- `NNN-a` creates one branch and one PR for numeric objective `NNN`;
  `NNN-b` through `NNN-z` amend that same branch and PR.
- The activated order, `active`, and corresponding report are committed and
  pushed on the objective PR. Committing strategic artifacts does not transfer
  their authorship or permit the coding agent to edit them.

FIFO `OK` messages provide synchronization only. The two FIFO objects live
outside the repository: the strategic model writes `control.fifo`, and the
coding agent writes `response.fifo`. Neither message selects work or records
project state.

## Report publication

Each report records:

```text
Implementation head SHA: <literal 40-hex commit before the report commit>
Report publication commit: SELF
```

`SELF` avoids impossible Git commit self-reference. Reviewers resolve it to
the GitHub commit containing the exact report. When that round sends FIFO
`OK`, the commit must be the current PR head, must change only the new report
file, and must have the recorded implementation head as its first parent. A
later activated continuation adds commits to the same PR, so the earlier
`SELF` will no longer be the current head; it remains immutable and reachable
in PR/Git history. Historical verification checks that containing commit and
its first parent, not whether the old commit is still the latest PR head.

OAP artifacts must never contain secrets, credentials, capability tokens,
session cookies, database URLs, private keys, or private artifact URLs.
