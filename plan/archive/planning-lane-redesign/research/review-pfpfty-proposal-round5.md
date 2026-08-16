# Adversarial review — round 5

**Proposal under review:** `SPECIFICATION/proposed_changes/planning-lane-realization.md`
in repository **`livespec-overseer`**
(<https://github.com/thewoolleyman/livespec-overseer/blob/master/SPECIFICATION/proposed_changes/planning-lane-realization.md>).

**Review is READ-ONLY.** Nothing was edited, created, deleted, committed,
pushed, ratified, or filed in any tracked tree. No worktree or branch was
created. The beads ledger was READ only (`bd show`; the auto-backup warning
those reads print is the documented correct-by-design tenant `DOLT_BACKUP`
denial, not a write). This file is the only write.

## MODEL ATTESTATION

This round-5 review was performed by **Fable 5** (`claude-fable-5`) — the model
`AGENTS.md` §"Independent Fable review before every ratification" requires.
The per-round record now stands: rounds 1 and 2 → Opus 5 (each under a
maintainer-authorized one-off deviation), round 4 → Fable 5, round 5 (this) →
Fable 5. No blanket `reviewer_model` value is honest for this history; any
ratification record must name the model per round, including this one.

## Pinned read

Every quotation below comes from committed state via `git show`, never a
working tree.

| | |
|---|---|
| Brief's pin | `origin/master` = `a3c922a`, proposal 728 lines, md5 `5b26eff3b494bf53421ba06de3358441` |
| `origin/master` at review time | **`5284908`** — two commits past the brief's pin |
| What those two commits touch | `plan/` archive moves ONLY (`47b5687`, `5284908`: archiving `resume-submit-integrity` and `adoptable-launch-discipline` plan directories). The `a3c922a..5284908` diffstat contains **zero** `SPECIFICATION/` paths, zero `tests/` paths. |
| Proposal at `5284908` | **728 lines, md5 `5b26eff3b494bf53421ba06de3358441` — byte-identical to the brief's pin** |
| The four target spec files | Byte-identical between `a3c922a` and `5284908` (no `SPECIFICATION/` path in the diffstat) |

The brief said to stop if the bytes differ. The reviewed FILE's bytes are
exactly the pinned bytes, and the spec tree under it is unchanged; only the
repo tip label moved. The review proceeded against `origin/master` = `5284908`.

## Bottom line, in plain language

**All three round-4 blockers are genuinely cleared — each re-derived against
live bytes and the live ledger, not read off the proposal's tables. All 25
replace-targets match verbatim and tree-wide uniquely, the in-memory
application of all 25 plus the scenario addition is clean, the heading-coverage
co-edit simulates to zero defects, and every cross-repo claim verifies live.
But simulating the applied result surfaces ONE defect every prior round
missed: a surviving parenthetical in `spec.md` — "(the one bounded existence
probe stated above notwithstanding)" — still asserts the supervision-artifact
probe EXISTS after every statement of that probe has been replaced by "the
discovery path performs no file-level probe inside a plan directory". Post-
application the ratified spec contradicts itself about whether discovery may
probe, and the parenthetical's referent dangles. The fix is one small
additional replace-pair in a section EDIT 3 already touches.**

### Notation

- **"live"** = bytes at `git show origin/master:<path>` (= `5284908`) in
  `livespec-overseer`, or at the named sibling repository's `origin/master`.
- **"post-application"** = the text after applying all 25 replacements plus
  the one scenario addition, computed by in-memory simulation on
  whitespace-normalized text; nothing written to disk.
- Every zero below carries a positive control, and controls sit on the READER
  where the reader is the risk: every mutation control was asserted
  `mutated != original` before use, so no control could silently no-op.

---

## Part A — the three round-4 blockers, re-derived

The proposal's §"What round 4 changed" table asserts all three are cleared.
Each was re-derived against live bytes; the table was not allowed to stand in
for verification.

### Round-4 blocker 1 (§"Ratification sequencing" false claims) — CLEARED

