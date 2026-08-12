# Adversarial review — round 1

**Proposal under review:** `SPECIFICATION/proposed_changes/planning-lane-realization.md`
in repository **`livespec-overseer`**
(<https://github.com/thewoolleyman/livespec-overseer/blob/master/SPECIFICATION/proposed_changes/planning-lane-realization.md>).

**Read from committed state** — every quotation below comes from
`git show origin/master:<path>`, never the working tree. The
`livespec-overseer` primary checkout was clean on `master` at
`134fdca` when this review ran.

**Review is READ-ONLY.** Nothing was filed, edited, ratified, or pushed. No
worktree was created. No ledger was touched.

---

## MODEL DEVIATION — read this before the findings

`AGENTS.md` §"Independent Fable review before every ratification" requires this
review to be performed by a **Fable-model** agent. It was not.

| | |
|---|---|
| **Model that actually performed this review** | **Opus 5** (`claude-opus-5[1m]`) |
| **Required model** | Fable 5 (`claude-fable-5`) |
| **Authorization** | The maintainer authorized proceeding on Opus as a deliberate ONE-OFF for this review only, on **2026-08-12**. It is not a rule change. |
| **Review performed at** | 2026-08-12T01:09Z |

**Consequence for whoever ratifies.** The eventual ratification record MUST
record `reviewer_model: opus`. Writing `fable` there would be a **false
attestation** — the exact defect correction T1 on this plan was written about,
where a conforming-looking review record was minted and the CLI accepted it
because it validates field *shape* rather than whether a review occurred. The
CLI cannot catch this; only the person filling the field can.

Independence itself is intact: this review did not author the proposal (a Fabro
sandbox did, `author: claude-fable-5`), so only the model attestation deviates,
not the independence of the review.

---

## Bottom line, in plain language

**The proposal is directionally right and should not be ratified as written.**

It correctly identifies that `livespec-overseer`'s spec still tells sessions to
resume from `plan/<topic>/handoff.md` and `plan/<topic>/supervisor-handoff.md`,
which the ratified fleet contract retired. Its replacement-target quoting is
excellent — all nineteen quoted targets exist verbatim and uniquely, which is
rare and worth saying.

But it swaps a **concrete pointer** for an **undefined noun**. The word "ledger"
appears **zero times** in `livespec-overseer`'s current specification. The
proposal makes "ledger-held plan state" the sole thing a restarted session is
told to read, in four files, without ever defining it, without giving the
restart prompt a way to name *which* ledger or *which* epic, and without a
single scenario establishing how a cold-open session resolves it. Today's prompt
at least names a real path. After this change it names a category. That is the
brief's hard check, and it fails.

It also carries three changes its own Summary never discloses: it revokes
`supervise-plan`'s permission to author `.ai/supervisor-protocol.md`, it retires
the mapping store's `resume` key (which is the actual respawn prompt, emitted on
every rewrite, not "legacy input"), and it rewrites a scenario into the exact
shape the integration test bound to that scenario was deliberately built to
reject.

**Six blockers below.** Each names the file, the live bytes, and why it matters.
Blockers 1, 2 and 3 are the substantive ones; 4, 5 and 6 are smaller but each
leaves a ratified contradiction in the tree.

### Notation used below

- **"live"** = the bytes at `git show origin/master:<path>` in the named repo.
- **Line numbers** for the four spec files are line numbers in the *current*
  (pre-change) file. Line numbers for the proposal are lines of the proposal file.
- **"positive control"** = a second query, stated beside every zero/negative
  result, proving the same query is capable of reporting a hit. No zero is
  reported here without one.

---

## What passed

Recorded so the maintainer can see the review was not one-sided.

**Criterion 1 — replacement-target fidelity: PASS.** All nineteen replace-targets
(fifteen block quotations plus the four inline replacements in EDIT 4) were
mechanically checked against the live files after normalizing line-wrapping.
Every one matches **verbatim and exactly once** — no near-matches, no ambiguous
multi-hits. Method: extract each `>` block from the proposal, collapse whitespace,
assert substring containment and `count == 1` against the same-normalized live
file. Positive control: the same harness reports `MISS` with a longest-prefix
diagnostic when fed a deliberately altered target.

