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

**STATE 2026-07-20 — W4 landed; W3 committed and BLOCKED ON A GITHUB OUTAGE.**

| | Item | State |
|---|---|---|
| W4 | Overseer wrap-up says COMMIT the handoff, not just update it | **MERGED** (PR #1492) and live-verified |
| W3 | Widen the invariant to `plan/` | **Committed as v170, UNPUSHED** — see below |

W3 is complete through ratification and blocked only on network:

- Branch `spec/widen-uncommitted-edits-to-plan`, worktree
  `~/.worktrees/livespec/spec-widen-uncommitted-edits-to-plan`.
- Proposal filed, then AMENDED for a real blocker found by the mandatory
  independent Fable review (the section's committed-violations delegation was
  false for `plan/`); re-reviewed to **NO BLOCKERS**; revise driven; **v170 cut**;
  `just check` **all 71 targets passed**.
- `git push` fails with HTTP 503 from the GitHub App credential helper.
  githubstatus.com reports a Minor Service Outage; `gh api` 503s as well. This
  is external and not a defect in the change.

**To resume: push, PR, merge, then refresh the primary and remove the worktree.**
Nothing needs re-deciding and nothing needs re-reviewing — the review verdict is
recorded in the commit messages on that branch.

~~Recommended first move is **layer 1**, the session-end check.~~ A 2026-07-19
investigation reshaped what that means; read `design.md` §"A `Stop` hook already
ships, already ran, and encodes the root cause" and §"The home question has a
third answer, and it is coupled to the posture" for the evidence — but take the
DISPOSITION from `plan.md`, not from this file.

**Layer 1 is not a greenfield build.** The Claude Driver bundle already
registers two `Stop` hooks, and one of them —
`warn_plan_persistence.py`, whose stated purpose is "completion includes
persistence" — fired at the end of the session that lost the handoff and emitted
nothing, because `:155` early-exits the moment any `Write` appears in the turn.
The root-cause conflation this thread names is encoded in shipped code at that
line. The hook is correct as specified; its contract stops at *written*. Not a
Driver bug.

**One decision, not two.** Home and posture looked independent and are not:

| Home | Posture available | Spec cycle | Repos covered |
|---|---|---|---|
| `livespec_dev_tooling.agent_hooks` | free — blocking already shipped there | none | 6 of 8 (wired in each committed `.claude/settings.json`) |
| Driver bundle | WARN-only by contract | yes, incl. any posture change | all governed repos |
| livespec-core-local | free | none | 1 |

~~**The recommendation flipped to blocking, in `livespec_dev_tooling.agent_hooks`.**~~
**RETRACTED 2026-07-19 — see [`plan.md`](./plan.md).** The blocking posture was
recommended on reasoning that did not survive review: it stalls overseer tracks,
and it hands a careless agent a destructive way to satisfy the block. The
paragraph below is preserved for its reasoning trail, not as a live
recommendation.
A WARN-only Stop hook lets the session end, so nothing commits the file — it
cannot produce this thread's outcome. Only exit `2` hands control back while the
authoring session can still act. The trap risk that argued for surface-only is
already solved in-fleet: `subagent_stop_guard` blocks with exit `2`, caps at
three blocks per session, and fails open on every error path. Both superseded
recommendations are struck and annotated in `design.md`, not deleted.

~~Still open, and a genuine maintainer call: **which home** (the table above), and
whether the existing plan-persistence contract should be widened in the same
pass or left alone.~~

**MOOT as of 2026-07-19 — see [`plan.md`](./plan.md).** No hook is built
anywhere under the cut plan, so the home question is disposed rather than open.
The table above is retained for its reasoning only. What remains is W3 (widen
the uncommitted-edits invariant to `plan/`) and W4 (say "commit it" in the
overseer wrap-up).

One further constraint will waste a session if discovered late:

- **Layer 2 is a spec change** carrying an unsettled slug rename, and a red
  `doctor-static` obstructs it: propose-change runs doctor static at both its
  pre-step and its post-step, and `--skip-pre-check` suppresses only the
  pre-step. The precise shape matters — the proposed-change file still lands on
  disk and the CLI then reports exit 3, so the operation cannot complete cleanly
  but the artifact is not lost.

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
