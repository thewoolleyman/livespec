---
proposal: aggregate-perf-and-iteration-loop
version_target: v039
filed_at: 2026-05-04T08:30:00Z
author_human: thewoolleyman@gmail.com
author_llm: claude-opus-4-7
---

# Proposal: aggregate-perf-and-iteration-loop

## Background

User-initiated 2026-05-04T08:30Z. Prior session (now killed) timed
out on a Green-amend coverage-gap loop in the comment_line_anchors
cycle: defensive branches in the impl (`try/except` clause + the
`if __name__ == "__main__":` guard) were not enumerated at Red
time, surfaced post-hoc at the `check-coverage` Green-amend gate,
required back-up to extend the Red test, and triggered a
5+-minute pre-commit aggregate retry. Three round-trips burned
~30 minutes for what should have been ~10 minutes of authoring.

The user wall-clock-profiled the existing aggregate. Result: two
targets dominate (95% of the total time):

| target | time | share |
|---|---|---|
| `check-coverage` | 223.96s | 64% |
| `check-tests` | 108.26s | 31% |
| 29 fast targets combined | ~17s | ~5% |
| **total** | ~349s | |

The `check-tests` target runs `pytest`; `check-coverage` runs
`pytest --cov --cov-branch` plus the per-file 100% gate. The
former is exercised entirely as a side effect of the latter —
running both is double-counting.

## Decisions

### D1 — drop `check-tests` from the canonical aggregate

`check-coverage` already runs the full test suite; the suite
existing as a separate `check-tests` target is a v007-era artifact
from before per-file coverage was the gate. Removing the
standalone target collapses ~108s out of the wall-clock with zero
information loss. PROPOSAL.md §"Activation" + §"Coexistence with
the pre-commit gate" + §"CI workflow" updated to reference only
`check-coverage` in the Red-mode skip semantic.
`python-skill-script-style-requirements.md` §"Canonical target
list" drops the row.

### D2 — `pytest -n auto` for `check-coverage`

pytest-xdist parallelizes the suite across cores; on a typical
multi-core developer machine the full coverage run drops from
~3.5 minutes serial to under a minute. Subprocess
instrumentation via the existing `.pth` startup hook continues
to drive `--cov-branch` inheritance unchanged. Combined with D1
the total `just check` aggregate drops from ~5:49 to ~1:30-2:00.

### D3 — `just check-coverage-incremental` path-scoped fast-feedback

