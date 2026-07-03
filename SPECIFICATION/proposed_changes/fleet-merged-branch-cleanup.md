---
topic: fleet-merged-branch-cleanup
author: claude-fable-5
created_at: 2026-07-03T22:41:56Z
---

## Proposal: Fleet merged-branch cleanup — delete_branch_on_merge as a fleet obligation

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Add a 'Merged-branch cleanup' rule paragraph to non-functional-requirements.md §'Fleet membership contract': every fleet-array repo MUST keep the GitHub delete_branch_on_merge repository setting enabled, enforced by a manifest-driven dev-tooling fleet-conformance Verifier (always wired into just check, one warn-vs-fail env lever for token-less contexts), with wire-fleet-member's reconcile mode ensuring the setting for newly wired members. Adopters are explicitly out of scope — the Verifier binds the fleet array only.

### Motivation

Maintainer directive (2026-07-04, plan/fleet-merged-branch-cleanup thread, epic livespec-ixap): merged-PR head branches were cleaned up inconsistently — only two of eight fleet repos had the setting, and the other six accumulated ~460 stale remote branches. The setting was rolled out fleet-wide on 2026-07-04 and the enforcement Verifier plus provisioning parity are filed as dev-tooling work-items (livespec-dev-tooling-g8j, livespec-dev-tooling-5o2). The invariant stays meaningful after rollout — it binds every future fleet repo — so it belongs in the fleet-membership contract as a durable obligation; without it the Verifier would enforce a rule no spec records. The adopter exclusion records the maintainer's 2026-07-04 adopter-scope decision (adopters own their repos; openbrain codified its own copy at its SPECIFICATION/constraints.md §'Merged-branch cleanup', accepted there as v093).

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md`, inside `### Fleet membership contract`, insert a new bold rule paragraph immediately AFTER the '**Obligations per repo class.**' paragraph and immediately BEFORE the '**Fleet-conformance enforcement.**' paragraph, with exactly this content:

```markdown
**Merged-branch cleanup.** Every `fleet`-array repo MUST keep the GitHub repository setting `delete_branch_on_merge` enabled, so the head branch of every merged pull request is deleted automatically at merge and stale remote branches do not accumulate (rolled out fleet-wide 2026-07-04; epic `livespec-ixap`). The dev-tooling fleet-conformance Verifier MUST assert the setting for every `fleet`-array repo — manifest-driven like the other fleet-conformance checks, always wired into `just check`, with one warn-vs-fail env lever for token-less contexts (no GitHub token → WARN with the finding still printed; token present → FAIL). Adopters are deliberately NOT bound: the `adopters` array is not consulted (adopters carry no per-class obligations, consistent with the **Adopters** rule above); an adopter that wants the invariant records it in its own spec (openbrain: its `SPECIFICATION/constraints.md` §"Merged-branch cleanup"). The `wire-fleet-member` reconcile mode MUST ensure the setting for a newly wired member, so a fresh repo passes the Verifier from birth per the **Repo birth procedure** rule.
```
