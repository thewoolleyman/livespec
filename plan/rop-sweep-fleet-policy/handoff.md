# rop-sweep-fleet-policy — EXECUTING. Critical path: re-dispatch the Fable ROP ruling (STEP 1 below)

**Read this whole file before acting.** Planning is done; execution is underway and partly
blocked on ONE design ruling. Status is READ from the ledgers (`bd`), never stored here.
Ledger note on epic `livespec-y2lkf4` carries the maintainer decisions; per-mirror notes carry
the review blockers.

## ⛔ Guards
- **DO NOT run `groom livespec-y2lkf4`** (the EPIC). It re-decomposes + closes; the epic is
  already decomposed (6 children + 10 slices). Individual-child `groom <id>` is fine.
- **DO NOT accept any work-item** without BOTH a separate Codex reviewer AND a separate Opus
  reviewer clearing it (maintainer rule, 2026-07-19).
- Dispatch DETACHED only (see playbook); a killed foreground dispatch strands the item `active`.

## Maintainer decisions (2026-07-19) — binding
1. **Railway scope** = convert ONLY the **expected-failure paths** (I/O, subprocess, network,
   parsing, error-handling) to the `returns` Result/IOResult railway + vendor `returns` + enable
   ruff `BLE` and pyright `reportUnusedCallResult`. Do NOT rewrite pure-transform functions.
2. **Grooming** = decompose the large children autonomously, no approval gate. (DONE — 10 slices.)
3. **Accept gate** = the agent runs `drive --action accept:<id>`, but ONLY after a separate
   **Codex** reviewer AND a separate **Opus** reviewer both clear the merged PR.

## STEP 1 (do this FIRST) — re-dispatch the Fable ROP ruling
The maintainer asked for a Fable subagent to settle an ambiguity that BLOCKS accepting heejvw and
BLOCKS briefing the 10 slices. It was dispatched and killed by a fleet-wide tmux kill-server (NOT
cancelled). Re-dispatch it with `Agent(subagent_type: "general-purpose", model: "fable")` using
this brief:

> You are the DESIGN AUTHORITY for the livespec fleet's ROP error-handling architecture. Author the
> definitive, unambiguous rule for when broad exception handling is permitted. Read
> `/data/projects/livespec/SPECIFICATION/non-functional-requirements.md` §"ROP composition",
> §"Shared content provenance" (~line 114), §"Supervisor discipline", §"Linter rule set" (ruff BLE),
> and the vendored idioms in `/data/projects/livespec-driver-claude/.claude-plugin/scripts/_vendor/returns/`
> (`@safe`, `@impure_safe`, `Result`, `IOResult`).
> **Ambiguity:** nfr.md says "The ONLY permitted broad `except Exception` is a single outermost
> boundary handler" (CLI supervisor bug-catcher, or a fail-open hook's silent pass-through). But
> railway code must catch at I/O seams to LIFT exceptions onto the failure track — which is exactly
> what `@impure_safe` does internally. Two real factory-produced styles disagree:
> • STYLE A — `/data/projects/livespec-driver-claude/.claude-plugin/hooks/block_auto_memory.py`:
>   `except Exception as exc:  # noqa: BLE001 - stdin boundary captured on IO rail` at I/O seams
>   (lifts exc onto IOResult), PLUS narrow `except (OSError, ValueError)` for decision logic, PLUS
>   one final `except Exception:  # noqa: BLE001 — fail-open by contract`.
> • STYLE B — `/data/projects/livespec-orchestrator-git-jsonl/.claude-plugin/scripts/livespec_orchestrator_git_jsonl/io/store.py`
>   and `.../store.py`: ZERO broad `except` — every catch narrowed and lifted to Failure/IOFailure.
> One reviewer called STYLE A's I/O-lift catches violations; another called them legitimate
> rail-lifting distinct from the fail-open boundary. Both defensible — settle it authoritatively.
> **Deliverable (return the full document):** (1) the most disciplined architecture that is
> pragmatically achievable in ALL cases — precisely when a broad `except Exception` is permitted vs.
> must be narrowed, covering the fail-open/supervisor boundary, I/O-seam lifting, the
> `@impure_safe`/`@safe` route vs. hand-rolled catches, and any difference for fail-open hooks vs.
> CLI supervisors vs. libraries; state it so a reviewer gets exactly ONE answer per site.
> (2) Proposed nfr.md prose updates — quote the EXACT current sentence(s), give the EXACT
> replacement. (3) GOOD/ACCEPTABLE vs BAD/UNACCEPTABLE code examples for: I/O-seam lift,
> decision-logic catch, fail-open/supervisor boundary, a discarded Result (bad), a swallowed bug
> (bad) vs a propagating bug (good). Standardize the `# noqa: BLE001` marker wording.
> READ-ONLY: edit nothing, commit nothing.

Then: land its prose via the spec lifecycle (`/livespec:propose-change` → independent review →
`/livespec:revise`), and use the ruling for STEP 2 and STEP 3.

## STEP 2 — disposition the 3 merged conversions (all parked in `acceptance`, NONE accepted)
Each mirror carries a `bd` note with full blocker detail. Summary:

