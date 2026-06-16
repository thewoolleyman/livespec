# livespec — repo orientation

`livespec` is a system that governs a living natural-language
specification. This repo is livespec CORE: the contract, the
harness-neutral driving prose, the reference spec-side CLIs, the
schemas, and the built-in templates, distributed as the `livespec`
Claude Code plugin (an artifact carrier — it exposes no slash
commands itself). The interactive `/livespec:*` surface ships from
the per-agent-runtime Driver plugin repo
[`livespec-driver-claude`](https://github.com/thewoolleyman/livespec-driver-claude).
The repo dogfoods its own design: livespec's own spec lives at
`SPECIFICATION/` and is itself maintained via the `/livespec:*`
slash commands.

## Repo layout

| Path | Purpose |
|---|---|
| `.claude-plugin/` | Plugin manifest, harness-neutral prose (`prose/`), Python scripts, vendored libs, built-in templates — NO skill bindings (extracted to `livespec-driver-claude`) |
| `SPECIFICATION/` | The live livespec specification (dogfooded; `spec.md`, `contracts.md`, `constraints.md`, `scenarios.md`, `history/`) |
| `dev-tooling/` | Standalone enforcement-suite Python scripts (run via `just check`) |
| `tests/` | pytest suite — mirrors the `.claude-plugin/scripts/` and `dev-tooling/` trees one-to-one |
| `prior-art/` | Reference source material adapted into the shipped livespec template |
| `archive/` | Frozen historical artifacts from the bootstrap process — do not edit |
| `pyproject.toml`, `justfile`, `lefthook.yml`, `.mise.toml`, `.python-version`, `.vendor.jsonc`, `.livespec.jsonc` | Toolchain configuration |
| `NOTICES.md` | Third-party vendoring notices |

## Slash commands and prose

The `/livespec:*` surface exposes eight sub-commands; each is driven
by a harness-neutral prose artifact CORE ships at
`.claude-plugin/prose/<name>.md`:

| Command | Core prose | Purpose |
|---|---|---|
| `/livespec:seed` | `prose/seed.md` | Author the initial natural-language spec |
| `/livespec:propose-change` | `prose/propose-change.md` | File a proposed change against an existing spec |
| `/livespec:critique` | `prose/critique.md` | Surface issues in an existing spec |
| `/livespec:revise` | `prose/revise.md` | Accept, modify, or reject pending proposed changes |
| `/livespec:doctor` | `prose/doctor.md` | Run static + LLM-driven validation against a spec tree |
| `/livespec:prune-history` | `prose/prune-history.md` | Collapse old `history/vNNN/` entries into a pruned-marker |
| `/livespec:next` | `prose/next.md` | Rank the next spec-side action (revise, propose-change, critique, prune-history, or none) over the current proposed_changes/ and history/ state |
| `/livespec:help` | `prose/help.md` | Overview + routing to the right sub-command |

Per `SPECIFICATION/spec.md` §"Contract + reference implementations
architecture", each operation is decomposed into (a) the
harness-neutral core prose artifact above carrying the dialogue
capture, prompt-driven content generation, CLI invocation flow, and
structured-finding interpretation, and (b) a THIN per-agent-runtime
Driver binding. The Claude Code bindings live in the
`livespec-driver-claude` repo (`.claude-plugin/skills/<name>/SKILL.md`
there); each binding resolves CORE's plugin root at runtime (env
override → governed-project checkout → installed `livespec@livespec`
cache), reads the prose, and dispatches the spec-side CLI named in
the governed project's `.livespec.jsonc` `spec_clis` section. Edit
the prose here for behavior; edit the Driver repo's SKILL.md only
for Claude-runtime mechanics. Core ships NO `.claude-plugin/skills/`
tree (guarded by `tests/test_plugin_distribution.py`).

### Cross-repo orchestration — retired Layer-3 skill; now the Dispatcher

