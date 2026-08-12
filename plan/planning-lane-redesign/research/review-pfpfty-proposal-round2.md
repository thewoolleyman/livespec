# Adversarial review — round 2

**Proposal under review:** `SPECIFICATION/proposed_changes/planning-lane-realization.md`
in repository **`livespec-overseer`**
(<https://github.com/thewoolleyman/livespec-overseer/blob/master/SPECIFICATION/proposed_changes/planning-lane-realization.md>).

**Review is READ-ONLY.** Nothing was edited, created, deleted, committed,
pushed, ratified, or filed. No worktree or branch was created. No beads ledger
was written (`bd show` reads only). No `just check` was run. This file is the
only write.

## Pinned read

Every quotation below comes from committed state via `git show`, never the
working tree — that primary checkout carries another session's uncommitted file.

| | |
|---|---|
| `livespec-overseer` `origin/master` at review start | `ca7068b8b002e7f1930deefa6fd079d0917a21e9` |
| Proposal md5 at that SHA | `a4b4c5586a04873d55bfd4ed507ade08` (522 lines) |
| `origin/master` re-checked at review END (after `git fetch`) | `ca7068b8b002e7f1930deefa6fd079d0917a21e9` — **unmoved** |
| Proposal md5 at review end | `a4b4c5586a04873d55bfd4ed507ade08` — **unchanged** |

Both match the brief exactly. The concurrent `overseer-4aqtcq` dispatch did not
land anything during this review, so nothing relied on below expired mid-review.

**But master DID move between round 1 and this review, and it mattered.** See
§"T3 check" — a sibling lane landed +15 lines in `spec.md`, +26 in
`scenarios.md`, +8 in `contracts.md` after the amendment merged. One of the
proposal's claims went stale as a result.

---

## MODEL ATTESTATION — read this before the findings

`AGENTS.md` §"Independent Fable review before every ratification" requires a
**Fable-model** reviewer. This review was performed by **Opus 5**
(`claude-opus-5[1m]`).

| | |
|---|---|
| Model that actually performed this review | **Opus 5** (`claude-opus-5[1m]`) |
| Required model | Fable 5 (`claude-fable-5`) |
| Authorization | The maintainer authorized Opus for this round on **2026-08-12**, as a **deliberate SECOND one-off**, having been told explicitly that this REPEATS the round-1 deviation rather than closing it. |
| Round performed | Round 2, 2026-08-12 |

**Consequence for whoever ratifies.** Any ratification record for this proposal
MUST read `reviewer_model: opus`. **Never `fable`.** Writing `fable` would be a
false attestation — the exact defect this plan's correction **T1** was written
about, where a conforming-looking review record was minted and the CLI accepted
it because it validates field *shape* rather than whether a review occurred. The
CLI cannot catch this; only the person filling the field can.

Independence is intact: this review did not author the proposal
(`author: claude-fable-5`, filed under `overseer-pfpfty.6`), so only the model
attestation deviates, not the independence.

**Instrument-variation note (defect class 4).** Round 1 was also Opus, so the
two rounds do NOT constitute independent instruments. I therefore deliberately
varied the *method* rather than relying on the reviewer differing: round 1
verified replacement targets by substring-containment counting; this round
additionally **simulated applying all 24 replacements in memory and swept the
RESULT**, which is a different measurement that can catch what counting cannot
(orphaned referents, adjacency breaks). Two of the four blockers below were
found only by the simulation and would have been invisible to a repeat of round
1's method.

---

## Bottom line, in plain language

**The amendment did substantial, honest work. Four of the six round-1 blockers
are fully cleared, one is cleared in substance, and one is only partially
cleared. But the fixes introduced four new defects, three of them in the same
two edits that were rewritten to clear round-1 blockers 1 and 4. It should not
be ratified as written.**

The headline problem is this. Round 1 said the restart prompt had become an
undefined category. The amendment's answer is to make the prompt name a
**concrete epic id** — which is the right answer — and to **refuse the respawn
entirely when no epic id is recorded**. That refusal is a hard gate on a field
that, right now, **nothing populates**: all 23 rows in the live mapping store
carry `epic: null`, and there are exactly four mentions of `epic` in the entire
overseer Python tree, none of which ever assigns it a value. Worse, the
amendment's own justifying sentence forecloses the one source the ratified
design record provides for that id — the plan store's write-once metadata
anchor — and that same anchor is precisely what the filed implementation slice
`overseer-pfpfty.4` names as where the epic id comes from. So the amended spec
would make its own implementation plan illegal while blocking every restart.

The second new problem is the supervisor half of the same fix. The prompt for a
supervisor pair member points at "the supervisor handoff entries on that same
epic" — but no fleet contract defines a supervisor-handoff entry class, and the
proposal never says what distinguishes one. Applying the proposal's *own* new
rule to itself: "a prompt naming only a category is not a pointer."

**Four blockers below.** Blockers 1 and 2 are substantive; 3 and 4 are wording
defects that would nonetheless ratify a contradiction and a status report into
the spec, and both live in the same replacement — one rewrite clears both.

### Notation used below

- **"live"** = bytes at `git show ca7068b8:<path>` in the named repo.
- **"positive control"** = a second query, stated beside every zero or negative
  result, proving the same query shape can report a hit. No zero is reported
  here without one. Where the control is on the READER rather than the query, I
  say so and say how I know the control provably changed what it claims to.
- **"post-application"** = the text as it would read after all 24 replacements
  land, computed by in-memory simulation, never written to disk.

---

## Part A — the six round-1 blockers, re-derived

The proposal's §"What round 1 changed" table asserts all six are cleared. That
is the author's claim about its own work. Every row below was re-derived against
live bytes; the table was not allowed to stand in for verification.

| # | Round-1 blocker | Verdict | Basis |
|---|---|---|---|
| 1 | Restart prompt became an undefined category; "ledger" defined nowhere | **PARTIALLY CLEARED** | Definition and worker-side locator landed; locator is unpopulatable (new Blocker 1) and the supervisor side is still a bare category (new Blocker 2) |
| 2 | Probe scenario rewritten into the case its bound test rejects | **CLEARED** | Heading renamed, `Given` amended, co-edit specified with an integration-tier `reason`, `overseer-pfpfty.7` verified to exist and match |
| 3 | `.ai/supervisor-protocol.md` permission + guard silently revoked | **CLEARED** | Target now quoted verbatim and unique; all four obligations preserved; both drift survivors amended |
| 4 | `handoff`/`resume` misdescribed; closed enumeration left contradicting | **CLEARED IN SUBSTANCE** | Retirement scoped to `handoff` only, `resume` preserved, `spec.md` enumeration amended — but the replacement introduces new Blockers 3 and 4 |
| 5 | "Planning Lane" installed where "plan" is required | **CLEARED** | All four replacements say **plan**; post-application sweep finds zero `plan[ -]thread` in all four files |
| 6 | Direct Control-Plane ledger append, no sanctioned-surface routing | **CLEARED** | Routing stated explicitly in BOTH replacements; sibling citation re-verified live |

### Round-1 blocker 1 — PARTIALLY CLEARED

**What landed, and it is real.** EDIT 3 adds a genuine defining passage to
`spec.md` §"Track discovery and the mapping store":

> The read-first target it hands to sessions is the plan's LEDGER-HELD PLAN
> STATE: the append-only, individually attributed and timestamped handoff
> entries carried on the governed plan's ledger epic, whose id the mapping store
> persists as that track's `epic` value.

EDIT 6 makes the locator obligation explicit in `contracts.md`:

> The prompt MUST name the track's repository path and the plan's epic id
> LITERALLY, so a session opening with no prior context can resolve what to read
> without opening any plan-tree file; a prompt naming only a category is not a
> pointer.

and adds the protective refusal, plus a new scenario pinning both clauses. That
answers round 1's clearing condition (a) *as written* — a concrete locator — and
condition (b) — a defining passage plus a scenario. Credit where due: this is a
better answer than round 1 asked for, because it also protects against spending
a `ready` on an unresolvable prompt.

**Why it is only partial.** The locator it names cannot be populated (Blocker 1)
and the supervisor variant of the prompt is still a bare category (Blocker 2).

### Round-1 blocker 2 — CLEARED

Verified independently, not from the table:

- The rename target `## Scenario: The supervision-artifact existence probe is
  liveness-gated and existence-only` exists verbatim and **exactly once** in
  live `scenarios.md`.
- The now-inert `Given` **is** amended (proposal lines 426-433), which round 1
  specifically required.
- The bound test's assertion is exactly as cited. Live
  `tests/integration/test_discovery_and_relay.py:282`:

  ```python
  assert _HANDOFF in live_probes  # ...MAY be probed for existence
  ```

- The `tests/heading-coverage.json` co-edit is specified in full, and **both**
  `reason` strings contain "integration-tier", satisfying
  `check-heading-coverage` direction 4 for a `TODO` entry on a `scenarios.md`
  heading.
- **Work-item `overseer-pfpfty.7` exists and matches.** `bd show
  overseer-pfpfty.7` returns "pfpfty P7: re-point the supervision-probe
  integration test to the no-probe scenario", whose description names the same
  test, the same line 282, the same assertion, and both `TODO` replacements. It
  `DEPENDS ON overseer-pfpfty.2` (the ratification valve). The citation is not
  decorative.
- **Post-ratification heading coverage verified by simulation.** Applying the
  rename and the addition to the manifest and to `scenarios.md` yields **zero**
  unmapped headings and **zero** orphaned entries. *Positive control on the
  reader:* the same checker scanned 89 `## ` headings across the four live files
  against 95 manifest entries and reported 0 unmapped at `ca7068b8` — i.e. it
  demonstrably reads both sides and can distinguish mapped from unmapped, since
  a deliberately-absent heading in the post-ratification arm would have appeared
  in the `unmapped` list that the rename exercise populates and empties.

### Round-1 blocker 3 — CLEARED

Round 1 required the descriptive target be quoted verbatim, four obligations
preserved, and two drift survivors amended. All six re-derived:

1. **Verbatim quoting.** EDIT 5's third target is now a contiguous two-paragraph
   block quotation (proposal lines 262-288). It matches live `spec.md`
   **verbatim and exactly once** — and because it matched as one contiguous
   normalized string, the two paragraphs are confirmed adjacent in the live file
   with nothing between them.
2. **`.ai/supervisor-protocol.md` permission preserved** — "MAY create exactly
   ONE named artifact in a watched repository — the shared role layer
   `.ai/supervisor-protocol.md`".
3. **Two-layer halt-with-remedy guard preserved** — "it MUST be read together
   with the shared layer, and it MUST emit a guard that HALTS with a labelled
   REMEDY if that layer is absent."
4. **Reviewed-commit-discipline sentence preserved** — "worktree, then pull
   request, then review, then merge — never directly to a primary checkout",
   correctly re-scoped to the one remaining file artifact.
5. **"Not a packaged plugin asset" preserved** — "Neither layer is a packaged
   plugin asset".
6. **Both drift survivors amended** — `spec.md` §"Supervised runtimes"
   cross-reference ("the **authoring permissions** are in…", proposal lines
   251-257) and the `scenarios.md` role-layer scenario `Given` (proposal lines
   456-460). `constraints.md` is aligned to "exactly ONE reviewed artifact".

*Positive control for the sweep:* the post-application text still contains
`supervisor-handoff.md` twice — both inside the NEW prohibition clauses — so the
sweep demonstrably finds that token where it survives, and its absence elsewhere
is a real absence.

**Bonus, unclaimed by the proposal:** removing the probe resolves a pre-existing
tension. Live `constraints.md:43-44` already said "The daemon NEVER reads,
writes, or hashes files under a repository's plan tree" with no probe carve-out,
while `spec.md` carved one out. The amendment removes the carve-out, so the two
files agree afterwards.

### Round-1 blocker 4 — CLEARED IN SUBSTANCE

The false "legacy input only" characterization is gone; retirement is scoped to
`handoff` alone; `resume` is explicitly preserved as the operator override; and
`spec.md`'s closed persisted-facts enumeration is amended in the same payload
and names the `epic` locator. That is exactly what round 1 asked for.

**But the replacement that does it introduces Blockers 3 and 4.** See below.

### Round-1 blocker 5 — CLEARED

All four EDIT 4 replacements say **plan**, not "Planning Lane":

| replacement | says |
|---|---|
| "Whoever archives a **plan** MUST leave NOTHING at its live path" | plan |
| "When a **plan** would close with anything unresolved" | plan |
| "TRANSFERRED to a different or new NON-ARCHIVED **plan** and/or work-item" | plan |
| "a **plan** worker, wrapped up, nudged, or respawned into ledger-held plan state" | plan |

Post-application sweep: **zero** `plan[ -]thread` occurrences remain in any of
the four files. *Positive control:* the same regex over the same four files
pre-application returns exactly four hits, all in `spec.md`, and the `\bhandoff\b`
regex run through the identical code path returns 13 post-application hits — so
the sweep reaches every file and can report non-zero.

### Round-1 blocker 6 — CLEARED

Routing is now stated in **both** replacements, which is what round 1 required:

- `spec.md`: "The binder's handoff entries MUST be appended THROUGH the
  orchestrator's sanctioned plan surface, never by a direct write to the plan
  epic's ledger…"
- `constraints.md`: "…THROUGH the orchestrator's sanctioned plan surface — never
  by a direct write to that ledger…"

Sibling citation re-verified live at `origin/master`:
`livespec-orchestrator-beads-fabro` `SPECIFICATION/contracts.md:1046-1047`
§"The two seams" still reads "*plan ↔ ledger, via the sanctioned plan surface
only*". The claim has not rotted.

---

## Part B — new defects introduced BY the amendment

## BLOCKER 1 — the respawn gate depends on a field nothing populates, and the amendment forecloses the design record's own source for it

*Criterion 2 (design-record fidelity); brief check D.*

**Where.** Proposal EDIT 4 (lines 195-199) and EDIT 6 (lines 331-340, 369-378),
landing in `livespec-overseer` `SPECIFICATION/spec.md` §"Track discovery and the
mapping store" and `SPECIFICATION/contracts.md` §"The restart interlock" and
§"Durable stores".

**What the amendment ratifies.** Three clauses that only work together:

> A track with NO recorded epic id is not respawned at all: the `ready`
> declaration is PRESERVED and the track surfaced, exactly as for a respawn that
> failed, so a declaration is never spent on a prompt the fresh session cannot
> resolve.

> The `epic` value is the plan-state locator the read-first chain resolves
> against, and it is REQUIRED for any track whose session may be restarted.

> The epic id qualifies because re-deriving it would mean reading a file inside a
> plan directory, which the daemon never does.

**Fact 1 — nothing populates `epic`, in code.** Across the entire shipped tree,
`epic` appears in exactly four places:

```
.claude-plugin/overseer/_registry_core.py:111:    "epic",          # durable-key tuple
.claude-plugin/overseer/_registry_core.py:217:    epic: str | None = None   # dataclass field, default None
.claude-plugin/overseer/_registry_store.py:102:        epic=_opt_str(key="epic"),   # read back
.claude-plugin/overseer/_registry_store.py:126:        "epic": track.epic,          # written through
```

It is read and written through; it is never assigned a value. Both discovery
constructors omit it entirely — `_supervisor_discovery.py:88-94` and `:207-213`
build `registry.Track(topic=…, repo=…, tmux=…, handoff=…, resume=…)` with no
`epic=`, so the field takes its `None` default and `_track_to_row` serializes
`"epic": null`. *Positive control on that zero:* the same grep over the same
`_supervisor_discovery.py` returns 3 lines for `resume` and 4 for `handoff` — the
query reaches the file and reports hits for adjacent keys; `epic` is genuinely
absent from it.

**Fact 2 — nothing populates `epic`, in the live store.** Reading the operator's
live mapping store `~/.livespec-overseer.jsonl`:

```
rows: 23
rows with non-null epic: 0
rows with handoff key   : 23
rows with resume key    : 23
epic values: ['None']
```

*Positive control on the READER, not merely the query:* the same reader over the
same 23 row objects reports 23 for `handoff` and 23 for `resume`. And the `epic`
key is **present in every row** — its value set is exactly `{None}`. So this is
not "reader looking at a missing field": the field exists, is read, and is
uniformly null. A reader that could not see values would have reported 0 for
`handoff` too.

**Fact 3 — the design record puts the epic id in exactly the file the amendment
declares unreadable.** `livespec` core `SPECIFICATION/spec.md:375` (v197):

> The plan store MUST contain only write-once research inputs under
> `plan/<slug>/research/` and **exactly one write-once metadata anchor written
> at plan open. The anchor MUST name the epic id** and MUST NOT be updated to
> mirror children, statuses, handoffs, readiness, or archive state.

That anchor lives inside `plan/<slug>/`. EDIT 4's justification says re-deriving
the epic id "would mean reading a file inside a plan directory, which the daemon
never does" — which is true of the daemon and is a property worth protecting,
but it closes the only source the ratified design record establishes, and the
amendment names no replacement.

**Fact 4 — the filed implementation slice names that same foreclosed source.**
`bd show overseer-pfpfty.4` ("foreman/daemon read-first chain repoints to
ledger-held plans"), under this very epic:

> …so a plan's resume source is its epic's ledger entries (**epic id from the
> plan's write-once metadata anchor**)…

So the amended spec would forbid the mechanism its own sibling work-item is
scoped to build.

**Why it matters.** Ratifying this leaves the spec requiring, for every
restartable track, a value that (a) no shipped code sets, (b) no spec clause
assigns any actor responsibility for setting, and (c) the same spec forbids
deriving from the design record's designated source — and then makes the absence
of that value a hard refusal to respawn. Applied to live state today, all 23
tracks become un-respawnable. Round 1's blocker was "after this change no live
track's prompt resolves"; the amendment converts that into "after this change no
live track is respawned at all". The operator-visible outcome is the same one
round 1 flagged.

Note also that the proposal demonstrably knows how to defer work properly — it
carves out test source explicitly and cites `overseer-pfpfty.7`. It carves out
nothing here.

**Fair statement of the counter-argument.** A spec may legitimately lead its
implementation, and the refusal is fail-safe rather than dangerous (it preserves
the declaration and surfaces the track). There is also a partial route the
amendment does not use: live `constraints.md:47-49` already permits "an
authorized unattended foreman MAY read plan-tree, pane, and work-item text
solely as evidence" — the foreman is not the daemon, so a foreman could read the
anchor without violating the daemon's boundary. But the amendment does not say
this, and the respawn gate sits in the daemon's restart path.

**What would clear it.** Any one of three, and the third is cheapest:
(a) name the actor and moment that records `epic` (most naturally the foreman
reading the write-once anchor as evidence, which existing `constraints.md`
already permits, or `supervise-plan` recording it at plan open); or (b) drop the
"REQUIRED / not respawned at all" hard gate to a surfaced warning until a
population path exists; or (c) keep both clauses but cite a work-item for the
population path in the same way `overseer-pfpfty.7` is cited for test source,
and reconcile EDIT 4's "which the daemon never does" sentence with
`overseer-pfpfty.4`'s stated mechanism so the two do not contradict.

---

## BLOCKER 2 — "supervisor handoff entries" is an undefined category, so the supervisor respawn prompt fails the proposal's own resolvability rule

*Criteria 1 and 3; defect class 2 (negative/implicit assertions about
sibling-owned surfaces).*

**Where.** Proposal EDIT 5 (lines 223-237) and EDIT 6 (lines 331-340), landing
in `livespec-overseer` `SPECIFICATION/spec.md` §"Supervised runtimes" and
`SPECIFICATION/contracts.md` §"The restart interlock".

**What the amendment ratifies.** The worker and the supervisor are pointed at
the **same** epic, distinguished only by an adjective:

> handed exactly one prompt: read that entity's ledger-held plan state — the
> **handoff entries** on the governed plan's ledger epic for a worker, or the
> **supervisor handoff entries** on **that same epic** for a supervisor pair
> member — and follow it.

and the pair-identity paragraph preserves a separation obligation that depended
on the two being different files:

> its wrap-up and keep-going messages are entity VARIANTS whose paths, session
> name, and append ritual refer to the supervisor's own layer … and **never to
> the worker's own read-first state**

**Why it matters.** Under the retired scheme the separation was mechanical: two
different paths, `plan/<topic>/handoff.md` and
`plan/<topic>/supervisor-handoff.md`. Under the new scheme both classes live on
one epic, and **nothing anywhere says what makes an entry a supervisor handoff
entry.** The prompt is required to carry only the repository path and the epic
id. A cold-open supervisor session receives coordinates that resolve to a stream
containing both classes and no stated way to filter.

That is precisely the failure mode the amendment itself legislates against, four
lines earlier in the same contract clause:

> a prompt naming only a category is not a pointer.

Applied to itself, "the supervisor handoff entries" is a category.

**No design record supplies the missing discriminator.** *Positive control
stated with each zero:*

| repo / file (at `origin/master`) | lines matching `supervisor` | control: lines matching `handoff` |
|---|---|---|
| `livespec-orchestrator-beads-fabro` `SPECIFICATION/contracts.md` | **1** | 38 |
| `livespec` core `SPECIFICATION/spec.md` | **1** | 4 |

In both files the single `supervisor` hit is the substring inside
`supervisor-handoff.md` in a **prohibition** list, not a definition — core
`spec.md:375` and orchestrator `contracts.md:1004`. The controls return 38 and 4
respectively over the same files with the same grep shape, so the query reaches
and reports hits; the absence is real.

What those records *do* define is one undifferentiated class. Core
`spec.md:378`: "Handoff persistence MUST provide append-only, per-entry ledger
entries, each individually attributed and timestamped". Orchestrator
`contracts.md:1019-1022` says the same. There is no supervisor sub-class in
either.

This also engages defect class 2 directly: the overseer's spec would carry an
implicit assertion about a **sibling-owned** surface — that the plan epic's
entry stream distinguishes supervisor entries — which the sibling does not
define, which nothing in the sibling would notice going stale, and which is
stated with no anchor to repo, file, or version.

**Fair statement of the counter-argument.** The overseer legitimately owns the
supervisor-pair concept; no fleet contract needs to know about supervisors, and
the overseer is entitled to layer its own notion on the shared entry stream. The
defect is not that it invents the class — it is that it relies on the class for
prompt resolvability and pair separation while never defining it.

**What would clear it.** Define the discriminator in EDIT 3's definitional
passage, which already exists and is the natural home — e.g. that a supervisor
handoff entry is one attributed to the track's supervisor session (attribution
is already a guaranteed property of every entry per core `spec.md:378`), or that
it carries a stated marker. Then either state the filter in the supervisor
prompt clause, or say plainly that the supervisor reads the same stream and
attribution is the separator, and amend the "never to the worker's own
read-first state" sentence to match.

---

## BLOCKER 3 — EDIT 6's mapping-store replacement orphans the "a row without the key" clause, and the nearest reading contradicts the REQUIRED-epic rule in the same bullet

*Defect class 3 (clause lockstep) — reintroduced by the fix for round-1 blocker 4.*

**Where.** Proposal EDIT 6 (lines 361-378), landing in `livespec-overseer`
`SPECIFICATION/contracts.md` §"Durable stores".

**What the live bullet says now.** `contracts.md:262-269` — the em-dash clause
sits immediately after `ctx_threshold` and unambiguously modifies it:

> Durable keys: `topic`, `repo`, `tmux`, `handoff`, `resume`, `epic`,
> `pinned_session_id`, plus **`ctx_threshold` ONLY when a per-track override is
> set — a row without the key means "inherit the daemon default", and readers
> MUST NOT materialize the default at read time.** Unknown keys survive rewrites.

**What it says post-application.** The replace-target ends at "…override is
set". The replacement inserts roughly ninety words about `epic`, the `handoff`
retirement, and `resume` **between** `ctx_threshold` and the em-dash clause,
which is left in place. Post-application (from the simulation):

> …plus `ctx_threshold` ONLY when a per-track override is set. The `epic` value
> is the plan-state locator … and it is **REQUIRED for any track whose session
> may be restarted**. This revision RETIRES the `handoff` key … The `resume` key
> is NOT retired; it remains the operator's optional per-track override of the
> respawn prompt, and when it is absent the daemon derives that prompt from
> `repo` and **`epic` — a row without the key means "inherit the daemon
> default", and readers MUST NOT materialize the default at read time.**

**Why it matters.** "The key" now has three candidate referents and the
originally intended one is the most distant:

| reading | result |
|---|---|
| `ctx_threshold` (original intent) | correct, but now ~90 words and three sentences away |
| `resume` (subject of the immediately preceding clause) | true and consistent |
| `epic` (last-named token, immediately adjacent) | **directly contradicts "REQUIRED … not respawned at all" four sentences earlier** |

Adjacency favours the reading that creates the contradiction. And the clause is
not decorative: "readers MUST NOT materialize the default at read time" is a
live, implemented invariant — `_track_to_row` deliberately **omits**
`ctx_threshold` when it is `None`, with an in-code comment saying exactly that
(`_registry_store.py:129-133`). The amendment strips that rule of its anchor
while handing it to a key for which it is false.

This is the same clause-lockstep class as round-1 blocker 4, reintroduced by the
sentence that was rewritten to fix it — which is why it was invisible to a
verification method that checks only whether targets match.

**What would clear it.** Either place the new `epic`/`handoff`/`resume` prose
AFTER the `ctx_threshold` clause so the em-dash clause keeps its referent, or
extend the replace-target to swallow the em-dash clause and re-emit it with
`ctx_threshold` named explicitly ("a row without **`ctx_threshold`** means
'inherit the daemon default'").

---

## BLOCKER 4 — EDIT 6 lands proposal meta-commentary as ratified spec text

*Defect class 1 (claims that expire at ratification).*

**Where.** Proposal EDIT 6 (lines 372-374), landing in `livespec-overseer`
`SPECIFICATION/contracts.md` §"Durable stores".

**What would be ratified.**

> **This revision RETIRES** the `handoff` key — **a change, not a description of
> existing legacy**: it named a plan-tree artifact the Planning Lane contract has
> retired, so rewrites MUST NOT emit it, and a legacy row still carrying it is
> read without error and rewritten without it.

**Why it matters.** "This revision RETIRES…" is a statement about a *deliberation
event*, not a contract. One second after the accept, "this revision" has no
referent for a reader of `contracts.md`, and "a change, not a description of
existing legacy" is commentary addressed to a reviewer, not an invariant. This is
class 1 exactly: *"If a sentence would need editing the instant it lands, it does
not belong in the spec at all… a spec states contracts and invariants; it is not
a status report."*

It is also an unforced error created by the fix. Round 1 asked the author to
"state the retirement as a change with its rationale" — that instruction was
about the **proposal's** prose, and the proposal already discharges it correctly
in §"What round 1 changed" row 4. It was additionally routed into the spec text.

**There is no house-style precedent for it.** *Positive control stated beside the
zero:* across all four live spec files, `this revision|this proposal` matches on
**0** lines, while a bare `This ` matches on 22 / 16 / 1 / 6 lines in
`spec.md` / `contracts.md` / `constraints.md` / `scenarios.md` — so the grep
reaches every file and reports hits abundantly. This sentence would be the first
of its kind in the ratified spec.

The adjacent "The `resume` key is NOT retired" is the same class but milder — it
reads as a live clarification and I would not block on it alone; it is cleanest
recast positively ("`resume` remains the operator's optional per-track override…").

**What would clear it.** Delete the meta-sentence and keep only the contract it
wraps: "The mapping store MUST NOT emit a `handoff` key; a legacy row still
carrying it is read without error and rewritten without it." One sentence, same
force, no expiry. Blockers 3 and 4 are both inside this single replacement — one
rewrite clears both.

---

## Part C — checks that PASSED

Recorded so the maintainer can see the review was not one-sided.

**Criterion 1 — replacement-target fidelity: PASS, count re-derived not assumed.**
The brief's prior count of 24 was re-derived rather than trusted, and it holds
for this amended 522-line proposal: the proposal contains **41** block
quotations, of which **20** are replace-targets (structurally identified as a
quote block whose next non-blank line is exactly `with:`), plus **4** inline
`Replace "X" with "Y"` bullets in EDIT 4 = **24 targets**. All 24 match their live
target file **verbatim and exactly once**, after whitespace normalization:
9 in `spec.md` (block) + 4 inline in `spec.md`, 4 in `contracts.md`, 1 in
`constraints.md`, 6 in `scenarios.md`.

*Positive control on the READER, and how I know it provably changed what it
claims to:* each target was additionally probed in mutated form, built by
replacing its first alphabetic run of three or more characters with a token
absent from every file. The harness asserted `mutated != original` for each — so
the mutation is proven to be a real change and not a silent no-op — and every
mutated arm returned zero hits while its unmutated arm returned exactly one.
Two further reader anchors: a known-present string (`The overseer's DAEMON`)
returned UNIQUE, and a known-absent string returned MISS. This is the specific
trap the brief flagged: a control whose mutation does nothing reports a hit in
both arms and proves nothing. Here both arms differ for all 24.

**Cross-method confirmation.** The in-memory simulation independently re-applied
all 24 replacements sequentially and reported **24/24 applied, 0 unapplied** —
a different instrument (in-place substitution with uniqueness required at apply
time) agreeing with the counting instrument.

**Criterion 4 — ratification mechanics: PASS.**
- Front-matter `topic: planning-lane-realization` equals the file stem
  `planning-lane-realization.md`.
- The proposal carries exactly **one** `## ` heading (line 7); its seven other
  sections are `### `. *Control:* the same grep counts 7 `### ` headings.
- Exactly **two** `## ` heading changes are made (one rename in `scenarios.md`,
  one addition), and exactly **two** `tests/heading-coverage.json` co-edits are
  specified — re-derived by enumeration, not taken from the proposal's "exactly
  two changes" claim.
- Both `TODO` entries' `reason` strings contain "integration-tier", satisfying
  `check-heading-coverage` direction 4.
- Post-ratification heading coverage simulated: 0 unmapped, 0 orphaned.
- The `SPECIFICATION/proposed_changes/` queue holds only `README.md` and this
  proposal, so there is no sibling proposal to reconcile against.

**No `[R1-n]` marker leaks into ratified text.** The sixteen `[R1-n]` annotations
appear only in the proposal's own connective prose. *Positive control:* grepping
`R1-` over quote-block lines returns **0**; over non-quote lines it returns
**16** — the same grep finds them abundantly where they legitimately live.

**Design-record direction: PASS.** Retiring the plan-tree binder as a read target
matches `livespec` core `spec.md:375` ("The plan store MUST NOT contain
`supervisor-handoff.md`…") and orchestrator `contracts.md:1017-1028`. The
narrowing of the retirement to the binder alone (blocker 3's fix) is what the
record actually supports.

**Forward references survive.** EDIT 5's replacement says the "exactly two
places" sentence and the startup gitignore refusal "continue to bind"; both
referents survive outside every replaced range, and the sibling lane's additions
did not disturb them.

**Drift sweep, run as a post-application sweep rather than a read of the edit
map.** After simulating all 24 replacements:

| token | spec.md | contracts.md | constraints.md | scenarios.md |
|---|---|---|---|---|
| `handoff.md` (worker path) | 0 | 0 | 0 | 0 |
| `plan thread` / `plan-thread` | 0 | 0 | 0 | 0 |
| `supervisor-handoff.md` | 1 | 0 | 1 | 0 |

Both surviving `supervisor-handoff.md` hits are inside the NEW prohibition
clauses ("never by creating or updating `plan/<topic>/supervisor-handoff.md`
through the pull request path") — intended, not drift. Every surviving
`\bhandoff\b` occurrence was inspected in context and accounted for; the only one
not introduced by this proposal is `contracts.md`'s "no handoff hash, no
payload", which uses "handoff" in the **state-file** sense and is correctly left
alone (round 1 non-blocking observation 3, still correct). `constraints.md`'s
"Separately, an authorized unattended foreman MAY read plan-tree, pane, and
work-item text solely as evidence" survives EDIT 7 intact and does not conflict.

---

## T3 check — did another lane land, and did it reopen anything?

The brief required this, because correction **T3** on this plan is exactly a
previously-cleared blocker reopening with no one touching the proposal.

**It happened, and one claim did rot.**

| SHA | `spec.md` md5 | `plan thread` lines |
|---|---|---|
| `134fdca` (round-1 review SHA) | `9aa1234c0d9f74fe2fb0c7861b07046d` | 369, 397, 400, 439 |
| `17a0e442` (amendment merge, PR #802) | `9aa1234c0d9f74fe2fb0c7861b07046d` | 369, 397, 400, 439 |
| `ca7068b8` (current `origin/master`) | `c390135853629ca73d22904bb3d1843b` | **384, 412, 415, 454** |

Between `17a0e442` and `ca7068b8`, a sibling lane ratified `v011`
("restarted-never-worked-attention"), adding +15 lines to `spec.md`, +26 to
`scenarios.md`, +8 to `contracts.md`, plus a `history/v011/` snapshot.

**What survived.** All 24 replacement targets still match verbatim and uniquely
at `ca7068b8` — I ran the harness against the CURRENT tip, not the amendment
merge, so target fidelity is confirmed post-landing. I read the sibling lane's
additions in full: they concern a restarted session that never begins work, and
they refer to "the track's **expected resume text**" abstractly without naming
any handoff path, so they are medium-agnostic and do not contradict the change.
Heading coverage at `ca7068b8` is complete (0 unmapped), so the sibling lane
carried its own co-edit and ratification will not fail for an unrelated reason.

**What rotted.** The proposal's Summary (line 58) still says the four
term-bearing lines are "re-enumerated in this tree as lines 369, 397, 400, and
439". Those numbers were correct at round 1 and correct at the amendment merge;
they are now wrong by 15 lines. Round 1 predicted this as non-blocking
observation 2 and it has now materialized.

**This is NOT a blocker.** The actual replace-targets are quoted verbatim and
verified unique, so ratification cannot mis-apply; the numbers are decorative.
The right fix is to **delete them** rather than re-derive them — the same
delete-the-magnitude move defect class 4 prescribes, since a re-derived number
will simply rot again on the next landing.

---

## Non-blocking observations

Recorded for the author; none should cost a round.

1. **Delete the line numbers** (proposal line 58), per the T3 check above. "the
   four current `spec.md` prose lines that still use old plan-thread vocabulary"
   is fully sufficient and cannot rot.
2. **"the orchestrator's sanctioned plan surface" is unanchored.** It is a
   positive dependency reference rather than a negative claim, which is the right
   shape — but it names no repo, file, or version, so a reader of the overseer
   spec cannot resolve which surface. Consider citing
   `livespec-orchestrator-beads-fabro` `SPECIFICATION/contracts.md` §"The two
   seams", the way the design record's own clauses carry citations.
3. **`bd show <epic>`'s CHILDREN listing is incomplete** — for `overseer-pfpfty`
   it displays only `.6` and `.7`, while `.1` through `.5` all exist and return
   full records on direct `bd show`. I only learned the implementation slices
   existed by probing each id individually. Anyone judging this epic's coverage
   from the CHILDREN block alone would conclude the daemon work was never filed.
   Worth a line in `.ai/beads-gaps-workarounds.md`.
4. **`overseer-pfpfty.4`'s stated mechanism needs updating alongside Blocker 1's
   fix**, whichever way that fix goes — its "epic id from the plan's write-once
   metadata anchor" and the amended spec's "which the daemon never does" cannot
   both stand as written.

---

## Summary table

| # | Class | Finding | Severity |
|---|---|---|---|
| 1 | Criterion 2 / brief D | `epic` is a hard respawn precondition that nothing populates (23/23 live rows null; 0 assigning code paths), and EDIT 4 forecloses the design record's own source for it (core `spec.md:375` anchor), which `overseer-pfpfty.4` names as the intended mechanism | **BLOCKER** |
| 2 | Criteria 1, 3 / class 2 | "supervisor handoff entries" on the shared epic is never defined; no fleet record defines the class; the supervisor prompt fails the proposal's own "a category is not a pointer" rule | **BLOCKER** |
| 3 | Class 3 | EDIT 6 orphans the `ctx_threshold` "a row without the key" clause; the nearest-referent reading contradicts "epic … REQUIRED" in the same bullet | **BLOCKER** |
| 4 | Class 1 | "This revision RETIRES the `handoff` key — a change, not a description of existing legacy" ratifies proposal meta-commentary as spec text; zero precedent in the live spec | **BLOCKER** |
| R1-1 | — | Partially cleared — definition + worker locator + refusal landed; see Blockers 1, 2 | PARTIAL |
| R1-2 | — | Cleared; `overseer-pfpfty.7` verified to exist and match; post-ratification coverage simulated clean | PASS |
| R1-3 | — | Cleared; target quoted verbatim, all four obligations preserved, both drift survivors amended | PASS |
| R1-4 | — | Cleared in substance; but its replacement carries Blockers 3 and 4 | PASS w/ new defects |
| R1-5 | — | Cleared; all four say **plan**; 0 `plan[ -]thread` post-application | PASS |
| R1-6 | — | Cleared; routing in both replacements; sibling citation re-verified live | PASS |
| — | Criterion 1 | 24/24 replace-targets verbatim and unique, count re-derived, mutation controls proven non-no-op | PASS |
| — | Criterion 4 | topic/stem match; 1 `## ` heading; 2 heading changes ↔ 2 co-edits; integration-tier reasons present | PASS |
| — | T3 | Master moved after the amendment; targets survived; the line-number claim rotted (non-blocking) | NOTED |

---

## VERDICT

**4 BLOCKERS**

1. The respawn gate depends on a mapping-store `epic` value that nothing
   populates — all 23 live rows carry `epic: null` (control: 23/23 carry
   `handoff` and `resume`), and the only four `epic` mentions in the overseer
   Python tree read and write it through without ever assigning it — while EDIT 4
   forecloses the design record's own source for that id (`livespec` core
   `spec.md:375`'s write-once metadata anchor), which is exactly the mechanism
   the filed slice `overseer-pfpfty.4` names. Ratified as written, no live track
   is respawnable and the spec forbids its own implementation plan.
2. "Supervisor handoff entries on that same epic" is an undefined category. The
   worker and supervisor are pointed at one epic with no stated discriminator,
   and neither `livespec` core `spec.md` nor `livespec-orchestrator-beads-fabro`
   `contracts.md` defines such a class (1 matching line each, both inside the
   `supervisor-handoff.md` prohibition string; controls: 4 and 38 `handoff` lines
   respectively). The amended contract's own rule — "a prompt naming only a
   category is not a pointer" — condemns it.
3. EDIT 6's mapping-store replacement inserts ~90 words between `ctx_threshold`
   and the "a row without the key means 'inherit the daemon default'" clause,
   orphaning its referent; the nearest-referent reading attaches it to `epic` and
   directly contradicts "REQUIRED … not respawned at all" four sentences earlier,
   while stripping a live implemented invariant (`_registry_store.py:129-133`) of
   its anchor.
4. EDIT 6 ratifies "This revision RETIRES the `handoff` key — a change, not a
   description of existing legacy" into `contracts.md` — a status report about a
   deliberation event, with no referent one second after the accept, and with
   zero precedent in the live spec (0 matching lines across all four files;
   control: 22/16/1/6 lines match a bare "This ").

Blockers 3 and 4 are both inside EDIT 6's durable-keys replacement; one rewrite
clears both.

**Reviewed by Opus 5 (`claude-opus-5[1m]`) on 2026-08-12, under the maintainer's
deliberate SECOND one-off authorization to deviate from the Fable-model
requirement — a repeat of the round-1 deviation, not a closure of it. Any
ratification record for this proposal MUST read `reviewer_model: opus`, never
`fable`.**

**Pinned at `livespec-overseer` `origin/master` =
`ca7068b8b002e7f1930deefa6fd079d0917a21e9`, re-checked unmoved at review end.**
