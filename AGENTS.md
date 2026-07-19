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
| `archive/` | Frozen historical artifacts — bootstrap-process records, plus retired research topics under `archive/research/` and retired prompt handoffs under `archive/prompts/` — do not edit |
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
(`livespec-orchestrator-beads-fabro`'s `dispatcher.py`): it polls the Beads ledger,
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
`archive/research/dark-factory-operability/preconditions.md`. Spec-side
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
    "livespec":               { "source": { "source": "github", "repo": "thewoolleyman/livespec", "ref": "release" } },
    "livespec-driver-claude": { "source": { "source": "github", "repo": "thewoolleyman/livespec-driver-claude", "ref": "release" } },
    "livespec-orchestrator-beads-fabro":    { "source": { "source": "github", "repo": "thewoolleyman/livespec-orchestrator-beads-fabro", "ref": "release" } }
  },
  "enabledPlugins": {
    "livespec@livespec": true,
    "livespec@livespec-driver-claude": true,
    "livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro": true
  }
}
```

Committing the settings is NOT enough on its own. `enabledPlugins`
enables a plugin that is already installed; it installs nothing. Each
enabled plugin must ALSO be installed into project scope, from the
project root:

```bash
claude plugin install livespec@livespec -s project
claude plugin install livespec@livespec-driver-claude -s project
claude plugin install livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro -s project
```

`-s project` keeps the install scoped to this project; the default
`-s user` installs into EVERY project on the host. `install` exits 0
when already installed, so the step is idempotent. This repo automates
exactly this via `just ensure-plugins`
(`livespec_dev_tooling/fleet/ensure_plugins.py`, which derives the set
from the committed settings and runs `install` then `update`); a
third-party adopter with no justfile must run the commands above.

Verify before relying on it: for every `enabledPlugins` key,
`~/.claude/plugins/installed_plugins.json` must hold an entry whose
`projectPath` equals this project's root. Enabled-but-not-installed
resolves no operations and reports no error, and a zero exit status
does not prove the right project was touched — see
`SPECIFICATION/contracts.md` §"Plugin distribution" (install
verification) for the invariant and the `-s project` resolution caveat.

Then restart Claude Code or run `/reload-plugins` — a freshly
installed plugin does not load into the session that installed it —
and the eight `/livespec:*` slash commands become available with the
`livespec:` namespace prefix (the Driver plugin is deliberately NAMED
`livespec` so the established surface is preserved; core's plugin
carries the prose, CLIs, and templates the Driver resolves at runtime).

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

## Codex dogfooding (OpenAI Codex CLI/TUI)

Core is ALSO Codex-installable, so the same eight `/livespec:*` spec-side
operations can be dogfooded from OpenAI Codex CLI/TUI. The model mirrors
the Claude path — core is the artifact carrier (prose + wrappers, no
skills of its own) and a per-runtime Driver supplies the command surface
— with one key asymmetry: Codex plugin enablement is **HOST-WIDE**, not
project-scoped.

Install the core plugin, the `livespec-driver-codex` Driver, and the
governed project's orchestrator plugin host-wide:

```bash
# Core (artifact carrier — ships prose/wrappers, no skills of its own):
codex plugin marketplace add thewoolleyman/livespec --ref release
codex plugin add livespec@livespec

# The Codex Driver (supplies the /livespec:* operation surface):
codex plugin marketplace add thewoolleyman/livespec-driver-codex --ref release
codex plugin add livespec@livespec-driver-codex

