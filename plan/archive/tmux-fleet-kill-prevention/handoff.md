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

---

## ADDENDUM 2026-07-21 — L1 was removed; two properties this epic never recorded

**Appended, not rewritten.** Everything above stands as the record of what was
believed and done at the time. This addendum records what was learned afterwards.
It was written by [`plan/archive/tmux-fleet-visibility/`](../tmux-fleet-visibility/handoff.md)
(ledger epic `livespec-l4g7wi`), which **supersedes the L1 environment-inversion
layer of this epic** on evidence that post-dates it. The L2 command guards, L3's
explicit per-invocation socket scoping, and the console AST check all STAND — L2 is
now the sole mechanical control.

### Finding 1 — L1 fails OPEN, silently, whenever its directory is missing

tmux falls back to the **shared default namespace** when `$TMUX_TMPDIR` does not
exist. No warning, no error — the scoping just stops applying. Read-only
reproduction:

```sh
P=/tmp/probe-$$
env -u TMUX TMUX_TMPDIR=$P /usr/bin/tmux ls    # dir ABSENT  -> lists the real fleet
mkdir -p $P
env -u TMUX TMUX_TMPDIR=$P /usr/bin/tmux ls    # dir PRESENT -> error connecting to $P/tmux-<uid>/default
rm -rf $P
env -u TMUX TMUX_TMPDIR=$P /usr/bin/tmux ls    # dir GONE    -> lists the real fleet again
```

Why that is reachable rather than theoretical: `/tmp` is **tmpfs** (wiped every
reboot); systemd-tmpfiles carries `q /tmp 1777 root root 10d` (10-day age-out); and
`supervisor.py::_agent_tmux_tmpdir()` did `mkdir(exist_ok=True)` at **spawn time
only**, with nothing recreating the directory afterwards. Long-lived agents carry
`TMUX_TMPDIR` in their process environment for days, so any of those events silently
un-scoped every one of them **while they still believed they were isolated**.

A control that fails open with no signal provides false confidence, which is worse
than a known absence.

### Finding 2 — `TMUX` overrides `TMUX_TMPDIR`, so `unset TMUX` was the load-bearing half

With the private directory existing (so finding 1 is not a confound):

```sh
P=/tmp/prec-$$; mkdir -p $P/tmux-$(id -u)
TMUX_TMPDIR=$P /usr/bin/tmux ls              # TMUX set   -> lists the real fleet
env -u TMUX TMUX_TMPDIR=$P /usr/bin/tmux ls  # TMUX unset -> resolves to $P
rm -rf $P
```

Inside a tmux pane, tmux sets `TMUX` itself, so `TMUX_TMPDIR` alone would have been
inert. Any future removal or reintroduction must take the WHOLE prefix; deleting only
the `TMUX_TMPDIR` export would leave dead configuration that reads as protective.

### Correction to the Calibration bullet above ("the reason L1 matters")

That bullet reads:

> **A `PreToolUse` hook cannot see inside a script's subprocesses.** It sees only the
> top-level command string; `python3 foo.py` is opaque. This is a structural limit of
> L2 and the reason L1 matters.

**The first two sentences are correct and still stand.** The conclusion does not.
L1 did not reliably cover that gap — finding 1 shows it lapsed silently whenever its
directory was absent, a condition guaranteed by reboot. The gap is now knowingly left
open, on the record that all four kills were top-level command strings the guards
could see, while L1's cost was paid continuously. **The evidence that would reopen
this:** a fleet kill originating INSIDE a script's subprocess, where the guards saw
only an opaque top-level command. If that happens, close the gap with a mechanism
that does not blind — not by restoring L1.

### Why L1 was removed at all — the categorical argument

Not cost/benefit. Tmux selects one server per invocation, and that selection governs
**every** subcommand. `TMUX`, `TMUX_TMPDIR`, `-L`, `-S` all answer *which server am I
talking to*; none can answer *what am I allowed to do to it*. So an agent that can
reach the fleet socket can list it **and** destroy it; one that cannot can do neither.
**Visibility and destructive power are the same bit**, and any namespace-level scoping
trades them one-for-one. No directory, location, or socket name yields protection
without blindness — `/run/user/<uid>` was considered and rejected, because it fixes
the fail-open but not the blindness.

Distinguishing a listing from a teardown requires reading the *command*, which is what
the L2 guards do. L2 is therefore not merely the layer doing the most work; it is the
only layer that **can** do this work. L1 was not badly implemented — it was
categorically unable to succeed. **This is recorded specifically to stop anyone
rebuilding an "L1 v2" with a better directory.**

Secondary: this epic's recorded root cause for the 2026-07-18 kill was an agent that
wanted a clean tmux server *"assuming an isolated environment."* L1 systematically
manufactured exactly that belief in every agent it scoped — a mitigation inducing the
mental state that caused the incident it prevents.

### The harm that forced the reversal

L1's blindness produced repeated false claims about session liveness. On 2026-07-19
two separate sessions reported fleet sessions dead that were alive the whole time; the
agent namespace held one socket and no `default`, so `tmux ls` returned a clean,
plausible, wrong "no server running". Six of sixteen live sessions were scoped at that
point. Probe (read-only):

```sh
for s in $(/usr/bin/tmux ls -F '#{session_name}'); do
  pid=$(/usr/bin/tmux list-panes -t "$s" -F '#{pane_pid}' | head -1)
  printf '%-32s %s\n' "$s" "$(tr '\0' '\n' < /proc/$pid/environ | grep '^TMUX_TMPDIR=' || echo unset)"
done
```

As of 2026-07-21 no live pane carries `TMUX_TMPDIR`, and a freshly spawned agent
running a bare `tmux ls` lists the real fleet.

### Not implicated: the oh-my-zsh `tmux` plugin

The superseding thread also removed an oh-my-zsh shell plugin that broke `tmux` inside
Claude Code Bash calls. **That plugin was NOT a cause of any of the four kills** — an
exhaustive read of this epic's files and all six revisions of its thread directory
found zero mentions of it, and decisively, the two 2026-07-18 kill commands invoked
tmux by absolute path, which bypasses alias resolution entirely. It is recorded here
only so a future reader does not mistake its removal for a root-cause fix. One
incidental security gain: that plugin shipped `tksv`, a four-keystroke alias for the
server-teardown command, live in every interactive shell. It is gone.

### Sandbox mirror `bd-ib-zaq3` — left in place, and the open question is ANSWERED

The Calibration bullet above asks whether the fabro provider bind-mounts host `/tmp`.
**It does not**: `fabro-sandbox/src/docker.rs` `host_config()` sets `binds: None`,
pinned by fabro's own test `container_config_has_no_bind_mounts_or_socket`. So the
sandbox mirror was defense-in-depth on an already-airtight boundary, exactly as this
epic supposed. It was deliberately LEFT in place: inside a container there is no host
fleet to reach (no protective value lost) and none to see (no blindness cost), and its
fail-open lands harmlessly inside the same container. Reopen only if that provider
ever starts bind-mounting host paths.
