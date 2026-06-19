---
topic: ci-telemetry-export
author: livespec-claude-opus-4-8
created_at: 2026-06-19T18:27:03Z
---

## Proposal: CI telemetry export

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Codify the now-deployed closed-loop CI-telemetry export as a durable non-functional requirement: every livespec-governed repo's CI exports per-run job timings to the family Honeycomb environment, the export self-verifies receipt and fails its own job (so the pipeline cannot die silently), it is gated to master-push/merge_group only, it authenticates with a dedicated write-only least-privilege per-repo ingest key (never the management key), and the impl-plugin copier template carries it so generated siblings inherit it.

### Motivation

A closed-loop CI-telemetry export now ships in all six family repos (livespec core PR #477 + 5 siblings + the impl-plugin template). The durable contract it establishes — family-wide CI observability with in-band, closed-loop failure detection and write-only ingest-key discipline — belongs in core's non-functional requirements as its canonical home, so the requirement (not the bash/YAML implementation) is enforceable and inherited family-wide. It also supersedes an interim tmp/ harvester that died silently because nothing watched for its absence.

### Proposed Changes

Add a new `### CI telemetry export` section to `SPECIFICATION/non-functional-requirements.md`, under the `## Contracts` top-level section, immediately after `### Enforcement-suite invocation` and before `### Orchestrator contract delegation`. The section is an H3 sibling of the surrounding `### ` Contracts sub-sections (so no new `## ` heading is introduced and no `tests/heading-coverage.json` co-edit is required).

The section codifies, at contract/architecture level (no bash, no YAML), the now-deployed family-wide CI-telemetry export:

1. **Requirement.** Every livespec-governed primary repo's CI MUST export each completed run's per-job timings to the family observability surface (the shared Honeycomb environment): one root span per run plus one child span per completed job, tagged with commit, branch, event, and conclusion, landing every repo's runs in one shared dataset under a family `service.namespace`. OTLP is named as the encoding but framed as an implementation detail.

2. **Closed-loop self-verification.** The export MUST be closed-loop: the same run that produces the data MUST confirm the surface accepted it and MUST fail its own job when confirmation does not arrive (non-success ingest, or reported rejection). Rationale: a CI run is the deterministic signal its own telemetry should exist, so absence is detectable in-band; a broken export reddens the run and fires the existing CI-failure notification instead of dying silently. Explicitly records that this replaced a predecessor harvester that failed silently with nothing watching for its absence.

3. **Gating.** master-push / merge_group ONLY (never pull_request, so zero PR latency); depends on the check jobs; runs even when an upstream check failed; excludes its own job.

4. **Ingest-key discipline.** A dedicated, least-privilege, write-only ingest key (send-only, cannot read/query/administer or create datasets); the management/query key MUST NEVER appear on the CI path. The key is a family-scoped secret following §"Family secrets — 1Password Environment as canonical source" (a derived per-repo GitHub Actions projection, named per the `HONEYCOMB_GITHUB_CI_INGEST_KEY_<CONSUMER>` convention mirroring the per-consumer Anthropic-key naming), never committed or echoed; per-repo rather than org-level because the family owner is a personal account with no org secret tier.

5. **Template inheritance.** The export script and its `ci.yml` job are carried by the impl-plugin copier template per §"Shared content sync — copier template", so every generated `livespec-impl-*` sibling inherits it; a generated repo provisions its own per-repo ingest-key secret, and a repo opting out removes the export job rather than leaving it wired against a missing secret.

The exact final section text is supplied as the `resulting_files[]` content in the paired revise pass.
