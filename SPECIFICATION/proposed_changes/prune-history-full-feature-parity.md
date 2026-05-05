---
topic: prune-history-full-feature-parity
author: Claude Opus 4.7 (1M context)
created_at: 2026-05-04T23:25:00Z
---

## Proposal: prune-history CLI surface

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Replace the `prune-history` row of the wrapper-CLI surface table in contracts.md (currently `(varies; Phase 7 widens)`) with the enumerated flag set authorized by PROPOSAL.md: required (none); optional `--skip-pre-check` / `--run-pre-check` (mutually exclusive), `--project-root <path>`. No positional argument. No `--spec-target <path>` — `prune-history` operates on the main spec only in v1, per PROPOSAL.md §"Spec-target selection contract" line 363-366 (which enumerates `--spec-target` for `propose-change`, `critique`, `revise` only) and §"`prune-history`" lines 2536-2538 ("no other arguments in v1").

### Motivation

PROPOSAL.md §"`prune-history`" lines 2532-2544 specify that `bin/prune_history.py` accepts only the mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag pair per §"Pre-step skip control" (lines 811-822). The universal `--project-root <path>` flag (per the wrapper-CLI baseline at contracts.md line 7 and PROPOSAL.md §"Project-root detection contract" line 348-362, which explicitly enumerates `bin/prune_history.py`) is inherited from the universal mechanism.

The seeded contracts.md row at line 15 was deliberately left as a placeholder at v001 because the Phase-3 minimum-viable wrapper exposed only the bare parser shape with no flags wired. Phase 7 sub-step 6 widens the wrapper to the full PROPOSAL-authorized contract, so the table row must enumerate the flags.

`--spec-target <path>` is intentionally absent from `prune-history`'s flag set per PROPOSAL.md §"Spec-target selection contract" line 363-366: the multi-tree mechanism enumerates `--spec-target` as applicable to `propose-change`, `critique`, and `revise` only. PROPOSAL.md §"Pruning history" lines 1827-1872 describe the operation in `<spec-root>`-parameterized terms, but the v1 wrapper CLI hard-codes `<spec-root>` to the main spec tree (resolved from `--project-root` and `.livespec.jsonc` via the shared upward-walk helper). Sub-spec history pruning is not exposed in v1; if a future custom-template author needs it, that's a post-v1.0.0 enhancement scoped via a new propose-change cycle.

### Proposed Changes

One atomic edit to **SPECIFICATION/contracts.md §"Wrapper CLI surface"**.

Replace the existing `prune-history` row at line 15 (currently: `| \`prune-history\` | (varies; Phase 7 widens) | (Phase 7 widens) |`) with:

> | `prune-history` | (none) | `--skip-pre-check`, `--run-pre-check`, `--project-root <path>` |

## Proposal: prune-history operation and invariants

### Target specification files

- SPECIFICATION/spec.md

### Summary

Codify in spec.md the architecture-level body of the `prune-history` wrapper: the 5-step prune mechanic (identify highest version `vN`; resolve carry-forward `first` from `v(N-1)/PRUNED_HISTORY.json` if present, otherwise from the earliest surviving v-directory; delete every `vK/` where `K < N-1`; replace `v(N-1)/` contents with a single `PRUNED_HISTORY.json` containing `{"pruned_range": [first, N-1]}`; leave `vN/` intact); the no-op short-circuits (only `v001` exists; oldest surviving is already a `PRUNED_HISTORY.json` marker); the version-counter-never-resets invariant; the no-metadata-in-marker invariant; the destructive-operation skill-frontmatter requirement.

### Motivation

