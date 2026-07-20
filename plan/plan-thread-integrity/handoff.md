# plan-thread-durability — handoff

**Ledger anchor:** epic `livespec-nr5h` (livespec CORE tenant).
**Opened:** 2026-07-19.

Status is READ from the ledger, never stored here. This file carries no
checkbox queue.

## What this thread is

A plan handoff written to disk is not saved. On 2026-07-19 one sat dirty in the
primary checkout carrying 153 unversioned lines, one `git checkout` from being
lost, with no attribution trail — and every mechanism that could have caught it
either did not cover `plan/` or did not run at the moment that mattered. The
root cause is that **"persisted to disk" was mistaken for "durable."**

The evidence, the mechanism, and the constraints are in
[`design.md`](./design.md). Read it before acting; this file is the resume
point, not the analysis.

| Layer | What it does | Status |
|---|---|---|
| 1 — session-end (Stop) check | Catches a dirty handoff while the authoring session can still commit. **Whether this PREVENTS or merely detects-at-session-end depends on an unsettled posture decision** — surface-only versus interruptive | Free of the spec lifecycle IF scoped livespec-core-local — see below |
| 2 — widen the existing invariant to `plan/` | **Detects**: makes it visible to `just check`, CI, and other sessions | Needs propose-change → Fable review → revise |
| 3 — session-start surface | **Recovers**: prompts the next session to rescue the file | Build only if layer 1 proves insufficient |

The layers are named by what they actually do. Layer 2 is the obvious fix and is
worth doing, but it fires `warn` (wrapper exit 0) and only runs when someone
invokes `just check` — so it detects rather than prevents, and calling it
enforcement would repeat the error this thread exists to correct.

## Start here

> **READ [`plan.md`](./plan.md) FIRST — it is authoritative and it supersedes
> this section.** Added 2026-07-19 after two independent adversarial reviews
> (Fable and Codex) each raised the staleness of this section as a BLOCKER.
>
> **The blocking session-end (`Stop`) hook recommended below is WITHDRAWN.** Do
> NOT build it. It would stall overseer-managed tracks past the 120s
> `_MARKER_VOID_GRACE`, and a careless agent can satisfy the block by running
> `git checkout -- plan/` — destroying the file the block exists to save.
> `plan.md` §"What this plan does NOT build, and why" carries the full
> reasoning.
>
> This matters because the overseer hands a respawned session exactly one
> prompt — "read this handoff and follow it" — so a successor reading only the
> text below would build the withdrawn mechanism. That is the failure both
> reviewers named.

**STATE 2026-07-20 — BOTH WORKSTREAMS COMPLETE. This thread is DONE.**

| | Item | Spec | Implementation |
|---|---|---|---|
| W4 | Overseer wrap-up says COMMIT the handoff, not just update it | n/a | **MERGED** (PR #1492), live-verified |
| W3 | Widen the uncommitted-edits invariant to `plan/` | **v170** (PR #1495) | **MERGED** (PR #1499), live-verified |

Nothing is in flight. No branch, no worktree, no pull request belongs to this
thread. Work-item `livespec-8h07` (the W3 implementation) is closed with
live-exercise evidence.

**The false pass is gone, and that was measured, not assumed.** Against a real
dirty `plan/` file on a real master worktree the check now reports:

```
status: warn
1 worktree(s) on `master` carry uncommitted spec-tree or `plan/` edits:
  /tmp/livecheck-master: plan: plan/plan-thread-integrity/handoff.md.
Corrective action: move the edits to a feature branch and commit them there.
NEVER discard `plan/` edits: an uncommitted handoff is frequently the only
copy of a planning thread.
```

Note what is absent: no discard suggestion, because only a `plan/` path was
implicated. Before the change the identical state reported `pass`.

**If you are resuming this thread, the likely reason is one of these — and none
of them is "build more mechanism":**

- The **multi-tree duplicate-warn** note: the check runs once per spec tree, so
  on a multi-spec-tree project one dirty `plan/` file could yield one identical
  `warn` per tree. Not hit here (single tree). Latent note, not a defect.
- The **overseer daemon** holds the old wrap-up text until restarted; that is a
  maintainer action in the overseer pane.
- A **second real incident**. If one occurs, `plan.md` §"Considered and cut"
  records the three larger mechanisms and exactly why each was cut — read the
  reasoning before reviving any of them, because two of the three were refuted
  on technical merits, not merely on cost.

## Conventions this thread holds itself to

- **This handoff is an owned artifact, not a read-only inbox.** Update it as
  findings land and commit them; do not accumulate findings in session context
  to be written at session end, because a session can die first — which is
  precisely how the incident above happened. Doc-only work is NOT gated by
  `check-doctor-static` at EITHER step — not the commit (`justfile:518`) and not
  the push, since `check-pre-push` delegates a zero-`.py` push to the same
  seven-target subset (`justfile:548`). So there is never a blocker excuse for
  leaving this file dirty.
- **Load-bearing claims cite the command that produced them.** `design.md` marks
  each claim MEASURED (with its command) or INFERRED. An earlier draft of this
  thread asserted the convention without applying it, and an adversarial review
  correctly called that self-refuting.
- **Correct in place and say so.** A disproved claim gets struck and annotated,
  not silently deleted.

## Review history

Two rounds of independent Codex review, both adversarial and read-only.

**Round 1** found the first draft incoherent: it bundled three defects —
durability, an authoring convention, and cross-session visibility — sharing only
"noticed during the same incident", not architecture, and the draft's own text
conceded they were independent and landable in any order. It also caught the
draft overstating a `warn` check as enforcement, and caught it failing to apply
its own evidence-labeling convention. The thread was narrowed to durability
alone; the two cut defects and the reasoning are preserved in `design.md`
§"Considered and deliberately not included" rather than dropped. The better
framing of the root cause — "persisted to disk" mistaken for "durable" — came
from that review.

**Round 2** reviewed the rewrite and found three remaining correctness problems,
all now fixed: a false MEASURED claim that only `push` runs the full aggregate
(doc-only pushes take the same reduced subset, `justfile:548` — verified
independently before accepting); an INFERRED conclusion labeled MEASURED and
overstated as "cannot be driven at all"; and the unqualified word "prevention"
on layer 1, whose posture is in fact undecided. That a document about
unverified claims twice shipped an unverified claim is itself the argument for
the convention it proposes.

## Out of scope

- The `cross_repo_targets` dual-purpose defect and the CI/local sibling-set
  divergence — ledger item `livespec-fxxfq6` under epic `livespec-n4ptl2`
  (`plan/fleet-pin-propagation/`). Corrections were relayed to that thread on
  2026-07-19, including a false "ships from `livespec-dev-tooling`" claim in the
  item's own text and the finding that CI's sibling-clone list is hardcoded and
  has drifted from `.livespec.jsonc` in both directions.
- The overseer gate work (Gate B, Gate E) — `plan/overseer-productization/`.
- The re-land of the cross-tenant linkage for
  `livespec-console-beads-fabro-tafkuw` — same fleet-pin-propagation thread.
