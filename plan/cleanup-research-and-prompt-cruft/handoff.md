# Handoff — cleanup-research-and-prompt-cruft

The single resumable entry point for the fleet-wide cleanup of legacy
root-level `research/` and `prompts/` directories: still-active tracks
migrate to `plan/<topic>/` threads, completed/stale material archives
under each repo's top-level `archive/`, non-spec-referenced living
reference stays, and spec-referenced docs get absorbed into (or
de-referenced from) the spec then archived (confirmed D1). A fresh
session executes the next action from this file alone via the
read-first chain — no chat history required.

## For a fresh session — read first

- **What this is.** Cross-repo cleanup epic driven FROM livespec by an
  overseer session that does all repo work via separate agents in
  separate sessions/worktrees in the corresponding repos. Full
  inventory, scoping decisions D1–D3, per-item dispositions with
  evidence, and cross-repo hazards:
  `plan/cleanup-research-and-prompt-cruft/research/01-inventory.md` —
  read it before acting.
- **Epic anchor:** `livespec-ztepy5` (livespec tenant). Status is READ
  from the ledger, never from this file:
  ```bash
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-ztepy5
  ```
  Per-repo child work-items live in each TARGET repo's own tenant and
  cite `livespec-ztepy5` in their descriptions; list them per repo with
  the same wrapper pattern (`bd -C /data/projects/<repo> list`) —
  EXCEPT openbrain, an independent tenant whose commands run under ITS
  wrapper: `source /data/projects/openbrain/scripts/with-openbrain-env.sh
  bd -C /data/projects/openbrain list`. Any brief composed for openbrain
  must carry that wrapper, never the livespec one.
- **Dirty repos (work to do):** livespec,
  livespec-orchestrator-beads-fabro, livespec-console-beads-fabro,
  livespec-dev-tooling, openbrain (default branch `main`).
  **Clean repos (verify-only at Phase 5):** livespec-driver-claude,
  livespec-driver-codex, livespec-orchestrator-git-jsonl,
  livespec-runtime.
- **⚑ Golden rules.**
  - D1–D3 are CONFIRMED (Phase 0 closed 2026-07-03): D1 = prune + the
    SPEC-ABSORB rule (spec-referenced docs get a propose-change that
    inlines their content into the spec or removes the obsolete
    reference, THEN archive — revise strictly before or atomically
    with the move); D2 = retire the prompts/ convention fleet-wide;
    D3 = openbrain `PLAN/` out of scope. Full statements in the
    inventory's "Scoping decisions" section.
  - Every repo mutation runs the full worktree → PR → merge → cleanup
    protocol IN ITS OWN REPO (worktrees under
    `~/.worktrees/<repo>/<branch>`), `mise exec -- git …` so hooks
    fire, never `--no-verify`, never force-push a branch another
    session created. All changesets here are doc/file moves — zero
    product `.py` — so commits are `chore(...)`-subject and exempt from
    the Red-Green-Replay ritual.
  - Spec files are never raw-edited: a `SPECIFICATION/` change in any
    repo goes through that repo's propose-change → revise cycle.
  - Archive moves are `git mv` (history-preserving), inbound-reference
    updates land in the SAME PR as the move, and `just check` (or the
    repo's equivalent gate) must be green before merge.
  - A new `plan/<topic>/` thread created for a still-active track gets
    its own epic anchor in THAT repo's tenant via the capture-work-item
    operation, citing `livespec-ztepy5`; its handoff must pass the
    handoff self-sufficiency gate (cold-open reader + one path + no
    dangling reference).
  - Secrets are probe-only (`printenv NAME | wc -c`); never echo values.
  - Don't reap worktrees while dispatched agents are active; refresh
    each primary checkout to origin after its PR merges; end every repo
    on its main branch, clean.
  - The overseer rotates before ~50% context: refresh THIS file (state,
    in-flight agents, next action), print the resume command verbatim
    as the recap's last line.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan cleanup-research-and-prompt-cruft`

## The next action

**Run Phase 3 — per-repo execution (mutating).** Phases 0–2 closed
2026-07-03; every disposition is now CONFIRMED — each repo's 02 file
ends with a "Phase 2 verdicts" section that is authoritative over its
table. Zero unresolved MAINTAINER rows. Concretely:

1. Read epic status from the ledger (command above).
2. File one child work-item per dirty repo in that repo's OWN tenant
   via the capture-work-item operation (citing `livespec-ztepy5`);
   openbrain's filing runs under ITS wrapper.
3. Dispatch one mutating agent per repo (all five in parallel — the
   repos are file-disjoint), each brief composed from the "Per-repo
   agent brief template" below with that repo's FULL 02 file (table +
   corrections + verdicts + obligations) pinned verbatim. Sequencing
   inside the livespec and openbrain briefs: SPEC-ABSORB rows are
   propose-change → revise → `git mv`, never the move first.
