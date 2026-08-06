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

Written at session wrap 2026-08-06T00:55Z. These are pointers to things that
existed then, NOT status. Re-measure each with the commands above before acting
on it; this plan has already been bitten twice by state that moved underneath a
written-down claim.

**The attestation hardening LANDED and was VERIFIED — no action needed.**
`livespec-pw55` closed green: PR #2077, merge `235d094b`, ledger
`resolution:completed`, confirmed an ancestor of `origin/master`. It added
`_revise_ratification_timing.py` with `DEFAULT_MIN_REVIEW_AGE_SECONDS = 1`, a
`created_at` floor, and a configurable
`spec_governance.ratification_min_review_age_seconds`.

Verified as more than "green": the parametrized
`test_validate_ratification_reviews_rejects_out_of_order_review_timestamps`
rejects all three bad shapes against `created_at 12:30:00` / `revised_at
12:37:25` — a `reviewed_at` preceding `created_at`, one EQUAL to `revised_at`
(the exact `v198` shape), and one post-dating it — while
`test_validate_ratification_reviews_accepts_v197_shaped_review_gap` keeps a
healthy gap passing, so the check discriminates rather than rejecting
everything. It also fails closed when the proposal cannot be read. 29 tests
pass.

A caveat worth carrying: `ratification_timestamp_error` returns `None` when
`revised_at` is `None`, so ordering validation is skipped on that path. It is
covered by a deliberate test and is correct for non-mutating calls, but if a
future caller ever reaches ratification with `revised_at` unset, the gate goes
quiet rather than failing closed. Worth a look if the surface changes.

**Everything else this seat held is discharged.** The full obligation record,
including discharge evidence and every finding, is the supervisor marker the
cold-open boot block already reads. Read it — it is the detail this section
deliberately does not duplicate.

**Owned elsewhere, not this seat's to drive:** grooming `bd-ib-mrqoy2`
(repository `livespec-orchestrator-beads-fabro`) and `overseer-pfpfty`
(repository `livespec-overseer`) — maintainer-owned cuts in their own
repositories, which this binder forbids decomposing from here;
`livespec-zsn2xh.5`, gated on that orchestrator rewrite; and five rename-only
sweeps now unblocked in their own repositories.

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
