# Design — rewrite the overseer as a deterministic multi-track supervisor

**Status:** DESIGN RATIFIED (2026-07-12), not yet built. **Owning session:**
livespec core, session "overseer-skill", 2026-07-12. This document is the
durable design record; `handoff.md` beside it is the self-sufficient resume
entry point.

## Bottom line

Replace the current markdown-only overseer skill with a **deterministic
top-pane supervisor daemon** (plain Python) that keeps multiple parallel
livespec plan tracks moving across tmux sessions. Each track is a Claude Code
session running a plan thread in some repo. The daemon watches every tracked
session's **context %**, and when a session crosses a threshold it injects a
wrap-up instruction; the session updates its own `handoff.md`, certifies it is
at a clean stopping point by printing a **sentinel line**, and the daemon then
**restarts that session with a fresh context** (renamed to the plan topic) and
pastes the resume line as the first prompt. The list of tracks is
**auto-discovered** from each watched repo's `plan/` directory; a persistent
`~/.livespec-overseer.jsonl` stores only the durable **topic↔tmux-session
mapping** needed for crash/reboot recovery.

The load-bearing idea: **the tracked session's own LLM makes every semantic
judgment** ("am I done? is the handoff good? are my sub-agents stopped?") and
expresses it as a machine-readable token; **Python only pattern-matches the
token** plus a deterministic busy-marker cross-check. No semantic inference in
Python, and no overseer-LLM context spent watching.

## Why rewrite — the current skill and its history

The current overseer is **two markdown files, no code**, and they disagree:

- **`.claude/skills/overseer/SKILL.md`** (the "lean" rewrite) — a Monitor-based
  coordinator with **no persistent registry** (explicitly: the watch-set lives
  only for the current session), tracks classed as "plan-driven" or
  "watch-only", stall detection via the harness `Monitor` tool, central rule =
  factory-dispatch (never hand-code impl inline).
- **`.claude/skills/overseer/livespec-overseer-startup.md`** — the older
  three-pane dashboard runbook (table top-left / notes+clock top-right /
  interactive below), most of whose body is spent phase content from late June.

The lean rewrite abandoned the panes and went Monitor-based; the startup file
still describes the dashboard. That drift is itself a reason to consolidate.

Two prior failure modes are why the design is shaped the way it is, and they
MUST NOT recur:

1. **Inline-worker context blowup** — a session ran the overseer window as an
   inline worker (did the track work itself), blew up its own context, and
   autocompacted.
2. **Frozen top-pane snapshot** — a `/clear` does not kill tmux panes, so a
   prior overseer's dashboard kept rendering an hours-old "everything idle"
   snapshot while nothing was actually live.

The deterministic-daemon design defeats both: the mechanics run in a dumb,
token-free process that cannot blow up a context, and the table is re-rendered
from live captures every loop so it can never freeze on a stale snapshot.

## Ratified decisions (2026-07-12, via maintainer pickers)

1. **Loop engine = deterministic top-pane supervisor daemon** (not a
   Claude-driven loop, not a hybrid). A Claude session cannot reliably poll on
   a timer and burns its own context doing so — that is the historical killer.
2. **Judgment = tracked-session sentinel.** The session certifies its own
   done/blocked state; Python matches the token. Judgment never moves into
   Python or the overseer LLM.
3. **List = discovery-driven, auto-managed.** The set of tracks is scanned from
   each watched repo's `plan/` directory, not hand-maintained.
4. **`~/.livespec-overseer.jsonl` = mapping store only.** It holds the durable
   topic↔tmux-session mapping (+ pinned session id, custom resume line,
   threshold override) — only facts that cannot be rederived from the
   filesystem.
5. **Surface-only.** For a discovered plan with no session, the overseer shows
   it as `unassigned` and flags it startable, but **never spawns a session on
   its own**. Starting a plan is a deliberate act (the maintainer, or a
   one-word command in the bottom pane).
6. **Cross-repo by construction.** Rows are repo-scoped; the mechanics never
   hardcode `/data/projects/livespec`. Any fleet or adopter repo with a local
   checkout + a tmux session is driven identically.
7. **Language = plain stdlib-only Python**, host-only, under
   `.claude/skills/overseer/`, deliberately **outside** the product gates
   (`pyright.include`, coverage, import-linter) — precedent:
   `.claude/hooks/livespec_footgun_guard.py`.

## Architecture

Two panes in the overseer's own tmux window:

- **Top pane = `supervisor.py`** — a stdlib Python daemon that both *acts* and
  *renders the table*. No LLM, no tokens.
- **Bottom pane = the thin interactive Claude `/overseer`** — starts the
  daemon, takes plain-text commands (start/assign/unassign a plan, add/remove
  an off-manifest repo, pause), surfaces gates and blocked tracks WITH a
  recommendation. It does NO track work and never polls.

