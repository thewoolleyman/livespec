# rop-sweep-fleet-policy — EXECUTING. Critical path: ratify the 13-edit proposal, then the 10 slices

**Read this whole file before acting.** The Fable ROP ruling is SETTLED and its prose is
filed as a pending proposed change; the blocker is now ratification, not design. Status is
READ from the ledgers (`bd`), never stored here. Ledger note on epic `livespec-y2lkf4`
carries the maintainer decisions; per-item notes carry the review blockers and evidence.

## ⛔ Guards
- **DO NOT run `groom livespec-y2lkf4`** (the EPIC). It re-decomposes + closes; the epic is
  already decomposed. Individual-child `groom <id>` is fine.
- **DO NOT accept any work-item** without BOTH a separate Codex reviewer AND a separate Opus
  reviewer clearing it (maintainer rule, 2026-07-19). This has paid for itself repeatedly —
  see "What the review gate caught" below.
- **DO NOT ratify a proposal without a NO-BLOCKERS independent review of the CURRENT text.**
  Three review rounds have each found real defects, including one introduced while fixing the
  previous round's.
- Dispatch DETACHED only. A killed foreground dispatch strands the item `active` — that is
  the `livespec-ftbvgc` bug, still unfixed.
- **Detached tmux dispatches are NOT harness-tracked.** No completion notification arrives.
  Arm a `Monitor` on the log (watch for the `__EXIT=` marker AND for the tmux session
  vanishing without one), or you will wait forever on an event that cannot fire.

## Maintainer decisions (binding)
1. **Railway scope** = convert ONLY the **expected-failure paths** (I/O, subprocess, network,
   parsing, error-handling) to the `returns` railway + vendor `returns` + enable ruff `BLE`
   and pyright `reportUnusedCallResult`. Do NOT rewrite pure-transform functions.
2. **Grooming** = decompose large children autonomously, no approval gate. (DONE.)
3. **Accept gate** = the agent runs `drive --action accept:<id>`, but ONLY after a separate
   **Codex** reviewer AND a separate **Opus** reviewer both clear the merged PR.
4. **The full-ROP bar DOES reach `.claude/skills/` host tooling** (2026-07-19). The overseer
   is being productized under the `overseer-productization` thread.
5. **`io_trees`-unset semantics: the SPEC is the intent, fix the check** (2026-07-19).
   `no_except_outside_io` must not no-op when `io_trees` is unset.
6. **Ratify-and-fix in parallel** (2026-07-19) — remediation does not wait on ratification.

## THE RULING (settled; this is the design, ratification is bookkeeping)

One sentence: **narrow at the seam; broad only at the boundary; at most one boundary per
process.** STYLE B (`livespec-orchestrator-git-jsonl`'s `io/store.py`) is the fleet standard.
A hand-rolled `except Exception` returning `Failure(exc)`/`IOFailure(exc)` is the blanket
`@safe`/`@impure_safe` form the spec ALREADY forbids, written longhand — the container the
catch returns does not change what the catch is. "It lifts onto the IO rail" is not a defense.

Five sanctioned `# noqa: BLE001` markers (em-dash), a CLOSED set:
```
— sole supervisor bug-catcher: log traceback, exit 1
— sole fail-open hook boundary: silent pass-through, exit 0
— sole fail-closed guard boundary: deny per policy, exit 0
— sole loop-iteration bug-catcher: log traceback, continue
— foreign-code isolation: <surface> crash captured as <ErrorType>, reported
```
`sole` scopes per process entry artifact for the three boundary markers, per SUPERVISION LOOP
for the loop-iteration marker. Foreign-code markers are accounted per invocation surface and
are not `sole` markers.

## STEP 1 (CRITICAL PATH) — ratify the pending proposal

`SPECIFICATION/proposed_changes/rop-broad-except-boundary-rule.md` on master carries **13
edits across 3 files** (`non-functional-requirements.md`, `constraints.md`, `contracts.md`).
It is PENDING — `/livespec:revise` has NOT run.

Landed so far: livespec PRs #1400 (initial 5 edits), #1405 (5th marker), #1407 (first 5
blockers), #1416 (next 4 blockers).

**Before ratifying:** confirm an independent Fable review of the CURRENT master text returned
NO BLOCKERS. If a review is still outstanding, wait for it. Then run `/livespec:revise`,
choosing accept for the single `rop-broad-except-boundary-rule` topic (decisions are
per-FILE, keyed on the file stem, not on a `## Proposal:` section name).

No `## ` heading changes across all 13 edits (verified by simulating the replacements), so
**no `tests/heading-coverage.json` co-edit is owed**.

