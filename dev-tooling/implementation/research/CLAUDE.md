# dev-tooling/implementation/research/

Vendored reference material from Open Brain documenting known
upstream `bd` (beads) problems and the workarounds the
sibling `setup-beads.sh` and `bd-doctor.sh` scripts apply.

Contents:

- `beads-problems.md` — living index of `bd` upstream issues
  encountered during real-world use. Each entry pairs a problem
  with the upstream issue / PR (when filed), the local workaround,
  and a status that gets updated as upstream progresses. Vendored
  verbatim from Open Brain's `research/beads-problems.md`; only a
  preface note was added explaining the provenance and the fact
  that Open Brain-specific issue ids (`ob-*`) are historical
  artifacts preserved for upstream-citation continuity.

Why this lives here rather than in the spec:
`SPECIFICATION/non-functional-requirements.md` §Constraints
§"Beads invariants" #5 names this document as the canonical
reference and explicitly defers mechanism details (recovery
paths, lock-file semantics, etc.) to it. Per the
architecture-vs-mechanism discipline, spec defines the
invariants those workarounds must satisfy; the workaround prose
itself lives here.
