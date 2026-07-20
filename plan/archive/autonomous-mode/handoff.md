# Autonomous-mode MVP — SUPERSEDED

> **This thread was SUPERSEDED and collapsed on 2026-07-19.** It had grown to
> 3220 lines by accreting a sibling repo's programme, and was judged coupled,
> non-cohesive, and off track. Its session narration (cont.1–24), its Step-0
> review-loop records, and its build-phase logs are **deliberately deleted** —
> all of it remains in git history.
>
> **ARCHIVED 2026-07-20** to `plan/archive/autonomous-mode/`. The three
> live-spec citations that name it as a design record were repointed to this
> path in the same landing — see below.

## Successors

| Thread | Owns |
|---|---|
| `plan/autonomous-mode-acceptance/handoff.md` (epic `livespec-j4odoz`) | The MVP acceptance — real fleet work-items driven end-to-end through the live console TUI, then the maintainer's accept. The only live work this thread still owned. |

The console programme (`livespec-console-beads-fabro:plan/cockpit-ux-docs-release/`)
was **never this thread's to own**. Tracking a duplicate copy of its state is
what broke this thread. Do not resume console work from here, and do not
re-home any of it into the successors.

The orchestrator-side sibling (`livespec-orchestrator-beads-fabro:plan/autonomous-mode/`)
was archived 2026-07-19; its work shipped and was superseded at orchestrator
spec v034.

## ⚠ THREE LIVE SPECS CITE THIS PATH — do not move it again without amending them

Three live-spec citations name this exact path (`plan/archive/autonomous-mode/handoff.md`) as the **design record**:

| Repo | Location |
|---|---|
| `livespec-orchestrator-beads-fabro` | `SPECIFICATION/contracts.md:1594` |
| `livespec-orchestrator-beads-fabro` | `SPECIFICATION/contracts.md:1649` |
| `livespec-console-beads-fabro` | `SPECIFICATION/spec.md:340` |

All three cite the section reproduced verbatim below. In this fleet the cited
design record is the **TIEBREAKER over shipped spec text**, and citation
fidelity is review-enforced only — no mechanical check would catch a dangling
path. Moving or deleting this file, or renaming that section heading, silently
corrupts future spec-conflict resolution. Amend all three citations first if
this file must ever move again.

All three were repointed from `plan/autonomous-mode/handoff.md` to this
archived path on 2026-07-20, in the same landing as the archive move, so no
window existed in which they dangled.

---

# THE CITED DESIGN RECORD — preserved verbatim

Everything below this line is reproduced byte-for-byte from the superseded
thread and is **historical**: it records what was decided on 2026-07-14, not
current state. Read it as the design record it is cited as, nothing more.

## SESSION UPDATE — 2026-07-14 (cont. 12): acceptance-model redesign RE-LOCKED — "master switch" REPLACED by THREE INDEPENDENT dispatcher settings + a general API⇒Settings⇒docs principle; the spec proposal is now RATIFIED (see cont. 13)

Fresh Claude (Opus) session resumed cont.11 to file the acceptance-model epic. In
the design-convergence dialogue the maintainer **REPLACED cont.11's single
"autonomous master switch" with a cleaner orthogonal model** and added a general
config-surface principle. **This section is the authoritative LOCKED design;
where it differs from cont.11 below, THIS wins.** RESUME = author the
`livespec-orchestrator-beads-fabro` spec proposal per this design → independent
Fable review → maintainer accept → impl epic.

### THE RE-LOCKED DESIGN (maintainer-declared 2026-07-14, cont. 12)
**"Full autonomous mode" is RETIRED OUTRIGHT** — removes the monolithic
`dispatcher.autonomous_mode` config key, the `--mode autonomous` flag + two-factor
dangerous arming, AND Scenarios 33–37. It is replaced by **independent
`dispatcher.*` settings**, each a **global default** that a **per-item ledger
label overrides**, each settable via the **orchestrator API AND the console**:

| # | Meaning | Config key | Values | Safe default |
|---|---|---|---|---|
| 1 | automatically mark items ready | `dispatcher.auto_approve_ready` | `true`/`false` | **`false`** |
| 2 | merge a past-cap failing review anyway | `dispatcher.merge_on_review_cap` | `true`/`false` | **`false`** (→ escalate) |
| 3 | acceptance mode | `dispatcher.acceptance_mode` | `ai-only`/`ai-then-human`/`human-only` | **`ai-then-human`** |
| 4 | review fix-round cap (inner, pre-merge) | `dispatcher.review_fix_cap` | int | **`3`** (the 2→3 bump = the default) |
| 5 | acceptance-rework cap (outer, post-merge) | `dispatcher.acceptance_rework_cap` | int | **`2`** |
| 6 | WIP cap (existing; now API-settable) | `dispatcher.wip_cap` | int | `5` (unchanged) |

