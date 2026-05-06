---
proposal: ci-discipline
version_target: v041
filed_at: 2026-05-06T07:09:52Z
author_human: thewoolleyman@gmail.com
author_llm: claude-opus-4-7
---

# Proposal: ci-discipline

## Background

User-initiated 2026-05-06T06:00:00Z. The Phase 7 → 8 transition surfaced three compounding drift modes that were silently inherited across multiple sessions:

1. **CI / branch-protection drift.** v039 D1 dropped `check-tests` from `.github/workflows/ci.yml`'s matrix (the canonical aggregate stopped including it because pytest-cov runs pytest as a side effect, making the standalone target redundant). The branch-protection required-checks list on master was NOT updated in lockstep. PR #4 (Phase 7) was BLOCKED because the required check `check-tests` could not report — it was no longer wired into CI. The drift sat invisible across PRs #1, #2, #3 (each merged onto already-red master) and was discovered only when PR #4 hit BLOCKED at the Phase 7 → 8 boundary.

2. **Silent-red master.** Master CI had been failing on `check-types`, `check-prompts`, and `e2e-test-claude-code-mock` since Phase 5 — these jobs were documented as "deferred until Phase 5/9 fix-cycles" in the `justfile` aggregate's comment, and that documentation was treated by every subsequent session as a license to leave master red. Each PR merge inherited the red state. The pattern hid genuine regressions in those deferred jobs (no signal when something else broke) and burned trust in CI as a load-bearing gate.

3. **PR cross-phase accumulation.** The Phase 7 → 8 advance commit landed on `phase-7-widen-sub-commands` without merging PR #4 or cutting a fresh `phase-8-*` branch. The next session inherited the prior session's "PR #4 stays in draft" framing and added 16 more commits (Phase 8 item 1 closure + item 2 cycles 1-4) on top, growing PR #4 to 175 commits across two phases. The user surfaced this only when asking "why are we still on PR #4?"

The root cause is the same in all three: the agent inherits prior-session state without checking whether it makes sense. Memory entries advising "be more careful" are not load-bearing because they require every future agent to read the right entry at the right moment. The fix has to be mechanical — guards that fire automatically (Layer 1), session-start sanity checks the bootstrap-skill always runs (Layer 2), and a phase-advance protocol the skill walks the user through step-by-step (Layer 3).

This codification (Layer 4) names the architectural rule that the three implementation layers enforce. Without the rule in PROPOSAL.md, future maintainers refactoring or trimming the guards have no governance reference for why they exist; the rule is the durable contract.

## Decisions

### D1 — CI / branch-protection discipline (hard constraint)

PROPOSAL.md §"Developer tooling layout" gains a new sub-section `### CI / branch-protection discipline (v041 D1)` codifying three contracts:

