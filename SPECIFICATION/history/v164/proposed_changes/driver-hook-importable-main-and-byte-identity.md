---
topic: driver-hook-importable-main-and-byte-identity
author: claude-opus-4-8
created_at: 2026-07-13T08:38:41Z
---

## Proposal: Permit importable-main() Python Driver hooks and narrow byte-identity to the declared neutral body

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Amends contracts.md §"Driver-shipped hooks" so the Claude Driver's auto-memory-redirect and plan-persistence-WARN hooks MAY ship as Python files (invoked `python3 .../<name>.py`) rather than only shell scripts; states the importable `main() -> int` entry discipline that makes hook bodies testable in-process for real per-file coverage; narrows the byte-identity mandate to the declared neutral shared body (`no_shadow_ledger.py`), clarifying that runtime-specific hooks share behavior not bytes; and points the mechanical no-drift guarantee at a consumer-side byte-identity Verifier pinned-and-imported from livespec-dev-tooling (the commit-refuse-hook Conformance precedent).

### Motivation

Full Driver CI parity requires check-per-file-coverage (100%) on the Drivers' hook bodies, which are currently tested only via subprocess — and the subprocess_spawn_allowlist mechanism scrubs coverage from the child, yielding zero coverage on the hook. Real coverage requires testing each hook in-process, which requires refactoring each from 'runs on import' to an importable main(). The core contract currently mandates the Claude hooks be shell scripts and (mis-)attributes the no-drift guarantee to the Plugin-resolution Conformance concern; both must be corrected before the Drivers can refactor. Slice S1 (livespec-pxj9) of epic livespec-9z8h; maintainer decision 2026-07-13.

### Proposed Changes

Amend `SPECIFICATION/contracts.md` §"Driver-shipped hooks" (H3) with the following edits. Each
quotes the CURRENT live text verbatim (the revise/replace target) followed by its PROPOSED
replacement. This is slice S1 (ledger `livespec-pxj9`) of the driver-hook-body epic
(`livespec-9z8h`); it unblocks refactoring both Drivers' hooks to an importable `main()` for real
in-process per-file coverage.

### Edit (a.1) — permit Python hook entries for the two Claude hooks

CURRENT:
> a `hooks.json` registration plus one script per hook — a shell script invoked by the harness as `"${CLAUDE_PLUGIN_ROOT}/hooks/<name>.sh"`, except the cross-Driver no-shadow-ledger hook, which is a Python script invoked as `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/no_shadow_ledger.py"` so its one neutral body can ship byte-identically in both Drivers' bundles.

PROPOSED:
> a `hooks.json` registration plus one executable hook entry per hook. The auto-memory redirect and plan-persistence WARN hook MAY be shell scripts invoked by the harness as `"${CLAUDE_PLUGIN_ROOT}/hooks/<name>.sh"` or Python scripts invoked as `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/<name>.py"`; the cross-Driver no-shadow-ledger hook is a Python script invoked as `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/no_shadow_ledger.py"` so its one neutral body can ship byte-identically in both Drivers' bundles.

### Edit (a.2) — auto-memory bullet: de-hardcode the `.sh` file name

CURRENT:
> - **PreToolUse auto-memory redirect** (`block-auto-memory.sh`). Registered on the `Write` tool;

PROPOSED:
> - **PreToolUse auto-memory redirect** (Claude hook surface; the Driver file MAY be a shell entry such as `block-auto-memory.sh` or a Python entry such as `block_auto_memory.py`). Registered on the `Write` tool;

### Edit (a.3) — plan-persistence bullet: de-hardcode the `.sh` file name

CURRENT:
> - **Stop plan-persistence WARN** (`warn-plan-persistence.sh`). Registered on the `Stop` event; scans the agent's last turn

PROPOSED:
> - **Stop plan-persistence WARN** (Claude hook surface; the Driver file MAY be a shell entry such as `warn-plan-persistence.sh` or a Python entry such as `warn_plan_persistence.py`). Registered on the `Stop` event; scans the agent's last turn

### Edit (a.4) — no-shadow-ledger bullet: drift-sweep the hardcoded names

CURRENT:
> Unlike `warn-plan-persistence`, which the Claude bundle carries alone, the no-shadow-ledger hook is REQUIRED in BOTH Drivers' bundles (see the cross-Driver single-sourcing paragraph below); the auto-memory-write guard is likewise present in BOTH bundles, but as a PER-RUNTIME pair rather than a single shared body — `block-auto-memory.sh` targets the Claude layout (`~/.claude/.../memory/*.md`), and the Codex Driver ships its own guard targeting the Codex local-memory store (`~/.codex/memories/`), per the Codex auto-memory-write-guard paragraph below.

