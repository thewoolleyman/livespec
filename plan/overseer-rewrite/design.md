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
   "tmux":"livespec:collector-otel-rename",
   "handoff":"/data/projects/livespec/plan/collector-otel-rename/handoff.md",
   "resume":"read /data/projects/livespec/plan/collector-otel-rename/handoff.md and follow it",
   "epic":"livespec-xxxx","ctx_threshold":50,"pinned_session_id":null,
   "added_at":"2026-07-12T13:00:00Z"}
  ```

  Append to add; rewrite-filter to remove; `epic` optional (plan-driven → can
  show `%Complete`; unassigned/watch-only → `—`). **The tmux session name is
  repo-qualified `<repo-slug>:<topic>`** (the `claude -n` display name stays the
  bare topic for humans) — because tmux session names are GLOBAL while plan
  topics are only unique per repo (adversarial-review blocker #8; two repos with
  the same topic would otherwise collide). The daemon **auto-links** a live tmux
  session to a row only when the `(repo, topic)` match is unambiguous AND the
  session's `#{pane_current_path}` resolves inside the row's `repo` — never by
  topic name alone.

- **Displayed table** = discovery LEFT-JOIN mapping. Columns:
  `Topic · Repo · tmux · Ctx% · Status` (+ optional `%Complete` for rows with
  an `epic`, refreshed on a slower cadence to avoid hammering beads). A row with
  no mapping shows blank `tmux`/`Ctx%` and status `unassigned`.

### Per-track state machine (daemon-driven)

Signals come from the trusted channels in "### Signal sources" below, NOT from
raw whole-pane text. **State precedence is evaluated top-to-bottom** — `working`
and `blocked:human` are detected BEFORE any injection can occur.

