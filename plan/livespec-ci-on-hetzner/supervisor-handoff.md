# Supervisor Handoff - livespec-ci-on-hetzner

## Resume state — written at session wrap-up 2026-08-06T02:15Z

You are the SUPERVISOR of the `livespec-ci-on-hetzner` thread. This section is the
only thing carried across the restart, so it is deliberately short and points at the
live sources rather than restating them. **Every status claim below is a reading with
a timestamp — re-measure before acting on any of it.** That is not boilerplate: this
thread's Corrections C2 and C5 are both instances of acting on a reading that had
already expired, one of them within two minutes. The predecessor's own marker recorded
a PR as OPEN roughly ELEVEN SECONDS after it had merged.

**Run the HALT-first preconditions and the Generator-provenance check below FIRST.**
Then read, in this order: `.ai/supervisor-protocol.md` (the shared layer — this binder
is incomplete without it), `plan/livespec-ci-on-hetzner/handoff.md` (the THREAD's own
record, much longer and the real status authority), and the supervisor marker at
`tmp/overseer/livespec-ci-on-hetzner/.supervisor-state`. The marker is gitignored but
survives on this host, and carries the full obligation record.

### Nothing of mine is in flight

At this wrap-up there is **no supervisor-owned PR, branch, or worktree outstanding**.
Five supervisor PRs landed this session — #2055, #2056, #2072, #2083, and the one
carrying this very section — and every worktree and branch behind them was reaped. If
you are reading this from the COMMITTED file rather than a working copy, the last of
them has by definition already landed.

That is still a claim with a timestamp, so verify rather than trust, and use a
FAIL-CAPABLE query — an empty listing and a broken listing look identical:

```sh
mise exec -- git -C /data/projects/livespec worktree list
mise exec -- git -C /data/projects/livespec branch --list 'master'   # positive control
```

**Eleven worktrees exist under `~/.worktrees/livespec/` and NONE is this thread's.**
The set CHANGES UNDER YOU — one appeared mid-session — so re-enumerate rather than
acting on any recorded list. Never touch, push, or reap another session's worktree or
branch. The primary checkout is SHARED: it moved under this supervisor twice, and a
peer lane cleared a dirty file of this thread's from it (correctly — it verified
byte-identity against `origin/master` BEFORE acting).

### Thread status — re-measure, do not inherit

Four slices CLOSED: `livespec-teasvm`, `livespec-uyfggr`, `livespec-hhx4gl`,
`livespec-dev-tooling-3otdg4`. **Every non-Hetzner slice is done.** The remaining
three — `livespec-3on57g`, `livespec-7wvyo7`, `livespec-q7sfu6` — are
`pending-approval` behind the homelab gate and CANNOT be started. Measured
2026-08-06T02:04Z: `hl-wkyeqg` and `hl-euzuhb` both still `pending-approval`,
`hl-xuu5j3` still `backlog`. That is a seventh consecutive reading with nothing moved.

**The gate's SHAPE changed even though its status did not, and that is the useful
part.** The host is no longer dark — it is up and bare metal — so the blocker is now
`hl-75f` (P1, `backlog`) plus those two ratifications plus thread 07 unstarted.
`hl-75f` is a real defect on `hetzner-prod`: its ESP was created at **512 GiB instead
of 1 GiB** because a byte-suffixed partition end was consumed as SECTORS, leaving the
ZFS pool under half its intended size. It is measured on the live machine, not
inferred. Expect a DESTRUCTIVE REPARTITION to sit between here and a serving runner,
so do not read "the host is up" as "the gate is nearly open." All of it is
homelab-side; consume it, never act on it.

So the thread is **legitimately parked at an external gate, not idling**. Do not
manufacture a slice to look busy; a previous worker was explicitly commended for
refusing to. If you have context to spend, spend it on verification or on the open
items below, not on inventing thread work.

### Maintainer decisions already taken — do NOT re-ask any of these

Three were put to the maintainer 2026-08-05T22:45Z and answered:

- **`livespec` PR #1960** (stuck `livespec-runtime` pin) — REBASE AND REGENERATE.
  **Executed and merged** as `cead37ca`; the pin caught up three releases to v0.16.0.
  Closed out, listed only so nobody re-opens it as a question.
- **`livespec-driver-claude-mu5`** — KEEP AT P1. It already measures `backlog`/P1, so
  **no edit is owed**. Do not re-raise the priority.
- **`livespec-cpqi`** — FIX THE SKIP SHAPE FIRST, then choose the adopter check set.
  The template half of `livespec-dev-tooling-zi29` lands BEFORE any of the 59 canonical
  checks are wired into `ci.yml.jinja`.

**The standing disposition that came with them matters more than the three answers.**
The maintainer rebuked the ASKING on #1960, not the analysis: it was a mechanical
unblock the supervisor was already authorized to perform, and the shared protocol says
so verbatim — *"If the SUPERVISOR can perform the unblock, PERFORM IT."* **Act on
mechanical unblocks. Reserve escalation for genuine product calls and irreversible
actions.**

### Open items this thread opened or touched, and who owns them

