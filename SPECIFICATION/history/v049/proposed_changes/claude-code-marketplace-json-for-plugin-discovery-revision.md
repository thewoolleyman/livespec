---
proposal: claude-code-marketplace-json-for-plugin-discovery.md
decision: modify
revised_at: 2026-05-07T03:12:35Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: livespec-revise-marketplace-json
---

## Decision and Rationale

Accept the proposal's intent (codify plugin distribution + spec the install path) but answer the three open questions explicitly: (Q1) marketplace name = `livespec` plain, not the auto-derived `thewoolleyman-livespec` — shorter, matches the plugin name, brand-neutral; (Q2) install-only for v1, no uninstall/update — those are Claude Code platform behaviors, not livespec contracts; (Q3) `plugin.json.description` is SoT, `marketplace.json` duplicates manually, no mechanical equality check in v1. Plus widen the spec section to also document the maintainer's daily dogfooding path (`--plugin-dir .` + `/reload-plugins`) since the marketplace-install path copies to `~/.claude/plugins/cache/` and does NOT live-reload — important operational distinction for anyone editing the plugin source.

## Modifications

From the original proposal:

- Q1 answered: marketplace name = `livespec` (plain). Original proposal considered `thewoolleyman-livespec` auto-derived; rejected as longer, less brand-neutral, and creating a mismatch with the plugin name.
- Q2 answered: install-only for v1. Original proposal asked whether to cover uninstall/update; rejected as out of scope (Claude Code platform behavior, not livespec contract).
- Q3 answered: `plugin.json.description` is SoT. Original proposal asked for SoT direction; chose `plugin.json` to match Claude Code's own version-resolution precedence (`plugin.json` wins over `marketplace.json`).
- Versioning policy / release-please content REMOVED from this revise scope. Originally considered for inclusion here, but moved to a separate parallel proposal (PR #14: conventional-commits-mandate-and-rebase-merge-only) since release-please depends on the merge-strategy choice (rebase-merge vs squash) which is itself a separate concern.
- ADDED: explicit §"Daily dogfooding path" sub-section describing the `--plugin-dir .` workflow vs marketplace-install workflow. The original proposal did not surface that distinction, but it is operationally load-bearing for any maintainer editing the plugin source.

## Resulting Changes

- spec.md
- contracts.md
