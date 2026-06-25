---
proposal: structural-commit-refuse-hook.md
decision: accept
revised_at: 2026-06-25T22:29:25Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Increment 5 / milestone M2 of epic livespec-zs22 (sub-epic livespec-zs22.7, milestone livespec-zs22.7.3 — the M2-2 core PR). Rewrites the commit-refuse hook contract for the STRUCTURAL mechanism (refuse when git-dir == git-common-dir; a secondary worktree's git-dir differs) with a livespec.sandboxExempt git-config Exemption marker the hook BODY reads, retiring the livespec.primaryPath arming step (the console-incident root-cause: an installed-but-unarmed hook failed OPEN). Edits: (1) NFR §"Workflow discipline — spec-side changes" Primary-checkout commit-refuse hook rule -> structural detection, armed on install, plus the sandboxExempt Exemption paragraph; (2) NFR §"Commit-refuse hook bootstrap procedure" -> drop the primaryPath set from the contract clauses, replace the illustrative canonical-body snippet with the structural+sandboxExempt body that delegates to lefthook; (3) NFR §"Conformance Pattern" concern #1 -> the confirmed Option-A wording (one uniform body installed everywhere incl. the sandbox; Verifier stays simple and accepts both bodies through migration; Exemption = the marker the hook BODY reads); (4) contracts.md §"master-direct-uncommitted-spec-edits" -> repair the show-toplevel explanation to the structural git-dir==git-common-dir refuse (internal consistency; conclusion unchanged). Spec-side half of M2-2, co-landing with the core justfile/wrapper edits (git-hook-wrapper.sh -> structural body byte-identical to livespec-dev-tooling v0.18.0; just install-commit-refuse-hooks Installer recipe bootstrap delegates to; primaryPath write retired). Maintainer-confirmed Option A (2026-06-25). Touches existing sections only (no ## heading added/changed/removed), so tests/heading-coverage.json is unaffected. The §"primary-checkout-commit-refuse-hook-installed" invariant needs no change — its narration is already body-agnostic.

## Resulting Changes

- non-functional-requirements.md
- contracts.md
