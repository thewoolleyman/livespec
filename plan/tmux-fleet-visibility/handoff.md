# Handoff — tmux-fleet-visibility

**Thread**: `plan/tmux-fleet-visibility/` (repo `livespec`).
**Ledger epic anchor**: `livespec-l4g7wi` (livespec tenant; filed 2026-07-19,
routed `backlog` — epic-shaped, driven from this plan track, not dispatched).
**Status**: OPEN — Phase 0 complete 2026-07-19, gate PASSED (see "Phase 0
execution record" at the end of this file). Next: Phase 1. Authored 2026-07-19.

**Supersedes**: the **L1 environment-inversion layer** of
[`plan/archive/tmux-fleet-kill-prevention/`](../archive/tmux-fleet-kill-prevention/handoff.md)
(ledger epic `livespec-yiycvd`, CLOSED 2026-07-19; L1 items `livespec-wa7ry3`
and sandbox mirror `bd-ib-zaq3`).

This thread does **not** supersede that epic's L2 command guards, which stay and
become the sole mechanical control. It reverses one specific design decision in a
closed epic, on evidence that post-dates it.

> **READ FIRST**, in order: this file → the archived handoff above (especially its
> "Calibration" section, which contains the strongest argument *against* this
> thread) → `.claude/skills/overseer/AGENTS.md` §L1 (lines ~1060–1070).

---

## Vocabulary (the archive's layer numbers, spelled out)

The archived epic numbered five defense layers. Two matter here. Anyone reading
this thread should not have to decode "L1"/"L2":

- **L1 — the environment inversion.** Every agent the overseer spawns is launched
  with `unset TMUX; export TMUX_TMPDIR=/tmp/tmux-agents-<uid>` prefixed to its
  command. That points the agent at a private tmux socket namespace instead of the
  shared one the maintainer's fleet lives on. Intent: an agent that cannot *reach*
  the fleet cannot destroy it. **This thread removes it.**
- **L2 — the command guards.** `PreToolUse` hooks that read each shell command
  before it runs and refuse the fleet-destroying class. Three copies: host
  (`~/.claude/hooks/tmux-fleet-guard.py`, work item `livespec-6dyst6`, repo
  `vps-info`), Claude Driver `v0.4.4`, Codex Driver `v0.5.4`. **This thread keeps
  them and makes them load-bearing alone.**

Also referenced: **L3**, the console test harness's explicit per-invocation socket
scoping (`-L`/`-S`). L3 **stays** — see "What we are NOT removing".

---

## What this thread is for

L1 makes agents blind to the fleet, and that blindness is now causing repeated
false claims about session liveness. On 2026-07-19 alone, two separate sessions
reported fleet sessions dead that were alive the whole time. One session's own
words:

> "I was wrong twice about session liveness today — first assuming
> fleet-pin-propagation was gone, then treating the revert as stalled when it had
> already landed. Both came from inferring session state from `tmux ls`, which sees
> nothing in my namespace."

`fleet-pin-propagation` was alive and had been since 11:03:29 that day.

There is a second, independent cause of the same symptom on this host — an
oh-my-zsh shell plugin that breaks `tmux` inside every Claude Code Bash call. Both
are removed here, because fixing either alone leaves agents still unable to trust
`tmux ls`, and because removing the plugin *first* would be actively harmful (see
Phase ordering).

**The goal is that a bare `tmux ls` tells the truth.** Not that agents remember to
run a special command — a wrapper they must know to use is the same prose-dependent
mitigation this epic's founding lesson already rejected.

---

## Evidence

All findings below were reproduced on `vps` on 2026-07-19. Reproductions are
read-only.

### 1. L1 silently stops working when its directory is missing

tmux falls back to the **shared default namespace** when `$TMUX_TMPDIR` does not
exist. No warning, no error — the scoping just stops applying.

```sh
P=/tmp/probe-$$
env -u TMUX TMUX_TMPDIR=$P /usr/bin/tmux ls    # dir ABSENT  -> lists the real fleet
mkdir -p $P
env -u TMUX TMUX_TMPDIR=$P /usr/bin/tmux ls    # dir PRESENT -> error connecting to $P/tmux-<uid>/default
rm -rf $P
env -u TMUX TMUX_TMPDIR=$P /usr/bin/tmux ls    # dir GONE    -> lists the real fleet again
```

Blast radius:

- `/tmp` is **tmpfs** — wiped on every reboot.
- systemd-tmpfiles carries `q /tmp 1777 root root 10d` — 10-day age-out.
- `supervisor.py::_agent_tmux_tmpdir()` does `mkdir(exist_ok=True)` at **spawn time
  only**. Nothing recreates the directory afterwards.

Long-lived agent processes carry `TMUX_TMPDIR` in their process environment for
days. If the directory is removed underneath them — reboot, tmpfiles aging, or a
routine `/tmp` tidy-up — every one of them silently stops being scoped and points
at the shared fleet, **while still believing it is isolated**.

This property is not recorded anywhere in the archived epic.

### 2. `TMUX` overrides `TMUX_TMPDIR`

With the private directory existing (so the fallback above is not a confound):

```sh
P=/tmp/prec-$$; mkdir -p $P/tmux-$(id -u)
TMUX_TMPDIR=$P /usr/bin/tmux ls              # TMUX set   -> lists the real fleet
env -u TMUX TMUX_TMPDIR=$P /usr/bin/tmux ls  # TMUX unset -> resolves to $P
rm -rf $P
```

So `unset TMUX` is the load-bearing half of L1 — inside a tmux pane, tmux sets
`TMUX` itself and `TMUX_TMPDIR` alone would be inert. **Removal must take the whole
prefix**; deleting only the `TMUX_TMPDIR` export would leave dead configuration
that reads as protective.

### 3. Six of sixteen live sessions were blinded

At authoring time, `TMUX_TMPDIR=/tmp/tmux-agents-1000` was set in the process
environment of: `cockpit-ux-docs-release`, `codex-yolo-sandbox`,
`fabro-ci-image-factoring`, `overseer-productization`, `rop-sweep-fleet-policy`,
`tmux-fleet-kill-prevention`. The agent namespace held exactly one socket
(`rop-drain`) and **no `default`** — so `tmux ls` in any of those six returned a
clean, plausible, wrong "no server running".

Reproduce with (read-only):

```sh
for s in $(/usr/bin/tmux ls -F '#{session_name}'); do
  pid=$(/usr/bin/tmux list-panes -t "$s" -F '#{pane_pid}' | head -1)
  printf '%-32s %s\n' "$s" "$(tr '\0' '\n' < /proc/$pid/environ | grep '^TMUX_TMPDIR=' || echo unset)"
done
```

### 4. The oh-my-zsh `tmux` plugin breaks tmux inside Claude Code

Separate from L1, and host-specific. oh-my-zsh's bundled `tmux` plugin is enabled at
`~/.acfs/zsh/acfs.zshrc:67` and defines `alias tmux=_zsh_tmux_plugin_run`.

Claude Code's shell snapshot captures that **alias** but omits the **function**:
the current snapshot contains `alias -- tmux=_zsh_tmux_plugin_run` and **zero**
single-underscore function definitions (versus nine double-underscore ones). In zsh
`_name` is the completion-function convention, so the snapshot filter drops them —
but it keeps aliases pointing at them.

Result, verified:

```
zsh -c  'type tmux'  -> tmux is /usr/bin/tmux                        (fine)
zsh -lc 'type tmux'  -> tmux is /usr/bin/tmux                        (fine)
Claude Code Bash     -> tmux is an alias for _zsh_tmux_plugin_run
                     -> zsh: command not found: _zsh_tmux_plugin_run  (exit 127)
```

Two consequences worth recording:

- `vps-info/CLAUDE.md` currently attributes this to "non-interactive shells". That
  is **wrong** and sends the next investigator to the wrong mechanism — plain
  non-interactive zsh is fine. It is specific to Claude Code's snapshot.
- The same snapshot defect leaves `tds` and `glp` (→ `_git_log_prettily`) dangling.
- The plugin also ships a four-keystroke alias for the fleet-destroying command
  (`tksv`), live in interactive shells. Removing the plugin removes it.

### 5. The plugin is NOT implicated in any of the four kills

An exhaustive read of the archived epic — all four files plus all six historical
revisions of the thread directory — found **zero** mentions of oh-my-zsh, zsh,
`_zsh_tmux_plugin_run`, `ZSH_TMUX_*`, shell aliases, shell functions, or exit 127.
Nothing was written and later removed.

Decisive: the two 2026-07-18 kill commands invoked tmux by **absolute path**
(`/usr/bin/tmux`), which bypasses alias resolution entirely.

**Do not let this thread be read as "we found the cause of the kills."** It did
not. The kills were agents deliberately invoking the server-teardown subcommand
against the default socket. This thread is about a different harm — blindness — and
about a fail-open property of the mitigation built to stop the kills.

---

## The argument for removing L1

Not primarily cost/benefit. The mechanism cannot do what it was asked to do.

Tmux selects one server per invocation, and that selection governs **every**
subcommand. `TMUX`, `TMUX_TMPDIR`, `-L`, `-S` all answer *which server am I talking
to*. None of them can answer *what am I allowed to do to it*. Therefore:

- If an agent can reach the fleet socket, it can list it **and** destroy it.
- If it cannot reach the fleet socket, it can do neither.

**Visibility and destructive power are the same bit.** Any namespace-level scoping
trades them one-for-one. There is no directory, no location (`/run/user/<uid>` was
considered and rejected — it fixes the fail-open but not the blindness), and no
socket name that yields protection without blindness.

Distinguishing a listing from a teardown requires reading the *command*. That is
what the L2 guards do. So L2 is not merely the layer doing the most work — it is
the only layer that **can** do this work. L1 was not badly implemented; it was
categorically unable to succeed.

This framing is deliberate: it should stop anyone rebuilding an "L1 v2" with a
better directory.

### The secondary argument: L1 reproduces its own threat model's precondition

The 2026-07-18 kill's recorded root cause was an agent that wanted a clean tmux
server **"assuming an isolated environment."** L1 systematically manufactures
exactly that belief in every agent it scopes. A mitigation that induces the mental
state that caused the incident it prevents is working against itself.

### Coverage, against the actual record

| Incident | Shape | L1 |
|---|---|---|
| 2026-07-03 | not recorded in detail | unknown |
| 2026-07-18 (b2) | bare teardown, absolute path | would stop it — **only if the directory exists** |
| 2026-07-18 (b3) | explicit `TMUX_TMPDIR=/tmp` | pierced |
| 2026-07-19 (codex) | explicit default-socket `-S` / `-L`, and an explicit env override | pierced, three ways |

One of four, conditional on a directory with no recreation guarantee, while
blinding every scoped agent 100% of the time.

---

## Answering the archive's counter-argument

The archived handoff states, at `plan/archive/tmux-fleet-kill-prevention/handoff.md:114-116`:

> **A `PreToolUse` hook cannot see inside a script's subprocesses.** It sees only
> the top-level command string; `python3 foo.py` is opaque. This is a structural
> limit of L2 **and the reason L1 matters.**

**This is correct and this thread does not refute it.** Removing L1 opens a real
gap: a script that internally invokes a fleet teardown is invisible to the guards,
and an inherited environment variable would have covered it.

Reasons to accept the gap anyway, recorded honestly:

1. **No incident has ever taken that shape.** All four kills were top-level Bash
   command strings the guards could see. The gap is theoretical; the blindness harm
   is demonstrated and recurring.
2. **L1's coverage of that gap was never reliable.** Finding 1 shows it silently
   lapses whenever its directory is absent — a condition guaranteed by reboot and
   reachable by tmpfiles aging. A control that fails open without signal provides
   false confidence, which is worse than a known absence.
3. **The cost is paid continuously; the benefit is paid rarely.** Six sessions were
   blind at authoring time, and blindness has already produced wrong liveness calls.
4. **Explicit scoping survives** where isolation is genuinely needed — see below.

**The evidence that would reopen this decision:** a fleet kill originating *inside*
a script's subprocess, where the guards saw only an opaque top-level command. If
that occurs, this thread was wrong and the gap must be closed — but by a mechanism
that does not blind, not by restoring L1.

---

## What we are NOT removing

- **The L2 guards** — all three copies stay and become the sole mechanical control.
- **L3, the console harness's explicit socket scoping.** The distinction that
  matters: L3 is *explicit, local, per-invocation* scoping in code that genuinely
  needs isolation, and it does not blind anyone. L1 was *implicit, global, blanket*
  scoping applied to every agent whether it needed isolation or not. Keep the
  former; drop the latter.
- **The console AST enforcement check** (PR #307) that keeps L3 honest.
- **The `tmuxinator` oh-my-zsh plugin.** Its aliases point at the real
  `tmuxinator` binary, not at underscore-prefixed shell functions, so it is
  unaffected by the snapshot defect. Left alone deliberately.

---

## Standing rules inherited from the superseded epic

Binding on this thread. Reproduced because they constrain how Phase 0 may be
executed:

1. **Never put a destructive command in a sub-agent brief** — not as an example,
   not as a thing to "try", not quoted. Describe the hazard class in prose. *(The
   fourth kill was caused by violating this.)*
2. **Guard-testing is payload-only.** Feed the command as a STRING to the guard's
   stdin and read the verdict. Never execute it to see whether it is blocked.
3. **A hook covers exactly one runtime.** Claude Code hooks do not cover Codex.
4. **Merged ≠ protected. Installed ≠ protected. Only FIRING is protected.**
5. **Verify a control in its INSTALL shape, not its dev shape.**
6. **Prefer a firing probe whose failure mode is harmless** — prove a control fires
   using a payload it denies for an UNRELATED, inert reason. Never prove a tmux
   guard with a tmux command.

Two Codex facts that defeat obvious mitigations: Codex **re-extracts its plugin
cache on every run** (patching the cache is silently reverted; a fix reaches Codex
only via a release), and Codex **silently skips UNTRUSTED hooks** (a changed
`hooks.json` invalidates `trusted_hash`, so a version bump can disarm a guard with
no warning — check `[hooks.state]` after every update).

---

## Phases

Ordering is load-bearing. Read "Why this order" before resequencing.

### Phase 0 — Anchor, and prove the guards are alive (BLOCKING)

Removing L1 makes L2 the only mechanical control. It must be verified **before**,
not after.

This matters specifically because the 2026-07-19 kill was caused by a guard that
was merged, released, installed, enabled, trusted, correctly wired, classifying
correctly — and **dead**, because it crashed on an unpackaged import and failed
open. Do not accept the archive's green table as current evidence; re-establish it
against what is shipping today.

1. Anchor a ledger epic for this thread via
   `/livespec-orchestrator-beads-fabro:capture-work-item`, cross-referencing
   `livespec-yiycvd` as superseded-in-part. Record the id at the top of this file.
2. For each of the three guards (host, Claude Driver, Codex Driver), verify **in
   install shape** — staged packaged subtree, bare `python3`, `PYTHONPATH` cleared —
   that it loads without import error and returns a deny verdict for the hazard
   class. **Payload-only** (rule 2): pass the command as a JSON string on stdin;
   execute nothing.
3. Separately prove each guard actually **fires** in its runtime, using an inert
   unrelated payload it denies (rule 6) — e.g. a `--no-verify` commit in a throwaway
   repo, or a blocked memory-file Write. Never prove a tmux guard with a tmux
   command.
4. Confirm the install-shaped test the archived epic added is still present and
   green in both Driver repos.

**Gate: if any guard fails to load, fails to fire, or the install-shaped test is
missing — STOP.** Repair it and re-verify before Phase 1. Do not proceed on the
reasoning that L1 is broken anyway.

### Phase 1 — Remove the environment inversion from the overseer

Repo `livespec`. Delete the whole prefix (finding 2: `unset TMUX` is the
load-bearing half; a partial removal leaves dead config that reads as protective).

| Path | Change |
|---|---|
| `.claude/skills/overseer/supervisor.py:2060-2078` | Delete `_agent_tmux_tmpdir()` and `_with_agent_tmux_tmpdir()` |
| `.claude/skills/overseer/supervisor.py:2093` | Remove the `_launch_command` docstring paragraph describing the inversion |
| `.claude/skills/overseer/test_supervisor.py:950,955,2075` | Remove the helper and assertions expecting the prefix; replace with an assertion that the launch command carries **no** `TMUX_TMPDIR` and **no** `unset TMUX`, so this cannot silently regress |
| `.claude/skills/overseer/AGENTS.md:1065,1069` | Update the spawn recipe; delete "**The `unset TMUX` + `TMUX_TMPDIR` prefix is NOT optional**", which becomes actively wrong |
| `.claude/skills/overseer/AGENTS.md:910,1351-1352` | Update history/regression notes to point here |
| `plan/plan-thread-integrity/design.md:120` | **Dependency check** — it references the namespace. Determine whether that thread depends on the behavior before changing it; if it does, coordinate rather than unilaterally edit |

**Callers** (enumerated at authoring time — re-confirm, line numbers drift):
`supervisor.py:2102` and `supervisor.py:2129`, i.e. **both** the Claude and Codex
launch paths. Both must lose the wrap. Re-check with
`grep -rn "_with_agent_tmux_tmpdir"`.

Also decide, and record: whether the **sandbox mirror** `bd-ib-zaq3` (orchestrator
tenant) is removed in the same change. The archive calls it defense-in-depth rather
than the breached boundary, since the Fabro sandbox is a docker container whose
isolation does not depend on `TMUX_TMPDIR`. It carries the same fail-open property
but not the same blindness cost, since sandboxed agents have no fleet to see. A
defensible outcome is to remove it for consistency, or to leave it and note why.
The archive's open question — whether the fabro provider bind-mounts host `/tmp` —
bears on this and is still unanswered.

### Phase 2 — Cycle the blinded sessions

Long-lived agent processes carry `TMUX_TMPDIR` in their environment and stay blind
until restarted; the Phase 1 change only affects **newly spawned** agents.

1. Re-run the finding-3 probe. The six named sessions may have turned over
   naturally by execution time — **cycle only those still carrying the variable.**
2. Restart each via the overseer's own restart path, not by hand.
3. Re-run the probe; confirm no live pane carries `TMUX_TMPDIR`.

**Constraint:** this touches the maintainer's live fleet. Blindness is confusing,
not dangerous, so there is no urgency justifying a risky bulk operation. Cycle
sessions individually. **Never** use a fleet-wide teardown to accomplish this —
that is the exact hazard class this lineage exists to prevent, and the guards
should refuse it.

### Phase 3 — Remove the oh-my-zsh tmux plugin

Repo `vps-info` (host-scoped; the change lands on `vps`). File it as a child work
item against that repo, as `livespec-6dyst6` was.

**Must come after Phase 1.** See "Why this order".

1. **Back up** `~/.acfs/zsh/acfs.zshrc` to a timestamped copy outside `/tmp` (it is
   tmpfs — a backup there does not survive reboot).
2. Remove `tmux` from the `plugins=(...)` list at `~/.acfs/zsh/acfs.zshrc:67`.
   Leave `tmuxinator`.
3. Add a defensive override to `~/.zshrc.local` — `unalias tmux tksv tds 2>/dev/null`
   — guarded so it is silent when the aliases are absent. `~/.zshrc.local` is sourced
   *after* `acfs.zshrc` (`~/.zshrc:2` then `:5`) and acfs does not own it, so this
   survives an acfs re-template.
4. **Regression vector, verified:** nothing in the locally installed acfs rewrites
   the `plugins=(...)` list — not `bin/acfs`, not `scripts/lib/*.sh`, not
   `onboard/onboard.sh`. (`scripts/lib/update.sh:1244` has a `plugins=(...)` array,
   but it is a git-pull list for four custom plugins, not a writer.) The live
   regression vector is re-running the **upstream** acfs installer or an acfs
   version bump re-templating `acfs.zshrc`. Note `~/.acfs/VERSION` is `0.5.0` while
   `state.json` records `0.3.0` — drift already exists. Step 3 is what makes the fix
   survive that.
5. Codify as a `services/` entry in `vps-info` with an idempotent `install.sh` plus
   smoke test, per that repo's stated convention (every service ships a config file
   and an idempotent installer that is the supported repair path).
6. **Correct `vps-info/CLAUDE.md`** — the tmux-config caveat attributing this to
   "non-interactive shells". Name the Claude Code snapshot mechanism instead
   (finding 4). Leaving it points the next investigator at the wrong layer.

**Verify:** a new shell resolves `type tmux` → `/usr/bin/tmux`; a fresh Claude Code
Bash call runs `tmux ls` successfully; the newest shell snapshot under
`~/.claude/shell-snapshots/` no longer contains a `tmux=` alias line.

**Revert:** restore the backup from step 1, remove the step-3 lines, start a new
shell. Nothing on the host depends on the plugin's aliases (`ta`, `tl`, `to`, `ts`,
`tkss`, `tds`, `tmuxconf`) — verified by search at authoring time — so revert is
clean. Re-verify that claim before relying on it.

