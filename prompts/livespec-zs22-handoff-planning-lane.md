# Handoff: Formalize the livespec blessed workflow (epic livespec-zs22)

**Track:** planning-lane · **Epic:** `livespec-zs22` · **Tenant:** livespec

This is the resumable runbook for the Planning Lane + Conformance Pattern
formalization. It carries *instructions*; the *rationale* lives in
`research/planning-workflow-gap/planning-lane-design.md`, and the
*authoritative status* lives in the ledger — never in this file.

## FIRST ACTION — print live status (do not trust this file for status)

```
/data/projects/1password-env-wrapper/with-livespec-env.sh bd show livespec-zs22
```

Derive every "what's done / what's next" answer from that, plus
`bd ready` and `git log`. This file lists the *plan*, not the *state*.

## Read first

1. `research/planning-workflow-gap/planning-lane-design.md` — the design,
   the three planes, the locked decisions, the increment sequence, and the
   three FINAL diagrams (§"Architecture diagrams") ready to land in the spec.
2. `research/factory-conformance/cross-repo-conformance-pattern.md` — the
   companion Conformance Pattern (files its milestones through this lane).
3. `research/planning-workflow-gap/missing-planning-workflow-thread.md` —
   the original gap note.

## Objective

Re-adopt livespec's own deferred planning design as a codified, disciplined
convention, place each piece on the plane that owns it (Spec /
Orchestrator / Control), and mechanically enforce the no-shadow-ledger
rule — then build the Conformance Pattern on top of it. Locked decisions
(see the design doc): handoff skill **orchestrator-side**; **`baseline`**
profile (not "factory"); **`just` mandated non-functionally only** (never
in core's public functional surface); fleet pins track **latest RELEASE**
not HEAD; the **console** is the Control-Plane runner.

## Status (refreshed 2026-06-25, post-increment-2)

**Run this track autonomously.** Standing maintainer directive (2026-06-25):
own the cuts (file children, draft, execute, land per increment), gate only
on a genuine architectural/intent question, and hand off to a fresh session
when context approaches budget. This supersedes the design doc's
per-cut approval gate for this track.

Landed: increment 0 + design refinements (PRs #568, #572; `livespec-zs22.1`
closed). **Increment 1** (`livespec-zs22.2`, PR #575, cut `v137`): the
`## Workflow planes and the Planning Lane` framing + planes/skills diagrams
in `spec.md`, the Control Plane + `plan/<topic>/` store on the canonical
diagram, the `README` field-comparison section, and the `AGENTS.md` diagram
authoring conventions (`livespec-1bvl` closed). **Increment 2**
(`livespec-zs22.4`, PR #577, cut `v138`): the NON-normative
`#### Planning Lane guidance` block under `### Orchestrator plugin ecosystem`
in `non-functional-requirements.md`. Epic is **3/5 children complete**.

Open children: **`livespec-zs22.5`** (increment 3, filed) and
**`livespec-zs22.3`** (plan-skill self-sufficiency — the acceptance harness
for increment 3a). Increments 4-5 are design-doc-sequenced, filed as they
ripen.

## Next concrete action

**Increment 3 (`livespec-zs22.5`)** — realize the Planning Lane. Two
independently-mergeable parts (groom/split as 3a/3b; drive each as its own
PR per increment discipline):

- **3a — orchestrator `plan` skill** (repo `livespec-orchestrator-beads-fabro`):
  a heavyweight, stateful skill modeled on `groom`. Author
  `.claude-plugin/prose/plan.md` (single source) + thin bindings
  `.claude-plugin/skills/plan/SKILL.md` (Claude) and
  `.claude-plugin/.codex-plugin/skills/plan/SKILL.md` (Codex). API (design
  doc §"Refinements"): `plan` (no-arg) = interactive — list open threads
  (ledger + `plan/` dirs) to resume, OR describe a new thread → propose a
  canonical dash-cased slug (propose-change's canonicalization) → confirm →
  create `plan/<slug>/` + a ledger epic anchor; `plan <slug>` = strict, must
  match an existing `plan/<slug>/` or fail hard listing slugs (no
  create-on-typo). Each invocation updates reasoning, refreshes the handoff,
  routes ripe pieces (`propose-change` for spec, `capture-work-item` for
  ledger work), or archives on close. `allowed-tools` include `Write` (it
  mutates `plan/`). **`livespec-zs22.3`** (cold-open self-sufficiency test +
  one-path next-command) is 3a's acceptance harness — co-deliver.
- **3b — no-shadow-ledger hook DRY across both Drivers**
  (`livespec-driver-claude` + `livespec-driver-codex`, one cross-repo epic):
  single-source a shape-aware extension of the existing WARN-ONLY
  `warn-plan-persistence.sh` Stop hook (neutral body + thin per-runtime
  adapters), reconciling the two divergent footgun guards. Discharges the
  Plugin-resolution concern's first slice. Honor NFR §"Hook chaining" and
  §"Codex dogfooding constraints".

**Then increment 4** (console control-plane contract: a NEW NON-normative
orchestrator/console-Plane `####` block in core
`non-functional-requirements.md`, modeled on the Dispatcher/grooming guidance,
+ the EXISTING `livespec-console-beads-fabro/SPECIFICATION/spec.md` diagram
extended — mermaid both sides) and **increment 5** (Conformance Pattern — file
the M0-M6 epic from
`research/factory-conformance/cross-repo-conformance-pattern.md` once
increment 3 lands). See §"Recon" for the verified cross-repo facts.

## Recon — cross-repo facts for increments 3-5 (verified 2026-06-25)

Baked in so a fresh session does not re-run the survey. Verify before relying
(repos move; this is a snapshot).

**Driver repos (both exist; NOT DRY — the increment-3b gap).**

- `livespec-driver-claude`: skills at `.claude-plugin/skills/<name>/SKILL.md`;
  hooks at `.claude-plugin/hooks/hooks.json` (PreToolUse:Write →
  `block-auto-memory.sh`; Stop → `warn-plan-persistence.sh`) PLUS repo-scoped
  `.claude/settings.json` (PreToolUse:Bash guard +
  `.claude/hooks/livespec_footgun_guard.py`).
- `livespec-driver-codex`: skills at `livespec/skills/<name>/SKILL.md`; hooks at
  `livespec/hooks/hooks.json` wiring ONLY PreToolUse:Bash →
  `livespec_footgun_guard.py`. NO `.sh` hooks (no block-auto-memory, no
  warn-plan-persistence).
- The two footgun guards are NOT byte-identical (228 vs 365 lines) — the
  cross-Driver DRY defect. Mirror the orchestrator's `prose/<name>.md` +
  thin-binding single-sourcing and core NFR §"Codex dogfooding constraints".
- `warn-plan-persistence.sh` is the literal shape to extend for the
  no-shadow-ledger hook: a Stop hook, WARN-ONLY (emits a `systemMessage`, never
  a decision key, never non-zero, fail-open), scanning the last turn for a
  planning artifact written with no persisting/ledger call.

**Orchestrator (`livespec-orchestrator-beads-fabro`).** 9 skills under
`.claude-plugin/skills/`; prose for the 5 heavyweight ops under
`.claude-plugin/prose/`. NO `plan`/`handoff` skill, NO `plan/` or `prompts/`
dir yet. `groom` is the closest analogue (heavyweight, stateful, re-entered):
copy its `SKILL.md` frontmatter; `groom` is `allowed-tools: Bash, Read, Grep,
Glob`, `capture-work-item` adds `Write` — `plan` needs `Write` too.

**Console (`livespec-console-beads-fabro`).** EXISTS (Rust), full
`SPECIFICATION/` tree. Already control-plane content in `spec.md`:
owns/does-not-own lists (`/livespec:* spec mutation semantics` is in
does-not-own) + an existing mermaid diagram (Console/LiveSpec/Orchestrator
nodes). Increment 4 EXTENDS this, not greenfield; it also has a `prompts/`
dir with handoff files.

**Core NFR integration.** The zs22.4 Planning Lane guidance sits as a `####`
under `### Orchestrator plugin ecosystem`, sibling to `#### Orchestrator-internal
Dispatcher guidance` (the NON-normative template). Increment 4's core side uses
the SAME template. `just` is referenced piecemeal (`### Toolchain pins`,
`### Enforcement-suite invocation`, `### Developer-tooling layout`) but has NO
consolidated mandate — increment 5 lands the "`just` keystone" NFR mandate.
`### Hook chaining` constrains 3b.

**Conformance Pattern (increment 5) skeleton**
(`research/factory-conformance/cross-repo-conformance-pattern.md`). Five slots:
**Contract / Mechanism / Installer (`just` recipe) / Verifier (fail-closed, in
`just check`) / Exemption**. `baseline` profile (every governed repo) + additive
layers (`fleet-infra`, `orchestrator-plugin`, `app`); declarative `adopters`
manifest in `.livespec-fleet-manifest.jsonc` (`fleet`/`adopters` arrays, each
`profile` + `posture` = `released`/`pinned`/`none`). Four tiers: author-time
(copier) / commit-time (lefthook→`just check`) / dispatch-time (orchestrator
runs installer+verifier pre-dispatch) / fleet-time (`just conformance` + drift
CI). Named concerns: Plugin-resolution, Terminology-guard, Worktree-discipline,
No-shadow-ledger, Ledger-closure, Pin-freshness. Milestones M0-M6 (M3 dogfoods
on `livespec-console-beads-fabro`; M4 on Open Brain).

## Constraints / non-negotiables

- **Dogfood the discipline.** All work in a worktree under
  `~/.worktrees/livespec/<branch>`; land via PR → rebase-merge; never
  commit on the primary checkout. `mise exec -- git …`; never
  `--no-verify`; halt and report on any hook failure.
- **No shadow ledger.** This handoff and every artifact point at ledger
  ids for status; they never embed a `[ ]`/`[x]` task queue.
- **Respect the planes.** The handoff/coordination skill is
  orchestrator-side; the reasoning capture is a Spec-Plane convention; the
  console is the Control Plane. `just` never leaks into core's functional
  surface or the `/livespec:*` skills.
- **Increment discipline.** Small, cohesive, independently mergeable,
  nothing breaks. One increment per PR.

## Handoff refresh

If context approaches budget mid-increment: wrap the in-flight increment
to a committed+pushed state, update the ledger (`bd`), print the closing
status table, and refresh this file (same epic id) with the exact
remaining work. End every session by naming the literal next-session
command.

## Archive condition

When `livespec-zs22` closes (all increments landed, the Planning Lane
guidance in core NFR, the Conformance Pattern shipped), `git mv` this file
to `archive/prompts/` with a completion banner. The durable history then
lives in the spec, the spec history, the commits, and the ledger.
