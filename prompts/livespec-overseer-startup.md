# Overseer startup — final wrap-up: close the tail, then groom M2

Run this to drive the **final wrap-up** of the livespec `zs22` work in the
`livespec-overseer` tmux session. The large epics are CLOSED; this session
**closes a small, enumerated punch-list of remaining open items, then walks the
maintainer through grooming the next milestone (M2)** — one clean decision at a
time. Load and follow the local overseer skill at
`.claude/skills/overseer/SKILL.md` (invoke `/overseer`); everything below is the
concrete punch-list + how to run it.

## Prime law (do not violate)

**Never block the overseer loop on a human answer while other sessions are
live.** Decide-and-inform over ask-and-wait; make every other track
self-sustaining before surfacing any unavoidable gate.

## Maintainer interaction style (learned 2026-06-27 — hold to it)

- **One clear, CLICKABLE choice at a time** (`AskUserQuestion`), in plain
  language, no jargon. Lead with a recommended option. Define every domain term
  inside the question.
- **Never** dump a prose wall of decisions. Walk the maintainer through items
  one by one.
- The maintainer is not a Python/infra expert — say the plain-language bottom
  line first, then detail.

## Baseline — already DONE this prior session (do NOT redo)

- The **`zs22` epic family is CLOSED**: the dev-tooling single-source
  convergence (`zs22.7.9`), the Conformance Pattern (`zs22.7`), and the
  blessed-workflow parent (`zs22`).
- Both maintainer decisions landed + closed: **`i05g` = Option B** (bump-pin
  gates on each consumer's own CI) and **`7a4e` = full coverage** (worktree-pack
  delivered to beads-fabro + console). Follow-ups `jzpx` + `usd3` merged.
- Fleet is on **dt v0.28.1**; all 6 repo primaries clean on master.

## The punch-list (this session's ENTIRE scope)

### A — close the done-but-open loose ends (autonomous: verify + close)

1. **`livespec-2exa`** (P1) — the plugin_structure regression. Fix already
   relocated + released; the fleet is healthy on it. Verify (no canonical-check
   breakage on core/orchestrators), then CLOSE the work-item.
2. **`livespec-2rab`** (P1) — the fan-out discover-siblings `jq` bug. Its note
   says **"dev-tooling side: FIXED + VERIFIED."** Check whether the consumer
   caller workflows (`release-dispatch.yml` / `bump-pin-from-dispatch.yml` /
   `pin-freshness.yml`) are still pinned at the stale `@v0.17.0` reusable-workflow
   tag; bump to current fleet-wide if so, then CLOSE.

### B — implement the deferred follow-ups, then close

3. **`livespec-dev-tooling-04g`** (P3) — subagent-stop-guard false-blocks a clean
   sub-agent on a SIBLING's in-flight worktree. Implement "scope by **creator**
   (worktrees this agent created), not transcript-**mention**"; preserve the
   `_MAX_BLOCKS_PER_SESSION=3` cap. The hook lives in the **dev-tooling** tenant;
   xref `dev-tooling-7us.2`.
4. **`livespec-n70w`** (P2) — doctor-static `no_cross_spec_reference` blind spot:
   a cross-repo citation that collides with a same-named LOCAL heading resolves
   silently. Repo-qualify + resolve against the cited repo so it fails loudly.
5. **`livespec-vtxt`** (P3) — doctor-static `no_spec_section_citation_in_code`
   doesn't scan Rust (`crates/**/src/*.rs`). Extend the scanned-source set
   (generalize the language set).
6. **`livespec-dev-tooling-23n`** — `wire_fleet_member`/reconcile reads
   `APP_ID`/`APP_PRIVATE_KEY` but the livespec env projects
   `GITHUB_APP_ID`/`GITHUB_PRIVATE_KEY`. Reconcile so the next fleet member's
   wiring is friction-free.

### C — groom the next milestone (MAINTAINER-GATED, interactive)

7. **M2 groom (`zs22.8`)** — the governed-repo-lifecycle epic. M1 is closed;
   **M2–M6 are not filed yet** ("child milestones are filed as they ripen — the
   maintainer owns the cut"). Run the grooming conversation
   (`/livespec-orchestrator-beads-fabro:groom`, or the standing handoff
   `prompts/governed-repo-lifecycle-handoff.md`) to cut **M2** into ready,
   dependency-ordered work-items. **The maintainer OWNS the cut** — draft,
   present one piece at a time, file ONLY on approval.

## How to run it (the walk-through contract)

1. Enumerate any warm track sessions (`command tmux ls`); reuse `livespec1`-`5`
   for dispatched work, name new ones `livespec6`+.
2. **FIRST — the autonomous tail (A + B):** dispatch items 1–6. They need NO
   maintainer decision — just inform as each lands. Fan out the non-conflicting
   ones in parallel (2exa/2rab are dev-tooling-fan-out; 04g is a dev-tooling hook;
   n70w/vtxt are core doctor-static; 23n is dev-tooling tooling — brief each
   sub-agent: own worktree only, never `--no-verify`, halt+report on hook
   failure). Verify each closes in the ledger.
3. **THEN — M2 (item 7):** walk the maintainer through grooming **one clean
   `AskUserQuestion` at a time**. They own every cut/file decision.
4. **Surface to the maintainer ONLY:** the M2 cut approvals, a genuine
   architectural/contract decision, or an unauthorized destructive op. Everything
   else is decide-and-inform.
5. **House rules:** repo mutations go `worktree → PR → rebase-merge`; never commit
   on a primary; never `--no-verify`; beads via
   `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec <args>`;
   scratch under `tmp/overseer/`.

## Explicitly OUT of scope (do NOT pull in unless the maintainer asks)

The broader pre-existing fleet backlog — ~12 other open items not from the
convergence work: `gcp2` (fleet-wide red-green-replay), `4dzbcv` (manifest
rename), `yc8e`, `4moata`, `mutreal*` (mutation testing), `9msu`, `qtjd`,
`i6rc`, `kvzt`, `h3e7`, `1t17`, `aava`, `0jxs`, etc. These are a separate,
larger backlog-triage — note they exist; leave them for a future session.

## Cold-start / crash recovery

Durable state is the **ledger** (the punch-list above is `bd ready` /
`bd list`) plus this prompt. After a crash: confirm the ledger is reachable
(`source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec list`),
`git status` clean on master, reap merged worktrees (`git worktree list`), then
re-run this prompt — the punch-list re-derives from the ledger.