PROPOSAL.md §"Pruning history" lines 1827-1872 define the architecture of how `prune-history` removes older history while preserving auditable continuity. The seeded SPECIFICATION/spec.md currently carries only a one-sentence summary at line 47 ("`prune-history` MAY remove the oldest contiguous block of `history/v*/` directories down to a caller-specified retention horizon while preserving the contiguous-version invariant for the remaining tail. Phase 3 lands the parser-only stub; Phase 7 widens it to the actual pruning mechanic."). That summary is too thin for a clean re-implementation: the 5-step mechanic, the carry-forward rule for `pruned_range[0]`, the precise no-op-detection precondition (oldest surviving is already a `PRUNED_HISTORY.json` marker), and the no-metadata-in-marker invariant cannot be derived from the summary alone.

Per the unified responsibility-separation pattern established for the other wrappers (e.g., revise's lifecycle and responsibility separation codified at v011 sub-step 5.b), prune-history's contract has two architecturally distinct halves: (a) skill-prose responsibility — the LLM-driven dialogue that decides whether and when to invoke the destructive operation, the post-prune narrative for the user; (b) wrapper responsibility — deterministic file-shaping work that does not branch on LLM judgment. The wrapper MUST NOT invoke the LLM, the interactive confirmation flow, or any retry handshake; it performs the 5-step mechanic + emits structured findings on stdout when it short-circuits with `status: "skipped"`.

Per PROPOSAL.md §"Pruning history" line 1846-1849, the version-counter-never-resets invariant is load-bearing: `PRUNED_HISTORY.json` carries `pruned_range` to preserve the original-earliest version number across multiple prune cycles, so `pruned_range[0]` of the new marker carries forward from the prior marker's `pruned_range[0]` (not the prior marker's `pruned_range[1]+1`). Without codifying the carry-forward rule explicitly, a clean re-implementation could mistakenly reset `first` to `N-1` on every prune, losing the earliest-version audit trail.

Per PROPOSAL.md §"Pruning history" line 1850-1852, the no-metadata invariant excludes timestamps, git SHAs, and identity fields from the marker — these are fragile under git rebase/merge, and git commit metadata already provides the audit context. The marker is a minimal `{"pruned_range": [first, last]}` document.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Sub-command lifecycle"**: append a new paragraph immediately after the `revise` lifecycle paragraph (added by the v011 sub-step 5.b edits) codifying the prune-history lifecycle:

> **`prune-history` lifecycle and responsibility separation (PROPOSAL.md §"Pruning history" lines 1827-1872, §"`prune-history`" lines 2532-2544).** The `prune-history` LLM-driven invocation dialogue, the destructive-operation user-confirmation flow (the skill SKILL.md frontmatter MUST set `disable-model-invocation: true` so the user MUST invoke `/livespec:prune-history` explicitly), and the post-prune narrative are skill-prose responsibilities under `prune-history/SKILL.md`; `bin/prune_history.py` MUST NOT invoke the template prompt, the LLM, or the interactive confirmation flow. The wrapper resolves the spec root from `--project-root` and `.livespec.jsonc` via the shared upward-walk helper (the main spec tree only — there is no `--spec-target` flag for prune-history in v1) and performs deterministic file-shaping: (a) it identifies the current highest version `vN` under `<spec-root>/history/`; (b) it resolves the carry-forward `first` field — if `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json` exists, it reads that file's `pruned_range[0]` and uses it as `first`; otherwise `first` is the smallest-numbered v-directory currently under `<spec-root>/history/` (typically `1`); (c) it deletes every `<spec-root>/history/vK/` where `K < N-1`; (d) it replaces the contents of `<spec-root>/history/v(N-1)/` with a single file `<spec-root>/history/v(N-1)/PRUNED_HISTORY.json` containing exactly `{"pruned_range": [first, N-1]}` — no timestamps, git SHAs, or identity fields (per the no-metadata invariant; git commit metadata already provides that audit context); (e) `<spec-root>/history/vN/` is left fully intact. The version counter never resets — `PRUNED_HISTORY.json`'s `pruned_range[0]` carries the original-earliest version number forward across multiple prune cycles. Two no-op short-circuits MUST be detected before reaching step (c): (i) only `v001` exists under `<spec-root>/history/` (nothing to prune); (ii) the oldest surviving v-directory under `<spec-root>/history/vK/` (smallest `K < N`) already contains a `PRUNED_HISTORY.json` marker (no full versions remain to prune below the prior marker). On either no-op, the wrapper emits a single-finding `{"findings": [{"check_id": "prune-history-no-op", "status": "skipped", "message": "nothing to prune; oldest surviving history is already PRUNED_HISTORY.json"}]}` JSON document to stdout and exits 0; the existing marker is NOT re-written, no new commit-worthy diff is produced.

