# Adversarial review — round 4

**Proposal under review:** `SPECIFICATION/proposed_changes/planning-lane-realization.md`
in repository **`livespec-overseer`**
(<https://github.com/thewoolleyman/livespec-overseer/blob/master/SPECIFICATION/proposed_changes/planning-lane-realization.md>).

**Review is READ-ONLY.** Nothing was edited, created, deleted, committed,
pushed, ratified, or filed. No worktree or branch was created. No beads ledger
was written (`bd show` reads only; the auto-backup warning those reads print is
the documented correct-by-design tenant `DOLT_BACKUP` denial, not a write). No
`just check` was run. This file is the only write.

## MODEL ATTESTATION — read this before the findings

This round-4 review was performed by **Fable 5** (`claude-fable-5`) — the model
`AGENTS.md` §"Independent Fable review before every ratification" actually
requires. **Rounds 1 and 2 were performed by Opus 5** under two separate
maintainer-authorized one-off deviations; the maintainer's choice of Fable for
this round closes that deviation going forward, and nothing more.

**A clean Fable round 4 does NOT retroactively make rounds 1 and 2 Fable
work.** The eventual ratification record MUST name the model that performed
each review it attests to: rounds 1 and 2 → Opus 5, round 4 → Fable 5. Writing
a blanket `reviewer_model: fable` over a review history that was two-thirds
Opus would be a false attestation — the defect this plan's correction T1 exists
for. Writing a blanket `opus` would misname the review this accept actually
gates on. Neither single value is honest; the record needs the per-round
attribution. (The ledger's own `overseer-pfpfty.2` record already states this
correctly; the proposal's §"Amendment history" does not — see Blocker 3.)

## Pinned read

Every quotation below comes from committed state via `git show`, never the
working tree — that primary checkout is behind origin and carries other
sessions' files.

| | |
|---|---|
| Brief's pin | `d3baa96341babd92047c607a4bc4f917751b8bcb` |
| `origin/master` at review start | `9af1b4e5a125f23c525c7c4bf07437191a808772` (one commit past the pin: `9af1b4e`, touches only `plan/supervisor-scratch-discipline/handoff.md`) |
| Proposal at that SHA | 630 lines, md5 `48f7ea91d5f2db996ba832d1cbf8074f` — **matches the brief exactly** |
| The four spec files | byte-identical since `ca7068b8` (round 2's pin) — `spec.md` md5 `c390135853629ca73d22904bb3d1843b` re-derived, and the `ca7068b8..9af1b4e5` diffstat contains no `SPECIFICATION/*.md` other than the proposal, no `tests/heading-coverage.json`, no `tests/integration/` |
| `origin/master` re-checked at review END | **`a868d4f1754905c7ada29bd76930522b46d4bc70` — master moved DURING this review.** The landing (`50dfc4a`, `aec745a`, `a868d4f`, release 0.34.3) touches `_supervisor_restart_attention.py`, its tests, version files, and a plan handoff — **no spec file, no manifest, no registry/discovery/prompt module, and not the integration test cited below.** Proposal md5 at the end tip: `48f7ea91...`, unchanged. Nothing relied on below moved. |

## Bottom line, in plain language

**The four round-2 blockers are genuinely cleared — every one re-derived
against live bytes, not read off the proposal's table. All 24 replacement
targets match verbatim and uniquely, the in-memory application of all 24 is
clean, and the post-application sweeps that caught round 2's junction defects
come back empty. But the round-3/round-4 amendments introduce three new
defects, all in the ~100 added lines: the new §"Ratification sequencing"
section's two load-bearing claims about `overseer-pfpfty.9` both fail
re-derivation; EDIT 3's ratified text grounds the foreman's anchor-read on a
permission whose surviving text is purpose-restricted to something
anchor-population is not; and the §"Amendment history" attestation instruction
("`reviewer_model: opus`, never `fable`") became false the moment the
maintainer commissioned this Fable round.** It should not be ratified as
written; all three fixes are small and none reopens the architecture.

### Notation

- **"live"** = bytes at `git show 9af1b4e5:<path>` in `livespec-overseer`
  (spec files byte-identical at the end tip `a868d4f1`), or at the named
  sibling repo's `origin/master`.
- **"post-application"** = the text after applying all 24 replacements plus
  the one scenario addition, computed by in-memory simulation on
  whitespace-normalized text; nothing written to disk.
- Every zero below carries a positive control, and the controls are on the
  READER where the reader is the risk: every mutation control was asserted
  `mutated != original` before use, so no control could silently no-op.

---

## Part A — the four round-2 blockers, re-derived

The proposal's §"What round 2 changed" table asserts all four are cleared. Each
row was re-derived against live bytes and tested against round 2's own "what
would clear it" paragraph, not against the table.

| # | Round-2 blocker | Verdict | Basis |
|---|---|---|---|
| 1 | Respawn gate on an unpopulated `epic`; EDIT 4 foreclosed the design record's source | **CLEARED IN SUBSTANCE** — actor and moment named, EDIT 4 reconciled, population path filed and cited; but the citing section carries new Blockers 1 and 2 | below |
| 2 | "Supervisor handoff entries" an undefined category | **CLEARED** | below |
| 3 | EDIT 6 orphaned the `ctx_threshold` em-dash clause | **CLEARED** | below |
| 4 | "This revision RETIRES…" meta-commentary as spec text | **CLEARED** | below |

### Round-2 blocker 1 — CLEARED IN SUBSTANCE, with new defects in the clearing text

Round 2 offered three clearing routes; the amendment took (a) and (c)
together and kept the hard gate, which round 2 explicitly permitted:

- **Actor and moment named** (EDIT 3 ratified text): "the id is recorded into
  the row AT TRACK ASSIGNMENT, from the plan's write-once metadata anchor, by
  the surface performing the assignment — the authorized unattended foreman
  … or supervise-plan at plan open. The daemon consumes the recorded value and
  never reads the anchor itself."
- **EDIT 4's foreclosing sentence reconciled**: the replacement now reads
  "…the daemon never reads one — which is why the id is recorded at track
  assignment by a surface that MAY read plan-tree text as evidence, and merely
  consumed by the daemon thereafter." The daemon-versus-assigning-surface
  distinction lets both sentences be true at once, exactly as round 2 asked.
- **Population path cited**: `overseer-pfpfty.9` exists in the ledger —
  "pfpfty P9: populate the mapping-store epic id from the plan write-once
  anchor (populate only, no repoint)", title quoted by the proposal verbatim.
  `bd show` confirms: `.9` has no dependency on `.2`; `.2` DEPENDS ON `.1`,
  `.6`, `.8`, `.9`; `.2` BLOCKS `.4`, `.7`, `.3`. The graph `.9 → .2 → .4` is
  acyclic — the earlier `.4`-citation cycle the brief describes was really
  fixed by the split (commit `4abceb7`).
- **Ground truth re-measured, not inherited from round 2**: the live mapping
  store still holds 23 rows, `epic` key present in 23/23, non-null in **0**
  (controls: 23/23 carry `handoff`, 23/23 carry `resume`); at the current tip
  the only `epic` assignment anywhere in either overseer tree is a test
  fixture (`overseer/test_registry.py:125`) — product code still only
  declares, serializes, and reads it back (control: the same grep returns 3
  `resume` lines in `_supervisor_discovery.py`). So `.9` has not landed, and
  the ordering constraint is still live.

Why only "in substance": the clearing text itself is where Blockers 1 and 2
below live — the sequencing section's justification for the `.9`-first order
is false in both its halves, and EDIT 3's foreman arm cites a permission whose
own text excludes the cited use.

### Round-2 blocker 2 — CLEARED

Round 2's clearing condition: define the discriminator in EDIT 3's
definitional passage, carry the filter into both prompts, and reconcile the
"never to the worker's own read-first state" sentence. All three landed:

- EDIT 3 (ratified): "ATTRIBUTION is what separates them: a SUPERVISOR
  HANDOFF ENTRY is an entry attributed to the track's supervisor entity, and a
  worker's entries are those attributed to the worker entity."
- EDIT 5's supervisor prompt: "read the entries on this track's ledger epic
  attributed to the supervisor entity and follow them, with the repository
  path, the epic id, and that entity name all stated literally." EDIT 6's
  contract: "The prompt MUST name the track's repository path, the plan's epic
  id, and the entity whose entries to read, all three LITERALLY."
- The separation sentence is recast on the shared stream: "The pair shares one
  epic and one stream; attribution, not a separate store, is what keeps the
  two layers distinct, and neither member may append under the other's
  attribution."

The attribution anchor holds against the live design record: livespec core
`SPECIFICATION/spec.md:378` (§"The Planning Lane") reads verbatim "append-only,
per-entry ledger entries, each individually attributed and timestamped", and
the orchestrator's §"Ledger-held handoff persistence" says the same
("append-only, per-entry, individually attributed, and timestamped").

### Round-2 blocker 3 — CLEARED

The replace-target is EXTENDED exactly as prescribed: it now runs through
"…readers MUST NOT materialize the default at read time." and matches live
`contracts.md` verbatim and uniquely (target #13 in the fidelity table below);
the trailing "Unknown keys survive rewrites." sits outside the target and
survives. The replacement re-emits the clause immediately after
`ctx_threshold` with its referent named explicitly — "a row without
`ctx_threshold` means 'inherit the daemon default'" — and only then introduces
the `epic`/`handoff`/`resume` prose. Post-application sweep: "a row without
the key" occurs **0** times in all four files (control: the same sweep finds
"a row without `ctx_threshold`" in the applied text), so the orphaned-referent
reading that contradicted the REQUIRED-epic rule is gone. The implemented
invariant (`_registry_store.py:129-133`) keeps its anchor.

### Round-2 blocker 4 — CLEARED

The meta-sentence is deleted; only the contract survives: "The mapping store
MUST NOT emit a `handoff` key; a legacy row still carrying one is read without
error and rewritten without it." `resume` is recast positively ("`resume`
remains the operator's optional per-track override of the respawn prompt…").
Post-application sweep: `this revision|this proposal` matches **0** lines
across all four files (control: the identical sweep run over the PROPOSAL's
own connective prose returns hits, so the pattern demonstrably fires).

---

## Part B — new defects introduced by the round-3/round-4 amendments

## BLOCKER 1 — §"Ratification sequencing": both load-bearing claims about `overseer-pfpfty.9` fail re-derivation

*Brief check C; criterion 2 (design-record fidelity); defect-class file's
"claims the reviewer must re-derive, not trust".*

**Where.** Proposal §"Ratification sequencing" (lines 149-167) — the section
that tells the ratifier what order is safe. It is proposal prose, not ratified
text, but it is the stated authority for the accept sequencing, which is what
makes its claims load-bearing.

**Claim (a): "at the moment a track is discovered or assigned — the same
mechanism this proposal describes in EDIT 3."** It is not the same mechanism.
EDIT 3's ratified mechanism names ASSIGNMENT only, performed by the assigning
surface (foreman or supervise-plan), and expressly bars the daemon:
"The daemon consumes the recorded value and never reads the anchor itself" and
"The discovery path performs no file-level probe inside a plan directory."
Discovery, by contrast, is the DAEMON's act in both the current and the
amended spec ("The track list is re-discovered every observation cycle…";
"the overseer enumerates plan DIRECTORIES to discover tracks"). The
"discovered" arm — quoted faithfully from `.9`'s own description ("at the
moment a track is discovered/assigned") — therefore names a population moment
whose actor is forbidden, by EDIT 3 itself, from reading the anchor. An
implementer following `.9`'s description on the discovery arm builds exactly
what EDIT 3 prohibits.

**Claim (b): "populating `epic` writes a value nothing yet reads … and
therefore contradicts no clause of the CURRENT spec."** False twice over:

1. **The current persisted-facts clause excludes it.** Live `spec.md`
   §"Track discovery and the mapping store" (this proposal's own EDIT 4
   target, verified verbatim): "The store persists ONLY facts that cannot be
   re-derived from the filesystem: the topic-to-session mapping, a custom
   resume line, a per-track threshold override, and a pinned session
   identity." A populated epic id is a persisted fact that is (i) not among
   the four members and (ii) re-derivable from the filesystem — its source is
   the write-once anchor, a file (livespec core `spec.md:375`: "exactly one
   write-once metadata anchor written at plan open. The anchor MUST name the
   epic id"). The decisive evidence is the proposal's own EDIT 4: it amends
   this exact clause — recasting the criterion to "facts the DAEMON cannot
   re-derive for itself", adding "the plan's ledger epic id" as a member, and
   supplying a bespoke justification for why the id qualifies. If the current
   clause already tolerated a populated epic, none of that amendment would be
   needed. The proposal cannot simultaneously amend the enumeration because
   the epic id is outside it and claim that persisting the epic id ahead of
   that amendment contradicts nothing.
2. **The discovery arm violates a second current clause.** If the population
   runs at discovery (claim (a)'s arm), it breaks the live "Discovery keys on
   the DIRECTORY existing — it never reads, stats, or hashes any file inside a
   plan directory" — a hard current contract, not merely a future one.

**Fair statement of the counter-argument.** The live store already persists
derivable `handoff` values not in the enumeration, so the ONLY-clause is
evidently held loosely today. But pre-existing drift does not make a new
violation a non-contradiction — this proposal retires `handoff` partly
BECAUSE of that drift — and a claim offered as the justification for a
ratification ordering has to be true, not merely no worse than existing
sloppiness. The refusal-gate consequence round 2 feared is also genuinely
mitigated here (the gate ratifies only after `.9` lands), so the ORDER chosen
may well be the right one; what is defective is the argument the ratifier is
given for it, which a doctor pass or drift sweep run in the `.9`-landed,
pre-accept window would immediately falsify.

**Why it matters.** The section exists so the ratifier does not have to
discover the ordering hazard; a false neutrality claim re-creates the hazard
one level up. The same false claim also appears in `.9`'s ledger description
and `.2`'s cycle-fix comment — it will propagate to whoever implements `.9`.

**What would clear it.** Rewrite the paragraph to (i) state the population
moment as EDIT 3 states it — at assignment, by the assigning surface, never
the daemon's discovery — and flag `.9`'s "discovered/" wording for correction
in the ledger (a write outside this review's permission); and (ii) replace
"contradicts no clause of the CURRENT spec" with the true, still-sufficient
statement: the population changes no read-first behavior, no respawn prompt,
and no daemon decision, but it does put a populated `epic` ahead of the
enumeration amendment that legalizes it, which is why the accept must follow
`.9` immediately (or land with it), not merely eventually.

---

## BLOCKER 2 — EDIT 3 grounds the foreman's anchor-read on a permission whose surviving text excludes that use

*Criterion 3 (drift-sweep completeness); the junction defect class only
simulation can see — target and replacement are individually correct.*

**Where.** Proposal EDIT 3 (ratified text), landing in `livespec-overseer`
`SPECIFICATION/spec.md` §"Track discovery and the mapping store"; the
conflicting clause is the surviving third paragraph of §"Non-interference with
tracked work" (live `spec.md:563-569`), which no edit touches.

**What the amendment ratifies.** "…the id is recorded into the row AT TRACK
ASSIGNMENT, from the plan's write-once metadata anchor, by the surface
performing the assignment — the authorized unattended foreman, **which
§"Non-interference with tracked work" already permits to read plan-tree text
solely as evidence**, or supervise-plan at plan open."

**What the cited clause actually says** (surviving, unamended, in the same
file): "An authorized UNATTENDED operator surface — the foreman — MAY READ
files under a watched repository's plan tree … **solely as EVIDENCE for its
own decision-routing**."

**Why it matters.** The citation is load-bearing — it is the proposal's whole
answer to "what authorizes any unattended actor to read the anchor at all?" —
and it elides the half of the clause that decides the question. "Solely" makes
the purpose exclusive, and the permitted purpose is the foreman's OWN
decision-routing (its report/consensus/escalation function, defined earlier in
the spec). Reading the anchor in order to record its content into the daemon's
mapping store, so that the DAEMON can later build a respawn prompt, is
provisioning for another actor — not the foreman's own decision-routing under
any natural reading. Post-application, §"Track discovery and the mapping
store" requires of the foreman what §"Non-interference with tracked work"'s
"solely" excludes, and the paraphrase ("solely as evidence", full stop) is
precisely what keeps the conflict invisible to a target-matching check: both
the target and the replacement are correct; the junction with the SURVIVING
paragraph is not.

I verified the good-faith prerequisites first: the foreman-evidence paragraph
IS in the cited section (so the cross-reference resolves — positive control:
`grep foreman` returns it at `spec.md:563` inside §"Non-interference…"), it
survives EDIT 5's two-paragraph replacement untouched (the verified target
ends before it), and nothing forbids the foreman writing the mapping store
itself (its write prohibitions cover state files, `plan/`-tree files, and
tracked files; `constraints.md` §"Atomicity" already contemplates non-daemon
writers of the overseer's stores). The defect is solely the read-PURPOSE
junction.

**Fair statement of the counter-argument.** Round 2's own clearing sketch
suggested "the foreman reading the write-once anchor as evidence, which
existing `constraints.md` already permits" — and `constraints.md`'s parallel
clause says only "solely as evidence", without the decision-routing qualifier.
The author followed the sketch. But EDIT 3 cites the spec.md section, whose
version carries the qualifier, and a reviewer's fix sketch is not spec text:
the author owns making the junction sound, and both clauses survive
ratification side by side. One could also stretch "evidence for its own
decision-routing" to cover assignment bookkeeping; the stretch is exactly what
a spec should not require.

**Supporting wobble, same sentence (not separately counted).** The apposition
defines "the surface performing the assignment" as the foreman or
supervise-plan "at plan open" — but the store's own definition is "one row per
assigned track" (`contracts.md:263`), and at plan open a track is typically
unassigned, so the supervise-plan arm records "into the row" at a moment the
row need not exist; and nothing elsewhere in the spec establishes either
surface as the one that assigns (assignment today is the operator's act —
"startable, never started"). A one-clause tightening of actor and moment
resolves this together with the main defect.

**What would clear it.** Either amend the surviving foreman paragraph in the
same payload so the purpose grant covers the new duty (e.g. "solely as
evidence for its own decision-routing **and to record the plan's epic id into
the track's mapping-store row at assignment**"), or re-ground EDIT 3's
citation on a purpose the clause actually grants, and state the moment
consistently for both arms (a row is created at assignment; supervise-plan's
recording lands then, or the sentence says what happens when no row exists
yet).

---

## BLOCKER 3 — the proposal's attestation instruction became false when this Fable round was commissioned

*Defect class 1's mechanism (a claim expired by a later event), applied to the
review-history prose the ratifier acts on; correction T1's exact subject.*

**Where.** Proposal §"Amendment history" (lines 28-32): "Both rounds were
performed by Opus 5 under maintainer-authorized one-off deviations … The
ratification record for this proposal MUST therefore read
`reviewer_model: opus`, never `fable`."

**Why it matters.** The sentence was accurate when written — the only reviews
then in existence were Opus. The maintainer has since commissioned this
round 4 on Fable 5, and if ratification proceeds it proceeds on THIS round's
verdict. Followed literally now, the proposal's "MUST … never `fable`"
instructs the ratifier to attest that the review the accept gates on was
performed by Opus — false in the other direction from the falsehood it was
written to prevent. The ledger already knows better: `overseer-pfpfty.2`'s
own record states "a round-4 verdict will be attributable to fable — but the
ROUND-1 AND ROUND-2 verdicts remain Opus work, and any ratification record
must state the model that actually performed the review it attests to." The
proposal and the ledger record now give the ratifier contradictory
instructions, and the proposal is the artifact the revise flow reads. A false
attestation either way is the T1 defect; this is the one blocker here that a
CLI cannot catch and only the person filling the field can.

**What would clear it.** One sentence: replace the "MUST therefore read
`reviewer_model: opus`, never `fable`" instruction with the per-round rule —
the ratification record names the model per review round (rounds 1-2: Opus 5;
round 4: Fable 5), and no blanket value is honest for this history. The next
amendment will touch this section anyway to record round 4 in the history.

---

## Part C — checks that PASSED

Recorded so the maintainer can see the review was not one-sided.

**Criterion 1 — replacement-target fidelity: PASS, count re-derived.** The
proposal contains 41 blockquote blocks; structural classification (a block
whose next non-blank line is exactly `with:`, paired with the block that
follows) yields **20** block replace-targets, plus **4** inline
`Replace "…" with "…"` bullets in EDIT 4 = **24**, matching the brief's count
by re-derivation. All 24 match their live file **verbatim and exactly once**
after whitespace normalization (9 block + 4 inline in `spec.md`, 4 in
`contracts.md`, 1 in `constraints.md`, 6 in `scenarios.md` — each target was
searched against ALL four files, so uniqueness is tree-wide, not per-file).
The 41st block is the one pure addition (the new scenario), correctly not a
replacement.

*Controls, on the reader and provably non-no-op:* every target was re-probed
in mutated form (first alphabetic run of ≥3 characters replaced with a
sentinel token absent from every file), with `mutated != original` ASSERTED
before use — the trap the brief describes, a mutation that silently no-ops,
is structurally excluded. Result: 24/24 unmutated hits, 0/24 mutant hits.
Reader anchors: a known-present string ("The overseer's DAEMON") returns
exactly 1; a known-absent string returns 0.

**In-memory application: 24/24 applied**, plus the scenario addition; a
different instrument (sequential in-place substitution requiring uniqueness at
apply time) agreeing with the counting instrument.

**Criterion 3 — drift sweep, run on the post-application result:**

| token | spec.md | contracts.md | constraints.md | scenarios.md |
|---|---|---|---|---|
| worker `handoff.md` | 0 | 0 | 0 | 0 |
| `plan thread`/`plan-thread` | 0 | 0 | 0 | 0 |
| `supervisor-handoff.md` | 1 | 0 | 1 | 0 |
| `this revision`/`this proposal` | 0 | 0 | 0 | 0 |
| `a row without the key` | 0 | 0 | 0 | 0 |

Both surviving `supervisor-handoff.md` hits sit inside the NEW prohibition
clauses ("never by creating or updating … through the pull request path") —
intended, not drift. Every surviving bare `handoff` occurrence was read in
context: all are either the new ledger-entry vocabulary, the retired-key
tolerance clause, or `contracts.md`'s state-file-sense "no handoff hash, no
payload" (correctly left alone, as rounds 1 and 2 both noted). Every
`§"…"` cross-reference in the post-application text resolves to an existing
`## ` heading (16 in spec.md, 15 in contracts.md, 1 in constraints.md — all
resolve; the check distinguishes, since it uses the post-rename heading set).

**Criterion 4 — ratification mechanics: PASS.** Front-matter
`topic: planning-lane-realization` equals the file stem. Exactly two `## `
heading changes (one rename, one addition — re-derived by enumeration) matched
by exactly two specified `tests/heading-coverage.json` co-edits. The old
heading exists in the live manifest exactly once, mapped to
`test_scenario_the_supervision_probe_is_liveness_gated_and_existence_only`;
the live test still asserts `assert _HANDOFF in live_probes` at
`tests/integration/test_discovery_and_relay.py:282`, exactly as the proposal
cites. Both replacement `reason` strings say "integration-tier-or-above",
satisfying `check-heading-coverage` direction 4. Simulated post-ratification
coverage: **0 unmapped headings, 0 orphaned entries** over 95(+1) entries —
*control on the reader:* deliberately removing the renamed entry from the
simulated manifest produces exactly 1 unmapped heading, so the checker
demonstrably reads both sides and can fail.

**Criterion 5 — cross-repo consistency: PASS.** Verified live at each
sibling's `origin/master`: livespec core `spec.md:375` (anchor names the epic
id; plan store must not contain `supervisor-handoff.md`) and `:378`
(attribution guarantee, quoted verbatim in the proposal's Summary, section
§"The Planning Lane" as cited); orchestrator `contracts.md` §"The two seams"
still reads "plan ↔ ledger, via the sanctioned plan surface only" (at
`f8789004`), so "the orchestrator's sanctioned plan surface" in the ratified
text still resolves. Ledger: `.9`, `.7`, `.2`, `.4` all exist with the roles
the proposal assigns them; `.7`'s description matches the test, line, and both
`TODO` replacements; the dependency graph is `.9 → .2 → .4`, acyclic, and
`.9` carries no blocking dependency — the brief's measured state re-measured
and confirmed.

**Brief check C, the ledger half: PASS** (the spec half is Blocker 1). The
cycle fix is complete in the ledger — no clause of the DEPENDENCY graph still
assumes the old `.4`-population arrangement, and the proposal's §"What round 2
changed" table was corrected to cite `.9` (commit `4abceb7`) so no stale
`.4`-as-population citation survives in the proposal either (grep for
`pfpfty.4` in the proposal returns only its correct narrow role, the gated
read-first repoint).

**Method note, per the shared-instrument discipline (defect class 4).** One
instrument failure occurred and was caught: my first cross-repo grep for
"sanctioned plan surface" returned zero because the phrase line-wraps in the
orchestrator's file ("sanctioned plan\nsurface"), while its positive control
(108 lines matching `plan`) passed — a passing control on the QUERY that said
nothing about the UNIT. The zero was not trusted; the section was read
directly and the phrase confirmed present. Recorded because it is exactly the
class the brief warns about, and because round 2's verification of the same
citation used line-insensitive normalization and would not have hit it.

---

## Non-blocking observations

Recorded for the author; none should cost a round on its own.

1. **"authors the same two layers it always has"** (EDIT 5, ratified text) is
   a historical comparison addressed to a reader who knows the old contract.
   It does not become false after the accept, so it does not block, but the
   plain grant without "it always has" is the cleaner spec sentence.
2. **"Every entry carries an attribution by construction"** (EDIT 3, ratified
   text) is a positive claim about a sibling-owned guarantee, verified true
   today (core `spec.md:378`; orchestrator §"Ledger-held handoff
   persistence") but unanchored in the ratified text — same shape as round 2's
   unanchored "sanctioned plan surface" observation. A citation in the style
   the design record itself uses would let a future reader tell a still-true
   claim from a rotted one.
3. **"asserts at line 282"** (§Co-edited non-spec files) is accurate at both
   the start and end tips of this review, but it is a rot-prone magnitude of
   exactly the kind this revision deleted for `spec.md` — and the assertion
   string is already quoted beside it, so the number adds nothing. Delete it
   in the next touch.
4. **The worker-prompt clauses state different literal-content minima**:
   spec.md (EDIT 2) requires repository path + epic id; contracts.md (EDIT 6)
   requires repository path + epic id + entity name for both entities. A
   conformant prompt satisfies both (subset/superset, not a contradiction);
   noted so a later sweep does not misread it, and because stating the entity
   in spec.md's clause too would cost three words.
5. **The false neutrality claim propagated into the ledger** — `.9`'s
   description and `.2`'s cycle-fix comment carry the same "contradicts no
   clause of the CURRENT spec" sentence Blocker 1 falsifies, and `.9`'s
   "discovered/assigned" wording carries the same discovery-arm hazard. This
   review is forbidden to write the ledger; whoever amends the proposal should
   correct both records in the same pass.

---

## Summary table

| # | Class | Finding | Severity |
|---|---|---|---|
| 1 | Brief C / criterion 2 | §"Ratification sequencing": "the same mechanism as EDIT 3" is false (`.9`'s "discovered" arm names the daemon's pass, which EDIT 3 bars from the anchor), and "contradicts no clause of the CURRENT spec" is false (the current persisted-facts ONLY-enumeration — the very clause EDIT 4 amends so `epic` qualifies — plus, on the discovery arm, the current no-read discovery clause) | **BLOCKER** |
| 2 | Criterion 3 / junction | EDIT 3 cites the foreman's read permission as "solely as evidence", eliding the surviving clause's "for its own decision-routing" purpose restriction, while ratifying an anchor-read whose purpose is provisioning the daemon — the purpose clause is left unamended and the two sections conflict post-application | **BLOCKER** |
| 3 | T1 / expired claim | §"Amendment history"'s "MUST therefore read `reviewer_model: opus`, never `fable`" became false when the maintainer commissioned this Fable round; the ledger's `.2` record already states the correct per-round rule, so the two instructions now conflict | **BLOCKER** |
| R2-1 | — | Cleared in substance: actor+moment named, EDIT 4 reconciled, `.9` filed/cited, graph acyclic, gate kept; new defects 1-2 sit in the clearing text | PASS w/ new defects |
| R2-2 | — | Cleared: attribution discriminator defined, carried into both prompts with the entity named literally, separation sentence reconciled; anchor verified live in both sibling records | PASS |
| R2-3 | — | Cleared: extended target verbatim+unique, referent re-emitted as "a row without `ctx_threshold`", 0 orphaned-referent hits post-application | PASS |
| R2-4 | — | Cleared: meta-commentary deleted, 0 `this revision/proposal` lines post-application, `resume` recast positively | PASS |
| — | Criterion 1 | 24/24 targets verbatim and tree-wide-unique; mutation controls asserted non-no-op; 24/24 applied in memory | PASS |
| — | Criterion 4 | topic=stem; 2 heading changes ↔ 2 co-edits; integration-tier reasons; simulated coverage 0/0 with a discriminating removal control | PASS |
| — | Criterion 5 | Core anchor+attribution quotes, orchestrator seam phrase, and all four cited work-items verified live | PASS |
| — | T3-style end check | Master moved during the review (`9af1b4e5` → `a868d4f1`); the landing touches no spec file, manifest, or cited test/module; proposal md5 unchanged | NOTED |

---

## VERDICT

**3 BLOCKERS**

1. §"Ratification sequencing"'s two load-bearing claims about
   `overseer-pfpfty.9` both fail re-derivation: the "discovered" arm of the
   population moment is not "the same mechanism this proposal describes in
   EDIT 3" (EDIT 3 bars the daemon — discovery's actor — from the anchor), and
   "contradicts no clause of the CURRENT spec" is disproved by the proposal's
   own EDIT 4, which amends the current persisted-facts ONLY-enumeration
   precisely because a populated epic id falls outside it (and, on the
   discovery arm, by the current no-read discovery clause). The prescribed
   `.9`-first order may still be right; the justification the ratifier is
   handed for it is false.
2. EDIT 3's ratified text grounds the foreman's anchor-read on
   §"Non-interference with tracked work" paraphrased as "solely as evidence",
   eliding the surviving clause's full restriction — "solely as EVIDENCE for
   its own decision-routing" — while the ratified duty (recording the id into
   the daemon's mapping store for the respawn prompt) is not the foreman's own
   decision-routing; no edit amends the purpose clause, so the two sections
   contradict post-application. A junction defect invisible to target-matching:
   target and replacement are individually correct.
3. §"Amendment history"'s instruction "The ratification record for this
   proposal MUST therefore read `reviewer_model: opus`, never `fable`" expired
   when the maintainer commissioned this Fable round 4: followed literally it
   now mandates a false attestation about the review the accept gates on,
   and it contradicts the per-round rule `overseer-pfpfty.2`'s own ledger
   record already states. The record must name the model per round —
   rounds 1-2: Opus 5; round 4: Fable 5.

All four round-2 blockers are genuinely cleared. Blockers 1 and 2 are cleared
together by one rewrite of the sequencing paragraph plus one clause-level
amendment (or re-grounding) of the foreman purpose grant; Blocker 3 is one
sentence in a section the next amendment touches anyway.

**Reviewed by Fable 5 (`claude-fable-5`) on 2026-08-12 — the model
`AGENTS.md` §"Independent Fable review before every ratification" requires.
Rounds 1 and 2 were performed by Opus 5 under maintainer-authorized one-offs;
this clean-model round does NOT retroactively make them Fable work, and the
eventual ratification record MUST name the model that performed each review it
attests to — a blanket `reviewer_model: fable` over a two-thirds-Opus history
would be a false attestation, exactly as a blanket `opus` over this round
would be.**

**Pinned at `livespec-overseer` `origin/master` = `9af1b4e5` at review start
(proposal 630 lines, md5 `48f7ea91d5f2db996ba832d1cbf8074f`, matching the
brief); re-checked at review end = `a868d4f1` — master moved during the
review, but the landing touches no byte this review relied on, and the
proposal is unchanged at the end tip.**
