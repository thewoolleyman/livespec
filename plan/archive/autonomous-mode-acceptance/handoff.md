# autonomous-mode-acceptance — handoff (ARCHIVED — acceptance COMPLETE)

**ARCHIVED 2026-07-20. The acceptance was performed and the epic is closed.
Nothing here is pending.** The body below is the pre-run charter, kept verbatim
because it defines the bar that was met; read this header first, because the
charter's "NEXT ACTION" is settled and would otherwise misdirect you.

**What happened.** Two REAL fleet work-items were driven end-to-end SOLELY
through the live console TUI and accepted with the `c` valve:

| Item (`livespec-console-beads-fabro` tenant) | PR | Final |
|---|---|---|
| `-5kd56a` — re-key the completeness staleness stamp to a digest of the orchestrator's declared key set | #337 merged | CLOSED |
| `-7rcps4` — work-item modal PgUp/PgDn pages by a hardcoded 10 rows | #338 merged | CLOSED |

Every operator action was performed in the TUI — approve (`p`), dispatch
(`:`→`drain`), move (`s`), accept (`c`). The CLI was used only to READ state and
to file defects. The full live-exercise evidence is journaled on epic
`livespec-j4odoz` in three increments; that ledger record, not this file, is the
authoritative account.

**The run had to repair the factory to finish**, which is the part worth
remembering. Three findings were blocking preconditions, not incidental defects:
`-8i9` (the dispatcher never read a consumer repo's own Fabro workflow, so every
dispatch into a Rust repo ran in a Python-only sandbox — the dark factory was
structurally dark for the ENTIRE RUST TENANT CLASS), `-m36` (the TUI drain was
once-per-store forever, and this store's one drain was already spent on a failed
run), and the live verification of PR #258's repeat-move fix, which no automated
gate can perform because the interactive loop is `#[cfg]`-excluded from tests.
Both defects were fixed, released, installed, and verified live during the run.

A weaker acceptance — a throwaway item, or a CLI fallback when the TUI balked —
would have reported success with all three still hidden. That is the argument for
the bar's strictness, and it is the reason to resist softening it if this
programme is ever re-run.

**11 defects filed**, all in the `livespec-console-beads-fabro` tenant. Two fixed
(`-8i9`, `-m36`). The most operationally significant one still open is **`-htp`**:
the drain shells the dispatcher INLINE on the UI thread, so the cockpit freezes
for the SUM of every dispatched item's runtime (42+ minutes measured; ~3 hours at
`wip_cap 5`). It BLOCKED THE ACCEPT ITSELF during this run, and it is inescapable
— the dispatcher is a CHILD PROCESS of the console, so restarting the cockpit to
regain input would abort in-flight factory work.

**The accept was delegated.** The charter below says the final `c` accept is the
maintainer's and must not be self-performed. Mid-run the maintainer delegated it
("you accept and do everything on my behalf"), and the epic's close reason records
that the designed human gate was satisfied by that delegation rather than skipped.

---

**Ledger anchor:** epic `livespec-j4odoz` (livespec CORE tenant) — CLOSED.
**Opened:** 2026-07-19, splitting the retired `plan/autonomous-mode/` thread.

Status is READ from the ledger, never stored here. This file carries no
checkbox queue and no session log — the thread this replaced failed largely by
accreting both.

**Composing status.** Operations named here are skills of the
`livespec-orchestrator-beads-fabro` plugin — invoke as
`/livespec-orchestrator-beads-fabro:<operation>` (`list-work-items`, `next`,
`groom`, `drive`). Each repo is its own beads tenant and the read surfaces
resolve the tenant from the working directory, so read a non-core tenant by
running from that repo's clone (`/data/projects/<repo>`).

## Read-first chain

1. This file.
2. `plan/archive/autonomous-mode-acceptance/research/live-tui-findings.md` — the
   live-TUI findings and the POST-FIX VALIDATION RUNBOOK from the last
   acceptance attempt. It moved here from the superseded thread; this thread
   owns it.

That is the whole chain.

## The objective

A human flips per-repo autonomous mode from the console TUI, and the Beads/Dolt
+ Fabro factory drives ready work to `done` unattended — LLM-resolving the
human gates, auditing every decision, surfacing only the truly-unresolvable
back to the operator.

**Everything is built.** Orchestrator O0–O10 shipped (releases through 0.43.0);
console C1–C3 shipped; cockpit behaviours B1–B5 shipped and two-repo
live-verified. The one step never performed is the final acceptance — called
"Stage-2" or "I2" in the retired thread.

## What acceptance means — the bar

Drive **MULTIPLE REAL fleet work-items end-to-end SOLELY through the live
console TUI**, parking them in `acceptance`, ending with the maintainer's final
`c` accept via the TUI.

