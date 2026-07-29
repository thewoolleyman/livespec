---
proposal: public-api-consumed-across-a-boundary.md
decision: accept
revised_at: 2026-07-29T04:32:26Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5-rop-railway-enforcement
---

## Decision and Rationale

ACCEPTED under the delegated accept/reject authority granted 2026-07-29 for the rop-railway-enforcement thread, extended to the livespec core spec tree. The rule set already stated the narrow spelling of this criterion (a _-prefixed name is not public regardless of __all__); this generalizes it from a SPELLING to the SUBSTANCE, and clause 0 preserves the ratified narrow rule verbatim in meaning rather than deleting it alongside its generalization.

Accepted on measurement rather than argument. Of 43 current offenders in livespec-dev-tooling the criterion classifies 9 as process entry points, 8 as public by product import, 1 as public via a distributed test harness, and removes 25 as test-visibility exports; the arithmetic is exact (9+8+1+25=43).

FLEET-WIDE SCOPE IS THE LOAD-BEARING PART and it was paid for. A repo-local reading of the same oracle classified parse_manifest as non-public; a hook in livespec-orchestrator-beads-fabro imports it, and its conversion turned that repo’s master RED. A criterion right about 40 functions and wrong about the ones crossing repo boundaries is worse than none, because it is confidently wrong exactly where the blast radius is largest.

THE COST IS RECORDED IN THE RATIFIED TEXT, NOT ONLY HERE: this materially shrinks enforcement scope (25 of 43 in one repo), the tightening half has ZERO measured effect today, and the static oracle cannot see dynamic reach. All three are stated in the text so a later reader does not rediscover them as surprises. The split-vantage clause is what keeps the fleet-wide claim honest: a repo-local check structurally cannot see a sibling’s import, so the criterion would otherwise assert a guarantee nothing computes — the manufactured-confidence failure this rule set exists to remove.

## Resulting Changes

- non-functional-requirements.md
