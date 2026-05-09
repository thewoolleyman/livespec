# research/beads/

Working catalogue of `bd` (gastownhall/beads) workarounds the
livespec implementation layer carries, framed for upstream
issue-filing rather than internal documentation. The goal is a
living index: each entry can be lifted directly into an upstream
GitHub issue, and entries get retired when upstream lands the
corresponding fix and we drop the workaround.

## What lives here

- `beads-gaps-workarounds.md` — the catalogue itself. Numbered
  entries with Observation / Current workaround / Proposed
  upstream change / Status; plus inherited entries cross-linked
  to the foundational vendored catalogue at
  `dev-tooling/implementation/research/beads-problems.md`.

Future docs in this directory might cover other beads-related
research: usage patterns we've found valuable, tradeoffs in
beads' Dolt-vs-JSONL sync model, comparisons with alternatives,
etc. Each gets one file; lifecycle stays per-doc.

## What this directory is NOT

- **Not the foundational catalogue.** That lives at
  `dev-tooling/implementation/research/beads-problems.md`,
  vendored from Open Brain. This directory complements it with
  livespec-specific findings; it does not replace or supersede.
- **Not load-bearing spec content.** Files here describe
  workarounds we're carrying — they are not requirements. Any
  finding that matures into "livespec MUST do X about beads"
  flows through `/livespec:propose-change` →
  `/livespec:revise` to land in
  `SPECIFICATION/non-functional-requirements.md`.
- **Not implementation prose.** The workarounds themselves live
  in code (`dev-tooling/implementation/setup-beads.sh`,
  `bd-doctor.sh`, plus the managed hook templates). This
  directory documents *why* those workarounds exist and what
  upstream changes would obviate them.

## Lifecycle

When an upstream beads change lands that addresses a workaround:

1. Update the entry's **Status / pointers** section in
   `beads-gaps-workarounds.md` with the released bd version and
   the issue / PR pointer.
2. Remove the workaround from `setup-beads.sh` /
   `bd-doctor.sh` / hook templates in a paired commit.
3. Mark the entry retired (or delete it from the catalogue) once
   the workaround removal has shipped.
