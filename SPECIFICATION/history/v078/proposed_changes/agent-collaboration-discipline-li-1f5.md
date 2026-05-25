---
topic: agent-collaboration-discipline-li-1f5
author: claude-opus-4-7
created_at: 2026-05-25T05:12:26Z
---

## Proposal: agent-collaboration-discipline-destructive-cli-wrapping

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a new H3 §"Agent collaboration discipline" subsection under §"Spec" in non-functional-requirements.md, with an H4 §"Destructive-default CLI wrapping" rule requiring that destructive-default external CLIs (those whose default behavior writes, commits, deletes, or mutates state without explicit opt-in) be invoked through project-local scripted wrappers (`just` recipes or `dev-tooling/` scripts) that pin safe flags. Direct CLI invocation by agents in agent-facing prose is forbidden when a wrapper exists; agents MUST prefer the wrapper.

### Motivation

Captured in li-1f5 item 1 (filed 2026-05-09 after PR #42's bootstrap session where `bd init`'s auto-commit-to-master surprised the user). The principle generalizes from beads (since-superseded by livespec-impl-plaintext) to every destructive-default tool the project consumes. Setup-beads.sh already enforced this for `bd init`; the spec rule generalizes the discipline so future tool additions don't repeat the failure mode.

### Proposed Changes

Insert a new H3 subsection at the end of `## Spec` in `non-functional-requirements.md` (after `### Codex dogfooding compatibility`, before `## Contracts`) titled `### Agent collaboration discipline`. Under it, add an H4 §"Destructive-default CLI wrapping":

> Destructive-default external CLIs — those whose default behavior writes, commits, deletes, or otherwise mutates persistent state without explicit opt-in — MUST be invoked through project-local scripted wrappers (`just` recipes under `justfile`, scripts under `dev-tooling/`, or equivalent) that pin safe flags. The wrapper MUST declare which flag combinations are considered safe-by-default and MUST NOT pass through arbitrary flag overrides. Agent-facing prose (skill prompts, CLAUDE.md, AGENTS.md, hook scripts) MUST refer to the wrapper, not the underlying CLI, whenever a wrapper exists for that tool. When a new destructive-default tool joins the project's toolchain, a wrapper MUST be authored before any agent-facing reference to the tool is added.
>
> The discipline mechanically prevents a class of agent-surprise failures: a tool whose default behavior is surprising to the user gets wrapped once, in one place, and every subsequent agent invocation runs through the safe-flag pin instead of relying on the agent's memory of the right flags. Realization of this rule (e.g., a `dev-tooling/checks/no_direct_destructive_cli.py` enforcement check) is tracked separately and lands once the rule is in spec.

## Proposal: agent-collaboration-discipline-verify-before-referring

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add an H4 §"Verify before referring" rule under the new §"Agent collaboration discipline" subsection. Agents MUST verify that a tool, skill, slash-command, or feature exists in the current environment AND does what is being claimed BEFORE referring to it by name in agent-facing prose or dialogue. Vague capability-name-dropping (e.g., suggesting `/schedule` as a follow-up without confirming it fits the situation) is forbidden.

### Motivation

Captured in li-1f5 item 2 (filed 2026-05-09 after the agent suggested `/schedule` as a follow-up mechanism without confirming it fit the situation; `/schedule` triggers on date/time, not conditions like "after PR #42 merges"). The failure mode is generic: agents trained on a broad capability vocabulary will reach for capability names that don't apply to the situation at hand, and the user has to redirect. The spec rule codifies the verify-then-refer discipline.

### Proposed Changes

Under the new `### Agent collaboration discipline` H3 (per the destructive-CLI-wrapping proposal), add an H4 §"Verify before referring":

> Agents MUST verify that a tool, skill, slash-command, plugin, or feature exists in the current environment AND does what is being claimed BEFORE referring to it by name in agent-facing prose, skill output, or dialogue suggestions. Verification means at minimum (a) confirming the name resolves in the active environment (e.g., the slash-command appears in the available-skills list; the CLI is on `$PATH`; the tool's help text matches the claimed semantics) and (b) confirming the capability's actual behavior matches the proposed use (e.g., a scheduler that fires on dates does not satisfy a condition-based trigger requirement).
>
> When verification is impractical mid-response (e.g., the agent cannot reasonably probe an external system inline), the agent MUST hedge explicitly: "I'd need to verify whether `<X>` applies here" rather than offering `<X>` as a confident path. Confident references to nonexistent or misapplied capabilities erode user trust and impose cleanup work the user shouldn't have to do.

## Proposal: agent-collaboration-discipline-completion-includes-workspace-cleanup

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Extend `### Definition of Done` (or add a paired H4 under the new §"Agent collaboration discipline") to require that agent-claimed completion includes (a) persisting substantial work artifacts before the message containing them is sent, and (b) restoring workspace state — switching back to master, fast-forwarding, deleting feature branches — rather than typing the cleanup commands as instructions for the user to run.

### Motivation

Captured in li-1f5 item 3 (filed 2026-05-09, expanded 2026-05-09). Two observed failure modes: (1) the auto-memory-migration audit (42-entry breakdown into 9 themed proposals) was produced as a chat message and would have been lost on conversation compaction had the user not pushed back; (2) three PRs landed during PR #42 / #43 / #44's session left the user on the merged feature branch with agent typing `git checkout master && git pull` instructions instead of running them. Both failures share the same root cause: treating chat text as a substitute for the mechanical action. This is already partially captured in the user's auto-memory as `feedback_end_on_main_branch`; promoting it to a spec rule makes it normative.

### Proposed Changes

Add an H4 §"Completion includes persistence and workspace cleanup" under the new `### Agent collaboration discipline` H3:

> Agent-claimed completion includes both artifact persistence and workspace cleanup. Substantial work artifacts (audit tables, multi-step plans, decision matrices, migration breakdowns — anything whose value extends beyond the current conversation turn) MUST be persisted (filed as a work-item via the impl-plugin, committed to a tracked file, or otherwise written to durable storage) BEFORE the message containing them is sent. Chat-only delivery is reserved for ephemeral, single-decision analysis.
>
> Workspace cleanup MUST be a part of "done" rather than a list of instructions appended to a completion message. When work goes through intermediate states that aren't the natural post-completion baseline (feature branches during PR work, checked-out hotfix branches, modified working trees, untracked test artifacts), the agent's "done" state MUST include the explicit cleanup actions: (a) after a PR merges, switch back to the project's default branch, fast-forward, delete the local feature branch, delete the remote branch (unless `gh pr merge --delete-branch` already did so); (b) after a destructive intermediate (`git reset --hard`, working-tree wipe, etc.), the "done" state is the recovered + re-validated state, not the destructive operation itself; (c) "I'll leave you to verify" is acceptable for verification steps requiring genuine user judgment (visual UI checks, subjective output review) but NOT as a stand-in for mechanical workspace hygiene the agent could perform.
>
> This widens `### Definition of Done` (above): the existing DoD captures the mechanical CI/test/coverage gates; this rule captures the workflow-hygiene gates. Both MUST be satisfied before an agent claims a task complete.