# The selected orchestrator plugin (supplies its own Codex skills):
codex plugin marketplace add thewoolleyman/livespec-orchestrator-beads-fabro --ref release
codex plugin add livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro
```

These registrations persist HOST-WIDE in `~/.codex/config.toml` (a
`[marketplaces.<name>]` entry plus a `[plugins."<plugin>@<marketplace>"]
enabled = true` entry) and apply to EVERY project on the host — Codex
offers no project-scoped plugin enablement, so there is no committed
`.claude/settings.json` analogue for the Codex path. This is asymmetric
to the Claude install above, which enables plugins PER PROJECT via a
committed `.claude/settings.json`. See `SPECIFICATION/contracts.md`
§"Plugin distribution" for the authoritative install contract.

Once installed, the eight spec-side operations (`seed`, `propose-change`,
`critique`, `revise`, `doctor`, `prune-history`, `help`, `next`) are
driven from Codex via `codex exec`. They are NAME-selected as
`livespec:<op>` (e.g. `livespec:next`) rather than as `/`-prefixed slash
commands; `codex exec` resolves the Codex Driver binding, which reads
CORE's harness-neutral prose (`.claude-plugin/prose/<name>.md`) and
invokes the spec-side wrapper under `.claude-plugin/scripts/bin/` named
in the governed project's `.livespec.jsonc`. The orchestrator plugin
adds its own Codex skills (`orchestrate`, `next`, `list-work-items`,
`detect-impl-gaps`, `capture-work-item`, `capture-impl-gaps`,
`capture-spec-drift`, `implement`, `groom`) under its plugin name. No
`AGENTS.md` skill→prose mapping is needed — the distributed Drivers
resolve their prose themselves (per
`SPECIFICATION/non-functional-requirements.md` §"Codex dogfooding
contracts").

The Codex TUI picker is a different surface from the colon-qualified
name-selection form. In `/skills` → `List skills` (or the `@` picker),
search by the short skill name, e.g. `orchestrate`; Codex renders the
owning plugin as context, e.g.
`orchestrate (livespec-orchestrator-beads-fabro)` with kind `Skill`.
The colon-qualified form (`livespec-orchestrator-beads-fabro:orchestrate`)
is for prompt / `codex exec` name selection and model-visible skill
references, not the picker row operators should expect.

Daily-dogfooding note: core ships the Codex packaging the Driver
resolves — a Codex marketplace catalog at `.agents/plugins/marketplace.json`
plus the paired `.claude-plugin/.codex-plugin/plugin.json`, both pointing
at the SAME `prose/` and `scripts/` the Claude marketplace ships (a
single cross-runtime artifact; no prose, wrapper, schema, or template is
duplicated). Editing core prose under `.claude-plugin/prose/<name>.md`
therefore changes behavior on BOTH runtimes; Codex Driver binding edits
themselves happen in the `livespec-driver-codex` repo, just as Claude
binding edits happen in `livespec-driver-claude`. Per
`SPECIFICATION/non-functional-requirements.md` §"Codex dogfooding
constraints", Codex-native plugin support is claimed only once the
registration creates an installed `livespec` plugin entry in
`~/.codex/config.toml` AND a `codex exec` invocation drives a `/livespec:*`
operation through it; a temporary local Codex marketplace registration
used for testing MUST be removed afterward unless you ask to keep it.

## Repository mutation protocol

Every repo change uses a worktree → PR → merge → cleanup path. Treat
leaving dirty state, committing on the primary checkout, or asking the
user whether to commit as failures of the workflow, not as acceptable
stopping points.

1. Confirm the primary checkout before editing (a primary checkout's
   git-dir equals its git-common-dir; a secondary worktree's differs —
   the structural test the commit-refuse hook itself uses):

   ```bash
   git -C /data/projects/livespec rev-parse --git-dir --git-common-dir
   git -C /data/projects/livespec status --short --branch
   ```

2. If the change will modify tracked files, create a dedicated worktree
   from the primary checkout's `master` and do all edits there. Every
   worktree lives under the per-user root `~/.worktrees/<repo>/<branch>`
   — NEVER as a peer of the clones under `/data/projects`, so the
   workspace holds only first-class clones:

   ```bash
   mise exec -- git -C /data/projects/livespec worktree add -b <branch> "$HOME/.worktrees/livespec/<branch>" master
   ```

   `just bootstrap` registers `~/.worktrees` as one of mise's
   `trusted_config_paths`, so a freshly created worktree's `.mise.toml`
   is auto-trusted and the first `mise exec` inside it never stalls on a
   "config not trusted" prompt.

3. Use `mise exec -- git commit ...` and `mise exec -- git push ...` so
   the mise-managed lefthook hooks actually run. Never pass
   `--no-verify`; if a hook fails, fix the cause or halt with the
   failure.
4. Open a PR, wait for required checks, and merge through the PR using
   the repo's rebase-merge discipline.
5. After merge, refresh `/data/projects/livespec` to `origin/master`,
   remove the feature worktree, delete the local branch, and verify the
   primary checkout is clean on `master`.

Do not leave orphaned worktrees. If a session must stop before cleanup,
record the active worktree path, branch, PR, validation state, and next
action in the relevant handoff document. For stale cleanup outside the
current branch's own worktree, use the repo's reaper entry point
(`just reap-stale-worktrees` or `just reap-stale-worktrees <repo>
--dry-run`) rather than hand-deleting unfamiliar state.

## Beads runtime prerequisites (what `just bootstrap` does NOT provision)

`just ensure-plugins` installs the `livespec-orchestrator-beads-fabro` *plugin*, but the beads
backend also needs host-level runtime that bootstrap canNOT provision. A fresh
clone connects to its beads tenant only when all of the following are present:

- **`bd` CLI, pinned v1.0.5**, at `/usr/local/bin/bd`, with `LIVESPEC_BD_PATH`
  pointing at it (the impl-beads wrappers shell out to `$LIVESPEC_BD_PATH`).
- **A running Dolt `sql-server`** reachable over **TCP `127.0.0.1:3307`**. The
  fleet tenants force TCP (not the unix socket): `/var/lib/doltdb/` is `0750
  dolt:dolt` and untraversable by the sandboxed caller, so `.beads/config.yaml`
  carries `dolt.*` host/port keys with NO `socket` key.
- **The tenant password** in env as a single **bare `BEADS_DOLT_PASSWORD`** —
  injected by THIS project's configured `credential_wrapper` (the `.livespec.jsonc`
  key naming the project's conforming credential-injection wrapper; the fleet
  reference default is the 1Password Environment wrapper `with-livespec-env.sh`).
  A FLEET tenant shares the
  one fleet password (members of the single livespec 1Password Environment) via
  the livespec 1Password Environment wrapper `with-livespec-env.sh` (canonical
  copy at `/data/projects/1password-env-wrapper/with-livespec-env.sh`); an
  INDEPENDENT (non-fleet) tenant injects its own tenant password from its own
  1Password Environment via its own `with-<project>-env.sh` wrapper. Either way
  `bd` consumes the same bare var — there is NO per-tenant
  `BEADS_DOLT_PASSWORD_<tenant>` suffix and NO per-tenant→bare mapping. Real
  isolation comes from the per-tenant SQL user + DB-scoped grant, not from
  password distinctness or wrapper identity. Secrets are probe-only — `printenv
  NAME | wc -c`, never echo values — and NEVER committed to `.livespec.jsonc` or
  `.beads/`.
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

- `just bootstrap` — first-touch setup on fresh clones; idempotently installs the canonical structural commit-refuse hook at `.git/hooks/pre-commit`, `.git/hooks/pre-push`, and `.git/hooks/commit-msg` (per `SPECIFICATION/non-functional-requirements.md` §"Primary-checkout commit-refuse hook" / §"Commit-refuse hook bootstrap procedure") — armed on install, refusing commits/pushes at the primary checkout structurally (when `git rev-parse --git-dir` equals `git rev-parse --git-common-dir`), with no `livespec.primaryPath` arming step — plus installs lefthook hooks and resolves plugin dependencies.
- `just check` — full enforcement aggregate (lint, types, tests, coverage, AST checks).
- `just check-pre-commit-doc-only` — fast subset for doc-only commits.
- **Cross-repo orchestration** is carried by the reference **Beads/Dolt + Fabro Dispatcher** (`livespec-orchestrator-beads-fabro`'s `dispatcher.py`), which retired the project-local `/livespec-orchestrate` Layer-3 skill at the W6 cutover (2026-06-15). The dark factory polls the ledger, dispatches ready work-items into Fabro sandboxes, gates each on `just check` + `/livespec:doctor`, and closes merged items unattended. See `### Cross-repo orchestration` above.

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

