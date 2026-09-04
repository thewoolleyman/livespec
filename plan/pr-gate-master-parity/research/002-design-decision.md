# 002 — Design decision: retire the skip (option 3), and the exact edits it requires

Recorded 2026-09-04 by the `pr-gate-master-parity` plan session. Resolves
the open decision in `001-root-cause-zero-py-skip.md` §"Options" and pins
the precise spec, enforcement, and fan-out edits the maturing plan files.

## Plain-language bottom line

The decision in research/001 was between **(3)** deleting the "only run the
full check set when a `.py` file changed" shortcut so every pull request
runs exactly what `master` runs, and **(1)** keeping a shortcut but making a
check opt IN to being skippable. We are taking **(3)**. It is the only
option that makes "a pull request can never pass a weaker gate than
`master`" true *by construction* — there is no predicate left that can rot —
and the maintainer's directive ("NOTHING SHOULD BE ABLE TO BREAK MASTER")
is an absolute that only a structural guarantee satisfies. Option (1) still
leaves a per-check declaration that a future check can forget to set.

## The invariant, stated precisely

**PR gate ≡ master gate.** For every fleet member: the set of *gating*
checks a `pull_request` must pass is identical to the set that runs on
`push` to `master` (and `merge_group`). "Gating" = any job the required
all-green gate job (`ci-green`) lists in its `needs:`. The invariant is
one-directional-safe: a pull request MAY run *additional* checks master
does not (e.g. `release-gate-pre-tag`, which skips harmlessly on ordinary
PRs); what is forbidden is a pull request running *fewer* gating checks
than master. Non-gating jobs (telemetry export, notifications — anything
absent from `ci-green.needs`) are exempt.

The load-bearing enforcement is **CI parity under branch protection**: the
sole required check is the `ci-green` gate, so if CI runs the full aggregate
on every PR, no change can merge without the full aggregate passing —
regardless of what any local hook did. Local pre-push is defense-in-depth,
not the gate.

## Why the old mechanism rotted (the false premise)

The retired clause justified the skip with: "the Python-code checks are
deterministic functions of the Python source tree, so with no `.py` delta
every Python-code check passes-or-fails identically against the merge-base."
That was true for the 22 checks of May 2026 and false for every check added
since that reads a non-Python input — `self_hosted_uv_lane` /
`self_hosted_routing` (read `ci.yml`), `plan_epic_parity` /
`plan_no_tombstone` (read `plan/` + the ledger), `wrapper_shape`, and
others. Nobody re-derived the premise when those landed, because nothing
asked. On 2026-09-04 a `ci.yml`-only pull request merged green and reddened
`master` twelve seconds later: the skipped `check-self-hosted-uv-lane` reads
the workflow file the PR changed.

## The exact spec edits (R1)

Two files, no `##` heading added/changed/removed, so **no
`tests/heading-coverage.json` co-edit** arises.

1. **`SPECIFICATION/contracts.md` §"Pre-commit step ordering"** — the
   pre-commit zero-`.py` doc-only subset is KEPT but relabelled a LOCAL
   speed optimization that is explicitly NOT a gate; the v050 mandate that
   pre-push and CI apply the same subset (its clauses (a)–(d) and the
   "soundness" paragraph) is DELETED and replaced by: pre-push delegates to
   `just check` (full aggregate); CI runs every gating check on a
   `pull_request` exactly as on `push`/`merge_group`; the PR-gate ≡
   master-gate invariant is named with its home in §"CI as a merge gate
   (branch protection)". The pre-1st-paragraph already says "Pre-push runs
   `just check` (the full aggregate)", so this restores internal
   consistency v050 broke.