- `livespec-dev-tooling-y6e2` (P1) — the `check-shell-quality` CI job skips installing
  the worktree pack, so the gate inspects a justfile with the pack's recipes removed
  and verifies nothing. Owner: the maintainer. **Review date 2026-08-12** — at that
  date it gets re-justified or dropped, never silently carried.
- `livespec-dev-tooling-a9xp` (P1) — NEW this session. `pretooluse_background_guard`
  directs callers to `just gate-start` / `just gate-wait` and an `.ai/` file, none of
  which exist in the repos where it fires: 7 repos arm the hook, 6 have none of the
  named artifacts. This is the **third** guard prescribing an unavailable remedy,
  alongside `livespec-driver-claude-mu5` and `livespec-f3tf`. The cost is the TRAINING
  EFFECT, not the friction — every workaround hides text from a safety guard.
- `livespec-dev-tooling-z68f` (P2) — `just bootstrap` self-dirties `.livespec.jsonc`.
  Acceptance clause 1 is DISCHARGED: **8 of 13 governed repos affected**, full
  enumeration in the item's notes. The fix choice — commit the key everywhere vs stop
  writing it — is deliberately left as a design call.
- `livespec-dev-tooling-irtt` (P0) — **STOOD DOWN, NOT MINE.** The maintainer ruled the
  `pure_trees` track owns it and considers it handled. Do not re-open that decision on
  the strength of a red master you happen to observe.
- Also open elsewhere and merely cross-referenced, not owned here:
  `livespec-dev-tooling-uw3h` (P2), `bd-ib-te4h` (P2, in
  `livespec-orchestrator-beads-fabro`), `livespec-f3tf` (P2),
  `livespec-dev-tooling-0j3i` (P0, owns pin-currency escalation).

### The routing rule that is easy to get wrong

**Homelab-side asks go to the homelab thread-12 coordinator, never to the maintainer
directly.** Two agents asking the same question makes him pay twice and can leave him
adjudicating a disagreement between his own agents. This does NOT suppress
livespec-side valves — those are still yours to raise.

### The worker

tmux session `livespec-ci-on-hetzner` was alive and idle at wrap-up with its track
complete apart from the external gate. **It was cleared and RESTARTED mid-session**
(its `pane_pid` changed), which destroyed its context minutes after it had answered a
question — the answer survived only because it had also been written to
`worker-status.log`. Two things follow. Write briefs and answers to files under
`runtime_dir`, never only into a pane. And a restart leaves a STAGED, UNSENT bootstrap
prompt in the composer: idle plus queued input is STUCK, not idle, so submit it.

Verify the worker with the preconditions below rather than assuming it is there. If
its pane looks idle, check for a stale limit modal before believing it —
shared-protocol C4.

## Shared Protocol

Read `.ai/supervisor-protocol.md` before driving. Validate this binder together
with that shared layer; neither layer is complete by itself.

Regeneration MUST preserve both Corrections sections byte-for-byte:

- `.ai/supervisor-protocol.md` `## Corrections` for role-level corrections.
- This binder's `## Corrections` for thread-specific corrections.

Preserve spelling, punctuation, code formatting, blank lines, and ordering
exactly; do not normalize Markdown or code spans. Live thread status is not in
this binder. Re-measure it from the ledger, the thread's planning records, forge
artifacts, and the supervisor marker.

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
truncation notice is mandatory whenever anything is hidden: a constant cap rots
as an append-only marker grows, a head-only cut can separate a live claim from
its later retraction, and Corrections land at the end.

## Bindings

Resolve and report these startup bindings before driving. They contain no live
status, next action, or date-gated behavior.

| Binding | Value |
|---|---|
| `repo_primary` | `/data/projects/livespec` |
| `thread_dir` | `/data/projects/livespec/plan/livespec-ci-on-hetzner` |
| `topic` | `livespec-ci-on-hetzner` |
| `worker_session` | `livespec-ci-on-hetzner` |
| `supervisor_session` | `livespec-ci-on-hetzner-supervisor` |
| `WORKER_TARGET` | `'=livespec-ci-on-hetzner:'` |
| `SUPERVISOR_TARGET` | `'=livespec-ci-on-hetzner-supervisor:'` |
| `runtime_dir` | `/data/projects/livespec/tmp/overseer/livespec-ci-on-hetzner/` |
| `supervisor_marker` | `/data/projects/livespec/tmp/overseer/livespec-ci-on-hetzner/.supervisor-state` |
| `wait_channel` | `/data/projects/livespec/tmp/overseer/livespec-ci-on-hetzner/worker-status.log` |
| `ledger_anchor` | `livespec-h22nve` |

The topic is not repo-qualified. The session-name derivation rule qualifies a
name only on a genuine cross-repository topic collision, and `livespec-ci-on-hetzner`
occurs in exactly one repository. The nearby homelab threads
`05-hetzner-fleet-member` and `12-hetzner-ci-critical-path-overseer` are
different topics, not collisions with this one.

Placeholder classes declared by this binder:

- Concretely bound: `repo_primary`, `topic`, `worker_session`,
  `supervisor_session`, and `ledger_anchor`.
- Composed bindings resolved transitively to the fixed-point values shown in the
  table: `thread_dir`, `WORKER_TARGET`, `SUPERVISOR_TARGET`, `runtime_dir`,
  `supervisor_marker`, and `wait_channel`.
