# bootstrap-pi-driver — initial research

Opened 2026-08-15. Goal: create **`livespec-driver-pi`** — a new
`driver-plugin`-class fleet member, exactly like
`livespec-driver-claude` and `livespec-driver-codex` in every fleet
obligation, differing only in the target agent harness: **pi** (the pi
coding agent, installed locally at `~/.local/bin/pi`, v0.84.1 at plan
open). Maintainer directive: full fleet member, "do everything EXACTLY
like they do, except for the pi harness."

## Finding 1 — the copier template does NOT cover this class (by design)

The maintainer asked to confirm the copier template has everything
needed. It does not, and that is contractual, not a gap to silently fix:

- `livespec-dev-tooling`'s fleet contract
  (`livespec_dev_tooling/fleet/_contract_classes.py`) declares
  `TEMPLATE_BORN_CLASSES = frozenset({"impl-plugin"})` — only the
  orchestrator/impl plugins are copier-born.
- Verified against live repos: `livespec-orchestrator-beads-fabro` and
  `livespec-orchestrator-git-jsonl` carry `.copier-answers.yml` on
  `origin/master`; `livespec-driver-claude` and `livespec-driver-codex`
  do NOT (checked via `git cat-file -e origin/master:.copier-answers.yml`).
- The copier question set
  (`livespec/templates/orchestrator-plugin/copier-questions.yml`) is
  impl-plugin-shaped throughout (`livespec-impl-<name>` naming).
- The birth procedure in `livespec/.livespec-fleet-manifest.jsonc` reads
  "scaffold (via the copier template **where the class has one**) →
  register HERE first → run `wire-fleet-member` → fleet conformance
  green" — driver-plugin has no template, so its sanctioned scaffold
  step is manual.

**Precedent:** `livespec-driver-codex` was born by hand — first commit
`948f904` "feat: bootstrap livespec-driver-codex — Codex Driver plugin +
family infra", then beads tenant pointers, family plugin provisioning,
fleet shim workflows, worktree-root adoption, release-please +
auto-enable-merge wiring, and pin bumps. `livespec-driver-codex` is the
closest structural donor for `livespec-driver-pi` (it is the younger,
second-runtime driver, so its history IS the "add a new runtime driver"
playbook).

**Decision recorded (default; maintainer may override):** follow the
codex-driver precedent — hand-bootstrap with `livespec-driver-codex` as
donor. Extending the copier template with a driver-plugin scaffold would
be a contract change (spec amendment to core's copier sections + a
`TEMPLATE_BORN_CLASSES` change in `livespec-dev-tooling`) and is NOT in
scope unless the maintainer asks for it; if a third driver-plugin ever
follows this one, that is the trigger to revisit templatization.

## Finding 2 — what "exactly like the existing Drivers" means (obligation inventory, to be verified per-repo)

From `livespec-dev-tooling`'s `_contract_classes.py`, `driver-plugin` is
in every obligation row except template-born:

- `PIN_WEB_CLASSES` — ships the release-dispatch PRODUCER shim
  (`release-dispatch.yml`).
- `RECEIVING_SHIM_CLASSES` — ships `bump-pin-from-dispatch.yml` +
  `pin-freshness.yml`.
- `DEV_TOOLING_PIN_CLASSES` — carries a `[tool.uv.sources]`
  livespec-dev-tooling tag pin.

Fleet-wide-by-intent obligations from `livespec`'s
`SPECIFICATION/non-functional-requirements.md`: red-green-replay gate
(lefthook + CI) for any first-party Python; ROP railway; primary-checkout
commit-refuse hooks; idempotent `just bootstrap`; branch protection with
a single required gate job (out-of-band GitHub setting); `just check` as
the single task-runner source of truth. Plus: own `SPECIFICATION/` tree
(dogfooded via `/livespec:*`), own beads tenant (Dolt SQL user +
DB-scoped grant + `.beads/config.yaml` committed, `metadata.json`
regenerable), registration in core's `.livespec-fleet-manifest.jsonc`
as `{ "repo": "livespec-driver-pi", "class": "driver-plugin" }`
**register-first**, then `wire-fleet-member`
(`livespec_dev_tooling.fleet.wire_fleet_member --repo <member>`), then
fleet-conformance green.

## Finding 3 — core-side co-changes (livespec repo)

The Codex driver's arrival left a pattern of core-side artifacts a third
runtime will likely mirror; each needs verification and probably a spec
proposal in core:

- Core ships per-runtime packaging the Driver resolves:
  Claude marketplace at `.claude-plugin/marketplace.json`; Codex catalog
  at `.agents/plugins/marketplace.json` + paired
  `.claude-plugin/.codex-plugin/plugin.json`, all pointing at the SAME
  `prose/` and `scripts/` (single cross-runtime artifact, nothing
  duplicated). Question: what packaging shape does pi's installer
  (`pi install <source>`) consume, and does core need a pi analogue?
- Spec amendments: `SPECIFICATION/contracts.md` §"Plugin distribution"
  and `SPECIFICATION/non-functional-requirements.md` carry
  Codex-specific sections ("Codex dogfooding contracts/constraints");
  a pi sibling set will be needed, via `/livespec:propose-change` +
  independent Fable review + `/livespec:revise`.
- Repo-orientation docs: core's `.claude/CLAUDE.md` / `AGENTS.md`
  document Claude and Codex dogfooding; a pi dogfooding section follows.

## Finding 4 — the pi harness surface (preliminary; needs its own research pass)

- `pi` v0.84.1 at `~/.local/bin/pi`. Has a first-class extension
  system: `pi install <source> [-l]`, `pi remove`, `pi update`,
  `pi list`, `pi config` (TUI enable/disable of package resources, with
  scope switching — suggests global vs local/project scope exists),
  `pi auth`.
- Non-interactive drive exists (`pi -p/--print`, plus `--mode json|rpc`)
  — the `codex exec` analogue for driving `/livespec:*` operations and
  for dispatch/e2e tests.
- Open questions for the next research pass: what a pi "extension
  source" is (git URL? npm? path?); whether pi has a skills/prompt-
  template notion that maps onto the eight `/livespec:*` operations or
  whether the Driver binds via custom tools/system-prompt appends;
  project-scoped vs host-wide enablement (Claude is project-scoped via
  committed `.claude/settings.json`; Codex is host-wide via
  `~/.codex/config.toml` — where does pi fall?); how the Driver
  resolves core's plugin root at runtime (env override →
  governed-project checkout → installed cache) under pi's layout.

## Rough shape of the work (to be cut into scoped children after research)

1. Research pi's extension/packaging surface; write it up as research
   note 2; decide the Driver binding mechanism and core packaging
   analogue.
2. Core spec proposals (pi dogfooding contracts/constraints, plugin
   distribution amendments) through propose-change → independent
   review → revise.
3. Bootstrap the `livespec-driver-pi` repo from the
   `livespec-driver-codex` donor (register-first in the fleet manifest,
   `wire-fleet-member`, beads tenant provisioning, branch protection,
   shim workflows, release-please).
4. Bind the eight operations for pi; live end-to-end exercise (the
   "done means exercised live" rule) driving a `/livespec:*` operation
   through an installed pi extension.
5. Fleet conformance green + docs (core CLAUDE.md/AGENTS.md pi
   dogfooding section).

Next action: research pass on pi's extension surface (item 1).
