Provenance: independent adversarial review (brief-03, 2026-08-04) of the Planning Lane redesign proposal landed by PR #2014 in repository livespec; committed as durable research evidence by brief-04. Content below is verbatim from the review's runtime deliverable.

# Independent adversarial review — Planning Lane redesign proposal (brief-03)

Reviewer: worker session `planning-lane-redesign` — an independent seat (the
proposal's author is `codex-gpt-5`, a Fabro sandbox agent; this reviewer wrote
none of it). Reviewed 2026-08-04 against a freshly fetched `origin/master` at
`fba470bc5f552ca77bc3d0a219707f95f4cb3ed6`; every file read via
`git show origin/master:<path>`, never the working tree. `.ai/spec-proposal-review.md`
read in full before starting.

Subject: `SPECIFICATION/proposed_changes/planning-lane-redesign.md`
(front-matter `topic: planning-lane-redesign`, 62 lines). Style note: this is a
DIRECTIVE proposal (numbered instructions to the revise author), not a
resulting-bytes proposal — so "replacement-target fidelity" here means each
quoted phrase and named section exists as claimed, and the revise payload will
still need its own exact-byte assembly against then-current master.

## Criterion 1 — replacement-target fidelity: PASS (with an enumeration note)

Every named heading exists at its stated level (`grep -n '^#...'` over the
five live files):

- `## Workflow planes and the Planning Lane` — spec.md:314 (H2, as claimed)
- `### The Planning Lane` — spec.md:358 (H3; proposal cites with §, not `## `)
- `## Contract + reference implementations architecture` — spec.md:400 (H2)
- `## Doctor cross-boundary invariants` — contracts.md:128 (H2; lives in
  contracts.md — the proposal never claims a file for it)
- `#### Planning Lane guidance` — non-functional-requirements.md:172 (H4, as
  written with four hashes)
- `### master-direct-uncommitted-spec-edits` — contracts.md:154
- `### Driver-shipped hooks` — contracts.md:227
- `## Happy-path doctor` — scenarios.md:171; `## Behavior clause lacking a
  scenario link is surfaced` — scenarios.md:315

Every quoted replace-target exists in the live text (modulo inline-code
backticks and Mermaid HTML escaping, acceptable for a directive proposal):

- `durable planning threads under plan/<topic>/` — spec.md:318 (live bytes:
  ``the durable planning threads under `plan/<topic>/` ``).
- Diagram node text `capture a planning thread in plan/<topic>/ (research +
  handoff), anchor a ledger epic, route matured pieces` — spec.md:379 (live
  bytes use `plan/&lt;topic&gt;/` and `<br/>`).
- The five named guidance paragraphs — nfr:176 (`The planning thread.`),
  178 (`The hosted supervision artifact.`), 180 (`No shadow ledger (the
  load-bearing rule).`), 182 (`Handoff self-sufficiency.`), 186 (`Archive on
  epic close.`).