### Phase 4 — Write the findings back to the archive

The archived epic documents a shipped mitigation whose fail-open property was
unknown to its authors. Leaving that unrecorded means the next reader trusts a
control that lapses silently.

Append to `plan/archive/tmux-fleet-kill-prevention/handoff.md` (append; do not
rewrite history):

- Finding 1, the fail-open behavior, with its reproduction.
- Finding 2, the `TMUX`/`TMUX_TMPDIR` precedence.
- A pointer to this thread as superseding L1, and the reasoning why.
- A correction to the Calibration bullet at line 116 — the hook's structural limit
  is real, but "the reason L1 matters" no longer holds, because L1 did not reliably
  cover it.

---

## Why this order

- **Phase 0 before Phase 1**, because L1 is the only layer beneath the guards and
  the last incident was caused by a guard everyone believed was working.
- **Phase 1 before Phase 3**, and this one is easy to get backwards: the broken
  shell alias currently **masks** the L1 blindness. In the six scoped sessions,
  `tmux ls` dies at exit 127 — loud and unmistakable — before the real binary ever
  runs. Remove the plugin first and those sessions flip from a *loud crash* to a
  *confident wrong answer*, which is strictly worse for the failure this thread
  exists to fix. Remove the cause of the silence before removing the noise that
  hides it.
