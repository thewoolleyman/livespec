# Handoff — work-item-state-machine (FLEET COORDINATOR)

This is the single resumable entry point for a fresh session resuming the
**work-item lifecycle epic rollout**. You are the **fleet coordinator +
anchor** for a multi-repo epic whose design is fully locked. A fresh session
can execute the next action from this file alone via the read-first chain —
no chat history required.

## ⚠️ For the next (fresh) overseer — read first

You are taking over a **LEAN overseer session**. The work-item-lifecycle
rollout is **L0 + L1 + L2 COMPLETE** — the deterministic state machine is
designed, the foundation (`livespec-runtime`) + both orchestrators are
released, and **all 9 beads tenants are migrated and doctor-verified**. What
remains is the **console track** and the **exit gate** — but as of session 8
the console track is **BLOCKED on an orchestrator fix that must land first**:
the factory cannot dispatch from a cache-installed/enabled plugin because the
orchestrator plugin is **not self-contained**. So the order is: **(1) drive
the orchestrator plugin self-containment fix**, **(2) dispatch the console's
remaining slices (E-3a → E-3b → E-4) through the fixed factory**, **(3) land
the exit gate**. To take over:

- **⚑ STANDING RULE — dispatch implementation through the factory; do NOT
  hand-code it inline.** The inline-tmux-Claude pattern below was a *bootstrap
  crutch*. Ready, factory-safe impl is dispatched via
  `/livespec-orchestrator-beads-fabro:orchestrate` (`run --action impl:<id>`),
  which runs Red→Green factory-side on **Codex/Fabro** — better code AND spends
  Codex quota, sparing Claude. **Concretely: the console's E-3a/E-3b/E-4 are
  dispatched via `orchestrate`, not hand-coded; "re-engage" means dispatch, not
  re-open an inline coder.** Canonical rule landed (session 8) — the
  Factory-dispatch-over-inline-implementation discipline in
  `.ai/agent-disciplines.md` (CORE PR #715, MERGED) + orchestrator
  `prose/plan.md` "plan files ripe work; the factory implements it"
  (livespec-orchestrator-beads-fabro PR #213, MERGED).
- **⛔ SESSION-8 BLOCKER on that rule — the factory does NOT yet dispatch from
  an enabled plugin.** `orchestrate run` from the ENABLED PLUGIN fails
  (dispatcher exit 3) because the orchestrator plugin is **not self-contained**:
  its Fabro workflow (`.fabro/workflows/implement-work-item/workflow.toml`)
  lives at the orchestrator repo ROOT, outside the packaged `.claude-plugin/`,
  and the dispatcher resolves it via source-layout path-math that
  install-flattening breaks. The factory has only ever worked from the
  orchestrator **SOURCE checkout** (the fleet has it; adopters don't) — which
  is exactly **why all prior impl went inline**. Until the self-containment fix
  lands, "dispatch the console's E-3a/E-3b/E-4" is BLOCKED; **drive the fix
  first** (see "The next action").
- **Re-arm monitoring.** The prior session's `Monitor` watchers died with it —
  they do NOT survive a session boundary. Start a **fresh persistent `Monitor`**
  over the console tmux session `livespec-console-beads-fabro`: poll its pane
  every ~20s and emit when it goes **sustained-idle**, EXCLUDING the strings
  `esc to interrupt`, `Waiting for N background`, and `N shell` from the
  idle test (so CI runs / sub-agent waits inside the console session don't
  false-fire the "it stalled" signal).
- **Re-engage at each clean boundary via tmux `send-keys`.** The console batches
  its own work per fresh context; `/clear` + resume it from
  `plan/work-item-lifecycle-redesign/handoff.md` at each clean boundary. Long
  pastes trigger bracketed-paste mode — send the text, then `Enter`, and
  **re-send `Enter`** until the pane shows `esc to interrupt` (i.e. it actually
  submitted; a stuck `[Pasted text]` means it has not).
- **MANAGE YOUR OWN CONTEXT.** Rotate the overseer role **before ~50% context**:
  refresh THIS handoff and hand off to another fresh overseer session. Be
  **terse** in status updates; **delegate any heavy authoring/migration to
  sub-agents** (spend their context, not yours); capture session panes with
  `tail` / scoped `capture-pane`, never full dumps. The prior overseer ballooned
  to ~80% context by doing all monitoring, authoring, and migration inline — do
  not repeat that. Orchestrate; don't do heavy work in the overseer pane.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan work-item-state-machine`.

## What this thread is

The design of livespec's **deterministic work-item lifecycle state machine**
is **COMPLETE** (decisions 1–46): A–H design walk done; design doc
re-synthesized; the **slice plan + execution structure are persisted**
(`research/04-slice-plan.md`). The epic ran in **ROLLOUT**, decomposed into
dependency-layered, per-repo tracks — each run in its OWN tmux session as its
OWN `/livespec-orchestrator-beads-fabro:plan` thread (own epic, own beads
tenant, prose-linked to the core anchor). **L0 (foundation) is COMPLETE and
released as `livespec-runtime` `v0.5.0`; L1a + L1b are COMPLETE and released
(`v0.3.0` each) → L1 COMPLETE; L2 (the 9-tenant migration) is COMPLETE — all
9 beads tenants migrated and doctor-verified on their live tenants.** The
remaining work is the **console track** and the **exit gate** — and as of
session 8 the console track is **BLOCKED on the orchestrator plugin
self-containment fix** (the factory can't dispatch from an enabled plugin yet).
See the Session-7 and Session-8 logs below for what landed.

**Your role (coordinator):** monitor + re-engage the console to its finish, then
land the exit gate. Run a **lightweight manual overseer** — INFORMED BY
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
  when the anchor is closed at the exit gate — a `bd update` on the core tenant.)*
- **L0 — `livespec-runtime` track: COMPLETE.** Runtime-tenant epic
  **`livespec-runtime-l4yojx`** is **CLOSED**; **`livespec-runtime` `v0.5.0`
  is released** (the artifact L1 vendors). Path done: `revise` ratified the
  contract (runtime history `v008`) → `groom` cut 5 children (S1 rank, S3
  types, S2 lifecycle, S4 tests, S5 release) → S1–S4 implemented via
  red-green-replay (100% coverage) → `v0.5.0` cut. CORE then bumped its
  `livespec-runtime` pin to `v0.5.0` (`377902c`). Full trail in the runtime
  track's own handoff at
  `/data/projects/livespec-runtime/plan/work-item-state-machine/handoff.md`.
- **Release-please hardening (surfaced during L0; now DONE fleet-wide):**
  **WI-A** (`livespec-runtime-emz`, runtime tenant, **CLOSED**, **PR #96**)
  ported the livespec App-token pattern into runtime's `release-please.yml`
  (a fleet audit found runtime was the ONLY drifted repo). **WI-B**
  (`livespec-0uu3`, CORE tenant, **CLOSED**, **PR #707** / `75110d0`, shipped
  in CORE **`v0.5.0`**) added `_strip_release_please_anchor_lines` so the CORE
  `doctor-out-of-band-edits` check normalizes `# x-release-please-version`
  anchor lines out of both sides before the byte compare.
- **L1a — `livespec-orchestrator-beads-fabro` track: COMPLETE.**
  Beads-fabro-tenant epic **`bd-ib-vvrxcb`** is **CLOSED**; **`v0.3.0`
  is released**. Re-vendored `livespec-runtime v0.5.0` + store-adapter
  (PR #203); shipped `next` rank ordering + `lane`/`lane_reason` emission + 5
  custom beads statuses + 2-step append + new `rebalance-ranks` command (whose
  `legacy_seed` primitive every L2 track used) + doctor checks; Dispatcher
  admission valve + per-repo WIP cap + post-merge acceptance (release PR #168).
  1245 tests, 100% coverage.
- **L1b — `livespec-orchestrator-git-jsonl` track: COMPLETE.** **`v0.3.0`
  is released** (PR #150 implement / PR #151 release). JSONL record schema
  16→17 (`+rank`, `−priority`; the 3 policy fields are `None`-on-read /
  dropped-on-write); store `rank` + `BOTTOM_SENTINEL` adapter; `next` ordering
  now `(rank, id)`. *(Doc-reconcile TODO: the policy-fields-dropped behavior is
  a slice-plan-vs-design-§6 tension worth reconciling in `research/02-design.md`
  §6 next time that doc is touched.)*
- **L1 COMPLETE.** L0 (`livespec-runtime` `v0.5.0`) + L1a (`v0.3.0`) + L1b
  (`v0.3.0`) all released.
- **L2 — the 9-tenant migration: COMPLETE.** All 9 beads tenants migrated —
  5 custom statuses registered (`bd config set status.custom`) + `rank`
  backfilled (`priority → captured_at → id` via `n_keys_between`) through the
  orchestrator's `rebalance_ranks.legacy_seed` primitive, **each doctor-verified
  on its live tenant**. Each track filed an L2 work-item prose-linked to anchor
  `livespec-35s3zo` and formalized in its own repo. The 9 tenants:
  | # | Tenant / track | L2 work-item / note |
  |---|---|---|
  | 1 | `livespec-runtime` | migrated + verified |
  | 2 | `livespec-orchestrator-beads-fabro` | migrated + verified |
  | 3 | `livespec-orchestrator-git-jsonl` | migrated + verified |
  | 4 | `livespec-driver-claude` | thin migration-only; migrated + verified |
  | 5 | `livespec-driver-codex` | thin migration-only; migrated + verified |
  | 6 | `livespec-dev-tooling` | thin migration-only; migrated + verified |
  | 7 | `openbrain` (adopter) | migrated + verified (pin bumps still need a client-side `/plugin install` + restart — see follow-ups) |
  | 8 | core `livespec` | work-item **`livespec-owwguc`**, **371 items**, migrated + verified |
  | 9 | `livespec-console-beads-fabro` | work-item **`…-vxq`** (12 live heads, `a0…aB`), migrated + verified (S6 doctor exits 0) |
- **Console E-walk + the session-8 BLOCKER.** The console's lifecycle-redesign
  E-walk (`plan/work-item-lifecycle-redesign/`, epic `…-vqh36l`) has **E-2b
  MERGED** (console PR #64). The epic was **GROOMED** (finer split,
  maintainer-approved) and regroomed-out into **E-3a**
  (`livespec-console-beads-fabro-en67su`, ready) → **E-3b** (dep on E-3a) →
  **E-4** (`livespec-console-beads-fabro-4rt6zi`, dep on E-3b); a toolchain
  blocker is filed as `livespec-console-beads-fabro-3vmgam`. **The E-walk is
  BLOCKED:** the factory cannot dispatch E-3a from an enabled plugin (root cause
  in the STANDING-RULE / SESSION-8-BLOCKER bullets above). **Maintainer
  decision:** make the orchestrator plugin **self-contained** so the factory
  dispatches from the ENABLED PLUGIN — fleet members and adopters then consume
  it IDENTICALLY (just enable the plugin; no orchestrator-source clone; the only
  clones left are of the TARGET repo, which is legitimate). Verdict:
  **achievable-with-work** (packaging + path-resolution, NOT architecture).
  Sequencing chosen: **self-containment fix FIRST**, then dispatch E-3a → E-3b →
  E-4 through the fixed factory as the validation. The design + change set are
  captured in a NEW orchestrator-repo thread at
  `/data/projects/livespec-orchestrator-beads-fabro/plan/orchestrator-plugin-self-containment/`
  (its handoff is the read-first for that work).
- **Plugin state (mapped session 8).** Per-repo Claude enablement is ALREADY
  correct in all 10 governed repos (committed `.claude/settings.json`); Codex is
  registered host-wide. Caches are STALE (core 0.4.0→0.5.0; orchestrator
  0.2.0/0.1.0→0.3.0). A cache refresh is **AUTHORIZED but DEPRIORITIZED** — it
  fixes staleness + the console's runtime-data (attention lens / lane board) but
  NOT dispatch; the self-containment fix is the real unblock.
- **Env note (worth a fleet fix):** `hydrate` does NOT provision the gitignored
  worktree-pack (`branch-protection.just` etc.) into fresh worktrees, so sessions
  must run `just install-worktree-pack` to get `just check` green (self-healed
  each time); the git-jsonl PRIMARY checkout also lacks `branch-protection.just`.

## The next action

**L0 + L1 + L2 are complete. The console E-walk is BLOCKED on the orchestrator
self-containment fix — drive that FIRST, then the console, then the exit gate:**

1. **Drive the orchestrator plugin self-containment fix FIRST (the real
   unblock).** The factory cannot dispatch from a cache-installed/enabled plugin
   until the orchestrator plugin is self-contained. Read-first:
   `/data/projects/livespec-orchestrator-beads-fabro/plan/orchestrator-plugin-self-containment/handoff.md`
   → `propose-change` → `groom` → `implement`. **Then dispatch the console
   slices through the fixed factory (Codex), as the validation that the fix
   works:** E-3a (`livespec-console-beads-fabro-en67su`) → E-3b → E-4
   (`livespec-console-beads-fabro-4rt6zi`). The console runs in its own tmux
   session `livespec-console-beads-fabro`, resuming
   `plan/work-item-lifecycle-redesign/` (epic `…-vqh36l`); E-1 + E-2a (PR #62) +
   E-2b (PR #64) are MERGED. Once dispatch resumes, do NOT freeze the
   coordinator on the console; keep it self-sustaining (see the "For the next
   overseer" section for the monitor + re-engage mechanics). The cache refresh
   (Status above) is an OPTIONAL parallel cleanup; it does NOT unblock dispatch.
2. **Exit gate (the final step — maintainer's call to declare the system
   dogfooded).** The exit gate is now **console E-walk done + the overseer
   updated** → close the anchor epic `livespec-35s3zo` (and the per-repo L2
   epics that were **left open by design** for archive-on-close). The local
   overseer skill (`.claude/skills/overseer/`) is **KEPT and UPDATED** to the
   lean, plan-skill-driven + factory-dispatch form (done), **not deleted** —
   there is no replacement for the manual coordinator until the **console
   operator-cockpit** (TUI minimum, GUI ideal), itself built via the factory,
   replaces it. Deleting the overseer is therefore **DEFERRED** to that future
   console-cockpit milestone, NOT part of this epic's exit gate. It is NOT done
   until the anchor + L2 epics close.
3. **Post-L2 follow-ups (none blocking) — capture as work-items when convenient:**
   - **No end-to-end `migrate-tenant` CLI.** `legacy_seed` /
     `register_custom_statuses` are library **primitives**, not a command — all
     9 tracks hand-composed the migration. A single `migrate-tenant` wrapper
     would make a future tenant onboard one command.
   - **`bd` cwd-tenant trap.** `bd` selects the tenant from the **cwd**'s
     `.beads/config.yaml`, NOT from `-C` (so `-C` does not switch tenants the way
     it looks like it should); bare `bd list` pages at 50 — use `--limit 0`.
   - **Stale `capture-work-item` / `plan` prose for v0.3.0.** It documents the
     OLD schema (`status=open` + `priority`, no `rank`); refresh to the 7-state +
     `rank` model.
   - **driver-codex `.livespec.jsonc` / `CLAUDE.md` mark its (live) beads
     connection block "DEFERRED"** — the tenant is actually migrated and
     connected; correct the stale "DEFERRED" wording.
   - **Slice-plan L2 scope named 5 tenants; the requirement is 9 (decision 46)** —
     fix `research/04-slice-plan.md`'s "L2" section to say 9.
   - **`hydrate` doesn't provision the worktree-pack** into fresh worktrees
     (self-healed via `just install-worktree-pack`) — see the Env note above.
   - **`templates/impl-plugin/` → `templates/orchestrator-plugin/` rename**
     (work-item **`livespec-m0xu`**, CORE tenant): the directory scaffolds
     orchestrator plugins, so the `impl-plugin` name misleads. Filed via raw
     `bd create` (the `capture-work-item` skill's package couldn't import
     `livespec_runtime` here — the same cache staleness as the Plugin-state
     bullet), so `m0xu` is a plain `open` item needing grooming into the new
     lifecycle later.
   - **Orchestrator-plugin cache is stale fleet-wide** (core 0.4.0→0.5.0;
     orchestrator 0.2.0/0.1.0→0.3.0); a cache refresh is AUTHORIZED but
     DEPRIORITIZED — fixes staleness + the console runtime-data, NOT dispatch.
   - **Open-item status reclassification deferred** (per-item grooming; a bulk
     rewrite is available if wanted).
   - **openbrain pin bump needs a client-side `/plugin install` + restart** —
     cannot be done in-session.
   - **Branch protection requires checks but 0 reviews** — relevant once external
     contributions arrive.

**Kickoff mechanics** (only if a NEW per-repo track is ever needed): land a
cold-startable brief under `briefs/` (template: `briefs/l0-runtime.md`),
confirm the repo is clean + on master + the orchestrator plugin enabled + its
tenant reachable, then:
```bash
command tmux send-keys -t <session> -l "read /data/projects/livespec/plan/work-item-state-machine/briefs/<brief>.md and follow it. Start now."
sleep 0.6; command tmux send-keys -t <session> Enter
# verify it submitted (capture the pane; re-send Enter if it shows [Pasted text])
```

**Mechanism notes (they gated the L2 + release work):**
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
| anchor | livespec (core) | `livespec-35s3zo` | coordinating · closes at the exit gate |
| L0 | livespec-runtime | `livespec-runtime-l4yojx` | **COMPLETE** · closed · `v0.5.0` released · L2-migrated |
| L1a | livespec-orchestrator-beads-fabro | `bd-ib-vvrxcb` | **COMPLETE** · closed · `v0.3.0` released · L2-migrated |
| L1b | livespec-orchestrator-git-jsonl | (in git-jsonl tenant) | **COMPLETE** · `v0.3.0` released · L2-migrated |
| L2 | livespec-driver-claude / driver-codex / dev-tooling | (per-tenant) | **COMPLETE** · thin migration-only · migrated + verified |
| L2 | openbrain (adopter) | (openbrain tenant) | **COMPLETE** · migrated + verified (client-side pin install pending) |
| L2 | core `livespec` | `livespec-owwguc` | **COMPLETE** · 371 items migrated + verified |
| L2 | livespec-console-beads-fabro (tenant) | `…-vxq` | **COMPLETE** · 12 heads migrated + verified |
| **blocker** | livespec-orchestrator-beads-fabro (self-containment) | new `/plan` thread `orchestrator-plugin-self-containment` | **NEXT — drive FIRST** · make the orchestrator plugin self-contained so the factory dispatches from the enabled plugin |
| console | livespec-console-beads-fabro (E-walk) | `…-vqh36l` | **BLOCKED on self-containment** · E-1+E-2a (PR #62) + E-2b (PR #64) MERGED; regroomed-out into E-3a (`…-en67su`) → E-3b → E-4 (`…-4rt6zi`); toolchain blocker `…-3vmgam` |

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
  runtime was the only App-token-drifted repo.
- **L1a + L1b kicked off autonomously**, each in its own tmux session driving
  its slice and creating its own `/plan` thread + epic, prose-linked to
  `livespec-35s3zo`.
- **L1a COMPLETE + released `v0.3.0`** (epic `bd-ib-vvrxcb` closed). Re-vendored
  `livespec-runtime v0.5.0` + store-adapter (PR #203); shipped `next` rank
  ordering + `lane`/`lane_reason` emission + 5 custom statuses + 2-step append +
  `rebalance-ranks` (whose `legacy_seed` primitive every L2 track then used) +
  doctor checks; Dispatcher admission valve + per-repo WIP cap + post-merge
  acceptance; release PR #168. 1245 tests, 100% coverage.
- **L1b COMPLETE + released `v0.3.0`** (PR #150 implement / #151 release). JSONL
  schema 16→17 (`+rank`, `−priority`; policy fields `None`-on-read /
  dropped-on-write); store `rank` + `BOTTOM_SENTINEL` adapter; `next` ordering
  `(rank, id)`.
- **L1 COMPLETE** (L0 `v0.5.0` + L1a `v0.3.0` + L1b `v0.3.0` all released).
- **L2 COMPLETE — all 9 beads tenants migrated and doctor-verified.** Each track
  registered the 5 custom statuses + backfilled `rank` via the orchestrator's
  `rebalance_ranks.legacy_seed` primitive, doctor-verified on the live tenant,
  filed an L2 work-item prose-linked to `livespec-35s3zo`, and formalized it in
  its repo. Tenants: livespec-runtime, beads-fabro, git-jsonl, driver-claude,
  driver-codex, dev-tooling, openbrain, **core `livespec`** (work-item
  `livespec-owwguc`, 371 items), and **console** (work-item `…-vxq`, 12 heads).
- **Console track running** — `plan/work-item-lifecycle-redesign/`: E-1
  (Beads-decoupled ingestion) + E-2a (lane-board data spine, PR #62) DONE;
  **E-2b (hybrid lane TUI sub-view) RUNNING NOW**; E-3 + E-4 remain.
- **All other sessions idle/done.** L0/L1a/L1b/runtime/beads-fabro/git-jsonl/
  dev-tooling/driver-claude/driver-codex/openbrain are done with their work.
- **Remaining:** console E-2b → E-3 → E-4 and the overseer update (DONE — the
  skill was rewritten to the lean, plan-skill-driven + factory-dispatch form,
  RETAINED not deleted), then the exit gate (close `livespec-35s3zo` + the
  per-repo L2 epics; the overseer is NOT deleted — its deletion is DEFERRED to
  the future console operator-cockpit milestone). Post-L2 follow-ups are
  captured under "The next action" (none blocking).

## Session-8 log

What landed / was decided in session 8:

- **Factory-dispatch is now the operating model (LANDED).** New fleet discipline
  in `.ai/agent-disciplines.md` (the Factory-dispatch-over-inline-implementation
  section, CORE **PR #715 MERGED**) + orchestrator `prose/plan.md` "plan files
  ripe work; the factory implements it" (livespec-orchestrator-beads-fabro
  **PR #213 MERGED**). Rule: ready, factory-safe IMPLEMENTATION is dispatched via
  `/livespec-orchestrator-beads-fabro:orchestrate` (Codex/Fabro), NEVER
  hand-coded inline in Claude; reserve Claude for planning, groom, spec-side,
  coordination, and maintainer-gated exits. Rationale: better code + spares
  Claude quota.
- **The overseer skill is RETAINED, not deleted — and was rewritten.** The local
  overseer skill (`.claude/skills/overseer/`) is KEPT and UPDATED to the lean,
  plan-skill-driven, factory-dispatching form (rewritten 716→303 lines, **PR
  #716 MERGED**; forbidden-citation fix **PR #717 MERGED**). Decision 47 in the
  decision-log. The epic's exit gate is now: console E-walk done + overseer
  updated (done) → close the anchor `livespec-35s3zo` + the per-repo L2 epics.
  The overseer is NOT deleted; its deletion is DEFERRED to a FUTURE console
  operator-cockpit milestone (itself built via the factory).
- **Console E-walk progress.** **E-2b MERGED** (console PR #64). Epic
  `…-vqh36l` was GROOMED (finer split, maintainer-approved) and regroomed-out
  into **E-3a** (`livespec-console-beads-fabro-en67su`, ready) → **E-3b** (dep
  on E-3a) → **E-4** (`livespec-console-beads-fabro-4rt6zi`, dep on E-3b); a
  toolchain blocker was filed as `livespec-console-beads-fabro-3vmgam`.
- **The factory cannot dispatch from a cache-installed plugin — ROOT CAUSE found
  (the real blocker).** The orchestrator plugin is NOT self-contained: its Fabro
  workflow (`.fabro/workflows/implement-work-item/workflow.toml`) lives at the
  orchestrator repo ROOT, outside the packaged `.claude-plugin/`, and the
  dispatcher resolves it via source-layout path-math that install-flattening
  breaks. So `orchestrate run` from an enabled plugin fails (dispatcher exit 3).
  The factory has only ever worked from the orchestrator SOURCE checkout (the
  fleet has it; adopters don't) — which is WHY all prior work went inline.
- **Maintainer decision: make the orchestrator plugin SELF-CONTAINED.** So the
  factory dispatches from the ENABLED PLUGIN, with fleet + adopters consuming it
  identically (just enable the plugin; the only clones left are of the TARGET
  repo). Verdict: ACHIEVABLE-WITH-WORK (packaging + path-resolution, NOT
  architecture). Sequencing: do the self-containment fix FIRST, then dispatch
  E-3a → E-3b → E-4 through the fixed factory as validation. Design + change set
  captured in a NEW orchestrator-repo thread at
  `plan/orchestrator-plugin-self-containment/` (its handoff is the read-first for
  that work).
- **Plugin state mapped.** Per-repo Claude enablement is ALREADY correct in all
  10 governed repos (committed `.claude/settings.json`); Codex is registered
  host-wide. Caches are stale (core 0.4.0→0.5.0; orchestrator 0.2.0/0.1.0→0.3.0).
  Cache refresh AUTHORIZED but DEPRIORITIZED — fixes staleness + console
  runtime-data, NOT dispatch.
- **Side work-item filed.** `livespec-m0xu` (CORE tenant): rename
  `templates/impl-plugin/` → `templates/orchestrator-plugin/` (it scaffolds
  orchestrator plugins; the name misleads). Filed via raw `bd create` because the
  `capture-work-item` skill's package couldn't import `livespec_runtime` here
  (same staleness) — so `m0xu` is a plain `open` item needing grooming into the
  new lifecycle later.

## Read-first chain (in order)

1. **`research/04-slice-plan.md`** — the execution structure (tracks, layers,
   per-repo routing, the per-repo-session model). Its trail is decisions 44–46.
   *(Note: its "L2" section still names 5 tenants; the requirement is 9 —
   decision 46. A post-L2 follow-up.)*
2. **`research/03-decision-log.md`** — authoritative on the DESIGN (decisions
   1–46; 44–46 = session-6 execution structure).
3. **`research/02-design.md`** — the design of record (current).
4. **`briefs/l0-runtime.md`** — the L0 kickoff brief + the template for every
   per-repo brief.
5. **`research/01-prior-art.md`** — external grounding.
6. **`conversation/transcript.md`** — verbatim session-1 design discussion.
7. **The orchestrator self-containment thread — the read-first for the BLOCKING
   next action:**
   `/data/projects/livespec-orchestrator-beads-fabro/plan/orchestrator-plugin-self-containment/handoff.md`.
8. **Per-track handoffs (each track's own state):** the L0 runtime track's
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
  behind a `rank.py` wrapper. Backfilled across all **9** tenants from
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
- **`bd` selects the tenant from the cwd**'s `.beads/config.yaml`, NOT from the
  `-C` flag — to operate against a tenant, run from inside that repo. Bare
  `bd list` pages at 50; pass `--limit 0` for the full set.

## Hard exit gate for the epic

`livespec-35s3zo` is NOT done until **both**: (1) the console E-walk is finished
(E-2b MERGED; the remaining E-3a → E-3b → E-4 dispatched through the fixed
factory once the orchestrator self-containment fix lands, the new system
dogfooded), and (2) the local **overseer skill**
(`.claude/skills/overseer/`) is **updated** to the lean,
plan-skill-driven + factory-dispatch form (DONE). The overseer is **KEPT and
UPDATED, NOT deleted** — there is no replacement for the manual coordinator
until the **console operator-cockpit** (TUI minimum, GUI ideal), itself built
via the factory, replaces it; deleting the overseer is therefore **DEFERRED** to
that future console-cockpit milestone, not this epic's exit gate. At the exit
gate, close `livespec-35s3zo` and the per-repo L2 epics that were left open by
design for archive-on-close (the overseer skill stays in place).

## Resume command

```
/livespec-orchestrator-beads-fabro:plan work-item-state-machine
```