### Execution gotchas

Three failure modes that cost dispatched agents real time:

1. **Multi-test-file Red.** The Red commit must stage EXACTLY ONE test file
   (zero impl). The commit-msg `red_green_replay` hook rejects more than one
   staged test file with `multi-test-file`, AND lefthook's pre-commit only takes
   the fast coverage-skip Red path when `test_count == 1 && impl_count == 0`
   (otherwise it runs full `just check` and fails at <100% coverage). When a
   change needs multiple new/changed test files, stage only ONE at Red (a genuine
   failing assertion), then add the remaining test files + the impl + ride-along
   docs at the Green `--amend`. (The old `LIVESPEC_PRECOMMIT_RED_MODE` env
   override is gone.)
2. **Preserve the Red trailer block at Green.** On the Green `git commit
   --amend`, do NOT pass a fresh `-m` that overwrites the message — that wipes the
   inline `TDD-Red-*` trailers the hook wrote at Red. The pre-push *range* replay
   check greps the FINAL commit body for BOTH `TDD-Red-Test-File-Checksum:` AND
   `TDD-Green-Verified-At:`; if the Red block is gone, the push is rejected. Use
   `--amend --no-edit` (or re-include BOTH trailer blocks). The Red and Green
   test-file bytes must stay byte-identical.
3. **Working-tree gate, not just staged.** lefthook's pre-commit runs the
   structural / dev-tooling checks over the WORKING TREE, not only the staged set.
   So "revert only the impl for Red" is INSUFFICIENT when the change also ADDS
   files that a working-tree gate inspects (e.g. a new structural check that
   asserts certain dirs are absent, while you've already created those dirs on
   disk). At Red, make the WHOLE working tree master-consistent: move new
   untracked files aside (e.g. to scratch) and revert modified non-test files,
   leaving only the one staged test divergent; then restore everything for the
   Green `--amend`.

**Exempt:** changesets with no product `.py` (docs, spec, work-items, shell,
config) use `chore(...)` / `docs(...)` / `chore(spec):` subjects and skip the
ritual entirely. Always use `mise exec -- git ...` so the hooks fire; never
pass `--no-verify`.

## Agent-instruction `.ai/` convention

Durable, non-ephemeral agent guidance in this repo lives in `AGENTS.md` and — for
detail that would bloat it — in sibling **`.ai/<topic>.md`** files referenced from
here, loaded **progressively** (only when working on that topic, so the
always-loaded `AGENTS.md` stays small). A `.ai/` directory is supported at ANY
directory level, beside that level's `AGENTS.md` and its symlinked
`.claude/CLAUDE.md`; nested topics are additive (a deeper topic augments, never
overrides, an ancestor topic of the same name). NEVER persist durable guidance to
the harness-private per-session local-memory store
(`~/.claude/projects/<slug>/memory/*.md`) — it is ephemeral, per-user, and
invisible to other agents and runtimes. This is the core contract
`SPECIFICATION/contracts.md` §"Fleet agent-instruction core"; the Driver-shipped
`block-auto-memory` hook intent-routes a blocked memory write to this home.

Referenced `.ai/<topic>.md` files (every reference here MUST resolve to an
existing file):

- **`.ai/agent-disciplines.md`** — read when ending a session or applying a
  cross-cutting discipline (TDD red-green-replay, the worktree → PR flow, the
  1Password secret-wrapper, no-local-memory), and for the session-end
  standing-handoff print rule.
- **`.ai/adding-an-adopter.md`** — read BEFORE touching
  `.livespec-fleet-manifest.jsonc` to register a new adopter repo, and before
  planning or driving any adopter's onboarding (registration is
  fleet-maintainer work HERE; onboarding is END-USER work in the adopter repo
  via `docs/installation.md` → `docs/livespec-installation-prompt.md`).
- **`.ai/ci-gate-discipline.md`** — read BEFORE touching any CI-green or
  merge-blocking gate (e.g. `check-master-ci-green`) and whenever such a gate
  blocks a repair. NEVER add a lever/env-var/escape mechanism to such a gate
  or demote it to warning — revert the breaking change (server-side revert PR
  when local commits are blocked) and re-land in the right order.
- **`.ai/beads-gaps-workarounds.md`** — read when integrating with, working
  around, or debugging the `bd` (beads) work-items backend, and before filing
  a beads issue upstream: the living catalogue of beads gaps and the
  workarounds the fleet carries, one upstream-liftable entry per gap.
