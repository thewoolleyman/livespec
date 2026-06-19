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
- The spec tree's `<spec-root>/history/` snapshots (for the
  since-version delta dimension's live-vs-prior diff). The
  doctor prose threads the resolved `<prior-vN>` and its
  history snapshot into this phase per `.claude-plugin/prose/doctor.md`
  Steps 6-7; this prompt assumes those reads are available.

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
prompt declares two dimensions: the open-spec-PR dimension and
the since-version delta-review dimension. The prompt MAY also
carry additional dimensions later.

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

### 2. Since-version delta review (skill-baked — only when a prior `vNNN` exists)

This dimension reasons ONLY about the regions of the spec tree
that CHANGED since the immediately-prior history snapshot. It
catches drift that whole-tree review tends to miss because the
unchanged surface dilutes attention: behavior introduced by the
latest revise pass that never grew a clause or scenario, a clause
landed in the wrong functional / non-functional bucket, and — in a
multi-repo project — realization mechanism that belongs in the
orchestrator's own spec rather than core. It is deterministic per
its mechanism: the diff between the live spec tree and the prior
snapshot is reproducible.

#### Applicability predicate

Run this dimension only when a prior history snapshot exists for
the spec tree. Resolve `<prior-vN>` the SAME way the revise prose
does (`.claude-plugin/prose/revise.md` Step 13(d), "Compute
`<prior-vN>`"): read the `vNNN` directory names under
`<spec-root>/history/`, identify the most-recently-cut `v<N>`, and
take `<prior-vN>` as the version immediately preceding it — the
highest `vNNN` BEFORE the just-cut `v<N>`. When only `v001` exists
(no prior version to diff against), this dimension is a NO-OP: emit
NO findings and surface the no-op as a structured `info`-level log
line (e.g., `info: since-version delta dimension skipped — only v001 present`).
The log line MUST NOT be emitted as a finding and MUST NOT lift any
exit code.

#### Diff mechanism

When the applicability predicate holds, compute the diff between
the live spec tree and `<spec-root>/history/<prior-vN>/`. Each
history snapshot is a full copy of the template-declared spec
files, so the diff is a per-file comparison of the live file
against its `<prior-vN>` counterpart (the doctor LLM-driven phase
is already permitted to read files and run tooling per the
LLM-phase contract; the static phase remains network-free).
Reason ONLY about the changed regions — added or modified clauses,
new sections, new scenarios. Unchanged regions are OUT of scope for
this dimension; whole-tree review is the other dimensions' job.

#### Per-finding classification

For each changed region, emit AT MOST ONE finding per the first
matching clause below (evaluated in order):

- **New behavior with no clause/scenario.** A changed region
  introduces load-bearing behavior — an observable input→output, a
  state transition, an error path, or an invariant the
  implementation must honor — that is NOT expressed as a BCP14
  `MUST`/`SHOULD` clause, OR is so expressed but has NO matching
  `## Scenario` in `scenarios.md`. Emit
  `doctor-llm-objective-delta-uncovered-behavior` with severity
  `medium`.
- **Wrong functional / non-functional bucket.** A changed clause
  sits in the wrong file per the boundary litmus in
  `SPECIFICATION/non-functional-requirements.md` §"Boundary" — e.g.,
  family-infrastructure / contributor-facing content landed in a
  user-facing file (`spec.md` / `contracts.md` / `constraints.md` /
  `scenarios.md`), or a contract a third-party consumer inherits
  landed in `non-functional-requirements.md`. Emit
  `doctor-llm-objective-delta-wrong-bucket` with severity `medium`.
- **Wrong repo (multi-repo projects only).** In a project whose
  `.livespec.jsonc` declares cross-repo targets, a changed region
  specifies realization mechanism (orchestration loop, dispatcher
  invocation surface, sandbox janitor gating) that belongs in the
  orchestrator's OWN specification rather than core's contract
  surface. Emit `doctor-llm-objective-delta-wrong-repo` with
  severity `medium`. In a single-repo project this clause never
  fires.

Changed regions that match none of the above are NOT findings; the
dimension is silent for routine clause edits, prose polish, and
already-covered behavior.

#### Per-finding fields

- `path`: the live spec file containing the changed region.
- `line`: the line in the live spec file (best effort; `0` when not
  pinnable to a single line).
- `spec_root`: the spec tree path that surfaced the finding.
- `proposed_change_hint` (passed to Step 11): a one-sentence
  remediation hint scoped to the classification — for
  delta-uncovered-behavior, re-state the changed prose as a BCP14
  clause or draft the missing Gherkin scenario; for
  delta-wrong-bucket, move the clause to the file the boundary
  litmus indicates; for delta-wrong-repo, relocate the realization
  mechanism into the orchestrator's own specification.

### Per-dimension scoring

For each finding, emit:

- `dimension`: one of `open-spec-pr-status`,
  `since-version-delta` (future dimensions add to the
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
`doctor-llm-objective-open-spec-pr-merge-conflict`,
`doctor-llm-objective-delta-uncovered-behavior`,
`doctor-llm-objective-delta-wrong-bucket`,
`doctor-llm-objective-delta-wrong-repo`.

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
- **No prior version (since-version delta dimension).** When
  only `v001` exists under `<spec-root>/history/`, the
  since-version delta dimension is a no-op: emit `findings: []`
  for that dimension and surface a structured `info`-level log
  line. Do NOT emit a `skipped` finding; the dimension is
  intentionally silent with no prior snapshot to diff against.
- **Empty / clean state.** When the prompt's review surfaces
  no issues (no open spec PRs, or all open spec PRs are in
  transient in-flight states that match none of the
  classification clauses), emit `findings: []`. The doctor
  SKILL.md surfaces this as "all objective checks passed"
  without per-finding dialogue.
