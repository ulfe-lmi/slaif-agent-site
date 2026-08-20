---
title: "Orchestrated Agentic Programming"
subtitle: "A Human-Governed Workflow for Strategic AI, High-Autonomy Coding Agents, and Review-Ready Software Delivery, Version 1.0.1"
author: "Janez Perš"
email: "janez.pers@fe.uni-lj.si"
date: "2026-06-14"
version: "1.0.1"
lang: "en"
toc: true
toc-depth: 3
numbersections: false
documentclass: scrbook
top-level-division: chapter
has-frontmatter: true
fontsize: 11pt
papersize: a4
classoption:
  - oneside
  - open=any
  - headings=big
  - parskip=half
geometry:
  - inner=30mm
  - outer=24mm
  - top=28mm
  - bottom=30mm
  - headheight=15pt
colorlinks: true
linkcolor: MidnightBlue
urlcolor: MidnightBlue
citecolor: MidnightBlue
toccolor: MidnightBlue
hyperrefoptions:
  - breaklinks=true
  - linktoc=all
urlstyle: same
bibliography: references.bib
csl: ieee.csl
link-citations: true
reference-section-title: References
header-includes: |
  \usepackage{microtype}
  \usepackage{etoolbox}
  \usepackage{fvextra}
  \usepackage{scrlayer-scrpage}
  \usepackage{xcolor}
  \definecolor{MidnightBlue}{HTML}{003366}
  \KOMAoptions{headsepline=true}
  \clearpairofpagestyles
  \ihead{\headmark}
  \ohead{\pagemark}
  \cfoot{}
  \automark[section]{chapter}
  \setkomafont{pagehead}{\small\normalfont\scshape}
  \setkomafont{chapter}{\Huge\bfseries}
  \setkomafont{section}{\Large\bfseries}
  \setkomafont{subsection}{\large\bfseries}
  \RecustomVerbatimEnvironment{Highlighting}{Verbatim}{commandchars=\\\{\},breaklines,breakanywhere}
  \setlength{\emergencystretch}{3em}
  \AtBeginEnvironment{CSLReferences}{\markboth{References}{References}}
  \AtBeginDocument{\hypersetup{breaklinks=true,linktoc=all,pdfborder={0 0 0}}}
---

<!-- document-front-matter-start -->
# Orchestrated Agentic Programming

**Author:** Janez Perš  
**Email:** janez.pers@fe.uni-lj.si  
**Version:** 1.0.1  
**Date:** 2026-06-14
<!-- document-front-matter-end -->

<nav id="markdown-table-of-contents">
<h1>Table of Contents</h1>
<ul>
<li style="margin-left: 0.0em"><a href="#acknowledgement">Acknowledgement</a></li>
<li style="margin-left: 0.0em"><a href="#abstract">Abstract</a></li>
<li style="margin-left: 0.0em"><a href="#preface">Preface</a></li>
<li style="margin-left: 1.5em"><a href="#how-to-read-this-manual">How to read this manual</a></li>
<li style="margin-left: 1.5em"><a href="#what-this-manual-does-not-claim">What this manual does not claim</a></li>
<li style="margin-left: 0.0em"><a href="#part-i-introduction-and-motivation">Part I: Introduction and Motivation</a></li>
<li style="margin-left: 1.5em"><a href="#i.1-why-oap-exists">I.1 Why OAP Exists</a></li>
<li style="margin-left: 3.0em"><a href="#the-widening-loop">The widening loop</a></li>
<li style="margin-left: 1.5em"><a href="#i.2-core-concepts-of-oap">I.2 Core Concepts of OAP</a></li>
<li style="margin-left: 3.0em"><a href="#start-with-strategic-discovery-not-code">Start with strategic discovery, not code</a></li>
<li style="margin-left: 3.0em"><a href="#the-human-owns-the-goal-not-the-terminal">The human owns the goal, not the terminal</a></li>
<li style="margin-left: 3.0em"><a href="#the-human-can-be-the-domain-expert">The human can be the domain expert</a></li>
<li style="margin-left: 3.0em"><a href="#strategic-ai-turns-domain-intent-into-architecture">Strategic AI turns domain intent into architecture</a></li>
<li style="margin-left: 3.0em"><a href="#strategic-ai-is-the-control-plane">Strategic AI is the control plane</a></li>
<li style="margin-left: 3.0em"><a href="#the-execution-agent-is-disposable-labor">The execution agent is disposable labor</a></li>
<li style="margin-left: 3.0em"><a href="#high-privilege-belongs-in-a-hardened-rebuildable-vm">High privilege belongs in a hardened, rebuildable VM</a></li>
<li style="margin-left: 3.0em"><a href="#the-remote-repository-is-project-truth">The remote repository is project truth</a></li>
<li style="margin-left: 3.0em"><a href="#review-becomes-evidence-interrogation">Review becomes evidence interrogation</a></li>
<li style="margin-left: 3.0em"><a href="#work-is-sliced-so-context-does-not-collapse">Work is sliced so context does not collapse</a></li>
<li style="margin-left: 3.0em"><a href="#the-project-constitution-is-machine-readable-governance">The project constitution is machine-readable governance</a></li>
<li style="margin-left: 3.0em"><a href="#validation-debt-is-the-main-debt">Validation debt is the main debt</a></li>
<li style="margin-left: 3.0em"><a href="#the-anti-pilot-rule">The anti-pilot rule</a></li>
<li style="margin-left: 1.5em"><a href="#i.3-what-oap-is">I.3 What OAP Is</a></li>
<li style="margin-left: 3.0em"><a href="#a-working-definition">A working definition</a></li>
<li style="margin-left: 3.0em"><a href="#why-orchestrated">Why orchestrated</a></li>
<li style="margin-left: 3.0em"><a href="#why-agentic">Why agentic</a></li>
<li style="margin-left: 3.0em"><a href="#why-programming">Why programming</a></li>
<li style="margin-left: 3.0em"><a href="#what-oap-is-not">What OAP is not</a></li>
<li style="margin-left: 1.5em"><a href="#i.4-the-human-role-shift">I.4 The Human Role Shift</a></li>
<li style="margin-left: 3.0em"><a href="#the-human-lead">The human lead</a></li>
<li style="margin-left: 3.0em"><a href="#the-strategic-ai">The strategic AI</a></li>
<li style="margin-left: 3.0em"><a href="#the-execution-agent">The execution agent</a></li>
<li style="margin-left: 3.0em"><a href="#the-new-human-skill-stack">The new human skill stack</a></li>
<li style="margin-left: 3.0em"><a href="#what-happens-to-implementers">What happens to implementers</a></li>
<li style="margin-left: 3.0em"><a href="#the-temptation-to-rubber-stamp">The temptation to rubber-stamp</a></li>
<li style="margin-left: 0.0em"><a href="#part-ii-operational-preflight">Part II: Operational Preflight</a></li>
<li style="margin-left: 1.5em"><a href="#ii.1-runtime-design-principles">II.1 Runtime Design Principles</a></li>
<li style="margin-left: 3.0em"><a href="#why-runtime-matters">Why runtime matters</a></li>
<li style="margin-left: 3.0em"><a href="#privilege-as-an-efficiency-boundary">Privilege as an efficiency boundary</a></li>
<li style="margin-left: 3.0em"><a href="#the-bounded-high-autonomy-pattern">The bounded high-autonomy pattern</a></li>
<li style="margin-left: 3.0em"><a href="#no-sudo-password-versus-no-boundary">No sudo password versus no boundary</a></li>
<li style="margin-left: 3.0em"><a href="#runtime-checklist">Runtime checklist</a></li>
<li style="margin-left: 3.0em"><a href="#runtime-anti-patterns">Runtime anti-patterns</a></li>
<li style="margin-left: 1.5em"><a href="#ii.2-baseline-agent-vm-setup">II.2 Baseline Agent VM Setup</a></li>
<li style="margin-left: 3.0em"><a href="#linux-guest-baseline">Linux guest baseline</a></li>
<li style="margin-left: 3.0em"><a href="#ssh-access-to-the-guest">SSH access to the guest</a></li>
<li style="margin-left: 3.0em"><a href="#snapshot-and-reset">Snapshot and reset</a></li>
<li style="margin-left: 1.5em"><a href="#ii.3-platform-recipes">II.3 Platform Recipes</a></li>
<li style="margin-left: 3.0em"><a href="#windows-option-a-wsl2-ubuntu-per-project">Windows option A: WSL2 Ubuntu per project</a></li>
<li style="margin-left: 3.0em"><a href="#windows-option-b-hyper-v-linux-vm">Windows option B: Hyper-V Linux VM</a></li>
<li style="margin-left: 3.0em"><a href="#windows-option-c-windows-sandbox-for-ephemeral-native-work">Windows option C: Windows Sandbox for ephemeral native work</a></li>
<li style="margin-left: 3.0em"><a href="#windows-option-d-persistent-windows-vm-with-openssh">Windows option D: persistent Windows VM with OpenSSH</a></li>
<li style="margin-left: 3.0em"><a href="#linux-option-a-kvmlibvirt-vm">Linux option A: KVM/libvirt VM</a></li>
<li style="margin-left: 3.0em"><a href="#linux-option-b-multipass-or-lxd-vm">Linux option B: Multipass or LXD VM</a></li>
<li style="margin-left: 3.0em"><a href="#linux-option-c-restricted-container-for-trusted-work">Linux option C: restricted container for trusted work</a></li>
<li style="margin-left: 3.0em"><a href="#linux-option-d-overlayfs-plus-chroot-as-reset-mechanism">Linux option D: OverlayFS plus chroot as reset mechanism</a></li>
<li style="margin-left: 3.0em"><a href="#macos-option-a-lima-ubuntu-vm">macOS option A: Lima Ubuntu VM</a></li>
<li style="margin-left: 3.0em"><a href="#macos-option-b-multipass-or-utm">macOS option B: Multipass or UTM</a></li>
<li style="margin-left: 1.5em"><a href="#ii.4-preflight-checklist">II.4 Preflight Checklist</a></li>
<li style="margin-left: 0.0em"><a href="#part-iii-strategic-discovery-and-constitution">Part III: Strategic Discovery and Constitution</a></li>
<li style="margin-left: 1.5em"><a href="#iii.1-the-first-conversation-with-the-strategic-model">III.1 The First Conversation With the Strategic Model</a></li>
<li style="margin-left: 3.0em"><a href="#the-discovery-conversation">The discovery conversation</a></li>
<li style="margin-left: 3.0em"><a href="#api-gateway-discovery-example">API Gateway discovery example</a></li>
<li style="margin-left: 3.0em"><a href="#human-prompt-examples">Human prompt examples</a></li>
<li style="margin-left: 3.0em"><a href="#technical-decisions-produced-by-discovery">Technical decisions produced by discovery</a></li>
<li style="margin-left: 3.0em"><a href="#discovery-artifacts">Discovery artifacts</a></li>
<li style="margin-left: 3.0em"><a href="#strategic-responsibilities">Strategic responsibilities</a></li>
<li style="margin-left: 3.0em"><a href="#model-selection-and-context-economics">Model selection and context economics</a></li>
<li style="margin-left: 3.0em"><a href="#strategic-output-the-work-order">Strategic output: the work order</a></li>
<li style="margin-left: 3.0em"><a href="#strategic-review-of-agent-reports">Strategic review of agent reports</a></li>
<li style="margin-left: 3.0em"><a href="#strategic-continuity">Strategic continuity</a></li>
<li style="margin-left: 1.5em"><a href="#iii.2-writing-the-project-constitution">III.2 Writing the Project Constitution</a></li>
<li style="margin-left: 3.0em"><a href="#discovery-before-constitution">Discovery before constitution</a></li>
<li style="margin-left: 3.0em"><a href="#what-a-constitution-is">What a constitution is</a></li>
<li style="margin-left: 3.0em"><a href="#minimum-constitution-structure">Minimum constitution structure</a></li>
<li style="margin-left: 3.0em"><a href="#constitution-as-memory">Constitution as memory</a></li>
<li style="margin-left: 3.0em"><a href="#constitution-smell-tests">Constitution smell tests</a></li>
<li style="margin-left: 1.5em"><a href="#iii.3-work-order-engineering">III.3 Work-Order Engineering</a></li>
<li style="margin-left: 3.0em"><a href="#work-order-template">Work-order template</a></li>
<li style="margin-left: 3.0em"><a href="#current-state-must-be-current">Current state must be current</a></li>
<li style="margin-left: 3.0em"><a href="#non-goals-as-guardrails">Non-goals as guardrails</a></li>
<li style="margin-left: 3.0em"><a href="#report-format-as-interface">Report format as interface</a></li>
<li style="margin-left: 3.0em"><a href="#prompt-smells">Prompt smells</a></li>
<li style="margin-left: 0.0em"><a href="#part-iv-coding-and-verification">Part IV: Coding and Verification</a></li>
<li style="margin-left: 1.5em"><a href="#iv.1-the-execution-layer">IV.1 The Execution Layer</a></li>
<li style="margin-left: 3.0em"><a href="#what-the-executor-should-own">What the executor should own</a></li>
<li style="margin-left: 3.0em"><a href="#the-executor-as-constrained-implementer">The executor as constrained implementer</a></li>
<li style="margin-left: 3.0em"><a href="#one-task-one-context">One task, one context</a></li>
<li style="margin-left: 3.0em"><a href="#required-executor-report">Required executor report</a></li>
<li style="margin-left: 3.0em"><a href="#executor-discipline">Executor discipline</a></li>
<li style="margin-left: 1.5em"><a href="#iv.2-pr-sized-delegation">IV.2 PR-Sized Delegation</a></li>
<li style="margin-left: 3.0em"><a href="#why-pr-sized-work-works">Why PR-sized work works</a></li>
<li style="margin-left: 3.0em"><a href="#anatomy-of-a-pr-sized-task">Anatomy of a PR-sized task</a></li>
<li style="margin-left: 3.0em"><a href="#scope-control">Scope control</a></li>
<li style="margin-left: 3.0em"><a href="#repair-prs">Repair PRs</a></li>
<li style="margin-left: 1.5em"><a href="#iv.3-verification-and-validation-debt">IV.3 Verification and Validation Debt</a></li>
<li style="margin-left: 3.0em"><a href="#what-validation-debt-means">What validation debt means</a></li>
<li style="margin-left: 3.0em"><a href="#tests-as-evidence">Tests as evidence</a></li>
<li style="margin-left: 3.0em"><a href="#skipped-tests-are-unknown">Skipped tests are unknown</a></li>
<li style="margin-left: 3.0em"><a href="#meaningful-tests">Meaningful tests</a></li>
<li style="margin-left: 3.0em"><a href="#verification-only-runs">Verification-only runs</a></li>
<li style="margin-left: 1.5em"><a href="#iv.4-security-and-safety-during-implementation">IV.4 Security and Safety During Implementation</a></li>
<li style="margin-left: 3.0em"><a href="#fail-closed">Fail closed</a></li>
<li style="margin-left: 3.0em"><a href="#secrets">Secrets</a></li>
<li style="margin-left: 3.0em"><a href="#approval-gates">Approval gates</a></li>
<li style="margin-left: 3.0em"><a href="#safety-scans">Safety scans</a></li>
<li style="margin-left: 3.0em"><a href="#avoiding-unsafe-helpfulness">Avoiding unsafe helpfulness</a></li>
<li style="margin-left: 1.5em"><a href="#iv.5-documentation-handoffs-and-memory">IV.5 Documentation, Handoffs, and Memory</a></li>
<li style="margin-left: 3.0em"><a href="#documentation-types">Documentation types</a></li>
<li style="margin-left: 3.0em"><a href="#handoffs">Handoffs</a></li>
<li style="margin-left: 3.0em"><a href="#documentation-as-contract">Documentation as contract</a></li>
<li style="margin-left: 3.0em"><a href="#runbooks">Runbooks</a></li>
<li style="margin-left: 0.0em"><a href="#part-v-review-audit-and-release">Part V: Review, Audit, and Release</a></li>
<li style="margin-left: 1.5em"><a href="#v.1-review-and-audit">V.1 Review and Audit</a></li>
<li style="margin-left: 3.0em"><a href="#strategic-review-brief">Strategic review brief</a></li>
<li style="margin-left: 3.0em"><a href="#human-review-as-management-discipline">Human review as management discipline</a></li>
<li style="margin-left: 3.0em"><a href="#ai-assisted-review">AI-assisted review</a></li>
<li style="margin-left: 3.0em"><a href="#cross-model-audit">Cross-model audit</a></li>
<li style="margin-left: 3.0em"><a href="#audit-cadence">Audit cadence</a></li>
<li style="margin-left: 3.0em"><a href="#audit-loop-mechanics">Audit loop mechanics</a></li>
<li style="margin-left: 3.0em"><a href="#external-audit">External audit</a></li>
<li style="margin-left: 3.0em"><a href="#review-comments-as-work-orders">Review comments as work orders</a></li>
<li style="margin-left: 1.5em"><a href="#v.2-release-readiness">V.2 Release Readiness</a></li>
<li style="margin-left: 3.0em"><a href="#completeness-levels">Completeness levels</a></li>
<li style="margin-left: 3.0em"><a href="#readiness-scoring">Readiness scoring</a></li>
<li style="margin-left: 3.0em"><a href="#release-decision-brief">Release decision brief</a></li>
<li style="margin-left: 3.0em"><a href="#release-gates">Release gates</a></li>
<li style="margin-left: 3.0em"><a href="#the-danger-of-apparent-completeness">The danger of apparent completeness</a></li>
<li style="margin-left: 0.0em"><a href="#part-vi-case-studies-and-applications">Part VI: Case Studies and Applications</a></li>
<li style="margin-left: 1.5em"><a href="#vi.1-case-study-slaif-api-gateway">VI.1 Case Study: SLAIF API Gateway</a></li>
<li style="margin-left: 3.0em"><a href="#problem-shape">Problem shape</a></li>
<li style="margin-left: 3.0em"><a href="#architecture-discovery">Architecture discovery</a></li>
<li style="margin-left: 3.0em"><a href="#constitution-first">Constitution first</a></li>
<li style="margin-left: 3.0em"><a href="#pr-sequence">PR sequence</a></li>
<li style="margin-left: 3.0em"><a href="#control-plane-in-practice">Control plane in practice</a></li>
<li style="margin-left: 3.0em"><a href="#audit-and-remediation">Audit and remediation</a></li>
<li style="margin-left: 3.0em"><a href="#lessons">Lessons</a></li>
<li style="margin-left: 1.5em"><a href="#vi.2-applying-oap-to-other-projects">VI.2 Applying OAP to Other Projects</a></li>
<li style="margin-left: 3.0em"><a href="#concept-demonstrations-across-examples">Concept demonstrations across examples</a></li>
<li style="margin-left: 3.0em"><a href="#writing-new-software">Writing new software</a></li>
<li style="margin-left: 3.0em"><a href="#taking-over-existing-software">Taking over existing software</a></li>
<li style="margin-left: 3.0em"><a href="#rewriting-wrong-shaped-or-failed-software">Rewriting wrong-shaped or failed software</a></li>
<li style="margin-left: 3.0em"><a href="#hardening-an-existing-serious-system">Hardening an existing serious system</a></li>
<li style="margin-left: 3.0em"><a href="#infrastructure-management-products">Infrastructure management products</a></li>
<li style="margin-left: 3.0em"><a href="#existing-academic-or-domain-software">Existing academic or domain software</a></li>
<li style="margin-left: 3.0em"><a href="#when-oap-is-too-heavy">When OAP is too heavy</a></li>
<li style="margin-left: 3.0em"><a href="#when-oap-is-especially-useful">When OAP is especially useful</a></li>
<li style="margin-left: 0.0em"><a href="#part-vii-discussion-and-doctrine">Part VII: Discussion and Doctrine</a></li>
<li style="margin-left: 1.5em"><a href="#vii.1-failure-modes">VII.1 Failure Modes</a></li>
<li style="margin-left: 3.0em"><a href="#hallucinated-apis-and-dependencies">Hallucinated APIs and dependencies</a></li>
<li style="margin-left: 3.0em"><a href="#shallow-tests">Shallow tests</a></li>
<li style="margin-left: 3.0em"><a href="#context-drift">Context drift</a></li>
<li style="margin-left: 3.0em"><a href="#weak-strategic-model">Weak strategic model</a></li>
<li style="margin-left: 3.0em"><a href="#control-inversion">Control inversion</a></li>
<li style="margin-left: 3.0em"><a href="#excessive-human-reading-burden">Excessive human reading burden</a></li>
<li style="margin-left: 3.0em"><a href="#scope-creep">Scope creep</a></li>
<li style="margin-left: 3.0em"><a href="#overclaiming">Overclaiming</a></li>
<li style="margin-left: 3.0em"><a href="#credential-leakage">Credential leakage</a></li>
<li style="margin-left: 3.0em"><a href="#human-complacency">Human complacency</a></li>
<li style="margin-left: 1.5em"><a href="#vii.2-practical-oap-doctrine">VII.2 Practical OAP Doctrine</a></li>
<li style="margin-left: 3.0em"><a href="#core-principles">Core principles</a></li>
<li style="margin-left: 3.0em"><a href="#minimum-viable-oap">Minimum viable OAP</a></li>
<li style="margin-left: 3.0em"><a href="#mature-oap">Mature OAP</a></li>
<li style="margin-left: 3.0em"><a href="#team-adoption">Team adoption</a></li>
<li style="margin-left: 1.5em"><a href="#vii.3-conclusions">VII.3 Conclusions</a></li>
<li style="margin-left: 0.0em"><a href="#appendices">Appendices</a></li>
<li style="margin-left: 1.5em"><a href="#appendix-a-example-agents.md-claude.md-structure">Appendix A: Example AGENTS.md / CLAUDE.md structure</a></li>
<li style="margin-left: 1.5em"><a href="#appendix-b-coding-agent-prompt-template">Appendix B: Coding-agent prompt template</a></li>
<li style="margin-left: 1.5em"><a href="#appendix-c-verification-only-prompt-template">Appendix C: Verification-only prompt template</a></li>
<li style="margin-left: 1.5em"><a href="#appendix-d-pr-readiness-checklist">Appendix D: PR readiness checklist</a></li>
<li style="margin-left: 1.5em"><a href="#appendix-e-release-readiness-checklist">Appendix E: Release readiness checklist</a></li>
<li style="margin-left: 1.5em"><a href="#appendix-f-operational-preflight-commands">Appendix F: Operational Preflight Commands</a></li>
<li style="margin-left: 3.0em"><a href="#linux-guest-user">Linux guest user</a></li>
<li style="margin-left: 3.0em"><a href="#guest-local-codex-state">Guest-local Codex state</a></li>
<li style="margin-left: 3.0em"><a href="#wsl2-ubuntu-install">WSL2 Ubuntu install</a></li>
<li style="margin-left: 3.0em"><a href="#wsl2-hardening-starting-point">WSL2 hardening starting point</a></li>
<li style="margin-left: 3.0em"><a href="#linux-openssh-inside-a-guest">Linux OpenSSH inside a guest</a></li>
<li style="margin-left: 3.0em"><a href="#windows-sandbox-openssh-bootstrap">Windows Sandbox OpenSSH bootstrap</a></li>
<li style="margin-left: 3.0em"><a href="#visual-studio-build-tools-bootstrap">Visual Studio Build Tools bootstrap</a></li>
<li style="margin-left: 3.0em"><a href="#multipass-ubuntu-vm">Multipass Ubuntu VM</a></li>
<li style="margin-left: 3.0em"><a href="#lima-ubuntu-vm">Lima Ubuntu VM</a></li>
<li style="margin-left: 3.0em"><a href="#overlayfs-reset-layer">OverlayFS reset layer</a></li>
<li style="margin-left: 1.5em"><a href="#appendix-g-platform-setup-references">Appendix G: Platform Setup References</a></li>
<li style="margin-left: 1.5em"><a href="#appendix-h-glossary">Appendix H: Glossary</a></li>
</ul>
</nav>


