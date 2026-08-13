# Adversarial review — round 5 DELTA confirmation (overseer-pfpfty.11)

**Scope:** NARROW delta confirmation of the `overseer-pfpfty.11` amendment
(repository `livespec-overseer`, PR #855) against the round-5 verdict's one
blocker — NOT a full round 6. Four points only, per the commissioning brief:
(a) new replace-pair fidelity, (b) applied-result seam, (c) Amendment-history
corrections, (d) no regression of round-5-confirmed facts.

**Review is READ-ONLY.** Nothing was edited, created, deleted, committed,
pushed, ratified, or filed in any tracked tree; no ledger access at all this
pass. This file is the only write.

**Performed by Fable 5 (`claude-fable-5`) on 2026-08-13**, continuing the
round-5 reviewer's own context (same instrument as round 5, by design of the
delta scope).

## Pinned read

| | |
|---|---|
| Brief's pin | merge sha `a81e0da33a3d662b32dcbb9b8e5e59c75b74eb1e`, proposal 770 lines, md5 `4bc3aef14e50774007d945a670a129de` |
| Verified | `a81e0da3` IS an ancestor of `origin/master`; the proposal at `a81e0da3` is 770 lines, md5 `4bc3aef14e50774007d945a670a129de`, and **byte-identical at the current `origin/master` tip** |
| Merge footprint | `a81e0da3` touches EXACTLY `SPECIFICATION/proposed_changes/planning-lane-realization.md` (70 insertions, 28 deletions); zero `SPECIFICATION/history/` paths — the carrier did not ratify |
| The four target spec files | md5-identical to the bytes round 5 verified (`spec.md` `c3901358…`, `contracts.md` `b58da93c…`, `constraints.md` `eb39bd10…`, `scenarios.md` `f92ef1ca…`) — the target side has not moved since round 5 |
| Byte-level delta | `diff` of the round-5 bytes (728 lines, md5 `5b26eff3…`) against the amendment: exactly six hunks — the Amendment-history round-5 record, the attestation sentences, the instrument-variation sentence, the two v011 corrections, the §"What round 5 changed" section, the target-count paragraph, and the new EDIT 3 replace-pair. **No other byte of the proposal changed**, which is what makes the narrow scope sound. |

## (a) The new replace-pair — PASS

The new pair (EDIT 3, proposal line 357, target 5 of 26) quotes the
tombstone-rationale sentence verbatim:

> This prohibition is load-bearing because of how discovery works. The
> archived-or-deleted test keys on the DIRECTORY alone, and discovery
> enumerates directories (the one bounded existence probe stated above
> notwithstanding).

