# Autonomous-mode MVP — overall plan handoff (livespec core)

**Status: SPEC FOUNDATIONS RATIFIED (2026-07-10) — Step 0 met; O1 and C1 both
ratified; the build phase (C2, O2) is NEXT and PAUSED at the maintainer's
request.** The Step-0 fable-review loop exited (round-6 NOTHING-BLOCKING +
maintainer certification, in the Loop state below); the driver then dispatched
O1 and C1 as scoped subagents and drove each through propose-change →
independent read-only Fable review → revise.

**Ratification record (2026-07-10):**
- **O1 → orchestrator v033 (RATIFIED).** Two propose-changes (irreducible human
  touchpoints; arming/audit contract): filed by the delegate (orchestrator
  PR #415), reconciled by the driver toward a fuller parallel maintainer/Fable
  draft (folded amendments K/L/O + the Scenario-33 routine qualifier; PR #416),
  Fable-reviewed NOTHING-BLOCKING, revised accept/accept to v033 (PR #417).
  **Arming/audit contract FROZEN → overall I1 SATISFIED** → console C3 and
  orchestrator O2 unblocked. On master: `drive --mode autonomous`=0;
  `loop --mode autonomous` is the mode surface; the design-human-gated set +
  `human-only` carve-out + single-persistent-permission key are live.
- **C1 → console v017 (RATIFIED).** Two propose-changes (citation-currency;
  autonomous-resolution delegation): filed (console PR #147), Fable-reviewed
  NOTHING-BLOCKING, revised accept/accept to v017 (PR #149) with a
  behavioral-coverage lockstep co-edit (process note below). MAIN ratification
  done; the persistence-seam amendment stays DEFERRED but is now I1-unblocked.
  `rt4` version pointer refreshed v013→v016.
- Reaped two stale/absorbed branches: orchestrator
  `o1-autonomous-mode-touchpoints-arming` (absorbed parallel draft; source at
  git 1f25529 + driver scratchpad), console `autonomous-mode-c1-spec-currency`
  (empty stale).

**PROCESS NOTE (carry forward) — console behavioral-coverage co-edit.** The
console repo's coverage gate binds normative-CLAUSE gap-ids (content-hashes of
each MUST/SHOULD line) to scenarios — NOT H2 names. ANY console spec revise that
adds/removes/rewords a normative clause REQUIRES a lockstep co-edit
(`tests/heading-coverage.json` clause-gap-id rebinding + the
`crates/console-spec-check/src/tests.rs` ground-truth count refresh) even with
zero `## ` H2 changes — the console analogue of core's H2 heading-coverage
co-edit (precedent: console v016 CN1 + v014). Future console propose-changes
should carry this in their `resulting_files`.

The Step-0 loop rules are kept below for the historical record: each round, a
FRESH Fable session reviewed ALL THREE plans AND FIXED every problem it found
(via worktree → PR → merge); a session that landed fixes could not clear the
gate (no self-certification) — the clean verdict always came from the NEXT fresh
session.

**Loop state:**
- Round 1 (2026-07-10, Fable session `livespec-autonomous-mode`): Step-0
  validation of the ORIGINAL plans → NO-BLOCKERS with 9 observations
  (`research/step0-fable-verdict.md`); the SAME session then FIXED every
  finding in all three plans (orchestrator PR #395, console PR #134, core
  PRs #1000 + this one) and wrote
  `research/fable-revising-session-self-assessment.md` — which does NOT
  clear the gate, because reviser and reviewer were the same session.
- Round 2 (2026-07-10, fresh Fable session, this repo's session
  `livespec-autonomous-mode` pane): first fresh-session review-AND-FIX over the
  REVISED plans → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-2.md`; core PR #1014, console PR #141,
  orchestrator PR #404). All round-1 revisions re-verified against live state;
  fixes were currency + internal-soundness precision (stale `orchestrate run`
  in core C2 step text; C2-gate two-phase-C1 ambiguity; fabro-token-refresh
  state moved; mb64bv type; O2 done-surface pin). Because fixes landed, this
  round does NOT clear the gate.
- Round 3 (2026-07-10, fresh Fable session): second fresh-session
  review-AND-FIX → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-3.md`; orchestrator PR #410 + the core PR
  carrying that record). Every rounds-1-2 revision re-verified against live
  state; no structural defect anywhere; the two fixes were small currency/
  precision (stale "PR #136 cleanup" pending-decision in core §9 +
  orchestrator §5 — the validation vehicle auto-merged 2026-07-10;
  `livespec-zs22.6` is a closed task, not an epic). The CONSOLE plan passed
  clean — its first no-fix round. Because fixes landed, this round does NOT
  clear the gate.
- Round 4 (2026-07-10, fresh Fable session spawned by the driver): third
  fresh-session review-AND-FIX → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-4.md`; fixes in core PR #1022, record +
  loop state in core PR #1023). Every rounds-1-3
  revision re-verified against live state; the two fixes were small
  consistency/currency, both in the overall plan (design §7 graph missing
  the `I1 ─► C1 persistence-seam` edge its own prose asserts; stale
  "revised rounds 1-2" Read-first annotation). BOTH sibling plans passed
  clean (console's second consecutive clean round; orchestrator's first).
  Because fixes landed, this round does NOT clear the gate.
- Round 5 (2026-07-10, fresh Fable session spawned by the driver): fourth
  fresh-session review-AND-FIX → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-5.md`; fix in core PR #1024, record + loop
  state in the core PR carrying this bullet). One currency fix, in the
  overall plan's own Loop state (the round-4 bullet omitted its
  record-carrying PR #1023). BOTH sibling plans passed clean again
  (console's third consecutive clean round; orchestrator's second).
  Because a fix landed, this round does NOT clear the gate.
- Round 6 (2026-07-10, fresh Fable session spawned by the driver): fifth
  fresh-session review → **NOTHING-BLOCKING** (verdict:
  `research/fable-review-round-6.md`; a purely read-only round — no fix
  was warranted, none was landed, so the no-self-certification rule is
  satisfied). Every load-bearing claim in all three plans re-verified
  first-hand as true; both sibling plans clean for the fourth/third
  consecutive round (console/orchestrator); the convergence trajectory
  (9 obs → 6 → 2 → 2 → 1 fixes) reaches zero. The verdict affirmatively
  certifies all three plans SOLID, EXECUTABLE, and MVP-MEETING.
- Maintainer certification: **GIVEN 2026-07-10** — the maintainer
  certified round 6's NOTHING-BLOCKING verdict in the driver session
  (recorded here by the driver). THE STEP-0 LOOP IS EXITED; C1/O1
  dispatch is unblocked (Next actions, step 4). → Dispatching C1 and O1
  in parallel is the next action.

**Thread role:** the OVERALL cross-repo plan. Ties together the console operator
surface and the orchestrator decision engine, owns the dependency graph, and
defines the driver + per-repo delegate-context delegation model (design.md §8).
livespec core authors no product code here.

## Read first
1. This file, then `design.md` in this directory (the full plan).
2. For the review loop: `research/fable-review-brief.md` (the brief each
   fresh reviewer runs), then the prior rounds
   (`research/step0-fable-verdict.md`,
   `research/fable-revising-session-self-assessment.md`,
   `research/fable-review-round-N.md` as they accumulate).
3. The two sibling repo plans this coordinates (both carry the accumulated
   review-round findings in their own step texts, kept current across the
   review-loop rounds):
   - `livespec-console-beads-fabro/plan/autonomous-mode/design.md`
   - `livespec-orchestrator-beads-fabro/plan/autonomous-mode/design.md`

## Goal (one line)
A human flips per-repo **full autonomous mode** from the
`livespec-console-beads-fabro` **TUI** (GUI out of scope) and the Beads/Dolt +
Fabro factory drives ready work to `done` unattended — LLM-resolving the human
gates, auditing every decision, surfacing only the truly-unresolvable back to the
operator.

## The spine (see design.md §7 for the full step catalogue)
```
Step 0 (fable-review LOOP — HARD GATE) ✓ MET 2026-07-10 (round 6 NOTHING-BLOCKING + maintainer certification)
  status: O1 RATIFIED (orch v033, I1 satisfied) ✓ · C1 MAIN RATIFIED (console v017) ✓ · build phase (C2, O2) NEXT — PAUSED at maintainer request.
  ├─ Console track (delegate console-autonomous-mode):  C1 spec fixes ✓ ─► C2 command foundation ─► C3 autonomous feature
  └─ Orchestrator track (delegate orchestrator-autonomous-mode): O1 spec fixes + arming contract ✓ ─► O2 build engine (bd-ib-82a)
                          O1 arming contract (I1) ✓ ─► C3 (and C1's persistence-seam portion, now I1-unblocked)
  Integration (driver session autonomous-mode): I2 end-to-end live exercise on a real tenant = MVP "done"
```
Console C2 and orchestrator O1→O2 run in parallel — but ONLY after the Step-0
loop exits. Contract-first: O1 publishes the arming/audit contract before C3
builds on it.

## Next actions (exact steps for a new session — the BUILD phase)

Step 0 + O1 + C1(main) are DONE (see Ratification record at top). The build
phase is PAUSED at the maintainer's request. C2 and O2 run concurrently; both
open now. Resume:

1. **O2 — implement the orchestrator engine (`bd-ib-82a`).** FIRST groom
   `bd-ib-82a` into dependency-layered slices — grooming is a MAINTAINER-OWNED
   cut (`/livespec-orchestrator-beads-fabro:groom`; the front-end drafts, the
   maintainer owns the acceptance), so set it up FOR the maintainer, do NOT
   auto-slice. Then build: the `dispatcher.autonomous_mode` key + `loop --mode
   autonomous` gate-collapse + the NEW LLM `needs-human` resolution stage +
   truly-unresolvable escalation + per-decision audit journal, composing the
   shipped valve/escalation/cost-gate machinery. Sequence the auto-admit slice
   around `livespec-nrdk` (factory-safe admission gate; design.md §9). Gate: O1
   (met). Refresh `bd-ib-82a`'s stale v025 spec pointer to v033 as it opens.
2. **C2 — console command foundation.** Add the five `work_item.*` valve/policy
   `CommandType` variants + handlers + a port onto the orchestrator's published
   `drive` action surface + the Scenario-11 test (TDD, console Red-Green ritual).
   Folds `pke3y3` (regroom against the current valve model — MAINTAINER-OWNED
   cut). Gate: C1's MAIN ratification (met). Runs concurrently with O2.
3. **Persistence-seam amendment (console, now I1-unblocked).** File the small
   console propose-change that drops/derives the console's own
   `livespec-console-beads-fabro.autonomous_mode.enabled` block so ONLY the
   orchestrator's `dispatcher.autonomous_mode` key persists (the C1 persistence
   portion deferred to I1; O1 froze the arming contract at v033). Route
   propose-change → independent read-only Fable review → revise, and per the
   PROCESS NOTE at top carry the `tests/heading-coverage.json` clause-rebinding +
   `console-spec-check` ground-truth co-edit in `resulting_files`. Gates C3.
4. **C3 — console autonomous feature.** Gate: C1 + C2 + I1 (I1 met; needs C2 +
   the persistence-seam amendment). Build `config.autonomous_mode_set` +
   `.livespec.jsonc` persistence/audit + `factory.autonomous_mode_*_requested` +
   TUI toggle/confirm-modal/dangerous-label/header + the Scenario-10
   enable/observe/reflect/escalate loop (NOT a console-side resolver — the engine
   owns resolution, per the ratified delegation re-scope).
5. **I2 — end-to-end live exercise (MVP "done").** Gate: C3 + O2 AND the
   design.md §9 operability conditions (verified cost ceiling + a real
   failure-surfacing path — note orchestrator bug `bd-ib-18r`: an in-loop park
   today orphans without ledger write-back, so I2's truly-unresolvable plant
   must be ledger-level or `bd-ib-18r` triaged first).
6. Every spec change routes propose-change → independent read-only Fable review →
   revise; core H2 changes co-edit `tests/heading-coverage.json`; CONSOLE
   normative-clause changes carry the clause-rebinding co-edit (PROCESS NOTE).
   Ratification is DRIVER-held: a delegate FILES + halts; the driver runs the
   Fable review and dispatches the revise on a NO-BLOCKERS verdict.

## Delegation model (design.md §8)
Driver + per-repo delegate contexts; the driver dispatches each delegate as a
scoped subagent (NOT a tmux pane — that mechanism is retired). Delegate contexts
are named for their repo so cross-plan status references resolve.
- Driver: Claude session `autonomous-mode` (cwd `/data/projects/livespec`) — owns
  the plan, gates, dispatch, synthesis, and the ratification review gate.
- Delegate `console-autonomous-mode` (cwd console repo) → C1/C2/C3.
- Delegate `orchestrator-autonomous-mode` (cwd orchestrator repo) → O1/O2.
- Reviewer: a FRESH Fable session per round for the Step-0 loop (review-AND-FIX —
  it lands its own fixes; no continuity with sessions whose fixes it reviews).
  For per-step ratification (C1/O1 etc.), the DRIVER spawns the read-only
  independent Fable review after a delegate files its propose-change.

## Ledger items in play (per repo tenant)
- Core: `livespec-bvuy4w` — this thread's epic anchor (driver filed it
  2026-07-10 via the `capture-work-item` operation, closing the round-2
  finding; epic-shaped → `backlog` per the intake Definition-of-Ready
  checklist; edges: `livespec-nrdk` blocks, `livespec-0jxs` related — bd
  refuses an epic→task `blocks` edge by design, so the task dependency
  carries a `related` edge instead).
- Console: `rt4` (operator surface → C3; version pointer refreshed v013→v016 during C1, but its description substance still reads pre-re-scope — refresh at C3 grooming), `pke3y3` (epic, "7 unimplemented commands" — regroom + split for C2, maintainer-owned cut), `ipi` (attention-stream TUI migration), `mb64bv` (chore: backlog-bounce vocab rename — verify the rename target against the orchestrator's actual journal field `bounced_to_regroom` before landing).
- Orchestrator: `bd-ib-82a` (the engine → O2; stale v025 pointer — refresh to v033 when O2 opens).
- Core deps TRACKED not re-owned: `livespec-nrdk` (factory-safe admission gate), `livespec-0jxs` (operability preconditions); orchestrator `plan/fabro-token-refresh` (long-run publish robustness); orchestrator bugs `bd-ib-18r` / `bd-ib-6vu` (unattended-run robustness — sequence around).

## Key cross-repo risks (design.md §6) — ALL THREE now RESOLVED by O1/C1 ratification
1. Persistence-model seam: RESOLVED at O1 v033 — the arming contract pins the
   orchestrator `dispatcher.autonomous_mode` key as the single persistent
   permission, the console factory-drain path as launcher, and `loop` (not
   `drive`) as the `--mode autonomous` surface. (Residual: the console still
   drops/derives its own duplicate block — the I1-unblocked persistence-seam
   amendment, Next actions step 3.)
2. Division of resolution: RESOLVED at C1 v017 — the Scenario-10 re-scope makes
   the engine own ALL gate resolution; the console enables/observes/reflects; the
   double-resolution race is explicitly killed (console-side resolver deferred).
3. Vocab drift: RESOLVED at C1 v017 — all four citation sites swept
   (`orchestrate`/`orchestrate run` → `drive`; lane-vocab ownership → orchestrator).

## Next action
Build phase is PAUSED at the maintainer's request (2026-07-10). Resume order
(Next actions above): O2 (groom `bd-ib-82a` WITH the maintainer, then build) and
C2 (console command foundation) run concurrently; the I1-unblocked console
persistence-seam amendment can land in parallel; C3 then needs C1 + C2 + I1; I2
is the MVP live-exercise gate. Both grooming cuts (`bd-ib-82a`, `pke3y3`) are
maintainer-owned — set them up, do not auto-slice. O1 (orch v033) and C1 (console
v017) are RATIFIED (Ratification record at top); I1 is satisfied.

## Pointers
- Ledger read (per tenant): `bd list --json` (or `bd show <id> --json`) run from
  inside the repo, via the credential wrapper
  `/usr/local/bin/with-livespec-env.sh -- bd …`; prefer it over the shared
  `list_work_items.py` cache path, which can mis-resolve the tenant.
- Repo mutation: worktree → PR → merge → cleanup; `mise exec -- git …`; never `--no-verify`; plan docs are `docs(plan):` commits.
