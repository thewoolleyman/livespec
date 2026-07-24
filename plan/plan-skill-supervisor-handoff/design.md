# plan-skill-supervisor-handoff — design note

**Status:** RESEARCH-ONLY thread, opened 2026-07-23. No `handoff.md` yet and no
ledger epic anchored yet — deliberate, see §9. A young thread MAY be
research-only per the store rule in
`SPECIFICATION/non-functional-requirements.md` §"The planning thread".

**The ask (maintainer, 2026-07-23):** make the `plan` operation create a
`supervisor-handoff.md` **by default**, beside the thread's existing
`plan/<topic>/handoff.md`. The generated file is a *prompt* for a supervising
session. It must **fail loudly and fast** when the tmux session and the
claude/codex session it names do not currently exist, with names matching the
plan's topic exactly. livespec must not acquire a tmux dependency.

**Decision (maintainer, 2026-07-23):** `by default` means **everywhere** —
unconditional generation for every plan thread. Rationale, verbatim in
substance: *most threads are unsupervised because supervision is manual; this
makes it easier.* This SUPERSEDES the generate-on-request recommendation in §8.1,
which was built on the wrong premise (that the low supervision rate reflected low
demand rather than friction).

> ## ⚠ §0 — READ FIRST: §3 is superseded by §10; **§11 carries the chosen shape**
>
> Read §11 FIRST — it is the maintainer's `supervise-plan` proposal, it
> dominates every option in §10.6, and it is what should be built. §10 remains
> the reasoning that rules the alternatives out.
>
> The original note found a **filename-level** collision (one handoff per topic)
> and proposed typing the file as a "supervision-lane facet". That resolution is
> **under-powered and partly wrong**, and §10 replaces it. The real obstacle is
> not the filename: it is **plane assignment and dependency direction**, and the
> feature as literally specified is blocked by written specification in BOTH
> repos that could plausibly generate the file. §10 carries the citations and the
> viable paths. Do not implement §3 as written.

---

## 1. Why this is worth doing — the durability evidence

Supervisor prompts are already a real, load-bearing fleet practice. Three exist
today. Two of them are **not durable**, and that is the defect this feature
closes:

| artifact | tracked by git? | verified how |
|---|---|---|
| `tmp/factory-success-rate-remediation-supervisor-prompt.md` | **NO** — gitignored | `git check-ignore -v` → `.gitignore:2:tmp/`; `git ls-files --error-unmatch` → "did not match any file(s) known to git" |
| `tmp/fleet-pin-propagation-supervisor-prompt.md` | **NO** — same `tmp/` rule | same |
| `plan/archive/autonomous-mode-retirement/supervisor-handoff.md` | **YES** | `git ls-files --error-unmatch` → path echoed |

