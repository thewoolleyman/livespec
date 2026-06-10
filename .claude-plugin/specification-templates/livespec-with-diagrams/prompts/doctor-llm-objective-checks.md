# `doctor` LLM objective-checks prompt — `livespec` template

> **Status: Phase-7-final per `SPECIFICATION/templates/livespec/contracts.md`
> §"Doctor-LLM-objective-checks prompt".** Future regenerations
> land via dogfooded propose-change/revise against the sub-spec.
>
> This prompt was authored per the coordinating epic
> `coordinating-epic-stale-revise-enforcement` (Layer 3' —
> "doctor LLM-phase surfaces open spec-PR status"). The
> open-spec-PR dimension below is the first dimension this prompt
> declares; future propose-change cycles MAY widen the dimension
> set without re-authoring the prompt scaffold.

## Inputs

- The active spec tree (under `<spec-root>/`, resolved per the
  doctor wrapper's enumeration of main + sub-spec trees).
- The repo's `.livespec.jsonc` (for the GitHub-hosted predicate
  guarding the open-spec-PR dimension). The doctor SKILL.md
  prose orchestrates which paths the LLM has read access to;
  this prompt assumes those reads have already happened.
- The local `gh` CLI surface for any network-aware dimension
  that needs it. The doctor LLM-driven phase is permitted to
  call `gh` per the existing LLM-phase contract; the static
  phase remains network-free per `SPECIFICATION/constraints.md`.

## Behavior

Run the LLM-driven objective-checks phase per
`SPECIFICATION/contracts.md` §"LLM-driven objective phase"
(doctor SKILL.md Step 7). Walk every spec tree and emit
findings along each dimension below. Each dimension is
deterministic per its declared mechanism — a "fail" finding
here represents an objective, reproducible state of the world
worth the user's attention via the doctor SKILL.md
per-finding dialogue (Step 11), NOT a hard stop.

### Dimensions

For the built-in `livespec` template, the objective-checks
prompt currently declares one dimension. The prompt MAY also
carry additional dimensions later; this revision DECLARES only
the open-spec-PR dimension.

### 1. Open spec-PR status (skill-baked — only applicable when `.livespec.jsonc` declares a GitHub-hosted project)

This dimension surfaces residual coordination state that the
preventive layers of `coordinating-epic-stale-revise-enforcement`
do NOT cover: an open spec-PR with red CI that auto-merge cannot
complete, a PR opened by a separate session the user has not
seen, or a merge-conflict that materialized after the PR was
opened. The mechanism is on-demand surfacing (only when the user
runs doctor) rather than bot-driven PR-comment / label spam.

#### Applicability predicate

Run this dimension only when BOTH of the following hold:

- The spec tree's `.livespec.jsonc` (or the repo's top-level
  `.livespec.jsonc` when the spec tree does not carry its own)
  declares a project hosted on GitHub. The hosting declaration
  is the presence of a GitHub-shaped `repo` / `host` entry in
  the cross-repo or canonical-branch surface; when the
  declaration is absent or non-GitHub, this dimension is a
  no-op.
- The local `gh` CLI is available on `PATH` and authenticated
  per `SPECIFICATION/contracts.md` §"GitHub CLI authentication".

When either predicate fails, emit NO findings for this
dimension. Surface the no-op as a structured `info`-level log
line so the absence of findings is auditable — e.g.,
`info: open-spec-pr dimension skipped — gh unavailable` or
`info: open-spec-pr dimension skipped — project not GitHub-hosted`.
The log line MUST NOT be emitted as a finding (it has no
disposition surface) and MUST NOT lift any exit code.

#### Discovery mechanism

When the applicability predicate holds, discover the candidate
PR set by invoking:

```
gh pr list --state open --head 'spec/*' --json number,state,statusCheckRollup,headRefName,createdAt,updatedAt,mergeable
```

The `--head 'spec/*'` filter scopes the query to spec-revise
branches per the livespec branching convention. The `--json`
projection enumerates the fields needed for the per-PR
classification below. The dimension processes each returned PR
independently; a PR MAY produce zero or one finding per the
classification below (never more than one — the classifications
are mutually exclusive by construction).

#### Per-PR classification

For each PR returned, emit AT MOST ONE finding per the first
matching clause below (evaluated in order):

- When `mergeable == "CONFLICTING"`: emit
  `doctor-llm-objective-open-spec-pr-merge-conflict` with
  severity `high`. Message:
  `[severity: high] PR #<number> (<headRefName>) has merge conflicts against the canonical branch.`