- **Phase 2 after Phase 1**, because cycling a session before the launch path is
  fixed just respawns it blind.
- **Phase 4 last**, so the archive records what was actually done.

---

## Definition of done

- [x] Ledger epic anchored; id recorded at the top of this file.
      (`livespec-l4g7wi`, 2026-07-19)
- [x] All three guards verified loading, classifying, and **firing** in install
      shape (payload-only), and the install-shaped test confirmed green in both
      Driver repos. (2026-07-19 — see "Phase 0 execution record")
- [ ] No spawn path in `livespec` emits `unset TMUX` or `TMUX_TMPDIR`; a test
      asserts their absence.
- [ ] `plan/plan-thread-integrity/design.md:120` dependency resolved, either way,
      and the resolution recorded.
- [ ] Sandbox-mirror decision made and recorded with reasoning.
- [ ] No live pane carries `TMUX_TMPDIR`.
- [ ] `tmux` resolves to `/usr/bin/tmux` in a Claude Code Bash call on `vps`; the
      change is codified in `vps-info/services/` with an idempotent installer.
- [ ] `vps-info/CLAUDE.md` names the snapshot mechanism, not "non-interactive
      shells".
- [ ] Archive appended with findings 1 and 2 and the supersede pointer.
- [ ] A bare `tmux ls` from a freshly spawned agent lists the maintainer's real
      fleet. **This is the acceptance test for the whole thread.**

