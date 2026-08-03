# Fleet shell discipline — terminal handoff

This planning thread is complete and archived. Its ledger anchor,
`livespec-hhu5pn`, was verified `closed` at 2026-08-03T00:48:04Z with
clause-by-clause acceptance evidence. The ledger remains the status authority;
this file records the terminal evidence and does not create a shadow queue.

## Delivered outcome

The convention and enforcement design owned by `livespec` is ratified as
`SPECIFICATION/history/v187/`, merged by PR #1918 at `3fbe9fb0`. It defines:

- one tracked, non-vendored `.sh` universe outside frozen archives, including
  template sources, with shebang-selected ShellCheck dialect and complete
  mechanical coverage;
- dependency-only or one-line direct Just recipes, no embedded shell programs
  or Just interpolation, positional recipe arguments with quoted shell
  parameters, explicit exported environment names for global values, parsed
  Just JSON enforcement, and real-zsh fixtures;
- canonical Bash and POSIX-sh option profiles, adjacent rationale for every
  noncanonical profile, bounded errexit suspension with status capture before
  restoration, and opt-in rather than universal extra Bash settings;
- a tracked static check-target inventory, a one-line `just check` entry, a
  shared continue-on-failure runner supplied by `livespec-dev-tooling`, copier
  projection of static inventory data, and in-repo plus cross-repo
  wiring-completeness backstops; and
- five contributor-facing Gherkin scenarios covering accepted recipes,
  rejected embedded programs/interpolation, option profiles, bounded errexit,
  and template-source ShellCheck coverage.

The proposal was adversarially reviewed in three independent Fable rounds.
Eight blockers were resolved across the first two rounds; the third returned
`NO-BLOCKERS`. The production revise operation cut `v187`; pre-step and
post-step static doctor, the LLM objective and subjective review, doc-only
hooks, and PR CI were green.

## Boundary and ledger reconciliation

This epic owned what the rule is and how its enforcement is designed.
`livespec-dev-tooling` owns building and releasing the shared verifier,
choosing the ShellCheck acceptance floor, and rolling pins through the fleet.
Its original epic `livespec-dev-tooling-42t4az` was already regroomed into
replacement slices before this thread reached implementation grooming. That
groom created the existing core rollout item `livespec-akg7k5`, nonlocally
dependent on `livespec-dev-tooling-jtrjzk`.

No local factory slice was filed or dispatched from `livespec-hhu5pn`:
creating another core rollout item would have duplicated the sibling-owned live
queue and violated the ratified boundary. The epic therefore closed on the
fully delivered convention and enforcement-design outcome. Future readers must
query the sibling ledger for rollout status rather than infer it from this
archive.

## Corpus evidence

The forge-backed census at 2026-08-02T22:58Z measured nine repositories and
719 recipes: 106 Bash-shebang bodies, 120 multiline bodies, and 49 recipe
bodies using Just interpolation. It also found 49 tracked `.sh` files. Initial
option profiles were 36 canonical Bash `errexit`/`nounset`/`pipefail`, six
intentional failure aggregators without errexit, one POSIX nounset-only
wrapper, and six files with no initial `set`. These measurements drove the
profile-and-rationale design instead of a blanket errexit rule. Re-fetch forge
state before using the counts as current corpus data.

## Transport and cleanup record

- PR #1913 established the worker-owned handoff and passed a cold-open review.
- PR #1914 merged the fresh corpus/design checkpoint at `dfb9e8f1`; a second
  cold-open review passed.
- PR #1917 merged the reviewed proposal at `d7085393`.
- PR #1918 ratified history `v187` at `3fbe9fb0` with all CI checks green.
- The proposal and revise worktrees and local branches were removed after
  their merges, and the primary checkout was refreshed to `origin/master`.
- The archive transport uses branch `docs/archive-fleet-shell-discipline` in
  worktree `/home/ubuntu/.worktrees/livespec/docs/archive-fleet-shell-discipline`.
  Its PR number and merge commit are recorded by the forge and worker-status
  milestone when the archive merges; after merge this worktree and branch are
  removed and the primary checkout is refreshed clean.

The two cold-read helpers completed with PASS and changed no files. No helper,
factory dispatch, or plan-owned background process remains active.
