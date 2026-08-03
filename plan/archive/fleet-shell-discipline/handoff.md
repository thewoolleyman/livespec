# Fleet shell discipline — terminal handoff

This planning thread is complete and archived. Its ledger anchor,
`livespec-hhu5pn`, was verified `closed` at 2026-08-03T00:48:04Z with
clause-by-clause acceptance evidence; a post-closure note now records the
maintainer-authorized v188 corrections. The ledger remains the status
authority; this file records the terminal evidence and does not create a shadow
queue.

## Delivered outcome

The convention and enforcement design owned by `livespec` is finally ratified
as `SPECIFICATION/history/v188/`, merged by PR #1926 at `dfa26280`. The original
design landed as v187 in PR #1918 at `3fbe9fb0`; v188 preserves that design and
closes two post-ratification ambiguities. The resulting policy defines:

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
  wiring-completeness backstops;
- `Shell-and-Justfile-discipline` as an explicit `baseline` concern binding
  every fleet repository and extending to opted-in adopters whose `posture` is
  `released`;
- CI matrix completeness against the tracked static check-target inventory
  reached by the one-line `just check` recipe, never an inventory inferred from
  the recipe body, while independently preserving gate-job `needs:` coverage;
  and
- five contributor-facing Gherkin scenarios covering accepted recipes,
  rejected embedded programs/interpolation, option profiles, bounded errexit,
  and template-source ShellCheck coverage.

The v187 proposal was adversarially reviewed in three independent Fable rounds:
eight blockers were resolved across the first two rounds and the third returned
`NO-BLOCKERS`. The v188 correction proposal merged separately in PR #1923 at
`b43ff5fa` after an exact-blob Fable review also returned `NO-BLOCKERS`. Both
production revise passes ran their post-step static doctor; their LLM objective
and subjective reviews, doc-only hooks, full PR matrices, and `ci-green` gates
were green. The v188 `capture-impl-gaps --since-version v187` pass surfaced 249
candidates because the detector scopes at changed-file granularity and the NFR
file contains that many BCP14 rules; no duplicate gap-tied item was filed
without the required per-gap consent.

## Boundary and ledger reconciliation

This epic owned what the rule is and how its enforcement is designed.
`livespec-dev-tooling` owns building and releasing the shared verifier,
choosing the ShellCheck acceptance floor, and rolling pins through the fleet.
Its original epic `livespec-dev-tooling-42t4az` was already regroomed into
replacement slices before this thread reached implementation grooming. That
groom created `livespec-dev-tooling-mvvr3f` for the convention verifier and the
existing core rollout item `livespec-akg7k5`, which is nonlocally dependent on
the sibling release/fan-out item `livespec-dev-tooling-jtrjzk`.

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
- PR #1921 archived the planning thread at `726b0bca`; its full matrix,
  `ci-green`, and the subsequent master run `30776062372` were successful.
- PR #1923 merged the independently reviewed correction proposal at
  `b43ff5fa`; PR #1926 ratified history `v188` at `dfa26280` with all CI checks
  green.
- Every worker-owned proposal, revise, and archive worktree and local branch
  named above was removed after merge, and the primary checkout was refreshed
  clean to `origin/master`. PR #1928 transports this v188 evidence refresh from
  branch `docs/fleet-shell-discipline-v188-evidence`; its forge record is
  authoritative for merge metadata, and no branch or PR is treated as plan
  state.

The two cold-read helpers completed with PASS and changed no files. No helper,
factory dispatch, or plan-owned background process remains active.
