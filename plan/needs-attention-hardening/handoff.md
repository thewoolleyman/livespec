# needs-attention-hardening — LIVING plan thread HANDOFF (resumable entry point)

**Purpose:** drove the unaddressed follow-ups from the just-closed `needs-attention`
rollout (`livespec-bj9x`, CLOSED) plus newly-surfaced cross-runtime / cross-repo
skill-correctness problems, until the `needs-attention` surface was
**dogfood-proven** on BOTH runtimes (Claude + Codex) across the entire SHIPPED
repo-class matrix. **That shipped-surface mission is now COMPLETE (2026-07-08)**
(see STATUS below); the thread STAYS OPEN as the living home for the three
prose-linked carry-over follow-ups. This doc is the single resumable entry point —
a fresh session should be able to execute the NEXT ACTION below from this file alone
(via the read-first chain), no chat history required.

Repo: `thewoolleyman/livespec` (host checkout `/data/projects/livespec`).
Ledger via the wrapper: `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C <repo> ...`.

## Ledger anchors (read status LIVE — never trust a status written here)

- **Epic:** `livespec-yes5` (livespec core tenant) — the LIVING
  needs-attention-hardening thread anchor.
- **Anchor slice:** `livespec-3wh4` (child of `yes5`) — needs-attention must
  behave correctly on both runtimes across all fleet + adopter repos.
- Read live (status is DERIVED from the ledger, never stored in this file):
  ```sh
  source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show livespec-yes5
  ```
  and the ranked next impl-side action:
  ```
  /livespec-orchestrator-beads-fabro:next
  ```

## This is the LIVING needs-attention thread — do NOT archive it early

Maintainer-declared (2026-07-08): this thread STAYS OPEN until the `needs-attention`
surface is **dogfood-proven** on BOTH runtimes (Claude + Codex) across ALL fleet
members AND adopters. Do **not** archive it at the first epic-close. Lesson from
the prior thread: `plan/needs-attention/` was archived at the `livespec-bj9x`
exit-gate (→ `plan/archive/needs-attention/`, the historical rollout record) and
that was **premature** — dogfooding then surfaced real defects (the spec-`next`
pointer; the Codex-in-`livespec-runtime` wrapper confusion). So: archive ONLY when
dogfooding across the full runtime × repo matrix passes, not merely when an epic's
slices merge. The archived rollout thread is reference-only; THIS is where the
continued work lives.

---

## Orchestration discipline (RE-ASSERT in EVERY handoff refresh for this track)

Maintainer-directed (2026-07-08): do **NOT** serialize this track's work inline in
one session, and do not hand-run heavy work that a sub-agent or the factory should
carry. Operate in orchestration mode, and **carry this section forward verbatim
into every handoff refresh for this track**:

- **Parallelize through the factory.** Dispatch every pre-authorized, independent,
  non-conflicting `ready` work-item in parallel via the Dispatcher / the `drive`
  operation — across ALL unblocked tracks, not only this one. Never hand-crank one
  item while other ready work sits idle. Take a ready-work census each session
  (`bd -C /data/projects/<tenant> list` per tenant; e.g. at 2026-07-08
  `livespec-orchestrator-beads-fabro` had `bd-ib-mwz/cur/h55/9ch/v5n` ready and
  core/runtime/console had ready items too).
- **Delegate heavy work to sub-agents.** Keep the MAIN session for
  plan / dispatch / synthesis; delegate reproduction, investigation, multi-file
  authoring, and implementation to scoped sub-agents (or a parallel Workflow) with
  self-contained briefs (forbid `--no-verify`; halt + report on hook failure).
  Do NOT run the heavy lifting inline.
- **Sequence only genuine conflicts** (work-items overlapping the same files). A
  "pause" means "start a new session," not "confirm every step."