**Criterion 4 — ratification mechanics: PASS on the mechanics as stated.**
Front-matter `topic: planning-lane-realization` matches the file stem
`planning-lane-realization.md`. The proposal carries exactly one `## ` section
(line 7). No `## ` heading in any of the four target files is added, removed, or
renamed by any of the seven edits, so the proposal's closing claim that no
`tests/heading-coverage.json` co-edit is owed is **mechanically true**. See
Blocker 2 for why that true statement is the problem rather than the reassurance
it reads as.

**Clause-lockstep re-derivation: PASS.** The proposal's count claim — "the four
current `spec.md` prose lines that still use old plan-thread vocabulary
(re-enumerated in this tree as lines 369, 397, 400, and 439)" — was re-derived,
not trusted. `grep -rniE 'plan[ -]thread'` across all four live spec files returns
**exactly four hits, at exactly 369, 397, 400, 439, all in `spec.md`**. Positive
control: the same grep relaxed to `plan` returns 37/4/5/10 hits across
spec/contracts/constraints/scenarios, so the query reaches all four files. The
enumeration is accurate. (The *replacement wording* is not — Blocker 5.)

**Forward references survive.** The EDIT 5 replacement text says the
"exactly two places" sentence below and the startup gitignore refusal "continue
to bind." Both referents survive the edit: `spec.md:556` and `spec.md:558`,
outside every replaced range.

**Direction matches the design record.** livespec core
`SPECIFICATION/spec.md:375` (v197) states the plan store "MUST NOT contain
`supervisor-handoff.md`, mutable status files, or any other mutable
planning-state document," and that a plan created after ratification "MUST NOT
create a live `handoff.md`." Retiring both as read targets is correct. The
`livespec-orchestrator-beads-fabro` realization agrees at
`SPECIFICATION/contracts.md:1017-1028` §"Ledger-held handoff persistence."

---

## BLOCKER 1 — the restart prompt becomes unresolvable, and "ledger" is never defined

*Criteria 1 and 3; the brief's second hard check.*

**Where.** Proposal EDIT 2 (lines 82-88) and EDIT 6 (lines 186-198), landing in
`livespec-overseer` `SPECIFICATION/spec.md:237` §"The restart" and
`SPECIFICATION/contracts.md:149-152` §"The restart interlock".

**What the proposal says.** The single prompt handed to a respawned session
becomes:

> read your track's ledger-held plan state and follow it.

and the contract guarantee becomes:

> handed exactly one prompt: read that entity's ledger-held plan state — the
> governed plan's epic ledger for a worker, or the supervisor handoff entries on
> that same epic for a supervisor pair member — and follow it.

**What the live bytes say.** `contracts.md:149-152` currently reads:

> handed exactly one prompt: read that entity's resume artifact —
> `<repo>/plan/<topic>/handoff.md` for a worker,
> `<repo>/plan/<topic>/supervisor-handoff.md` for a supervisor pair member —
> and follow it.

and the shipped builder at
`.claude-plugin/overseer/_supervisor_prompts.py:190-192` substitutes a real
absolute path:

```python
def default_resume(*, repo: str, topic: str) -> str:
    """The first prompt pasted into a (re)started session: read the handoff."""
    return f"read {default_handoff(repo=repo, topic=topic)} and follow it"
```

**Why it matters.** The word **"ledger" appears zero times** in
`livespec-overseer`'s four live spec files. *Positive control for that zero:* the
same grep over the same four files returns hits for `work-item`
(`spec.md:400`, `spec.md:549`, `constraints.md:48`, `scenarios.md:542`) and for
`orchestrator` (`spec.md:34`, `spec.md:58`, `scenarios.md:608`) — the query
reaches these files and finds adjacent domain terms; "ledger" is genuinely absent.

So the proposal introduces a load-bearing new noun — "ledger-held plan state",
"the governed plan's epic ledger", "supervisor handoff ledger entries" — across
all four files, defines it nowhere, adds no `## ` section for it, and adds no
scenario establishing how it is resolved.

Concretely, a cold-open respawn under the proposed contract receives the sentence
"read your track's ledger-held plan state and follow it" and has:

- no epic id (the daemon holds one — the `epic` mapping-store key — but neither
  the spec.md restart paragraph nor the contracts.md restart guarantee requires
  the prompt to *carry* it);
- no repository coordinates in the prompt text;
- no named command, CLI, or read path.

