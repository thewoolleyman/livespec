# Overseer — maintenance guide (for the developer editing it)

This is guidance for **editing the overseer**, not for running it. It is a
DIFFERENT document from `SKILL.md`:

- `SKILL.md` = the overseer **at runtime** ("when invoked, do X").
- this file = guidance for the developer **changing** the overseer ("when you
  change X, preserve invariant Y, watch gotcha Z, verify via W").

The overseer is a **deterministic multi-track supervisor**: a stdlib-Python
daemon (`supervisor.py`, the top pane) that watches parallel livespec plan
tracks across tmux sessions, plus a thin interactive Claude bottom pane
(`SKILL.md`). The daemon acts and renders a live table; it holds NO semantic
judgment. Every "am I done / blocked?" decision is made by the tracked
session's own LLM and expressed out-of-band on the filesystem
(`.overseer-ready` / `.overseer-blocked` marker files); the daemon only
pattern-matches deterministic tmux signals and those markers.

## Why it exists / history

Two prior failure modes shaped this design, and they MUST NOT recur:

1. **Inline-worker context blowup.** A session ran the overseer window as an
   inline worker (did the track work itself), blew up its own context, and
   autocompacted. → The mechanics now run in a dumb, token-free Python process
   that cannot blow up a context; the interactive pane stays thin.
2. **Frozen top-pane snapshot.** A `/clear` does not kill tmux panes, so a prior
   overseer's dashboard kept rendering an hours-old "everything idle" snapshot
   while nothing was live. → The table is re-rendered from live captures every
   tick (and time-stamped), so it can never freeze on a stale snapshot.

Status: **RETAINED** as the coordination layer until the console
operator-cockpit (built via the factory) replaces it — not retired.
**LOCAL-ONLY and unsynced:** it lives under `.claude/skills/overseer/` in this
repo only. Do NOT add it to the plugin, the spec, the copier template, fleet
manifests, conformance checks, or any other repo.

## Architecture invariants that must not regress

1. **The supervisor owns mechanics only.** Semantic judgment ("am I done / am I
   blocked?") stays in the tracked session's LLM, expressed via **out-of-band
   marker files** — NEVER inferred from printed pane text (prompt-echo, model
   quotation, scroll, and line-wrap all corrupt pane text; see the adversarial
   review). If you ever find yourself parsing a "the session says it's done"
   sentinel out of a pane capture, stop — that is the exact anti-pattern the
   marker protocol replaced.
2. **The overseer stays thin.** The interactive bottom pane never does track
   work inline and never polls the tracked sessions from the Claude pane on a
   timer. Watching is the daemon's job.
3. **Surface-only.** The daemon NEVER auto-spawns a session. Launching a plan is
   a deliberate act (`start`, user-initiated). A discovered plan with no session
   shows as `unassigned`, flagged ready to start — never started automatically.
4. **Discovery-driven list; JSONL = mapping only.** The track list is
   re-discovered from each watched repo's `plan/*/` every tick. The JSONL store
   (`~/.livespec-overseer.jsonl`) holds ONLY facts that cannot be rederived from
   the filesystem (topic↔tmux mapping, custom resume line, threshold override).
   Do NOT regress to a hand-maintained plan list.
5. **Cross-repo by construction.** Rows are repo-scoped; tmux session ids are
   repo-qualified `<repo-slug>:<topic>` (tmux names are global; plan topics are
   unique only per repo). Never hardcode `/data/projects/livespec`. Auto-link a
   live session to a discovered plan ONLY when the repo-qualified session exists
   AND its `#{pane_current_path}` resolves inside the row's repo — never by topic
   name alone.

## Load-bearing mechanics + gotchas

- **`command tmux` semantics (`tmuxio.py`).** Every tmux call is
  `subprocess.run([...], shell=False)` with an argv LIST — no shell is spawned,
  so a user's zsh `tmux` function shim is bypassed (the `command tmux` effect).
  Never build a shell string for word-splitting.
- **Bracketed paste, never line-by-line.** Multi-line payloads (the wrap-up, the
  resume line) go in via `load-buffer -` + `paste-buffer -p` so the receiving
  Claude TUI takes the whole blob as ONE pasted input that cannot fragment into
  separate submitted prompts. `send-keys -l` typing a multi-line payload would
  fragment it — do not.
- **Single-Enter submission caveat.** `_submit_prompt` pastes, sleeps briefly,
  then sends ONE `Enter` to submit. A bracketed paste is collapsed to
  `[Pasted text]`, and a single `Enter` does not always submit it. The
  historical, robust mechanic is to re-send `Enter` and re-capture the pane
  until it shows `esc to interrupt` (proof it submitted and the model is
  working). If you touch the submit path, preserve or strengthen that
  "repeat-Enter-until-`esc to interrupt`" behavior — the lone Enter is the
  known edge.
- **Anchored, fail-closed Ctx% parse (`signals.parse_ctx_remaining`).** Read the
  remaining-% from the statusline by parsing ONLY the last non-empty pane row,
  ANSI-stripped, taking the LAST `Ctx: N% left` match on that row. NEVER `grep`
  the whole capture — page content (including the overseer design doc itself)
  contains the literal string `Ctx: N% left` and would yield a false reading. No
  match on the status row ⇒ **unknown**, which keeps the last known value and
  NEVER counts as a threshold crossing. This is the one coupling: if the
  statusline stops emitting `Ctx: N% left`, ctx reads unknown and the daemon
  degrades safely (the table shows a dash) rather than into a spurious wrap-up.
- **Busy markers (`signals.is_busy`).** `esc to interrupt`, `Waiting for N
  background`, `N shell`. A liberal (over-firing) busy detector is the SAFE
  direction: a false busy merely suppresses an injection/restart; a missed busy
  is the dangerous one.
- **Marker-file certification (`signals.ready_marker_valid` /
  `blocked_marker`).** The restart interlock fires ONLY when: an injection stamp
  exists for this round, the `.overseer-ready` file exists, its mtime is strictly
  newer than the injection stamp, AND its contents equal the daemon's own
  SHA-256 of the on-disk `handoff.md`. Any missing/unreadable file ⇒ False
  (fail-closed). The daemon writes the injection stamp BEFORE pasting the wrap-up
  (so a subsequent marker has `mtime > stamp`) and DELETES the marker as it
  restarts (so it can never re-trigger). The full contract is in
  `marker-protocol.md`; keep it and `supervisor.py`'s `WRAPUP_TEMPLATE` in sync.
- **State precedence.** `working` and `blocked:human` are evaluated FIRST, so an
  injection/keystroke is suppressed while a pane is busy or showing a structured
  gate (permission prompt / picker) — never keystroke into a gate. `restarting`
  is checked before `warned` (a valid ready marker supersedes any re-warn).
- **Atomic restart via `respawn-pane -k`, proven by `#{pane_current_command}`.**
  Restart replaces the pane's process in one step (`respawn-pane -k -c <repo>
  'claude -n <topic>'`) — NEVER `/exit` then screen-scrape a shell prompt. The
  `❯` glyph is ambiguously BOTH the Claude idle prompt and the zsh prompt, so a
  mis-timed "shell is back" could type `claude …` into the still-live session.
  Wait for the fresh TUI by polling `#{pane_current_command}` → `node`/`claude`
  (`signals.pane_is_claude`), never by scraping `❯`. The abrupt kill is safe:
  the interlock already proved the handoff is written and the ready marker
  exists.
- **`claude -n <topic>`** sets the session's display name in the prompt box, the
  `--resume` picker, AND the terminal title (which tmux surfaces) — a cleaner
  equivalent of typing `/rename`. The shipped restart passes `-n <topic>` and
  then pastes the resume line as the first prompt (a `claude "<prompt>"` argv
  only pre-fills, no auto-submit — which is why the resume line is pasted after
  launch, not passed on the command line). Related `claude` flags to know:
  `--session-id` and `--resume`.

## Build / toolchain facts

- **Stdlib-only Python, host-only.** No third-party imports; four modules
  (`registry.py`, `signals.py`, `tmuxio.py`, `supervisor.py`) plus beside-tests.
  Precedent for host-only Python under `.claude/`:
  `.claude/hooks/livespec_footgun_guard.py`.
- **Deliberately OUTSIDE the product gates.** The folder is excluded from every
  product Python gate, by four concrete config facts (the design's "PR #1109 /
  dev-tooling `.claude/` universe exemption" labels are paraphrase for these):
  - **ruff** — `pyproject.toml` `[tool.ruff].extend-exclude` names
    `.claude/skills/overseer/**` (ruff's repo-wide scan is the one gate whose
    denylist must name the path; precedent `.claude/hooks/**`).
  - **pyright** — `[tool.pyright].include` lists only `.claude-plugin/scripts`
    and `dev-tooling`; the overseer folder is omitted, so it is never
    type-checked.
  - **coverage** — pytest's `testpaths = ["tests"]` means the product suite
    never collects the beside-tests, so `fail_under = 100` does not apply to
    these modules.
  - **import-linter** — `root_packages = ["livespec"]`; these modules are not
    part of the `livespec` package, so no import contract touches them.
  - The dev-tooling shared checks read their scope from
    `livespec_dev_tooling.config` (`source_tree_prefixes` /
    `target_dirs`), none of which include `.claude/skills/` — so
    `check-claude-md-coverage` and the style checks never reach here.
- **Run the beside-tests explicitly** — they are NOT part of the product
  `tests/` tree:

  ```bash
  uv run pytest .claude/skills/overseer/ -q
  ```

  (`conftest.py` puts the folder on `sys.path` so `import registry` / `import
  signals` / `import tmuxio` resolve when pytest collects the beside-tests.)
- **Adding a `.py` here?** Keep it stdlib-only. The ruff `**` exclude covers new
  files automatically, but new beside-tests must be run manually (they will not
  be collected by `just check`'s product suite).
- **The nested `.claude/CLAUDE.md -> ../AGENTS.md` symlink beside this file** is
  the repo's per-directory nested-memory convention (so Claude Code loads this
  guide when working in the folder). No structural or coverage check objects to
  a nested `.claude/` dir inside a skill folder — verified against
  `tests/test_plugin_distribution.py` (which only asserts `.claude-plugin/skills/`
  is absent and the repo-root `.claude/skills` is not a symlink).

## How to exercise it live

Per "done means exercised live", drive the shipped behavior end-to-end:

1. Two or three real tracks across **at least two repos** (proves the cross-repo,
   repo-qualified path, not just the same-repo happy path).
2. Start the daemon (`python3 .claude/skills/overseer/supervisor.py daemon 2>
   tmp/overseer/daemon.log`) and confirm the live `Topic · Repo · tmux · Ctx% ·
   Status` table renders and refreshes.
3. Force a **threshold crossing** on one track (a low `--stamp`/threshold or a
   genuinely heavy track), watch the daemon inject the wrap-up, have that session
   write `.overseer-ready`, and watch a **real auto-restart + rename** (the
   `respawn-pane -k` → `claude -n <topic>` → pasted resume line).
4. Verify **archive-GC** (archive a plan under `plan/archive/` and confirm its
   mapping row drops) and **reboot recovery** (kill a mapped session, restart the
   daemon with `--recover`, confirm the session is recreated from the mapping).

The daemon's diagnostics + `overseer[SURFACE]:` alerts go to stderr; redirect
them to a log under `tmp/overseer/` (maintainer-owned scratch root — use a
scoped subdir, never `rm` the root).

## Pointers

- `design.md` (beside the plan at `plan/overseer-rewrite/`) — the hardened
  design, including its "Adversarial review (2026-07-12)" section (the 8 blockers
  and why the mechanics are shaped as they are).
- `SKILL.md` — the runtime bottom-pane contract.
- `marker-protocol.md` — the wrap-up + marker certification contract.
- The repo-root agent-instruction guidance — the root `AGENTS.md` and its
  `.ai/agent-disciplines` topic (the "Overseer / long-running-coordinator
  discipline" and "Factory-dispatch over inline implementation" sections).
