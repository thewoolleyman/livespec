# needs-attention-hardening — KICKOFF HANDOFF (fresh session entry point)

**Purpose:** open a NEW track (plan thread + epic) that drives the unaddressed
follow-ups from the just-closed `needs-attention` rollout (`livespec-bj9x`, now
CLOSED) plus newly-surfaced cross-runtime / cross-repo skill-correctness
problems. This doc is the cold-start entry point — a fresh session should be able
to execute the FIRST ACTIONS below from this file alone.

Repo: `thewoolleyman/livespec` (host checkout `/data/projects/livespec`).
Ledger via the wrapper: `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C <repo> ...`.

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

## FIRST ACTIONS (do these in order, from a fresh CURRENT-plugin session)

### 1. File the headline work-item FIRST (before opening the plan/epic)

File a work-item (core `livespec` tenant, or the tenant you judge most correct)
titled roughly: **"needs-attention skill must work under BOTH Claude AND Codex
on ALL fleet + adopter repos"**. Scope/description:

- **Observed defect (maintainer, 2026-07-08):** the `needs-attention` skill does
  NOT work under **Codex** in the **`livespec-runtime`** repo — it is "confused
  about wrappers." `livespec-runtime` is a **library** (class=`library`), it does
  NOT ship a `needs-attention` surface of its own; the shared orchestrator skill,
  invoked in a repo with no orchestrator `.livespec.jsonc` / no work-items
  backend, mis-resolves the wrapper/plugin-root and fails. This is the general
  class of "run a fleet skill in a repo it isn't set up for."
- **Required outcome:** `needs-attention` (and, by extension, audit the other
  `/livespec:*` + orchestrator skills) must behave CORRECTLY on **both runtimes
  (Claude Code + Codex)** across **every fleet member AND adopter**: it either
  produces the right attention list, or fails soft with a clear, correct message
  — never a confusing wrapper error, never a wrong-plugin resolution. This spans
  the beads-fabro + git-jsonl bindings' plugin-root/CLI resolution (the same
  cross-plane resolver just built for spec-next — see the `livespec-runtime-ego`
  fix) AND the per-runtime SKILL.md preambles (Codex `$PLUGIN_ROOT` tiers vs
  Claude `${CLAUDE_PLUGIN_ROOT}`).
- **Verification bar (per the "done means exercised live" discipline):** run the
  skill on BOTH runtimes against a representative matrix — a fleet member WITH an
  orchestrator (beads-fabro repo), a fleet member that is a pure LIBRARY
  (`livespec-runtime`), a driver-plugin repo, core, and both adopters
  (`openbrain`, `resume`) — and show correct output or correct fail-soft each
  time. Codex plugin resolution is HOST-WIDE (`~/.codex/config.toml`,
  `ref=release`); Claude is project-scoped (`.claude/settings.json`).

This is the anchor problem; file it first so the epic can be anchored to it.

### 2. Open the new plan thread + epic

Run `/livespec-orchestrator-beads-fabro:plan needs-attention-hardening` (or a
name you prefer) to open a durable plan thread and anchor a ledger epic. Route
EVERY carried-over item below into that epic (per-repo tenants + cross-repo prose
links, the `livespec-bj9x` filing model). The headline work-item from step 1 is
the epic's first/anchor slice.

---

## What is DONE (context — do NOT redo)

