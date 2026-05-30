---
topic: cli-end-to-end-harness-contract
author: livespec-orchestrate
created_at: 2026-05-30T22:01:33Z
---

## Proposal: CLI end-to-end harness contract

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a new `## CLI end-to-end harness contract` section to `contracts.md`
mandating a top-of-pyramid, *user-surface* end-to-end test tier that drives the
`claude` CLI binary itself — installing a livespec-family plugin via the CLI's
plugin-install surface and exercising its skills via slash commands from a
foreign tmp project root. This tier is distinct from, and coexists with, the
existing wrapper-chain `## E2E harness contract` (which drives wrapper scripts
as Python subprocesses). The existing section is amended to clarify it is the
*wrapper-chain tier* — a sibling to, not a superset of, the new CLI tier.

### Motivation

Today's `## E2E harness contract` drives wrapper scripts as Python subprocesses
anchored at `_REPO_ROOT/.claude-plugin/scripts/bin/`. That is a *wrapper-surface*
test, not a *user-surface* test: it does not exercise the `claude` CLI binary,
plugin marketplace install, plugin loading, or slash-command dispatch as a real
end user does. Install-shape bugs are invisible to it because every test in every
family repo runs from the dev tree where those bugs do not manifest.

Two P1 bugs filed against `livespec-impl-plaintext` make the gap concrete: the
published plugin bundle shipped without `_vendor/livespec_runtime/` (`li-k5dadf`),
and every `SKILL.md` quoted a wrapper path that did not survive the installer's
directory flattening (`li-m4q4h5`). A single CLI-driven end-to-end test would
have caught both immediately; no existing tier could. The family needs a tier
whose only entry point is the user-visible CLI.

### Proposed Changes

Add a new `## CLI end-to-end harness contract` H2 section to `contracts.md`,
placed immediately after the existing `## E2E harness contract`. Because this
adds a `## ` (H2) heading, the revise pass landing it MUST co-edit
`tests/heading-coverage.json` to register the new heading (a `TODO` + reason
entry is acceptable during transition), per §"Self-application" co-edit
discipline. The new section body MUST encode the following seven normative
requirements:

---

## CLI end-to-end harness contract

Every plugin in the livespec family MUST be covered by a top-of-pyramid,
user-surface end-to-end test whose sole interaction surface is the `claude` CLI
binary. This contract is a sibling to §"E2E harness contract" (the wrapper-chain
tier): it adds a higher tier, replaces neither, and both coexist in CI.

1. **Sole entry point is the `claude` CLI binary.** Setup MUST pre-populate a
   tmp `HOME` with `~/.claude/settings.json` declaring the marketplace and the
   enabled plugin (or run `claude -p "/plugin install …"` as the first step).
   Every workflow step MUST be a `claude -p` subprocess invocation issuing a
   slash command, multi-turn via `--continue` / `--resume <id>`. The harness
   MUST NOT reach around to wrapper Python files and MUST NOT depend on cache
   layout. The claude-agent-sdk programmatic surface MUST NOT be used here — the
   SDK is the wrapper-chain tier, not this tier.

2. **Pluggable implementation.** The harness MUST drive the upstream `livespec`
   plugin in lockstep with one *impl* plugin (today `livespec-impl-plaintext`;
   tomorrow alternate implementations). The impl-plugin id MUST be a parameter to
   the harness. The spec-side skill set is fixed; the impl-side skill set is
   whatever the installed impl plugin exposes.

3. **Structural skill discovery.** Skill enumeration MUST walk
   `<installed-plugin>/skills/*/SKILL.md` in each plugin's installed location, and
   the plugin slash-command prefix MUST be read from `plugin.json`'s `name`
   field. There MUST be no parallel manifest file; the Claude Code plugin
   directory structure is the canonical source of truth.

4. **Per-skill fixtures as a parallel filesystem convention.** A fixtures
   directory (suggested `<consumer-repo>/tests/e2e-cli/fixtures/<skill>/`) MUST
   hold a `prompt.md` (text piped to `claude -p`) and an `expected_files.txt`
   (paths that MUST exist afterward) per skill. Discovery walks the same way:
   directory present == fixture exists.

5. **Time-bomb coverage gate (fail-closed).** The harness MUST assert
   `discovered_skills - fixtured_skills == ∅` and MUST fail the run otherwise. A
   new skill added to either plugin trips the gate until either (a) a fixture
   directory is added, or (b) the skill is explicitly listed in an
   `EXEMPT_SKILLS` table in the consumer repo with a written justification.

6. **Single canonical implementation in `livespec-dev-tooling`.** The harness
   itself (driver, fixtures loader, discovery, coverage gate, step orchestrator)
   MUST ship from `livespec-dev-tooling` and be consumed by every plugin repo via
   the existing pin-bump dependency flow. Each consumer repo wires the imported
   test function into its own pytest collection.

7. **Consumer obligations.** Each plugin claiming livespec-family membership
   MUST: (a) be installable solely via the `claude` CLI plugin-install surface;
   (b) ship a `tests/e2e-cli/` directory with per-skill fixtures; and (c) pass
   the imported harness against itself and, where applicable, against the
   upstream `livespec` plugin paired in lockstep.

---

Additionally, amend the existing `## E2E harness contract` section: add a
clarifying lead sentence stating it is the **wrapper-chain tier** — the
second-tier integration test (faster, deterministic, mock-LLM), a sibling to and
NOT a superset of the new `## CLI end-to-end harness contract`. Both tiers coexist
in CI; the new tier replaces neither.
