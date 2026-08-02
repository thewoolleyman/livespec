# Fleet shell discipline — worker handoff

This is the worker-owned continuation record for the `livespec` planning thread
anchored by epic `livespec-hhu5pn`. The epic is the status authority; this file
does not mirror a work queue or assert that a previously measured status is
still current.

## Read first

Read these committed `livespec` artifacts in order:

1. `AGENTS.md`
2. `.ai/agent-disciplines.md`
3. `plan/fleet-shell-discipline/why-this-shape.md`
4. `.ai/beads-gaps-workarounds.md`
5. `.ai/verifying-against-the-right-source.md`
6. `.ai/dispatcher-drain-operations.md`

Use the installed `livespec-orchestrator-beads-fabro` `plan` and `groom`
operations for planning and decomposition. Ready, factory-safe implementation
must go through the Dispatcher/Fabro factory; do not implement it inline.

## Ratified boundary and outcome

The `livespec` epic owns the convention and enforcement design: which fleet
shell forms are permitted, which Bash option discipline applies to each script,
how intentional deviations are declared, and how the ban on interpolated Bash
logic in `justfile` recipes is stated in a mechanically testable way.

The sibling `livespec-dev-tooling` epic `livespec-dev-tooling-42t4az` owns
building and shipping the shared check, choosing the shellcheck adoption floor
or baseline, and rolling the check through the fleet by pin. Cross-references
are read-only; neither thread mirrors the other's status.

## Fresh corpus measurement

The worker fetched every fleet repository from the forge and measured each
`origin/master` through `git show` plus `just --dump --dump-format json`. This is
a historical measurement at `2026-08-02T22:58Z`; re-fetch before treating it as
current.

| Repository | Recipes | Bash shebang recipes | Multi-line bodies | Recipes using just interpolation | Tracked `.sh` |
|---|---:|---:|---:|---:|---:|
| `livespec` | 99 | 14 | 14 | 8 | 4 |
| `livespec-dev-tooling` | 85 | 13 | 13 | 8 | 19 |
| `livespec-driver-claude` | 77 | 8 | 9 | 1 | 1 |
| `livespec-driver-codex` | 78 | 9 | 10 | 1 | 1 |
| `livespec-orchestrator-beads-fabro` | 101 | 16 | 19 | 11 | 17 |
| `livespec-orchestrator-git-jsonl` | 85 | 12 | 14 | 7 | 3 |
| `livespec-runtime` | 78 | 12 | 12 | 5 | 1 |
| `livespec-console-beads-fabro` | 33 | 6 | 13 | 3 | 2 |
| `livespec-overseer` | 83 | 16 | 16 | 5 | 1 |
| **Fleet total** | **719** | **106** | **120** | **49** | **49** |

The prior note's totals were 718 recipes, 105 shebang recipes, 118 multi-line
bodies, and 48 tracked shell files. The one-recipe, one-shebang, two-multi-line,
and one-shell-file increases are real forge drift since that reading, not a
parser discrepancy.

The just interpolation uses divide into 41 whole-argument substitutions and 8
substitutions embedded inside shell text or paths. Of the 49 tracked shell
files, 36 initially enable `errexit`, `nounset`, and `pipefail`; 6 deliberately
start with `nounset` and `pipefail` so an aggregate can collect failures; one
POSIX wrapper starts with `nounset` only; and 6 have no initial `set` command.
The no-`set` population is four small POSIX exec guards, one deliberate
pass-through test hook, and one frozen script under an archived plan. This is
why a blanket option rule is wrong even though silent omission remains a defect.

## Resolved convention and enforcement design

These decisions are the input the `livespec-dev-tooling` sibling thread needs.
They are no longer open questions:

1. **A `justfile` is a task index, not a shell-program store.** A recipe may be
   dependency-only or have one plain command line that directly invokes one
   executable, another `just` recipe, or a tracked script. Shebang recipe
   bodies, multiple command lines, control flow, pipelines, redirections,
   command substitutions, and shell command chaining are forbidden. Any such
   logic moves into a tracked script or the repository's implementation
   language. Quiet-command syntax and leading environment assignments do not
   turn an otherwise direct invocation into logic.
2. **Recipe bodies contain no just interpolation.** Recipe parameters use the
   per-recipe positional-arguments attribute and reach the direct command as
   double-quoted positional shell arguments; a variadic tail uses the quoted
   all-arguments form. Global just values needed by a script are explicitly
   exported under a named environment variable and read by that script. This
   eliminates both unsafe textual argument splitting and the Fabro-templating
   collision class. The check should inspect just's JSON dump, not grep source
   text, so comments and declarations cannot produce false positives.