The old text failed by pointing at a file that might not exist. The new text
fails earlier: the session cannot form the query at all. That is a regression
against the exact defect this track exists to remove, and the brief names it a
blocker condition.

This is not hypothetical for edge cases only. **All six live (unarchived) plans in
`livespec-overseer` currently have a `handoff.md` at the git tip** —
`adoptable-launch-discipline`, `charter-gate-ratchet`, `foreman`,
`resume-submit-integrity`, `supervisor-scratch-discipline`,
`winddown-rationale-expiry`. *Positive control:* the same `git cat-file -e` probe
reports `ABSENT` for `plan/definitely-not-a-plan/handoff.md`, so the check can
distinguish the two states. Meaning: today every live track's respawn prompt
resolves; after this change none of them do.

**What would clear it.** Either (a) the contract must require the restart prompt
to carry a concrete, resolvable locator (the epic id and the repo, or a named
read command), so the pasted sentence is self-sufficient for a session with no
context; or (b) the proposal must add a defining passage — and at least one
scenario — establishing what "ledger-held plan state" is and how a cold-open
session resolves it. Preferably both.

---

## BLOCKER 2 — a scenario is rewritten to contradict the integration test bound to it

*Criteria 3 and 4.*

**Where.** Proposal EDIT 7 (lines 264-281), landing in `livespec-overseer`
`SPECIFICATION/scenarios.md:390-400`.

**What the proposal does.** It replaces the scenario body with:

> Then it performs no file-level probe inside the plan directory
>
> And it never opens, reads, or hashes plan-tree handoff files as authorization
>
> And it points the session at ledger-held plan state instead

explicitly "without renaming its `## ` heading."

**What the live bytes say.** `scenarios.md:390-400`:

```
## Scenario: The supervision-artifact existence probe is liveness-gated and existence-only

Given a watched repository containing a plan directory whose track has a currently matching live session

When the daemon's discovery pass runs

Then it MAY test whether plan/<topic>/supervisor-handoff.md exists
...
```

**Why it matters — three compounding problems.**

1. **The heading now contradicts its own body.** The retained heading asserts
   that a probe exists and is liveness-gated and existence-only; the new body
   asserts no probe exists at all. A scenario cannot be its own negation.

2. **The `Given` line is left unamended and becomes meaningless.** "Given a
   watched repository containing a plan directory whose track has a currently
   matching live session" — the live-session condition was the *gate that made
   the probe legal*. With no probe, the precondition governs nothing. It sits in
   the replaced scenario's body and the proposal does not touch it.

3. **The bound test asserts the opposite, positively.**
   `tests/heading-coverage.json:383-385` maps this exact heading to
   `tests.integration.test_discovery_and_relay.test_scenario_the_supervision_probe_is_liveness_gated_and_existence_only`,
   and the mapping's own `reason` field explains the design:

   > The liveness gate is exercised by DIFFERENCE on the same repo and file — the
   > live-session pass **must probe it** and the dead-session pass must not.
   > Asserting only the absence would pass against a daemon that never probes at
   > all, a different bug wearing the same green tick.

   The test at `tests/integration/test_discovery_and_relay.py:282-284` carries
   that as a positive assertion:

   ```python
   assert _HANDOFF in live_probes  # ...MAY be probed for existence
   assert dead.status == "session-gone"  # no live matching session...
   assert _HANDOFF not in dead_probes  # ...means no file-level probe at all
   ```

   The proposal's rewritten scenario **is** the "daemon that never probes at all"
   case the test was deliberately constructed to reject.

**The mechanism that hid this.** The proposal's closing sentence — "No
target-file `## ` heading is added, removed, or renamed by these edits, so
ratification owes no `tests/heading-coverage.json` co-edit" — is *true*, and it
is true precisely *because* the heading was left in place. Not renaming the
heading is what avoided the co-edit, and avoiding the co-edit is what kept the
mapped test out of view. The co-edit rule is a tripwire for exactly this
coupling; this edit walks around it.

**What would clear it.** Rename the heading to state what the scenario now
asserts, co-edit `tests/heading-coverage.json` in the SAME payload (the new
`reason` must name the integration tier, or `check-heading-coverage` direction 4
fails), amend or delete the now-inert `Given` line, and either re-point or
retire `test_scenario_the_supervision_probe_is_liveness_gated_and_existence_only`
under a named work-item. The proposal currently names none of this.