| Child (tracking) | Mirror / repo | PR | Review | Disposition |
|---|---|---|---|---|
| `livespec-heejvw` | `livespec-driver-claude-7u7` / livespec-driver-claude | #210 | Codex BLOCKERS vs **Opus CLEAR** | Pure I/O-lift dispute → **accept if Fable permits I/O-seam rail-lifting**, else narrow the I/O catches |
| `livespec-kumh3e` | `livespec-driver-codex-96q` / livespec-driver-codex | #194 | both BLOCKERS | **Fix regardless**: undocumented whole-file `ignore` of `reportUnusedCallResult` for `no_shadow_ledger.py` (fix the gate, not the bypass — use `_ = sys.stdout.write(...)` or a line-level ignore); 2nd internal broad except at `livespec_footgun_guard.py:213` |
| `livespec-unc45o` | `bd-gj-hab` / livespec-orchestrator-git-jsonl | #335 | both BLOCKERS | **Fix regardless**: store `read/append → IOResult` broke the shared `WorkItemStore` protocol and the PR **DELETED** the `_: type[WorkItemStore]` conformance binding instead of reconciling; discarded `IOResult` in `migration/beads_to_jsonl.py:74` and `migration/merge_evidence_backfill_core.py:81` (append failures reported as success); stale docstrings. NOTE: zero broad except here, so the I/O-lift question does NOT apply |

For each fix: file a fix work-item **in that repo's own tenant**, dispatch detached, re-run the
dual review, then `drive --action accept:<mirror-id>` and close the livespec-tenant tracking child.

## STEP 3 — the 10 groomed slices (filed `backlog`, deliberately HELD)
`livespec-apiiwc` and `livespec-qgp2jt` are **blocked/superseded**; do not dispatch them whole.
Their replacements, all linked to the epic via `tracks`:
- **livespec-runtime**: `livespec-4nlb` (**ANCHOR** — vendors `returns`, enables BLE, narrows
  `retry.py:49`, railways `cross_repo/`), then `livespec-p41z` (`github_auth/`),
  `livespec-shz8` (`work_items/`), `livespec-0bpr` (`hygiene_scan_*`).
- **livespec-dev-tooling**: `livespec-h2hs` (**ANCHOR** — vendors `returns`, enables BLE, routes the
  5 product blind-catches), then `livespec-9cts` (checks/external-tool), `livespec-ss2j`
  (checks/source-scan+AST), `livespec-5dpg` (`cross_repo/`), `livespec-tvlq` (`fleet/`),
  `livespec-gcsn` (agent_hooks + driver_checks + workflow_checks + installers).
Each conversion slice `depends_on` its repo's ANCHOR (the anchor vendors returns + enables BLE
repo-wide), so land anchors first, then the rest can run in parallel.
**Before promoting any slice to `ready`: bake the Fable ruling into its brief** so the factory
implements to the right bar first time. Then mirror + dispatch (playbook below).

## STEP 4 — reconcile `ftbvgc`
Core's `BLE` add MERGED and is live (livespec PR #1381), but the item is stuck `active`: an earlier
FOREGROUND dispatch was killed mid-gate so it never transitioned active→acceptance. `drive impl` on
it is refused (`not in the ready set`) and `accept:` refuses (`expected acceptance source state;
found active`). Do NOT hack-close it (bypasses evidence-journaling). Investigate the dispatcher's
post-merge path (`dispatcher.py janitor-check`, `_dispatcher_valves.py`) for the legitimate
reconcile, or surface to the maintainer.

## Mechanics (hard-won — do not rediscover)
- **Cross-tenant rule: factory dispatch requires item-tenant == target-repo-tenant.** The epic +
  tracking children live in the **livespec** tenant, so a child targeting a sibling repo CANNOT be
  dispatched directly. File a **dispatch-mirror in the target repo's tenant** (the `bd-ib-zaq3`
  pattern), dispatch that, and close BOTH on completion. Only core-targeting items dispatch directly.
  - Mirror playbook: `cd <target-repo>` → `bd create --title "<same>" --type task -p 2 --labels
    "origin:freeform,rop-sweep-mirror" --body-file <brief-with-mirror-header> --acceptance "<same>"`
    → `bd update <mirror-id> --status ready` → dispatch detached.
  - Target tenants: git-jsonl=`bd-gj`, driver-claude=`livespec-driver-claude`,
    driver-codex=`livespec-driver-codex`, runtime/dev-tooling similarly.
- **Detached dispatch playbook** (~20-45 min each; foreground caps at 20 min and the harness blocks
  backgrounding it; a killed foreground dispatch STRANDS the item `active`):
  `/usr/bin/tmux -L rop-drain new -d -s <name> "python3 <plugin-root>/scripts/bin/drive.py --action impl:<id> --repo <repo> --json > <log> 2>&1; echo __EXIT=\$? >> <log>"`
  Use `/usr/bin/tmux` directly (the zsh tmux alias fails non-interactively) and a SCOPED `-L` socket
  (never the default socket). `drive.py` self-wraps under the credential wrapper.
- **State machine**: `ready → active → acceptance → done`. Only a running dispatcher advances
  active→acceptance. Re-invoking `drive impl` on a non-`ready` item is refused, so it can never
  duplicate a PR.
- All `bd` calls go through `/data/projects/1password-env-wrapper/with-livespec-env.sh`. The
  `auto-backup failed … command denied` warning is correct-by-design, not a fault.

## Meta-finding (worth acting on)
The factory's conversions pass the mechanical janitor gate (`just check` green) but carry ROP-
**semantic** defects — bypass-ignores, discarded Results, a broken protocol with its guard deleted.
The dual-review gate is what caught this. Expect a review→fix loop per conversion; the clarified
nfr.md rule (STEP 1) should raise first-pass quality for the 10 slices.

## What already landed
- Spec + template: livespec PR #1321 (nfr.md v165 — ROP observability rule, ruff `BLE` 27→28,
  full-ROP fleet+adopter bar). Handoff/bookkeeping: PRs #1331, #1344, #1376, #1384 (all merged).
- Core `BLE` (ftbvgc): livespec PR #1381 merged.
- Railway conversions merged (pending accept): driver-claude #210, driver-codex #194, git-jsonl #335.

## Close-out
When all children + slices are `done`, epic `livespec-y2lkf4` closes and this thread archives to
`plan/archive/rop-sweep-fleet-policy/`.
