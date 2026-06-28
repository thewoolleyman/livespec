# Prior art — the external grounding for the work-item state machine

This note records the external sources that ground the design in
`02-design.md`. It is reference material captured during the design
session; every non-trivial claim carries its source. The verbatim
research passes that produced it are preserved under
`../conversation/transcript.md`.

The one-line thesis it supports: **livespec is already ~70% of a
Gas Town** (it stands on the same Beads/Dolt ledger), and the missing
30% — an explicit lane state machine, a capacity governor (WIP), a
human-acceptance gate, and tiered cheap-determinism supervision — is
exactly what this design adds.

---

## 1. Nate B. Jones — "Open Engine" (the task-record + receipts model)

Source: "Stop being the integration layer for your AIs" / "Grab the
Open Engine guide" (natesnewsletter.substack.com/p/ai-agent-handoffs,
2026-06-26), read in full via the Nate B. Jones Executive Circle MCP,
plus the "Every Agent Needs an Owner" prompt kit.

The thesis: once agents can *act*, the hard problem is no longer "can
the agent do it" but **"can the work survive the trip to the next
tool"** — and the human is the integration layer doing the handoffs by
hand. The fix is a **shared task record**, not a smarter model: "What
they share is the task record, not the model."

Pieces that map directly onto this design:

- **The seven-part task record:** requester/owner, desired outcome,
  sources, acceptance criteria, boundaries (ask-first list), blocker
  rule, receipt. → our `WorkItem` fields + `owner` + the acceptance
  gate + the admission/acceptance policies.
