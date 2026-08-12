# Supervisor Handoff - spec-side-autonomy

## Resume state — written 2026-08-12T06:38Z at session wrap-up

READ THIS FIRST. It is the live state of the thread and it EXPIRES: re-measure
everything below before acting on it. Supplementary depth is in the supervisor
marker at
`/data/projects/livespec/tmp/overseer/spec-side-autonomy/.supervisor-state`
(gitignored, same host, read by the cold-open boot block). This section is
self-sufficient; the marker is extra, not required.

### START HERE — the thread's stated work is DONE. Nothing is in flight.

**Epic `livespec-jvdvx4` is FULLY CLOSED — 18 of 18 children.** Measured
2026-08-12T05:24Z with `--all`; the default listing hides closed items and would
misreport it. Do NOT re-drive any of it. Re-enumerate from the ledger rather
than citing this paragraph.

Nothing is dispatched, no agent of this thread is running, no worktree or branch
of this thread exists, and **no maintainer decision is pending**. Both primary
checkouts (`livespec`, `livespec-orchestrator-git-jsonl`) are clean on their
default branches. Six worktrees under `$HOME/.worktrees/livespec/` are all
FOREIGN — never touch or reap them, and never run the worktree reaper here.
Re-derive that list; it grew from four to six during one session.

The previous revision of this section opened by warning that the spec-PR merge
gate was SHIPPED AND BROKEN. **That is fixed, and the fix has been validated by a
real production ratification.** Nothing in that warning is live.

### What shipped, and the one piece of evidence that matters

| Piece | Evidence |
|---|---|
| `livespec-jvdvx4.13` (P1) — rename derivation + errexit crash | PR #2157, merge `f8c98ced` |
| **v202 ratified** — single-authority channel partition + the shared-CI-logic lane | PR #2195, merge `45de58f2` |
| `livespec-jvdvx4.9` — the lane implemented end to end | module `72967098`; CI command `28b2850e`; reusable workflow `97b9bddf`; template gate `15e52ca1` |
| `.10`, `.11`, `.12`, `livespec-0ybg`, `livespec-odkk`, `livespec-n0ka` | all CLOSED |

**The evidence that matters is not the ratification.** `livespec-jvdvx4.13`
shipped broken because a real ratifying pull request RENAMES a proposal into
`history/vNNN/proposed_changes/` and no probe had ever produced that shape. PR
#2195 — the v202 ratification itself — was a genuine one, and all three
diagnostic legs were read IN ORDER: run `31550839305` CONCLUDED SUCCESS; the
policy step EMITTED ITS OWN OUTPUT; and only then `autoMergeRequest: None`.

**That ordering is the thread's hardest-won rule. A crashed step and a
manual-policy step both leave auto-merge unset.** `.13` shipped broken precisely
because nobody checked which one they had. Never read an absent `auto_merge` as a
pass on its own.

### Standing operational facts — these do not expire, but verify before leaning

- **Every spec-touching PR in `livespec` needs a MANUAL merge.** Core has never
  declared `spec_governance.spec_pr_merge`, so it inherits the safe `manual`
  default. Do not wait for auto-merge on one; do not read its absence as a fault.
- **A proposal-filing PR auto-merges BEFORE review, by design.**
  `non-functional-requirements.md` exempts a PR that adds under
  `proposed_changes/` but nothing under `history/*/proposed_changes/`. So filing
  and reviewing are NOT sequential gates on one PR — the filing lands unreviewed
  and the review gates RATIFICATION. Plan on a follow-up correction PR.
- **The `.jinja` template pins are outside pin automation.** Five pins are
  correct today and will NOT be bumped. That is `livespec-dev-tooling-ep8n`.

### WHAT REMAINS — none of it this thread's to finish alone