## STEP 2 — the three original conversions (all still parked in `acceptance`)

| Item | Repo | PR | State |
|---|---|---|---|
| `livespec-driver-codex-96q` | livespec-driver-codex | #194 | held; its follow-up `-64s` is DONE |
| `livespec-driver-claude-7u7` | livespec-driver-claude | #210 | held; follow-ups `ob3`+`hfm` in `acceptance` |
| `bd-gj-hab` | livespec-orchestrator-git-jsonl | #335 | held; **not yet worked this session** |

`bd-gj-hab` is the untouched one. Its blockers: `store.py` `read/append → IOResult` broke the
shared `WorkItemStore` protocol and the PR **DELETED** the `_: type[WorkItemStore]`
conformance binding instead of reconciling; discarded `IOResult` in
`migration/beads_to_jsonl.py:74` and `migration/merge_evidence_backfill_core.py:81` (append
failures reported as success); stale docstrings. **Sequencing caution:** the protocol is
VENDORED from livespec-runtime, so git-jsonl cannot redefine it from downstream
(No-Circular-Dependency). Either restore the facade to protocol-conforming signatures now, or
sequence behind `livespec-shz8` (livespec-runtime `work_items/`). Recommend the former.

## STEP 3 — the 10 groomed slices (filed `backlog`, still HELD)

`livespec-apiiwc` and `livespec-qgp2jt` are blocked/superseded; do not dispatch them whole.
- **livespec-runtime**: `livespec-4nlb` (**ANCHOR**), then `livespec-p41z`, `livespec-shz8`,
  `livespec-0bpr`.
- **livespec-dev-tooling**: `livespec-h2hs` (**ANCHOR**), then `livespec-9cts`,
  `livespec-ss2j`, `livespec-5dpg`, `livespec-tvlq`, `livespec-gcsn`.

Land anchors first (they vendor `returns` + enable `BLE` repo-wide), then the rest parallel.
**Bake the ruling above into each brief** — the five markers, the breadth-not-position rule,
and the "no discarded Result" rule — so the factory implements to the right bar first time.

## STEP 4 — `livespec-ftbvgc` is STILL stranded, and that is correct

Core's `BLE` add merged (livespec PR #1381) but the item is stuck `active`. **Root-caused:**
the only `active → acceptance` write is `complete_and_accept`
(`_dispatcher_completion.py:89`, status write `:111`), whose sole caller is
`post_run_dispositions` (`_dispatcher_loop_selection.py:137`). That transition lives ENTIRELY
inside the dispatching process, so ANY death of it after merge strands the item — janitor
false-red, SIGKILL, host restart, timeout. The tracked bug `bd-ib-lza6`'s original
"janitor-failed" framing was too narrow; it has been retitled.

