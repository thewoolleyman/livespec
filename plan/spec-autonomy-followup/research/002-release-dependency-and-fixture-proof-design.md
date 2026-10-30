# 002 — Release dependency and fixture-proof design

Written 2026-10-30 by Claude Code session `ce19c72a-238e-4973-bbde-0a4f85197eb8` (plan owner), after the
first four of the five carrier children merged.

## What merged

All four were dispatched through `drive impl:<id>` and merged with the post-merge janitor green.
I read each diff myself.

| Plan assertion | Repo | Work-item | Pull request | Merge commit |
|---|---|---|---|---|
| 1 | `thewoolleyman/livespec` | `livespec-hitmrz` | #2996 | `c967cbe5` |
| 2 | `thewoolleyman/livespec-driver-pi` | `livespec-driver-pi-4q5bnp` | #420 | `de7f2d02` |
| 2 | `thewoolleyman/livespec-driver-codex` | `livespec-driver-codex-nzyruz` | #874 | `86a5cdb` |
| 2 | `thewoolleyman/livespec-driver-claude` | `livespec-driver-claude-dyvp2j` | #929 | `2d95e7b` |
| 3 | `thewoolleyman/livespec-orchestrator-beads-fabro` | `bd-ib-wlizdf` | (in flight) | — |

## The release dependency

Plan assertions 1–3 say "released". Every merge above landed as a `docs(...)` commit. Each repo's
`release-please-config.json` releases only on `feat`, `fix`, `perf`, `revert` and `refactor`
(plus `deps` in `livespec-orchestrator-beads-fabro`), so NONE of these merges cut a release by
itself. The plugins install from each repo's `release` ref, so an installed surface keeps the old
wording until that repo's NEXT releasing commit.

Decision: wait for organic releases rather than push an empty `fix:` commit to force one. A
manufactured releasing commit would misdescribe the change log, and the fleet's other lanes
produce releasing commits routinely. If a repo has not released by the plan's deadline
(2026-10-31T18:00Z on the epic's pointer budget), the remedy is to surface that one repo to the
coordinator, not to forge a commit.

Verification once released: read the plugin cache for the version named in the session's startup
output (not a filesystem glob over the cache; see `.ai/verifying-against-the-right-source.md`) and
confirm each changed sentence is present.

## Fixture-proof design (plan assertions 4 and 5)

There is no canary repository in the fleet, so the fixture is a scratch governed project built for
this proof and thrown away afterwards. It is never registered in the fleet manifest.

1. Create a scratch git repository outside `/data/projects` (the session scratchpad).
2. Seed it with core's `seed` operation and the `livespec` template.
3. Commit a `.livespec.jsonc` with `revise_decision_mode: delegated`, `ratification_review:
   manual-spawn` (deliberately, so the proof also exercises the rule that delegated mode
   auto-spawns the reviewer anyway), and `ratification_reviewer_model: ["sonnet"]`.
4. Enable the RELEASED core and Claude Driver plugins at project scope with a committed
   `.claude/settings.json` (`ref: release`) plus `claude plugin install ... -s project`, and
   verify the install record's `projectPath` equals the fixture root.
5. File three proposals with `propose-change`:
   - **A** — a plain non-drift wording change with no `decision_policy` (delegated-eligible);
   - **B** — the same shape with `decision_policy: manual` (manual control);
   - **C** — a drift-origin proposal (core floor; must never be decided by `revise_decision_mode`).
     "Drift origin" is NOT a front-matter field: the driver asserts it in the revise payload as
     `revise_decision_context.drift_origin: true`, and the revise CLI
     (`.claude-plugin/scripts/livespec/commands/_revise_decision.py`) refuses with
     `revise: human decision input required: ...` unless `human_decision_confirmed` is also true.
     So C is exercised at two layers: the driven session must stop for the maintainer, and a
     direct CLI invocation with the flag set and no confirmation must exit with that refusal.
6. Run one bounded, explicitly initiated, non-interactive revise per topic
   (`claude -p "/livespec:revise --only-topic <topic>"` with a wall-clock timeout).
7. Observe:
   - **A** produces a new `history/vNNN/` revision whose ratification evidence carries `NO BLOCKERS`
     from a separately spawned reviewer and a delegated-decider acceptance, both naming the same
     canonical final-bytes digest; the run asked the user nothing.
   - **B** and **C** each stop for explicit maintainer confirmation, and no revision is written for
     either.
8. Post the steps and observed output as a `captured` plan Proof of Done record; a DIFFERENT
   session replays them for `verified`.

Spend: three short headless sessions plus one reviewer spawn and one decider spawn per accepted
proposal — well under one factory run.