2. **`SPECIFICATION/non-functional-requirements.md`**:
   - §"CI as a merge gate (branch protection)" GAINS a `**PR gate ≡ master
     gate.**` paragraph stating the invariant and naming the `ci_gate_parity`
     shared check as the companion to the existing `ci_matrix_completeness`
     (warn-until-armed via `LIVESPEC_FAIL_IF_CI_GATE_PARITY_GAPS_EXIST`).
     `ci_matrix_completeness` confirms every gating check is PRESENT and in
     the gate job's `needs:`; `ci_gate_parity` confirms every such check
     actually RUNS on a pull request rather than being conditionally skipped.
   - The `comment_no_historical_refs` enforcement paragraph's sentence "The
     check is categorized as a python-code check … so it is skipped when
     zero `.py` files change" is swept to state it runs unconditionally in
     the full aggregate.

## The mechanical guard (R2, livespec-dev-tooling)

`ci_gate_parity` — a new shared check reading `.github/workflows/ci.yml`
statically. It FAILS when a gating job (one in `ci-green.needs`) has its
real steps conditioned on the triggering event or on a changeset
`.py`-predicate (the `needs.setup.outputs.py_changed == 'true'` shape). It
warns by default and fails only under
`LIVESPEC_FAIL_IF_CI_GATE_PARITY_GAPS_EXIST`, so it propagates to a
not-yet-fixed repo safely (the `ci_matrix_completeness` pattern). It is a
repo-metadata check → runs in `check-metadata-batch`, always. Per the
No-Circular-Dependency Directive it lives in dev-tooling and each consumer
runs it against its OWN `ci.yml` (dev-tooling never reads into a consumer).

## The per-repo transformation (R3) — 6 carriers only

Fleet survey (2026-09-04) found the `.py`-skip predicate in BOTH `ci.yml`
and the justfile/lefthook layer in exactly six repos: **livespec,
livespec-dev-tooling, livespec-orchestrator-beads-fabro,
livespec-orchestrator-git-jsonl, livespec-runtime, livespec-overseer**. The
transformation per carrier:

- `ci.yml`: remove the `setup`/`detect-py-changes` job; drop `needs: setup`
  and every `if: needs.setup.outputs.py_changed == 'true'` step condition
  and the paired "Skip when no .py changes" no-op steps, so the python jobs
  run unconditionally; fix any `needs:`/`if:` that referenced `setup`
  (release-gate, export-telemetry). `ci-green.needs` is unchanged.
- justfile/lefthook: pre-push runs the full `just check` (drop the
  zero-`.py` branch of `check-pre-push`); the pre-commit doc-only subset MAY
  stay as a local speed optimization.
- bump the dev-tooling pin to the `ci_gate_parity` release and arm
  `LIVESPEC_FAIL_IF_CI_GATE_PARITY_GAPS_EXIST` in CI AFTER the `ci.yml` fix.

Also (R4): the copier template `templates/orchestrator-plugin/` copies of
`ci.yml`/`justfile`/`lefthook.yml` in livespec get the same transformation
so new orchestrator members never carry the skip
(`check-copier-template-smoke` / `copier-template-workflow-coverage` stay
green).

## Deferrals (see the plan-epic scope event)

- The 3 `livespec-driver-*` repos are NOT touched: they use a tree-hash
  green-token clean-tree skip (byte-identical tree ⇒ provably identical
  result — a sound mechanism, unlike the `.py` predicate), and their CI runs
  the full aggregate unconditionally.
- Adopters (openbrain, dolt-server, resume, homelab) and
  livespec-console-beads-fabro carry no `.py` skip — nothing to retire;
  `ci_gate_parity` must pass on them unchanged.

## Read-first chain

This note → `001-root-cause-zero-py-skip.md` → the plan epic
`livespec-citqsd` scope event + 2026-09-04 decision handoff → livespec
`SPECIFICATION/contracts.md` §"Pre-commit step ordering" → livespec
`SPECIFICATION/non-functional-requirements.md` §"CI as a merge gate (branch
protection)" (the `ci_matrix_completeness` companion) → the proposal file
`SPECIFICATION/proposed_changes/pr-gate-master-parity.md`.
