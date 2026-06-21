# Non-functional requirements — `livespec`

This document MUST be read alongside `spec.md`, `contracts.md`, `constraints.md`, and `scenarios.md`. It enumerates the project's non-functional requirements: invariants on the development environment, repository tooling, build and test discipline, contributor workflow, and any other internal-facing concerns that are NOT visible at the user-facing CLI/API surface. The five top-level `##` sections below mirror the same four-file boundary the user-facing spec uses (`Spec` / `Contracts` / `Constraints` / `Scenarios`) plus a `Boundary` preamble, so contributors and agents apply the same categorization rule when landing new content.

## Boundary

`non-functional-requirements.md` covers concerns of the form "how the project is built, tested, and maintained".

`livespec`'s self-application surface — its sibling-repo family (`livespec-dev-tooling`, `livespec-runtime`, the `livespec-orchestrator-*` registry), the copier scaffold channel, the shared-code and shared-runtime channels, the family release-coordination surface, and the sibling registry the doctor cross-repo checks read — is internal-facing self-application and MUST be specified here, NOT in the user-facing functional files. The user-facing functional files (`spec.md` / `contracts.md` / `constraints.md` / `scenarios.md`) describe ONLY the contract a third-party `livespec` consumer inherits. The litmus test for new content is: "does a project merely governed by `livespec` inherit this, or is it `livespec`'s own family infrastructure?" — family infrastructure lives in this document.

The top-level sections below mirror the user-facing spec files. The decision rule for each section:

- `## Spec` — process *intent and behavior*: what testing means in this project, what TDD means here, what "done" means, how `livespec` applies to itself. Mirrors `spec.md`'s role.
- `## Contracts` — *external interfaces and contributor-facing toolchain*: the specific tools the project depends on, the contributor-facing invocation surface (`just check`), and any wire-level test/coverage data file shapes. Mirrors `contracts.md`'s role.
- `## Constraints` — *architectural invariants on the implementation*: code patterns, layout rules, thresholds, style rules. Mirrors `constraints.md`'s role.
- `## Scenarios` — *Gherkin-style scenarios for contributor-facing workflows*. Mirrors `scenarios.md`'s role. Empty initially; populated when specific contributor flows need to be pinned.

The boundary against the user-facing spec files:

- User-facing intent or behavior MUST stay in `spec.md`.
- User-facing wire contracts MUST stay in `contracts.md`.
- Constraints whose violation an end user could observe MUST stay in `constraints.md` (runtime versions, exit-code contracts, dependency envelopes, structured-logging schemas, vendored-library discipline, NLSpec discipline including BCP14 and heading-taxonomy rules).
- User-facing scenarios MUST stay in `scenarios.md`.

The trickiest boundary is `constraints.md` ↔ `non-functional-requirements.md`: constraints whose violation an end user could observe MUST stay in `constraints.md`; constraints that bind only the project's contributors MUST move here.

## Spec

This section's sub-sections enumerate the project's contributor-facing process intent and behavior — the analogue of `spec.md`'s role for the user-facing surface.

### Test-Driven Development discipline

This section codifies how the Test-Driven Development discipline is applied at the keyboard, day to day, in Python.

**Authoring rhythm.** Red and Green happen in the editor; only the cohesive unit of value (Red+Green together for a feature/bugfix; or a behavior-preserving structural change for a refactor) commits. `just check` runs as the pre-commit hook and a failing test rejects the commit — the discipline aligns with that: keep the Red phase in the editor, run it, observe it fail for the right reason, then write Green and commit the pair.

**Running a Red test in isolation.** Use pytest's `-k` or test-id syntax to run exactly the new test: `uv run pytest tests/livespec/<area>/test_<module>.py::<test_name>`. Confirm the failure message names the missing behavior. Unhelpful Reds (`ImportError`, `ModuleNotFoundError`, `NameError`, `TypeError` on call shape) MUST be fixed before proceeding to Green.

**Writing Green: the minimum that turns Red green.** A stub that returns `Failure(<error>)` for the specific inputs the test exercises is often enough. Resist anticipating downstream tests. Once Green, run `just check-coverage` (full suite + 100% line+branch in one pass per v039 D1).

**Per v039 D4 (proactive coverage discipline).** Before staging the Green amend, run `just check-coverage-incremental --paths <impl_path>`. The incremental tool finishes in seconds and surfaces coverage gaps (including defensive branches) BEFORE the Green amend triggers the full pre-commit aggregate. The full `check-coverage` aggregate runs at pre-commit as the load-bearing safety net; the incremental tool exists to make the failure mode rare.

**Refactor cycle (independent, structure-only).** A refactor commit is reviewable on its own terms: (1) confirm the suite is green pre-refactor; (2) identify and characterize any coverage gaps in the area; (3) apply the structural change, running `just check` after each meaningful step — tests MUST stay green throughout; (4) commit with a `refactor:` message prefix. If a test goes red mid-refactor, behavior changed — stop and reapply as a Red-Green-driven feature or restart with better characterization.

**Exception clauses (exhaustive list):**

| Change | Exception category |
|---|---|
| Rename a file via grep (no behavior change; existing tests follow) | Mechanical migration |
| Add `# noqa: E501` to a long line | Configuration-only |
| Add `__all__: list[str] = []` to a module | Type-only / convention |
| Update `CLAUDE.md` text | Documentation-only |
| Bump `pytest` minor version in `pyproject.toml` | Configuration-only (version pin)* |
| Introduce a `NewType` alias and propagate annotations | Type-only |
| Extract a helper function with no behavior change | Pure refactor |

\* If a config bump surfaces a new lint violation in covered code, the violation IS a behavior change and test-first reapplies — the failing-rule output is the Red signal. "I couldn't think of a failing test smaller than the implementation" is NOT an exception.

### Testing approach

Every Python source file under `livespec/`, `bin/`, and `dev-tooling/checks/` MUST have a paired test file at the mirrored path under `tests/`, except: (a) **private-helper modules** — `.py` files whose filename starts with `_` and is NOT `__init__.py` (e.g., `_seed_railway_emits.py`); these are covered transitively through the public function that imports them. (b) **Pure-declaration modules** — files whose AST contains no `FunctionDef` / `AsyncFunctionDef` anywhere (no module-level or class-level functions); covers boilerplate `__init__.py`, pure dataclass declarations, value-object modules, and the `LivespecError` hierarchy — none have testable behavior independent of their consumers. The `bin/_bootstrap.py` shebang preamble has its own special-cased test at `tests/bin/test_bootstrap.py`. The `dev-tooling/checks/tests_mirror_pairing.py` script enforces the binding mechanically and runs in the `just check` aggregate. Per-file line+branch coverage MUST be 100% (enforced by `dev-tooling/checks/per_file_coverage.py`). Coverage is computed under `pytest --cov` with `pyproject.toml`'s `[tool.coverage.run]` settings active.

The v034 D2-D3 Red→Green replay contract gates every `feat:` / `fix:` commit: the Red commit stages exactly one new test file and zero impl files; the Green amend stages the impl that turns the test green; the commit-msg hook verifies the temporal Red→Green order via reflog inspection plus test-file SHA-256 checksum.

**Prompt-QA tier.** Above the unit-test layer (which gates 100% per-file line+branch coverage on `livespec/`, `bin/`, `dev-tooling/checks/`), every built-in template's REQUIRED prompts (`prompts/seed.md`, `prompts/propose-change.md`, `prompts/revise.md`, `prompts/critique.md`) are exercised by per-prompt tests under `tests/prompts/<template>/`. Each test loads one or more fixture files capturing a prompt-input + canonical-LLM-response pair, validates the canonical response against its named JSON Schema (`seed_input.schema.json`, `proposal_findings.schema.json`, `revise_input.schema.json`), and asserts every declared semantic-property name in the fixture against per-template assertion functions. The prompt-QA tier is invoked via `just check-prompts` (included in `just check`); each built-in template MUST ship at least one prompt-QA test per REQUIRED prompt (4 prompts × 2 built-in templates = 8 minimum cases). The prompt-QA tier is scope-distinct from the v014 N9 end-to-end harness at `tests/e2e/` (which drives wrappers via the Claude Agent SDK surface) — the prompt-QA harness performs no LLM round-trip and no wrapper invocation, only deterministic replay-and-assert against canonical fixtures. Per the unit-tier coverage scope codified above, `tests/prompts/` is NOT measured for line+branch coverage; the prompt-QA tier provides additional confidence but does not contribute to the 100% gate.

Tests MUST NOT mutate files under `tests/fixtures/`; test-local filesystem state MUST use pytest's `tmp_path` fixture. Tests MUST NOT require network access; impure wrappers are stubbed via `monkeypatch.setattr`. Tests MUST be independent of execution order; no module-level mutable state that a prior test could leave behind. `@pytest.mark.parametrize` is the preferred idiom for tabulated inputs. Assertions use pytest's default assertion-introspection; no third-party assertion library is used. `pytest-icdiff` is enabled via `pyproject.toml`; it produces structured diffs on failure, aiding LLM consumption of test output.

The meta-test `tests/test_meta_section_drift_prevention.py` verifies every top-level (`##`) heading in each specification file has at least one corresponding entry in `tests/heading-coverage.json`. The meta-test `tests/bin/test_wrappers.py` verifies every `bin/*.py` wrapper (excluding `_bootstrap.py`) matches the canonical 5-statement shebang-wrapper shape.

#### Property-based testing for pure modules

Pure `Result`-returning modules (`livespec/parse/` and `livespec/validate/`) are mandatory targets for property-based testing via `hypothesis` (uv-managed per v024, NOT vendored). PBT generates many input shapes and checks invariants the test author may not have imagined.

- `hypothesis` and `hypothesis-jsonschema` (MIT) MUST be uv-managed via `pyproject.toml` `[dependency-groups.dev]`. They are NOT vendored in `_vendor/`.
- Each test module under `tests/livespec/parse/` and `tests/livespec/validate/` MUST declare at least one `@given(...)`-decorated test function.
- For schema-driven validators, `hypothesis-jsonschema` provides auto-generated strategies from the schema's JSON Schema definition; tests SHOULD use this rather than hand-authoring `@composite` strategies.

Enforced by AST check `check-pbt-coverage-pure-modules`.

#### Mutation testing as release-gate

Mutation testing via `mutmut` (MIT; uv-managed per v024, NOT vendored) runs on a release-gate schedule (CI release branch only; not per-commit; NOT part of `just check`).

- `just check-mutation` runs `mutmut run` against `livespec/parse/` and `livespec/validate/` and reports kill rate.
- **Threshold:** ≥80% mutation kill rate. The 80% figure is initial guidance; first real measurement against shipping code may surface a different appropriate value, updated via a new propose-change cycle.
- Before first release-tag run, a `.mutmut-baseline.json` file MUST be committed at the repo root recording the kill-rate measurement at initial adoption. Subsequent tag runs compare against `min(baseline.kill_rate_percent - 5, 80)`.
- `just check-mutation` MUST emit to stderr a structured JSON summary when the threshold fails, containing `threshold_percent`, `kill_rate_percent`, and a `surviving_mutants` array with `file`, `line`, and `mutation_kind` fields.

### Definition of Done

A `livespec` change MUST satisfy the Definition of Done (above) before merge. The DoD comprises: `just check` aggregate passes, paired tests exist for every new source file, the CLAUDE.md coverage check passes, the heading-coverage check passes against `tests/heading-coverage.json`, and the v034 D3 replay-hook trailers are present on `feat:` / `fix:` commits.

The DoD widens via dogfooded propose-change cycles when individual DoD items surface as needing more rigorous specification.

### Self-application bootstrap exception

The initial bootstrap imperative window is closed. Every mutation to this `SPECIFICATION/` MUST flow through `/livespec:propose-change` → `/livespec:revise` against the appropriate spec target. Hand-edits to spec files outside the propose-change/revise loop are forbidden and would be caught by `dev-tooling/checks` plus the doctor static phase.
### Orchestrator plugin ecosystem

The implementation workflow lives in a sibling-repo topology distinct from `livespec`. Every orchestrator plugin MUST live in its own repository under the name `livespec-orchestrator-<ledger>[-<loop>]`, naming BOTH axes that distinguish one orchestrator from another: `<ledger>` identifies the work-item ledger substrate (e.g., `beads`, `git-jsonl`, `gitlab`), and the OPTIONAL `<loop>` segment identifies the loop driver when the ledger admits more than one (e.g., `fabro` for the parallel-sandbox loop). The `<loop>` segment is REQUIRED whenever naming the ledger alone would be ambiguous — a loop is ledger-portable (one loop driver MAY run over multiple ledgers), so a repo carrying a distinct loop MUST name it rather than letting the ledger imply it (examples: `livespec-orchestrator-beads-fabro`, `livespec-orchestrator-git-jsonl`, `livespec-orchestrator-gitlab`). Each `livespec-orchestrator-*` plugin MUST dogfood its own `SPECIFICATION/`. Cross-boundary conformance is the orchestrator CLI contract published by `livespec` (`contracts.md` §"Orchestrator CLI contract — the three named CLIs"): the orchestrator owns its work-item machinery, and core's contract sees only the three named CLIs.

`livespec-orchestrator-beads-fabro` backs the parallel-capable Beads/Dolt ledger + Fabro loop reference orchestrator that the livespec family itself dogfoods; `livespec-orchestrator-git-jsonl` carries the existing homegrown serial orchestration logic over a git-jsonl ledger (see `spec.md` §"Contract + reference implementations architecture" for both). The two reference names illustrate why both axes are named: Fabro is loop-portable across ledgers, so the loop MUST be named (`-fabro`), not just the ledger; the git-jsonl reference carries a single homegrown serial loop, so the ledger name alone is unambiguous and no `<loop>` segment is needed. Other catalog variants (e.g., a `gitlab` ledger) are deferred from immediate implementation but retained as recognized future variants.

`livespec` itself KEEPS its name and is NOT subject to the `livespec-orchestrator-*` convention: it is the core meta-tool, not an orchestrator plugin (the `livespec` → `livespec-core` rename was retired per `history/v068`). `livespec` MUST NOT depend on any `livespec-orchestrator-*` plugin in its code dependency graph: it MUST be installable standalone. The orchestrator-side skills are simply unavailable until a consumer installs an orchestrator plugin.

#### Shared content provenance

The non-functional requirements documented in this spec partition across two parallel sibling provenance channels along the static-vs-executable axis:

- **Static-scaffold requirements.** Requirements whose expression is static scaffolding (TDD harness shape, testing-approach scaffolds, the `justfile` recipe surface, `lefthook.yml`, `.mise.toml`, `pyproject.toml` skeletons, `.github/workflows/` scaffolds, commit-and-merge-discipline scaffolds) MUST be authoritative for `livespec` AND MUST flow into every `livespec-orchestrator-*` repo via the `copier` template at `templates/impl-plugin/` (see §"Shared content sync — copier template").
- **Executable-enforcement-suite requirements.** Requirements whose expression is executable enforcement-suite code — notably the checks under `dev-tooling/checks/` that mechanically enforce style, coverage, AST shape, CI alignment, and red-green-replay discipline — MUST flow into every livespec-governed consumer (`livespec-orchestrator-*` plugins AND sibling libraries such as `livespec-dev-tooling` itself) via the `livespec-dev-tooling` Python package and its composite Actions / reusable workflows (see §"Shared code sync — livespec-dev-tooling"). The shared-vs-`livespec`-private partition for these checks is codified in `livespec-dev-tooling`'s own `contracts.md`.

Drift between `livespec`'s requirements and a consumer repo's content MUST surface via one of two mechanisms keyed to the channel: static-scaffold drift MUST surface via CI's `copier update --dry-run --vcs-ref=master` check; executable-enforcement-suite drift MUST surface via the compatibility enforcement owned by the family/dev-tooling coordination surface — the `compat` block schema and bump-pin policy live in `livespec-dev-tooling`'s spec (see §"Cross-repo coordination — pin-and-bump" for the pointer) — since both channels' pins live in the same `compat` mechanism.

`copier` MUST be pinned via `uv` against `pyproject.toml`'s `[dependency-groups.dev]` (consistent with the existing rule that `uv` manages Python and Python packages while `mise` pins only non-Python binaries). The pin MUST be present in every consuming repo's `pyproject.toml` so `uv` resolves a reproducible `copier` version per the existing lock-file discipline. `livespec-dev-tooling` MUST be pinned via the same `uv` mechanism (`[tool.uv.sources]` with a `git` URL and a `tag`) so the executable-enforcement-suite version is similarly reproducible.

