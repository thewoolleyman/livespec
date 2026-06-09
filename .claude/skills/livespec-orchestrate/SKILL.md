---
name: livespec-orchestrate
description: Layer 3 cross-repo orchestration driver for the livespec family (invoked as /livespec-orchestrate). Composes /livespec:next and the active impl-plugin's next; dispatches sub-agents (each working in its own self-managed secondary worktree, NOT the harness isolation mechanism) into livespec, livespec-impl-*, livespec-dev-tooling, and livespec-runtime; reaps merged worktrees via `just reap-stale-worktrees`; runs `just check` + /livespec:doctor as a hard gate; emits a structured iteration journal; halts on architectural ambiguity, broken state, destructive ops, phase boundaries (default; can be pre-authorized), or (defensive) context-budget exhaustion. Per `SPECIFICATION/spec.md` §"Three-layer orchestration architecture" and §"Layer 3 loop driver — required shape and discipline" in non-functional-requirements.md, this skill is the SINGLE Layer 3 driver across the livespec family — impl-plugin repos do NOT carry their own. The directory name carries a `livespec-` visual prefix to disambiguate from the harness's built-in `/loop` skill (recurring-task scheduler); project-local skills have no real namespace mechanism, so the prefix is a convention, not enforcement.
---

# Layer 3 cross-repo orchestration driver

This skill is livespec's resident Layer 3 loop driver per
`SPECIFICATION/spec.md` §"Three-layer orchestration architecture" →
"Layer 3 — Cross-repo orchestration (livespec-resident)" and
`SPECIFICATION/non-functional-requirements.md` §"Layer 3 loop driver —
required shape and discipline". It is the single Layer 3 driver across
the livespec family of repos:

- `/data/projects/livespec/` (this repo)
- `/data/projects/livespec-impl-plaintext/`
- `/data/projects/livespec-dev-tooling/`
- `/data/projects/livespec-runtime/`

The active impl-plugin is now `livespec-impl-beads` (its
`list_work_items` wrapper and `/livespec-impl-beads:*` skills are what
the dispatch table and §"Cross-repo state aggregation" invoke); the
whole family's work-items live in beads-on-Dolt tenants, one per repo.
Note `livespec-impl-plaintext` above is the still-present family REPO
directory (itself now a beads tenant), distinct from the retired
plaintext impl-plugin. Future sibling repos join the family by being
added to the cross-repo state aggregation step below.

## Inputs

The driver accepts these parameters; the user supplies them inline or
via the `/livespec-orchestrate` invocation argument:

- **`mode`** (`interactive` | `autonomous`). Default `interactive`
  when the next picked action is spec-side (revise, propose-change,
  critique, prune-history); default `autonomous` when it is impl-side
  (implement, capture-impl-gaps, capture-spec-drift, process-memos).
  The default flips per-iteration based on what `next` returns.

