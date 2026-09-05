# 001 — Root cause: the zero-`.py` skip lets a pull request merge green and turn master red

Recorded 2026-09-04 by the `ci-runner-pod-lifecycle-reliability` session
(epic `livespec-ifwnqj`) after `livespec-orchestrator-beads-fabro` master
went red at 482a16c4. Maintainer directive that opened this plan, verbatim:
"NOTHING SHOULD BE ABLE TO BREAK MASTER."

## Plain-language bottom line

A pull request that changes only the CI workflow file merged with a green
gate and broke master twelve seconds later, because the gate a pull request
runs is a SUBSET of the gate master runs, and the subset is chosen by asking
"did any Python file change?" — a question that has nothing to do with what
the skipped checks actually read. The rule that mandates this subsetting is a
ratified clause of livespec's own specification. This plan retires the
mechanism (or makes it provably safe), in the spec first and then in every
fleet member, so that the check set a pull request passes is exactly the
check set master enforces.

## What happened (evidence)

| When (UTC) | Where | Event |
|---|---|---|
| 2026-09-04 16:33 | livespec-orchestrator-beads-fabro PR #2139 (ci.yml-only: `runs-on` switched to the `CI_RUNNER_LABELS` form) | CI run 33895801359 **success**. `detect-py-changes` set `py_changed=false`; every `check-python-batch` job ran its "Skip when no .py changes" step and reported success. |
| 16:34:35 | auto-merge | 482a16c4 lands on master. |
| 16:34:38 | master push run 33895911436 | `py_changed=true` unconditionally on `push`; `check-python-batch (root)` runs `check-self-hosted-uv-lane`, which reads ci.yml and fails: `missing: ["UV_CONCURRENT_DOWNLOADS", "UV_HTTP_TIMEOUT"]`. Master red. |
| 17:29 | master push run 33900864789 (unrelated pin bump) | Still red; every open PR and the factory's green-master gate blocked. |
| 17:55 | PR #2143 = bef83890 | Symptom repaired (the two env lines added). Master green. |

The same predicate exists at three layers, all keyed on `.py`:

1. **CI** — `.github/workflows/ci.yml` `setup` job: on `pull_request`,
   `git diff --name-only origin/<base>...HEAD | grep '\.py$'`; on `push`,
   always true. Python-batch matrix jobs gate on `py_changed == 'true'`.
2. **lefthook pre-commit** — `just check-pre-commit` runs the five-target
   doc-only subset when zero `.py` files are staged.
3. **lefthook pre-push** — `just check-pre-push` diffs `@{upstream}..HEAD`
   and takes the same subset on zero `.py`. Observed: the repair push's
   pre-push `check` finished in 7 seconds — the subset, not `just check`.

So the author's own hooks, the PR gate, and auto-merge all agreed the change
was safe, and none of them had run the check that reads the file the change
touched.

## Where the rule comes from

- **Spec:** livespec `SPECIFICATION/contracts.md` §"Pre-commit step
  ordering", ratified at **v050 (2026-05-07)** from proposal
  `claude-opus-critique` (`history/v050/proposed_changes/claude-opus-critique.md`),
  whose own title is: "contracts.md line 93 forbids zero-.py subsetting in
  pre-push and CI; must be inverted." Before v050 the clause said the
  opposite: "Pre-push and CI never apply this subsetting — the full
  aggregate is the load-bearing safety net for any branch landing on
  master."
- **Implementation:** livespec `babc21ef` (same day), then carried into every
  member scaffolded from livespec's copier template (the orchestrator repo's
  scaffold commit `d0650fae`, 2026-06-08, names `gh:thewoolleyman/livespec`
  at `b30e727a` as its source).
- **A second clause depends on it:** `non-functional-requirements.md`
  ("…categorized as a python-code check per §'Pre-commit step ordering' so it
  is skipped when zero `.py` files change", the `comment_no_historical_refs`
  enforcement paragraph). Any amendment must sweep it.

## Why it rots: two defects in the clause itself

1. **A false premise, stated as the soundness proof.** "The zero-`.py`
   subsetting is sound because the Python-code checks are deterministic
   functions of the Python source tree." True for the 22 checks of May 2026.
   False for every check added since that reads a non-Python input:
   `self_hosted_uv_lane` and `self_hosted_routing` (read `ci.yml`),
   `plan_epic_parity` / `plan_no_tombstone` (read `plan/` and the ledger),
   `supervisor_discipline`, `wrapper_shape`, and others. Nobody re-derived
   the invariant when those landed, because nothing asks.