## Proposal: Pre-step skip control mechanism

### Target specification files

- SPECIFICATION/spec.md

### Summary

Codify in spec.md the mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag pair per PROPOSAL.md §"Pre-step skip control" (lines 811-822). The mechanism applies uniformly to every pre-step-having wrapper: `propose-change`, `critique`, `revise`, `prune-history`. Both flags set together MUST result in a `UsageError` (exit 2). The `pre_step_skip_static_checks` config-key fallback (default `false`) applies when neither flag is on the CLI. A skipped pre-step emits a JSON finding (`status: "skipped"`, `message: "pre-step checks skipped by user config or --skip-pre-check"`) — the wrapper MUST NOT print warning text outside the structured-findings contract.

### Motivation

PROPOSAL.md §"Pre-step skip control" (lines 811-822) specifies the mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag pair for sub-commands that have a pre-step (`propose-change`, `critique`, `revise`, `prune-history`). The seeded SPECIFICATION/spec.md does not yet codify the pre-step skip control mechanism. Phase 7 prune-history widening surfaces it because prune-history's wrapper is the third prune-history-touching component (after the SKILL.md prose and doctor's pre-step orchestration) that depends on the contract.

The flag pair's effective skip resolution is: (1) `--skip-pre-check` on CLI → skip = true; (2) `--run-pre-check` on CLI → skip = false (overrides config); (3) neither flag → use config key `pre_step_skip_static_checks` (default `false`); (4) both flags set → argparse usage error, exit 2.

The skipped-pre-step JSON finding is emitted on stdout per the standard wrapper-output contract. The Python layer MUST NOT print the warning text directly to stderr or stdout outside the structured-findings contract; LLM narration in the skill prose surfaces the warning to the user.

`bin/doctor_static.py` rejects BOTH flags (it IS the static phase) — passing either to it results in argparse usage error, exit 2.

### Proposed Changes

One atomic edit to **SPECIFICATION/spec.md §"Sub-command lifecycle"**: append a new paragraph immediately after the `prune-history` lifecycle paragraph (added by the companion finding above) codifying the pre-step skip control mechanism shared by every pre-step-having wrapper:

> **Pre-step skip control (PROPOSAL.md §"Pre-step skip control" lines 811-822).** The `propose-change`, `critique`, `revise`, and `prune-history` wrappers each support a mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag pair via argparse's `add_mutually_exclusive_group`. Effective skip resolution: (1) `--skip-pre-check` present → skip = true; (2) `--run-pre-check` present → skip = false (overrides config); (3) neither flag → use the `.livespec.jsonc` config key `pre_step_skip_static_checks` (default `false`); (4) both flags present → argparse rejects with a usage error and the wrapper exits 2 via `IOFailure(UsageError)`. When the resolved value is `true`, the wrapper MUST emit a single-finding `{"findings": [{"check_id": "pre-step-skipped", "status": "skipped", "message": "pre-step checks skipped by user config or --skip-pre-check"}]}` JSON document to stdout and proceed without invoking the pre-step doctor static phase. The Python layer MUST NOT print warning text outside the structured-findings contract or as ad-hoc stderr text — LLM narration in the SKILL.md prose surfaces the warning to the user. `bin/doctor_static.py` rejects BOTH `--skip-pre-check` AND `--run-pre-check` (it IS the static phase); passing either to it results in argparse usage error, exit 2.
