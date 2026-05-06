---
proposal: flaky-tests-unacceptable
version_target: v040
filed_at: 2026-05-05T00:50:00Z
author_human: thewoolleyman@gmail.com
author_llm: claude-opus-4-7
---

# Proposal: flaky-tests-unacceptable

## Background

User-initiated 2026-05-05T00:45:00Z. The v039 implementation chain
surfaced a hypothesis-based test
(`tests/livespec/validate/test_proposal_findings.py::test_validate_proposal_findings_round_trips_name_text`)
that flaked once under the new `pytest -n auto` xdist conditions
introduced by v039 D2 (`-n auto` in `check-coverage`). The flake
passed on retry. The executor initially recorded it as a
non-blocking follow-up note in STATUS.md.

User-stated principle (verbatim): "Flaky tests are always
unacceptable. They must either be fixed with a conclusive
resolution of the flakiness, or else deleted. This must be
codified as a hard constraint." User explicitly rejected the
"non-blocking note" disposition: any observed flake halts work
until conclusively resolved.

The flaky test in question was already fixed deterministically
prior to this codification (commit `aaaaa82`, `refactor: cache
proposal_findings schema at module level` — eliminated per-example
file I/O so hypothesis examples no longer push past the 200ms
deadline under xdist worker contention). v040 codifies the
GENERAL rule so future flakes are blocked the same way.

## Decisions

### D1 — flaky tests are unacceptable (hard constraint)

PROPOSAL.md §"Test-Driven Development discipline" gains a new
sub-section `### Determinism: flaky tests are unacceptable (v040
D1)` placed between the existing `### Failing for the right
reason` and `### Legitimate exceptions to test-first`
sub-sections.

The new sub-section reads, verbatim:

