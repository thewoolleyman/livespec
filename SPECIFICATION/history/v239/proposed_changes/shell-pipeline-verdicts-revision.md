---
proposal: shell-pipeline-verdicts.md
decision: modify
revised_at: 2026-11-09T20:40:29Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5:fleet-flaky-tests
---

## Decision and Rationale

The proposal places a fleet-wide hazard beside the pipefail mandate that creates it: core's Shell and Justfile discipline already requires pipefail in every governed Bash script, so the early-exiting-reader rule that three repositories restated locally belongs there, where every fleet repository inherits it. It respects all three authoring splits: a behaviour clause with a scenario, a contributor-facing constraint in non-functional-requirements.md, and a repository-agnostic rule. It is modified rather than accepted because a pre-merge doctor walk, which measured the bash behaviour, found the proposal's scope clause ambiguous: 'a pipeline whose status the script does not use' left the errexit case unclassified, although an errexit script that assigns `$(cmd | head -n 1)` aborts with 141 on a large output.

## Modifications

(a) The paragraph defines when a file uses a pipeline's status: when it tests it, captures it, returns it as the last command of a function whose status the caller uses, or runs it where errexit is in effect, including a command substitution stored by a plain assignment. A status masked by local, export or declare does not reach errexit. (b) The list of early-exiting readers adds `grep --max-count=N`, `head -N`, a `sed` program that quits, and `read`; the doctor walk measured each returning 141. (c) The status-excluding grouping is a MAY for taking the first part of an output, shown as `first=$({ cmd || true; } | head -n 1)`, with its cost stated: it also discards the writer's own failure. The membership-test remedies stay SHOULD. (d) The paragraph states that 64 KiB is the size at which a single-write writer fails reliably, and that a multi-write writer can fail on a smaller input, so a passing small input proves nothing. (e) scenarios.md gains a second scenario in the new group, for the errexit first-line case.

## Resulting Changes

- non-functional-requirements.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-09T20:39:57Z
verdict: NO BLOCKERS
proposal_stem: shell-pipeline-verdicts
content_digest: 4690b50564f853b3827aa1f270500b3777b6f9c2bac85a8fc8fa45db2fe11e96