### The list = discovery ⋈ mapping

- **Discovery.** For each watched repo, scan `<repo>/plan/*/` excluding
  `plan/archive/**`. Every unarchived plan topic is a row — **including those
  with no session** (`unassigned`, flagged *ready to start*).
- **Watch-set.** Default = repos with a local checkout that have a `plan/` dir,
  seeded from `.livespec-fleet-manifest.jsonc` (fleet members + adopters), with
  a manual override for anything off-manifest.
- **Mapping (`~/.livespec-overseer.jsonl`).** One JSON object per assigned
  plan, e.g.:

  ```jsonc
  {"topic":"collector-otel-rename","repo":"/data/projects/livespec",
   "tmux":"collector-otel-rename",
   "handoff":"/data/projects/livespec/plan/collector-otel-rename/handoff.md",
   "resume":"read /data/projects/livespec/plan/collector-otel-rename/handoff.md and follow it",
   "epic":"livespec-xxxx","ctx_threshold":50,"pinned_session_id":null,
   "added_at":"2026-07-12T13:00:00Z"}
  ```

  Append to add; rewrite-filter to remove; `epic` optional (plan-driven → can
  show `%Complete`; unassigned/watch-only → `—`). The daemon **auto-links** a
  live tmux session whose name matches a discovered topic (so restarting the
  overseer re-adopts running sessions with no manual step).

- **Displayed table** = discovery LEFT-JOIN mapping. Columns:
  `Topic · Repo · tmux · Ctx% · Status` (+ optional `%Complete` for rows with
  an `epic`, refreshed on a slower cadence to avoid hammering beads). A row with
  no mapping shows blank `tmux`/`Ctx%` and status `unassigned`.

### Per-track state machine (daemon-driven)

| State | Trigger (from live pane capture) | Daemon action |
|---|---|---|
| `unassigned` | discovered, no session in mapping | show + flag *ready to start*; **never** auto-start |
| `working` | `esc to interrupt` / `Waiting for N background` / `N shell` present | leave alone |
| `idle` | idle at `❯`, `Ctx: left` above threshold | leave alone |
| `warned` | `Ctx: left ≤ threshold` (default 50) | inject wrap-up once; re-send once if ctx keeps climbing |
| `blocked:human` | structured-gate UI (permission prompt / picker) or `OVERSEER-BLOCKED-ON-HUMAN` sentinel | show in table; surface to the bottom pane |
| `ready → restart` | `OVERSEER-READY-TO-RESTART:<exact handoff path>` **and** no busy markers **and** idle at `❯` | `/exit` → wait for shell → `claude -n <topic>` → wait for banner → paste resume line → `working` (fresh context, renamed) |
| (removed) | `<repo>/plan/<topic>/` archived or gone | drop the mapping row; note it |
| danger | ctx ≈80% with no sentinel | **surface to the human; NEVER force-kill a session mid-work** |

## The sentinel protocol (the heart of the design)

Some pane states are deterministic; one is not:

| State | Detectable by regex from a captured pane? |
|---|---|
| Actively working | Yes — `esc to interrupt` |
| Background sub-agents / subprocess running | Yes — `Waiting for N background…`, `N shell` |
| Blocked on a **structured** gate (permission prompt, picker) | Mostly — distinctive numbered-option UI |
| Idle-and-**done** vs idle-and-**asking-a-prose-question** | **No** — both are an empty `❯` |

The last row is why judgment must live in the tracked session, which alone
knows which case it is. When the daemon sees `Ctx: left ≤ threshold`, it injects
(via the send-keys mechanic) one wrap-up message:

```
Your context is now under {N}%. Wrap up for a clean session restart:
 1. Update {handoff} so a FRESH session can resume from it alone
    (read-first chain present, concrete next action, resume command printed).
 2. Stop every background sub-agent and subprocess you started.
 3. ONLY when you are genuinely at a clean stopping point with the handoff
    ready, print this exact line by itself, and then stop:
        OVERSEER-READY-TO-RESTART: {handoff}
 If instead you are blocked on a human decision, print this and stop:
        OVERSEER-BLOCKED-ON-HUMAN: <one-line summary of what you need>
```

The restart interlock then requires **all four**, deterministically:

1. `OVERSEER-READY-TO-RESTART: <the exact registry handoff path>` in the
   capture, **and**
2. no `esc to interrupt`, **and**
3. no `Waiting for N background` / `N shell`, **and**
4. the pane idle at `❯`.

If the sentinel is present but a busy marker still shows, the interlock fails
and it waits — belt and suspenders. **The restart is safe by construction:** a
session blocked on the human will not print the ready sentinel, so no sentinel
→ no restart, even for the prose-question case Python cannot read. Because step
1 updates the handoff *before* the sentinel, even a premature restart just
resumes from the handoff — bounded blast radius.

