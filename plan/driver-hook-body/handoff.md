# Handoff — driver-hook-body

The single resumable entry point for the **driver-hook-body** thread: refactor both
Driver plugins' shipped hooks from "runs-on-import" to an importable `main()` so their
logic is testable IN-PROCESS for REAL per-file coverage — co-designed with the
byte-identity single-sourcing contract and full aggregate/coverage/types CI parity across
both Drivers. Spans 4 repos: `livespec-driver-claude`, `livespec-driver-codex`,
`livespec-dev-tooling`, `livespec` (core). A fresh session executes the next action from
this file alone via the read-first chain below — no chat history required.

## State — GROOMED (2026-07-13). Now DRIVING.

Epic `livespec-9z8h` was groomed into **6 dependency-layered slices**, filed in the
**core tenant** (the epic stays OPEN as the narrative umbrella; `livespec-uvgi` and
`livespec-tawm` were closed as subsumed). Status is READ LIVE from the ledger — the
ready/blocked notes below are the point-in-time shape at grooming, not a stored source of
truth. Re-derive with `bd -C /data/projects/livespec ready` (via the credential wrapper
`/usr/local/bin/with-livespec-env.sh -- bd …`).

| Slice | Ledger id | Repo | Tier | Blocked by |
|---|---|---|---|---|
| S1 core-spec amendment | `livespec-pxj9` | `livespec` | spec-change (propose-change→revise) | — (READY) |
| S2 dev-tooling byte-identity concern | `livespec-8zxu` | `livespec-dev-tooling` | factory | S1 |
| S3 Claude Driver hook refactor + own-spec + coverage | `livespec-nj7d` | `livespec-driver-claude` | factory, host-side | S1, S2 |
| S4 Codex Driver hook refactor + stale-comment + coverage | `livespec-8wea` | `livespec-driver-codex` | factory, host-side | S2 |
| S5 Claude Driver aggregate reorder + CI wiring | `livespec-2ua9` | `livespec-driver-claude` | host-side (workflows) | S3 |
| S6 Codex Driver aggregate reorder + CI wiring | `livespec-vuy3` | `livespec-driver-codex` | host-side (workflows) | S4 |

Layering: **S1 → (S2, S3); S2 → (S3, S4); S3 → S5; S4 → S6.** Only **S1** is ready to start.

## The next action

**Drive S1 (`livespec-pxj9`) — the core-spec amendment** — then unblock the rest in
dependency order. S1 amends `SPECIFICATION/contracts.md` §"Driver-shipped hooks" (H3) to:
(a) permit the Claude auto-memory + plan-persistence hooks to ship as Python files invoked
`python3 "${CLAUDE_PLUGIN_ROOT}/hooks/<name>.py"` (the section currently mandates `.sh` at
the paragraphs naming `block-auto-memory.sh` / `warn-plan-persistence.sh`); (b) state the
importable-`main()` entry discipline as the required in-process-testable form; (c) narrow
the byte-identity mandate to the declared neutral shared body (`no_shadow_ledger.py`) and
clarify runtime-specific hooks share behavior, not bytes; (d) point the mechanical no-drift
guarantee at S2's dev-tooling Verifier.

Drive it as a core spec-lifecycle op: `/livespec:propose-change` against core → **independent
Fable NO-BLOCKERS review** → `/livespec:revise` → PR → merge. Host-side (core primary
checkout, dogfooded). Read each slice's full scope from `bd show <id>`.

### Driving disciplines (all slices)

- **HOST-SIDE, not factory-safe** — S5/S6 touch `.github/workflows/` (the factory GitHub App
  token lacks `workflows` permission). Author via scoped agents in worktrees under maintainer
  creds; Driver PRs auto-merge on green CI → review-the-merged-commit + fix-forward.
- **Independent Fable NO-BLOCKERS review before ratifying each spec change** (S1 core spec;
  S3 folds in the Claude Driver's OWN spec propose-change) — fleet discipline, never self-waived.
- **Byte-identical hook bodies** across both Drivers — the canonical source-of-truth is the
  dev-tooling packaged constant `CANONICAL_NO_SHADOW_LEDGER_BODY` (S2), mirroring the
  concern-#1 commit-refuse `CANONICAL_HOOK_BODY` precedent. Change the constant + both Driver
  copies together, guarded by the consumer-side Conformance Verifier. Never edit one copy
  unilaterally (that deepens the drift).
- **Delegate the heavy authoring to codex subagents** in worktrees (self-contained briefs,
  never `--no-verify`, halt on hook failure); keep the main session for plan/dispatch/synthesis.

## Resolved design-checks (grooming inputs — no longer open)

- **Pins**: both Drivers are on `livespec-dev-tooling` **v0.43.2** on origin/master. No pin-bump gate.
- **`.sh`→`.py` is a spec change** against BOTH livespec core (`contracts.md` §"Driver-shipped
  hooks") AND the Claude Driver's own spec (`spec.md` §Purpose + `contracts.md` §"Hook bundle"
  say "POSIX shell scripts"). → S1 (core) + the own-spec propose-change inside S3.
- **Byte-identity source = dev-tooling packaged constant** (self-resolved). No reusable
  verifier exists; the concern-#1 commit-refuse hook is the precedent (`CANONICAL_HOOK_BODY`
  + `primary_checkout_commit_refuse_hook_installed` importing-and-comparing it). Core is NOT a
  Python dep of the Drivers, so "core-as-reference" would force a fragile cross-repo file read.
- **Stale `livespec-driver-codex` justfile comment** (lines ~298–311): claims
  `file_lloc_hard_gate` "DELIBERATELY NOT set" and `check-aggregate-completeness` "DELIBERATELY
  NOT wired… Drivers outside universal-propagation (2026-07-12)" — both false/superseded by the
  2026-07-13 full-parity decision. → rewritten in S6 (and the file_lloc note in S4).

## Read-first chain (for a fresh session)

- **Epic anchor `livespec-9z8h`** [EPIC, open] — `bd -C /data/projects/livespec show livespec-9z8h`;
  its latest comment narrates the 6 slices + layering.
- **Full unified scope + rationale**: the DECISION comment on the CLOSED `livespec-uvgi`
  (`bd -C /data/projects/livespec show livespec-uvgi`) — the wall analysis + the 4 workstreams.
- **Design note**: `plan/driver-hook-body/research/importable-main-slice-design.md` — the
  importable-`main()` entry form, in-process/subprocess coverage split, byte-identity boundary,
  verifier direction, recommended order.
- Each slice's full scope + acceptance lives on its ledger record (`bd show <id>`).

## Golden rules

- Status is READ live from the ledger (`bd show <id>` / `bd ready`), never stored here.
- HOST-SIDE (workflows-permission wall) — author host-side under review, never `--no-verify`.
- Independent Fable review before every spec ratification.
- Rotate this handoff before ~50% context; refresh current state + next action, print the
  resume command as the last line.

**Resume command:** `/livespec-orchestrator-beads-fabro:plan driver-hook-body`