> A flaky test — one that passes sometimes and fails sometimes
> under any condition (ordering, parallelism, environment,
> hardware load, hypothesis seed, time-of-day) — is unacceptable.
> The instant a flake is observed (in CI, in pre-commit
> aggregate runs, during local development, or via any other
> channel), work halts on whatever was in progress and the
> flake is conclusively resolved.
>
> **Conclusive resolution** means one of:
>
> 1. **Fix deterministically.** Identify the root cause
>    (timing assumption, shared state, ordering dependency,
>    nondeterministic input space, hypothesis deadline,
>    fixture pollution, etc.) and apply a deterministic
>    remedy: pin the seed, eliminate the slow path,
>    use `monkeypatch.chdir(tmp_path)` for cwd-fallback
>    branches, set `@settings(deadline=None)` only when
>    timing has no semantic relevance to the test, isolate
>    fixtures, refactor away from the shared state — whatever
>    the cause demands. The fix MUST be verified by repeated
>    runs (typically ≥5 consecutive `just check-coverage`
>    invocations).
> 2. **Delete.** If the test cannot be made deterministic
>    (e.g., it asserts behavior that is itself
>    nondeterministic, or the cost of pinning is greater than
>    the test's value), delete it. A deleted flaky test is
>    strictly preferable to a kept flaky test: a kept flake
>    erodes the suite's signal value over time by training
>    contributors to retry-and-ignore failed builds.
>
> **Forbidden alternatives:**
>
> - Marking the test `@pytest.mark.flaky` (or any retry plugin)
>   to auto-retry on failure. Retry-on-failure tolerates the
>   flake; this rule does not.
> - Recording the flake as a "non-blocking follow-up note" in
>   STATUS.md or any other deferred-items log. Flakes are
>   ALWAYS blocking; deferral is not a valid disposition.
> - Filing the flake as a low-severity open-issues entry. Same
>   reason — open-issues severity does not apply to flakes.
> - "It's flaky in CI but passes locally" or "it's only flaky
>   under -n auto" or "I couldn't reproduce" as deferral
>   grounds. The first observation is the trigger; reproducing
>   the flake to investigate is part of the fix, not a gate
>   on whether to fix.
>
> The mechanical enforcement is the existing pre-commit and
> pre-push aggregate (`just check-coverage` running pytest
> under `-n auto`). Any observed pytest failure under that
> aggregate — whether the failure reproduces deterministically
> or appears flaky — blocks the commit / push. There is no
> separate "flake check"; the rule is: the aggregate MUST be
> green every time.

Rationale for each forbidden alternative:

- `@pytest.mark.flaky` retry-plugins are the canonical anti-pattern.
  They turn flake into noise rather than signal. The user-codified
  memory `feedback_flaky_tests_unacceptable.md` explicitly forbids.
- Non-blocking-note disposition is exactly what the executor did
  prior to v040 codification (recorded in STATUS at v039 mini-track
  completion). User explicitly corrected: flakes are not
  non-blocking.
- Low-severity open-issues entries: same correction.
- "Couldn't reproduce" deferrals are the source of long-tail
  flake-tolerance. The first observation is enough; the second
  observation already happened (or will happen at the next CI run).

### D2 — plan-text + housekeeping

- Plan §"Version basis" gains a v040 decision summary block
  immediately after the v039 block (mirroring the
  established convention from v024 onward).
- Plan Phase 0 step 1 byte-identity reference bumps from
  `history/v039/PROPOSAL.md` to `history/v040/PROPOSAL.md`.
- Plan Phase 0 step 2 frozen-status header literal bumps from
  "Frozen at v039" to "Frozen at v040" (per the no-op
  convention since v024 — the literal PROPOSAL.md header line
  never actually changes; the plan's narrative reference is
  what bumps).
- Plan execution-prompt block authoritative-version line bumps
  from "Treat PROPOSAL.md v039 as authoritative" to
  "Treat PROPOSAL.md v040 as authoritative".
- STATUS.md updated to record v040 codification.

## Implementation impact

- **Mechanical enforcement.** The existing `pytest -n auto`
  pre-commit + pre-push aggregate already enforces the rule
  (any failure blocks). No new check is required because the
  rule is "the aggregate MUST be green," which the existing
  gate already enforces.
- **Process enforcement.** The bootstrap skill's halt-on-blocking
  flow now MUST treat any observed flake as a blocking issue;
  the "non-blocking-pre-phase-6" / "non-blocking-post-phase-6"
  severities do NOT apply to flakes. This is captured in the
  user-side memory at
  `feedback_flaky_tests_unacceptable.md` and reinforced by the
  PROPOSAL.md sub-section.
- **Carry-over from v039 D3 verification.** The hypothesis flake
  fixed at commit `aaaaa82` is the originating instance; v040
  codifies the rule retroactively. No additional impl change is
  required for v040 itself.

## What was considered and rejected

### Rejected: a separate `check-no-flaky-tests` enforcement script

Considered authoring a new dev-tooling/checks/ script that runs
the suite N times to detect flakes. Rejected because:

- The existing `pytest -n auto` already runs every test. Flakes
  surface in normal use; they don't need a dedicated detection
  layer.
- A re-run loop would consume meaningful CI time for the rare
  case where a flake exists.
- The discipline is a process rule, not a code rule. PROPOSAL.md
  prose is the right home; the executor + the user are the
  enforcement layer.

### Rejected: allow `@pytest.mark.flaky` with retries=2

Considered allowing the retry-plugin pattern as a "soft" tier
between fix-or-delete and current behavior. Rejected because:

- Retry-on-failure trains contributors to retry-and-ignore. The
  cognitive cost of "is this real or just flaky" propagates to
  every future failure — even non-flaky ones.
- The few cases where retries are genuinely appropriate (e.g.,
  network-dependent integration tests with known transient
  failures) don't apply to livespec — the test suite is
  hermetic.

### Rejected: bundle with v039 retroactively

Considered re-versioning v039 to include this rule, since the
flake was discovered as a side effect of v039 D2. Rejected
because v039 is already codified at `fa7f3bd` and snapshotted at
`history/v039/`; re-versioning would require rewriting committed
history. The clean approach is to land this as v040 referencing
the v039 trigger.

## Provenance

User chat 2026-05-05 (verbatim): "The two side effects need to be
fixed immediately at the highest priority. Flaky tests are always
unacceptable. They must either be fixed with a conclusive
resolution of the flakiness, or else deleted. This must be
codified as a hard constraint. And this particular case must be
addressed immediately." See `bootstrap/decisions.md` 2026-05-05
entry (to be added by the v040 codification commit) for the
discussion-level capture.
