# W6 cutover-gate rules — mechanical writedown (livespec-iaut)

**STATUS: DRAFT — PENDING USER RATIFICATION.** No rule in this document
is in force until the user ratifies it. The tpu disposition in §3 is a
RECOMMENDATION and is explicitly marked as requiring user ratification.
This document is the deliverable of work-item `livespec-iaut` (design
pass; no code changes). It belongs with `dw1t` (the W6 dark-factory
wave) and `a8bb` (orchestrator retirement) and MUST be resolved —
ratified or amended — BEFORE any gate-pass declaration.

## 1. Why this document exists

The W6 cutover gate — **10 consecutive green work-items, across at
least 2 repos, with 0 rescues** — decides when `/livespec-orchestrate`
retires (livespec `a8bb`) and the Beads+Fabro Dispatcher runs
unattended (the dark-factory switchover inside epic `livespec-4moata`,
wave `dw1t`). Two defects in how the gate has operated so far:

1. **The rules lived only in handoff prose.** What counts, what
   resets, what a rescue is, and whether sub-agent-routed work counts
   or breaks the streak were unwritten interpretations — and the
   sub-agent interpretation in particular let risky work route AROUND
   the gate without the gate ever seeing it.
2. **The streak is being earned under orchestrator curation** —
   crisp-item selection, host preflights, per-repo goal scoping,
   premise gates, embargo sequencing. A streak earned that way proves
   a babysat dispatcher, not an unattended one.

