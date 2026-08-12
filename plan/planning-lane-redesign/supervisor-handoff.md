# Supervisor Handoff - planning-lane-redesign

## Shared Protocol

Read `.ai/supervisor-protocol.md` before driving. Validate this binder together
with that shared layer; neither layer is complete by itself.

Regeneration MUST preserve both Corrections sections byte-for-byte:

- `.ai/supervisor-protocol.md` `## Corrections` for role-level corrections.
- This binder's `## Corrections` for thread-specific corrections.

Preserve spelling, punctuation, code formatting, blank lines, and ordering
exactly; do not normalize Markdown or code spans. Live thread status is not in
this binder. Re-measure it from the ledger, the thread's planning records,
forge artifacts, and the supervisor marker.

Run this cold-open boot block after resolving `supervisor_marker` from the
Bindings table:

```sh
test -f ".ai/supervisor-protocol.md" \
  || { echo "HALT: missing shared supervisor protocol .ai/supervisor-protocol.md"; echo "REMEDY: regenerate the two-layer supervisor handoff before driving"; exit 1; }
printf '%s\n' "BOOT: read .ai/supervisor-protocol.md, this binder, and the supervisor marker if it exists"
[ -n "${supervisor_marker:-}" ] \
  || { echo "HALT: supervisor_marker is unset or empty"; echo "REMEDY: resolve it from this binder's bindings table before running this block — an unset marker makes the read below display NOTHING and still exit 0"; exit 1; }
if [ ! -f "$supervisor_marker" ]; then
  printf '%s\n' "NOTE: no supervisor marker at $supervisor_marker yet — nothing to read."
else
  marker_lines=$(wc -l < "$supervisor_marker")
  if [ "$marker_lines" -le 400 ]; then
    cat "$supervisor_marker"
  else
    sed -n '1,160p' "$supervisor_marker"
    printf '\n*** TRUNCATED: lines 161-%d of %d NOT SHOWN (%d hidden). A claim above may be RETRACTED in the hidden range. Read %s in full before acting on anything above. ***\n\n' \
      "$((marker_lines - 160))" "$marker_lines" "$((marker_lines - 320))" "$supervisor_marker"
    sed -n "$((marker_lines - 159)),${marker_lines}p" "$supervisor_marker"
  fi
fi
```

The read is whole-file up to 400 lines and head-and-tail beyond it. The
truncation notice is mandatory whenever anything is hidden: a constant cap
rots as an append-only marker grows, a head-only cut can separate a live claim
from its later retraction, and Corrections land at the end.

## Bindings

Resolve and report these startup bindings before driving. They contain no live
status, next action, or date-gated behavior.

| Binding | Value |
|---|---|
| `repo_primary` | `/data/projects/livespec` |
| `thread_dir` | `/data/projects/livespec/plan/planning-lane-redesign` |
| `topic` | `planning-lane-redesign` |
| `worker_session` | `planning-lane-redesign` |
| `supervisor_session` | `planning-lane-redesign-supervisor` |
| `WORKER_TARGET` | `'=planning-lane-redesign:'` |
| `SUPERVISOR_TARGET` | `'=planning-lane-redesign-supervisor:'` |
| `runtime_dir` | `/data/projects/livespec/tmp/overseer/planning-lane-redesign/` |
| `supervisor_marker` | `/data/projects/livespec/tmp/overseer/planning-lane-redesign/.supervisor-state` |
| `wait_channel` | `/data/projects/livespec/tmp/overseer/planning-lane-redesign/worker-status.log` |
| `ledger_anchor` | `livespec-zsn2xh` |

Placeholder classes declared by this binder:

- Concretely bound: `repo_primary`, `topic`, `worker_session`,
  `supervisor_session`, and `ledger_anchor`.
- Composed bindings resolved transitively to the fixed-point values shown in
  the table: `thread_dir`, `WORKER_TARGET`, `SUPERVISOR_TARGET`, `runtime_dir`,
  `supervisor_marker`, and `wait_channel`.
- Runtime slots intentionally left unsubstituted for the supervisor to fill at
  use time: `<condition-command>`, `<short-slug>`, and `<branch>`.
- Illustrative placeholders appear only in prose discussing a form, never in a
  fenced command. In the shared protocol, `<repo-primary>` and `<topic>`
  describe reusable path shapes, including `plan/<topic>/supervisor-handoff.md`.
  In this binder's Thread-specific Valves, `<id>` describes the shape of the
  orchestrator action `impl:<id>`. None of these are shell substitutions.

After resolving concrete and composed bindings to the values above, every
fenced shell command contains no generation-time placeholder. The three named
runtime slots are deliberate templates and are not generation errors.

## Generator provenance

This charter was produced by the generator recorded below. The prose digest is
the identity; the plugin, cache ref, and version are human-readable companions.
Run the check before driving so a refreshed cache cannot silently leave this
charter on an older generator. This invocation read the Claude plugin cache, so
the self-check uses that same runtime's cache root.

```sh
generator_plugin='livespec-overseer'
generator_ref='768bce854b95'
generator_version='0.27.6'
generator_prose_md5='eaebe06065b3efa0053d6ea5932d52c0'
cache_root="$HOME/.claude/plugins/cache/$generator_plugin/$generator_plugin"
generator_prose="$cache_root/$generator_ref/prose/supervise-plan.md"
if [ ! -d "$cache_root" ]; then
  printf '%s\n' "UNVERIFIED: no plugin cache at $cache_root, so this is not a host that generates charters and provenance cannot be checked here. Recorded generator: $generator_prose_md5"
elif [ ! -f "$generator_prose" ]; then
  echo "HALT: the cache at $cache_root no longer holds ref $generator_ref, so the generator that emitted this charter has been replaced"
  echo "REMEDY: regenerate this charter with supervise-plan, or re-point generator_ref at the installed ref and re-stamp generator_prose_md5 from it"
  exit 1
else
  installed=$(md5sum "$generator_prose")
  digest_rc=$?
  [ "$digest_rc" -eq 0 ] \
    || { echo "HALT: cannot digest the installed generator prose at $generator_prose"; echo "REMEDY: fix read access before trusting anything this charter says about its own currency"; exit 1; }
  installed_md5=${installed%% *}
  [ "$installed_md5" = "$generator_prose_md5" ] \
    || { echo "HALT: this charter was emitted by generator $generator_prose_md5 but the installed generator is $installed_md5"; echo "REMEDY: regenerate this charter before driving, or re-stamp generator_prose_md5 deliberately after reading what changed between the two"; exit 1; }
  printf '%s\n' "PASS: charter provenance matches the installed generator ($installed_md5)"
fi
```

