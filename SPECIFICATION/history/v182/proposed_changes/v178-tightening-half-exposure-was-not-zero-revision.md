---
proposal: v178-tightening-half-exposure-was-not-zero.md
decision: accept
revised_at: 2026-08-01T02:51:03Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5-rop-railway-enforcement
---

## Decision and Rationale

ACCEPTED. This consumes a correction THIS THREAD filed on 2026-07-29 (livespec PR #1834) and then left pending across two later revise passes of its own — including the v181 pass run minutes ago.

⛔ THE REASON IT SAT UNCONSUMED WAS A FALSE MECHANICAL PREMISE, NOT A JUDGEMENT CALL, and correcting the premise matters more than landing the text. The originating handoff records, as fact, that `a revise consumes one decision PER FILE — so revising means adjudicating both` of the two unrelated pending proposals, and declined on that basis because those two are other work's to judge. THAT IS FALSE. `_write_and_move_per_decision` iterates the DECISIONS supplied, not the directory, so a revise consumes exactly the topics named and leaves every other pending file untouched. Established by reading the implementation and then VERIFIED EMPIRICALLY TWICE — the v181 pass named one topic, and all three other files were still pending in `proposed_changes/` both in the worktree and on merged master afterwards. So the overreach the thread was avoiding was never on offer, and a true finding sat filed-as-wrong for two passes because nobody re-tested the belief that blocked it.

THE CORRECTION IS LOAD-BEARING, NOT TIDINESS. The false paragraph tells a planner the tightening half's exposure is ZERO and that it is `a guard against future gaming, not a correction of present state`. Both halves are wrong, and the second is the one that does damage: every fan-out estimate for the remaining governed repos was computed assuming this criterion only ever REMOVES functions from scope. It also ADDS them — a sibling has already measured HIGHER than its pre-criterion figure — and this thread has retired two fleet-wide counts for exactly that reason. A ratified sentence saying the tightening half touches nothing is precisely what would let the next planner skip the re-measurement.

ACCEPTED WITHOUT SOFTENING, as the proposal requires. The figure is recorded as WRONG WHEN WRITTEN rather than superseded, because the reason it was wrong is the part that generalizes: A CLAUSE'S EXPOSURE CANNOT BE MEASURED BEFORE THE CLAUSE IS MECHANIZED. What was measured in its place was what the OLD `__all__`-membership proxy could see — exactly the set the tightening half exists to look past — so it was a prediction wearing a measurement's clothes. `fetch_manifest` is named, and named as NETWORK-reaching, because that is what makes it a conversion candidate under v179 member 1 clause (c) rather than an exemption candidate, and what makes the error consequential rather than cosmetic.

⛔ AND THE CLAUSE ITSELF IS UNCHANGED. Only the paragraph estimating its blast radius was wrong. The corrected text says so explicitly, because a reader who takes this as evidence against the clause has taken it backwards — the clause found a real unrailed network-reaching public function on its first run.

## Resulting Changes

- non-functional-requirements.md