- **`.ai/no-circular-dependency.md`** — read BEFORE adding any cross-repo
  check, tool, or read to a fleet repo. The No-Circular-Dependency Directive:
  a foundational/upstream repo (e.g. `livespec-dev-tooling`) must NEVER read
  INTO a downstream consumer; cross-repo consistency checks live on the
  consumer side reading the producer, or the coupling is designed away.

## Working with the maintainer

- **The maintainer is not a Python developer** (though fluent in general software
  engineering). When explaining Python, spell out language basics and idioms
  (`class`, `def`, `pass`, `self`, `__init__`, `super()`, decorators, tuples,
  dunder/magic methods, `match`, descriptors) and why each is needed. Never
  abbreviate code with `# ...` or ellipses — show complete bodies, and show
  alternatives in full.
- **Lead with the plain-language bottom line.** Open every explanation, finding,
  or decision question with one or two concrete sentences before any detail or
  options. The maintainer is not a Python/SQL/Dolt/infra expert: define every
  domain term inside the question, answer the literal question the jargon
  raises, and never put a decision in undefined jargon — prefer "here's my
  recommendation plus the plain trade-offs" over a bare jargon picker.
- **Name the repo in every artifact reference.** The fleet spans many sibling
  repos, and work driven from a session in one repo routinely lands artifacts
  in another. When citing any file, PR, branch, or commit the maintainer might
  look up — a review handoff, a gate presentation, a status report — state the
  owning repository explicitly and prefer a full clickable GitHub URL
  (`https://github.com/thewoolleyman/<repo>/blob/<branch>/<path>`) over a bare
  repo-relative path; "on master" is meaningless without the repo. When the
  maintainer will review locally, name which clone to pull. Never assume the
  session's cwd repo is the reader's mental default. **NEVER abbreviate a repo to
  a family-suffix shorthand that more than one repo shares — this is a hard ban,
  in prose to the maintainer exactly as much as in commands.** The bare word
  **`beads-fabro` is BANNED as a standalone repo name** because TWO repos end in
  it — `livespec-orchestrator-beads-fabro` (the orchestrator plugin) and
  `livespec-console-beads-fabro` (the operator console app); always write the FULL
  name so the maintainer never has to guess which. The same applies to any shared
  suffix (`orchestrator`, `driver`, `git-jsonl`): write
  `livespec-orchestrator-git-jsonl`, `livespec-driver-claude`,
  `livespec-driver-codex` in full, every time.
- **Always recommend.** In any interview or critique dialogue, never present
  options as a neutral menu: lead with an explicit recommended option (first,
  labeled "Recommended"), state the reasoning, and yield gracefully if challenged.
- **Prefer structured pickers over free-form prose questions.** When prompting the
  maintainer for a decision, use the harness's structured multiple-choice picker
  (Claude Code: the `AskUserQuestion` tool) with a clearly-recommended first option —
  do NOT ask free-form prose questions the maintainer must type answers to. Reserve
  prose for stating self-resolved actions and findings.
- **Honest pushback over agreement.** When the maintainer challenges a
  recommendation or says "don't just agree with me / are we over-specifying,"
  reconsider substantively against the project's principles (architecture-not-
  mechanism, recreatability) — reshape if they're right, explain with specifics
  if they're wrong; never capitulate reflexively, and re-check your later edits
  against the new disposition.
- **Questions are not directives.** When a message is interrogative ("why X?",
  "what about Y?"), answer it and stop; act only on a clear imperative.
- **No human-scale time framings.** Avoid "from day one", "daily", "over time",
  "eventually", "stabilized through cycles" in commits, docs, work-items, spec,
  or summaries — agent work happens in minutes; prefer event/state-based
  phrasing (concrete dates that appear in artifacts are fine).
- **Spell out "non-functional-requirements" in full** — never abbreviate it as
  "NFR" anywhere.
- **Spell out "Definition-of-Ready" in full** — the acronym "DoR" is BANNED
  (maintainer-declared 2026-07-04: non-intuitive, carries no meaning). Never
  use it in any prose, document, work-item, commit, or report; always write
  "Definition-of-Ready". (Quoting pre-existing text verbatim for mechanical
  replacement targeting is the only exception.)
