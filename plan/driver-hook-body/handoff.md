# Handoff — driver-hook-body

The single resumable entry point for the **driver-hook-body** thread: refactor both
Driver plugins' shipped hooks from "runs-on-import" to an importable `main()` so their
logic is testable IN-PROCESS for REAL per-file coverage — co-designed with the
byte-identity single-sourcing contract and full aggregate/coverage/types CI parity across
both Drivers. Spans 4 repos: `livespec-driver-claude`, `livespec-driver-codex`,
`livespec-dev-tooling`, `livespec` (core). A fresh session executes the next action from
this file alone via the read-first chain below — no chat history required.

## State — S1 ✅ + S2 ✅ DONE (2026-07-13). Next: S3 + S4 (both READY).

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

Layering: **S1 → (S2, S3); S2 → (S3, S4); S3 → S5; S4 → S6.** **S1 + S2 are CLOSED** (merged + released — see "Done so far"); **S3 (`livespec-nj7d`) and S4 (`livespec-8wea`) are now READY** and run in parallel (independent repos, no shared files). S5/S6 unblock after S3/S4.

## Done so far (S1 + S2)

- **S1 (`livespec-pxj9`, CLOSED)** — core `SPECIFICATION/contracts.md` §"Driver-shipped hooks" amended via revise **v164** (PR `thewoolleyman/livespec#1181`): `.py` hooks permitted, importable-`main()` discipline (SHOULD), byte-identity narrowed to the neutral `no_shadow_ledger.py`, no-drift pointed at a consumer-side dev-tooling Verifier. Independent Fable review + maintainer approval.
- **S2 (`livespec-8zxu`, CLOSED)** — `livespec-dev-tooling` byte-identity machinery, **released v0.44.0**:
  - Code (PR `livespec-dev-tooling#367`): `CANONICAL_NO_SHADOW_LEDGER_BODY` (the `main()`-refactored neutral body) + `install_no_shadow_ledger` (`just install-no-shadow-ledger`) + `checks/no_shadow_ledger_body_identical` Verifier (imports the constant, byte-compares the consumer's configured `neutral_hook_body_path`, no-ops when absent) + the `neutral_hook_body_path` role key + justfile aggregate + CI-matrix wiring. Single-commit Red-Green-Replay, `just check` green.
  - Spec (PR `livespec-dev-tooling#369`, revise **v024**): documents the Verifier's five slots + role key in dev-tooling `contracts.md`. Independent Fable NO-BLOCKERS review (2 blocker-fix rounds — the drift-sweep also surfaced + named the previously-undocumented `install_worktree_pack`).
  - **Follow-ups filed in the `livespec-dev-tooling` tenant** (not blocking): `livespec-dev-tooling-okz` (Verifier compares decoded text, not bytes — switch to `read_bytes`), `-ckb` (commit-refuse-check H3 doesn't document its worktree-pack + vendored-copies arms), `-zbo` (justfile `install-worktree-pack` comment says "tracked" but the pack is gitignored).

## The next action

**Drive S3 (`livespec-nj7d`, `livespec-driver-claude`) and S4 (`livespec-8wea`,
`livespec-driver-codex`) — the two Driver hook refactors — in parallel** (independent repos,
no shared files). Read each slice's full scope from `bd show <id>` first. Each Driver:

1. **Bump its `livespec-dev-tooling` pin to v0.44.0** (carries the Verifier + constant + installer + role key).
2. **Make its `no_shadow_ledger.py` byte-identical to `CANONICAL_NO_SHADOW_LEDGER_BODY`.** Declare the
   `neutral_hook_body_path` role key in the Driver's `pyproject.toml [tool.livespec_dev_tooling]`
   (Claude: `.claude-plugin/hooks/no_shadow_ledger.py`; Codex: `livespec/hooks/no_shadow_ledger.py`),
   then either run `just install-no-shadow-ledger` to write the canonical body OR hand-apply the
   `main()`-refactor and let the check confirm identity. Wire `check-no-shadow-ledger-body-identical`
   into the Driver's `just check` aggregate (and CI matrix — HOST-SIDE, see S5/S6).
3. **Convert the Driver's other run-on-import hooks to importable `main()`** for real per-file coverage.
   Claude: the two `.sh` hooks (`block-auto-memory.sh` / `warn-plan-persistence.sh`) → `.py` invoked
   `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/<name>.py"` — this needs the **Claude Driver's OWN-spec
   propose-change** (its `spec.md` §Purpose + `contracts.md` §"Hook bundle" still say "POSIX shell
   scripts"; independent Fable NO-BLOCKERS review before ratifying). Codex: normalize the existing
   `main()` entries, remove internal `sys.exit()` calls, keep footgun/apply_patch coverage.
4. **Test split**: in-process `main()` tests (monkeypatched stdin/stdout/cwd/env) + one subprocess
   smoke per hook (declared in `subprocess_spawn_allowlist`); add coverage config; keep fail-open posture.

S4 also fixes the stale `livespec-driver-codex` justfile comment (§"Resolved design-checks"). Then
**S5 (`livespec-2ua9`) unblocks after S3, S6 (`livespec-vuy3`) after S4** — the `just check` aggregate
reorder + full CI wiring (HOST-SIDE: `.github/workflows/`, maintainer creds; Driver PRs auto-merge on
green CI → review-the-merged-commit + fix-forward).

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

- **Pins**: S2 released **`livespec-dev-tooling` v0.44.0** (the Verifier + `CANONICAL_NO_SHADOW_LEDGER_BODY` + `install_no_shadow_ledger` + `neutral_hook_body_path` role key). Both Drivers were on v0.43.2 pre-S2; **S3/S4 MUST bump each Driver's pin to v0.44.0** to consume the Verifier.
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
