# Spec-side autonomy — gate inventory and lever design

Grounded brainstorm for automating the remaining HUMAN gates in the
livespec lifecycle — the spec-side ones above all — so designated
repos/tasks can run the whole lifecycle unattended under the planned
livespec-overseer foreman (repo `livespec-overseer`, thread
`plan/foreman/`). Ledger anchor: epic `livespec-jvdvx4`.

Maintainer directive (2026-08-03): the two impl-side levers are
confirmed as what they are; brainstorm how to automate the rest of the
human gates, spec side first (revise, grooming, "any other human needs
in the whole process"), composing with the foreman plan. The maintainer
chose this repo (livespec core) as the plan home because the doctrine,
the prose, and the config namespace the design touches are core-owned;
the foreman thread stays a consumer and is cross-linked, never
duplicated.

## Baseline — what is already automated

`/data/projects/livespec/.livespec.jsonc` (the `dispatcher` block)
arms two of the orchestrator's "three policy settings"
(`livespec-orchestrator-beads-fabro` repo,
`SPECIFICATION/contracts.md` §"Dispatcher policy settings" →
§"The three policy settings"):

- `auto_approve_ready: true` — the Readiness Admit: items move
  `pending-approval → ready` with no human `approve:` valve.
- `acceptance_mode: "ai-only"` — Auto AI-only Acceptance: post-merge,
  a passing AI acceptance pass closes the item to `done` with no human
  `accept:` valve. The AI pass always still runs ("no release with
  zero verification" is structural: the pass sits outside every policy
  branch in `_dispatcher_completion.complete_and_accept`).
- `merge_on_review_cap` deliberately stays at its safe `false`
  default: a review that cannot converge within `review_fix_cap`
  rounds must reach a human, per the maintainer's design record quoted
  in that repo's contracts ("…or even worse if the review gate is
  automated, pushing it all to production").

The same two levers are armed in
`livespec-orchestrator-beads-fabro`'s own `.livespec.jsonc`;
`livespec-overseer` arms only `acceptance_mode` and deliberately keeps
admission manual.

The spec plane, by contrast, has ZERO autonomy levers. There is no
spec-side sibling of the `dispatcher.*` block, and by contract the
orchestrator's `drive` executor refuses spec-side action-ids outright:
"Spec lifecycle actions remain human handoffs outside this executor"
(`livespec-orchestrator-beads-fabro` `SPECIFICATION/contracts.md`,
the `drive` section; also that repo's `skills/drive/SKILL.md`). The
only spec-side `.livespec.jsonc` keys that exist today
(`pre_step_skip_static_checks`, `post_step_skip_doctor_llm_*`,
`post_step_skip_capture_impl_gaps`, `pre_step_skip_stale_branch_check`,
`next.prune_history_threshold`) gate CHECK phases, never dialogue.

## Gate inventory — three classes

### Class (a) — mechanical re-asks; no doctrine behind them

Automatable with prose/CLI changes only:

- `propose-change`'s intent and topic questions
  (`.claude-plugin/prose/propose-change.md` Steps 3–4) and
  `critique`'s "what do you want critiqued?" scoping question. Real
  questions only when a human initiates; when the caller is
  `capture-spec-drift`, a doctor finding disposition, or a foreman
  brief, the intent already exists upstream and the prose re-asks it.
- `propose-change`'s per-in-flight-branch relationship elicitation
  (align / modify-to-accommodate / explicitly supersede, Step 2.6;
  contract at `SPECIFICATION/spec.md` §"Baseline") — needs a policy
  default (e.g. default-align) plus escalation on genuine conflict.
- `revise`'s optional steering-intent prompt (already skippable —
  "leave blank").
- Spec PR merge: the impl side already uses
  `gh pr merge --rebase --auto` on green; spec-side PRs have no
  equivalent. Pure workflow parity; no contract blocks it
  (`SPECIFICATION/non-functional-requirements.md` §"Workflow
  discipline — spec-side changes" already FORBIDS per-step
  "should I commit?" gates).

### Class (b) — the deciding machinery is already AI; only the arming surface is missing

- **Revise per-proposal accept / modify / reject** — the single
  highest-leverage gate. The prose already carries an in-dialogue
  "delegate remaining proposals to the LLM" toggle
  (`.claude-plugin/prose/revise.md`, Step 5): once set it
  auto-accepts the LLM's decisions for ALL remaining proposals across
  all remaining files, whole-revise scope. But it is session-only and
  can only be flipped inside the dialogue by a human — there is no
  config key and no CLI flag that pre-arms it.
- **The independent adversarial ratification review** — the AGENTS.md
  rule (maintainer-declared 2026-07-04): every proposed change in any
  fleet repo gets an independent read-only adversarial review by a
  separately-spawned Fable-model agent BEFORE `/livespec:revise`
  accepts it; a NO-BLOCKERS verdict is a precondition; "any blocker
  routes to the maintainer with a recommended fix — it is never
  self-waived". This is ALREADY an AI reviewer by construction — only
  the spawn is manual, and only blockers reach the human. Codifying
  auto-spawn changes nothing doctrinally. `.ai/spec-proposal-review.md`
  adds the three latent defect classes (claims that expire at
  ratification; negative assertions about sibling-owned surfaces;
  clause lockstep) with named mechanical greps — same agent, extended
  checklist.
- **Standing precedent that an AI review can discharge a human leg**:
  the AGENTS.md acceptance-policy addendum (maintainer-declared
  2026-07-20) — for non-behavior-bearing deliverables, "the
  discharging evidence is an INDEPENDENT ADVERSARIAL REVIEW … That
  review MAY be performed by a separately-spawned agent, and it
  satisfies the `ai-then-human` acceptance policy's second leg. What
  never relaxes is 'no release with zero verification' — not the
  particular form the verification takes." This is the fleet's
  existing template for the whole design below.
- **Doctor per-finding dispositions** — every non-`pass` finding runs
  a five-verb menu (fix-now / capture-as-work-item / propose-change /
  defer / dismiss; `SPECIFICATION/contracts.md`, the doctor finding
  dialogue). A `check_id → default disposition` policy map (unmapped
  checks escalate) clears the dialogue; needs a modest contract
  amendment since the menu's content-and-availability is
  contract-mandated.
- **Orchestrator-side capture consent** (`capture-impl-gaps`,
  `capture-spec-drift` per-finding confirms) — an operation-class
  waiver exists but is invocation-scoped and "MUST NOT be a default"
  (`livespec-orchestrator-beads-fabro`
  `SPECIFICATION/contracts.md` §"Store-write consent discipline");
  promoting it to a config key is a propose-change in that repo.

### Class (c) — doctrine floors; a config key cannot touch them without a ratified amendment

1. **Drift acceptance.** `SPECIFICATION/spec.md` (this repo), the
   drift doctrine paragraph: "Drift's human gate is load-bearing
   doctrine. Only a human can rule 'the implementation is right, the
   spec is wrong' … the propose-change/revise gate IS the human
   adjudication mechanism, and it is the irreducible human touchpoint
   that survives even a fully autonomous orchestrator. Orchestrators
   MAY file drift (the machine path); only humans accept it." Fully
   automating revise for drift-origin proposals reverses this
   sentence — the biggest values call in the whole plan.
2. **The groom cut.** "The maintainer OWNS the cut and the
   acceptance — `groom` only proposes"
   (`livespec-orchestrator-beads-fabro`
   `SPECIFICATION/contracts.md` §"Grooming and slice-size
   calibration"), backed by the maintainer's design-record quote about
   the factory going wild past an automated review gate.
3. **The truly-unresolvable set.** Drift acceptance, spec-change
   slices, and regroom/backlog bounce are human-gated BY DESIGN: "no
   dispatcher policy setting may auto-dispose them; they MUST stay
   escalated" (`livespec-orchestrator-beads-fabro`
   `SPECIFICATION/spec.md` §"Terminology"; contracts §"Every
   needs-human escalation still reaches a human"). Also
   `resolve-blocked` for `blocked_reason: needs-human` items. The
   foreman thread's review findings already scoped relaxing this
   honestly as "a REVERSAL of the needs-human clause's core guarantee,
   not an extension", touching three repos
   (`livespec-overseer` `plan/foreman/research/review-findings.md`).

### Recommend keeping human permanently (low value to automate)

`seed`'s greenfield intent interview; `prune-history` (destructive,
human-invocation-only by contract); lessons ratification (a human
merging the PR is the whole safety property,
`livespec-orchestrator-beads-fabro` contracts); design-record
contradictions and design-record-absence findings in revise/critique —
the "never self-waived" clauses become the ESCALATION TARGETS of every
automated path below, not gates to remove. The revise prose already
carves this out: the delegation toggle "never delegates this
acknowledgment: a delegated pass reaching such a contradiction MUST
fall back to the explicit per-proposal confirmation for that
proposal" (`.claude-plugin/prose/revise.md`, the intent-preservation
gate).