PROPOSED:
> Unlike the plan-persistence WARN hook, which the Claude bundle carries alone, the no-shadow-ledger hook is REQUIRED in BOTH Drivers' bundles (see the cross-Driver single-sourcing paragraph below); the auto-memory-write guard is likewise present in BOTH bundles, but as a PER-RUNTIME pair rather than a single shared body — the Claude auto-memory redirect targets the Claude layout (`~/.claude/.../memory/*.md`), and the Codex Driver ships its own guard targeting the Codex local-memory store (`~/.codex/memories/`), per the Codex auto-memory-write-guard paragraph below.

### Edit (a.5) — Codex auto-memory-guard paragraph: drift-sweep the hardcoded name

CURRENT:
> The Codex Driver (`livespec-driver-codex`) MUST ship a Codex `pre_tool_use` hook that is the per-runtime sibling of the Claude `block-auto-memory.sh`: in a livespec-governed project it MUST intercept a tool call that would write a file into the Codex local-memory store (`~/.codex/memories/`)

PROPOSED:
> The Codex Driver (`livespec-driver-codex`) MUST ship a Codex `pre_tool_use` hook that is the per-runtime sibling of the Claude auto-memory redirect: in a livespec-governed project it MUST intercept a tool call that would write a file into the Codex local-memory store (`~/.codex/memories/`)

### Edit (b) — importable-main() discipline (append to the "Fail-open discipline (every hook)" paragraph)

Insert after the sentence "A hook acts only when it POSITIVELY identifies its gating condition." the new sentences:
> Each Python hook body SHOULD expose an importable `main() -> int` that owns stdin/stdout at the hook boundary, catches expected and unexpected failures, returns `0` on every path, and does not call `sys.exit()` internally; the script entry tail MAY translate that return code into process exit. This keeps the body testable in-process for real per-file coverage while retaining a subprocess smoke test for the real hook I/O contract.

### Edit (c) — narrow byte-identity to the declared neutral body

CURRENT (in the "Cross-Driver single-sourcing (no-shadow-ledger)" paragraph):
> Codex consumes the Claude `Stop` hook I/O format, so one neutral body serves both runtimes.

PROPOSED:
> Codex consumes the Claude `Stop` hook I/O format, so one neutral body serves both runtimes. Byte-identity is mandatory ONLY for hook bodies this contract declares neutral shared bodies, currently `no_shadow_ledger.py`. Runtime-specific hooks — the per-runtime auto-memory guards, the Codex footgun guard, and the Claude-only plan-persistence WARN hook — share behavior where their contracts say so, not bytes, and are NOT byte-identity-bound.

### Edit (d) — point the no-drift guarantee at the dev-tooling consumer-side Verifier

CURRENT:
> This section requires the single-sourced-and-byte-identical disposition; the mechanical guarantee that the two copies do not drift is a cross-repo Conformance concern (the Plugin-resolution concern of the Conformance Pattern), realized separately and not pinned to any one sync mechanism here.

PROPOSED:
> This section requires the single-sourced-and-byte-identical disposition for the declared neutral shared body; the mechanical guarantee that the Driver copies do not drift is realized by a consumer-side byte-identity Verifier pinned-and-imported from `livespec-dev-tooling` — each Driver's `just check` asserts its bundled copy is byte-identical to the packaged canonical body — per the Conformance Pattern's reuse-by-default rule (the commit-refuse hook body is the precedent). Its full five-slot expansion lives in `livespec-dev-tooling`'s own spec and is not pinned here to any one source-copying or synchronization mechanism.

### Non-heading / drift notes
- §"Driver-shipped hooks" is an H3 (`### `) heading; no `## ` H2 is added, removed, or renamed, so no `tests/heading-coverage.json` co-edit is required.
- Drift-sweep: the only other `.sh` references in `contracts.md` are `with-livespec-env.sh` credential-wrapper examples (not hook-body contracts); `spec.md` has no contradicting hook-shell references. The `livespec-driver-claude` OWN-spec shell references (`spec.md` §Purpose, `contracts.md` §"Hook bundle") are a separate propose-change handled in slice S3 (`livespec-nj7d`).

