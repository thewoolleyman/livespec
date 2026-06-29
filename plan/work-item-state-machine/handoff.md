# Handoff — work-item-state-machine (FLEET COORDINATOR)

This is the single resumable entry point for a fresh session resuming the
**work-item lifecycle epic rollout**. You are the **fleet coordinator +
anchor** for a multi-repo epic whose design is fully locked. A fresh session
can execute the next action from this file alone via the read-first chain —
no chat history required.

## What this thread is

The design of livespec's **deterministic work-item lifecycle state machine**
is **COMPLETE** (decisions 1–46): A–H design walk done; design doc
re-synthesized; the **slice plan + execution structure are persisted**
(`research/04-slice-plan.md`). The epic is in **ROLLOUT**, decomposed into
dependency-layered, per-repo tracks — each run in its OWN tmux session as its
OWN `/livespec-orchestrator-beads-fabro:plan` thread (own epic, own beads
tenant, prose-linked to the core anchor). **L0 (the foundation track) is
COMPLETE and released as `livespec-runtime` `v0.5.0`; L1a + L1b are COMPLETE
and released (`v0.3.0` each) → L1 COMPLETE (≈60% of the epic).** The console
track is now KICKED OFF and running autonomously; **L2 (the 9-tenant migration)
is the active next phase, now UNBLOCKED.** See the Session-7 autonomous-run log
below for what landed while the maintainer was asleep.

**Your role (coordinator):** drive the rollout in `research/04-slice-plan.md`,
foundation-first. Run a **lightweight manual overseer** — INFORMED BY
`.claude/skills/overseer/` but do NOT invoke it or stand up its three-pane
dashboard (decision 45; it is the heavy, throwaway part this epic deletes).
Adopt only: the **status table** (`Epic · Track · Status · %Complete`) printed
in THIS pane before any gate/status; the **anti-stall discipline** (never
freeze the coordinator on one track; keep others self-sustaining; never park a
track on a non-blocker; decide-and-inform for reversible/in-intent calls);
`command tmux send-keys` kickoff; and the cross-repo brief discipline (a
cold-startable brief per repo under `briefs/`, status from the ledger, no
shadow queue).

## Status (read from the ledger — never from this file)

- **Core anchor epic:** `livespec-35s3zo` (livespec core tenant). 0 children —
  the per-track epics live in their OWN tenants, prose-linked. Check live:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-35s3zo
  ```
  *(Hygiene TODO: its DESCRIPTION still lists the old state set
  `…/deferred/…` with no `pending-approval`; update it to the 7 locked states
  next time the anchor is touched — a `bd update` on the core tenant.)*
- **L0 — `livespec-runtime` track: COMPLETE.** Runtime-tenant epic
  **`livespec-runtime-l4yojx`** is **CLOSED**; **`livespec-runtime` `v0.5.0`
  is released** (the artifact L1 vendors). Path done: `revise` ratified the
  contract (runtime history `v008` — `contracts.md` got the 7-state status,
  `+rank:str`, `−priority`, admission/acceptance/blocked policy fields, the
  `lane_of` lifecycle authority, the `rank` fractional-index primitive, and a
  `:131` upstream-schema drift fix) → `groom` cut 5 children (S1 rank, S3
  types, S2 lifecycle, S4 tests, S5 release) → S1–S4 implemented via
  red-green-replay (100% coverage) → `v0.5.0` cut. CORE then bumped its
  `livespec-runtime` pin to `v0.5.0` (`377902c`). Full trail in the runtime
  track's own handoff at
  `/data/projects/livespec-runtime/plan/work-item-state-machine/handoff.md`.
- **Release-please hardening (surfaced during L0; it blocked the v0.5.0
  release; now DONE fleet-wide):**
  - **WI-A** (`livespec-runtime-emz`, runtime tenant, **CLOSED**): runtime's
    `release-please.yml` used the default `GITHUB_TOKEN`, so its release PRs
    were authored by `github-actions[bot]` → CI parked (`action_required`) →
    required checks never reported → release blocked. Fixed by porting the
    livespec App-token pattern (`actions/create-github-app-token` + `token:`
    to release-please-action) — **PR #96**. A fleet audit found
    livespec-runtime was the ONLY drifted repo (all others already App-token).
  - **WI-B** (`livespec-0uu3`, CORE tenant, **CLOSED**): release-please
    mechanically bumps version anchors INSIDE spec files (`contracts.md` lines
    tagged `# x-release-please-version`), which the CORE doctor
    `doctor-out-of-band-edits` check flagged as drift vs the latest
    `history/vNNN/` snapshot → reddened master CI → `check-master-ci-green`
    would freeze the repo. Fixed in CORE by a pure helper
    `_strip_release_please_anchor_lines` that normalizes anchor-marked lines
    out of BOTH sides before the byte compare — **PR #707** (`75110d0`),
    shipped in CORE **`v0.5.0`**.
