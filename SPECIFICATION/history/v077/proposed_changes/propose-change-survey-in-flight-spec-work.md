---
topic: propose-change-survey-in-flight-spec-work
author: claude-opus-4-7
created_at: 2026-05-25T03:16:39Z
---

## Proposal: propose-change must enumerate in-flight propose-change branches and open spec-changing PRs before authoring

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a normative rule to contracts.md requiring `/livespec:propose-change`'s pre-authoring phase to enumerate (a) sibling propose-change branches on the remote and (b) open pull requests touching the spec tree, and to surface the enumeration to the user so the new proposal can be aligned with, modified to accommodate, or explicitly supersede the in-flight design. Symmetric to the cross-tree narration discipline already required of `/livespec:revise`.

### Motivation

Captured originally as memo `mm-jdmtgc` (2026-05-23). Observed: two competing v071 designs for cross-repo work-item dependency awareness landed on different branches. PR #160 (`spec/revise-v071-next-and-cross-repo-deps`) chose the resolver-skill design (new `depends_on_external` + `external_dep_cache` fields, new `/livespec:resolve-cross-repo-deps` skill, `next` stays local-only); the later-authored `cross-project-interdependencies` propose-change (merged as commit `38e9562`) chose the syntactic-extension design (extend existing `depends_on` with `<repo-slug>:<work-item-id>` colon form, widen `next` to walk all manifest stores). The two designs are architecturally opposed on the line-252 pin ("next stays local-only"). Neither propose-change session surveyed the other; neither revise session had visibility into the other. Steering at revise can catch the symptom retroactively, but the deeper structural fix is at propose-change: enumerate open propose-change branches + open spec-changing PRs before authoring, so the new proposal either aligns, modifies, or explicitly supersedes the in-flight design. Related: the `/livespec:revise` SKILL.md already enumerates sibling sub-spec proposed_changes/ queues for cross-tree narration — extending this discipline to "across-branch in-flight propose-change drift" is a natural widening.

### Proposed Changes

Add a new normative subsection under SPECIFICATION/contracts.md §"Cross-boundary handoffs" (or a new §"propose-change in-flight survey") that requires `/livespec:propose-change`'s pre-authoring phase to:

1. Enumerate remote branches matching `spec/*` or any configured propose-change branch prefix.
2. Enumerate open pull requests whose diff touches the spec tree (any `<spec-root>/**.md` file).
3. Surface the enumeration to the user with a brief characterization of each in-flight item (topic slug, branch/PR title, key sections touched).
4. Pause for the user to decide whether the new proposal aligns with, modifies, or explicitly supersedes each in-flight design.

The rule is symmetric to the existing cross-tree narration discipline that `/livespec:revise` already applies to sibling sub-spec proposed_changes/ queues. The enumeration MAY be skipped only when the user explicitly types `--no-survey` (or similar opt-out flag) on the propose-change invocation, logged for audit.

Wrapper enforcement: `bin/propose_change.py` SHOULD perform the enumeration automatically and emit the characterized list to stderr before any findings-JSON write. SKILL.md prose SHOULD route the user through the alignment dialogue before invoking the wrapper.
