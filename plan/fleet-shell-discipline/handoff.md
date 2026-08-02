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

## Resume command

First re-measure the epic through this repository's configured credential
wrapper; do not carry forward the reading below as current state:

```sh
cd /data/projects/livespec
/usr/local/bin/with-livespec-env.sh -- /usr/local/bin/bd show livespec-hhu5pn --json
```

Historical measurement: at `2026-08-02T22:50:02Z`, the epic was `backlog`, with
zero dependencies and zero dependents.

## Next action

Re-measure the complete fleet corpus against freshly fetched forge state, then
finish the convention design. In particular, classify recipe bodies and tracked
shell scripts by actual behavior; define the allowed direct-invocation recipe
shape, the parameter-passing replacement for just interpolation, the default
Bash option profile, and the explicit declaration for justified deviations.
Before filing any child, prove its acceptance is not already delivered and keep
its description below the factory sizing warning. Name the just interpolation
construct in prose without reproducing its literal delimiter token.

After the convention is concrete and testable, groom epic `livespec-hhu5pn`
into dependency-layered slices, dispatch each ready factory-safe slice through
the `drive` operation, and verify every acceptance-criterion clause against the
merged forge state and live behavior before closure. Archive this directory only
after the epic is closed.

## Repository discipline

Every tracked change uses a dedicated worktree, reviewed pull request, rebase
merge, primary refresh, and cleanup. Use `mise exec -- git` for git writes,
never pass `--no-verify`, and halt on a hook failure. Never touch another
session's worktree or branch and never kill the acting overseer daemon.