| State | Trigger | Daemon action |
|---|---|---|
| `unassigned` | discovered, no session in mapping | show + flag *ready to start*; **never** auto-start |
| `working` | busy markers on the pane (`esc to interrupt` / `Waiting for N background` / `N shell`) | leave alone; **suppress injection** |
| `blocked:human` | structured-gate UI (permission prompt / picker) on the pane, or a `.overseer-blocked` marker file | show in table; surface to the bottom pane; **suppress injection** (never keystroke into a gate) |
| `idle` | verified idle-input state, ctx above threshold | leave alone |
| `warned` | ctx `left ≤ threshold` (default 50) **and** verified idle-input state | record an injection stamp, then **bracketed-paste** the wrap-up once; re-send once if ctx keeps climbing |
| `ready → restart` | fresh **`.overseer-ready` marker** (mtime > injection stamp, contents = daemon's `sha256sum` of the on-disk handoff) **and** no busy markers **and** verified idle-input | `respawn-pane -k -c <repo> 'claude -n <topic>'` → wait for `pane_current_command` transition → bracketed-paste resume line → delete marker → `working` |
| (removed) | `<repo>/plan/<topic>/` archived or gone | drop the mapping row; note it |
| danger | ctx ≈80% with no ready marker | **surface to the human; NEVER force-kill a session mid-work** |

### Signal sources (what is trusted from where)

- **busy** — pane markers `esc to interrupt` / `Waiting for N background` / `N shell`.
- **structured gate** — the pane's distinctive numbered-option permission/picker UI.
- **idle-input** — a *verified* normal input state: prompt box present AND no busy markers AND no structured gate. "Not busy" alone is NOT idle-input.
- **ctx %** — the anchored last-status-row parse (see "Context-% reading"); fail-closed to *unknown* on no-match.
- **readiness / blocked** — **filesystem marker files** (`.overseer-ready` / `.overseer-blocked`), NOT printed pane text (adversarial review: pane text is echo/scroll/wrap-corrupted and cannot certify "asserts X now").
- **process identity** — `#{pane_current_command}` (shell vs `node`/claude) and `#{pane_current_path}` (which repo), for restart proof and auto-link — never the `❯` glyph.

## The certification protocol (the heart of the design)

Some pane states are deterministic; one is not:

| State | Detectable from a captured pane? |
|---|---|
| Actively working | Yes — `esc to interrupt` |
| Background sub-agents / subprocess running | Yes — `Waiting for N background…`, `N shell` |
| Blocked on a **structured** gate (permission prompt, picker) | Mostly — distinctive numbered-option UI |
| Idle-and-**done** vs idle-and-**asking-a-prose-question** | **No** — both are an empty `❯` |

The last row is why the *judgment* must live in the tracked session, which alone
knows which case it is. But the session must express that judgment through a
channel Python can trust — and **pane text is NOT such a channel**
(adversarial review, 2026-07-12, blockers #1–#4): the injected instruction is
echoed back into the transcript, the model quotes tokens in narration, output
scrolls above the visible capture, and long lines wrap — any of which turns a
printed sentinel into a **false match**. So certification is **out-of-band, on
the filesystem**, never a printed line.

**The wrap-up injection.** When ctx `left ≤ threshold` AND the pane is in a
verified idle-input state (see "Signal sources"), the daemon records an
**injection stamp** (a timestamp/nonce in a sidecar) and **bracketed-pastes**
(`tmux load-buffer` + `paste-buffer -p`, never line-by-line `send-keys`, so the
multi-line body can't fragment into separate submitted prompts — blocker #2) one
wrap-up message:

```
Your context is now under {N}%. Wrap up for a clean session restart:
 1. Update {handoff} so a FRESH session can resume from it alone
    (read-first chain present, concrete next action, resume command printed).
 2. Stop every background sub-agent and subprocess you started.
 3. ONLY when genuinely at a clean stopping point with the handoff ready,
    WRITE the ready marker (do not merely print it), then stop:
        sha256sum {handoff} | cut -d' ' -f1 > {repo}/plan/{topic}/.overseer-ready
 If instead you are blocked on a human decision, write:
        echo "<one-line summary>" > {repo}/plan/{topic}/.overseer-blocked
```

**The restart interlock** requires **all** of, deterministically:

1. the **`.overseer-ready` marker file exists**, its **mtime is newer than the
   injection stamp**, and its contents equal the daemon's own `sha256sum` of the
   current on-disk `handoff.md` — this proves the session actually updated the
   handoff AND that the marker is from this round, not stale, **and**
2. no `esc to interrupt`, **and**
3. no `Waiting for N background` / `N shell`, **and**
4. the pane in a verified idle-input state.

A file write **cannot be forged by prompt-echo, cannot scroll off, and cannot
line-wrap**, so blockers #1–#4 all dissolve. Pane scraping is retained ONLY for
the busy/idle/gate signals, which are not echo-forgeable in a harmful direction.
The daemon **deletes the marker** as it restarts, so it can never re-trigger.
**Safe by construction:** no fresh, hash-matching marker → no restart; and
because the marker is written only after the handoff update, a restart always
resumes from an updated handoff.

(Secondary confirmation, optional: read the tracked session's transcript
`~/.claude/projects/<slug>/<session-id>.jsonl` and inspect the last *assistant*
message — role-aware, so it distinguishes session output from injected user
input. Kept as a cross-check only; the marker file is authoritative because the
transcript format is internal and unstable.)

**Guards.** If ctx keeps climbing with no ready marker, re-send the wrap-up once
after a few minutes; at a danger line (~80%) still with no marker, surface
"track X won't wrap up" to the human rather than force-kill.

## Context-% reading (anchored, fail-closed)

The remaining-context % comes from the global statusline
(`~/.claude/statusline-command.sh`), which prints `Ctx: N% left` from
`context_window.remaining_percentage` on the **bottom status row** of the pane
(correct for the 1M-context model automatically). Verified 2026-07-12: a live
session computed to 27% used / ~73% left against its 1M window.

Parsing is **anchored and fail-closed** (adversarial-review blocker #5): read
only the **last non-empty row** of `tmux capture-pane -p -t <session>`, strip
ANSI, and take the **last** `Ctx:\s*(\d+)%\s*left` match on that row — NEVER
`grep` the whole capture, because page content (including this very design doc)
contains the string `Ctx: N% left` and would yield a false reading. If the
status row carries no match this tick, the value is **unknown → keep the last
known value**, and unknown NEVER counts as a threshold crossing. This is the
one coupling: if the statusline stops emitting `Ctx: N% left`, ctx reads
*unknown* (the table shows "ctx unreadable"), degrading safely rather than into
a spurious wrap-up or restart.

(Transcript fallback: the last assistant `usage` block in
`~/.claude/projects/<slug>/<session-id>.jsonl` sums `input_tokens +
cache_read_input_tokens + cache_creation_input_tokens` = context fill; it
requires the session-id→file mapping and the window size, so the statusline row
is primary.)

## Restart / rename / crash recovery mechanics

- **Rename.** `claude -n <topic>` sets the session's display name in the prompt
  box, the `--resume` picker, **and the terminal title** (which tmux surfaces) —
  a cleaner equivalent of typing `/rename`, and it makes "which session resumes
  in which tmux" legible after a reboot.
- **Restart — deterministic, no screen-scraped shell prompt** (adversarial-review
  blockers #2, #7). Do NOT drive `/exit` and then guess when a shell returned:
  `❯` is ambiguously BOTH the Claude idle prompt and the zsh prompt, so a
  mis-timed "shell is back" could type `claude …` *into the still-live session*
  and corrupt it. Instead **replace the pane's process atomically**:
  `command tmux respawn-pane -k -c <repo> -t <pane> 'claude -n <topic>'` — kills
  whatever ran in the pane and launches a fresh Claude in the row's repo. The
  abrupt kill is safe: the interlock already proved the handoff is written and
  the ready marker exists, so nothing is unsaved. Then **wait for the new TUI**
  by polling `#{pane_current_command}` (→ `node`) and/or the welcome banner (not
  the prompt glyph), **bracketed-paste** the row's resume line (`load-buffer` +
  `paste-buffer -p`, so a multi-line resume can't fragment into separate
  prompts), and finally **delete the `.overseer-ready` marker** so the restart
  can't re-trigger. (`claude "<prompt>"` only pre-fills, no auto-submit — which
  is why the resume line is pasted after launch, not passed as an argv.)
- **Reboot recovery (a new strength).** A fresh overseer reads
  `~/.livespec-overseer.jsonl`, recreates any missing
  `tmux new-session -s <repo-slug>:<topic> -c <repo>`, relaunches
  `claude -n <topic>`, and bracketed-pastes each row's resume line. The
  persistent mapping makes recovery mechanical.

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
  *mechanics only*; semantic judgment stays in the tracked session's LLM,
  expressed via **out-of-band marker files** (never printed pane text —
  echo/scroll/wrap corrupt it); (2) overseer stays thin, never does track work
  inline, never polls from the Claude pane; (3) surface-only — never auto-spawn
  a session; (4) discovery-driven list, JSONL = mapping only (do not regress to
  a hand-maintained plan list); (5) cross-repo — rows repo-scoped, tmux ids
  repo-qualified, never hardcode core.
- **Load-bearing mechanics + gotchas** — `command tmux` (bypass the zsh shim);
  **bracketed-paste** (`load-buffer`+`paste-buffer -p`) for multi-line payloads,
  never line-by-line `send-keys`; the **anchored** statusline-`Ctx:` parse
  (last row only, fail-closed) and its coupling; busy-marker list; the
  `.overseer-ready`/`.overseer-blocked` **marker-file certification** (mtime >
  injection stamp + handoff-hash match; delete on restart); the restart
  interlock; **`respawn-pane -k`** restart + `#{pane_current_command}` proof (do
  NOT screen-scrape the `❯` prompt); `claude -n` sets name + terminal title;
  `--session-id` / `--resume`.
- **Build/toolchain facts** — stdlib-only Python, host-only, deliberately
  outside the product gates (footgun-guard precedent); do not wire it into
  pyright.include / coverage / import-linter.
- **How to exercise it** — the live-exercise procedure (≥2 repos, force a
  threshold crossing, watch a real restart + rename, verify archive-GC); daemon
  log location under `tmp/overseer/`.
- **Pointers** — `.ai/agent-disciplines.md` (overseer discipline, factory-
  dispatch), `SKILL.md`, the wrap-up + marker-protocol convention doc, and the
  "## Adversarial review (2026-07-12)" section of this design (the 8 blockers
  and why the mechanics are shaped as they are).

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
   anchored Ctx% parse (last status row, fail-closed), pane signal detection
   (busy-markers, structured-gate, verified idle-input), `#{pane_current_command}`
   / `#{pane_current_path}` process-identity checks, the **marker-file
   certification** read (`.overseer-ready` mtime + handoff-hash match;
   `.overseer-blocked`), bracketed-paste injection, the restart interlock via
   `respawn-pane -k`, archive-GC, and the table renderer (clear + reprint each
   loop).
2. **Registry helpers** — read/write/filter `~/.livespec-overseer.jsonl`
   (repo-qualified tmux ids, injection-stamp sidecar) and the discovery ⋈
   mapping join.
3. **Rewritten `SKILL.md`** (bottom pane, thin) — builds the 2-pane layout,
   starts the daemon, takes plain-text commands, surfaces gates.
4. **Wrap-up + marker-protocol convention doc** — the wrap-up text and the
   `.overseer-ready` / `.overseer-blocked` marker contract (what the session
   writes, what the daemon validates), referenced by `SKILL.md` and by tracked
   sessions' handoffs.
5. **Maintenance `AGENTS.md`** (+ symlink, + optional `.ai/`) — as above.
6. **Retire `livespec-overseer-startup.md`** — fold live bits into `SKILL.md`.

## Build phases

1. Registry schema + read/write/GC helpers (+ tests).
2. Signal detection: anchored Ctx% parse, busy-markers, structured-gate,
   verified idle-input, `pane_current_command`/`pane_current_path`, and the
   marker-file certification read — against captured-pane + on-disk fixtures
   (+ tests).
3. `supervisor.py` wiring the above (bracketed-paste injection, `respawn-pane`
   restart); the table renderer.
4. Rewrite `SKILL.md`; author the wrap-up + marker-protocol convention doc; add
   the maintenance `AGENTS.md` (+ symlink); retire `livespec-overseer-startup.md`.
5. **Live exercise** (per "done means exercised live"): 2–3 real tracks across
   ≥2 repos, force a threshold crossing, watch a real auto-restart + rename,
   verify archive-GC and reboot-recovery from the mapping file.

Tests for the host-only Python live beside it (they are not part of the product
`tests/` tree, which mirrors `.claude-plugin/scripts/` + `dev-tooling/`). Phase
1 confirms no repo-wide `.py` gate objects to the daemon's location.

## Open / deferred (non-blocking)

- **`.overseer-blocked` marker as a standing convention.** Whether to bake
  "write `.overseer-blocked` when you stop to ask the human" into tracked-session
  handoffs for airtight blocked-detection, vs. accepting the cosmetic
  prose-question gap (a prose question with no marker shows as `idle` in the
  table; the restart stays safe regardless, since restart requires the
  `.overseer-ready` marker). Decide in Phase 4.
- **`%Complete` cadence.** Reading epic `%Complete` needs the credential wrapper
  + tenant; keep it off the fast ~10s loop (slow refresh or on-demand from the
  bottom pane) to avoid hammering beads.

## Adversarial review (2026-07-12)

Before implementation, this design was reviewed READ-ONLY by two independent
adversarial reviewers — a **Fable**-model agent (8 findings) and a **Codex**
agent (5 findings, a corroborating subset). Both affirmed the **architecture**
(deterministic daemon, discovery ⋈ mapping, surface-only, judgment-in-the-
tracked-session) and found the blockers entirely in the **pane-signal
mechanics**. The unifying lesson: **a pane's text stream cannot carry a
trustworthy "the session asserts X now" signal** — prompt-echo, model
quotation, scroll, and line-wrap all corrupt it — so certification moved
out-of-band to the filesystem, and state detection to tmux process metadata.
All 8 are resolved in the mechanics above:

| # | Blocker | Resolution (folded in above) |
|---|---|---|
| 1 | Injected wrap-up contains the exact `OVERSEER-READY-TO-RESTART:` string → echo → false restart before the handoff was updated | Certification is an **out-of-band `.overseer-ready` marker file** (mtime > injection stamp, contents = daemon's `sha256sum` of the on-disk handoff); un-echoable, this-round, hash-validated |
| 2 | Multi-line `send-keys` submits the bare sentinel line as its own prompt | **Bracketed paste** (`load-buffer` + `paste-buffer -p`) for all multi-line payloads |
| 3 | A printed sentinel can scroll above the visible capture | Moot — the marker is a file (mtime-ordered), not screen text |
| 4 | The long `…handoff.md` path line-wraps, breaking the exact match | Moot — file-based; any residual token is short + registry-verified |
| 5 | Unanchored `grep 'Ctx:'` matches `Ctx: N% left` in page content | Parse **only the last status row**, last match, ANSI-stripped, no-match ⇒ *unknown/keep-last* (fail-closed) |
| 6 | Injecting keystrokes while a permission/picker gate is up can approve actions | **State precedence** — `working`/`blocked:human` detected first; inject only in *verified idle-input* |
| 7 | `/exit` shell-prompt detection is ambiguous (`❯` dual-use) → can type into the live session | **`respawn-pane -k`** atomic process replacement + `#{pane_current_command}` proof; no prompt-glyph scraping |
| 8 | Auto-link by topic alone cross-links two repos sharing a topic | **Repo-qualified** tmux id `<repo-slug>:<topic>` + `#{pane_current_path}` verification before linking |

Nits were ignored per the review scope. The reviews are the reason the
"certification protocol", "Context-% reading", "Restart mechanics", and
"Signal sources" sections read as they do.

## Live-exercise corrections (2026-07-13)

The live exercise (Phase 5 — driving the daemon against a REAL Claude TUI in an
isolated scratch tmux session) validated the mechanics end-to-end and corrected
THREE pane-parsing assumptions the mocked unit tests had baked in. The mocked
tests all passed while the real behavior was wrong — exactly why "done means
exercised live." Fixes landed in `signals.py` + `supervisor.py` (+ real-shape
test fixtures):

| # | Assumption (wrong) | Reality (verified live) | Fix |
|---|---|---|---|
| 1 | statusline is the LAST pane row | it is the SECOND-to-last — a footer hint (`⏵⏵ …` / `? for shortcuts`) renders below it | `parse_ctx_remaining` scans the last few rows (`_CTX_TAIL_ROWS`), still bounded to preserve the anti-false-match intent |
| 2 | idle prompt is a `╭─╮` box + `? for shortcuts` | it is an EMPTY `❯` between horizontal rule lines | `is_idle_input` detects that structural shape (glyph/hint-independent), prompt required EMPTY |
| 3 | busy = `esc to interrupt` | that string is not shown while streaming; the busy indicator is a `✻ … (… · Ns · ↓ tokens)` spinner — AND during main token-streaming NO persistent spinner is captured at all (the pane looks idle) | `is_busy` keys on the spinner content; the daemon adds a two-capture **settled-delta** (`_pane_settled`) so a changing pane reads `working` |

Two things the live exercise CONFIRMED WORKING as designed:

- **Submission** — a bracketed paste (`load-buffer` + `paste-buffer -p`, single-
  or multi-line) submits with a single `Enter` on a STEADY idle session; the old
  "repeat-Enter" concern is NOT a `send-keys -l` payload-collapse problem (the
  paste is always atomic). BUT the restart+rename validation found a real
  fresh-TUI **submit-timing** bug: a freshly-`respawn`-ed session is still drawing
  its welcome/news screen when the first `Enter` arrives and DROPS it, leaving the
  resume line un-submitted and the auto-restart stalled. Fixed by a verify loop in
  `_submit_prompt` (re-send `Enter` until `signals.input_box_ready`); validated
  live — the restarted session then reads its handoff and follows the resume line
  unattended. The atomic-paste mechanic itself is correct.
- **Restart + rename** — `respawn-pane -k 'claude -n <topic>'` validated live: the
  pane's PID changes (old process killed, fresh Claude launched), the old
  session's context is gone (fresh), and the `-n <topic>` name shows in the input
  box header (`──── <topic> ──`).
- **`is_structured_gate`** — caught a real first-run trust prompt
  (`❯ 1. Yes …`), correctly suppressing injection.

Where the inline "### Signal sources", "Context-% reading", and state-machine
`busy` descriptions above differ from this section, THIS section and the shipped
`signals.py` / `supervisor.py` govern.

**Known assumption recorded here:** a restart (`respawn-pane -k 'claude -n …'`)
assumes the managed repo is already Claude-*trusted* (governed repos the
maintainer runs are). In a never-trusted dir, the first-run trust prompt would
intervene before the resume-line paste; managed repos do not hit this.

## House rules (this repo)

- Repo mutations go `worktree → PR → rebase-merge`; never commit on the primary
  checkout; never `--no-verify` (`mise exec -- git …` so the hooks fire).
- Beads via the env wrapper:
  `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C <repo> <args>`.
- Secrets are probe-only (`printenv NAME | wc -c`); never echo values.
- Scratch under `tmp/overseer/` (never the `tmp/` root; it is maintainer-owned).

## This skill is local-only and PERMANENT

It lives under `.claude/skills/overseer/` in *this* repo and is usable **only
from this repo**; it is **not** part of the livespec plugin, the spec, the copier
template, or any fleet-propagated surface — do not add it to manifests,
conformance checks, or other repos. It is a **permanent, human-supervised
alternate to autonomous mode** (the Beads/Dolt + Fabro Dispatcher / dark
factory), NOT a stopgap awaiting the console cockpit: the two are standing peers —
autonomous mode runs ready work-items unattended through the ledger, while the
overseer keeps interactive plan tracks moving in parallel under a human driver.
Maintain it in place.