- **`budget`** (one of: iteration count, wallclock duration, token
  consumption — or a composition). The driver MUST honor a finite
  budget; an unbounded loop is forbidden. Default: **drive the
  resolved scope to completion** (every work-item in the epic /
  scope-file / open queue), capped at 30 iterations and ~300K
  orchestrator-context tokens as defensive safety nets — not as the
  primary stop condition. The primary stop condition is "scope
  drained or halt condition fired."

  Because the driver dispatches each work-item to a sub-agent that
  does the work in its OWN secondary worktree (see §"Steps" →
  §"Dispatch"), orchestrator context grows only from state-checks,
  the iteration journal, and short sub-agent return summaries — NOT
  from the work the sub-agents do. Sub-agents have their own
  independent context budgets. For a typical 5-10 work-item epic the
  orchestrator's own context consumption is in the tens of thousands
  of tokens. The iteration and context caps above are safety nets for
  degenerate dispatch malfunction (a runaway journal, a dispatch loop
  that's actually doing the work itself), not the typical-case gate.

- **`epic`** (optional work-item ID — e.g., `li-univck`). When set,
  the driver scopes work to that epic and its `depends_on[]`
  sub-tasks; the cross-repo state aggregation filters to the
  union of {epic, its dependencies (recursively), open work-items
  pre-authorized via a wave-plan in the conversation context}. When
  unset, the driver picks from the open queue across the family.

- **`scope-file`** (optional path; e.g., `tmp/prompt.md`). When set,
  the driver reads pre-authorization rules from this file —
  what's authorized for autonomous dispatch, what requires user
  approval, halt conditions specific to this epic. The wave-plan
  grammar is described in §"Wave-plan grammar" below.

## Steps

1. **Verify session state (cross-repo).** For each repo in the
   family, fetch origin/master and tabulate truly-open work-items
   via the impl-plugin's `list_work_items` thin-transport wrapper
   against the live per-repo beads tenant (work-items are no longer
   a git-tracked file — the old root `work-items.jsonl` is frozen at
   `archive/work-items.jsonl`; canonical work-item state is now the
   running Dolt tenant). The exact, copy-pasteable invocation —
   including the wrapper path, the `.beads/{config.yaml,metadata.json}`
   + `BEADS_DOLT_PASSWORD` connection prerequisites, and the common
   mistakes it avoids — is in §"Cross-repo state aggregation" below;
   do NOT hand-roll the reducer. Also surface: open PRs
   across the family, pending PCs in each repo's `proposed_changes/`,
   any current worktrees on master with uncommitted spec edits, any
   master red CI. Per `feedback_master_red_is_not_deferral`, master
   red MUST be surfaced at session-start; do NOT proceed silently
   on a broken family.

   For the master-red-CI check, do NOT hand-roll a `gh run list`
   query: a bare `gh run list --branch master --limit 1` returns the
   most-recent run of ANY workflow, so a more-recent non-CI run
   ("Auto-update behind PRs", "Pin freshness sweep", "Bump pin from
   sibling dispatch", "Release Please") MASKS an older red CI run
   (the li-bxhwh3 mistake-pattern, per
   `feedback_master_ci_query_must_filter_workflow`). Instead run
   dev-tooling's canonical `master_ci_green` check from INSIDE each
   family repo — it already scopes the query to `--workflow CI`, so a
   non-CI run can never mask a red CI conclusion, and `gh` infers the
   repo from that repo's git remote (the check takes no repo arg):

   ```bash
   for repo in livespec livespec-impl-plaintext \
               livespec-dev-tooling livespec-runtime; do
     ( cd "/data/projects/$repo" \
       && uv run python -m livespec_dev_tooling.checks.master_ci_green ) \
       || echo "RED master CI in $repo — HALT (master red is not a deferral)"
   done
   ```

   It exits 1 on a red conclusion (`failure` / `cancelled` /
   `timed_out` / `action_required` / `stale` / `startup_failure`) and
   0 on `success` / pending / no-run / `gh`-unavailable. It is
   import-clean in every family repo (`livespec_dev_tooling` is a
   pinned dependency of each), so the same invocation scales to
   future siblings — add the repo to the loop. Any repo's exit 1 is
   the highest-severity halt for the survey.

   Also reconcile orphaned worktrees left by prior or crashed
   sessions: for each family repo, run the reaper
   `mise exec -- just reap-stale-worktrees /data/projects/<repo>`
   (run from the livespec primary; the recipe takes a repo-path
   arg). This is what catches the async-merge-after-exit leftovers —
   a sub-agent's PR `--auto`-merges server-side AFTER the agent has
   exited, so the agent cannot self-clean its own worktree (see
   §"Worktree hygiene (reaper)"). The reaper is idempotent and only
   removes non-primary worktrees whose branch is remote-gone/merged
   AND clean AND not live-locked, so it is safe to run unconditionally
   at session start.

2. **Resolve the work scope.** Based on `epic` / `scope-file` inputs,
   produce the iteration's candidate work set:
   - If `epic` is set: union of {epic, recursive `depends_on[]`}.
   - If `scope-file` is set: parse the wave-plan and use its
     enumerated work-items + pre-authorization rules.
   - Otherwise: compose `/livespec:next` + each impl-plugin's
     `next` across the family. The driver decides ordering;
     neither Layer 2 ranker bakes in a cross-side weighting
     (per `contracts.md` §"Cross-side composition exclusion").

3. **Dispatch loop.** While budget remaining AND work pending AND
   no halt condition fired:

   a. **Pick.** Select the highest-ranked candidate from §Step 2.
      Apply the dispatch table in §"Dispatch table" below to map
      action → skill invocation.

   b. **Dispatch.** For work that mutates a repo, dispatch a
      sub-agent with `agentType: livespec-implementer` (the custom
      subagent defined at `.claude/agents/livespec-implementer.md`;
      see §"Dispatch table") rather than a bare general-purpose
      agent. Because that agent's definition carries the standing
      dispatch contract ONCE, the per-dispatch brief shrinks to a
      SHORT task line — "implement <work-item-id> in <repo>" — PLUS a
      one-line binding-rules handoff naming the exact path, e.g.
      "binding repo rules: <worktree>/AGENTS.md — read first." Do NOT
      re-paste the Red-Green-Replay protocol or the worktree /
      mise-exec / no-`--no-verify` disciplines into the brief; they
      live in the agent definition (this is the whole purpose of epic
      li-dispatch-agents — kill the per-dispatch re-derivation tax).
      The agent creates its OWN secondary worktree in the target repo
      via `git -C /data/projects/<repo> worktree add
      <repo>/.claude/worktrees/<slug> -b <branch> origin/master` and
      works inside it. Do NOT use the harness `isolation: "worktree"`
      mechanism — it only auto-removes UNCHANGED worktrees, so any
      worktree carrying committed work is left permanently orphaned,
      and it has been observed to flip `core.bare`. The primary is NOT
      bare (epic li-unbare eliminated the bare flag; `core.bare` MUST
      stay unset); edits happen in the self-managed secondary because
      the primary carries a commit-refuse hook, not because it is
      bare. The sub-agent does the work end-to-end: edits, tests,
      `mise exec -- git commit`, `gh pr create`, `gh pr merge
      --auto --rebase --delete-branch`. The driver does NOT
      perform the edits inline; it dispatches and tracks. The
      ORCHESTRATOR — not the sub-agent — owns reaping the
      sub-agent's worktree once the PR confirms merged (Step 3c).

   c. **Run janitor.** After the sub-agent reports completion AND
      the orchestrator has CONFIRMED the PR merged (poll
      `gh pr view <PR#> --json state` until `MERGED`; the
      sub-agent reports only that auto-merge is armed — see
      §"Tooling reminders"), run the janitor as a hard gate:
      `just check` + `/livespec:doctor`. A non-zero janitor exit
      MUST prevent the next iteration from proceeding. Recovery:
      surface findings to the user (interactive mode) or halt
      with a resume snapshot (autonomous mode). Once the janitor
      passes, run the reaper against that repo —
      `mise exec -- just reap-stale-worktrees /data/projects/<repo>`
      — to remove the just-merged sub-agent worktree (its branch
      is now remote-gone). See §"Worktree hygiene (reaper)".

      **Live work-item enforcement at the `/livespec:doctor` gate.**
      The six cross-boundary work-item integrity invariants
      (`no-orphan-dependency`, `no-stalled-epic`,
      `no-duplicate-gap-id`, `no-stale-gap-tied`,
      `depends_on-ref-wellformedness`, `unresolved-spec-commitment`)
      acquire their work-items by invoking the active impl-plugin's
      `list-work-items` wrapper (per livespec `contracts.md`
      §"Doctor cross-boundary invariants" → "Work-item integrity
      invariants — plugin-agnostic data acquisition"). For these
      invariants to RUN live (pass/fail/warn) rather than skip, the
      `/livespec:doctor` invocation MUST be run with
      `LIVESPEC_IMPL_LIST_WORK_ITEMS` pointing at the active impl-
      plugin's wrapper PLUS the per-tenant beads connection in the
      environment — the SAME env the §"Cross-repo state aggregation"
      read-path already establishes (source the mode-600
      `tenant-secrets.env.local`, export `BEADS_DOLT_PASSWORD` for
      the repo's tenant, export `LIVESPEC_BD_PATH=/usr/local/bin/bd`,
      and run from `cwd=/data/projects/<repo>` so `bd` reads
      `.beads/{config.yaml,metadata.json}`). Reuse that section's
      recipe verbatim; do not duplicate it. Concretely, prefix the
      doctor run with:

      ```bash
      # env already sourced per §"Cross-repo state aggregation":
      #   set -a; . .../tenant-secrets.env.local; set +a
      #   export LIVESPEC_BD_PATH=/usr/local/bin/bd
      #   export BEADS_DOLT_PASSWORD="$(eval echo \"\$BEADS_DOLT_PASSWORD_$(echo $repo | tr '.-' '__')\")"
      #   cd /data/projects/$repo
      export LIVESPEC_IMPL_LIST_WORK_ITEMS=/data/projects/livespec-impl-beads/.claude-plugin/scripts/bin/list_work_items.py
      ```

      When `LIVESPEC_IMPL_LIST_WORK_ITEMS` is unset (e.g. a hermetic
      CI run), the six invariants `skip` cleanly — that is the
      intended no-regression default; the live janitor gate is where
      they ENFORCE.

   d. **Journal.** Append one record to the iteration journal
      (§"Iteration journal" below) capturing pick, dispatched
      skill, sub-agent outcome (PR URL / commit SHA / rollback),
      janitor result, and budget remaining.

4. **Post-loop.** When the loop exits cleanly (queue drained,
   epic complete, or budget exhausted), surface the journal
   summary to the user. When the loop exits on a halt condition,
   write a resume snapshot (§"Resume protocol" below) naming the
   next concrete step. Either way, run a final reaper sweep across
   every touched family repo —
   `mise exec -- just reap-stale-worktrees /data/projects/<repo>`
   per repo — so no merged sub-agent worktree (including any whose
   `--auto` merge landed after the per-iteration Step 3c poll) is
   left orphaned. See §"Worktree hygiene (reaper)".

## Dispatch table

Every mutating dispatch (any row whose mechanism is "sub-agent …" or
an impl-side skill that commits + PRs) MUST be dispatched as
`agentType: livespec-implementer` — the custom subagent defined at
`.claude/agents/livespec-implementer.md` — NOT a bare general-purpose
agent. That agent carries the standing dispatch contract (worktree
discipline, the Red-Green-Replay commit ritual, `mise exec -- git`,
never `--no-verify` / `core.bare true`, the PR handoff) ONCE, so the
per-dispatch brief shrinks to "implement work-item X in repo Y" plus a
one-line binding-rules handoff (see §"Steps" → 3b). Spec-side
`/livespec:*` rows that run in the orchestrator's OWN session
(revise / propose-change / critique / prune-history) are NOT dispatched
this way — they compose inline.

| Action from `next` / scope | Skill / mechanism | Dispatch as |
|---|---|---|
| `revise` (spec-side, livespec) | `/livespec:revise --spec-target <path>` | inline (orchestrator session) |
| `propose-change` (spec-side) | `/livespec:propose-change` | inline (orchestrator session) |
| `critique` (spec-side) | `/livespec:critique` | inline (orchestrator session) |
| `prune-history` (spec-side) | `/livespec:prune-history` | inline (orchestrator session) |
| `implement` (impl-side, beads) | `/livespec-impl-beads:implement <work-item-id>` | `agentType: livespec-implementer` |
| `capture-impl-gaps` (impl-side) | `/livespec-impl-beads:capture-impl-gaps` | `agentType: livespec-implementer` |
| `capture-spec-drift` (impl-side) | `/livespec-impl-beads:capture-spec-drift` | `agentType: livespec-implementer` |
| `process-memos` (impl-side) | `/livespec-impl-beads:process-memos` | `agentType: livespec-implementer` |
| Bug fix (no spec change) | sub-agent: edit + test + commit + PR in the relevant repo's worktree | `agentType: livespec-implementer` |
| Cross-repo coordinated change | sub-agent per repo, dispatched in parallel where independent and sequential where one PR blocks another | `agentType: livespec-implementer` (one per repo) |
| `none` | exit cleanly with journal summary | — |

Per `feedback_cross_repo_epic_driving`, NEVER defer multi-repo work
to "follow-up PRs in another session" — frame as epic, file per-repo
work-items, use doctor as the cross-repo consistency check at the
end of the loop.

## Halt conditions

The driver MUST halt (write resume snapshot + exit) when:

1. **Architectural ambiguity.** A genuine architectural choice not
   pre-decided in `scope-file` surfaces (e.g., "should this be
   pattern A, B, or C?"). Per `feedback_only_ask_on_genuine_doubt`,
   only halt on REAL architectural calls; self-resolve trivial
   wording fixes.

2. **Broken state.** Red CI on a PR the sub-agent couldn't unstick;
   merge conflict the sub-agent couldn't auto-resolve; lefthook-
   blocked commit whose root cause isn't obvious; master red on
   any family repo.

3. **Context-budget exhaustion (defensive safety net).**
   Orchestrator context usage approaching ~300K tokens — under the
   dispatch model this should NOT fire in normal operation (see
   §"Inputs" → `budget`); if it does, that indicates a dispatch
   malfunction or runaway journal, not normal epic progression.
   Write a one-paragraph resume snapshot naming the next concrete
   step from which to resume, then exit cleanly.

4. **Destructive ops not pre-authorized.** Force-push, branch
   delete on shared infrastructure, schema migration without prior
   sign-off, etc. Per `feedback_plan_prescribed_ops_dont_need_auth`,
   ops codified in `scope-file` are pre-authorized; ops outside
   that scope require user judgment.

5. **Phase-boundary advance — DEFAULT halt with explicit opt-out.**
   Per `feedback_phase_advance_is_pr_boundary`, a Phase N → N+1 PR
   boundary is a natural re-orientation point and the DEFAULT halt
   for multi-phase epics. The driver MAY push through a phase
   boundary without halting when (a) the `scope-file` enumerates
   the spanning phases under §"Pre-authorized for autonomous
   dispatch", OR (b) the user invocation explicitly authorizes the
   multi-phase span (e.g., "drive the full epic" or "through Phase
   N"). Outside those, halt at every phase boundary and write a
   resume snapshot.

The driver MUST NOT halt on:

- Self-resolvable typos with one obvious fix (per
  `feedback_dont_halt_on_simple_typos`).
- Minor cosmetic PROPOSAL drift (per
  `feedback_severity_judgment_over_rule_following`); rides along
  with the next substantive revision.
- Routine impl-side `implement` failures that resolve in retry.

## Iteration journal

The driver MUST emit a structured per-iteration record. Storage is
project-local: write to `tmp/loop-status.md` (gitignored;
user-owned scratch per `project_tmp_directory_ownership`).
Append-only; one block per iteration, oldest first.

Each block carries:

```
## Iteration <N> — <ISO-8601-UTC>

- **Pick:** <work-item-id or action description>
- **Dispatched skill:** <skill name + invocation>
- **Sub-agent outcome:** <PR URL | commit SHA | rollback reason>
- **Janitor result:** <green | red + finding summary>
- **Budget remaining:** <iterations-left | wallclock-left | tokens-est>
- **Exit reason** (final block only): <queue-drained | epic-complete | budget-exhausted | halt-<reason>>
```

The journal is machine-readable enough that the next session can
parse the final block to determine resume state.

## Resume protocol

When the loop exits on a halt condition, append a §"Resume snapshot"
block to `tmp/loop-status.md`:

```
## Resume snapshot — <ISO-8601-UTC>

**Halt reason:** <one of the halt conditions above>

**Next concrete step:** <one paragraph naming the work-item, repo,
file, or decision that the next session should pick up from. Cite
specific paths and IDs — no vague references.>

**State at halt:**
- origin/master commits on each family repo: <SHA per repo>
- Open PRs awaiting action: <URL list>
- Truly-open work-items: <count per repo>
```

The next session reads the resume snapshot, verifies state (master
may have moved since), and re-enters the loop at the named step.

## Cross-repo state aggregation

The driver materializes work-item state from each repo via the active
impl-plugin's (`livespec-impl-beads`) `list_work_items`
**thin-transport wrapper** — NOT a hand-rolled reducer. The wrapper
emits a top-level JSON **array** of work-item views. It is the
supported machine-query surface (per impl-beads `contracts.md`
§"Thin-transport skills (3) — required machine query surface") and
needs NO venv and NO `PYTHONPATH` — invoke it with a plain `python3`.

The wrapper lives at (note: filename uses **underscores**):

```
/data/projects/livespec-impl-beads/.claude-plugin/scripts/bin/list_work_items.py
```

**Canonical-state caveat (scope of `feedback_read_canonical_state_via_git_show`).**
For SPEC and CODE state, still read canonical committed state from
`origin/master`, not the on-disk working tree (which can lag or carry
edits). But work-item canonical state is NO LONGER a git file: the
family flipped from the plaintext JSONL store to beads-on-Dolt (server
mode), so there is no `origin/master:work-items.jsonl` to read — the
old root file is frozen at `archive/work-items.jsonl`. Canonical
work-item state is the LIVE per-repo Dolt tenant (one tenant DB per
repo, server mode on TCP `127.0.0.1:3307`). The git-show rule keeps
applying to spec/code; for work-items, the live tenant IS canonical.

**Connection model (under beads).** The wrapper takes NO
`--work-items-path` — its `work_items_arg` is accepted-and-ignored.
Connection comes from the CWD's `.beads/{config.yaml,metadata.json}`
plus `BEADS_DOLT_PASSWORD` in the environment, so each enumeration runs
with `cd /data/projects/$repo`. Prerequisites per repo:

- `.beads/config.yaml` — checked in; the server/tenant pointer.
- `.beads/metadata.json` — the local workspace pointer. It is
  **gitignored** (a per-machine file — do NOT commit it). If a repo
  lacks it, it is REGENERABLE from `.beads/config.yaml` + the live
  tenant; `project_id` is SERVER-STABLE (re-running `bd init` yields
  the identical `project_id`). Regenerate WITHOUT touching the
  primary's git (`bd init` auto-commits inside a git repo — never run
  it inside a primary or worktree) via a `/tmp` scratch dir:

  ```bash
  establish_meta() {
    repo="$1"; tenant="$1"            # tenant DB name == repo directory name
    probe="/tmp/bd-ws/$repo"; rm -rf "$probe"; mkdir -p "$probe/.beads"
    cp "/data/projects/$repo/.beads/config.yaml" "$probe/.beads/"
    ( cd "$probe" && BEADS_DOLT_PASSWORD="$pw" /usr/local/bin/bd init --server --external \
        --server-host 127.0.0.1 --server-port 3307 --server-user "$tenant" \
        --database "$tenant" --prefix "$tenant" --skip-agents --skip-hooks \
        --non-interactive --quiet )
    cp "$probe/.beads/metadata.json" "/data/projects/$repo/.beads/metadata.json"
  }
  ```

- `BEADS_DOLT_PASSWORD` — per-tenant secret sourced from the mode-600
  file `/home/ubuntu/workspace/dolt-server/tenant-secrets.env.local`.
  The key is `BEADS_DOLT_PASSWORD_<tenant>` with dots/hyphens mapped to
  underscores.
- `LIVESPEC_BD_PATH=/usr/local/bin/bd` — the pinned `bd` v1.0.5
  binary; NEVER the mise shim.

There is **no `open` filter** — valid `--filter` choices are
`all|gap-tied|freeform|blocked|ready|closed`; pass `--filter all` and
select `status == "open"` yourself (or use `--filter ready` for
open-with-all-deps-closed). `bd list` is read-only and does NOT
auto-commit, so running it against the primaries is safe:

```bash
set -a; . /home/ubuntu/workspace/dolt-server/tenant-secrets.env.local; set +a  # mode-600
export LIVESPEC_BD_PATH=/usr/local/bin/bd     # pinned v1.0.5; NEVER the mise shim
WRAPPER=/data/projects/livespec-impl-beads/.claude-plugin/scripts/bin/list_work_items.py
for repo in livespec livespec-impl-plaintext livespec-dev-tooling livespec-runtime; do
  cd "/data/projects/$repo"                    # bd reads connection from CWD's .beads/
  # password key: BEADS_DOLT_PASSWORD_<tenant with dots/hyphens -> underscores>
  export BEADS_DOLT_PASSWORD="$(eval echo \"\$BEADS_DOLT_PASSWORD_$(echo $repo | tr '.-' '__')\")"
  echo "=== $repo (open) ==="
  python3 "$WRAPPER" --project-root "/data/projects/$repo" --filter all --json \
    | python3 -c "import json,sys
items = json.load(sys.stdin)                       # top-level ARRAY
opens = [w for w in items if w['status'] == 'open']
for w in sorted(opens, key=lambda x: (str(x['priority']), x['id'])):
    print(f\"  {w['id']:24} p{w['priority']} {str(w.get('type','')):9} {w['title'][:54]}\")
print(f'  OPEN={len(opens)}')"
done
```

Common mistakes this pattern avoids: `--filter open` (not a valid
choice — use `--filter all` + select, or `--filter ready`); the
hyphenated filename `list-work-items.py` (the script is
`list_work_items.py`); using the mise `bd` shim instead of the pinned
`/usr/local/bin/bd` v1.0.5; and treating `--work-items-path` as
load-bearing (under beads it is accepted-and-ignored — connection comes
from `.beads/` + `BEADS_DOLT_PASSWORD`, not a file path).

> NOTE: the CI half of this Step-1 survey (work-item **li-bxhwh3**)
> is now mechanically fixed — a bare `gh run list --branch master`
> could mask a red CI run when a more-recent non-CI workflow ran. The
> fix is in Step 1 above: the survey runs dev-tooling's canonical
> `master_ci_green` check from inside each family repo, and that check
> hardcodes `--workflow CI`, so a non-CI run can never mask a red CI
> conclusion. Do NOT hand-roll the `gh run list` query in the survey;
> run the per-repo check (per
> `feedback_master_ci_query_must_filter_workflow`).

## Wave-plan grammar (for `scope-file`)

A `scope-file` (e.g., `tmp/prompt.md`) MAY enumerate work in waves
with explicit pre-authorization. The driver recognizes the
following markers:

- `## Wave <N> — <description>` — a parallel-eligible group of
  work-items. The driver dispatches all items in a wave
  concurrently (multiple Agent tool calls in one message) when
  none of them depend on each other; sequentially when they do.

- `### Pre-authorized for autonomous dispatch:` — work-items
  listed under this heading do NOT require user approval before
  dispatch. The driver proceeds.

- `### Halt + ask user:` — work-items listed under this heading
  ALWAYS require user approval before dispatch, regardless of
  `mode=autonomous`.

- `## Halt conditions` — supplements the default §"Halt conditions"
  above with epic-specific halt triggers.

The wave-plan IS the canonical source of pre-authorization for an
epic; the driver MUST NOT improvise beyond it. When `scope-file`
is absent, the driver falls back to the default safety rules in
§"Halt conditions" above.

## Worktree hygiene (reaper)

Sub-agents dispatched per §"Steps" → §"Dispatch" create their own
secondary worktrees and CANNOT self-clean them, because each PR
`--auto`-merges server-side after the sub-agent has usually exited.
The orchestrator therefore OWNS the cleanup ACTION via the reaper:

```
mise exec -- just reap-stale-worktrees /data/projects/<repo>
mise exec -- just reap-stale-worktrees /data/projects/<repo> --dry-run
```

backed by `dev-tooling/reap_stale_worktrees.py`. The reaper is
livespec-resident and operates on any family repo by path; the
recipe takes a repo-path argument (defaults to `.`). It is
deterministic and idempotent: it removes ONLY non-primary worktrees
whose branch is remote-gone/merged-PR AND whose working tree is
clean AND which are not held by a live process lock — never the
primary, never dirty/remote-present/live-locked worktrees. It is
safe to run unconditionally.

The orchestrator runs the reaper at three points:

1. **Session start (Step 1):** sweep every family repo to reconcile
   orphans left by prior or crashed sessions — this is what catches
   the async-merge-after-exit leftovers.
2. **Post-merge (Step 3c):** after a sub-agent's PR is CONFIRMED
   merged and the janitor passes, reap that repo to remove the
   just-merged worktree.
3. **Post-loop (Step 4):** a final sweep across every touched repo.

DETECTION is the counterpart, owned by the doctor `no-stale-worktree`
check, which warns when a worktree's branch is done — case (a)
merged-into-default OR case (b) remote-gone. The doctor check only
WARNS; the reaper is the deterministic ACTION the orchestrator owns
to clean the orphans the check surfaces.

## Tooling reminders (carried-forward conventions)

- `mise exec -- git ...` for commit / push so lefthook hooks fire
  (per `feedback_mise_exec_for_git_hooks`).
- The primary checkout in each family repo carries a
  commit-refuse hook at `.git/hooks/pre-commit` and
  `.git/hooks/pre-push` that exits 1 when invoked at the primary;
  all edits happen in secondary worktrees via `git worktree add`
  (per `feedback_worktree_discipline_mechanical_enforcement` and
  the codified `primary-checkout-commit-refuse-hook-installed`
  doctor invariant).
- Use `chore(spec):` prefix for spec-only commits (per
  `feedback_chore_spec_for_spec_only_commits`); the red-green-replay
  commit-msg hook rejects `fix:`/`feat:` for spec-only changes.
- Ending-on-master is the ORCHESTRATOR's job, not the sub-agent's.
  A dispatched sub-agent MUST NOT `git checkout master` in its own
  worktree (master is held by the primary, which occupies
  `refs/heads/master`) and MUST NOT run `git config core.bare true`
  under any circumstances — that re-introduces the eliminated bare
  flag (per `contracts.md`
  §`primary-checkout-commit-refuse-hook-installed`: `core.bare` MUST
  NOT be set on the primary). The sub-agent self-manages its own
  worktree and does NOT attempt to clean it up post-merge: the merge
  is async/server-side (`gh pr merge --auto` lands AFTER the sub-agent
  has usually already exited), so the agent CANNOT reliably self-clean
  its worktree. The ORCHESTRATOR owns worktree reaping (Step 3c +
  Step 4 + the session-start sweep in Step 1; see §"Worktree hygiene
  (reaper)"). The sub-agent just reports the PR number and that
  auto-merge is armed.
- The orchestrator refreshes each touched primary itself via `git -C
  /data/projects/<repo> pull --ff-only origin master` (per
  `feedback_end_on_main_branch`; the bind-mounted
  `/home/ubuntu/workspace/<repo>` shares the same `.git`, so one pull
  updates both views). After EVERY merging sub-agent that touched a
  family repo, the orchestrator MUST re-verify `git -C <primary>
  config --get core.bare` is empty; if it regressed to `true`, remove
  any master-squatting worktree, `git config --unset core.bare`, and
  `git reset --hard origin/master` to repopulate the working tree.
  This re-verify+repair is STILL required even with self-managed
  worktrees: `core.bare` has been observed to regress even without
  the harness `isolation: "worktree"` mechanism (tracked as
  li-iroguc), so dropping that mechanism does NOT fix it. Keep this
  guard on every merging dispatch.
- For cross-repo dep awareness: the impl-plugin's `next` ranker
  excludes candidates whose `depends_on[]` resolves to any open
  upstream item via `livespec_runtime.cross_repo.resolve_ref` (per
  `contracts.md` §"Cross-repo dependency awareness"). The driver
  trusts the ranker's exclusion; it does NOT re-implement the
  dependency walk.