3. **Every active tracked shell script declares its initial option set before
   its first executable statement, and the declaration must match reality.**
   The canonical Bash profile declares and enables `errexit`, `nounset`, and
   `pipefail`; the canonical POSIX-sh profile declares and enables `errexit`
   and `nounset`. A different set is valid only with an adjacent non-empty
   rationale explaining the behavior that requires it. Failure-aggregating
   harnesses therefore declare `nounset` plus `pipefail` and say that expected
   non-zero results are collected for a final summary; tiny POSIX exec wrappers
   use their POSIX profile rather than pretending `pipefail` exists there.
4. **Local option suspension is explicit and paired.** A script that temporarily
   disables `errexit` places a reason at that boundary, captures the intended
   command status immediately, and restores `errexit` before unrelated work.
   An unpaired toggle or an undeclared initial omission is a check failure.
5. **The reference boilerplate is guidance, not a mandatory sourced file.**
   `noclobber`, `errtrace`, and an `ERR` trap are opt-in when a script benefits
   from them. They are not fleet defaults: `noclobber` breaks intentional
   overwrite redirections, and `errtrace` has no value without an error trap.
   A sourced preamble would also recreate a hand-maintained second source for
   the option policy.
6. **Shellcheck covers the live shell corpus.** The mechanically enumerated
   universe is every tracked, non-vendored `.sh` outside frozen archive paths,
   including template sources that generate future fleet scripts. The shebang
   chooses the shellcheck dialect. The sibling `livespec-dev-tooling` epic owns
   the initial severity floor or baseline and ratchet, but the shipped check
   must make new violations fail and must remain wired into the canonical
   aggregate. Frozen archive evidence is excluded from mutation, not silently
   treated as live code.

The enforcement must exercise its justfile parsing and command invocation from
the fleet's real zsh command environment, while shell scripts themselves run
under the interpreter named by their shebang.

## Resume command

First re-measure the epic through this repository's configured credential
wrapper; do not carry forward the reading below as current state:

```sh
cd /data/projects/livespec
/usr/local/bin/with-livespec-env.sh -- /usr/local/bin/bd show livespec-hhu5pn --json
```

Historical measurement: at `2026-08-02T22:50:02Z`, the epic was `backlog`, with
zero dependencies and zero dependents.

## Checkpoint transport and helper state

- Prior checkpoint PR `livespec` #1913 is merged; its branch and worktree were
  removed and the primary checkout was refreshed clean to `origin/master`.
- At `2026-08-02T23:12:32Z`, this checkpoint is carried on branch
  `docs/fleet-shell-checkpoint-1` in draft PR `livespec` #1914. Treat this as a
  timestamped transport record, not live forge state; the worker must verify the
  PR from the forge before acting on it.
- Two fresh-reader helpers have completed with PASS and changed no files.
  `handoff_cold_read` validated the first durable handoff; `checkpoint_cold_read`
  validated this refreshed checkpoint, including all six ordered read-first
  artifacts, exact resume commands, resolved design rules, Dispatcher/Fabro
  routing, and terminal verification requirements. No helper remains active.

## Exact next commands and operation selections

After this checkpoint PR merges and its worktree is cleaned up, run:

```sh
cd /data/projects/livespec
mise exec -- git fetch --prune origin
/usr/local/bin/with-livespec-env.sh -- /usr/local/bin/bd show livespec-hhu5pn --json
```

Then invoke these runtime skill selections in order:

```text
livespec:propose-change --spec-target SPECIFICATION/ --topic fleet-shell-discipline
livespec-orchestrator-beads-fabro:groom livespec-hhu5pn
```

The proposed change should add the six resolved rules above to
`SPECIFICATION/non-functional-requirements.md` without adding a new H2 heading
unless one is genuinely needed. If it changes an H2 set, co-edit
`tests/heading-coverage.json`. Before ratification, run the repository-mandated
independent adversarial proposal review; accept only a no-blockers result.

The groom draft should separate the human-gated spec ratification from local
factory-safe conformance work, keep each dispatchable description under the
factory sizing warning, and name the just interpolation construct without
reproducing its literal delimiter token. Before filing or dispatching each
child, verify against freshly fetched forge state that its acceptance is not
already delivered.

For each filed ready child, dispatch with the operation selection
`livespec-orchestrator-beads-fabro:drive --action impl:<child-id>`. Re-enumerate
after every outcome, wait for the journal's terminal `outcome` event, and verify
each acceptance-criterion clause independently against the merged forge state
and live behavior. Close and archive only after all clauses are evidenced.

## Repository discipline

Every tracked change uses a dedicated worktree, reviewed pull request, rebase
merge, primary refresh, and cleanup. Use `mise exec -- git` for git writes,
never pass `--no-verify`, and halt on a hook failure. Never touch another
session's worktree or branch and never kill the acting overseer daemon.