- **The receipt vocabulary** ("the minimum language of trust"):
  `AGENT CLAIMED / BLOCKED / HUMAN HOLD / RESUMED / DONE / FAILED`. →
  our named transitions over the state machine. He explicitly splits
  **`AGENT BLOCKED`** (needs a *fact that belongs on the task*) from
  **`AGENT HUMAN HOLD`** (needs the *owner's* approval) — our
  `blocked_reason` split.
- **The statuses:** `Standing → Agent Todo → Agent Working →
  Agent Needs Input → Agent Review → Agent Done`, where **`Agent Review`
  is "the honest middle"** — scoped work done, a human must inspect.
  This is the seed of our **`acceptance`** lane (renamed away from
  "review" to avoid conflating with Fabro's internal LLM review).
- **The anti-stall law:** "a blocked task is a *pause*, not a terminal
  state; `AGENT RESUMED` is the only thing between a paused task and a
  dead one." → exactly the overseer's failure mode, now backed by state.
- **WIP discipline:** "process one task per run, keep failures small."
- **Ownership** (the prompt kit): every agent/work-unit needs exactly
  **one accountable owner**, conservative-by-default (read/draft-only)
  permissions, explicit pause/retirement conditions. → our required
  `owner` and safe-by-default policies.
- **Field placement:** the closest corollary he names is **Symphony**
  (OpenAI's open-source Codex orchestration spec — "issue trackers as
  control planes for always-on coding agents"), which is the
  Beads-as-control-plane thesis.

## 2. Gas Town — Steve Yegge's agent factory (the closest reference architecture)

Sources: Yegge, "Welcome to Gas Town" (steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04,
2026-01-01); the Gas Town and Beads READMEs (github.com/gastownhall/gastown,
github.com/gastownhall/beads); DoltHub "A Day in Gas Town"
(dolthub.com/blog/2026-01-15-a-day-in-gas-town/).

Gas Town is Yegge's own open-source multi-agent orchestration system,
and **Beads is also Yegge's project** — so livespec stands on Yegge's
ledger, and Gas Town is the nearest existing architecture to what we
are building.

Spine: `Mayor decomposes a request → beads → Convoy → sling to a Hook →
atomic claim (assignee + in_progress) → molecule steps → gt done →
Refinery merges`. The same shape as livespec's `plan → epic → ready →
Dispatcher → Fabro → janitor gate → merge`.

What Gas Town has that the livespec overseer lacks — i.e. what this
design adds:

| Gas Town | livespec today | this design adds |
|---|---|---|
| `scheduler.max_polecats` — a capacity governor **decoupled from dispatch** | nothing (per-wave `--budget`/`--parallel` only) | the **WIP cap** |
| explicit **Hook state machine** `Created→Active→Suspended→Active→Completed→Archived` | a bash `PARKED=()` table + prose comments in the overseer | the **lane state machine** |
| **tiered supervision**: a deterministic Go daemon (3-min heartbeat) → AI triage (Boot) → cross-rig patrol (Deacon) → human | one Opus-1M session md5-hashing tmux panes | **cheap determinism low** (console = the daemon tier) |
| **two human channels**: severity-routed `gt escalate` beads vs. a health classifier (`GUPP Violation/Stalled/Zombie/Working/Idle`) | one AI deciding ad hoc | the **needs-decision vs. needs-poke** split |
| **Refinery** — a bisecting merge queue; "polecats never push directly to main" | factory self-merges on green | the **`acceptance` gate** |

Transferable lessons (Yegge's own framing, distilled):

1. **Externalize the state machine into a durable, dependency-aware
   ledger, not agent memory.** "Ready" is *derived* ("no open
   blockers"); atomic claim prevents double-dispatch.
2. **Decouple a capacity governor from dispatch** — one WIP knob,
   default-unlimited with an opt-in cap.
3. **Make resumption idempotent** via a propulsion invariant + a
   per-agent inbox (GUPP: "if there is work on your hook, run it").
4. **Tier the supervision; spend cheap determinism low, AI/human
   high.** A deterministic heartbeat escalates to AI triage, then a
   human, with explicit health-state classification.
5. **Separate "blocked, needs decision" from "unhealthy, needs poke,"
   and keep the human gate at the merge boundary.**

Cautionary data point: DoltHub's Tim Sehn **closed Gas Town** after it
autonomously merged PRs unattended — the strongest argument for keeping
the `acceptance` gate (an *un-gated* release valve is the dangerous one).

## 3. WIP limits / pull systems (the capacity-governor theory)

Sources: getnave.com/blog/introducing-wip-limits/,
learnleansigma.com/lean-manufacturing/wip-limits-explained/ and
.../littles-law-explained-formula/, kanbanzone.com/resources/lean/littles-law/.

- A **WIP limit** caps concurrent items per lane; when hit, no new work
  is pulled — forcing "**stop starting, start finishing**" and making
  the bottleneck visible (work piles in front of the constraint).
- **Little's Law:** `Lead Time = WIP / Throughput`. At roughly stable
  throughput, lead time falls *linearly* with WIP — so a WIP cap is a
  cycle-time control, not just tidiness.
- A **pull** system takes work only when it has free capacity; a
  **push** system injects on a schedule regardless. The Dispatcher must
  be pull (free a slot → pull the next eligible item).

## 4. Linear's category/status model (the two-level lane pattern)

Source: linear.app/docs/configuring-workflows, .../triage, .../conceptual-model.

Linear groups every status into a small fixed set of **categories**
(Backlog, Unstarted/Todo, Started/In Progress, Completed/Done,
Canceled), and lets teams add custom **statuses inside** a category
(Linear's own team runs `In Progress`, `In Review`, `Ready to Merge`
inside the Started category). The **category** is the small,
machine-meaningful axis automation keys off; the **status** is the
customizable human label.

Our realization of this pattern: the small machine-meaningful axis is
the **abstract `WorkItemStatus`** (livespec's own ubiquitous vocabulary);
a backend (Beads) maps it onto whatever native primitive it has. We do
**not** get Linear-style customizable statuses (Beads' enum is fixed) —
so the "finer layer" is structured fields/labels, not custom statuses.

## 5. Agentic "factory" work-state models — and the gap we fill

Sources: Devin API (docs.devin.ai/api-reference/sessions/*),
OpenHands SDK (github.com/OpenHands/software-agent-sdk … conversation/state.py),
Factory.ai (factory.ai/news/software-factory).

- **Devin:** session `status_enum` `working/blocked/expired/finished`,
  with `waiting_for_user` vs `waiting_for_approval` sub-states.
- **OpenHands:** `IDLE/RUNNING/PAUSED/WAITING_FOR_CONFIRMATION/FINISHED/ERROR/STUCK`.
- **Factory.ai:** no per-task state enum — a graduated **autonomy**
  spectrum (approve-every-change → low → medium → high → async) gates
  human involvement; phase model Spec→Test→Implement→Verify→Complete.

**The differentiating finding:** *none* of these cleanly separates
(a) "blocked, needs a human" from (b) "blocked on infra/external/
non-human" from (c) "claimed done, awaiting human acceptance." They
collapse all of it into one generic `blocked` or a terminal `done`.
**That three-way split — our `blocked_reason` {needs-human,
infra-external, dependency} plus the `acceptance` gate — is the gap this
design fills.** (Factory.ai's graduated autonomy is the closest analog
to our per-item, human-delegable admission/acceptance policies.)