---

## Residuals / open questions

1. **Does the fabro provider bind-mount host `/tmp`?** Inherited unanswered from the
   archived epic. It determines whether the sandbox mirror was load-bearing or
   decorative, and therefore what removing it costs.
2. **The script-subprocess gap is left open**, knowingly (see "Answering the
   archive's counter-argument"). If a kill ever originates inside a script's
   subprocess, reopen — but close it with something that does not blind.
3. **Claude Code's snapshot filter is an upstream defect**, not fixed here. It will
   keep breaking any alias pointing at a single-underscore function, in any plugin,
   on any host. Removing this plugin fixes the instance, not the class. Worth
   reporting upstream; out of scope for this thread.

---

## Phase 0 execution record (2026-07-19)

Executed per the phase text above; the gate **PASSED** on every leg. All
probing was payload-only (standing rule 2): commands traveled exclusively as
JSON strings on each guard's stdin or as file-carried inert probes — nothing
hazard-shaped was executed at any point.

1. **Epic anchored**: `livespec-l4g7wi` (livespec tenant), type `epic`,
   routed `backlog` by the intake Definition-of-Ready checklist (epic-shaped —
   the expected routing for a plan-thread anchor). Description cross-references
   `livespec-yiycvd` as superseded-in-part.
2. **Install-shape classification** — each guard's full stdin/stdout hook
   boundary driven as a subprocess under bare `python3` with `PYTHONPATH`
   cleared, against the host guard's committed 100-case corpus (63 block +
   37 allow), from the INSTALLED artifacts:
   - host `~/.claude/hooks/tmux-fleet-guard.py` — 63/63 + 37/37, 0 errors;
   - Claude Driver v0.4.4 (installed revision `0896984e7c08`) — 63/63 +
     37/37, 0 errors;
   - Codex Driver v0.5.4 (`~/.codex/plugins/cache/.../0.5.4`) — 63/63 +
     37/37, 0 errors;
   - **0 cross-guard disagreements** over the whole corpus.