> ### CI / branch-protection discipline (v041 D1)
>
> Three rules govern the relationship between the CI workflow at `.github/workflows/ci.yml`, the master-branch protection's required-checks list, and the master CI conclusion at any commit:
>
> 1. **No permanent-red CI jobs.** No job in `.github/workflows/*.yml` MAY be configured to run while documented as failing-and-deferred. A job MUST be either (a) repaired in the same commit that breaks it, or (b) removed from the workflow until repaired. "Deferred until Phase X" is not a permitted CI state — the comment in `justfile`'s aggregate stating a target is deferred and the matrix line that runs the same target as red MUST NOT coexist. When a deferred job is later repaired, it re-joins the matrix in the same commit that fixes its underlying issue.
>
> 2. **CI matrix and branch-protection required-checks list MUST agree.** The set of required checks on master branch protection MUST equal the set of jobs in `.github/workflows/ci.yml`'s `matrix.target`, modulo workflows explicitly marked optional (e.g., the `e2e-real.yml` real-Claude harness, which is a manually-triggered release-gate workflow). Drift between the two — a required check that is not in the matrix, or a matrix entry that is not required — produces the v039 D1 / `check-tests` failure mode where GitHub blocks merges on a missing-not-failing required check.
>
> 3. **Master CI is green at every commit.** No commit MAY land on a phase-N branch when master CI is red on its most recent run. "Master red" includes failed required checks AND failed non-required-but-running jobs — the rule covers every job the workflow is configured to run, since rule 1 already removes deferred jobs.
>
> Mechanical enforcement (Guard Layer 1):
>
> - `dev-tooling/checks/branch_protection_alignment.py` reads `.github/workflows/ci.yml`'s `matrix.target` list, fetches master branch protection's `required_status_checks.contexts` via `gh api`, and fails on any required-but-missing-from-ci.yml entry. ci.yml-but-not-required entries emit informational warnings (some workflows are intentionally optional).
>
> - `dev-tooling/checks/master_ci_green.py` fetches the most recent master CI run via `gh run list --branch master --limit 1 --workflow CI` and fails on conclusion `failure`, `cancelled`, `timed_out`, `action_required`, `stale`, or `startup_failure`. Pending statuses (`queued`, `in_progress`, `waiting`, `pending`, `requested`) are treated as non-blocking — CI may not have caught up to a fresh master push yet.
>
> Both checks gracefully exit 0 with a structured warning when `gh` is unavailable or unauthenticated locally so per-commit pre-commit runs are not blocked; CI with `GH_TOKEN` exercises the full enforcement path. Both are wired into the `just check` aggregate as `check-branch-protection-alignment` and `check-master-ci-green`.
>
> Skill-side enforcement (Guard Layer 2): `bootstrap/.claude-plugin/skills/bootstrap/SKILL.md` step 1 sub-step 6 runs three session-start sanity checks before any work begins — branch ↔ STATUS phase alignment, master CI green, active-PR mergeability. Drift detected here halts the session via the "Report an issue first" gate before the agent burns time writing on a broken base.
>
> Phase-advance enforcement (Guard Layer 3): `SKILL.md` §5d encodes phase advancement as a 4-step transaction (verify prior-phase PR merged, verify master CI green, cut fresh `phase-(N+1)-*` branch from master HEAD, land STATUS commit on new branch). Skipping any step produces the cross-phase-PR drift that grew PR #4 to 175 commits.
>
> The three contracts above are NOT post-Phase-6 SPECIFICATION/ work — they govern the bootstrap-process scaffolding itself. The Layer 1 mechanical checks live in `dev-tooling/checks/` and survive into the production livespec plugin's enforcement suite. The skill-side enforcement (Layers 2-3) lives in the throwaway bootstrap skill and disappears at Phase 11 cleanup; future production-plugin sessions don't need the equivalents because the production plugin doesn't have a phase-advance lifecycle.

### D2 — plan-text + housekeeping

Plan-level edits paired with D1:

- §"Version basis" preamble at the top of `PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` gains a new bullet for v041:
  - `v041 D1 (PROPOSAL.md): codify CI / branch-protection discipline as a sub-section under §"Developer tooling layout". Three rules: no permanent-red CI jobs; CI matrix and branch-protection required-checks list MUST agree; master CI green at every commit. Layer-1 mechanical enforcement via `branch_protection_alignment.py` + `master_ci_green.py`; skill-side enforcement via SKILL.md steps 1.6 and 5d.`
  - `v041 D2 (plan-level): plan-text + housekeeping. Phase 0 step 1 byte-identity reference bumps to history/v041/PROPOSAL.md. Phase 0 step 2 frozen-status header literal bumps to "Frozen at v041". Execution-prompt block authoritative-version line bumps to v041. STATUS.md updated.`
- §"Developer tooling layout" enumeration of dev-tooling/checks/ scripts gains two new entries: `branch_protection_alignment.py` and `master_ci_green.py` (both v041 D1).
- Phase 0 step 1 byte-identity reference bumps to `history/v041/PROPOSAL.md`.
- Phase 0 step 2 frozen-status header literal bumps to "Frozen at v041".
- Execution-prompt block authoritative-version line bumps to v041.

## Implementation impact

