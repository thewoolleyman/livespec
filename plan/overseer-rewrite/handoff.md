# Handoff — overseer `adopt` FIXED (matches the `claude -n` border topic)

**Status (2026-07-13): DONE + merged (PR #1186, livespec core).** The `adopt`
pass now correctly picks up the maintainer's `claude -n <topic>` worker sessions.
The two-pane bootstrap (`overseer-start`) was already live-proven and is
unchanged. **HOLD on archive still stands** — this thread is complete but kept
per the maintainer's standing hold. **Owning session:** livespec core,
"overseer-rewrite".

## What was wrong (and the corrected understanding)

The prior `adopt` matched **`topic == the tmux SESSION NAME`**. Real worker
sessions have GENERIC names (`livespec`, `livespec1`, `livespec2`), so adopt
found zero. That was the whole failure (Root Cause A).

The prior handoff proposed matching the **pane TITLE** (`#{pane_title}`). That is
**fragile and was NOT adopted**: Claude Code **drifts the terminal title to a
generated task summary** — proven live on the very session that wrote the prior
handoff (its title was `Follow overseer rewrite handoff plan`, not
`overseer-rewrite`). The stable signal is the **`claude -n <topic>` name Claude
Code renders into the input-box BORDER** (`─── <topic> ──`).

## The fix (merged)

- **`signals.parse_border_topic`** — reads the `-n` topic from the border line
  immediately ABOVE the bottom-most `❯` prompt. ANCHORED to the input box (not a
  bounded tail scan), so scrolled page content and long output can't false-match,
  and there is no fragile row limit. Pure-rule border (no `-n`) → None; codex `›`
  prompt → None.
- **`adopt_sessions`** matches that border topic against active plan topics under
  the same three guards (fleet-repo cwd, worker command, active-topic).
- **`tmuxio` per-session reads go through `list-panes`** (reliable), not
  `display-message`, with `#{pane_id}` filtering preserving RB3 exactness.
- **`bun` added to the worker set** (codex runs via bun).

## Correct behavior verified LIVE (3× against the real fleet, scratch store)

adopt now adopts every claude `-n` session whose border topic is active, and
correctly SKIPS: codex/bun sessions (no titled border), sessions launched without
`-n` (pure-rule border), non-active-topic borders, and out-of-fleet sessions.

**The oracle DRIFTS — always re-derive it live.** The prior handoff's set of 4 is
stale; when this landed the live-correct set was 2 (`livespec1→codex-acp-auto-bump`,
`livespec2→ledger-status-conformance`), because the maintainer had moved
`driver-hook-body` onto a codex session (`livespec`, `bun`) and this session
(`overseer-rewrite`) was launched without `-n`.

## Known gaps / notes

- **Root Cause B (flaky `display-message`) did NOT reproduce** — 21/21 sessions,
  repeatedly, identical to `list-panes`. Reads route through `list-panes` anyway
  (the reliable primitive); the daemon's per-tick pane-id identity reads were left
  on the verified path.
- **codex adoption is NOT supported yet (documented gap).** Codex renders a
  different UI (`› ` prompt, no `─── <topic> ──` border); its topic sits in the
  status line (`… · <topic> · Main [default]`). A codex-specific signal would be
  needed to adopt codex/bun sessions. `bun` is in the worker set but yields no
  border → skipped (never mis-adopted).

## Where the code lives

`.claude/skills/overseer/` — `signals.py` (`parse_border_topic`, `bun`),
`tmuxio.py` (`_pane_field` list-panes reads), `supervisor.py` (`adopt_sessions`),
beside-tests (128 green), `SKILL.md` / `AGENTS.md` (adopt docs). Gate:
`uv run pytest .claude/skills/overseer/ -q`.

## Resume command

Nothing to resume — the adopt fix is complete and merged. If codex adoption is
wanted next, the entry point is a codex status-line topic parser feeding the same
`adopt_sessions` guard.
