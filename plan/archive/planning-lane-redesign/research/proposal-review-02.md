Provenance: independent re-review (brief-05, 2026-08-05) of the Planning Lane redesign proposal as amended by livespec-zsn2xh.6 / PR #2029; committed as durable research evidence by brief-06. Content below is verbatim from the review's runtime deliverable.

# Independent re-review — AMENDED Planning Lane proposal (brief-05)

Reviewer: worker session `planning-lane-redesign`, still an independent seat
(the amendment was authored by a Fabro sandbox via `livespec-zsn2xh.6`; this
reviewer wrote none of it). Reviewed 2026-08-05 against a freshly fetched
`origin/master` at `fcbb781c0968f679b9e0a422bd454449d4893254` (the PR #2029
merge itself); every file read via `git show origin/master:<path>`. PR #2029
verified to touch ONLY the proposal file, so all live-spec line references
from review 01 remain valid.

**Independence constraint — applied.** I drafted my own version of this
amendment (`amended-proposal-draft.md`, gitignored; the sandbox never saw
it). Per the brief, divergence from that draft is NOT a defect and none is
reported as one. Concretely, the sandbox diverged from my draft in at least
three ways I judged PASS on the objective criteria: per-bullet citation
sentences instead of one consolidated citation directive; a dedicated
constraints.md item instead of a drift-sweep bullet; and per-Driver hook
assignments more precise than my draft's. The two blockers below are NOT
divergences from my draft — both are gaps my own review-01 recommended fix
UNDER-SPECIFIED and the sandbox implemented faithfully; I flag that
explicitly for accountability.

## Part A — the six blockers

1. **CLEARED.** Item 4's replaced-paragraph list now names all SIX paragraphs
   including `The two seams`, and the replacement wording ("the two seams are
   ledger comments/child reads plus sanctioned capture/admission surfaces,
   not a read-only prompt-to-ledger seam") is consistent with the amended
   item 2 seams bullet, which now says the plan surface "writes and reads
   plan-epic ledger comments for handoffs". The write path is explicit in
   both places; the contradiction is gone.
2. **CLEARED.** `SPECIFICATION/constraints.md` added to the target list; new
   item 7 targets §"Design-record citations (authorized exception)" — that
   heading exists verbatim at constraints.md:265 (`### Design-record
   citations (authorized exception)`) — and the quoted target `a
   plan/<topic>/ thread archive` matches constraints.md:267 modulo inline
   backticks, with replacement wording using the `plan` vocabulary.
3. **CLEARED.** New drift-sweep bullet quotes nfr:229's Archive-on-epic-close
   member and re-derives its parenthetical to "close/archive is gated by no
   undisposed children plus independent completeness review" — epic close is
   no longer implied ungated, and the iff-binding survives.
4. **PARTIALLY CLEARED — residuals are Blockers 1 and 2 below.** The
   amendment adds both halves of the recommended fix: migration MUST preserve
   a pre-existing `handoff.md` as write-once historical evidence under
   `plan/<slug>/research/` and MUST NOT delete it from the git tip (store
   bullet, nfr guidance directive, and a scenario), and new citations MUST use
   archive-stable paths (dedicated bullet). But the brief's criterion —
   "confirm this actually protects the live citations at nfr:741/:771/:797" —
   is not fully met: relocation to `research/` still breaks the EXACT cited
   path `plan/rop-railway-enforcement/handoff.md` in repository
   livespec-dev-tooling the moment that repo migrates, and nothing directs a
   citation update. The record survives (the deletion harm is fixed); the
   citation still rots. My own review-01 fix offered relocation as
   sufficient, which was under-specified — the sandbox implemented it
   faithfully.
5. **CLEARED.** Item 10 names both Driver repositories with per-Driver
   precision that matches the live hook contract (contracts.md:233/:235):
   `livespec-driver-claude` Stop plan-persistence AND Stop no-shadow-ledger
   narration; `livespec-driver-codex` Stop no-shadow-ledger bundle and
   narration (the plan-persistence hook is Claude-bundle-only in the live
   contract, so the asymmetry is correct, not an omission).
6. **CLEARED.** Every new load-bearing definition — plan, store, scoping
   event, deferral, handoff surface, seams, archive gate, citation-stability,
   vocabulary — now carries a rationale sentence plus a repo-qualified
   design-record citation naming the specific record(s) behind it.

## Part B — full re-review of the amended text

- **Replacement-target fidelity: PASS.** All newly quoted targets verified
  verbatim in the live files (constraints heading and :267 phrase; nfr:229
  member text; the six named nfr paragraphs including `The two seams` at
  nfr:184). Review-01's targets unchanged (PR #2029 touched only the
  proposal).