The only supervisor prompt that survived is the one a maintainer directed into
`plan/` (2026-07-23, archived beside that thread's own `handoff.md`). The other
two sit one `rm -rf tmp/` — or one lost machine — from gone, and they carry
hard-won operational knowledge: the `TMUX_BIN` naming hazard, the
`IDLE`-plus-queued-input stall signature, the beads-command `PreToolUse` guard,
cross-track factory serialization rules.

So the feature is not "a new artifact type". It is **moving an artifact the
fleet already depends on out of a gitignored scratch directory and into the
durable record**, and generating it consistently instead of by hand.

## 2. Where the change actually lands — TWO repos, and core is the blocker

This is the reason this thread is opened in **livespec core** even though the
`plan` skill itself lives elsewhere.

- **The realization** — the `plan` skill — belongs to
  `livespec-orchestrator-beads-fabro`:
  - `.claude-plugin/prose/plan.md` §"The planning-thread store" and its Flow
    steps (the real driving prose; the SKILL.md files are thin bindings that
    add no behavior),
  - `SPECIFICATION/contracts.md` §"The `plan/<topic>/` thread store",
  - the thin bindings at `.claude-plugin/skills/plan/SKILL.md` and the
    `.codex-plugin` twin.
- **The blocking constraint is CORE's.** Core records the Planning-Lane
  *pattern* in `SPECIFICATION/non-functional-requirements.md` §"Planning Lane
  guidance": *"at most one resumable handoff … Only one resumption point may be
  active per topic"*, plus the no-shadow-ledger rule's *"handoffs live at the
  reserved `plan/<topic>/handoff.md` path"*. Core is explicitly NON-normative on
  the realization ("NO new core skill, NO new core CLI, NO new core doctor
  invariant") — but the *one-resumption-point* rule is core's own recorded
  discipline, and this feature adds a second prompt file to every thread
  directory. **Core must decide first; the orchestrator implements after.**

Sequencing: core NFR amendment (via `/livespec:propose-change` → `/livespec:revise`)
→ orchestrator contract amendment → orchestrator prose change → bindings.

## 3. The blocking design question

Is `supervisor-handoff.md` a second handoff, a research note, or a new facet?

The orchestrator's store rule (`prose/plan.md:43-47`, verbatim):

> **At most one handoff** — the reserved filename `plan/<topic>/handoff.md`,
> the single resumable execution-coordination point for the thread. Only one
> resumption point may be active per topic; a second handoff (any other
> `handoff*.md`) is malformed and this operation refuses to create it.

Three readings, and they do not agree:

- **(A) A second handoff → REFUSED.** By the sentence's *spirit* — "only one
  resumption point may be active per topic" — a supervisor prompt that a fresh
  supervising session opens to resume supervision plainly *is* a resumption
  point. Under this reading the feature is currently forbidden.
- **(B) A research file → allowed today, but mis-typed.** Research files are
  defined as "durable reasoning ('why this shape')". A supervisor prompt is an
  operational instrument, not reasoning. It would also be forced under
  `research/` as soon as a thread has more than one note, which buries it.
- **(C) A new, explicitly-named third facet → requires amendment.** Exactly one
  optional `plan/<topic>/supervisor-handoff.md`, typed as a **supervision-lane**
  artifact.

**Recommendation: (C).** The rationale that makes (C) consistent rather than a
carve-out: *"one resumption point per topic" is a rule about the THREAD'S OWN
WORK.* `handoff.md` resumes the session doing the work; `supervisor-handoff.md`
resumes a **different actor** — the supervisor — whose job is explicitly *not*
to do that work. Two actors, two resumption points, no ambiguity about which
file a given session opens, and the invariant that matters (a work session has
exactly one resumption point) is preserved verbatim. The amendment should say
this in those terms rather than simply raising the count to two.

## 4. A glob technicality that must NOT be used as the answer

Worth recording so a later session does not "discover" it and treat it as
permission:

- The refusal pattern is `handoff*.md` — an anchored prefix. `supervisor-handoff.md`
  **does not match it**.
- All three fleet checks that scan plan threads glob `*/handoff.md` exactly —
  `plan_thread_anchor_declared.py:48`, `plan_thread_epic_parity.py:48`,
  `handoff_dispatch_routing.py:47` (verified in `livespec-dev-tooling`).

So a `supervisor-handoff.md` dropped into every plan thread today would sail
past both the operation's refusal and every static gate, silently. **That is an
accident of pattern-anchoring, not a decision.** The feature must land on an
explicit amendment (§3C). Two consequences to carry into implementation:

1. If the amendment lands, those three globs stay correct as-is (they *should*
   ignore the supervisor file — it has no ledger anchor of its own and is not
   the thread's dispatch-routing surface). Confirm rather than assume when
   implementing.
2. The orchestrator's own refusal pattern should be tightened to name
   `supervisor-handoff.md` as the *one* permitted exception and keep refusing
   everything else, so the exception is enumerated rather than incidental.

## 5. The tmux dependency — how livespec avoids acquiring one

This is the crux of the maintainer's constraint, and it resolves cleanly on a
**generation-time vs use-time** split:

- **Generation time** (`/plan` runs): the operation writes a markdown file. It
  runs **no tmux command, imports nothing, shells out to nothing**. It does not
  check whether any session exists. livespec's dependency surface is *unchanged*.
- **Use time** (a supervising agent opens the generated file): the file's FIRST
  instruction block is a precondition gate the *reading agent* executes.

So the tmux coupling lives entirely in **generated prose**, executed by the
agent that reads it — never in livespec code, tests, or CI. Nothing in the
fleet's `just check` ever invokes tmux because of this feature.

The corollary is a hard authoring rule for the template: **the precondition
block must never be silently skippable.** A prompt whose gate the reader can
shrug off is the "a verifier must be able to fail" failure mode this fleet has
already documented repeatedly.

## 6. The fail-loud precondition contract

The generated `supervisor-handoff.md` opens with a HALT-first block, before any
role or mission prose, stating that the agent must run these checks and stop on
the first failure — reporting the exact failing check, not improvising a
workaround:

1. **Supervised session exists.** `tmux has-session -t <topic>` must succeed.
   The name is the plan topic **exactly** — no fuzzy matching, no prefix search,
   no "did you mean". Observed fleet reality confirms the convention:
   `cutover-and-shipping`, `fleet-pin-propagation`, `rop-sweep-fleet-policy`,
   `factory-success-rate-remediation` are all tmux sessions named exactly for
   their plan topic.
2. **It is really an agent session.** The session's pane must be running a
   `claude` or `codex` CLI process — checked inline (pane pid → process argv),
   not assumed from the name. A tmux session named for the topic that is just a
   shell is a FAILURE, not a pass: it means the supervised session died and the
   name outlived it. Which driver was found (claude vs codex) is reported, since
   the drive mechanics differ.
3. **Supervisor session exists.** `tmux has-session -t <topic>-supervisor`,
   again exact.

On any failure: **stop immediately, report which check failed and the exact
expected name, and do nothing else** — do not create the missing session, do not
fall back to a different one, do not proceed read-only. Creating a session to
satisfy your own precondition destroys the signal the precondition exists to
give.

**Reference implementation, NOT a dependency:** `livespec-overseer`'s
`overseer/claude_sessions.py` and `overseer/codex_sessions.py` already solve
driver-detection-from-a-pane robustly. Read them for the technique when writing
the template's check; do **not** make livespec or the orchestrator depend on
that package — the Control-Plane tool is a peer, never a component.

## 10. THE REAL OBSTACLE — plane assignment and dependency direction

*Added 2026-07-23 after auditing the actual specifications across all three
repos. This supersedes §3's recommendation.*

### 10.1 The absence proof

Grepped across every spec file in both upstream repos:

| repo | spec files | mentions of `overseer` or `tmux` |
|---|---|---|
| `livespec` (core) | `spec.md`, `contracts.md`, `constraints.md`, `non-functional-requirements.md` | **0, 0, 0, 0** |
| `livespec-orchestrator-beads-fabro` | `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`, `README.md` | **0, 0, 0, 0, 0** |

There is **no specification anywhere upstream** that authorizes a supervision
artifact. Building one into the `plan` operation does not fill a gap — it
introduces Control-Plane vocabulary into two planes that deliberately contain
none.

### 10.2 The three planes, and the rule that every artifact belongs to exactly one

`livespec/SPECIFICATION/spec.md:283` — *"LiveSpec's blessed workflow spans three
planes; conflating them is the recurring design error. Each plane owns a distinct
concern, and **every artifact and skill belongs to exactly one**"*:

- **Spec Plane** (core) — *"owns `SPECIFICATION/`, **the durable planning threads
  under `plan/<topic>/`**, and the `/livespec:*` lifecycle"* (`spec.md:285`).
- **Orchestrator Plane** — ledger, Dispatcher, Loop (`spec.md:286`).
- **Control Plane** — *"the operator experience: observe every plane's state,
  surface what needs attention, and **coordinate the human through multi-session
  work**"* (`spec.md:287`).

A supervisor prompt is, word for word, the Control Plane's charter. And
`plan/<topic>/` is, word for word, a Spec-Plane store. So placing one inside the
other assigns a single artifact to two planes — the specific error `spec.md:283`
names as *the recurring design error*.

`livespec-overseer` is a Control-Plane member: repo class `control-plane-tool`,
*"a Control-Plane member that ships an operator TOOL rather than the cockpit
APPLICATION the `console` class carries; the two are PEERS"*
(`non-functional-requirements.md:1051`).

### 10.3 The seam count is closed, and the direction is backwards

`spec.md:329` — *"The Planning Lane touches the Orchestrator Plane at **exactly
two** explicit, **one-directional** seams: (1) a handoff cites ledger ids
read-only … (2) routing ripe work into the ledger … through `capture-work-item`"*.

Both sanctioned seams run **Spec → Orchestrator**. A supervision artifact creates
a **third** seam, to a plane the sentence does not contemplate, running
**Control → Spec** — inbound to the plane that is supposed to depend on nothing.

The governing rule is `non-functional-requirements.md:199`: *"The console **MUST
NOT** become a dependency of the workflow it observes: the spec lifecycle and the
orchestrator skills MUST stay independently drivable without it. The Control Plane
ENRICHES the operator experience rather than gating it … **no plane depends on the
console.**"* If every plan thread carries a prompt encoding tmux session naming
and claude/codex driver detection, the Planning Lane's own artifact store now
hard-codes ONE Control-Plane realization — in a model where the console/tool is a
pluggable reference realization, not a fixture.

**Prose does not launder this.** §5's generation-time/use-time split correctly
shows livespec acquires no *runtime* tmux dependency. But authoring the template
still puts Control-Plane knowledge inside an Orchestrator-Plane skill. The
dependency being violated is architectural, not packaging.

### 10.4 …and the Control Plane cannot write it either

The obvious fix — let the overseer generate the file, since it already enumerates
every watched repo's `plan/*/` directories (`overseer/registry.py:503`) and
already owns session naming — is blocked by the overseer's **own** specification.

`livespec-overseer/SPECIFICATION/spec.md:228` §"Non-interference with tracked
work": *"The overseer **NEVER** touches files under any repository's plan tree …
it **never opens, writes, or hashes** those files"*. Discovery is pinned to
directory existence only (`spec.md:172-177`), and its state lives in *"exactly
two places: its home-directory stores, and a per-track temporary directory inside
each watched repository's **gitignored** scratch area … the daemon verifies that
every watched repository ignores that scratch path and **REFUSES to run** if any
does not — so supervision can **never dirty a tracked working tree**"*
(`spec.md:237-241`).

That is not incidental prose: it is enforced by a startup refusal and exists to
guarantee supervision cannot dirty tracked state.

**So the feature as literally specified is blocked in both candidate homes.** The
`plan` skill may write to `plan/` but must not know about tmux; the overseer
knows about tmux but must not write to `plan/`.

### 10.5 What is already specified, and therefore need not be rebuilt

The maintainer's "names matching the plan's topic exactly" requirement **already
exists as ratified spec, in the right plane**:
`livespec-overseer/SPECIFICATION/spec.md:188-193` — a supervised session is named
after its **bare plan topic**, qualified as `<repo-slug>-<topic>` only on a genuine
cross-repository collision — and `spec.md:225-226` requires runtime identity to be
established *"from exact live process evidence, never inferred from a topic name"*,
which is precisely the claude/codex check §6 asks for. Re-specifying either inside
a generated prompt would duplicate ratified spec into a plane that must not hold it.

### 10.6 Viable paths, in recommended order

1. **Split by plane (RECOMMENDED).** `plan` generates the file for every thread —
   satisfying the "everywhere" decision — but its content is **plane-clean**: the
   thread's topic, repo, ledger anchor, the supervisor-not-implementer role, the
   decision-vetting rubric, the corrections discipline. **No tmux, no driver
   names, no session names.** It points at the Control-Plane contract for
   preconditions. The tmux fail-fast lives in the overseer's `/overseer` operator
   surface — which is being built right now under `livespec-overseer`'s
   `plan/cutover-and-shipping/` scope item 3, so there is a natural home landing
   imminently. Cost: one narrow core amendment (admitting a second, non-resumable
   planning-thread facet). No seam added, no direction inverted, no overseer write.
2. **Control-Plane durable store outside the plan tree.** The overseer gains a
   committed store for supervisor prompts. Keeps planes clean and needs no core
   change, but requires amending the overseer's two-places state rule, and loses
   co-location with the thread.
3. **Amend both specs to allow it as asked.** Core admits a named Control-Plane
   artifact inside `plan/<topic>/`, AND the overseer carves an exception into
   non-interference. **Not recommended:** the carve-out weakens a safety property
   enforced by a startup refusal, trading a real guarantee for file placement.

### 10.7 Correction to §3

§3's "supervision-lane facet resuming a different actor" resolves only the
one-resumption-point collision. It does not address plane assignment, and naming a
"supervision lane" would add a fourth lane to a three-plane model whose first rule
is that every artifact belongs to exactly one plane — making the change larger than
§3 represented, not smaller. The two-actors *argument* remains useful for the
narrow amendment in path 1; the *framing* as a new lane should be dropped.

## 11. THE CHOSEN SHAPE — a Control-Plane `supervise-plan` skill

*Maintainer proposal, 2026-07-23, audited and ADOPTED. Dominates every option in
§10.6; those remain only as the record of why the alternatives fail.*

**The shape.** A new `supervise-plan` skill in the overseer's own plugin
namespace (Control Plane) creates `plan/<topic>/supervisor-handoff.md`, under a
single named carve-out, writing it through the target repo's **own documented
commit discipline** — worktree → PR → review → merge, driven by prose that reads
the repo's conventions rather than hard-coding them. Nothing is added to
`livespec` core, the orchestrator, or any Driver.

### 11.1 Why this dominates §10.6

- **The dependency-direction break disappears entirely.** §10.3's third seam and
  the `NFR:199` violation existed because an *upstream* plane would have had to
  learn tmux. Here the generator is Control-Plane, where that knowledge already
  legitimately lives. Core and orchestrator specs keep their **0** mentions of
  `overseer`/`tmux` (§10.1). The `plan` operation is not modified, so its
  "a second handoff… this operation refuses to create it" clause is never even
  reached — that refusal is scoped to *that operation*.
- **It reuses ratified spec instead of duplicating it.** §10.5's session-naming
  rule (`livespec-overseer/SPECIFICATION/spec.md:188-193`) and the live-process
  identity rule (`:225-226`) are already the Control Plane's; a Control-Plane
  skill simply invokes them. The §6 fail-fast gate stops being a duplication.
- **The plugin home is real and imminent, not hypothetical.** The operator
  surface is DECIDED as a fleet-standard plugin with a thin skill binding over
  repo-owned prose (`research/operator-surface.md`), and the entry-points slice
  `overseer-m5dtmj` is in the factory as this is written. `supervise-plan` is a
  natural sibling slice under epic `overseer-3wt`, not a new effort.

### 11.2 Why the non-interference objection does NOT survive — the key move

§10.6 path 3 was rejected because a carve-out "weakens a safety property enforced
by a startup refusal". **The worktree discipline defeats that objection**, and
this is the load-bearing insight of the proposal.

The property the rule protects is stated in its own words: *"supervision can
**never dirty a tracked working tree**"*
(`livespec-overseer/SPECIFICATION/spec.md:241`). A worktree → PR → merge flow
**never writes to the primary checkout at all**. The file reaches the repo by
merge commit, exactly like every other tracked file. So the invariant is
**preserved literally**, not traded away.

Be precise about what still changes, though — do not oversell this as a no-op:

- The rule as WRITTEN binds the whole tool: *"The **overseer** NEVER touches
  files under any repository's plan tree"* (`spec.md:230`). So a real amendment
  is required; it is not merely a clarification.
- The rule's RATIONALE, however, is entirely daemon-shaped: the plan tree is
  *"the supervised session's own workflow"*, and *"the restart interlock
  deliberately inspects nothing beyond the state-file token for the same
  reason"*. Both concerns are about an **unattended tick loop racing a live
  session** — neither applies to an attended, reviewed, worktree-based write.
- The correct amendment therefore SCOPES the prohibition rather than punching a
  hole in it: the **daemon's observation and restart loop** never touches the
  plan tree (unchanged, safety-critical, still enforced by the startup refusal);
  an **attended operator skill** may create exactly one named artifact through
  the repo's normal commit discipline.
- The *"state lives in exactly two places"* sentence (`spec.md:237`) needs one
  distinction, not a third entry: `supervisor-handoff.md` is an artifact the
  Control Plane **authors for a human or agent to read**, never runtime state the
  daemon reads back. The daemon must still never open it. Keeping "state" and
  "authored artifact" distinct preserves that sentence intact.

### 11.3 What still needs amending — and why it is not coupling

Two one-line amendments remain, because both upstream specs **enumerate** the
planning thread's contents, so a third file contradicts them no matter who wrote
it:

- `livespec` core `non-functional-requirements.md:175` — *"carrying two
  facets"*.
- `livespec-orchestrator-beads-fabro` `contracts.md` §"The `plan/<topic>/` thread
  store" — *"holding two facets"*.

Both amendments are **realization-agnostic declarations of non-ownership**, which
is the opposite of coupling: core says a planning-thread directory MAY host one
Control-Plane artifact that the Spec and Orchestrator planes MUST ignore; the
orchestrator says the `plan` operation neither creates, reads, nor validates it.
Neither names tmux, the overseer, or any tool — core already carries the
Control-Plane concept generically (`spec.md:287`), so this adds no new vocabulary
and no new dependency.

The honest answer to "no coupling anywhere upstream" is therefore: **no coupling,
but not literal silence.** Silence would leave `NFR:175`'s enumeration
contradicted in fact — precisely the unstated drift the fleet's doctor checks
exist to catch. Declaring the artifact ignored is what keeps the specs true.

### 11.4 Surfacing — DECIDED (maintainer, 2026-07-23): liveness-gated, two messages

`by default = everywhere` is delivered by an **automatic nudge with an attended
write**: the Control Plane surfaces the need, the operator runs `supervise-plan`,
the skill writes via worktree → PR. The nudge is what makes it "everywhere"; the
write stays reviewed.

**The anti-spam primitive is a liveness gate.** A track surfaces ONLY if it has a
CURRENTLY MATCHING live session. Most plan threads across the watched repos have
no session at all, and nagging about those forever is the failure mode this gate
exists to prevent. Two distinct messages:

- **Surface A — "no supervision prompt."** Live matching session exists, and
  `plan/<topic>/supervisor-handoff.md` is MISSING → offer `supervise-plan`.
- **Surface B — "nobody supervising."** Live matching session exists, the file IS
  present, but NO SUPERVISOR IS RUNNING → offer to start one.

#### The full truth table — including a cell the two rules do not cover

Gate first: **no live matching session → silent, always.** Within a live track:

| supervisor file | supervisor running | surface |
|---|---|---|
| missing | no | **A** — no supervision prompt |
| present | no | **B** — nobody supervising |
| present | yes | silent (healthy) |
| **missing** | **yes** | **UNSPECIFIED — see below** |

The fourth cell is not hypothetical: it is **the state of every supervised track
right now** (2026-07-23). Three supervisors are running tonight, and all three
keep their charter in gitignored `tmp/`, so every one of them is "supervisor
running, no file". Left undefined, the most likely implementation silently treats
a running supervisor as healthy and **never surfaces the missing file** — which
would permanently exempt precisely the tracks that already proved they need one,
and would quietly defeat the durability motive in §1. Recommended: treat it as
**A**, worded as a capture offer ("supervision is running but has no durable
prompt — capture it"), since it is also the migration path for the three live
charters.

#### "Running" must be proven, never inferred from a name

Apply the repo's own rule — runtime identity is established *"from exact live
process evidence, never inferred from a topic name"*
(`livespec-overseer/SPECIFICATION/spec.md:225-226`). A tmux session named
`<topic>-supervisor` is NOT sufficient evidence for Surface B: its pane must be
running a `claude`/`codex` process. Otherwise a dead supervisor's leftover tmux
session suppresses Surface B forever — a false negative that hides the exact
condition the surface exists to report. This is the same failure shape as §6's
precondition 2, and the same shape as the fleet's standing "a verifier must be
able to fail" rule.

#### Both surfaces MUST be edge-triggered

One line per EPISODE, not per tick. This is not a stylistic preference: the
daemon shipped exactly this defect and it was fixed hours before this note —
`overseer-4dr`, the malformed-state alert re-firing every tick instead of
edge-triggering, which alert-spammed a real operator pane. Re-arm only when the
condition clears and recurs. The machinery already exists and should be reused
rather than reinvented (`supervisor.py` carries edge-triggered alert state and
the `notified_bands` stamp pattern for exactly this).

#### Precedence — never bury a real signal

These are the lowest-priority surfaces. A track that is genuinely blocked on a
human (`blocked:` declaration or a structured gate on its pane) must show THAT,
not a supervision nag. Order supervision surfaces strictly below the existing
NEEDS-YOU / blocked classes.

#### What this costs, honestly

- **The stat allowance shrinks to something defensible.** Surface A still needs
  to test existence of one path inside a plan directory, which
  `spec.md:174-175` currently forbids (*"never reads, stats, or hashes any file
  inside a plan directory"*). But the liveness gate means it runs **only for
  tracks with an established live session** — a handful, not every thread in
  every watched repo. The amendment becomes narrow and bounded: for a track with
  live-session evidence, the daemon MAY test existence of the single reserved
  supervision-artifact path, and MUST NOT open, read, or hash it. That is a much
  smaller ask than the general-purpose stat the earlier draft implied, and it
  keeps the interlock rationale (never inspect the session's working files)
  intact.
- **Supervisor sessions are NEW machinery, though small.** Verified: the overseer
  today has NO notion of a `<topic>-supervisor` session — discovery is
  plan-directory-driven, and a supervisor session has no plan directory of its
  own, so it is not a track. Surface B therefore needs a new lookup (does a tmux
  session by that derived name exist, and is its pane a live agent process). Both
  halves are operations the overseer already performs for tracks; the work is
  wiring, not new capability. Derive the name with the SAME rule as
  `spec.md:188-193` (bare plan topic, repo-qualified only on genuine
  cross-repository collision) so the two never disagree.

#### Still available if the stat allowance is refused

`supervise-plan --all` — walk every watched repo's unarchived threads and open
ONE PR. Covers "everywhere" in a single attended invocation with nothing stat-ing
on a tick. Weaker ergonomics, zero spec cost. Keep as the fallback.

### 11.5 Net effect

| objection | status under §11 |
|---|---|
| §10.1 no upstream authorization | **Gone** — nothing tmux/overseer-shaped goes upstream |
| §10.2 artifact in two planes | **Survives**, resolved by one realization-agnostic core line |
| §10.3 third seam, inverted direction | **Gone** — generator is Control-Plane |
| §10.4 overseer non-interference | **Defused** — worktree→PR preserves the actual invariant; amendment scopes the daemon rule |
| §10.5 duplicating ratified spec | **Gone** — the skill invokes the overseer's own rules |
| "everywhere by default" | **DECIDED** — §11.4: liveness-gated nudge + attended write. Two open sub-questions only: the narrow stat allowance, and the fourth truth-table cell |

### 11.6 THE CUT — ready to work

Slices, dependency-ordered. All land in `livespec-overseer` under epic
`overseer-3wt` unless stated.

> **⚠ Correction, 2026-07-23 — an earlier revision of this section claimed
> "Slice 1 is unblocked NOW" because the entry-points slice `overseer-m5dtmj`
> merged (PR #42, `5ddcfee`). THAT WAS WRONG.** It conflated the two halves of
> the operator-surface decision: `research/operator-surface.md` decides BOTH (1)
> a fleet-standard **plugin**, with `/overseer` as a thin skill binding, AND (2)
> public **entry points**. `m5dtmj` shipped **(2) only**. A `supervise-plan`
> SKILL must live inside a plugin, so slice 1's real dependency is the plugin
> **scaffold** slice (`overseer-tn3hmi`), which has NOT landed. The
> `livespec-overseer` ledger already models this correctly — slice 1 is filed as
> `overseer-myjovi` held behind `tn3hmi` — and **the ledger edge is
> authoritative over this note; do not regroom it to match a claim made here.**
> Caught by the supervised session flagging the divergence rather than deferring
> to this document.

1. **`supervise-plan` skill + template.** Thin binding over repo-owned prose (the
   pattern `research/operator-surface.md` already chose). Creates
   `plan/<topic>/supervisor-handoff.md` via the TARGET repo's own documented
   commit discipline — worktree → PR → merge, prose-determined, never hard-coded.
   Template content per §7; HALT-first precondition block per §6, deriving names
   with the `spec.md:188-193` rule rather than restating it. **No daemon changes
   in this slice** — it is invocable by hand, which makes it independently
   useful and independently testable.
2. **Overseer spec amendment — scope non-interference.** Per §11.2: the DAEMON's
   unattended observation/restart loop never touches the plan tree (unchanged,
   still enforced by the startup refusal); an ATTENDED operator skill may create
   exactly one named artifact through the repo's normal commit discipline. Keep
   "authored artifact" and "runtime state" distinct so the two-places sentence
   (`spec.md:237`) survives intact. Independent Fable review before ratification,
   per repo discipline.
3. **Surface A + B, liveness-gated and edge-triggered.** Per §11.4. Needs the
   narrow stat allowance (slice 3a, an amendment bounded to live-session tracks,
   existence-test only) and the `<topic>-supervisor` session lookup with live
   process evidence. **Decide the fourth truth-table cell before building** — it
   is the current state of all three live supervisors and the default
   implementation gets it wrong.
4. **Upstream one-liners** (`livespec` core `NFR:175`; orchestrator
   `contracts.md` thread store) via `/livespec:propose-change` → `/livespec:revise`.
   **Deliberately LAST** — the amendments should describe something that exists,
   not something planned.
5. **Migrate the three live charters** out of gitignored `tmp/` into their
   threads, closing the §1 durability defect that motivated all of this.

**Not yet anchored:** this thread has no `handoff.md` and no core ledger epic, and
that remains deliberate — the implementation work items belong under
`overseer-3wt` in `livespec-overseer` (§11.5), not to a core-tenant epic, and an
active handoff would have to declare a concrete anchor or fail
`plan_thread_anchor_declared`. This note is the design record; the ledger carries
the work.

**Next action:** file `supervise-plan` as a groomed slice under epic
`overseer-3wt` in `livespec-overseer`, sequenced after the plugin and
entry-points slices land, and route the two upstream one-liners through
`/livespec:propose-change` at that time — not before, so the amendments describe
something that exists.

## 7. What the generated template should carry

Distilled from the three real prompts (§1) — they converged independently, which
is decent evidence these are the load-bearing sections:

- The HALT-first precondition block (§6).
- **Role: supervisor, NOT implementer.** Every existing prompt states this, and
  the archived one records a maintainer correcting a supervisor twice for doing
  the work itself. Hand work to the session marked **INPUT TO VERIFY**, with the
  explicit clause that if the session's verification contradicts the
  supervisor's, the supervisor is wrong.
- **How to inspect and drive**, with the hazards already paid for: one-line
  `send-keys` or the `load-buffer`/`paste-buffer` path with paste-chip
  verification; `IDLE` + queued input means STUCK not idle; never name a
  variable `TMUX`; never `kill-server` on the maintainer's socket.
- **The decision-vetting rubric** — escalate only what is *both* genuinely
  blocking and genuinely human-facing; drive decision-PREP first and surface the
  result with the question. Note the archived prompt's recorded maintainer
  correction that this bar is *higher* than it first reads.
- **AskUserQuestion presentation rules** — recommended option first and labelled,
  one question per turn, full repo names, `---` as the final line before a picker.
- **Standing safety clauses** to repeat into every instruction sent: no
  `--no-verify`, halt-and-report on hook failure, never touch another session's
  worktrees or branches.
- **A corrections section the supervisor keeps about ITS OWN errors.** Both
  archived prompts carry one and it is the highest-signal part of each. A record
  that logs only the supervised session's mistakes is a wrong record.

Sections stay in the template as headed prompts even when empty, so a fresh
supervisor fills them rather than discovering it needed them.

## 8. Open questions for the maintainer

1. **`by default` — how default?** Every new thread unconditionally, or written
   on first use with an opt-out? Most threads are never supervised; unconditional
   generation puts an unused prompt in every directory. A middle option: `/plan`
   generates it on request and on *resume* offers it when a `<topic>-supervisor`
   tmux session is observed. **Recommendation: generate on request + offer on
   resume**, so the artifact appears exactly when supervision actually starts —
   which also keeps §6's gate meaningful instead of routinely-failing noise.
2. **Retrofit the two live gitignored prompts?** They are the strongest template
   source material and the least durable artifacts on the machine. Suggest yes,
   as a one-time move into their threads, separate from this feature.
3. **Archive coupling.** `supervisor-handoff.md` archives with its thread — the
   autonomous-mode-retirement precedent already did exactly this. Assumed, not
   yet ratified.

## 9. Next actions

1. **Maintainer decides §8.1** (the `by default` shape) — it changes the surface.
2. **Anchor a ledger epic in the livespec core tenant and add `handoff.md`.**
   Deliberately not done here: an active handoff MUST declare a concrete
   `**Ledger anchor:**` epic id or `plan_thread_anchor_declared` fails
   `just check` (placeholders like `<epic-id>`/`TBD` are rejected), and inventing
   a core-tenant epic on the maintainer's behalf is not this note's call. Until
   then this thread is legitimately research-only.
3. **Core amendment** via `/livespec:propose-change` → `/livespec:revise` on
   `non-functional-requirements.md` §"Planning Lane guidance", per §3C's
   two-actors framing.
4. **Orchestrator amendment + implementation** in
   `livespec-orchestrator-beads-fabro`: contract, then `prose/plan.md`, then the
   two bindings; tighten the refusal pattern per §4.2.
5. **Template authoring** per §6/§7.

## 12. SHIPPED — 2026-07-24 status addendum

*Recorded by the plan-skill-supervisor-handoff session after driving the §11.6
cut. The ledger stays authoritative; the anchors below are pointers, not a
status store.*

- **Slice 1 SHIPPED and ACCEPTED.** The plugin scaffold landed as
  `livespec-overseer` PR #46 (work-item `overseer-tn3hmi`, accepted done with
  journaled evidence) and the `supervise-plan` skill as `livespec-overseer`
  PR #49 (work-item `overseer-myjovi`, accepted done). The acceptance's live
  exercise drove the shipped prose end-to-end against the live
  `rop-sweep-fleet-policy` track: all four HALT-first preconditions verified
  from live process evidence, then the operation generated
  `plan/rop-sweep-fleet-policy/supervisor-handoff.md` through THIS repo's own
  worktree → PR → merge discipline (livespec PR #1706). The fail-fast negative
  leg was observed honestly: against this thread itself the operation halts at
  precondition 3 (no `plan-skill-supervisor-handoff-supervisor` session), and
  no session was created to satisfy the gate.
- **Slice 2 FILED (not yet ratified).** The overseer non-interference scoping
  amendment is a pending proposed change in `livespec-overseer`'s own
  `SPECIFICATION/proposed_changes/` (filed via its PR #44), awaiting
  `/livespec:revise` there with the required independent review.
- **Slice 4 FILED (not yet ratified) — §11.6's "deliberately LAST" precondition
  met.** Both upstream one-liners were routed through `/livespec:propose-change`
  AFTER the skill existed and had produced a real artifact: livespec core
  PR #1724 (`SPECIFICATION/proposed_changes/supervisor-handoff-hosted-control-plane-artifact-in-plan-threads.md`)
  and `livespec-orchestrator-beads-fabro` PR #920
  (`SPECIFICATION/proposed_changes/supervisor-handoff-hosted-artifact-in-the-thread-store.md`).
  Ratification remains human-gated at `/livespec:revise` in each repo.
- **Slice 3 (+3a) still needs the §11.4 fourth-cell decision** before filing —
  unchanged from §11.6.
- **Slice 5 unblocked.** `overseer-tvko3z` (migrate the three live `tmp/`
  charters) is dependency-clear in the `livespec-overseer` ledger now that
  `overseer-myjovi` is done. Note `rop-sweep-fleet-policy` is NOT one of the
  three — its prompt was generated fresh by the live exercise above precisely
  because it had no `tmp/` charter to migrate.

The §11.6 "Next action" paragraph is discharged; the remaining maintainer
surface is: the fourth-cell decision (slice 3), the three pending
ratifications (slices 2 and 4), and dispatching `overseer-tvko3z` (slice 5).