# Acknowledgement {.unnumbered}

We acknowledge the support of the EC/EuroHPC JU and the Slovenian Ministry of HESI via the project SLAIF (grant number 101254461).

# Abstract {.unnumbered}

Orchestrated Agentic Programming is a human-governed method for building software with AI coding agents. It separates strategic reasoning from operational execution: a high-powered, long-context strategic AI helps transform domain intent into architecture, tool choices, task plans, critique, and precise work orders, while a high-autonomy execution agent works inside a hardened, rebuildable machine environment to edit code, install tools, run commands, execute tests, commit changes, and open pull requests. The human remains the control point for intent, risk, and release, but does not waste time supervising every low-level step.

This manual presents Orchestrated Agentic Programming as a practical subtype of agentic software engineering. It is more disciplined than vibe coding, more autonomous than ordinary AI pair programming, and more governable than open-ended agent swarms. Its central artifacts are a project constitution such as `AGENTS.md` for Codex CLI or `CLAUDE.md` for Claude Code CLI, narrow PR-sized work units, explicit non-goals, reproducible verification, audit-ready reports, remote-repository truth, and durable handoffs. The manual argues that the main bottleneck in AI-assisted software development is shifting from code production to validation, governance, context preservation, and judgment.

Rather than promising effortless software creation, this manual teaches a repeatable workflow for making AI-generated software auditable, constrained, test-backed, and aligned with human intent. It is a guide for freeing the human from low-level implementation labor while preserving high-level control. In OAP the human inevitably moves up the ladder: less coder, less line-level software engineer, more product owner, domain expert, engineering manager, reviewer of evidence, and release authority. The human begins by asking the strategic AI what kind of system is needed and which architecture and tools fit the domain; later the human interrogates the strategic AI for proof, risk, and readiness. The execution agent performs disposable implementation work in a bounded runtime.

# Preface {.unnumbered}

This manual is written for people who have already noticed that modern AI coding tools are no longer just autocomplete. They can inspect repositories, modify files, run tests, use terminals, and in some environments open pull requests. The practical question is no longer whether AI can produce code. The practical question is how to organize this capability so that serious software can be produced without losing control of architecture, security, correctness, documentation, and responsibility.

The method described here is called **Orchestrated Agentic Programming**, abbreviated **OAP**. The name is intentionally operational. It does not claim that every component is new. Repository instructions, coding agents, AI code review, branch-based work, human review, and multi-agent research systems all already exist [@codex-agents-md; @hula; @metagpt; @chatdev]. The contribution of OAP is the composition: a human lead uses a strategic model first for architecture discovery and tool selection, then for critique and work-order design, delegates implementation to a high-autonomy coding agent inside a bounded runtime, and treats every change as a reviewable, test-backed, auditable unit.

This is not a manual about asking a chatbot to write a function. It is not a manual about removing humans from software engineering. It is a manual about moving the human into a higher-leverage management role: domain expert, intent owner, product judge, risk owner, strategic interrogator, release authority, and process designer. The human should not become the agent's assistant, dependency installer, or manual traceback courier. If the workflow causes the agent to pilot the human through low-level chores, the orchestration has failed.

The manual uses examples from several project types: a public OpenAI-compatible API gateway, a private grading workflow, a public browser-based SSH workflow, and a public early-stage infrastructure management product. Private examples are used only as design material. Public sources are cited where the manual refers to broader history, tools, benchmarks, repositories, and research.

## How to read this manual {.unnumbered}

Readers who want the shortest path should read Parts I through V first, then the SLAIF API Gateway case study in Part VI. Readers building a training course should read the full document and use the appendices as workshop templates. Readers evaluating the method academically should focus on the conceptual chapters, the verification and audit chapters, the case studies, and the references.

## What this manual does not claim {.unnumbered}

This manual does not claim that OAP is a new scientific discipline. It does not claim that domain experts building or shaping software is historically new; end-user software engineering, low-code/end-user development, AI-assisted end-user coding, and citizen development all address related terrain [@ko-euse-2011; @schenkenfelder-lowcode-eud-2024; @weber-ai-eud-2025; @mit-ai-citizen-dev-2024]. It does not claim that coding agents are reliable enough to run without boundaries. It does not claim that high-autonomy execution is safe by default. It does not claim that a generated pull request is proof of completion. It also does not claim that the human must manually review every line of every agent-generated diff. It claims something narrower and stronger: with the right strategic control plane, project constitution, rebuildable runtime boundary, PR discipline, verification practice, and evidence interrogation, coding agents can become serious implementation labor without turning the human into their operator.

# Part I: Introduction and Motivation

## I.1 Why OAP Exists

AI-assisted coding has moved through several recognizable stages. The earliest widely adopted form was completion: the tool predicted the next token, line, or small block inside the editor. The human remained fully inside the code-writing act. The tool accelerated typing and sometimes suggested APIs or idioms, but it did not own a task.

The next stage was AI pair programming. GitHub Copilot popularized the framing of an "AI pair programmer" and made generated code suggestions part of everyday editor work [@github-copilot]. Controlled research on GitHub Copilot found a substantial speed improvement on a bounded programming task, with the treated group completing the task 55.8 percent faster than the control group [@copilot-productivity]. That result matters, but its scope also matters: it studied a specific task shape, not the whole problem of shipping reliable software.

Chat-based coding changed the interface. A developer could explain intent in natural language, ask for design alternatives, paste errors, request tests, and iterate conversationally. This made AI useful outside the editor. It also created a new failure mode: code could look coherent in conversation while remaining untested, unreviewed, or incompatible with the actual repository.

The current stage is agentic software delivery. Coding agents can inspect a repository, edit multiple files, run commands, execute tests, and work against issue or pull-request workflows. SWE-bench made real GitHub issue resolution a central benchmark for this movement, with a public repository that helped standardize benchmark access and reproducibility [@swebench-paper; @swebench-repo]. SWE-agent showed that the interface between agent and computer materially affects agent performance, not merely the model behind the agent, and its open repository made that agent-computer-interface work inspectable [@sweagent-paper; @sweagent-repo]. Human-in-the-loop systems such as HULA show that there is practical and research interest in agents that plan, code, and raise pull requests while keeping engineers involved at checkpoints [@hula].

OAP belongs to this later stage. Its concern is not completion quality alone. Its concern is the whole delivery loop:

- who defines the goal;
- who turns the goal into a safe plan;
- who operates the repository;
- what boundaries contain the executor;
- what evidence proves work was done;
- who reviews that evidence;
- who decides whether software is ready.

The center of gravity has shifted from "help me type code" to "help me operate a software delivery process." That shift is why OAP needs to be described as an operating discipline rather than as a prompting trick.

### The widening loop

Each generation of tool widened the loop:

| Stage | Human activity | AI capability | Main risk |
|---|---|---|---|
| Completion | Writes code directly | Suggests local continuations | Wrong or insecure snippet accepted quickly |
| Pair programming | Co-edits and asks questions | Suggests, explains, refactors | Plausible answers without repository proof |
| Chat-based coding | Describes tasks and errors | Generates files, tests, designs | Context drift between chat and repo |
| Coding agent | Delegates repo task | Edits, runs commands, tests | Autonomy without governance |
| OAP | Orchestrates delivery loop | Strategic critique plus execution labor | Human rubber-stamping of weak evidence |

OAP is not a rejection of previous stages. It uses them. The strategic model is often chat-like. The execution agent may expose IDE-like operations. The difference is that the work is organized around accountable delivery.

## I.2 Core Concepts of OAP

OAP should be understood first as a control system. Its purpose is not to make the human type less while staying trapped in the same low-level workflow. Its purpose is to keep human attention on intent, risk, proof, and release while delegating implementation labor to machines that can move faster than humans.

![The OAP control plane.](assets/fig-00-oap-control-plane.svg)

### Start with strategic discovery, not code

An OAP project should begin with a strategic discovery conversation, not with the execution agent and not with a blank repository prompt. The first question is not "what code should the agent write?" The first question is "what kind of system should exist?"

This is especially important when the human is a domain expert rather than a professional software architect. The human may know the operational need precisely: an institution must issue limited LLM API keys, a laboratory must manage workflows, a teacher must grade exams, an HPC service must launch jobs without receiving SSH credentials, or a Raspberry Pi appliance must apply DHCP configuration safely. That does not mean the human knows the right stack, trust boundary, data model, background-job system, browser-extension model, or deployment shape.

The strategic model helps the human ask and answer:

- What is the real product category?
- Which existing tools or architectures solve nearby problems?
- Which stack is boring and safe enough for this domain?
- Which components should be separate because the trust boundaries differ?
- Which parts should be postponed because they are too risky for the first slice?
- What must the execution agent never be allowed to improvise?

This is a management act. The strategic model proposes architectures and explains tradeoffs. The human accepts, rejects, or redirects based on domain knowledge. Only after this discovery does OAP produce the constitution and first execution prompt.

### The human owns the goal, not the terminal

The human's most important job is to keep the project pointed at the right problem. OAP therefore moves the human up the organizational ladder. The human is no longer primarily the coder and often not even the active software engineer in the day-to-day implementation sense. The human is acting more like a product owner, engineering manager, technical director, or accountable reviewer of evidence.

This is not just a change in tools. It is a change in role. The human manages intent, risk, priorities, and acceptance. This management role must be disciplined, not ceremonial: the human defines goals, acceptance criteria, release criteria, non-goals, budget of risk, and proof standards. But the human should do this with shorter texts, tighter summaries, and fewer low-level artifacts to inspect. The strategic AI manages translation, memory, compression, and technical synthesis. The execution agent manages code production inside a bounded environment.

The human asks:

- What are we trying to build?
- What must not be broken?
- What did we actually implement?
- Where is the proof?
- What risks remain?
- What should happen next?

The human should usually ask these questions of the strategic AI, not of the execution agent directly. Direct agent supervision is expensive because it pulls the human back into command-by-command work. If the agent says it needs a package, a compiler, a browser driver, a database fixture, or a local service, the preferred OAP answer is not "ask the human to install it." The preferred answer is "the agent installs or configures it inside the hardened execution space and reports what changed."

The strategic AI should answer in compressed form first: conclusion, evidence, risk, and next decision. The human can then drill down into files, logs, tests, or PR lines only when the summary is weak, the risk is high, or the answer does not make sense.

### The human can be the domain expert

The human in OAP does not have to be a professional software engineer. In many cases the best human lead is the domain expert: the physician, teacher, scientist, infrastructure operator, compliance specialist, manufacturing engineer, researcher, librarian, or public-sector process owner who understands the problem better than a software team ever will.

This is related to end-user software engineering and citizen development, but it is not the same shape. Traditional end-user development often asks the domain expert to become the builder, using spreadsheets, scripts, low-code tools, or AI-assisted prompts. OAP moves differently: the domain expert becomes the manager of an agentic delivery system. The strategic AI translates domain intent into technical work orders. The execution agent builds. The domain expert judges whether the resulting system serves the real domain need.

This matters because software often fails in translation. Requirements move from users to analysts, from analysts to tickets, from tickets to engineers, from engineers back to reviewers, and finally back to users. Every handoff can lose domain meaning. OAP can shorten that loop. The person closest to the domain can ask the strategic AI:

- Did we implement the workflow the users actually need?
- Does this match the real operational constraint?
- What assumption did the agent make about the domain?
- Which acceptance criterion proves the domain behavior?
- What would make this unsafe or useless in practice?

The domain expert does not need to inspect every class or function. The domain expert needs disciplined control over goals, acceptance criteria, release criteria, and evidence.

### Strategic AI turns domain intent into architecture

One of the most important OAP moments happens before the execution agent touches the repository. The domain expert asks the strategic model questions such as:

- What kind of system do I actually need?
- Which architecture fits this operational problem?
- Which tools, frameworks, databases, runtimes, and protocols are appropriate?
- Which parts are risky enough to isolate?
- What should be built first, and what should explicitly wait?
- What would a professional software team worry about here?

This is where modern high-reasoning models are especially useful to non-software-specialist domain experts. A domain expert may understand the real workflow, failure costs, policy constraints, and user pain, but not know the current software architecture landscape. The strategic model can act as an architecture translator and technology scout: it maps the domain problem into plausible software shapes, explains tradeoffs, identifies standard components, and proposes an implementation sequence that the execution agent can later follow.

This does not make the model the architect of record. The model can be wrong, outdated, or overconfident. The human still owns the goal and must challenge the answer. But without this initial strategic discussion, OAP becomes weaker: the execution agent may build from a shallow prompt instead of from a domain-informed architecture.

### Strategic AI is the control plane

The strategic AI is the human's main interface to the project. It translates human intent into architecture, tool choices, work orders, review questions, and release evidence. It interprets agent reports, compares evidence against goals, and prepares the next narrow task. It should be a strong, long-context model because it is not supposed to burn context on thousands of file edits. Its context is spent slowly: human discussion, project state, PR summaries, architectural decisions, risk registers, and evidence questions.

In an ideal OAP workflow, the strategic model almost never forgets the project. That ideal is not fully realistic, but it is the direction of travel. The workflow should preserve strategic context as long as possible, refresh it with handoffs when necessary, and avoid wasting it on mechanical implementation.

### The execution agent is disposable labor

The execution agent is valuable because it can operate the repository at machine speed. It reads files, modifies code, installs dependencies, runs tests, starts services, writes docs, commits, and opens PRs. It does not need to carry the whole project in its context forever. It needs enough context to complete one sliced task and return evidence.

This creates a useful asymmetry:

- the strategic AI should be the strongest practical model, with long context and high reasoning quality;
- the execution agent can be cheaper, faster, or both;
- the execution agent's context should last one PR-sized task;
- after the PR, the execution context can be compacted, reset, or discarded;
- the durable truth must live in the remote repository, PR discussion, CI logs, documentation, and handoff summaries.

### High privilege belongs in a hardened, rebuildable VM

Restricting an agent so strongly that it cannot install tools, rebuild libraries, run migrations, launch local services, or repair its own test environment often wastes human time. Modern coding agents are fast enough that one missing dependency can turn into hours of human work: chasing package versions, rebuilding native tools, setting up databases, or relaying terminal output. At that point OAP degenerates into the opposite of its purpose: the AI is piloting the human.

The preferred pattern is a hardened execution space that the agent may control extensively and that the project can afford to lose. The VM should contain no production secrets, no irreplaceable state, and no uncommitted project truth. If the agent breaks it, the VM can be rebuilt from the remote repository and documented setup commands. This makes high privilege safer than a fragile locked-down environment that constantly recruits the human for chores.

### The remote repository is project truth

OAP depends on a sharp distinction between disposable runtime state and durable project truth. The execution VM is temporary. The remote repository, branch, PR, CI log, tests, docs, issue trail, and release notes are durable. A local VM can be destroyed. A bad branch can be abandoned. A failed PR can be closed. But the project truth must remain visible, versioned, reviewable, and reconstructable.

This principle is what makes high-autonomy execution tolerable. The agent may be powerful inside the box because the box is not the source of truth.

### Review becomes evidence interrogation

OAP does not require the human to manually read every line of every PR as the default workflow. That can be as wasteful as installing dependencies by hand. The human instead interrogates the strategic model:

- Did we implement the requirement exactly?
- Which files changed and why?
- Which tests prove the critical behavior?
- What negative path did we test?
- Did the agent touch secrets or production-like data?
- Did docs overclaim readiness?
- What would make this PR unsafe to merge?

Manual code inspection remains available for high-risk areas, unclear reports, security-sensitive changes, or suspicious diffs. But the default human posture is not line-by-line labor. The default posture is adversarial questioning of the strategic AI's evidence map.

### Work is sliced so context does not collapse

PR-sized delegation is not only a Git habit. It is a context-management mechanism. A sliced task keeps the execution agent's context short enough to finish reliably. It keeps the strategic AI's context clean enough to remember the goal. It keeps the human's attention on decisions rather than implementation clutter.

The target state is simple: the strategic AI does not lose context, the human does not lose the goal, and the execution agent does not need to remember anything beyond the current task.

### The project constitution is machine-readable governance

The project constitution, usually `AGENTS.md` or an equivalent instruction file, converts repeated human correction into durable operational law. It tells agents how to behave when the human is not watching. It defines architecture, tests, security rules, forbidden actions, reporting requirements, and the definition of done.

Without a constitution, OAP decays into a sequence of clever prompts. With a constitution, every prompt inherits project law.

### Validation debt is the main debt

AI coding makes code cheap. It does not make correctness cheap. The faster agents generate implementation, the more the bottleneck moves to proof: tests, CI, architecture checks, security review, documentation accuracy, and release honesty. OAP is therefore not primarily a productivity trick. It is a validation-management method.

The strategic AI should help carry that validation burden. The human should not accept "done" as a feeling. The human should demand evidence through the strategic control plane.

### The anti-pilot rule

The most compact rule of OAP is this:

> The human pilots the strategic AI; the strategic AI directs the execution agent; the execution agent operates the machine. If the execution agent starts directing the human through low-level work, the control loop is inverted and must be redesigned.

## I.3 What OAP Is

Orchestrated Agentic Programming is a workflow in which a human lead coordinates at least three layers:

1. **Human intent and judgment.** The human defines the product goal, constraints, risk tolerance, and release decision.
2. **Strategic AI.** A high-reasoning, long-context model acts as architect, planner, reviewer, critic, memory layer, and prompt compiler.
3. **Execution agent.** A coding agent operates inside a bounded, rebuildable machine environment, edits the repository, installs tools, runs tests, creates commits, and opens pull requests.

![The OAP operating loop.](assets/fig-01-oap-loop.svg)

The decisive design choice is that the strategic model and the execution agent are not fused into one uncontrolled loop, and the human is not dragged into agent babysitting. The human normally interacts with the strategic AI. The strategic AI converts human intent into work orders, reads execution reports, maps claims to evidence, and explains risk. The execution agent performs work and returns evidence. The human accepts, rejects, redirects, or releases based on strategic interrogation, not on trust in the executor's confidence.

### A working definition

**Orchestrated Agentic Programming is a human-governed, constitution-driven subtype of agentic software engineering in which a long-context strategic AI serves as the control plane, a high-autonomy coding agent executes in a hardened and rebuildable machine environment, and the human preserves goal, risk, evidence demands, and release authority.**

This definition is deliberately strict. A single chatbot conversation is not OAP. A coding agent making a patch is not enough. A multi-agent swarm without human gates is not OAP. A human manually carrying out the agent's setup chores is also not mature OAP. The method requires role separation, durable rules, bounded autonomy, rebuildable execution, evidence, strategic memory, and human accountability.

### Why "orchestrated"

The word "orchestrated" is useful because the human is not merely prompting. The human is arranging roles, timing, constraints, feedback, evidence, and context economics. A software orchestrator does not type every line, install every dependency, or read every generated line by default. The orchestrator is responsible for the system that emerges and for the questions that force the strategic model to prove the system is coherent.

This distinction matters. In low-discipline AI coding, the human often keeps asking for fixes until the demo appears to work. In inverted agentic workflows, the agent keeps asking the human to run commands, install packages, paste logs, or decide low-level repairs. In OAP, the human defines the task boundary, forbidden shortcuts, and evidence requirements; the strategic model translates those into execution; and the execution environment is powerful enough that the agent can do the low-level work itself.

### Why "agentic"

The method assumes the executor can act. It reads files, changes code, runs commands, observes failures, and adapts. This is a different class of activity from generating a code block in chat. Official Codex documentation, for example, distinguishes sandbox and approval settings that determine what an agent can technically do and when it must ask before acting [@codex-security].

OAP can be practiced with cautious approval settings, or in high-autonomy modes when the runtime is deliberately bounded. The stronger claim is not "always use full autonomy." The stronger claim is "if you grant autonomy, move safety into the runtime boundary, project constitution, PR discipline, and strategic evidence loop." A high-privilege agent inside a disposable VM can be safer and more productive than a weakly empowered agent that repeatedly recruits the human for operational chores.

### Why "programming"

Programming does not disappear. It moves. The system still consists of code, tests, migrations, configuration, documentation, and deployment scripts. The difference is that the human no longer has to be the primary typist or the agent's terminal assistant. The human programs the process: intent, architecture, constraints, work orders, evidence demands, and decisions.

### What OAP is not

OAP is not vibe coding. Vibe coding is useful as a term for informal natural-language-led software creation where the developer may accept results based on feel. OAP moves in the opposite direction: more explicit constraints, smaller units, more tests, stronger review, and more honest readiness language.

OAP is not ordinary AI pair programming. Pair programming keeps the human inside the implementation loop. OAP can remove the human from most typing and command execution, while increasing the human role in strategy and validation.

OAP is not fully autonomous software engineering. Marketing around "AI software engineers" often emphasizes independent execution. OAP emphasizes governed execution. The agent may have high autonomy inside the machine, but it does not own product meaning or release authority.

## I.4 The Human Role Shift

The most uncomfortable question in OAP is: if the human does not write most of the code and does not manually supervise every agent step, what exactly does the human do?

The answer is that the human moves from implementation labor to management responsibility. This is not a demotion. It is a more abstract and often more difficult role. In mature OAP, the human is no longer primarily a coder. The human may be a product owner, engineering manager, technical lead, release manager, domain expert, or accountable decision maker. In many OAP projects, domain expertise matters more than coding expertise because the execution agent can produce code, while only the domain expert can judge whether the product is useful, safe, and faithful to the real workflow. That role can and must run a strong discipline: clear goals, explicit release criteria, acceptance thresholds, non-goals, risk posture, and evidence requirements. The human must understand enough about the domain, architecture, security, tests, and deployment to interrogate whether the system still makes sense. The human does that primarily through the strategic AI, not by becoming a slow manual wrapper around the execution agent.

![Role separation in OAP.](assets/fig-02-role-separation.svg)

### The human lead

The human lead owns:

- the problem definition;
- product purpose;
- domain truth;
- user needs;
- ethical and legal boundaries;
- risk appetite;
- prioritization;
- acceptance criteria;
- release decisions;
- responsibility when the result is wrong.

These cannot be delegated to a model. A model can help articulate them. It can challenge inconsistencies. It can produce checklists. It can compare alternatives. But responsibility remains with the human or organization using the method.

The human lead also decides when the strategic answer is not good enough. This is central. An execution agent can produce a clean diff, passing tests, and a persuasive report while still solving the wrong problem. A strategic model can summarize that report and still miss a domain risk. Only the human lead can decide whether the result serves the intended purpose.

The human lead should ask the strategic AI uncomfortable questions:

- Did we implement the exact requirement or only something adjacent?
- Does this match the domain workflow users actually follow?
- Which test would fail if the critical behavior regressed?
- Did the agent touch any secrets, migrations, credentials, or deployment files?
- What files changed for reasons not directly tied to the work order?
- What evidence would you show to a skeptical external reviewer?
- What would you refuse to merge?

These questions are higher leverage than asking the execution agent to explain every command while it is working.

### The strategic AI

The strategic AI is not used primarily as a code generator. It is the control plane and memory layer. Its jobs include:

- helping the domain expert discover the right software shape;
- comparing architecture and stack options;
- turning broad intent into architecture;
- identifying missing requirements;
- proposing safe implementation order;
- writing work orders for the execution agent;
- reviewing execution reports;
- spotting documentation drift;
- identifying security and testing gaps;
- preparing handoff material;
- estimating release readiness.

The strategic AI should be allowed to think, criticize, and disagree. It should not be reduced to a prompt beautifier. In OAP, the strategic model is closest to a staff engineer, architect, technical program manager, and reviewer combined. It is still not accountable. It is an advisory and synthesis layer.

Because the strategic model carries project continuity, it should be the strongest practical model available: high reasoning quality, long context, strong instruction following, and good ability to compare claims against evidence. This is the place to spend expensive model capacity. The strategic model is not burning context on repetitive file edits or local retries; it is preserving the project story, the domain assumptions, and the human's goal.

### The execution agent

The execution agent is the implementation labor. It should not decide the product. It should not silently expand the scope. It should not merge its own pull requests. It also should not routinely ask the human to perform environment setup on its behalf. Its job is to execute a bounded work order:

- inspect relevant files;
- install or configure required local tools inside the execution VM;
- make a scoped change;
- run requested tests;
- update documentation as required;
- commit only related files;
- open a pull request;
- report exactly what happened.

The execution agent is valuable because it can do tedious work at machine speed. It can also do incorrect work at machine speed. That is why OAP pairs high autonomy with narrow scope and evidence requirements. The executor's context only needs to last one PR-sized task. After that task, it can be compacted, reset, or replaced.

### The new human skill stack

OAP increases the value of:

- requirements thinking;
- architectural judgment;
- security thinking;
- test design;
- evidence interrogation;
- debugging from reports;
- release management;
- documentation discipline;
- prompt/work-order design;
- knowing when not to delegate.

It decreases the relative importance of remembering every framework idiom by heart and the value of doing setup chores manually. It does not remove the need to understand software.

### What happens to implementers

The statement that the human moves up the ladder is clearest for the person who controls the OAP loop. It is less automatic for the people whose previous work was line-level implementation. OAP adoption should not pretend that implementation labor remains unchanged. Some of that work is compressed. Some of it is automated. Some of it becomes more valuable because the system now needs stronger validation, review, operations, and domain translation.

In a healthy adoption, implementers move toward higher-leverage roles:

- translating domain intent into precise acceptance criteria;
- designing tests and fixtures that prove behavior;
- reviewing architecture, security, privacy, and operations risk;
- maintaining the agent runtime, project constitution, and CI gates;
- turning audit findings into bounded work orders;
- inspecting high-risk diffs rather than reading every generated line;
- owning release engineering and incident runbooks.

In an unhealthy adoption, implementers are simply removed from the loop and the remaining human rubber-stamps agent output. That is not mature OAP. The method works only when the work formerly spent on typing and routine setup is reinvested into judgment, evidence, domain correctness, security, and release honesty.

### The temptation to rubber-stamp

The main human failure mode is rubber-stamping. The agent returns a confident report. The tests look green. The PR exists. The strategic model summarizes it fluently. The human wants progress. The temptation is to accept.

OAP must train the opposite reflex: treat every report as a claim, not proof. Ask the strategic model to point to evidence. Ask whether the tests cover the risk. Ask whether the docs overclaim. Ask whether the change made the system conceptually cleaner or merely more complete-looking. Inspect the diff directly when the evidence is weak, the risk is high, or the strategic answer does not withstand questioning.

# Part II: Operational Preflight

## II.1 Runtime Design Principles

The execution agent's autonomy is not only a prompt choice. It is a runtime design decision. OAP can use cautious approval modes, but its most distinctive form uses a high-autonomy coding agent in a dedicated VM or similarly bounded machine environment. The VM is not trusted because the agent is harmless. It is trusted because it is hardened, isolated, reconstructable, and not the source of project truth.

![High autonomy belongs inside a deliberate runtime boundary.](assets/fig-06-runtime-boundary.svg)

### Why runtime matters

An agent that can edit files but cannot run tests is a code generator with extra steps. An agent that can run commands, install dependencies, start services, run migrations against test databases, inspect logs, and open pull requests can replace a large share of human implementation labor.

That power must be contained. The runtime should be designed so that the agent can be effective without being near production secrets or production data.

The runtime must also protect human time. A modern coding agent can attempt many edits, test runs, package installations, and repairs in the time a human spends reading one dependency error. If the agent is blocked by every missing tool, the human becomes the slow actuator in the system. The workflow then stops being OAP and becomes AI-directed human labor.

### Privilege as an efficiency boundary

High privilege is often treated only as a security problem. In OAP it is also an efficiency boundary. The question is not "how little can the agent do?" The question is "what can the agent do inside a space that we are willing to throw away?"

If the strategic AI decides that the execution agent should use a new testing library, browser runner, database extension, compiler, package manager, or migration tool, the execution agent should normally install and configure it inside the execution VM. The agent should document the commands and commit durable project changes. It should not require the human to chase dependencies manually unless the action crosses a deliberate safety boundary.

This distinction matters because dependency work is precisely the kind of low-level labor OAP is meant to remove from the human. A missing native library, Docker permission, Playwright browser, Python wheel, Node package, or database fixture can consume hours. Those hours are poor use of the human lead if the work can happen in a disposable VM.

The preferred design is therefore:

- high privilege inside the execution VM;
- no production secrets inside the execution VM;
- no irreplaceable data inside the execution VM;
- remote repository and PRs as durable truth;
- setup commands documented by the agent;
- ability to rebuild the VM from the repository and setup notes;
- ability to abandon a broken VM without losing project state.