- Runtime slots intentionally left unsubstituted for the supervisor to fill at
  use time: `<condition-command>`, `<short-slug>`, and `<branch>`.
- Illustrative placeholders appear only in prose discussing a form, never in a
  fenced command. In the shared protocol, `<repo-primary>` and `<topic>` describe
  reusable path shapes, including `plan/<topic>/supervisor-handoff.md`. In this
  binder's Thread-specific Valves, `impl:<id>` describes the shape of an
  orchestrator action id and `<unit>` describes a systemd unit-file name. None of
  these are shell substitutions.

After resolving concrete and composed bindings to the values above, every fenced
shell command contains no generation-time placeholder. The three named runtime
slots are deliberate templates and are not generation errors.

## Generator provenance

This charter was produced by the generator recorded below. The prose digest is
the identity; the plugin, cache ref, and version are human-readable companions.
Run the check before driving so a refreshed cache cannot silently leave this
charter on an older generator. This invocation read the Claude plugin cache, so
the self-check uses that same runtime's cache root.

```sh
generator_plugin='livespec-overseer'
generator_ref='3fb2c257cdf1'
generator_version='0.27.2'
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
existing cache root that no longer contains the recorded ref means the generator
was replaced and is a HALT. These absence cases are intentionally different.

The recorded ref is the ref INSTALLED for this project at generation time, which
is not always the ref the skill binding was invoked from. This charter was
generated in a session whose binding still pointed at the superseded ref
`373924fc5da9` while `claude plugin update` had already installed `3fb2c257cdf1`
for `/data/projects/livespec`. Recording the invoking ref would have armed a HALT
that fires the moment the superseded ref is pruned, reporting a replaced
generator where the prose never changed. The prose in both refs is byte-identical
at `eaebe06065b3efa0053d6ea5932d52c0`, which is why the digest — not the ref and
not the version — is the identity. The version is a companion for the same
reason: this same prose digest has shipped under several versions.

## Thread-specific Valves

- The ledger anchor is epic `livespec-h22nve` in the `livespec` tenant. The
  thread's own records are `plan/livespec-ci-on-hetzner/handoff.md` and
  `plan/livespec-ci-on-hetzner/approach.md`; they carry coordination and decision
  boundaries, not a parallel work queue. Read status from the ledger.
- **Run every `bd` call from `/data/projects/livespec`.** The fleet credential
  wrapper self-heals its tenant secret from the repository it is standing in, so
  `with-livespec-env.sh -- bd list` issued from the `homelab` tree fails with
  `Error 1045 (28000): Access denied for user 'homelab'`. A homelab-side session
  recorded this whole track as UNMEASURABLE on the strength of that error. An
  access-denied raised from the wrong tree is not a measurement of anything.
- **The epic is groomed. Do not groom it again.** `livespec-h22nve` is held at
  `active` rather than `backlog` deliberately, because `groom` refuses any target
  not at exactly `backlog` and that refusal is what stops a later session
  re-decomposing the epic into duplicate slices. Do not return it to `backlog`.
- **Expect to reverse a false clear on the anchor.** `groom` closes an epic as
  "regroomed out" as its normal final step, which for a plan-thread anchor would
  archive this thread while none of the completion evidence exists. It was
  reversed once already in this repository, and twice in `homelab` (`hl-bfwpqb`
  false-clearing thread 05, `hl-6uldtn` false-clearing thread 07). The structural
  cause is that the ledger refuses task-blocks-epic edges, so replacement slices
  cannot inherit the block and the mitigation has to be prose. Re-apply the
  correction if anything closes the anchor before the completion evidence exists.
- **Only `livespec-dev-tooling-3otdg4` is factory-dispatchable.** Its acceptance
  is local and credential-free and it touches no workflow file, so it routes
  through the orchestrator as `impl:<id>`. Every other livespec slice is
  maintainer-side, because the factory dispatch credential deliberately withholds
  the `workflows` grant and a dispatched agent therefore cannot push a branch
  touching `.github/workflows/`. Drive those in-session through the worktree → PR
  → merge → cleanup protocol. That slice lives in the `livespec-dev-tooling`
  tenant, not this one.
- **Never `bd create --force` for a cross-repo slice.** The groom minted the
  dev-tooling slice with this repository's prefix as `livespec-qheazr`; the target
  tenant refused the foreign prefix, and it was refiled under a native id with the
  referring slice rewritten to match. Forcing would plant a foreign-prefix id in a
  sibling tenant permanently. The orchestrator defect is `bd-ib-a8zi` in
  `livespec-orchestrator-beads-fabro`.
- **Hosted GitHub Actions minutes are paid and scarce.** Exhaust local controls
  before pushing, let one pushed candidate carry all locally proven work, and
  never rerun unchanged code merely to see. The live required-job and fallback
  exercises are factory-ineligible external-state verification and are the
  expensive ones; budget for them.
- **`.ai/ci-gate-discipline.md` is load-bearing for every remaining slice.** Never
  add a lever, env var, flag, or carve-out that lets a commit, push, merge, or
  dispatch proceed while a CI-green gate reports red, and never demote such a gate
  to a warning. This is the thread-specific face of the shared protocol's "never
  REMOVE, WEAKEN, or SKIP an existing check".
- **`livespec-hhx4gl` mutates the SHARED FACTORY HOST, whose blast radius is
  fleet-wide.** That host runs Fabro, the Dispatcher, and Dolt — and Dolt backs
  the beads ledger every repository in this fleet reads, including every homelab
  thread. Nothing under `/usr/local/lib/ci-runner/` is in git, so back the tree up
  before deleting: the archive IS the rollback path. The item's own acceptance
  already requires a negative control (`systemctl preset-all --dry-run` showing
  nothing that would re-enable a `<unit>` of the removed set) proving the removal
  is durable rather than merely stopped, and an explicit confirmation that Fabro,
  Dolt on `127.0.0.1:3307`, and the Dispatcher are healthy and untouched. That
  confirmation is what distinguishes success from "the units are gone and
  something else quietly broke"; the removal is not done without it.
- **`gate-runner` is deliberately out of scope and must stay there.** Whether the
  factory-host clause reaches the privileged `[self-hosted, livespec-orchestrator]`
  tier is genuinely unresolved: the Scope carve-out names the Execution-identity,
  Credential-separation and Event-routing clauses, and the factory-host clause
  sits in a different section. Refer that reading to
  `livespec-orchestrator-beads-fabro`'s own specification rather than deciding it
  here or widening `livespec-hhx4gl`.
- **The Hetzner-gated slices cannot complete on livespec evidence alone.**
  `livespec-3on57g`, `livespec-7wvyo7` and `livespec-q7sfu6` all need a
  self-hosted runner on `hetzner-prod`, which homelab thread 07 (`hl-xuu5j3`) owns
  downstream of fleet admission (`hl-euzuhb`) and machine provisioning
  (`hl-wkyeqg`). A healthy box is not an admitted one. beads refuses cross-tenant
  edges for these, so the precondition is prose-only and blocks nothing
  mechanically — re-measure it rather than trusting an edge to hold it.
- **Hetzner/NixOS service realization belongs to homelab thread 07, exclusively.**
  Supply v192 properties to that owner and consume its measured outputs. Never
  create a competing homelab plan, contact the host from this thread, or file a
  duplicate livespec implementation item for host modules or services. Do not
  hard-code labels, service names, or a fallback mechanism before measuring the
  host owner's accepted interface.
- **A homelab freeze does not gate the livespec repository.** The freeze pins
  `thewoolleyman/homelab` main at an anchor so that a re-install stays cheap;
  landing `livespec` PRs does not move `homelab` main. Treat "held because of the
  Hetzner freeze" as a misread unless the specific artifact being held is a
  `homelab` ref.
- **A cross-track directive without an expiry is a defect.** The homelab-side
  coordinator's hold on `livespec-hhx4gl` carried the explicit condition "until
  the wipe window closes" and was released the moment that condition was met.
  When accepting any future hold from a peer track, record its stated condition
  and its expiry in the supervisor marker as an obligation with a `timeout`; a
  hold whose condition nobody is re-measuring silently becomes a permanent queue
  item.
- **Do not revive the archived shared-factory resident listener pool.** A
  persistent registration is nonconforming even if it runs only one job at a time.
- **Route every homelab-side ask through the homelab thread-12 coordinator, never
  to the maintainer directly.** That thread coordinates the homelab critical path
  and holds the maintainer escalations for it. A livespec-side thread that also
  asks makes the maintainer pay for the same question twice, and the two asks can
  carry different framings — so instead of getting a decision he ends up
  adjudicating a disagreement between two of his own agents. If something
  homelab-side appears to block this thread, send it to that coordinator, which
  will either answer it or escalate it once with the reasoning attached. This is a
  routing rule, not a permission rule: it does not stop this thread raising
  livespec-side valves to the maintainer.
- Write every repository name in full in maintainer-facing output. This thread
  cites `livespec-orchestrator-beads-fabro` and `livespec-dev-tooling` constantly,
  and the bare suffix `beads-fabro` is ambiguous with
  `livespec-console-beads-fabro`.

## HALT-first preconditions

Expected worker session: `livespec-ci-on-hetzner`.

Expected supervisor session: `livespec-ci-on-hetzner-supervisor`.

Exact target repository: `/data/projects/livespec`.

Run these in order before doing anything else. Stop on the first failure and act
on its labelled `REMEDY:`.

1. The supervised session exists:

```bash
WORKER_TARGET='=livespec-ci-on-hetzner:'
tmux has-session -t "$WORKER_TARGET" \
  || { echo "HALT: expected worker session 'livespec-ci-on-hetzner'"; echo "REMEDY: ask the maintainer whether to start that worker session"; exit 1; }
