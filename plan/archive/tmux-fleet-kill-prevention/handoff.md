# Handoff — tmux-fleet-kill-prevention (ARCHIVED — thread complete, epic closed)

**Thread**: `plan/archive/tmux-fleet-kill-prevention/` (repo `livespec`).
**Ledger epic anchor**: `livespec-yiycvd` (livespec tenant) — CLOSED 2026-07-19.
**Status**: all five children closed, all four mirrors accepted with live-exercise
evidence journaled. Two residuals recorded below — neither is a silent omission.

## What this epic was for

Four times (2026-07-03, 2026-07-18 ×2, 2026-07-19) a dispatched agent destroyed the
maintainer's entire live tmux fleet — ~20 agent panes on one shared default socket —
by running a fleet-killing tmux command for "cleanup". The fourth kill was caused by
the agent working ON this prevention epic, which makes it the most instructive.

The goal was never "tell agents not to do it". Prose prohibition already existed in a
sibling repo's `AGENTS.md` and did not propagate. The goal was to make destruction
**structurally impossible**, via mechanical guards and environment shaping.

## Final state — what is actually live

| Layer | Item | State |
|---|---|---|
| **L1 overseer** | `livespec-wa7ry3` (repo `livespec`) | **LIVE** — verified by reading `/proc/<pid>/environ` of a running spawned pane: `TMUX_TMPDIR=/tmp/tmux-agents-1000`, and that agent-scoped socket dir is in active use. |
| **L1 sandbox** | mirror `bd-ib-zaq3` (orchestrator) | **ACCEPTED** — env inversion unconditional in the single dispatch path, fail-closed on error, installed artifact byte-identical to source. Defense-in-depth, not the breached boundary (see Calibration). |
| **L2 host** | `livespec-6dyst6` (repo `vps-info`) | **LIVE** — `~/.claude/hooks/tmux-fleet-guard.py`, user-scope `PreToolUse`/`Bash`, independent of any plugin. |
| **L2 Claude Driver** | mirror `livespec-driver-claude-w6f` | **ACCEPTED** — released `v0.4.4`, installed, payload-verified, PROVEN TO FIRE. |
| **L2 Codex** | mirror `livespec-driver-codex-72z` | **ACCEPTED** — released `v0.5.4`, installed, payload-verified, PROVEN TO FIRE. |
| **L3 console** | mirror `livespec-console-beads-fabro-f2k` | **ACCEPTED** — harness was always correct; its *enforcing check* was repaired (PR #307) before acceptance. |
| **L4 resilience** | `livespec-4vzhwp` | **DETACHED** to an independent backlog item at maintainer direction — see Residuals. |

Final verification of all three guards, against the **installed** artifacts, under bare
`python3` with `PYTHONPATH` cleared:

| | 40-case corpus | 50-case adversarial corpus | fires & blocks |
|---|---|---|---|
| Codex `v0.5.4` | 0 misses | 0 mismatches | yes |
| Claude Driver `v0.4.4` | 0 misses | 0 mismatches | yes |
| Host guard | 0 misses | 0 mismatches | wired, verified |

**Zero disagreements between all three.** Before repair they disagreed on 18 of 50.

## The three lessons this epic actually taught

### 1. Merged is not installed; installed is not protecting; only FIRING is protecting

The Codex guard was merged, released, installed, enabled, trusted, correctly wired,
and classifying correctly — and protected **nothing**, for 37 minutes before it failed
to stop the fourth kill. It crashed on an unpackaged import (`_vendor` lived at repo
root, outside the packaged subtree) and **failed OPEN**, exiting non-zero so the tool
call proceeded. The Claude Driver had the identical defect against `returns`.

Blast radius: **8 of 12 active distributed hooks could not start**, including
`block_auto_memory.py`, which enforces the no-local-memory contract. CI was green
throughout, because tests ran under `uv` where the dependency resolved — never in the
install shape.

The durable fix is not the shim; it is the **install-shaped test** both Driver repos
now carry, which stages ONLY the packaged subtree and runs each hook under a bare
interpreter, asserting real verdicts.

### 2. A correct classifier is not a control — and your own corpus will not find that out

After the packaging repair, both guards scored 15/15 on the author's corpus and were
demonstrated to fire. They were still trivially bypassable. An independent adversarial
review found **37 real bypasses**: Codex missed 16 of 35 hazards, Claude missed 21 of 35.

Root cause, identical in both: each peeled a **closed allowlist** of wrapper prefixes
and then inspected only **token position 0**. Anything displacing the hazard off that
position passed — `timeout`, `exec`, `command`, `nice`, `nohup`, `env -i`, `xargs`,
subshells, brace groups, `eval`, command substitution. Two findings deserve singling out:

- `mise exec -- <fleet-kill>` was ALLOWED by the Claude guard — **the fleet's own
  documented git idiom**, the form most likely to be typed by accident.
- A `pkill` pattern form was ALLOWED by the Codex guard; verified inertly against
  `/proc`, that pattern matched **15 live processes** at review time.

The fix was to invert the polarity: **scan every token position** for a hazard command
head. Both corpora are now committed as regression tests in both repos.

### 3. The same defect shape recurred in a fourth place nobody had scoped

The console's AST check — the thing that made the harness's socket scoping
"mechanically enforced, not remembered" — had the identical structure: three closed
enumerations plus one positional test, each failing open. It validated **shape**, not
**value**: the `env` arm compared only the KEY name, and the socket test compared only
an INDEX. So a builder pairing `TMUX_TMPDIR=/tmp` with the default socket label and a
server-teardown sub-command passed clean — the exact shape of the original incident.
It also had a 6-of-~170 sub-command allowlist, failed open on a variable rename, never
analyzed the ordinary non-chained build idiom, and would **silently pass while scanning
zero files** if its one target directory ever moved.

Repaired by console PR #307 (`5bddff8`), suspect-by-default. Verified by the accepting
operator: arch-check exit 0 with no false positives on the correct harness, 48 unit
tests pass, master CI green.

**The generalization worth carrying forward:** every layer of checking found something
the previous layer missed — the author's corpus found 0, an independent probe found 12,
an adversarial reviewer found ~3× more, and the *fix* then exposed a fourth component
nobody had briefed. Assume your own corpus grades your own assumptions.

## Calibration — what these controls do NOT cover

Recorded deliberately, so the epic is not read as claiming more than it delivered.

- **The sandbox item is defense-in-depth, not the breached boundary.** The Fabro
  sandbox is a docker container, so the host's socket is unreachable from inside
  regardless of `TMUX_TMPDIR`. The population that caused all four kills was
  **host-side ad-hoc sub-agents**, which are covered by the L2 guards, not by L1.
  Open question worth one check by someone with the fabro provider source: whether
  that provider bind-mounts host `/tmp` by default. If it did, L1-sandbox would be
  load-bearing rather than defense-in-depth.
- **An agent inside a sandbox can trivially override the env var.** `TMUX_TMPDIR` is
  scoping, not a security boundary.
- **A `PreToolUse` hook cannot see inside a script's subprocesses.** It sees only the
  top-level command string; `python3 foo.py` is opaque. This is a structural limit of
  L2 and the reason L1 matters.
- **COUPLING TO WATCH:** the post-merge janitor runs the aggregate check **on the host,
  unscoped**. Harmless today only because that aggregate deliberately excludes the tmux
  e2e job. `ci.yml` explicitly contemplates promoting that job into the required set;
  if that ever happens, the host-side janitor would spawn tmux on the host and the
  console's AST check becomes the last line of defense. Neither item surfaced this
  alone — it came from reading them together.

## Residuals — open, recorded, NOT claimed as done

1. **Console e2e suite has never been run on this host.** Deliberately deferred by the
   maintainer (2026-07-19) while the fleet carried ~13 live agent sessions, on the
   reasoning that CI already proves the suite in an isolated container and a
   `PreToolUse` hook cannot protect a test process. CI's `check-e2e-tmux` is green and
   genuinely runs tests (7 passed, guarded by the justfile's zero-test grep). Note it
   is advisory, not merge-blocking. Run it during a drained window to close this.
2. **L4 fleet-recreate resilience — `livespec-4vzhwp`**, detached from this epic and
   re-scoped as an independent P3 backlog item at maintainer direction. The open
   question is **not** "how do we build the systemd unit" but **"has another
   agent-caused kill occurred since 2026-07-19?"** If none has, the cost/benefit that
   motivated it (four manual rebuilds) has changed materially and it may be correctly
   closed as won't-do. If one has, that is the strongest possible evidence that
   prevention alone is insufficient. If built, note `livespec-dev-tooling-s2t` flags
   hand-edited systemd state as non-recreatable, so it should land as a committed
   artifact.

## Process findings filed elsewhere

- `livespec-dev-tooling-fp5yfv` — `red_green_replay._IMPL_PREFIXES` under-covers
  configured source trees. `.claude/hooks/` is omitted too, so
  `livespec-orchestrator-beads-fabro` is also exposed; `livespec-driver-codex` is
  covered only ACCIDENTALLY by a legacy fixture prefix whose own source comment
  asserts production has no such directory — a cleanup retiring it would silently
  expose codex. Recommends deriving impl paths from each repo's declared
  `source_tree_prefixes` rather than a hardcoded list that has now drifted twice.
  Cross-linked to `livespec-dev-tooling-30g` and `-9j8.7`; the three want grooming
  together. Left `blocked`/`needs-human` because the fix direction is a maintainer
  design call.
- `bd-ib-brry`, `bd-ib-lza6` (orchestrator tenant) — pre-existing janitor/valve
  follow-ups, untouched by this epic.

## Standing rules this epic established

These are binding on any future work touching guards or dispatched agents.

1. **Never put a destructive command in a sub-agent brief** — not as an example, not
   as a thing to "try", not quoted. Describe the hazard class in prose and require
   verification by classifier payload.
2. **Guard-testing is payload-only.** Feed the command as a STRING to the guard's
   stdin and read the verdict. Executing it to "see if it is blocked" risks the exact
   destruction the guard exists to prevent.
3. **A hook covers exactly one runtime.** Claude Code hooks do not cover Codex.
   Enumerate the runtime a dispatched agent will execute on before dispatching.
4. **Merged ≠ protected. Installed ≠ protected. Only FIRING is protected.**
5. **A `PreToolUse` hook cannot see a script's internal subprocesses.**
6. **Verify a control in its INSTALL shape, not its dev shape.** A test that does not
   stage the packaged subtree and run it under a bare interpreter is testing something
   the user never runs.
7. **Prefer a firing probe whose failure mode is harmless.** Prove a control fires
   using a payload it denies for an UNRELATED, inert reason. Never prove a tmux guard
   with a tmux command.
8. **Suspect-by-default beats enumerate-the-bad.** Closed allowlists inspected at one
   position fail open, and did so in four independent components here.

## Verification recipe (reusable)

Payload-probe a guard by feeding `{"tool_name":"Bash","tool_input":{"command":"<STRING>"}}`
to its stdin and reading the verdict; nothing is executed. Then prove FIRING with a
payload the guard denies for an unrelated, inert reason — a `--no-verify` commit in a
throwaway repo, or a blocked memory-file Write. To inspect Codex hook behavior without
touching host config, point `CODEX_HOME` at a scratch directory (copy `auth.json` in,
delete the directory after) and use `codex exec --dangerously-bypass-hook-trust` with a
recorder plugin.

Two Codex-specific facts that defeat obvious mitigations: **Codex re-extracts its plugin
cache on every run** (so patching the cache is silently reverted — a fix reaches Codex
only via a release), and **Codex silently skips UNTRUSTED hooks** (a changed `hooks.json`
invalidates its `trusted_hash`, so any version bump can disarm a guard with no warning —
check `[hooks.state]` after every update).

A footnote that is itself evidence: the first attempt to journal the console acceptance
note was DENIED by the repaired host guard, because the note quoted hazard command
strings and the shell quoting made the command line unparseable — so the guard failed
CLOSED, exactly as designed. The note was re-routed through a file.
