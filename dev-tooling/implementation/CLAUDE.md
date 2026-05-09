# dev-tooling/implementation/

Mechanism scripts and supporting reference material for the
repo-local `livespec-implementation` workflow. These are NOT part
of the shipped `livespec` plugin (which lives under
`.claude-plugin/`); they are dogfooding-only tooling for the
project-local plugin at `.claude/plugins/livespec-implementation/`.

Contents:

- `setup-beads.sh` — idempotent bootstrap for `bd` (beads) on
  this clone. Creates the `.beads/` embedded Dolt database, chains
  beads hooks behind lefthook, asserts required bd config keys.
  Adapted from Open Brain's `scripts/setup-beads.sh`.
- `bd-doctor.sh` — health-checks the beads installation per the
  embedded-mode invariants `bd doctor` does not cover. Adapted
  from Open Brain's `scripts/bd-doctor.sh`.
- `research/` — vendored upstream-issue references documenting
  known `bd` upstream problems and the workarounds these scripts
  apply.

Spec authority:
`SPECIFICATION/non-functional-requirements.md` §Contracts
§"Implementation justfile namespace" defines the architectural
invariants every script here must satisfy. §Constraints §"Beads
invariants" codifies the five rules (li- prefix, Dolt
source-of-truth, noninteractive-only `bd`, gap-id ↔ label
exactly-once, hook chaining + setup invariants).

Invocation: every entry point is exposed through `just
implementation::<recipe>` (see `implementation.just` at the repo
root). Direct invocation of these scripts works but is discouraged
— prefer the just recipe so any future preconditions live in one
place.