- Uncommitted-`plan/` rationale — contracts.md:160 ("a plan-thread handoff is
  the durable record of a planning thread and an uncommitted one is frequently
  the ONLY copy").
- `a plan/doc file, or work-items` — contracts.md:233; `a handoff, or any
  markdown file under a `plan/` or `prompts/` directory` — contracts.md:235.
- "a design record ... a planning thread" — spec.md:214.

**Enumeration note (feeds Blocker 1 context, not itself a blocker):** the
`planstore[("plan/&lt;topic&gt;/")]` label appears in THREE diagrams —
spec.md:37 (top-level lifecycle), :332 (planes), :445 (canonical
architecture) — plus the node text at :379. Item 3 says "the Planning Lane
Mermaid diagrams" and item 8 says "diagrams" (plural, unenumerated); the
revise payload must hit all four sites, including the line-37 lifecycle
diagram that is arguably not a "Planning Lane diagram".

## Criterion 2 — design-record fidelity: PASS

Checked against `research/seed-prompt.md`, `brainstorm.md`,
`maintainer-rulings.md` (rulings win), and `bd-long-prose-spike.md` including
the PR #2012 evidence correction:

- Ruling 1 (mutable planning state in the ledger; store keeps research +
  anchor) — items 2 and 4 match exactly, including "exactly one write-once
  metadata anchor... MUST NOT be updated".
- Ruling 2 (vocabulary ban with the verbatim-quoting exception; frozen trees
  keep old wording) — item 2 final bullet + item 8 catch-all match.
- Ruling 3 (no gate presumes a seed/research document shape) — the scoping
  event constrains the TRANSITION (requirements cut into carriers before
  implementation children), not the prose shape. Matches route 2 of
  `brainstorm.md` as adopted.
- Spike fidelity — "append-only ledger comments... authoritative read path is
  the ledger comment JSON/timeline read path, not git" matches the spike's
  recommendation and its `bd comments <epic-id> --json` read path. The
  proposal does NOT repeat the spike's invalidated search evidence (corrected
  by PR #2012), and asserts nothing about comment searchability.
- Deferral honors the admission-valve rule ("MUST NOT hand-edit admission
  labels or bypass that valve") — matches `maintainer-rulings.md` and the
  ledger's actual 7-state status set (no native `deferred` state, so the
  label-through-valve branch is the operative one).
- Two-leg archive gate (mechanical no-undisposed-children + independent
  completeness review) — matches the accepted recommendation verbatim in
  substance.

## Criterion 3 — drift-sweep completeness: BLOCKERS FOUND

Full-term sweep over the five live files (`grep -n -i -o` for plan
thread/planning thread/plan-thread/handoff*/plan/<topic>//supervisor-handoff*/
plan_lifecycle_anchor, then every hit classified). Hits in spec.md
(37, 214, 318, 332, 360, 362, 379, 445), contracts.md (160, 233, 235), and
nfr (174–186) are each covered by items 1–8. scenarios.md has ZERO stale-term
hits — and per the standing evidence rule, that empty result is trusted only
because the SAME command shape returned dozens of hits in the sibling files
in the same invocation (positive control satisfied). contracts.md:382's
"human handoff" is a different sense (the revise decision handoff), not a
plan-handoff reference; no rewrite needed.

Four hits are NOT covered — see Blockers 1–4.

## Criterion 4 — ratification mechanics: PASS

- Front-matter `topic: planning-lane-redesign` equals the file stem exactly.
- H2-set derivation, done independently rather than trusting the proposal's
  sentence: items 1–2 replace prose under existing H2/H3s; item 3 edits
  Mermaid labels; item 4 replaces bold run-in paragraphs under an H4; items
  5–6 replace prose under H3s in contracts.md; item 7 adds scenarios under
  two EXISTING H2s (both verified present); item 8 rewrites sentences in
  place. No directive adds, removes, or renames any `## ` heading in any of
  the four target files, so the H2 sets are unchanged and the "no
  `tests/heading-coverage.json` co-edit" claim is CONFIRMED by derivation.

## Criterion 5 — cross-repo consistency: ONE BLOCKER (see Blocker 5), rest PASS

- `livespec-orchestrator-beads-fabro`: the plan-surface rewrite obligations
  match already-filed item `bd-ib-mrqoy2`; "sanctioned capture/admission
  surfaces" matches the existing capture-work-item seam; the deferral clause
  matches the admission-valve contract.
- `livespec-orchestrator-git-jsonl`: item 4's equivalence latitude ("an
  equivalent append-only, per-entry, timestamped ledger comment/journal
  surface") accommodates a non-Beads ledger. ADVISORY, not a blocker:
  spec.md's own MUST (item 2 bullet 5) says "append-only ledger comments"
  while the latitude lives only in non-functional-requirements guidance;
  consider the spec.md wording "append-only, per-entry ledger entries
  (comments in the Beads reference realization)" so the binding MUST is not
  read as requiring a literal comments feature of every ledger.
- `livespec-overseer`: dropping `supervisor-handoff.md` hosting matches filed
  item `overseer-pfpfty`.
- `livespec-console-beads-fabro`: item 9 names the rendering work; matches
  filed item `livespec-console-beads-fabro-sisnmx`.
- The Driver repos: NOT named, though item 6 rewrites the Driver-shipped hook
  contract — Blocker 5.

## Latent class 1 — claims that expire at ratification: PASS

The spec-destined bullets state durable contracts; no "currently/not
yet/today" tense. Item 9's present-state notes are proposal-body, not spec
text. The heading-preservation sentence and co-edit claim are mechanics
remarks that do not land in the spec.

## Latent class 2 — negative assertions about sibling-owned surfaces: PASS

"MUST NOT introduce direct Spec-Plane writes to orchestrator-private storage"
constrains the owning surface, not a sibling's internals. Item 4's non-Beads
latitude is a positive grant. No "sibling lacks X" assertions found.

## Latent class 3 — clause lockstep: PASS (with notes)

"two seams", "two-leg", and "exactly one ... anchor" are counts over
enumerations of two/two/one stated adjacently — small and locally re-derivable,
but the revise author should re-count them in the final text. The
Conformance-Pattern member list at nfr:229 is a lockstep enumeration the
redesign touches semantically — folded into Blocker 3.

---

VERDICT: BLOCKERS

1. **nfr §"Planning Lane guidance" has SIX named paragraphs; item 4 replaces
   five and omits `The two seams.` (nfr:184).** That paragraph teaches
   "*prompt → ledger* is read-only — a handoff cites ledger ids and composes
   status ... never writing back", which the redesign contradicts: handoffs
   BECOME ledger comment writes. Left unamended it directly contradicts item
   2 bullet 6's redefined seams. Recommended fix: add `The two seams` to item
   4's replaced-paragraph list, with replacement wording matching item 2
   bullet 6.
2. **`SPECIFICATION/constraints.md` is absent from the target-file list, and
   constraints.md:267 says "(e.g., a `plan/<topic>/` thread archive)"** —
   banned vocabulary plus the retired path shape, uncovered by any item
   (item 8's catch-all token list does not match this phrasing and the file
   is not targeted). Recommended fix: add constraints.md to the targets with
   a one-phrase amendment (e.g., "a `plan/archive/<slug>/` record").
3. **nfr:229's Conformance-Pattern member "Archive-on-epic-close (a
   `plan/<topic>/` thread is active if and only if its ledger epic is open
   ...)" is uncovered.** Stale path/vocabulary, and the member's parenthetical
   should be re-derived against the two-leg archive gate (the iff-binding
   survives; the wording must not imply epic close is UNGATED). Recommended
   fix: add this line to item 8's sweep with wording like "a `plan/<slug>/`
   record is active if and only if its ledger epic is open".