The project-local `/livespec-orchestrate` Layer-3 loop-driver skill
(formerly `.claude/skills/livespec-orchestrate/SKILL.md`) and its
`livespec-implementer` dispatch agent were **RETIRED at the W6
dark-factory cutover** (user-declared 2026-06-15). Their successor is
the reference **Beads/Dolt + Fabro orchestrator's Dispatcher**
(`livespec-impl-beads`'s `dispatcher.py`): it polls the Beads ledger,
dispatches each ready work-item into its own Fabro sandbox, runs
`just check` + `/livespec:doctor` as a hard janitor gate, verifies the
merge, and closes the item — carrying routine cross-repo work
unattended.

Per `SPECIFICATION/spec.md` §"Contract + reference implementations
architecture" and `non-functional-requirements.md` §"Orchestrator-internal
Dispatcher guidance", no repository is REQUIRED to carry a cross-repo
loop driver as core contract surface; the Dispatcher's invocation
surface (`mode`/`budget`), janitor hard-gate, and structured iteration
journal are codified in the orchestrator repo's own specification. The
retired skill and agent are recoverable from git history; the duties
they performed and their relocation homes are recorded in
`research/dark-factory-operability/preconditions.md`. Spec-side
`/livespec:*` lifecycle work and host-only self-machinery changes are
driven directly by a maintainer (or surfaced by the Dispatcher for a
human), not by a resident loop skill.

## Agent prerequisites for plugin work

When investigating issues or making changes related to the Claude Code plugin installation, marketplace, or distribution:

1. **Establish execution context first** — Do NOT assume or make changes based on how you think the system works. Instead:
   - Run `claude plugin marketplace list` to see which marketplaces are configured and whether they point to local files or remote repos
   - Understand that changes to local `marketplace.json` will NOT affect installations from remote GitHub marketplaces
   - Read `SPECIFICATION/contracts.md` §"Plugin distribution" to understand the intended contract

2. **Map the execution flow before making changes**:
   - Trace where the actual install command is fetching from (local or remote)
   - Verify that any changes you make will actually affect that code path
   - If the marketplace points to remote GitHub, local changes are irrelevant — you either need to push to GitHub first or test against the local marketplace

3. **Use the correct testing approach**:
   - For remote marketplaces: push changes to GitHub, then test
   - For local marketplaces: use `/plugin marketplace add ./.claude-plugin/marketplace.json` and test against that
   - Never test local changes against a remote marketplace and assume they will work

This prevents wasted effort on changes that have no effect on the actual problem.

## Plugin install (end users)

Core is distributed via a Claude Code marketplace at
`.claude-plugin/marketplace.json` (per `SPECIFICATION/contracts.md`
§"Plugin distribution"); the `/livespec:*` commands ship from the
`livespec-driver-claude` Driver marketplace. Enable BOTH (plus the
impl-plugin named by the project's `.livespec.jsonc`) **at project
scope** by committing a `.claude/settings.json` — so the skills and
the Driver's bundled hooks load only in the governed project, never
machine-wide:

```jsonc
{
  "extraKnownMarketplaces": {
    "livespec":               { "source": { "source": "github", "repo": "thewoolleyman/livespec" } },
    "livespec-driver-claude": { "source": { "source": "github", "repo": "thewoolleyman/livespec-driver-claude" } },
    "livespec-impl-beads":    { "source": { "source": "github", "repo": "thewoolleyman/livespec-impl-beads" } }
  },
  "enabledPlugins": {
    "livespec@livespec": true,
    "livespec@livespec-driver-claude": true,
    "livespec-impl-beads@livespec-impl-beads": true
  }
}
```

After committing the settings (restart Claude Code or `/reload-plugins`),
the eight `/livespec:*` slash commands become available with the
`livespec:` namespace prefix (the Driver plugin is deliberately NAMED
`livespec` so the established surface is preserved; core's plugin
carries the prose, CLIs, and templates the Driver resolves at runtime).
A machine-wide `/plugin install livespec@livespec` +
`/plugin install livespec@livespec-driver-claude` still works but
enables the plugins in EVERY project on the host; prefer the committed
project-scoped form above.

## Daily dogfooding (maintainer development)

When editing the plugin source in this repo, two workflows:

- **Live-reload mode**: launch Claude Code with `claude --plugin-dir .`
  from the repo root. The core plugin loads directly from local source;
  edits to `.claude-plugin/prose/<name>.md` and
  `.claude-plugin/scripts/...` are picked up via `/reload-plugins`
  without re-installing. This is the daily-edit path. The Driver's
  bindings resolve THIS checkout's `.claude-plugin/` automatically
  when the governed project is this repo, so prose/CLI edits take
  effect without touching the installed core cache. (Binding edits
  themselves happen in the `livespec-driver-claude` repo.)
- **Marketplace install path** (verifies the published flow): use the
  install commands above, or
  `/plugin marketplace add ./.claude-plugin/marketplace.json` for the
  local variant. Either copies the plugin into `~/.claude/plugins/cache/`
  and does NOT live-reload — run `/plugin update livespec@livespec` to
  pull changes after editing. Use this path to verify the install flow
  end-to-end before pushing.

The `.claude/skills` symlink (which used to load the skills as
PROJECT-level without the namespace prefix) was removed in v049. The
Driver-plugin marketplace install is now the way the `/livespec:*`
skills load with the correct namespace.

## Beads runtime prerequisites (what `just bootstrap` does NOT provision)

`just ensure-plugins` installs the `livespec-impl-beads` *plugin*, but the beads
backend also needs host-level runtime that bootstrap canNOT provision. A fresh
clone connects to its beads tenant only when all of the following are present:

- **`bd` CLI, pinned v1.0.5**, at `/usr/local/bin/bd`, with `LIVESPEC_BD_PATH`
  pointing at it (the impl-beads wrappers shell out to `$LIVESPEC_BD_PATH`).
- **A running Dolt `sql-server`** reachable over **TCP `127.0.0.1:3307`**. The
  family tenants force TCP (not the unix socket): `/var/lib/doltdb/` is `0750
  dolt:dolt` and untraversable by the sandboxed caller, so `.beads/config.yaml`
  carries `dolt.*` host/port keys with NO `socket` key.
- **The per-tenant password** in env as
  `BEADS_DOLT_PASSWORD_<tenant_underscores>` (tenant DB name == repo name),
  injected by the livespec 1Password Environment wrapper `with-livespec-env.sh`
  (canonical copy at `/data/projects/1password-env-wrapper/with-livespec-env.sh`).
  Secrets are probe-only — `printenv NAME | wc -c`, never echo values — and
  NEVER committed to `.livespec.jsonc` or `.beads/`.
- **The `.beads/` pointer files** in the repo: `config.yaml` (committed; carries
  the `dolt.*` server keys) and `metadata.json` (gitignored). `metadata.json` is
  REGENERABLE — `project_id` is server-stable, so re-running `bd init --server …`
  in a `/tmp` scratch dir with the repo's `config.yaml` yields the identical
  `project_id`; copy its `metadata.json` into the repo. NEVER run `bd init` inside
  a primary checkout or worktree — it auto-commits and clobbers `.beads/`.

This is the bridge between "plugin installed" and "backend actually connects":
without the Dolt server + bd binary + tenant secret + `.beads/` pointers, `bd
list` fails with "no beads database found" even though the plugin is present.

## Daily commands

- `just bootstrap` — first-touch setup on fresh clones; idempotently sets `livespec.primaryPath` on the primary checkout and installs the canonical commit-refuse hook at `.git/hooks/pre-commit` + `.git/hooks/pre-push` (per `SPECIFICATION/non-functional-requirements.md` §"Primary-checkout commit-refuse hook" / §"Commit-refuse hook bootstrap procedure") plus installs lefthook hooks and resolves plugin dependencies.
- `just check` — full enforcement aggregate (lint, types, tests, coverage, AST checks).
- `just check-pre-commit-doc-only` — fast subset for doc-only commits.
- **Cross-repo orchestration** is carried by the reference **Beads/Dolt + Fabro Dispatcher** (`livespec-impl-beads`'s `dispatcher.py`), which retired the project-local `/livespec-orchestrate` Layer-3 skill at the W6 cutover (2026-06-15). The dark factory polls the ledger, dispatches ready work-items into Fabro sandboxes, gates each on `just check` + `/livespec:doctor`, and closes merged items unattended. See `### Cross-repo orchestration` above.

`just check` is the load-bearing safety net; it runs locally, in
pre-push, and in CI. The doc-only subset is invoked only by lefthook
pre-commit when zero `.py` files are staged.

## Revise co-edit discipline — `tests/heading-coverage.json`

Per `SPECIFICATION/spec.md` §"Self-application", every revise pass
that adds, changes, or removes a `## ` heading in any spec file MUST
update `tests/heading-coverage.json` via the same `resulting_files[]`
mechanism so the test-coverage map stays in lockstep with the spec.
When drafting a revise payload that touches a spec file's H2 set:

1. Diff the proposed `## ` heading set against the current spec
   file's H2 set.
2. For each added heading, include a `TODO` + `reason` entry in
   `tests/heading-coverage.json` (the v064 pattern); for each
   removed heading, drop the corresponding entry; for renamed
   headings, update the `heading` field.
3. Include `tests/heading-coverage.json` in the revise payload's
   `resulting_files[]` (path spelled as `../tests/heading-coverage.json`
   when `--spec-target` is the main `SPECIFICATION/` tree, so the
   wrapper's `spec_target / path` join resolves it to the project-
   root-relative file). Pre-commit's `check-heading-coverage` is the
   mechanical guard, but catching the omission at payload-assembly
   time keeps the revise commit atomic.

## Historical context

`archive/` contains the bootstrap-process artifacts: the design
brainstorming archive, the bootstrap PLAN, the bootstrap skill bundle
(removed at Phase 11), the per-phase STATUS / decisions / open-issues
logs, and the v032 quality-comparison report. The live spec at
`SPECIFICATION/` is the canonical authoritative source for current
design intent — `archive/` is reference-only.

## Red-Green-Replay commit protocol

Product `.py` changes are committed via a 2-step single-commit TDD ritual,
enforced by the `red_green_replay` commit-refuse hook (it inspects the staged
tree and writes `TDD-*` trailers). The final result is ONE commit carrying the
test, the impl, and both trailer sets.

1. **Red commit.** Stage the test file ALONE — no impl — and commit with a
   `fix:`/`feat:` subject. The hook runs pytest on the staged tree; the staged
   test MUST fail on pytest (non-zero exit). An `ImportError` or a collection
   error counts as a failure to the hook, BUT you SHOULD prefer a genuine
   assertion failure so Red proves the behavior is actually unimplemented
   rather than merely unimportable — see the new-module stub technique below.
   It records `TDD-Red-*` trailers (test path, failure reason, test-file
   checksum, output checksum, captured-at).
   - Gotcha: the impl must be UNMODIFIED on disk at the Red commit, because the
     hook's pytest reads the on-disk module. If the impl already carries the
     change the test passes, and the hook rejects with `test-passed-at-red`.
2. **Green amend.** Stage the impl and run `git commit --amend`. The hook sees
   the `TDD-Red-*` trailers + the staged impl, re-runs the SAME test (now
   passing), and records `TDD-Green-*` trailers. The test file bytes MUST be
   byte-identical across the Red→Green pair; to change the test, author a fresh
   Red commit.

### New-module stub technique (avoiding false reds)

When the impl module under test does NOT exist yet, the natural Red would be an
`ImportError` or a collection error rather than an assertion failure. The hook
accepts that as a failing Red, but it does not prove the behavior is
unimplemented — only that the module is unimportable. To make Red fail on a
genuine assertion instead:

1. At Red time, create the impl module as a minimal **stub** on disk — enough
   that the test imports and runs, but its assertion FAILS (e.g. a function
   that returns a wrong/sentinel value, or raises `NotImplementedError` only
   when that still yields an assertion failure rather than a collection error).
2. The stub must NOT make the test pass — a passing test at Red trips the
   hook's `test-passed-at-red` gate.
3. Then the **Green amend** replaces the stub with the real implementation that
   makes the assertion pass.

This keeps Red honest: it proves the behavior is unimplemented, not merely that
the module is missing.

**Exempt:** changesets with no product `.py` (docs, spec, work-items, shell,
config) use `chore(...)` / `docs(...)` / `chore(spec):` subjects and skip the
ritual entirely. Always use `mise exec -- git ...` so the hooks fire; never
pass `--no-verify`.