**It is explicitly NOT satisfied by what has been done so far.** One `c` accept
was performed, on a THROWAWAY item (`bd-ib-dqt`). That proved the accept
MECHANISM fires — valve fired, item closed, reflected live in the cockpit
Events stream — and nothing more. Real fleet items, driven the whole way, is
the bar.

This matters because of the fleet's completion rule: *"done means rolled out
and exercised live — never merely merged + CI-green + AI-accepted."* This
acceptance is what makes the autonomous-mode programme done.

## How to run it

**Launch.** A tmux session named EXACTLY `console-autonomous-mode` (so the
maintainer can attach and watch), one pane per repo tenant when overseeing more
than one. Build the console binary (`just build-release` in
`/data/projects/livespec-console-beads-fabro`), then run it under the
credential wrapper FROM THE TARGET TENANT'S cwd so it targets that tenant:

```
cd /data/projects/<target-repo>
with-livespec-env.sh -- /data/projects/livespec-console-beads-fabro/target/release/livespec-console-beads-fabro serve
```

**Dispatch discipline — carried from the retired thread, do not rediscover.**
Dispatch PER ITEM; never a bare drain. Since the O2 work landed, the dispatcher
drains by default, so a bare drain will pull work you did not intend into the
acceptance run.

**Drive through the TUI, not the CLI.** Any operator-steering action you cannot
cleanly drive through the TUI is a **USABILITY HOLE** — log it and route it to
the maintainer for a fix discussion. Do NOT silently fall back to the CLI.

### The scope boundary — what is a hole vs. by-design CLI

Maintainer-declared and CORRECTED 2026-07-12. Almost everything is
TUI-drivable, because almost everything is a groomed work-item the factory
runs, and the operator drives/observes the factory from the cockpit.

**Drive via the factory → TUI; a gap here IS a usability hole:**
- Watching each track's ledger / factory / needs-attention state.
- Flipping autonomous mode on/off.
- Per-item valves: approve / accept / reject / set-admission / set-acceptance.
- Draining the factory; observing auto-resolutions reflected.
- Triaging a truly-unresolvable needs-attention item.
- **Code fixes and PR authoring + merge** — as groomed work-items dispatched
  through the factory; the operator dispatches/observes/valves from the cockpit.

**Off-factory / CLI — the NARROW documented exception, NOT a hole:**
- Repo/dev-tooling PLUMBING unsafe to self-run through the factory (the factory
  substrate itself, the commit-refuse hooks, the dispatch machinery).
- Spec ratification keeps its DESIGNED human gate (independent Fable review +
  the maintainer's accept), and grooming is a maintainer-owned cut. Deliberate
  human touchpoints, not holes.

If a deliverable "can't" be a factory work-item, that is a smell — re-groom it
until it can, or confirm it is the narrow plumbing exception.

## NEXT ACTION

**Ask the maintainer whether the acceptance run may start now.**

The retired thread carried "Stage-2 LAST" as its ordering — after the console's
B6/B7/B8 and E2E backfill. That was **maintainer-declared programme order, not
a hard technical dependency**: B1–B5 and the full valve surface are shipped and
live-verified, so the TUI can already drive an acceptance run. Whether to wait
for the docs and release capstone is the maintainer's call, and it is the one
question blocking this thread.

If cleared to proceed: self-validate first (drive items yourself end-to-end,
journal live-exercise evidence on each), then present the final `c` accept to
the maintainer. **Do not perform the final accept yourself** — it is the
maintainer's step, and it is the acceptance.

## Deliberately NOT owned here

- **The console cockpit programme.** `livespec-console-beads-fabro:plan/cockpit-ux-docs-release/`
  owns B6 (user-docs tree), B7 (key-by-key walkthrough), the B8 release
  capstone remainder, and the real-TUI E2E backfill. The thread this replaced
  duplicated that programme's tracking, and that duplication caused a
  lost-pointer crisis. **Do not re-home any of it here.** Reference it; never
  copy its state.
- **The superseded thread's cleanup.** Already DONE 2026-07-19, not a pending
  task: `plan/autonomous-mode/handoff.md` was collapsed 3220 → ~280 lines
  (its cited design record preserved verbatim in place, so the three live-spec
  citations still resolve), its `design.md` and review-loop research removed,
  and the orchestrator's stale sibling thread archived. Nothing is owed there.

## Implementation route

Any ledger-backed work this thread files is built **factory-side**: dispatch
via the `drive` operation (`impl:<work-item-id>`) or let the Dispatcher drain
it once `ready`. Do NOT hand-code in a planning session and do NOT use the
in-session Red→Green `implement` operation.

The acceptance RUN itself is the exception by nature — it is a human-gated
operator exercise, not a dispatchable work-item.
