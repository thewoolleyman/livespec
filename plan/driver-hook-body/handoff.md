# Handoff — driver-hook-body

The single resumable entry point for the **driver-hook-body** thread: refactor both
Driver plugins' shipped hooks from "runs-on-import" to an importable `main()` so their
logic is testable IN-PROCESS for REAL per-file coverage — co-designed with the
byte-identity single-sourcing contract and full aggregate/coverage/types CI parity across
both Drivers. Spans 4 repos: `livespec-driver-claude`, `livespec-driver-codex`,
`livespec-dev-tooling`, `livespec` (core). A fresh session executes the next action from
this file alone via the read-first chain below — no chat history required.

## For a fresh session — read first

- **Ledger epic anchor: `livespec-9z8h`** [EPIC, open]. Read it FIRST for the shape:
  `bd -C /data/projects/livespec show livespec-9z8h` (via the credential wrapper —
  `/usr/local/bin/with-livespec-env.sh -- bd …`).
- **The FULL unified scope + rationale lives in the `livespec-uvgi` DECISION comment**
  (maintainer, 2026-07-13): `bd -C /data/projects/livespec show livespec-uvgi`. It carries
  the wall analysis (why importable-`main()` is required for real coverage) and the FOUR
  workstreams: (1) hook refactor to importable `main()` byte-identically across both
  Drivers, reconciled with `main_guard`; (2) byte-identity single-sourcing via livespec's
  Conformance Pattern (Contract/Mechanism/Installer/Verifier, reuse-from-dev-tooling),
  folding in the original `livespec-tawm` `__all__`+docstring reconciliation; (3) coverage +
  types infra on both Drivers (mirror `livespec-runtime`), with a declared
  `subprocess_spawn_allowlist` for the RETAINED subprocess I/O tests; (4) aggregate + CI
  wiring — reorder each `check:` aggregate to a contiguous alphabetical canonical block,
  wire every canonical check into `ci.yml` + `ci-green.needs`, flip
  `LIVESPEC_FAIL_IF_CI_MATRIX_GAPS_EXIST` to fail.
- **`livespec-tawm`** [open] — the byte-identity single-sourcing residual, subsumed here:
  `bd -C /data/projects/livespec show livespec-tawm`. The two Drivers'
  `no_shadow_ledger.py` copies drifted (claude `.claude-plugin/hooks/…` vs codex
  `livespec/hooks/…`) and the byte-identity contract (livespec core `contracts.md`
  §"Driver-shipped hooks") is unenforced.
- **Design note:** `plan/driver-hook-body/research/importable-main-slice-design.md`.
  Read this after the ledger items above; it records the importable-`main()` entry form,
  in-process coverage split, byte-identity boundary, verifier direction, and recommended
  grooming order.

## The next action

**Run the `groom` operation on `livespec-9z8h` into ready, dependency-layered slices, using
the design note from the read-first chain as the design input.** The design note records the
importable-`main()` entry form, the in-process coverage/subprocess smoke split, the cross-repo
byte-identity boundary, the no-circular-dependency constraint for the verifier, and the
recommended slice order. Then DRIVE host-side:

- **HOST-SIDE, not factory-safe** — touches `.github/workflows/` (the factory GitHub App
  token lacks `workflows` permission; proven repeatedly in the fleet-check-coverage epic).
  Author via scoped agents in worktrees under maintainer creds; Driver PRs auto-merge on
  green CI → review-the-merged-commit + fix-forward.
- **Independent Fable NO-BLOCKERS review before ratifying each slice** (fleet discipline).
- **Byte-identical hook bodies** across both Drivers — never edit one copy unilaterally
  (that deepens the drift). The current design narrows byte-identity to declared neutral
  bodies, currently `no_shadow_ledger.py`; runtime-specific hooks share behavior, not bytes.
  Change the canonical neutral body + both copies together, guarded by the consumer-side
  Conformance Pattern Verifier.

## Context / gotchas (from the fleet-check-coverage epic that surfaced this)

- Both Drivers' `just check` is currently RED locally on the aggregate-ordering + the
  coverage/types/subprocess gaps this epic closes; CI stays green because those checks are
  not yet Driver CI jobs. So a HUMAN/agent local push to a Driver is blocked until this
  lands — plan host-side pushes accordingly.
- `livespec-driver-codex` has a stale `justfile` comment (~line 299) saying
  `file_lloc_hard_gate` is "DELIBERATELY NOT set" while `pyproject.toml` has it `true` —
  fold the 1-line comment fix into this epic's Driver-justfile rework.
- Re-check the Driver pins before grooming: the primary `livespec-driver-claude` checkout
  currently shows `livespec-dev-tooling` v0.40.0, and `livespec-driver-codex` shows v0.43.0.
  The prior handoff's "all 4 repos v0.43.2" statement is therefore not safe as an input
  unless the implementation worktree is on a newer branch.

## Golden rules

- Status is READ live from the ledger (`bd show <id>`), never stored here.
- Ready, factory-safe work is factory-dispatched; but this epic is HOST-SIDE (workflows
  permission wall) — author host-side under review, never `--no-verify`.
- Rotate this handoff before ~50% context; refresh current state + next action, print the
  resume command as the last line.

**Resume command:** `/livespec-orchestrator-beads-fabro:plan driver-hook-body`