Names are provisional (maintainer said "meaningful names"); adjust only with
maintainer sign-off. Config keys are `dispatcher.*` (siblings of the existing
`wip_cap`/`fabro_bin`).

### The behaviors these settings gate
- **Real post-merge AI acceptance pass** (replaces the hardcoded
  `{"confirmed": true}` stub in `_dispatcher_completion.py`): read-and-judge the
  merged diff vs. acceptance criteria + watch telemetry → **pass/fail**. Every
  acceptance carries ≥1 AI pass ("no release with zero verification" floor kept).
  - `ai-only`: AI pass PASS → `done`.
  - `ai-then-human`: AI pass PASS → **park** in `acceptance` for the human `accept`
    (`c`) valve.
  - `human-only`: park for the human; AI pass runs advisory.
- **AI-acceptance FAIL → auto-rework** back into the factory (fix-forward → `active`,
  re-merge, re-accept) with **NO human for a fail** — bounded by
  `acceptance_rework_cap` (the OUTER loop). Exceeding the cap → `blocked`/needs-human.
- **In-factory review becomes BLOCKING.** A still-blocking review at `review_fix_cap`
  (the INNER loop): if `merge_on_review_cap=true` → ship the PR anyway (escape
  hatch); else (default) → **escalate to `blocked`/needs-human** (a TERMINAL state
  — NOT eligible for auto-approve, so no infinite loop). Cited design record:
  `contracts.md` maintainer quote "…if the review gate is automated, pushing it all
  to production."
- **Two SEPARATE caps, both configurable** (#4 inner review loop, #5 outer
  acceptance loop). The review cap terminates at `blocked` (no loop); the
  acceptance cap is the one that prevents an infinite post-merge rework loop.
