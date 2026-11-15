---
topic: wrapper-cli-surface-pre-check-pair
author: claude-opus-5-5
created_at: 2026-11-15T04:46:20Z
---

## Proposal: Wrapper CLI surface table lists the pre-check flag pair on propose-change, critique and revise

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The §"Wrapper CLI surface" table lists `--skip-pre-check` / `--run-pre-check` only on the `prune-history` row, which contradicts §"Sub-command wire contracts" (L453): "The `propose-change`, `critique`, `revise`, and `prune-history` wrappers each support a mutually-exclusive `--skip-pre-check` / `--run-pre-check` flag pair". Conform the table to L453 by adding the pair to the `propose-change`, `critique` and `revise` rows' optional flags. `seed` is not added, because L453 omits it.

### Motivation

Internal-consistency conformance. L453 is the normative wire contract, and the shipped wrappers implement it (livespec-b37cfx, merged as 4aef25f1 and released in v0.47.11, wired the pair into propose-change, critique and revise). The table is the surface every Driver binding reads, and its omission is what let the installed propose-change skill and the core CLI disagree about `--run-pre-check`. Filed at the coordinator's direction for plan epic overseer-iyfjbo; the coordinator decides it at revise.

### Proposed Changes

The table MUST list the `--skip-pre-check` / `--run-pre-check` pair on every wrapper that §"Sub-command wire contracts" (L453) requires to support it. In `SPECIFICATION/contracts.md` §"Wrapper CLI surface", replace these three table rows (current text at L14–16, verified at livespec master 90409a29):

```text
| `propose-change` | `--findings-json <path>`, `<topic>` (positional) | `--author <id>`, `--reserve-suffix <text>`, `--spec-target <path>`, `--project-root <path>` |
| `critique` | `--findings-json <path>` | `--author <id>`, `--spec-target <path>`, `--project-root <path>` |
| `revise` | `--revise-json <path>` | `--author <id>`, `--spec-target <path>`, `--project-root <path>` |
```

with:

```text
| `propose-change` | `--findings-json <path>`, `<topic>` (positional) | `--author <id>`, `--reserve-suffix <text>`, `--spec-target <path>`, `--skip-pre-check`, `--run-pre-check`, `--project-root <path>` |
| `critique` | `--findings-json <path>` | `--author <id>`, `--spec-target <path>`, `--skip-pre-check`, `--run-pre-check`, `--project-root <path>` |
| `revise` | `--revise-json <path>` | `--author <id>`, `--spec-target <path>`, `--skip-pre-check`, `--run-pre-check`, `--project-root <path>` |
```

The `seed`, `prune-history`, `doctor`, `resolve-template`, `next` and `spec-governance` rows are unchanged. `seed` is NOT given the pair, because §"Sub-command wire contracts" L453 does not list it. No other text changes.