- **Already landed.** Layer 1 mechanical checks (PR #6, sha `f3812121`): `dev-tooling/checks/branch_protection_alignment.py` + `master_ci_green.py` + paired tests + justfile wiring + just-check aggregate inclusion. Layers 2 + 3 in the same PR: SKILL.md step 1 sub-step 6 + §5d rewrite. Plus prep cleanup (PR #5, sha `05c4f10`): drop `check-types`, `check-prompts`, `e2e-test-claude-code-mock` from ci.yml matrix; remove stale `check-tests` from master branch-protection required-checks list.
- **This codification.** PROPOSAL.md gains the §"CI / branch-protection discipline (v041 D1)" sub-section. Plan v-pointers bump to v041. v041/ snapshot lands. No further implementation impact — the layers are already in place; this is the durable governance reference they enforce.
- **Future SPECIFICATION migration.** Phase 8 item 7 (`static-check-semantics`) will eventually carry a propose-change cycle migrating the v041 D1 contracts into `SPECIFICATION/constraints.md` (or a dedicated SPECIFICATION/ governance file), at which point the PROPOSAL section becomes reference-only per the post-Phase-6 dogfooding contract. Until then, PROPOSAL.md remains the authoritative source for the contracts.

## What was considered and rejected

### Rejected: per-line `# pragma: no cover` for CI-only branches

The two new check scripts have branches that only exercise in CI (where `gh` is authenticated with admin scope). Locally `shutil.which("gh")` may return None and the branch short-circuits with a graceful skip. To get 100% coverage, the alternative was per-line `# pragma: no cover` annotations on the gh-available branches.

Rejected because PROPOSAL.md §"Code coverage" (v031 D1) constrains the structural-exclusion set to four specific patterns (`if TYPE_CHECKING:`, `raise NotImplementedError`, `@overload`, `case _:`). Per-line pragma is a different mechanism (`coverage.py`'s line-level skip) and is outside the codified exclusion set. The implemented approach instead uses fake `gh` shell stubs at `tmp_path/bin/gh` to exercise both branches under test, achieving 100% coverage without expanding the exclusion set.

### Rejected: codify in SPECIFICATION/ directly without a PROPOSAL halt-and-revise

Layer 4's PROPOSAL codification could in principle skip the halt-and-revise step and go straight to a Phase 8 propose-change against `SPECIFICATION/`. This would produce a single propose-change cycle landing the rule in SPECIFICATION/constraints.md.

Rejected because the architectural rule precedes the SPECIFICATION/ migration. PROPOSAL.md is the brainstorming-source-of-truth for architectural decisions; SPECIFICATION/ is the post-Phase-6 working copy. New architectural rules should be codified in PROPOSAL first (so the rationale lands alongside the decision history) and then migrated to SPECIFICATION as a separate cycle. This matches the v039 / v040 pattern: D1 codification in PROPOSAL.md, with SPECIFICATION migration deferred to a future Phase 8 cycle.

### Rejected: bundle Layer 4 with the Layer 1+2+3 implementation PR

Could have been a single PR landing the implementation AND the PROPOSAL codification. Rejected because the per-PR scope discipline (the principle the user emphasized after PR #4 grew to 175 commits across two phases) calls for separable scopes. Layer 1+2+3 is implementation; Layer 4 is governance. They merge to master independently; if one is rejected the other can stand alone.

## Provenance

- v041 codification triggered by user direction 2026-05-06T05:50:00Z after the Phase 7 → 8 PR-merge investigation surfaced three compounding drift modes simultaneously. User asked: "Looks like you shouldn't have made a giant PR, huh? And why were you ignoring the broken master?" The follow-up was: "First I want you to propose the changes so these mistakes won't ever happen again." This codification documents the rules; PR #6 lands the implementation.
- Implementation-PR provenance: PR #5 (`chore: drop deferred-and-failing jobs from .github/workflows/ci.yml`, sha `05c4f10`) unblocked master; PR #4 (`phase-7: widen sub-commands to feature parity + phase-8 item 1 + item 2 cycles 1-4`, sha `26c5168`) merged the accumulated Phase 7+8 work; PR #6 (`chore: guard layers 1+2+3`, sha `f3812121`) landed the mechanical + skill-side enforcement.
