# rop-sweep-fleet-policy — RULING RATIFIED (v169, LIVE ON MASTER). Next: unblock dispatch, then the 10 slices

**Read this whole file before acting.** The ROP ruling is SETTLED and RATIFIED — v169 is
merged and live on master (livespec commit `2288197b`, PR #1424); the proposal is consumed
from `SPECIFICATION/proposed_changes/`. **Do NOT re-ratify it.** What remains is execution.
Status is READ from the ledgers (`bd`), never stored here. Ledger note on epic
`livespec-y2lkf4` carries the consolidated state; per-item notes carry review blockers and
evidence.

## START HERE — first three moves, in order

1. **Check whether the two maintainer blocks below cleared.** Probe the credential by
   dispatching `bd-ib-47gr` (it is already `ready`); if it fails at `run-config-overlay`
   again, dispatch is still down and you should NOT keep retrying — report and work the
   unblocked items instead.
2. **If dispatch works:** land `bd-ib-47gr`, then run ONE combined dual review over
   `bd-ib-sw0i` + `bd-ib-47gr` (see HELD below — `sw0i` needs it on two counts).
3. **If dispatch is still down:** everything factory-side is blocked. The unblocked work is
   the two P1 dev-tooling gate fixes (`qm5`, `6vz`), which are ordinary worktree→PR→merge
   changes needing no dispatcher.

Nothing is running from the prior session: no dispatches, no monitors, no sub-agents. The
`rop-drain` tmux socket is empty. Every worktree and branch that session created is cleaned up.

## ⛔ BLOCKED ON THE MAINTAINER — two things, both outside agent reach

1. **`codex login` on the orchestrator host.** Factory dispatch is DOWN. `bd-ib-47gr` failed at
   `run-config-overlay` with *"Host Codex credential is too short-lived for the run budget; run
   `codex login` on the orchestrator host to renew it."* Every further `drive impl` will fail the
   same way. The item was left stranded `active` and has been moved back to `ready` via the
   sanctioned `move:` valve (safe — it never reached a merge, so re-dispatch rebuilds nothing).
2. **`livespec-giq7` (P0)** — the tmux guard fix is merged AND released
   (`livespec-driver-claude` v0.4.2) but NOT rolled out. Per
   `~/.claude/plugins/installed_plugins.json`, every project EXCEPT `/data/projects/livespec` is
   bound to a pre-fix plugin cache copy whose guard **fails open**. Remedy is
   `claude plugin update livespec@livespec-driver-claude -s project` per project + reload. NOT
   done unilaterally: it mutates the environment of other live agent sessions on this host.

## ⛔ Guards
- **DO NOT run `groom livespec-y2lkf4`** (the EPIC). Already decomposed; individual-child
  `groom <id>` is fine.
- **DO NOT accept any work-item** without BOTH a separate Codex reviewer AND a separate Opus
  reviewer clearing it. This has repeatedly caught defects every mechanical gate passed.
- Dispatch DETACHED only; a killed foreground dispatch strands the item `active`.
- **Detached tmux dispatches are NOT harness-tracked.** Arm a `Monitor` (watch for the `__EXIT=`
  marker AND for the tmux session vanishing without one) or you will wait forever on an event
  that cannot fire.
- **A correction note on a work-item does NOT reach an already-dispatched agent.** Once
  dispatched, the brief is frozen. Let it complete and reject, or stop it — do not append-and-hope.
  This exact mistake produced a defective guard (`bd-ib-ug4z`).

## THE RULING — ratified, v169

`SPECIFICATION/proposed_changes/rop-broad-except-boundary-rule.md` was ACCEPTED into v169 and
is MERGED (livespec PR #1424, commit `2288197b`): 16 edits across
`non-functional-requirements.md`, `constraints.md`, `contracts.md`. The proposal file is gone
from the pending queue and now lives at `SPECIFICATION/history/v169/proposed_changes/`. It grew
5 → 16 edits over SIX independent review rounds (blockers per round: 5, 4, 2, 2, 0). Landed via
PRs #1400, #1405, #1407, #1416, #1420, #1421, then ratified by #1424.

**narrow at the seam; broad only at the boundary; at most one boundary per process.**

STYLE B (`livespec-orchestrator-git-jsonl`'s `io/store.py`) is the fleet standard. A hand-rolled
`except Exception` returning `Failure(exc)`/`IOFailure(exc)` is the blanket `@safe`/`@impure_safe`
form the spec ALREADY forbids, written longhand — the container does not change what the catch
is. *"It lifts onto the IO rail"* is not a defense; that argument was raised, adjudicated, rejected.

The five sanctioned `# noqa: BLE001` markers (em-dash), a CLOSED set:
```
— sole supervisor bug-catcher: log traceback, exit 1
— sole fail-open hook boundary: silent pass-through, exit 0
— sole fail-closed guard boundary: deny per policy, exit 0
— sole loop-iteration bug-catcher: log traceback, continue
— foreign-code isolation: <surface> crash captured as <ErrorType>, reported
```
`sole` scopes per process entry artifact for the three boundary markers, per SUPERVISION LOOP for
the loop-iteration marker. Foreign-code markers are not `sole` markers.

**The ruling is already baked into all 10 STEP 3 slice work-items** as a ledger note, including
the failure modes below. Do not re-derive it.

## DONE — accepted, dual-reviewed, live-exercised

| Item | Repo | PR |
|---|---|---|
| `livespec-driver-codex-64s` | livespec-driver-codex | #199 |
| `livespec-driver-claude-hfm` | livespec-driver-claude | #219 |
| `livespec-driver-claude-ob3` | livespec-driver-claude | #215 |
| `bd-gj-li0` | livespec-orchestrator-git-jsonl | #341 (+#343) |

## HELD — `bd-ib-sw0i`, on TWO counts

1. **Journal-deletion blocker.** `_dispatcher_reconcile_merged.py:75-78`'s ambiguous-PR refusal
   calls `_remove_journal(path=journal.path)` on the SHARED cross-item dispatch journal
   (`repo/tmp/fabro-dispatch-journal.jsonl` — the same default the loop appends to for every
   item). So reconcile against item B deletes in-flight records a live dispatch is writing for
   unrelated item A. This is the SAME bug class the work-item exists to close, relocated from
   worktree-deletion to journal-deletion, and it violates its own "evidence-journaling must stay
   intact" constraint. The giveaway: the `merged is None` branch two lines below deletes nothing.
   Fix filed as **`bd-ib-47gr`** (ready, blocked on `codex login`).
2. **Missing second verdict.** Only the Codex reviewer delivered. The Opus reviewer went idle
   three times without producing a verdict despite two follow-ups. The dual-review precondition
   is NOT met.

**When `47gr` lands, run ONE combined dual review over `sw0i` + `47gr`** rather than reviewing
`sw0i` now — `47gr` changes the file under review, so a review today reviews superseded code.

## STILL STRANDED BY DESIGN — `livespec-ftbvgc`

Core's `BLE` add merged (livespec PR #1381) but the item is stuck `active`. Root cause: the only
`active → acceptance` write is `complete_and_accept` (`_dispatcher_completion.py:89`, status
write `:111`), whose sole caller is `post_run_dispositions`
(`_dispatcher_loop_selection.py:137`) — that transition lives ENTIRELY inside the dispatching
process, so ANY death of it after merge strands the item.

**Do NOT hand-close it, and do NOT run the reconcile valve on it until `bd-ib-47gr` lands** —
the race is closed for the worktree but still open for the journal.

## NEXT — the 10 groomed slices (backlog; ruling already baked into each)

`livespec-apiiwc` and `livespec-qgp2jt` are blocked/superseded; do not dispatch them whole.
- **livespec-runtime**: `livespec-4nlb` (**ANCHOR**), then `livespec-p41z`, `livespec-shz8`,
  `livespec-0bpr`.
- **livespec-dev-tooling**: `livespec-h2hs` (**ANCHOR**), then `livespec-9cts`, `livespec-ss2j`,
  `livespec-5dpg`, `livespec-tvlq`, `livespec-gcsn`.

Anchors first (they vendor `returns` + enable `BLE` repo-wide), then the rest in parallel.
Cross-tenant rule applies: these live in the **livespec** tenant but target siblings, so each
needs a dispatch-mirror in the target repo's tenant.

**`livespec-shz8` carries a cross-repo obligation** — see its ledger note. When it moves the
`WorkItemStore` protocol to `IOResult`, git-jsonl's deliberately-tracked divergence resolves and
its tracking test will fail BY DESIGN. File the paired git-jsonl repair BEFORE landing `shz8`.

## OPEN FOLLOW-UPS

| Item | Repo | Pri | What |
|---|---|---|---|
| `livespec-giq7` | livespec | **P0** | Guard fix released but not rolled out (see top) |
| `bd-ib-47gr` | livespec-orchestrator-beads-fabro | P1 | Shared-journal deletion; ready, blocked on credential |
| `livespec-dev-tooling-qm5` | livespec-dev-tooling | P1 | `no_except_outside_io` no-ops when `io_trees` unset. **Brief CORRECTED — breadth, not position** |
| `livespec-dev-tooling-6vz` | livespec-dev-tooling | P1 | `no_raise_outside_io` hardcodes core's four error names → vacuous everywhere else |
| `livespec-dev-tooling-jjb` | livespec-dev-tooling | P2 | Mechanize cardinality + marker wording (the ratified spec says these are review-enforced today) |
| `livespec-dev-tooling-bbl` | livespec-dev-tooling | P2 | Make the canonical no-shadow-ledger body type-checkable so both Drivers drop pyright carve-outs |

## TWO VACUOUS GATES — do NOT trust either

Both report green while enforcing nothing. Verified directly:
1. `check-no-except-outside-io` returns 0 immediately when `io_trees` is unset — which is the
   case in BOTH Driver repos, i.e. exactly the repos whose hooks drifted (`qm5`).
2. `check-no-raise-outside-io` hardcodes `_DOMAIN_ERROR_NAMES` to core's four names; a repo whose
   errors are named differently gets zero coverage. Instrumented against git-jsonl it flagged 0
   of 9 raises including a genuine outside-`io/` one (`6vz`).

This one distorted a real design decision: the choice between restoring protocol conformance and
tracking the divergence was argued partly on whether unwrapping would trip that check. It
wouldn't have.

## WHAT THE REVIEW GATE CAUGHT (do not weaken it)

Every finding below passed all mechanical gates:
- **The tmux guard failed OPEN** while its comment claimed fail-closed — on the guard that exists
  to stop the agent-caused fleet kill that happened the same day.
- **The reconcile valve could clobber a live dispatch**, causing the very stranding it prevents.
- **Its replacement guard was INERT** — gated on a heartbeat that is silent in exactly the
  contested window, so it waved every caller through while looking like protection.
- **Then the fix for THAT relocated the same bug** from worktree-deletion to journal-deletion.
- **A proposed spec edit re-asserted a FALSE enforcement claim** while claiming to make spec and
  code agree.
- **Two tests were inert** — one guarded behind `hasattr` on a symbol its own PR deleted, so it
  passed against a reintroduced fail-open.
- **Two of six spec review rounds found blockers introduced by the previous round's fix.**

## MECHANICS (hard-won — do not rediscover)

- **These repos REBASE-merge.** A "merge SHA" is a span tip, not a two-parent merge commit;
  `git show <tip>` reviews only the last commit — in one case an entirely unrelated commit.
  Resolve `base..head` via `gh pr view <n> --json commits,baseRefOid,headRefOid,additions,deletions,changedFiles`
  and cross-check totals. **Brief every reviewer with this.**
- **A `--force-with-lease` "stale info" rejection is ambiguous** between your own merged-and-deleted
  branch and a peer's push. STOP and investigate; never force blind.
- **PRs here merge fast.** Land corrections as FRESH branches off current master, not amendments.
- **Require reviewers to verify by EXECUTION**, not reading — revert the impl, watch the test
  fail, report the output. That framing caught the inert guard, the inert tests, and the journal
  deletion; a structural read passed all three.
- **A test-only brief must NOT demand Red-Green-Replay** — no impl to add at Green. Use the
  established `TDD-Suite-Green-*` shape.
- **`status` is a read-only variable in zsh** and will silently kill a `Monitor` script.
- **Do NOT read a local agent's `.output` file** — it is a symlink to the full subagent transcript
  and will overflow context. Use the agent result or `SendMessage`.
- **Spec edits go through `/livespec:propose-change`**, never a direct edit backfilled by doctor.
  PR #797 did the latter and doctor SELF-ACCEPTED the drift (`author_llm: livespec-doctor`),
  bypassing the never-self-waived independent-review rule. Put this line in every dispatch brief.
- All `bd` calls go through `/data/projects/1password-env-wrapper/with-livespec-env.sh`. The
  `auto-backup failed … command denied` warning is correct-by-design.

## CORRECTIONS TO EARLIER FINDINGS (do not re-derive the wrong conclusion)

- **`no_shadow_ledger.py` is NOT "a bypass in both Drivers".** Neither Driver owns it — the single
  source is `livespec_dev_tooling.install_no_shadow_ledger.CANONICAL_NO_SHADOW_LEDGER_BODY`,
  installed via `just install-no-shadow-ledger` and guarded byte-identical by
  `check-no-shadow-ledger-body-identical` (exit 4 on drift). Editing it in a Driver is FORBIDDEN.
  livespec-driver-claude's pyright carve-out is documented and principled
  (`pyproject.toml:280-292`); only livespec-driver-codex's is undocumented. The body also carries
  bare `dict`/`list` annotations failing strict pyright, so a one-line fix is insufficient. Real
  fix: `livespec-dev-tooling-bbl`.
- **The heartbeat probe is the WRONG fix for the reconcile race.** `post_merge` runs AFTER the
  Fabro run completes and the heartbeat is fed DURING it, so the probe is silent in exactly the
  contested window and returns a false "dead" verdict.
- **`BLE001` markers in both Drivers' hook trees are DECORATIVE** — those trees are
  `extend-exclude`d from ruff, so `BLE001` never fires. `livespec-dev-tooling-jjb` must add a
  POSITIVE AST guard, not merely remove a carve-out.

## Close-out

When all children + slices are `done`, epic `livespec-y2lkf4` closes and this thread archives to
`plan/archive/rop-sweep-fleet-policy/`.
