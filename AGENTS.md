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

The plugin exposes seven sub-commands; each is backed by a skill at
`.claude-plugin/skills/<name>/SKILL.md`:

| Command | Skill | Purpose |
|---|---|---|
| `/livespec:seed` | `skills/seed/SKILL.md` | Author the initial natural-language spec |
| `/livespec:propose-change` | `skills/propose-change/SKILL.md` | File a proposed change against an existing spec |
| `/livespec:critique` | `skills/critique/SKILL.md` | Surface issues in an existing spec |
| `/livespec:revise` | `skills/revise/SKILL.md` | Accept, modify, or reject pending proposed changes |
| `/livespec:doctor` | `skills/doctor/SKILL.md` | Run static + LLM-driven validation against a spec tree |
| `/livespec:prune-history` | `skills/prune-history/SKILL.md` | Collapse old `history/vNNN/` entries into a pruned-marker |
| `/livespec:help` | `skills/help/SKILL.md` | Overview + routing to the right sub-command |

Each skill orchestrates dialogue capture, prompt-driven content
generation, wrapper invocation against `.claude-plugin/scripts/bin/<sub-command>.py`,
and structured-finding interpretation.

## Plugin install (end users)

The plugin is distributed via a Claude Code marketplace at
`.claude-plugin/marketplace.json` (per `SPECIFICATION/contracts.md`
§"Plugin distribution"). Install with:

```
/plugin marketplace add thewoolleyman/livespec
/plugin install livespec@livespec
```

After install, the seven `/livespec:*` slash commands become available
with the `livespec:` namespace prefix.

## Daily dogfooding (maintainer development)

When editing the plugin source in this repo, two workflows:

- **Live-reload mode**: launch Claude Code with `claude --plugin-dir .`
  from the repo root. Plugin loads directly from local source; edits to
  `.claude-plugin/skills/<name>/SKILL.md` and `.claude-plugin/scripts/...`
  are picked up via `/reload-plugins` without re-installing. This is the
  daily-edit path.
- **Marketplace install path** (verifies the published flow): use the
  install commands above, or
  `/plugin marketplace add ./.claude-plugin/marketplace.json` for the
  local variant. Either copies the plugin into `~/.claude/plugins/cache/`
  and does NOT live-reload — run `/plugin update livespec@livespec` to
  pull changes after editing. Use this path to verify the install flow
  end-to-end before pushing.

The `.claude/skills` symlink (which used to load the plugin's skills as
PROJECT-level without the namespace prefix) was removed in v049. The
marketplace install or `--plugin-dir` is now the only way the plugin's
skills load with the correct `/livespec:*` namespace.

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