```

2. The supervised session is a live agent session:

```bash
WORKER_TARGET='=livespec-ci-on-hetzner:'
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
[ -n "$pane_pid" ] \
  || { echo "HALT: empty pane_pid for 'livespec-ci-on-hetzner'"; echo "REMEDY: re-check the exact worker target and stop if it still resolves empty"; exit 1; }
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
WORKER_TARGET='=livespec-ci-on-hetzner:'
SUPERVISOR_TARGET='=livespec-ci-on-hetzner-supervisor:'
tmux has-session -t "$SUPERVISOR_TARGET" \
  || { echo "HALT: expected supervisor session 'livespec-ci-on-hetzner-supervisor'"; echo "REMEDY: switch to the correct supervisor session or ask the maintainer to bootstrap it"; exit 1; }
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
supervisor_pane_pid=$(tmux display-message -p -t "$SUPERVISOR_TARGET" '#{pane_pid}')
[ -n "$supervisor_pane_pid" ] \
  || { echo "HALT: empty pane_pid for 'livespec-ci-on-hetzner-supervisor'"; echo "REMEDY: re-check the exact supervisor target and stop if it still resolves empty"; exit 1; }
[ "$supervisor_pane_pid" != "$pane_pid" ] \
  || { echo "HALT: supervisor and worker resolve to the SAME pane"; echo "REMEDY: re-check both exact targets — a prefix match puts both names on one pane, and the worker's agent then reads as the supervisor's"; exit 1; }