- **`needs-human` ALWAYS escalates to a human** — retiring autonomous mode DROPS
  its riskiest behavior (the LLM *guessing* human decisions on `needs-human`
  blocks; old Scenario 35). Spec-change-tier (design-human-gated) items are NEVER
  auto-approved regardless of `auto_approve_ready` (the old Scenario 36 substance,
  preserved as setting #1's exception).

### GENERAL PRINCIPLE (new contract, maintainer-declared cont. 12)
**Anything configurable via the orchestrator API MUST appear in THREE places, in
lockstep:** (1) a row under console **Settings**, (2) the TUI **inline/context
help**, (3) the **settings doc** (Markdown in the app's repo docs). Propose a
**mechanical completeness check** (dev-tooling/doctor) that FAILS if an
API-configurable key is missing from Settings or the settings doc — the
enforcement that keeps the principle real. Consequence: Settings surfaces ALL
API-configurable dispatcher knobs (incl. `wip_cap`), not just #1–#3.

### Console UX (LOCKED — maintainer asked me to design it, approved the mockup)
- **Global defaults → a NEW first-class "Settings" left-nav**, two levels:
  `Settings` → sub-menu `Dispatcher settings` (first & only item for now) → the
  settings rows. Enter/Space toggles a bool / cycles an enum / edits an int; the
  write persists to the orchestrator's `.livespec.jsonc` via a new orchestrator
  API action. Ships with its own **docs page + context-specific help**.
- **Per-item overrides → the EXISTING item valves** (`set-admission`/`set-acceptance`
  + a NEW per-item review-cap override), acting on the selected work-item (a
  per-item label that beats the global default for that one item).
- Mockup (approved):
  ```
  ┌─ Views ──────┐┌─ Settings ▸ Dispatcher settings ──────────────┐
  │ Attention    ││ Auto-approve ready          [ off ]           │
  │ Lanes        ││ Merge on review cap         [ off ]           │
  │ Repos        ││ Acceptance mode        [ ai-then-human ]      │
  │▶Settings     ││ Review fix cap              [ 3 ]             │
  │              ││ Acceptance rework cap       [ 2 ]             │
  │              ││ WIP cap                     [ 5 ]             │
  └──────────────┘└────────────────────────────────────────────────┘
  ```

### CONFIRMED (all locked with the maintainer this session)
Retire Full autonomous mode outright (A: yes); global defaults + per-item override
(B: yes, both controllable in the console); per-item override for ALL settings
**EXCEPT `wip_cap`** (see the CORRECTION below); drop auto-resolve-needs-human; all
defaults SAFE (#3 default `ai-then-human`); the two configurable caps; the
API⇒Settings⇒help⇒docs principle + mechanical check; `wip_cap` API-settable + in
Settings; console Settings nav + mockup + docs.

#### CORRECTION / ADDENDUM (2026-07-14, cont. 12 authoring session) — `wip_cap` is NOT per-item overridable
An earlier draft of this section said "uniform per-item override for ALL settings".
That is **too literal and must not be read as intent.** The maintainer picked the
option labeled "All six per-item overridable", whose option TEXT explicitly noted
"`wip_cap` presumably still excluded as nonsensical per-item". The RULE OF RECORD is
therefore:

> **Every dispatcher setting is per-item overridable EXCEPT `dispatcher.wip_cap`.**
> `wip_cap` is a per-repo CONCURRENCY CEILING (max items `active` at once), so a
> per-item value is structurally meaningless. The three policy settings
> (`auto_approve_ready`, `merge_on_review_cap`, `acceptance_mode`) AND both numeric
> caps (`review_fix_cap`, `acceptance_rework_cap`) each carry a per-item override
> label.

This correction is load-bearing: per `livespec-orchestrator-beads-fabro`
`SPECIFICATION/contracts.md` §"Intent preservation", THE CITED DESIGN RECORD (this
file) is the TIEBREAKER over the shipped spec when the two conflict. Left uncorrected,
the literal "ALL settings" wording here would silently OUTRANK the spec's `wip_cap`
carve-out in any future conflict. **Flagged for maintainer confirmation at accept
time** — the exclusion follows from the option text they chose, not from words they
typed themselves.

**Semantic inversion to be aware of (deliberate, and a REVERSAL of observed
behavior):** retired Full autonomous mode OVERRODE a stored per-item `manual` label
(that is how `bd-ib-jz62h3` was swept in and auto-approved in cont.11). The new model
INVERTS that precedence — **a per-item label BEATS the global default** — so an item
explicitly marked `manual` now HOLDS at `pending-approval` even with
`auto_approve_ready` on. Only an UNLABELED item inherits the global. This is the safer
precedence and follows directly from "global defaults, but allow per-item overrides",
but it is a deliberate reversal and is now normative in the proposal.

#### DECISION (maintainer-declared 2026-07-14) — `human-only` acceptance: the AI ADVISES, it never DECIDES
The maintainer asked the sharp question: *"If the acceptance is human only, how could
an AI ever do anything with it?"* The answer, and the RULE OF RECORD:

> Under `acceptance_mode: human-only` the AI acceptance pass **still RUNS** — that is
> what satisfies the existing "no release with zero verification" floor
> (`contracts.md` §"Post-merge acceptance": *"every acceptance carries at least one AI
> pass"*) — but it is **ADVISORY: it INFORMS, it never DECIDES.** It reads the merged
> diff against the acceptance criteria + telemetry and produces **findings**. It CANNOT
> accept, reject, or rework.
> **`human-only` means "no AI DECIDES this", NOT "no AI READS this."**

Consequence — the **AI-FAIL → auto-rework route is MODE-SCOPED**, applying ONLY to
`ai-only` and `ai-then-human`. Under `human-only` a FAILING pass surfaces as an
advisory **finding** and the item **STAYS PARKED** in `acceptance`; the human keeps the
accept / `reject (rework)` / `reject (re-groom)` decision. Rationale: **an auto-rework
IS the AI deciding**, exactly what `human-only` reserves to the human — unscoped, the
machine could repeatedly bounce an item the human explicitly claimed, stripping their
accept-vs-reject call. (Maintainer chose option A, "stay parked; advisory only", over
option B "auto-rework regardless of mode"; B would also have forced amending the
zero-verification floor.)

Landed: **`livespec-orchestrator-beads-fabro` PR #601** scopes the FAIL route in all
four places it appeared (the A.3 contract clause, the D.10 Scenario-25 addition, the
D.11 replacement scenario, and the Summary) and adds the `human-only` carve-out.

### THE CROSS-REPO EPIC (per "drive multi-repo work as one epic")
- **`livespec-orchestrator-beads-fabro` (spec + API + impl):** retire Full
  autonomous mode (§"Full autonomous mode", Scenarios 33–37, two-factor arming);
  add the six `dispatcher.*` settings (global-default + per-item-override) to
  `contracts.md` §"Dispatcher admission, WIP cap, and post-merge acceptance" (or a
  new §"Dispatcher policy settings"); real AI acceptance pass + AI-fail→auto-rework
  + `acceptance_rework_cap`→escalate; review gate blocking + configurable
  `review_fix_cap`; new scenarios replacing 33–37; the general API⇒Settings⇒docs
  contract; the orchestrator API config-write surface; `tests/heading-coverage.json`
  co-edits for every H2 change.
- **`livespec-console-beads-fabro` (Settings surface + docs):** first-class
  Settings left-nav → Dispatcher settings sub-menu; read/display + write the
  settings via the orchestrator API; the new per-item review-cap override valve;
  docs page + context-specific help; the mechanical completeness check (whichever
  side owns it — likely dev-tooling reading the console+orchestrator surfaces, per
  the No-Circular-Dependency Directive).

### RESUME ORDER (fresh session)
1. ~~**Author the orchestrator spec proposal**~~ — **DONE 2026-07-14.** Filed as
   `SPECIFICATION/proposed_changes/dispatcher-policy-settings.md` in
   `livespec-orchestrator-beads-fabro`, across FOUR merged PRs:
   **#599** (the proposal) → **#600** (over-broad safe-defaults scenario + the REQUIRED
   design-record citation) → **#601** (scope AI-fail auto-rework to the AI-dispositive
   modes; the `human-only` advisory carve-out). The `proposed_changes/` queue was
   verified EMPTY first. **INDEPENDENT FABLE REVIEW: 5 rounds, TEN blockers raised,
   all fixed.** Re-run a final Fable pass on the CURRENT file before the accept if you
   want a fresh NO-BLOCKERS verdict on record (the last verdict predates #601).
   **The review is what made this safe — do not skip it.** Its catches included: a
   misattributed design-record cross-reference the proposal would have RATIFIED; a
   dangling reference to the deleted heading that the driver's OWN drift-sweep grep
   hid (a broken exclusion filter — never trust a single sweep); the BREAKING console
   drain leg; and TWO instances of the same class of error — a blanket claim falsified
   by per-item labels (the safe-defaults scenario, and the `human-only` × AI-FAIL cell).
2. **NEXT — the maintainer's `/livespec:revise` ACCEPT** on topic
   `dispatcher-policy-settings` (spec ratification keeps its designed human gate;
   ONE decision, per-file, topic == file stem). Two things to confirm at accept
   time: (a) the `wip_cap` per-item exclusion (see the CORRECTION above); (b) the
   per-item-beats-global precedence INVERSION. The revise pass applies a
   FOUR-file change (`spec.md`, `constraints.md`, `contracts.md`, `scenarios.md`)
   plus the `../tests/heading-coverage.json` co-edit — the proposal spells out
   every edit, incl. the full drift sweep.
3. **File the impl epic + children** via the groom/capture consent seam (both
   repos, cross-repo-linked). MUST include the **3 BREAKING console legs** (below).
4. **Then re-run Stage-2 the CORRECT way** (from cont.11): a supervised dispatch
   that parks in `acceptance`, maintainer accepts via the TUI `c` valve.

### ⚠ BREAKING cross-repo legs the retirement creates (found by the Fable review)
Retiring `--mode autonomous` **breaks the live cockpit** unless the console changes
in lockstep. THREE `livespec-console-beads-fabro` legs, all must land with the
orchestrator change:
1. `factory.autonomous_mode_enable_requested` / `_disable_requested` commands →
   replaced by per-setting write commands.
2. **The factory-drain launcher argv (the breaking one).** The console drain passes
   `["--mode","autonomous"]` when armed (cont.11 LIVE-VERIFIED the argv). Once the
   Dispatcher drops the flag, argparse REJECTS it → **every armed drain lands
   `failed`.** The console MUST stop passing it (no per-run arming flag exists any
   more; the Dispatcher reads the `dispatcher.*` settings from `.livespec.jsonc`).
3. The TUI dangerous-arming confirm (type-the-repo-name) retires with the mode.

### STATE / REAP
- Core primary clean on master; orchestrator primary clean on master, CI green.
- Cockpit tmux `console-autonomous-mode` still running; autonomous DISARMED.
- Reap core worktree `docs-autonomous-mode-cont12-addendum` (this update) after its
  PR merges, and orchestrator worktree `spec-dispatcher-policy-settings` after
  PR #599 merges. cont.12's `docs-autonomous-mode-dispatcher-settings` already
  reaped (PR #1218 merged).
- **NEW side finding — the pin fan-out is STALLED.**
  `livespec-orchestrator-beads-fabro` has **11 stale open deps-bump PRs** (livespec
  v0.10.1→v0.11.1; dev-tooling v0.44.0→v0.46.1), and they ALL fail the SAME check:
  **`check-aggregate-completeness`**. Master CI is green, so this is not a broken
  master — but the orchestrator is receiving NO upstream releases. ONE conformance
  fix unblocks the entire queue. Recommend folding it into the epic.
- Side items from cont.11 (unchanged): `bd-ib-86k` parked in `acceptance`;
  `bd-ib-e0t`+`bd-ib-jz62h3` auto-closed on the stub (maintainer to decide
  keep/review/reverse); cockpit bugs to file in `livespec-console-beads-fabro`.

