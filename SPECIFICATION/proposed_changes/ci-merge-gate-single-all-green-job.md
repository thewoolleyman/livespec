---
topic: ci-merge-gate-single-all-green-job
author: claude-opus-4-8
created_at: 2026-07-10T22:40:54Z
---

## Proposal: Codify the single all-green gate job as the CI merge-gate rule

### Target specification files

- non-functional-requirements.md

### Summary

Revise `non-functional-requirements.md` §"CI as a merge gate (branch
protection)" so it describes the **single all-green gate-job** merge-gate
model the fleet now runs, replacing the superseded rule that a repo's
`master` branch-protection required-check set must **enumerate every CI
matrix check**. Under the new model, each repo's `master` branch
protection requires exactly ONE status check — a single all-green gate
job (the fleet convention names it `ci-green`) whose `needs:` covers every
gating CI job — kept honest by two shared `livespec-dev-tooling` checks:
`branch_protection_alignment` reads the live branch protection via `gh api`
(rejecting absent protection, an enabled `strict`, or a phantom required
check, and accepting the top-level gate job), and `ci_matrix_completeness`
proves — from committed files alone — that CI actually runs and gates the
whole `just check` aggregate. This closes the
spec-vs-reality drift opened by the fleet-ci-aggregate-coverage epic
(`livespec-cf4bcu`), which has already moved every fleet repo to require
only `ci-green`.

### Motivation

The clause as written is now contradicted by every fleet repo, exactly the
outlier situation the runtime CI-invocation clause was in before
`ci-invocation-clause-align-fleet-matrix`:

- **The epic decision (2026-07-10) chose the single all-green gate job**
  over per-check required contexts. Per-check contexts are brittle: N
  context-names deadlock master merges on any target rename, and they live
  out-of-band from git — no PR, no history, silent drift against the CI
  matrix. A single gate job whose `needs:` fans out over the matrix
  removes that drift surface by construction while keeping the required set
  a single stable context that never churns as checks are added or renamed.

- **The model is already shipped fleet-wide.** All five large-track repos
  (`livespec`, `livespec-runtime`, `livespec-orchestrator-beads-fabro`,
  `livespec-orchestrator-git-jsonl`, `livespec-dev-tooling`) plus the three
  non-core repos (`livespec-driver-claude`, `livespec-driver-codex`,
  `livespec-console-beads-fabro`) now require ONLY `ci-green`. The
  drift-guard `ci_matrix_completeness` (slug `check-ci-matrix-completeness`)
  ships from `livespec-dev-tooling` (v0.37.0–v0.37.3) and is armed in every
  large-track repo. The NFR still prescribing *"the required-check set MUST
  cover the repo's full CI matrix"* directly contradicts every fleet repo's
  actual, single-context required set.

- **The companion check's behavior already changed.** `branch_protection_alignment`
  was updated (v0.37.3) to recognize a top-level gate job as a valid
  required check (it errors on a required check matching neither a matrix
  leg nor a top-level job — a phantom that can never report — but a
  required `ci-green` is accepted). The NFR's description of that check's
  failure modes predates the change and must be realigned so the spec no
  longer claims the check enforces matrix-superset coverage.

- **This codifies a contract, not a mechanism.** The revision names the
  concrete conventions (`ci-green`, `ci_matrix_completeness`, the
  world-gate exclusion) at the same altitude the section already operates
  at — it already names `branch_protection_alignment`, `strict`,
  `enforce_admins`, and their failure modes. No `ci.yml` YAML is
  prescribed; the contract is *"one all-green gate job is the required
  check, and shared checks prove CI runs and gates the whole aggregate."*

The rule's *intent* — a red pull request MUST NOT be mergeable, enforced
structurally rather than by author vigilance — is unchanged and preserved;
only the realization (single gate job vs. enumerated matrix) is updated to
match the shipped fleet.

### Proposed Changes

In `non-functional-requirements.md` §"CI as a merge gate (branch
protection)", replace:

> Every livespec-governed primary repo's `master` branch MUST have GitHub branch protection configured so that the repo's CI matrix checks are REQUIRED status checks. A pull request MUST NOT be mergeable while CI is red: the required-check gate MUST block the merge until every CI matrix check reports success.

with:

> Every livespec-governed primary repo's `master` branch MUST have GitHub branch protection configured so that a single all-green gate job is the sole REQUIRED status check. A pull request MUST NOT be mergeable while CI is red: the required-check gate MUST block the merge until that gate job reports success, and the gate job reports success only when every CI job it depends on succeeded — so requiring the one gate job gates the merge on the entire CI matrix.

Replace:

> The required-check set MUST cover the repo's full CI matrix; a protection whose required-check set omits any CI matrix check is out-of-contract because the omitted check becomes advisory again.

with:

> The required-check set MUST be exactly the single all-green gate job (the fleet convention names it `ci-green`): a summary CI job whose `needs:` lists every gating job — any job that runs a `just <target>` command or carries a `strategy.matrix.target` list, canonical or not — and which fails whenever any of those dependencies failed or was cancelled. Requiring only the gate job blocks merges on the whole matrix (the gate cannot report success unless every check it depends on did) while keeping the required-check set a single stable context that never churns as checks are added or renamed, so per-check branch-protection edits are never needed again. This is the deliberate replacement for a per-check required set: because branch-protection membership is out-of-band settings (below) with no committed-file record, a per-check required set drifts silently against the CI matrix, whereas the single gate job removes that drift surface by construction. The gate job's guarantee is enforced structurally by `branch_protection_alignment` (below), which reads the live protection via `gh api` and fails on absent protection, an enabled `strict`, or a phantom required check that names no real CI job (a required top-level gate job is accepted), and — from committed files alone — by the companion `ci_matrix_completeness` check, which confirms CI actually runs and gates the whole aggregate: (a) the set of canonical `just check` slugs CI runs is a superset of the justfile `check:` aggregate — excluding the pre-push-only world-gate checks, which assert master/world state rather than the changeset and enforce out-of-band under an admin token — and (b) the gate job's `needs:` covers every gating job. A canonical slug that runs at pre-push but never in CI, or a gating job the gate job omits from its `needs:`, therefore FAILS CI once the repo arms the guard (the `LIVESPEC_FAIL_IF_CI_MATRIX_GAPS_EXIST` lever; until then the same finding warns without reddening, so the check can propagate to a not-yet-wired repo safely).

Replace:

> The check MUST fail when branch protection is absent on `master`, when `enforce_admins` is not set, when `strict` IS enabled (it MUST be off per the rule above), or when the protection's required-check set does not cover the repo's CI matrix.

with:

> The check MUST fail when branch protection is absent on `master`, when `enforce_admins` is not set, when `strict` IS enabled (it MUST be off per the rule above), or when a required check matches neither a CI matrix leg nor a top-level CI job — a phantom required check that can never report and would deadlock every merge. A required top-level all-green gate job (the `ci-green` single-gate model) is a valid required check and is NOT flagged, even though it is not a matrix leg, because requiring it gates the whole matrix through its `needs:`; the complementary guarantee that CI actually runs and gates the whole aggregate is enforced by the companion `ci_matrix_completeness` check, not by `branch_protection_alignment`.

Replace:

> Every consumer repo MUST wire `branch_protection_alignment` into its `just check` aggregate AND CI matrix on the same invocation-agnostic cadence governing every other shared check, per the wiring-completeness invariant codified in §"Shared code sync — livespec-dev-tooling".

with:

> Every consumer repo MUST wire `branch_protection_alignment` into its `just check` aggregate on the same invocation-agnostic cadence governing every other shared check, per the wiring-completeness invariant codified in §"Shared code sync — livespec-dev-tooling"; but as a world-gate check that reads live branch protection via `gh api` — which the per-PR CI Actions token cannot — it is deliberately NOT run in the per-PR CI matrix, where it would always-skip, and `ci_matrix_completeness` correspondingly excludes it (with the other world-gate check) from its CI-runs-the-aggregate assertion.