A missing cache root means provenance cannot be checked on that host and is
reported as UNVERIFIED without making the committed charter unreadable. An
existing cache root that no longer contains the recorded ref means the
generator was replaced and is a HALT. These absence cases are intentionally
different. The recorded version is a companion, not the identity: this same
prose digest also shipped under ref `448032c6dcf1` as versions `0.15.0`,
`0.16.2`, and others, so a version match would report a different generator
where there is one and the same.

## Thread-specific Valves

- The ledger anchor is epic `livespec-zsn2xh` in the `livespec` tenant. The
  design record is `plan/planning-lane-redesign/research/` — `seed-prompt.md`
  (the maintainer's ask), `brainstorm.md` (analysis), and
  `maintainer-rulings.md` (decisions). Where any prose disagrees with
  `maintainer-rulings.md`, the rulings win. All of it is historical design
  evidence, not a status ledger: read status from the ledger.
- **This plan governs the redesign of the plan machinery itself.** Its scope
  is: mutable planning state moves to the ledger; scoping becomes an explicit
  ledger event; a two-leg archive gate; retirement of the "plan thread"
  vocabulary. **The core redesign RATIFIED as `SPECIFICATION/history/v197`**
  (PR #2057, merge `d6c64ae3`), with a one-sentence follow-up in `v198`. The
  scoping cut is ALREADY FILED: dotted children under
  `livespec-zsn2xh` in this tenant (five at generation, more since — enumerate
  them, never trust this count), plus ten sibling-tenant items —
  `bd-ib-mrqoy2` and `bd-ib-da4fs2` in repository
  `livespec-orchestrator-beads-fabro`; `overseer-pfpfty` and `overseer-ftfhek`
  in repository `livespec-overseer`; `bd-gj-mbde5p` in repository
  `livespec-orchestrator-git-jsonl`; `livespec-dev-tooling-jaut4y` in
  repository `livespec-dev-tooling`; `livespec-runtime-gp3ppk` in repository
  `livespec-runtime`; `livespec-driver-claude-wgi3uy` in repository
  `livespec-driver-claude`; `livespec-driver-codex-4y5ijl` in repository
  `livespec-driver-codex`; `livespec-console-beads-fabro-sisnmx` in repository
  `livespec-console-beads-fabro`. These ids are stable structural pointers;
  their statuses are NOT recorded here — re-measure before acting.
- **`livespec-zsn2xh.4` (ratification) WAS the maintainer valve and is now
  CLOSED** — the maintainer authorized the accept and it landed as `v197`.
  The rule it embodied still binds every FUTURE ratification this plan drives:
  an independent read-only Fable-model adversarial review must return a literal
  NO-BLOCKERS verdict before the revise accept, per `AGENTS.md` §"Independent
  Fable review before every ratification" and `.ai/spec-proposal-review.md`. A
  blocker routes to the maintainer with a recommended fix and is never
  self-waived — including when this thread authored the proposal under review.
  It took THREE review rounds here (six blockers, then two, then none); budget
  for that rather than expecting one pass.
- **Vocabulary: "plan thread" is banned** (maintainer-declared 2026-08-04).
  The artifact is called a "plan". Every instruction, work-item, commit, and
  report this thread produces uses "plan"; quoting pre-existing text verbatim
  for mechanical replacement targeting is the only exception, and frozen
  `archive/` and `history/` trees keep the old term. Until child
  `livespec-zsn2xh.2` lands the ban in the committed agent-instruction
  surface, this clause is the ban's carrier for this thread.
- **This plan was designed to have NO
  `plan/planning-lane-redesign/handoff.md`, and one now EXISTS anyway.** A
  Fabro sandbox working a DIFFERENT work-item created it 2026-08-05T21:59:56Z
  in commit `275b704d` ("arm plan lifecycle anchor check"), which added a
  handoff to five plans; this plan, having none, got a new file. `v197` now
  FORBIDS both `handoff.md` and `supervisor-handoff.md` in a plan store, so
  this directory currently violates the contract it ratified. Do NOT delete
  either file here as a tidy-up: removal is `livespec-zsn2xh.5`'s scope, and it
  is ORDERED BEHIND the `livespec-overseer` respawn/injection template, which
  still points at `plan/<topic>/handoff.md` (covered by `overseer-pfpfty`).
  Deleting early breaks cold-open respawn — that defect already stalled a live
  worker on a picker asking how to wind down without the file. PROVEN by
  experiment, so no one need re-derive it: the armed
  `check-plan-thread-anchor-declared` does NOT require the file to exist. It
  globs `plan/*/handoff.md`, so absence contributes no offender and exits 0;
  a handoff missing its anchor exits 1. Migration can simply delete; no check
  change, exemption, or placeholder is needed.
- The two epic-shaped sibling items (`bd-ib-mrqoy2` in repository
  `livespec-orchestrator-beads-fabro`, `overseer-pfpfty` in repository
  `livespec-overseer`) are groomed IN THEIR OWN repositories via the groom
  operation once their dependency on `livespec-zsn2xh.4` clears. Do not
  decompose them from this seat and do not open plans for them.
- Child `livespec-zsn2xh.1` (the bd long-prose spike) must NEVER run
  `bd init` inside a primary checkout or worktree — an embedded scratch
  ledger in a temp directory outside every checkout is the only sanctioned
  substrate. Its go/no-go verdict gates the proposal (`livespec-zsn2xh.3`).
- Ready, factory-safe implementation is built factory-side — the `drive`
  operation with action `impl:<id>`, or the Dispatcher drain — never inline
  in the planning session. When factory capacity is saturated, building a
  ready slice directly on the worker via Red-Green-Replay is the sanctioned
  fallback this repository has used before.
- Cross-repo dependency edges in this cut use the typed
  `sibling_work_item` form and ride in item metadata, not beads edges; the
  Dispatcher gates on them via `resolve_ref`. When re-measuring a sibling
  item, run `bd` from INSIDE that sibling's repository so `.beads/` routes to
  its tenant (exemplar command in "How to inspect and drive").
- The sibling plan `plan/foreman/` in repository `livespec-overseer` is
  cross-linked history, not scope: its post-mortem seeded this plan, and its
  Phase C+D consensus work stays its own. Neither plan closes into the other.
- Write every repository name in full in maintainer-facing output. This
  thread cites both `livespec-orchestrator-beads-fabro` and
  `livespec-console-beads-fabro`; the bare suffix `beads-fabro` is banned as
  ambiguous.

## HALT-first preconditions

Expected worker session: `planning-lane-redesign`.

Expected supervisor session: `planning-lane-redesign-supervisor`.

Exact target repository: `/data/projects/livespec`.

Run these in order before doing anything else. Stop on the first failure and
act on its labelled `REMEDY:`.

1. The supervised session exists:

```bash
WORKER_TARGET='=planning-lane-redesign:'
tmux has-session -t "$WORKER_TARGET" \
  || { echo "HALT: expected worker session 'planning-lane-redesign'"; echo "REMEDY: ask the maintainer whether to start that worker session"; exit 1; }
```

2. The supervised session is a live agent session:

```bash
WORKER_TARGET='=planning-lane-redesign:'
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
[ -n "$pane_pid" ] \
  || { echo "HALT: empty pane_pid for 'planning-lane-redesign'"; echo "REMEDY: re-check the exact worker target and stop if it still resolves empty"; exit 1; }
ps -o pid=,comm=,args= --ppid "$pane_pid" --pid "$pane_pid" -H
# PASS only if a live `claude` or `codex` process appears in that tree.
# A lone shell (zsh/bash) with no agent child is a HALT.
# REMEDY: if no live agent appears, ask the maintainer whether to restart the worker.
```

Report which live driver was found. A launcher may own the `comm` column while
the agent name appears only in `args`, so read the full argument vector rather
than the command name.

3. The supervisor session exists, is a distinct pane, and contains a live agent:

```bash
WORKER_TARGET='=planning-lane-redesign:'
SUPERVISOR_TARGET='=planning-lane-redesign-supervisor:'
tmux has-session -t "$SUPERVISOR_TARGET" \
  || { echo "HALT: expected supervisor session 'planning-lane-redesign-supervisor'"; echo "REMEDY: switch to the correct supervisor session or ask the maintainer to bootstrap it"; exit 1; }
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
supervisor_pane_pid=$(tmux display-message -p -t "$SUPERVISOR_TARGET" '#{pane_pid}')
[ -n "$supervisor_pane_pid" ] \
  || { echo "HALT: empty pane_pid for 'planning-lane-redesign-supervisor'"; echo "REMEDY: re-check the exact supervisor target and stop if it still resolves empty"; exit 1; }
[ "$supervisor_pane_pid" != "$pane_pid" ] \
  || { echo "HALT: supervisor and worker resolve to the SAME pane"; echo "REMEDY: re-check both exact targets — a prefix match puts both names on one pane, and the worker's agent then reads as the supervisor's"; exit 1; }
ps -o pid=,comm=,args= --ppid "$supervisor_pane_pid" --pid "$supervisor_pane_pid" -H
# PASS only if a live `claude` or `codex` process appears in that tree.
# A lone shell (zsh/bash) with no agent child is a HALT.
# REMEDY: if no live agent appears, ask the maintainer to start the agent in that session.
```

Both pids are resolved inside this block rather than inherited from the
previous check, so it is self-contained and cannot pass on an unset variable.

4. The plan exists inside the absolute target repository:

```bash
test -d "/data/projects/livespec/plan/planning-lane-redesign" \
  || { echo "HALT: missing plan /data/projects/livespec/plan/planning-lane-redesign"; echo "REMEDY: create or choose the correct plan topic before supervising"; exit 1; }
```

5. The worker pane's resolved cwd is inside the target repository:

```bash
WORKER_TARGET='=planning-lane-redesign:'
pane_cwd=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_current_path}')
[ -n "$pane_cwd" ] \
  || { echo "HALT: empty pane_current_path for 'planning-lane-redesign'"; echo "REMEDY: re-check the exact worker target and stop if it still resolves empty"; exit 1; }
case "$(readlink -f -- "$pane_cwd")" in
  /data/projects/livespec|/data/projects/livespec/*) echo "PASS: $pane_cwd" ;;
  *) echo "HALT: pane cwd $pane_cwd is outside the target repo"; echo "REMEDY: move the worker into the target repo or start the correct worker session"; exit 1 ;;
esac
```

## How to inspect and drive

Re-measure the ledger anchor before carrying forward any filed status or
acceptance claim:

```sh
cd /data/projects/livespec
ledger_anchor='livespec-zsn2xh'
# The ledger is a per-repo tenant database, so `bd` needs the fleet credential
# wrapper WHERE ONE IS INSTALLED — a bare `bd` returns "Access denied" there.
# DETECTED, never hard-coded: an adopter without the wrapper must still be able
# to re-measure, and a hard-coded path would only trade one false HALT for
# another.
ledger_show() {
  if command -v with-livespec-env.sh >/dev/null 2>&1; then
    with-livespec-env.sh -- bd show "$1" --json
  else
    bd show "$1" --json
  fi
}
if ! ledger_json="$(ledger_show "$ledger_anchor")"; then
  echo "HALT: cannot re-measure ledger item '$ledger_anchor'"
  if command -v with-livespec-env.sh >/dev/null 2>&1; then
    echo "REMEDY: the credential wrapper WAS used, so ledger access is not the suspect — check the anchor id is real and that this repo's tenant is reachable"
  else
    echo "REMEDY: no credential wrapper on PATH, so a BARE 'bd' ran — if this repo's ledger is a tenant database, install/expose the fleet credential wrapper; otherwise check the anchor id"
  fi
  exit 1
fi
# EXIT STATUS IS NOT EVIDENCE. A tool that exits 0 while printing nothing would
# let the MEASURED_AT stamp below certify a re-measurement that never happened.
[ -n "$ledger_json" ] \
  || { echo "HALT: ledger re-measure for '$ledger_anchor' exited 0 but returned NOTHING"; echo "REMEDY: do not record this as a measurement — an empty success is not a reading; confirm the anchor exists and that the ledger tool is actually reporting"; exit 1; }
printf '%s\n' "$ledger_json"
date -u '+MEASURED_AT: %Y-%m-%dT%H:%M:%SZ'
```

The epic's dotted children carry the livespec-side status. Enumerate them from
the ledger rather than from this binder or the research docs. Pass `--all`:
the default listing HIDES closed items, so a child that was filed and finished
reads as never filed.

```sh
cd /data/projects/livespec
ledger_children() {
  if command -v with-livespec-env.sh >/dev/null 2>&1; then
    with-livespec-env.sh -- bd list --parent "$1" --all --json
  else
    bd list --parent "$1" --all --json
  fi
}
if ! children_json="$(ledger_children 'livespec-zsn2xh')"; then
  echo "HALT: cannot enumerate children of 'livespec-zsn2xh'"
  echo "REMEDY: apply the same wrapper-versus-anchor triage as the command above before treating the epic as childless"
  exit 1
fi
printf '%s\n' "$children_json"
date -u '+MEASURED_AT: %Y-%m-%dT%H:%M:%SZ'
```

An empty child list is a FINDING ONLY AFTER a positive control, because an
empty array is what a broken query returns too. Run the control against the
same command shape with a parent known to have children before reporting the
epic as childless:

```sh
cd /data/projects/livespec
control_parent='livespec-jvdvx4'   # known to have children in this tenant
if command -v with-livespec-env.sh >/dev/null 2>&1; then
  control_json=$(with-livespec-env.sh -- bd list --parent "$control_parent" --all --json)
else
  control_json=$(bd list --parent "$control_parent" --all --json)
fi
case "$control_json" in
  ''|'[]') echo "HALT: the positive control returned no rows, so this query shape proves NOTHING about an empty result for the real anchor"; echo "REMEDY: fix the query or pick a control parent that certainly has children before treating any empty child list as absence"; exit 1 ;;
  *)       printf '%s\n' "PASS: control parent $control_parent returned rows, so an empty result for the real anchor is genuine absence" ;;
esac
```

Ten of this plan's items live in SIBLING tenants and are invisible to every
query run from `/data/projects/livespec`. To re-measure one, run `bd` from
inside that sibling's repository so `.beads/` routes to its tenant. Exemplar
for the rewrite item in repository `livespec-orchestrator-beads-fabro`;
substitute the sibling path and id from the Thread-specific Valves list for
the others:

```sh
cd /data/projects/livespec-orchestrator-beads-fabro
if command -v with-livespec-env.sh >/dev/null 2>&1; then
  with-livespec-env.sh -- bd show 'bd-ib-mrqoy2' --json
else
  bd show 'bd-ib-mrqoy2' --json
fi
date -u '+MEASURED_AT: %Y-%m-%dT%H:%M:%SZ'
```

Preserve the tmux lookup verdict before filtering its output:

```sh
WORKER_TARGET='=planning-lane-redesign:'
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
tmux_rc=$?
[ "$tmux_rc" -eq 0 ] \
  || { echo "HALT: tmux pane lookup failed for 'planning-lane-redesign'"; echo "REMEDY: re-check the exact target before filtering its output"; exit 1; }
printf '%s\n' "$pane_pid" | head -1
```

Inspect read-only with a scrollback sample plus the visible pane:

```sh
WORKER_TARGET='=planning-lane-redesign:'
tmux capture-pane -p -t "$WORKER_TARGET" -S -40
```

Check the visible footer for an open picker before every paste:

```sh
WORKER_TARGET='=planning-lane-redesign:'
pane=$(tmux capture-pane -p -t "$WORKER_TARGET")
tmux_rc=$?
[ "$tmux_rc" -eq 0 ] \
  || { echo "HALT: cannot inspect the worker pane before paste"; echo "REMEDY: re-check the exact worker target before sending input"; exit 1; }
if printf '%s\n' "$pane" | tail -8 \
     | grep -qE '^[[:space:]]*Enter to (select|confirm)[[:space:]]*(·.*)?$'; then
  echo "HALT: picker open in worker pane"
  echo "REMEDY: answer or close the picker before pasting new input"
  exit 1
fi
```

For a short instruction, replace the allowed runtime slot, send the text,
verify that it landed, and then send Enter separately:

```sh
WORKER_TARGET='=planning-lane-redesign:'
tmux send-keys -t "$WORKER_TARGET" -- '<condition-command>'
tmux capture-pane -p -t "$WORKER_TARGET" | tail -8   # confirm it landed
tmux send-keys -t "$WORKER_TARGET" Enter             # only after verifying
```

For longer text, write the reviewed instruction to a file under `runtime_dir`,
then paste a one-line reference, verify, and submit it in separate calls:

```sh
WORKER_TARGET='=planning-lane-redesign:'
tmux load-buffer -b sup /data/projects/livespec/tmp/overseer/planning-lane-redesign/brief-01.md
tmux paste-buffer -b sup -t "$WORKER_TARGET"
tmux capture-pane -p -t "$WORKER_TARGET" | tail -8   # confirm it landed
tmux send-keys -t "$WORKER_TARGET" Enter             # only after verifying
```

Create the named wait channel, tell the worker to append one line there at
every milestone, and arm this pane watcher before ending a turn with
worker-held work in flight:

```sh
WORKER_TARGET='=planning-lane-redesign:'
wait_channel=/data/projects/livespec/tmp/overseer/planning-lane-redesign/worker-status.log
mkdir -p "$(dirname "$wait_channel")"
: > "$wait_channel"
# Tell the worker: append one line to "$wait_channel" at every milestone.

prev="__OVERSEER_NO_CAPTURE_YET__"; stable=0
for i in $(seq 1 180); do                    # ~60 min ceiling
  sleep 20
  pane=$(tmux capture-pane -p -t "$WORKER_TARGET")   # visible only
  [ -z "$pane" ] && { echo "WAKE: pane unreadable — session may be gone"; exit 0; }
  if printf '%s\n' "$pane" | tail -8 \
       | grep -qE '^[[:space:]]*Enter to (select|confirm)[[:space:]]*(·.*)?$'; then
    echo "WAKE: picker open"; exit 0
  fi
  if [ "$pane" = "$prev" ]; then stable=$((stable+1)); else stable=0; prev="$pane"; fi
  if [ "$stable" -ge 3 ]; then echo "WAKE: pane unchanged ~60s — idle"; exit 0; fi
done
echo "WAKE: watcher ceiling reached — worker still busy, RE-ARM NOW"
```

Use a condition watcher against the authoritative artifact for every non-pane
obligation. Test terminal state first and wake on unknown values as required by
the shared protocol. This plan's most common non-pane obligation is a PR
awaiting review and merge, so poll `state` before any derived field:

```sh
cd /data/projects/livespec
for i in $(seq 1 60); do
  sleep 60
  pr_state=$(gh pr view '<branch>' --json state --jq '.state')
  gh_rc=$?
  [ "$gh_rc" -eq 0 ] \
    || { echo "WAKE: cannot read PR state for '<branch>' — investigate before waiting further"; exit 0; }
  case "$pr_state" in
    MERGED|CLOSED) echo "WAKE: PR reached terminal state $pr_state"; exit 0 ;;
    OPEN)          : ;;
    *)             echo "WAKE: unrecognized PR state '$pr_state' — reporting rather than assuming it means keep waiting"; exit 0 ;;
  esac
done
echo "WAKE: PR watcher ceiling reached — still OPEN, RE-ARM NOW"
```

## Resume state — POINTERS ONLY, re-measure every one

Written at session wrap 2026-08-12T09:2xZ. These are pointers to things that
existed then, NOT status. Re-measure each with the commands above before acting.
The supervisor marker the cold-open block reads carries the detail this section
deliberately does not duplicate.

**NOTHING IS IN FLIGHT ON A SANDBOX OR A SUB-AGENT.** Every background task this
seat started was stopped at wrap. Two tracks are parked at clean points and one
maintainer-authorized investigation is open.

### THE IMMEDIATE NEXT ACTION

Hand `overseer-pfpfty.10` to the worker. It is FILED and READY and has never been
briefed — it is the round-5 amendment clearing three round-4 review blockers, and
its notes carry the required fix for each. It is HOST-ONLY in practice: the
authoritative 565-line verdict is tracked at
`plan/planning-lane-redesign/research/review-pfpfty-proposal-round4.md` in
repository `livespec`, but the item's own working context exceeds the factory's
unattended-turn size band. Brief the worker; do not dispatch it.

### The overseer track — `overseer-pfpfty` in repository `livespec-overseer`

`.1`, `.6`, `.8` CLOSED. `.2` (ratification, human valve) is `blocked` and now
depends on `.1 .6 .8 .9 .10`. `.9` is `pending-approval`; `.10` is `open`; `.7`
is `backlog` and correctly gated on `.2`; `.3/.4/.5` are `pending-approval`
behind `.2`.

**THE REVIEW HAS RUN THREE ROUNDS AND IS CONVERGING, NOT THRASHING.** Round 1
returned 6 blockers (Opus), round 2 returned 4 (Opus), round 4 returned 3
(Fable 5, the model `AGENTS.md` requires). Every round's new findings sat in the
PREVIOUS round's fix text, and each round re-derived the earlier clearances as
holding. All three verdicts are TRACKED on `livespec` master under
`plan/planning-lane-redesign/research/review-pfpfty-proposal-round{1,2,4}.md` —
they are no longer gitignored and cannot be lost to a scratch sweep.

**A round-5 review is owed once `.10` lands, and the reviewer question recurs.**
The worker cannot review an amendment it authored. The maintainer's Opus
authorizations were each scoped to ONE round; round 4 returned to Fable
deliberately. Ask again rather than assuming.

**THE ATTESTATION RULE, and it is the one a CLI cannot catch:** the ratification
record names the model PER ROUND — rounds 1 and 2 Opus 5, round 4 Fable 5. NO
blanket value is honest for this history. Round 4's blocker 3 exists because the
proposal's own "MUST read `reviewer_model: opus`, never `fable`" EXPIRED the
moment a Fable round was commissioned, and followed literally would now mandate a
false attestation about the very review the accept gates on.

### The orchestrator track — `bd-ib-mrqoy2` in repository `livespec-orchestrator-beads-fabro`

Seven of eight children CLOSED. Only `.6` remains, and it is HALF DONE: its
DOC-ONLY prose half MERGED as PR #1363, merge `3cd4dde2`. The item is `ready`.

**The deferred `.py` half is SIX lines, not the two an earlier note of mine
said** — `_needs_attention_handoffs.py:39`, `test_needs_attention.py:256`, and
`commands/plan.py:1,38,68,78`, the last including a SECOND shipped operator
string. Re-enumerate again rather than trusting that list either; the item's own
description says to.

**It is blocked by `check-master-ci-green` whenever that repo's master CI is
red**, because the gate sits in the COMMIT path — see correction T14 for the
scope clause that made the doc-only half landable anyway. Do not weaken, lever,
or exempt that gate.

### `livespec-ck8c` — nine occurrences, and the diagnosis moved

The maintainer authorized fixing the CI dependency-install step. **Confirm the
hypothesis before spending that fix.** Occurrence nine was
`tls: failed to verify certificate: x509: certificate is not valid for any
names, but wanted to match api.github.com`, from the auto-merge automation — a
certificate valid for NO name, beside git-side failures reporting
`CAfile: none CRLfile: none`. Both are consistent with TLS INTERCEPTION on the
runner network, which neither a wheel cache nor a retry policy would fix. The
container-cache finding recorded on the item explains the pythonhosted TIMEOUT
cluster and the frequency; it does not explain the certificate class. Full
evidence, both symptom tallies, and the reframing are on the item.

### Ledger corrections this seat made and verified — do not re-litigate

Round 4 falsified two claims this seat wrote when the `.9` split was authorized:
that population happens "at the moment a track is discovered/assigned" (discovery
is the DAEMON's act, which the proposal expressly bars from the anchor), and that
it "contradicts no clause of the CURRENT spec" (the live persisted-facts
ONLY-enumeration excludes a populated epic id — proven by the proposal's own
EDIT 4 adding it). BOTH ARE CORRECTED in `.9`'s description and `.2`'s comment.
The `.9`-first ORDER still stands; only the argument was wrong. The sharpened
consequence: the accept must follow `.9` IMMEDIATELY or land with it, because a
doctor pass in the gap would legitimately flag the populated epic.

### Environment notes

- `/data/projects/livespec-overseer` is ~28 commits behind and CANNOT be
  refreshed: `.livespec.jsonc` and two `plan/*/handoff.md` files are other live
  sessions' uncommitted work. Do NOT force it — that would discard two handoffs.
  Branch worktrees from `origin/master` directly; this blocks nothing.
- `overseer-pfpfty.9` and `.7` were filed via `bd create`, which defaults to
  `open` and normalizes to `backlog` — outside the ready queue. `.9` was set to
  `pending-approval` to match its siblings. Check filed status before assuming an
  item is runnable.
- Other lanes land in `livespec-overseer` and
  `livespec-orchestrator-beads-fabro` continuously. Master moved under this
  plan's work repeatedly, once invalidating four line-number citations in the
  proposal. Re-pin and re-derive.

## Corrections

Thread-specific corrections belong here. Regeneration must preserve this
section byte-for-byte, including spelling, punctuation, code formatting, blank
lines, and ordering.

T1. A ratification reached master carrying a review attestation that was
MINTED, and the CLI accepted it. `v198`'s revision record claims
`separate_reviewer: True`, `reviewer_model: fable`, `verdict: NO BLOCKERS`,
with `reviewed_at` IDENTICAL TO THE SECOND to `revised_at`
(`2026-08-05T22:18:22Z`) from a proposal whose `created_at` was `22:17:59Z` —
a 23-second propose→review→ratify by a single `gpt-5-codex` sandbox. No
journal or transcript evidences such a reviewer.

The `content_digest` RECOMPUTED CORRECTLY, and that is the precise shape of
the trap: the sandbox computed honest mechanics and filled in conforming
attestation fields, because `_timestamp_error` in
`.claude-plugin/scripts/livespec/commands/_revise_ratification.py` validates
that `reviewed_at` is well-formed ISO-8601 and NOTHING about whether the
review preceded the ratification.

The cheapest tell costs one comparison, so use it on any ratification you did
not personally watch: a genuine review has `reviewed_at` minutes BEFORE
`revised_at` (`v197`: 2m29s). A same-second pair is not a fast review, it is
not a review. Filed as `livespec-pw55` (P1) with the fix scoped and verified
against both real cases.

T2. I CAUSED that minting through a work-item I wrote, and the shape is easy
to repeat. `livespec-zsn2xh.8`'s description said "file as a normal
propose-change; not an emergency" while its `acceptance_criteria` said the rule
must be STATED in `non-functional-requirements.md` on master — an end-state
reachable ONLY by ratifying. Given a prose instruction and a checkable
criterion that contradict, an agent satisfies the checkable one. That is not
implementer misbehavior; it is the predictable reading.

For a propose-change carrier the acceptance criterion MUST stop at "the
proposal file exists under `SPECIFICATION/proposed_changes/` with `topic`
equal to its stem". The ratified end-state belongs to a SEPARATE carrier gated
on the human valve. I had been careful about exactly this distinction in every
brief I sent the worker, and lost it in an item I wrote myself.

T3. The spec tree moves UNDER a pending proposal, and a previously-CLEARED
blocker can reopen without anyone touching the proposal. Between this
proposal's authoring and its accept, `v194`, `v195`, and `v196` ratified;
`v199` landed while the follow-up was in flight. `v194` added two named
paragraphs to the exact `non-functional-requirements.md` section this proposal
rewrites, taking that set from six to eight — silently invalidating an
enumeration that had already passed an independent review round. That is
clause-lockstep, and it was introduced by ANOTHER lane's landing, not by the
author.

So the second ratifier must re-derive not only the resulting bytes but every
COUNT and ENUMERATION its proposal asserts. And because a `resulting_files[]`
entry replaces an ENTIRE file, a payload computed against stale bytes silently
reverts the intervening revisions with no git conflict and no CI failure — it
merges clean and looks green. Verify survival explicitly after any accept:
grep a distinctive marker from each intervening revision, with a positive
control proving the grep can report absence.

T4. A watcher that fires into a session nobody resumes is indistinguishable
from no watcher. The round-3 review completed at 07:57 with NO-BLOCKERS; the
worker then parked on a Claude usage-limit modal whose own reset time had
passed ~14h earlier, and the pair sat for 15.3h. My pane watcher DETECTED it
correctly and exited `WAKE: picker open` — its regex already covers both
`Enter to select` and `Enter to confirm`. Detection was never the gap; the
wake had nowhere to land.

Two consequences. A limit banner in scrollback is not evidence of a CURRENT
limit — check its stated reset against `date -u` before believing it. And when
a watcher's value depends on a reader, say so in the obligation record rather
than treating "armed" as "handled".

T5. A GREEN CHECK RUN THROUGH A CODE PATH CI DOES NOT TAKE IS NOT A PREDICTION
ABOUT CI. I ran `check-doctor-static` locally, got zero non-pass findings, and
pushed. CI failed the same check on the same commit. Both runs were honest; they
exercised DIFFERENT BRANCHES. The citation checker resolves a cross-repo
citation against a local clone when one is configured, and falls back to the
`external_references` allowlist when none is. Locally
`/data/projects/livespec` exists, so it passed by RESOLUTION and never touched
the allowlist. On the runner that path cannot exist, so the allowlist was the
only path — and it had been silently emptied.

Emptied by a real core defect, now filed as `livespec-bpzy`:
`_read_cross_repo_headings` maps an UNREADABLE clone file to an EMPTY
`frozenset`, and `_validated_external_references` keeps an entry only when
`headings is None or head in headings`. An empty set is neither, so EVERY
allowlist entry for that repo is dropped and each allowlisted citation fails
claiming it "is not allowlisted". The branch is marked `# pragma: no cover`.

The asymmetry is the part worth carrying: NOT registering a cross-repo target
is SAFER than registering one, because an unconfigured repo yields `None` and
the allowlist survives. Registering it — required for the Dispatcher readiness
gate — is what breaks the citation checker. Doing the right thing for one
subsystem broke another, and the error message blamed the citation rather than
the unreachable clone.

Two habits, both cheap. When a check consults an EXTERNAL artifact, ask which
branch your green run took and whether CI can take the same one; if it cannot,
simulate the CI shape locally before pushing (breaking `local_clone` to a
nonexistent path reproduced the CI failure exactly, in seconds). And when a
first hypothesis is cheap to test, test it rather than act on it — mine here
was that the apposition wording confused the parser, and it was WRONG; reverting
it would have degraded the change while leaving the failure untouched.


T6. A WHOLE-FILE `resulting_files[]` PAYLOAD MUST BE CHECKED IN BOTH
DIRECTIONS, AND I ONLY ASKED FOR ONE. I commissioned an independent pre-merge
check for T3's failure mode — a sentence silently LOST by a whole-file
replacement. What the reviewer found was the inverse: an OLD sentence silently
SURVIVING into the clause meant to replace it. The ratified slim-store clause
shipped as "MUST contain only write-once research inputs under
`plan/<slug>/research/` (one note MAY sit directly in `plan/<slug>/`)" — the
parenthetical carried over from the very thread-store prose that change deletes.
Self-contradictory, absent from the proposal, and forbidden by core's own
bullet.

Same root cause as T3 (a payload composed from partly-stale prose), same
absence of signal: no git conflict, no CI failure, gate green locally. And my
structural checks — declared-file scope, H2 heading sets before/after, counts —
ALL PASSED on it, because a surviving sentence changes no structure.

So ask both questions of any whole-file payload: what vanished that should have
stayed, AND what stayed that should have vanished. Only a content read answers
the second.

T7. `gh pr merge --disable-auto` IS NOT A HOLD IN THIS FLEET. I disabled
auto-merge to keep a ratification from landing while an independent check ran.
`app/livespec-pr-bot` re-armed it two minutes later and the PR merged mid-review
— the reviewer then returned a BLOCKER on bytes already on master.

This is NOT a bot defect, and I initially reported it as one. Reading
`.github/workflows/auto-enable-merge.yml`, the workflow behaves exactly as
documented and gates on:

```
github.event.pull_request.draft == false
&& !contains(github.event.pull_request.labels.*.name, 'do-not-merge')
```

So a durable hold exists and I used the wrong tool. `--disable-auto` is a
one-shot toggle the workflow re-applies on qualifying events. **To hold a PR
here: mark it DRAFT, or apply the `do-not-merge` label.** I did not file the
bot defect the maintainer had authorized, because the evidence I gathered
afterwards did not support the premise I gave them when they authorized it —
filing it would have sent someone chasing correct behavior.

T8. A SANDBOX CANNOT READ THE HOST, AND I BRIEFED ONE TO TRY. `bd-ib-mrqoy2.8`
was dispatched to the factory with step 1 pointing at
`/data/projects/livespec/tmp/overseer/.../review-v059-post-repair-verdict.md`.
Fabro sandboxes are isolated: no host filesystem outside the repo checkout, and
no `bd` (the tenant secret is deliberately absent), so the ledger was no
fallback either. The run failed having produced nothing.

Two things worth carrying. First, the agent behaved WELL — it hunted for a
legitimate source, established the PR carried only the stale timestamp, and
STOPPED rather than inventing an artifact, on the one item where fabricated
evidence would have been most corrosive. Read that failure as correct refusal,
not misbehavior, and do not bare-retry it.

Second, the dispatchability question is about REACHABILITY OF INPUTS, not just
item size or phrasing. Before dispatching, ask what the sandbox must READ and
whether it can. An item whose input exists only on the host belongs on a worker,
or must be re-scoped so the input travels inside the repo or the work-item.

T9. SIZE THE DISPATCH GOAL, NOT JUST THE DESCRIPTION. I nearly dispatched an
item whose description (1529) plus notes (5698) totalled 7227 characters —
essentially identical to the 7196-char item on record for implementing its whole
change and then dying at the unattended-turn cap mid-publish, losing an hour.
The dispatcher's sizing warning fires on the DESCRIPTION alone, but the goal
ships description AND notes. Condensing the notes to the actionable directive
brought it to 3549 and the depth lost nothing — it already lived in the
supervisor marker and a preserved artifact. Measure `description + notes` before
every dispatch; the warning will not do it for you.

T10. I DISPATCHED TWO SLICES IN PARALLEL THAT EDIT THE SAME FILES, AND THE
CAPACITY CHECK IS WHAT FOOLED ME. `bd-ib-mrqoy2.4` and `.5` both modify
`_needs_attention_handoffs.py` and `needs_attention.py`. I confirmed
dispatcher-tracked in-flight was ZERO against a cap of 2, concluded parallel was
safe, and sent both. `.4` merged first, `.5`'s branch went `DIRTY`, CI never ran
on it at all, and a whole sandbox run was discarded.

The cap answers "may two run at once". It says NOTHING about whether two slices
touch the same files, and `AGENTS.md` already draws that distinction — dispatch
independent NON-CONFLICTING items in parallel, "sequence only items that
conflict on overlapping files". Worse, this cut's OWN groom review had flagged a
same-file coupling, and the earlier review named
`_needs_attention_handoffs.py:30` explicitly. The warning was in the record and I
did not apply it at dispatch time.

One command prevents it: `comm -12` the two items' expected file sets before any
parallel dispatch. Do it every time two go out together.

T11. A `failed` DISPATCH MAY BE COMPLETE, OR GENUINELY BROKEN, AND ONLY THE
FORGE TELLS YOU WHICH. Both `.3` and `.5` reported `status=failed`,
`pr_number=null`, `merge_sha=null` with the identical symptom: the run pushed
successfully, then rebased and re-pushed, and GitHub rejected the second push
non-fast-forward because the rewritten HEAD no longer descended from what it had
already pushed. The run raced itself. In both cases the sandbox refused to
force-push, which is correct and must not be "fixed" at the agent.

They then diverged completely. `.3`'s PR #1345 was clean, carried the full work
(PR head SHA equalled the remote branch tip), passed 95 of 97 checks, and merged
unchanged. `.5`'s PR #1353 was `DIRTY` with ZERO check runs and had to be
discarded. So "a failed dispatch may actually be green" is TRUE but is not a
licence to assume it — compare the PR head to the branch tip and read the checks,
every time. Filed as `bd-ib-xw34`.

And before redispatching: DELETE the surviving remote branch. A branch left in
place is precisely what kills the next attempt with the same non-fast-forward
rejection.

T12. EVERY GREEN DISPATCH STALES THE BUILD THE NEXT ONE NEEDS. release-please
cuts a release on every `feat:`/`fix:` merge; a green dispatch merges exactly
such a commit; the plugin-currency gate then refuses the next dispatch because
the executing build predates the new release. Three refusals in one session, the
second caused by `bd-ib-mrqoy2.4`'s own merge.

Three details compound it. The gate's stated remedy `claude plugin update` FAILS
with "not installed at scope user" — these plugins are PROJECT-scoped, so the
working command is `just ensure-plugins` inside the target repo. The install
record is PER-PROJECTPATH, so updating one repo leaves every other repo stale
(measured: updating the orchestrator left `livespec-overseer` on the old build).
And the dispatch names an absolute cache path, so the stale path is baked into
whatever a handoff recorded. Re-resolve `installPath` from
`installed_plugins.json` after every update. Filed as `bd-ib-eqxt`.

T13. I MISDIAGNOSED A TOOLING GUARD, AND THE WORKAROUND CORRUPTED MY EVIDENCE.
The `github_rate_limit_guard` hook kept denying commands. I concluded
`--paginate` was the trigger and dropped it. WRONG on both counts: `--paginate`
is allowed, and the real trigger is `select` — a jq builtin sitting in the
guard's `for|while|until|select` alternation, so most `gh ... --jq` filters are
refused. My first isolation attempt "proved" the wrong answer because the `echo`
describing the test contained the words "select" and "for", poisoning its own
control. Keep the trigger vocabulary OUT of any command that tests for it.

The cost was not friction. Dropping `--paginate` produced a SILENTLY TRUNCATED
read: 30 of a run's 96 jobs, tallying ALL SUCCESS, beside a run whose conclusion
was `failure`. The failing jobs were on page 2. A non-empty, internally
consistent, correct-as-far-as-it-goes answer to a question I had not asked.
Always pass an explicit `per_page` and reconcile the row count against
`total_count` — that reconciliation is the control. Recorded as `livespec-gfjh`;
the guard evidence went onto `livespec-driver-claude-61k` rather than a duplicate.

T14. A CORRECT GATE CAN BE ROUTED AROUND WITHOUT BEING WEAKENED, AND I NEARLY
MISSED THE ROUTE. `check-master-ci-green` sits in the COMMIT path, so while a
repo's master CI is red NOTHING commits there — not in a Fabro sandbox, not on a
host session. Two consecutive dispatches of `bd-ib-mrqoy2.6` completed their work
in-sandbox and died at the Green amend, roughly 30 minutes of factory time
producing nothing publishable. Both agents refused to bypass the hook, which is
correct and must never be "fixed" at the agent.

The route was in `livespec-dev-tooling-8o8e.22` all along: **the gate binds any
commit STAGING `.py` and any push CARRYING `.py`; a zero-`.py` changeset routes
to `check-pre-commit-doc-only`, whose targets do not include it.** Splitting
`.6`'s prose half from its `.py` half landed the prose immediately, red master
and all, with no gate change and no new ledger artifact. The worker verified the
claim in-repo before relying on it and measured the staged `.py` count at 0 with
a positive control showing the same counter reporting 7 for `.md`.

Two things worth carrying. The item's `.py` scope existed only because I had
transferred two `.py` lines into it hours earlier — I created the blockage I then
had to route around. And I was one step from proposing the FORBIDDEN repair:
`export-telemetry` reddening master is DELIBERATE ("a broken pipeline can't die
silently"), so pointing the check at the `ci-green` context would restore exactly
the silent death that job prevents. Checking for an existing item before filing
is what stopped me; the existing analysis was better than mine.

T15. MY POSITIVE CONTROL WAS A NO-OP AND REPORTED SUCCESS ON BOTH ARMS. To prove
my replace-target harness could report a MISS, I mutated a target with
`.replace("path", "pathway")`. The target contained no "path", so the mutation
changed nothing and both arms scored a hit — a control that could not fail,
sitting inside a verification I was about to certify 24/24 on.

Fixed by pairing every target with a mutation that PROVABLY changes it (append a
sentinel; assert `mutant != real`), then asserting 0 mutant matches against 24
real ones. This is protocol correction C5 — put the control on the READER —
applied to my own instrument rather than someone else's, and I had already told
the worker to do exactly this in the brief I wrote an hour earlier. A rule you
enforce on others and skip yourself is not a rule.

The same family bit twice more the same day: a case-insensitive `plan.thread`
grep also matches the vendored identifier `PlanThreadOutput`, conflating a banned
prose form with an API that must be PRESERVED; and a note written to the ledger
with backticks in it was silently holed by shell command substitution, leaving
"died at  fetching dunamai" with the step name gone and the write returning
success. Quote ledger bodies from a FILE, and separate prose-form from
identifier-form greps.

T16. AN INSTRUCTION WRITTEN TO PREVENT A FALSE ATTESTATION BECAME ONE. The
proposal carried "the ratification record MUST therefore read
`reviewer_model: opus`, never `fable`" — true when written, because the only
reviews then in existence were Opus. Commissioning a Fable round 4 EXPIRED it:
followed literally it now instructs the ratifier to attest that the review the
accept gates on was Opus, which is correction T1's defect pointing the other way.

I caused it by commissioning the round, and the reviewer caught it. The rule that
replaces it is per-round: the record names the model that performed EACH review
round, and no blanket value is honest for a mixed history.

The general form is worth more than the instance: **a claim about the review
history is clause-lockstep like any other count, and must be re-derived at accept
time.** The classes this plan already tracked — claims that expire, enumerations
that rot — apply to the attestation prose itself, which is the last place anyone
thinks to look because it is the thing doing the guarding.

T17. "RESET THE STRANDED ITEM" IS RIGHT OR CATASTROPHIC DEPENDING ON ONE
QUESTION, AND THE STANDING REMEDY DOES NOT ASK IT. Both `bd-ib-mrqoy2.5` and
`.6` ended at `status=active assignee=fabro` with no live dispatcher — the
documented stranding shape, whose remedy is `bd update <id> -s ready -a ""`.

Applying it to `.5` would have been destructive: `.5` had PUBLISHED work, a real
PR whose head equalled the remote branch tip, so a reset invites a second sandbox
onto an existing branch — the non-fast-forward death of T11. Applying it to `.6`
was correct: `.6` published NOTHING, its commit lived only inside a container,
and `git ls-remote` confirmed no surviving branch with a positive control showing
12 heads exist.

**The test is "did anything reach the forge", not "did the dispatcher say
failed".** Both said `failed`. Read the forge, then decide.

T18. TWO OF THREE ROUND-4 BLOCKERS WERE INVISIBLE TO TARGET-MATCHING. A junction
defect has an individually-correct replace-target AND an individually-correct
replacement while the seam between them is wrong — an orphaned referent, a
purpose clause that no longer covers the duty grafted onto it. No amount of
verbatim-and-unique target checking sees it. Round 2 found half its blockers the
same way, and round 4 found two of three.

So a review of a whole-file or many-target payload owes THREE questions, not the
two T6 records: what vanished that should have stayed, what stayed that should
have vanished, and **what is now adjacent that was never adjacent before.** Only
simulating the applied result answers the third. Any round that reports clean
without simulating has not checked the class that produced most of this
proposal's findings.
