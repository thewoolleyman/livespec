# history

Versioned snapshots of the (pre-seed) `PROPOSAL.md` plus every proposed
change and revision that produced each version. This directory is
backfilled by hand to mirror what `livespec`'s own `history/`
mechanism would have produced if it had existed at the time these
revisions were made.

## Filename convention

Two filename conventions appear here, reflecting a rule change in
v003. The v003 revision dropped the `vNNN-` prefix from files inside
`history/vNNN/` to preserve relative markdown links under the parallel
`proposed_changes/` subdirectory structure. Historic v001 and v002
entries keep their original naming (immutable history).

**v001 and v002 (legacy naming, retained unchanged):**

- `vNNN/vNNN-PROPOSAL.md` — frozen copy of the working proposal.
- `vNNN/vNNN-proposed-change-<topic>.md` — a proposed change
  processed by the revise that cut this version.
- `vNNN/vNNN-proposed-change-<topic>-acknowledgement.md` — the
  paired decision record. (The term `acknowledgement` was renamed
  to `revision` in v003.)

**v003 and later (current naming):**

- `vNNN/PROPOSAL.md` — frozen copy of the working proposal.
- `vNNN/proposed_changes/<topic>.md` — a proposed change processed
  by the revise that cut this version.
- `vNNN/proposed_changes/<topic>-revision.md` — the paired
  revision decision record.
- Additional reference artifacts (pre-interview drafts, notes) MAY
  appear in `vNNN/proposed_changes/` with descriptive suffixes.

## Versions

- **v001** — initial proposal (commit `abba068`), seeded by hand
  before `livespec` existed. No proposed-change files; the `seed`
  step itself is not represented as a proposal under the model.
- **v002** — revise driven by `v002-proposed-change-proposal-
  critique-v01.md` and its acknowledgement, plus several follow-on
  in-conversation corrections that were absorbed into v002 rather
  than filed as separate proposals (gherkin-format change, holdout
  removal, doctor-warning removal, progressive-disclosure removal,
  filename rename `livespec-nlspec-guidelines.md` →
  `livespec-nlspec-spec.md`, etc.).
- **v003** — revise driven by
  `proposed_changes/proposal-critique-v02.md` and its revision.
  Restructures the proposal around: plugin packaging (not skill
  alone), Option 3 template architecture with custom templates in
  v1 scope, multi-proposal file format, rename
  `acknowledgement` → `revision`, rename `<freeform text>` →
  `<intent>` / `<revision-steering-intent>`, drop of `partition`
  term in favor of `specification file`, drop of `vNNN-` prefix
  inside history directories in favor of a parallel subdir layout,
  new `prune-history` sub-command with `PRUNED_HISTORY.json`
  marker, `jq` hard dependency, static-phase JSON output contract,
  objective/subjective split of doctor's LLM-driven phase with
  skip config and CLI flag, auto-backfill on check #9 drift
  detection, drop of `openspec` reservation, drop of
  `custom_critique_prompt` and `specification_dir` from
  `.livespec.jsonc`, and more. Full decision record is in
  `v003/proposed_changes/proposal-critique-v02-revision.md`.
- **v004** — revise driven by
  `proposed_changes/proposal-critique-v03.md` and its revision.
  Mid-interview, the user rewrote
  `bash-skill-script-style-requirements.md` to add module
  structure, purity/I/O isolation, complexity thresholds,
  testability, coverage, and architectural checks; four
  additional critique items (G22-G26) were appended to cover
  gaps between the rewritten style doc and PROPOSAL.md.
  Major structural changes: `schemas/` added to skill layout;
  `livespec-nlspec-spec.md` canonicalized at template root
  only; executables renamed (`dispatch`, `doctor-static` with
  no `.sh`); `scripts/bash-boilerplate.sh` added; `scripts/ci/`
  renamed to `scripts/checks/` in both PROPOSAL.md and the
  bash style doc; `prompts/propose-change.md` promoted to
  REQUIRED; `critique` uses internal delegation to
  `propose-change`; check #9 compares committed state
  (`git show HEAD:`) rather than working tree; doctor
  static-phase exit codes aligned to bash style doc (0/1/3);
  `plugin.json` delegated to Claude Code's current format;
  check #13 collapsed into #2 (now 12 static checks);
  `prune-history` preserves original-earliest across repeat
  prunes; `propose-change` drops content-shape sniffing in
  favor of `--findings-json` flag; `revise` orders files by
  `created_at` with whole-revise delegation scope;
  `<revision-steering-intent>` now forbids content injection;
  Testing section consolidated to name `bats-assert`,
  `bats-support`, `kcov` with coverage thresholds, and the
  `tests/` skeleton tree. Full decision record is in
  `v004/proposed_changes/proposal-critique-v03-revision.md`.

## Pointer

The current working `PROPOSAL.md` lives at the parent directory
(`brainstorming/approach-2-nlspec-based/PROPOSAL.md`). It is
byte-identical to `history/v004/PROPOSAL.md` until the next revise.
