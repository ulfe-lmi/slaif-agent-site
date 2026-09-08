# OAP Work Order — 077-c

## Human-authorized protocol reconciliation

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; no new PR and no
merge. Required starting remote report head is
`7c4afcbcfe90263974691bedaa257af6b0f2a174`, whose sole parent is 077-b
implementation commit `b47d53481faed98da16b214d139bb05961cb8837`.
Remote `main` remains
`067676314e0d9664d40cb8514ea549b966a4eb2d`.

The human project owner explicitly authorized one exceptional correction to
the already activated 077-b order after its strategy-authored issue reference
caused the mandatory Markdown gate to fail. This direct human instruction
overrides activated-order byte immutability for exactly the change below and
for no other historical artifact:

```diff
-#67. Preserve 077-a implementation and report history, but do not claim that
+GitHub issue #67. Preserve 077-a implementation and report history, but do not claim that
```

The original remains permanently preserved in commits
`b47d53481faed98da16b214d139bb05961cb8837` and
`7c4afcbcfe90263974691bedaa257af6b0f2a174`. Strategy has applied only that
authorized one-line change in the current checkout. The old 077-b order hash
was `c8bff681872d45fd6b97c6d1a2732ed1bf255ba82c86c4ad6de87c7cc49eaf51`;
the authorized corrected hash is
`98e31feff3e26ab08c6b8a5e18158f398d90027821c0e82cbd265c5dbfbedc8b`.

## Required work and acceptance

1. Fetch GitHub, verify the exact named PR/branch/head, and preserve all
   existing 077-a/077-b implementation and report commits.
2. Commit exactly the strategy-owned one-line 077-b order correction, this
   unchanged 077-c order, and exact `oap/active = 077-c`. Do not modify any
   other activated order, prior report, architecture, constitution, product,
   test, dependency, policy, exception, documentation, image, or evidence file.
3. Verify the committed corrected 077-b order has the exact new SHA-256 above
   and that its diff from starting head is exactly one deletion plus one
   addition on line 16 with no whitespace or wrapping changes elsewhere.
4. Run the repository-wide Markdown command against every Markdown file and
   require zero findings. Do not ignore the file, disable MD018, add a lint
   exclusion, change Markdown configuration, narrow the glob, or weaken CI.
5. Run repository policy and the focused supply-chain policy/evidence tests to
   confirm the 077-b ledger/Chrome changes remain intact. Do not rerun expensive
   image qualification merely for activity; the exact 077-b evidence remains
   authoritative unless a current required check exposes a concrete regression.
6. Push the same branch and wait for/inspect every required current-head CI
   check. All must be terminal success; none may be failed, cancelled, missing,
   skipped, or pending. Repair only a concrete failure caused by this exact
   reconciliation, without touching unrelated product work.

This round closes only the Markdown/protocol blocker around the already
completed 077-b prerequisites. It does not accept 077-a or Objective 077. The
private foundation-table dependency, implicit locale-configuration escalation,
PATCH/OpenAPI scope mismatch, missing competing route-move race, and all later
locale/navigation/redirect/Render work remain for subsequent bounded orders on
this same PR.

Do not close GitHub issue 67 yet: the fixed Chrome commit is not on remote
`main`. Strategic may close the issue only after the containing Objective 077
PR is eventually accepted, merged, and verified on remote `main`. Do not merge,
enable auto-merge, create a PR, reopen Objective 076, implement 077 product
behavior, add an exception, or access production systems/data/secrets.

## Immutable report

Publish exactly
`oap/reports/077-c-reconcile-authorized-order-correction.md` as a final
report-only child of the literal implementation SHA and push it before
signaling. Include the human override; old/new order hashes; exact one-line
diff; Git history preservation; PR/base/head/commit topology; files changed;
global Markdown, repository-policy and focused supply-chain results; every
current-head CI check; no lint weakening/historical change/product change/new
PR/merge/issue closure/secret confirmation; and strongest remaining reason not
to merge Objective 077. Use `Report publication commit: SELF`.

Report `COMPLETE` only when the global Markdown gate and all required current-
head checks are terminal success. A concrete external/tool failure may be
`BLOCKED`; do not return early merely because CI takes time. No post-report
push. Signal exact FIFO `OK`, then wait for strategic review.