ps -o pid=,comm=,args= --ppid "$supervisor_pane_pid" --pid "$supervisor_pane_pid" -H
# PASS only if a live `claude` or `codex` process appears in that tree.
# A lone shell (zsh/bash) with no agent child is a HALT.
# REMEDY: if no live agent appears, ask the maintainer to start the agent in that session.
```

Both pids are resolved inside this block rather than inherited from the previous
check, so it is self-contained and cannot pass on an unset variable.

4. The plan thread exists inside the absolute target repository:

```bash
test -d "/data/projects/livespec/plan/livespec-ci-on-hetzner" \
  || { echo "HALT: missing plan thread /data/projects/livespec/plan/livespec-ci-on-hetzner"; echo "REMEDY: create or choose the correct plan topic before supervising"; exit 1; }
```

5. The worker pane's resolved cwd is inside the target repository:

```bash
WORKER_TARGET='=livespec-ci-on-hetzner:'
pane_cwd=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_current_path}')
[ -n "$pane_cwd" ] \
  || { echo "HALT: empty pane_current_path for 'livespec-ci-on-hetzner'"; echo "REMEDY: re-check the exact worker target and stop if it still resolves empty"; exit 1; }
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
ledger_anchor='livespec-h22nve'
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

The `cd` is not cosmetic. This wrapper resolves its tenant from the working
directory, so the same call from a sibling checkout fails access-denied against
that sibling's tenant name.

The epic's slices carry the per-increment status. Enumerate them from the ledger
rather than from this binder or from the thread's planning records, which record
the cut rather than live status.

Capture a status before filtering it, because a pipeline reports only its last
command:

```sh
WORKER_TARGET='=livespec-ci-on-hetzner:'
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
tmux_rc=$?
[ "$tmux_rc" -eq 0 ] \
  || { echo "HALT: tmux pane lookup failed for 'livespec-ci-on-hetzner'"; echo "REMEDY: re-check the exact target before filtering its output"; exit 1; }
printf '%s\n' "$pane_pid" | head -1
```

A pipeline whose last command deliberately owns the verdict is fine, for example
`tmux list-sessions -F '#{session_name}' | grep -Fqx 'livespec-ci-on-hetzner'`.

Inspect read-only:

```sh
tmux capture-pane -p -t '=livespec-ci-on-hetzner:' -S -40
```

`-S -40` starts 40 lines back in history and then includes the entire visible
pane. It is not "the last 40 lines." Do not pipe it to the invalid placeholder
form `tail -N`.

Send a short instruction as text, verify that it landed, then send Enter in a
separate call. Verify by comparing the COMPOSER REGION across two spaced reads —
never a `tail -N` of the pane:

```sh
WORKER_TARGET='=livespec-ci-on-hetzner:'
composer() {
  # The prompt marker is U+276F followed by a NON-BREAKING SPACE (U+00A0), so a
  # pattern of '^❯ ' with an ordinary space silently matches NOTHING and the
  # function returns empty. Match the marker alone.
  #
  # Anchor on the LAST marker line, not the first. Once any instruction has been
  # submitted, the pane holds the ECHOED prompt above the live composer, and both
  # begin with the marker. A first-match scan returns the echo — settled text that
  # is byte-identical across any two reads. See C6.
  tmux capture-pane -p -t "$WORKER_TARGET" | awk '
    { line[NR] = $0; if ($0 ~ /^❯/) last = NR }
    END {
      if (last == 0) exit
      for (i = last; i <= NR; i++) {
        if (i > last && line[i] ~ /^─+/) exit
        print line[i]
      }
    }'
}
tmux send-keys -t "$WORKER_TARGET" -- '<condition-command>'
a=$(composer); sleep 3; b=$(composer)
[ -n "$a" ] \
  || { echo "HALT: composer extraction returned EMPTY — the extractor is broken, not the composer"; echo "REMEDY: print the pane through 'cat -A' and re-derive the marker bytes before trusting any comparison"; exit 1; }
[ "$a" = "$b" ] \
  || { echo "HALT: composer still changing — text is mid-delivery"; echo "REMEDY: re-read until two spaced reads match, then send Enter"; exit 1; }
# STABILITY IS NOT IDENTITY. Assert the composer actually holds what you sent,
# against a distinctive fragment of it, before pressing Enter.
printf '%s\n' "$a"
case "$a" in
  *'<a distinctive fragment of the text you just sent>'*) : ;;
  *) echo "HALT: composer does NOT contain the text just sent"; echo "REMEDY: do not press Enter — re-read the pane, and suspect the extractor before suspecting the send"; exit 1 ;;
esac
tmux send-keys -t "$WORKER_TARGET" Enter             # only after verifying
```