#### Orchestrator-internal Dispatcher guidance

This guidance is explicitly NON-normative on core's contract: core neither names nor verifies any of it (doctor's cross-boundary job is CLI callability only, per `contracts.md` §"Doctor cross-boundary invariants"). It records, for orchestrator authors, the loop discipline that earlier revisions of this spec mandated for a livespec-resident cross-repo loop driver; under the contract + reference implementations architecture (`spec.md` §"Contract + reference implementations architecture"), that discipline belongs to the orchestrator-internal Dispatcher and is properly codified in the orchestrator repo's own specification.

A Dispatcher SHOULD support:

- a **mode parameter** distinguishing at minimum interactive dispatch (a human approves each mutation) from autonomous dispatch (human review at PR boundaries only);
- a **budget parameter** bounding the loop (iteration count, wallclock duration, token consumption, or a composition) — an unbounded loop is a defect;
- a **janitor command run as a hard gate**: on every iteration where a mutation occurred, a non-zero janitor exit prevents that iteration's commit (the recovery policy — retry, escalate to interactive, halt — is the orchestrator's choice);
- a **structured iteration journal**, machine-readable for post-hoc audit, recording each iteration's pick, dispatch, janitor result, commit (or rollback), and exit reason.

The janitor command, integration branch, repo manifest, and worktree/isolation strategy come from the orchestrator's own configuration, never hardcoded. No repository is REQUIRED or expected to carry a cross-repo loop driver as core contract surface; the `.claude/skills/livespec-orchestrate/SKILL.md` this repository carried as interim working tooling (WITHOUT contract status) has been RETIRED now that a reference orchestrator realizes the Dispatcher — the Beads/Dolt + Fabro dark factory carries routine cross-repo work unattended (see `spec.md` §"Contract + reference implementations architecture").

#### Orchestrator-internal grooming guidance

Like the Dispatcher guidance above, this is explicitly NON-normative on core's contract: core neither names nor verifies any of it. It records, for orchestrator authors, the human-led *grooming* discipline — the front-end work-breakdown that sits BEFORE autonomous dispatch, where a maintainer decides how work is split into the units the orchestrator's Loop and Dispatcher then carry. Grooming operates on the orchestrator-internal Ledger, so it is orchestrator-internal and belongs in the orchestrator repo's own specification; what core records here is the repo-agnostic PATTERN, not the realization. The guidance is repo-agnostic: a single-repo and a multi-repo project groom identically. Multi-repo coordination is `livespec`'s own family self-application — already covered in this document — and is NOT part of the general grooming pattern; the only functional tie between multi-repo work and core is the `.livespec.jsonc` CLI delegation seam.

Core deliberately gets the GUIDANCE only. This pattern introduces NO new core skill, NO new core CLI, and NO new core doctor invariant. The concrete realization — the groom front-end, the ledger state it reads and writes, and the calibration mechanics — belongs to the reference orchestrator's own specification (for the family's dogfood default, `livespec-orchestrator-beads-fabro`'s `SPECIFICATION/`). The cut-line PRINCIPLE below reaches down to exactly ONE core *functional* concept: the scenario / acceptance.

**The slice cut-line.** A slice is the smallest unit with exactly ONE coherent "done". Two independent "done"s mean two slices: split. A slice's single "done" is verified one of two ways:

- *scenario-verified* — one named scenario passes (behavioral feature work); or
- *gate-verified* — the project's standing gates (its enforcement aggregate plus the `doctor` operation) fully define "done", with no scenario (configuration, spec-text, refactor, or cross-repo-bump work).

A slice-size FLOOR balances the cut-line against over-splitting: a unit is not split below the point where two slices cost more coordination than they save (for example, two changes with the same blast radius ride together). The floor is currently uncalibrated and rests on human judgement; see slice-size calibration below.

**The intake Definition-of-Ready.** A readiness checklist folded into the orchestrator's existing work-item capture front-ends — no new machinery; the capture aid auto-answers what it can and prompts the human only on the rest. An item is ready only when all of these hold; otherwise it is routed (not filed as ready):

- *one coherent "done"* — exactly one acceptance (one named scenario, or "the standing gates fully define done, no scenario"); an item that cannot name exactly one is an epic and routes to a regroom pass;
- *autonomously-verifiable acceptance* — an agent can confirm "done" with no human judgement call (the scenario passes, or the standing gates pass); an acceptance that needs human taste is given a verifiable acceptance or marked human-gated;
- *autonomy tier assigned* — a spec-change slice is human-gated (it routes through the propose-change / revise operations and is never auto-dispatched); every other slice is factory-dispatchable;
- *dependencies linked* — blockers are identified and linked; "ready" means blockers are closed AND an acceptance exists, never dependency-closure alone;
- *repo target named* — one slice targets one ledger / repo;
- *above the floor* — big enough to deserve its own slice rather than riding along with a same-blast-radius sibling.

**The agent-drafts / human-approves regroom pass.** The heavier breakdown that actually splits not-yet-ready items (epics, too-big items) into slices. It is the field's only published breakdown ritual: the orchestrator's groom front-end produces a read-only DRAFT, the human OWNS the cut and the acceptance and approves it, and only then are slices filed. The pass:

1. *read-only draft* — the groom front-end reads the epic, the relevant spec / scenarios, and the ledger, and drafts candidate slices with the intake fields above pre-filled; it files nothing yet;
2. *layer* — the drafted slices are arranged into dependency layers (no-blocker slices dispatch immediately; same-layer slices parallelize);
3. *human approves the cut* — the human edits the cut, acceptance, dependencies, and tiers and approves, or sends the draft back to re-draft;
4. *file on approval* — approved slices are filed via the existing capture machinery with dependencies linked; spec-change slices route to propose-change / revise rather than the factory;
5. *per-layer validation checkpoint* — after a layer converges, the standing gates and the named scenarios re-run before the next layer dispatches.

The regroom pass is triggered by an intake item marked needs-regroom (an epic) OR by factory non-convergence: a dispatched slice that will not converge IS the "too big" signal — it routes back to a human regroom pass, never an infinite retry. In an otherwise-autonomous loop this is the one human-in-the-loop step: the Dispatcher SURFACES needs-regroom items (escalate, do not drop), a human grooms and approves, and the factory drains the resulting ready slices.

**Slice-size calibration.** The field publishes no quantitative agent-sizing cut-point, so an orchestrator does not guess thresholds: it instruments. The approach emits, on the orchestrator's run journal, an outcome signal (did the slice converge to a merged result through the janitor gate without human rescue; the verify-then-fix loop count; an outcome class; the economic cost; whether it bounced to regroom) plus several mechanical size proxies (acceptance count, diff size, dependency fan-out, spec surface touched, dispatch-context size, archetype, repo), then correlates them to discover a ceiling — the proxy value(s) above which trouble spikes — empirically. The ceiling and the floor are asymmetric: the ceiling has a direct outcome signal (non-convergence, rising fix-loops) and calibrates straightforwardly; the floor has no direct signal — over-splitting's cost is a counterfactual the data never shows — so the floor needs a separate retrospective method and lags the ceiling. The ceiling is used two ways: reactively, by bailing after N fix-loops to a regroom pass (doable without calibration — it is the non-convergence trigger above); and predictively, by flagging an oversized slice at intake (which needs calibration, and the reactive bail-out is its training signal). Calibration is phased from a cold start: dispatch on the qualitative "one coherent done" with a human-guessed ceiling and reactive bail-out on while everything is instrumented; once runs accrue, an analysis pass proposes data-backed thresholds a human reviews and adopts; the adopted thresholds become advisory inputs to the size gate, re-calibrated as the model and codebase drift. The qualitative "one coherent done" stays the primary rule; the numbers are an advisory safety net the data calibrates.

**Hard versus advisory gating (resolved), by gate type.** The structural gates — one coherent "done"; an acceptance exists; dependencies linked — can be HARD: they are mechanically checkable and certain. The slice-size gate is ADVISORY: it is data-derived and uncertain, so it informs rather than blocks.

**Open questions (not resolved here).** The following are surfaced for a later decision rather than settled by this guidance: the slice-size FLOOR value (uncalibrated); whether the intake Definition-of-Ready and the regroom pass are better framed as ONE mechanism (the Definition-of-Ready gate plus what you do when it fails) rather than two; and the calibration sample size required before a threshold is trustworthy together with the re-calibration cadence against model and codebase drift.

### Codex dogfooding compatibility

The `livespec` repository supports maintainer dogfooding from OpenAI Codex CLI/TUI through Codex project skills under `.agents/skills/` and through the repository's `AGENTS.md` instructions.

Codex dogfooding is an adapter for repository development, not a separate LiveSpec product command model. The authoritative command behavior remains the core-owned operation prose under `.claude-plugin/prose/<name>.md` plus the spec-side wrapper contracts under `.claude-plugin/scripts/bin/`. Claude Code and Codex differ only in their runtime binding mechanics: the Claude Driver plugin binds the same core prose and wrappers from its own repository, while Codex project skills in this repository bind them from `.agents/skills/livespec-*`.

When a Codex session in this repository receives a request for a verified Codex adapter such as `/livespec:help`, `livespec next`, or `livespec doctor`, Codex MUST read the matching `.agents/skills/livespec-<name>/SKILL.md` adapter, then MUST read the matching `.claude-plugin/prose/<name>.md` file completely before acting. When that prose calls for a CLI, Codex MUST invoke the configured wrapper under `.claude-plugin/scripts/bin/` with explicit argv.

This compatibility path intentionally avoids duplicating operation prose, wrapper files, or built-in templates. Codex adapters MUST NOT copy Claude Driver `SKILL.md` bodies and MUST NOT point at `.claude-plugin/skills/*`; core intentionally ships no `.claude-plugin/skills/` tree.

The currently verified Codex project-skill surface is limited to the read-only `help`, `next`, and `doctor` adapters. Mutating operations (`seed`, `propose-change`, `critique`, `revise`, and `prune-history`) remain out of the Codex adapter surface until a later propose-change / revise cycle specifies and proves their Codex runtime controls. Under the sibling-repo topology, future Codex dogfooding adapters MAY map both `/livespec:*` and `/livespec-orchestrator-<ledger>[-<loop>]:*` consistently with the multi-repo architecture, but each orchestrator plugin's repository is responsible for its own Codex dogfooding mapping. Implementation-side workflows MUST NOT be promoted into `livespec` by Codex compatibility work.

### Agent collaboration discipline

The following rules establish baseline discipline for agent collaboration in livespec-governed projects. Each rule addresses a specific class of agent-collaboration failure observed during livespec's own bootstrap and dogfooding sessions. The rules apply to every agent-facing surface: skill prompts, CLAUDE.md / AGENTS.md content, hook scripts, and ad-hoc agent dialogue inside livespec-governed repositories.

#### Destructive-default CLI wrapping

Destructive-default external CLIs — those whose default behavior writes, commits, deletes, or otherwise mutates persistent state without explicit opt-in — MUST be invoked through project-local scripted wrappers (`just` recipes under `justfile`, scripts under `dev-tooling/`, or equivalent) that pin safe flags. The wrapper MUST declare which flag combinations are considered safe-by-default and MUST NOT pass through arbitrary flag overrides. Agent-facing prose (skill prompts, CLAUDE.md, AGENTS.md, hook scripts) MUST refer to the wrapper, not the underlying CLI, whenever a wrapper exists for that tool. When a new destructive-default tool joins the project's toolchain, a wrapper MUST be authored before any agent-facing reference to the tool is added.

The discipline mechanically prevents a class of agent-surprise failures: a tool whose default behavior is surprising to the user gets wrapped once, in one place, and every subsequent agent invocation runs through the safe-flag pin instead of relying on the agent's memory of the right flags. Realization of this rule (e.g., a `dev-tooling/checks/no_direct_destructive_cli.py` enforcement check) is tracked separately and lands once the rule is in spec.

#### Verify before referring