The reconcile valve was built (`bd-ib-lza6`, PR #797) but is **HELD** — see below. **Do NOT
hand-close `ftbvgc`, and do NOT run the valve on it until `bd-ib-ug4z` lands**, because
running it now is itself the race.

## Open work filed this session

| Item | Repo | Pri | What |
|---|---|---|---|
| `livespec-giq7` | livespec | **P0** | Guard fix merged+released but NOT rolled out; every project except `/data/projects/livespec` runs a fail-open `tmux_fleet_guard`. Needs `claude plugin update livespec@livespec-driver-claude -s project` per project + reload. NOT done unilaterally — mutates other live sessions. |
| `bd-ib-ug4z` | livespec-orchestrator-beads-fabro | P1 | reconcile-merged liveness race + the first-of-N title-search bug. **Brief was CORRECTED mid-flight — read its notes.** |
| `livespec-driver-claude-hfm` | livespec-driver-claude | P1 | Test-integrity repair. PR #219 merged, in `acceptance`. |
| `livespec-dev-tooling-qm5` | livespec-dev-tooling | P1 | `no_except_outside_io` must run when `io_trees` unset. **Brief CORRECTED — breadth, not position.** |
| `livespec-dev-tooling-jjb` | livespec-dev-tooling | P2 | Mechanize cardinality + marker-wording (currently review-enforced only). |
| `livespec-dev-tooling-bbl` | livespec-dev-tooling | P2 | Make the canonical no-shadow-ledger body type-checkable so both Drivers can drop pyright carve-outs. |

## What the review gate caught (do not weaken it)

Every round found real defects that all mechanical gates missed:
- **The tmux guard failed OPEN** while its comment claimed fail-closed — on the guard that
  exists to stop the fleet kill that happened *today*. `just check` was green.
- **The reconcile valve could clobber a live dispatch** and cause the very stranding it
  exists to prevent, via an unconditional `git worktree remove --force` on a shared
  deterministic path during a window up to ~2h20m.
- **A proposed spec edit re-asserted a FALSE enforcement claim** (`check-supervisor-discipline`
  polices only `sys.exit` confinement, nothing about catch-alls) while claiming to make spec
  and code agree.
- **Two tests were inert/vacuous** — one guarded behind `hasattr` on a symbol its own PR
  deleted, so it passed against a reintroduced fail-open.
- **A fix round introduced a new contradiction** that would have made the flagship
  STYLE-B artifact fail the check the same sentence mandated.

## Mechanics (hard-won — do not rediscover)

- **These repos REBASE-merge.** The "merge SHA" is the tip of a rebased span, NOT a two-parent
  merge commit. `git show <tip>` shows only the LAST commit's diff — often test-only, and in
  one case an entirely unrelated commit. Always resolve `base..head` via
  `gh pr view <n> --json commits,baseRefOid,headRefOid,additions,deletions,changedFiles` and
  cross-check your diff totals against the API. Brief every reviewer with this.
- **A `--force-with-lease` "stale info" rejection is ambiguous.** It looks identical whether
  your branch was deleted by its own merge or a peer pushed to it. STOP and investigate; never
  force blind. Both occurrences this session were the former, but the failure mode is a
  cross-session clobber.
- **PRs here merge fast.** Amending a pushed branch races the merge. Land each correction as a
  FRESH branch off current master rather than amending.
- **Cross-tenant rule: factory dispatch requires item-tenant == target-repo-tenant.** File a
  dispatch-mirror in the target repo's tenant and close BOTH on completion.
- **Detached dispatch:**
  `/usr/bin/tmux -L rop-drain new -d -s <name> "python3 <plugin-root>/scripts/bin/drive.py --action impl:<id> --repo <repo> --json > <log> 2>&1; echo __EXIT=\$? >> <log>"`
  Use `/usr/bin/tmux` directly and a SCOPED `-L` socket. `drive.py` self-wraps under the
  credential wrapper.
- **In a `Monitor` script, `status` is a read-only variable in zsh** — it will kill the
  monitor with exit 1. Use another name.
- **State machine**: `ready → active → acceptance → done`. Only a running dispatcher advances
  `active → acceptance`.
- All `bd` calls go through `/data/projects/1password-env-wrapper/with-livespec-env.sh`. The
  `auto-backup failed … command denied` warning is correct-by-design.

## Corrections to earlier findings (do not re-derive the wrong conclusion)

- **`no_shadow_ledger.py` is NOT a "bypass in both Drivers".** Neither Driver owns it. The
  single source is `livespec_dev_tooling.install_no_shadow_ledger.CANONICAL_NO_SHADOW_LEDGER_BODY`,
  installed via `just install-no-shadow-ledger` and guarded byte-identical by
  `check-no-shadow-ledger-body-identical` (exit 4 on drift). Editing it in a Driver is
  FORBIDDEN, not merely awkward. livespec-driver-claude's pyright carve-out is documented and
  principled (`pyproject.toml:280-292`); only livespec-driver-codex's is undocumented. The
  body also carries bare `dict`/`list` annotations that fail strict pyright, so a one-line fix
  is insufficient. Real fix: `livespec-dev-tooling-bbl`.
- **The heartbeat probe is the WRONG fix for the reconcile race.** `post_merge` runs AFTER the
  Fabro run completes, and the heartbeat is fed during that run — so it goes silent exactly in
  the contested window and would return a false "dead" verdict, green-lighting the clobber.
  Use a separate checkout path + a pid-bearing dispatch lock instead.
- **`BLE001` markers in both Drivers' hook trees are currently DECORATIVE.**
  `.claude-plugin/hooks/**` and `livespec/hooks/**` are `extend-exclude`d from ruff, so
  `BLE001` never fires there. The ROP state is correct but UNPROTECTED — tracked as
  `livespec-dev-tooling-jjb`, which must add a POSITIVE AST guard, not merely remove a
  carve-out.

## Process rule adopted this session

**Spec edits go through `/livespec:propose-change` — never a direct edit backfilled by
doctor.** PR #797 direct-edited `SPECIFICATION/contracts.md`; doctor detected the drift
afterward and SELF-ACCEPTED it (`author_human: livespec-doctor`,
`author_llm: livespec-doctor`), the only `out-of-band-edit-<timestamp>` revision among
v034–v041. That bypassed the "independent review is never self-waived" rule via automation.
Put this line in every dispatch brief.

## Close-out

When all children + slices are `done`, epic `livespec-y2lkf4` closes and this thread archives
to `plan/archive/rop-sweep-fleet-policy/`.