A `tail -N` comparison CANNOT stabilize while the worker is busy. A working pane
renders a spinner whose elapsed timer ticks every second, so the tail differs
between any two reads no matter what the composer is doing, and the check reports
"not stable" forever while the text has in fact been sitting there complete. That
is a FALSE NEGATIVE, and it is the mirror of the false positive C2 warns about:
one blocks a delivered instruction, the other blesses an undelivered one. Measured
live in this thread — the tail comparison failed repeatedly on text that was
already complete and unchanging.

The emptiness assertion is not ceremony. The first version of this extractor used
`'^❯ '` with an ordinary space and returned zero bytes on every read; two empty
strings compare EQUAL, so without the `-n` test the check would have reported
STABLE on a composer it had never actually read, and pressed Enter on that basis.
An extractor that matches nothing is indistinguishable from an empty composer.
Prove the extractor finds something before trusting what it says about change.

It is NOT sufficient, though, and C6 is the case it misses. The `-n` test and the
stability test together still pass when the extractor matches the WRONG region —
a stale echoed prompt is non-empty AND perfectly stable. Non-empty, unchanging,
and wrong is the hardest of the three states to see, because both guards report
health. Only the content assertion above catches it.

Prefer a file reference over a paste for anything longer. Write the brief under
`runtime_dir` and send a one-line instruction naming that path; a one-line
reference is delivered atomically, verifies in one read, and leaves a durable
copy that survives a composer reset.

Idle plus queued input means stuck, not idle. Never name a variable `TMUX`, never
run `tmux kill-server` on the maintainer's socket, and never kill the acting
overseer daemon in tmux `livespec-overseer:1.1`.

## Never end a turn without an armed re-entry

Arm the wait channel and the pane watcher before ending any turn with the worker
in flight:

```sh
wait_channel=/data/projects/livespec/tmp/overseer/livespec-ci-on-hetzner/worker-status.log
mkdir -p "$(dirname "$wait_channel")"
: > "$wait_channel"
# Tell the worker: append one line to "$wait_channel" at every milestone.

WORKER_TARGET='=livespec-ci-on-hetzner:'
prev="__OVERSEER_NO_CAPTURE_YET__"; stable=0
for i in $(seq 1 180); do                    # ~60 min ceiling
  sleep 20
  pane=$(tmux capture-pane -p -t "$WORKER_TARGET")   # visible only
  [ -z "$pane" ] && { echo "WAKE: pane unreadable — session may be gone"; exit 0; } # before the diff
  if printf '%s\n' "$pane" | tail -8 \
       | grep -qE '^[[:space:]]*Enter to (select|confirm)[[:space:]]*(·.*)?$'; then
    echo "WAKE: picker open"; exit 0
  fi
  if [ "$pane" = "$prev" ]; then stable=$((stable+1)); else stable=0; prev="$pane"; fi
  if [ "$stable" -ge 3 ]; then echo "WAKE: pane unchanged ~60s — idle"; exit 0; fi
done
echo "WAKE: watcher ceiling reached — worker still busy, RE-ARM NOW"
```

Detect busy by pane change rather than by a status string: a working pane renders
a spinner whose timer ticks every second, so "unchanged across three 20s polls"
separates busy from idle without depending on TUI wording. The picker test stays a
string test but is scoped to the last visible lines and anchored at both ends,
because a substring scan matches prose that merely quotes `Enter to select` and a
start-only anchor can match a wrapped continuation line.

Watcher expiry is itself a wake and says `RE-ARM NOW`. Do not replace it with an
echo of an intention to check later.

This thread's non-pane obligations are the ones that need a condition watcher
rather than the pane watcher: a livespec PR's merge state, a dispatched
`impl:<id>` run in the `livespec-dev-tooling` tenant, and the homelab-side
admission outcomes this thread consumes but does not own. For a PR, read `state`
for `MERGED` or `CLOSED` before any derived field such as `mergeStateStatus`, and
wake and report on any unrecognized value rather than treating it as "keep
waiting."

## Corrections

Thread-specific corrections to this supervisor's own behavior belong here.
Regeneration must preserve this section byte-for-byte, including spelling,
punctuation, code formatting, blank lines, and ordering.

C1. I tried to answer the worker's open AskUserQuestion picker by sending my
answer as `send-keys` text, the way the shared protocol describes sending an
instruction. The picker CONSUMED the keystrokes as navigation. Nothing appeared
in any composer, no free-text box opened, and a `capture-pane` taken afterwards
showed the picker completely unchanged with the cursor still on option 1. Had I
not read the pane back before pressing Enter, I would have believed a 400-word
brief had been delivered when not one character of it existed anywhere.

