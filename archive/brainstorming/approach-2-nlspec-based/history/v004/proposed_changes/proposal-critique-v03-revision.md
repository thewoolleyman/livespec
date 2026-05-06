---
proposal: proposal-critique-v03.md
decision: modify
revised_at: 2026-04-22T00:00:00Z
reviser_human: thewoolleyman
reviser_llm: Claude Opus 4.7 (1M context)
---

# Revision: proposal-critique-v03

## Provenance

- **Proposed change:** `proposal-critique-v03.md` (in this directory)
- **Revised by:** thewoolleyman (human) in dialogue with Claude Opus 4.7
  (1M context)
- **Revised at:** 2026-04-22 (UTC)
- **Scope:** v003 PROPOSAL.md → v004 PROPOSAL.md

## Summary of dispositions

| Severity | Count | Accepted | Modified-on-accept | Deferred | Rejected |
|---|---|---|---|---|---|
| Major (blocks seeding) | 8 | 6 | 2 | 0 | 0 |
| Significant | 6 | 3 | 3 | 0 | 0 |
| Smaller / cleanup | 7 | 7 | 0 | 0 | 0 |
| Added mid-interview (from bash-style-doc rewrite) | 4 | 3 | 1 | 0 | 0 |

Mid-interview additions: G22, G23, G25, G26 were added to the critique
file after the user rewrote
`bash-skill-script-style-requirements.md` during the interview,
surfacing gaps between PROPOSAL.md and the updated style doc. The
critique file was updated in-place to include these items.

---

## Disposition by item

### Major gaps

**M1. `schemas/` directory missing from skill layout.**
Decision: **Accepted.** Add `schemas/` to the skill-layout tree
with `critique-findings.json` as a representative file. Additional
schemas are authored as a post-seed `propose-change`.

**M2. `livespec-nlspec-spec.md` location contradiction.**
Decision: **Accepted.** Canonicalize on template-root. Remove the
skill-root layout entry; fix the `prompts/` typo in §"Built-in
template: `livespec`" to "at its root". Single-location model:
present at template root only; used for prompt-context injection.

**M3. Sub-command dispatch script unnamed.**
Decision: **Modified-on-accept.**
Two-script model retained (dispatch + doctor-static). Names updated
to conform to bash-style-doc's "no `.sh` extension on executables"
rule: `scripts/dispatch` and `scripts/doctor-static` (both
executables lose the `.sh` suffix). Dispatcher contract: tokenizes
`$@`, emits resolved sub-command + remaining positional args on
stdout, exits nonzero with diagnostic on invalid invocation.

**M4. Bundled-default propose-change prompt location.**
Decision: **Accepted.** Promote `prompts/propose-change.md` to
REQUIRED in the template layout, same tier as seed/revise/critique.
Drop "bundled default" fallback language. Templates without the
prompt fail doctor check #2.

**M5. `critique` → `propose-change` invocation mode.**
Decision: **Accepted.** Internal delegation (not sub-command
re-invocation). `critique` calls `propose-change`'s file-write
logic directly, bypassing the dispatcher. Pre/post doctor runs
once (outer `critique` only). Add a one-sentence carve-out to
§"livespec skill sub-commands" stating that internal delegation
between sub-commands does not re-trigger doctor.

**M6. `shared/` directory contents truncated.**
Decision: **Accepted.** Collapse to prose. Layout shows
`shared/` with no enumerated members; prose states membership is
an implementation concern driven by DRY needs during command
authoring.

**M7. Pre-step doctor auto-backfill blast radius.**
Decision: **Modified-on-accept** (two-part resolution).

- **M7a (comparison target):** Doctor check #9 compares **committed
  state** (`git show HEAD:SPECIFICATION/*`) to `history/vN/`, not
  the working tree. Cleaner invariant: WIP in the working tree is
  always the user's in-flight work; committed state is what
  corresponds to history. Non-git projects: skip check #9 entirely
  (no committed state to compare). Fixes the case where uncommitted
  WIP + previously-committed out-of-band drift would previously skip
  detection.
- **M7b (handling):** Auto-backfill retained in pre-step. On
  detection: auto-create proposed-change + revision under
  machine-generated topic (`out-of-band-edit-<UTC-seconds>`), write
  `history/v(N+1)/` with current spec content, move the backfill
  inside it, exit nonzero with finding instructing the user to
  commit and re-run the original command.

