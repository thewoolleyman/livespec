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

Status: **PERMANENT** — a human-supervised alternate to autonomous mode (the
Beads/Dolt + Fabro Dispatcher / dark factory), not a stopgap awaiting a
replacement. The two are standing peers: autonomous mode runs *ready work-items*
unattended through the ledger; the overseer keeps *interactive plan tracks*
moving in parallel under a human driver, automating only the context-% wrap-up +
restart mechanics. Maintain it in place. **LOCAL-ONLY and unsynced:** it lives
under `.claude/skills/overseer/` in this repo only and is usable only from it. Do
NOT add it to the plugin, the spec, the copier template, fleet manifests,
conformance checks, or any other repo.

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
   repo-qualified `<repo-slug>--<topic>` (tmux names are global; plan topics are
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
- **Bracketed-paste submission (`_submit_prompt`) — verified-submit loop.** Paste
  (`load-buffer` + `paste-buffer -p`, single- or multi-line, atomic — never type
  a payload key-by-key), then re-send `Enter` until the empty box returns
  (`signals.input_box_ready`), up to `_SUBMIT_MAX_ENTERS`. Verified live
  (2026-07-13): on a STEADY idle session a single `Enter` submits; but a
  freshly-`respawn`-ed session is often still drawing its welcome/news screen when
  the first `Enter` arrives and DROPS it, leaving the resume line un-submitted and
  the auto-restart stalled. The verify loop fixes that (an extra `Enter` on an
  already-empty prompt is a harmless no-op). Note: this is NOT the old
  `send-keys -l` key-by-key-typing collapse problem — the paste is always atomic;
  it is purely fresh-TUI submit TIMING.
- **Anchored, fail-closed Ctx% parse (`signals.parse_ctx_remaining`).** Scan only
  the last FEW non-empty pane rows (`_CTX_TAIL_ROWS`), ANSI-stripped, taking the
  LAST `Ctx: N% left` match. The statusline is the SECOND-to-last row — a footer
  hint (`⏵⏵ …` / `? for shortcuts`) renders BELOW it (verified live 2026-07-13) —
  so reading only the LAST row misses `Ctx:` entirely. NEVER scan the whole
  capture — page content (including the overseer design doc itself) contains
  `Ctx: N% left` and would yield a false reading; the small bound keeps that
  anti-false-match intent. No match ⇒ **unknown**, which keeps the last known
  value and NEVER counts as a threshold crossing. This is the one coupling: if
  the statusline stops emitting `Ctx: N% left`, ctx reads unknown and the daemon
  degrades safely (the table shows a dash).
- **Busy detection (`signals.is_busy` + the daemon's settled-delta).** The live
  TUI (verified 2026-07-13) renders NO persistent busy string while streaming
  tokens — the input box looks idle and the response accumulates above it — so
  single-capture markers are insufficient. `signals.is_busy` fires on the real
  active-generation spinner (`✻ … (… · Ns · ↓ tokens)` / `(running … hook…)`),
  `esc to interrupt` (older layouts), and `Waiting for N background`; it
  deliberately does NOT fire on the lingering completed-turn summary
  (`✻ Brewed for 25s`). Because streaming shows no spinner in the captured
  region, the daemon ALSO runs a two-capture **settled-delta**
  (`Supervisor._pane_settled`) before injecting/restarting an apparently-idle
  track: two captures `_SETTLE_DELAY` apart that DIFFER ⇒ actively working ⇒
  treated as `working` and skipped. Over-firing busy is the SAFE direction.
- **Idle-input detection (`signals.is_idle_input`).** The real idle prompt is an
  EMPTY `❯` between two horizontal rule lines (`────…`), statusline + hint below
  — NOT a `╭─╮` box with `? for shortcuts` (verified live 2026-07-13). Detect
  that structural shape (glyph/hint-independent); require the prompt EMPTY so the
  daemon never injects over existing input; gate with not-busy + not-gate.
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
  `.claude/hooks/livespec_footgun_guard.py`. Stdlib-only is now **load-bearing
  for the invocation surface too**: `supervisor.py` carries a
  `#!/usr/bin/env -S uv run --script --no-project` shebang, so it runs with an
  isolated interpreter and **no dependencies** — a third-party import would break
  the shebang launch (there is no project sync to satisfy it).
- **Invocation surface (2026-07-13 de-gold-plating).** The `/overseer` skill is
  the SOLE operator surface; there is no supported `python3 …/supervisor.py`
  path. `supervisor.py` is a self-invokable `uv` script — the shebang above,
  `chmod +x`, launched directly (`.claude/skills/overseer/supervisor.py daemon`).
  When run as an executable, Python puts the script's own dir on `sys.path[0]`,
  so `import registry` / `signals` / `tmuxio` resolve (verified). The CLI carries
  **no config knobs**: store (`~/.livespec-overseer.jsonl`) and injection-stamp
  (`~/.livespec-overseer-stamps.json`) paths are hard-coded via the `registry`
  defaults, and the watch-set is the whole fleet read from
  `.livespec-fleet-manifest.jsonc` — no `--store` / `--stamp` / `--repos` /
  `--repos-only` / `--manifest`. The `Supervisor` dataclass keeps `store_path` /
  `stamp_path` / `watch_repos` / `manifest_path` injectable, but **only the
  beside-tests inject them** (they redirect `registry.DEFAULT_STORE_PATH` for CLI
  isolation) — the CLI never exposes them. Track subcommands take `--repo` /
  `--topic` KEYWORD flags (the skill prompts for whichever the maintainer omits);
  `daemon` needs no args.
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
- **ALWAYS run the beside-tests before pushing ANY change to this folder — they
  are the ONLY gate on it.** This folder is outside the product discipline, so
  `just check`, the pre-push hook, and CI do NOT run these tests (pytest
  `testpaths = ["tests"]` never collects them; nothing in the justfile or
  `.github/` references `skills/overseer/`). A broken overseer change will merge
  green with NOTHING having exercised its behavior — that is exactly how a
  critical regression once reached master here (the auto-merge landed a green PR
  whose overseer bug no gate caught). So running them is a **hard pre-push step
  for the developer**, not optional:

  ```bash
  uv run pytest .claude/skills/overseer/ -q
  ```

  (`conftest.py` puts the folder on `sys.path` so `import registry` / `import
  signals` / `import tmuxio` resolve when pytest collects the beside-tests.)
  Deliberately kept lightweight (a manual pre-push run, no CI wiring) to preserve
  the "outside the product gates" design — the discipline lives here, in the
  developer's hands, not in a gate.
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

The **beside-tests are the primary, complete gate** for the acting mechanics
(inject → certify → restart, archive-GC, reboot recovery, and the RB1 marker /
round timing) — they drive a FAKE tmux deterministically, so they own that
coverage. Run them first (see "Build / toolchain facts"). Since the CLI no longer
has a `--repos` / `--store` escape hatch, there is no scratch-repo sandbox: live
exercise runs against the **real fleet** (maintainer decision 2026-07-13). That
is safe because the daemon is **surface-only** — nothing is touched unless a real
track crosses threshold AND certifies (`.overseer-ready`) AND is idle.

For a change to the invocation / config surface (this file's usual subject), the
end-to-end check is the discovery + render path, exercised safely read-only:

1. Run a **read-only render** against the real fleet:
   `.claude/skills/overseer/supervisor.py list` — it calls `tick(act=False)`, so
   it discovers every fleet-manifest repo's `plan/*/`, joins the mapping, and
   prints the `Topic · Repo · tmux · Ctx% · Status` table **without injecting or
   restarting anything**. This exercises the whole reshaped CLI (no-flags launch,
   fixed store path, fleet-only watch-set) with zero mutation risk.
2. Optionally observe a **brief live daemon**
   (`.claude/skills/overseer/supervisor.py daemon 2> tmp/overseer/daemon.log`,
   stopped after a render or two) to confirm the loop renders and refreshes.
   Surface-only means it will not act on any real session unless that session is
   genuinely at threshold + certified + idle.

The daemon's diagnostics + `overseer[SURFACE]:` alerts go to stderr; redirect
them to a log under `tmp/overseer/` (maintainer-owned scratch root — use a
scoped subdir, never `rm` the root).

**Timing-sensitive behavior (the RB1 lesson) is covered by the beside-tests, not
a hand-driven loop.** The regression that once slipped through a live re-test —
the "void the ready marker when busy" logic racing the certifying turn's own busy
tail (final streaming + stop hooks keep the pane busy 10–60s AFTER the marker is
written) — is now pinned by deterministic fake-tmux tests
(`test_fresh_marker_survives_busy_certifying_tail`,
`test_stale_marker_voided_when_busy_past_grace`,
`test_void_resets_inject_state_so_round_can_recertify`). Do NOT try to reproduce
it by manufacturing a threshold crossing on a real working session — the daemon
exercises the full inject → certify → restart cycle live only when a real track
naturally reaches it (its steady-state job); the deterministic tests own that
coverage, and hand-spaced `--once` ticks would mask the timing anyway.

## Pointers

- `design.md` (beside the plan at `plan/overseer-rewrite/`) — the hardened
  design, including its "Adversarial review (2026-07-12)" section (the 8 blockers
  and why the mechanics are shaped as they are).
- `SKILL.md` — the runtime bottom-pane contract.
- `marker-protocol.md` — the wrap-up + marker certification contract.
- The repo-root agent-instruction guidance — the root `AGENTS.md` and its
  `.ai/agent-disciplines` topic (the "Overseer / long-running-coordinator
  discipline" and "Factory-dispatch over inline implementation" sections).