If the agent destroys the VM, the failure is operational noise. If the human spends hours doing dependency work for the agent, the control loop has inverted.

### The bounded high-autonomy pattern

The core pattern is:

1. Use a dedicated VM, container, devcontainer, or cloud sandbox.
2. Put only the intended repository and test fixtures inside it.
3. Give the agent enough permission to install, build, test, and run local services.
4. Keep production credentials out.
5. Use separate test databases and disposable services.
6. Make all changes visible through version control.
7. Require pull requests rather than direct main changes.
8. Treat the remote repository, not the VM, as the source of truth.

This allows a high-autonomy mode to be useful without pretending it is harmless. Codex documentation identifies `--dangerously-bypass-approvals-and-sandbox`, also known as `--yolo`, as dangerous full access: no sandbox and no approvals [@codex-security]. Claude Code documents the equivalent high-autonomy permission-bypass mode as `--dangerously-skip-permissions`, equivalent to `--permission-mode bypassPermissions` [@claude-code-cli-reference]. OAP can use that kind of mode only when the outer machine boundary is the safety mechanism.

### No sudo password versus no boundary

The phrase "without sudo password" can mean two different things:

- the agent has no way to elevate and is constrained by the user account;
- the agent can run passwordless `sudo` for selected commands or broad administrative actions.

OAP should make this explicit. A good execution VM may allow passwordless access to local test setup commands, package installation, Docker for disposable services, browser dependencies, or database fixture creation. A bad execution VM gives broad root power near production data or valuable personal files.

The correct question is not "does the agent have sudo?" The correct questions are:

- What can the agent destroy?
- What secrets can it read?
- What networks can it reach?
- What persistent systems can it mutate?
- Can every change be reverted?
- Can every external effect be audited?
- Can the VM be rebuilt if it is damaged?
- Is the agent asking the human to do work it should be able to do safely inside the VM?

### Runtime checklist

Before high-autonomy execution, verify:

- The repository is under version control.
- The agent starts from a clean working tree or reports existing changes.
- Production secrets are absent.
- Test secrets are clearly fake or disposable.
- Databases are test databases.
- External APIs are mocked unless explicitly required.
- Network access is deliberate.
- Package installation policy is clear.
- Docker or service permissions are understood.
- VM rebuild steps are documented.
- The remote repository and PRs contain durable project truth.
- The agent cannot push directly to protected branches.
- The final output must be a branch and PR, not an untracked local mutation.

### Runtime anti-patterns

Avoid:

- running a high-autonomy agent on a developer laptop full of unrelated secrets;
- allowing access to production databases;
- giving an agent cloud credentials with broad permissions;
- letting the agent change CI secrets;
- letting the agent merge its own PR;
- forcing the agent to ask the human for routine dependency installation;
- accepting "tests passed" without command output or CI confirmation;
- running high autonomy in a folder that is not version-controlled.

High autonomy is not unsafe because it is high autonomy. It is unsafe when the surrounding system assumes the agent will behave like a careful human, or when the runtime contains assets that should never have been inside the blast radius. In a well-designed OAP runtime, the agent can be powerful because the environment is disposable and the durable state is elsewhere.

## II.2 Baseline Agent VM Setup

Operational preflight is the work done before the execution agent receives a coding task. It answers one question: can the agent run with enough power to be useful without being able to damage the human's workstation, host home directory, or long-lived credentials?

This is not a hostile-malware containment problem. OAP does not assume that coding agents are malicious. It assumes that autonomous command execution can be wrong, over-broad, confused by repository instructions, or pushed into unsafe paths by dependency scripts. The reasonable target is:

- the agent can install tools and run tests inside its own environment;
- the agent cannot read or overwrite the human's normal home directory;
- the agent cannot reach long-lived SSH, cloud, browser, password-manager, or production credentials;
- the agent can be reset cheaply;
- durable work lives in Git, not in the disposable machine.

For terminal coding agents, this matters most when using full-access or permission-bypass modes. Codex documents `--dangerously-bypass-approvals-and-sandbox`, also aliased as `--yolo`, as running commands without approvals or sandboxing and says it should be used only inside an externally hardened environment [@codex-cli-reference]. Claude Code documents `--dangerously-skip-permissions` as skipping permission prompts and equivalent to `--permission-mode bypassPermissions` [@claude-code-cli-reference]. The OAP answer is to put the hard boundary outside the CLI agent: the guest machine, distro, sandbox, or VM is the safety boundary.

### Linux guest baseline

Use this pattern inside a disposable Ubuntu VM, imported WSL2 distro, Lima VM, Multipass VM, Hyper-V Linux VM, or similar guest:

```bash
sudo adduser agent
sudo usermod -aG sudo agent
sudo visudo -f /etc/sudoers.d/90-agent-nopasswd
```

Add:

```sudoers
agent ALL=(ALL) NOPASSWD:ALL
```

Then verify:

```bash
sudo chmod 0440 /etc/sudoers.d/90-agent-nopasswd
sudo visudo -c
su - agent
sudo -n true && echo "passwordless sudo works"
```

Keep agent state guest-local:

```bash
mkdir -p "$HOME/.codex-agent"
export CODEX_HOME="$HOME/.codex-agent"
mkdir -p "$HOME/.claude-agent"
export CLAUDE_CONFIG_DIR="$HOME/.claude-agent"
```

For a high-autonomy Codex CLI run inside this guest:

```bash
cd ~/work/project
codex --yolo
```

The equivalent long Codex CLI form is:

```bash
codex --dangerously-bypass-approvals-and-sandbox
```

For the same execution role with Claude Code CLI:

```bash
cd ~/work/project
claude --dangerously-skip-permissions
```

The equivalent Claude Code CLI setting form is:

```bash
claude --permission-mode bypassPermissions
```

The repository should be cloned into the guest filesystem or into a narrow project mount. Do not mount the host home directory writable. Do not mount host SSH keys, cloud credential directories, browser profiles, password-manager files, Docker socket, or production `.env` files. A guest-local `~/.ssh/authorized_keys` file for inbound access is fine; host private keys and production SSH credentials are not.

### SSH access to the guest

For SSH-in workflows, install OpenSSH inside the guest and connect from the host:

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh || sudo service ssh start
mkdir -p ~/.ssh
chmod 700 ~/.ssh
```

Then add the host public key to `~/.ssh/authorized_keys` inside the guest. Prefer SSH key login over passwords. For a local VM, bind forwarded ports to localhost when possible:

```text
host localhost:2222 -> guest port 22
```

The SSH boundary is a convenience boundary, not the security boundary. The security boundary is still the guest isolation, mounted filesystem policy, and absence of host secrets. In an SSH-in VM or sandbox, `~/.ssh` will normally exist. Its existence is not a preflight failure; copied host identities, production private keys, agent forwarding into the guest, or broad credential mounts are the failure.

### Snapshot and reset

The preflight is incomplete until reset is cheap:

```text
before run:
  snapshot/export/checkpoint the guest

after broken run:
  destroy or revert the guest

after useful run:
  preserve only Git commits, PRs, logs, and documented setup changes
```

If the environment takes hours to reconstruct, humans will be tempted to preserve it as an irreplaceable workstation. OAP environments should instead be managed as replaceable runtime units: valuable when working, rebuildable when damaged.

## II.3 Platform Recipes

The following recipes are starting points, not compliance requirements. Choose the weakest setup that protects host data and still lets the agent do real work. The default recommendation is a per-project Linux VM or WSL2 distro for Linux-oriented work, and a persistent Windows VM only when native Windows toolchains are required.

![Operational preflight platform choices.](assets/fig-07-preflight-platforms.svg)

### Windows option A: WSL2 Ubuntu per project

WSL2 is a convenient Windows-hosted Linux environment. Microsoft documents `wsl --install` as the default installation path and notes that new installs use WSL2 by default [@microsoft-wsl-install]. For coding-agent work:

```powershell
wsl --install -d Ubuntu
wsl -l -v
wsl --set-version Ubuntu 2
```

Inside Ubuntu:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y build-essential git curl wget unzip zip ca-certificates openssh-server
```

Store Linux projects in the Linux filesystem, not under `/mnt/c`, because Microsoft recommends keeping Linux-command-line projects in the WSL filesystem for performance [@microsoft-wsl-filesystems]:

```bash
mkdir -p ~/work
cd ~/work
git clone <repo-url>
```

For a hardened agent distro, reduce accidental host coupling in `/etc/wsl.conf`:

```ini
[automount]
enabled=false

[interop]
enabled=false
appendWindowsPath=false

[user]
default=agent
```

WSL settings are split between per-distribution `/etc/wsl.conf` and user-level `.wslconfig`; Microsoft documents that changes apply after the distribution fully stops and restarts [@microsoft-wsl-config].

To SSH into WSL2 from Windows, run `sshd` in the distro and connect to the distro address or to a forwarded port. On current Windows 11, mirrored networking can make WSL reachable more naturally from the local network, but Microsoft documents firewall considerations for inbound access [@microsoft-wsl-networking]. For a simple local-only setup, prefer:

```powershell
ssh -p 2222 agent localhost
```

with an explicit Windows port proxy or VM tool forwarding rule if localhost forwarding is not automatic in the target Windows/WSL version.

### Windows option B: Hyper-V Linux VM

Use a real Linux VM when WSL2 filesystem and networking behavior is too coupled to the host, or when you want snapshots/checkpoints with a clearer boundary:

```text
Windows host
+-- Hyper-V Ubuntu VM
    +-- repo cloned inside VM
    +-- OpenSSH enabled
    +-- agent user with passwordless sudo
    +-- no host profile shares
    +-- checkpoint before each major run
```

Connect over SSH, use a VM checkpoint before each agent session, and keep the repository remote as the durable truth.

### Windows option C: Windows Sandbox for ephemeral native work

Windows Sandbox is useful for disposable native-Windows smoke tests or one-off agent runs. It supports `.wsb` configuration with networking, mapped folders, and a logon command; mapped folders are available before the logon command runs [@microsoft-windows-sandbox-config]. It is deliberately ephemeral. When the sandbox closes, installed tools, users, OpenSSH host keys, repository clones, and Build Tools installations are gone.

Example `AgentSandbox.wsb`:

```xml
<Configuration>
  <Networking>Enable</Networking>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>C:\agent-sandbox\in</HostFolder>
      <SandboxFolder>C:\agent-in</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
    <MappedFolder>
      <HostFolder>C:\agent-sandbox\out</HostFolder>
      <SandboxFolder>C:\agent-out</SandboxFolder>
      <ReadOnly>false</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>powershell.exe -ExecutionPolicy Bypass -File C:\agent-in\bootstrap.ps1</Command>
  </LogonCommand>
  <MemoryInMB>8192</MemoryInMB>
</Configuration>
```

Inside `bootstrap.ps1`, OpenSSH Server can be installed and started with the Windows optional capability commands documented by Microsoft [@microsoft-openssh-windows]:

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic

if (!(Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue)) {
  New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" `
    -DisplayName "OpenSSH Server (sshd)" `
    -Enabled True `
    -Direction Inbound `
    -Protocol TCP `
    -Action Allow `
    -LocalPort 22
}

ipconfig | Out-File C:\agent-out\sandbox-network.txt
```

On Windows 11 24H2 and later, the Windows Sandbox CLI can list sandboxes and report a sandbox IP [@microsoft-windows-sandbox-cli]:

```powershell
wsb list
wsb ip --id <sandbox-id>
```

Visual Studio Build Tools can also be installed non-interactively. Microsoft documents quiet command-line installation parameters such as `--quiet`, `--wait`, and `--norestart`, and publishes Build Tools workload/component IDs [@microsoft-vs-install; @microsoft-vs-buildtools]:

```powershell
$vsArgs = @(
  "--quiet", "--wait", "--norestart", "--nocache",
  "--installPath", "C:\BuildTools",
  "--add", "Microsoft.VisualStudio.Workload.VCTools",
  "--includeRecommended"
)
Start-Process C:\agent-in\vs_BuildTools.exe -Wait -ArgumentList $vsArgs
```

This is technically workable, but slow if repeated often. Use it when ephemerality is the point.

### Windows option D: persistent Windows VM with OpenSSH

Use a persistent Windows VM when the project needs repeated native Windows work: MSVC, Windows SDKs, COM, PowerShell-only automation, Windows service behavior, or Visual Studio Build Tools caches. Configure it like a real agent VM:

```text
Windows host or Linux hypervisor
+-- Windows guest VM
    +-- OpenSSH Server enabled
    +-- dedicated local agent account
    +-- Visual Studio Build Tools installed once
    +-- checkpoint before high-autonomy work
    +-- no host home/profile share
    +-- repository cloned inside the VM
```

This VM is persistent, so treat it as a managed development machine. Patch it, snapshot it, rotate credentials, and periodically rebuild it. Also note the licensing boundary: a persistent Windows guest normally requires appropriate Windows licensing separate from the host or from Windows Sandbox entitlement. Microsoft licensing guidance distinguishes Windows desktop virtualization and VDA access rights from ordinary local installation rights [@microsoft-windows-licensing]. This manual does not give legal advice; verify the licensing model before standardizing a persistent Windows VM.

### Linux option A: KVM/libvirt VM

On a Linux workstation, a KVM/libvirt VM is the cleanest default. Ubuntu documents Virtual Machine Manager as a GUI for managing local and remote VMs using tools such as `virt-install`, `virt-clone`, and `virt-viewer` [@ubuntu-virt-manager]. A practical setup is:

```bash
sudo apt update
sudo apt install -y qemu-kvm libvirt-daemon-system virt-manager openssh-client
```

Create an Ubuntu VM, enable OpenSSH inside it, and connect from the host. For host-only development, NAT plus SSH is usually enough. For LAN access, use bridged networking or explicit port forwarding. libvirt documents the common "virtual network" and "shared physical device" models, and its network XML format is the authoritative reference for network definitions [@libvirt-networking; @libvirt-network-xml].

### Linux option B: Multipass or LXD VM

For a faster CLI-native Ubuntu VM, Multipass is reasonable. Canonical describes Multipass as a tool for quickly generating cloud-style Ubuntu VMs on Linux, macOS, and Windows [@canonical-multipass]:

```bash
sudo snap install multipass
multipass launch 24.04 --name agent --cpus 6 --memory 12G --disk 80G
multipass shell agent
```

Then configure the guest user, SSH, and passwordless sudo. LXD virtual machines are another option when an organization already uses LXD; Ubuntu documents LXD as managing both system containers and virtual machines [@ubuntu-lxd].

### Linux option C: restricted container for trusted work

Containers are convenient for trusted repositories, but they are a weaker boundary than a VM for unrestricted agents. Avoid:

```text
--privileged
-v /:/host
-v ~/.ssh:/home/agent/.ssh
-v /var/run/docker.sock:/var/run/docker.sock
--net=host
```

A container can be useful for narrow CI-like tasks, but a full `--yolo` coding agent with package installation and arbitrary command execution belongs in a VM unless the repository and dependency scripts are already trusted.

### Linux option D: OverlayFS plus chroot as reset mechanism

OverlayFS can provide a fast filesystem reset layer:

```bash
sudo mkdir -p /srv/agent/base /srv/agent/upper /srv/agent/work /srv/agent/merged

sudo mount -t overlay overlay \
  -o lowerdir=/srv/agent/base,upperdir=/srv/agent/upper,workdir=/srv/agent/work \
  /srv/agent/merged

sudo chroot /srv/agent/merged /bin/bash
```

The Linux kernel documentation describes the lower, upper, work, and merged directories used by OverlayFS [@linux-overlayfs]. This is useful as a reset mechanism, not as a strong security boundary for a privileged autonomous agent. `systemd-nspawn` is stronger than bare chroot and useful for lightweight machine containers, but it still does not replace a VM for untrusted full-access work [@systemd-nspawn].

### macOS option A: Lima Ubuntu VM

On macOS, use a Linux VM rather than giving the agent access to the macOS host. Lima is a good command-line-native default. Its documentation shows that host home directories are mounted read-only by default and can be made writable or disabled explicitly [@lima-usage]. For OAP, prefer a narrow writable share or no host mount.

Example `agent.yaml`:

```yaml
images:
- location: "https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-arm64.img"
  arch: "aarch64"
- location: "https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64.img"
  arch: "x86_64"

cpus: 6
memory: "12GiB"
disk: "80GiB"

mounts:
- location: "~"
  writable: false
- location: "/tmp/lima-agent-share"
  writable: true
```

Start and enter:

```bash
brew install lima
limactl start ./agent.yaml --name agent
limactl shell agent
```

Lima documents several host-filesystem mount methods, including reverse-sshfs, 9p, and virtiofs depending on version and VM backend [@lima-mounts]. Keep those mounts narrow.

### macOS option B: Multipass or UTM

Multipass is also available on macOS and gives a simple Ubuntu VM:

```bash
brew install --cask multipass
multipass launch 24.04 --name agent --cpus 6 --memory 12G --disk 80G
multipass shell agent
```

Use UTM, VMware Fusion, or Parallels when the organization already standardizes on those tools. The OAP principle is unchanged: do not give the agent broad write access to the macOS home directory or long-lived host credentials.

## II.4 Preflight Checklist

Before launching an unrestricted agent mode, the operator should be able to check every item below:

```text
[ ] Agent runs inside disposable VM/distro/sandbox, not normal host account
[ ] Agent user is dedicated
[ ] Passwordless sudo/admin exists only inside the guest
[ ] Repository is inside guest or narrow writable mount
[ ] Host home directory is not mounted writable
[ ] No host/prod SSH private keys are mounted or copied into guest
[ ] No host/prod cloud, kube, or Docker credentials are in guest
[ ] No password-store files, browser profile, or production .env in guest
[ ] Guest-local ~/.ssh is expected for SSH-in guests
[ ] Guest-local ~/.ssh has VM/sandbox access material only
[ ] CODEX_HOME is guest-local
[ ] Network policy is understood
[ ] Snapshot/export/checkpoint exists
[ ] Git working tree starts clean or known dirty
[ ] Logs are enabled
[ ] Credentials, if any, are short-lived and least-privilege
[ ] Agent cannot merge its own PR
[ ] Recovery path has been tested once
```

The preflight can be short because OAP does not require perfect isolation. It requires a boundary that makes the expected failure survivable. A reasonable summary is:

> The agent may be powerful inside the guest, but the guest must not contain anything the human cannot afford to lose or rotate.

# Part III: Strategic Discovery and Constitution

## III.1 The First Conversation With the Strategic Model

The strategic layer is where OAP differs most from ordinary coding-agent use. Many workflows delegate a task directly to a coding agent. OAP inserts a reasoning layer before and after execution, and it makes that reasoning layer the human's main interface to the project.

The human should not normally manage the execution agent directly. Direct management is tempting because it feels precise: paste this error, run that command, inspect that file. But it consumes the human's scarce attention at the wrong level. This is especially important when the human is a domain expert rather than a professional developer. The strategic AI should absorb executor reports, inspect repository evidence, translate technical claims into domain-relevant terms, and answer the human's high-level questions.

![Strategic discovery turns domain intent into executable project law.](assets/fig-08-strategic-discovery.svg)

### The discovery conversation

Strategic discovery starts with the human's domain problem, not with a stack. The human asks the strongest available strategic model to determine what kind of software system is needed, which tools are appropriate, what professional rules should govern the work, and what the execution agent must not improvise.

The conversation should be explicit enough that a future `AGENTS.md` can be drafted from it. A useful sequence is:

1. State the domain problem in operational language.
2. Ask what kind of system this really is.
3. Ask which architecture and trust boundaries fit.
4. Ask which stack is boring, robust, and suitable.
5. Ask which data model, background jobs, admin flows, and tests a professional team would expect.
6. Ask what should be excluded from the first release.
7. Ask the model to convert the decisions into `AGENTS.md`, design docs, and first work orders.

The human does not need to know the answer in advance. The human needs to know the domain well enough to reject the wrong answer.

### API Gateway discovery example

The SLAIF API Gateway work demonstrates the pattern clearly. The opening human problem was not "write a FastAPI app." It was a training and governance problem: for SLAIF/WP6 workshops, participants needed LLM API access with bounded cost, auditable usage, and no exposure of real provider keys.

The strategic model first clarified the upstream limitation: ordinary provider API keys and project budgets were not enough for strict per-key hard quota. That shifted the product category. The system was no longer "a set of keys" or "a script for users." It became a controlled OpenAI-compatible gateway: users receive gateway-issued keys, use ordinary OpenAI SDK conventions, and the backend authenticates, checks quota, routes to providers, substitutes server-side provider credentials, records usage, and fails closed when policy or pricing is unknown. The public repository now reflects that product shape [@slaif-repo].

The discovery chain looked like this:

| Domain question | Strategic translation | Resulting project decision |
|---|---|---|
| Can users have hard per-key OpenAI spend limits? | Native provider controls are insufficient for strict per-user workshop caps. | Build a local quota-enforcing gateway. |
| Can users keep ordinary OpenAI examples? | Compatibility matters more than custom naming. | Use `OPENAI_API_KEY` and `OPENAI_BASE_URL`; expose `/v1`. |
| How should keys be stored? | Treat gateway keys as bearer tokens and never store plaintext. | Store HMAC-derived token hashes with server-side pepper. |
| How can hard quota survive concurrency? | Estimate before forwarding and finalize after provider usage returns. | Implement reserve-then-finalize quota/accounting. |
| Which backend stack fits? | Async HTTP proxying, streaming, database transactions, and admin workflows are central. | FastAPI/Starlette, `httpx`, PostgreSQL, Redis/Celery, SQLAlchemy/Alembic. |
| How should admins manage workshops? | The system needs both web and terminal operations. | Server-rendered admin dashboard plus Typer CLI. |
| How should the executor be guided? | Architecture and invariants must be repository law before broad implementation. | Write `AGENTS.md`, schema docs, compatibility matrix, tests, and PR workflow. |

The important point is that the model did not merely answer syntax questions. It helped the domain expert discover the product category, then the architecture, then the implementation constitution.

### Human prompt examples

In the API Gateway chats, the human's prompts were short but managerial. They asked questions like:

```text
Is hard per-key spend control possible?

If not, can I build my own API server, issue my own keys,
do the accounting, and forward allowed requests to OpenAI?

Can the client remain the ordinary OpenAI Python client
with no code changes?

Before writing AGENTS.md, tell me how cost and token
accounting per key should work.

Now specify the building blocks and tools:
database, framework, admin UI, CLI, email, tests, deployment.

Should the database schema be placed in the repo before
the execution agent starts?
```

These are not low-level implementation prompts. They are management prompts. The human supplies domain intent, constraints, and acceptance pressure. The strategic model supplies architecture options and professional defaults. The execution agent later receives bounded work.

### Technical decisions produced by discovery

A good strategic model should make technical decisions legible to a domain expert. In the API Gateway case, the model explained not only what to use, but why:

- **FastAPI, Starlette streaming, Uvicorn/Gunicorn**: asynchronous API logic, Server-Sent Events pass-through, and production worker management.
- **PostgreSQL, SQLAlchemy async, asyncpg, Alembic**: durable quota/accounting truth, non-blocking database access, and reproducible schema evolution.
- **Redis and Celery**: short-lived coordination, rate limits, reservations, and background jobs such as email and reports.
- **Jinja2, HTMX, Tailwind, Typer**: simple admin dashboard and CLI without turning the project into a large frontend application.
- **pytest, pytest-asyncio, respx/pytest-httpx, testcontainers, Hypothesis, Playwright**: tests for async code, mocked upstream APIs, real database/Redis behavior, accounting invariants, and admin UI flows.
- **Docker Compose**: reproducible small deployment with API, database, Redis, worker, scheduler, and optional reverse proxy.

The domain expert did not need to know all these components beforehand. The human needed to interrogate whether each component served the domain goal: bounded workshop keys, provider-key secrecy, usage evidence, OpenAI-compatible examples, and release honesty.

### Discovery artifacts

The output of strategic discovery should be written down before the execution agent starts broad implementation. In a mature OAP project, discovery produces at least:

- a short architecture note;
- an `AGENTS.md` constitution;
- a data model or schema document;
- a compatibility matrix when external APIs are being emulated;
- a test strategy;
- a deployment sketch;
- a first PR-sized implementation sequence;
- explicit non-goals.

For the API Gateway, one decisive discovery artifact was the database schema. The strategic model advised putting a human-readable `docs/database-schema.md` into the repository before Codex implemented SQLAlchemy models and Alembic migrations. That is the right OAP reflex: make the strategic decision durable before asking the executor to produce code.

### Strategic responsibilities

The strategic layer should:

- understand the product goal;
- preserve domain assumptions;
- translate domain language into technical work orders;
- preserve the project's long-running context;
- identify missing assumptions;
- sequence work safely;
- choose the next narrow PR;
- write explicit work orders;
- interpret agent reports;
- compare results against the constitution;
- map claims to concrete evidence;
- answer the human's readiness questions;
- explain technical evidence in domain terms;
- decide whether to repair, continue, or stop;
- maintain project-state summaries;
- create handoffs when context grows too large.

The strategic layer is not necessarily one model forever. A project may use one model for planning, another for code review, another for documentation critique, and another for external audit. What matters is that the human lead controls when and why these models are consulted, and that one strategic thread remains responsible for the project story.

### Model selection and context economics

OAP should normally use the strongest practical model for the strategic layer. This means a model with strong reasoning, long context, reliable instruction following, good code comprehension, and enough patience to compare claims against evidence. The strategic model is where expensive tokens are most valuable.

The reason is context economics. The strategic model's context burns slowly. It contains:

- the product goal;
- domain vocabulary and constraints;
- architectural decisions;
- unresolved risks;
- previous PR outcomes;
- current release status;
- evidence trails;
- human preferences;
- handoff summaries;
- open questions.

The execution agent's context burns quickly because it reads files, edits code, sees command output, retries failures, and explores local state. That is acceptable. The executor only needs enough context to complete one PR-sized task. The strategic model should preserve continuity across many such tasks.

The desired operating state is:

- the strategic AI does not lose context;
- the human does not lose the goal;
- the execution agent does not need to remember beyond the current PR;
- durable state is written back into the repository, PRs, issues, docs, and handoffs.

### Strategic output: the work order

The strategic layer's most important output is not code. It is a work order that the execution agent can follow without improvising the product and without asking the human to perform low-level work. When the human is a domain expert, the work order is also a translation artifact: it turns domain intent into implementable software behavior while preserving acceptance criteria.

A good work order includes:

- current verified project state;
- exact task goal;
- domain behavior to preserve;
- acceptance criteria in domain language;
- files or areas to inspect;
- constraints and non-goals;
- required implementation behavior;
- tests to add or run;
- tools, dependencies, or local services the agent may install inside the execution VM;
- documentation updates;
- branch and PR instructions;
- final report format.

This is one reason OAP is not "prompt engineering" in the shallow sense. The prompt is a software management artifact. It encodes scope, risk, verification, and workflow.

### Strategic review of agent reports

After execution, the strategic layer reviews:

- Did the agent do the requested task?
- Did it do extra work?
- Did it touch unrelated files?
- Are the tests meaningful?
- Are skipped tests honestly reported?
- Did documentation change with behavior?
- Did the change preserve architecture?
- Did it introduce new risk?
- Did the agent ask the human to do work that belonged inside the execution VM?
- Is a repair prompt needed before merge?

The strategic model performs the first review pass and prepares answers for the human. The human must judge that review. A model can miss risks. A model can overpraise. A model can rationalize. The human lead must remain skeptical, but skepticism should be expressed as high-level interrogation:

- Show me the exact test evidence.
- Show me the files that enforce the invariant.
- Explain why this does not expose secrets.
- Explain why this dependency is necessary.
- Explain what would fail if the behavior were broken.
- Tell me what you are least confident about.

### Strategic continuity

Long projects need continuity. The strategic layer should periodically produce concise state handoffs. These are not just notes for humans. They are context-preservation artifacts for future strategic sessions:

```markdown
# Project Handoff

## Current truth
- Main branch state:
- Open PRs:
- Recently merged PRs:
- Known CI status:

## Product goal
- Current milestone:
- Release target:

## Implemented
- ...

## Missing
- ...

## Non-negotiable rules
- ...

## Next recommended task
- ...

## Do not do next
- ...
```

The handoff is not a substitute for verifying current repository state. It is a memory aid. Every new strategic session should treat the live repository as authoritative.

## III.2 Writing the Project Constitution

A project constitution is the durable rule set that tells agents how to work in the repository. In Codex, the direct mechanism is `AGENTS.md`: Codex reads such files before starting work and layers global, project, and nested instructions by precedence [@codex-agents-md]. In Claude Code, the analogous project instruction mechanism is `CLAUDE.md`, which Anthropic documents as persistent instructions loaded at the start of a session [@claude-code-memory]. Other tools use related mechanisms: repository custom instructions or rule files [@github-copilot-agent; @cursor].

When a project may be worked by both Codex CLI and Claude Code CLI, keep `AGENTS.md` and `CLAUDE.md` aligned. They do not need to be word-for-word identical, but the operational law should be the same: mission, architecture, forbidden actions, tests, workflow, and final report requirements.

OAP treats the constitution as a first-class artifact.

![The project constitution as layered operational guidance.](assets/fig-03-project-constitution.svg)

### Discovery before constitution

The constitution should be written after strategic discovery, not before it. Otherwise `AGENTS.md` becomes a list of arbitrary preferences rather than the operational law of a real product.

A domain expert should first use the strategic model to explore:

- the product category;
- user workflow;
- operational constraints;
- security and privacy boundaries;
- plausible architectures;
- stack choices and alternatives;
- minimum viable release scope;
- explicit non-goals.

The result of that conversation becomes the constitution. The strategic model can draft it, but the human must judge whether it reflects the real domain. This is why the opening phase of OAP is managerial. The human is not asking, "write me Django code." The human is asking, "given this domain and these constraints, should this be Django, FastAPI, Go, a browser extension, a local agent, a queue-backed system, a signed-artifact system, or something else?"

### What a constitution is

A constitution is not a README. A README explains the project to users and contributors. A constitution instructs the agent how to behave while changing the project.

A constitution is not a single prompt. A prompt is temporary. A constitution persists across tasks and becomes part of the repository's operational memory.

A constitution is not merely style guidance. It should include architecture, safety rules, tests, documentation contracts, workflow, and definition of done.

### Minimum constitution structure

A serious OAP constitution should include:

```markdown
# AGENTS.md or CLAUDE.md

## Discovery Summary
- Domain problem.
- Chosen product shape.
- Architecture and stack rationale.
- Important alternatives rejected.
- First release scope.

## Mission
- What this repository is for.
- What user promise must not be broken.

## Architecture
- Main components.
- Stack and versions.
- Ownership boundaries.
- Data flow assumptions.

## Non-negotiable invariants
- Security rules.
- Privacy rules.
- Data retention rules.
- Backward compatibility rules.

## Forbidden actions
- Files or systems not to touch.
- Dependencies not to add.
- Secrets never to log or commit.
- Production resources never to access.

## Workflow
- Branch requirements.
- Commit requirements.
- Pull request requirements.
- No direct commits to main.

## Testing
- Required unit tests.
- Required integration tests.
- When browser/E2E tests are required.
- How to report skipped or blocked tests.

## Documentation
- Which docs must change with behavior.
- Where compatibility matrices live.
- How to state limitations.

## Reporting
- Required final report format.
- Required evidence.
- Required risk and follow-up section.
```

### Constitution as memory

Long AI-assisted projects suffer from context decay. Chat histories become too long. Uploaded files expire. Models forget details. A constitution counters this by putting stable project law in the repository.

The constitution should evolve when recurring corrections appear. If an agent repeatedly removes a required README block, add a rule. If an agent repeatedly claims skipped tests passed, add reporting language. If a security review finds a class of unsafe behavior, encode it as a forbidden action and a test requirement.

The official Codex documentation explicitly frames `AGENTS.md` as durable project guidance and recommends using it for build and test commands, review expectations, conventions, and recurring feedback [@codex-agents-md]. OAP extends that idea: for serious work, the constitution is the center of governance.

### Constitution smell tests

A constitution is too weak if:

- it only says "write good code";
- it does not name tests;
- it does not define forbidden behavior;
- it does not explain release or PR workflow;
- it does not mention secrets;
- it does not say what evidence the agent must report;
- it cannot help a new strategic model continue the project.

A constitution is too large if:

- it contains stale historical chat;
- it repeats documentation better kept elsewhere;
- it exceeds tool context limits;
- it contains contradictory rules;
- agents routinely ignore it because it is too diffuse.

The solution is layered guidance: top-level rules for the whole repo, nested rules for specialized directories, and separate docs for long background material.

## III.3 Work-Order Engineering

Prompting in OAP is not about clever phrasing. It is about work-order engineering. A work order turns strategic judgment into executable instructions. In mature OAP, the human does not usually write this prompt directly for the execution agent. The human explains intent and questions to the strategic AI; the strategic AI compiles the executor work order.

This aligns with current coding-agent practice: the durable setup, the real working directory, and the specificity of instructions matter as much as the model invocation itself [@codex-best-practices].

### Work-order template

```markdown
# Coding Agent Work Order

You are working in repository: `<repo>`.

## Governing instructions
- Read `AGENTS.md` first.
- Follow repository workflow.
- If live repository state differs from this prompt, report the difference.

## Current verified state
- ...

## Goal
- ...

## Scope
- ...

## Non-goals
- ...

## Files to inspect
- ...

## Required behavior
- ...

## Tests required
- ...

## Local setup allowed
- Install missing test tools inside the execution VM if required.
- Document any package, browser, database, or service setup performed.
- Do not ask the human to perform routine dependency setup unless a safety boundary blocks it.

## Documentation required
- ...

## Workflow
- Start from fresh `main`.
- Create a feature branch.
- Commit only related files.
- Push branch.
- Open a pull request.
- Do not merge.

## Final report
- Branch.
- Commit.
- PR URL.
- Summary.
- Tests run and results.
- Local tools or dependencies installed.
- Docs changed.
- Risks or skipped tests.
```

### Current state must be current

The work order should not blindly trust an old handoff. It should say what is known and instruct the agent to verify. If the repository has moved, the agent should report it rather than building on stale assumptions.

This is especially important for long projects where multiple PRs are merged between chats. The strategic layer should verify current `main`, open PRs, and CI before drafting the next task. The human should be able to ask the strategic model "what is true now?" and receive an answer grounded in repository state, not memory alone.

### Non-goals as guardrails

Agents do not naturally understand product boundaries. They understand text. If a task should not touch a subsystem, say so. If a tempting feature is deferred, say so. If docs must not overclaim production readiness, say so.

Good non-goals are concrete:

- "Do not add a new database migration."
- "Do not change public API shape."
- "Do not store prompts or raw response bodies."
- "Do not run real upstream API calls."
- "Do not report skipped browser tests as passed."

### Report format as interface

The final report is the interface between execution and strategy. If the report is unstructured, the strategic model must reconstruct evidence manually and the human will be pulled toward low-level audit work. If the report is structured, the strategic model can answer high-level human questions faster and with less drift.

Reports should distinguish:

- passed;
- failed;
- skipped;
- not run;
- blocked;
- out of scope.

The phrase "all tests passed" should be avoided unless it literally means the requested or full relevant test suite passed. "Focused tests passed; integration tests were not run" is more useful.

### Prompt smells

A prompt is weak if it says:

- "make this better";
- "finish the feature";
- "fix all issues";
- "use your judgment" without constraints;
- "run tests" without naming which tests;
- "update docs" without naming the documentation contract;
- "ask me if dependencies are missing" without naming a safety reason.

A prompt is stronger if the strategic AI can determine success before the agent starts and the human can later interrogate the evidence without reconstructing the work manually.

# Part IV: Coding and Verification

## IV.1 The Execution Layer

The execution layer is the coding agent operating against a repository. It is valuable because it can perform implementation labor: navigating files, editing code, installing tools, running test commands, interpreting failures, and iterating. It is not valuable because it remembers the whole project forever. Continuity belongs to the strategic layer and the repository.

### What the executor should own

The executor should own:

- mechanical implementation;
- local exploration;
- local dependency and tool setup inside the execution VM;
- disposable service setup for tests;
- creating or updating tests;
- running specified verification;
- fixing failures within scope;
- documenting changed behavior;
- producing commits and PRs;
- reporting exact outcomes.

The executor should not own:

- product strategy;
- release claims;
- security exceptions;
- production access decisions;
- broad scope expansion;
- final merge decisions.
- long-term project memory;
- assigning routine environment chores to the human.

### The executor as constrained implementer

A coding agent is most useful when the task is narrow enough that success can be evaluated. "Improve the system" is too vague. "Add a fail-closed check for unknown pricing and tests proving no provider call occurs before rejection" is better.

The executor should not need to infer the release roadmap. It should not need to decide whether a feature belongs in RC2. It should receive a bounded task and return evidence. If it needs a tool to complete that task, it should install or configure it within the allowed execution boundary and report the change.

### One task, one context

The execution agent's context should be treated as a consumable work buffer. It should last long enough to complete the current PR-sized task and no longer. Between tasks, the agent can be compacted, reset, or given a fresh work order from the strategic model.

This prevents two common failures:

- the executor accumulates stale assumptions from earlier work;
- the human tries to preserve context by manually narrating every detail to the executor.

The strategic model carries continuity. The executor carries action. The repository carries truth.

### Required executor report

Every execution task should end with a report like:

```markdown
## Agent Report

Branch: feature/short-name
Commit: abc1234
Pull request: https://github.com/org/repo/pull/123

## Summary
- ...

## Files changed
- ...

## Tests run
- command: result
- command: result

## Documentation impact
- ...

## Safety confirmations
- No production secrets committed.
- No unrelated files changed.
- No skipped test reported as passed.
- New local tools or dependencies installed only inside allowed execution space.

## Known limitations
- ...

## Follow-up recommended
- ...
```

This report is not proof by itself. It is an index into evidence that the strategic model can inspect and the human can interrogate.

### Executor discipline

Execution agents should:

- start from the correct branch;
- inspect before editing;
- make small commits;
- use existing project patterns;
- avoid broad refactors unless requested;
- run focused tests first, broader tests when needed;
- install permitted dependencies without pulling the human into routine setup;
- stop and report real blockers;
- never fake a PR URL;
- never claim unavailable CI results.

The most dangerous executor is not the one that fails. It is the one that succeeds loudly while quietly violating scope.

## IV.2 PR-Sized Delegation

OAP's atomic unit is the pull request. A PR is small enough for the strategic model to inspect deeply, large enough to preserve useful implementation context, and structured enough to carry evidence. The human does not need to read every line by default, but the PR must be coherent enough that the human can demand precise answers about it.

![PR-sized delegation pipeline.](assets/fig-04-pr-pipeline.svg)

### Why PR-sized work works

PR-sized delegation has several advantages:

- It forces scope.
- It creates a durable diff.
- It supports CI.
- It invites strategic review and human interrogation.
- It can be reverted.
- It preserves history.
- It separates implementation from merge authority.

This is why "one prompt, one PR" is often a good default. There are exceptions: investigation-only tasks, verification-only runs, or documentation planning may not need PRs. But implementation work should normally produce a reviewable branch that the strategic model can summarize, challenge, and connect to tests.

### Anatomy of a PR-sized task

A good task has:

- a name;
- a reason;
- a defined scope;
- explicit non-goals;
- relevant files;
- acceptance criteria;
- tests;
- documentation impact;
- report requirements;
- permitted local setup or dependency work.

Example:

```text
Task: Add endpoint permission check for conversation item delete.

Current state:
- Conversation references exist.
- Item create/list/retrieve are implemented.

Goal:
- Delete must require explicit conversation item permission.
- Unknown or non-owned conversation IDs must return OpenAI-shaped 404 before provider forwarding.

Non-goals:
- Do not implement conversation update.
- Do not change Chat Completions.
- Do not add local content storage.

Tests:
- Add unit tests for permission denial.
- Add provider forwarding test proving no upstream call on non-owned ID.
- Run focused tests and ruff.

PR:
- New branch from main.
- Commit only related files.
- Open PR.
- Do not merge.
```

### Scope control

The most important section is often "Non-goals." Agents are trained to be helpful. Without explicit non-goals, helpfulness becomes scope creep.

Non-goals should name:

- features not to implement;
- files not to touch;
- APIs not to change;
- migrations not to create;
- dependencies not to add;
- tests not to skip;
- claims not to make.

For high-risk systems, constraints are not bureaucracy. They are part of correctness.

### Repair PRs

Sometimes a PR is open and needs repair. The next work order should not start a new feature if the current PR has failing CI, unresolved review comments, security concerns, documentation drift, or unanswered human questions about evidence.

Repair prompts should be narrower than feature prompts:

```text
Repair PR #123 only.
Do not add new feature behavior.
Read the failing CI logs.
Fix the minimum necessary issue.
Run the failing test locally.
Push to the same branch.
Report the exact failure cause and fix.
```

This keeps the project from accumulating half-valid work.

## IV.3 Verification and Validation Debt

AI coding reduces generation cost. It does not reduce the need for proof. In many cases it increases it, because generated code can be plausible, broad, and fast. OAP handles this by separating evidence collection from evidence presentation: the executor generates raw evidence, the strategic model compresses it, and the human interrogates the compressed result.

![Validation debt.](assets/fig-05-validation-debt.svg)

### What validation debt means

Validation debt is the review, testing, and reasoning burden created when code is generated faster than it can be understood. It is similar to technical debt, but it appears at the process level.

Validation debt accumulates when:

- large diffs are generated quickly;
- tests are shallow;
- the agent changes unrelated files;
- the report overstates certainty;
- reviewers trust style over substance;
- documentation claims more than code proves.

The solution is not to stop using agents. The solution is to constrain the work unit, demand evidence, and keep the human's review surface short enough to support real judgment.

### Tests as evidence

Tests are evidence only when they cover the claim. A unit test proves a narrow behavior. An integration test proves component interaction. An E2E test proves a user path. A browser smoke test proves that at least one visual workflow loads. None proves everything.

OAP reports should name test scope:

```markdown
Tests run:
- `python -m pytest tests/unit/test_policy.py`: 18 passed.
- `python -m pytest tests/integration/test_quota.py`: not run; no TEST_DATABASE_URL configured.
- `ruff check app tests`: passed.
```

This is better than:

```markdown
All checks passed.
```

### Skipped tests are unknown

One of OAP's most important rules is:

> A skipped test is not a passing test. A test that was not run is not evidence.

This rule should appear in the constitution. Agents often try to be helpful by summarizing partial success as success. That behavior must be corrected.

### Meaningful tests

Test quality matters. A test can be meaningless if it:

- asserts implementation details without checking behavior;
- only checks that a function returns something;
- mocks away the risk being tested;
- reproduces the current bug as expected behavior;
- uses generated expected output without independent reasoning.

The strategic layer should ask: if this feature were broken in the dangerous way, would the test fail? The human should be able to ask that same question and receive a concise answer with a pointer to the relevant test.

### Verification-only runs

Sometimes the next task should not be implementation. It should be verification. A verification-only agent prompt should forbid edits:

```text
This is a verification-only run.
Do not create a branch.
Do not edit files.
Do not commit.
Run the specified verification commands.
Report exact results, skipped tests, and blockers.
```

Verification-only runs are useful before releases, after large merges, or when the strategic layer suspects that reports are too narrow.

## IV.4 Security and Safety During Implementation

OAP assumes agents can be powerful enough to cause harm. Security rules must therefore be explicit, repeated, tested, and encoded in the constitution.

### Fail closed

Fail-closed behavior means that uncertain or unsupported states are rejected safely rather than passed through optimistically.

Examples:

- unknown pricing rejects a cost-limited request;
- unknown route capability rejects forwarding;
- non-owned resource IDs return not found before provider access;
- bad host keys stop an SSH workflow before credential entry;
- missing test database blocks integration claims;
- unsupported provider features return explicit unsupported errors.

Fail closed is a design posture. It is especially important when an execution agent might otherwise "make it work" by relaxing validation.

### Secrets

The agent runtime should not contain production secrets. The repository should not contain real provider keys. Logs should not contain credentials. Documentation should use placeholders.

The constitution should say:

```markdown
## Secrets
- Never commit real provider keys.
- Never store plaintext gateway keys.
- Never print tokens in test output.
- Never paste production secrets into prompts.
- Use fake placeholders in docs and tests.
- If a secret appears in output, stop and report.
```

For coding-agent systems, this is not optional. Prompt history, tool logs, shell history, test output, telemetry, and PR comments can all become accidental disclosure channels.

### Approval gates

Human approval is required for:

- production deployment;
- merge to protected branches;
- destructive data operations;
- credential rotation;
- public release claims;
- adding risky dependencies;
- widening network access;
- changing security posture.

Codex documents sandbox and approval layers as separate controls: sandbox mode determines what the agent can technically do; approval policy determines when it must ask [@codex-security]. OAP uses the same separation concept at the process level. The runtime boundary controls what can happen. The human gate controls what is accepted.

### Safety scans

For security-sensitive projects, execution reports should include scans such as:

```bash
rg "api_key|Authorization|Bearer|password|secret|token" app tests docs -n
git diff --check
python -m pytest tests/unit
ruff check app tests
```

The exact commands depend on the stack. The point is that safety checks should be named and repeatable.

### Avoiding unsafe helpfulness

Agents may try to:

- disable a failing test;
- loosen validation;
- add a broad catch-all;
- mock the wrong boundary;
- skip a hard integration path;
- use real services because mocks are inconvenient;
- make documentation sound more complete than reality.

The strategic layer must punish these shortcuts. In OAP, "working" is not enough. The change must work inside the project's rules.

## IV.5 Documentation, Handoffs, and Memory

AI workflows need durable memory. Chat transcripts are useful, but they are not enough. They become long, stale, unavailable, or hard to search. OAP treats documentation as operational memory for humans and agents. Documentation should also reduce reading load: short summaries should point to deeper details instead of forcing every future reader to reconstruct the project from chat.

### Documentation types

A mature OAP project often needs:

- README;
- quickstart;
- architecture overview;
- security model;
- compatibility matrix;
- deployment guide;
- runbooks;
- testing guide;
- release notes;
- review archive;
- remediation matrix;
- handoff documents.

Not every project needs all of these. But every serious project needs enough documentation for a new human, strategic model, or execution agent to continue safely.

### Handoffs

Handoffs solve context transfer. They should be written for the next strategic session, not for the end user. A good handoff should be short enough to reload context quickly while still pointing to durable evidence. It includes:

- current repository truth;
- recent merged PRs;
- open PRs;
- known blockers;
- implemented scope;
- missing scope;
- safety rules;
- next recommended task;
- tasks explicitly not recommended.

Handoffs should never be treated as authoritative over the live repository. They are snapshots. The first step after reading a handoff is verification.

### Documentation as contract

Documentation must track behavior. If an endpoint is implemented, the compatibility matrix changes. If a feature is deliberately unsupported, docs should say so. If a release is beta, docs should not imply production certification.

This is part of OAP's honesty discipline. Generated code can create the appearance of maturity quickly. Documentation must counterbalance that by stating actual scope.

### Runbooks

Runbooks are procedures for failure and operations:

- key rotation;
- compromised key response;
- database backup and restore;
- Redis outage;
- email ambiguity;
- admin lockout;
- deployment rollback;
- metrics alert response.

Agents can draft runbooks, but humans must ensure they do not invent commands or promise unsupported recovery paths.

# Part V: Review, Audit, and Release

## V.1 Review and Audit

Review is where OAP either becomes engineering or collapses into automation theater. The agent's output must be reviewed, but review does not mean the human must manually read every generated line as the default path. Mature OAP reviews through compressed evidence first and targeted inspection second.

### Strategic review brief

Every PR should produce a short strategic review brief for the human:

```markdown
## Decision Brief
Recommendation: merge / repair / reject / defer

Goal match:
- ...

Evidence:
- Test command and result:
- CI result:
- Key files changed:
- Documentation changed:

Risks:
- ...

Human decision needed:
- ...
```

The brief should be short enough to read quickly. It should not hide evidence. It should point to it. The human can then ask for expansion:

- show the exact test;
- show the changed invariant;
- explain the security implication;
- compare the PR against the original goal;
- identify what was not tested;
- identify what would make you reject this PR.

### Human review as management discipline

Human review should evaluate:

- diff scope;
- behavior;
- tests;
- security;
- documentation;
- migration safety;
- release claims;
- operator impact.

The reviewer should not only ask "does this compile?" The reviewer should ask "does this preserve the system's meaning?" The human can make that judgment from a decision brief, strategic questioning, targeted file inspection, and external audit when risk demands it. The human does not need to make line-by-line review the routine bottleneck.

### AI-assisted review

AI can help review, and in OAP the strategic AI is the default first reviewer. It should not be the final accountable reviewer. Useful AI review prompts include:

```text
Review this diff for:
- security regressions;
- missing tests;
- documentation drift;
- violations of AGENTS.md.

Prioritize concrete findings over praise.
```

AI review is particularly useful for:

- scanning for inconsistency;
- checking docs against behavior;
- finding missing negative tests;
- comparing PR claims with diff;
- preparing human review questions;
- compressing large diffs into short decision briefs.

Codex's GitHub integration is one public example of this direction: review behavior can be customized through repository instructions, and review prompts can focus the agent on concerns such as security regressions [@codex-github].

### Cross-model audit

One useful OAP pattern is to build with one model family and audit with another. This does not make the audit objective, but it reduces one kind of circularity. A model that did not participate in implementation may notice different issues, especially around overclaiming, missing tests, security boundaries, accounting invariants, and documentation drift.

Cross-model audit should not be treated as a decorative final review. In a mature OAP project it is a cadence: build, audit, remediate, verify, and audit again when the risk profile changes. The public SLAIF API Gateway archive shows this pattern clearly. Reviews were preserved as project artifacts, findings were tracked in a remediation matrix, and later work connected findings to PRs and verification evidence [@slaif-reviews-archive; @slaif-remediation-matrix].

Cross-model audit works best when the auditor sees:

- repository URL or snapshot;
- project goals;
- known limitations;
- test results;
- specific questions;
- no pressure to praise.

The human can use cross-model audit as management leverage: not to read more, but to ask better questions and decide where to inspect.

### Audit cadence

Cross-model audit should usually be invoked at these points:

- **Architecture audit.** After the constitution, initial scaffold, and first executable skeleton exist, but before many features accumulate.
- **Boundary audit.** After authentication, secrets, billing, quota, streaming, deployment, or other high-risk boundaries are introduced.
- **Maturity audit.** Before changing project language from prototype to beta, release candidate, or production-ready.
- **Follow-up audit.** After remediation PRs land, especially when the original finding touched security, accounting, or release claims.

Extra audit rounds are justified when:

- a broad refactor changes architecture or transaction boundaries;
- a feature introduces new trust boundaries or credential flow;
- tests pass but the strategic model cannot explain the proof clearly;
- documentation starts to claim more than the implementation supports;
- CI failures repeat in a pattern that suggests fragile design;
- a release decision depends on an assumption that has not been challenged;
- the human feels tempted to accept a result mainly because the agent sounds confident.

The SLAIF API Gateway Review 6.0 / RC1 audit is a good example of why this matters. The review classified the project as credible RC-beta for the implemented scope, but it also identified a concrete remaining hard-quota risk: input-token and cost pre-reservation could underestimate non-message Chat Completions fields such as `tools` and `response_format` schemas [@slaif-review6]. That finding became bounded remediation rather than a vague concern. The remediation matrix then tracked the fix for non-message input estimation, follow-up invariant tests, and production runbooks as separate work items with verification evidence [@slaif-remediation-matrix].

### Audit loop mechanics

An audit round should produce artifacts that the project can use:

1. Freeze the current scope: branch, commit, release candidate, or repository URL.
2. State implemented scope and known exclusions.
3. Ask the auditor for findings, not encouragement.
4. Separate current-scope defects from future feature requests.
5. Add accepted findings to a remediation matrix.
6. Convert each current-scope finding into one or more PR-sized work orders.
7. Close findings only with tests, docs, code links, or release-note changes.
8. Preserve honest language: an audit is not certification unless it really is.

The important management move is step 4. External models often complain about features that were never intended for the current release. OAP does not blindly implement every audit comment. The human, with help from the strategic AI, classifies findings: real defect, missing test, documentation drift, future work, or rejected recommendation. The execution agent then receives only bounded work orders.

### External audit

For serious systems, external audit should be treated as a project artifact. Findings should be archived, mapped to remediation tasks, and closed with evidence. The point is not to collect flattering scores. The point is to create a review trail.

### Review comments as work orders

A review comment can become the next execution task. The strategic layer should convert it into a precise repair prompt:

```text
Address only the unresolved review comment about missing ownership checks.
Do not refactor unrelated code.
Add a regression test proving non-owned IDs do not reach the provider adapter.
Push to the existing PR branch.
Report changed files and tests.
```

## V.2 Release Readiness

Feature completion is not release readiness. A feature can exist and still be unsafe to ship. In OAP, release readiness is a management decision backed by technical evidence. The human owns the release criteria and asks the strategic AI to compress evidence into a decision-ready form.

![Release readiness requires more than implemented code.](assets/fig-07-release-readiness.svg)

### Completeness levels

OAP should distinguish:

- prototype complete;
- implemented for a narrow path;
- tested for expected path;
- tested for negative paths;
- documented;
- operationally recoverable;
- reviewed;
- release candidate;
- production ready.

These are different claims. A manual, README, or release note should not blur them.

### Readiness scoring

Readiness scoring can help if it is honest. Example:

| Dimension | Question |
|---|---|
| Functional completeness | Is the intended behavior implemented? |
| Architecture quality | Does it fit the system design? |
| Security posture | Are known risks controlled? |
| Test coverage | Do tests prove core and negative paths? |
| Documentation | Can users and operators understand scope? |
| Operational readiness | Can it be deployed, monitored, and recovered? |
| Release honesty | Are limitations stated clearly? |

Scores should not replace evidence. They summarize evidence.

### Release decision brief

Before a release decision, the strategic AI should prepare a short brief:

```markdown
## Release Decision Brief
Recommendation: release / do not release / release with limitations

Goal:
- ...

Release criteria:
- ...

Evidence:
- CI:
- Tests:
- Security:
- Documentation:
- Rollback:

Known limitations:
- ...

Decision required:
- ...
```

This brief lets the human act like a disciplined manager: short text first, direct questions second, targeted inspection third. The human should not have to reconstruct release readiness from raw PRs, logs, and scattered chat history.

### Release gates

Before release, require:

- explicit release goal;
- explicit release criteria;
- clean working tree;
- all release-relevant CI green;
- no required tests skipped without explicit blocker classification;
- docs aligned with implemented scope;
- known limitations documented;
- security scans complete;
- migration and rollback notes ready;
- final human release decision.

### The danger of apparent completeness

Agentic coding can make a project look complete faster than it becomes coherent. It can add files, tests, docs, and UI elements rapidly. The human release manager must ask whether the pieces form a system.

Release readiness is the discipline of saying "not yet" when the diff looks impressive but the evidence is weak.

# Part VI: Case Studies and Applications

## VI.1 Case Study: SLAIF API Gateway

This chapter uses a public project as an illustrative case: an OpenAI-compatible API gateway for issuing limited gateway keys while keeping upstream provider credentials protected [@slaif-repo]. The point is not the specific domain. The point is the workflow.

### Problem shape

The product problem was not "make an app." It was a serious system:

- OpenAI-compatible client behavior;
- gateway-issued keys;
- quota enforcement;
- provider routing;
- usage accounting;
- admin operations;
- secure key handling;
- deployment and operator documentation.

This kind of system is a good OAP candidate because it has clear invariants, many mechanical implementation slices, and high security risk. It is also a good example of why the human must move up the ladder: the important human work is not typing CRUD handlers, but managing invariants, release claims, security posture, and proof.

### Architecture discovery

The first management act was not asking an agent to generate endpoints. It was asking the strategic model what kind of system the domain problem required and which technical ingredients were appropriate. The human supplied the domain need: many users need practical LLM API access, but the institution must protect upstream provider credentials, enforce spending limits, account for usage, and operate the system safely. The strategic model translated that into an architecture: OpenAI-compatible gateway, server-side provider keys, gateway-issued keys, PostgreSQL-backed hard quota/accounting, Redis as optional operational throttling, admin workflows, background jobs, tests, and deployment documentation.

This is important because a domain expert can know the problem deeply without knowing the current best software stack. OAP uses the strategic model to bridge that gap. The human remains manager and domain authority; the strategic model proposes architecture and tradeoffs; the execution agent later implements bounded slices.

The same pattern appears in the DHCP/IPAM appliance example. The domain problem was not "make a DHCP web UI." It was "manage DHCP/IPAM/DNS state safely on replaceable Raspberry Pi edge appliances." Strategic discovery changed the software shape: server-side source of truth, outbound edge connections, signed desired-state artifacts, a minimal local apply helper, `dnsmasq` validation, rollback, audit logs, and a public view that must be a sanitized snapshot rather than hidden admin controls. That architecture is a management output before it is an implementation task.

### Constitution first

The early artifact was not code. It was a detailed implementation brief and governing instruction file produced from the strategic discovery phase. This allowed the execution agent to work inside constraints rather than discovering the architecture through improvisation.

The constitution encoded:

- stack choices;
- security rules;
- testing expectations;
- PR workflow;
- documentation requirements;
- no real provider keys;
- no plaintext gateway key storage;
- no overclaiming production readiness.

### PR sequence

The project advanced through many small PRs. Each PR implemented or hardened a slice: schema, key service, quota reservation, provider routing, admin UI, documentation, tests, runbooks, feature families, release verification.

This matters because agentic work becomes reviewable when it is sliced. A large autonomous implementation would have been much harder to trust. Slicing also protected context: the execution agent could focus on one task, while the strategic model and documentation preserved the larger story.

### Control plane in practice

The human-facing work was not continuous direct conversation with the execution agent. The useful human questions were management questions:

- Is the gateway still fail-closed?
- Which tests prove quota enforcement?
- What secrets could leak?
- What is implemented versus merely documented?
- What remains before release?

Those questions belong to the strategic layer. The strategic model turns them into work orders, review briefs, remediation lists, and release-readiness summaries. The execution agent turns work orders into branches, tests, and PRs.

### Audit and remediation

External model review was used to assess architecture, security posture, test coverage, documentation, and production readiness. Findings were turned into remediation work rather than treated as praise. The public review archive and remediation matrix matter because they make the audit loop inspectable rather than anecdotal [@slaif-reviews-archive; @slaif-remediation-matrix].

The RC1 audit did not merely say the project was good. It made a management judgment: the implemented scope was credible as RC-beta, but not production certification, compliance attestation, or penetration testing. It also identified concrete remaining work, including non-message Chat Completions input/cost estimation, quota/accounting/reconciliation invariant tests, and production runbooks [@slaif-review6]. Those findings became bounded work:

- the non-message input estimation issue was fixed as a focused policy, pricing, quota, and provider-forwarding remediation;
- invariant tests were added for quota, accounting, reconciliation, idempotency, and safe ledger/audit metadata;
- operator runbooks were added for key rotation, leaked key response, HMAC and one-time-secret handling, backup/restore, reconciliation, Redis outage, PostgreSQL readiness, metrics, deployment troubleshooting, and RC-beta upgrades.

This demonstrates a central OAP claim: the human does not need to personally implement every fix, but the human must manage the quality loop. The human decides which audit findings are current-scope defects, which are future work, which require tests, and which release claims are allowed. The strategic AI converts that decision into precise work orders. The execution agent performs the implementation and verification. The repository preserves the evidence.

This is the OAP review loop:

1. Build with execution agent.
2. Review with strategic model.
3. Audit with external model or reviewer.
4. Ask human management questions about goal, risk, and release criteria.
5. Convert findings into PR-sized work.
6. Verify and document closure.

### Lessons

The case illustrates several general lessons:

- A coding agent can perform large amounts of implementation labor.
- The human does not disappear; the human becomes more managerial and more important at gates.
- Domain knowledge remains decisive: the human must understand why quota, provider-key isolation, user-key issuance, accounting, and workshop operations matter.
- The strategic model should compress evidence into short decision material.
- The execution environment should let the agent do setup work without recruiting the human.
- Documentation and runbooks are not afterthoughts.
- Tests become the language of trust.
- Release honesty prevents agentic velocity from turning into false maturity.

## VI.2 Applying OAP to Other Projects

OAP is not limited to API gateways. The method generalizes by pattern: identify the domain goal, write the constitution, slice work into PRs, keep the execution runtime disposable, preserve repository truth, and review through evidence. Public repositories can then be used as examples of use cases, not as proof that every project is finished or production-certified.

The examples below should be read in two layers:

1. the **general use case**, which is reusable guidance;
2. the **visible repository example**, where a public repository exists and illustrates the pattern.

Private or internal projects can still inform the pattern, but they should not be presented as public examples. If the repository is not visible, describe the use case without pretending there is a public URL.

### Concept demonstrations across examples

**Human as manager and domain expert.** Demonstrated in the API gateway, SLAIF Connect, and DHCP/IPAM appliance examples. The human supplied the product invariants: protect provider keys, do not collect SSH credentials, do not expose inbound Pi management, and keep release claims honest.

**Strategic discovery and tool selection.** Demonstrated most clearly in the API gateway and DHCP/IPAM examples. The human asked what kind of system was needed and which tools fit the domain; the strategic model translated that into gateway architecture, quota/accounting choices, server/control-plane boundaries, edge-agent boundaries, and safe first milestones.

**Constitution-first execution.** Demonstrated in the API gateway and DHCP/IPAM scaffold work. The agent received architecture, non-goals, security rules, tests, and report format before broad implementation.

**Execution agent as implementation labor.** Demonstrated by public PR sequences and branch names across the visible repositories. The executor handled repository edits, tests, docs, and PR mechanics while the human stayed focused on decisions.

**PR as the unit of work.** Demonstrated in the API gateway, SLAIF Connect, and DHCP/IPAM appliance examples. Work stayed reviewable, revertible, and attributable. Later audit findings could become narrow PRs rather than vague repair campaigns.

**Remote repository as project truth.** Demonstrated through public GitHub repositories and review archives. Durable truth lived in branches, PRs, docs, CI, review files, and remediation matrices rather than in a local agent VM.

**Cross-model audit and remediation.** Demonstrated in the SLAIF API Gateway review archive. External critique found release-relevant issues that were converted into remediation work with verification evidence.

**Release honesty.** Demonstrated by the SLAIF API Gateway RC-beta language. The project could claim RC-beta readiness for implemented scope without pretending to be production-certified.

**Validation debt management.** Demonstrated through tests, compatibility matrices, runbooks, and remediation matrices. Fast implementation was balanced by stronger proof, operator documentation, and explicit known limitations.

### Writing new software

General concept: OAP works well for greenfield software when the human can define a strong product goal and begin with strategic discovery. The first practical artifact may be a constitution, but the first intellectual artifact is the architecture discussion: what kind of system is this, which tools fit, where are the trust boundaries, and what should the first release not attempt?

The key management move is to avoid the "make me an app" prompt. The human should instead define:

- what the product is for;
- what kind of product category or architecture is appropriate;
- which tools and frameworks are plausible;
- what must never happen;
- what the first release is allowed to claim;
- how evidence will be checked;
- which pieces are intentionally out of scope.

Visible examples:

- **SLAIF API Gateway**: a public OpenAI-compatible gateway for institutional LLM access, quota enforcement, provider routing, usage accounting, and operator workflows [@slaif-repo]. It demonstrates greenfield OAP at serious-product scale: specification first, many PR-sized implementation slices, strong security invariants, broad tests, documentation, release notes, and external review.
- **Managed DHCP/IPAM Edge Appliance**: a public early-stage DHCP/IPAM edge-management repository [@dhcp-web-interface-repo]. This is not a finished-product example. It demonstrates how OAP should begin a risky infrastructure product: scaffold and trust boundaries first, not a rushed web UI that can mutate network infrastructure.

How the concepts helped:

- The human manager defined domain hazards that a generic coder might miss.
- The strategic model translated those hazards into architecture and tool choices.
- The constitution prevented unsafe shortcuts from becoming architecture.
- The first PRs created reviewable foundations rather than a large unreviewable implementation dump.
- The execution agent could work autonomously because the work was bounded.

### Taking over existing software

General concept: OAP is useful when an existing codebase, fork, research tool, or academic project has value but lacks professional structure. The method should not begin by rewriting everything. It should begin by asking what must be preserved, what is unsafe, what is accidental complexity, and what evidence proves a safe transition.

The strategic AI is especially useful here because it can compare the old system against the desired system:

- what is real product logic;
- what is prototype scaffolding;
- what is copied upstream code;
- what should become a dependency rather than owned code;
- what tests are needed before replacing behavior.

Visible example:

- **SLAIF Connect**: a public browser-based SSH and remote-compute access project [@slaif-connect-repo]. The project began around a fork/prototype of a well-known browser SSH stack, but the OAP analysis pushed it toward a cleaner architecture: a non-fork extension, pinned upstream `libapps` as a build-time dependency, a WebSocket-to-TCP relay, extension-side host policy, and the rule that the SLAIF service must not receive SSH credentials.

How the concepts helped:

- The human domain manager supplied the real invariant: SLAIF may orchestrate HPC work, but must not become the SSH credential holder.
- The strategic layer separated useful prototype knowledge from wrong long-term ownership.
- The execution plan avoided an uncontrolled fork by turning upstream code into a pinned dependency and SLAIF behavior into project-owned extension, relay, policy, and tests.

### Rewriting wrong-shaped or failed software

General concept: sometimes the old system is not merely incomplete; it encodes the wrong shape. In that case OAP should not ask the agent to patch indefinitely. It should freeze the old implementation as a reference, extract the domain invariants, write a new constitution, and rebuild in small PRs.

This is different from a casual rewrite. A rewrite under OAP needs:

- a clear reason the old architecture cannot carry the next stage;
- a list of behavior and domain knowledge to preserve;
- explicit non-goals for the new first milestone;
- testable migration checkpoints;
- a public or internal audit trail explaining the choice.

Visible example:

- **SLAIF Connect** again illustrates this pattern [@slaif-connect-repo]. The wrong-shaped path was maintaining a divergent general-purpose Secure Shell fork as the product. The OAP path preserved the real domain goal while changing the architecture: browser-side SSH remains, credentials stay local to the user and HPC server, the relay forwards encrypted bytes, and project-specific policy lives outside upstream source.

How the concepts helped:

- The human did not ask the agent to "finish the fork." The human managed the goal and accepted a strategic architectural correction.
- The strategic AI turned a messy fork question into a migration plan.
- The executor could then build the new path incrementally through scaffold, vendoring, relay tests, browser validation, signed policy, and pilot-readiness work.

### Hardening an existing serious system

General concept: OAP is not only for creation. It is also strong for hardening a system that already works but needs release discipline. At this stage, the human's management role becomes more important, not less. The question shifts from "can the agent build it?" to "what evidence permits us to claim readiness?"

Visible example:

- **SLAIF API Gateway** demonstrates audit-driven hardening [@slaif-repo]. The Review 6.0 / RC1 audit identified a real remaining quota/cost-estimation issue and recommended invariant tests and production runbooks [@slaif-review6]. The remediation matrix then tracked the resulting fixes and their verification evidence [@slaif-remediation-matrix].

How the concepts helped:

- Cross-model audit challenged the project at the right level: architecture, accounting, security, tests, and release language.
- The human classified audit findings into current-scope remediation versus future work.
- The strategic AI converted findings into PR-sized prompts.
- The execution agent fixed, tested, documented, and reported.
- Release language stayed honest: RC-beta for implemented scope, not production certification.

### Infrastructure management products

General concept: infrastructure management products need extra caution because the agent can quickly build a dashboard that looks useful while hiding dangerous control channels. OAP should force the architecture to separate desired state, validation, privileged local apply, audit logs, and rollback before automation reaches real infrastructure.

Visible example:

- **Managed DHCP/IPAM Edge Appliance** [@dhcp-web-interface-repo] demonstrates this conservative start, not a completed product. The public README describes a server-side control plane, outbound edge appliance communication, signed desired-state artifacts, a local privileged apply helper, and the rule that the Pi must not expose inbound management or run a root network-facing daemon.

How the concepts helped:

- The domain manager defined the infrastructure hazard before implementation.
- The agent was asked for scaffold and backend foundations first, not privileged deployment logic or production DHCP automation.
- The architecture made the local apply helper tiny, auditable, and separated from network communication.
- Public no-login views were treated as sanitized published snapshots, not hidden-button versions of admin APIs.

### Existing academic or domain software

General concept: academic and domain software often has useful algorithms or workflows but weak packaging, tests, CI, privacy defaults, documentation, release process, and operator experience. OAP can professionalize such software through staged work:

- write or revise `AGENTS.md`;
- inventory existing files and risks;
- fix privacy and credential defaults first;
- add focused tests before broad refactors;
- add CI and packaging;
- preserve scientific or domain semantics;
- move toward release checklists and reproducible workflows.

If the repository is private, do not list it as a public example. The pattern remains valid, but public readers should see it as guidance rather than as a named visible case study.

### When OAP is too heavy

OAP may be too heavy for:

- one-off scripts;
- throwaway prototypes;
- experiments with no long-term value;
- personal utilities with low risk;
- tasks where direct human editing is faster than defining the process.

The method has overhead. Use it when the overhead buys safety, continuity, or scale.

### When OAP is especially useful

OAP is especially useful when:

- the project has security constraints;
- the system has multiple components;
- documentation matters;
- the work spans many PRs;
- tests can prove behavior;
- a domain expert can judge intent but cannot implement everything by hand;
- the domain expert knows the problem but not the best current architecture or toolchain;
- users and domain experts are closer to the problem than available software engineers;
- release readiness matters.

# Part VII: Discussion and Doctrine

## VII.1 Failure Modes

OAP is designed around failure modes that appear repeatedly in AI-assisted software work.

### Hallucinated APIs and dependencies

Models can invent library methods, configuration flags, packages, or endpoint shapes. Package hallucination has been studied as a supply-chain risk because nonexistent packages can become attack targets if attackers publish them later [@package-hallucination].

Mitigation:

- verify official docs for unstable APIs;
- run code;
- pin dependencies;
- avoid adding dependencies casually;
- test real import paths.

### Shallow tests

Agents can generate tests that assert the code they just wrote rather than the behavior that matters.

Mitigation:

- require negative tests;
- require tests that fail before the fix when practical;
- review mocks;
- ask whether the test protects the risk.

### Context drift

Long sessions drift. The model remembers old PR states, stale architecture, or expired decisions. OAP splits this risk: the strategic model should preserve long context, while the execution agent should not carry assumptions beyond one task.

Mitigation:

- verify current repository state;
- write handoffs;
- keep constitution current;
- prefer live source over chat memory.
- compact or reset the execution agent between PR-sized tasks.

### Weak strategic model

OAP fails if the strategic layer is too weak for the role. A cheap or short-context model may summarize confidently while missing architectural drift, security implications, or unresolved human goals.

Mitigation:

- use the strongest practical model for strategy;
- keep strategic context clean and long-lived;
- ask for explicit evidence mapping;
- use cross-model audit for high-risk decisions;
- write handoffs before context becomes brittle.

### Control inversion

Control inversion happens when the execution agent starts piloting the human. Symptoms include repeated requests for the human to install packages, run commands, paste logs, repair environments, or decide low-level implementation details that belong inside the execution VM.

Mitigation:

- give the agent enough privilege inside a hardened VM;
- keep production secrets and irreplaceable state out of that VM;
- require the agent to document local setup;
- rebuild disposable environments instead of manually nursing them;
- route human decisions through the strategic model.

### Excessive human reading burden

OAP fails if the human must read large diffs, long logs, and verbose reports for every small decision. That recreates the labor bottleneck at a different layer.

Mitigation:

- require short decision briefs;
- ask the strategic AI for conclusion, evidence, risk, and decision;
- drill down only when risk or uncertainty demands it;
- keep PRs small enough for strategic inspection;
- forbid vague reports that force reconstruction.

### Scope creep

Agents may implement neighboring features because they look related.

Mitigation:

- explicit non-goals;
- PR-sized tasks;
- reject broad diffs;
- repair scope before merge.

### Overclaiming

Agents and humans may overstate readiness. "Implemented" becomes "supported." "Focused tests passed" becomes "fully tested." "RC" becomes "production ready."

Mitigation:

- standard report vocabulary;
- release-readiness checklist;
- documentation review;
- external audit.

### Credential leakage

Agents can expose secrets through prompts, logs, commits, screenshots, or telemetry.

Mitigation:

- no production secrets in agent runtime;
- secret scans;
- fake placeholders;
- redacted telemetry;
- no raw prompt or payload storage unless deliberately designed.

### Human complacency

The final failure mode is human complacency. OAP fails if the human stops judging. The process can make it easy to feel productive while accepting too much. Moving into a management role does not mean becoming passive. It means running a stricter discipline over goals, release criteria, evidence, and risk.

Mitigation:

- slow down at gates;
- demand short evidence briefs;
- inspect deeper when evidence is weak;
- ask for external review;
- treat every merge as a human decision.

## VII.2 Practical OAP Doctrine

This chapter condenses the manual into doctrine: rules that can guide real projects.

### Core principles

1. **Human moves up the ladder.** The human is no longer primarily the coder; the human manages goals, criteria, risk, and release.
2. **Domain expertise can lead.** The best human lead may be the person who understands the domain, not the person who writes code.
3. **Start with strategic discovery.** Before coding, ask what kind of system is needed, which tools fit, and where the boundaries are.
4. **Human owns intent.** Never outsource product meaning.
5. **Human owns risk.** The model cannot accept liability.
6. **Human owns release.** The agent does not decide readiness.
7. **Human works from short decision material.** Strategic AI should compress detail into evidence-linked briefs.
8. **Strategic AI is the control plane.** Use the strongest practical long-context model for architecture discovery, technology selection, memory, critique, domain translation, work orders, and evidence.
9. **Execution agent is disposable labor.** Its context should last one PR-sized task.
10. **Strategy and execution are separate.** Planning and repository mutation should be different roles.
11. **The constitution governs.** Durable rules beat repeated reminders.
12. **Autonomy lives inside a rebuildable boundary.** High privilege is acceptable only in a hardened disposable runtime.
13. **Remote repository is truth.** The VM is disposable; branches, PRs, CI, docs, and handoffs are durable.
14. **The PR is the unit.** Work should be reviewable, revertible, and evidenced.
15. **Non-goals are safety tools.** Say what not to do.
16. **Tests are evidence, not ritual.** Match tests to claims.
17. **Skipped is not passed.** Unknown remains unknown.
18. **Documentation is part of the artifact.** Behavior and claims must align.
19. **Audit is normal.** External critique is not a failure.
20. **Release language must be honest.** Beta means beta.
21. **Velocity must not outrun judgment.** Faster coding increases validation responsibility.
22. **Never let the agent pilot the human.** If the human is doing routine setup for the agent, redesign the runtime.

### Minimum viable OAP

For a small serious project:

- hold a strategic discovery conversation;
- decide the product shape, stack, trust boundaries, and first release scope;
- create `AGENTS.md`;
- use a capable strategic model as the human-facing control plane;
- use a dedicated branch per task;
- write work orders with goal, non-goals, tests, report format;
- run focused tests;
- require a PR;
- produce a short decision brief before merge;
- human interrogates evidence before merge;
- keep a simple handoff file.

### Mature OAP

For a larger project:

- documented strategic discovery and architecture rationale;
- layered constitutions;
- dedicated execution VM;
- high-autonomy mode inside hardened rebuildable runtime;
- passwordless local setup privileges where safe;
- no production secrets or irreplaceable data in the VM;
- premium long-context strategic model;
- per-PR executor context reset or compaction;
- protected branches;
- CI gates;
- security scans;
- external model review;
- runbooks;
- release-readiness scoring;
- release decision briefs;
- final verification harness;
- archived audit findings.

### Team adoption

Teams should start with low-risk tasks:

- documentation improvements;
- test additions;
- small bug fixes;
- refactors with strong tests;
- internal tooling.

Then expand toward feature work once the team trusts:

- constitution quality;
- prompt templates;
- runtime isolation;
- strategic review discipline;
- decision-brief quality;
- CI coverage.

The goal is not to maximize autonomy immediately. The goal is to increase autonomy only where evidence and boundaries support it.

## VII.3 Conclusions

OAP changes where human attention belongs. The human no longer needs to be the person who installs every dependency, writes every boilerplate file, and follows every traceback. The human becomes the person who defines the goal, asks the strategic questions, decides acceptable risk, and demands evidence.

This is not a reduction in responsibility. It is a relocation of responsibility. The human is still accountable for what is released. The difference is that the human governs through architecture, constitution, work orders, tests, audits, and release decisions rather than through continuous low-level coding.

The durable lesson is simple:

```text
Strategic model: translate intent into architecture and evidence questions.
Execution agent: perform bounded implementation labor inside a disposable runtime.
Human manager: own goal, risk, release, and domain correctness.
Repository: preserve truth.
```

When this loop works, agentic programming becomes less like chatting with a code generator and more like managing a fast, disciplined implementation shop. When it fails, it usually fails by collapsing the hierarchy: the execution agent pilots the human, the strategic model rubber-stamps vague reports, or the repository stops being the source of truth.

The method is therefore not "trust the agent." It is "design the control system so the agent can be useful without being trusted as the final authority."

# Appendices

## Appendix A: Example `AGENTS.md` / `CLAUDE.md` structure

```markdown
# AGENTS.md or CLAUDE.md

## Mission
This repository implements <product>. Preserve <core promise>.

## Discovery Summary
- Domain problem:
- Product shape:
- Chosen architecture:
- Stack and tool rationale:
- Alternatives rejected:
- First release scope:
- Explicit non-goals:

## Domain
- Domain expert:
- Domain vocabulary:
- Domain workflows:
- Domain failure modes:

## Architecture
- Backend:
- Frontend:
- Database:
- Background jobs:
- External services:

## Non-negotiable rules
- ...

## Security
- Never commit secrets.
- Never log raw credentials.
- Use fake placeholders in docs and tests.

## Workflow
- Create a branch from current main.
- Commit only related files.
- Open a pull request.
- Do not merge your own PR.

## Local setup
- Install missing local tools only inside the approved execution environment.
- Document setup commands that should become durable project knowledge.
- Do not ask the human to perform routine setup unless a safety boundary blocks it.

## Tests
- Unit:
- Integration:
- E2E:
- Lint:

## Documentation
- Update docs when behavior changes.
- Do not claim production readiness without release approval.

## Final report
- Branch:
- Commit:
- PR:
- Tests:
- Local tools or dependencies installed:
- Risks:
```

## Appendix B: Coding-agent prompt template

```text
Read AGENTS.md and CLAUDE.md first if both exist.

Strategic discovery baseline:
- Product category:
- Architecture decision:
- Stack/tool choices:
- Trust boundaries:
- Alternatives rejected:
- First release scope:

Current state:
- ...

Goal:
- ...

Domain behavior:
- ...

Acceptance criteria:
- ...

Non-goals:
- ...

Files to inspect:
- ...

Implementation requirements:
- ...

Local setup:
- You may install required local tools or dependencies inside the execution VM.
- Document anything installed or configured.
- Do not ask the human to run setup commands unless blocked by an explicit safety boundary.

Tests:
- ...

Documentation:
- ...

Workflow:
- Start from current main.
- Create a feature branch.
- Commit only related files.
- Push and open a PR.
- Do not merge.

Report:
- Branch, commit, PR URL.
- Summary.
- Domain behavior implemented.
- Tests run with exact results.
- Files changed.
- Local tools or dependencies installed.
- Docs changed.
- Skipped tests or blockers.
- Safety confirmations.
```

## Appendix C: Verification-only prompt template

```text
This is verification only.

Do not edit files.
Do not create a branch.
Do not commit.
Do not open a PR.

Verify current main with these commands:
- ...

Report:
- Commit SHA tested.
- Commands run.
- Exact pass/fail/skip results.
- Environment blockers.
- Whether RESULT is OK, FAIL, or ENVIRONMENT_BLOCKED.
```

## Appendix D: PR readiness checklist

- [ ] Scope matches prompt.
- [ ] No unrelated files changed.
- [ ] Tests named and run.
- [ ] Skipped tests reported as skipped.
- [ ] Docs updated or explicitly not needed.
- [ ] No secrets committed.
- [ ] No production systems touched.
- [ ] CI green or failures explained.
- [ ] Known limitations documented.
- [ ] Local setup changes documented.
- [ ] Strategic decision brief prepared.
- [ ] Human release or merge decision maker understands goal match, evidence, and risk.

## Appendix E: Release readiness checklist

- [ ] Release goal explicit.
- [ ] Release criteria explicit.
- [ ] Feature scope complete.
- [ ] Negative paths tested.
- [ ] Integration/E2E coverage adequate.
- [ ] Documentation aligned.
- [ ] Runbooks updated.
- [ ] Security review complete.
- [ ] Known limitations public.
- [ ] Rollback path known.
- [ ] Final verification completed.
- [ ] Strategic release brief prepared.
- [ ] Human release authority accepts evidence.

## Appendix F: Operational Preflight Commands

These commands are starting points. Adjust names, ports, CPU, memory, and disk sizes to the local machine and project.

### Linux guest user

```bash
sudo adduser agent
sudo usermod -aG sudo agent
sudo visudo -f /etc/sudoers.d/90-agent-nopasswd
```

Add:

```sudoers
agent ALL=(ALL) NOPASSWD:ALL
```

Verify:

```bash
sudo chmod 0440 /etc/sudoers.d/90-agent-nopasswd
sudo visudo -c
su - agent
sudo -n true && echo "passwordless sudo works"
```

### Guest-local Codex state

```bash
mkdir -p "$HOME/.codex-agent"
export CODEX_HOME="$HOME/.codex-agent"
```

### WSL2 Ubuntu install

```powershell
wsl --install -d Ubuntu
wsl -l -v
wsl --set-version Ubuntu 2
```

Inside Ubuntu:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y build-essential git curl wget unzip zip ca-certificates openssh-server
mkdir -p ~/work
```

### WSL2 hardening starting point

`/etc/wsl.conf`:

```ini
[automount]
enabled=false

[interop]
enabled=false
appendWindowsPath=false

[user]
default=agent
```

Restart WSL:

```powershell
wsl --shutdown
```

### Linux OpenSSH inside a guest

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh || sudo service ssh start
mkdir -p ~/.ssh
chmod 700 ~/.ssh
```

### Windows Sandbox OpenSSH bootstrap

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic

if (!(Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue)) {
  New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" `
    -DisplayName "OpenSSH Server (sshd)" `
    -Enabled True `
    -Direction Inbound `
    -Protocol TCP `
    -Action Allow `
    -LocalPort 22
}
```

### Visual Studio Build Tools bootstrap

```powershell
$vsArgs = @(
  "--quiet", "--wait", "--norestart", "--nocache",
  "--installPath", "C:\BuildTools",
  "--add", "Microsoft.VisualStudio.Workload.VCTools",
  "--includeRecommended"
)
Start-Process C:\agent-in\vs_BuildTools.exe -Wait -ArgumentList $vsArgs
```

### Multipass Ubuntu VM

```bash
sudo snap install multipass
multipass launch 24.04 --name agent --cpus 6 --memory 12G --disk 80G
multipass shell agent
```

### Lima Ubuntu VM

```bash
brew install lima
limactl start ./agent.yaml --name agent
limactl shell agent
```

### OverlayFS reset layer

```bash
sudo mkdir -p /srv/agent/base /srv/agent/upper /srv/agent/work /srv/agent/merged

sudo mount -t overlay overlay \
  -o lowerdir=/srv/agent/base,upperdir=/srv/agent/upper,workdir=/srv/agent/work \
  /srv/agent/merged

sudo chroot /srv/agent/merged /bin/bash
```

## Appendix G: Platform Setup References

The following public references are useful when turning the preflight recipes into local operating procedures:

- Codex CLI flags and `--yolo`: [@codex-cli-reference].
- Codex approvals and sandboxing: [@codex-security].
- Codex `AGENTS.md` discovery and precedence: [@codex-agents-md].
- Claude Code CLI permission-bypass flags: [@claude-code-cli-reference].
- Claude Code `CLAUDE.md` memory/instruction files: [@claude-code-memory].
- WSL installation: [@microsoft-wsl-install].
- WSL filesystem placement: [@microsoft-wsl-filesystems].
- WSL advanced configuration: [@microsoft-wsl-config].
- WSL networking and mirrored mode: [@microsoft-wsl-networking].
- Windows Sandbox overview and configuration: [@microsoft-windows-sandbox; @microsoft-windows-sandbox-config].
- Windows Sandbox CLI: [@microsoft-windows-sandbox-cli].
- OpenSSH Server on Windows: [@microsoft-openssh-windows].
- Visual Studio command-line installation and Build Tools workload IDs: [@microsoft-vs-install; @microsoft-vs-buildtools].
- Windows licensing overview: [@microsoft-windows-licensing].
- Ubuntu Virtual Machine Manager: [@ubuntu-virt-manager].
- Multipass: [@canonical-multipass].
- LXD virtual machines and containers: [@ubuntu-lxd].
- libvirt networking: [@libvirt-networking; @libvirt-network-xml].
- OverlayFS: [@linux-overlayfs].
- `systemd-nspawn`: [@systemd-nspawn].
- Lima usage and mounts: [@lima-usage; @lima-mounts].

## Appendix H: Glossary

**Agentic software engineering:** Software development using AI systems that can plan, use tools, edit repositories, run commands, and iterate.

**Execution agent:** The coding agent that operates the repository and machine environment.

**Strategic AI:** The high-powered, long-context model used for planning, architecture, critique, work-order generation, evidence compression, and human-facing decision support.

**Strategic control plane:** The OAP layer where human intent, project context, agent reports, evidence, and next work orders are synthesized.

**Domain expert orchestrator:** A human lead whose primary authority comes from domain knowledge rather than coding expertise, and who governs goals, acceptance criteria, risk, and release through the strategic AI.

**Domain truth:** The real-world workflow, constraints, vocabulary, user needs, risks, and success criteria that software must preserve.

**Project constitution:** Durable repository instructions that define rules for agents.

**Validation debt:** The verification burden created when generated code appears faster than it can be reviewed.

**High-autonomy runtime:** An agent environment with broad ability to execute commands and modify files, bounded by VM, container, sandbox, credentials, and workflow.

**Rebuildable execution VM:** A hardened disposable environment where the agent may install tools and run tests because durable project truth lives outside the VM.

**PR-sized delegation:** A work unit scoped so that the result can be reviewed as one coherent pull request.

**Decision brief:** A short strategic summary containing recommendation, goal match, evidence, risk, and the human decision required.

**Control inversion:** A failure mode where the execution agent starts directing the human through low-level setup or debugging work.