**Guards.** If context keeps climbing with no sentinel, re-send the wrap-up once
after a few minutes; at a danger line (~80%) still with no sentinel, surface
"track X won't wrap up" to the human rather than force-kill.

## Context-% reading (a documented coupling)

The reader is `tmux capture-pane -p -t <session> | grep 'Ctx:'`. The global
statusline (`~/.claude/statusline-command.sh`) prints `Ctx: N% left` on the
bottom line of every pane, computed from `context_window.remaining_percentage`
(correct for the 1M-context model automatically). **This is a coupling:** if
that statusline stops emitting `Ctx: N% left`, the parser breaks. Verified
2026-07-12: a live session computed to 27% used / ~73% left against its 1M
window; the statusline JSON on stdin carries `context_window.remaining_percentage`
and the script renders `Ctx: {rounded}% left`.

(A transcript-file fallback exists — the last assistant `usage` block in
`~/.claude/projects/<slug>/<session-id>.jsonl` sums `input_tokens +
cache_read_input_tokens + cache_creation_input_tokens` = context fill — but it
requires knowing the session-id→file mapping and the window size, so the
statusline capture is primary.)

## Restart / rename / crash recovery mechanics

- **Rename.** `claude -n <topic>` sets the session's display name in the prompt
  box, the `--resume` picker, **and the terminal title** (which tmux surfaces) —
  a cleaner equivalent of typing `/rename`, and it makes "which session resumes
  in which tmux" legible after a reboot.
- **Restart.** `claude "<prompt>"` only *pre-fills* (does not auto-submit), so
  the restart uses the proven mechanic: `/exit` → wait for the shell prompt →
  `claude -n <topic>` (fresh context) → wait for the welcome banner →
  `command tmux send-keys -l "<resume line>"` + repeated `Enter` until
  `esc to interrupt`. A fresh context is the whole point; the updated handoff
  carries continuity, so `--resume` is not used for the wrap-up restart.
- **Reboot recovery (a new strength).** A fresh overseer reads
  `~/.livespec-overseer.jsonl`, recreates any missing
  `tmux new-session -s <topic> -c <repo>`, relaunches `claude -n <topic>`, and
  pastes each row's resume line. The persistent mapping makes recovery
  mechanical.

## Maintenance `AGENTS.md` in the skill folder

Per the repo's `.ai/` / `AGENTS.md` convention (a canonical `AGENTS.md` +
`.claude/CLAUDE.md -> ../AGENTS.md` symlink + optional `.ai/<topic>.md`, at any
directory level; precedent at root, `archive/`, `archive/bootstrap/`,
`templates/orchestrator-plugin/`), drop a maintenance guide at
`.claude/skills/overseer/AGENTS.md` (canonical) with the paired
`.claude/skills/overseer/.claude/CLAUDE.md` symlink, local-only and unsynced
like the skill.

It is a DIFFERENT document from `SKILL.md`, not a duplicate:

