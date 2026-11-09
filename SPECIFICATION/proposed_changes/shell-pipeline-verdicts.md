---
topic: shell-pipeline-verdicts
author: claude:fleet-flaky-tests
created_at: 2026-11-09T18:51:14Z
---

## Proposal: A pipefail shell script judges a pipeline only from a reader that drains its input

### Target specification files

- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md

### Summary

Add one paragraph to `### Shell and Justfile discipline`: a governed shell file whose option policy enables pipefail judges a pipeline only from a reader that drains its whole input, never from an early-exiting reader such as `grep -q` or `head -n 1`, and gives the same verdict on an input larger than a pipe buffer. Add its scenario group to scenarios.md. Every fleet repository then inherits the rule that three repositories have each restated locally.

### Motivation

Fleet-wide end state for plan fleet-flaky-tests (epic livespec-dev-tooling-zwveqp), asked for by legacy-coordinator-agent under its rule K on 2026-11-09. The pipefail early-exit-reader flake was swept repository by repository: livespec-dev-tooling ratified it locally as non-functional-requirements.md "## Shell script pipeline verdicts" (livespec-dev-tooling-y53wpo, -ftgiu4, -mfk3h4, -leok3r); livespec-orchestrator-beads-fabro's share bd-ib-tcfwol cited its own "## Provisional fleet launch scripts"; livespec-orchestrator-git-jsonl's bd-gj-3oh5tk cited "## Inherited from livespec" although core states no such rule; and livespec-overseer's share overseer-ng3b3w was refused at the R316 Definition of Done preflight on 2026-11-09T18:31:31Z because no overseer heading governed it, which needed a repository-local mirror (livespec-overseer#2911, proposal shell-script-pipeline-verdicts). Core's `### Shell and Justfile discipline` already mandates pipefail in every governed Bash script and binds every fleet repository, so the hazard pipefail creates belongs beside that mandate. This proposal does not block overseer-ng3b3w or any open item; it is filed at a low band.

### Proposed Changes

In SPECIFICATION/non-functional-requirements.md, `### Shell and Justfile discipline`, insert this paragraph immediately after the paragraph that begins "A local errexit suspension MUST have a non-empty rationale":

> A governed shell file whose effective option policy enables pipefail MUST judge a pipeline's success only from a reader that consumes the pipeline's whole input. A pipeline whose exit status the script uses MUST NOT end in a reader that can exit before its writer finishes, such as `grep -q`, `grep --quiet`, `grep -m N`, `head -n N`, `head -c N` or an `awk` program that calls `exit`, because under pipefail the writer's SIGPIPE (exit 141) turns a match into a failure, and it does so only when the writer has more output than the reader read, which presents as a load-dependent flake. Where only a membership test is wanted, the script SHOULD use a here-string (`grep -q PAT <<<"$var"`), a reader that drains its input (`grep PAT >/dev/null`), or a grouping whose status excludes the writer's. Such a script MUST give the same verdict on an input larger than a pipe buffer (64 KiB) as on a small one. A pipeline whose status the script does not use, or one that runs where pipefail is off, is out of scope.

In SPECIFICATION/scenarios.md, append this scenario group at the end of the file:

## A pipefail shell script reports a match in a large input as a match

```gherkin
Feature: Pipeline verdicts under pipefail
  As a fleet maintainer
  I want a pipefail script's verdict to be independent of how much its writer prints
  So that a match is never reported as a failure under load

Scenario: A pipefail script reports a match in a large input as a match
  Given a governed shell file whose option policy enables pipefail and that tests whether its input contains a pattern
  When the input contains the pattern near its start and is larger than 64 KiB
  Then the script reports the pattern as present
  And its verdict is the same as for a 200-byte input that contains the pattern
```

The non-functional-requirements.md edit adds no `## ` heading. The scenarios.md group adds one, so the ratifying revise owes its heading-coverage entry in the same change.
