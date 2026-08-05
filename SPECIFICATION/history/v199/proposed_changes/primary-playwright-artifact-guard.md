---
topic: primary-playwright-artifact-guard
author: gpt-5.6
created_at: 2026-08-05T22:14:01Z
---

## Proposal: Refuse Playwright MCP calls from governed primary checkouts

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Extend the Claude Driver hook contract with a PreToolUse guard that prevents Playwright MCP side effects from dirtying livespec-governed primary checkouts.

### Motivation

A Claude Code session invoked browser_take_screenshot with a relative filename while its cwd was the livespec-dev-tooling primary checkout, creating install-livespec-pr-bot.png there. The same Playwright MCP server also created ignored .playwright-mcp artifact trees in multiple fleet and adopter primary checkouts. The existing repository footgun guard matches Bash only, so MCP browser calls bypass it. Host-level output-directory redirection limits damage on one machine but does not enforce the fleet invariant or protect other operators.

### Proposed Changes

Under contracts.md section 'Driver-shipped hooks', increase the Claude Driver bundle count and require a PreToolUse primary-checkout Playwright guard registered for every mcp__playwright__* tool. When hook input positively identifies a livespec-governed primary checkout by resolving the cwd's Git repository and finding that the resolved git-dir equals the resolved git-common-dir, the guard MUST deny the call before MCP invocation. It MUST guard all Playwright MCP calls, not only screenshot calls, because navigation and inspection calls may also emit automatic snapshots, console logs, and network logs. It MUST allow calls from linked worktrees, non-governed repositories, and non-repository directories; ambiguous or failed resolution MUST follow the default fail-open hook discipline. The denial reason MUST direct the agent to perform browser work from a secondary worktree. Redirecting Playwright output to a host cache MAY be used as defense in depth but MUST NOT replace the guard. Add a scenarios.md behavior scenario proving that every Playwright MCP call is refused at a governed primary checkout before artifacts can be created, while the same call from a linked worktree is allowed. The Driver-owned implementation and its tests remain in livespec-driver-claude per the existing partition.