- **Move the track; gate ONLY genuine blockers — never freeze the loop to ask a
  non-blocker.** (Maintainer-directed 2026-07-08, after a session halted ALL work
  to ask permission for a fix whose slicing the investigation had already pinned to
  exact files/functions.) DECIDE-AND-INFORM on anything clear, reversible, or
  within established intent: file the obvious slices, dispatch ready work, extend a
  batch authorization the maintainer already granted, dispose a flagged side-issue.
  A groom cut whose slicing is **unambiguous** is mechanical execution, NOT a
  maintainer-owned gate — file it and dispatch, then report what you did. Reserve
  gates for GENUINE blockers ONLY: the FIRST accept-on-behalf authorization of a
  campaign, spec ratification, irreversible/outward-facing actions not pre-
  authorized, an **ambiguous** cut where the slicing is a real judgment call, and
  the exit gate. Litmus test before surfacing anything: "is it irreversible AND not
  clearly what they want?" — if no, do it and inform. When one track genuinely
  needs a gate, keep the OTHER tracks moving; never stop the whole loop on it.
- **Print the status table every 15 minutes (maintainer-directed 2026-07-08).**
  While coordinating, run a recurring 15-minute status tick that prints the
  `Epic · Track · Status · %Complete` table (read LIVE from the ledger + drain
  session panes) for every watched track, with a one-line note under it for any
  stall/blocker/completion. Set it up with `/loop 15m <status-tick prompt>` (which
  schedules a `3,18,33,48 * * * *` cron — offset off the :00/:30 marks). This cron
  is **session-only**, so **a fresh overseer session/rotation MUST re-establish it**
  as its first coordination act (this is why it is codified here, not just in a live
  session).

## STATUS — CORE MISSION COMPLETE (2026-07-08)

The `needs-attention` surface is **dogfood-proven on BOTH runtimes (Claude + Codex) across the entire SHIPPED repo-class matrix** — core, runtime library, driver plugin, both orchestrators, console, openbrain, resume. Anchor slice `livespec-3wh4` is **CLOSED** (full per-column evidence in its ledger comments). Epic `livespec-yes5` is 1/1 and **stays OPEN as the LIVING thread** for the follow-ups below.