---

## BLOCKER 3 — `.ai/supervisor-protocol.md` authoring permission is silently revoked

*Criteria 2, 3 and 5; the "claims that expire" and drift-sweep classes.*

**Where.** Proposal EDIT 5 (lines 167-184) and EDIT 7 (lines 232-243), landing in
`livespec-overseer` `SPECIFICATION/spec.md:534-546` §"Non-interference with
tracked work" and `SPECIFICATION/constraints.md:44-47` §"Filesystem boundaries".

**What the live bytes say.** `spec.md:534-546` currently grants a **two-artifact**
permission with a guard obligation:

> An ATTENDED Control-Plane operator skill (supervise-plan) MAY create exactly
> TWO named artifacts in a watched repository: the shared role layer
> `.ai/supervisor-protocol.md`, and the per-thread binder
> `plan/<topic>/supervisor-handoff.md`. The binder is intentionally thin and is
> NOT complete on its own; it MUST be read together with the shared layer, and
> it MUST emit a guard that HALTS with a labelled REMEDY if that layer is absent.
> Both MUST be written exclusively through that repository's own documented
> commit discipline — worktree, then pull request, then review, then merge —
> never directly to a primary checkout. Neither is a packaged plugin asset...

`constraints.md:44-47` mirrors it as the authoritative boundary:

> The attended Control-Plane authoring exception permits supervise-plan to create
> exactly two reviewed artifacts, `.ai/supervisor-protocol.md` and
> `plan/<topic>/supervisor-handoff.md`.

**What the proposal replaces them with.** Both become a ledger-append-only
permission. `.ai/supervisor-protocol.md` is not mentioned in either replacement.
Also dropped without replacement: the two-layer guard obligation (halt with a
labelled remedy when the shared layer is absent), the "worktree → PR → review →
merge" discipline sentence, and "Neither is a packaged plugin asset."

**Why it matters.**

1. **It is not in the design record.** livespec core `SPECIFICATION/spec.md:375`
   retires artifacts *in the plan store*: "The plan store MUST NOT contain
   `supervisor-handoff.md`, mutable status files, or any other mutable
   planning-state document." `.ai/supervisor-protocol.md` is **not in the plan
   store** — it is a repo-root role layer. Nothing in v197, v198, or
   `livespec-orchestrator-beads-fabro` v059 retires it. Criterion 2 says where
   prose and the record disagree, the record wins; here the prose goes beyond the
   record.

2. **The proposal contradicts itself.** Its Motivation (lines 41-46) asserts "The
   protected properties do not change," and its Summary (lines 18-24) scopes the
   change to the PR-authored `supervisor-handoff.md` path and `handoff.md`.
   Revoking the shared-layer permission is neither disclosed nor motivated.

3. **It contradicts the shipped skill.** `livespec-overseer`
   `.claude-plugin/prose/supervise-plan.md:170-186` instructs the operator to
   "create or update both emitted layers", names `.ai/supervisor-protocol.md`
   as "the single shared role-level layer", and emits a cold-open boot guard
   (lines 204-206) that HALTS when it is missing. After ratification the spec
   would no longer authorize the write the shipped skill performs.

4. **The drift sweep is incomplete — two statements are left contradicting the
   change.**
   - `scenarios.md:492-500` §"Scenario: A missing supervisor role layer halts the
     binder with a remedy" survives untouched, still reading "Given a
     supervise-plan-authored binder whose required shared role layer
     `.ai/supervisor-protocol.md` is absent". Both nouns in that line — the binder
     and the shared layer — are things the amended spec no longer authorizes
     anyone to create.
   - `spec.md:485-486` still says "A tracked session MAY have an attended
     SUPERVISOR session beside it (the **artifact permission** is in
     §"Non-interference with tracked work")." After EDIT 5 that section grants no
     artifact permission at all, only a ledger-append permission; the
     cross-reference's noun goes stale.

   *Positive control for this sweep:* `grep -rn 'supervisor-protocol'` over the
   four live spec files returns three hits (`spec.md:536`, `constraints.md:46`,
   `scenarios.md:494`), of which the proposal amends two and leaves one — so the
   query demonstrably finds hits, and the surviving one is a real omission, not
   an empty result.