**M8. Doctor exit codes conflict with bash style doc.**
Decision: **Accepted.** Update PROPOSAL.md static-phase exit codes
to match the bash-style-doc's POSIX-ish convention:
- `0`: all checks pass; LLM-driven phase MAY proceed.
- `1`: script-internal failure (bug in `doctor-static`).
- `3`: at least one check failed; LLM-driven phase MUST NOT run;
  the invoking sub-command MUST abort.

### Significant gaps

**S9. `plugin.json` schema undefined.**
Decision: **Accepted.** Delegate to Claude Code's current plugin
format. Implementer follows Claude Code's current plugin-format
documentation at build time; livespec itself does not validate
`plugin.json`. PROPOSAL.md states this explicitly.

**S10. Check #13 redundant with check #2.**
Decision: **Accepted.** Delete check #13. Fold its diagnostics
requirement ("name the offending field, its value, and the path to
`.livespec.jsonc`") into check #2. Update DoD item 6 from "13
checks" to "12 checks".

**S11. `prune-history` `first` semantics on repeat prunes.**
Decision: **Accepted.** Before deleting an existing
`PRUNED_HISTORY.json` marker, `prune-history` reads its
`pruned_range[0]` and carries it forward as the new `first`. If no
prior marker exists, `first` is the earliest v-directory version
number found in `history/`. Preserves original-earliest info
across successive prunes.

**S12. Testing implementation language not pinned.**
Decision: **Modified-on-accept.** Merge S12 + G25 + G26 + C18
into a single consolidated §"Testing approach" rewrite (see G25
and G26 entries below for full tooling and directory details).
This supersedes the "language not pinned" stance.

**S13. `propose-change` input-shape discrimination.**
Decision: **Modified-on-accept.** Drop shape-sniffing entirely.
`propose-change <topic> <intent>` always treats `<intent>` as raw
text. External programmatic callers use a `--findings-json <path>`
flag for structured JSON input. `critique`'s path uses internal
delegation (per M5), which bypasses the CLI entirely and hands
findings directly to `propose-change`'s logic. Cleaner contract;
no content-sniffing edge cases.

**S14. `revise` file and proposal ordering.**
Decision: **Modified-on-accept.** Files in `proposed_changes/`
are processed in **creation-time order** by YAML front-matter
`created_at` (oldest first), with **lexicographic filename** as
fallback on tie. Within each file, `## Proposal` sections are
processed in document order. The delegation toggle, once set,
applies to **all remaining proposals across files** (whole-revise
scope), not just the current file.

### Smaller issues

**C15. Duplicate "no open questions" rule.**
Decision: **Accepted.** Delete the duplicate from
§"propose-change". Retain the statement in §"Proposed-change file
format".

**C16. `seed` idempotency edge cases.**
Decision: **Accepted.** `.livespec.jsonc` is NOT a
template-declared target file. `seed` creates it only if absent;
validates and reuses if present. Template-declared targets are
files under the template's `specification-template/`. Any target
file's existence (including partial states) → refusal with a list
of the offending files.

**C17. `history/vNNN/README.md` semantics.**
Decision: **Accepted.** Tighten inline annotations on the tree to
distinguish skill-owned `history/README.md` from the per-version
`history/vNNN/README.md` (archived user-content copy).

**C18. `<project-root>/tests/` location clarification.**
Decision: **Accepted** (merged into the Testing section rewrite
from S12/G25/G26). PROPOSAL.md specifies: "Tests for the
`livespec` skill live at the skill-repo root under `tests/` (a
sibling of `.claude-plugin/`). Tests of a user's own
SPECIFICATION are out of scope for livespec."

**C19. `<revision-steering-intent>` content injection.**
Decision: **Accepted.** Tighten §"revise":
`<revision-steering-intent>` MUST NOT contain new spec content.
It MUST only steer per-proposal decisions. On detected content
injection, skill warns and directs the user to run
`propose-change` first. Resolves latent conflict with the "no
other ingress paths" invariant in §"Template-agnostic principles".

**C20. Section-drift meta-test naming.**
Decision: **Accepted.** Update DoD item 10 from
"`section_drift_prevention`" to
"`test_meta_section_drift_prevention.bats`" to match §"Testing
approach".

**C21. Pre-step skip warning channel.**
Decision: **Accepted.** Skill-level warning is surfaced via LLM
narration. Bash layer emits a structured JSON finding
(`status: "skipped"`, descriptive message). LLM reads the finding
and narrates to the user. Bash MUST NOT print the warning to
stdout (reserved for findings) or as raw stderr text (LLM is the
proper channel for user-facing warnings).

### Added mid-interview (from bash-style-doc rewrite)

During the interview, the user rewrote
`bash-skill-script-style-requirements.md` to add module-structure,
purity/I/O, complexity thresholds, testability, coverage, and
architectural-check sections. That surfaced four additional gaps
between the updated style doc and PROPOSAL.md, which were appended
to the critique file and interviewed.

**G22. `scripts/bash-boilerplate.sh` missing from skill layout.**
Decision: **Accepted.** Add `scripts/bash-boilerplate.sh` to the
skill-layout tree. Discussed alternative of per-script
copy-paste + CI-verified uniformity; concluded the shared
boilerplate is appropriate given the skill's bundle discipline and
small script count. The claimed "source-path fragility" of
`${BASH_SOURCE[0]}`+`realpath` was examined in detail and
retracted — the sourcing mechanism is robust and author errors
are caught loudly on first run.

**G23. `scripts/ci/` directory misnamed.**
Decision: **Modified-on-accept.** Rename the directory from
`scripts/ci/` to `scripts/checks/` in both PROPOSAL.md and the
bash-skill-script-style-requirements.md. The architectural checks
run in both git pre-commit hooks and CI, so `ci` was a misnomer;
`checks` is accurate for both invocation surfaces.

**G25. Strengthen Testing section with bats-assert + kcov.**
Decision: **Accepted** (merged into the consolidated Testing
rewrite from S12/G26/C18). PROPOSAL.md names all tooling:
`bats-core` + `bats-assert` (with `bats-support`), `.bats`
extension, fixtures under `tests/fixtures/`, test-local state
under `BATS_TEST_TMPDIR`, coverage measured by `kcov` with 100%
pure / ≥80% overall thresholds. Full contract lives in the
companion bash style doc.

**G26. `tests/` directory structure in PROPOSAL.md.**
Decision: **Accepted** (merged into the consolidated Testing
rewrite). Add a `tests/` skeleton tree to §"Testing approach":

```
tests/
├── CLAUDE.md
├── heading-coverage.json
├── fixtures/
├── scripts/
│   ├── dispatch.bats
│   └── doctor-static.bats
└── test_*.bats
```

---

## Self-consistency check

Post-revision invariants rechecked (per the embedded guidelines):

- **Two-implementer test:** renamed scripts (dispatch,
  doctor-static) match the bash style doc's extension rule;
  schemas/ and scripts/bash-boilerplate.sh now declared in the
  layout; JSON-schema-enforced skill↔template layer remains
  intact.
- **Recreatability:** with v004, a competent implementer can
  generate the livespec plugin, built-in template, sub-commands,
  and all enforcement machinery from PROPOSAL.md +
  `livespec-nlspec-spec.md` +
  `bash-skill-script-style-requirements.md` alone.
- **Define-once:** the duplicate "no open questions" rule is
  removed; check #13 is collapsed into check #2; the
  `livespec-nlspec-spec.md` location is canonical; testing tooling
  lives in one consolidated section.
- **Definition of Done:** updated for revised check count (12
  instead of 13) and canonical meta-test name.

## Outstanding follow-ups

Filed as the first batch of `propose-change`s after `seed`:

- Detailed authoring of each template prompt's input/output JSON
  schemas and prompts themselves (`prompts/seed.md`,
  `prompts/revise.md`, `prompts/critique.md`,
  `prompts/propose-change.md`).
- Migration of brainstorming-folder companion documents
  (`subdomains-and-unsolved-routing.md`, `prior-art.md`,
  `bash-skill-script-style-requirements.md` etc.) into the seeded
  `SPECIFICATION/` at their appropriate destinations.
- Authoring of the specific architectural-check scripts under
  `scripts/checks/` (now renamed from `scripts/ci/`).

## What was rejected

Nothing was rejected outright. Two classes of reshape occurred:

- Several "Accept as proposed" items from the critique were
  merged into consolidated rewrites during application (S12/G25/
  G26/C18 → one Testing section; M7a/M7b → two parts of one
  §"Pre-step auto-backfill" resolution).
- My claimed "source-path fragility" as a reason to avoid the
  shared boilerplate was rejected on cross-examination; the
  shared pattern is coherent and the critique author's
  counter-recommendation did not hold up.