**What landed (do NOT redo):**
- Both credential-fail-soft fix halves: RT `livespec-runtime-2y1` (v0.9.2) + OR `bd-ib-0s7` (orchestrator v0.13.7, PR #370). Under the DEFAULT Codex sandbox, `needs-attention` now fails SOFT with a clean actionable message instead of a raw `sudo` dump.
- Codex + Claude matrix columns swept CLEAN for the shipped surface. Attack #5 (no `spec:next` pointer) holds everywhere; attack #7 (`internal:` id rejection) is latent/not-manifested.
- The one defect found — the local `needs-attention-fleet` skill hardcoded the fleet credential wrapper, silently dropping independent-tenant `openbrain` — FIXED + live-verified + merged (PR #941).

**CARVE-OUT (documented, deliberately deferred):** the two git-jsonl Codex cells (git-jsonl-orchestrator × Codex + `resume` × Codex) are NOT proven — git-jsonl ships no `.codex-plugin` skill packaging. This is a git-jsonl PACKAGING prerequisite, not a `needs-attention` behavior gap. The full-peer packaging epic `livespec-xfqd` was **DROPPED** (2026-07-08) as duplicative of / superseded by `plan/make-git-jsonl-real/` in the `livespec-orchestrator-git-jsonl` repo — which delivers git-jsonl's functional drive-loop/executor but NOT its Codex skill packaging. If git-jsonl later gains Codex skill packaging, re-verify + retro-journal these 2 cells against the closed `livespec-3wh4`.

## REMAINING (yes5 living scope) — needs maintainer promote/groom

Three prose-linked carry-over follow-ups, all in backlog (each needs a maintainer promotion/groom to advance — the overseer surfaces, the maintainer runs the command in the owning repo):
- `livespec-runtime-dnu` (runtime tenant, P3 bug) — `validate_attention_item_id` rejects the `internal:` prefix. CONFIRMED latent/not-manifested under the shipped local skills (they never validate an `internal:` id) — real but not urgent.
- `livespec-console-beads-fabro-fpo` (console tenant, P2 bug) — `work_item stream_seq` u64→SQLite signed overflow; apply the 63-bit mask.
- `livespec-console-beads-fabro-ipi` (console tenant, P3 task) — migrate the console TUI render path from lane-derived to the `attention_item.*` stream.

NEXT ACTION: surface each follow-up for maintainer promotion (one at a time), or the maintainer routes them. There is no ready impl work to dispatch on this track until one is promoted.

## Read-first chain (open these, in order, before acting)

1. **THIS handoff.**
2. `plan/needs-attention-hardening/live-adversarial-review-prompt.md` — the dogfood
   matrix table (repo class × runtime × expected behavior) and the 12 attack points
   for an independent live reviewer.
3. **The ledger epic `livespec-yes5`** (live via the wrapper) + the ranked
   `/livespec-orchestrator-beads-fabro:next`.
4. The `livespec-runtime-ego` fix as the cross-plane resolver reference —
   beads-fabro PR #357 (`c39ed041`) + git-jsonl PR #202 (`d25e525`) / release #203
   (`1514739`).

---

## What is DONE (context — do NOT redo)

- **Kickoff FIRST ACTIONS (2026-07-08): DONE.** Headline anchor slice
  `livespec-3wh4` filed (core tenant) + epic `livespec-yes5` anchored + all three
  already-filed cross-tenant carry-overs (`-ipi`, `-fpo`, `-dnu`) back-linked to
  `yes5`. Scope boundary vs `livespec-xfqd` confirmed (correctness HERE;
  surface/packaging parity in `xfqd`).
- **`livespec-bj9x` (needs-attention rollout): CLOSED.** All 12 slices landed +
  adversarial-reviewed + accepted. Notably the F1 reaper default-branch destructive
  regression (CO1) was fixed at the root: `livespec-runtime` **v0.9.1** (PR #142)
  guard in the shared `_stale_worktree_finding` + `livespec` core **v0.7.1**
  (PR #922) belt-and-suspenders reaper action-layer skip + regression test. Prior
  rollout plan thread archived to `plan/archive/needs-attention/`.
- **`livespec-runtime-ego` (spec-next pointer defect): CLOSED, fixed in BOTH
  orchestrators.** `needs-attention` now invokes spec-`next` cross-plane behind an
  injectable `SpecNextSeam`, adapts the top ripe candidate (or nothing), fail-soft
  — no pointer. beads-fabro **v0.13.1** (PR #357, `c39ed041`); git-jsonl **v0.5.1**
  (PR #202 `d25e525` + release #203, `1514739`). Verified in the live console Codex
  pane (no `spec:next` pointer). The cross-plane CORE-CLI resolver (3 tiers) is the
  reference for the anchor-slice work above.

## CARRY-OVER FOLLOW-UPS (routing status per item)

**needs-attention residuals (filed, backlog; back-linked to `yes5`):**
- `livespec-console-beads-fabro-ipi` — migrate the console **TUI render path**
  from lane-derived to the `attention_item.*` stream. Task.
- `livespec-console-beads-fabro-fpo` — pre-existing `work_item` `stream_seq`
  `u64`→SQLite signed-int overflow; apply the same 63-bit mask CN1 used. Bug.
- `livespec-runtime-dnu` — `validate_attention_item_id` REJECTS the `internal:`
  id prefix although `kind="internal"` is first-class; add `internal` to
  `_THREE_PART_PREFIXES` in `livespec_runtime/attention_item.py` + test. Bug.

**Fleet skill/doc audit (folded into the anchor slice `livespec-3wh4`):**
- **`needs-attention-internal` + `-fleet` local skills** (livespec core,
  `.claude/skills/`, unsynced): the `dnu` id-prefix issue above is their one known
  seam. Re-audit them under Codex as part of the anchor-slice cross-runtime audit.

**Reassigned OUT of this epic (2026-07-08):**
- **git-jsonl skill-count drift** — REASSIGNED to `livespec-xfqd`
  (orchestrator-surface-parity), NOT filed under `yes5`. It is a surface/count
  matter (how many skills exist + are documented across git-jsonl's
  README/contracts/constraints), owned by `xfqd` **P2** (mechanical
  skill-set-consistency check) + **P4** (git-jsonl spec supersede, 8→12 full peer)
  per the confirmed scope split. Reconciling the count under `yes5` would duplicate
  and be obsoleted by xfqd's 8→12 rewrite. The specifics (README self-contradiction
  "10-skill" vs "Seven"; contracts "seven-skill surface") are recorded on the
  `xfqd` epic + `plan/orchestrator-surface-parity/research/design.md` §"Slice plan
  (6)" P4.

**Factory robustness (coordinate with the SEPARATE `livespec-nrdk` epic — do NOT
re-drive nrdk from this track, but these block clean factory completion):**
- **Fabro 60-min token TTL** — the fleet Fabro GitHub-App installation token has a
  hard 60-min TTL, minted once at dispatch, no per-node refresh; ANY factory run
  >~60 min fails at push with `Invalid username or token`. Durable fix =
  JIT-refresh the token at the push node. Tracked as a candidate slice on
  `livespec-nrdk`. Fabro fork PR **#552** (upstream `fabro-sh/fabro`, OPEN) is a
  checkpoint-COMMIT-timeout config and is **NOT** the token fix (verified).
- **`bd-gj-9sj`** — a fresh `git worktree add` does not hydrate the gitignored
  worktree-pack (`branch-protection.sh` + `.just` fragments), so a fresh janitor
  worktree fails `just check` on branch-protection until `just install-worktree-pack`.
  Blocks CLEAN git-jsonl factory completion. Candidate: auto-hydrate on worktree
  creation (related `livespec-qtjd`).

## Separate open tracks (NOT this epic — listed so they aren't forgotten)

- `livespec-nrdk` — factory-safe-by-default (factory-safe default + machine-readable
  `not-factory-safe:<reason>` admission gate + capability widening + host-only
  needs-attention lane). Carries the token-TTL fix.
- `livespec-xfqd` — orchestrator-surface-parity: **DROPPED/CLOSED 2026-07-08** as duplicative of `plan/make-git-jsonl-real/` (in the `livespec-orchestrator-git-jsonl` repo). The P1 core-spec proposal was withdrawn unratified (PR #945); the epic + slice `livespec-xfqd.1` are closed. Its non-duplicate residue (P5/P6 description conventions + the git-jsonl skill-count drift) is recorded in the epic's close reason if it needs re-homing.

## Standing disciplines (apply throughout)

- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; NEVER
  `--no-verify`; product `.py` uses the Red-Green-Replay ritual (the hook runs
  pytest against the **on-disk** module — at Red the impl must be the
  pre-change/pointer version on disk; move the fix aside, stage the test alone).
- Injectable seams (mirror `livespec_runtime.github_auth.MintSeams`) for any I/O
  that would otherwise need a hermetic `~/.codex`/`~/.claude` — unit-test tier
  logic with tmp dirs, never HOME monkeypatching.
- Independent adversarial (Fable) review before any spec ratification; verify
  sub-agent claims (static facts + your own live re-run), don't trust
  self-summaries.
- Codex plugin resolution is HOST-WIDE (`~/.codex`, `ref=release`); to see a fix
  in a running Codex TUI you must merge → release → `codex plugin marketplace
  upgrade <name>` → **restart the TUI** (`codex resume <id>`) so it reloads the
  installed cache (a running session caches the old version and its skill-load
  breaks when the cache is replaced).
- Secrets probe-only (`printenv NAME | wc -c`). Beads via the credential wrapper.
- No standing auto-accept authorization exists for this track — surface gates until
  the maintainer grants one.

## Clean state at handoff

Epic `livespec-yes5` + anchor slice `livespec-3wh4` filed (2026-07-08); carry-overs
routed. No implementation slices filed yet (the anchor defect must be reproduced +
its fix shape known before grooming `3wh4`). Handoff refresh landing via
worktree → PR. `livespec-bj9x` and `livespec-runtime-ego` are CLOSED. Verify no
orphaned worktrees + all primaries current on `origin/master` at session end.