- When `statusCheckRollup` contains ANY check whose state is
  `FAILURE`, `ERROR`, or `CANCELLED`: emit
  `doctor-llm-objective-open-spec-pr-red-ci` with severity
  `high`. Message:
  `[severity: high] PR #<number> (<headRefName>) has red CI; failing checks: <comma-separated check names>.`
- When `mergeable == "MERGEABLE"` AND every entry in
  `statusCheckRollup` is `SUCCESS` (or the rollup is empty
  because the repo declares no required checks): emit
  `doctor-llm-objective-open-spec-pr-green-unmerged` with
  severity `medium`. Message:
  `[severity: medium] PR #<number> (<headRefName>) is green and mergeable but unmerged; auto-merge is not enabled.`

PRs whose state matches none of the above (e.g., CI still
running, `mergeable == "UNKNOWN"`, draft PRs) are NOT findings;
the dimension is silent for transient in-flight states.

#### Per-finding fields

- `path`: empty string. The finding is repo-scoped, not
  spec-file-scoped.
- `line`: 0.
- `spec_root`: the spec tree path that surfaced the finding.
- `proposed_change_hint` (passed to Step 11): a one-sentence
  remediation hint scoped to the finding's severity — e.g., for
  green-unmerged, `Invoke 'gh pr merge --auto --rebase --delete-branch <number>' to enable auto-merge`;
  for red-ci, `Investigate failing checks on PR #<number> before re-attempting merge`;
  for merge-conflict, `Rebase the spec/* branch onto the canonical branch and resolve conflicts before re-attempting merge`.

### Per-dimension scoring

For each finding, emit:

- `dimension`: one of `open-spec-pr-status` (this revision
  declares only this value; future dimensions add to the
  set). Recorded inside the finding's `message` field as a
  structured prefix where useful, since the
  `doctor_findings.schema.json` does NOT carry a separate
  `dimension` field at v1. Future schema widening MAY split
  the dimension into its own field.
- `severity`: a qualitative `low` / `medium` / `high` judgment
  encoded inside the `message` field's structured prefix (e.g.,
  `[severity: medium] ...`). The doctor static phase's
  `pass`/`fail`/`skipped`/`warn` enum doesn't have a severity
  axis; the LLM-driven phase encodes severity prose-side for
  the per-finding user dialogue at the SKILL.md layer.

## Output schema

Emit JSON conforming to
`.claude-plugin/scripts/livespec/schemas/doctor_findings.schema.json`:

```json
{
  "findings": [
    {
      "check_id": "doctor-llm-objective-open-spec-pr-<classification>",
      "status": "fail",
      "message": "[severity: <low|medium|high>] <one-sentence finding>",
      "path": "",
      "line": 0,
      "spec_root": "<spec_root path>"
    }
  ]
}
```

`status` is always `fail` for surfaced findings — the
LLM-driven objective phase emits findings only when something
warrants the user's attention. Empty findings (no issues, or
the applicability predicate failed) results in a `findings: []`
payload.

`check_id` uses the `doctor-llm-objective-` prefix to
distinguish from the static-phase and subjective-phase check
IDs; the suffix encodes the dimension and (where applicable)
the classification — e.g.,
`doctor-llm-objective-open-spec-pr-red-ci`,
`doctor-llm-objective-open-spec-pr-green-unmerged`,
`doctor-llm-objective-open-spec-pr-merge-conflict`.

## Failure modes

- **Schema-violation retry.** Same as the other LLM-driven
  prompts. The doctor SKILL.md re-invokes with the error
  context.
- **`gh` unavailable.** Per the open-spec-PR dimension's
  applicability predicate: emit `findings: []` and surface a
  structured `info`-level log line. Do NOT emit a `skipped`
  finding; the dimension is intentionally silent when its
  precondition does not hold.
- **`gh` transient error (auth lapse, rate-limit, network
  partition).** Treat the same as `gh unavailable`: emit no
  findings and surface a structured `info`-level log line
  identifying the failure mode. Transient errors are NOT
  doctor failures; the user re-runs doctor when the underlying
  condition clears.
- **Large open-PR set.** When the spec-branch open-PR set is
  large enough that exhaustive classification would exceed
  reasonable LLM context, the prompt SHOULD emit findings for
  the highest-severity classifications first (merge-conflict
  and red-ci before green-unmerged) and surface a summary
  finding noting the partial coverage. Re-run doctor for
  full coverage once the highest-severity items are resolved.
- **Empty / clean state.** When the prompt's review surfaces
  no issues (no open spec PRs, or all open spec PRs are in
  transient in-flight states that match none of the
  classification clauses), emit `findings: []`. The doctor
  SKILL.md surfaces this as "all objective checks passed"
  without per-finding dialogue.