A tmux pane with a picker open is NOT a composer, and "send text, verify, send
Enter" silently means something different there. The sequence that works: verify
which option the cursor is on, press Enter to select THAT option, wait for the
composer to return, and only then send prose as a normal instruction. Selecting
an option and elaborating afterwards is two steps and cannot be collapsed.

The general rule this thread should carry: the verify step in "send, verify,
Enter" is not a formality to be skipped when the send looks routine. It is the
only thing standing between a supervisor and a confidently reported instruction
that was never delivered. This is the same defect class as an empty result read
as a finding — silence that looks like success.

C2. I read a PEER TRACK'S append-only status log and treated its newest line as
current state. The homelab thread-12 log's last word at `10:50:00Z` was that the
`hetzner-prod` closure-identity check needed the maintainer's MacBook operator
key. I verified the key constraint itself carefully — singleton `authorizedKey`
in the homelab configuration, this workstation's fingerprint — and every one of
those facts was true. Then I built a three-option `AskUserQuestion` on top of them
and put it to the maintainer.

The maintainer had ALREADY RUN the check, at approximately `10:52Z`. It PASSED:
`/run/current-system` and `/run/booted-system` both resolved to the declared
toplevel, hostid as declared, `zroot` ONLINE across both mirror members with no
errors. My reading expired roughly two minutes after I took it, and I spent a
maintainer interruption asking a question that already had an answer. Two of my
three options rested on the dead premise, and the third proposed as new a change
that was already in flight as a draft PR — a deliberately RESTRICTED key, forced
command and no pty, because an unrestricted key on this shared factory host would
hand every concurrent agent session an interactive shell on production.

READING A PEER'S LOG IS NOT ASKING THE PEER. An append-only log is evidence of
what a peer knew when it wrote, never of what is true when you read; the newest
line is the peer's oldest unretracted claim, not a live measurement. Where the
authoritative state lives with another actor, ask that actor. This is the same
defect the shared protocol names for ledgers and gates — filed status is a claim
with a timestamp — and I applied it diligently to the ledger and the forge in the
same session while failing to apply it to a peer's log, because a log READS like a
feed. My careful verification of the key constraint made it worse rather than
better: it made a stale conclusion feel measured.

Corollary, and it is the more expensive half: this thread does not own the homelab
escalation channel. See the Thread-specific Valve on routing homelab asks through
the homelab thread-12 coordinator. Even had my premise been live, that picker
should have gone to the coordinator rather than to the maintainer.

C3. I REPORTED AN EMPTY GREP AS A FINDING, IN THE SAME DOCUMENT WHERE I INSTRUCTED
THE WORKER TO PROVE A CHECK COULD FAIL BEFORE TRUSTING IT. Reviewing a newly filed
hazard item, I searched its description with a case-sensitive Python `'Acceptance'
in desc`, got `False`, and wrote to the worker that the item had "no acceptance
criteria anywhere ... I searched for the string and it is absent." The description
carried an all-caps `ACCEPTANCE:` section at line 19. The worker caught it and
told me so.

Only half my claim was true. The structured `acceptance_criteria` FIELD was
genuinely empty, and filling it was worth doing. But the evidence I gave for the
stronger half was a broken query, and I stated it with more confidence than
anything else in that brief — naming the search as though naming it made it sound.

The shared protocol already carries this rule under "An empty result is not a
finding. Run a positive control first." I QUOTED THAT PRINCIPLE TO THE WORKER AS
REQUIREMENT 3 OF THE SAME BRIEF, asking it to prove the replacement check could
fail on a synthetic unit before trusting it to pass. Then I ran an unproven query
and shipped its silence as fact. Knowing a rule well enough to teach it is not the
same as executing it, and the gap is invisible from the inside — the query FELT
like verification because I had run something.

Practical form for this thread: any grep, `find`, ledger query, or field read whose
NEGATIVE result you are about to report must first be shown returning a positive on
an instance you know exists. One extra line. Case sensitivity, a wrong field name,
a wrong tenant, or a pathspec matching nothing tracked all fail identically and all
look like clean absence.

Two corrections in one session now share a root, and the pairing is the real
lesson: in C2 I read a peer's log instead of asking the peer, and here I read my
own query's silence instead of testing the query. Both times the mechanism I
trusted was one I had never watched fail. The worker made the mirror-image error in
the same hour — a `jq` read of `acceptance` where the field is `acceptance_criteria`
— and self-corrected it. Adopt its sharpening of the sweep requirement as the
general rule: A ZERO-HIT SEARCH COUNTS ONLY IF THE SAME PATTERN IS SHOWN MATCHING A
KNOWN-PRESENT INSTANCE.

C4. I TRUNCATED MY OWN OUTPUT AT EXACTLY THE POINT THE ANSWER WOULD HAVE APPEARED,
and C3's rule does not catch it. Checking whether `livespec-driver-claude` declares
the keys the replay gate derives its prefixes from, I listed that repo's config keys
through `sort -u | head -20`. The list is ALPHABETICAL and the cut fell on `pinned`
— the very next entries are the `s…` keys I was looking for. My query was not empty;
it was AMPUTATED, and it returned a confident-looking twenty-line answer that simply
did not reach the region in question.