4. As each repo's PR merges: refresh its primary checkout, verify the
   agent cleaned its worktree/branch, close its child work-item.

Then proceed to Phase 4/5 per the phase plan below.

## Phase plan

Phases run strictly in order; within Phase 1 and Phase 3 the per-repo
agents are independent (no shared files across repos) and run in
parallel.

- **Phase 0 — maintainer scoping confirmation. CLOSED 2026-07-03:**
  D1 confirmed MODIFIED (prune + spec-absorb rule), D2 confirmed
  (retire prompts/ convention), D3 confirmed (openbrain `PLAN/` out of
  scope) — verdicts recorded in the inventory's "Scoping decisions"
  section.
- **Phase 1 — per-repo disposition validation (read-only).** Dispatch
  one read-only agent per dirty repo (5 agents, parallel) to: re-run
  the survey sweep for its repo, verify every VERIFY row's evidence
  (git log --grep for the landing merge, spec history version, ledger
  state via the repo's own tenant), confirm the inbound-reference line
  numbers still hold, and return a finalized disposition table
  (ARCHIVE / PLAN-THREAD / STAYS / SPEC-ABSORB / MAINTAINER, with
  evidence strings).
  The overseer commits the returned tables as
  `plan/cleanup-research-and-prompt-cruft/research/02-dispositions-<repo>.md`
  in livespec via this thread's worktree → PR flow.
- **Phase 2 — maintainer checkpoint.** Walk every remaining MAINTAINER
  row with the maintainer, one item per turn, recommended disposition
  first (known queue from the inventory: livespec
  `dark-factory-operability/work-breakdown.md`, the
  `workflow-processes` reframing/mermaid docs,
  `prompts/livespec-overseer-startup.md`, and openbrain
  `ob1-fork-patches.md` — spec-referenced live registry, see its row
  for the three checkpoint options; plus whatever Phase 1 escalates).
  Record verdicts into the 02-dispositions files (same commit flow).
  Exit: zero MAINTAINER rows left.
- **Phase 3 — per-repo execution (mutating).** File one child
  work-item per dirty repo in that repo's OWN tenant via the
  capture-work-item operation (citing `livespec-ztepy5`), then dispatch
  one mutating agent per repo (parallel across repos; each agent stays
  inside its one repo and its one worktree/branch). Each agent executes
  its repo's 02-dispositions file: `git mv` ARCHIVE rows to
  `archive/research/<topic>/` / `archive/prompts/`, create PLAN-THREAD
  rows as proper threads (directory + handoff passing the
  self-sufficiency gate + epic anchor in that repo's tenant), execute
  SPEC-ABSORB rows in the load-bearing order — propose-change → revise
  (inline the content or remove the obsolete reference) → `git mv` to
  archive, never the move first — apply the D2 convention-doc edits,
  update every inbound reference in the same PR, run the repo's full
  gate green, open the PR, merge under the repo's merge discipline,
  refresh the primary checkout, clean up the worktree/branch, and close
  its child work-item. livespec's agent also carries the D2 spec
  sentence (§"No shadow ledger" naming `prompts/AGENTS.md`) through
  propose-change → revise, plus any heading-set change ripple
  (`tests/heading-coverage.json` co-edit discipline); openbrain's agent
  drives its SPEC-ABSORB revises through openbrain's own
  propose-change → revise cycle.
- **Phase 4 — livespec convention docs.** Whatever D2 doc updates are
  NOT already carried by Phase 3 agents (e.g. livespec
  `.ai/agent-disciplines.md` handoff-convention rewrite, the stale
  `archive/` description in the repo-layout table) land via one more
  livespec PR. May fold into livespec's Phase 3 PR if that agent takes
  it explicitly.
- **Phase 5 — fleet re-scan + close.** Re-run the inventory's survey
  sweep across all 9 repos (dirty ones now clean of ARCHIVE,
  PLAN-THREAD, and SPEC-ABSORB rows; the 4 clean repos still clean;
  STAYS rows intact and no spec reference pointing into them), run
  `/livespec:doctor` in the fleet repos touched, verify all child
  work-items closed, then close `livespec-ztepy5` and archive this
  thread (`git mv plan/cleanup-research-and-prompt-cruft/
  plan/archive/cleanup-research-and-prompt-cruft/` through the normal
  PR flow).

## Per-repo agent brief template

Compose each dispatch brief from these blocks plus the relevant
disposition table pinned VERBATIM (never "see the file" alone — pin the
rows into the brief and ALSO name the file). Which table depends on the
phase: **Phase 1 briefs pin the inventory's per-repo table plus the
corrected survey sweep** (the `02-dispositions-<repo>.md` files do not
exist yet — Phase 1 produces them); **Phase 3 briefs pin the finalized
`02-dispositions-<repo>.md` table**.

Common safety block (both phases):

> Work ONLY in <repo>. Never touch, push, or force-push any worktree or
> branch other than the one you create. Use `mise exec -- git …` for
> every commit/push so hooks run; NEVER pass `--no-verify`; if a hook
> fails, halt and report the failure verbatim. Secrets are probe-only
> (`printenv NAME | wc -c`). Do not run worktree reapers. Do not edit
> any `SPECIFICATION/` file directly — spec changes go through the
> repo's propose-change → revise cycle. Halt and report on any
> ambiguity instead of improvising.

Phase 1 (validation, read-only) adds:

> Read-only toward the repo: no commits, no worktrees, no ledger
> writes. Re-run the survey sweep for <repo>; for each VERIFY row find
> the concrete landing evidence (merge SHA via `git log --grep`,
> accepted spec history version, or ledger state via
> `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/<repo> list`);
> re-confirm inbound-reference file:line anchors; return a finalized
> markdown disposition table with an evidence column. Escalate a row to
> MAINTAINER only when evidence is genuinely absent or contradictory.

Phase 3 (execution, mutating) adds:

> Create `~/.worktrees/<repo>/<branch>` from the repo's default branch
> and do ALL edits there. Execute the pinned disposition table exactly:
> `git mv` each ARCHIVE row to its target, create each PLAN-THREAD as a
> proper `plan/<topic>/` (handoff passing the self-sufficiency gate;
> epic anchor filed in <repo>'s own tenant via capture-work-item,
> citing livespec-ztepy5), apply the pinned convention-doc edits,
> update every pinned inbound reference in the same changeset, run the
> repo's full gate (`just check` or documented equivalent) to green,
> commit with a `chore(...)` subject, push, open a PR, wait for
> required checks, merge under the repo's merge discipline, refresh the
> primary checkout to origin, remove your worktree and branch, and
> report: PR URL, merge SHA, gate output tail, and the final
> `git status` of the primary. If anything blocks, STOP and report —
> do not improvise dispositions not in your table.

## Sequencing notes

- Phase 3 repos are file-disjoint — dispatch all five in parallel.
  The only cross-repo text couplings (openbrain→livespec
  `beads-gaps-workarounds` mention; livespec ci.yml → dev-tooling
  `justcheck-performance`; dev-tooling `branch-protection.sh` →
  livespec `factory-conformance`) all point at STAYS rows under D1, so
  no ordering constraint exists. If Phase 2 turns any of those rows
  into ARCHIVE, sequence the citing repo AFTER the moving repo and add
  the reference retarget to the citing repo's brief.
- openbrain uses `main`, its own tenant prefix (`ob-*`), and its own
  credential wrapper (`with-openbrain-env.sh`) — the openbrain briefs
  must say so explicitly.
- Another active thread (`plan/fleet-plugin-currency/`) is running in
  livespec — do not touch its files, worktrees, or epic
  (`livespec-c1k9`).

## Session log

### Session 1 (2026-07-03) — thread opened

- Maintainer directive: clean root `research/`/`prompts/` cruft across
  the fleet + openbrain; active → `plan/<topic>/`, else → top-level
  `archive/`; structure for autonomous overseer driving; topic name
  fixed by the maintainer.
- Surveyed all 8 fleet repos + openbrain (committed state); found 5
  dirty repos, 4 clean; built the inbound-reference map; identified the
  load-bearing third category (spec-mandated, runtime-written, and
  cross-repo-referenced research docs) that motivated D1.
- Asked the maintainer the three scoping questions; no response after
  60s (away from keyboard) — adopted the recommended defaults as
  PROVISIONAL D1–D3 and gated all mutation behind Phase 0.
- Filed epic anchor `livespec-ztepy5` (livespec tenant; intake DoR
  verdict `needs-regroom`, correct for an epic anchor).
- Authored this thread scaffold (`research/01-inventory.md` +
  `handoff.md`) on branch `plan-cleanup-research-and-prompt-cruft`
  (worktree `~/.worktrees/livespec/plan-cleanup-research-and-prompt-cruft`),
  landed to master via the Session-1 scaffold PR — if you are reading
  this file on master, the scaffold landed and the worktree/branch were
  cleaned up; Phase 0's verdict edit starts a FRESH worktree/PR.
- Ran the handoff self-sufficiency gate: cold-open reader run #1
  returned FAIL with four findings (unrecorded scaffold git state, no
  explicit next-action section, `origin/master` hardcoded in the survey
  sweep false-greening openbrain, Phase 1 brief-pin ambiguity); all
  four repaired in this file + the inventory, then re-verified.

### Session 2 (2026-07-03) — Phase 0 closed

- Maintainer answered all three scoping questions (same calendar day,
  same overseer session as Session 1 after a picker-timeout gap).
- **D1 confirmed MODIFIED** — prune, PLUS the spec-absorb rule: no doc
  stays in `research/` on account of a SPEC reference; each
  spec-referenced doc gets a propose-change that inlines its content
  into the specification or removes the incorrect/obsolete reference,
  and archives once the revise lands. Docs referenced only by
  code/AGENTS.md and the runtime-written `lessons.md` keep the prune
  default. New SPEC-ABSORB disposition class added; rows reshaped:
  livespec `workflow-processes` mandated pair, openbrain
  `android-voice-path-decision.md`, openbrain `gmail-ingest-filter/`
  → SPEC-ABSORB; openbrain `ob1-fork-patches.md` → MAINTAINER
  (spec-referenced live registry — inlining mutable tracking state
  into a spec conflicts with "spec is for contracts, not tracking";
  three options queued for Phase 2).
- **D2 confirmed** — retire the root prompts/ handoff convention
  fleet-wide. **D3 confirmed** — openbrain `PLAN/` out of scope.
- Recorded the verdicts in the inventory (PROVISIONAL → CONFIRMED) and
  refreshed this handoff (next action now Phase 1).

### Session 2 continued (2026-07-03) — Phase 1 executed

- Dispatched the five read-only validation agents in parallel; all
  returned finalized tables, committed as
  `research/02-dispositions-<repo>.md`.
- Headline corrections the agents surfaced (details in each 02 file):
  - livespec: mermaid-handoff landing evidence corrected (v151
    lifecycle diagram, not v105); fleet-terminology prompts escalated
    to MAINTAINER (residual active-scope `family` occurrences, no
    committed classification inventory); `.claude/CLAUDE.md` is a
    symlink to `AGENTS.md` (cited double-anchors collapse to one);
    new inbound ref `templates/orchestrator-plugin/copier-questions.yml:75`
    → factory-conformance.
  - orchestrator: context-completeness resolved to ARCHIVE (epic
    `bd-ib-fqh` closed, merges `1485fb1`/`2fd4efd`); w7 relocation
    conflicts with the repo-local `research/archive/` convention
    ratified in its `research/CLAUDE.md` (escalated, rec relocate
    anyway); `pyproject.toml:319` = documentary
    `destructive_cli_allowlist` entry (non-behavioral path rewrite,
    keep the entry); fifth w7 ref found (`orchestrator-image/README.md:13`);
    `Dockerfile:5` path was ALREADY stale.
  - console: BOTH prompts handoffs → ARCHIVE — the active track's D2
    conversion already exists as the parked `plan/impl-dispatch/`
    thread (do NOT create a second); AGENTS.md anchor drifted 47→55;
    gate = `just check` (Rust aggregate).
  - dev-tooling: shell-logic-audit → PLAN-THREAD
    (`plan/shell-logic-hardening/`) anchored on EXISTING open epic
    `livespec-dev-tooling-9j8` (all 8 children BACKLOG);
    agent-instruction-inheritance ARCHIVE verified (v146 + merges).
  - openbrain: `ob1-inline-autonomous-factory.md` flipped
    ARCHIVE → STAYS (live code ref `scripts/promote.ts:6`);
    gmail-ingest-filter has a live tool coupling
    (`scripts/explore-gmail.ts` hard-codes the dir — tool retirement
    escalated); spec link at `contracts.md:663` characterized as
    provenance-only and stale (candidates JSON frozen at v3 vs
    normative inline v8) — the revise de-references, inlines nothing;
    applied-migration comments are immutable (never edit).
- Next action advanced to Phase 2 (maintainer checkpoint; queue in
  "The next action" above).

### Session 3 (2026-07-03) — Phase 2 closed

- Walked all 10 checkpoint items with the maintainer, one picker per
  turn. Nine confirmed as recommended; ONE override: the
  workflow-processes contract/reframing pair went **ARCHIVE + retarget
  README** (recommendation had been STAYS).
- Verdicts recorded as an authoritative "Phase 2 verdicts" section
  appended to each repo's 02 file. Highlights: livespec empties
  `prompts/` entirely (overseer-startup RELOCATES to
  `.claude/skills/overseer/`; terminology pair archives after ONE
  residual-`family` work-item is filed); the whole
  `research/workflow-processes/` tree leaves `research/` once the
  mandate-retirement revise lands; orchestrator relocates w7 +
  archives context-completeness; console archives both prompts files
  (plan/impl-dispatch/ is the conversion); openbrain records the
  ob1-fork-patches D1 exemption (registry = tracking state) and
  retires explore-gmail.ts with its directory.
- Post-execution `research/` residents (livespec): `CLAUDE.md`,
  `beads/`, `dark-factory-operability/{CLAUDE.md,preconditions.md}`,
  `factory-conformance/`, `planning-workflow-gap/`.
- Next action advanced to Phase 3 (per-repo mutating execution).