## Proposed design — a core-owned `spec_governance` lever family

Mirror the proven `dispatcher.*` mechanics (see "Pattern checklist"
below). A core-owned block in `.livespec.jsonc`, since spec-side
operations are livespec-core surface:

```jsonc
"spec_governance": {
  // Per-proposal revise decisions. "delegated" pre-arms the existing
  // in-dialogue toggle; "consensus" requires the ratified panel tier.
  "revise_decision_mode": "manual",      // manual | delegated | consensus
  // Drift-origin proposals get their own, stricter floor — this is
  // the drift-doctrine knob, deliberately separate:
  "drift_acceptance_mode": "human",      // human | consensus
  // The independent adversarial ratification review, codified from
  // AGENTS.md into contract. Runs unconditionally under every mode —
  // the new structural floor "no ratification with zero review",
  // mirroring "no release with zero verification":
  "ratification_review": "manual-spawn", // manual-spawn | auto-spawn
  "doctor_dispositions": {},             // check_id → default verb
  "spec_pr_merge": "manual"              // manual | auto-on-green
}
```

Per-proposal override lives in the proposed-change file's front matter
(e.g. `decision_policy: manual`) — exactly analogous to the per-item
`admission:` / `acceptance:` labels. Unconditional floors, enforced as
the FIRST branch of every effective-policy resolver so no mode can
reach past them:

- design-record contradiction and design-record absence always
  escalate to the maintainer;
- any ratification-review blocker always escalates ("never
  self-waived" is preserved because automation only handles the
  NO-BLOCKERS path);
- drift-origin proposals floor at `drift_acceptance_mode` regardless
  of `revise_decision_mode`.

Two structural properties worth preserving through all later design:

- **The delegated path composes review + decision as two independent
  AIs.** Under `delegated`, the auto-spawned adversarial review must
  return NO BLOCKERS AND the delegated decider must accept;
  disagreement escalates to the human. Strictly stronger than today's
  manual path, where the review is a discipline the maintainer must
  remember to run.
- **The foreman is the spec-side executor, so `drive`'s refusal
  contract never changes.** The orchestrator keeps refusing spec-side
  action-ids; the foreman (which already plans to run sessions and to
  consume `needs-attention`'s spec-next handoff) simply RUNS
  `livespec:revise` in a session when the governed repo's levers
  authorize an unattended pass. The foreman thread currently routes
  ALL spec matter to humans and never proposes automating a spec-side
  gate — this thread fills that gap rather than conflicting with it.

## Three increments, mapped to repos

**Increment 1 — no doctrine change** (unblocks "foreman files, human
only ratifies"): intent/topic threading + non-interactive batch modes
for `propose-change` / `critique`; `spec_pr_merge: auto-on-green`;
`doctor_dispositions`; `ratification_review: auto-spawn` (lifting the
AGENTS.md rule + `.ai/spec-proposal-review.md` into contract). Lands
in: **livespec** (prose + contracts + config keys),
**livespec-driver-claude** / **livespec-driver-codex** (thin binding
pass-throughs if any), **livespec-dev-tooling** (extend the
API-configurable-completeness check family, consumer-side per the
No-Circular-Dependency Directive, `.ai/no-circular-dependency.md`).

**Increment 2 — the revise doctrine amendment**:
`revise_decision_mode: delegated` for non-drift proposals with the
review-as-floor semantics above. Lands in: **livespec** (`spec.md`
§"Intent preservation and design-record authority", the revise prose,
contracts for the lever), plus **livespec-orchestrator-beads-fabro**
(its citations of core doctrine; `needs-attention` stops advertising
the spec-revise human handoff lane when the lever retires it — the
same shared-predicate retirement pattern `auto_approve_ready` uses).

**Increment 3 — the consensus reversal** (shared with foreman
Phase C): `drift_acceptance_mode: consensus`, auto-groom with a
regroom cap, and consensus-disposed `resolve-blocked` — all riding the
foreman thread's already-decided opt-in consensus tier (unanimous
cross-vendor panel, closed action vocabulary so unanimity is string
equality, non-overridable dissent, journaled, budgeted). Lands in:
**livespec** (amending the drift-doctrine sentence to "only humans or
a ratified consensus process accept it"),
**livespec-orchestrator-beads-fabro** (the truly-unresolvable-set
amendment + groom mode + consensus valve disposal),
**livespec-overseer** (the panel implementation foreman Phase C
builds — ONE panel serving both planes).

Sequencing: increments 1–2 are useful without the foreman existing
(any attended session benefits), and foreman Phases A/B do not need
them — the two tracks proceed in parallel and meet at
Increment 3 / Phase C. Bootstrap note: the foreman thread's own six
proposed changes sit un-ratified in `livespec-overseer`
`SPECIFICATION/proposed_changes/` awaiting exactly the kind of revise
pass Increment 2 automates.

## Pattern checklist — the `dispatcher.*` mechanics to mirror

Distilled from `livespec-orchestrator-beads-fabro`
(`_dispatcher_policy_settings.py`, `_drive_config_schema.py`,
`_drive_valve_predicates.py`, `_dispatcher_completion.py`):

1. One resolver module, fail-open to SAFE defaults (missing file /
   block / key / wrong type → default, never raise); type-strict
   coercion (`is True` / `is False` for booleans, `frozenset`
   membership for enums).
2. A declarative `ConfigKey` row per key (key, value_type, default,
   per_item_override, values) driving parse, coercion, manifest, and
   error text from one tuple; a committed API-configurable-keys
   manifest.
3. An `effective_<thing>()` resolver with fixed precedence: hard
   design floor FIRST → per-proposal override → global lever → safe
   default. The floor in the first branch means every downstream
   consumer inherits it for free (this is how "a spec-change-tier item
   is never auto-approved" holds everywhere today).
4. Every auto-disposition journaled, naming the governing setting.
5. A `set-<thing>` action with a value allowlist and a `clear`
   sentinel; a policy edit is never a state transition.
6. One shared predicate module gating BOTH enforcement and
   `needs-attention` advertisement, so an armed lever automatically
   stops advertising the valve it retires.
7. Spec text in three places (spec.md doctrine, contracts.md wire
   surface + design record, constraints.md safe-default + audit +
   still-escalate rails) plus scenarios: the global, the per-proposal
   override, the design-floor exemption, and
   all-defaults-arm-nothing.

## Values calls — ALL THREE RESOLVED 2026-08-03

Calls 1 and 2 were put to the maintainer after an independent review
judged them genuinely maintainer-owned rather than determinable from
existing doctrine; call 3 was self-resolved on that same review's
OBVIOUS-ADOPT verdict. The decisions below are ratified inputs to
Increments 2 and 3 — not recommendations, and not re-openable without
a fresh maintainer decision.

1. **Does the drift-doctrine sentence get amended at all?**
   **RESOLVED — YES, consensus tier only, via a DEDICATED key.**
   Add `spec_governance.drift_acceptance_mode` with values
   `human | consensus`, defaulting to `human`, opt-in per repo,
   requiring the unanimous cross-vendor panel, at Increment 3. Amend the
   drift-doctrine sentence in `SPECIFICATION/spec.md` to "only humans or
   a ratified consensus process accept it".

   Hard limits: `delegated` is NEVER a legal value — a single model may
   not accept drift. The key is DEDICATED: drift acceptance must never
   be reachable through `revise_decision_mode`, and the drift floor
   resolves BEFORE that lever. Default is `human`; an adopter opts in
   deliberately. The key must not ship armed-able before the consensus
   panel actually exists.

   Rationale the maintainer gave: a dedicated, separately-armed setting
   is a STRONGER safety design than a hard-coded floor, because it
   defaults safe, is auditable per repo, and cannot be flipped as a side
   effect of the general revise lever.

   Scope note: drift DETECTION was never gated. `capture-spec-drift`
   already files drift unattended and the doctrine explicitly blesses
   that machine path. Only ACCEPTANCE was ever human-gated, and it is
   acceptance this decision governs.

2. **Does the groom cut ever leave the maintainer's hands?**
   **RESOLVED — YES, but automated LAST and consensus-gated.** Only
   after Increments 1–2 land, only behind the same consensus tier, and
   only with slice-size ceilings plus a regroom cap as REQUIRED rails,
   not optional ones. `livespec-orchestrator-beads-fabro`
   `SPECIFICATION/contracts.md` §"Grooming and slice-size calibration"
   is amendable at Increment 3 for the cut only.

3. **Where does the consensus-tier DEFINITION live?**
   **RESOLVED — core-defined, orchestrator/overseer-implemented.**
   `livespec-orchestrator-beads-fabro` `SPECIFICATION/spec.md`
   §"Terminology" already adopts core's glossary verbatim and states
   that plugin-local terms "extend the upstream glossary, never
   contradict it" — the same shape as this question. Reinforced by
   `.ai/no-circular-dependency.md`: the tier must serve ONE panel across
   both planes, so the only non-circular home for the shared definition
   is the upstream repo both planes already cite. Deserves its own design pass
   before Increment 3.

## Cross-links

- `livespec-overseer` `plan/foreman/` — `handoff.md` (thread binder),
  `research/brainstorm.md` (decisions 1–4; v2 phasing A–E),
  `research/review-findings.md` (33 adversarial findings; C1 makes
  human valves report-only for the foreman until the consensus tier
  ratifies; the consensus reversal scoped as three repos).
- `livespec-orchestrator-beads-fabro` `SPECIFICATION/contracts.md`
  §"Dispatcher policy settings" (the pattern), §"Grooming and
  slice-size calibration" (the groom gate), §"Every needs-human
  escalation still reaches a human" (the floor);
  `SPECIFICATION/spec.md` §"Terminology" (the truly-unresolvable set).
- This repo: `AGENTS.md` §"Independent Fable review before every
  ratification" and the acceptance-policy second-leg addendum
  (2026-07-20); `.ai/spec-proposal-review.md`;
  `.claude-plugin/prose/revise.md` (the delegation toggle and the
  intent-preservation gate); `SPECIFICATION/spec.md` (the drift
  doctrine).
