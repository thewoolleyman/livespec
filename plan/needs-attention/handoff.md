# needs-attention — track handoff (overseer run-prompt)

**Track:** `needs-attention` · **Repo:** `thewoolleyman/livespec` ·
**Ledger epic anchor:** `livespec-bj9x` (read status LIVE from the
ledger; never trust a status written here).

**Read-first chain (open these, in order, before acting):**

1. The `livespec-bj9x` ledger comments, top-to-bottom — the newest is the
   **2026-07-07 RESUME RECIPE (needs-attention overseer)**, a self-contained
   snapshot with full live state. Read via the credential wrapper: `source
   /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C
   /data/projects/livespec show livespec-bj9x`.
2. `research/design.md` — the settled design + the full cross-repo rollout.
3. `research/glossary.md` — every term used below.

## Current state (2026-07-07; verify live against the ledger, don't trust this)

**ALL 3 STRADDLE SPEC-SPLITS RATIFIED this session** (2026-07-07): BR2
(driver-codex v004, PR #78), OR3 (git-jsonl v017, PR #195), CN1 (console v016,
PR #101/#102). The needs-attention **spec surface is now fully specified across
every repo it touches**. Peripheral doc-fixes (design.md #907, orchestrator
README #352) and the maintainer-directed **openbrain install-prompt side-quest**
(Phase 6 + real step-5 per-tenant Fabro-server recipe, both-orchestrator-correct;
livespec #908/#909/#910/#911) also merged. The **newest RESUME RECIPE comment on
epic `livespec-bj9x` (2026-07-07) is authoritative** for the full remaining phase
+ exact next actions — read it first.

## How to drive this track

The exact remaining phase + next actions live in the epic's **newest RESUME RECIPE
comment** (read-first chain step 1) — follow that; it supersedes any older step list.
Remaining phase in brief:

1. **CODE-SLICE DISPATCHES** (factory, host-wide sequential; fleet App works —
   the openbrain failure was adopter-App-specific): OR3-code `bd-gj-8nh`
   (git-jsonl), BR2-code `livespec-driver-codex-01a` (driver-codex), CN1-code
   `livespec-console-beads-fabro-xb7bcr` (console) — all spec-ratified,
   dispatch-ready; accept-on-behalf after live-exercise evidence.
2. **CO1** `livespec-bj9x.1` (core reaper refactor) + **CO2** (file
   needs-attention-internal/-fleet local CORE skills) — core-tenant dispatch
   churns the pin → fresh session / session-end.
3. **bd-ib-z2ctra build** (openbrain durable unblock; groom cut DRAFTED —
   slices A/B/C/D1/D2a + NEW **E** = dispatcher resolves `dispatcher.fabro_home`;
   DROP the parameterized-prepare sub-goal) — needs maintainer approval of the cut.
4. **EXIT GATE:** surface closing `livespec-bj9x` when every piece is done.
Follow-ups: git-jsonl skill-count drift; fresh-worktree worktree-pack hydration
(`just install-worktree-pack`).

## Gate map

| Step | Overseer does | Maintainer gate |
|---|---|---|
| Dispatch RT1/OR1 | dispatches ready items through the factory; closes each landed item after journaling live-exercise evidence | **accept-on-behalf is STANDING for this track** (no per-batch ask) |
| SP2 spec | drives push + spawns independent CODEX review; surfaces ratification | **spec ratification** (+ mandatory independent review) |
| Next-wave code | files ripe slices; dispatches through the factory | groom / approve per item as needed |
| Close | surfaces the exit gate | **exit gate** (close the epic) |

## Standing authorizations + operating disciplines (this track only)

Maintainer-declared 2026-07-06 for the `needs-attention` track (epic
`livespec-bj9x`) **only** — NOT system-wide, NOT permanent; these expire when
the epic closes. Also journaled on the epic (read them there too, via the
read-first chain).

- **Auto-acceptance (accept-on-behalf) is authorized for EVERY item in this
  track, and PERSISTS ACROSS overseer handoffs.** A fresh overseer does NOT
  re-ask — it closes each landed item (`acceptance → done` via the `accept:`
  valve) without prompting the maintainer. **Guardrail (unchanged):** accept an
  item ONLY after live-exercise evidence is journaled on it (the "done means
  exercised live" discipline); weak or absent evidence → HALT and surface that
  item, never accept on faith. Covers the RT1+OR1 batch and every future slice
  (RT2, OR2/OR3, CO1/CO2, CN1, BR1–4, and any follow-ups).
- **Do not surface a handoff / rotation gate until the overseer's context
  exceeds ~50%.** Below that, keep driving autonomously — never park ready work
  behind a "my context is heavy" rationale.
- **Run non-factory work in scoped subagents** (doc PRs, spec propose-change /
  revise authoring, independent adversarial reviews, grep-migrations) to keep
  the overseer context lean; the overseer retains plan / dispatch / synthesis
  and the maintainer-gated exit.

## Standing constraints

- Status is derived from the ledger, never stored here (no shadow queue).
- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; never `--no-verify`.
- Ripe work is built factory-side under the janitor gate, never hand-coded.
- **NEVER hand-edit `~/.claude/plugins/installed_plugins.json`** (it is a
  per-project registry; a manual dedup corrupted it and was reverted from a
  backup). **NEVER lever the currency gate** (no `LIVESPEC_CORE_PLUGIN_ROOT`
  override, no `--no-verify`) per `.ai/ci-gate-discipline.md`; if a livespec
  CLI reports "stale", `/reload-plugins` and retry.
- Independent adversarial review is REQUIRED before every ratification — use a
  separately-spawned **CODEX** sub-agent (Fable is out of free usage; Opus 4.8
  is an acceptable fallback).
- Loose ends: reap the obsolete `needs-attention-sp1-revise` worktree; keep
  `needs-attention-sp2-attention-rename` (parked SP2 proposal).
- Observability/telemetry is deferred (`design.md` §"Deferred") — out of this rollout.
