# needs-attention-hardening — LIVING plan thread HANDOFF (resumable entry point)

**Purpose:** drive the unaddressed follow-ups from the just-closed `needs-attention`
rollout (`livespec-bj9x`, CLOSED) plus newly-surfaced cross-runtime / cross-repo
skill-correctness problems, until the `needs-attention` surface is
**dogfood-proven** on BOTH runtimes (Claude + Codex) across ALL fleet members AND
adopters. This doc is the single resumable entry point — a fresh session should be
able to execute the NEXT ACTION below from this file alone (via the read-first
chain), no chat history required.

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

## NEXT ACTION (execute from this file alone)

The kickoff FIRST ACTIONS are **DONE** — the epic (`livespec-yes5`) and the anchor
slice (`livespec-3wh4`) are filed and the carry-overs are routed (see below). The
next action is to START PROVING the runtime × repo matrix, beginning with the
reported anchor defect:

1. **Reproduce the anchor defect LIVE.** Drive `needs-attention` under **Codex** in
   **`livespec-runtime`** (a pure LIBRARY — no orchestrator `.livespec.jsonc`, no
   work-items backend) and capture the exact failure (the maintainer's "confused
   about wrappers" report). Invocation:
   - **Codex** (host-wide plugins, `~/.codex/config.toml`, `ref=release`) — from
     the repo dir, name-select the orchestrator skill via `codex exec`:
     `cd /data/projects/livespec-runtime && codex exec "livespec-orchestrator-beads-fabro:needs-attention"`.
     Confirm the exact name-selection against the installed Codex plugin as the
     first reproduce sub-step:
     `codex plugin list --json -m livespec-orchestrator-beads-fabro`.
   - **Claude** (project-scoped plugins) — from a Claude Code session in the repo,
     the slash command `/livespec-orchestrator-beads-fabro:needs-attention`.

   Expected-vs-wrong behavior is pinned in
   `plan/needs-attention-hardening/live-adversarial-review-prompt.md` attack
   point #1: CORRECT = an explicit fail-soft ("no applicable needs-attention
   backend in this repo"); WRONG = chasing a nonexistent local wrapper, resolving
   the wrong plugin-root, or a stack trace / import error. Capture: command, repo,
   runtime, plugin version + installed cache path, and full output — distinguish
   fresh output from scrollback.
2. **Locate the resolution seam.** The fix mirrors the cross-plane CORE-CLI
   resolver just built for spec-`next` (`livespec-runtime-ego`, CLOSED — 3 tiers:
   fleet-sibling → Claude `installed_plugins.json` → Codex installed cache
   `~/.codex/plugins/cache/livespec/livespec/<version>`). Find where the
   beads-fabro + git-jsonl `needs-attention` bindings resolve the plugin-root/CLI,
   and where a library repo with no applicable backend should fail **soft** with a
   clear, actionable message ("no needs-attention backend in this repo") instead of
   a wrapper/plugin-root error or a stack trace.
3. **Groom `livespec-3wh4` into per-repo/per-runtime fix slices** once the fix
   shape is known — filed into their OWNING tenants (beads-fabro, git-jsonl, core;
   the `livespec-bj9x` per-tenant + cross-repo-prose model). Each fix slice carries
   a red test for its named failure mode + a live fail-soft/correct-list fixture.
4. **Prove the matrix.** Run `needs-attention` on BOTH runtimes across the repo
   classes (core, runtime library, driver plugin, both orchestrators, console,
   `openbrain`, `resume`); each cell = correct attention list OR correct fail-soft.
   The authoritative matrix table + attack points live in
   `plan/needs-attention-hardening/live-adversarial-review-prompt.md`.

Injectable seams (mirror `livespec_runtime.github_auth.MintSeams`) for any I/O that
would otherwise need a hermetic `~/.codex` / `~/.claude` — unit-test tier logic
with tmp dirs, never HOME monkeypatching.

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

## CARRY-OVER FOLLOW-UPS (routed into epic `livespec-yes5`)

**needs-attention residuals (filed, backlog; back-linked to `yes5`):**
- `livespec-console-beads-fabro-ipi` — migrate the console **TUI render path**
  from lane-derived to the `attention_item.*` stream. Task.
- `livespec-console-beads-fabro-fpo` — pre-existing `work_item` `stream_seq`
  `u64`→SQLite signed-int overflow; apply the same 63-bit mask CN1 used. Bug.
- `livespec-runtime-dnu` — `validate_attention_item_id` REJECTS the `internal:`
  id prefix although `kind="internal"` is first-class; add `internal` to
  `_THREE_PART_PREFIXES` in `livespec_runtime/attention_item.py` + test. Bug.

**Fleet skill/doc hygiene (TO FILE / audit):**
- **git-jsonl skill-count drift** — README ("9-skill") vs contracts ("seven-skill")
  vs constraints (missing `detect-impl-gaps`); reconcile to one source via
  `/livespec:propose-change` (governed-spec counts). Spec-lifecycle piece, NOT a
  factory slice. Not yet filed.
- **`needs-attention-internal` + `-fleet` local skills** (livespec core,
  `.claude/skills/`, unsynced): the `dnu` id-prefix issue above is their one known
  seam. Re-audit them under Codex as part of the anchor-slice cross-runtime audit.

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
- `livespec-xfqd` — orchestrator-surface-parity (git-jsonl becomes a full peer:
  identical cross-runtime + cross-orchestrator skill surfaces, mechanically
  enforced). **Scope reconciled (2026-07-08):** `xfqd` owns surface/packaging
  PARITY (which skills exist + are packaged where, static + mechanically enforced);
  THIS epic owns runtime BEHAVIOR correctness (resolution + fail-soft, dogfood-
  proven). Cross-link, do not duplicate.

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
