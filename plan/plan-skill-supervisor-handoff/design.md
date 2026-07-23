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