A new target that takes `--paths <impl_paths>`, resolves each
impl's mirror-paired test (per v033 D1), runs `pytest -n auto
--cov=<impl_path> tests/<mirror>/test_<name>.py` per pair, then
runs the per-file 100% gate on the impacted impl files only.
Wall-clock target: under 10 seconds for a typical single-file
pair. NOT a replacement for `check-coverage` — the full-tree run
remains the load-bearing pre-commit gate. The fast-feedback role
is to surface coverage gaps proactively during the Red→Green
authoring loop, BEFORE the Green amend triggers a multi-minute
aggregate retry on a missed defensive branch.

The pytest-cov subprocess-instrumentation path-translation
behavior under explicit `--cov=<path>` filters (the user found
this returns 0% in some configurations) is the v039 D5
deferred-spike. D3's contract is finalized after the spike
resolves — either the spike finds the right configuration knob
or D3 falls back to a "full suite + post-hoc filter" mechanism
with degraded but still useful wall-clock.

### D4 — Red-time branch enumeration + proactive coverage discipline

The v034 D2-D3 amend pattern locks the test-file SHA-256 at the
Red commit; the Green amend can only stage impl. Coverage gaps
in defensive branches surface as Green-amend gate failures,
requiring back-up to Red plus full-aggregate retries. v039 D4
codifies the Red-time discipline directly in PROPOSAL.md
§"Test-Driven Development discipline":

- **Red-time enumeration:** before committing the Red moment,
  the executor enumerates every branch the planned impl will
  introduce — including defensive ones (`try/except` arms,
  `isinstance` narrowings, optional-arg fallbacks, `sys.path`
  guards, `if __name__ == "__main__":` entry points). One test
  per branch.
- **Proactive coverage:** after authoring the Green draft and
  before staging, the executor runs `just
  check-coverage-incremental --paths <impl_path>` to surface
  gaps in seconds.

Q1+Q2 are not directly mechanically enforceable — D3's tool
makes them mechanically cheap to follow; the existing
post-hoc `check-coverage` per-file gate at Green-amend time
catches missed gaps as the safety net. The honest framing is
captured in PROPOSAL.md §"Mechanical reinforcement": D3 is
the load-bearing mechanical addition, D4 is the discipline
that becomes ergonomic because of D3.

### D5 — defer pytest-cov subprocess-instrumentation spike

Highest-priority follow-up after the in-progress
`wip/comment-line-anchors` Red+wip-Green pair lands. Captured
as `bootstrap/open-issues.md` 2026-05-04T08:30:00Z. Outcome
dictates D3's final contract.

### D6 — plan-text + housekeeping

Phase 0 step 1 byte-identity reference bumps to
`history/v039/PROPOSAL.md`. Phase 0 step 2 frozen-status
header literal bumps to "Frozen at v039". Execution-prompt
block authoritative-version line bumps to v039. STATUS.md
updated.

## What was considered and rejected

### Rejected: collapse 29 small AST checks into one runner

The user proposed this as item 3 alongside D1+D2. Numerically:
saves ~12s of `uv run` interpreter startup overhead spread
across 29 invocations. Cost: collides with v033 D1
mirror-pairing (one test file per check script), v033 D2
per-file 100% coverage (one coverage measurement per script),
`check-main-guard`, `check-wrapper-shape`, and the
"`dev-tooling/checks/<name>.py` per check" structure
explicitly enumerated in PROPOSAL.md §"Repository layout".
The 12s payoff doesn't earn the rework. Dropped.

### Rejected: split into v039 (perf) + v040 (discipline)

Considered keeping D1+D2 as a perf-only v039 and filing
D3+D4+D5 as a follow-up v040. Rejected because they share the
iteration-loop thesis — perf without discipline still leaves
the loop slow when defensive branches are missed; discipline
without perf has no fast-feedback layer to actually run
proactively. Bundling is correct.

### Rejected: skip codification, edit justfile directly

Considered a "pure dev-tooling" framing where v039 doesn't
touch PROPOSAL.md. Rejected because PROPOSAL.md §"Activation",
§"Coexistence with the pre-commit gate", and §"CI workflow"
all explicitly enumerate `check-tests` and `check-coverage`
in the Red-mode skip semantic. Dropping `check-tests` from
the aggregate without updating PROPOSAL.md creates plan/spec
drift the next bootstrap halt would catch.

## Implementation impact

- `justfile`: drop `check-tests` from `check:` target list at
  `justfile:84` (and remove the `check-tests:` recipe at
  `justfile:154-169` — Red-mode-skip logic relocates into the
  `check-coverage` recipe). Add `-n auto` to the
  `check-coverage` pytest invocation at `justfile:189`. Add a
  new `check-coverage-incremental:` recipe per D3's contract.
- `lefthook.yml`: no changes — the hook delegates to
  `just check-pre-commit` which delegates to `just check`;
  the aggregate composition change is transparent to
  lefthook.
- `dev-tooling/checks/`: no changes to the existing 29 fast
  checks. The new `check-coverage-incremental` may need a
  small wrapper script under `dev-tooling/checks/` to
  resolve mirror-paired tests + format the pytest+coverage
  invocation.
- `pyproject.toml`: pytest-xdist added to
  `[dependency-groups.dev]`. `[tool.coverage.paths]` may need
  a configuration entry depending on the v039 D5 spike
  outcome.
- `tests/`: no test changes required for the canonical
  aggregate. The `wip/comment-line-anchors` cycle resumes
  via the existing patch file once D3 is implemented; the
  defensive-branch tests are authored at that point per the
  v039 D4 discipline.

## Provenance

User chat 2026-05-04 (compressed): perf framing → research →
timing data → design discussion → severity-ranking → bundle
choice → preservation → codification authorization. See
`bootstrap/decisions.md` 2026-05-04T08:30:00Z for the
discussion-level capture.
