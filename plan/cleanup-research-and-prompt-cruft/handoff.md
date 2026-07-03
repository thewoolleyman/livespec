# Handoff — cleanup-research-and-prompt-cruft

The single resumable entry point for the fleet-wide cleanup of legacy
root-level `research/` and `prompts/` directories: still-active tracks
migrate to `plan/<topic>/` threads, completed/stale material archives
under each repo's top-level `archive/`, load-bearing living reference
stays (provisional D1). A fresh session executes the next action from
this file alone via the read-first chain — no chat history required.

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
  - D1–D3 in the inventory are PROVISIONAL until Phase 0 confirms them
    with the maintainer. No repo mutation before Phase 0 closes.
  - Every repo mutation runs the full worktree → PR → merge → cleanup
    protocol IN ITS OWN REPO (worktrees under
    `~/.worktrees/<repo>/<branch>`), `mise exec -- git …` so hooks
    fire, never `--no-verify`, never force-push a branch another
    session created. All changesets here are doc/file moves — zero
    product `.py` — so commits are `chore(...)`-subject and exempt from
    the Red-Green-Replay ritual, EXCEPT any orchestrator code change
    (only if D1 flips) which is full TDD.
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

**Run Phase 0 — maintainer scoping confirmation.** Concretely:

1. Read epic status from the ledger (command above).
2. Present D1, then D2, then D3 from the inventory's "Scoping
   decisions" section via the structured picker — one question per
   turn, recommended default listed first, flip costs stated from the
   inventory's notes.
3. Record the verdicts by editing that section from PROVISIONAL to
   CONFIRMED (or re-scoped) and land the edit through this thread's
   normal worktree → PR flow.
4. If D1 flips to "eliminate": STOP and re-plan per the inventory's
   "Cross-repo coordination hazards" section before any further phase.

Then proceed to Phase 1 below.

## Phase plan

Phases run strictly in order; within Phase 1 and Phase 3 the per-repo
agents are independent (no shared files across repos) and run in
parallel.

- **Phase 0 — maintainer scoping confirmation.** Present D1–D3 from the
  inventory (recommended defaults first) via the structured picker, one
  question per turn. Record verdicts by editing the inventory's
  "Scoping decisions" section from PROVISIONAL to CONFIRMED (or
  re-scoping per its flip notes) through this thread's normal
  worktree → PR flow. If D1 flips to "eliminate", STOP and re-plan (the
  inventory's cross-repo hazards section enumerates what grows).
- **Phase 1 — per-repo disposition validation (read-only).** Dispatch
  one read-only agent per dirty repo (5 agents, parallel) to: re-run
  the survey sweep for its repo, verify every VERIFY row's evidence
  (git log --grep for the landing merge, spec history version, ledger
  state via the repo's own tenant), confirm the inbound-reference line
  numbers still hold, and return a finalized disposition table
  (ARCHIVE / PLAN-THREAD / STAYS / MAINTAINER, with evidence strings).
  The overseer commits the returned tables as
  `plan/cleanup-research-and-prompt-cruft/research/02-dispositions-<repo>.md`
  in livespec via this thread's worktree → PR flow.
- **Phase 2 — maintainer checkpoint.** Walk every remaining MAINTAINER
  row with the maintainer, one item per turn, recommended disposition
  first (known queue from the inventory: livespec
  `dark-factory-operability/work-breakdown.md`, the
  `workflow-processes` reframing/mermaid docs, and
  `prompts/livespec-overseer-startup.md`; plus whatever Phase 1
  escalates). Record verdicts into the 02-dispositions files (same
  commit flow). Exit: zero MAINTAINER rows left.
- **Phase 3 — per-repo execution (mutating).** File one child
  work-item per dirty repo in that repo's OWN tenant via the
  capture-work-item operation (citing `livespec-ztepy5`), then dispatch
  one mutating agent per repo (parallel across repos; each agent stays
  inside its one repo and its one worktree/branch). Each agent executes
  its repo's 02-dispositions file: `git mv` ARCHIVE rows to
  `archive/research/<topic>/` / `archive/prompts/`, create PLAN-THREAD
  rows as proper threads (directory + handoff passing the
  self-sufficiency gate + epic anchor in that repo's tenant), apply the
  D2 convention-doc edits, update every inbound reference in the same
  PR, run the repo's full gate green, open the PR, merge under the
  repo's merge discipline, refresh the primary checkout, clean up the
  worktree/branch, and close its child work-item. livespec's agent also
  carries the two spec-side pieces through propose-change → revise: the
  D2 sentence (§"No shadow ledger" naming `prompts/AGENTS.md`) and any
  heading-set change ripple (`tests/heading-coverage.json` co-edit
  discipline).
- **Phase 4 — livespec convention docs.** Whatever D2 doc updates are
  NOT already carried by Phase 3 agents (e.g. livespec
  `.ai/agent-disciplines.md` handoff-convention rewrite, the stale
  `archive/` description in the repo-layout table) land via one more
  livespec PR. May fold into livespec's Phase 3 PR if that agent takes
  it explicitly.
- **Phase 5 — fleet re-scan + close.** Re-run the inventory's survey
  sweep across all 9 repos (dirty ones now clean of ARCHIVE/PLAN-THREAD
  rows; the 4 clean repos still clean; STAYS rows intact), run
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