Agents MUST verify that a tool, skill, slash-command, plugin, or feature exists in the current environment AND does what is being claimed BEFORE referring to it by name in agent-facing prose, skill output, or dialogue suggestions. Verification means at minimum (a) confirming the name resolves in the active environment (e.g., the slash-command appears in the available-skills list; the CLI is on `$PATH`; the tool's help text matches the claimed semantics) and (b) confirming the capability's actual behavior matches the proposed use (e.g., a scheduler that fires on dates does not satisfy a condition-based trigger requirement).

When verification is impractical mid-response (e.g., the agent cannot reasonably probe an external system inline), the agent MUST hedge explicitly: "I'd need to verify whether `<X>` applies here" rather than offering `<X>` as a confident path. Confident references to nonexistent or misapplied capabilities erode user trust and impose cleanup work the user shouldn't have to do.

#### Completion includes persistence and workspace cleanup

Agent-claimed completion includes both artifact persistence and workspace cleanup. Substantial work artifacts (audit tables, multi-step plans, decision matrices, migration breakdowns — anything whose value extends beyond the current conversation turn) MUST be persisted (filed as a work-item via the orchestrator's capture tooling, committed to a tracked file, or otherwise written to durable storage) BEFORE the message containing them is sent. Chat-only delivery is reserved for ephemeral, single-decision analysis.

Workspace cleanup MUST be a part of "done" rather than a list of instructions appended to a completion message. When work goes through intermediate states that aren't the natural post-completion baseline (feature branches during PR work, checked-out hotfix branches, modified working trees, untracked test artifacts), the agent's "done" state MUST include the explicit cleanup actions: (a) after a PR merges, switch back to the project's default branch, fast-forward, delete the local feature branch, delete the remote branch (unless `gh pr merge --delete-branch` already did so); (b) after a destructive intermediate (`git reset --hard`, working-tree wipe, etc.), the "done" state is the recovered + re-validated state, not the destructive operation itself; (c) "I'll leave you to verify" is acceptable for verification steps requiring genuine user judgment (visual UI checks, subjective output review) but NOT as a stand-in for mechanical workspace hygiene the agent could perform.

This widens `### Definition of Done` (above): the existing DoD captures the mechanical CI/test/coverage gates; this rule captures the workflow-hygiene gates. Both MUST be satisfied before an agent claims a task complete.

### Sibling spec ownership

Implementation surfaces hosted by livespec-governed sibling libraries — `livespec-dev-tooling`'s composite Action / reusable workflow / Python check inventory, `livespec-runtime`'s subpackage public APIs, and any future sibling library's contractual surface — MUST be specified in those siblings' own `contracts.md` files. `livespec`'s spec states the policy (the requirement that the surface exists, the consumer-facing shape, the semver discipline principle); the sibling's spec owns the specific surface enumeration and the implementation contract.

This partition mirrors the existing precedent at §"Shared code sync — livespec-dev-tooling" ("The canonical partition list MUST live in `livespec-dev-tooling`'s own `contracts.md`") and generalizes it across every sibling library. When a future sibling library joins the livespec family, its own seeded `SPECIFICATION/` tree becomes the authoritative location for its implementation contract; `livespec`'s own spec MUST NOT duplicate that content.

The rule applies symmetrically to automation surfaces hosted in `livespec-dev-tooling`'s `.github/` (per its `contracts.md` §"Cross-repo coordination automation surface"). `livespec`'s spec MAY cross-reference these surfaces but MUST NOT specify their input/output schemas, dispatch payload shapes, auth models, or any other implementation detail — those live in the owning sibling's spec.

## Contracts

This section's sub-sections enumerate the project's contributor-facing external interfaces and toolchain — the analogue of `contracts.md`'s role for the user-facing surface.

### Toolchain pins

The project's contributor-facing toolchain MUST be pinned via the version managers below. End users install only the shipped plugin runtime; per `constraints.md` §"End-user runtime dependencies", end users do NOT need any of these tools.

Non-Python binary tools — `uv`, `just`, `lefthook`, and any other binary the dev workflow requires — MUST pin via `.mise.toml`. Python itself and Python dev dependencies MUST pin via `uv` against `pyproject.toml`'s `[dependency-groups.dev]` (lockfile: `uv.lock`).

The contributor toolchain's roles:

- `mise` — manages versions of `uv`, `just`, `lefthook`, and any future binary additions.
- `uv` — manages Python + Python dev dependencies.
- `just` — task runner; the canonical entry point for every dev-tooling invocation. See §"Enforcement-suite invocation" below.
- `lefthook` — git hook manager registering pre-commit, commit-msg, and pre-push behaviors.
- `pytest` (+ `pytest-cov`, `pytest-xdist`, `pytest-icdiff`) — test runner.
- `hypothesis` (+ `hypothesis-jsonschema`) — property-based testing for pure modules.
- `ruff` — linter and formatter; rule set codified under §"Linter rule set".
- `pyright` — type checker (configured strict); rule set codified under §"Typechecker rule set".
- `mutmut` — release-gate mutation testing (NOT part of `just check`).
- `bd` (beads) — distributed graph issue tracker (Dolt-backed) used by orchestrator plugins that track work in beads. Pinned via `.mise.toml`. Backend-specific usage rules live in the relevant `livespec-orchestrator-<ledger>[-<loop>]` plugin's own `SPECIFICATION/` (notably `livespec-orchestrator-beads-fabro`).

**Lefthook installation source.** `lefthook` MUST NOT be installed through npm or any node package because its postinstall behavior can overwrite `core.hooksPath` and bypass any other hook wrappers. The `.mise.toml` pin is the single source of truth.

The `dev-tooling/checks/no_direct_tool_invocation.py` AST check enforces that `lefthook.yml` and CI workflows MUST delegate to `just <target>` and MUST NOT shell out to underlying tools directly.

### Enforcement-suite invocation

The enforcement suite is **invocation-surface-agnostic**. Every check is a `just` target; pre-commit, pre-push, CI, and manual invocation are consumers. Linux is the primary platform; macOS is a supported developer platform. No Windows support.

The canonical target list is maintained in the justfile. Key groupings:

- **Per-commit aggregate (`just check`):** runs every check below sequentially, continues on failure, exits non-zero if any failed.
- **Standard per-commit checks:** `check-lint`, `check-format`, `check-types`, `check-complexity`, `check-imports-architecture`, `check-private-calls`, `check-global-writes`, `check-rop-pipeline-shape`, `check-supervisor-discipline`, `check-no-raise-outside-io`, `check-no-except-outside-io`, `check-public-api-result-typed`, `check-schema-dataclass-pairing`, `check-main-guard`, `check-wrapper-shape`, `check-keyword-only-args`, `check-match-keyword-only`, `check-no-inheritance`, `check-assert-never-exhaustiveness`, `check-newtype-domain-primitives`, `check-all-declared`, `check-no-write-direct`, `check-pbt-coverage-pure-modules`, `check-claude-md-coverage`, `check-heading-coverage`, `check-vendor-manifest`, `check-no-direct-tool-invocation`, `check-tools`, `check-coverage`, `check-doctor-static`, `e2e-test-claude-code-mock`, `check-prompts`.
- **Alternate-cadence targets (NOT in `just check`):** `e2e-test-claude-code-real` (requires `ANTHROPIC_API_KEY`; runs on merge-queue, master push, and `workflow_dispatch`).
- **Release-gate targets (release-tag CI only; NOT in `just check`):** `check-mutation` (mutmut; ≥80% kill rate on `parse/` + `validate/`); `check-no-todo-registry` (rejects any `test: "TODO"` entry in `tests/heading-coverage.json`).
- **Mutating targets (opt-in, not in CI):** `just fmt` (`ruff format`), `just lint-fix` (`ruff check --fix`), `just vendor-update <lib>`.

**Invocation surfaces:**

- **Pre-commit and pre-push (local):** `lefthook.yml` runs `just check`.
- **CI (GitHub Actions):** one job per check via a matrix strategy with `fail-fast: false`, each calling `just <target>`. The `jdx/mise-action@v2` step installs pinned tools.
- **Manual (developer at the shell):** `just <target>` — same targets hooks and CI use.

**Doctor static-phase coverage.** The `check-doctor-static` target MUST run doctor's deterministic static phase (`bin/doctor_static.py`) against the main `SPECIFICATION/` tree AND every sub-spec under `SPECIFICATION/templates/<name>/`, exiting non-zero (exit 3) on any `fail`-status finding from any tree. The target MUST be part of `just check` — invocation-surface-agnostic per the rule above, so it runs identically from lefthook pre-push, CI, and manual developer invocation. The LLM-driven objective and subjective phases are OUT of scope for this target: they require LLM judgment, produce non-deterministic output, and remain interactive-only via the `/livespec:doctor` skill's post-step phase per `spec.md` §"Sub-command lifecycle". The pre-step / post-step doctor invocations carried by individual `/livespec:*` wrappers remain in place per the existing sub-command lifecycle contract; the `check-doctor-static` target is a coverage backstop, not a replacement.


### CI telemetry export

Every livespec-governed primary repo's CI MUST export each completed run's per-job timings to the family observability surface (the shared Honeycomb environment), so that CI behavior — run durations, per-check job costs, failure distribution across the matrix — is observable across the whole family from one place rather than knowable only by reading individual GitHub run logs. The export carries one root span per run plus one child span per completed job, tagged with the run's commit, branch, triggering event, conclusion, and per-job conclusion; the family-scoped resource attributes (`service.namespace` identifying the livespec family, the dataset/`service.name` collecting CI runs) place every repo's runs in the same shared dataset. The wire encoding is OTLP, an implementation detail of the export; the contract is that per-run job timings reach the family observability surface.

**Closed-loop self-verification.** The export MUST be a closed-loop self-verification, NOT an out-of-band monitor: the same CI run that produces the timing data MUST confirm the observability surface accepted it, and MUST fail its own job when that confirmation does not arrive (the ingest endpoint did not return success, or the surface reported rejected data). The rationale is that a CI run is the deterministic signal that its own telemetry should exist, so the absence of that telemetry is detectable in-band. A broken export therefore reddens the run and fires the repo's existing CI-failure notification (per §"CI as a merge gate (branch protection)") instead of dying silently. This requirement exists because the predecessor mechanism — a harvester external to the runs it observed — failed silently when it stopped, with nothing watching for its absence; the closed loop structurally removes that failure mode. A broken telemetry pipeline MUST be fixed, never suppressed.

**Gating.** The export job MUST run on `push` to `master` and on `merge_group` events ONLY; it MUST NOT run on `pull_request`, so it adds zero latency to PR feedback. It MUST depend on the repo's check jobs so it observes their timings, MUST run even when an upstream check failed (so failed runs still export — a failed run is exactly the run whose telemetry is most worth keeping), and MUST exclude its own job from the exported set.

**Ingest-key discipline.** Authentication to the observability surface MUST use a dedicated, least-privilege, write-only ingest key — one that can send data but cannot read, query, or administer the surface (e.g., cannot create datasets). The management/query key MUST NEVER appear on the CI export path. The ingest key is a family-scoped secret and follows §"Family secrets — 1Password Environment as canonical source": it is a derived GitHub Actions secret projection of the canonical Environment, named per repo (the `HONEYCOMB_GITHUB_CI_INGEST_KEY_<CONSUMER>` convention, mirroring the per-consumer Anthropic-key naming in that section), never committed and never echoed. Because the family owner is a personal GitHub account with no organization secret tier, the secret is provisioned per repo rather than once at the org level.

**Template inheritance.** The export script and its `ci.yml` job MUST be carried by the orchestrator-plugin copier template per §"Shared content sync — copier template", so every generated `livespec-orchestrator-*` sibling inherits the export at scaffold time. A generated repo completes the inheritance by provisioning its own per-repo ingest-key secret; a repo that opts out MUST remove the export job (rather than leave it wired against a missing secret, which the closed loop would correctly redden).

### Orchestrator contract delegation

Each orchestrator's command surface, justfile namespace, work-item and gap-report machinery, and backend-specific invariants are defined in that orchestrator's own `SPECIFICATION/` (this applies to each `livespec-orchestrator-<ledger>[-<loop>]` repository playing the orchestrator role). `livespec` publishes only the orchestrator CLI contract (`contracts.md` §"Orchestrator CLI contract — the three named CLIs"): the orchestrator owns its work-item machinery, and core's contract sees only the three named CLIs.

### Codex dogfooding contracts

The repository's `.agents/skills/` directory is the Codex-native project-skill entrypoint for `livespec` dogfooding. It MUST expose project-local adapter directories, not symlinks into core or the Claude Driver. The currently verified adapter set is:

| Codex project skill path | Core prose source | Wrapper |
|---|---|---|
| `.agents/skills/livespec-help/SKILL.md` | `.claude-plugin/prose/help.md` | none |
| `.agents/skills/livespec-next/SKILL.md` | `.claude-plugin/prose/next.md` | `.claude-plugin/scripts/bin/next.py` |
| `.agents/skills/livespec-doctor/SKILL.md` | `.claude-plugin/prose/doctor.md` | `.claude-plugin/scripts/bin/doctor_static.py` |

Each Codex adapter MUST have valid Codex YAML frontmatter with `name` matching the adapter directory name and a non-empty `description`. Each adapter MUST be thin: it reads the named core prose file completely, follows that prose for behavior and failure handling, invokes the named wrapper when wrapper-backed, and does not copy operation-specific prose sections.

The three adapters above are the only core `livespec` Codex project skills this repository MAY claim today. Adding Codex adapters for `seed`, `propose-change`, `critique`, `revise`, or `prune-history` requires a later propose-change / revise cycle, a committed adapter implementation, a mechanical sync check update, and separate read-only or mutation-safe `codex exec` proof appropriate to the operation. Until then, mutating livespec operations MUST remain outside the Codex adapter surface.

`AGENTS.md` is the committed repository-instruction entrypoint for Codex sessions in this repository. It MUST orient Codex to worktree discipline, wrapper usage, Beads access, and the current project-local adapter surface, but it MUST NOT map Codex commands to `.claude-plugin/skills/*` because core ships no `.claude-plugin/skills/` tree.

The detailed Codex mapping table for `/livespec-orchestrator-<ledger>[-<loop>]:*` commands is deferred to each orchestrator plugin's own spec or to a later refinement, consistent with §"Codex dogfooding compatibility".

Codex compatibility verification is performed with separate Codex processes. Required verification commands for the current project-skill path:

- `find .agents/skills -maxdepth 2 -type f -name SKILL.md -print`
- `codex debug prompt-input '/livespec:help'`
- `codex exec --sandbox read-only '/livespec:help. Do not edit files. Tell me exactly which local instruction/prose file you read.'`
- `codex exec --sandbox read-only 'livespec next dry run only. Do not edit files. Tell me exactly which wrapper you would invoke.'`
- `codex exec --sandbox read-only 'livespec doctor help only. Do not edit files. Tell me exactly which wrapper you would invoke.'`

The expected verification result is that Codex names the selected `.agents/skills/livespec-*/SKILL.md` adapter, the matching `.claude-plugin/prose/<name>.md` file, and, for wrapper-backed commands, the matching `.claude-plugin/scripts/bin/...` wrapper. `codex debug prompt-input` MAY be used as positive evidence that Codex sees the project-local skill root when running on a Codex version that prints project skills in prompt assembly; it MUST NOT be used to claim Codex marketplace/plugin registry support.

### Cross-repo coordination — pin-and-bump

Pin-and-bump — the release-level coordination mechanism between `livespec` and every livespec-governed sibling consumer — RELOCATES to the family/dev-tooling coordination surface. The `compat` block schema, the bump-pin policy (pinned-release discipline, automatic bump-pin PRs on each `livespec` release, additive landing of breaking contract changes), and the compatibility enforcement are owned by `livespec-dev-tooling`'s own spec, whose `contracts.md` already owns the bump-pin automation per its §"Cross-repo coordination automation surface"; the relocation lands via that sibling's own propose-change cycle. The `contract-version-compatibility` doctor invariant is correspondingly DROPPED from core's catalogue — it is not "is a named CLI callable" (per `contracts.md` §"Doctor cross-boundary invariants"). The release-coordination use of the former `cross_repo_targets` config block lives at the same family-coordination surface alongside pin-and-bump; its work-item-resolution use is orchestrator-private (the work-item dependency graph is the orchestrator's Ledger).

### Shared content sync — copier template

The shared-content sync mechanism between `livespec` and its sibling `livespec-orchestrator-*` repos is `copier`: `livespec/templates/impl-plugin/` is the canonical scaffold for shared non-functional content (justfile, lefthook, mise, ruff/pyright, GitHub Actions workflows). Every `livespec-orchestrator-*` repo MUST be generated from this template via `copier copy` and re-synced via `copier update --vcs-ref=master`; each MUST carry a `.copier-answers.yml` tracking the template version it was last generated from. CI in each orchestrator repo SHOULD run `copier update --dry-run --vcs-ref=master` to surface drift.

The `--vcs-ref=master` pin is load-bearing on every blessed `copier copy` / `copier update` invocation, including `--dry-run` drift checks: a bare invocation resolves the template repo's latest git tag, which can long predate template HEAD (the `v1.0.0` tag predates the entire `.github/workflows/` template set), silently re-syncing a consumer to stale scaffolding. Blessed invocations MUST pin `--vcs-ref=master`.

`livespec` MUST publish a copier template at `templates/impl-plugin/` (project-root-relative) containing the canonical scaffolding every `livespec-orchestrator-*` repo derives from: `justfile`, `lefthook.yml`, `.mise.toml`, `pyproject.toml` (with the ruff/pyright config), `.claude-plugin/marketplace.json` and `plugin.json` skeletons, a starter `SPECIFICATION/` skeleton, and the following `.github/workflows/` files:

- `ci.yml` — the per-repo CI pipeline (matrix of static-phase checks; `pull_request` + `push` + `merge_group` triggers).
- `copier-update-drift.yml` — the periodic `copier update --dry-run --vcs-ref=master` drift detector that surfaces template divergence.
- `auto-enable-merge.yml` — auto-enables REBASE auto-merge on PR open. Required so that propose-change PRs in every orchestrator-plugin repo merge with the same cadence as upstream `livespec` PRs (incident 2026-05-26: `livespec-impl-plaintext` PR #26 sat OPEN/CLEAN for 10+ minutes because this file was absent).
- `auto-update-branches.yml` — auto-updates open-PR branches against `master` when the base advances. Paired with `auto-enable-merge.yml`; together they make merging a hands-free operation for green PRs.
- `bump-pin-from-dispatch.yml` — accepts the bump-pin dispatch payload from `livespec`'s release flow per `livespec-dev-tooling`'s cross-repo coordination automation surface.
- `pin-freshness.yml` — the periodic check that the pin tag in `.livespec.jsonc` is not older than the drift threshold per the compatibility enforcement owned by the family-coordination surface (per §"Cross-repo coordination — pin-and-bump").
- `release-dispatch.yml` — accepts the release-dispatch payload from `livespec`'s release flow.

The list is EXHAUSTIVE for the orchestrator-plugin scaffold: any workflow file added to `templates/impl-plugin/.github/workflows/` requires a contract-clause amendment (this section) and a corresponding update to the `copier-template-workflow-coverage` doctor invariant (codified in `contracts.md` §"Doctor cross-boundary invariants"). Livespec-private workflow files (e.g., `release-tag.yml` for livespec's own marketplace release flow, `e2e-real.yml` for livespec-private smoke tests) MUST NOT be added to the template and MUST NOT appear in the required-list.

Each enumerated file MAY be a Jinja-templated thin pass-through that delegates to a reusable workflow at `thewoolleyman/livespec-dev-tooling/.github/workflows/<name>.yml@vX.Y.Z` (per §"Shared code sync — livespec-dev-tooling") — the reusable-workflow consumption pattern is the canonical sharing mechanism for any workflow whose implementation is uniform across livespec-governed repos. The contract-level requirement is that the file EXISTS in each orchestrator-plugin's `.github/workflows/`; whether the file's body inlines logic or `uses:` a reusable workflow is the template author's choice.

Every `livespec-orchestrator-*` repository MUST be generated from this template via `copier copy gh:thewoolleyman/livespec <target> --vcs-ref=master` (the repo-root `copier.yml` routes to `templates/impl-plugin/` via `_subdirectory`) and MUST carry a `.copier-answers.yml` at the repo root tracking the template version it was last generated from.

When `livespec`'s `templates/impl-plugin/` changes, each orchestrator repo SHOULD run `copier update --vcs-ref=master` to re-sync; the 3-way merge preserves local divergence where possible and surfaces conflicts as merge markers. Each orchestrator repo's CI SHOULD run `copier update --dry-run --vcs-ref=master` and fail or warn on detected drift.

Secrets MUST NOT be templated through `copier`; secret material lives only in environment variables, OS keyring, or a secret manager.

The copier channel MAY ship committed STATIC DATA files that the template consumes as render-time content (e.g., `templates/impl-plugin/canonical-slugs.yml`, the release-time projection of `livespec_dev_tooling.canonical_checks` consumed by `justfile.jinja` per §"Shared code sync — livespec-dev-tooling" → Template gate); such data files are static scaffold content and do NOT violate the channel partition's prohibition on `copier` delivering executable code. Render-time copier `_jinja_extensions` that import executable modules from the template tree MUST NOT be used to inject content the consumer `copier update` path depends on, because copier clones the template to an ephemeral checkout with no PYTHONPATH injection and the import cannot resolve there.

### Shared code sync — livespec-dev-tooling

The shared-code sync mechanism between `livespec` and every livespec-governed consumer is `livespec-dev-tooling`: a versioned Python package plus a set of GitHub composite Actions and reusable workflows, both published from `github.com/thewoolleyman/livespec-dev-tooling`. The mechanism is sibling-and-complementary to `copier` (which remains the shared-SCAFFOLD mechanism per §"Shared content sync — copier template"); `copier` MUST NOT deliver executable Python or shell code, and `livespec-dev-tooling` MUST NOT deliver static scaffolds. The two channels partition livespec's shared content along the static-vs-executable axis.

`livespec-dev-tooling` MUST be governed by livespec via its own seeded `SPECIFICATION/` tree (the `livespec` 4-file template plus `non-functional-requirements.md`) and MUST track its own work via its selected orchestrator per `.livespec.jsonc`. The sibling library MUST declare a `compat` block on a `livespec-dev-tooling` top-level key in its own `.livespec.jsonc`, conforming to the `compat` block schema owned by the family/dev-tooling coordination surface (see §"Cross-repo coordination — pin-and-bump" for the relocation pointer).

Consumers MUST consume `livespec-dev-tooling` via two parallel surfaces:

- **Python package.** Added to `pyproject.toml` `[dependency-groups].dev` via `[tool.uv.sources]` declaring a `git = "https://github.com/thewoolleyman/livespec-dev-tooling.git"` plus `tag = "vX.Y.Z"`. Invocation MUST take the form `uv run python -m livespec_dev_tooling.checks.<slug>`. PyPI publishing is NOT required in v1; the uv git-source path is sufficient for tag-pinned reproducible builds.
- **Composite Actions and reusable workflows.** Invoked via `uses: thewoolleyman/livespec-dev-tooling/.github/actions/<name>@vX.Y.Z` and `uses: thewoolleyman/livespec-dev-tooling/.github/workflows/<name>.yml@vX.Y.Z` from each consumer's `.github/workflows/ci.yml`.

Enforcement-suite checks that ship in `livespec-dev-tooling` MUST be those whose intent and CLI surface are stable across every livespec-governed project (e.g., style gates, coverage-pairing gates, AST gates, CI-alignment gates, red-green-replay gates). Checks whose intent is specific to `livespec` itself (e.g., checks asserting properties of the `templates/impl-plugin/` scaffold, checks asserting schema/dataclass pairing in `livespec`'s own package layout) MUST remain `livespec`-private and MUST NOT migrate. The canonical partition list MUST live in `livespec-dev-tooling`'s own `contracts.md` and is established by a subsequent propose-change cycle against that spec.

**Wiring-completeness invariant.** Every check in `livespec-dev-tooling`'s canonical set MUST appear in every consumer's `just check` aggregate, in alphabetical order. Consumer-private checks MAY appear after the canonical set. The canonical set is dynamically derived from `livespec_dev_tooling/checks/*.py` (excluding `_*`-prefixed helper modules and `__init__.py`) by the `livespec_dev_tooling.canonical_checks` module, which is the single source of truth for the canonical slug list. Manual lists of "the canonical checks" elsewhere in any consumer (e.g., hand-maintained justfile arrays, READMEs, CI matrix snippets) MUST be replaced by mechanical derivation from `livespec_dev_tooling.canonical_checks` or by a check that compares the manual list to the canonical list and fails on drift.

The invariant is enforced via three layers, designed as defense-in-depth so that no single layer's failure leaves the discipline unenforced:

1. **In-repo gate.** Every consumer MUST wire `check-aggregate-completeness` — the `livespec-dev-tooling` check (shipped at `livespec_dev_tooling.checks.aggregate_completeness`) that compares the consumer's own `just check` aggregate body against the canonical set and fails on any missing canonical slug or any non-alphabetical ordering within the canonical-set range. The gate is self-bootstrapping: `check-aggregate-completeness` is itself one of the canonical checks, so a consumer that drops it from its aggregate fails the invariant on the next `just check` run (because the canonical slug is now missing) and on every subsequent run until the gate is re-wired.

2. **Template gate.** `livespec/templates/impl-plugin/justfile.jinja` MUST stamp the full canonical aggregate at `copier copy` / `copier update` time so every newly-generated `livespec-orchestrator-*` sibling inherits the wiring-completeness state from inception and every existing sibling re-syncs to canonical-set growth. The stamped list MUST be derived from `livespec_dev_tooling.canonical_checks` (the single source of truth), NOT from a hand-maintained list in the template. The derivation MUST happen as a release-time PROJECTION inside `livespec`: a `livespec`-side step (a `just` target wired into the release path and enforced in CI) reads `livespec_dev_tooling.canonical_checks` and writes the resulting alphabetically-sorted slug set into a committed template data file (`templates/impl-plugin/canonical-slugs.yml`); `justfile.jinja` consumes that committed file as static template content. The canonical block MUST render WITHOUT importing any module at `copier copy` / `copier update` time — the consumer `copier update --vcs-ref=master` path reads only the committed data file (copier clones the template to an ephemeral checkout with no PYTHONPATH injection, so a render-time `_jinja_extension` importing `livespec_dev_tooling.canonical_checks` cannot resolve there and is therefore PROHIBITED for this gate). A `livespec`-private enforcement check (run in `just check` and CI) MUST assert that the committed `canonical-slugs.yml` projection equals `livespec_dev_tooling.canonical_checks.canonical_check_slugs()`, so the projection can never silently drift from the source of truth. For existing siblings, because the stamped block renders the full current canonical set as concrete data, `copier update`'s 3-way merge surfaces canonical-set growth as a real, reviewable diff against the consumer's current `justfile`, giving an additional human-review checkpoint on top of the in-repo gate.

3. **Cross-repo backstop.** The cross-repo backstop layer is the `wiring-completeness-cross-repo` doctor invariant, per `contracts.md` §"Doctor cross-boundary invariants". It walks every registered sibling repo (the `livespec-dev-tooling` / `livespec-runtime` / `livespec-orchestrator-*` registries declared in this document) and fires `fail` on any aggregate lacking a canonical slug, covering the adversarial-drift case in which a consumer drops both a canonical slug AND `check-aggregate-completeness` from its aggregate in the same change — the combination the in-repo gate cannot catch.

The canonical-checks Python module (`livespec_dev_tooling.canonical_checks`) lands in `livespec-dev-tooling` per the work-item `li-canon` (epic li-univck Phase 1.2). The `aggregate_completeness` check that powers the in-repo gate lands per the work-item `li-aggchk` (epic li-univck Phase 1.3). The template stamp and the cross-repo doctor invariant land in subsequent phases of the same epic.

Consumer-private checks (checks whose intent is specific to a single consumer per the partition rule above) MAY appear in a consumer's `just check` aggregate after the canonical set, in any order convenient to the consumer. The wiring-completeness invariant applies only to the canonical-set range; consumer-private extensions are unconstrained by it.

`livespec-dev-tooling` MUST declare a semver-stable surface covering its check invocation set, composite Action contracts, reusable workflow contracts, and any additional cross-repo coordination surface elements it ships. The canonical surface enumeration (the specific list of covered elements, the MAJOR/MINOR/PATCH bump rules, and the Conventional Commits → semver mapping) MUST live in `livespec-dev-tooling`'s own `contracts.md` §"Semver discipline" — the principle (semver-stable surface, no breaking changes outside MAJOR bumps) is `livespec`'s policy; the specific surface enumeration is the sibling's implementation contract.

`livespec-dev-tooling` MUST NOT perform network I/O from any check; MUST target Python 3.10+ exclusively (matching `livespec`'s floor per §"Toolchain pins"); MUST NOT take a runtime dependency on `livespec` itself (the library is consumed by `livespec`, not the other way around); MUST follow the comment, type, and coverage disciplines codified in `livespec`'s §"Linter rule set", §"Typechecker rule set", and §"Code coverage thresholds".

### Shared runtime — livespec-runtime

The shared-runtime mechanism between `livespec` and every livespec-governed consumer is `livespec-runtime`: a versioned Python package published from `github.com/thewoolleyman/livespec-runtime`. The mechanism is sibling-and-complementary to `livespec-dev-tooling` (which owns enforcement-suite code per §"Shared code sync — livespec-dev-tooling") and to `copier` (which owns static scaffolds per §"Shared content sync — copier template"). The three channels partition livespec's shared content along the static-vs-buildtime-vs-runtime axis: `copier` ships static files; `livespec-dev-tooling` ships build-time check modules consumed via `[dependency-groups].dev`; `livespec-runtime` ships runtime modules consumed by skills, doctor invariants, hooks, and CI workflows at invocation time.

`livespec-runtime` MUST be governed by livespec via its own seeded `SPECIFICATION/` tree (the `livespec` 4-file template plus `non-functional-requirements.md`) and MUST track its own work via its selected orchestrator per `.livespec.jsonc`. The sibling library MUST declare a `compat` block on a `livespec-runtime` top-level key in its own `.livespec.jsonc`, conforming to the `compat` block schema owned by the family/dev-tooling coordination surface (see §"Cross-repo coordination — pin-and-bump" for the relocation pointer).

Consumers consume `livespec-runtime` via one surface: the Python package added to `pyproject.toml` either as a runtime dependency under `[project].dependencies` or as a dev dependency under `[dependency-groups].dev`, with `[tool.uv.sources]` declaring `git = "https://github.com/thewoolleyman/livespec-runtime.git"` plus `tag = "vX.Y.Z"`. Invocation MUST take the form `import livespec_runtime.<subpackage>` or `python -m livespec_runtime.<entry>`. PyPI publishing is NOT required in v1; the uv git-source path is sufficient for tag-pinned reproducible builds. There is NO reusable GitHub Actions surface (consumers invoke `livespec-runtime` from their own workflow steps directly, since the call sites are inside skill / hook / wrapper code that the consumer composes itself).

The initial subpackage scope at `v0.1.0` is the empty `livespec_runtime.cross_repo` skeleton. Core's contract no longer names the `livespec_runtime.cross_repo` surface: cross-repo work-item dependency machinery is orchestrator-private, so that subpackage's public surface is contract surface of whichever orchestrator consumes it, documented in that orchestrator's own SPECIFICATION (per `spec.md` §"Contract + reference implementations architecture"). Future subpackages MAY be added under `livespec_runtime/<name>/`; each new subpackage's public surface MUST be defined in `livespec-runtime`'s own `contracts.md`.

`livespec-runtime` MUST declare a semver-stable public API: each subpackage's exported names, dataclass shapes, function signatures, and `python -m` entry points MUST NOT change without a MAJOR version bump. Internal module layout MAY change at any version increment.

`livespec-runtime` MUST target Python 3.10+ exclusively (matching `livespec`'s floor per §"Toolchain pins"); MUST NOT take a runtime dependency on `livespec` itself (the library is consumed by `livespec`, not the other way around); MUST follow the comment, type, and coverage disciplines codified in `livespec`'s §"Linter rule set", §"Typechecker rule set", and §"Code coverage thresholds". Unlike `livespec-dev-tooling`, `livespec-runtime` MAY perform network I/O (the cross-repo subpackage's GitHub queries depend on it); the no-network-I/O rule is specific to enforcement-suite code.

## Constraints

This section's sub-sections enumerate the architectural invariants on the project's implementation — the analogue of `constraints.md`'s role for the user-facing surface, but bound to contributor-facing concerns.

### Developer-tooling layout

`justfile` is the single source of truth for every dev-tooling invocation. `lefthook.yml` and CI workflows MUST delegate to `just <target>` and MUST NOT shell out to underlying tools directly (enforced by `dev-tooling/checks/no_direct_tool_invocation.py`). Tool versions for non-Python binaries (`uv`, `just`, `lefthook`) pin via `.mise.toml`; Python and Python packages pin via `uv` against `pyproject.toml`'s `[dependency-groups.dev]`. Lefthook pre-commit runs `just lint-autofix-staged` as its first step, which applies `ruff check --fix` + `ruff format` to the staged Python files only and re-stages them in place; this lets auto-fixable lint trivia (import ordering, formatting) get fixed without forcing a full pre-commit retry. The autofix step runs BEFORE the v034 D3 commit-msg replay hook computes the Red commit's test-file SHA-256 checksum, so the recorded checksum reflects post-autofix bytes; the Green amend stages impl files only (not the test), preserving the test-file-byte-identical invariant the replay hook enforces.

The canonical `just check` aggregate is enumerated in the justfile recipe. The aggregate runs sequentially with continue-on-failure semantics and exits non-zero if any target fails. This matches CI's `fail-fast: false` matrix; one local run reproduces full CI feedback.

**First-time bootstrap:** `mise install`, then `uv sync --all-groups` (resolves Python dev deps into a project-local `.venv` and commits `uv.lock`), then `just bootstrap`. The `bootstrap` target runs `lefthook install` (registers the pre-commit and pre-push hooks with git) and any other one-time setup. Without `just bootstrap`, lefthook hooks do not fire on commit.

### research/workflow-processes/ tool-agnostic vs implementation-specific split

The `research/workflow-processes/` directory MUST host two structurally separate artifacts. `tool-agnostic-workflow.md` describes the generic spec ↔ implementation workflow pattern using tooling-agnostic vocabulary ("Specification", "Implementation", "Capture Impl Gaps", "Capture Spec Drift", "Spec Reader", "Persistent Agent Knowledge", etc.); it MUST NOT reference `livespec-*` names. `architecture-summary.html` describes the livespec-specific implementation of that workflow using `livespec-core`, `livespec-orchestrator-git-jsonl`, `livespec-orchestrator-beads-fabro`, `/livespec:*`, and other tooling-specific names. The tool-agnostic doc is the source of truth — concept changes (e.g., gap-vs-drift naming) MUST land in the tool-agnostic doc first and then regenerate the livespec-specific doc to match. The two MUST NOT be collapsed into a single document. If the two drift, contributors MUST halt and reconcile rather than letting either become silently authoritative.

### Package layout

The plugin's Python surface lives under `.claude-plugin/scripts/`. The canonical directory tree is the directory itself; this file does not duplicate it.

The top-level layout has three roots:

- **`bin/`** — executable shebang-wrappers plus the shared `_bootstrap.py`. Each wrapper file MUST match the canonical 5-statement wrapper shape (plus an optional single blank line between the imports and `raise SystemExit(main())` per v016 P5). No logic. `chmod +x` MUST be applied.
- **`_vendor/`** — vendored third-party libs, EXEMPT from livespec rules per `## Constraint scope` above.
- **`livespec/`** — the Python package. Every other file under this root MUST follow every rule in `SPECIFICATION/constraints.md`.

Per-subpackage conventions:

- **`commands/<cmd>.py`** — one module per sub-command. MUST export `run()` (railway-emitting; returns `IOResult`) and `main()` (the supervisor that unwraps the final `IOResult` to a process exit code).
- **`doctor/run_static.py`** — the static-phase orchestrator. MUST compose every check module in `doctor/static/` via a single railway chain. The composition primitive (e.g., `Fold.collect`, manual fan-out) is implementer choice under the architecture-level constraints elsewhere in this file.
- **`doctor/static/__init__.py`** — the **static check registry**. MUST import every check module by explicit name and re-export a tuple of `(SLUG, run)` pairs. Adding or removing a check MUST be one explicit edit to the registry; dynamic discovery is forbidden so pyright strict can fully type-check the composition.
- **`doctor/static/<check>.py`** — one module per static check. MUST export a `SLUG` constant and a `run(ctx) -> IOResult[Finding, E]` function where `E` is any `LivespecError` subclass. (See `## ROP composition` and the supervisor discipline sections below for the railway/error contract.)
- **`io/`** — the impure boundary. Every function MUST wrap a side-effecting operation (filesystem, subprocess, git, argparse) with `@impure_safe` from the `returns` library. `io/` also hosts thin typed facades over vendored libs whose surface types are not strict-pyright-clean (e.g., `fastjsonschema`, `structlog`); see `### Vendored-lib type-safety integration` under `## Type safety`.
- **`parse/`** — pure parsers. Every function MUST take a string/bytes/dict and return `Result[T, ParseError]`. Includes the restricted-YAML parser at `parse/front_matter.py`.
- **`validate/`** — pure validators using the **factory shape**. Each validator at `validate/<name>.py` MUST export `validate_<name>(payload: dict, schema: dict) -> Result[<Dataclass>, ValidationError]`, where `<Dataclass>` is the paired dataclass at `schemas/dataclasses/<name>.py`. Callers in `commands/` or `doctor/` read schemas from disk via `io/` wrappers and pass the parsed dict. Validators invoke `livespec.io.fastjsonschema_facade.compile_schema` for the actual compile (the facade owns the compile cache). `validate/` MUST stay strictly pure: no module-level mutable state, no filesystem I/O. Every schema at `schemas/*.schema.json` MUST have a paired validator at `validate/<name>.py` AND a paired dataclass at `schemas/dataclasses/<name>.py`; three-way drift is caught by `check-schema-dataclass-pairing` per v013 M6.
- **`schemas/`** — JSON Schema Draft-7 files plus the `dataclasses/` subdirectory holding the paired hand-authored dataclasses. Filename matches the dataclass: `LivespecConfig` → `livespec_config.schema.json` paired with `schemas/dataclasses/livespec_config.py` AND `validate/livespec_config.py`. `check-schema-dataclass-pairing` enforces three-way drift-freedom (every schema has matching dataclass + validator; every dataclass has matching schema + validator; every validator has matching schema + dataclass).
- **`context.py`** — immutable context dataclasses (`DoctorContext`, `SeedContext`, etc.). The railway payload threaded through every command. See `### Context dataclasses` below for the field sets.
- **`errors.py`** — the `LivespecError` hierarchy with per-subclass `exit_code` class attribute. The hierarchy MUST hold ONLY expected-failure (domain error) classes per the error-handling discipline; bugs MUST NOT be represented as `LivespecError` subclasses (they propagate as raised exceptions to the supervisor's bug-catcher).

#### Dataclass authorship

Each JSON Schema under `schemas/*.schema.json` MUST have a paired hand-authored `@dataclass(frozen=True, kw_only=True, slots=True)` at `schemas/dataclasses/<name>.py`. The dataclass and the schema are co-authoritative: the schema is the wire contract (validated at the boundary by `fastjsonschema`); the dataclass is the Python type threaded through the railway (`Result[<Dataclass>, ValidationError]` from each validator per the factory shape). Domain-meaningful field types MUST use the canonical `NewType` aliases from `livespec/types.py`.

- The file name MUST match the `$id`-derived snake_case dataclass name (e.g., `LivespecConfig` → `livespec_config.py`).
- Fields MUST match the schema one-to-one in name and Python type.
- `schemas/__init__.py` MUST re-export every dataclass name for convenient import.
- No codegen toolchain. No generator. Drift between schema, dataclass, and validator MUST be caught mechanically by `check-schema-dataclass-pairing` (three-way AST walker per v013 M6: schema ↔ dataclass ↔ validator).

#### Context dataclasses

Every context dataclass MUST be `@dataclass(frozen=True, kw_only=True, slots=True)` and carry exactly the fields below at minimum. Sub-command contexts MUST embed `DoctorContext` rather than inheriting so the type checker can narrow each sub-command's payload independently. Domain-meaningful fields MUST use `NewType` aliases from `livespec/types.py`.

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from livespec.types import Author, RunId, SpecRoot, TopicSlug

@dataclass(frozen=True, kw_only=True, slots=True)
class DoctorContext:
    project_root: Path          # repo root containing the spec tree
    spec_root: SpecRoot         # resolved template.json spec_root (default: Path("SPECIFICATION/"))
    config: LivespecConfig      # parsed .livespec.jsonc (dataclass; see validate/livespec_config.py)
    config_load_status: Literal["ok", "absent", "malformed", "schema_invalid"]  # v014 N3 bootstrap-lenience
    template_root: Path         # resolved template directory (built-in path or custom)
    template_load_status: Literal["ok", "absent", "malformed", "schema_invalid"]  # v014 N3 bootstrap-lenience
    run_id: RunId               # uuid4 string bound at wrapper startup
    git_head_available: bool    # false when not a git repo or no HEAD commit

@dataclass(frozen=True, kw_only=True, slots=True)
class SeedContext:
    doctor: DoctorContext
    seed_input: SeedInput       # parsed seed_input.schema.json payload

@dataclass(frozen=True, kw_only=True, slots=True)
class ProposeChangeContext:
    doctor: DoctorContext
    findings: ProposalFindings  # parsed proposal_findings.schema.json payload
    topic: TopicSlug

@dataclass(frozen=True, kw_only=True, slots=True)
class CritiqueContext:
    doctor: DoctorContext
    findings: ProposalFindings
    author: Author

@dataclass(frozen=True, kw_only=True, slots=True)
class ReviseContext:
    doctor: DoctorContext
    revise_input: ReviseInput   # parsed revise_input.schema.json payload
    steering_intent: str | None

@dataclass(frozen=True, kw_only=True, slots=True)
class PruneHistoryContext:
    doctor: DoctorContext
```

`LivespecConfig`, `SeedInput`, `ProposalFindings`, and `ReviseInput` are dataclasses paired with the corresponding `*.schema.json` files; each schema carries a `$id` naming the dataclass. Fields MUST be filled at validation time via the factory-shape validators under `livespec/validate/`.

#### CLI argument parsing seam

`argparse` MUST be the sole CLI parser and MUST live in `livespec/io/cli.py`. Rationale: `ArgumentParser.parse_args()` raises `SystemExit` on usage errors and `--help`; the 5-statement wrapper shape leaves no room for it; `check-supervisor-discipline` forbids `SystemExit` outside `bin/*.py`. Routing argparse through the impure boundary keeps the railway intact.

Contract:

- **`livespec/io/cli.py`** MUST expose `@impure_safe`-wrapped functions that construct argparse invocations with `exit_on_error=False` (Python 3.9+), returning `IOResult[Namespace, UsageError | HelpRequested]`. `-h` / `--help` MUST be detected explicitly before `parse_args` runs; on detection, the function MUST return `IOFailure(HelpRequested("<help text>"))` (NOT `UsageError`). The supervisor pattern-matches `HelpRequested` into an exit-0 path (help text to stdout), distinct from `UsageError`'s exit-2 path (bad flag / wrong arg count to stderr). This avoids argparse's implicit `SystemExit(0)` without conflating help requests with usage errors.
- **`livespec/commands/<cmd>.py`** MUST expose a pure `build_parser() -> ArgumentParser` factory. The factory MUST construct the parser (subparsers, flags, help strings) but MUST NOT parse. Keeping construction pure lets tests introspect the parser shape without effectful invocation.
- **`livespec.commands.<cmd>.main()`** MUST thread argv through the railway. The supervisor pattern-match derives the exit code from the final `IOResult` payload:
  - `IOFailure(HelpRequested(text))`: emit `text` to stdout; exit 0.
  - `IOFailure(err)` where `err` is a `LivespecError` subclass: emit a structured-error JSON line to stderr via structlog; exit `err.exit_code` (`2` for `UsageError`, `3` for `PreconditionError` / `GitUnavailableError`, `4` for `ValidationError`, `126` for `PermissionDeniedError`, `127` for `ToolMissingError`).
  - `IOSuccess(...)` with any `status: "fail"` finding: exit `3`.
  - `IOSuccess(...)` otherwise: exit `0`.
  - Uncaught exception (bug): the supervisor's top-level `try/except Exception` MUST log via structlog with traceback and return `1`.
- `check-supervisor-discipline` scope: `.claude-plugin/scripts/livespec/**` is in scope; `bin/*.py` (including `_bootstrap.py`) is the sole exempt subtree. `argparse`'s `SystemExit` path is impossible under `exit_on_error=False`; the AST check has no special case for it.

### Pure / IO boundary

Purity is enforced **structurally** by directory, not by per-file markers:

- **`livespec/parse/**` and `livespec/validate/**` are PURE.** Modules here MUST NOT import from: `livespec.io.*`, `subprocess`, filesystem APIs (`open`, `pathlib.Path.read_text`, `.read_bytes`, `.write_text`, `.write_bytes`, any `os.*` I/O function), `returns.io.*` (pure code uses `Result`, not `IOResult`), or `socket`/`http.*`/`urllib.*` (no network).
- **`livespec/io/**` is IMPURE.** Every function MUST be decorated with `@impure_safe` from `dry-python/returns`. Functions here are thin wrappers over one side-effecting operation each. `io/` also hosts thin typed facades over vendored libs whose surface types are not strict-pyright-clean.
- **Everything else** (`commands/`, `doctor/**`, `context.py`, `errors.py`) MAY call both pure and impure layers; these are composition layers.

`LivespecError` raise-sites are restricted to `livespec/io/` and `errors.py`. The `dev-tooling/checks/no_raise_outside_io.py` AST check enforces the raise-site discipline mechanically.

Validators MUST stay pure by accepting their schema as a parameter (factory shape). The schema dict is read from disk by an `io/` wrapper and passed in by the caller; `fastjsonschema.compile` is cached in the impure `io/fastjsonschema_facade.py` module-level cache keyed on the schema's `$id`. This separates "reading" (impure) from "checking" (pure).

Enforced by `check-imports-architecture` (Import-Linter contracts over `parse/` and `validate/` imports) and `check-no-raise-outside-io` (AST raise-site check).

#### Import-Linter contracts (minimum configuration)

Per v013 M7 (scope narrowed in v017 Q3), the Import-Linter contracts in `pyproject.toml`'s `[tool.importlinter]` section MUST collectively enforce purity and layered architecture. The minimum concrete configuration below is **illustrative** of the canonical shape; contract names, layer names, and ignore-import globs MAY be restructured so long as the two authoritative rules below are enforced. (The v012 L15a third contract covering the raise-discipline import surface was retracted in v017 Q3; raise-site enforcement via `check-no-raise-outside-io` is the sole enforcement point.)

```toml
[tool.importlinter]
root_packages = ["livespec"]

[[tool.importlinter.contracts]]
name = "parse-and-validate-are-pure"
type = "forbidden"
source_modules = ["livespec.parse", "livespec.validate"]
forbidden_modules = [
    "livespec.io",
    "subprocess",
    "returns.io",
    "socket",
    "http",
    "urllib",
    "pathlib",
]

[[tool.importlinter.contracts]]
name = "layered-architecture"
type = "layers"
layers = [
    "livespec.commands | livespec.doctor",
    "livespec.io",
    "livespec.validate",
    "livespec.parse",
]
```

The authoritative rules (enforced by ANY valid Import-Linter configuration satisfying these two statements):

1. Modules in `livespec.parse` and `livespec.validate` MUST NOT import `livespec.io`, `subprocess`, filesystem APIs (`pathlib`, `open`), `returns.io`, `socket`, `http`, or `urllib`.
2. Higher layers MAY import lower layers but MUST NOT vice-versa; the layer stack is `parse` < `validate` < `io` < `commands` | `doctor`. No circular imports follow by construction.

**Raise-discipline is NOT an Import-Linter concern (v017 Q3).** `LivespecError` raise-sites are restricted to `livespec.io.*` and `livespec.errors` (enforced by `check-no-raise-outside-io`). `livespec.errors` MAY be imported from any module that needs to reference `LivespecError` or a subclass in a type annotation, `match` pattern, or attribute access (e.g., `err.exit_code`).

**Implementation overlay.** Two items from rule 1 — `returns.io` and `pathlib` — are intentionally absent from the realized `pyproject.toml` `forbidden_modules` list per the architecture-vs-mechanism principle. `returns.io` is a subpackage of an external package; Import-Linter v2 rejects subpackage forbids on externals — the `IOResult`/`IOFailure` ban in pure layers is enforced at raise-site by `check-no-raise-outside-io`. `pathlib` is required by `livespec.types` (for `SpecRoot = NewType("SpecRoot", Path)`) and flows transitively into pure layers through wire dataclasses; importing the `Path` class is not I/O — only its method calls are. The no-I/O-at-runtime intent is caught by `check-no-write-direct`, `check-supervisor-discipline`, and `check-no-raise-outside-io`.

### ROP composition

Every public function in `livespec/` MUST compose via ROP using `dry-python/returns` primitives:

- **Pure functions** (in `parse/`, `validate/`) MUST return `Result[T, E]`.
- **Impure functions** (in `io/`) MUST return `IOResult[T, E]`.
- **Composition code** (`commands/`, `doctor/`) threads steps together using `dry-python/returns` composition primitives (`flow`, `bind`, `bind_result`, `bind_ioresult`, `Fold.collect`, `.map`, `.lash`, etc.). The specific primitives chosen for a given chain are **implementer choice** under the architecture-level constraints. Mixed-monad chains (e.g., `IOResult`-returning I/O steps followed by `Result`-returning pure steps) MUST use the appropriate lifting primitive (such as `bind_result` on an `IOResult` chain, or explicit `IOResult.from_result(...)`); pyright strict and `check-public-api-result-typed` are the guardrails that catch mis-composition.

Error-handling routing:

- **Expected failure modes** — user input, environment, infra, timing — MUST flow through the Result track as `LivespecError` subclass payloads (*domain errors*).
- **Unrecoverable bugs** — type mismatches, unreachable-branch assertions, broken invariants, dependency misuse — MUST propagate as raised exceptions, not via the Result track.
- **Third-party code that raises DOMAIN-meaningful exceptions** (`FileNotFoundError`, `PermissionError`, `JSONDecodeError`, etc.) MUST be wrapped at the `io/` boundary using `@safe(exceptions=(ExcType1, ExcType2, ...))` or `@impure_safe(exceptions=(...))` with **explicit enumeration** of the expected exception types. A blanket `@safe` or `@impure_safe` with NO exception enumeration is forbidden — it would swallow bugs as domain failures.
- **Raising `LivespecError` subclasses** is restricted to `io/**` and `errors.py`. Enforced by `check-no-raise-outside-io` (AST). Raising bug-class exceptions (`TypeError`, `NotImplementedError`, `AssertionError`, `RuntimeError` for unreachable branches, etc.) is **permitted anywhere**; the AST check distinguishes the two by subclass relationship to `LivespecError`.
- **Catching exceptions** outside `io/**` is restricted to ONE call site: the outermost supervisor's `try/except Exception` bug-catcher (see `## Supervisor discipline`). `check-no-except-outside-io` enforces.
- **`assert` statements are first-class.** Use them for invariants the implementer believes always hold. An `AssertionError` is a bug; it propagates to the supervisor bug-catcher.
- **`sys.exit` and `raise SystemExit`** MUST appear ONLY in `bin/*.py` files. Enforced by `check-supervisor-discipline`.

Every public function's `return` annotation MUST be `Result[_, _]` or `IOResult[_, _]`, unless the function is a supervisor at a deliberate side-effect boundary (`main() -> int` in `commands/*.py` and `doctor/run_static.py`, or any function returning `None`). The rule exempts only such supervisors. Enforced by `check-public-api-result-typed` (AST).

#### ROP pipeline shape

A class decorated with `@rop_pipeline` MUST carry exactly ONE public method (the entry point). Every other method MUST be `_`-prefixed (private). Dunder methods (`__init__`, `__call__`, etc., matching `^__.+__$`) are not counted toward the public-method quota.

The decorator is a runtime no-op (returns the decorated class unchanged) declared in `livespec.types`. AST enforcement lives in `dev-tooling/checks/rop_pipeline_shape.py`. The decorator serves as an AST marker for the static check and as documentation at the def-site.

Each pipeline class encapsulates one cohesive railway chain. Enforcing the shape prevents the public surface from drifting as new chain steps are added — agent-authored code that grows a second public method is caught at check time. Helper classes and helper modules (anything NOT carrying `@rop_pipeline`) are exempt and MAY export multiple public names.

The marker is a decorator rather than a base class because the `check-no-inheritance` allowlist is intentionally small (`{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`); adding `RopPipeline` to the allowlist would expand the open-extension-point set for an application pattern.

Enforced by `just check-rop-pipeline-shape`.

### Supervisor discipline

Each command's `main()` function MUST be the only place outside `livespec/io/` where `sys.exit` (or its `raise SystemExit(...)` shape inside `bin/`) MAY appear. The supervisor pattern-matches the final railway `IOResult` onto an exit code via `unsafe_perform_io` plus a `match` statement that ends in `case _: assert_never(unwrapped)` for exhaustiveness. The `dev-tooling/checks/supervisor_discipline.py` AST check enforces this shape.

The shebang-wrapper layer at `bin/<sub-command>.py` MUST conform to the canonical 5-statement shape: shebang → docstring → `from _bootstrap import bootstrap` → `bootstrap()` → `from livespec.<...> import main` → `raise SystemExit(main())`. The optional blank line between statements 4 and 5 is permitted per v016 P5.

Every supervisor MUST wrap its ROP chain body in one `try/except Exception` bug-catcher whose exclusive job is: (1) log the exception via `structlog` with full traceback and structured context (module, function, `run_id`); (2) return the bug-class exit code (`1`). This is the ONLY catch-all `except Exception` permitted in the codebase. `check-supervisor-discipline` enforces the scope: exactly one catch-all per supervisor; no catch-alls outside supervisors; no catch-alls swallow exceptions without logging and exit-1 return.

### Typechecker rule set

`pyright` MUST run in strict mode against the `livespec/**` surface. `pyproject.toml`'s `[tool.pyright]` MUST set `typeCheckingMode = "strict"` and exclude `_vendor/**` from strict scope while keeping `useLibraryCodeForTypes = true`. NO `pluginPaths` entry: per v025 D1, pyright has no plugin system (microsoft/pyright#607) and no `returns_pyright_plugin` exists upstream.

`returns` library typechecker integration MUST use plain pyright strict (no plugin); the v018 Q4 returns-pyright-plugin assumption was falsified at v025 D1 — pyright has no plugin system and dry-python/returns explicitly does not support pyright. The seven strict-plus diagnostics below carry the load.

**The following seven strict-plus diagnostics MUST be enabled in `[tool.pyright]`.** Each closes a documented LLM-authored-code failure pattern:

- `reportUnusedCallResult = "error"` — every call to a function whose return type is non-`None` MUST be bound or passed on; the rare legitimate fire-and-forget pattern uses `_ = do_something(ctx)` explicit-discard binding. **This is the load-bearing diagnostic for the ROP discipline:** without it, an LLM can silently discard the entire `Result` / `IOResult` failure track.
- `reportImplicitOverride = "error"` — every method override MUST carry `@override` (imported from `typing_extensions` per the uniform-import discipline). Renaming a base-class method without `@override` silently strands the override.
- `reportUninitializedInstanceVariable = "error"` — every instance attribute MUST be initialized in `__init__` or have a class-level default.
- `reportUnnecessaryTypeIgnoreComment = "error"` — flags `# type: ignore` comments that no longer suppress any diagnostic.
- `reportUnnecessaryCast = "error"` — flags `cast(X, value)` where `value` is already typed `X`.
- `reportUnnecessaryIsInstance = "error"` — flags `isinstance(x, T)` when the type checker already knows `x: T`.
- `reportImplicitStringConcatenation = "error"` — catches `["foo" "bar"]` (missing comma) bugs in lists / sets / tuples.

Every public function (per the `__all__` declaration; see `### Module API surface`) and every dataclass field MUST have type annotations. Private helpers (single-leading-underscore prefix or not in `__all__`) SHOULD be annotated.

Every public function's `return` annotation MUST be `Result[_, _]` or `IOResult[_, _]`, unless the function is a supervisor at a deliberate side-effect boundary (e.g., `main() -> int` in `commands/*.py` and `doctor/run_static.py`, or any function returning `None`), OR the `build_parser() -> ArgumentParser` factory in `commands/**.py`. Enforced by `check-public-api-result-typed` (AST).

**`Any` is forbidden outside `io/` boundary wrappers and vendored-lib facades.** The thin facades under `livespec/io/<lib>_facade.py` are the ONLY place `Any` MAY appear. An AST check rejects `Any` annotations elsewhere.

**`# type: ignore` is forbidden without a narrow justification comment** of the form `# type: ignore[<specific-code>] — <reason>`. Vendored-lib facades MAY use `# type: ignore` for vendored-lib types pyright cannot see; livespec code outside the facades MUST NOT.

Implicit `Optional` via `None` default without `| None` annotation is forbidden (pyright strict flags this). `mypy` is not used; there is no mypy configuration file.

#### @override and assert_never import source

Both symbols MUST be imported uniformly from `typing_extensions`, not from stdlib `typing`, regardless of Python version. `typing_extensions` is vendored full upstream verbatim at tag `4.12.2` per v027 D1 at `.claude-plugin/scripts/_vendor/typing_extensions/__init__.py`. The upstream-canonical module name is retained so pyright's `reportImplicitOverride` recognizes the import path and `check-assert-never-exhaustiveness` recognizes the `Never`-narrowing signature. Uniform import discipline (`from typing_extensions import override, assert_never`) eliminates per-version conditionals.

#### Module API surface

Every module in `.claude-plugin/scripts/livespec/**` MUST declare a module-top `__all__: list[str]` listing the public API names. Public functions, public classes, and public `NewType` aliases belong in `__all__`; private helpers (single-leading-underscore prefix) MUST NOT appear in `__all__`. `__init__.py` files MAY declare `__all__` for re-export composition; every name listed MUST resolve in the module's namespace, including imported names.

Enforced by AST check `check-all-declared`: walks every module under `.claude-plugin/scripts/livespec/**`; verifies a module-level `__all__: list[str]` assignment exists; verifies every name in `__all__` is actually defined in the module (catches stale entries after a rename).

#### Domain primitives via NewType

Domain identifiers in `.claude-plugin/scripts/livespec/**` MUST use a `typing.NewType` alias from the canonical declarations in `livespec/types.py`. `NewType` creates a zero-runtime-cost type alias that pyright treats as distinct from the underlying primitive — passing a `RunId` where a `CheckId` is expected becomes a type error.

Canonical role → NewType mapping (field-name → NewType):

| Field name | NewType | Underlying | Concept |
|---|---|---|---|
| `check_id` | `CheckId` | `str` | doctor-static check slug |
| `run_id` | `RunId` | `str` | per-invocation UUID |
| `topic` | `TopicSlug` | `str` | proposed-change topic |
| `spec_root` | `SpecRoot` | `Path` | resolved spec-root path |
| `schema_id` | `SchemaId` | `str` | JSON Schema `$id` |
| `template` | `TemplateName` | `str` | `.livespec.jsonc` template field |
| `author` / `author_human` / `author_llm` | `Author` | `str` | author identifier |
| `version_tag` | `VersionTag` | `str` | `vNNN` version identifier |

Note: `template_root` in `DoctorContext` is the resolved-directory `Path` and MUST use raw `Path`, NOT `TemplateName`. Dataclass fields and function signatures handling these roles MUST use the `NewType`, not the underlying primitive. Construction uses the `NewType` as a callable: `CheckId("doctor-out-of-band-edits")`.

Enforced by `check-newtype-domain-primitives` (AST): walks `schemas/dataclasses/*.py` and function signatures; verifies field annotations matching the listed roles use the corresponding `NewType`.

#### Inheritance and structural typing

Class inheritance in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**` is RESTRICTED. The AST check `check-no-inheritance` rejects any `class X(Y):` definition where `Y` is not in the **direct-parent allowlist**: `{Exception, BaseException, LivespecError, Protocol, NamedTuple, TypedDict}`. The rule is DIRECT-PARENT only; `LivespecError` subclasses (e.g., `UsageError`, `ValidationError`) are NOT acceptable bases for further subclassing (v013 M5). This enforces the flat-composition direction: `class RateLimitError(UsageError):` is rejected; `class RateLimitError(LivespecError):` is permitted.

Structural interfaces MUST be declared via `typing.Protocol`. `abc.ABC`, `abc.ABCMeta`, and `abc.abstractmethod` imports are banned via the ruff TID rule configuration.

The `@final` decorator (imported from `typing_extensions`) is OPTIONAL; the AST check is the source of truth. Authors MAY use `@final` as documentation-by-decorator for clarity.

#### Exhaustiveness

Every `match` statement in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**` MUST terminate with `case _: assert_never(<subject>)` regardless of subject type. `assert_never` MUST be imported from `typing_extensions`.

When all variants of a closed-union subject are handled by preceding `case` arms, the residual type at the default arm is `Never` and pyright accepts the call. When a new variant is added without updating the dispatch site, the residual type narrows to the unhandled variant and `assert_never` becomes a type error. The conservative scope (every `match`, regardless of subject type) is preferred over a precise scope (only closed-union subjects) because false positives are cheap and the simpler check is more maintainable.

Enforced by AST check `check-assert-never-exhaustiveness`.

#### Vendored-lib type-safety integration

- **`fastjsonschema`** exposes generated callables typed as `Callable[[Any], Any]`. The thin facade at `livespec/io/fastjsonschema_facade.py` MUST expose a fully-typed surface: `compile_schema(schema_id: str, schema: dict) -> Callable[[dict], Result[dict, ValidationError]]`. The facade holds a module-level `_COMPILED: dict[str, Callable] = {}` keyed on `$id` to dedupe compiles across calls. `functools.lru_cache` cannot be used directly (dicts are unhashable), and a module-level cache would trip `check-global-writes` in pure code — the cache lives in the impure facade layer and is explicitly exempted.
- **`structlog`** logger calls are dynamically typed. The thin facade at `livespec/io/structlog_facade.py` MUST expose typed logging functions: `info(message: str, **kwargs: object) -> None`, etc.
- **`dry-python/returns`**: `Result` and `IOResult` types are used pervasively. The facade pattern does not apply uniformly; pyright strict plus the seven strict-plus diagnostics (especially `reportUnusedCallResult`) are the guardrails.

#### Vendored-import pyright resolution discipline

Vendored libs under `.claude-plugin/scripts/_vendor/` MUST resolve to typed surfaces under pyright via three coupled `pyproject.toml` `[tool.pyright]` settings:

- `extraPaths` MUST include both `.claude-plugin/scripts` (for first-party imports) and `.claude-plugin/scripts/_vendor` (for vendored libs). Without these, vendored-import lookups resolve as Unknown and cascade into `reportUnknownMemberType` / `reportUnknownVariableType` / `reportUnknownArgumentType` at every downstream call site.
- `stubPath` MUST be set to `.claude-plugin/scripts/_stubs` so pyright finds per-vendor PEP 561 stub trees for vendored libs lacking an upstream `py.typed` marker.
- For each vendored lib without an upstream `py.typed` marker, a project-local stub tree at `.claude-plugin/scripts/_stubs/<lib>-stubs/` MUST exist, carrying at minimum `__init__.pyi` declaring the public surface used in first-party code. The stub tree MUST be excluded from strict-mode coverage via `[tool.pyright].exclude += ["**/_stubs/**"]`.

The same `_stubs/` tree and `[tool.pyright]` block MUST be copied into every new `livespec-orchestrator-*` sibling repository at creation time so pyright resolves vendored imports identically across the family.

### Linter rule set

`ruff` (astral-sh/ruff) is the sole linter, formatter, import-sorter, and complexity checker. Uv-managed per v024 via `pyproject.toml` `[dependency-groups.dev]`.

`pyproject.toml`'s `[tool.ruff]` MUST configure:

- `target-version = "py310"`.
- `line-length = 100`.
- **Rule selection** (27 categories): `E F I B UP SIM C90 N RUF PL PTH` (11 baseline categories) PLUS `TRY FBT PIE SLF LOG G TID ERA ARG RSE PT FURB SLOT ISC T20 S` (16 v012 additions = 27 total). Key per-category meanings:
  - `TRY` (tryceratops) — exception-handling discipline.
  - `FBT` — boolean-trap; forbids boolean POSITIONAL arguments; reinforces keyword-only discipline.
  - `SLF` — forbids accessing `_`-prefixed attributes from outside the defining class.
  - `LOG` + `G` — logging discipline (no f-strings in log calls; kwargs only).
  - `TID` — tidy imports (no relative imports; banned-module list via `flake8-tidy-imports`).
  - `ERA` — eradicate commented-out code (a frequent LLM artifact).
  - `T20` (flake8-print) — bans `print` and `pprint`.
  - `S` (flake8-bandit) — security anti-patterns: `pickle.loads`, `subprocess` with `shell=True`, `eval`, `exec`, etc.
- `[tool.ruff.lint.pylint]` MUST set `max-args = 6`, `max-positional-args = 6`, `max-branches = 10`, `max-statements = 30`.
- `[tool.ruff.lint.flake8-tidy-imports]` MUST set `ban-relative-imports = "all"` and a banned-imports list including: `abc.ABC`, `abc.ABCMeta`, `abc.abstractmethod` (structural interfaces MUST use `typing.Protocol` instead); `pickle`, `marshal`, `shelve` (arbitrary-code-execution surface on `load()`; livespec uses JSON/JSONC for all serialization).

`just check-lint` runs `ruff check .`. Any finding fails the gate. `just check-format` runs `ruff format --check .`. Any diff fails. Mutating targets for developers: `just fmt` (`ruff format`), `just lint-fix` (`ruff check --fix`).

`# noqa: <CODE> — <reason>` is the only permitted per-line escape. Bare `# noqa` without a code and reason is forbidden; the `check-lint` enforcement inspects the comment shape.

### Comment discipline

Comments in first-party trees (`justfile`, `lefthook.yml`, `.github/workflows/*.yml`, `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, `dev-tooling/**`, `tests/**`) MUST follow two rules:

**Rule 1 — WHY-not-WHAT.** A comment MUST explain WHY a section, recipe, or block exists when the WHY is non-obvious to a future reader: a hidden constraint, a subtle invariant, a workaround for a specific tooling bug, or behavior that would surprise a reader. A comment MUST NOT explain WHAT the code does — well-named identifiers, BCP14 normative prose, and the surrounding spec already convey WHAT. If removing the comment would not confuse a future reader who can read the code, the comment MUST be deleted.

**Rule 2 — No historical-bookkeeping references.** Comments MUST NOT cite version numbers (`v033`, `v034 D2`), decision IDs (`Per v036 D1`, `v037 D1`), phase numbers (`Phase 4`), cycle numbers (`cycle 117`), commit references (`this commit`, `the previous PR`), or any other temporal/historical bookkeeping marker. The audit trail of decisions lives in `SPECIFICATION/history/vNNN/`, `git log`, the v034 D3 replay-hook trailers, and per-revision proposed-change files; duplicating it in source-file comments creates bit-rot risk and reader-archeology cost. Comments MUST state the live constraint in present tense without reference to when, why-historically, or by-which-decision the constraint was adopted.

**Scope exemptions.** The two rules DO NOT apply to: (a) `_vendor/**` (vendored upstream code; comments are inherited as-is); (b) the YAML front-matter and Markdown body of files under `SPECIFICATION/` (the spec IS the historical record; cross-references to other spec sections are acceptable); (c) `SPECIFICATION/history/vNNN/` snapshots (immutable); (d) `archive/` (frozen historical artifacts). Inside in-scope trees, the per-line escapes `# noqa: <CODE> — <reason>` (per §"Linter rule set") and `# type: ignore[<code>] — <reason>` (per §"Typechecker rule set") are already WHY-formed and remain compliant.

**Retroactive cleanup.** As part of accepting this proposal, every comment in the in-scope trees that violates Rule 1 or Rule 2 MUST be either rewritten to a WHY-form (when the comment carries a still-relevant non-obvious WHY) or deleted (when the comment is pure historical bookkeeping or pure WHAT). Reference checklist for the cleanup pass: every match for the regex `(?i)\b(v\d{3}\s*[A-Z]\d|per v\d{3}|phase\s+\d+|cycle\s+\d+|this commit|the previous (commit|PR))\b` in the in-scope trees MUST be reviewed and either rewritten or deleted.

**Enforcement.** A new `dev-tooling/checks/comment_no_historical_refs.py` script MUST be added to the `just check` aggregate (alongside `check-comment-line-anchors`) that greps every in-scope file for the historical-reference regex above and exits non-zero with structured findings naming each violation site. The check is categorized as a python-code check per §"Pre-commit step ordering" so it is skipped when zero `.py` files change. Rule 1 (WHY-not-WHAT) is judgment-based and MUST NOT be mechanically enforced — code review is the gate. Rule 2 is mechanically grep-able and MUST be enforced by the new check.

### Prose conventions

Every version reference in spec prose MUST be prefixed with the owning project name. Examples: `livespec v078`, `livespec-runtime v0.3.0`, `livespec-orchestrator-git-jsonl v0.x`, `livespec-dev-tooling v0.5.x`. External dependency versions follow the same shape (`uv 0.5.x`, `gh 2.x`, `Python 3.10+`). Rationale: livespec-governed repos cross-reference each other constantly; a bare `v0.2.0` is ambiguous between the meta-tool and its siblings.

Inline JSON or TOML example snippets are exempt when the version is the value of a typed field whose key already encodes the project name (e.g. `livespec-runtime.compat.pinned`, `[tool.uv.sources].livespec-runtime`). The structural key carries the disambiguation; the value stays unprefixed and is automated via release-please `extra-files` wiring.

Sibling-repo specs inherit this convention. The same rule applies to every livespec-governed `SPECIFICATION/` tree.

A future doctor LLM-subjective check SHOULD surface bare `v\d+\.\d+\.\d+` literals in spec prose as findings.

### Complexity thresholds

The following complexity thresholds MUST be satisfied by all first-party `.py` files under `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**`. **Waivers are not permitted.** A function or file that cannot meet a threshold MUST be decomposed; no escape hatch exists.

- **Cyclomatic complexity ≤ 10** per function (ruff `C901`).
- **Function body ≤ 30 logical lines** (ruff `PLR0915`).
- **File ≤ 200 LLOC (SOFT) / ≤ 250 LLOC (HARD).** LLOC excludes blank lines, comment-only lines, and docstrings. Files at 201-250 LLOC pass the per-commit `check-complexity` target with a structured warning emitted to stderr; `just check` stays green but the file is flagged for refactoring. Files above 250 LLOC fail the check (exit 1). The `dev-tooling/checks/file_lloc.py` script enforces both tiers. The `check-no-lloc-soft-warnings` release-gate (NOT in `just check`; fires on release-tag CI only) rejects any file in the 201-250 LLOC soft band before a release tag.
- **Max nesting depth ≤ 4** (ruff PLR rule).
- **Arguments ≤ 6** per function, counted TWO ways, both enforced: total args (ruff `PLR0913`, `max-args = 6`) AND positional args (ruff `PLR0917`, `max-positional-args = 6`). Functions needing more parameters MUST be refactored to accept a dataclass.

Enforced by `just check-complexity`.

### Code coverage thresholds

**100% line + branch coverage** is mandatory across the whole Python surface in `.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, and `dev-tooling/**`. No tier split. `_vendor/` is excluded. `bin/` is included because `_bootstrap.py` carries real logic (version check + sys.path setup) AND the 5-statement wrapper bodies carry the `bootstrap()` call + `raise SystemExit(main())` dispatch — all executable lines covered by dedicated `tests/bin/test_<cmd>.py` files. NO `# pragma: no cover` is applied to wrapper bodies; NO `[tool.coverage.run].omit` for `bin/`.

`pyproject.toml`'s `[tool.coverage.run]` MUST set `branch = true` and `source` to include both the `livespec` package and the `bin/` directory. `[tool.coverage.report]` MUST set `fail_under = 100`, `show_missing = true`, `skip_covered = false`. Enforced by `just check-coverage`.

**No line-level pragma escape hatch.** `# pragma: no cover` comments are forbidden anywhere in covered trees. The ONLY coverage exclusions permitted are the seven structural patterns in `[tool.coverage.report].exclude_also`: `if TYPE_CHECKING:`, `raise NotImplementedError`, `raise ImportError`, `@overload`, `if __name__ == .__main__.:`, `sys.path.insert`, and `case _:` (the assert_never exhaustiveness arm). These are block-level patterns recognized by coverage.py without per-instance annotation:

- `if TYPE_CHECKING:` guards are matched by the `exclude_also` pattern.
- `sys.version_info` gates in `bin/_bootstrap.py` are covered by dedicated `tests/bin/test_bootstrap.py` tests that monkeypatch `sys.version_info` to exercise both branches.
- `case _: assert_never(<subject>)` arms are structurally unreachable by the spec mandate (every `match` MUST terminate with the pattern; `check-assert-never-exhaustiveness` enforces the body shape). The `case _:` exclude_also pattern catches the entire arm.

A targeted check (`# pragma: no cover` literal match) in `dev-tooling/checks/` rejects any commit that introduces the comment in covered code.

**Wrapper coverage.** Each wrapper has a matching `tests/bin/test_<cmd>.py` that imports the wrapper and catches `SystemExit` via `pytest.raises`, with `monkeypatch` stubbing the target `main` to a no-op returning exit `0`. The import triggers the 5-statement wrapper body under coverage.py's tracer.

### Keyword-only arguments

All user-defined callables in livespec's scope (`.claude-plugin/scripts/livespec/**`, `.claude-plugin/scripts/bin/**`, `dev-tooling/**`) MUST accept every parameter as keyword-only. Call-site ambiguity over positional order is eliminated by construction.

Rules:

- Every `def` MUST place a lone `*` as its first parameter (or, for methods, immediately after `self` / `cls`) so that every subsequent parameter is in `kwonlyargs`.
- Every `@dataclass` decorator MUST include the full strict-dataclass triple: `frozen=True, kw_only=True, slots=True`. `frozen=True` prevents reassigning attributes after construction. `kw_only=True` makes the generated `__init__` keyword-only. `slots=True` uses `__slots__` storage — attribute-name typos raise `AttributeError` rather than silently creating new attributes.
- Callers MUST pass arguments by keyword wherever the callee permits it.

**Exempt from the `*`-separator rule:**

- Dunder methods whose signatures are fixed by Python (`__eq__(self, other)`, `__hash__(self)`, `__getitem__(self, key)`, `__iter__(self)`, `__next__(self)`, etc.).
- `__init__` of `Exception` subclasses when the only positional argument is the message forwarded to `super().__init__(msg)`.
- `__post_init__(self)` on dataclasses.
- Call-sites into stdlib / third-party / vendored-lib APIs that require positional arguments; the rule binds only livespec-authored definitions.
- **ROP-chain DSL callbacks.** Functions whose name appears as a positional argument to a `dry-python/returns` chain method (`.bind`, `.map`, `.alt`, `.lash`, `.apply`, `.bind_result`, `.bind_ioresult`) are exempt. The library invokes these callbacks positionally with the unwrapped `Success` / `Failure` value; positional-order ambiguity does not arise.
- **Protocol method definitions.** Methods declared inside a class whose direct-parent base is `Protocol` are exempt; a `Protocol` class is a structural type-system surface documenting the shape of an external API.

Enforced by `just check-keyword-only-args` (AST).

### Structural pattern matching

`match` statements destructuring livespec-authored classes MUST use keyword patterns, not positional patterns. Concrete form: `case Foo(x=x, y=y)` (keyword) rather than `case Foo(x, y)` (positional). This eliminates the need for `__match_args__` on any livespec class — the class pattern binds attributes by name directly from the instance.

Rules:

- Livespec-authored classes (anything under `.claude-plugin/scripts/livespec/**`, `dev-tooling/**`, or `.claude-plugin/scripts/bin/**`) MUST NOT declare `__match_args__` at class scope.
- Class patterns in `match` statements whose class resolves to a livespec-authored class MUST use keyword sub-patterns.
- Class patterns resolving to third-party types (e.g., `dry-python/returns`'s `IOFailure`, `IOSuccess`, `Result.Success`, `Result.Failure`) MAY use positional destructure, because those libraries define `__match_args__` idiomatically for sum-type wrappers.

Enforced by `just check-match-keyword-only` (AST).

**HelpRequested example.** Under the keyword-only rules, the supervisor's three-way match dispatch reads:

```python
from typing_extensions import assert_never

match result:
    case IOFailure(HelpRequested(text=text)):
        sys.stdout.write(text)
        return 0
    case IOFailure(err):
        log.error("livespec failed", error=err)
        return err.exit_code
    case IOSuccess(report):
        return 0
    case _:
        assert_never(result)
```

The outer `IOFailure(...)` uses positional destructure (permitted — `IOFailure` is from `dry-python/returns`). The inner `HelpRequested(text=text)` uses keyword destructure. `HelpRequested` declares no `__match_args__`. The trailing `case _: assert_never(result)` is mandatory per `## ROP composition — Exhaustiveness`.

### CLAUDE.md coverage

Every directory under:

- `.claude-plugin/scripts/` (with the entire `_vendor/` subtree explicitly excluded), AND
- `<repo-root>/tests/` (with the entire `fixtures/` subtree explicitly excluded at any depth — e.g., `tests/fixtures/` AND `tests/e2e/fixtures/` per v014 N9), AND
- `<repo-root>/dev-tooling/`

MUST contain a `CLAUDE.md` file describing the local constraints an agent working in that directory must satisfy.

Each `CLAUDE.md`:

- States the directory's purpose in one sentence.
- Lists directory-local rules (e.g., "this directory is pure; no imports from `io/`").
- Links to the global style doc for global rules rather than duplicating.
- Is kept short (typically under 50 lines); it's a local crib sheet, not a full reference.

One optional `tests/fixtures/CLAUDE.md` (and `tests/e2e/fixtures/CLAUDE.md`) is permitted but not required; subdirectories under any `fixtures/` tree are never required to carry `CLAUDE.md`. The `_vendor/` carve-out prevents forcing `CLAUDE.md` inside vendored libs.

Enforced by `just check-claude-md-coverage`.


### Behavior-clause-to-scenario link check

The `behavior_scenario_link` enforcement-suite check extracts every `MUST` / `MUST NOT` / `SHOULD` / `SHOULD NOT` behavior clause from the live core spec's behavior-bearing files (`spec.md`, `contracts.md`, `constraints.md`, `non-functional-requirements.md`) via the shared `dev-tooling/spec_clauses.py` extractor, derives each clause's gap-id, and surfaces every clause whose gap-id has no `clauses[]` link to a live `scenarios.md` `##` (H2) section in `tests/heading-coverage.json`. The `clauses[]` link shape is defined in `constraints.md` §"Heading taxonomy".

The check MUST be always-wired into the `just check` aggregate and always-running; it MUST NOT be silently skipped. Its severity is governed by a self-documenting per-check lever — the `LIVESPEC_BEHAVIOR_SCENARIO_LINK` environment variable — whose only recognized values are `warn` and `fail`. In `warn` mode (the DEFAULT) the check MUST surface each unlinked behavior clause as a warning and exit `0`; this is the advisory posture while the clause-to-scenario link backlog is backfilled. In `fail` mode the check MUST surface each unlinked behavior clause as an error and exit non-zero. An unset or unrecognized lever value MUST default to `warn`.

The lever is the SEVERITY switch, NOT a wiring carve-out: the check always extracts every behavior clause and always runs regardless of the lever value, per the carve-out-is-a-severity-lever-not-an-invariant-relax discipline. Enforced by `just check-behavior-scenario-link`.


### Commit and merge discipline

Every commit on every branch and every commit landing on `master` MUST conform to Conventional Commits 1.0:

```
<type>[(scope)][!]: <subject>

[optional body]

[optional footers]
```

Valid types: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `revert`. Breaking changes MUST be indicated by `!` after the type/scope OR a `BREAKING CHANGE:` footer (or both).

`master` accepts only **rebase-merge**. Squash-merge and merge-commit strategies are forbidden at the GitHub repo-settings level (`allow_squash_merge: false`, `allow_merge_commit: false`, `allow_rebase_merge: true`). Combined with `required_linear_history: true`, every commit on `master` is a per-cycle commit landed individually with its own Conventional Commits subject — including `!` breaking-change markers — intact. release-please reads each commit's type directly without squash flattening or PR-title cross-check.

The local commit-msg hook MUST validate the Conventional Commits subject prefix as the FIRST step, BEFORE the v034 D3 Red→Green replay dispatch. Non-conformant subjects MUST exit non-zero regardless of staged shape. The validation regex pins the canonical type set: `^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)(\([^)]+\))?!?: .+`. The hook MUST emit a structured diagnostic naming the canonical type set when rejecting.

A CI workflow validating PR titles for Conventional Commits conformance is OPTIONAL and advisory only (PR titles are NOT load-bearing under rebase-merge since per-commit subjects land on `master`). The OPTIONAL workflow MAY be added separately if the open-PR list becomes noisy with non-Conventional titles.

The plugin's release versioning is auto-managed via `release-please` from per-commit Conventional Commits per `contracts.md` §"Plugin versioning". The Conventional Commits mandate is the load-bearing input that makes release-please's auto-bump mechanism deterministic.

### Workflow discipline — spec-side changes

Every change to a livespec-governed `SPECIFICATION/` tree (this repo and every sibling-repo `SPECIFICATION/`) MUST land via a worktree → PR → merge → cleanup cycle. The discipline:

1. Create a fresh `git worktree` on a new branch (typically `<type>/<topic>` per Conventional Commits — `spec/...`, `docs/...`, `feat/...`, `fix/...`, etc.).
2. Do every commit inside the worktree. The primary worktree (the one bound to `master`) MUST NOT carry uncommitted spec-tree edits at any time.
3. Run `/livespec:propose-change`, `/livespec:critique`, `/livespec:revise`, and any doctor passes from within the worktree.
4. Open a PR via `gh pr create`. CI runs against the worktree branch.
5. Rebase-merge the PR to `master` (per the rebase-merge-only rule already codified for `master`).
6. After the merge lands, remove the worktree (`git worktree remove <path>`) and delete the local branch. The remote branch deletion is part of the same step (use `gh pr merge --delete-branch`).

This rule codifies both the PRESCRIPTIVE side (every change starts on a fresh worktree) and the CLEANUP side (step 6 removes the worktree and branches after the merge). Mechanical stale-worktree detection is the orchestrator's janitor territory (see §"Orchestrator-internal Dispatcher guidance"), not a core doctor invariant.

Direct edits to `master`, leaving uncommitted state in the primary worktree across sessions, or asking the user per-step "should I commit?" confirmation gates are all FORBIDDEN.

A future doctor invariant SHOULD detect master-direct uncommitted spec-tree edits as a `warn` finding (the static phase MAY check for untracked / modified files under `<spec-root>/` in the primary worktree).

**Primary-checkout commit-refuse hook.** Every livespec-governed primary checkout MUST host a populated working tree tracking `origin/master` via normal `git pull --ff-only` AND MUST install a `.git/hooks/pre-commit` and `.git/hooks/pre-push` hook that refuses to run at the primary. The rule is family-wide-by-intent: it applies UNIFORMLY to `livespec` itself, every `livespec-orchestrator-*` plugin's primary checkout, `livespec-dev-tooling`'s primary checkout, `livespec-runtime`'s primary checkout, and every future sibling repo generated from the copier template per §"Shared content sync — copier template". A repo whose primary checkout lacks the commit-refuse hook (or whose hook body does not match the canonical livespec body) is out-of-contract regardless of which family role it plays. `core.bare` MUST NOT be set on the primary checkout — the v091–v094 bare-flag mechanism is superseded by this hook mechanism, and the bare-flag-induced stale-on-disk-read failure mode is the explicit motivation for the swap.

The hook body is a small portable POSIX-shell snippet that runs `git rev-parse --show-toplevel`, compares the result to the consumer's configured primary path (stored under `livespec.primaryPath` in the primary's `.git/config` and set by the bootstrap step), and exits 1 with a "use a worktree" message on match (refusing the commit / push at the primary) or exits 0 on mismatch (allowing the commit / push at a worktree). Because secondary worktrees share the primary's `.git/` directory and therefore inherit the same hook script, but `git rev-parse --show-toplevel` returns the WORKTREE's path (not the primary's) when invoked inside a worktree, the toplevel comparison fails inside every worktree and the hook is a silent no-op there. The mechanism is the minimum that achieves the "no commits at primary" guarantee while leaving the working tree populated and `git pull --ff-only`-refreshable.

The hook pairs with two companion mechanisms: a bootstrap step (see §"Commit-refuse hook bootstrap procedure" below) that idempotently installs the hook on fresh clones, and the `primary-checkout-commit-refuse-hook-installed` doctor static invariant (see `contracts.md` §"Doctor cross-boundary invariants") that verifies the hook is installed and contains the canonical body on every doctor run. The canonical implementation of the latter ships in `livespec-dev-tooling` at `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed` per §"Shared code sync — livespec-dev-tooling"; every consumer repo MUST wire it into its `just check` aggregate AND CI matrix on the same invocation-agnostic cadence governing every other shared check, per the wiring-completeness invariant codified in §"Shared code sync — livespec-dev-tooling" (added by v094). Per-clone non-hook state is the failure mode the bootstrap step addresses; user-tampering or pre-bootstrap clones are the failure mode the doctor invariant addresses. Together the three (NFR rule, bootstrap step, doctor invariant) make the workflow discipline structurally enforceable rather than author-vigilance-dependent — and the universality of the rule means a single shared implementation of the check satisfies the contract for every sibling at once.

The mechanism explicitly preserves on-disk reads at the primary. Doctor cross-boundary invariants and ad-hoc agent reads MAY read filesystem paths at the primary directly; `git show HEAD:<path>` is no longer required as a workaround for stale-working-tree state. The bare-flag-era workaround of routing every primary read through `git -C <clone> show HEAD:<path>` becomes obsolete upon adoption of this contract.

### Commit-refuse hook bootstrap procedure

Every livespec-governed repository MUST surface an idempotent bootstrap entry point that, when invoked, installs the canonical commit-refuse hook body at `.git/hooks/pre-commit` AND `.git/hooks/pre-push` in the primary checkout, and sets `livespec.primaryPath` in the primary's `.git/config` to the absolute path of the primary checkout. The exact entry point shape is implementation choice (a `just bootstrap` target, a livespec-managed setup skill, a hook chained into clone-time tooling, etc.); the contract is that:

1. The entry point MUST be documented in the repo's `README.md`, `CLAUDE.md`, or equivalent first-touch-discovery surface.
2. Running the entry point on a fresh clone MUST result in `.git/hooks/pre-commit` and `.git/hooks/pre-push` both existing, executable (`chmod +x`), and containing the canonical livespec commit-refuse hook body, AND `livespec.primaryPath` being set in `.git/config` to the absolute path of the primary checkout.
3. Running the entry point again on a checkout that already has the canonical hook body installed at both paths AND the correct `livespec.primaryPath` MUST be a no-op (idempotent; no error, no duplicate content, no side-effect).
4. The entry point MAY perform other clone-time setup (lefthook installation, dependency installation, mise tool resolution) as long as the hook-install step is uncoupled from the rest (a partial failure in another setup step MUST NOT leave the hook unset).
5. When `.git/hooks/pre-commit` or `.git/hooks/pre-push` already exists with non-canonical content (a user-customized hook), the entry point MUST NOT silently overwrite. Acceptable resolutions: (a) emit a warning naming the customized hook path and require the user to either remove the customization or manually merge the livespec hook body into it; (b) preserve the customized hook and emit a `warn` finding that the doctor invariant will subsequently surface. The entry point MUST NOT proceed as if the install succeeded when a custom hook is present.

The bootstrap step is what makes the family-wide commit-refuse hook mandate enforceable across clones rather than constituting a single-workstation hack. Doctor's `primary-checkout-commit-refuse-hook-installed` invariant (see `contracts.md` §"Doctor cross-boundary invariants") verifies the hook's presence and canonical body; the bootstrap step is the mechanism by which a user resolves a doctor `fail` finding on that invariant.

The bootstrap-step requirement is itself family-wide-by-intent: every livespec-governed sibling repo — `livespec`, every `livespec-orchestrator-*` plugin, `livespec-dev-tooling`, `livespec-runtime`, and every copier-template-generated sibling — MUST surface its own idempotent bootstrap entry point satisfying the five contract clauses above. The shared check at `livespec_dev_tooling.checks.primary_checkout_commit_refuse_hook_installed` is the mechanical verifier across the family; the per-repo `just bootstrap` recipe (or equivalent entry point) is the mechanical fixer that resolves a `fail` finding on a fresh or tampered clone. The bootstrap implementation is per-repo-private — a sibling MAY embed the hook-install steps directly, MAY copy a starter recipe from `livespec`'s own `justfile`, or MAY inherit it via copier-template scaffolding — but the contractual existence of an idempotent bootstrap entry point is universal.

The canonical hook body is a small portable POSIX-shell snippet of the following shape (illustrative; the canonical text lives in `livespec-dev-tooling` alongside the shared check implementation and is the source of truth for the canonical body the doctor invariant compares against):

```sh
#!/bin/sh
# livespec commit-refuse hook — refuses commits/pushes at the primary checkout.
# No-op at worktrees because git rev-parse --show-toplevel returns the worktree path there.
primary_path="$(git config --get livespec.primaryPath || true)"
toplevel="$(git rev-parse --show-toplevel)"
if [ -n "$primary_path" ] && [ "$toplevel" = "$primary_path" ]; then
  echo "livespec: refusing commit/push at primary checkout ($toplevel); use a worktree" >&2
  exit 1
fi
exit 0
```

The configured primary path is stored under `livespec.primaryPath` in the primary's `.git/config` and is set by the bootstrap step. Worktrees inherit the `.git/` directory but their `git rev-parse --show-toplevel` returns the worktree's own path, so the comparison fails and the hook exits 0.

### CI as a merge gate (branch protection)

**CI as a merge gate.** Every livespec-governed primary repo's `master` branch MUST have GitHub branch protection configured so that the repo's CI matrix checks are REQUIRED status checks. A pull request MUST NOT be mergeable while CI is red: the required-check gate MUST block the merge until every CI matrix check reports success. The rule is family-wide-by-intent: it applies UNIFORMLY to `livespec` itself, every `livespec-orchestrator-*` plugin, `livespec-dev-tooling`, `livespec-runtime`, and every future sibling repo generated from the copier template per §"Shared content sync — copier template". A repo whose `master` lacks required-check branch protection is out-of-contract regardless of which family role it plays.

The protection MUST set `enforce_admins` (no admin bypass of the required checks — repository administrators are subject to the same red-CI block as every other contributor) AND MUST require branches be up to date before merging (`strict`, so a pull request MUST be rebased onto the latest `master` before its required checks count toward mergeability). The required-check set MUST cover the repo's full CI matrix; a protection whose required-check set omits any CI matrix check is out-of-contract because the omitted check becomes advisory again.

IMPORTANT — why this is declared as its own infra rule rather than treated as already-covered by CI existing: branch protection is GitHub repository *settings*, NOT a committed file in the repository tree. It therefore does NOT propagate when a sibling is scaffolded from the copier template (the copier channel ships only static files per §"Shared content sync — copier template"), and it MUST be enabled per-repo as an explicit out-of-band setup step. Without it, CI runs but is purely advisory: `gh pr merge --auto` merges a pull request instantly without waiting for the CI run, and a red pull request can land on `master`. That exact failure already occurred (a red pull request merged to `master` because no required-check gate existed); this rule is the contract that prevents its recurrence.

The rule pairs with two companion mechanisms, realizing the same NFR-rule + bootstrap + doctor-invariant triad the commit-refuse-hook rule uses (see the **Primary-checkout commit-refuse hook** rule under §"Workflow discipline — spec-side changes"): a per-repo setup step that enables the protection on `master` with the required-check set, `enforce_admins`, and `strict` (the exact entry-point shape is implementation choice — a `gh api` call in a bootstrap recipe, a documented one-time `gh` invocation, or template-adjacent setup tooling — but the contractual requirement is that the protection is enabled per-repo, since the copier template cannot carry it); and the `branch_protection_alignment` shared check, which is the mechanical enforcer. The `branch_protection_alignment` check ships from `livespec-dev-tooling`'s shared inventory per §"Shared code sync — livespec-dev-tooling" (its intent and CLI surface are stable across every livespec-governed project, so a single implementation is correct for the whole family). The check MUST fail when branch protection is absent on `master`, when `enforce_admins` is not set, when `strict` is not set, or when the protection's required-check set does not cover the repo's CI matrix. Every consumer repo MUST wire `branch_protection_alignment` into its `just check` aggregate AND CI matrix on the same invocation-agnostic cadence governing every other shared check, per the wiring-completeness invariant codified in §"Shared code sync — livespec-dev-tooling". Together the three (this NFR rule, the per-repo enable step, and the `branch_protection_alignment` check) make the merge-gate discipline structurally enforceable rather than author-vigilance-dependent — and the universality of the rule means a single shared implementation of the check satisfies the contract for every sibling at once.

### Family secrets — 1Password Environment as canonical source

**Canonical source.** The livespec 1Password Environment — consumed via the installed `with-livespec-env.sh` wrapper from the 1password-env-wrapper project — is the SINGLE canonical source for every family-scoped secret: the GitHub App bump-bot credentials (`APP_ID`, `APP_PRIVATE_KEY` — one canonical App private key shared by all family repos), the per-tenant beads/Dolt passwords, the Fabro-dispatch Claude Code OAuth token, and the per-consumer Anthropic API keys (`ANTHROPIC_API_KEY_<CONSUMER>`; first consumer: the weekly e2e canary's `ANTHROPIC_API_KEY_LIVESPEC_E2E`).

**Local consumption rule.** Processes MUST consume secrets via environment injection — invoked under the wrapper. Standing secret-bearing files at rest on the host are PROHIBITED. The single permitted at-rest secret is the wrapper's own 1Password service-account token, sealed via systemd-creds; that token is the bootstrap root of trust.

**Scoped transient-materialization rule.** Where a consumer's interface physically cannot read environment variables (config-file-only interfaces), a run-scoped projection — generated from the environment at invocation time and removed when the run ends — is permitted; standing copies remain PROHIBITED.

**GitHub Actions exception.** Hosted runners can only read GitHub's own encrypted secret store, so Actions secrets are DERIVED projections of the Environment, pushed via `gh secret set` executed under the wrapper. Rotation is: update the Environment once, then re-run the projection.

**Write-side constraint.** The `op` CLI has no Environment write surface (`op environment read` only) and the family service account holds zero vault grants; adding or rotating canonical values is a manual operator step in the 1Password UI.

**No leakage.** Secret values are never committed and never echoed into transcripts or logs — they are referenced by variable name only.

**Per-consumer Anthropic API key naming.** One Anthropic API key per consumer. The key is named `ANTHROPIC_API_KEY_<CONSUMER>` both in the 1Password Environment and as the GitHub Actions secret name, and the key is named after its consumer in the Anthropic console; it is mapped to the SDK's required `ANTHROPIC_API_KEY` env var only at the consuming workflow's `env:` hop. First consumer: the weekly e2e canary → `ANTHROPIC_API_KEY_LIVESPEC_E2E`.

### Fleet membership contract

**Fleet manifest.** A committed file in livespec core — `fleet-manifest.jsonc` at the repo root — enumerates every family repo and its repo class (core / enforcement-suite / orchestrator-plugin / driver-plugin / library). Livespec core owns fleet-level facts (precedent: the copier template at `templates/impl-plugin/` is already core-hosted and sibling-consumed per §"Shared content sync — copier template"); per-repo facts stay in consumer-local config. Both the release fan-out and the fleet-conformance check MUST read the manifest — fetched from livespec master at run time — with the GitHub `livespec-sibling` topic demoted to a discovery safety net (see the **Discovery safety net** rule below).

**Obligations per repo class.** Each repo class carries obligations organized by the three obligation types: committed files (the shim workflows `bump-pin-from-dispatch.yml` / `pin-freshness.yml` / `release-dispatch.yml` for pin-consuming classes, `ci.yml`, the dev-tooling pin, and copier-answers for template-born classes); GitHub-side state (the `livespec-sibling` topic, `APP_ID` + `APP_PRIVATE_KEY` secrets present, the GitHub App installation, and branch protection present AND aligned per §"CI as a merge gate (branch protection)"); and host-side state (the per-repo beads tenant — backend-specific usage rules live in the relevant `livespec-orchestrator-<ledger>[-<loop>]` plugin's own `SPECIFICATION/` per §"Toolchain pins" — and the primary-checkout commit-refuse hooks per the **Primary-checkout commit-refuse hook** rule under §"Workflow discipline — spec-side changes").

**Fleet-conformance enforcement.** A dev-tooling check enumerates the manifest and asserts each member's obligations from a central vantage point — the piece repo-local CI cannot provide, because a repo missing wiring never fails checks it does not run. It runs on a schedule AND as a BLOCKING preflight of the dev-tooling release fan-out: an unwired member fails the release fast and loudly instead of being silently skipped.

**Reconcile mode.** An idempotent `wire-fleet-member` operation shares the conformance check's contract definition — assert mode is CI; reconcile mode is wiring — with secrets flowing through the 1Password projection per §"Family secrets — 1Password Environment as canonical source".

**Discovery safety net.** The conformance run also flags any repo under the family owner matching the `livespec-*` naming or carrying the `livespec-sibling` topic that is NOT in the manifest.

**Repo birth procedure.** Scaffold (via the copier template where the class has one) → register in the manifest FIRST → run `wire-fleet-member` → fleet conformance green. Register-first makes a half-wired new repo red fleet CI rather than an invisible straggler.

**New-obligation discipline.** A change adding an obligation row MUST wire all current members in the same change — the retrofit travels with the rule. The check's fail-fast bite is reserved for new members and regressions, so the fleet is never red by construction at the moment a rule lands.

**No-circular-gating rule.** A conformance failure MUST NOT be fixable only by an action the check itself gates; wiring MUST NOT depend on a dev-tooling release going out.

### Hook chaining

Livespec-installed git hooks MUST chain to pre-existing project hooks rather than replace them. A hook that livespec tooling installs into a repository whose existing gates (`just check` / pre-commit / pre-push) already run as hooks MUST run those pre-existing gates FIRST, then run its own behavior, while preserving and returning the pre-existing gates' exit status.

### Codex dogfooding constraints

Codex compatibility for repository dogfooding MUST NOT duplicate LiveSpec operation prose, Python wrappers, or built-in specification templates.

Core prose under `.claude-plugin/prose/<name>.md` and wrapper CLIs under `.claude-plugin/scripts/bin/` are the shared source of truth for core LiveSpec command behavior. Codex project skills MUST remain thin adapters over those files; they MUST NOT copy or restate operation-specific steps, failure handling, output schemas, or wrapper behavior in a way that can drift from the shared core files. Codex project skills MUST NOT point at `.claude-plugin/skills/*` or require that tree to exist.

The current repository MAY claim Codex-native project-skill support only for the verified project-local `.agents/skills/livespec-help`, `.agents/skills/livespec-next`, and `.agents/skills/livespec-doctor` adapters. It MUST NOT claim Codex-native plugin marketplace support solely because a `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, or `plugins/livespec/` package exists. A Codex-native plugin registry path is accepted only after marketplace registration creates an installed LiveSpec plugin entry and a separate `codex exec` invocation can use that registered plugin without relying on `.agents/skills/*` or `AGENTS.md`.

Codex dogfooding MUST work without installing or modifying global/system packages. Temporary local Codex marketplace registrations used for testing MUST be removed after the test unless the user explicitly asks to keep them.

The Codex adapter surface MUST preserve destructive-command controls from the core prose. In particular, `prune-history` remains explicit-user-invocation only, and Codex MUST NOT infer or auto-activate it from a generic mention of history. Until mutating adapters are separately specified and proven, Codex MUST NOT expose project-local adapters for `seed`, `propose-change`, `critique`, `revise`, or `prune-history`.

## Scenarios

Contributor-facing Gherkin scenarios — the analogue of `scenarios.md`'s role for the user-facing surface. Each scenario uses the gherkin-blank-line convention (one step per paragraph, no fenced code blocks) so every step renders as its own Markdown paragraph.

### Scenario: Codex help maps through the project adapter to core prose

Given a maintainer is running OpenAI Codex CLI/TUI in the `livespec` repository

And `.agents/skills/livespec-help/SKILL.md` exists

When the maintainer asks `/livespec:help`

Then Codex reads `.agents/skills/livespec-help/SKILL.md`

And Codex reads `.claude-plugin/prose/help.md`

And Codex produces the LiveSpec help overview from that core prose

And Codex does not require a Codex-native plugin install

### Scenario: Codex next dry run identifies the shared wrapper

Given a maintainer is running OpenAI Codex CLI/TUI in the `livespec` repository

And `.agents/skills/livespec-next/SKILL.md` exists

When the maintainer asks for a read-only `livespec next` dry run

Then Codex reads `.agents/skills/livespec-next/SKILL.md`

And Codex reads `.claude-plugin/prose/next.md`

And Codex identifies `.claude-plugin/scripts/bin/next.py` as the wrapper it would invoke

And Codex does not duplicate or reimplement the wrapper contract

### Scenario: Codex doctor help identifies the static wrapper

Given a maintainer is running OpenAI Codex CLI/TUI in the `livespec` repository

And `.agents/skills/livespec-doctor/SKILL.md` exists

When the maintainer asks for `livespec doctor help only`

Then Codex reads `.agents/skills/livespec-doctor/SKILL.md`

And Codex reads `.claude-plugin/prose/doctor.md`

And Codex identifies `.claude-plugin/scripts/bin/doctor_static.py` as the wrapper it would invoke

### Scenario: Codex plugin registry is not assumed from metadata alone

Given `.codex-plugin/plugin.json` or `.agents/plugins/marketplace.json` exists

When marketplace registration does not create an installed LiveSpec plugin entry

Then repository documentation MUST NOT claim Codex-native plugin support

And Codex dogfooding continues through the verified project-local `.agents/skills/livespec-*` adapters and `AGENTS.md` repository instructions
