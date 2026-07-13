# Handoff — overseer `adopt` is BROKEN (wrong match key); two-pane split works

**Status (2026-07-13):** The two-pane bootstrap (`overseer-start` splitting its
OWN window) WORKS and is live-proven. But the **`adopt` pass is BROKEN**: it
found ZERO of the maintainer's real worker sessions. The prior session
misimplemented the match key AND tested against a synthetic session that matched
its own wrong interpretation instead of the maintainer's REAL sessions. This
handoff carries the exact root cause, the real-session test oracle, and the
testing discipline the fresh session MUST follow. **Owning session:** livespec
core, "overseer-rewrite". **HOLD on archive still stands.**

## THE FAILURE (what the maintainer hit)

The maintainer ran `/overseer` in the `livespec-overseer` tmux session. The
daemon top pane came up fine (split works), but **adopt detected NONE of the
existing tmux sessions** — including the ones running claude/codex on plan topics
that SHOULD have been auto-tracked. Absolute failure of the adopt requirement.

## ROOT CAUSE A — adopt matches the wrong thing (the primary bug)

`Supervisor.adopt_sessions` (in `.claude/skills/overseer/supervisor.py`, merged in
PR #1177) matches **`topic == the tmux SESSION NAME`**. That is WRONG. The
maintainer launches each worker with **`claude -n <topic>`** (or the codex
equivalent), which sets the **terminal/pane TITLE** to the topic — NOT the tmux
session name. The tmux session names are generic (`livespec`, `livespec1`,
`livespec-autonomous-mode`); the TOPIC lives in `#{pane_title}` as
`<status-glyph> <topic>`.

**Real evidence (captured live 2026-07-13 via `tmux list-panes -t <s> -F ...`):**

| tmux session | `#{pane_title}` | cmd | cwd | topic (glyph-stripped) | active plan in cwd-repo? | adopt? |
|---|---|---|---|---|---|---|
| `livespec` | `✳ driver-hook-body` | claude | /data/projects/livespec | driver-hook-body | YES | **ADOPT → tmux=`livespec`** |
| `livespec1` | `✳ codex-acp-auto-bump` | claude | /data/projects/livespec | codex-acp-auto-bump | YES | **ADOPT → `livespec1`** |
| `livespec2` | `✳ ledger-status-conformance` | claude | /data/projects/livespec | ledger-status-conformance | YES | **ADOPT → `livespec2`** |
| `livespec4` | `⠂ overseer-rewrite` | claude | /data/projects/livespec | overseer-rewrite | YES | **ADOPT → `livespec4`** |
| `livespec-autonomous-mode` | `✳ console-autonomous-mode` | claude | /data/projects/livespec | console-autonomous-mode | NO (not a plan in livespec) | skip |
| `livespec3` | `⠹ livespec` | bun | /data/projects/livespec | livespec | NO (not a topic) | skip |
| `resume2`, `vps-info` | `✳ Claude Code` | claude | (outside fleet) | — | — | skip |
| `openclaw-info` | `✳ Review bench …` | claude | /data/projects/fabro | — | — | skip |

**The fix:** adopt must match by the **pane TITLE**, stripped of the leading
status glyph + whitespace (e.g. `✳ driver-hook-body` → `driver-hook-body`;
`⠂ overseer-rewrite` → `overseer-rewrite`), compared against the ACTIVE plan
topics in the pane's cwd-repo — and map to the **tmux SESSION holding that pane**
(`tmux == session`). The three guards stay: (a) cwd inside a fleet repo, (b)
running a claude/codex worker, (c) the glyph-stripped title is an active topic in
that repo. Guard (c) naturally rejects `✳ Claude Code`, `⠹ livespec`, etc.

**TEST ORACLE — a correct adopt against the CURRENT real fleet MUST adopt exactly
these 4** (verify by name; the set may drift, so always re-derive it live):
`livespec→driver-hook-body`, `livespec1→codex-acp-auto-bump`,
`livespec2→ledger-status-conformance`, `livespec4→overseer-rewrite`.
Active livespec plan topics right now: autonomous-mode, cloud-local-memory-cleanup,
codex-acp-auto-bump, collector-otel-rename, driver-hook-body,
fabro-ci-image-factoring, factory-safe-by-default, greenfield-install-experience,
ledger-status-conformance, overseer-rewrite.

## ROOT CAUSE B — flaky `display-message` read (latent, must fix too)

`tmuxio.pane_current_command` / `pane_current_path` / `pane_id` all read via
`tmux display-message -p -t <session> '#{...}'`. **That returns EMPTY for most
DETACHED sessions** (verified live: a system-wide loop returned empty
window/title/cmd/path for ~19 of 21 sessions, while a single retry sometimes
returned a value — it is inconsistent). **`tmux list-panes -t <session> -F
'#{...}'` (first/active pane) is RELIABLE** — it returned the real cmd/path/title
for every session, every time. So even after fixing the match key, adopt (and
likely the daemon's per-tick `auto_link` / identity gate / ctx reads) will still
intermittently see `None` and skip real sessions.

**The fix:** switch tmuxio's per-session pane reads to `list-panes -t <session>
-F '#{...}'` (take the active/first pane), and add a `pane_title(session)`
accessor the same way. INVESTIGATE whether the daemon's other display-message
readers are affected the same way and fix them consistently (this may be why the
daemon has only ever been "validated" against fresh/attached scratch sessions,
never the maintainer's real detached ones).

## Worker-detection nuance (codex runs as `bun`)

A claude session's `#{pane_current_command}` is `claude`. A **codex** session's is
**`bun`** (codex-cli runs through bun) — e.g. `livespec3` above is `cmd=bun`.
`signals.pane_is_worker` currently accepts `{node, claude, codex}` — it is MISSING
`bun`. Add it (the strong title==active-topic + in-fleet-repo guards keep a stray
non-codex `bun` app like `openbrain` out). VERIFY live what a real codex session's
`pane_current_command` actually is before finalizing (it was `bun` here).

## What ALREADY WORKS (do NOT rebuild — merged in PR #1177, release 0.10.0)

- **`overseer-start`** two-pane bootstrap: reads `$TMUX_PANE` (Claude Code DOES
  inherit it), splits its OWN window (`tmux split-window -v -b -d -P -F
  '#{pane_id}' -t $TMUX_PANE`), runs `overseerd` in a TOP pane titled
  `overseer-daemon`, keeps focus on the bottom pane, idempotent via the pane
  title, never grabs another session. PROVEN live, including in the maintainer's
  own `livespec-overseer` session (it currently has a `%NN title=overseer-daemon`
  daemon pane + the `%20` claude bottom pane). This part is CORRECT — keep it.
- `tmuxio.split_window_top` / `set_pane_title` / `window_pane_titles`;
  `signals.pane_is_worker`; the `adopt` subcommand + `Supervisor.adopt_sessions`
  skeleton; SKILL.md runs `overseer-start` first. Only the adopt MATCH KEY (title
  vs session name) + the flaky read + the missing `bun` are wrong.

## Verified environment facts (trust these; re-verify only if suspicious)

- `command tmux` = tmux 3.5a (bypass the zsh alias). Claude Code's bash inherits
  `$TMUX`/`$TMUX_PANE`. `claude -n <topic>` sets `#{pane_title}` to
  `<status-glyph> <topic>` (glyphs seen: `✳ `, `⠂ `, `⠹ `, `⠇ `).
- **`list-panes -t <session> -F` is the reliable per-session read; `display-message
  -t <session>` is flaky for detached sessions** (Root Cause B).
- `overseerd` uv shebang works with a NORMAL `$HOME` (warm `~/.cache/uv`). Do NOT
  isolate a test with `HOME=<empty dir>` — that cold-rebuilds uv's cache and HANGS
  (a long red herring last time). To isolate the store instead, inject
  `store_path=` on the `Supervisor` dataclass (tests do this) or symlink
  `~/.cache` into the scratch HOME.
- **Beside-tests are the ONLY code gate on this folder:** `uv run pytest
  .claude/skills/overseer/ -q` (currently 115 green). CI does NOT run them. Run
  them before every push.
- The maintainer has an overseer daemon RUNNING in `livespec-overseer` (holds the
  singleton lock). A second daemon will refuse to start. Work around it (test the
  adopt logic directly / against a scratch store) or coordinate.

## Testing discipline the fresh session MUST follow (the lesson)

The prior session's fatal mistake: it "proved" adopt by creating a SYNTHETIC tmux
session literally NAMED as a topic — i.e. it tested its own WRONG interpretation,
not the maintainer's real setup. NEVER do that. Instead:

1. **System-wide census FIRST.** `tmux list-sessions` + `list-panes -t <s> -F
   '#{pane_title} #{pane_current_command} #{pane_current_path}'` for EVERY session.
   Understand how the REAL sessions surface their topic (the pane title) before
   writing any match logic.
2. **Test against the REAL sessions, not synthetic ones.** Run adopt against the
   live fleet and assert it produces the TEST ORACLE set above (re-derived live).
   A synthetic session may only be added to cover a case the real fleet lacks —
   never as the primary proof.
3. **Exploratory-test THREE times**, end-to-end, that adopt assigns the real
   matching sessions and the daemon table then shows them assigned — BEFORE
   handing back to the maintainer. Clean up any test writes (restore
   `~/.livespec-overseer.jsonl`).
4. Beside-tests green + the three live runs, THEN hand back. Never ask the
   maintainer to manually test unverified behavior.

## Files to change (all under `.claude/skills/overseer/`)

- `supervisor.py` — `adopt_sessions`: match glyph-stripped `pane_title` against
  active topics; map to the session; keep the 3 guards + no-double-add.
- `tmuxio.py` — add `pane_title(session)`; switch per-session pane reads to
  `list-panes -t <session> -F` (reliable). Consider a single `pane_facts(session)`
  that returns (title, cmd, path) in one reliable call.
- `signals.py` — `pane_is_worker`: add `bun` (codex). Add a glyph-strip helper
  (e.g. `strip_title_glyph`) or do it in supervisor.
- Beside-tests — update the adopt tests to the title-based match (FakeTmux needs a
  `pane_title` + titles carrying a leading glyph); test the flaky-read fix.
- SKILL.md / AGENTS.md — update the adopt description (match by the
  `claude -n <topic>` pane title, not the session name).

## Resume command

`read plan/overseer-rewrite/handoff.md and follow it`