**Procedural note attached to this blocker.** EDIT 5's third replacement is the
only one in the proposal with a **descriptive rather than quoted** target: "the
non-interference paragraph beginning 'The overseer's DAEMON' and **the attended
artifact paragraph**." The second half is named, not quoted — which is exactly
how a paragraph's worth of dropped obligations (the guard, the commit
discipline, the plugin-asset clause, the shared layer itself) passes unnoticed.
Quote it verbatim like the other eighteen targets.

**What would clear it.** Either preserve the `.ai/supervisor-protocol.md`
authorization, its guard obligation, and its reviewed-commit-discipline sentence
explicitly in both replacements — retiring only the plan-tree binder, which is
what the design record actually retires — or, if revoking it is intended, say so
in the Summary, cite the design record that authorizes the revocation, and amend
`scenarios.md:492-500` and `spec.md:485-486` in the same payload.

---

## BLOCKER 4 — EDIT 6d misdescribes live behavior and leaves `spec.md` contradicting it

*Criterion 3; the clause-lockstep class.*

**Where.** Proposal EDIT 6 (lines 219-230), landing in `livespec-overseer`
`SPECIFICATION/contracts.md:262-269` §"Durable stores".

**What the proposal says.**

> ...retired `handoff` and `resume` keys are legacy input only and MUST NOT be
> emitted by rewrites.

**What the live bytes say.** Both keys are unconditionally emitted on **every**
row rewrite — `.claude-plugin/overseer/_registry_store.py:119-128`:

```python
def _track_to_row(*, track: Track) -> dict[str, object]:
    row: dict[str, object] = {
        "topic": track.topic,
        "repo": track.repo,
        "tmux": track.tmux,
        "handoff": track.handoff,
        "resume": track.resume,
        "epic": track.epic,
        "pinned_session_id": track.pinned_session_id,
    }
```

and discovery actively *derives and writes* them —
`.claude-plugin/overseer/_supervisor_discovery.py:88-94` sets
`handoff=track.handoff or default_handoff(...)` and
`resume=default_resume(...)`. Further, `resume` is the **actual respawn prompt**:
`_supervisor_restart.py:226-229` and `:282-285` read
`track.resume or <default>` to decide what gets pasted.

**Why it matters.** Calling these "legacy input only" describes a state that does
not exist. `resume` is not a vestige — it is the operator's per-track override of
the respawn prompt, and it is the one mechanism that could supply the resolvable
locator Blocker 1 says the new prompt lacks. Retiring it is a substantive
behavior change that neither the Summary nor the Motivation discloses, and it is
presented as a description of existing legacy rather than as the change it is.

**And it leaves a direct contradiction.** `spec.md:360-363` — untouched by any of
the seven edits — still reads:

> The store persists ONLY facts that cannot be re-derived from the filesystem:
> the topic-to-session mapping, **a custom resume line**, a per-track threshold
> override, and a pinned session identity.

That is a closed four-member enumeration ("ONLY"). EDIT 6d removes one member and
promotes another (`epic`, which the sentence does not mention at all, becomes
"the plan-state locator for the read-first chain"). The enumeration is not
re-derived. This is the clause-lockstep class precisely.

**What would clear it.** Drop the false "legacy input only" characterization;
state the retirement as a change with its rationale; amend `spec.md:360-363` in
the same payload so the persisted-facts enumeration matches the new durable-key
set (and names the `epic` locator); and reconcile with Blocker 1 — if `resume` is
retired, the locator has to come from somewhere else, and the proposal must say
where.

---

## BLOCKER 5 — EDIT 4 uses the wrong ratified vocabulary

*Criterion 2.*

**Where.** Proposal EDIT 4 (lines 112-126), landing in `livespec-overseer`
`SPECIFICATION/spec.md` lines 369, 397, 400, 439.

**What the proposal does.** It replaces "plan thread" / "plan-thread" with
**"Planning Lane"**:

| live text | proposed replacement |
|---|---|
| "Whoever archives a **plan thread** MUST leave NOTHING at its live path" | "Whoever archives a **Planning Lane topic** …" |
| "When a **plan thread** would close with anything unresolved" | "When a **Planning Lane** would close with anything unresolved" |
| "TRANSFERRED to a different or new NON-ARCHIVED **plan thread** and/or work-item" | "… NON-ARCHIVED **Planning Lane** and/or work-item" |
| "a **plan-thread** worker, wrapped up, nudged, or respawned into a plan handoff" | "a **Planning Lane** worker, … respawned into ledger-held plan state" |