- **The "discovered or" arm is gone.** The section now states the population
  moment as EDIT 3 states it: "at track ASSIGNMENT and by the assigning
  surface — never on the daemon's discovery pass", and adds the enforcement
  rationale ("An implementer who populated at discovery would be building the
  one thing EDIT 3 forbids, because discovery is the daemon's act").
- **The neutrality claim is replaced by the true one.** The section now says
  explicitly that populating `epic` ahead of the accept "does NOT follow that
  it contradicts no clause of the CURRENT spec. It contradicts one" — the
  live persisted-facts ONLY-enumeration — names the between-window a doctor
  pass would flag, and derives the "immediately, or land with it" ordering
  from it. I re-verified the live enumeration (replace-target 5) still admits
  only four members, so the corrected argument is true against live bytes.
- **Blockquote classifier, with its control on the reader.** The three
  round-4 defective phrases occur 5 times in the proposal — `discovered or`
  ×1, `contradicts no clause of the CURRENT spec` ×2,
  `reviewer_model: opus` ×2 — and **0** of those occurrences are on
  blockquote lines (the `with:`-convention text that becomes ratified spec
  bytes); all sit in the amendment-history narrative or in refuting position.
  *Control:* the same classifier reports **245** blockquote lines in the
  file, and a positive-presence probe (`never on the daemon's discovery
  pass`) returns a hit — the classifier demonstrably reads both categories.
- **The propagated ledger falsehood was corrected.** `bd show
  overseer-pfpfty.9` (read live): its description now carries the corrected
  population moment ("AT ASSIGNMENT, PERFORMED BY THE ASSIGNING SURFACE …
  NEVER at the daemon's discovery pass") and the corrected sequencing
  argument, with a dated correction note crediting the round-4 review. One
  residue survives — see non-blocking observation 4.
- **Ground truth re-measured, not inherited.** The live mapping store
  (`~/.livespec-overseer.jsonl`) now holds **24** rows; `epic` is non-null in
  **0** of them (*controls:* 24/24 carry `resume`, 24/24 carry `handoff`).
  The only `epic` occurrences in either overseer product tree remain
  declaration, serialization, and read-back
  (`_registry_core.py:111,217`, `_registry_store.py:102,126`, identical in
  both trees) — `overseer-pfpfty.9` has NOT landed, so the ordering
  constraint is still live. Note the row count moved from the proposal's 23;
  see non-blocking observation 3.
- **The ordering claim tested in both directions.** (i) Populating before the
  accept: contradicts exactly the one clause the section now says it
  contradicts — verified against the live enumeration. (ii) The ledger graph
  agrees with the asserted order `overseer-pfpfty.9` → accept
  (`overseer-pfpfty.2`) → `overseer-pfpfty.4`: `bd show` (read live) gives
  `.9` BLOCKS `.2`; `.2` DEPENDS ON `.1`, `.6`, `.8`, `.9`, `.10` (`.10`,
  the round-4 amendment, is closed) and BLOCKS `.4`, `.7`, `.3`; `.9`
  carries no dependency on `.2`, which is what lets it land first, exactly
  as the section states.

### Round-4 blocker 2 (foreman purpose-grant junction) — CLEARED

- **The surviving paragraph is now amended in the same payload.** EDIT 5
  gains a 25th replace-target — the foreman purpose grant in
  §"Non-interference with tracked work" — verified verbatim, tree-wide
  unique, and cleanly applied. The replacement keeps `solely` exclusive and
  widens the enumerated purposes from one to exactly two: "solely as
  EVIDENCE for its own decision-routing and, when it is the surface
  assigning a track, to record that plan's ledger epic id into the track's
  mapping-store row at assignment."
- **The seam is sound post-application.** EDIT 3's re-grounded citation —
  "Where that surface is the authorized unattended foreman,
  §"Non-interference with tracked work" grants it this purpose expressly,
  alongside its own decision-routing" — now names a purpose the amended
  clause actually grants. The clause's write prohibitions survive
  immediately adjacent and untouched ("It MUST NOT write, delete, or
  hash-as-authorization anything under `plan/` …"), and recording into the
  mapping store is neither a `plan/` write nor a tracked-file write (the
  store is home-directory runtime state), so no surviving prohibition
  collides with the new duty.
- **The actor/moment wobble is fixed.** The supervise-plan-at-plan-open arm
  is gone. EDIT 3 now ties the moment to row creation — "AT TRACK
  ASSIGNMENT — the moment the row itself comes into being, since the store
  holds one row per ASSIGNED track" (live `contracts.md` verified: "one row
  per assigned track.") — declares no surface the assigner, attaches the
  obligation to whichever surface assigns, and states the unreadable-anchor
  case (no recorded `epic`; the interlock refuses the respawn and preserves
  the declaration).

### Round-4 blocker 3 (expired attestation instruction) — CLEARED

§"Amendment history" now carries the per-round rule: "The ratification record
names the model that performed each review round, and no blanket value is
honest for this history" — rounds 1 and 2 Opus 5 (round 2 stated explicitly as
a SECOND one-off repeating the round-1 deviation, matching round 2's own
attestation block), round 4 Fable 5. The expired "MUST read
`reviewer_model: opus`, never `fable`" instruction survives only as recounted
history, explicitly marked as expired, with the symmetric-falsehood point
("Attesting `opus` for a round Fable performed is the same defect as attesting
`fable` for a round Opus performed") preserved. **I checked whether recording
round 4 introduced a new expiring claim: it did not.** The per-round rule is
round-count-agnostic, so this Fable round 5 falls under it without falsifying
any sentence; "Round 4 was the first round performed on Fable 5" and "closing
the deviation" are historical facts that do not expire. (The amendment that
answers this verdict's Blocker 1 must add round 5 — Fable 5 — to the history
in the ordinary way.)

---

## Part B — new defect, found only by simulating the applied result

## BLOCKER 1 — a surviving parenthetical still asserts the retired probe exists, and its referent dangles

*The orphaned-referent / junction class (round-2 blocker 3's and round-1
blocker 2's classes combined); visible only post-application; missed by all
prior rounds.*

**Where.** Live `livespec-overseer` `SPECIFICATION/spec.md:399-402`,
§"Track discovery and the mapping store" — the same section EDIT 3 and EDIT 4
amend — in the tombstone-prohibition rationale paragraph, which **no edit
touches**:

> This prohibition is load-bearing because of how discovery works. The
> archived-or-deleted test keys on the DIRECTORY alone, and discovery
> enumerates directories (the one bounded existence probe stated above
> notwithstanding). The live directory's continued existence — including via a
> symlink to a directory — makes an archived thread read as ACTIVE, so its
> mapping row is never garbage-collected and the finished thread remains
> eligible for nudges, for wrap-up injection, and for RESTART.

**What "stated above" refers to.** Live `spec.md:368-373`, the discovery
paragraph's bounded-probe carve-out ("One bounded exception: … the daemon MAY
test the EXISTENCE of exactly one named artifact,
plan/<topic>/supervisor-handoff.md … This is the ONLY file-level probe the
discovery path may ever perform.") — which is replace-target 4, and EDIT 3
replaces it with "The discovery path performs no file-level probe inside a
plan directory." EDIT 5 likewise replaces the parallel carve-out in
§"Non-interference with tracked work" (live `spec.md:541`) with the same
no-probe sentence.

**Why it matters.** Post-application, every statement of the probe is gone —
and this parenthetical survives, three paragraphs below EDIT 3's replacement,
in the same section. Three compounding problems:

1. **Dangling referent.** "the one bounded existence probe stated above"
   points at text that no longer exists anywhere in the file. A reader
   walking up the section finds only the opposite statement.
2. **Ratified self-contradiction.** The parenthetical positively asserts a
   probe exists and carves it out ("notwithstanding") of the
   discovery-enumerates-directories claim, while the amended text states
   twice — once in this very section, once in §"Non-interference with tracked
   work" — that "The discovery path performs no file-level probe inside a
   plan directory," and the renamed scenario pins the no-probe behavior. The
   spec would assert the probe's existence and its nonexistence
   simultaneously.
3. **It is precisely the drift the proposal's own motivation targets.** The
   proposal's Motivation says the probe protections are "RE-DERIVED onto the
   new surface rather than dropped"; this survivor keeps a clause of the old
   surface alive.

**Why four rounds missed it.** The prior sweeps grepped `handoff`,
`plan[ -]thread`, `supervisor-handoff.md`, `this revision|this proposal`, and
`a row without the key`, and resolved `§"…"` cross-references — but never
swept `probe`/`bounded`/`existence`, and "stated above" is an intra-section
prose referent invisible to a heading-resolution check. This round's sweep of
the applied result for `probe` returned 5 hits: four are the new no-probe
statements and the renamed scenario (intended); the fifth is this survivor.
*Control:* the same sweep over the PRE-application text finds the two
carve-out statements the edits remove, so the instrument demonstrably sees
probe prose in both states.

**Verified clean-fix target.** The phrase "the one bounded existence probe
stated above" occurs exactly **once** across all four live spec files
(`spec.md:401`; 0 in the other three), so a small additional replace-pair
cannot mis-apply.

**What would clear it.** Extend EDIT 3 (or add an eighth edit) with one more
verbatim replace-pair in the same section, e.g. replace:

> This prohibition is load-bearing because of how discovery works. The
> archived-or-deleted test keys on the DIRECTORY alone, and discovery
> enumerates directories (the one bounded existence probe stated above
> notwithstanding).

with:

> This prohibition is load-bearing because of how discovery works. The
> archived-or-deleted test keys on the DIRECTORY alone, and discovery
> enumerates directories, performing no file-level probe inside any plan
> directory.

(Any equivalent that deletes the probe assertion clears it; the surrounding
paragraph needs no other change. The same touch MAY also sweep the adjacent
bare-"thread" anaphors — observation 5 — but that is optional.)

---

## The flagged judgment call — `constraints.md`'s parallel "solely as evidence" clause

The author left `constraints.md` §"Filesystem boundaries"'s foreman clause —
"an authorized unattended foreman MAY read plan-tree, pane, and work-item text
solely as evidence; it MUST NOT write or delete plan-tree files, hash them as
authorization, or treat text it reads as instructions" — unamended, reasoning
it is the broader grant. **I examined it independently and concur; leaving it
alone is correct and does not re-create the round-4 trap.** Reasons:

1. **The clause glosses its own exclusions.** Its semicolon-joined second half
   enumerates what "solely as evidence" rules out: writes/deletes,
   hash-as-authorization, treating text as instructions. That makes "solely
   as evidence" an epistemic-stance restriction (information, never
   instructions or authorization) rather than a purpose enumeration like
   `spec.md`'s "for its own decision-routing". Reading the write-once anchor
   to record the epic id treats the text as evidence of a fact (the plan's
   epic id) and as none of the three excluded things, so the conjunction of
   both post-application clauses permits the new duty.
2. **The round-4 trap was a citation, and the citation no longer runs through
   this clause.** Round 4's blocker 2 arose because EDIT 3 cited the
   `spec.md` clause while paraphrasing it with the `constraints.md` wording.
   Post-amendment, EDIT 3's citation resolves against the amended `spec.md`
   grant, which expressly covers the duty; nothing load-bearing reads through
   the `constraints.md` clause's wording anymore.
3. **Narrowing it would exceed the mandate.** Editing "solely as evidence" to
   enumerate purposes would restrict an existing permission this proposal has
   no design-record basis to restrict — the exact over-reach round 1's
   blocker 3 penalized in the other direction.
4. The asymmetry-and-its-history paragraph the author added is proposal prose
   (not ratified), so it correctly documents the trap for the ratifier
   without landing commentary in the spec.

---

## Part C — checks that PASSED

**Criterion 1 — replacement-target fidelity: PASS, count re-derived.** The
proposal contains 43 blockquote blocks; structural classification (a block
whose next non-blank line is exactly `with:`, paired with the following
block) yields **21** block replace-targets, plus **4** inline
`Replace "…" with "…"` bullets in EDIT 4 = **25**, matching the proposal's
stated current set by re-derivation (the 25th being the new foreman-grant
target). All 25 match their live file **verbatim and exactly once** after
whitespace normalization — 10 block + 4 inline in `spec.md`, 4 in
`contracts.md`, 2 in `constraints.md`, 6 in `scenarios.md` (round 4's
per-file split, plus the new `spec.md` target) — and each was searched
against ALL five spec-tree files (`non-functional-requirements.md`
included), so uniqueness is tree-wide. The remaining blocks are the one pure
scenario addition and the two heading-coverage `reason` strings, correctly
not replacements. *Controls on the reader, provably non-no-op:* every target
re-probed in mutated form (first alphabetic run ≥3 chars replaced with a
sentinel absent from every file), `mutated != original` ASSERTED before use;
result 25/25 unmutated hits, **0/25 mutant hits**. Reader anchors: a
known-present string returns exactly 1, a known-absent string returns 0.

**In-memory application: 25/25 applied** (uniqueness required at apply time —
a second instrument agreeing with the counting instrument), plus the scenario
addition. No target overlaps another; EDIT 5's two-paragraph target ends
before the foreman paragraph its sibling target replaces.

**The three questions, asked of the applied result.**
*What vanished that should have stayed:* nothing — walked every replacement
for dropped obligations; the wrap-up message's obligations, the four
preserved supervisor-layer obligations (role-layer permission, two-layer
halt-with-remedy guard, reviewed-commit discipline, not-a-plugin-asset), the
persisted-facts members, the `ctx_threshold` conditional with its re-emitted
referent, "Unknown keys survive rewrites.", the "exactly two places" sentence
and the startup gitignore refusal all survive (each confirmed present
post-application).
*What stayed that should have vanished:* **one thing — Blocker 1.** All other
sweeps clean: worker `handoff.md` 0/0/0/0; `plan[ -]thread` 0/0/0/0 (pre:
4 in `spec.md`, the EDIT 4 set — control that the sweep fires);
`this revision|this proposal` 0 across all four; `a row without the key` 0
(pre: 1 — control); `resume artifact` 0; `conventional handoff` 0; every
surviving `handoff` token classified in context (new ledger-entry vocabulary,
the two intended `supervisor-handoff.md` prohibition clauses, the retired-key
tolerance clause, `contracts.md`'s state-file-sense "no handoff hash", and
the new scenario's "plan-tree handoff files as authorization" — all intended).
*What is now adjacent that was never adjacent:* the foreman grant now sits
directly after EDIT 5's replacement paragraphs and reads coherently; EDIT 3's
tail abuts EDIT 4's enumeration replacement coherently; the EDIT 6 insertion
abuts "Unknown keys survive rewrites." coherently. The one bad adjacency is
Blocker 1's parenthetical, now standing three paragraphs below its
contradiction.

**Cross-reference resolution: PASS.** All 14 distinct `§"…"` references in
the post-application text resolve against the post-rename heading set
(*control:* a fabricated heading fails the same membership test). Only
target 18 touches any `## ` heading, so the heading set is otherwise stable.

**Criterion 4 — ratification mechanics: PASS.** Front-matter
`topic: planning-lane-realization` equals the file stem. Exactly two `## `
heading changes (one rename, one addition — re-derived by enumeration)
matched by exactly two specified `tests/heading-coverage.json` co-edits. The
old heading exists in the live manifest exactly once, mapped to
`test_scenario_the_supervision_probe_is_liveness_gated_and_existence_only`;
the live test still asserts `assert _HANDOFF in live_probes` at
`tests/integration/test_discovery_and_relay.py:282`, exactly as the proposal
cites. Both replacement `reason` strings name the integration tier,
satisfying `check-heading-coverage` direction 4. Simulated post-ratification
coverage over 96 entries: **0 unmapped headings, 0 orphaned entries** —
*control on the reader:* deliberately removing the renamed entry from the
simulated manifest produces exactly 1 unmapped heading.

**Criterion 5 — cross-repo consistency: PASS.** Verified live at each
sibling's `origin/master`: `livespec` core `SPECIFICATION/spec.md` still
reads verbatim "append-only, per-entry ledger entries, each individually
attributed and timestamped" (the attribution anchor the proposal quotes),
"exactly one write-once metadata anchor written at plan open." and "The
anchor MUST name the epic id …" (EDIT 3's source), and the vocabulary clause
banning `plan thread`/`planning thread`/`plan-thread` (EDIT 4's basis);
`livespec-orchestrator-beads-fabro` `SPECIFICATION/contracts.md` still
carries "sanctioned plan surface" (checked on line-wrap-normalized text —
round 4's recorded instrument hazard — 1 occurrence found). Ledger: `.9`,
`.7`, `.2`, `.4` all exist with the roles the proposal assigns them; the
dependency graph is acyclic and matches §"Ratification sequencing".

**Sequencing ground truth: still live.** `overseer-pfpfty.9` is
pending-approval (not landed); no product code assigns `epic`; all 24 live
mapping-store rows carry `epic: null`. The gate's ordering constraint
remains exactly as the proposal states it.

---

## Non-blocking observations

Recorded for the author; none should cost a round on its own.

1. **"Rounds 1 through 4 verified 24 replace-targets" (§"Verification
   method") is false for round 1.** Round 1's own verdict verified
   **nineteen** targets ("fifteen block quotations plus the four inline
   replacements"); the set grew to 24 with the round-1 amendment and was 24
   at rounds 2 and 4. The sentence exists to keep the count history precise,
   which is what makes the slip worth fixing: write "Rounds 2 and 4 verified
   24" (or "the rounds since the round-1 amendment"). Proposal prose only;
   no act depends on it.
2. **The v011 timing claim is false in both places it appears.** The Summary
   and the §"Proposed Changes" preamble say the v011 ratification moved the
   four EDIT 4 anchors "between round 2 and this revision". Re-derived from
   git: v011 landed `38af93b` 2026-08-12T04:33:27Z, and round 2's own pinned
   read (`ca7068b8`) already shows the moved line numbers (384/412/415/454
   versus round 1's 369/397/400/439) — the move happened between round 1 and
   round 2, and round 2's T3 section documented it. The argument the claim
   supports (self-locating targets over line numbers) is unaffected; fix the
   timing to "between round 1 and round 2".
3. **The live mapping store now holds 24 rows, not 23** (a track was added
   since the amendment; all 24 still `epic: null`, controls 24/24 on
   `resume` and `handoff`, and no assigning code exists). The proposal's
   "every one of the 23 rows" is scoped by "As of this revision", so it is
   not false-as-written — but the magnitude is rot-prone runtime state.
   Prefer "every row" and drop the number, the same delete-the-magnitude
   move rounds 2 and 4 prescribed for line numbers.
4. **`overseer-pfpfty.9`'s `acceptance_criteria` still carries the
   discovery arm** — "has a non-null `epic` in its mapping-store row after a
   **discovery/assignment** pass" — the exact wording whose "discovered" arm
   the round-4 correction removed from the description. An implementer
   satisfying the acceptance criteria literally could build the
   discovery-pass population EDIT 3 forbids. This review is forbidden to
   write the ledger; whoever amends the proposal should fix that field in
   the same pass.
5. **Bare-"thread" anaphors survive around the EDIT 4 replacements.** Nine
   bare "thread" nouns in `spec.md` (e.g. "the finished thread", "an
   archived thread read as ACTIVE", "Either the thread is LEFT UN-ARCHIVED",
   "after which the thread is archived whole") refer to what the amended
   adjacent sentences now call a plan. The ratified vocabulary clause bans
   only the two-word forms, and EDIT 4 claims only the four `plan[ -]thread`
   lines, so this is not a violation — but post-application the antecedent
   says "plan" while the anaphor says "thread". The Blocker 1 amendment
   touches this exact neighborhood and could sweep them cheaply.
6. **Round 4's standing observations remain accurate and open**: the
   spec.md/contracts.md prompt-content minima are still subset/superset
   (consistent, not contradictory); "authors the same two layers it always
   has" is still a historical comparison in ratified text; "Every entry
   carries an attribution by construction" is still an unanchored
   sibling-owned claim (verified true today); "asserts at line 282" is still
   accurate today and still rot-prone.

---

## Summary table

| # | Class | Finding | Severity |
|---|---|---|---|
| 1 | Orphaned referent / post-application contradiction | `spec.md:399-402`'s "(the one bounded existence probe stated above notwithstanding)" survives every edit while both statements of the probe are replaced by "performs no file-level probe inside a plan directory" — the referent dangles and the ratified spec asserts the probe's existence and nonexistence simultaneously | **BLOCKER** |
| R4-1 | — | Cleared: assignment-only moment stated, neutrality claim replaced by the true contradicts-one-clause argument, ledger `.9` description corrected, defective phrases 0-in-blockquote (control: 245 blockquote lines), graph re-verified `.9`→`.2`→`.4` | PASS |
| R4-2 | — | Cleared: foreman grant amended in-payload as the 25th target, two enumerated purposes with `solely` kept, seam re-grounded, wobble fixed (row-at-assignment, no declared assigner, unreadable-anchor case) | PASS |
| R4-3 | — | Cleared: per-round attestation rule (1-2 Opus 5, 4 Fable 5), no blanket value, no new expiring claim; round 5 (Fable 5) falls under the rule without falsifying it | PASS |
| — | Criterion 1 | 25/25 targets verbatim and tree-wide-unique across all five spec-tree files; mutation controls asserted non-no-op; 25/25 applied in memory | PASS |
| — | Criterion 3 | Post-application sweeps clean except Blocker 1; all obligations preserved; all 14 § cross-references resolve (fake-ref control) | PASS except Blocker 1 |
| — | Criterion 4 | topic=stem; 2 heading changes ↔ 2 co-edits; integration-tier reasons; simulated coverage 0/0 with a discriminating removal control; cited test assertion re-read at line 282 | PASS |
| — | Criterion 5 | Core anchor, attribution, and vocabulary quotes, orchestrator seam phrase, and all four cited work-items verified live | PASS |
| — | Judgment call | `constraints.md` foreman clause correctly left alone — its own gloss (not-instructions, not-authorization) admits the anchor-read, and no load-bearing citation runs through it post-amendment | CONCUR |
| — | Pin check | File bytes identical to the brief's pin at the current tip `5284908`; the two commits past `a3c922a` touch `plan/` archive moves only, zero `SPECIFICATION/` paths | NOTED |

---

## VERDICT

**1 BLOCKER**

1. Post-application, live `spec.md:399-402`'s parenthetical "(the one bounded
   existence probe stated above notwithstanding)" — in §"Track discovery and
   the mapping store", untouched by any edit — still asserts the
   supervision-artifact existence probe EXISTS and carves it out of
   discovery's directory-enumeration claim, while EDIT 3 and EDIT 5 replace
   every statement of that probe with "The discovery path performs no
   file-level probe inside a plan directory" and EDIT 7's renamed scenario
   pins the no-probe behavior. The referent dangles and the ratified spec
   contradicts itself about whether discovery may probe. Fix: one additional
   verbatim replace-pair deleting the probe assertion (the phrase is unique
   tree-wide, so it cannot mis-apply); the amendment must also record this
   round 5 (Fable 5) in §"Amendment history" per the proposal's own per-round
   attestation rule.

All three round-4 blockers are genuinely cleared. The new blocker is the
orphaned-referent class both prior simulating rounds hunted — it survived
because no round's sweep tokens included the probe vocabulary; this round's
applied-result sweep of `probe`/`bounded`/`existence` caught it, with
positive controls on both the query and the reader.

**Reviewed by Fable 5 (`claude-fable-5`) on 2026-08-13 — the model
`AGENTS.md` §"Independent Fable review before every ratification" requires.
Per-round record: rounds 1-2 Opus 5 (maintainer-authorized one-offs), round 4
Fable 5, round 5 Fable 5; no blanket `reviewer_model` value is honest for
this history.**

**Pinned at `livespec-overseer` `origin/master` = `5284908` (proposal 728
lines, md5 `5b26eff3b494bf53421ba06de3358441`, byte-identical to the brief's
pin at `a3c922a`; the intervening commits touch only `plan/` archive moves,
no `SPECIFICATION/` or `tests/` path).**

1 BLOCKERS