It matches live `spec.md` **verbatim and exactly once**, and is unique across
all four target files (searched against all of them). *Controls, on the
reader:* the mutated form (first alphabetic run replaced by a sentinel,
asserted `mutant != original`) returns **0** hits against the 1 real hit;
run inside the full 26-target harness, all controls behaved as in round 5.
The replacement is exactly the pair round 5 recommended, ending at the same
sentence boundary, so the surviving remainder of the paragraph ("The live
directory's continued existence — …") is untouched by construction.

## (b) The applied result — PASS; the orphan is gone and the seam is clean

All **26** replace-targets (22 block + 4 inline, re-derived structurally from
45 blockquote blocks) applied in memory **26/26**, uniqueness required at
apply time, plus the scenario addition. Post-application sweeps:

| token | spec.md | contracts.md | constraints.md | scenarios.md | pre-application control |
|---|---|---|---|---|---|
| `stated above` | 0 | 0 | 0 | 0 | 1 in spec.md |
| `notwithstanding` | 0 | 0 | 0 | 0 | 1 in spec.md |
| `bounded existence` / `the one bounded` | 0 | 0 | 0 | 0 | 1 in spec.md |

Each zero's control is the same sweep over the pre-application text finding
the one occurrence the edit removes — the instrument demonstrably fires in
both states. Every surviving `probe` occurrence (3 in `spec.md`, 2 in
`scenarios.md`) was read in context: all five are the no-probe statements
themselves (EDIT 3's, the new pair's, EDIT 5's, the renamed scenario heading
and its body) — mutually consistent negatives; the self-contradiction round 5
blocked on is gone.

**Seam inspection (the point that matters most).** The applied paragraph
reads: "…which is the tombstone condition wearing a different name. This
prohibition is load-bearing because of how discovery works. The
archived-or-deleted test keys on the DIRECTORY alone, and discovery
enumerates directories, performing no file-level probe inside any plan
directory. The live directory's continued existence — including via a symlink
to a directory — makes an archived thread read as ACTIVE, …". The three
questions, asked of the delta: nothing vanished that should have stayed (the
target stops at the sentence boundary; the symlink/garbage-collection
rationale and everything after survive verbatim); nothing stayed that should
have vanished (the orphan and its carve-out assertion are gone); nothing
newly adjacent breaks (the replacement's closing clause flows into the
surviving sentence with no dangling referent, no contradiction, and no
duplicated clause — "performing no file-level probe inside any plan
directory" restates the section's rule consistently, it does not conflict
with it). All 14 distinct `§"…"` cross-references in the applied result still
resolve against the post-rename heading set (the new pair introduces none;
control: a fabricated heading fails the membership test).

## (c) Amendment-history corrections — PASS, with one new non-blocking slip

- **Round 5 recorded as Fable 5**: yes, in all four places — the
  §"Amendment history" narrative ("Round 5 …, performed by Fable 5"), the
  attestation sentence ("Round 4 and round 5 were performed by Fable 5, the
  model `AGENTS.md` requires, closing the deviation"), the
  instrument-variation sentence, and the new §"What round 5 changed" section.
  The per-round rule survives intact and no blanket value is asserted. The
  round-5 summary accurately restates the round-5 verdict (three round-4
  blockers cleared, 25 then-current targets, one new defect: the orphaned
  intra-section referent).
- **"Rounds 1 through 4 verified 24" corrected**: the target-count paragraph
  now reads "Round 1 verified **19** replace-targets. Rounds 2 through 4
  verified **24** replace-targets." — the substance round 5 asked for. The
  stale sentence is absent from the file (grep exit non-zero; control: the
  corrected sentence found at line 251-252).
- **v011 timing corrected in BOTH places**: the Summary and the §"Proposed
  Changes" preamble both now read "between rounds 1 and 2" (2 occurrences
  found; the stale "between round 2 and this revision" is absent).
- **No new expiring claim**: "it expired when the first Fable round was
  commissioned" replaces the round-anchored phrasing; "the current set is 26"
  is re-derived true; "Historical statements … that cite 24 or 25 describe
  the rounds in which that count was the whole set" is accurate. The new
  `[R5-1]` markers sit only in connective prose, never in ratified
  blockquotes (post-application marker sweep: 0 across all four files).

**RETRACTED (was: non-blocking date note) — the proposal's "Round 5
(2026-08-12)" is CORRECT; the reviewer's clock was the defect.** This
verdict originally flagged line 28's "(2026-08-12)" against the round-5
verdict's "on 2026-08-13" attestation. Re-measured after the finding was
challenged: this host runs local UTC+2, the fleet's attestation fields are
ISO-8601 UTC, and rounds 5 and this delta pass ran at roughly 23:0x-23:4xZ
on **2026-08-12 UTC** — which is already past midnight LOCAL on 2026-08-13.
The "2026-08-13" dates in the round-5 verdict and in this document were read
from the local clock, not UTC; the proposal's UTC date is the correct one,
and "fixing" it to 2026-08-13 would plant a FALSE date in
attestation-adjacent prose. This is the fleet's recorded
date-read-from-the-wrong-clock trap, this time committed by the reviewer.
The round-5 verdict's "on 2026-08-13" attestation line should be read as
local time; in UTC — the fleet's attestation convention — both rounds are
2026-08-12. No one should edit the proposal's date.

**Cosmetic, recorded only for completeness:** "Rounds 2 through 4" names a
range that includes round 3, and no round-3 review exists (the document's own
history lists rounds 1, 2, 4, 5). "Rounds 2 and 4" would be exact. No reader
with the section in front of them is misled.

## (d) No regression — PASS

- The four target spec files are **byte-identical** to the bytes round 5
  verified (md5s above), so every round-5 target-side conclusion carries.
- The proposal diff contains **only** the six delta hunks; the 25 previously
  verified replace-pairs are byte-unchanged, and the full harness re-run
  confirms all **26 targets verbatim, tree-wide unique, 0/26 mutant hits,
  26/26 applied**, with reader anchors passing in both directions.
- All round-5 drift sweeps reproduce identically on the new applied result
  (worker `handoff.md` 0; `plan[ -]thread` 0; `this revision|this proposal`
  0; `a row without the key` 0; both `supervisor-handoff.md` survivors inside
  the intended prohibition clauses; `[R…-n]` markers 0 in applied text).
- The cleared round-4 blockers are textually untouched by the delta
  (§"Ratification sequencing", the EDIT 5 foreman pair, and the per-round
  attestation rule appear in no hunk except the additive round-5 sentences
  checked above).
- Heading mechanics unchanged: still exactly two `## ` heading changes (the
  proposal's blockquotes contain exactly 3 heading lines — rename source,
  rename target, added scenario), matched by the same two
  `tests/heading-coverage.json` co-edits; the simulation still yields
  **0 unmapped, 0 orphaned** over 96 entries, and the removal control still
  produces exactly 1 unmapped heading.

## Summary

| Point | Finding | Result |
|---|---|---|
| (a) | New pair verbatim, tree-wide unique, non-no-op mutation control 0/1 | PASS |
| (b) | Orphan phrases 0 post-application (pre-controls fire); all 5 surviving `probe` hits are the consistent no-probe statements; seam coherent; § refs resolve | PASS |
| (c) | Round 5 recorded as Fable 5; both false history claims corrected; no new expiring claim; the proposal's "(2026-08-12)" date is correct in UTC (the reviewer's original date note is RETRACTED — local-clock read) | PASS, one cosmetic range wording |
| (d) | Spec files byte-identical to round 5; only the six delta hunks changed; 26/26 verified; sweeps and heading simulation reproduce | PASS |

The round-5 blocker is genuinely cleared, exactly as specified, with no new
defect introduced at the seam. The one surviving non-blocking note (the
cosmetic "Rounds 2 through 4" range) routes to the next touch of the
Amendment-history section; it does not warrant a round.

NO BLOCKERS