- **`livespec-bj9x` (needs-attention rollout): CLOSED.** All 12 slices landed +
  adversarial-reviewed + accepted. Notably the F1 reaper default-branch
  destructive regression (CO1) was fixed at the root: `livespec-runtime` **v0.9.1**
  (PR #142) guard in the shared `_stale_worktree_finding` + `livespec` core
  **v0.7.1** (PR #922) belt-and-suspenders reaper action-layer skip + regression
  test. Plan thread archived to `plan/archive/needs-attention/`.
- **`livespec-runtime-ego` (spec-next pointer defect): CLOSED, fixed in BOTH
  orchestrators.** `needs-attention` now invokes spec-`next` cross-plane behind an
  injectable `SpecNextSeam`, adapts the top ripe candidate (or nothing), fail-soft
  — no pointer. beads-fabro **v0.13.1** (PR #357, `c39ed041`); git-jsonl **v0.5.1**
  (PR #202 `d25e525` + release #203, `1514739`). Verified in the live console
  Codex pane (no `spec:next` pointer). The cross-plane CORE-CLI resolver (3 tiers:
  fleet-sibling → Claude `installed_plugins.json` → Codex installed cache
  `~/.codex/plugins/cache/livespec/livespec/<version>`) is the reference for the
  step-1 work above.

---

## CARRY-OVER FOLLOW-UPS (route all into the new epic)

**needs-attention residuals (filed, backlog):**
- `livespec-console-beads-fabro-ipi` — migrate the console **TUI render path**
  from lane-derived to the `attention_item.*` stream (v016 retains Scenario 5;
  this is the natural completion). Task.
- `livespec-console-beads-fabro-fpo` — pre-existing `work_item` `stream_seq`
  `u64`→SQLite signed-int overflow; apply the same 63-bit mask CN1 used. Bug.
- `livespec-runtime-dnu` — `validate_attention_item_id` REJECTS the `internal:`
  id prefix although `kind="internal"` is first-class; add `internal` to
  `_THREE_PART_PREFIXES` in `livespec_runtime/attention_item.py` + test. Bug.
  (The shipped `needs-attention-internal` local skill emits `internal:<signal>:<repo>`
  ids the validator currently rejects — prose-only today, but a latent seam.)

**Fleet skill/doc hygiene:**
- **git-jsonl skill-count drift** — README ("9-skill") vs contracts ("seven-skill")
  vs constraints (missing `detect-impl-gaps`); reconcile to one source via
  propose-change (governed-spec counts).
- **`needs-attention-internal` + `-fleet` local skills** (livespec core,
  `.claude/skills/`, unsynced): authored this rollout; the `dnu` id-prefix issue
  above is their one known seam. Also re-check they behave on Codex (part of the
  step-1 cross-runtime audit).

**Factory robustness (coordinate with the SEPARATE `livespec-nrdk` epic — do NOT
re-drive nrdk from this track, but these block clean factory completion):**
- **Fabro 60-min token TTL** — the fleet Fabro GitHub App installation token has a
  hard 60-min TTL, minted once at dispatch, no per-node refresh; ANY factory run
  >~60 min fails at push with `Invalid username or token` (it killed CN1's Rust
  build AND core-Python CO1 at ~67 min — NOT Rust-specific). Durable fix =
  JIT-refresh the token at the push node. Tracked as a candidate slice on
  `livespec-nrdk`. Fabro fork PR **#552** (upstream `fabro-sh/fabro`, OPEN) is a
  checkpoint-COMMIT-timeout config and is **NOT** the token fix (verified).
- **`bd-gj-9sj`** — a fresh `git worktree add` does not hydrate the gitignored
  worktree-pack (`branch-protection.sh` + `.just` fragments), so a fresh janitor
  worktree fails `just check` on branch-protection until `just install-worktree-pack`.
  Blocks CLEAN git-jsonl factory completion. Candidate: auto-hydrate on worktree
  creation (related `livespec-qtjd`).

**Separate open tracks (NOT this epic — listed so they aren't forgotten):**
- `livespec-nrdk` — factory-safe-by-default (factory-safe default + machine-readable
  `not-factory-safe:<reason>` admission gate + capability widening + host-only
  needs-attention lane). Carries the token-TTL fix.
- `livespec-xfqd` — orchestrator-surface-parity (git-jsonl becomes a full peer:
  identical cross-runtime + cross-orchestrator skill surfaces, mechanically
  enforced). **NOTE:** this overlaps the step-1 cross-runtime skill-correctness
  work — reconcile scope between this new epic and `xfqd` early so they don't
  duplicate.

---

## Standing disciplines (apply throughout)

- Repo mutations: worktree → PR → rebase-merge; `mise exec -- git`; NEVER
  `--no-verify`; product `.py` uses the Red-Green-Replay ritual (the hook runs
  pytest against the **on-disk** module — at Red the impl must be the
  pre-change/pointer version on disk; move the fix aside, stage the test alone).
- Injectable seams (mirror `livespec_runtime.github_auth.MintSeams`) for any I/O
  that would otherwise need a hermetic `~/.codex`/`~/.claude` — unit-test tier
  logic with tmp dirs, never HOME monkeypatching.
- Independent adversarial review before any spec ratification (and this session's
  review caught two real defects — keep that bar). Verify sub-agent claims
  (static facts + your own live re-run), don't trust self-summaries.
- Codex plugin resolution is HOST-WIDE (`~/.codex`, `ref=release`); to see a fix
  in a running Codex TUI you must merge → release → `codex plugin marketplace
  upgrade <name>` → **restart the TUI** (`codex resume <id>`) so it reloads the
  installed cache (a running session caches the old version and its skill-load
  breaks when the cache is replaced).
- Secrets probe-only (`printenv NAME | wc -c`). Beads via the credential wrapper.
- No standing auto-accept authorization exists for this new track (the
  `livespec-bj9x` one expired at its close) — surface gates until the maintainer
  grants one.

## Clean state at handoff

No orphaned worktrees, no background sub-agents/subprocesses running. All primaries
(`livespec`, `livespec-runtime`, `livespec-console-beads-fabro`,
`livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`) are current
on `origin/master`. `livespec-bj9x` and `livespec-runtime-ego` are CLOSED.
</content>
