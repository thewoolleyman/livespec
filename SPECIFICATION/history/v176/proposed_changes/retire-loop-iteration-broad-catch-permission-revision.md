---
proposal: retire-loop-iteration-broad-catch-permission.md
decision: accept
revised_at: 2026-07-26T13:23:28Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Maintainer ruling 2026-07-26: the daemon loop-iteration broad catch is REMOVED, not mechanized -- 'let it crash, systemd restarts', exactly one broad catch per program in main(). Options (A) file-scoped loop-body exemption, (B) loop-body exemption anywhere in source_trees, and (C) a new role key declaring loop position are ALL rejected: no new exemption shape, no widened position rule, no new config key. Amends four locations (lines 114, 651, 675, 783) rather than one, because a single-location edit would ratify a PARTIAL narrowing and leave the Linter rule set still listing the retired marker as a conforming escape. Re-derives four closed tallies: five standardized markers -> four; four supervisor/boundary/loop categories -> three; two categories outside the boundary-handler rule -> one; four review-enforced rules -> two. Folds in the livespec-dev-tooling-jjb enforcement-attribution correction, because it is literally the same two sentences the narrowing rewrites in BOTH sections and would otherwise be edited twice: exact marker wording and per-artifact sole cardinality are now MECHANIZED, per-supervision-loop cardinality DISSOLVED, and only flavor pairing plus per-flavor contract discharge remain review-enforced. TWO INDEPENDENT ADVERSARIAL REVIEWS were run on identical bytes and DISAGREED, which is why both were required: reviewer 1 returned NO-BLOCKERS; reviewer 2 found TWO real blockers, both in the proposal document and both my own errors -- a Sequencing enumeration that still listed livespec-driver-claude-jzy as remaining work after it had landed (commit 56269561), and a stale bare citation of the armed catch at supervisor.py:2779 when my own earlier changes had moved it to 2793. Both fixed before this accept, and every remaining cross-repo citation re-anchored to cite the enclosing FUNCTION first so it cannot rot the same way. Ordering satisfied: livespec-dev-tooling PR #681 retired the wording from the enforcement suite and inverted the test BEFORE this ratification, so at no point did the specification forbid what the suite still accepted.

## Resulting Changes

- non-functional-requirements.md