- **Design-record fidelity: PASS on content** — the added contract text
  tracks `maintainer-rulings.md`, `brainstorm.md`, and the corrected spike
  faithfully; no ruling is contradicted. (The citation PATH form is Blocker
  1, a reachability defect, not a fidelity defect.)
- **Drift-sweep completeness: PASS.** The three review-01 sweep gaps
  (nfr:184 two-seams, constraints.md:267, nfr:229) are all covered. Re-ran
  the full term sweep over the five live files: no uncovered instance
  remains. Empty-result claims carry positive controls: the same grep shape
  returns dozens of hits in covered locations.
- **Ratification mechanics: PASS.** Front-matter `topic:
  planning-lane-redesign` still equals the file stem. H2 sets of ALL FIVE
  target files re-derived: PR #2029 changed only the proposal, and the
  amended directives (including new item 7, which replaces a parenthetical
  under an existing H3) add, remove, and rename no `## ` heading. The
  no-heading-coverage-co-edit claim remains correct by derivation.
- **Cross-repo consistency: PASS**, with review-01's advisory RE-RAISED
  unchanged: spec.md's binding MUST still says "append-only ledger comments"
  while the non-Beads equivalence latitude lives only in the
  non-functional-requirements guidance (item 4). The amendment did not
  address it. Still advisory, not a blocker — a
  livespec-orchestrator-git-jsonl realization can conform through the
  guidance's equivalence clause — but the ratifying maintainer should decide
  deliberately whether the spec-level MUST binds the property or the literal
  feature.
- **Latent class 1 (claims false at/around ratification): BLOCKER 1.** Every
  design-record citation in the amended text points at
  `plan/archive/planning-lane-redesign/research/<record>.md` — a path that
  DOES NOT EXIST and will not exist until this plan's epic closes. Evidence:
  `ls /data/projects/livespec/plan/archive/planning-lane-redesign` → no such
  directory, with a positive control in the same shape
  (`plan/archive/autonomous-mode` resolves, so the absence reading is
  meaningful). At the moment of ratification, every one of these citations is
  unreachable — the mirror image of the defect they were introduced to
  prevent, and exactly the "reachable design record" requirement of
  spec.md:216 read strictly.
- **Latent class 2 (negative sibling assertions): PASS.** Nothing new.
- **Latent class 3 (clause lockstep): PASS.** The six-paragraph list matches
  the live six; the target-file list carries no stated count; per-bullet
  citation enumerations are stable sets.

---

VERDICT: BLOCKERS

1. **Citations dead until archive.** The archive-stable citation form
   (`plan/archive/planning-lane-redesign/research/...`) is unreachable at
   ratification time and stays so until the plan archives — measured absent
   at `fcbb781c`, positive control passing. Recommended fix (small): cite
   BOTH forms once — e.g. "repo `thewoolleyman/livespec`,
   `plan/planning-lane-redesign/research/<record>.md` (post-archive:
   `plan/archive/planning-lane-redesign/research/<record>.md`)" — OR add one
   sentence to the citation-stability bullet codifying the resolution rule
   that a plan-record citation resolves at `plan/<slug>/...` or
   `plan/archive/<slug>/...`, whichever exists, and keep the single
   archive-form path. Either makes every citation reachable at every point
   in the plan's lifecycle.
2. **Relocation still breaks pre-existing ratified citations.** Migration
   preserves a pre-existing `handoff.md` by RELOCATING it under
   `plan/<slug>/research/`, which breaks the exact ratified paths at
   nfr:741/:771/:797 (repo `livespec-dev-tooling`,
   `plan/rop-railway-enforcement/handoff.md`) the moment that repo migrates.
   Recommended fix (one sentence in the migration bullet): a migration MUST
   update, in the same change or an explicitly linked work-item, every
   fleet-spec statement whose design-record citation names a path the
   migration relocates — mechanically findable by grepping each fleet repo's
   `SPECIFICATION/` for the pre-relocation path.