C3 guards a zero-hit result. This one had NINETEEN hits, so every positive-control
instinct C3 installs reports a healthy query. A truncated result is worse than an
empty one precisely because it LOOKS like data.

Two practical forms for this thread. When you pipe a listing through `head`, `tail`,
or a fixed line cap, either print the total count beside it or drop the cap — a
window without a denominator cannot be reasoned about. And when you are searching a
SORTED list for a specific key, never window it at all: grep for the key. I applied
a cap out of tidiness on output nobody was going to be overwhelmed by, and the
tidiness cost the answer.

This is the same family as the binder's own marker-read rule, which mandates a
truncation notice whenever anything is hidden. I wrote that rule into this charter
and then truncated my own console output without one.

C5. I CHOSE A "HOLD THIS PR" OPTION WITHOUT FIRST CHECKING WHETHER THE PR HAD
ALREADY MERGED. IT HAD. The worker surfaced `livespec-dev-tooling#1296` — an
archival that would false-clear two open defects — as a picker whose every option
assumed the PR was still open, and flagged that auto-merge was armed, so there was a
CLOCK. I reasoned carefully about reversibility, chose the hold, and wrote a brief
about giving holds an expiry. By the time the disable ran, `gh` answered
`Can't disable auto-merge for this pull request`: it had already merged.

The reasoning was sound and the premise was dead. That is C2's failure class
recurring in a form C2 does not name: C2 is about inheriting a PEER'S stale claim,
and this is about a decision whose OWN premise expires while you deliberate. A clock
that makes a decision urgent is the same clock that invalidates it, and the more
carefully you deliberate the likelier it expires — the diligence and the staleness
grow together.

The rule: WHEN AN OPTION SET IS PREMISED ON A RACE, RE-MEASURE THE RACE IMMEDIATELY
BEFORE ACTING, NOT WHEN THE OPTIONS WERE DRAFTED. One `gh pr view --json state` call
before selecting would have shown `MERGED` and turned a hold into a post-merge
record — which is exactly what the worker converted it to, correctly, on its own.

Salvage note, because the outcome was still good: the worker did NOT let the record
claim a hold existed. It posted a post-merge comment opening with "no hold is in
effect, and none was applied ... nobody should go looking for a block that does not
exist." A supervisor instruction that has become impossible must be reported as
impossible, never quietly approximated — and it discharged the substance anyway by
recording the debt on the merged PR.

C6. THE COMPOSER EXTRACTOR IN THIS CHARTER READ THE WRONG REGION OF THE PANE, AND
BOTH GUARDS AROUND IT REPORTED HEALTH. I sent a ~900-character instruction, ran the
verify block, and it reported 21 bytes. I compared two spaced reads, they matched, so
the stability gate passed and I pressed Enter on a 21-byte reading of a 900-character
instruction. It landed correctly — by luck, not by method. Had it not, I would have
submitted a fragment and reported a delivered brief.

The mechanism, reproduced deliberately afterwards rather than guessed at. The old
extractor scanned for the FIRST line beginning with the prompt marker. Once any
instruction has been submitted, the pane holds the ECHOED prompt above the live
composer and BOTH begin with that marker, so a first-match scan latches onto the
echo. Measured live against this worker's pane with the composer verifiably EMPTY:
the old extractor returned **1903 bytes** of the previously-submitted instruction;
the corrected last-match form returned **5 bytes**, which is the bare marker plus its
non-breaking space — an empty composer, correctly reported.

**WHY THE EXISTING GUARDS COULD NOT CATCH IT, which is the part worth carrying.**
This charter already installs two: a `-n` emptiness assertion and a two-read
stability comparison. A stale echoed prompt defeats BOTH BY BEING HEALTHY — it is
non-empty, so `-n` passes, and it is settled transcript that cannot change, so it is
the most stable thing in the pane. The existing prose says "an extractor that matches
nothing is indistinguishable from an empty composer." The gap is one step further
out: AN EXTRACTOR THAT MATCHES THE WRONG THING IS INDISTINGUISHABLE FROM A CORRECT
ONE, and it is worse, because emptiness at least looks suspicious while 1903 bytes of
plausible text looks like proof. This is C4's amputated-listing lesson arriving in a
new place — a result that is confidently wrong reads better than one that is
obviously broken.

The fix is in two parts and the second is the load-bearing one. Anchor on the LAST
marker line, so the live composer is what gets read. Then STOP TREATING STABILITY AS
IDENTITY: assert that the extracted text actually CONTAINS a distinctive fragment of
what was just sent. Stability answers "has delivery finished," never "is this my
text" — and only the second question is the one being asked before pressing Enter.

Two process notes. First, I printed only a BYTE COUNT rather than the content;
printing the content would have exposed this instantly, and the count is exactly the
kind of denominator-free window C4 warns against. Second, my initial check of whether
the generator re-mints this defect grepped the generator for the very term whose
absence I was asserting — a non-control, C3's error, committed while writing up an
extractor bug. Re-run properly, the generator is clean (675 lines, 63 `supervisor`
hits, zero composer prose), so this was authored into THIS binder and exactly one
file in the repository carries it. The blast radius claim is measured, not assumed.