- **Maintainer-facing documents must explain their own notation.** Define
  every symbol before or beside its first use (an arrow, a column, a tally),
  make headings match their content (a list titled "the 7 X" must contain
  seven X — or say why it doesn't), and write complete sentences over
  compressed fragments. A reviewing maintainer should never have to ask
  "what are the arrows for?"

## When to ask, proceed, or self-resolve

- **Ask one thing at a time.** When walking a structured list (critiques, TODOs,
  decisions), ask exactly one question per turn — never batch sub-items unless
  the maintainer groups them.
- **Only ask on genuine doubt.** Self-resolve trivial wording fixes,
  internal-consistency repairs, and items clearly aligned with established
  preferences; reserve user gates for genuine architectural trade-offs or real
  intent ambiguity. Present each self-resolved item with its disposition.
- **One investigation, one finding, one question.** When a focused investigation
  surfaces unrelated discrepancies, finish the original question first and
  surface only the load-bearing finding; log side observations briefly. Cosmetic
  drift never blocks on its own; genuinely independent decisions are asked
  sequentially.
- **Don't halt on simple typos.** A spec typo with one obviously-correct fix
  aligned with adjacent rules: propose the fix via the normal cycle and proceed.
- **Research before gating.** If a question is answerable by reading docs or
  testing on a live system, do that, decide, implement, and report for
  objection — don't offload an answerable technical decision to the maintainer.
  Reserve gates for genuine product/values calls, irreversible or outward-facing
  actions, and secret/host-mutation authorization.
- **Prescribed destructive ops are pre-authorized.** When a destructive git op
  is the codified mechanism of an adopted workflow (e.g. the `git commit --amend`
  of the Red→Green step), the adoption is the authorization — proceed without
  per-instance confirmation. Keep per-instance gating for ad-hoc `--amend`,
  force-push, `reset --hard`, or `branch -D` on unmerged branches.
- **Fast-forward mode.** When told to "fast-forward" a named scope, run its steps
  back-to-back without per-step gates while still running all correctness/safety
  scans and the established commit pattern; stop only on a blocking issue,
  genuine ambiguity, a phase boundary, or an unauthorized destructive op.

## Python and code conventions

- **uv is the Python toolchain.** uv owns the Python version (`uv python pin`)
  and all packages (`pyproject.toml` dev group + `uv sync`); mise pins only
  non-Python binaries (`uv`, `just`, `lefthook`). Never recommend
  pip/pipx/poetry/pip-tools.
- **Strongest reasonable guardrails for agent-authored Python**: pyright strict,
  Result/Railway-Oriented error handling, mechanically-enforced loose coupling
  and high cohesion — the burden of justification sits on looser options. Most
  style rules (keyword-only args, no inheritance / use `Protocol`, no `raise`
  outside `io/`, comment discipline) are enforced by the `dev-tooling` checks in
  `just check`; follow the surrounding code and let the checks teach the edges.
- **Domain errors vs. bugs.** Route only EXPECTED errors (external/user/
  environment/timing failures that retry could fix) through the Result failure
  track; let bugs propagate as raised exceptions to the outermost supervisor
  (log + exit 1). Wrap `@safe`/`@impure_safe` around specific expected exception
  types, never blanket-catch; `assert` for invariants.
- **Specify architecture, not mechanism.** In architecture-constrained specs,
  constrain languages/versions, tooling gates, public-API type guarantees,
  structural boundaries, and externally-visible invariants — not internal
  composition. For each implementation-mechanism sentence ask "could this be
  deleted without losing the guardrail?"; if an AST/type/style check already
  enforces it, cut the prose.
- **Static enumeration only for typed dispatch.** Use an explicit-import static
  registry for dispatch tables the type checker must verify for completeness;
  auto-derive plain-string lists from the filesystem (with a naming convention
  for exclusions) to avoid a second drifting source of truth.
- **Prefer well-maintained libraries; minimize new dependencies.** Present the
  library option fully (maintenance, type ergonomics, idioms) rather than
  reflexively hand-rolling on LOC count; vendoring small, permissively-licensed,
  actively-maintained pure-Python libs under `scripts/_vendor/` is authorized.
  But first check whether already-vendored tools suffice — prefer JSONC (vendored
  `jsoncomment`) or plain text over adding TOML/YAML parsers; when a stdlib-vs-
  third-party choice is Python-version-gated, say so.
- **Hand-rolled SDK mocks are first-class livespec code** — they comply with
  every livespec Python rule by construction (no inheritance, keyword-only args,
  strict dataclasses). A mock handles I/O streams and subprocesses; it need not
  subclass or shape-match SDK types. Don't raise style-vs-mock exemptions unless
  a rule and the mock's contract are forcedly incompatible.
- **User-provided extensions owe only the calling-API contract.** Impose nothing
  on extension code (custom doctor checks, templates, hooks) beyond the boundary
  type contract; livespec doesn't lint, vendor for, or prescribe architecture to
  extension authors, and never vendors a library just because an extension might
  want it.
- **Isolate cwd in tests.** Any test that can reach a `Path.cwd()` default (even
  via downstream delegation) must `monkeypatch.chdir(tmp_path)`, or the code
  under test writes into the repo and pollutes tracked state.

## Spec and work-item conventions

- **The spec is for contracts, not tracking.** Put an artifact in `SPECIFICATION/`
  only if it stays meaningful after the work it describes is done (contracts,
  invariants, schemas, architectural commitments); epics, plans, and in-flight
  tracking live in the work-items ledger.
- **Don't codify transient conventions.** Before migrating anything into
  `SPECIFICATION/`, ask "would this rule still make sense after the workflow it
  scaffolds stabilizes?" — if not, leave it in working notes.
- **In brainstorming/design mode, don't anchor on prior iterations.** Present the
  cleanest structural break first unless the maintainer asks to preserve
  compatibility.
- **Enumerate every spec-target's queue before critiquing.** Each `--spec-target`
  (sub-spec) has its own `proposed_changes/` queue that main-spec enumeration
  doesn't surface; list it first, and if a pending proposal already covers the
  scope, recommend revising it rather than filing a duplicate.
- **Revise decisions are per-file.** One decision entry per proposed-change FILE
  with `proposal_topic` = the file stem (front-matter topic), never a
  `## Proposal:` section name (mismatch → silent exit 3); for selective
  disposition, split proposals across separate files.
- **Independent Fable review before every ratification.** Every proposed
  change — in ANY fleet repo — gets an independent, READ-ONLY adversarial
  review by a separately-spawned Fable-model agent BEFORE `/livespec:revise`
  accepts it (maintainer-declared 2026-07-04). The reviewer verifies at
  minimum: replacement-target fidelity (every quoted replace-target exists
  verbatim in the live file), design-record fidelity (the change matches the
  cited design record, never merely the shipped implementation), drift-sweep
  completeness (no unamended statement is left contradicting the change),
  ratification mechanics (topic/stem match, `tests/heading-coverage.json`
  co-edits for any `## ` heading change), and cross-repo consistency. A
  NO-BLOCKERS verdict is a precondition for driving the accept; any blocker
  routes to the maintainer with a recommended fix — it is never self-waived.
- **`depends_on` entries are typed dicts** `{"kind": "local", "work_item_id":
  "..."}`, never bare id strings — the store wrapper accepts bare strings but
  doctor-static (full `just check`) rejects them; copy the shape from an existing
  record and validate with full `just check`.

## Spec and architecture diagram authoring conventions

Architecture diagrams are **Mermaid only**, authored as fenced
` ```mermaid ` blocks directly inside `kind: markdown` spec files — no
manifest entry, no render command, no paired rendered artifact (per
`SPECIFICATION/spec.md` §"Template manifest"). The **canonical**
architecture diagram is the single source of truth in
`SPECIFICATION/spec.md` §"Contract + reference implementations
architecture"; the repo README **references** it and never embeds a
second copy OF THAT ARCHITECTURE DIAGRAM (no duplication, no drift for
the one canonical diagram). The narrowed rule forbids duplicating the
ARCHITECTURE diagram specifically — NOT all Mermaid in the README: the
README MAY embed OTHER, non-architecture diagrams (e.g. the
human-readable work-item-lifecycle `stateDiagram-v2`), since only the
canonical architecture diagram is single-sourced.

**Intentional exception — multiple diagrams at different zoom levels.**
`SPECIFICATION/spec.md` itself deliberately carries SEVERAL architecture
diagrams whose content overlaps, because each renders a different zoom
level / layer of the SAME architecture — e.g. the top-level
lifecycle/dataflow view (§"Tool-agnostic workflow — spec / implementation
lifecycle"), the plane model (§"Workflow planes and the Planning Lane"),
the revision loop (§"Lifecycle"), and the canonical dependency/boundary
view (§"Contract + reference implementations architecture"). That
intra-spec overlap is DELIBERATE, not drift: each diagram is the source of
truth for its own layer, so you MUST NOT consolidate or "de-duplicate"
them to satisfy the no-duplication rule. That rule still binds the
README→spec relationship (the README references the canonical architecture
diagram and never embeds a copy OF IT, though it MAY embed other,
non-architecture diagrams such as the work-item-lifecycle state diagram)
and forbids genuine same-layer copies — it does NOT forbid these deliberate
different-zoom views.

Hold these conventions when
authoring or revising any architecture diagram:

- **Three planes, named exactly.** Spec Plane (livespec core),
  Orchestrator Plane (the producer), Control Plane (the operator
  console). The console is the **Control Plane / operator cockpit** —
  NEVER call it a "Driver"; "Driver" is the per-agent-runtime binding
  (`livespec-driver-claude`, `livespec-driver-codex`). Render each plane
  as a subgraph.
- **Full skill names in labels, no abbreviations.** Write
  `propose-change`, `capture-work-item` in node *labels* (terse node
  *ids* are fine).
- **Stores are cylinders.** Filesystem / data stores — `SPECIFICATION/`,
  `plan/<topic>/`, the Ledger, IMPLEMENTATION — use the cylinder shape
  `[( … )]`. `plan/<topic>/` is a plain store node, not a skill.
- **IMPLEMENTATION sits inside the Orchestrator Plane** (it is the
  producer's work product), never a free-floating peer.
- **No temporal markers.** Skills and nodes are uniform; do not annotate
  a node as "new", "deferred", "phase-N", or "current" — a diagram
  depicts the target architecture, not a migration state.
- **Escape HTML in labels.** Use `&lt;` / `&gt;` for angle brackets
  (e.g. `plan/&lt;topic&gt;/`) and `<br/>` for in-label line breaks.

The three increment-1 framing diagrams (planes; skills; the canonical
contract diagram) and their rationale live in
`archive/research/planning-workflow-gap/planning-lane-design.md`
§"Architecture diagrams".

## Enforcement-suite and tooling discipline

- **"Done" means rolled out and exercised live — never merely merged +
  CI-green + AI-accepted.** Completion of any behavior-bearing change
  requires driving the SHIPPED behavior end-to-end in its real
  environment, including every cross-boundary shape the change claims to
  support (a `--repo` flag exercised cross-repo, a cross-tenant path
  exercised against a second real tenant — not only the same-repo happy
  path its tests cover). The post-merge acceptance leg (`accept:`) and
  any "track complete" report MUST carry live-exercise evidence journaled
  on the item; an overseer/operator MUST NOT trigger `accept:` without
  it. Maintainer-declared 2026-07-04, after the `approve:` operator
  surface shipped green through the full factory gate and its FIRST real
  cross-repo use found a wrong-tenant correctness bug.
- **The task runner is the single source of truth.** The justfile owns every
  check/build/test/lint/format/coverage invocation; lefthook and CI delegate via
  `just <target>` and never call underlying tools directly.
- **Fix the gate, not the bypass.** When two systems conflict, ask which is
  mis-designed for the current architecture and fix it — never reach for a skip
  flag, exemption entry, or install-but-neuter. When an architecture decision
  changes the world, enumerate the old-world invariants and re-derive each (keep
  / re-scope its check / retire); cross-repo bump cost is never an argument
  against the correct fix.
- **Never skip a test as the first or easiest fix — root-cause it.** When a
  test fails anywhere (local, CI, or a janitor/dispatch gate), the default is to
  diagnose and fix the underlying cause; skipping, disabling, deleting, or
  carving the test out to make the gate pass forfeits the verification the test
  exists for and hides the defect. A *normal, recurring* failure mode — e.g. a
  plugin's hooks needing re-trust after a version-pin bump, or any hardcoded
  value that drifts out of sync with its source — MUST be handled
  **automatically at its source** (derive it, refresh it, or accept it
  programmatically), never skipped. A scoped, self-documenting carve-out is a
  last resort, allowed only after a genuine root-cause fix is shown impossible —
  and even then it is a documented severity lever, never a silent skip.
- **Carve-outs are a severity lever, not an invariant relaxation.** When a check
  legitimately can't behave identically everywhere, keep it always wired into
  `just check` and always invoked, and add one self-documenting per-check env
  lever (warn-vs-fail for fast checks; run/skip for too-slow ones, set in all CI
  jobs) — never silently skip or weaken wiring-completeness. If escape-hatches
  approach 1:1 with invariants, reshape the invariant instead of adding the Nth
  hatch.
- **Flaky tests are unacceptable.** Treat any observed flake as a hard blocker:
  fix it conclusively (root-caused, deterministic, verified by repeated runs) or
  delete it — never `@flaky`/retry or leave it as a non-blocking note. For
  Hypothesis prefer `@settings(deadline=None)`; for order-dependence fix fixture
  isolation.

## Git and cross-repo working discipline

- **Read canonical committed state via `git show`.** For any governed checkout
  (host or sibling), read `git -C <clone> show origin/master:<path>` (or
  `HEAD:<path>` for the local tip) rather than the filesystem — a working tree
  can lag origin or carry edits. Never set `core.bare=true` on a primary checkout
  (it freezes the tree; the commit-refuse-hook invariant fails on it).
- **End on the main branch.** When finishing work in any repo you touched, switch
  its checkout back to main, pull (or fetch + reset --hard to origin), and verify
  clean status — never leave the maintainer on a feature branch, including after
  `gh pr merge --auto`.
- **Refresh the primary after a merge.** After any PR you drove lands,
  `git -C /data/projects/<repo> pull --ff-only origin master` so the maintainer's
  session sees it (the workspace path reaches the same `.git`, so there's no
  separate clone to update).
- **Force-push your OWN branch freely; never another session's.** Force-pushing
  a feature branch YOU created — e.g. `--force-with-lease` to update your own PR
  after a clean rebase onto `master` — is the standard, sanctioned PR-update flow;
  do it without gating. NEVER force-push (or otherwise rewrite-and-push) a branch
  or worktree ANOTHER session created; that is a cross-session clobber. For a
  branch you did not create, never force-push without explicit per-instance
  authorization. The same split applies to dispatched sub-agents: their briefs
  MUST forbid touching, pushing, or force-pushing any worktree/branch other than
  the one they create.
- **Master CI: surface red, query precisely.** On the first turn of a session,
  check master CI; a job the CI workflow runs being red is a real broken state,
  not a deferral — repair it or remove it from CI/branch-protection. Always query
  with `--workflow CI` (a bare `gh run list` is masked by non-CI workflows and
  reports a misleading green).
- **One Bash call per non-trivial step.** Don't chain multi-step git/file
  cleanups (worktree remove + branch delete + prune + refresh, loops over
  `git diff` output) into one call; issue each step separately and show its
  output, so the maintainer keeps visibility and an interrupt point.
- **One tool call per turn for sequential/fallible work** (git commit/push, PR
  create, edits depending on a prior read, surveys of unknown shape); reserve
  parallel batching for genuinely independent read-only calls. A
  `Cancelled: parallel tool call X errored` message means you broke your own
  batch (collateral) — re-issue the named failing call alone; never probe, wake,
  or snapshot in response. When overwriting an existing file, make sure a fresh
  read of it landed in an earlier turn (not the same batch), or use an edit
  instead of a full overwrite.
- **Verify a fix isn't already landed before filing.** Before filing a work-item
  from a memo or prior finding, grep git log (`--grep` on the id and the bug
  noun) to confirm it isn't fixed on master; if it is, dispose as already-fixed.
- **Verify per-repo state before cross-repo plans.** The fleet is non-uniform —
  verify the concrete per-repo state a cross-repo rule depends on (heading
  styles, registry entries, pins, which checks each repo runs) directly in each
  target repo; treat a plan's claims about sibling state as hypotheses to confirm.
- **Drive multi-repo work as one epic.** Never defer pieces to "follow-up PRs in
  another session/repo"; file the epic plus per-repo work-items with cross-repo
  links, and use `/livespec:doctor` as the cross-repo consistency check. Routine
  lib bumps and contract changes ARE the steady-state use case for cross-repo
  tooling — don't dismiss it as "no use case yet."
- **A required-key schema change is a cross-repo epic.** Making a work-items
  schema key required must, in the same epic, backfill that key into every
  sibling repo's legacy records — the fleet shares one schema validator over
  independent stores, so the originating repo's CI stays green while every
  sibling store becomes unreadable.
- **Dogfooding pins track the latest RELEASE, not raw master.** Across the
  self-consuming fleet, cross-repo pins resolve to core's latest release tag,
  because a release carries release-gate validation (`release-tag.yml`'s
  mutation testing, full heading coverage, no LLOC soft-warnings) that
  per-commit `just check` deliberately skips — a release is the more-validated
  artifact. This does NOT reintroduce stale pins: release-please cuts a release
  on every `feat:`/`fix:` push, so "latest release" stays close to master, and
  the cross-repo fan-out's `bump-pin` auto-rewrites every pin (`compat.pinned`
  and the other pin formats) to each new release tag — so upstream breakage
  still surfaces promptly, now gated by the release rather than by raw HEAD.
  `bump-pin` rewriting a sibling's `compat.pinned` from `"master"` to a release
  tag is correct-by-design: the `"master"` values are bootstrap placeholders
  that become release tags on the first successful fan-out. One accepted seam:
  `refactor:`/`perf:` commits cut no release, so a behavior-changing refactor
  reaches siblings only on the next `feat:`/`fix:` release.
- **Secrets are probe-only.** Read secret presence with `printenv NAME | wc -c`,
  never echo a value; never print tokens, env dumps, or remote URLs that may
  embed a token (e.g. a sandbox clone remote); on accidental exposure, rotate.

## Orchestration and delegation

- **Orchestrate; don't do heavy work inline.** For substantial multi-step work
  (scaffolding, authoring many files, cross-repo work), delegate the heavy
  lifting to scoped sub-agents (or a parallel workflow) with self-contained
  briefs and keep the main session for plan/dispatch/synthesis. Watch your
  context budget and write a concrete handoff before quality degrades.
- **Fan out pre-authorized work.** Dispatch all genuinely pre-authorized,
  independent, non-conflicting work-items in parallel; sequence only items that
  conflict on overlapping files. A "pause" means "start a new session," not
  "confirm everything from now on."
- **Brief sub-agents fully and safely.** Sub-agents don't inherit the parent's
  discipline: every dispatch brief touching git commit/push must explicitly
  forbid `--no-verify` and tell the agent to halt and report on hook failure.
  Pin load-bearing contract text verbatim into the brief (run a sequential
  contract-verification pass first; don't trust a research agent's "✓ covered"
  without re-checking its pinned text). Give trusted mutating executor agents NO
  tools allowlist (inherit everything) — real footguns are Bash-pattern
  behaviors caught by hooks + the prompt, not tool allowlists; reserve tight
  allowlists for read-only research agents.
- **Don't reap during active dispatch.** Never run the worktree reaper against a
  repo while a dispatched agent is working in one of its worktrees; reap only at
  session start, after a dispatched PR is confirmed merged and the agent exited,
  or at loop end.
- **Prefer primitives over new artifacts.** For coordination problems, reach for
  existing primitives + a naming convention before proposing new schemas,
  invariants, or skills; if a plan would create more than ~2 new artifacts, stop
  and check whether a convention suffices. Add mechanical enforcement only when a
  single maintainer can no longer verify state by reading.
- **Derive derivable fields; readers fail soft.** When a field is derivable from
  another, derive it on read rather than storing + requiring it; make readers
  skip/default and name the offender rather than crashing the whole enumeration;
  design bad data out with actionable errors and a discoverable blessed path.
- **Relocate, never drop, valuable work.** When useful work (doctor checks,
  hooks, disciplines, prose) leaves a repo, relocate it to where it now belongs
  and file a work-item there citing the pre-deletion commit SHA; self-resolve
  "keep/relocate/drop" as "relocate," and carry this into every handoff.

## Plugin and skill authoring

- **One skill per sub-command.** A Claude Code plugin with multiple sub-commands
  ships `skills/<name>/SKILL.md` per sub-command (not one skill with internal
  `commands/`), so each frontmatter scopes its description, least-privilege
  `allowed-tools`, and (for destructive ops) `disable-model-invocation`. Keep
  shared scripts/libs/schemas at plugin root; invoke as `/<plugin>:<skill>`. When
  naming a sibling skill, keep the original's domain noun + modifier and only
  swap the verb (sibling of `capture-impl-gaps` is `detect-impl-gaps`), carrying
  `impl`/`spec` prefixes verbatim.
- **Invoke plugin scripts via `${CLAUDE_PLUGIN_ROOT}`.** In any SKILL.md, write
  `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bin/<name>.py" "$@"` — never the
  `.claude-plugin/` path literal and never `uv run`: the installer flattens
  `.claude-plugin/scripts/` → `scripts/` and omits
  `pyproject.toml`/`uv.lock`/`.python-version`, so only `${CLAUDE_PLUGIN_ROOT}` +
  plain `python3` resolves in both the install cache and `--plugin-dir .` dev mode.

## Standing environment facts

- **`/home/ubuntu/workspace` and `/home/ubuntu/projects` are single top-level
  symlinks to `/data/projects`** — there are no per-repo bind-mounts. A workspace
  repo path is the same `/data/projects/<repo>` `.git` reached through the
  symlinked parent, so a repo path-move is a plain `mv` of `/data/projects/<repo>`
  plus `git remote set-url` and a config edit — no unmount/remount/fstab/
  privileged operation.
- **A Dolt `command denied to user '<tenant>'@'%'` error for `CALL
  DOLT_BACKUP(...)` is correct-by-design, not a fault.** `DOLT_BACKUP` needs
  SUPER, deliberately confined to one dedicated `backup`@localhost user; tenant
  users intentionally lack it. Backups run hourly via the systemd
  `dolt-backup.timer` — never treat tenant-level backup denial as a bug or blocker.
- **Default tmux socket is maintainer-owned.** Never run tmux cleanup against the
  default socket namespace. Scratch tmux servers MUST use an explicit `-L <name>`
  or `-S <path>`, and `tmux kill-server` MUST NOT be run unless that same command
  is scoped with `-L` or `-S`.
- **`tmp/` is maintainer-owned scratch.** Never `rm` it or assume it's
  disposable; put agent/tooling scratch under a scoped subdir (e.g.
  `tmp/bootstrap/`). Don't codify the `tmp/` convention into `SPECIFICATION/`.