**PRINCIPLE: every manual streak-protection must become a dispatcher
feature before cutover, or the gate is theater.** The good precedent
is `cgd`: the manual host preflight (`just check` on the target
primary before every dispatch) was replaced by a mechanized janitor
that runs in a fresh detached worktree of the merged ref
(impl-beads PR #22), with its venue fixed out of the `/tmp` coverage
omit by `1l6` (impl-beads PR #25). The host preflight is now
redundant — the protection is a dispatcher feature, not an operator
habit. §4 inventories the protections that have NOT yet made that
transition.

## 2. Gate events and verdicts (mechanical rules)

### 2.0 Unit of account and ordering

- The unit of account is the **per-repo dispatcher leg**: one
  dispatcher invocation (`dispatcher.py dispatch --item X --repo Y`)
  that starts a sandbox against one target repo. A work-item split
  into per-repo legs yields one gate event per leg (precedent: `7us.5`
  split into 4 legs — `7dro`, `90k`, `tpu`, `ay2` — each its own gate
  event, recorded by comment on the parent item).
- Gate events are **ordered by the dispatcher's final-verdict
  timestamp** (the janitor verdict for greens; the terminal journal
  entry for reds). Concurrent dispatches are sequenced by that
  timestamp, not by dispatch start.
- Every gate event MUST be evidenced by a dispatcher journal
  (`--journal <path>`, JSONL). Gate evaluation reads journals, not
  operator memory. Gate accounting itself is currently manual
  (handoff prose plus orchestrator recall); a mechanically derivable
  gate-evaluation report over the journals is itself a pre-cutover
  mechanization target (§4).

### 2.1 GREEN — what counts

A gate event is **GREEN** if and only if ALL of the following hold:

1. The work-item leg was **dispatcher-dispatched** (sandbox started by
   `dispatcher.py`; host sub-agent work never counts — §2.6).
2. The resulting PR **merged without human intervention**: auto-merge
   armed by the sandbox agent, CI green, no human commit, no human
   force-action, no human re-arm, no human conflict resolution.
3. The **post-merge janitor mechanically confirmed green**: the
   janitor ran in its fresh detached worktree of the merged ref at
   `<repo>/worktrees/janitor-<item>` (the cgd+1l6 venue) and exited
   green, OR the run classified as `janitor-env-degraded` per the
   mechanized rule (§2.5).

A GREEN advances the streak by exactly 1.

### 2.2 What RESETS the streak

The streak resets to 0 on any of:

1. **A rescue** (§2.3): any dispatched leg that required human action
   for the WORK to land or close correctly — even if the PR
   ultimately merged and the janitor went green.
2. **A mechanically classified red**: the dispatcher's final verdict
   for a dispatched leg is failed/abandoned (sandbox failure, janitor
   red inside the fresh checkout, mechanized retry budget exhausted,
   timeout). Dispatcher-internal retries that complete without human
   action are part of one gate event; only the final verdict counts.
3. **A red whose classification required ad-hoc human forensics**:
   if a human had to investigate to decide whether a red was "real"
   or an artifact, that investigation IS a rescue of the gate's
   instrumentation and resets — regardless of what the forensics
   concluded. (Forward rule; see §3 for the one grandfathered
   exception, tpu.)

What does NOT reset: non-events (§2.4, §2.6) and
`janitor-env-degraded` greens (§2.5).

### 2.3 RESCUE — precise definition

A **rescue** is any human action without which the dispatched
work-item would not have landed or closed correctly. Tests:

- Human pushes a commit to the PR branch, resolves a conflict, edits
  the work product, or re-runs/overrides CI to get the merge through
  → rescue.
- Human re-arms auto-merge, manually merges, or manually closes the
  item because the sandbox agent failed to complete its own handoff
  → rescue.
- Human performs ad-hoc forensics to classify a red (and the
  classification is not produced by a pre-ratified mechanized rule)
  → rescue (of the instrumentation; still resets — §2.2.3).
- Human files a follow-up bug, comments on the item, or reads the
  journal WITHOUT changing the outcome of the leg → NOT a rescue
  (observation is free; intervention is not).
- A mechanized action by the dispatcher itself (bn4 retry, cgd
  classification, janitor venue provisioning) → NOT a rescue, by
  construction.

The boundary question to ask: **if no human had been watching, would
this leg have landed and closed correctly anyway?** If yes, no rescue
occurred.

### 2.4 Pre-flight validation failures — non-events

A dispatch attempt that fails the dispatcher's own pre-flight
validation **before any sandbox starts** (zero side effects: no fabro
run, no branch, no PR, no ledger mutation beyond the attempt record)
is a **non-event**: it neither counts as a green nor resets the
streak. The work-item simply was never dispatched.

Evidence (2026-06-13, current session): fabro pre-flight rejects item
goal text containing literal double-curly tokens (justfile syntax)
with `template_undefined_variable` in the workflow graph — no sandbox
started, zero side effects. Filed as `livespec-impl-beads-ajv`.

**Obligation:** recurring pre-flight failure classes MUST be filed as
dispatcher bugs (as ajv was). A pre-flight class that recurs without a
filed bug is a curation smell — the operator is absorbing a defect the
dispatcher should reject gracefully or tolerate.

### 2.5 `janitor-env-degraded` — green by mechanized rule

When the janitor's fresh-worktree **provisioning** fails (worktree
add, mise trust), the run classifies as `janitor-env-degraded` and the
gate event **stays GREEN** — the merge is already confirmed, and a
host-environment problem is not a work-item failure. This is the
cgd-mechanized classification (impl-beads PR #22): the prep/run
boundary IS the classifier. No stderr-pattern heuristics, and —
critically — **no human judgment**: the classification is green
because the mechanized rule says so, never because an operator decided
the red "didn't really count". A red INSIDE the successfully
provisioned checkout is change-shaped, classifies failed, and resets
(§2.2.2).

### 2.6 Sub-agent-routed work — neither counts nor resets, but is measured

Work routed to a **host sub-agent** instead of the dispatcher (current
routing reasons: judgment-leaning items, items touching the
dispatcher's own machinery per `ddu`, reproduction-shaped goals)
produces NO gate event: it neither counts nor resets.

But this is exactly the loophole this document was filed to close:
**risky work routing around the gate inflates the streak's apparent
meaning** — the dispatcher looks 10-for-10 because everything hard was
quietly routed elsewhere. Mechanical requirements:

1. Every host-sub-agent routing of an otherwise dispatcher-eligible
   item MUST be **logged with an explicit routing reason** (item
   comment or journal entry) at routing time.
2. At gate-evaluation time, the evaluation MUST report the **routing
   ratio** for the gate window:
   `routed = host-sub-agent-routed eligible items`,
   `dispatched = dispatcher gate events`,
   `routing ratio = routed / (routed + dispatched)`.
   The ratifier sees, in one number, how much work bypassed the
   dispatcher while the streak was being earned.
3. **Proposed bound (for ratification):** if the routing ratio over
   the qualifying window exceeds **1/3**, gate-pass declaration is
   blocked until each routing is individually justified to the
   ratifier and the ratifier accepts that the routed class will remain
   out of dispatcher scope after cutover (or has a filed mechanization
   item). The number 1/3 is a proposal, not a derivation — the
   load-bearing part is that the ratio is REPORTED and BOUNDED, not
   the specific threshold.

### 2.7 Consecutiveness and the at-least-2-repos window

- The **qualifying window** is a run of 10 gate events, consecutive in
  final-verdict order, all GREEN, with no reset event (§2.2) anywhere
  inside the run. Non-events (§2.4, §2.6) do not occupy positions in
  the sequence and do not break consecutiveness.
- Among the 10 greens of the qualifying window, the set of **target
  repos must have cardinality ≥ 2**. A 10-green run confined to one
  repo does not pass; the streak simply continues until the sliding
  most-recent-10 window spans ≥ 2 repos (or a reset intervenes).
- There is no wall-clock window: consecutiveness is in event order,
  not time. (Long gaps between dispatches are allowed; what is NOT
  allowed is a reset event inside the run.)

**Current state under these rules:** streak = 6 — `smc`, `90k`,
`7dro`, `lta`, `7us.4`, `ay2` — across 4 repos (livespec,
livespec-runtime, livespec-impl-git-jsonl, livespec-dev-tooling). The
repo-cardinality condition is already satisfied; 4 more greens with no
reset complete the numeric condition. Completing the number does NOT
declare the gate passed — see §5.

## 3. The tpu disposition — RECOMMENDED, requires user ratification

**Recommendation: GRANDFATHER. tpu neither counts nor resets; the
streak stands at 6.**

Facts (forensics in `tmp/contract-re-steering-session-1-status.md`,
2026-06-13 entries):

- tpu's work merged green without rescue (impl-beads PR #24: sandbox
  green, CI green, auto-merge, no human touch on the work).
- The dispatcher verdict was red, but the red was a **defect in the
  gate's INSTRUMENTATION, not in the work**: the cgd janitor's first
  live exercise provisioned its fresh worktree under
  `/tmp/fabro-janitor-<item>`; the family `pyproject` coverage omit
  contains `/tmp/*`; every source file was omitted; coverage raised
  `NoDataError`; the janitor went red. Proven by discriminating
  experiment (same sha green at the primary, deterministically red in
  the venue) and fixed forward: `1l6` (impl-beads PR #25) moved the
  venue to `<repo>/worktrees/janitor-<item>`, with a regression test
  that pins the venue against the REAL coverage omit globs.
- The human forensics fixed the **measurement**, not the work. tpu
  predates the very mechanized classification rules (§2.2.3, §2.5)
  that its failure motivated; applying those rules to it
  retroactively would punish the event that produced them.

**FORWARD RULE (in force from ratification):** now that cgd and 1l6
exist, any future red that needs ad-hoc human forensics to classify
IS a rescue and resets the streak (§2.2.3). No more grandfathering.
If a new instrumentation-artifact class appears, the correct response
is: take the reset, fix the instrumentation as a dispatcher feature,
add the mechanized classification, and re-earn the greens — that is
the cgd pattern, and it is the only path that keeps the gate honest.

## 4. Mechanization inventory — manual streak-protections vs required dispatcher features

The cgd precedent is the pattern each row must follow: a manual
operator habit becomes a dispatcher feature with a mechanized rule
and a regression test, after which the habit is redundant.

| Manual streak-protection | Current state | Dispatcher feature required before cutover | Proposed work-item one-liner |
|---|---|---|---|
| Host preflight (`just check` on target primary before dispatch) | **MECHANIZED — the precedent.** cgd janitor runs in a fresh detached worktree of the merged ref (PR #22); 1l6 fixed the venue out of the `/tmp` coverage omit (PR #25). Host preflights now redundant. | (done) | (closed: `cgd`, `1l6`) |
| Item-sizing / authoring quality (crisp-item selection, per-repo goal scoping) | `bn4` sizing check **WARNS only** — observed live 2026-06-13: a 1686-char description warned and dispatched anyway. Crisp scoping is pure orchestrator judgment. | Promote sizing to fail-closed: oversize goals are rejected at pre-flight (a non-event, §2.4) with a mechanized split-or-override path; goal-scoping lint on dispatch. | "Promote bn4 item-sizing warn to fail-closed reject with an explicit split/override path." |
| Premise verification ("agents MUST verify item premises against master") | Prose convention pasted into dispatch briefs; enforcement is the sandbox agent's diligence. | Mechanical pre-flight premise check: items carry machine-checkable premises (paths exist, pins at expected values, target state asserted) verified against fresh origin/master before sandbox start; failure = non-event + ledger comment. | "Add machine-checkable premise assertions to work-items and verify them in dispatcher pre-flight." |
| Cross-repo sequencing / impl-beads embargo (never pull the impl-beads primary while a dispatcher is alive; dispatch impl-beads-targeted items alone) | Orchestrator discipline in handoff prose. | Dispatcher-level repo lock: dispatching takes a per-repo lease; impl-beads-targeted dispatches require an exclusive family lease; concurrent-dispatch conflicts rejected at pre-flight. | "Replace the impl-beads embargo convention with a dispatcher-level per-repo dispatch lease." |
| Goal-text escaping (literal double-curly tokens break fabro template rendering) | Fails pre-flight with `template_undefined_variable`; zero side effects; operator currently rewords goals by hand. **FILED.** | Escape or fence goal text before template rendering so arbitrary item prose cannot break the workflow graph. | (filed: `livespec-impl-beads-ajv`) |
| Gate accounting itself (streak count, event ledger) | Handoff prose + orchestrator recall, evidenced ad hoc by `tmp/dispatcher-journal-*.jsonl`. | Mechanically derivable gate-evaluation report over the journals: event sequence, verdicts, repo set, routing ratio (§2.6), current streak. | "Emit a mechanical gate-evaluation report (streak, repo set, routing ratio) from dispatcher journals." |

Rows 2–4 are the "remaining unmechanized" set named by `livespec-iaut`;
the last row is added by this writedown (§2.0 requires it). Until every
row is mechanized (or the user explicitly waives a row at
ratification), greens continue to accrue under curation and the gate's
unattended claim remains qualified.

## 5. Gate-pass declaration is not automatic

**Reaching a numeric streak of 10 does NOT auto-declare gate-pass.**
Declaration additionally requires, in any order before the
declaration:

1. **These rules ratified by the user** — including the tpu
   disposition (§3), the routing-ratio bound (§2.6.3), and an explicit
   keep-or-waive decision on each open row of the §4 inventory.
2. **`livespec-0jxs` resolved** — the operability preconditions item
   (and the `a8bb` duty-relocation question it carries) closed or
   explicitly waived by the user.

Until both hold, the streak is a necessary-but-insufficient counter.
The declaration itself is a user act, recorded on `dw1t`, after seeing
the gate-evaluation report (event list, repo set, routing ratio,
non-event log).

---

**DRAFT — PENDING USER RATIFICATION** (repeated deliberately: nothing
above is in force until ratified; the streak-stands-at-6 reading in
§2.7/§3 is the recommended, not the ruled, state).
