# rop-sweep-fleet-policy — full-ROP railway backfill; briefs rewritten; EXECUTING (cross-tenant mirrors)

**State (2026-07-19).** Planning refined; maintainer authorized in-session autonomous execution.
The 6 child briefs are rewritten to mandate the full ROP railway everywhere (a code audit showed
the earlier "thin repo / decide vendoring returns" framing was wrong). Execution is UNDERWAY via
the factory, with two hard-won mechanics below. Status is READ from the ledgers, not stored here.

## ⛔ DO NOT run `groom livespec-y2lkf4` (the EPIC)
Epic-level groom re-decomposes + closes; it would duplicate/orphan the 6 children. Individual-child
`groom <child-id>` IS allowed/expected for the oversized ones (`qgp2jt`, likely `apiiwc`).

## ‼️ Execution mechanics learned the hard way (2026-07-19)

**1. Factory dispatch requires item-tenant == target-repo-tenant.** The epic + tracking children
live in the **livespec** tenant, but a child can only be DISPATCHED into the repo whose tenant it
lives in. So only `ftbvgc` (targets livespec itself) was directly dispatchable. Each of the 5
sibling-targeting children needs a **dispatch-mirror filed in its target repo's tenant** (the
maintainer-blessed `bd-ib-zaq3` = mirror-of-`livespec-kiwfyv` pattern). The livespec-tenant child
stays for epic tracking; the mirror carries the brief and is what gets dispatched. On completion
close BOTH the mirror and the tracking child. (This corrects the earlier handoff's WRONG claim that
"the single coordinating tenant dispatches each child into its target repo".)

**Mirror playbook (per sibling child):**
- `cd <target-repo>`; `bd create --title "<same>" --type task -p 2 --labels origin:freeform,rop-sweep-mirror --body-file <brief-with-mirror-header> --acceptance "<same>"`
- `bd update <mirror-id> --status ready`
- Dispatch DETACHED (see #2): `drive.py --action impl:<mirror-id> --repo <target-repo> --json`
- Target tenants: git-jsonl=`livespec-orchestrator-git-jsonl` (prefix bd-gj), driver-claude=`livespec-driver-claude`, driver-codex=`livespec-driver-codex`, runtime + dev-tooling similarly.

**2. Dispatch = ~20-45 min, un-backgroundable via the harness, foreground caps at 20 min.**
A KILLED foreground dispatch leaves the item stuck `active` (state machine: ready→active→acceptance
→done; only the running dispatcher advances active→acceptance→done). So dispatch **DETACHED** on a
SCOPED tmux socket (never the default socket — that's what was killing sessions):
`/usr/bin/tmux -L rop-drain new -d -s <name> "python3 <drive.py> --action impl:<id> --repo <repo> --json > <log> 2>&1; echo __EXIT=\$? >> <log>"`
(`/usr/bin/tmux` directly — the zsh tmux alias fails non-interactively.) The detached dispatch runs
to completion (auto-merge PR + close) surviving this pane. Re-invoking `drive impl` on a non-`ready`
item is REFUSED (`not in the ready set`) — so it can never duplicate a PR.

## Execution status (READ the ledgers for truth)
- `ftbvgc` (core): PR #1381 MERGED, BLE live, CI green — but item stuck `active` (killed its
  FOREGROUND dispatch mid-gate). Needs a proper reconcile to `done` (accept valve wants `acceptance`
  state; re-dispatch refused as non-ready). Do NOT hack-close (bypasses evidence-journaling).
- `heejvw` (driver-claude): mirror **livespec-driver-claude-7u7** filed + ready + dispatched DETACHED
  (session `heejvw` on socket `rop-drain`). In flight.
- `unc45o` (git-jsonl), `kumh3e` (driver-codex): bounded — mirror + dispatch next (same playbook).
- `apiiwc` (runtime ~3.9k LOC), `qgp2jt` (dev-tooling ~23.7k LOC): LARGE — `groom <child-id>` into
  per-subpackage slices FIRST (maintainer owns the cut), then mirror + dispatch each slice.

## The rewrite that landed (livespec PR #1376, merged)
6 briefs mandate: vendor `returns` + Result/IOResult railway + `BLE` (+ `reportUnusedCallResult` for
the Drivers). Core (`ftbvgc`) is the reference (already on the railway) → BLE only. Per-repo LOC +
"on railway now?" table: see git history of this file / the ledger briefs.

## Reference — maintainer decisions
1. **Flat: full ROP everywhere** (2026-07-18, re-affirmed after the 2026-07-19 code audit) — every
   Python-carrying fleet repo vendors `returns` + is on the railway, Drivers + dev-tooling included;
   sole exemption = zero-first-party-Python (Rust console).
2. **ruff `BLE`** = add to template + backfill fleet.
3. **Execution = in-session, autonomous** (2026-07-19).

## Close-out
When all children (+ groomed slices + mirrors) are `done`, the epic closes and this thread archives
to `plan/archive/rop-sweep-fleet-policy/`.