4. **Design-record reachability regression.** Ratified spec text already
   cites live `handoff.md` files as design records — nfr:741, :771, :797 all
   cite repo `thewoolleyman/livespec-dev-tooling`,
   `plan/rop-railway-enforcement/handoff.md` — and spec.md
   §"Intent preservation and design-record authority" makes an unreachable
   design record an incompleteness defect. The redesign's migration removes
   `handoff.md` files from live plans, which would break those ratified
   citations; the proposal's own new citation (item 2 bullet 5, the spike at
   `plan/planning-lane-redesign/research/bd-long-prose-spike.md`) is likewise
   broken by this very plan's future archive move to `plan/archive/...`.
   Recommended fix: add to the contract that (a) migration MUST preserve a
   pre-existing `handoff.md` as a write-once historical-evidence file under
   `plan/<slug>/research/` (never deleted from the git tip) or update every
   citing spec statement in lockstep, and (b) design-record citations in
   ratified text use an archive-stable form (the spec's own exemplar at
   spec.md:214 already cites a `plan/archive/...` path).
5. **Item 9's downstream enumeration omits the Driver repositories although
   item 6 rewrites the Driver-shipped hook contract** (the Stop
   plan-persistence WARN and Stop no-shadow-ledger WARN narrations ship from
   `livespec-driver-claude`, and the no-shadow-ledger hook is required in
   BOTH Drivers' bundles per contracts.md:235 — so `livespec-driver-codex`
   too). The filed cut's driver items are rename-only sweeps; hook-narration
   changes currently have NO carrier — which is precisely the
   scope-without-a-carrier failure this plan exists to eliminate. Recommended
   fix: name `livespec-driver-claude` and `livespec-driver-codex` hook
   updates in item 9 so post-ratification filing gives them carriers.
6. **New load-bearing definitions lack design-record citations.** spec.md:216
   requires every load-bearing semantic definition to carry rationale plus a
   repo-qualified design-record citation; of the new definitions (plan store,
   scoping event, deferral representation, archive gate, vocabulary), only
   the handoff bullet cites its record (the spike). Recommended fix: a
   directive that the resulting spec text carries repo-qualified citations to
   `plan/planning-lane-redesign/research/seed-prompt.md`, `brainstorm.md`,
   and `maintainer-rulings.md` (in the archive-stable form per Blocker 4) for
   each new definition.