2. **The unsafe bucket is the default.** Rule (d): "Every other target in
   `just check` is a python-code check." A new check is skippable unless
   someone moves it to the five-item metadata list by hand. The safe
   direction — always run unless proven skippable — is the inverse.

A third, smaller defect: the clause routes a pre-existing failure to
`check-master-ci-green` as "a master-branch-state concern, not a per-PR
concern". For a check whose input the PR itself changes, the PR is the only
place the failure can be caught before master.

## The invariant this plan must establish

**PR gate ≡ master gate.** For every fleet member: the set of checks that
must pass before a change merges is identical to the set master enforces on
push, and that identity is asserted mechanically (a check that fails when a
job or target runs on one event and not the other, or when a local hook path
takes a subset the CI path does not). "Nothing can break master" is then a
property of the definitions, not of anyone's diligence.

## Options

| | Shape | Guarantee | Cost | Rot risk |
|---|---|---|---|---|
| **(3) Retire the skip — RECOMMENDED** | Delete `detect-py-changes` gating, `check-pre-push` subsetting, and the pre-commit doc-only subset (or keep pre-commit's as a pure speed optimisation that is NOT the gate). Every PR and every push runs `just check`. Add `check-ci-gate-parity` (dev-tooling) asserting no job/target is conditioned on the event. | Total, by construction. | Doc-only PRs run the full aggregate. On the PowerEdge pool with the warm uv seed and the compilation cache this is minutes, not the hosted-runner cost that motivated v050. Measure once; record the number. | None: there is no predicate to rot. |
| (1) Invert the default | Keep a skip, but a check is skippable only if it DECLARES Python-only inputs (e.g. a `skippable_on_zero_py = True` marker in the check module, read by the justfile/CI generator); everything else always runs. | Strong, if the declaration is honest. | A declaration per check; a generator or lint that derives the two matrices from the declarations so they cannot drift (the clause's rule (d) already demands "no drift" and had no mechanism). | Low but non-zero: a check that reads a new input without updating its declaration. |
| (2) Widen the path list | Add `.github/workflows/`, `justfile`, `lefthook.yml`, `.livespec.jsonc`, `plan/` to the predicate. | Weak. | Trivial. | High: exactly the failure mode that just occurred, one new input later. |

Recommendation: (3), with (1) reconsidered only if the measured full-gate
cost on a doc-only PR is material after the pool's caches. The maintainer's
directive is an absolute; (3) is the only option that makes the property
structural.

## Scope of the change (what a maturing plan files)

1. **Spec-op in livespec:** `propose-change` amending `contracts.md`
   §"Pre-commit step ordering" (restore the pre-v050 sentence in substance:
   pre-push and CI run the full aggregate; pre-commit may subset for speed
   but is not the gate), sweeping the dependent paragraph in
   `non-functional-requirements.md`, and adding the PR-gate ≡ master-gate
   invariant with its mechanical guard. Independent adversarial review, then
   `revise`.
2. **livespec-dev-tooling:** the `ci_gate_parity` check (event-conditioned
   jobs/targets are a failure), wired into `just check`; the copier template's
   `ci.yml`, `justfile`, `lefthook.yml` updated so new members never carry the
   skip.
3. **Fleet fan-out (one epic, one child per member):** every governed
   repository's `ci.yml` / `justfile` / `lefthook.yml` — and the four adopters
   are their own call. Branch protection's required contexts re-verified per
   repo (the python-batch contexts are already required; they must now be
   guaranteed to RUN, not merely to exist).
4. **Measurement:** full-aggregate wall clock for a doc-only PR on the pool,
   recorded here, to close the "is (3) affordable" question with a number.

## Read-first chain

This note → livespec `SPECIFICATION/contracts.md` §"Pre-commit step
ordering" (live) → `history/v050/proposed_changes/claude-opus-critique.md`
(the inversion and its stated soundness argument) → livespec-orchestrator-beads-fabro
runs 33895801359 (green PR) and 33895911436 (red master) → livespec-dev-tooling
`livespec_dev_tooling/checks/self_hosted_uv_lane.py` (a check whose input is
the workflow file) → epic `livespec-ifwnqj`'s 2026-09-04 handoffs (the
incident's context).