- **L1a — `livespec-orchestrator-beads-fabro` track: COMPLETE.**
  Beads-fabro-tenant epic **`bd-ib-vvrxcb`** is **CLOSED**; **`v0.3.0`
  is released**. Landed across its slices: re-vendor `livespec-runtime v0.5.0`
  + store-adapter (S1+S2, PR #203); the `next` rank ordering + `lane`/`lane_reason`
  emission + 5 custom beads statuses + 2-step append + new `rebalance-ranks`
  command + doctor checks (S4/S6); the Dispatcher admission valve + per-repo WIP
  cap + post-merge acceptance (S3 — `complete→acceptance→accept-per-policy`,
  reject routing, non-convergence→backlog; PR re-expressing scenarios 10/11 +
  adding 22–25); release PR #168. 1245 tests, 100% coverage. **NOTE:** its live
  beads tenant stays PRE-migration — L2 migrates the statuses in lockstep; the
  epic closures used the schema-tolerant read path.
- **L1b — `livespec-orchestrator-git-jsonl` track: COMPLETE.** **`v0.3.0`
  is released** (PR #150 implement / PR #151 release). JSONL record schema
  16→17 (`+rank`, `−priority`; the 3 policy fields are `None`-on-read /
  dropped-on-write); store `rank` + `BOTTOM_SENTINEL` adapter; `next` ordering
  now `(rank, id)`. *(Doc-reconcile TODO: the policy-fields-dropped behavior is
  a slice-plan-vs-design-§6 tension worth reconciling in `research/02-design.md`
  §6 next time that doc is touched.)*
- **L1 COMPLETE → ≈60% of the epic.** L0 (`livespec-runtime` `v0.5.0`) + L1a
  (`v0.3.0`) + L1b (`v0.3.0`) are all released. L2 is now unblocked on both the
  L1 releases AND the `rebalance-ranks` command (shipped in L1a `v0.3.0`).
- **Console track — `livespec-console-beads-fabro`: KICKED OFF (running
  autonomously).** Resuming its existing thread `plan/work-item-lifecycle-redesign/`
  (epic `livespec-console-beads-fabro-vqh36l`) to CONSUME the orchestrator's flat
  `lane`/`lane_reason` emission from `list-work-items` and RETIRE the `bd ready`
  re-derivation — decoupling the console from Beads (orchestrator-CLI-only, zero
  primary lifecycle state; decision 41).
- **L2 — the 9-tenant migration: NOT STARTED, now UNBLOCKED.** Register the 5
  custom beads statuses (`bd config set status.custom`) + backfill `rank`
  (`priority → captured_at → id` via `n_keys_between`, legacy-seeded) into EACH
  of the 9 beads tenants, applied through the orchestrator's `rebalance-ranks`
  (legacy-seed entry). Tracks: **openbrain** (adopter — also bumps its
  core/runtime/orchestrator pins to the new releases + `.livespec.jsonc` WIP-cap
  config + custom-status registration + rank backfill); the **thin
  migration-only tracks** (`livespec-dev-tooling`, `livespec-driver-claude`,
  `livespec-driver-codex` — tenant migration only, formalized in each repo's
  history); and the core `livespec` tenant is swept too. Each thin track gets its
  own `/plan` track per `research/04-slice-plan.md` "L2".
- **Env note (worth a fleet fix):** `hydrate` does NOT provision the gitignored
  worktree-pack (`branch-protection.just` etc.) into fresh worktrees, so sessions
  must run `just install-worktree-pack` to get `just check` green (self-healed
  each time); the git-jsonl PRIMARY checkout also lacks `branch-protection.just`.

## The next action

**L1 is complete. Drive the active phase (L2) and the console, in this order:**

1. **Monitor the console (autonomous).** It runs in its own tmux session,
   resuming `plan/work-item-lifecycle-redesign/` (epic `…-vqh36l`). Confirm it
   CONSUMES `list-work-items --json`'s flat `lane` + `lane_reason`, retires its
   `bd ready` re-derivation, merges, and (optionally) cuts a release. Do NOT
   freeze the coordinator waiting on it — keep it self-sustaining.
2. **Drive L2 (the active next phase — the 9-tenant migration).** Author + kick
   off the `openbrain` adopter (core/runtime/orchestrator pin bumps to the new
   releases + `.livespec.jsonc` WIP-cap config + custom-status registration +
   `rank` backfill) and the **thin migration-only** tracks
   (`livespec-dev-tooling`, `livespec-driver-claude`, `livespec-driver-codex`:
   register the 5 custom statuses + per-tenant `rank` backfill via the
   orchestrator's `rebalance-ranks` legacy-seeded path); sweep the core
   `livespec` tenant too — **9 tenants total**. Each thin track = its own
   `/plan` track.
3. **Exit gate:** delete `.claude/skills/overseer/` once the new system is
   dogfooded → then close `livespec-35s3zo` — it is NOT done until this lands.

**Kickoff mechanics** (per remaining L2 track): land a
cold-startable brief under `briefs/` (template: `briefs/l0-runtime.md`),
confirm the repo is clean + on master + the orchestrator plugin enabled + its
tenant reachable, then:
```bash
command tmux send-keys -t <session> -l "read /data/projects/livespec/plan/work-item-state-machine/briefs/<brief>.md and follow it. Start now."
sleep 0.6; command tmux send-keys -t <session> Enter
# verify it submitted (capture the pane; re-send Enter if it shows [Pasted text])
```
All required sessions already exist: `livespec-runtime`,
`livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`,
`livespec-console-beads-fabro`, `openbrain`, `livespec-dev-tooling`,
`livespec-driver-claude`, `livespec-driver-codex`.

**Mechanism notes (learned this session — they gate the L2 + release work):**
- A CORE doctor/contract fix reaches a governed repo only via a **CORE
  RELEASE + that repo's core-pin bump** (governed repos pin CORE at
  `compat.pinned`, NOT master) — the `bump-pin` fan-out auto-opens the sibling
  pin-bump PRs on each CORE release.
- release-please PRs MUST be **App-authored** (App token) to run CI ungated; a
  release PR opened under the old `GITHUB_TOKEN` flow needs a one-time
  **close+reopen** to re-author it under the App identity.

## Track table (refresh from the ledger before acting)

| Layer | Track (session) | Epic | Status |
|---|---|---|---|
| anchor | livespec (core) | `livespec-35s3zo` | coordinating |
| L0 | livespec-runtime | `livespec-runtime-l4yojx` | **COMPLETE** · closed · `v0.5.0` released |
| L1a | livespec-orchestrator-beads-fabro | `bd-ib-vvrxcb` | **COMPLETE** · closed · `v0.3.0` released |
| L1b | livespec-orchestrator-git-jsonl | (in git-jsonl tenant) | **COMPLETE** · `v0.3.0` released |
| console | livespec-console-beads-fabro | `…-vqh36l` | **running autonomously** (consuming lane/lane_reason) |
| L2 | openbrain (adopter) | — | not started · **UNBLOCKED** (L1 released) |
| L2 | livespec-dev-tooling / driver-claude / driver-codex | — | not started · thin migration-only · **UNBLOCKED** |

## Session-7 autonomous-run log

What landed while the maintainer was asleep (session 7, autonomous):

- **L0 COMPLETE + released.** `livespec-runtime-l4yojx` closed; `livespec-runtime`
  `v0.5.0` cut. Path: `revise` (runtime history `v008`) → `groom` (5 children
  S1–S5) → S1–S4 red-green-replay at 100% coverage → release. CORE bumped its
  runtime pin to `v0.5.0` (`377902c`).
- **Release-please hardening — DONE fleet-wide** (it blocked the v0.5.0
  release): **WI-A** (`livespec-runtime-emz`, PR #96) ported the App-token
  pattern into runtime's `release-please.yml`; **WI-B** (`livespec-0uu3`,
  PR #707 / `75110d0`) added `_strip_release_please_anchor_lines` to CORE's
  `doctor-out-of-band-edits`, shipped in CORE `v0.5.0`. A fleet audit confirmed
  runtime was the only App-token-drifted repo. The release-please problem is
  now systemically fixed across the fleet.
- **L1a + L1b kicked off autonomously**, each in its own tmux session driving
  its slice and creating its own `/plan` thread + epic, prose-linked to
  `livespec-35s3zo`.
- **L1a COMPLETE + released `v0.3.0`** (epic `bd-ib-vvrxcb` closed). Re-vendored
  `livespec-runtime v0.5.0` + store-adapter (PR #203); shipped `next` rank
  ordering + `lane`/`lane_reason` emission + 5 custom statuses + 2-step append +
  `rebalance-ranks` + doctor checks; Dispatcher admission valve + per-repo WIP
  cap + post-merge acceptance (PR re-expressing scenarios 10/11 + adding 22–25);
  release PR #168. 1245 tests, 100% coverage. Its live beads tenant stays
  PRE-migration (L2 migrates statuses in lockstep).
- **L1b COMPLETE + released `v0.3.0`** (PR #150 implement / #151 release). JSONL
  schema 16→17 (`+rank`, `−priority`; policy fields `None`-on-read /
  dropped-on-write); store `rank` + `BOTTOM_SENTINEL` adapter; `next` ordering
  `(rank, id)`.
- **L1 COMPLETE → ≈60% of the epic** (L0 `v0.5.0` + L1a `v0.3.0` + L1b `v0.3.0`
  all released).
- **Console track kicked off autonomously** — resuming
  `plan/work-item-lifecycle-redesign/` to consume the orchestrator's
  `lane`/`lane_reason` emission and retire its `bd ready` re-derivation.
- **L2 (the 9-tenant migration) + the exit gate remain.** L2 is unblocked on the
  L1 releases + `rebalance-ranks`; the overseer-deletion exit gate is still pending.

## Read-first chain (in order)

1. **`research/04-slice-plan.md`** — START HERE; the execution structure
   (tracks, layers, per-repo routing, the per-repo-session model). Its trail
   is decisions 44–46.
2. **`research/03-decision-log.md`** — authoritative on the DESIGN (decisions
   1–46; 44–46 = session-6 execution structure).
3. **`research/02-design.md`** — the design of record (current).
4. **`briefs/l0-runtime.md`** — the L0 kickoff brief + the template for every
   per-repo brief.
5. **`research/01-prior-art.md`** — external grounding.
6. **`conversation/transcript.md`** — verbatim session-1 design discussion.
7. **Per-track handoffs (each track's own state):** the L0 runtime track's
   handoff (`/data/projects/livespec-runtime/plan/work-item-state-machine/handoff.md`);
   the console thread (`/data/projects/livespec-console-beads-fabro/plan/work-item-lifecycle-redesign/handoff.md`).

## The locked model (the spine for every track)

- **Seven stored states:** `backlog · pending-approval · ready · active ·
  acceptance · blocked · done`. Single derived overlay: `ready` + open dep →
  `blocked:dependency` (auto-clears). "Receipt" retired.
- **Grooming = `backlog → pending-approval`**; **approval = `pending-approval →
  ready`**. `defer` → `pending-approval`; `bounce`/`reject(re-groom)` → `backlog`.
- **Acceptance is POST-MERGE / in-production** (decision 33): ship-on-green,
  then AI/human confirm the shipped artifact vs tests + telemetry; `reject` =
  revert/fix-forward. `just check` stays the pre-merge floor.
- **Ownership = the existing `assignee` field** (decision 35): zero migration,
  set by the Dispatcher on `admit`, invariant `active ⟹ assignee`.
- **WIP cap is per-repo** (`.livespec.jsonc`, default 5; fleet total = sum).
- **`rank`** (decisions 38–39): a strictly-required NON-NULL `str` fractional
  key, the sole order. PORT (verbatim CC0 copy) of the rocicorp/httpie
  fractional-index module → `livespec_runtime/work_items/_fractional_indexing.py`
  behind a `rank.py` wrapper. Backfill across all **9** tenants from
  `priority → captured_at → id` via `n_keys_between`, reusing `rebalance-ranks`
  (legacy-seeded); `priority` dropped (no scrub). Store adapter substitutes a
  bottom-sentinel (`"~"`) for legacy lines; doctor invariant: every live item
  has a real rank. Rebalance on-demand only (decision 38 G-2) + a doctor
  key-length warning.
- **Beads encoding** (decision 36, vs v1.0.5): 5 custom statuses
  (`backlog`, `pending-approval`, `ready:active`, `active:wip`, `acceptance:wip`)
  + 2 built-in reuses (`blocked`; `done`→`closed`). `bd create` forces `open`,
  so `append_work_item` is a 2-step create+update.
- **`lane_of`** (decisions 40 + 42): `lane_of(*, item, index, manifest) -> Lane`
  (`Lane = {name, reason}`), net-new in `livespec_runtime/work_items/lifecycle.py`
  as the single authority, with `is_item_ready` + `ready_sort_key` (keyed on
  `rank`) **pure-core-relocated + backend-lookup-injected** (no runtime→beads
  back-edge). `list-work-items --json` emits flat `lane` + `lane_reason`; the
  console CONSUMES them.
- **Spec-routing reframe** (decision 44): the contract lives in the
  `livespec-runtime` + orchestrator `SPECIFICATION`s, **NOT** CORE (CORE's spec
  delegates the whole surface). The epic is anchored in core, but core is the
  anchor, not the work site.
- **Tenant scope = 9** (decision 46): the 8 fleet tenants + the `openbrain`
  adopter; drivers + dev-tooling are migration-only (zero-dep) thin tracks.

## Beads ground-truth (for any further beads research)

- Canonical beads origin is **`github.com/gastownhall/beads`**; local clone at
  `/data/projects/beads`, parked at tag **v1.0.5** (the livespec-pinned
  version). Custom statuses + categories are real; 7 built-ins; no
  status-transition enforcement; `bd create` forces `open`/`deferred`.

## Hard exit gate for the epic

`livespec-35s3zo` is NOT done until the local **overseer skill**
(`.claude/skills/overseer/`) is **deleted** — it keeps running until the new
system is dogfooded, then is removed as the final step.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan work-item-state-machine
```