**What the design record says.** livespec core
`SPECIFICATION/spec.md:374` (ratified v197) draws the distinction explicitly:

> The **Planning Lane** is the Spec-Plane *convention* for durable, multi-session
> planning work… **A plan** is anchored by a ledger epic and has a write-once git
> store at `plan/<slug>/`.

and `spec.md:382`:

> **The vocabulary is `plan`.** New live prose MUST NOT say `plan thread`,
> `planning thread`, or `plan-thread` except when quoting old text as an exact
> replacement target.

The maintainer's standing ruling of 2026-08-04, recorded in
`livespec/.claude/CLAUDE.md`, says the same: "Call the planning artifact a
'plan'… always write 'plan'."

**Why it matters.** The Planning Lane is the *convention*; a **plan** is the
*artifact*. The proposal substitutes the name of the convention for the name of
the artifact in all four places, which changes what the sentences mean: one does
not archive a Planning Lane, close a Planning Lane, or transfer work to "a
different or new NON-ARCHIVED Planning Lane" — there is one Lane, and it never
closes. The correct replacements are "a plan", "a plan worker", and so on. The
proposal removes the banned term but installs the wrong one, and its Summary
(line 28) states the intent as "to Planning Lane terms," so this is deliberate
rather than a slip — which means it will not self-correct.

