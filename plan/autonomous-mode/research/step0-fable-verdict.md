# Step-0 multi-model validation verdict — autonomous-mode MVP plans

**Reviewer:** independent Fable-model session `livespec-autonomous-mode`
(read-only; no edits, no commits, no ledger writes during the review).
**Date:** 2026-07-10. **Brief:** `tmp/fable-handoff.md` (repo
`thewoolleyman/livespec`, maintainer-provided, session-local).

Scope: the three plan documents landed 2026-07-10 —
[`livespec/plan/autonomous-mode/design.md`](https://github.com/thewoolleyman/livespec/blob/master/plan/autonomous-mode/design.md)
(overall),
[`livespec-console-beads-fabro/plan/autonomous-mode/design.md`](https://github.com/thewoolleyman/livespec-console-beads-fabro/blob/master/plan/autonomous-mode/design.md)
(console operator surface), and
[`livespec-orchestrator-beads-fabro/plan/autonomous-mode/design.md`](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro/blob/master/plan/autonomous-mode/design.md)
(orchestrator decision engine), each read together with its `handoff.md`.
Every factual claim was checked against the live spec trees, the
crate/script sources on `origin/master`, the three Beads tenants, and
master CI.

## Overall verdict: NO-BLOCKERS

### Per-plan
- **livespec (overall):** NO-BLOCKERS
- **console operator surface (`livespec-console-beads-fabro`):** NO-BLOCKERS
- **orchestrator engine (`livespec-orchestrator-beads-fabro`):** NO-BLOCKERS

Executing the steps in the plans' order, with the observations below folded
into the C1/O1 briefs, reaches the MVP goal and passes the I2 live
exercise. The dependency graph is consistent across all three documents
(Step 0 → C1 → C2 → C3 → I2; Step 0 → O1 → O2 → I2; O1/I1 → C3), contains
no circular or missing edge, and the parallelism claim holds: C2 depends
only on the orchestrator's already-shipped `drive` action surface
(verified shipped — orchestrator `SPECIFICATION/contracts.md` §"`drive`",
actions `approve:/accept:/reject:…:{rework,regroom}/set-admission:/set-acceptance:`,
wrapper `.claude-plugin/scripts/bin/drive.py`), so it genuinely runs
concurrently with O1→O2. Scope is honestly TUI-only (the GUI is deferred
everywhere it appears), and every plan names the repo disciplines
correctly (worktree → PR → merge, `mise exec -- git`, never
`--no-verify`, Red-Green-Replay for product code,
`tests/heading-coverage.json` co-edits, independent Fable review before
every ratification). All three plan commits are `docs(plan):` and master
CI was green on all three repos at review time.

### Blockers (most severe first)

**None.** The two candidates that came closest, and why they do not cross
the bar:

1. The orchestrator spec v032, as written, would let the autonomous
   collapse bypass the spec-change human gate (detail in observation 1) —
   but the *plan* does not permit this: the orchestrator plan's "Hard
   boundary" section forbids it and step O1 is explicitly scoped to verify
   the boundary and file a propose-change when the spec falls short, gated
   by independent Fable review, before O2 builds anything. A diligent O1
   execution catches and fixes this; no step is missing or mis-ordered.
2. The regroom/auto-groom hazard is structurally absent: a non-convergence
   bounce rests in the `backlog` state (orchestrator
   `SPECIFICATION/contracts.md` §"Dispatcher grooming behavior": "MUST
   bounce the item to `backlog` and SURFACE it (escalate-don't-drop),
   never infinite-retry"), which the engine's ready-queue drain and
   `pending-approval` collapse never touch, and drift acceptance lives in
   the Spec-Plane propose-change/revise path the engine never enters. The
   engine cannot auto-groom or auto-accept drift under any plan step.

### Non-blocking observations (fold these into the C1/O1 dispatch briefs)

1. **O1's propose-change is REQUIRED, not "likely."** The orchestrator
   plan says "if [the spec] is silent, that is the one likely
   propose-change." The spec is worse than silent: its truly-unresolvable
   definition (`spec.md` §"Terminology") is only a general three-pronged
   test (insufficient LLM confidence / unobtainable information / a policy
   marks it human-only) that never names drift-acceptance, spec-change
   slices, or regroom — and the collapse clause affirmatively
   auto-approves "even items whose stored `admission_policy` is `manual`"
   while the grooming-behavior section names `manual` admission as "the
   first-class realization of the prior `human-gated` **spec-change**
   marker." As written, an autonomous run would auto-admit a spec-change
   slice. A second internal tension: contracts' blanket "treat every
   item's effective `acceptance_policy` as `ai-only`" literally includes
   `human-only` items, while Scenario 36 escalates
   policy-marked-human-only decisions. O1's propose-change must (a) name
   the design-human-gated set, (b) define how the engine distinguishes
   design-gated `manual` (spec-change) from routine `manual`, and
   (c) reconcile the `human-only`-acceptance carve-out with the blanket
   collapse wording.

2. **The persistence-seam recommendation is incomplete.** The
   reconciliation is genuinely available — the orchestrator contract's
   arming surface is a persistent *permission* key
   (`livespec-orchestrator-beads-fabro.dispatcher.autonomous_mode` in the
   governed repo's `.livespec.jsonc`, default `false`) plus a required
   per-invocation `drive --mode autonomous` flag, with "MUST NOT persist
   beyond the current invocation" governing the armed mode, not the key.
   But the plans' recommended resolution ("console persists intent; the
   loop launcher passes the flag per run") never says what happens to the
   orchestrator's own config key, leaving **two** persistent booleans in
   the same `.livespec.jsonc` meaning nearly the same thing. Recommended
   O1 pin: the console's `factory.autonomous_mode_enable/disable_requested`
   maps to setting the orchestrator's own key (the single persistent
   permission), with the console's namespaced block either dropped or
   defined as derived. O1 must also **name the loop launcher** (the
   natural MVP answer is the console's existing factory-drain path
   extended to pass the mode) and pin which surface carries `--mode`: the
   spec attaches it to `drive` (a one-action executor), but the shipped
   mode-bearing entry point is the dispatcher `loop` subcommand
   (`dispatcher.py:2594`).

3. **Console C1 should expect a ratified revision, not "no change
   needed."** The recommended division-of-resolution reading (the
   orchestrator engine owns all gate resolution; the console enables +
   observes + reflects + surfaces the unresolvable) is compatible with the
   console spec's plane-delegation MUSTs, which dominate its blanket
   resolve-MUST for orchestrator-owned decisions. But Scenario 10's first
   Gherkin case has *the console* record an auto-decision command —
   unsatisfiable for orchestrator-owned gates under that reading, since
   the audit then lives in the orchestrator journal. C1 will most likely
   need a console propose-change re-scoping Scenario 10 (and the §"Full
   Autonomous Mode" resolve-MUST) to the delegation model. If instead a
   console-side resolver is kept, note the concrete hazard: an item
   resting between engine runs could be resolved by both layers
   (double-resolution race).

4. **Two confirmed vocabulary-drift instances are missing from C1's diff
   list.** (d) The console contract cites "the orchestrator's published
   `orchestrate run` action-id surface"; the orchestrator renamed that
   surface to **`drive`** — "orchestrate run" appears nowhere in its live
   contracts. (e) The console contract says "the lane vocabulary is owned
   by livespec core, referenced here" — livespec core's SPECIFICATION/
   defines no lane vocabulary at all; it is owned by
   `livespec-orchestrator-beads-fabro` (contracts §"Work-item state
   semantics"). Both are one-line C1 fixes. The enumerated three
   vocabularies otherwise verify cleanly: the seven lane names match
   exactly, `blocked:dependency` flows through the orchestrator-emitted
   `lane`/`lane_reason`, and the acceptance/reject enums match exactly.

5. **C1∥O1 both "resolve" the persistence seam with no coordination
   edge.** Both run concurrently after Step 0 and could ratify divergent
   resolutions. In practice both plans carry the same recommendation, but
   the driver should sequence C1's persistence-seam portion after O1's
   arming contract freezes (I1), or make it an explicit joint decision at
   a driver boundary.

6. **I2's gate line was internally inconsistent with §9.** The overall
   plan's step catalogue gated I2 on "C3 AND O2" alone, while §9 says to
   gate I2 on the cost ceiling and a failure-surfacing path being real.
   (Fixed in the same commit as this verdict.) Related: open bug
   `bd-ib-18r` (in the `livespec-orchestrator-beads-fabro` tenant) records
   that a run parked at an in-loop human gate today gets orphaned with
   **no ledger write-back** — so I2's "truly-unresolvable surfaces in-TUI"
   leg should either plant its unresolvable item at the ledger level
   (which O2's new escalation code serves) or triage `bd-ib-18r` first; an
   in-loop-park plant would not surface today.

7. **`pke3y3`'s regroom must split, not silently narrow.** Its stale
   "7 unimplemented commands" list predates spec v014/v016; the current
   contract's thirteen initial commands include four that neither C2 (the
   five `work_item.*` commands) nor C3 (the three autonomous-mode
   commands) covers: `factory.dispatch_item_requested`,
   `factory.pause_requested`, `factory.resume_requested`,
   `spec.doctor_requested` (snooze/acknowledge are killed;
   `grooming.regroom_requested` retired). The regroom should carve those
   four into their own tracked item rather than closing them out of
   existence.

8. **`mb64bv` rename target should be verified against the orchestrator's
   actual journal vocabulary.** "backlog-bounce" as a token appears
   nowhere in the orchestrator's spec or code; the journal field is
   `bounced_to_regroom` and the concept is "the `backlog` bounce
   disposition". The console-side rename is fine as console-local
   labeling, but the adapter must keep matching what the orchestrator
   journal actually emits.

9. Trivia: `pke3y3` is an epic, not a task; the overall handoff's
   shorthand "`pke3y3` (5 valve commands)" mischaracterizes it (the design
   docs describe it correctly); "Open Engine" is a nickname not matching
   `livespec-35s3zo`'s stored title (the id and closed status check out).

### Currency findings (brief claims that did not verify as stated)

1. **"Core declares three irreducible human touchpoints that survive even
   a fully autonomous orchestrator" — PARTIAL.** Only drift-acceptance
   carries that exact normative framing (`livespec/SPECIFICATION/spec.md`
   §"Contract + reference implementations architecture": "the irreducible
   human touchpoint that survives even a fully autonomous orchestrator.
   Orchestrators MAY file drift (the machine path); only humans accept
   it"). Spec-change human-gating is one bullet of the intake
   Definition-of-Ready and regroom is "the one human-in-the-loop step,"
   both inside `non-functional-requirements.md` guidance that core itself
   marks "explicitly NON-normative on core's contract." The
   three-touchpoint boundary is sound and maintainer-declared in the
   plans, but the plans' §4 and O1's eventual propose-change rationale
   should attribute it precisely — it is largely the plan's synthesis
   being *promoted into* the orchestrator's spec, not a consistency
   restoration with existing core law. Core's Control-Plane console
   guidance also says nothing about autonomous mode or LLM operator
   stand-ins (its "never owns" and "not a required dependency" clauses in
   fact support the delegation reading).
2. **Core owns neither the `attention_item` schema nor the lane
   vocabulary nor the acceptance enums in SPECIFICATION/.** The shared
   `attention_item` shape lives in core's *shipped runtime*
   (`livespec/.claude-plugin/scripts/_vendor/livespec_runtime/attention_item.py`);
   C1's seam-(c) diff target is that shipped schema, not a core spec
   section.
3. **"orchestrate run" is stale fleet-wide:** the published surface is
   now `drive` (see observation 4).
4. **Orchestrator `SPECIFICATION/proposed_changes/` holds a `.gitkeep`,
   not a README** — the substance (zero pending proposals) holds; same
   for the console (README only).
5. **Everything else verified TRUE**, including: console spec v016 /
   orchestrator v032 current with zero pending proposals; all named spec
   sections and Scenarios 9–12 / 33–37 present; console `CommandType` =
   only `FactoryDrainRequested` (`crates/console-domain/src/lib.rs:310-313`);
   zero `autonomous` hits in `crates/`; `TuiView`/`TuiOverlay`/
   `OperatorAction` exactly as claimed; the real
   `DispatcherFactoryDrainPort` wired in both serve and TUI paths
   (`crates/console-cli/src/main.rs:104`, `:130`) with `NotWired` as
   honest fallback; no `.livespec.jsonc`/Configuration code in any crate;
   orchestrator `--mode autonomous` a queue-scope switch only, valves
   mode-blind, cost gate fail-closed on unobservable-in-autonomous,
   reflection stage no-LLM, out-of-band reflector a pure post-verdict
   observer, no `dispatcher.autonomous_mode` key in code; ledger statuses
   exactly as claimed for `rt4`/`pke3y3`/`ipi`/`mb64bv` (its gate closed),
   the fully-closed impl-dispatch chain, `bd-ib-82a` (backlog, no slices,
   no deps, stale v025 pointer as flagged), open `bd-ib-18r`/`bd-ib-6vu`,
   core `livespec-nrdk`/`livespec-0jxs` backlog, and all
   composed-machinery items closed.
