---
topic: driver-shipped-hooks
author: claude-fable-5
created_at: 2026-06-12T07:42:49Z
---

## Proposal: driver-shipped-hooks

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Codify the Claude Code Driver plugin's agent-runtime hook bundle in contracts.md §"Plugin distribution" as a new §"Driver-shipped hooks" subsection: the PreToolUse auto-memory redirect hook (block-auto-memory.sh; matcher Write(**/memory/*.md); blocks with a redirect to the active impl-plugin's /<plugin>:capture-memo skill, resolved from .livespec.jsonc implementation.plugin — the sole config gate) and the Stop plan-persistence WARN hook (warn-plan-persistence.sh; mechanical substantial-planning-artifact thresholds over the last turn; warn-only — never blocks, never auto-files), plus the shared fail-open discipline (any failure is a silent exit-0 pass-through; a hook acts only on positive identification of its gate) and the change-control rule (posture/surface changes need a propose-change cycle; detection internals are Driver-tunable).

### Motivation

Driver PRs #4 and #5 (merged 2026-06-11, work-items livespec-driver-claude-e1s and livespec-driver-claude-4jp) shipped two agent-runtime hooks in livespec-driver-claude's .claude-plugin/hooks/ bundle, but core's contracts.md — which owns the plugin-distribution contract the Driver binding realizes — does not name them. The originating work-item (lineage livespec-hookimpl / li-zmlkrl; deferred spec leg tracked as livespec-7nmc) requires the hook bundle to be codified via the propose-change → revise lifecycle so the surfaces, the implementation.plugin config gate, the warn-only posture of the Stop hook, and the fail-open discipline become normative contract rather than unstated implementation behavior. The Stop hook is the runtime realization of non-functional-requirements.md §"Completion includes persistence and workspace cleanup"; without a contract anchor, future Driver changes could silently flip a warn into a block or break non-livespec projects with a fail-closed hook.

### Proposed Changes

Insert a new H3 subsection `### Driver-shipped hooks` into `SPECIFICATION/contracts.md` under §"Plugin distribution", placed after the paragraph noting that plugin uninstall/update flows are platform behaviors and immediately BEFORE the existing `### Daily dogfooding path` subsection. The subsection text is exact and complete (no H2 headings are added, changed, or removed, so `tests/heading-coverage.json` is unaffected):

### Driver-shipped hooks

The Claude Code Driver plugin (`livespec-driver-claude`) SHIPS an agent-runtime hook bundle at `.claude-plugin/hooks/`: a `hooks.json` registration plus one shell script per hook, each invoked by the harness as `"${CLAUDE_PLUGIN_ROOT}/hooks/<name>.sh"`. The bundle is Driver-owned runtime mechanics per the Driver-binding partition (`spec.md` §"Contract + reference implementations architecture"): this section states the required hook surfaces and their behavioral disciplines; the script implementations and their tests live in the Driver repo. The bundle carries two hooks:

- **PreToolUse auto-memory redirect** (`block-auto-memory.sh`). Registered on the `Write` tool; the effective matcher is `Write(**/memory/*.md)` — the hook acts only when the written file's immediate parent directory is `memory` and the filename ends in `.md` (the Claude Code auto-memory layout, `~/.claude/projects/<slug>/memory/*.md`). When such a write occurs AND the governed project (resolved via `CLAUDE_PROJECT_DIR`) carries a `.livespec.jsonc` whose `implementation.plugin` key names an active impl-plugin, the hook emits a block decision (PreToolUse `permissionDecision: deny`) whose reason redirects the agent to the active impl-plugin's `/<plugin>:capture-memo` skill, so in-flight observations land in the durable memo store instead of harness-private auto-memory files. The redirect target MUST be resolved from `implementation.plugin` — never hardcoded to any one impl-plugin. The presence of a non-empty `implementation.plugin` value is the SOLE config gate (the `memos_path` gate named in the originating work-item predates the orchestrator-substrate migration and is retired; the memo substrate is orchestrator-private).

- **Stop plan-persistence WARN** (`warn-plan-persistence.sh`). Registered on the `Stop` event; scans the agent's last turn — the transcript entries after the last REAL user message (tool-result deliveries do not reset the window) — for substantial planning artifacts via mechanical thresholds (3+ markdown headings, 5+ table rows, or 10+ list items in the aggregated assistant text). When such an artifact exists and NO file-persisting tool call (`Write` / `Edit` / `MultiEdit` / `NotebookEdit`) happened in the same window, the hook emits a `systemMessage` warning directing the agent to persist the plan (a plan/doc file, or work-items via the active impl-plugin) before moving on. The hook is WARN-ONLY by contract: it MUST NOT block the stop (it never emits a `decision` key and never exits non-zero) and MUST NOT auto-file anything. It is the agent-runtime nudge realizing `non-functional-requirements.md` §"Completion includes persistence and workspace cleanup".

**Fail-open discipline (both hooks).** ANY hook failure — `python3` absent from `PATH`, malformed hook-input JSON on stdin, unset `CLAUDE_PROJECT_DIR`, missing/unreadable/unparseable `.livespec.jsonc`, missing or malformed transcript — MUST be a silent pass-through with exit 0. A hook acts only when it POSITIVELY identifies its gating condition. Because the Driver plugin installs globally (per-user, not per-project), the config gate is what scopes hook behavior to livespec-governed projects; the hooks MUST NOT disturb non-livespec projects and MUST NOT break a degraded agent session.

Adding or removing a hook in the Driver bundle, renaming a hook surface, or changing a hook's posture (block vs. warn) requires a propose-change cycle against this section. The mechanical detection internals (matcher predicates, artifact thresholds, persisting-tool set) are Driver implementation detail and MAY be tuned Driver-side without a core spec cycle, provided the posture and gating disciplines above hold.