- `SKILL.md` = the overseer **at runtime** ("when invoked, do X").
- `AGENTS.md` = guidance for the **developer editing the overseer** ("when you
  change X, preserve invariant Y, watch gotcha Z, verify via W").

Content outline for `AGENTS.md`:

- **Why it exists / history** — the two failure modes above; retained-until-
  console status; local-only + unsynced (do not add to manifests, conformance
  checks, or other repos).
- **Architecture invariants that must not regress** — (1) supervisor owns
  *mechanics only*; semantic judgment stays in the tracked session's LLM via
  sentinels; (2) overseer stays thin, never does track work inline, never polls
  from the Claude pane; (3) surface-only — never auto-spawn a session; (4)
  discovery-driven list, JSONL = mapping only (do not regress to a hand-
  maintained plan list); (5) cross-repo — rows repo-scoped, never hardcode core.
- **Load-bearing mechanics + gotchas** — `command tmux` (bypass the zsh shim);
  bracketed-paste → repeated-Enter until `esc to interrupt`; the
  statusline-`Ctx:` coupling; busy-marker list; the two sentinel tokens; the
  4-condition interlock; `claude -n` sets name + terminal title;
  `--session-id` / `--resume`.
- **Build/toolchain facts** — stdlib-only Python, host-only, deliberately
  outside the product gates (footgun-guard precedent); do not wire it into
  pyright.include / coverage / import-linter.
- **How to exercise it** — the live-exercise procedure (≥2 repos, force a
  threshold crossing, watch a real restart + rename, verify archive-GC); daemon
  log location under `tmp/overseer/`.
- **Pointers** — `.ai/agent-disciplines.md` (overseer discipline, factory-
  dispatch), `SKILL.md`, and the sentinel-convention doc.

`SKILL.md` gains a one-line cross-reference pointing maintainers at `AGENTS.md`.

**Build-time verification (flagged):** confirm a nested `.claude/` dir *inside*
a skill folder does not confuse the plugin/skill loader or any structural check.
If it does, fall back to a direct `.claude/skills/overseer/CLAUDE.md ->
AGENTS.md` symlink (which Claude Code's per-directory nested-memory loader
picks up) instead of the nested-`.claude/` form. Either way the canonical
`AGENTS.md` + the SKILL.md cross-reference guarantee discoverability.

## Keep · Rewrite · Scrap (from the current skill)

| Verdict | What |
|---|---|
| **KEEP** | tmux `send-keys -l` re-engage mechanics (bracketed-paste → repeated-Enter until `esc to interrupt`); busy-marker idle detection (`esc to interrupt` / `Waiting for N background` / `N shell`); "verify live state, don't trust a session's self-summary"; worktree/house-rules boundaries; "kill every background sub-agent before handoff"; the status-table column idea |
| **REWRITE** | The operating model — add the persistent `~/.livespec-overseer.jsonl` mapping (reverses the old "no persistent registry"); collapse to 2 panes; add the context-% → wrap-up → auto-restart → rename lifecycle; make the list discovery-driven |
| **SCRAP** | The spent phase content in `livespec-overseer-startup.md`; the 50/50 top-split / "explicit row count not 33%" dashboard fiddliness. Fold the still-live bits (prime law, maintainer-interaction style, cold-start recovery) into the new `SKILL.md`, then retire the startup file. |

## Components to build

1. **`supervisor.py`** (top pane) — the loop: discovery, mapping read/write/GC,
   pane capture + parsers (Ctx%, busy-markers, sentinels, structured-gate,
   welcome-banner), wrap-up injection, the restart interlock + kill/relaunch/
   rename, archive-GC, and the table renderer (clear + reprint each loop).
2. **Registry helpers** — read/write/filter `~/.livespec-overseer.jsonl` and the
   discovery ⋈ mapping join.
3. **Rewritten `SKILL.md`** (bottom pane, thin) — builds the 2-pane layout,
   starts the daemon, takes plain-text commands, surfaces gates.
4. **Sentinel-convention doc** — the wrap-up text + the two sentinels,
   referenced by `SKILL.md` and by tracked sessions' handoffs.
5. **Maintenance `AGENTS.md`** (+ symlink, + optional `.ai/`) — as above.
6. **Retire `livespec-overseer-startup.md`** — fold live bits into `SKILL.md`.

## Build phases

1. Registry schema + read/write/GC helpers (+ tests).
2. Pane-parsers: Ctx%, busy-markers, sentinels, structured-gate, welcome-banner
   — against captured pane fixtures (+ tests).
3. `supervisor.py` wiring the above; the table renderer.
4. Rewrite `SKILL.md`; author the sentinel-convention doc; add the maintenance
   `AGENTS.md` (+ symlink); retire `livespec-overseer-startup.md`.
5. **Live exercise** (per "done means exercised live"): 2–3 real tracks across
   ≥2 repos, force a threshold crossing, watch a real auto-restart + rename,
   verify archive-GC and reboot-recovery from the mapping file.

Tests for the host-only Python live beside it (they are not part of the product
`tests/` tree, which mirrors `.claude-plugin/scripts/` + `dev-tooling/`). Phase
1 confirms no repo-wide `.py` gate objects to the daemon's location.

## Open / deferred (non-blocking)

- **`OVERSEER-BLOCKED-ON-HUMAN` as a standing convention.** Whether to bake the
  blocked sentinel into tracked-session handoffs for airtight blocked-detection,
  vs. accepting the cosmetic prose-question gap (a prose question with no
  sentinel shows as `idle` in the table; the restart stays safe regardless).
  Decide in Phase 4.
- **`%Complete` cadence.** Reading epic `%Complete` needs the credential wrapper
  + tenant; keep it off the fast ~10s loop (slow refresh or on-demand from the
  bottom pane) to avoid hammering beads.

## House rules (this repo)

- Repo mutations go `worktree → PR → rebase-merge`; never commit on the primary
  checkout; never `--no-verify` (`mise exec -- git …` so the hooks fire).
- Beads via the env wrapper:
  `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C <repo> <args>`.
- Secrets are probe-only (`printenv NAME | wc -c`); never echo values.
- Scratch under `tmp/overseer/` (never the `tmp/` root; it is maintainer-owned).

## This skill is local-only and RETAINED

It lives under `.claude/skills/overseer/` in *this* repo and is **not** part of
the livespec plugin, the spec, the copier template, or any fleet-propagated
surface — do not add it to manifests, conformance checks, or other repos. It is
RETAINED as the coordination layer and improved in place until the console
operator-cockpit (built via the factory) replaces it.
