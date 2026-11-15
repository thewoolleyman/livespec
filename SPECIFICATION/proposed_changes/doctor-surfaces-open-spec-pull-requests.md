---
topic: doctor-surfaces-open-spec-pull-requests
author: claude-opus-5-5 (livespec-t4pdc4)
created_at: 2026-11-15T04:55:09Z
---

## Proposal: Doctor objective phase surfaces open spec pull requests

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Add a contract clause under contracts.md `## Built-in template contracts` requiring the doctor LLM-driven objective phase (as carried by the `livespec` and `livespec-with-diagrams` built-in templates' objective-checks prompt) to surface every open pull request whose head branch matches the project's propose-change branch prefix (default `spec/*`), with each PR's number, mergeability and check state; to discover them with a filter that actually matches the prefix; and to surface a gh or network failure as a degraded-check warning rather than a silent empty result. Add one scenario in scenarios.md for the case where open `spec/*` pull requests exist and doctor reports them.

### Motivation

Carrier work-item livespec-t4pdc4. The open-spec-PR dimension of the built-in objective-checks prompt discovers candidates with `gh pr list --state open --head 'spec/*' ...`. gh's `--head` flag takes an exact branch name and accepts no glob, so the query exits 0 with `[]` on every run: measured 2026-11-15 against livespec-orchestrator-beads-fabro, the glob form returned `[]` while an unfiltered open-PR listing filtered on `headRefName` by the `spec/` prefix returned 8 open spec/* PRs (#5293, #5281, #5180, #5120, #5083, #5061, #5048, #5005). The check is therefore silent in every consumer, and red-CI, green-unmerged and merge-conflict spec PRs are never reported. No SPECIFICATION clause states this doctor check today, so nothing pins the discovery requirement and the defect could ship unnoticed. The nearest clause, spec.md `### propose-change operation-prose responsibilities` (the propose-change in-flight survey), governs propose-change, not doctor, and is deliberately left unchanged. The objective-checks prompt is template-internal behavior a consumer inherits when selecting the `livespec` template, which is exactly the scope of `## Built-in template contracts`; the fix belongs in core because every consumer inherits it through the built-in template.

### Proposed Changes

1. In `SPECIFICATION/contracts.md` §"Built-in template contracts", insert the following new paragraph immediately after the `**`livespec` template.**` paragraph (before the `**`minimal` template.**` paragraph):

> **Open spec pull requests in the doctor objective phase.** For every built-in template whose `template.json` declares a non-`null` `doctor_llm_objective_checks_prompt` (`livespec` and `livespec-with-diagrams`), the doctor LLM-driven objective phase MUST, when the project is GitHub-hosted and the `gh` CLI is available and authenticated, surface every open pull request whose head branch matches the project's propose-change branch prefix (default `spec/*`), and for each surfaced pull request report its number, its mergeability, and its check state; the template's per-PR classification then determines which surfaced pull requests additionally become findings. Discovery MUST use a filter that actually matches the prefix — list the open pull requests and filter each one's `headRefName` by the prefix — and MUST NOT pass a glob to `gh pr list --head`, which accepts only an exact branch name and silently returns an empty list for a glob. A `gh` or network failure during discovery (`gh` exiting non-zero, missing auth, no network) MUST be surfaced as a degraded-check warning naming what failed, and MUST NOT be reported as an empty result; an empty result is reported only when the listing succeeded and no open pull request matched the prefix.

2. In `SPECIFICATION/scenarios.md`, append a new H2 scenario:

~~~~markdown
## Doctor surfaces open spec pull requests

```gherkin
Feature: Doctor surfaces open propose-change pull requests
  As a maintainer running doctor on a GitHub-hosted livespec project
  I want every open spec/* pull request reported with its state
  So that red-CI, merge-conflicted and green-but-unmerged spec work is visible

Scenario: Open spec/* pull requests exist and doctor reports them
  Given a GitHub-hosted project using the livespec built-in template with an authenticated gh CLI
  And the repository has open pull requests on head branches spec/alpha and spec/beta
  And an open pull request on head branch feature/other
  When the doctor LLM-driven objective phase runs
  Then it reports the pull requests on spec/alpha and spec/beta with each one's number, mergeability and check state
  And it does not report the pull request on feature/other
```
~~~~

The revise pass that accepts this proposal MUST co-edit `tests/heading-coverage.json` with a `TODO` entry for the new `scenarios.md` heading `Doctor surfaces open spec pull requests` whose `reason` names the integration tier (path `../tests/heading-coverage.json` in `resulting_files[]`). `## Built-in template contracts` keeps its heading, so no heading-coverage change is needed for contracts.md.

3. Implementation surface the clause governs (both template copies MUST be brought into conformance by the implementing work-item, not by this spec change):

- `.claude-plugin/specification-templates/livespec/prompts/doctor-llm-objective-checks.md` — the discovery command at line 88 (`gh pr list --state open --head 'spec/*' --json number,state,statusCheckRollup,headRefName,createdAt,updatedAt,mergeable`) and the claim at line 91 ("The `--head 'spec/*'` filter scopes the query to spec-revise branches").
- `.claude-plugin/specification-templates/livespec-with-diagrams/prompts/doctor-llm-objective-checks.md` — the same discovery command at line 83 and the same claim at line 86.

In each copy, replace the `--head 'spec/*'` discovery with an unfiltered open-PR listing (for example `gh pr list --state open --limit <N> --json number,state,statusCheckRollup,headRefName,createdAt,updatedAt,mergeable`) filtered client-side on `headRefName` starting with the propose-change branch prefix, add the report of every surfaced PR's number, mergeability and check state, and replace the silent no-op on a `gh` failure during discovery with a degraded-check warning.