3. **Firing proofs** (standing rule 6 — inert payloads, each denied for a
   reason whose failure mode is harmless; the three deny texts are distinct,
   so the surfaced reason identifies which guard fired):
   - **Claude Driver**: a live in-session Bash call (an inert unquoted-mention
     `echo` probe, denied by the classifiers' documented over-blocking bias)
     was denied carrying the Driver's `_DENY_REASON` text.
   - **Host**: the same file-carried probe run from a headless `claude -p`
     session in a NON-governed cwd (Driver plugin not loaded there) was denied
     carrying the HOST guard's distinct reason text — isolating the user-scope
     hook as the firing guard.
   - **Codex Driver**: `codex exec` in a throwaway scratch repo attempted the
     archive recipe's probe (a `--no-verify` commit — inert there) and was
     `PreToolUse Blocked` by `livespec_footgun_guard.py (livespec-driver-codex)`,
     the same entry file that carries the tmux classifier; no commit landed.
     This transitively proves the `[hooks.state]` trust is valid for the
     current `hooks.json` — an untrusted hook is silently skipped and would
     not have denied.
4. **Install-shaped tests**: `tests/hooks/test_shipped_hooks_install_shape.py`
   present and green at the origin/master tip of BOTH Driver repos
   (`livespec-driver-claude`: 104 passed; `livespec-driver-codex`: 102
   passed). Content verified to actually stage the packaged-subtree-only cache
   layout under a bare interpreter with a sandbox assertion that `returns` is
   unimportable.

Phase 1 may proceed.
