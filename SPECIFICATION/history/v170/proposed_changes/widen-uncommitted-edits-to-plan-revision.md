---
proposal: widen-uncommitted-edits-to-plan.md
decision: accept
revised_at: 2026-07-20T00:51:10Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Accepted after an independent READ-ONLY adversarial Fable review returned NO BLOCKERS on the amended proposal (commit 63cb5d04). Round 1 found one blocker — the drift sweep failed inside the amended section itself, where contracts.md delegated committed-and-then-discovered violations to the `out-of-band-edits` check, a delegation that is false for the `plan/` half because that check compares committed spec state against `history/vNNN/` snapshots which capture only files under the spec root. The proposal was amended to scope the delegation per path class rather than waived. Round 2 verified all three replace-targets exist verbatim and exactly once, are non-overlapping, that the insertion anchor is unique, and that the new delegation text is factually correct against `out_of_band_edits.py` and `spec.md`. The widening is the maintainer's recorded decision (`plan/overseer-productization/handoff.md`, commit 2312b4e4) and is scoped in `plan/plan-thread-integrity/plan.md` (epic livespec-nr5h), where three larger mechanisms were considered and cut as disproportionate to a single rescued near-miss with no data loss. Severity stays `warn`, the default-branch-worktree scope is unchanged, and the slug is deliberately not renamed.

## Resulting Changes

- contracts.md