This also engages the fleet's **Terminology-guard** conformance concern
(livespec `SPECIFICATION/non-functional-requirements.md:233`: "a renamed term
does not silently survive in prose") in a sibling repo's ratified spec.

**What would clear it.** Use **plan** in all four replacements.

---

## BLOCKER 6 — the Control-Plane ledger-append permission omits the sanctioned-surface seam

*Criterion 5.*

**Where.** Proposal EDIT 5 (lines 180-184) and EDIT 7 (lines 241-243), landing in
`livespec-overseer` `SPECIFICATION/spec.md` §"Non-interference with tracked work"
and `SPECIFICATION/constraints.md:44-47` §"Filesystem boundaries".

**What the proposal grants.** spec.md gets:

> An ATTENDED Control-Plane operator skill (supervise-plan) MAY append supervisor
> handoff entries to the governed plan's epic ledger. It MUST do so through the
> repository's ratified Planning Lane ledger discipline…

and constraints.md gets:

> The attended Control-Plane authoring exception permits supervise-plan to append
> supervisor handoff entries to the governed plan's epic ledger; it MUST NOT
> create or update plan-tree handoff files through the pull request path.

**What the ratified sibling contracts say.**
`livespec-orchestrator-beads-fabro` `SPECIFICATION/contracts.md:1042-1053`
§"The two seams":

> The Planning Lane is Spec-Plane but touches the Orchestrator Plane at exactly
> two explicit seams… (1) *plan ↔ ledger, **via the sanctioned plan surface
> only*** — the plan surface appends and reads plan-epic ledger handoff entries…

and livespec core `SPECIFICATION/non-functional-requirements.md:202`:

> The console is the single human interface that INVOKES every plane's operations
> on the operator's behalf… When it issues a command it does so **through the
> owning plane's published surface**, the same one-directional seam discipline
> the Planning Lane's two seams codify, so the owning plane stays both the source
> of truth and the actor of record.

**Why it matters.** The overseer is the **Control Plane**, not the Spec Plane and
not the plan surface. The ratified seam routes plan-epic handoff appends through
the sanctioned `plan` surface; the console issues through the owning plane's
published surface rather than writing directly. The proposal grants
`supervise-plan` a direct append.

The spec.md wording — "through the repository's ratified Planning Lane ledger
discipline" — *might* be intended to carry the seam, but it reads naturally as a
*content* property (append-only, attributed, timestamped) rather than an *actor*
routing requirement. And the constraints.md replacement, which is the
authoritative filesystem-and-permission boundary for this repo, drops that phrase
entirely: as ratified it would permit a direct Control-Plane ledger write with no
routing requirement whatsoever.

**What would clear it.** State the routing explicitly in **both** replacements —
that `supervise-plan` appends **through the orchestrator's sanctioned plan
surface**, never by writing the plan epic's ledger directly — so the boundary
constraint cannot be read as a standing direct-write grant.

---

## Non-blocking observations

Recorded for the author; none of these alone should cost a round.

1. **"Ratification is deliberately out of scope for this slice"** (line 30) is
   confusing in a document whose entire purpose is to be ratified. It appears to
   mean "this slice does not change the ratification machinery," but as written a
   reader can take it as a claim about the proposal's own disposition.
2. **The line-number citations** (lines 369, 397, 400, 439 at line 27) expire the
   moment any earlier edit lands. They are correctly scoped by "re-enumerated in
   this tree as," and they verify correct right now, so this is a note rather than
   a defect — but a successor re-reading this proposal after a partial application
   should re-derive rather than trust them.
3. **`contracts.md:32`** ("Beyond the token, the file's contents are never
   inspected — no handoff hash, no payload") uses "handoff" in the state-file
   sense, not the plan-artifact sense. It is correctly left unamended; noted so a
   later sweep does not "fix" it.

---

## Summary table

| # | Criterion | Finding | Severity |
|---|---|---|---|
| 1 | 1, 3 + brief hard-check 2 | Restart prompt becomes an undefined category; "ledger" defined nowhere in this spec; cold-open respawn cannot resolve it | **BLOCKER** |
| 2 | 3, 4 | Probe scenario rewritten to the exact case its bound integration test asserts against; heading and `Given` left contradicting the body | **BLOCKER** |
| 3 | 2, 3, 5 | `.ai/supervisor-protocol.md` permission + two-layer guard silently revoked; `scenarios.md:492-500` and `spec.md:485-486` left contradicting | **BLOCKER** |
| 4 | 3 | `handoff`/`resume` misdescribed as "legacy input"; `resume` is the live respawn prompt; `spec.md:360-363` left contradicting | **BLOCKER** |
| 5 | 2 | "Planning Lane" (the convention) substituted for "plan" (the artifact) in four places, against the ratified vocabulary clause | **BLOCKER** |
| 6 | 5 | Direct Control-Plane ledger append granted without the sanctioned-plan-surface seam | **BLOCKER** |
| — | 1 | All 19 replace-targets verbatim and unique | PASS |
| — | 4 | Topic/stem match; heading-coverage claim mechanically true | PASS (see #2) |

---

## VERDICT

**6 BLOCKERS**

1. The restart prompt is replaced by an undefined noun. "Ledger" appears zero
   times in `livespec-overseer`'s live spec (positive control: `work-item` and
   `orchestrator` both return hits over the same files), yet "ledger-held plan
   state" becomes the sole thing a respawned session is told to read, with no
   definition, no locator in the prompt, and no scenario. All six live plans
   resolve today; none would after ratification.
2. `scenarios.md:390-400` is rewritten into the "daemon that never probes at all"
   case that `tests/integration/test_discovery_and_relay.py:282` asserts against
   positively, while the heading and `Given` line are retained and contradict the
   new body. The proposal's true "no heading-coverage co-edit owed" claim is what
   kept this coupling out of view.
3. `supervise-plan`'s permission to author `.ai/supervisor-protocol.md`, its
   two-layer halt-with-remedy guard, and its reviewed-commit-discipline sentence
   are dropped undisclosed and without design-record basis, leaving
   `scenarios.md:492-500` and `spec.md:485-486` contradicting the amended spec.
4. EDIT 6d calls `handoff`/`resume` "legacy input only" when
   `_registry_store.py:119-128` emits both on every rewrite and
   `_supervisor_restart.py:226` uses `resume` as the actual respawn prompt; and it
   leaves `spec.md:360-363`'s closed four-member enumeration contradicting it.
5. EDIT 4 replaces the banned "plan thread" with "Planning Lane" — the
   convention — where the ratified vocabulary (livespec `spec.md:374`, `:382`)
   and the maintainer's 2026-08-04 ruling require **plan**, the artifact.
6. Both replacements grant the Control Plane a direct plan-epic ledger append
   without routing it through the sanctioned plan surface required by
   `livespec-orchestrator-beads-fabro` `contracts.md:1042-1053` and livespec core
   `non-functional-requirements.md:202`; constraints.md's version drops even the
   discipline phrase.

**Reviewed by Opus 5 (`claude-opus-5[1m]`) on 2026-08-12, under the maintainer's
one-off authorization to deviate from the Fable-model requirement. Any
ratification record for this proposal MUST read `reviewer_model: opus`.**