| Item | Tenant | State |
|---|---|---|
| `livespec-dev-tooling-ep8n` | `livespec-dev-tooling` | **HANDED OFF** to whoever grooms `livespec-dev-tooling`, by maintainer decision 2026-08-12; listed here for continuity only and NOT this thread's to advance. Pin autodiscovery misses `.jinja` template pins on BOTH directory and suffix. Shape decided (generic scanner extension). The recorded reason it is blocked, kept so the receiving groomer need not re-derive it: it needs a ratified amendment in THAT repo, because its `contracts.md` §"Pin autodiscovery rules" names `.github/workflows/*.yml`/`*.yaml`, and a `.jinja` renders a workflow rather than being one. |
| `livespec-5qu1` | `livespec` | **Direction chosen by the maintainer 2026-08-12 and the template change LANDED** (PR #2214, merge `88842637`): the copier template mints with `@v3` + `app-id:`, which is auth-neutral for both consumers because both already carry `app-id:`. `app-id` and `client-id` are NOT interchangeable, and `app-id` is deprecated-but-accepted at `@v3` — that warning is carried deliberately. The `client-id:` migration is decoupled, not cancelled. **Still OPEN on ONE leg: the LIVE auto-merge exercise**, which no consumer pull request open today can serve. |
| `livespec-jvz8` | `livespec` | Spec ratifications auto-merge UNGATED in `livespec-dev-tooling` and `livespec-runtime`. PRE-EXISTING, not fix-created; neither consumes the copier template, so the ratified applicable set already excluded them. Banned resolution recorded on the item. |

`livespec-dev-tooling-ep8n` was MOVED (not mirrored) out of the `livespec` tenant
when the generic-scanner shape was chosen, because from that moment the work is
upstream. `livespec-4kwu` is CLOSED in `livespec` as the moved-out record — that
is not a duplicate, and re-filing it here would create one.

### NOT THIS THREAD'S — surface, do not adopt

**CI egress failures are an infrastructure pattern, not flakes to re-run.** Four
across 2026-08-11/12: two TLS "certificate is not valid for any names" on
checkout, one `uv` dependency-install failure, and one `mise` cannot-install-
shellcheck TLS failure. Threads `phase0-selfhosted-shadow-lane` and
`livespec-ci-on-hetzner` own that surface. Report it; do NOT file into their
lanes unilaterally.

When master CI is red, **read the STEP list, not the job colour.** The
2026-08-12 red on `check-copier-template-smoke` was step 7 "Install Python dev
deps via uv" FAILING and step 10 — the check that gives the job its NAME — being
SKIPPED. A discriminating control settled it: `15e52ca1` CONTAINS the template
change and was CI-SUCCESS, and the red commit differed only by release metadata.

### Standing hazards — each cost this thread real time

- **A FILE UNDER `history/vNNN/proposed_changes/` IS NOT A DESIGN RECORD.** A
  history cut archives accepted AND REJECTED proposals side by side; only the
  paired `<stem>-revision.md` front matter says which. Read its `decision:` field
  AND grep the cut's own ratified spec files. A sentence that never reached a
  ratified file was never a guarantee.
- **DELETE a count, never correct it.** A corrected count re-rots at the next
  amendment; an absent one cannot. Demonstrated inside one hour: a peer session
  corrected a total 28→29 and it needed to be 30 before either PR settled.
- **A `resulting_files[]` entry REPLACES THE ENTIRE FILE.** Re-derive from
  freshly fetched bytes immediately before applying. The durable fix now exists —
  a mechanical applicator that re-derives from freshly fetched `origin/master`
  and ABORTS unless every target is present exactly once. Use it; do not
  hand-splice.
- **TWO REVIEWERS IS NOT TWO OPINIONS unless the INSTRUMENTS differ.** Give each
  reviewer a distinct probe. When that was done, findings were DISJOINT every
  round — neither could have substituted for the other.
- **A correction is not safe because it corrects something real.** Three of
  v202's ten blockers were INTRODUCED by a fix round correcting real defects, and
  the last was a citation made MORE PRECISE and thereby FALSE. Review the FIX.
- **Under rebase-merge ONE change has TWO SHAs.** `git merge-base --is-ancestor`
  on a merged PR's branch tip gives a FALSE NEGATIVE; test the merge commit.
- **A fresh worktree fails `check-primary-checkout-commit-refuse-hook-installed`**
  with `worktree_pack_absent`. Run `just install-worktree-pack`, then
  `git checkout -- .livespec.jsonc` immediately after creating any worktree.
- **Never discard an unexamined dirty tracked file** — diff against
  `origin/master` first. A dirty `plan/` file belonging to ANOTHER session
  appeared in the primary this session; it was left alone and its owner cleaned
  it.
- **The repo's rate-limit guard denies any command pairing a loop keyword with
  `gh pr`/`gh run`** — and it matches jq's `select(` and a bare `for` in an
  inline python one-liner. Capture the forge read to a FILE in one call and parse
  in a SEPARATE call; poll with `gh api --cache`.
- **Run fleet sweeps as `bash <file>`, never inline** — `mapfile` is bash-only
  and this shell is zsh.

### Next concrete action

**One item is live and has a named next step: `livespec-5qu1`. One item needs a
maintainer design call: `livespec-jvz8`. Nothing else is this thread's.**

**`livespec-5qu1` — the maintainer chose the `app-id:` direction on 2026-08-12,
and the template change has LANDED** (PR #2214, merge `88842637`). The copier
template now mints with `actions/create-github-app-token@v3` passing `app-id:`,
which is auth-neutral for both generated consumers because both already carry
`app-id:`. Do NOT re-open that choice, and do NOT propose the `client-id:`
migration as an alternative — it is decoupled, not cancelled, and needs each
consumer's `APP_ID` secret reset to the App's OAuth client ID first, which only
the maintainer can do.

**The item stays OPEN on ONE named leg: the LIVE auto-merge exercise.** Rendering
is not evidence. The `@v3` + `app-id:` pairing exists in no repository yet; it
reaches a consumer only after livespec cuts a release carrying `88842637` and
that consumer takes a `copier update`. Consumer pull requests open today cannot
serve — each runs its own committed `@v1` + `app-id:` workflow, so a green one
would prove the OLD form works. What discharges the leg, and in what order to
read it, is recorded on the ledger item itself.

**`livespec-dev-tooling-ep8n` was HANDED OFF by maintainer decision on
2026-08-12. This thread does not carry it further, and the choice that produced
that hand-off must NOT be re-offered.** The maintainer was asked whether to
authorise the independent adversarial review this thread needed in order to
ratify the amendment and land the fix, or to hand the item to whoever grooms
`livespec-dev-tooling`; they chose to hand it off. The authority is
`plan/spec-side-autonomy/handoff.md` §"Disposition of the one open decision —
SETTLED, do not reopen" — read it before forming any plan that touches `ep8n`.

An earlier revision of this section recommended `ep8n` as the most consequential
thing to pick up absent direction. That recommendation was written at
2026-08-12T05:50Z, four minutes BEFORE the hand-off landed, and acting on it
would reverse a maintainer decision. It is retracted, not merely superseded.

A second sentence in this section is also retracted. It read that
`livespec-5qu1` "is blocked on the maintainer for the half that cannot be read
from outside the consumer repositories", and that neither remaining item was
available. That was true when written at 06:13Z and stopped being true minutes
later, when the maintainer chose the `app-id:` direction — which needs NO secret
read and therefore unblocked the item. Do not carry that sentence forward from
any cached reading of this file.

`livespec-jvz8` remains the one item still needing a maintainer DESIGN call: its
obvious resolution is BANNED, so it is not available for autonomous pickup and
must not be started on a successor's own initiative.

Do NOT archive `plan/spec-side-autonomy/`.

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
| `thread_dir` | `/data/projects/livespec/plan/spec-side-autonomy` |
| `topic` | `spec-side-autonomy` |
| `worker_session` | `spec-side-autonomy` |
| `supervisor_session` | `spec-side-autonomy-supervisor` |
| `WORKER_TARGET` | `'=spec-side-autonomy:'` |
| `SUPERVISOR_TARGET` | `'=spec-side-autonomy-supervisor:'` |
| `runtime_dir` | `/data/projects/livespec/tmp/overseer/spec-side-autonomy/` |
| `supervisor_marker` | `/data/projects/livespec/tmp/overseer/spec-side-autonomy/.supervisor-state` |
| `wait_channel` | `/data/projects/livespec/tmp/overseer/spec-side-autonomy/worker-status.log` |
| `ledger_anchor` | `livespec-jvdvx4` |

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
generator_ref='448032c6dcf1'
generator_version='0.16.2'
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
prose digest also shipped under version `0.15.0`, so a version match would
report a different generator where there is one and the same.

## Thread-specific Valves

- The ledger anchor is epic `livespec-jvdvx4` in the `livespec` tenant. The
  design record is `plan/spec-side-autonomy/research/brainstorm.md`; it is
  historical design evidence, not a status ledger. Read status from the ledger.
- **Lane A is CLOSED as of 2026-08-03. Do not re-ask its three values calls.**
  All three are resolved and recorded in `plan/spec-side-autonomy/handoff.md`
  §"Lane A — CLOSED" and `research/brainstorm.md` §"Values calls — ALL THREE
  RESOLVED 2026-08-03". Re-opening them requires a fresh maintainer decision,
  not a re-ask. The lane-independence rule it used to carry still holds for any
  FUTURE maintainer-owned call: such a call gates only the increment that needs
  it, never the whole thread, so stand down on that action alone and keep
  driving everything else.
- The resolved decisions bind later increments and are not recommendations:
  drift acceptance is amendable to the consensus tier ONLY, through a DEDICATED
  `spec_governance.drift_acceptance_mode` key (`human | consensus`, default
  `human`, opt-in), never through `revise_decision_mode` and never to
  `delegated`; the groom cut may be automated last, consensus-gated, with
  slice-size ceilings and a regroom cap as required rails; the consensus-tier
  definition lives in livespec core and is implemented by
  `livespec-orchestrator-beads-fabro` and `livespec-overseer`.
- **Class (c) doctrine floors are the checks this thread must not weaken.**
  Drift acceptance, the groom cut, and the truly-unresolvable set may not be
  touched by any config key without a ratified spec amendment, and any such
  amendment is Increment 3. Lane A unblocked those amendments in principle, but
  Increment 3 stays blocked in practice until the consensus panel exists, and
  the `drift_acceptance_mode` key must not ship armed-able before it does. The
  shared protocol's "never
  REMOVE, WEAKEN, or SKIP an existing check" applies here to doctrine sentences,
  not only to executable checks — a proposal that relaxes one of these is a
  reversal of a safety guarantee and reaches the maintainer.
- The `drive` contract's refusal of spec-side action-ids in
  `livespec-orchestrator-beads-fabro` is deliberately preserved. The foreman is
  the spec-side executor. Do not propose changing that refusal.
- Every proposed change this thread files is ratified only after the independent
  read-only adversarial review returns NO BLOCKERS, per `AGENTS.md`
  §"Independent Fable review before every ratification" and
  `.ai/spec-proposal-review.md`. A blocker routes to the maintainer with a
  recommended fix and is never self-waived — including when this thread is the
  author of the proposal under review.
- File one topic file per independently-acceptable piece. A revise decision is
  per proposed-change FILE, so a bundle that must be dispositioned selectively
  has to be split before it is filed.
- Ready, factory-safe implementation slices are built factory-side — the `drive`
  operation with action `impl:<id>`, or the Dispatcher drain — never inline in
  a planning session. File them as children of `livespec-jvdvx4`.
- Cross-repo pieces land as ONE epic with per-repo child work-items and
  cross-repo links, never as "follow-up PRs in another session". Increment 1
  alone spans `livespec`, `livespec-driver-claude`, `livespec-driver-codex`,
  and `livespec-dev-tooling`.
- The sibling thread `plan/foreman/` in repository `livespec-overseer` is
  cross-linked, never duplicated: it owns the foreman and the consensus-panel
  implementation; this thread owns the core-owned `spec_governance` lever
  design. Neither thread closes into the other, and this binder does not mirror
  the sibling's live status. If a slice fits neither side clearly, prepare the
  classification evidence before raising that boundary as a valve.
- Write every repository name in full in maintainer-facing output. This thread
  cites `livespec-orchestrator-beads-fabro` constantly, and the bare suffix
  `beads-fabro` is ambiguous with `livespec-console-beads-fabro`.

## HALT-first preconditions

Expected worker session: `spec-side-autonomy`.

Expected supervisor session: `spec-side-autonomy-supervisor`.

Exact target repository: `/data/projects/livespec`.

Run these in order before doing anything else. Stop on the first failure and
act on its labelled `REMEDY:`.

1. The supervised session exists:

```bash
WORKER_TARGET='=spec-side-autonomy:'
tmux has-session -t "$WORKER_TARGET" \
  || { echo "HALT: expected worker session 'spec-side-autonomy'"; echo "REMEDY: ask the maintainer whether to start that worker session"; exit 1; }
```

2. The supervised session is a live agent session:

```bash
WORKER_TARGET='=spec-side-autonomy:'
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
[ -n "$pane_pid" ] \
  || { echo "HALT: empty pane_pid for 'spec-side-autonomy'"; echo "REMEDY: re-check the exact worker target and stop if it still resolves empty"; exit 1; }
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
WORKER_TARGET='=spec-side-autonomy:'
SUPERVISOR_TARGET='=spec-side-autonomy-supervisor:'
tmux has-session -t "$SUPERVISOR_TARGET" \
  || { echo "HALT: expected supervisor session 'spec-side-autonomy-supervisor'"; echo "REMEDY: switch to the correct supervisor session or ask the maintainer to bootstrap it"; exit 1; }
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
supervisor_pane_pid=$(tmux display-message -p -t "$SUPERVISOR_TARGET" '#{pane_pid}')
[ -n "$supervisor_pane_pid" ] \
  || { echo "HALT: empty pane_pid for 'spec-side-autonomy-supervisor'"; echo "REMEDY: re-check the exact supervisor target and stop if it still resolves empty"; exit 1; }
[ "$supervisor_pane_pid" != "$pane_pid" ] \
  || { echo "HALT: supervisor and worker resolve to the SAME pane"; echo "REMEDY: re-check both exact targets — a prefix match puts both names on one pane, and the worker's agent then reads as the supervisor's"; exit 1; }
ps -o pid=,comm=,args= --ppid "$supervisor_pane_pid" --pid "$supervisor_pane_pid" -H
# PASS only if a live `claude` or `codex` process appears in that tree.
# A lone shell (zsh/bash) with no agent child is a HALT.
# REMEDY: if no live agent appears, ask the maintainer to start the agent in that session.
```

Both pids are resolved inside this block rather than inherited from the
previous check, so it is self-contained and cannot pass on an unset variable.

4. The plan thread exists inside the absolute target repository:

```bash
test -d "/data/projects/livespec/plan/spec-side-autonomy" \
  || { echo "HALT: missing plan thread /data/projects/livespec/plan/spec-side-autonomy"; echo "REMEDY: create or choose the correct plan topic before supervising"; exit 1; }
```

5. The worker pane's resolved cwd is inside the target repository:

```bash
WORKER_TARGET='=spec-side-autonomy:'
pane_cwd=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_current_path}')
[ -n "$pane_cwd" ] \
  || { echo "HALT: empty pane_current_path for 'spec-side-autonomy'"; echo "REMEDY: re-check the exact worker target and stop if it still resolves empty"; exit 1; }
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
ledger_anchor='livespec-jvdvx4'
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

The epic's children carry the per-increment status. Enumerate them from the
ledger rather than from this binder or from the thread's design record. Pass
`--all`: the default listing HIDES closed items, so a slice that was filed and
finished reads as never filed. Measured in this tenant on 2026-08-03, the same
parent returned 1 row by default and 15 rows with `--all`.

```sh
cd /data/projects/livespec
ledger_children() {
  if command -v with-livespec-env.sh >/dev/null 2>&1; then
    with-livespec-env.sh -- bd list --parent "$1" --all --json
  else
    bd list --parent "$1" --all --json
  fi
}
if ! children_json="$(ledger_children 'livespec-jvdvx4')"; then
  echo "HALT: cannot enumerate children of 'livespec-jvdvx4'"
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
control_parent='livespec-c1k9'   # known to have children in this tenant
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

Measured on 2026-08-03: the control passes, and both `livespec-jvdvx4` and the
sibling epic `livespec-hhu5pn` genuinely had zero children at that time. That
zero is trustworthy only because the control ran; re-run it, do not cite this
sentence as the measurement.

Preserve the tmux lookup verdict before filtering its output:

```sh
WORKER_TARGET='=spec-side-autonomy:'
pane_pid=$(tmux display-message -p -t "$WORKER_TARGET" '#{pane_pid}')
tmux_rc=$?
[ "$tmux_rc" -eq 0 ] \
  || { echo "HALT: tmux pane lookup failed for 'spec-side-autonomy'"; echo "REMEDY: re-check the exact target before filtering its output"; exit 1; }
printf '%s\n' "$pane_pid" | head -1
```

Inspect read-only with a scrollback sample plus the visible pane:

```sh
WORKER_TARGET='=spec-side-autonomy:'
tmux capture-pane -p -t "$WORKER_TARGET" -S -40
```

Check the visible footer for an open picker before every paste:

```sh
WORKER_TARGET='=spec-side-autonomy:'
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
WORKER_TARGET='=spec-side-autonomy:'
tmux send-keys -t "$WORKER_TARGET" -- '<condition-command>'
tmux capture-pane -p -t "$WORKER_TARGET" | tail -8   # confirm it landed
tmux send-keys -t "$WORKER_TARGET" Enter             # only after verifying
```

For longer text, write the reviewed instruction to `/tmp/msg.txt`, then paste,
verify, and submit it in separate calls:

```sh
WORKER_TARGET='=spec-side-autonomy:'
tmux load-buffer -b sup /tmp/msg.txt
tmux paste-buffer -b sup -t "$WORKER_TARGET"
tmux capture-pane -p -t "$WORKER_TARGET" | tail -8   # confirm it landed
tmux send-keys -t "$WORKER_TARGET" Enter             # only after verifying
```

Create the named wait channel, tell the worker to append one line there at every
milestone, and arm this pane watcher before ending a turn with worker-held work
in flight:

```sh
WORKER_TARGET='=spec-side-autonomy:'
wait_channel=/data/projects/livespec/tmp/overseer/spec-side-autonomy/worker-status.log
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
the shared protocol. This thread's most common non-pane obligation is a spec PR
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

## Corrections

Thread-specific corrections belong here. Regeneration must preserve this
section byte-for-byte, including spelling, punctuation, code formatting, blank
lines, and ordering.

T1. A queued instruction decays. A codex worker drains its input queue only at
turn end, so orders written minutes earlier are read against a world that has
moved. In this thread the queue reached five deep and one entry — "delete
spec-governance-pr-merge.md from the branch" — was correct when written and
would have CORRUPTED v190 had it executed after the revise already rejected that
proposal into history. Interrupt, VOID the whole queue, and re-send one
instruction that opens by voiding everything prior. Never append to a stale
queue.

T2. I applied the shared protocol's own paste rule too narrowly and it bit me.
C1 says verify a paste only when its size is stable across two spaced reads; I
compared the PASTE-TOKEN size, which sat still at "1020 chars" across both reads
while the tail of the message arrived as literal text BESIDE the token. Enter
then did not submit and the composer held a mangled instruction. Compare the
WHOLE composer line, not the token's self-reported count — and better, obey C1's
second clause, which already said not to paste long briefs at all. The
file-reference path worked first try. A rule applied only when the input LOOKS
long is not a rule.

T3. I walked into T2 again, on the fourth message of the next session, having
read T2 that same session and cited it in my own marker. I sent a ~1900-char
instruction with `tmux send-keys` because it felt "short enough" for the
file-reference path. The composer showed `[Pasted Content 1020 chars]` and
nothing else, stable across two spaced reads and stable in a full-pane `cat -A`
capture, so I read it as TRUNCATION. It was T2's spill: the token held the first
1020 chars and the remainder sat beside it, in pane real-estate I was not
reading. The threshold is not length and never was — it is MORE THAN ONE LINE.
Every file-reference send in that session landed first try; the one inline send
cost a recovery and a rewrite.

The recovery sequence is the part worth keeping, because C1 recorded only that a
second `C-c` "would have killed a live agent session" and left the safe path
untested. Measured, on an IDLE worker with nothing in flight: ONE `C-c` did NOT
clear the composer and did NOT kill the agent — it removed the collapsed token
and REVEALED the literal remainder, which is what finally proved spill rather
than truncation; the codex process was confirmed alive immediately after. ONE
`C-u` then cleared the revealed remainder. Then the file-reference path landed
first try. Editing keys are safe ONLY under those two preconditions — composer
stable across two spaced reads, and the worker IDLE rather than mid-turn —
because C1's damage came from sending them INTO a still-arriving stream, where
they are consumed as input rather than as commands. Measure both before sending
any.

T4. TWO MORE WAYS THE COMPOSER READS EMPTY WHEN IT IS NOT, both mine, both in one
session, and T2/T3 covered neither. T2 and T3 are about a paste SPILLING; these
are about the READER being wrong.

- **Wrong REGION.** I verified a send with `capture-pane | tail -4`, which CUT
  ABOVE the composer line. Empty.
- **Wrong TIME.** I verified with `tail -12` — correct region — but in the SAME
  Bash call as the `send-keys`, so the capture RACED the delivery. Empty.

Either one, acted on, produces a re-send or a `C-u` into a live stream, which is
C1's exact damage. THE RULE THAT COVERS ALL FOUR CAUSES: verify in a SEPARATE
call from the send, read `tail -12` or wider, and ASSERT THE REGION CONTAINS A
DISTINCTIVE FRAGMENT OF WHAT YOU SENT. Emptiness and stability both pass on a bad
read; only the content assertion discriminates.

A related trap when the worker is BUSY: comparing `tail -N` of the whole pane
across two reads always reports CHANGING, because the live transcript above the
composer moves. Compare the composer LINE — `grep '^❯' | tail -1`, taking the
LAST marker, never the first, because the first is the stale echoed prompt (C5).

T5. I DOUBLE-ARMED THE PANE WATCHER TWICE, the second time one hour after
writing down that I would check first. Two watchers over one channel
double-deliver every milestone, which reads as duplicated progress.

The first time I stopped the duplicate and resolved to check `pgrep` before
arming. That resolution failed, because a rule held in working memory competes
with everything else in context. The second time I put a SINGLE-INSTANCE LOCK in
the watcher script itself — it writes its PID, traps EXIT to clear it, and
refuses with `REFUSED: watcher already running as PID <n>` if a live holder
exists. I then RAN the script to prove the guard fires rather than assuming it.

The general form, and the reason it is worth a Correction rather than a note:
when the same slip recurs, the fix is not a better resolution — it is moving the
check from the agent to the tool, at the point of use. This session's other
durable fixes have the identical shape: a mechanical applicator that re-derives
`resulting_files` from freshly fetched bytes instead of trusting the author to
remember, and an acceptance clause written INTO a ledger item instead of into a
conversation that ends.
