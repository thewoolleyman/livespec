# livespec — repo orientation

`livespec` is a Claude Code plugin that governs a living natural-language
specification. The repo dogfoods its own design: the plugin's own spec
lives at `SPECIFICATION/` and is itself maintained via the plugin's
`/livespec:*` slash commands.

## Repo layout

| Path | Purpose |
|---|---|
| `.claude-plugin/` | Plugin manifest, skill prompts, Python scripts, vendored libs, built-in templates |
| `SPECIFICATION/` | The live livespec specification (dogfooded; `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`, `history/`) |
| `dev-tooling/` | Standalone enforcement-suite Python scripts (run via `just check`) |
| `tests/` | pytest suite — mirrors the `.claude-plugin/scripts/` and `dev-tooling/` trees one-to-one |
| `prior-art/` | Reference source material adapted into the shipped livespec template |
| `archive/` | Frozen historical artifacts from the bootstrap process — do not edit |
| `pyproject.toml`, `justfile`, `lefthook.yml`, `.mise.toml`, `.python-version`, `.vendor.jsonc`, `.livespec.jsonc` | Toolchain configuration |
| `NOTICES.md` | Third-party vendoring notices |

## Slash commands and skills

The plugin exposes six sub-commands; each is backed by a skill at
`.claude-plugin/skills/<name>/SKILL.md`:

| Command | Skill | Purpose |
|---|---|---|
| `/livespec:seed` | `skills/seed/SKILL.md` | Author the initial natural-language spec |
| `/livespec:propose-change` | `skills/propose-change/SKILL.md` | File a proposed change against an existing spec |
| `/livespec:critique` | `skills/critique/SKILL.md` | Surface issues in an existing spec |
| `/livespec:revise` | `skills/revise/SKILL.md` | Accept, modify, or reject pending proposed changes |
| `/livespec:doctor` | `skills/doctor/SKILL.md` | Run static + LLM-driven validation against a spec tree |
| `/livespec:prune-history` | `skills/prune-history/SKILL.md` | Collapse old `history/vNNN/` entries into a pruned-marker |

Each skill orchestrates dialogue capture, prompt-driven content
generation, wrapper invocation against `.claude-plugin/scripts/bin/<sub-command>.py`,
and structured-finding interpretation.

## Daily commands

- `just check` — full enforcement aggregate (lint, types, tests, coverage, AST checks).
- `just check-pre-commit-doc-only` — fast subset for doc-only commits.

`just check` is the load-bearing safety net; it runs locally, in
pre-push, and in CI. The doc-only subset is invoked only by lefthook
pre-commit when zero `.py` files are staged.

## Historical context

`archive/` contains the bootstrap-process artifacts: the design
brainstorming archive, the bootstrap PLAN, the bootstrap skill bundle
(removed at Phase 11), the per-phase STATUS / decisions / open-issues
logs, and the v032 quality-comparison report. The live spec at
`SPECIFICATION/` is the canonical authoritative source for current
design intent — `archive/` is reference-only.
