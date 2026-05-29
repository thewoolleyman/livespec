---
name: livespec-orchestrate
description: Layer 3 cross-repo orchestration driver for the livespec family (invoked as /livespec-orchestrate). Composes /livespec:next and the active impl-plugin's next; dispatches sub-agents (with worktree isolation) into livespec, livespec-impl-*, livespec-dev-tooling, and livespec-runtime; runs `just check` + /livespec:doctor as a hard gate; emits a structured iteration journal; halts on architectural ambiguity, broken state, destructive ops, phase boundaries (default; can be pre-authorized), or (defensive) context-budget exhaustion. Per `SPECIFICATION/spec.md` §"Three-layer orchestration architecture" and §"Layer 3 loop driver — required shape and discipline" in non-functional-requirements.md, this skill is the SINGLE Layer 3 driver across the livespec family — impl-plugin repos do NOT carry their own. The directory name carries a `livespec-` visual prefix to disambiguate from the harness's built-in `/loop` skill (recurring-task scheduler); project-local skills have no real namespace mechanism, so the prefix is a convention, not enforcement.
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

Future sibling repos (e.g., `livespec-impl-beads`) join the family by
being added to the cross-repo state aggregation step below.

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

  Because the driver dispatches each work-item via Agent tool with
  `isolation: "worktree"` (see §"Steps" → §"Dispatch"), orchestrator
  context grows only from state-checks, the iteration journal, and
  short sub-agent return summaries — NOT from the work the
  sub-agents do. Sub-agents have their own independent context
  budgets. For a typical 5-10 work-item epic the orchestrator's own
  context consumption is in the tens of thousands of tokens. The
  iteration and context caps above are safety nets for degenerate
  dispatch malfunction (a runaway journal, a dispatch loop that's
  actually doing the work itself), not the typical-case gate.

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
   family, fetch origin/master, materialize work-items.jsonl via
   the impl-plugin's `materialize_work_items` (last-wins reducer),
   and tabulate truly-open work-items. Also surface: open PRs
   across the family, pending PCs in each repo's `proposed_changes/`,
   any current worktrees on master with uncommitted spec edits, any
   master red CI. Per `feedback_master_red_is_not_deferral`, master
   red MUST be surfaced at session-start; do NOT proceed silently
   on a broken family.

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

   b. **Dispatch.** For work that mutates a repo, dispatch via the
      Agent tool with `isolation: "worktree"` (the primary
      checkout is bare; edits MUST happen in secondaries). The
      sub-agent does the work end-to-end: edits, tests,
      `mise exec -- git commit`, `gh pr create`, `gh pr merge
      --auto --rebase --delete-branch`. The driver does NOT
      perform the edits inline; it dispatches and tracks.

   c. **Run janitor.** After the sub-agent reports completion AND
      the PR auto-merges, run the janitor as a hard gate:
      `just check` + `/livespec:doctor`. A non-zero janitor exit
      MUST prevent the next iteration from proceeding. Recovery:
      surface findings to the user (interactive mode) or halt
      with a resume snapshot (autonomous mode).

   d. **Journal.** Append one record to the iteration journal
      (§"Iteration journal" below) capturing pick, dispatched
      skill, sub-agent outcome (PR URL / commit SHA / rollback),
      janitor result, and budget remaining.

4. **Post-loop.** When the loop exits cleanly (queue drained,
   epic complete, or budget exhausted), surface the journal
   summary to the user. When the loop exits on a halt condition,
   write a resume snapshot (§"Resume protocol" below) naming the
   next concrete step.

## Dispatch table

| Action from `next` / scope | Skill / mechanism |
|---|---|
| `revise` (spec-side, livespec) | `/livespec:revise --spec-target <path>` |
| `propose-change` (spec-side) | `/livespec:propose-change` |
| `critique` (spec-side) | `/livespec:critique` |
| `prune-history` (spec-side) | `/livespec:prune-history` |
| `implement` (impl-side, plaintext) | `/livespec-impl-plaintext:implement <work-item-id>` |
| `capture-impl-gaps` (impl-side) | `/livespec-impl-plaintext:capture-impl-gaps` |
| `capture-spec-drift` (impl-side) | `/livespec-impl-plaintext:capture-spec-drift` |
| `process-memos` (impl-side) | `/livespec-impl-plaintext:process-memos` |
| Bug fix (no spec change) | sub-agent: edit + test + commit + PR in the relevant repo's worktree |
| Cross-repo coordinated change | sub-agent per repo, dispatched in parallel where independent and sequential where one PR blocks another |
| `none` | exit cleanly with journal summary |

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

The driver materializes work-item state from each repo's
`work-items.jsonl` using the impl-plugin's `materialize_work_items`
reducer (last-wins per ID). The verified pattern:

```bash
git -C /data/projects/<repo> show origin/master:work-items.jsonl \
  | <impl-plugin-venv>/bin/python -c "
    import json, sys
    from livespec_impl_plaintext.store import materialize_work_items
    records = [json.loads(line) for line in sys.stdin if line.strip()]
    open_items = [r for r in materialize_work_items(records=records).values()
                  if r.status == 'open']
    print(json.dumps([asdict(r) for r in open_items]))
  "
```

The canonical impl-plugin venv for invoking the reducer across any
repo's JSONL store is
`/data/projects/livespec-impl-plaintext/.venv/bin/python`.

Per `feedback_verify_fix_landed_before_memo_disposition` and
`feedback_no_reproducibility_in_dogfooding`, the aggregation reads
`origin/master:work-items.jsonl` directly (not on-disk bare-repo
files, which may be stale).

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
  A dispatched worktree-isolated sub-agent MUST NOT `git checkout
  master` in its own worktree (master is held by the primary, which
  occupies `refs/heads/master`) and MUST NOT run `git config
  core.bare true` under any circumstances — that re-introduces the
  eliminated bare flag (per `contracts.md`
  §`primary-checkout-commit-refuse-hook-installed`: `core.bare` MUST
  NOT be set on the primary). After a sub-agent's PR merges
  server-side, it LEAVES its worktree on its feature branch (or lets
  the worktree be torn down) and reports the merge — it does NOT
  switch the worktree to master.
- The orchestrator refreshes each touched primary itself via `git -C
  /data/projects/<repo> pull --ff-only origin master` (per
  `feedback_end_on_main_branch`; the bind-mounted
  `/home/ubuntu/workspace/<repo>` shares the same `.git`, so one pull
  updates both views). After EVERY merging sub-agent that touched a
  family repo, the orchestrator MUST re-verify `git -C <primary>
  config --get core.bare` is empty; if it regressed to `true`, remove
  any master-squatting worktree, `git config --unset core.bare`, and
  `git reset --hard origin/master` to repopulate the working tree.
- For cross-repo dep awareness: the impl-plugin's `next` ranker
  excludes candidates whose `depends_on[]` resolves to any open
  upstream item via `livespec_runtime.cross_repo.resolve_ref` (per
  `contracts.md` §"Cross-repo dependency awareness"). The driver
  trusts the ranker's exclusion; it does NOT re-implement the
  dependency walk.
