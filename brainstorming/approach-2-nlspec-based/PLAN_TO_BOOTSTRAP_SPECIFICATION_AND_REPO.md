# Plan: Bootstrap the `livespec` specification and repo

**Status:** Pre-execution. This document captures everything required
to exit the brainstorming phase and stand up a working `livespec`
repo whose own `SPECIFICATION/` tree is seeded from the brainstorming
artifacts and whose skill bundle implements the PROPOSAL.

**Version basis.** The plan body below is written against
PROPOSAL.md v022, which has now been produced by:
1. the continuation interview pass that landed v018
   Q1-Option-A (template sub-specifications) alongside v018
   Q2-Q6,
2. a fast-track single-issue revise (v019 Q1) that resolved
   a logical contradiction in v018 §"Self-application" steps
   2/4 + the Q2 bootstrap-exception clause,
3. a four-issue critique pass (v020 Q1-Q4) closing two
   shipped-contract defects in the v018 Q1 template-sub-
   specification mechanism (Q1 — `minimal` sub-spec
   structural contradiction; Q2 — `livespec` template's seed
   prompt unconditionally emitted `sub_specs[]`) plus two
   plan-level quality fixes (Q3 — Phase 3 sub-spec routing
   smoke check; Q4 — Phase 3 four-prompt widening), AND
4. a three-issue critique pass (v021 Q1-Q3) closing one
   PROPOSAL ↔ PLAN consistency defect in the v018 Q1 doctor
   static-check applicability mechanism (Q1 — orchestrator-
   only dispatch; `template_scope` field on `DoctorContext`
   replaced by `template_name`; per-check `APPLIES_TO`
   constants and `gherkin_blank_line_format` runtime-skip
   removed) plus two plan-level under-specifications (Q2 —
   Phase 3 `seed/SKILL.md` enumerates the v020 Q2 three-
   question pre-seed dialogue explicitly; Q3 — Phase 6
   names an explicit imperative one-time
   `tests/heading-coverage.json` population sub-step).

v018 decisions still in force:
- v018 Q2: explicit bootstrap-exception clause in §"Self-
  application" (imperative window ends at first seed).
- v018 Q3: one-time initial-vendoring procedure in
  §"Vendoring discipline" (applies at Phase 2 of this plan).
- v018 Q4: closures for `returns-pyright-plugin-disposition`
  (vendor the plugin as sixth vendored lib) and
  `basedpyright-vs-pyright` (stay on pyright). Both land at
  Phase 1 via `pyproject.toml` pinning per the
  post-commit-b041d19 plan revision.
- v018 Q5: new prompt-QA tier at `tests/prompts/<template>/`
  + `just check-prompts` recipe in Phase 5 test-suite phase.
- v018 Q6: Companion-documents migration-class policy +
  per-doc assignment table in PROPOSAL.md §"Self-application"
  (Phase 6 / Phase 8 consumption).

v019 decision:
- v019 Q1: Step 2 of §"Self-application" is widened to
  include minimum-viable implementations of `propose-change`,
  `critique`, and `revise` (alongside the seed surface)
  sufficient to file the first dogfooded change cycle against
  the seeded `SPECIFICATION/`. Step 4 is re-narrated as pure
  widening of those minimum-viable sub-commands to full
  feature parity, plus implementation of `prune-history` and
  doctor's LLM-driven phase, all via dogfooded
  propose-change/revise cycles. The Q2 bootstrap-exception
  clause's "imperative window ends at first seed" boundary is
  unmoved; an acknowledgment sentence is appended noting that
  step 2's widening lands minimum-viable sub-commands BEFORE
  the seed (inside the imperative window).

v020 decisions:
- v020 Q1: Sub-specs are reframed as livespec-internal
  artifacts using the multi-file livespec layout uniformly,
  decoupled from the end-user-facing convention of the
  template the sub-spec describes. The `minimal` sub-spec
  gains a sub-spec-root `README.md` and a per-version
  `README.md` snapshot it did not have in v019. PROPOSAL.md
  §"Template sub-specifications" framing line + `minimal`
  diagram + §"`seed`" wrapper file-shaping item 5 amended
  accordingly. Plan Phase 6 per-tree description for the
  `minimal` sub-spec is amended uniformly with the `livespec`
  sub-spec.
- v020 Q2: Sub-spec emission becomes opt-in via a new
  pre-seed dialogue question ("Does this project ship its own
  livespec templates that should be governed by sub-spec
  trees? — default: no"). The shipped `livespec` template's
  seed prompt no longer hard-codes sub_specs[] emission;
  end-user projects get `sub_specs: []` by default.
  PROPOSAL.md §"`seed`" pre-seed-template-selection paragraph
  + sub_specs-payload paragraph amended. Plan Phase 2
  (livespec template's `prompts/seed.md` minimum-viable scope
  includes the dialogue question), Phase 3 (bootstrap-minimum
  widening handles both dialogue branches rigorously), and
  Phase 6 (seed intent block answers "yes" and names the two
  built-ins) updated accordingly.
- v020 Q3: Phase 3 exit criterion grows by one propose-
  change/revise smoke cycle targeting the sub-spec tree
  (`<tmp>/SPECIFICATION/templates/livespec`). PROPOSAL.md
  unchanged.
- v020 Q4: Phase 3 widens all four `livespec`-template
  prompts (`seed`, `propose-change`, `revise`, `critique`)
  to bootstrap-minimum, mirroring v019's existing seed.md
  widening pattern. Resolves the quality risk where Phase 7's
  heaviest semantic work would otherwise run through Phase
  2-minimum prompts. PROPOSAL.md unchanged.

v021 decisions:
- v021 Q1: Doctor static-check applicability dispatch is
  collapsed to a single source at the orchestrator level.
  PROPOSAL.md §"doctor → Static-phase orchestrator" — the
  `DoctorContext` field added under v018 Q1 is finalized as
  `template_name: str` (replacing the binary
  `template_scope: Literal["main", "sub-spec"]`). The
  per-check `APPLIES_TO: frozenset[Literal["main",
  "sub-spec"]]` constant introduced in the prior plan
  revision is dropped; the registry shape reverts to
  `(SLUG, run)` pairs. The `gherkin_blank_line_format`
  runtime-skip-via-Finding mechanism for the `minimal`
  sub-spec is removed; applicability is decided by the
  orchestrator-owned table per (template_name, check_slug).
  PROPOSAL.md §"Per-tree check applicability" (existing
  prose) is now the authoritative table. PLAN Phase 3
  context.py + run_static.py + static/__init__.py +
  static/ per-check bullets amended; Phase 8 item 16's
  `template_scope` reference swapped to `template_name`.
- v021 Q2: PLAN Phase 3 `seed/SKILL.md` bullet enumerates
  the v020 Q2 three-question pre-seed dialogue explicitly:
  (1) template-selection question; (2) sub-spec-emission
  question with default "no"; (3) on "yes", template-name
  follow-up. PROPOSAL.md unchanged (already explicit at
  §"`seed`" lines 1717-1759).
- v021 Q3: PLAN Phase 6 names an explicit imperative
  one-time `tests/heading-coverage.json` population sub-step
  performed by the executor agent after the seed wrapper
  succeeds and before Phase 6's exit criterion is asserted.
  Justified under the v018 Q2 / v019 Q1 bootstrap-exception
  clause (Phase 6 is the imperative window's closing step).
  PROPOSAL.md unchanged (the seed wrapper's file-shaping
  contract at §"`seed`" items 1-6 is unchanged; the meta-
  test data file population is outside the wrapper's
  scope).

PROPOSAL.md v028 is now the frozen basis for every phase
below; Phase 0 freezes at v028. (v023 is a critique-fix
overlay against v022 with no PROPOSAL.md substance change;
v024 is a critique-fix overlay against v023 WITH PROPOSAL.md
substance change — the UV-toolchain decision; v025 is a
critique-fix overlay against v024 WITH PROPOSAL.md substance
change — drops the non-existent `returns_pyright_plugin`
vendoring (pyright has no plugin system; no upstream artifact
exists) and corrects the `returns` license label to
BSD-3-Clause; v026 is a critique-fix overlay against v025
WITH PROPOSAL.md substance change — reclassifies
`jsoncomment` from upstream-sourced lib to hand-authored
shim (per the v013 M1 pattern) because the canonical upstream
(`bitbucket.org/Dando_Real_ITA/json-comment`) was sunset by
Atlassian and no live git mirror exists, so the v018 Q3
git-based initial-vendoring procedure cannot apply; v027 is
a critique-fix overlay against v026 WITH PROPOSAL.md
substance change — reclassifies `typing_extensions` from
hand-authored shim (v013 M1) to upstream-sourced lib
(vendored full upstream verbatim at tag `4.12.2`) because
the v013 M1 minimal-shim approach cannot satisfy variadic-
generics usage (`Generic[..., Unpack[TypeVarTuple(...)]]`)
inside the vendored returns lib on Python 3.10; PROPOSAL.md
v013 M1 explicitly anticipated this scope-widening path;
v029 is a critique-fix overlay against v028 WITH PROPOSAL.md
substance change — re-aligns the `dev-tooling/checks/`
directory listing (PROPOSAL lines 3496-3520) with the
authored / planned check set (adds `rop_pipeline_shape.py`,
`heading_coverage.py`, `vendor_manifest.py`, `check_tools.py`,
`check_mutation.py` to the listing) and corrects the
`keyword_only_args.py` annotation to enumerate the full
strict-dataclass triple (`frozen=True + kw_only=True +
slots=True`); see the v029 decision block below for
provenance. v028 is a critique-fix overlay against v027 WITH
PROPOSAL.md substance change — corrects the bundle-root
derivation formula at PROPOSAL §"Template resolution
contract" line 1466, replacing the off-by-one
`Path(__file__).resolve().parent.parent` (which resolves
to `.claude-plugin/scripts/`) with the correct
`Path(__file__).resolve().parents[3]` from the
`livespec/commands/resolve_template.py` implementation file
(which resolves to `.claude-plugin/`, where
`specification-templates/` actually lives); see the v023,
v024, v025, v026, v027, v028, and v029 decision blocks below for
provenance.)

v022 decisions (direct critique-fix overlay; see
`history/v022/proposed_changes/critique-fix-v021-revision.md`):
- v022 D1: PROPOSAL §"Built-in template: `livespec`" names a
  new template-root file class **template-bundled prompt-
  reference materials**, with `livespec-nlspec-spec.md` as the
  v1 instance — exempt from the Plan §3 cutover hand-edit ban,
  not sub-spec-governed, not Phase-7 agent-regenerated.
- v022 D2: PROPOSAL §"Template resolution contract — Deferred
  future feature" extends the new file class to custom
  templates.
- v022 D3: PROPOSAL §"Companion documents and migration classes"
  table row for `livespec-nlspec-spec.md` reclassified to
  `ARCHIVE-ONLY + TEMPLATE-BUNDLED-PROMPT-REFERENCE` with
  refined destination column.
- v022 D4 (plan-level): Plan §3 cutover principle carves out
  the new file class.
- v022 D5 (plan-level): Plan Phase 8 item 2 rewritten as
  per-section split (one propose-change/revise per top-level
  section of the source style doc).
- v022 D6 (plan-level): Plan Phase 8 item 14 replaces "see
  Phase 9" pointer with explicit forward-pointing
  bookkeeping-closure mechanism.
- v022 D7 (plan-level): Plan Phase 3 stub policy switches to
  narrowed-registry (Phase 3 registers only the 8 implemented
  doctor-static checks; Phase 7 adds the remaining four
  alongside their implementations).
- v022 D8 (plan-level): Plan Phase 7 ordering preamble
  promotes §6 Risk #5 mitigation language into the work-item
  list (sub-spec widening before regeneration; harness before
  regen-cycle verification).
- v022 D9 (plan-level): Plan Phase 5 line 980 typo
  ("Phase 8" → "Phase 9").
- v022 D10 (plan-level): Plan §8 added describing the
  `bootstrap/` execution-scaffolding directory and the
  bootstrap skill; Phase 0 sub-step list grows by one item;
  Phase 1 preconditions explicitly mention `bootstrap/`;
  Phase 10 exit picks up `bootstrap/` archive-or-delete.

v023 decisions (direct critique-fix overlay; see
`history/v023/proposed_changes/critique-fix-v022-revision.md`):
- v023 D1 (plan-level): Plan Phase 0 step 3 (was: "`tmp/` is
  deleted") replaced with the `tmp/bootstrap/` ownership
  convention — the repo-root `tmp/` is git-untracked
  user-owned scratch and must NOT be deleted; bootstrap-owned
  scratch goes under `tmp/bootstrap/`. Plan Phase 0
  exit-criterion text drops the "`tmp/` removal" clause and
  bumps the freeze commit message label to `freeze: v023
  brainstorming`. Plan Phase 0 step 1 byte-identity reference
  bumps to `history/v023/PROPOSAL.md`. Plan Phase 0 step 2
  frozen-status header literal bumps to "Frozen at v023".
  Plan Execution-prompt block authoritative-version line bumps
  to v023. PROPOSAL.md substance unchanged. Triggered during
  Phase 0 of the in-flight bootstrap by the bootstrap skill's
  cascading-impact scan (skill commit `398bfa8`).

v024 decisions (direct critique-fix overlay; see
`history/v024/proposed_changes/critique-fix-v023-revision.md`):
- v024 D1: PROPOSAL §"Developer-time dependencies (livespec
  repo only)" rewritten to name UV (astral-sh/uv) as the Python
  toolchain manager. UV manages the interpreter version and
  every Python package the enforcement suite requires (`ruff`,
  `pyright`, `pytest`, `pytest-cov`, `pytest-icdiff`,
  `hypothesis`, `hypothesis-jsonschema`, `mutmut`,
  `import-linter`).
- v024 D2: Mise's role narrows to non-Python binaries only —
  `.mise.toml` pins `uv`, `just`, `lefthook`. `python` no
  longer appears in `.mise.toml`.
- v024 D3: Python pin moves from `.mise.toml` to
  `pyproject.toml` `[project.requires-python]` plus a
  committed `.python-version` (managed by `uv python pin`).
  Python dev deps move to `pyproject.toml`
  `[dependency-groups.dev]`, resolved into a committed
  `uv.lock` and installed by `uv sync --all-groups`.
- v024 D4: First-time bootstrap sequence becomes three steps:
  `mise install` → `uv sync --all-groups` → `just bootstrap`.
  `just bootstrap` continues to handle `lefthook install` and
  any other one-time setup.
- v024 D5 (plan-level): Plan Phase 1 first bullet rewritten —
  `.mise.toml` pins `uv`, `just`, `lefthook` only. New plan
  bullet adds `.python-version` + `pyproject.toml`
  `[project.requires-python]` for the Python pin. The
  `pyproject.toml` bullet gains a `[project]` /
  `[dependency-groups.dev]` sub-bullet listing the nine
  Python dev tools. Plan Phase 1 exit criterion adds
  `uv sync --all-groups` between `mise install` and
  `just bootstrap`.
- v024 D6 (plan-level): Plan Phase 0 step 1 byte-identity
  reference bumps to `history/v024/PROPOSAL.md`. Plan Phase 0
  step 2 frozen-status header literal bumps to "Frozen at
  v024". Plan Execution-prompt block authoritative-version
  line bumps to v024.
- v024 D7 (plan-level): Plan §"Preconditions" extends the
  must-not-yet-exist file list with `.python-version` and
  `uv.lock`.
- Triggered during Phase 1 sub-step 1 of the in-flight
  bootstrap when the executor reflex-defaulted to `pipx:` for
  the Python dev-tool backend; user corrected with the
  UV-as-Python-toolchain principle. Routed via the bootstrap
  skill's Case-A PROPOSAL-drift rule (auto-blocking;
  halt-and-revise required).

v025 decisions (direct critique-fix overlay; see
`history/v025/proposed_changes/critique-fix-v024-revision.md`):
- v025 D1: PROPOSAL §"Runtime dependencies — Vendored
  pure-Python libraries" drops `returns_pyright_plugin` from
  the canonical vendored-libs list (now five entries:
  `returns`, `fastjsonschema`, `structlog`, `jsoncomment`,
  `typing_extensions`). PROPOSAL §"Developer-time dependencies
  → Typechecker decision" strikes the `pluginPaths =
  ["_vendor/returns_pyright_plugin"]` claim from
  `[tool.pyright]`. The v018 Q4 closure of the
  `returns-pyright-plugin-disposition` deferred item is
  rescinded and re-closed in v025 with the revised
  disposition: **no pyright plugin is vendored, because no
  such plugin exists upstream and pyright does not support
  plugins by design.** The seven strict-plus diagnostics
  (`reportUnusedCallResult` in particular) remain the
  load-bearing guardrails against silent `Result` /
  `IOResult` discards. The pyright-over-basedpyright decision
  from v018 Q4 is preserved.
- v025 D2 (cosmetic): PROPOSAL.md `returns` license label
  corrected from `BSD-2` to `BSD-3-Clause` to match upstream
  `dry-python/returns` v0.25.0 `pyproject.toml`. Library is
  in policy at either license per style-doc allowed-list (no
  architectural implication; cosmetic ride-along).
- v025 D3 (plan-level): Plan Phase 1 sub-step 3
  (`pyproject.toml`) bullet on `[tool.pyright]` strikes the
  `pluginPaths = ["_vendor/returns_pyright_plugin"]` clause
  and the rationale paragraph that referenced the plugin;
  retains the seven strict-plus diagnostics enumeration and
  the pyright-over-basedpyright closure.
- v025 D4 (plan-level): Plan Phase 1 sub-step 9
  (`.vendor.jsonc`) bullet drops `returns_pyright_plugin`
  from the six-entry enumeration (now five entries: `returns`,
  `fastjsonschema`, `structlog`, `jsoncomment`,
  `typing_extensions`). Plan Phase 2's placeholder-
  replacement note updated correspondingly.
- v025 D5 (plan-level): Plan Phase 1 sub-step 11
  (`NOTICES.md`) bullet drops `returns_pyright_plugin` from
  the six-library enumeration (now five). Plan also corrects
  the `returns` license citation to BSD-3-Clause.
- v025 D6 (plan-level): Plan Phase 2 sub-step 5
  (`.claude-plugin/scripts/_vendor/`) drops the
  `returns_pyright_plugin/` bullet from the vendoring sub-list
  (now five upstream-sourced libs).
- v025 D7 (plan-level): Plan Phase 0 step 1 byte-identity
  reference bumps to `history/v025/PROPOSAL.md`. Plan Phase 0
  step 2 frozen-status header literal bumps to "Frozen at
  v025". Plan Execution-prompt block authoritative-version
  line bumps to v025.

v026 decisions (direct critique-fix overlay; see
`history/v026/proposed_changes/critique-fix-v025-revision.md`):
- v026 D1: PROPOSAL §"Runtime dependencies — Vendored
  pure-Python libraries" reclassifies `jsoncomment` from
  upstream-sourced lib to hand-authored shim per the v013 M1
  pattern. Lib count stays at five; the breakdown shifts to 3
  upstream-sourced (`returns`, `fastjsonschema`, `structlog`)
  + 2 shims (`typing_extensions` per v013 M1; `jsoncomment`
  per v026 D1). The shim retains the import name
  `jsoncomment` (so `import jsoncomment` works unchanged) and
  faithfully replicates jsoncomment 0.4.2's `//` line-comment
  + `/* */` block-comment stripping semantics. License: MIT
  derivative work with verbatim attribution to Gaspare Iengo.
  PROPOSAL §"Vendoring discipline — Initial-vendoring
  exception" drops `jsoncomment` from the v018 Q3 upstream-
  sourced procedure's domain (now: `returns`, `fastjsonschema`,
  `structlog`); the bootstrap-circularity rationale stands but
  the satisfying mechanism shifts from "git-clone-and-copy of
  upstream" to "hand-author the shim at Phase 2 of the
  bootstrap plan."
- v026 D2 (plan-level): Plan Phase 1 sub-step 9
  (`.vendor.jsonc`) bullet's enumeration retains five entries
  total but jsoncomment shifts category — its entry now
  carries `"shim": true`, `"upstream_ref": "0.4.2"`, and
  `"upstream_url": "https://pypi.org/project/jsoncomment/"`
  (the canonical surviving source-of-record on PyPI; the
  bitbucket homepage URL is dead). The Phase 2's placeholder-
  replacement note narrows to the 3 upstream-sourced libs.
- v026 D3 (plan-level): Plan Phase 1 sub-step 11
  (`NOTICES.md`) bullet updates the jsoncomment entry to
  shim status with derivative-work MIT attribution to Gaspare
  Iengo; the prologue framing acknowledges the 3 + 2
  breakdown.
- v026 D4 (plan-level): Plan Phase 2 sub-step 5
  (`.claude-plugin/scripts/_vendor/`) moves `jsoncomment/`
  from the upstream-sourced sub-list to the shim sub-list
  (alongside `typing_extensions/`); the surrounding language
  describing the v018 Q3 procedure scope narrows to the 3
  upstream-sourced libs.
- v026 D5 (plan-level): Plan Phase 0 step 1 byte-identity
  reference bumps to `history/v026/PROPOSAL.md`. Plan Phase 0
  step 2 frozen-status header literal bumps to "Frozen at
  v026". Plan Execution-prompt block authoritative-version
  line bumps to v026.

v027 decisions (direct critique-fix overlay; see
`history/v027/proposed_changes/critique-fix-v026-revision.md`):
- v027 D1: PROPOSAL §"Runtime dependencies — Vendored
  pure-Python libraries" reclassifies `typing_extensions` from
  hand-authored shim (per v013 M1) to upstream-sourced lib
  (vendored full upstream verbatim at tag `4.12.2`). Lib count
  stays at five; the breakdown shifts to 4 upstream-sourced
  (`returns`, `fastjsonschema`, `structlog`,
  `typing_extensions`) + 1 shim (`jsoncomment` per v026 D1).
  PROPOSAL §"Vendoring discipline — Initial-vendoring
  exception" adds `typing_extensions` to the v018 Q3 git-based
  procedure's domain. The "shim libraries" sentence narrows
  to one entry (jsoncomment only). Triggered during Phase 2
  sub-step 5 of the in-flight bootstrap when the smoke test on
  Python 3.10.16 (the pinned dev-env per `.python-version`)
  failed at `from returns.io import IOResult` because
  `returns/primitives/hkt.py` uses
  `Generic[..., Unpack[TypeVarTuple(...)]]` — variadic-
  generics support that 3.10 stdlib lacks and a hand-authored
  minimal shim cannot synthesize on 3.10. PROPOSAL.md v013 M1
  explicitly anticipated this scope-widening path
  ("re-vendoring the full upstream is a future option tracked
  as a scope-widening decision, not a v013 default"); v027 D1
  exercises that decision.
- v027 D2 (plan-level): Plan Phase 1 sub-step 9
  (`.vendor.jsonc`) — `typing_extensions` entry no longer
  carries `"shim": true`. Phase 2's placeholder-replacement
  note widens to cover the 4 upstream-sourced entries;
  `jsoncomment` remains the sole shim with its real
  `upstream_ref` carried from v026 D1.
- v027 D3 (plan-level): Plan Phase 1 sub-step 11
  (`NOTICES.md`) — update typing_extensions block to
  upstream-sourced framing (no longer marked as shim).
- v027 D4 (plan-level): Plan Phase 2 sub-step 5
  (`.claude-plugin/scripts/_vendor/`) moves
  `typing_extensions/` from the shim sub-list to the
  upstream-sourced sub-list. Now 4 upstream-sourced
  + 1 shim (jsoncomment).
- v027 D5 (plan-level): Plan Phase 0 step 1 byte-identity
  reference bumps to `history/v027/PROPOSAL.md`. Plan Phase 0
  step 2 frozen-status header literal bumps to "Frozen at
  v027". Plan Execution-prompt block authoritative-version
  line bumps to v027.
- Triggered during Phase 2 sub-step 5 of the in-flight
  bootstrap when the executor cloned `dry-python/returns` at
  v0.25.0 to vendor the pyright plugin and discovered the
  source artifact does not exist. Sub-agent investigation
  confirmed pyright has no plugin system (microsoft/pyright#607)
  and dry-python explicitly will not support pyright
  (dry-python/returns#1513). Routed via the bootstrap skill's
  Case-A PROPOSAL-drift rule (auto-blocking; halt-and-revise
  required).

v028 decisions (direct critique-fix overlay; see
`history/v028/proposed_changes/critique-fix-v027-revision.md`):
- v028 D1: PROPOSAL §"Template resolution contract" line 1466
  bundle-root derivation formula corrected from
  `Path(__file__).resolve().parent.parent` (which resolves to
  `.claude-plugin/scripts/` — wrong; that's `<scripts-root>`,
  not `<bundle-root>`) to the verbal description "the
  `.claude-plugin/` directory of the installed plugin (the
  parent of the `scripts/` subtree)" plus the concrete formula
  `Path(__file__).resolve().parents[3]` anchored to the
  `livespec/commands/resolve_template.py` implementation file
  where `parents[0]` is `commands/`, `parents[1]` is
  `livespec/`, `parents[2]` is `scripts/`, and `parents[3]` is
  `.claude-plugin/`. The shebang wrapper at
  `bin/resolve_template.py` has no room for path-computation
  logic per the wrapper-shape contract, so the path derivation
  happens in the `commands/` implementation, not the
  shebang wrapper. The directory tree at PROPOSAL lines 88 +
  172 was always correct (`specification-templates/` is a
  sibling of `scripts/` under `.claude-plugin/`); only the
  formula derived from the tree was wrong.
- v028 D2 (plan-level): Plan Phase 0 step 1 byte-identity
  reference bumps to `history/v028/PROPOSAL.md`. Plan Phase 0
  step 2 frozen-status header literal bumps to "Frozen at
  v028". Plan Execution-prompt block authoritative-version
  line bumps to v028.
- Triggered during Phase 3 sub-step 12 of the in-flight
  bootstrap when the executor began `livespec/commands/
  resolve_template.py` implementation work and traced the
  PROPOSAL line 1466 formula against the actual on-disk
  layout. Routed via the bootstrap skill's Case-A
  PROPOSAL-drift rule (auto-blocking; halt-and-revise
  required).

v029 decisions (direct critique-fix overlay; see
`history/v029/proposed_changes/critique-fix-v028-revision.md`):
- v029 D1: PROPOSAL `dev-tooling/checks/` directory listing
  (lines 3496-3520) re-aligned with the authored / planned
  check set. Five filenames added: `rop_pipeline_shape.py`
  (newly authored at Phase 4 sub-step 13 to enforce single-
  public-method on `@rop_pipeline`-decorated classes,
  encoding the Command / Use Case Interactor lineage at the
  class level), plus `heading_coverage.py`, `vendor_manifest.py`,
  `check_tools.py`, `check_mutation.py` — all of which already
  exist in the justfile and the Phase 4 plan but were absent
  from the PROPOSAL listing. Additionally, the
  `keyword_only_args.py` annotation is updated from "frozen=True
  + slots=True" (two-of-three subset) to "frozen=True +
  kw_only=True + slots=True" (the full strict-dataclass triple
  per style doc lines 1311-1320 + the actual implementation in
  `dev-tooling/checks/keyword_only_args.py`).
- v029 D2 (plan-level): Plan Phase 0 step 1 byte-identity
  reference bumps to `history/v029/PROPOSAL.md`. Plan Phase 0
  step 2 frozen-status header literal bumps to "Frozen at
  v029". Plan Execution-prompt block authoritative-version
  line bumps to v029. Plan Phase 4 enforcement-script
  enumeration (line 1419) carries `rop_pipeline_shape.py`
  adjacent to `supervisor_discipline.py` to match PROPOSAL.
- Triggered during Phase 4 sub-step 13 of the in-flight
  bootstrap when the executor authored
  `dev-tooling/checks/rop_pipeline_shape.py` and the cascading-
  impact scan flagged the missing PROPOSAL listing entries.
  Routed via the bootstrap skill's Case-A PROPOSAL-drift rule
  (auto-blocking; halt-and-revise required).
- v030 D1 (PROPOSAL.md): adds a new top-level section
  §"Test-Driven Development discipline" before §"Testing
  approach", codifying Beck-style test-first authoring (Red
  → Green) as the authoring rhythm for any new behavior, and
  refactor as an independent unit of value (no new failing
  test; existing tests stay green). Authoring rhythm vs.
  commit boundaries: commits represent cohesive units of
  user-facing value, NOT phases of an internal RGR cycle.
  Plus the "fail for the right reason" clause, the
  five-category exhaustive exception list, the rationale
  ("why not just the coverage gate"), and the test pyramid
  framing (the 100% gate is anchored at the unit-test layer
  under `tests/livespec/`, `tests/bin/`,
  `tests/dev-tooling/checks/` — integration and prompt-QA
  layers do not contribute to the gate).
- v030 D2 (PROPOSAL.md + style doc): eliminates the
  per-line `# pragma: no cover` escape hatch. The "≤ 3
  pragma-lines per file with reason" allowance from style
  doc lines 1339-1343 is replaced by an outright
  prohibition; the only structural exclusions are
  `if TYPE_CHECKING:`, `raise NotImplementedError`, and
  `@overload` blocks via
  `[tool.coverage.report].exclude_also`. Both prior
  legitimate pragma uses are now addressed structurally
  (TYPE_CHECKING via `exclude_also`; `_bootstrap.py`
  version gate via dedicated `tests/bin/test_bootstrap.py`
  monkeypatched tests, authored Phase 5 sub-step 2 commit
  a2b4f5d). PROPOSAL.md §"Testing approach" coverage
  paragraph gains the matching "no pragma" sentence.
- v030 D3 (PROPOSAL.md): adds an explicit "Activation"
  paragraph to §"Testing approach" stating that the
  hard-constraint pre-commit gate becomes binding at the
  Phase 5 `just bootstrap` promotion sub-step (when
  `lefthook install` runs); pre-Phase-5 commits are
  grandfathered.
- v030 D4 (PROPOSAL.md): adds a one-sentence cross-reference
  at the top of §"Testing approach" coverage paragraph
  pointing readers at §"Test-Driven Development discipline"
  as the methodology framing.
- v030 D5 (companion-doc, style doc): paired §"Test-Driven
  Development discipline" section authored as a sibling to
  §"Code coverage", carrying operational specifics (running
  Red tests in isolation, useful-vs-unhelpful Red examples,
  refactor-cycle operational shape, exception-clause
  examples). Style-doc edit per the established
  style-doc-drift convention.
- v030 D6 (plan-level): Plan Phase 0 step 1 byte-identity
  reference bumps to `history/v030/PROPOSAL.md`. Plan Phase
  0 step 2 frozen-status header literal bumps to "Frozen at
  v030". Plan Execution-prompt block authoritative-version
  line bumps to v030. Plan Phase 5 §"`just bootstrap`
  promotion" sub-step gains a one-sentence note that this
  is the activation point of the hard-constraint per-commit
  gate per PROPOSAL.md §"Testing approach — Activation".
- Triggered by user direction during Phase 5 sub-step 3
  (test-authoring campaign) — explicit ask to codify the
  TDD discipline + tighten the coverage gate as a hard
  constraint. Routed via the bootstrap skill's Case-A
  PROPOSAL extension flow (halt-and-revise; same mechanism
  as drift-driven snapshots).
- v031 D1 (PROPOSAL.md): extends §"Testing approach" lines
  3372-3375 from a 3-pattern enumeration of structural
  coverage exclusions (`if TYPE_CHECKING:`,
  `raise NotImplementedError`, `@overload`) to 4 patterns by
  adding `case _:`. The fourth pattern reflects the
  universal `case _: assert_never(<subject>)` mandate at
  companion style-doc lines 1054-1066 plus the AST-level
  enforcement at
  `dev-tooling/checks/assert_never_exhaustiveness.py`: every
  `case _:` arm in the codebase is the structurally-
  unreachable assert-never sentinel. Coverage.py's
  compound-statement exclusion rule excludes the arm body
  (`assert_never(<subject>)`) in the same sweep as the
  `case _:` line, removing the need for contrived
  per-test triggers across ~15-20 future match-statement-
  bearing modules in Phase 5 sub-step 3 onward.
- v031 D2 (plan-level): Plan Phase 0 step 1 byte-identity
  reference bumps to `history/v031/PROPOSAL.md`. Plan Phase
  0 step 2 frozen-status header literal bumps to "Frozen at
  v031". Plan Execution-prompt block authoritative-version
  line bumps to v031. No Phase-N body edits required: v031
  substance is contained in PROPOSAL.md §"Testing approach";
  phase work references the rule by pointer rather than
  enumerating patterns.
- Companion-doc + pyproject edits already shipped at commit
  `abd0cdd` via the v028-D1-style overlay precedent (style
  doc + pyproject lead implementation; PROPOSAL revision
  follows). The v031 revision file documents the
  PROPOSAL-side reconciliation; the originating
  open-issues entry (2026-04-29T02:44:18Z) gets
  `Status: resolved` upon v031 commit landing.
- Triggered by Phase 5 sub-step 3 test-authoring work for
  `livespec/parse/jsonc.py`: the `case _: assert_never(
  raw_result)` arm forced a per-test contrived monkeypatch
  trigger to satisfy 100% line+branch coverage; user gate
  authorized the structural-exclusion path for the remaining
  match-statement-bearing modules. Routed via the bootstrap
  skill's Case-A PROPOSAL-drift rule (auto-blocking;
  halt-and-revise required because PROPOSAL.md lines 3372-
  3375 enumerated only 3 patterns).
- v032 D1 (PROPOSAL.md): rewrites §"Test-Driven Development
  discipline" opening paragraph (lines 3103-3110) to strike
  the "non-negotiable from Phase 5 exit onward" temporal
  carve-out and clarify that the discipline applies from the
  first Python module onward; what activates at Phase 5 exit
  is the mechanical enforcement gate (lefthook + 100%
  coverage), NOT the discipline itself. References Plan Phase
  5 §"Retroactive TDD redo of Phase 3 + Phase 4 work" as the
  one-time mechanism that brings the pre-v032 codebase under
  the discipline.
- v032 D2 (plan-level): Plan Phase 3 and Phase 4 each gain a
  one-paragraph **Authoring discipline** preamble mandating
  Red→Green-per-behavior. Plan Phase 5 gains a new
  §"Retroactive TDD redo of Phase 3 + Phase 4 work"
  sub-section laying out the stash → walk-modules-in-
  dependency-order → exit-condition procedure. Stash
  mechanism: `bootstrap/scratch/pre-redo.zip` is a committed
  binary blob (under SCM, not source-readable; only
  legitimate `unzip` is at v032 D3 measurement time).
- v032 D3 (plan-level): Plan Phase 5 gains §"Quality-
  comparison report" sub-section requiring an explicit
  before/after report on architecture, coupling, cohesion,
  and unnecessary-code elimination, with at least one
  quantitative metric per dimension and a behavioral-
  equivalence audit. Report is gated by AskUserQuestion
  before Phase 5 advance.
- v032 D4 (plan-level + new dev-tooling check): Plan Phase 5
  gains §"Per-commit Red-output discipline" sub-section
  mandating a `## Red output` fenced block in every
  feature/bugfix commit body. New `red_output_in_commit.py`
  check enumerated in Phase 4's check list; activates as a
  hard `just check` gate at Phase 5 exit.
- v032 D5 (plan-level): Plan Phase 0 step 1 byte-identity
  reference bumps to `history/v032/PROPOSAL.md`. Plan Phase
  0 step 2 frozen-status header literal bumps to "Frozen at
  v032". Plan Execution-prompt block authoritative-version
  line bumps to v032.
- Triggered by user-flagged design concern: characterization-
  style backfill at Phase 5 sub-step 3 produces covered code,
  not designed code; the load-bearing TDD benefits (loose
  coupling, high cohesion, unnecessary-code elimination,
  good architecture) require Red→Green-per-behavior
  authoring, not impl-first-with-tests-after.

Execution is performed by the prompt at the end of this file. The
prompt is self-contained; it can be pasted into a fresh Claude Code
session in the `livespec` repo.

---

## 1. Inputs (authoritative sources)

The plan operates on these files. They are the single source of
truth for every decision encoded below; the plan itself does not
restate their content.

Working proposal + embedded grounding:

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md` (frozen at
  the latest post-interview version; see "Version basis" above)
- `brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md`
- `prior-art/nlspec-spec.md`

Companion documents (all under
`brainstorming/approach-2-nlspec-based/`):

- `python-skill-script-style-requirements.md`
- `deferred-items.md`
- `goals-and-non-goals.md`
- `subdomains-and-unsolved-routing.md`
- `prior-art.md`
- `2026-04-19-nlspec-lifecycle-diagram.md`
- `2026-04-19-nlspec-lifecycle-diagram-detailed.md`
- `2026-04-19-nlspec-lifecycle-legend.md`
- `2026-04-19-nlspec-terminology-and-structure-summary.md`

History:

- `brainstorming/approach-2-nlspec-based/history/README.md`
- `brainstorming/approach-2-nlspec-based/history/v001/` through
  the latest `history/vNNN/` directory (every `PROPOSAL.md`,
  `proposed_changes/`, `conversation.json`,
  `retired-documents/`)

Anything NOT in the list above MUST NOT influence the plan's
output. Files under `history/vNNN/retired-documents/` are
reference-only.

---

## 2. Preconditions

- Repo root is `/data/projects/livespec/` with `master` branch
  clean.
- No `.mise.toml`, `.python-version`, `uv.lock`, `justfile`,
  `lefthook.yml`, `pyproject.toml`, `dev-tooling/`, `tests/`,
  `SPECIFICATION/`, `SPECIFICATION.md`, `NOTICES.md`, or
  `.vendor.jsonc` exist yet at repo root. (`.python-version` and
  `uv.lock` are added per v024.)
- `.claude-plugin/` MAY exist at repo root, BUT only with
  `marketplace.json` (the bootstrap-marketplace manifest declaring
  the `livespec-bootstrap` plugin's location). Phase 2 adds
  `plugin.json` to the same `.claude-plugin/` directory for the
  production livespec plugin; `marketplace.json` and `plugin.json`
  coexist there until Phase 11 removes `marketplace.json`.
- `.claude/` MAY exist at repo root, BUT only with the bootstrap-
  scaffolding contents (`.claude/plugins/livespec-bootstrap/`
  containing the plugin manifest at
  `.claude/plugins/livespec-bootstrap/.claude-plugin/plugin.json`
  and the skill at `.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md`).
  The `.claude/settings.local.json` file (machine-local
  permissions) is gitignored. Phase 2 creates `.claude/skills/`
  as a directory-level symlink to `../.claude-plugin/skills/`;
  that symlink coexists with the pre-existing
  `.claude/plugins/livespec-bootstrap/` directory. Phase 11
  removes `.claude/plugins/livespec-bootstrap/` (and
  `.claude/plugins/` if empty) at cleanup.
- `bootstrap/` MAY exist at repo root as the execution-scaffolding
  directory described in §8 below. After this layout fix it
  contains only the state files (`STATUS.md`, `open-issues.md`,
  `decisions.md`, `AGENTS.md`) — the plugin contents now live
  under `.claude/plugins/livespec-bootstrap/`. The bootstrap-
  authoring commit creates it; the directory itself stays in
  place after Phase 11 (only the plugin location and the
  repo-root `AGENTS.md` are removed at Phase 11 cleanup).
- `AGENTS.md` MAY exist at repo root as the orientation file for
  fresh AI sessions during bootstrap (per §8 below). Removed by
  Phase 11. Per-directory `AGENTS.md` files inside `bootstrap/`
  and `brainstorming/` stay in place after Phase 11 since those
  directories themselves stay.
- `brainstorming/` and `prior-art/` persist AS-IS — they are
  historical reference material and are not rewritten or moved by
  this plan.
- The brainstorming interview passes producing v018, v019,
  v020, and v021 HAVE RUN and been frozen. The v018 revision
  file (at
  `brainstorming/approach-2-nlspec-based/history/v018/proposed_changes/proposal-critique-v17-revision.md`)
  records six accepted decisions (Q1-Q6 all accepted at
  option A): Q1-Option-A (template sub-specifications under
  `SPECIFICATION/templates/<name>/`), Q2 (bootstrap-exception
  clause), Q3 (initial-vendoring procedure), Q4 (returns
  pyright plugin vendored + pyright stays), Q5 (prompt-QA
  tier at `tests/prompts/`), Q6 (companion-documents
  migration-class policy + assignment table). The v019 revision
  file (at
  `brainstorming/approach-2-nlspec-based/history/v019/proposed_changes/proposal-critique-v18-revision.md`)
  records one accepted decision (v019 Q1, accepted at Option A):
  §"Self-application" step 2 widened to include minimum-viable
  `propose-change`/`critique`/`revise` alongside seed; step 4
  re-narrated as pure widening + remaining-sub-command
  implementation via dogfood; Q2 boundary unmoved. The v020
  revision file (at
  `brainstorming/approach-2-nlspec-based/history/v020/proposed_changes/proposal-critique-v19-revision.md`)
  records four accepted decisions (Q1-Q4 all accepted at
  Option A): Q1 (sub-specs reframed as livespec-internal,
  uniformly multi-file with sub-spec-root + per-version
  README; `minimal` sub-spec structural contradiction
  resolved), Q2 (sub-spec emission becomes user-driven via
  pre-seed dialogue question; shipped seed prompt no longer
  hard-codes per-template emission), Q3 (Phase 3 exit
  criterion grows by sub-spec-targeted propose-change/revise
  smoke cycle), Q4 (Phase 3 widens all four livespec-template
  prompts to bootstrap-minimum). The v021 revision file (at
  `brainstorming/approach-2-nlspec-based/history/v021/proposed_changes/proposal-critique-v20-revision.md`)
  records three accepted decisions (Q1-Q3 all accepted at
  Option A): Q1 (orchestrator-only doctor static-check
  applicability dispatch; `DoctorContext.template_scope`
  replaced by `template_name`; per-check `APPLIES_TO`
  constants and `gherkin_blank_line_format` runtime-skip
  removed; PROPOSAL.md §"doctor → Static-phase orchestrator"
  amended), Q2 (Phase 3 `seed/SKILL.md` bullet enumerates
  the v020 Q2 three-question pre-seed dialogue explicitly),
  Q3 (Phase 6 names an explicit imperative one-time
  `tests/heading-coverage.json` population sub-step under
  the v018 Q2 / v019 Q1 bootstrap-exception clause). The
  resulting frozen `PROPOSAL.md` v021, plus touched
  companion docs (`deferred-items.md`;
  `python-skill-script-style-requirements.md` — both unchanged
  by v019, v020, and v021), is the authority for Phases
  0-10 below.
- PROPOSAL.md is treated as frozen from Phase 0 onward. No
  further brainstorming revisions are produced; all subsequent
  refinement happens inside the seeded `SPECIFICATION/` via
  `propose-change` / `revise`.

---

## 3. Cutover principle

Brainstorming artifacts → immutable. The first real
`SPECIFICATION/` tree is produced by `livespec seed` run against
this repo; from that moment on, every change flows through the
governed loop (propose-change → critique → revise). The
brainstorming folder becomes archival.

The skill implementation is bootstrapped by hand only to the
minimum shape required to (a) run `seed` against this repo
AND (b) file the first dogfooded propose-change → revise cycle
against the seeded SPECIFICATION/. The remaining scope lands
through `propose-change` / `revise` cycles authored by the skill
itself (dogfooding, per PROPOSAL.md §"Self-application").
**PROPOSAL.md v018 Q2 (clarified by v019 Q1) codifies the
bootstrap exception**: the bootstrap ordering in §"Self-
application" steps 1-3 (this plan's Phases 0-5, up through
the first seed in Phase 6) lands imperatively; the governed
loop becomes MANDATORY from Phase 6 onward. **v019 Q1 widens
step 2 to include minimum-viable `propose-change`, `critique`,
and `revise` implementations BEFORE the seed**, so they exist
at the moment Phase 6 completes — the imperative window's
closing point at first seed is unmoved. Hand-editing any file
under any spec tree or under
`.claude-plugin/specification-templates/<name>/` after Phase 6
is a bug in execution per that clause; Phase 7 widens the
minimum-viable sub-commands to full feature parity exclusively
through dogfooded cycles.

**Carve-out for template-bundled prompt-reference materials.**
The hand-edit ban under
`.claude-plugin/specification-templates/<name>/` is bounded to
the three governed file classes: `template.json`, anything
under `prompts/`, and anything under `specification-template/`.
Template-bundled prompt-reference materials shipped at template
root (the file class introduced in PROPOSAL.md §"Built-in
template: `livespec`"; v1 instance is the `livespec` template's
`livespec-nlspec-spec.md`) are EXEMPT from the ban. Such files
are not sub-spec-governed and are not agent-regenerated in
Phase 7; they evolve post-bootstrap via direct edit of the
bundled file under ordinary PR review. The carve-out applies
uniformly to custom templates that ship their own prompt-
reference materials at template root (see PROPOSAL.md §"Template
resolution contract — Deferred future feature").

The SPECIFICATION tree is NOT flat: it contains the main spec
files AND a nested sub-spec per built-in template under
`SPECIFICATION/templates/<name>/` (per v018 Q1-Option-A). Each
sub-spec is a first-class livespec-managed spec tree with its
own `proposed_changes/` and `history/`. `seed` produces main +
two template sub-specs atomically; later `propose-change` /
`revise` invocations target a specific spec tree via
`--spec-target <path>`. The agentic generation of each built-in
template's shipped content (its `template.json`,
`prompts/*.md`, and `specification-template/`) flows from
that template's sub-spec.

---

## 4. Phases

Each phase has a clear exit criterion. Phases are sequential;
sub-steps within a phase MAY run in parallel where noted.

### Phase 0 — Freeze the brainstorming folder

1. Confirm `brainstorming/approach-2-nlspec-based/PROPOSAL.md` is
   byte-identical to `history/v032/PROPOSAL.md` (the v032
   snapshot — v031 substance plus the §"Test-Driven Development
   discipline" opening-paragraph rewrite at lines 3103-3110
   striking the "Phase 5 exit onward" temporal carve-out per
   `history/v032/proposed_changes/critique-fix-v031-revision.md`;
   v031 substance is v030 substance plus the `case _:` 4th
   structural-coverage-exclusion pattern at §"Testing approach"
   lines 3372-3375 per
   `history/v031/proposed_changes/critique-fix-v030-revision.md`;
   v030 substance is v029 substance plus the §"Test-Driven Development
   discipline" section, the `# pragma: no cover` escape-hatch
   removal, the §"Testing approach — Activation" clause, and
   the cross-reference at the top of the coverage paragraph,
   per `history/v030/proposed_changes/critique-fix-v029-revision.md`;
   v029 substance is v028 substance plus the
   `dev-tooling/checks/` directory-listing realignment + the
   `keyword_only_args.py` triple-annotation fix per
   `history/v029/proposed_changes/critique-fix-v028-revision.md`;
   v028 substance is v027 substance with the bundle-root
   formula correction at PROPOSAL §"Template resolution
   contract" line 1466 (`Path(__file__).resolve().parent.parent`
   → `Path(__file__).resolve().parents[3]`) per
   `history/v028/proposed_changes/critique-fix-v027-revision.md`;
   v027 substance is v026
   substance with
   `typing_extensions` reclassified from hand-authored shim to
   upstream-sourced lib per
   `history/v027/proposed_changes/critique-fix-v026-revision.md`;
   v026 substance is v025 substance with
   `jsoncomment` reclassified from upstream-sourced lib to
   hand-authored shim per
   `history/v026/proposed_changes/critique-fix-v025-revision.md`;
   v025 substance is v024 substance with the
   `returns_pyright_plugin` vendoring removed and the `returns`
   license corrected to BSD-3-Clause per
   `history/v025/proposed_changes/critique-fix-v024-revision.md`;
   v024 substance is v023 substance plus
   v024's UV-toolchain decision per
   `history/v024/proposed_changes/critique-fix-v023-revision.md`;
   v023 substance is v022 substance plus the `tmp/bootstrap/`
   ownership convention; v022's substance carries v018
   Q1-Option-A through Q6, v019 Q1, v020 Q1-Q4, v021 Q1-Q3,
   plus v022's prompt-reference-metadata file class and four
   plan-level corrections per the Preconditions section).
   v028's snapshot was created during a halt-and-revise in
   Phase 3 sub-step 12 of the in-flight bootstrap; see
   `history/v030/proposed_changes/critique-fix-v029-revision.md`
   for the v030 decision provenance,
   `history/v029/proposed_changes/critique-fix-v028-revision.md`
   for the v029 decision provenance,
   `history/v028/proposed_changes/critique-fix-v027-revision.md`
   for the v028 decision provenance,
   `history/v027/proposed_changes/critique-fix-v026-revision.md`
   for v027's,
   `history/v026/proposed_changes/critique-fix-v025-revision.md`
   for v026's,
   `history/v025/proposed_changes/critique-fix-v024-revision.md`
   for v025's,
   `history/v024/proposed_changes/critique-fix-v023-revision.md`
   for v024's,
   `history/v023/proposed_changes/critique-fix-v022-revision.md`
   for v023's, and
   `history/v022/proposed_changes/critique-fix-v021-revision.md`
   for v022's underlying substance.
2. Add a top-of-file note to
   `brainstorming/approach-2-nlspec-based/PROPOSAL.md`:
   > **Status:** Frozen at v032. Further evolution happens in
   > `SPECIFICATION/` via `propose-change` / `revise`. This file
   > and the rest of the `brainstorming/` tree are historical
   > reference only.
3. `tmp/` is left untouched. The repo-root `tmp/` is git-untracked
   user-owned scratch space; the bootstrap MUST NOT delete or
   modify it. Any bootstrap-owned scratch needs go under
   `tmp/bootstrap/` (creatable on demand, freely deletable by the
   bootstrap).
4. Nothing else in `brainstorming/` is modified.
5. Confirm the bootstrap scaffolding exists per §8 below:
   `bootstrap/STATUS.md`, `bootstrap/open-issues.md`,
   `bootstrap/decisions.md`, `bootstrap/AGENTS.md`,
   `.claude-plugin/marketplace.json`, and
   `.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md`.
   If any are missing, the bootstrap-authoring commit was skipped —
   halt and request the scaffolding be created before continuing.

**Exit criterion:** PROPOSAL.md carries the frozen-status
header in its committed state; the latest history/vNNN snapshot
is byte-identical to live PROPOSAL.md; the plan's active
version pointers reference the latest snapshot. Originally
planned as a single `freeze: v022 brainstorming` commit; v023's
halt-and-revise broadened this to "the v023 revision commit"
(which lands the frozen-status header on PROPOSAL.md alongside
the v023 history snapshot, revision file, and paired plan-text
edits). v024's halt-and-revise during Phase 1 sub-step 1 added
the UV-toolchain decision; future halt-and-revises during
execution may produce additional snapshots v025+ via the same
mechanism.

### Phase 1 — Repo-root developer tooling

Create at repo root (outside the plugin bundle), exactly as
specified in PROPOSAL.md §"Developer tooling layout" and the
style doc §"Dev tooling and task runner":

- `.mise.toml` pinning `uv`, `just`, `lefthook` to exact
  versions — non-Python binaries only, per v024. Python and
  every Python dev dependency are managed by `uv` via
  `pyproject.toml` (see next bullet). (`typing_extensions` is
  vendored per v013 M1, NOT mise-pinned and NOT uv-managed.)
- `.python-version` recording the exact Python 3.10.x patch,
  managed by `uv python pin` per v024. `pyproject.toml`'s
  `[project.requires-python]` declares the same constraint.
- `pyproject.toml` containing:
  - `[tool.ruff]` per style doc §"Linter and formatter"
    (27 categories; pylint thresholds; TID banned imports).
  - `[tool.pyright]` strict + the seven strict-plus diagnostics
    (`reportUnusedCallResult`, `reportImplicitOverride`,
    `reportUninitializedInstanceVariable`,
    `reportUnnecessaryTypeIgnoreComment`,
    `reportUnnecessaryCast`, `reportUnnecessaryIsInstance`,
    `reportImplicitStringConcatenation`). NO `pluginPaths`
    entry: per v025, pyright has no plugin system and no
    upstream `returns_pyright_plugin` exists (the v018 Q4
    closure of `returns-pyright-plugin-disposition` was
    re-opened and re-closed in v025 — see
    `history/v025/proposed_changes/critique-fix-v024-revision.md`
    decision D1). The `basedpyright-vs-pyright` deferred item
    remains CLOSED in v018 Q4 with the original decision:
    **pyright is the chosen typechecker, NOT basedpyright**
    (PROPOSAL.md §"Runtime dependencies — Developer-time
    dependencies → Typechecker decision (v018 Q4)").
    Rationale is captured in a leading `#` comment block in
    `pyproject.toml` cross-referencing those PROPOSAL.md
    sections plus the v025 plugin-removal context. Phase 6
    migrates the rationale into
    `SPECIFICATION/constraints.md`; Phase 8 item 9
    (basedpyright-vs-pyright) becomes a bookkeeping close
    pointing at the Phase-1 commit; Phase 8 item 8
    (returns-pyright-plugin-disposition) is similarly closed
    pointing at the v025 revision.
  - `[tool.pytest.ini_options]` wiring `pytest-cov` +
    `pytest-icdiff`.
  - `[tool.coverage.run]` / `[tool.coverage.report]` with
    100% line+branch, `source = [".claude-plugin/scripts/livespec",
    ".claude-plugin/scripts/bin", "dev-tooling"]` (repo-root-relative
    paths; `dev-tooling/` is included so Phase-4 enforcement
    scripts are gated by the same 100% line+branch standard as
    the shipped bundle), `fail_under = 100`.
  - `[tool.importlinter]` with the two authoritative contracts
    (`parse-and-validate-are-pure`, `layered-architecture`) per
    v013 M7 as narrowed by v017 Q3.
  - `[tool.mutmut]` for mutmut runtime config ONLY; NO
    `threshold` key. The ratchet-with-ceiling semantics
    (floor = current baseline, capped at 80%) live entirely
    in the `just check-mutation` recipe: it reads
    `.mutmut-baseline.json`, computes
    `min(baseline_kill_rate, 80)`, and fails if the run's
    kill-rate is below that. A static `threshold = 80` in
    pyproject would misstate the spec (DoD 10).
  - NO build-system section (livespec is not a published PyPI
    package; it ships via Claude Code plugin bundling).
  - `[project]` table per v024 with `name = "livespec"`,
    `version = "0.0.0"` (placeholder; livespec is not
    published), and `requires-python = ">=3.10,<3.11"`. NO
    `[project.dependencies]` (livespec ships nothing as a
    runtime dep — the bundle's `_vendor/` is the runtime).
  - `[dependency-groups]` per v024 with a `dev` group listing
    `ruff`, `pyright`, `pytest`, `pytest-cov`, `pytest-icdiff`,
    `hypothesis`, `hypothesis-jsonschema`, `mutmut`,
    `import-linter` to exact versions. UV resolves and installs
    these into a project-local `.venv` via `uv sync
    --all-groups`, producing a committed `uv.lock`.
- `justfile` with the canonical target list from the style doc
  §"Enforcement suite — Canonical target list". All recipes
  delegate to their underlying tool or to
  `python3 dev-tooling/checks/<name>.py`. Includes
  `just bootstrap`, `just check`, every `just check-*`,
  `just e2e-test-claude-code-mock`,
  `just e2e-test-claude-code-real`,
  `just check-prompts` (v018 Q5; recipe body
  `pytest tests/prompts/`),
  `just check-mutation`,
  `just check-no-todo-registry`, `just fmt`, `just lint-fix`,
  `just vendor-update <lib>`, `just check-heading-coverage`,
  `just check-vendor-manifest`. At this phase, `just bootstrap`
  contains ONLY a placeholder echo line ("bootstrap: nothing to
  do until Phase 5"); the `lefthook install` step is added at
  Phase 5's exit (when full `just check` first passes), and the
  `.claude/skills → ../.claude-plugin/skills` symlink-recreation
  step is added by Phase 2 (after the target directory exists).
  **Lefthook install is deliberately deferred from Phase 1 to
  Phase 5** so that pre-commit `just check` invocations during
  Phases 2-4 do not block commits on targets whose backing
  content (tests, dev-tooling scripts) does not yet exist.
- `lefthook.yml` with pre-commit and pre-push hooks; every
  `run:` is `just check`. (Hook config lands in Phase 1 as part
  of the repo-tooling layout; lefthook's actual installation
  into `.git/hooks/` is deferred to Phase 5 per the
  `just bootstrap` note above.)
- `.github/workflows/ci.yml` — per-target matrix with
  `fail-fast: false` invoking `just <target>`; installs pinned
  tools via `jdx/mise-action@v2`.
- `.github/workflows/release-tag.yml` — runs
  `just check-mutation` and `just check-no-todo-registry` on
  tag push.
- `.github/workflows/e2e-real.yml` — invokes
  `just e2e-test-claude-code-real` on `merge_group`, `push` to
  `master`, and `workflow_dispatch`; gated on
  `ANTHROPIC_API_KEY`.
- `.vendor.jsonc` — JSONC with an entry per vendored library
  (`returns`, `fastjsonschema`, `structlog`, `jsoncomment`,
  `typing_extensions` — five entries total per v025 D4; the
  v018 Q4 sixth entry `returns_pyright_plugin` was dropped
  in v025). Per v027 D2, the breakdown is 4 upstream-sourced
  (`returns`, `fastjsonschema`, `structlog`,
  `typing_extensions`) + 1 shim (`jsoncomment` per v026 D1
  + v027 D1 reclassification of typing_extensions to
  upstream-sourced). Each entry records `upstream_url`,
  `upstream_ref`, `vendored_at`; only `jsoncomment` records
  `shim: true`. For the `jsoncomment` shim, `upstream_ref` is
  the upstream release whose comment-stripping semantics the
  shim faithfully replicates (`"0.4.2"`), giving reviewers a
  concrete comparison target; `upstream_url` is the canonical
  surviving source-of-record on PyPI
  (`https://pypi.org/project/jsoncomment/`) since the bitbucket
  homepage URL is dead. Widening the jsoncomment shim later
  updates `upstream_ref` to the then-matching upstream
  version. Phase 1 authors all five entries with placeholder
  `upstream_ref` and `vendored_at` values for the 4 upstream-
  sourced libs (the 1 shim has its real `upstream_ref` value
  from authoring time, since shims do not depend on the v018
  Q3 git-clone-and-copy step); Phase 2's initial-vendoring
  procedure (per v018 Q3) populates the real values for the 4
  upstream-sourced libs during the manual git-clone-and-copy
  step.
- `.mutmut-baseline.json` — placeholder recording
  `baseline_reason: "pre-implementation placeholder; real
  baseline captured on first release-tag run"`, `kill_rate_percent: 0`,
  `mutants_surviving: 0`, `mutants_total: 0`,
  `measured_at: "<UTC>"`. Replaced on first release-tag run.
- `NOTICES.md` listing every vendored library with its
  upstream project, license name, and a verbatim license
  reference.
- `.gitignore` amendments (ignore `__pycache__/`, `.pytest_cache/`,
  `.coverage`, `.ruff_cache/`, `.pyright/`, `.mutmut-cache/`,
  `htmlcov/`, `.venv/` per v024 — uv sync produces a project-
  local `.venv` that must not be committed). `.mypy_cache/` is
  intentionally NOT listed: mypy compatibility is a style-doc
  non-goal, so its cache path is not a tolerated artifact.

**Exit criterion:** `mise install` succeeds; `uv sync
--all-groups` succeeds and produces a project-local `.venv` with
the dev-dep set plus a committed `uv.lock` (per v024);
`just bootstrap` (placeholder no-op at this stage per the
deferral above) succeeds; `just --list` shows every target from
the canonical table. Lefthook is NOT yet installed into
`.git/hooks/`; that lands in Phase 5.

### Phase 2 — Plugin bundle skeleton

Create the plugin bundle under `.claude-plugin/` exactly matching
PROPOSAL.md §"Skill layout inside the plugin":

- `.claude-plugin/plugin.json` populated per the current Claude
  Code plugin format.
- `.claude/skills/` → relative symlink to `../.claude-plugin/skills/`;
  committed as a tracked symlink.
- `.claude-plugin/skills/<sub-command>/SKILL.md` for each of:
  `help`, `seed`, `propose-change`, `critique`, `revise`,
  `doctor`, `prune-history`. At this stage each SKILL.md carries
  the required frontmatter (`name`, `description`,
  `allowed-tools`, plus `disable-model-invocation: true` on
  `prune-history`) and a placeholder body marked "authoring
  deferred to `skill-md-prose-authoring`".
- `.claude-plugin/scripts/bin/` — shebang wrappers per
  §"Shebang-wrapper contract":
  - `_bootstrap.py` — full body per the style doc's
    `bin/_bootstrap.py` contract.
  - `seed.py`, `propose_change.py`, `critique.py`, `revise.py`,
    `doctor_static.py`, `resolve_template.py`,
    `prune_history.py` — each is the exact 6-statement form
    (`check-wrapper-shape` passes).
  - `chmod +x` applied to every wrapper.
- `.claude-plugin/scripts/_vendor/<lib>/` — vendored pure-Python
  libraries, each with its `LICENSE` (verbatim upstream copy
  for upstream-sourced libs; derivative-work attribution for
  the `jsoncomment` shim), at the exact upstream ref recorded
  in `.vendor.jsonc`. **Per v018 Q3, the initial population
  of each upstream-sourced lib follows the one-time manual
  procedure documented in PROPOSAL.md §"Vendoring discipline
  — Initial-vendoring exception"** (git clone + checkout +
  cp + LICENSE capture + record in `.vendor.jsonc` +
  smoke-test import); after the `jsoncomment` shim is hand-
  authored at this phase, subsequent re-vendoring of any
  upstream-sourced lib flows through `just vendor-update
  <lib>`. Per v027 D4, the upstream-sourced sub-list is 4
  libs and the shim sub-list is 1 lib.
  - Upstream-sourced (v018 Q3 git-based procedure applies):
    - `returns/` (dry-python/returns, BSD-3-Clause; license
      corrected from BSD-2 in v025 D2)
    - `fastjsonschema/` (MIT)
    - `structlog/` (BSD-2 / MIT dual)
    - `typing_extensions/` (PSF-2.0) — full upstream
      vendored at tag `4.12.2` per v027 D1 (was the v013 M1
      hand-authored shim pre-v027). Provides the variadic-
      generics + Self + Never + TypedDict + ParamSpec +
      TypeVarTuple + Unpack symbols that the vendored returns
      + structlog + fastjsonschema sources transitively
      require, plus livespec's own `override` + `assert_never`
      canonical-import-path needs.
  - Shim (livespec-authored by hand; v018 Q3 procedure does
    NOT apply):
    - `jsoncomment/` — the JSONC parser shim per v026 D1,
      faithfully replicating jsoncomment 0.4.2's `//` line-
      comment and `/* */` block-comment stripping semantics
      (multi-line strings + trailing-commas optional, only
      if `livespec/parse/jsonc.py` requires them). Module-
      named `jsoncomment` so existing `import jsoncomment`
      statements work unchanged. The shim's `LICENSE` carries
      verbatim MIT attribution to Gaspare Iengo (citing
      jsoncomment 0.4.2's `COPYING` file as the derivative-
      work source); livespec's shim is a derivative work
      under MIT.
- `.claude-plugin/scripts/livespec/` — Python package with the
  subdirectories enumerated in the PROPOSAL tree
  (§"Skill layout"): `commands/`, `doctor/` (with
  `run_static.py` + `static/__init__.py` registry +
  per-check modules), `io/`, `parse/`, `validate/`,
  `schemas/` (plus `schemas/dataclasses/`), `context.py`,
  `types.py`, `errors.py`, `__init__.py`. **`errors.py` is
  authored fully at Phase 2, NOT stubbed** — it carries the
  full `LivespecError` hierarchy + `HelpRequested` per the
  style doc §"Exit code contract". Justification: Phase 2's
  stub contract requires `IOFailure(<DomainError>(...))` /
  `Failure(<DomainError>(...))` return statements that
  reference `LivespecError` subclasses defined in
  `errors.py`. Phase 2 must therefore land `errors.py` in
  full so the stubs can reference real domain-error classes.
  `livespec/__init__.py` (structlog configuration + `run_id`
  bind) is also full at Phase 2.
- `.claude-plugin/specification-templates/livespec/` and
  `.claude-plugin/specification-templates/minimal/` — both
  built-in templates, at **bootstrap-minimum scaffolding
  only** (per v018 Q1-Option-A). Each has:
  - `template.json` with required fields
    (`template_format_version: 1`, `spec_root`, optional
    doctor-hook paths populated per PROPOSAL.md's template
    schema).
  - `prompts/{seed,propose-change,revise,critique}.md` each
    authored at a minimum-viable level — just enough for the
    Phase 3 / Phase 6 bootstrap seed to succeed against this
    repo. Per v020 Q2, the `livespec` template's
    `prompts/seed.md` minimum-viable scaffold MUST include the
    new pre-seed dialogue question ("Does this project ship
    its own livespec templates...?") and a stub branch for
    each answer ("yes" → enumerate templates and emit
    sub_specs[]; "no" → emit `sub_specs: []`); rigorous
    handling of the dialogue branches is the Phase 3 widening
    target. Their full authoring lands in Phase 7 as agent-
    generated output against each template's sub-spec (which
    itself is seeded in Phase 6).
  - `specification-template/…` as an empty skeleton
    (directory tree only, no starter content files). Starter
    content is generated agentically in Phase 7 from the
    template's sub-spec.
  The `livespec` template also ships `livespec-nlspec-spec.md`
  at its root (copied verbatim from
  `brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md`)
  and carries a stub `prompts/doctor-llm-subjective-checks.md`.
  The `minimal` template's stub prompts carry placeholder
  delimiter-comment markers; the final delimiter-comment
  format and its codification in the `minimal` template
  sub-spec (`SPECIFICATION/templates/minimal/contracts.md`)
  are Phase 7 work.

All code in this phase is stub-level EXCEPT the wrapper shapes,
`_bootstrap.py`, `livespec/__init__.py` (structlog
configuration + `run_id` bind), and `livespec/errors.py` (full
`LivespecError` hierarchy + `HelpRequested` — required by the
stub contract below so stub bodies can reference real
domain-error classes).

**Stub contract (authoritative for Phases 2–3 stubs).** Every
stubbed module under `.claude-plugin/scripts/livespec/**`
satisfies the following from the moment it lands:

- A module-top `__all__: list[str]` is declared and enumerates
  every public name the module exposes (required by
  `check-all-declared`).
- Every public function carries complete type annotations
  including the `Result[...]` or `IOResult[...]` return type
  (required by `check-public-api-result-typed`).
- Every stubbed function body is exactly one statement returning
  a single, stable value:
  - `IOResult`-returning functions: `return
    IOFailure(<DomainError>("<module>: not yet implemented"))`
    where `<DomainError>` is a `LivespecError` subclass already
    defined in `livespec/errors.py`.
  - Pure `Result`-returning functions: `return
    Failure(<DomainError>("<module>: not yet implemented"))`.
- Phase 5 tests assert that single return path; one test per
  stubbed public function is sufficient for 100% line+branch
  coverage of the stub.

Also, Phase 2 amends `just bootstrap` authored in Phase 1 to
append the defensive symlink step:
`ln -sfn ../.claude-plugin/skills .claude/skills` — safe to run
now that `.claude-plugin/skills/` exists. (`lefthook install`
is NOT yet part of `just bootstrap` — that step lands at Phase
5; see Phase 1's `just bootstrap` note.)

Phase 2 ALSO replaces the placeholder `upstream_ref` and
`vendored_at` fields in `.vendor.jsonc` (authored in Phase 1)
with real values for all five vendored entries. The
initial-vendoring procedure (per v018 Q3) populates these
during the manual git-clone-and-copy step. Phase 2's exit
explicitly asserts that no `.vendor.jsonc` entry retains a
placeholder string (substring search; no
`"upstream_ref": "TBD"`, no `"vendored_at": ""`, no entries
missing either field).

Every directory under `.claude-plugin/scripts/` (excluding the
entire `_vendor/` subtree) MUST carry a `CLAUDE.md` describing
its local constraints.

**Exit criterion:** `ruff check` passes on the skeleton.
`check-wrapper-shape`, `check-main-guard`, and
`check-claude-md-coverage` are deferred to Phase 5's exit per Phase
3's deferral list ("every target backed by a Phase-4
`dev-tooling/checks/*.py` script"); their backing scripts are
authored at Phase 4. `pyright` may still report errors against the
stub bodies (acceptable at this phase; `check-types` is a Phase-7
gate, once `livespec/**` stubs widen toward their full
implementations). **Plugin-loading smoke check**: `readlink .claude/skills`
resolves to `../.claude-plugin/skills`; `ls .claude/skills/`
enumerates exactly the seven sub-command directories (`help`,
`seed`, `propose-change`, `critique`, `revise`, `doctor`,
`prune-history`); and a fresh `claude` session rooted at the repo
lists seven `/livespec:*` slash commands in its autocomplete menu.
**Manual file-existence verification**: every directory under
`.claude-plugin/scripts/` (excluding `_vendor/`) carries a
`CLAUDE.md`; `.vendor.jsonc` retains no placeholder strings; every
module in `livespec/**` has a top-level `__all__: list[str]`. These
manual checks are mechanically enforced once Phase 4's scripts land
and Phase 5 wires them into `just check`.

### Phase 3 — Minimum viable `livespec seed` + minimum-viable propose-change/critique/revise

Flesh out exactly the code paths required to (a) run `livespec
seed` successfully against this repo AND (b) file the first
dogfooded `propose-change` → `revise` cycle against the seeded
SPECIFICATION/. Per **v019 Q1**, the latter is part of step 2's
imperative-landing scope: minimum-viable `propose-change`,
`critique`, and `revise` MUST exist before Phase 6's seed cuts
SPECIFICATION/, so that Phase 7's full-feature widening can
proceed entirely through the governed loop.

**Authoring discipline (v032 D1).** Every module enumerated
below is authored under strict Red→Green-per-behavior. The
enumeration fixes WHICH modules exist and WHAT each owns; it
does NOT prescribe the order or granularity of the internal
authoring cycles. For each module: identify a behavior the
module owes (driven by a specific consumer or invariant);
write the smallest failing test that names that behavior;
observe the failure mode is the behavior gap, not a SyntaxError
/ ImportError / fixture issue; write the minimum
implementation that turns it Green; commit the Red-Green pair
atomically with the failing-test output captured in the commit
body per Plan Phase 5 §"Per-commit Red-output discipline". No
bulk authoring of an entire module followed by tests-after; no
characterization-style backfill; no speculative defensive code.

Required implementation surface (everything else stays stubbed):

- `livespec/errors.py` — landed in Phase 2 (full
  `LivespecError` hierarchy + `HelpRequested` per the style
  doc §"Exit code contract"). Phase 3 verifies Phase 2's
  errors.py covers every domain-error class the seed
  implementation uses; widens the hierarchy if Phase 3
  surfaces new classes that weren't anticipated at Phase 2.
- `livespec/types.py` — every canonical `NewType` alias listed in
  the style doc §"Domain primitives via `NewType`".
- `livespec/context.py` — `DoctorContext`, `SeedContext`, and
  the other context dataclasses with the exact fields named in
  the style doc §"Context dataclasses", including v014 N3's
  `config_load_status` / `template_load_status` AND v018 Q1's
  `template_name: str` (`"main"` sentinel for the main spec
  tree, or the sub-spec directory name for each sub-spec tree;
  consumed by `run_static.py`'s orchestrator-owned applicability
  table — see the orchestrator bullet below in this phase's
  `livespec/doctor/run_static.py` enumeration; the field-name
  was finalized in v021 Q1, replacing the prior binary
  `template_scope: Literal["main", "sub-spec"]`).
- `livespec/io/`:
  - `fs.py` — `@impure_safe` filesystem primitives; shared
    upward-walk helper per v017 Q9.
  - `git.py` — `get_git_user() -> IOResult[str, GitUnavailableError]`
    with the three-branch semantics (full success / partial /
    absent) from PROPOSAL.md §"Git".
  - `cli.py` — argparse-with-`exit_on_error=False` wrapped per
    the style doc §"CLI argument parsing seam".
  - `fastjsonschema_facade.py` — cached compile keyed on `$id`.
  - `structlog_facade.py` — typed logging wrapper.
  - `returns_facade.py` — typed re-exports (pending
    `returns-pyright-plugin-disposition`).
- `livespec/parse/jsonc.py` — thin pure wrapper over the
  vendored `jsoncomment`.
- `livespec/validate/` — factory-shape validators for the
  schemas seed actually needs in Phase 3 AND for the
  v019-Q1-mandated minimum-viable propose-change/revise cycle:
  `livespec_config.py`, `template_config.py`, `seed_input.py`,
  `sub_spec_payload.py`, `finding.py`, `doctor_findings.py`,
  `proposed_change_front_matter.py`,
  `revision_front_matter.py`, `proposal_findings.py`,
  `revise_input.py`.
- `livespec/schemas/*.schema.json` + paired
  `schemas/dataclasses/*.py` for the same set. Three-way
  pairing passes `check-schema-dataclass-pairing`.
- `livespec/commands/resolve_template.py` — full implementation
  per PROPOSAL.md §"Template resolution contract": supports
  `--project-root`, `--template`, upward-walk on `.livespec.jsonc`,
  built-in-name-vs-path resolution, stdout contract, exit-code
  table.
- `livespec/commands/seed.py` — full implementation per
  PROPOSAL.md §"`seed`": `--seed-json` intake, pre-seed
  `.livespec.jsonc` bootstrap per v016 P2 + v017 Q5/Q6,
  idempotency refusal, v001 history materialization,
  auto-capture of `seed.md` proposed-change +
  `seed-revision.md`. Per v018 Q1-Option-A, the
  implementation ALSO produces the two template sub-spec
  trees under `SPECIFICATION/templates/<name>/` atomically
  with the main tree — each sub-spec gets its own
  `spec.md`/`contracts.md`/`constraints.md`/`scenarios.md`,
  its own `proposed_changes/` with `README.md`, and its own
  `history/v001/` materialized from the payload.
  `seed_input.schema.json` widens to carry a
  `sub_specs: list[SubSpecPayload]` field; Phase 3 authors
  the schema + dataclass + validator triple for
  `SubSpecPayload`.
- `livespec/commands/propose_change.py` — **minimum-viable per
  v019 Q1**: validates the inbound `--findings-json <path>`
  payload against `proposal_findings.schema.json` (per PROPOSAL.md
  §"`propose-change`" lines 2149-2161), composes a
  proposed-change file from the findings (one `## Proposal:
  <name>` section per finding via the field-copy mapping in
  PROPOSAL.md lines 2232-2242), and writes it to
  `<spec-target>/proposed_changes/<topic>.md` (the `<spec-target>`
  is selected via the `--spec-target <path>` flag, defaulting to
  the project's main spec root). Collisions surface as exit-3
  domain failures. **Out of Phase-3 scope** (deferred to Phase 7's
  dogfooded widening): topic canonicalization (v015 O3),
  reserve-suffix canonicalization (v016 P3; v017 Q1), unified
  author precedence beyond the simplest two-source rule, collision
  disambiguation prompts (v014 N6), single-canonicalization
  invariant routing (v016 P4). Phase 3's minimum-viable version
  rejects topics that would require canonicalization rather than
  silently rewriting them — failure surface is "topic not
  canonical" with exit code 4.
- `livespec/commands/critique.py` — **minimum-viable per v019
  Q1**: invokes `propose_change.py` internally with the
  `-critique` reserve-suffix appended (the simplest delegation
  shape; full reserve-suffix algorithm lives in Phase 7).
  Accepts `--spec-target <path>` and routes the delegation with
  the same target. **Out of Phase-3 scope**: full critique
  prompt-driven flow (LLM-side); critique-as-internal-delegation
  is the wrapper-level mechanic, sufficient for the Phase 6
  first dogfooded cycle.
- `livespec/commands/revise.py` — **minimum-viable per v019 Q1**:
  reads every `<spec-target>/proposed_changes/*.md`, accepts a
  per-proposal accept/reject decision via stdin payload (the
  full LLM-driven decision flow lives in Phase 7), writes the
  paired `<topic>-revision.md`, and on accept cuts a new
  `<spec-target>/history/vNNN/` materialized from the
  current spec files. Accepts `--spec-target <path>`. **Out of
  Phase-3 scope**: per-proposal LLM decision flow with
  delegation toggle, rejection-flow audit trail richness beyond
  the simplest "decision: reject" front-matter line.
- `livespec/doctor/run_static.py` — orchestrator per PROPOSAL.md
  §"Static-phase structure" + v014 N3 bootstrap lenience + v018
  Q1 per-tree iteration (applicability dispatch finalized in
  v021 Q1). The orchestrator enumerates
  `(spec_root, template_name)` pairs at startup (main tree
  first with template-name sentinel `"main"`; then each
  sub-spec tree under `<main-spec-root>/templates/<sub-name>/`
  with template-name set to the sub-spec directory name); per
  pair it builds a per-tree `DoctorContext` (with `template_name`
  set appropriately) and runs the applicable check subset
  decided by the orchestrator-owned applicability table:
  - `template_exists` and `template_files_present` invoked
    only when `template_name == "main"` (sub-spec trees are
    spec trees, not template payloads).
  - `gherkin_blank_line_format` invoked when (`template_name
    == "main"` AND main `.livespec.jsonc.template ==
    "livespec"`) OR `template_name == "livespec"`; never
    invoked when `template_name == "minimal"` (matches
    PROPOSAL.md §"Per-tree check applicability"; the
    `minimal` sub-spec's `scenarios.md` follows the minimal
    template's no-Gherkin convention).
  - All other checks invoked uniformly per tree.

  The orchestrator never asks a check whether it applies; the
  table is the single source. Checks themselves emit no
  applicability-driven `skipped` Findings (skipped status is
  reserved for the v014 N3 bootstrap-lenience checks and
  semantically equivalent content-aware skips codified in the
  `static-check-semantics` deferred entry).
- `livespec/doctor/static/__init__.py` — static registry. Each
  entry exposes the pair `(SLUG, run)` (the v018 Q1 triple
  shape with `APPLIES_TO` is reverted in v021 Q1; the
  orchestrator now owns the applicability table).
- `livespec/doctor/static/` — each check module exposes
  `SLUG` and `run` only (no `APPLIES_TO` constant per v021
  Q1 — applicability is the orchestrator's responsibility,
  not the check's). The v1 applicability narrowings are
  documented at the orchestrator level above; checks
  themselves remain template-name-agnostic. Bootstrap-
  lenience semantics (v014 N3) and any other content-aware
  `skipped` semantics remain inside individual check modules
  per the `static-check-semantics` deferred entry.
  Phase-3 minimum subset of checks the seed post-step
  exercises: `livespec_jsonc_valid`, `template_exists`,
  `template_files_present`, `proposed_changes_and_history_dirs`,
  `version_directories_complete`, `version_contiguity`,
  `revision_to_proposed_change_pairing`,
  `proposed_change_topic_format`. **Phase 3 registers ONLY
  these 8 implemented checks in `static/__init__.py`.** The
  remaining four checks (`out_of_band_edits`,
  `bcp14_keyword_wellformedness`, `gherkin_blank_line_format`,
  `anchor_reference_resolution`) are not yet present in the
  codebase at Phase 3 — neither as modules nor as registry
  entries. Phase 7 lands their implementations and adds them
  to `static/__init__.py` as a single explicit registry edit
  alongside the implementations (PROPOSAL.md §"doctor → Static-
  phase orchestrator" already permits the registry to grow
  via explicit edits). This avoids overloading the
  `skipped` Finding status — which is reserved for v014 N3
  bootstrap-lenience and content-aware skips per the
  applicability rules above — with a third "transitional
  not-yet-implemented" semantic, and keeps Phase 6's exit
  criterion ("all marked `pass`") literally satisfiable.
- `seed/SKILL.md` — **bootstrap prose** covering the pre-seed
  dialogue, the two-step `resolve_template.py` →
  Read(`prompts/seed.md`) dispatch, payload assembly, wrapper
  invocation, post-wrapper narration, and exit-code handling
  with retry-on-4. The pre-seed dialogue per PROPOSAL.md
  §"`seed`" lines 1717-1759 has THREE questions when the
  selected template is `livespec`, all of which the bootstrap
  prose MUST author (v021 Q2):

  1. **Template-selection question** (v014 N1 / v017 Q2) —
     options: `livespec` (multi-file recommended default),
     `minimal` (single-file `SPECIFICATION.md`), or a custom
     template path.
  2. **(v020 Q2) Sub-spec-emission question** (asked only
     when the selected template's seed prompt declares
     sub-spec-emission capability — the `livespec` built-in
     is the v1 example): "Does this project ship its own
     livespec templates that should be governed by sub-spec
     trees under `SPECIFICATION/templates/<name>/`?
     (default: no)"
  3. **(v020 Q2) Template-name follow-up** (asked only on a
     "yes" answer to question 2): the user provides the list
     of template directory names under
     `.claude-plugin/specification-templates/` (or equivalent
     project-specific location) that should each receive a
     sub-spec tree.

  This is intentionally narrower than the full per-sub-command
  body structure in PROPOSAL.md; Phase 7 brings it to final per
  `skill-md-prose-authoring`.
- `propose-change/SKILL.md`, `critique/SKILL.md`,
  `revise/SKILL.md` — **bootstrap prose per v019 Q1**: just
  enough to (a) accept an inline authored propose-change file
  via the SKILL.md prose, (b) invoke the wrapper with
  `--spec-target`, (c) narrate the result. No interview-style
  authoring flow; no LLM-driven critique/revise decision flow.
  Phase 7 brings all three to final per
  `skill-md-prose-authoring`.
- `doctor/SKILL.md`, `help/SKILL.md` — **bootstrap prose**
  (Phase 3's `doctor/SKILL.md` covers static-phase invocation
  ONLY and explicitly does NOT invoke an LLM-driven phase;
  Phase 7 adds LLM-phase orchestration per
  `skill-md-prose-authoring`).
- The `livespec` template's prompts — **bootstrap-minimum
  authoring per prompt (v020 Q4 four-prompt widening)**. v019
  widened only `prompts/seed.md`; v020 Q4 widens all four
  livespec-template prompts at this phase, mirroring the
  existing seed.md widening pattern, to remove the quality
  risk where Phase 7's heaviest semantic work would otherwise
  run through Phase-2-minimum prompts:

  - `prompts/seed.md` — bootstrap-minimum authoring sufficient
    for the Phase 6 seed LLM round-trip to produce a schema-
    valid `seed_input.schema.json` payload covering the main
    spec AND, when the user answers "yes" to the pre-seed
    "ships own livespec templates" question per v020 Q2 (Phase
    6 does), one `sub_specs[]` entry per named template. The
    prompt handles BOTH dialogue branches rigorously: "yes" →
    enumerate the named templates and emit `sub_specs[]`; "no"
    → emit `sub_specs: []`. (Q2 + Q4 joint widening.) This is
    intentionally narrower than the full template-controlled
    seed interview; the full `prompts/seed.md` is regenerated
    from the `livespec` template's sub-spec in Phase 7.
  - `prompts/propose-change.md` — bootstrap-minimum authoring
    sufficient for Phase 7's first dogfooded cycle to file
    full-fidelity propose-change files: full front-matter
    authoring, sub-spec routing via `--spec-target`, reserve-
    suffix awareness for `-critique` etc. The prompt MUST
    produce propose-change content of sufficient quality to
    drive the Phase 7 widening cycles for the propose-change
    command itself.
  - `prompts/revise.md` — bootstrap-minimum authoring
    sufficient for Phase 7's first dogfooded cycle to drive
    per-proposal decisions, write paired revision files with
    full audit trails, and trigger version cuts. The prompt
    MUST produce revision content of sufficient quality to
    drive the Phase 7 widening cycles for the revise command
    itself (including the cycles that author the final
    revise.md prompt).
  - `prompts/critique.md` — bootstrap-minimum authoring
    sufficient for Phase 7's first dogfooded cycle to invoke
    critique-as-internal-delegation against either a main-spec
    or sub-spec target via `--spec-target`. The prompt MUST
    produce critique-driven propose-change content of
    sufficient quality to drive the Phase 7 widening cycles
    for the critique command itself.

  The `minimal` template's prompts stay stubbed at this phase
  — Phase 6 uses only the `livespec` template. All four
  `minimal`-template prompts are Phase 7 work.

**Exit criterion (narrow Phase-3 gate).** `just check-lint`
succeeds (the only tool-backed gate available at Phase 3 — the
dev-tooling-backed checks `check-wrapper-shape`,
`check-main-guard`, and `check-schema-dataclass-pairing` are
deferred to Phase 5 per the deferral list below, since their
backing `dev-tooling/checks/*.py` scripts are Phase 4 work).
Running `/livespec:seed` against a throwaway `tmp_path` fixture
(with
the seed dialogue answering "yes" to v020 Q2's "ships own
livespec templates" question and naming `livespec` and
`minimal`) produces a valid `.livespec.jsonc`, the main spec
tree with `history/v001/`, AND both template sub-spec trees
under `<tmp>/SPECIFICATION/templates/{livespec,minimal}/` each
with their own `history/v001/` (each sub-spec tree carrying
the uniform multi-file livespec layout per v020 Q1: spec.md,
contracts.md, constraints.md, scenarios.md, sub-spec-root
README.md, plus per-version README in history/v001/) — all
three trees materialized atomically by the single seed
invocation (M5; v018 Q1; v020 Q1 uniform README). Following
the seed, the throwaway-fixture round-trip ALSO files a
propose-change against the main tree via
`/livespec:propose-change --spec-target <tmp>/SPECIFICATION`
and revises it via `/livespec:revise --spec-target
<tmp>/SPECIFICATION`, demonstrating that Phase 6's first
dogfooded cycle is mechanically achievable (v019 Q1).

**v020 Q3 — sub-spec routing smoke cycle.** After the
main-tree propose-change/revise cycle, the smoke test files a
SECOND propose-change/revise cycle targeting the sub-spec tree:

  /livespec:propose-change --spec-target <tmp>/SPECIFICATION/templates/livespec
  /livespec:revise         --spec-target <tmp>/SPECIFICATION/templates/livespec

Confirm `<tmp>/SPECIFICATION/templates/livespec/history/v002/`
materializes with the expected `proposed_changes/` subdir
contents (the propose-change file + its paired revision
record). Same code path as the main-tree smoke; different
`--spec-target` argument. Catches `--spec-target` sub-spec
routing bugs at the Phase 3 boundary, where recovery is
imperative-landing (cheap), instead of Phase 7's dogfood
boundary where recovery would require the broken governed
loop.

Full `just check` is NOT a Phase-3 gate. The following targets
are deliberately deferred and reactivate at the phases where
their backing content lands: `check-tests`, `check-coverage`,
`check-pbt-coverage-pure-modules`, `check-claude-md-coverage`
(tests/ branch), and every target backed by a Phase-4
`dev-tooling/checks/*.py` script reactivate at Phase 4 or
Phase 5 exit per the Phase 4 / Phase 5 deferral lists.
`check-types` (pyright strict against `livespec/**`) reactivates
at **Phase 7**, once stubs widen toward their full implementations
— not Phase 5, because Phase-2/3 stubs do not yet satisfy strict
pyright against their wider implementation contracts.
`e2e-test-claude-code-mock` reactivates at **Phase 9**, once
`tests/e2e/fake_claude.py` is fleshed out. Phase-2/3 stubs
conform to the Phase-2 stub contract so they pass Phase-5
gates without refactor; the strict-pyright gate against the
widened implementations is what activates at Phase 7.

### Phase 4 — Developer tooling enforcement scripts

Author every enforcement check under `dev-tooling/checks/` per
the canonical `just` target list. Each script is a standalone
Python module conforming to the same style rules as the shipped
code (`just check` includes `dev-tooling/**` in scope).

**Authoring discipline (v032 D1).** Every check below is
authored test-first per the same Red→Green-per-behavior
discipline that applies to `livespec/**`. For each check:
write the failing test in `tests/dev-tooling/checks/` that
names ONE failure mode the check exists to catch (a specific
violation pattern, with input that should be rejected); observe
the test fail because the check has not yet been written; write
the minimum check logic that turns it Green; commit the
Red-Green pair. Repeat per failure mode until the check covers
every pattern PROPOSAL.md §"Canonical target list" / the style
doc names for that target. No characterization-style
backfilling of tests against pre-existing checks; the existing
Phase 4 check implementations are deleted and re-derived under
this discipline as part of Plan Phase 5 §"Retroactive TDD redo
of Phase 3 + Phase 4 work".

Scripts:

- `file_lloc.py` — file ≤ 200 logical lines.
- `private_calls.py`, `global_writes.py`,
  `supervisor_discipline.py`, `rop_pipeline_shape.py` (v029 D1:
  single public method per `@rop_pipeline`-decorated class),
  `no_raise_outside_io.py` (raise-site
  only per v017 Q3), `no_except_outside_io.py`,
  `public_api_result_typed.py` (`__all__`-based per v012 L9),
  `main_guard.py`, `wrapper_shape.py` (permits the optional blank
  line per v016 P5), `schema_dataclass_pairing.py` (three-way per
  v013 M6), `keyword_only_args.py` (also verifies
  `frozen=True`+`kw_only=True`+`slots=True` on `@dataclass`),
  `match_keyword_only.py`, `no_inheritance.py` (direct-parent
  allowlist per v013 M5), `assert_never_exhaustiveness.py`,
  `newtype_domain_primitives.py`, `all_declared.py`,
  `no_write_direct.py`, `pbt_coverage_pure_modules.py`,
  `claude_md_coverage.py`, `no_direct_tool_invocation.py`
  (grep-level), `no_todo_registry.py` (release-gate only),
  `heading_coverage.py` (validates that every `##` heading in
  every spec tree — main + each sub-spec under
  `SPECIFICATION/templates/<name>/` — has a corresponding
  entry in `tests/heading-coverage.json` whose `spec_root`
  field matches the heading's tree; tolerates an empty `[]`
  array pre-Phase-6, before any spec tree exists; from Phase
  6 onward emptiness is a failure if any spec tree exists),
  `vendor_manifest.py` (validates `.vendor.jsonc` against a
  schema that forbids placeholder strings — every entry has
  a non-empty `upstream_url`, a non-empty `upstream_ref`, a
  parseable-ISO `vendored_at`, and the `shim: true` flag is
  present on `jsoncomment` (the v026 D1 hand-authored shim)
  and absent on every other entry (post-v027 D1
  `typing_extensions` is upstream-sourced, NOT a shim)),
  `red_output_in_commit.py` (v032 D4: walks `git log --grep`
  against the v032-redo commit range and rejects any
  feature/bugfix commit lacking a `## Red output` fenced
  block in its body; activates as a hard `just check` gate
  at Phase 5 exit, informational pre-Phase-5-exit).

Each script has a paired `tests/dev-tooling/checks/test_<name>.py`.

Every `dev-tooling/` directory carries a `CLAUDE.md`.

**Exit criterion:** `just check` passes against the current code
base for every target except those still deferred to Phase 5's
exit criterion (carrying forward Phase 3's deferral list, less
the targets satisfied by this phase). Every check listed in the
canonical table is invokable and non-trivial (tests cover both
pass and fail cases).

The following `just check` targets remain deferred at Phase 4
exit. Each target's reactivation phase is enumerated below; the
target becomes a Phase-N exit gate at the phase where its backing
content lands:

- `check-tests` and `check-coverage` — activate at Phase 5;
  require the Phase 5 test suite (per-wrapper coverage via
  monkeypatched `main`, `_bootstrap.bootstrap()` coverage via
  `sys.version_info` monkeypatch, 100% line+branch across
  `livespec/**`, `bin/**`, and `dev-tooling/**`).
- `check-prompts` — activates at Phase 5 against placeholder
  test files that pass trivially; `tests/prompts/` is created
  as a Phase 5 skeleton and fleshed out in Phase 7.
- `check-types` (pyright strict against the `livespec/**`
  surface) — activates at **Phase 7**, once `livespec/**` stubs
  widen toward their full implementations. Phase 4 dev-tooling
  code conforms to the style rules by convention (the rules are
  unchanged); the automated gate cannot pass at Phase 5 because
  the Phase-2/3 stubs do not yet satisfy strict pyright against
  their wider implementation contracts.
- `e2e-test-claude-code-mock` — activates at **Phase 9**, once
  `tests/e2e/fake_claude.py` is fleshed out per the Phase 9
  end-to-end integration test work. Phase 5 creates only the
  `tests/e2e/` skeleton + placeholder `fake_claude.py`.

Targets explicitly active at Phase 4 exit (must pass): every
`dev-tooling/checks/*.py`-backed target in the canonical list,
plus `check-lint`, `check-format`, `check-complexity`,
`check-imports-architecture`, and `check-tools`.

### Phase 5 — Test suite

Build out the test tree per PROPOSAL.md §"Testing approach":

- `tests/` mirrors `.claude-plugin/scripts/livespec/`,
  `.claude-plugin/scripts/bin/`, and `<repo-root>/dev-tooling/`
  one-to-one.
- `tests/bin/test_wrappers.py` — meta-test: every wrapper matches
  the 6-statement shape.
- `tests/bin/test_<cmd>.py` — per-wrapper coverage test that
  imports the wrapper under `monkeypatch`-stubbed `main`,
  catches `SystemExit` via `pytest.raises`.
- `tests/bin/test_bootstrap.py` — covers `_bootstrap.bootstrap()`.
  Covers BOTH sides of the `sys.version_info` check via
  `monkeypatch.setattr(sys, "version_info", (3, 9, 0, "final", 0))`
  (and its 3.10+ counterpart). Pragma exclusions on `bin/*.py`
  are forbidden by v011 K3, so branch coverage of the
  exit-127 path is achieved exclusively through monkeypatching.
- `tests/e2e/` — skeleton directory, `CLAUDE.md`, placeholder
  `fake_claude.py`. Real E2E content is fleshed out in Phase 9
  (Phase 8 only files the forward-pointing closure for the
  `end-to-end-integration-test` deferred item per Phase 8 item
  14; the actual `fake_claude.py`, fixtures, and pytest suite
  land as Phase 9 propose-changes against `SPECIFICATION/`).
- `tests/prompts/` — (v018 Q5) skeleton directory with
  `CLAUDE.md` describing the prompt-QA harness conventions
  (distinct from `tests/e2e/fake_claude.py`), plus
  `tests/prompts/<template>/` subdirectories for each
  built-in template (`livespec`, `minimal`). Each
  per-template subdirectory carries its own `CLAUDE.md`
  per the strict DoD-13 rule (every directory under
  `tests/` has a `CLAUDE.md`); the per-template
  `CLAUDE.md` MAY be a brief one-paragraph cross-reference
  to `tests/prompts/CLAUDE.md` when conventions don't
  diverge. Each per-template subdirectory carries placeholder
  `test_{seed,propose_change,revise,critique}.py` per
  PROPOSAL.md §"Testing approach — Prompt-QA tier". Real
  prompt-QA content (harness + fixtures + semantic-property
  assertions) is fleshed out in Phase 7 (as part of each
  built-in template's sub-spec-driven content generation)
  and closed by Phase 8's `prompt-qa-harness` deferred-items
  revision. `just check-prompts` is authored in Phase 1's
  justfile alongside the rest of the canonical target list
  (recipe body: `pytest tests/prompts/`); at Phase 1 time
  `tests/prompts/` doesn't exist yet so the target fails on
  invocation, but Phase 1's exit criterion is that
  `just --list` shows every target — failing-but-defined is
  fine and consistent with how `check-tests` and
  `check-coverage` are listed in Phase 1's justfile but rely
  on Phase-5 test code to actually pass.
- `tests/fixtures/` — empty at this phase; grows through Phases
  6–9.
- `tests/heading-coverage.json` — initially empty array `[]`
  (populated alongside the seeded spec in Phase 6 and after each
  deferred-item-driven revise). Entry shape per v018
  Q1-Option-A carries a `spec_root` field discriminating the
  main spec from each template sub-spec tree.
- `tests/test_meta_section_drift_prevention.py` — covers the
  registry.
- Every `tests/` directory (with `fixtures/` subtrees excluded at
  any depth) carries a `CLAUDE.md`.

#### Retroactive TDD redo of Phase 3 + Phase 4 work (v032 D2)

Phase 3 and Phase 4 produced impl-first code with tests
authored afterward. v032 D1 closes the temporal carve-out
that permitted that mode; this sub-section bridges the gap
by deleting every Phase 3 / Phase 4 / Phase 5-so-far Python
artifact and re-authoring each module under strict
Red→Green-per-behavior. Procedure:

1. **Stash the pre-redo tree as a committed zip archive.**
   Archive every `.py` file under
   `.claude-plugin/scripts/livespec/` (excluding
   `_vendor/**` and `__init__.py` files), every `.py` under
   `.claude-plugin/scripts/bin/` (excluding `_bootstrap.py`,
   which has its own meta-test contract and is preserved as
   the version-gate), every `.py` under
   `dev-tooling/checks/`, every `.py` under
   `tests/livespec/`, every `.py` under `tests/bin/`
   (excluding `tests/bin/test_bootstrap.py` and
   `tests/bin/conftest.py`), and every `.py` under
   `tests/dev-tooling/checks/` into
   `bootstrap/scratch/pre-redo.zip`. The zip is committed to
   the repo (binary blob, under SCM but not source-readable —
   `git grep` skips it, `Read` on it returns binary garbage,
   the only access path is deliberate `unzip`). Then delete
   the originals. The pre-redo zip preserves the audit trail
   for the v032 D3 quality-comparison report and survives
   until Phase 11 cleanup, which removes it via `git rm`. The
   zip MUST NOT be `unzip`-ed during authoring of the redone
   modules; the only legitimate `unzip` is the
   measurement-time extraction at v032 D3 report authoring,
   which extracts to a `tmp/bootstrap/pre-redo-extracted/`
   scratch dir, runs the metrics, and deletes the extraction
   when done.
2. **Verify clean state.** `just check-tests` against the
   stripped tree runs cleanly but collects ONLY the surviving
   `tests/bin/test_bootstrap.py` (the preserved Phase-2
   bootstrap meta-test, paired with the preserved
   `bin/_bootstrap.py`); zero Phase-3-5 tests survive
   collection because their imports are now gone. Confirms
   the tree is genuinely empty of Phase 3-5 Python. Expected
   pytest summary: a small handful of bootstrap tests pass,
   nothing else collected.
3. **Walk the PROPOSAL-prescribed module enumeration in
   dependency order**, re-authoring each module under
   Red→Green-per-behavior. Recommended order, derived from
   import dependencies: (a) `livespec/types.py`,
   `livespec/errors.py`, `livespec/context.py`,
   `livespec/__init__.py`; (b) `livespec/schemas/dataclasses/`
   (10 modules); (c) `livespec/parse/` (jsonc, front_matter);
   (d) `livespec/validate/` (10 modules); (e)
   `livespec/io/` (cli, fs, git,
   fastjsonschema_facade, returns_facade, structlog_facade);
   (f) `livespec/commands/` (resolve_template, seed,
   propose_change, critique, revise, prune_history, plus
   `_seed_helpers`, `_revise_helpers`); (g)
   `livespec/doctor/` (run_static plus the 12 static checks
   per PROPOSAL.md §"Static-phase structure"); (h)
   `dev-tooling/checks/` (26 checks); (i)
   `.claude-plugin/scripts/bin/` wrappers (8 modules; meta-
   tested via `tests/bin/test_wrappers.py` per the existing
   wrapper-shape contract). The order is a recommendation,
   not a contract — Red→Green discipline determines the next
   module by which test the executor wants to write next.
4. **Per-module discipline.** Each Red→Green pair lands as
   one commit. The commit message starts with `phase-5: ...`
   (since this is Phase 5 execution work) and the commit
   body MUST include the captured Red output per Plan Phase
   5 §"Per-commit Red-output discipline" (v032 D4). Refactor
   commits are separate per PROPOSAL.md §"The independent
   refactor cycle" — they do NOT include a new failing test
   and have a `refactor: ...` message prefix.
5. **No re-derivation by inspection.** The committed
   `bootstrap/scratch/pre-redo.zip` MUST NOT be `unzip`-ed
   during redo authoring. The zip is binary-blob committed
   so the audit trail is solid, but extracting it during
   module authoring would defeat the discipline. The
   architecture is PROPOSAL-prescribed; the implementation
   must emerge from the failing tests, not be transcribed
   from the prior version. The only legitimate extraction is
   at D3 quality-comparison report authoring time.
6. **Exit condition.** All Phase 3 / Phase 4 / Phase 5 exit
   criteria pass against the redone tree (in particular:
   `just check-tests`, `just check-coverage` at 100%
   line+branch across `livespec/**`, `bin/**`,
   `dev-tooling/**`, the seed round-trip, and the propose-
   change/revise smoke cycle). The v032 D3 quality-
   comparison report passes its acceptance criteria.

The redo is bracketed within Phase 5 because Phase 5 is when
the test infrastructure becomes operational; the pre-redo
test infrastructure existed but the discipline did not. The
redo is a one-time event; once complete, normal Phase
5-onward work resumes from the (new) sub-step that was
in-progress at v032 commit time.

#### Quality-comparison report (v032 D3)

After the retroactive redo completes and all Phase 3 / Phase
4 / Phase 5 exit gates pass, the executor authors
`bootstrap/v032-quality-report.md` (committed alongside the
zip stash; both removed at Phase 11 via `git rm`). The report
MUST cover all four dimensions below with concrete
measurements drawn from a one-time extraction of
`bootstrap/scratch/pre-redo.zip` (pre) versus the live tree
(post). Extraction procedure: `unzip
bootstrap/scratch/pre-redo.zip -d
tmp/bootstrap/pre-redo-extracted/`; run all metrics against
the extracted tree; delete `tmp/bootstrap/pre-redo-extracted/`
when the report is authored. The extraction is the ONLY
legitimate `unzip` of the stash; it happens once, after the
redo is complete, with the explicit purpose of measurement.
Subjective claims are not sufficient — every dimension below
carries at least one quantitative metric.

**Dimension 1 — Architecture.**

- Module count delta per top-level package
  (`livespec/commands/`, `livespec/io/`, `livespec/doctor/`,
  `livespec/validate/`, `livespec/parse/`, `livespec/schemas/`,
  `dev-tooling/checks/`, `tests/**`). Pre and post counts;
  delta with sign.
- Architectural-rule compliance: count of distinct
  PROPOSAL.md / style-doc rule citations the post-tree
  implementation satisfies that the pre-tree did not (e.g.,
  ROP pipeline shape, `@impure_safe` boundaries,
  `@rop_pipeline` single-public-method, supervisor
  discipline) — the executor MUST identify any rule the
  pre-tree was violating that the redo brought into
  compliance, OR explicitly state "no rule-compliance
  delta" and explain why the rules were already satisfied.
- Public-API surface: union of all `__all__` entries across
  `livespec/**`. Pre count, post count, delta with sign.
  Reductions are improvements (smaller surface ⇒ tighter
  contract); growth requires justification per added entry.

**Dimension 2 — Coupling.**

- Per-module import count: for each module under
  `livespec/**`, count of distinct module-level `import` /
  `from … import` statements (excluding `_vendor/**`).
  Report mean and max pre vs post; delta with sign.
  Reductions are improvements.
- Cross-package edges: count of import edges that cross
  package boundaries (`commands/` → `io/`, `doctor/` →
  `validate/`, etc.). Pre vs post; delta with sign.
- Cyclic-import / fan-out hotspots: any module with
  fan-out > 8 in either tree gets called out by name. The
  report MUST identify whether each hotspot survived the
  redo (and why) or was eliminated.

**Dimension 3 — Cohesion.**

- LOC per module (logical lines, per
  `dev-tooling/checks/file_lloc.py`). Pre mean / max / count
  > 100 LLOC; post mean / max / count > 100 LLOC. Each
  dimension delta with sign.
- Public-method count per public class: report mean and max
  pre vs post. The `@rop_pipeline` single-public-method rule
  (v029 D1) means classes carrying that decorator have
  exactly one public method; the report MUST confirm
  compliance for both trees and surface any
  multi-public-method classes that survived the redo.
- Public-function-per-module count: pre vs post mean and
  max; delta. Higher cohesion typically presents as fewer
  public functions per module with more focused
  responsibilities.

**Dimension 4 — Unnecessary-code elimination.**

- Total LOC delta (impl + test, separately): pre LLOC,
  post LLOC, delta with sign. Pure reductions are the
  expected primary signal of TDD's "minimum implementation"
  rule.
- Defensive / unreachable code count: count of `pragma: no
  cover` directives (must be zero in both trees per v030
  D2), count of `raise NotImplementedError` exclusions, count
  of `case _:` arms (the structurally-unreachable
  assert-never sentinels — these are expected to survive the
  redo wherever exhaustive `match` statements remain). Pre
  vs post; delta with sign.
- Helper-function reuse: count of helper functions in
  `_*.py` private-helper modules pre vs post. The redo is
  expected to *reduce* helper count if Phase 3-4 introduced
  speculative helpers that no specific test demanded.
- Behavioral-equivalence audit: the executor MUST run the
  Phase 3 exit-criterion smoke (seed round-trip + propose-
  change/revise) against both the pre-redo stash (after
  temporary restoration to a scratch venv if needed) and
  the post-redo tree, and confirm output equivalence. Any
  behavior that changed during the redo is a defect of the
  redo (TDD redo is supposed to be behavior-preserving at
  the contract level), not a feature.

**Acceptance criteria.** The report is acceptable iff:

1. Every dimension above is covered with the named
   quantitative metrics.
2. At least three of the four dimensions show concrete
   improvement (negative delta on LOC, fan-out, public
   surface, etc., or positive delta on rule compliance).
   Materially-equivalent measurements across all four
   dimensions ("the redo produced the same code") indicate
   the discipline lapsed and the redo failed; the user MAY
   reject the report and demand a re-redo, OR MAY accept
   it as evidence that the original Phase 3-4 code was
   already at the design quality TDD would have produced
   (which is a possible-but-rare outcome the report
   captures honestly rather than overclaiming).
3. The behavioral-equivalence audit passes (Phase 3
   smoke produces equivalent output against both trees).

The report is gated by AskUserQuestion before Phase 5
advance: the user reads the report, accepts or rejects, and
on rejection the redo is re-attempted (or the stash is
restored if the user concludes the redo cannot improve on
the original).

#### Per-commit Red-output discipline (v032 D4)

Every Red→Green commit authored under v032 D2's retroactive
redo (and every subsequent feature/bugfix commit from this
phase onward, per the universal §"Test-Driven Development
discipline") MUST include the captured failing-test output
in the commit body. Format: a `## Red output` heading
followed by a fenced code block containing the literal
`pytest` output the executor observed when the test was
first run prior to any implementation. The block confirms
the failure was at the assertion site (the behavior gap),
not at parse/import/fixture time.

`tests/dev-tooling/checks/test_red_output_in_commit.py`
(authored as part of the dev-tooling checks redo) walks
`git log --grep` against the redo's commit range and rejects
any feature/bugfix commit that lacks a `## Red output`
section. The check is informational pre-Phase-5-exit; it
becomes a hard `just check` gate at Phase 5 exit (lefthook
+ post-Phase-5-exit commits).

`just check-coverage` MUST pass at 100% line+branch.

Phase 5 ALSO promotes `just bootstrap` from its Phase-1
placeholder to the real recipe: `lefthook install &&
ln -sfn ../.claude-plugin/skills .claude/skills`. Running
`just bootstrap` installs lefthook into `.git/hooks/` so
that every commit from Phase 6 onward triggers `just check`
on the now-passing enforcement suite. **This is the
activation point of the hard-constraint per-commit gate per
PROPOSAL.md §"Testing approach — Activation"**; pre-Phase-5
commits are grandfathered, and from this commit onward no
commit lands without passing the per-commit gate.

**Exit criterion:** `just check` passes for every target except
those still deferred to later phases (carrying forward Phase 4's
deferral list, less the targets satisfied by this phase). Targets
explicitly active at Phase 5 exit (must pass): `check-tests`,
`check-coverage` (100% line+branch across `livespec/**`, `bin/**`,
and `dev-tooling/**`), `check-pbt-coverage-pure-modules`,
`check-claude-md-coverage`, `check-heading-coverage` (against the
empty-array baseline; full enforcement begins in Phase 6),
`check-vendor-manifest`, `check-prompts` (against placeholder
test files that pass trivially), plus every target already passing
at Phase 4 exit (`check-lint`, `check-format`, `check-complexity`,
`check-imports-architecture`, `check-tools`, and every
`dev-tooling/checks/*.py`-backed target in the canonical list).
`just bootstrap` has been run and lefthook is installed. The
v032 D3 retroactive-TDD quality-comparison report (Plan Phase
5 §"Quality-comparison report") has been authored and its
acceptance criteria pass — the redone tree demonstrates
concrete improvement on architecture, coupling, cohesion,
and unnecessary-code elimination relative to the
`bootstrap/scratch/pre-redo.zip` stash.

The following `just check` targets remain deferred at Phase 5
exit and activate at later phases:

- `check-types` — activates at **Phase 7**, once `livespec/**`
  stubs widen toward their full implementations. The Phase-2/3
  stubs in `livespec/**` do not yet satisfy strict pyright
  against their wider implementation contracts.
- `e2e-test-claude-code-mock` — activates at **Phase 9**, once
  `tests/e2e/fake_claude.py` is fleshed out per the Phase 9
  end-to-end integration test work. Phase 5 creates only the
  skeleton + placeholder.

### Phase 6 — First self-application seed

The executor agent — the same Claude Code session executing this
plan — invokes `/livespec:seed` against `/data/projects/livespec`
itself via the Skill tool. The skill bundle being invoked is the
plugin bundle this very executor session loaded from
`.claude-plugin/`. Self-application is literal: livespec-as-skill
seeds livespec-as-project. The invocation produces the real
`SPECIFICATION/` tree — main spec + the two built-in-template
sub-specs atomically, per v018 Q1-Option-A.

Seed scope is deliberately NARROW for the MAIN spec: Phase 6
seeds the main spec from PROPOSAL.md + `goals-and-non-goals.md`
ONLY. The companion docs
(`python-skill-script-style-requirements.md`,
`livespec-nlspec-spec.md`, `subdomains-and-unsolved-routing.md`,
lifecycle/terminology docs, prior-art survey) are migrated
individually in Phase 8 via dedicated propose-change/revise
cycles (items 2 and 3). This preserves the seed as a clean
PROPOSAL.md-grounded first cut and lets each companion-doc
migration be auditable as its own revision, rather than relying
on a single 295KB-context seed pass that risks lossy
compression.

**Acknowledgment of deviation from `deferred-items.md`.** The
`python-style-doc-into-constraints` deferred entry's "How to
resolve" guidance says "Migrate ... at seed time." Phase 6
deliberately deviates from that guidance for the audit-
granularity reason above (one Phase-8 propose-change per
companion doc gives finer-grained, more reviewable history than
folding every companion doc into a single seed payload).
`deferred-items.md` is frozen at v018 and cannot be revised; the
deviation is acknowledged here and made explicit in Phase 8
item 2's revise. The remaining companion-doc-targeting deferred
entries (`companion-docs-mapping`) consume the same Phase-8
mechanism uniformly, so the deviation is consistent across all
companion docs except `goals-and-non-goals.md` (which IS
seeded at Phase 6 because it's the project's intent
description, not implementation guidance).

For the two TEMPLATE SUB-SPECS, Phase 6 seeds from the
PROPOSAL.md sections describing each built-in template plus
the `livespec-nlspec-spec.md` shipped alongside the `livespec`
template. The sub-specs land bootstrap-minimum at this phase;
they are widened in Phase 7 via propose-change/revise when the
full template content (prompts, starter content, delimiter-
comment format) is authored.

Seed intent fed to the prompt:

> Seed this project's `SPECIFICATION/` tree from the frozen
> `PROPOSAL.md` and `goals-and-non-goals.md` in
> `brainstorming/approach-2-nlspec-based/`. Use the `livespec`
> built-in template (multi-file). The
> `livespec-nlspec-spec.md` the template's prompts use at
> seed-time comes from the template's own copy, NOT from the
> brainstorming folder.
>
> **Pre-seed dialogue answers (v020 Q2).** Answer the
> template-selection question with `livespec`. Answer the new
> "Does this project ship its own livespec templates that
> should be governed by sub-spec trees under
> `SPECIFICATION/templates/<name>/`?" question with **YES**.
> When the dialogue follows up asking which template directory
> names should receive sub-spec trees, name **two**:
> `livespec` and `minimal` (the two v1 built-ins shipped under
> `.claude-plugin/specification-templates/`). The seed prompt
> emits one `sub_specs[]` entry per name; the wrapper
> materializes both sub-spec trees atomically with the main
> tree (per v018 Q1 + v020 Q1 uniform-multi-file structure).
>
> MAIN SPEC:
> `spec.md` carries the core PROPOSAL material (runtime and
> packaging, specification model, sub-command lifecycle,
> versioning, pruning, sub-commands, proposed-change /
> revision file formats, testing approach, developer-tooling
> layout, Definition of Done, non-goals, self-application).
> `contracts.md` carries the skill↔template JSON contracts
> (input/output schemas; wrapper CLI shapes), the
> lifecycle exit-code table, and the sub-spec structural
> mechanism (propose-change/revise `--spec-target` flag;
> `seed_input.schema.json`'s `sub_specs` field; per-sub-spec
> doctor parameterization).
> `constraints.md` carries the architecture-level
> constraints PROPOSAL.md states directly (Python 3.10+ pin,
> vendored-lib discipline, pure/IO boundary, ROP composition,
> supervisor discipline) plus the typechecker decisions
> pinned in Phase 1. The bulk of
> `python-skill-script-style-requirements.md` lands via a
> Phase 8 propose-change (item 2), NOT here.
> `scenarios.md` carries the happy-path seed/propose-change/
> revise/doctor scenario plus the three error paths v014 N9
> enumerates and the recovery paths from §"seed", §"doctor",
> and §"Pruning history" in PROPOSAL.md.
>
> TEMPLATE SUB-SPEC `SPECIFICATION/templates/livespec/`:
> `README.md` is a one-paragraph orientation: "This sub-spec
> governs the `livespec` built-in template's prompt interview
> flows, starter content, NLSpec-discipline injection, and
> template-internal contracts. Sub-spec layout follows
> livespec's internal multi-file convention per v020 Q1 and
> is decoupled from the `livespec` template's end-user
> conventions for end-user spec layout."
> `spec.md` carries the `livespec` template's user-visible
> behavior: the seed interview flow's intent, the
> propose-change/revise/critique prompt interview intents,
> how `livespec-nlspec-spec.md` is internalized by each
> prompt, and the starter-content policy (what headings get
> derived, what BCP14 placement looks like, the scenarios.md
> literal stub). **`spec.md` MUST also explicitly specify
> that the `livespec` template's `prompts/seed.md` implements
> the v020 Q2 sub-spec-emission contract: the prompt asks the
> pre-seed question "Does this project ship its own livespec
> templates that should be governed by sub-spec trees under
> `SPECIFICATION/templates/<name>/`?"; on "yes" it enumerates
> the user-named templates and emits one `sub_specs[]` entry
> per name per `seed_input.schema.json`'s `SubSpecPayload`
> shape; on "no" (the default) it emits `sub_specs: []`.** The
> seed prompt regenerated from this sub-spec in Phase 7 MUST
> preserve this user-answer-driven behavior; Phase 7's revise
> step rejects regenerated prompts that hard-code emission
> per v019's now-superseded contract.
> `contracts.md` carries the template-internal JSON contracts
> (what `seed_input.schema.json` payload fields this template
> populates, what `proposal_findings.schema.json` fields the
> critique prompt populates) AND a "Per-prompt
> semantic-property catalogue" subsection enumerating the
> testable semantic properties for each REQUIRED prompt
> (`seed`, `propose-change`, `revise`, `critique`) — at
> Phase 6 this is bootstrap-minimum (1-2 properties per
> prompt; e.g., for `seed`: "MUST derive top-level headings
> from intent nouns, not from a fixed taxonomy"; "MUST ask
> the v020 Q2 sub-spec-emission question and route emission
> by the user's answer"); Phase 7's first propose-change
> against this sub-spec widens the catalogue to the full
> assertion surface that the v018 Q5 prompt-QA harness
> asserts against.
> `constraints.md` carries the NLSpec discipline constraints
> (Gherkin blank-line convention, BCP14 keyword well-
> formedness, heading taxonomy conventions).
> `scenarios.md` carries a happy-path seed-interview scenario
> (covering both the "yes" and "no" branches of the v020 Q2
> sub-spec-emission question) plus one edge-case per prompt.
>
> TEMPLATE SUB-SPEC `SPECIFICATION/templates/minimal/`:
> `README.md` is a one-paragraph orientation: "This sub-spec
> governs the `minimal` built-in template's prompt interview
> flows, starter content, delimiter-comment format, and
> template-internal contracts. Sub-spec layout follows
> livespec's internal multi-file convention per v020 Q1 and
> is decoupled from the `minimal` template's end-user
> single-file convention — sub-specs are livespec-internal
> artifacts governing template behavior, not exemplars of
> end-user template usage."
> `spec.md` carries the `minimal` template's single-file
> positioning (reference-minimum for custom-template authors;
> canonical fixture for the end-to-end integration test) and
> its prompt interview intents (reduced vs. `livespec`; the
> `minimal` template's seed prompt does NOT implement the
> v020 Q2 sub-spec-emission capability — `minimal`-rooted
> projects always get `sub_specs: []`).
> `contracts.md` carries the delimiter-comment format
> contract (format is itself Phase 7 work; at Phase 6 this
> section is a placeholder with a "TBD in Phase 7" note) AND
> a "Per-prompt semantic-property catalogue" subsection
> bootstrap-minimum the same way the `livespec` sub-spec's
> contracts.md is, scoped to `minimal`'s reduced prompt
> contracts.
> `constraints.md` carries the single-file-only constraint
> (for end-user output of the `minimal` template; this is
> NOT a constraint on the sub-spec's own structure, which is
> uniformly multi-file per v020 Q1), the `spec_root: "./"`
> convention, and the `gherkin-blank-line-format` doctor-
> check exemption.
> `scenarios.md` carries the end-to-end-integration-test
> scenarios' structural outline (retry-on-exit-4, doctor-
> static-fail-then-fix, prune-history-no-op).

After seed, the working tree contains:

- `.livespec.jsonc` at repo root.
- **Main spec** (per the `livespec` template's multi-file
  convention):
  - `SPECIFICATION/{README.md, spec.md, contracts.md,
    constraints.md, scenarios.md}`.
  - `SPECIFICATION/proposed_changes/` containing only the
    skill-owned `README.md`.
  - `SPECIFICATION/history/README.md` (skill-owned;
    directory-description paragraph per PROPOSAL.md
    §"SPECIFICATION directory structure").
  - `SPECIFICATION/history/v001/` containing frozen copies
    of every main-spec file (`README.md`, `spec.md`,
    `contracts.md`, `constraints.md`, `scenarios.md`) +
    `proposed_changes/seed.md` +
    `proposed_changes/seed-revision.md`.
- **`livespec` template sub-spec** (uniform livespec-internal
  multi-file layout per v020 Q1):
  - `SPECIFICATION/templates/livespec/{README.md, spec.md,
    contracts.md, constraints.md, scenarios.md}`.
  - `SPECIFICATION/templates/livespec/proposed_changes/`
    containing only the skill-owned `README.md`.
  - `SPECIFICATION/templates/livespec/history/README.md`
    (skill-owned).
  - `SPECIFICATION/templates/livespec/history/v001/`
    containing frozen copies of every sub-spec file
    (`README.md`, `spec.md`, `contracts.md`, `constraints.md`,
    `scenarios.md`) + an EMPTY `proposed_changes/` subdir
    (sub-specs do NOT receive auto-captured seed proposals
    per v018 Q1 — the main-spec `seed.md` + `seed-revision.md`
    documents the whole multi-tree creation).
- **`minimal` template sub-spec** (uniform livespec-internal
  multi-file layout per v020 Q1; structurally identical to
  the `livespec` sub-spec; sub-spec layout is decoupled from
  the minimal template's end-user single-file convention
  because sub-specs are livespec-internal artifacts governing
  template behavior, not exemplars of end-user template
  usage):
  - `SPECIFICATION/templates/minimal/{README.md, spec.md,
    contracts.md, constraints.md, scenarios.md}`.
  - `SPECIFICATION/templates/minimal/proposed_changes/`
    containing only the skill-owned `README.md`.
  - `SPECIFICATION/templates/minimal/history/README.md`
    (skill-owned).
  - `SPECIFICATION/templates/minimal/history/v001/`
    containing frozen copies of every sub-spec file
    (`README.md`, `spec.md`, `contracts.md`, `constraints.md`,
    `scenarios.md`) + an EMPTY `proposed_changes/` subdir
    (sub-specs do NOT receive auto-captured seed proposals
    per v018 Q1).

The seed wrapper writes the skill-owned `proposed_changes/
README.md` AND `history/README.md` per-tree (same content
across trees; only the `<spec-root>/` base differs). Per v020
Q1, sub-spec README presence is uniform across all sub-spec
trees (sub-spec-root README + per-version README); the v019
asymmetry that mirrored each sub-spec's described template
convention is superseded — sub-specs are livespec-internal
spec trees and use the multi-file livespec layout uniformly.

Running `/livespec:doctor` against this newly-seeded state
passes its STATIC phase per-tree (main + each sub-spec).
**LLM-driven phases (objective + subjective checks) do NOT run
at Phase 6** — the full LLM-driven phase orchestration in
`doctor/SKILL.md` is Phase-7 work per `skill-md-prose-authoring`.
Phase 3's `doctor/SKILL.md` bootstrap prose covers static-phase
invocation only; it explicitly does NOT invoke an LLM-driven
phase. Phase 7 brings doctor's LLM-driven phase to operability;
the surfaced findings can then be acted on (or not) via separate
`critique` invocations, but doctor's LLM phase does NOT itself
require `critique` to function — they're independent
sub-commands.

**Imperative one-time heading-coverage population (v021 Q3).**
After the seed wrapper completes successfully and BEFORE
Phase 6's exit criterion is asserted, the executor agent
performs one additional imperative step: walk every `##`
heading in every seeded spec file (main + both sub-specs)
and write a corresponding entry to
`tests/heading-coverage.json`. Each entry carries a
`spec_root` field naming its tree; entries land with
`test: "TODO"` + non-empty `reason` placeholders at this
point (Phase 7–8 work replaces TODOs with real test IDs via
the governed loop). The file is committed alongside the
Phase 6 seed commit.

This step is permitted under PROPOSAL.md §"Self-application"
Bootstrap exception (v018 Q2; v019 Q1 clarification) — Phase
6 is the imperative window's closing step, and meta-test
data file population is a one-time bootstrap side-effect
that does not belong in the seed wrapper's deterministic
file-shaping contract (PROPOSAL.md §"`seed`" wrapper
file-shaping work items 1-6 are unchanged). From Phase 7
onward, every propose-change/revise that adds / changes /
removes `##` headings updates `tests/heading-coverage.json`
via the governed loop's `resulting_files[]` mechanism.

**Exit criterion:** `just check` passes (now including
`check-heading-coverage` against the populated
`tests/heading-coverage.json`); `/livespec:doctor`'s static
phase runs cleanly against every spec tree — one wrapper
invocation, exit `0` overall, with per-tree findings emitted
and all marked `pass`. LLM-driven phases are Phase-7 scope;
they are NOT invoked at Phase 6 and consequently NOT part of
Phase 6's exit criterion.

### Phase 7 — Widen sub-commands to full feature parity + full doctor coverage

With `SPECIFICATION/` in place AND the v019-Q1-mandated
minimum-viable `propose-change`/`critique`/`revise` already
operable from Phase 3, **widen** every minimum-viable
sub-command to full feature parity, **implement** the
sub-commands not present in Phase 3 (`prune-history`,
doctor's LLM-driven phase), and flesh out the remaining
doctor static checks. **Every change in this phase lands via
a `propose-change` → `revise` cycle against the seeded
spec — Phase 7 has zero imperative landings**, mirroring v019
Q1's clarified step 4 ("widen via dogfood; no imperative
work after the seed"). SPECIFICATION/ revisions and code
implementation land atomically per the dogfooding rule.
PROPOSAL.md stays frozen — from Phase 6 onward, SPECIFICATION/
is the living oracle.

**Ordering inside Phase 7.** The work items below are not all
parallel; two dependency edges constrain execution:

1. **Sub-spec widening before dependent regeneration.** Each
   sub-spec (`SPECIFICATION/templates/livespec/`,
   `SPECIFICATION/templates/minimal/`) lands at Phase 6 with
   bootstrap-minimum content and (for `minimal`) explicit
   "TBD in Phase 7" markers — most notably the delimiter-
   comment format in `SPECIFICATION/templates/minimal/
   contracts.md`'s "Template↔mock delimiter-comment format"
   section, which all four `minimal` prompts depend on.
   Shared-dependency sections like that one are widened in a
   dedicated prior propose-change/revise cycle (no template
   regeneration in the same revise) before any dependent
   prompt or starter-content regeneration runs. Per-prompt
   semantic-property-catalogue widening (in
   `SPECIFICATION/templates/<name>/contracts.md`) happens
   **in-line** with each prompt's regeneration cycle: one
   revise updates both the catalogue subsection for that
   prompt and the regenerated `prompts/<prompt>.md` file
   atomically. This also delivers §6 Risk #5's mitigation
   (catching under-specified sub-spec content via critique-
   driven widening before any template content generation).
2. **Prompt-QA harness before dependent prompt regeneration.**
   The prompt-QA harness work item below (template-agnostic
   `tests/prompts/_harness.py` + per-template fixtures) MUST
   land before any per-prompt regeneration cycle that
   verifies the regenerated prompt against the harness — most
   notably the v018 Q5 / v020 Q2 smoke-check on the
   regenerated `prompts/seed.md` that exercises both
   sub-spec-emission dialogue branches. Listing order in this
   document is by topic, not execution order; the executor
   agent sequences the harness implementation cycle before the
   first prompt regeneration cycle that depends on it.

Work items (each is one or more propose-change files filed
against the seeded `SPECIFICATION/`):

- `livespec/commands/propose_change.py` — **widen** the Phase-3
  minimum-viable implementation to full feature parity: topic
  canonicalization (v015 O3), reserve-suffix canonicalization
  (v016 P3; v017 Q1), unified author precedence, full schema
  validation, collision disambiguation (v014 N6), single-
  canonicalization invariant routing (v016 P4). The
  `--spec-target <path>` flag (per v018 Q1-Option-A) is
  already wired in Phase 3; Phase 7 only widens the body
  surface, not the CLI surface.
- `livespec/commands/critique.py` — **widen** the Phase-3
  minimum-viable internal-delegation shape to full
  reserve-suffix-aware delegation, accepting `--spec-target`
  and routing delegation with the same target.
- `livespec/commands/revise.py` — **widen** the Phase-3
  minimum-viable accept/reject decision flow to the full
  per-proposal LLM-driven decision flow (skill-prose-side),
  with delegation toggle, full version-cut + history
  materialization, rejection flow preserving audit trail. The
  `--spec-target <path>` flag is already wired in Phase 3;
  Phase 7 widens the body surface only.
- `livespec/commands/prune_history.py` — full pruning logic with
  `PRUNED_HISTORY.json` marker, no-op short-circuit, numeric
  contiguity.
- `livespec/doctor/static/` — the four remaining checks
  (`out_of_band_edits`, `bcp14_keyword_wellformedness`,
  `gherkin_blank_line_format`, `anchor_reference_resolution`)
  implemented in full with the semantics from PROPOSAL.md
  §"Static-phase checks" and codified in the
  `static-check-semantics` deferred item. `out_of_band_edits`
  honors the pre-backfill guard + auto-backfill semantics
  including author identifier `livespec-doctor`. **Registry
  edit:** the same propose-change/revise cycle (or one
  per-check cycle, executor's choice) that lands each
  implementation also adds the corresponding `(SLUG, run)`
  entry to `livespec/doctor/static/__init__.py` — the four
  checks are not present in the registry at Phase 3 per the
  Phase-3 narrowed-registry policy and are introduced into
  the registry exactly when their implementations land. All
  doctor-static checks are parameterized per-spec-tree per
  v018 Q1-Option-A: `run_static.py` iterates over the main
  spec root + each sub-spec root discovered under
  `<main-spec-root>/templates/<name>/`, running the
  appropriate check subset per tree (e.g.,
  `gherkin_blank_line_format` applies to the main spec and
  the `livespec` sub-spec but NOT the `minimal` sub-spec).
- `livespec/doctor/` — LLM-driven phase orchestration in
  `doctor/SKILL.md` including both objective and subjective
  checks + template-extension hooks.
- `parse/front_matter.py` — restricted-YAML parser (tracked by
  the `front-matter-parser` deferred item).
- The full `livespec` template content — its
  `prompts/seed.md` (replacing the Phase 3 bootstrap-minimum
  version), `prompts/propose-change.md`,
  `prompts/revise.md`, `prompts/critique.md`,
  `prompts/doctor-llm-subjective-checks.md` (plus optional
  `doctor-llm-objective-checks.md`), and the
  `specification-template/SPECIFICATION/` starter content —
  is **agent-generated from
  `SPECIFICATION/templates/livespec/`** (the sub-spec seeded
  in Phase 6). Each prompt's authoring lands via a
  `propose-change --spec-target SPECIFICATION/templates/livespec`
  → `revise --spec-target ...` cycle against that sub-spec,
  and the generated template files are committed alongside
  the sub-spec revision. No hand-authoring.
  **Verification (v018 Q1; v020 Q2 user-answer-driven).** The
  regenerated `prompts/seed.md` MUST implement the v020 Q2
  sub-spec-emission contract: ask the pre-seed "Does this
  project ship its own livespec templates...?" question; on
  "yes", enumerate the user-named templates and emit one
  `sub_specs[]` entry per name conforming to
  `seed_input.schema.json`'s `SubSpecPayload` shape; on "no"
  (the default), emit `sub_specs: []`. Phase 7's revise step
  for `prompts/seed.md` MUST run a smoke-check against the
  regenerated prompt that exercises BOTH branches (the
  prompt-QA harness from v018 Q5 covers this in
  tests/prompts/livespec/test_seed.py; the harness fixtures
  include both a "yes" answer with named templates and a "no"
  answer). If the regenerated prompt hard-codes emission per
  v019's now-superseded contract OR omits the user-driven
  dialogue question, Phase 7's revise rejects the modification.
- The full `minimal` template content — its four prompts
  with their delimiter comments and its single-file starter
  `specification-template/SPECIFICATION.md` — is
  agent-generated from
  `SPECIFICATION/templates/minimal/` sub-spec via the same
  `--spec-target` mechanism. The delimiter-comment format
  is CHOSEN here (not at Phase 9); the choice is codified in
  `SPECIFICATION/templates/minimal/contracts.md` under a
  "Template↔mock delimiter-comment format" section, and THAT
  is what Phase 9's `fake_claude.py` parses against. Future
  custom-template authors can replicate the mock harness
  without reading the parser source.
- All seven SKILL.md prose bodies brought to final per the
  deferred item `skill-md-prose-authoring` — including
  replacing the Phase-3 bootstrap prose for `seed`,
  `propose-change`, `critique`, `revise`, `doctor`, and `help`
  with the full per-sub-command body structure from PROPOSAL.md
  (opening, when-to-invoke, inputs, steps, post-wrapper,
  failure handling).
- **Prompt-QA harness machinery (template-agnostic
  infrastructure; v018 Q5).** Implement the harness shared by
  every per-template prompt-QA test under
  `tests/prompts/<template>/`: the `fake_claude.py`-style
  prompt-invocation seam (separate from `tests/e2e/fake_claude.py`
  per the Phase 5 note), the fixture-payload format, and the
  semantic-property assertion API the per-prompt tests consume.
  The harness lives at `tests/prompts/_harness.py` (or similar
  shared location) and is consumed UNIFORMLY by both
  `tests/prompts/livespec/test_*.py` and
  `tests/prompts/minimal/test_*.py`. The harness MUST itself
  satisfy every livespec Python rule (style doc compliance,
  `__all__` declaration, return-type annotations, etc.). The
  harness is template-agnostic; per-template semantic-property
  catalogues live in each template's sub-spec
  (`SPECIFICATION/templates/<name>/contracts.md` "Per-prompt
  semantic-property catalogue" subsection) and are consumed by
  the per-template tests, not by the harness itself. Phase 8
  item 17 (`prompt-qa-harness`) closes against this work.

**Exit criterion:** every wrapper in `bin/` has a real
implementation path; every doctor-static check runs in full;
`just check` + `/livespec:doctor` pass on the project's own
`SPECIFICATION/`; every `test: "TODO"` in
`heading-coverage.json` has been resolved to a real test id;
`just check-prompts` (template-agnostic harness + per-template
tests) passes.

### Phase 8 — Process every deferred-items entry

Walk `brainstorming/approach-2-nlspec-based/deferred-items.md` in
order, filing one or more `propose-change` files for each entry
and running `revise` against them. Each entry's revision either
fully incorporates the content into `SPECIFICATION/` (primary
case) or explains why the entry is superseded / moot / deferred
further (secondary case, with a paired revision explaining the
deferral).

**Default `--spec-target` for Phase 8 (v018 Q1).** Every Phase
8 propose-change uses `--spec-target SPECIFICATION` (the main
spec tree) by default UNLESS the per-item entry below names a
different target. Justification: most deferred items target
spec content in `SPECIFICATION/spec.md` /
`SPECIFICATION/contracts.md` /
`SPECIFICATION/constraints.md` (main); the actual
implementation files (`dev-tooling/checks/`, `pyproject.toml`,
`.claude-plugin/scripts/`, etc.) are committed alongside the
revise but are described BY the main-spec content. The two
v018 NEW entries (`sub-spec-structural-formalization`,
`prompt-qa-harness`) and the three v018 CLOSED entries
(`template-prompt-authoring`,
`returns-pyright-plugin-disposition`,
`basedpyright-vs-pyright`) are bookkeeping closures pointing
at PROPOSAL.md / Phase-1 / Phase-3 / Phase-6 / Phase-7
decisions; their Phase 8 revises are also `--spec-target
SPECIFICATION` (main) — the closure record lives in main's
`history/`, not in any sub-spec's history.

Canonical deferred items — 17 items after v018 (the `### <id>`
schema-example heading at `deferred-items.md` line 29 is not an
item): 15 carried forward from v017 plus 2 new in v018
(`sub-spec-structural-formalization`, `prompt-qa-harness`); 3
closed in v018 (`template-prompt-authoring`,
`returns-pyright-plugin-disposition`,
`basedpyright-vs-pyright`) land as bookkeeping revisions
pointing at PROPOSAL.md / Phase-1 / Phase-7 decisions:

1. `template-prompt-authoring` — CLOSED in v018 Q1. Content
   already landed in Phase 7, generated agentically from
   each template's sub-spec under
   `SPECIFICATION/templates/<name>/` per v018 Q1-Option-A.
   The Phase-7 propose-change that landed the `minimal`
   template's delimiter comments also codified the delimiter-
   comment format contract in
   `SPECIFICATION/templates/minimal/contracts.md` (under a
   "Template↔mock delimiter-comment format" section).
   Phase 8's revise records the closure, pointing at the
   relevant Phase-7 sub-spec revisions and PROPOSAL.md
   §"SPECIFICATION directory structure — Template
   sub-specifications".
2. `python-style-doc-into-constraints` — **performs** the
   migration of `python-skill-script-style-requirements.md`
   (≈92KB) into `SPECIFICATION/constraints.md`, restructured for
   the spec's heading conventions and BCP 14 requirement
   language. **Per-section split (one propose-change/revise per
   top-level source-doc section).** The migration is NOT a
   single revise cycle. The source style doc decomposes into
   roughly 15-25 top-level sections (e.g., Linter and formatter,
   Type discipline, Domain primitives via `NewType`,
   `Result`/`IOResult` discipline, Wrappers, Context dataclasses,
   Dev tooling and task runner, Enforcement suite, etc.). Each
   section becomes its own propose-change topic against
   `SPECIFICATION/`, paired with its own revise that lands a
   bounded chunk of restructured-for-BCP14 content into
   `SPECIFICATION/constraints.md` (or `SPECIFICATION/spec.md`
   when the destination heading taxonomy fits better — chosen
   per propose-change). The split matches the granularity Phase
   8 item 3 (`companion-docs-mapping`) already uses for
   companion docs, and applies the same audit-granularity
   rationale Phase 6 invokes for the seed scope ("audit
   granularity beats single-pass seed compression risk"): each
   section's revision is human-reviewable in isolation, and
   later need to revisit a particular style rule does not have
   to contend with a single 92KB historical revision.

   Sequencing within item 2: the executor selects a section
   ordering (e.g., source-doc reading order) and files each
   propose-change in that order. Each revise lands its own
   `history/vNNN/` snapshot. The first cycle's paired revise
   body acknowledges the deviation from `deferred-items.md`
   §`python-style-doc-into-constraints`'s "at seed time"
   guidance (per Phase 6's documented reason); subsequent
   cycles cross-reference the first. The last cycle's revise
   records the deferred entry as fully closed: every
   source-doc section has a paired revision; the brainstorming
   `python-skill-script-style-requirements.md` is reference-
   only (frozen); `SPECIFICATION/constraints.md` (plus
   `spec.md` where chosen) is the living oracle for all style-
   doc rules going forward.
3. `companion-docs-mapping` — (v018 Q6) processes every
   companion doc according to its pre-assigned migration class
   (MIGRATED-to-SPEC-file / SUPERSEDED-by-section /
   ARCHIVE-ONLY) per PROPOSAL.md §"Companion documents and
   migration classes". The deferred entry's body is a pointer
   to that section; each Phase-8 propose-change targets one
   companion doc; the paired revise records the migration
   outcome (what was migrated, into which section, or why the
   doc is ARCHIVE-ONLY). Phase 6 has already migrated
   `goals-and-non-goals.md`; Phase 8 processes the remaining
   assignments.
4. `enforcement-check-scripts` — **migrates** the canonical
   enforcement-check list (and the narrowed-to-two
   import-linter contracts per v017 Q3) into
   `SPECIFICATION/constraints.md` (or `spec.md` if the
   migrated content fits the spec.md heading taxonomy
   better — chosen during the propose-change). After this
   Phase-8 revise lands, `SPECIFICATION/` is the authoritative
   oracle for the canonical check list; Phase-4's actual
   `dev-tooling/checks/*.py` implementation is then validated
   to match the now-spec-resident list, and any drift is its
   own propose-change.
5. `claude-md-prose` — verifies every `CLAUDE.md` exists and
   carries real content (not lorem-ipsum stubs).
6. `task-runner-and-ci-config` — verifies `justfile`,
   `lefthook.yml`, `.github/workflows/*.yml` match the
   configuration codified in `SPECIFICATION/` (the seeded and
   Phase-8-migrated oracle; PROPOSAL.md is frozen reference
   material only).
7. `static-check-semantics` — materializes the
   semantics-codification paragraph for every check touched by
   v006–v017 widenings (bootstrap lenience, GFM anchor rules,
   reserve-suffix algorithm, wrapper-shape blank-line tolerance,
   etc.) into `constraints.md` or `spec.md` as appropriate.
8. `returns-pyright-plugin-disposition` — Originally CLOSED
   in v018 Q4 (vendor a pyright plugin alongside the library).
   RE-OPENED and RE-CLOSED in v025 D1 with the revised
   disposition: **no pyright plugin is vendored, because no
   such plugin exists upstream and pyright does not support
   plugins by design** (microsoft/pyright#607,
   dry-python/returns#1513). The `[tool.pyright]` config in
   `pyproject.toml` (Phase 1) carries no `pluginPaths` entry;
   `.claude-plugin/scripts/_vendor/` (Phase 2) carries no
   `returns_pyright_plugin/` directory. Rationale migrated
   to `SPECIFICATION/constraints.md` in Phase 6. Bookkeeping
   close pointing at the v025 revision and PROPOSAL.md
   §"Runtime dependencies — Vendored pure-Python libraries".
9. `basedpyright-vs-pyright` — CLOSED in v018 Q4. pyright is
   the chosen typechecker; basedpyright is NOT used.
   Rationale in PROPOSAL.md §"Runtime dependencies —
   Developer-time dependencies → Typechecker decision
   (v018 Q4)"; migrated to `SPECIFICATION/constraints.md` in
   Phase 6. Bookkeeping close pointing at the Phase-1 commit.
10. `front-matter-parser` — landed in Phase 7.
11. `skill-md-prose-authoring` — landed in Phase 7.
12. `wrapper-input-schemas` — every input schema authored
    (`seed_input` including v018 Q1's `sub_specs: list[
    SubSpecPayload]` field; new standalone
    `sub_spec_payload.schema.json` + paired dataclass +
    validator per v018 Q1; `proposal_findings`,
    `revise_input`, `proposed_change_front_matter`,
    `revision_front_matter`, plus `doctor_findings`,
    `livespec_config`, `template_config`, `finding` as
    already done).
13. `user-hosted-custom-templates` — documented as v2 scope;
    revise closes the entry with a pointer to the v2 tracking
    (extended in v018 Q1 with the sub-spec-mechanism note —
    v2+ template-discovery extensions MAY declare their own
    sub-spec structure; the `--spec-target` flag surface is
    v1-frozen).
14. `end-to-end-integration-test` — Phase 8 files a
    forward-pointing **bookkeeping closure** (one propose-
    change/revise cycle against `SPECIFICATION/` whose
    revise body records: "Item 14 will be materialized in
    Phase 9 via the e2e harness work; this revise is the
    deferred-item closure record, not the implementation").
    The actual `tests/e2e/fake_claude.py`, fixtures, and
    pytest suite then land in Phase 9 as ordinary Phase 9
    propose-changes against `SPECIFICATION/`, NOT as
    additional deferred-item closures. This pattern matches
    how items 1, 8, 9, 10, 11, 13, 15, 16, and 17 are
    handled (forward- or backward-pointing bookkeeping
    closures) and lets Phase 8's exit criterion ("every
    deferred-item entry has a paired revision") be cleanly
    met by end of Phase 8 without leaking the Phase 8/9
    boundary. See Phase 9 for the implementation work
    itself.
15. `local-bundled-model-e2e` — documented as v2 scope; revise
    closes.
16. `sub-spec-structural-formalization` — (v018 Q1 NEW)
    materialized across Phase 3 (seed's multi-tree
    file-shaping work; `--spec-target` flag implementation on
    propose-change / critique / revise; `SubSpecPayload`
    schema + dataclass + validator; `DoctorContext`
    `template_name` field per v021 Q1), Phase 6 (sub-spec
    tree seeding atomically with main tree), Phase 7 (each
    built-in template's sub-spec contents authored via
    `propose-change --spec-target` cycles), and confirmed
    clean by Phase 8. Bookkeeping close pointing at the
    relevant phase commits.
17. `prompt-qa-harness` — (v018 Q5 NEW) materialized in
    Phase 5 (`tests/prompts/` skeleton), Phase 7 (per-prompt
    test content + harness implementation + fixture format —
    joint-resolved with `sub-spec-structural-formalization`
    for the per-prompt semantic-property catalogue authored
    in each sub-spec's `scenarios.md` or `contracts.md`),
    and confirmed green by Phase 8. Bookkeeping close.

**Exit criterion:** every deferred-item entry has a paired
revision under `SPECIFICATION/history/vNNN/proposed_changes/`.
`brainstorming/approach-2-nlspec-based/deferred-items.md` is
left AS-IS (brainstorming is frozen); the authoritative list of
future work now lives in `SPECIFICATION/` itself if any remains.

### Phase 9 — End-to-end integration test

Per v014 N9 and the `end-to-end-integration-test` deferred item:

- `tests/e2e/fake_claude.py` — the livespec-authored API-
  compatible mock of the Claude Agent SDK's query-interface
  surface. Parses the `minimal` template's prompt delimiter
  comments (format codified by Phase 7 in
  `SPECIFICATION/templates/minimal/contracts.md` under the
  "Template↔mock delimiter-comment format" section per v018
  Q1; the v014-N9-era joint-resolution between
  `template-prompt-authoring` and `end-to-end-integration-test`
  is superseded by v018 Q1's sub-spec codification, and
  `template-prompt-authoring` is closed) and drives wrappers
  deterministically.
- `tests/e2e/fixtures/` — `tmp_path`-template fixtures for the
  happy path + two error paths (retry-on-exit-4,
  doctor-static-fail-then-fix) + one no-op edge case
  (prune-history-no-op, which is a valid no-op outcome rather
  than an error path).
- `tests/e2e/test_*.py` — common pytest suite; mode selected
  by `LIVESPEC_E2E_HARNESS=mock|real`. Mock-only tests carry
  explicit pytest markers / `skipif` annotations.
- `.github/workflows/e2e-real.yml` — NOT modified in Phase 9.
  Phase 1 already authored the complete workflow (triggers,
  `just e2e-test-claude-code-real` invocation, secret gating).
  Phase 9 verifies the workflow runs green now that
  `fake_claude.py`, fixtures, and the pytest suite exist.

**Exit criterion:**
`just e2e-test-claude-code-mock` passes locally and in CI as part
of `just check`. `just e2e-test-claude-code-real` passes in the
dedicated workflow (manual or merge-queue trigger).

### Phase 10 — Verify the v1 Definition of Done

Run through the "Definition of Done (v1)" section as it lives
in `SPECIFICATION/spec.md` (migrated from PROPOSAL.md during
Phase 6) item-by-item (DoD 1–15), and produce a checklist
revision in `SPECIFICATION/history/vNNN/` confirming each
item. Any gaps become `propose-change` inputs and are revised.
PROPOSAL.md is reference material only; the verification is
against SPECIFICATION/'s version of DoD. When every DoD item
is marked done, tag the commit `v1.0.0`.

**Exit criterion:** `v1.0.0` tag exists; release-tag CI workflow
runs `just check-mutation` (first real baseline captured in
`.mutmut-baseline.json`) and `just check-no-todo-registry`;
both pass.

Phase 11 (cleanup) follows Phase 10. It is bookkeeping — not part
of the v1.0.0 release gate.

### Phase 11 — Cleanup of bootstrap scaffolding

After Phase 10's `v1.0.0` tag lands, remove the production-facing
references to the bootstrap scaffolding. The `bootstrap/` and
`brainstorming/` directories themselves stay in place as historical
reference; only the references that make them production-active
are removed.

1. **Remove the bootstrap plugin and its marketplace.** Three
   removals, gated by AskUserQuestion since these are committed
   files:
   - `rm -r .claude/plugins/livespec-bootstrap` (the plugin
     contents)
   - `rmdir .claude/plugins` (only if empty)
   - `rm .claude-plugin/marketplace.json` (the marketplace
     manifest at repo root)

   Do NOT remove `.claude/skills/` — that is the production
   plugin's symlink, established in Phase 2 and required by
   `/livespec:*` slash commands. Do NOT remove
   `.claude-plugin/plugin.json` — that is the production plugin's
   manifest, also from Phase 2. Do NOT remove
   `.claude/settings.local.json` if present (machine-local,
   gitignored anyway).

   Optional follow-up the user runs in Claude Code to clean up
   the locally-installed plugin state:
   ```
   /plugin uninstall livespec-bootstrap@livespec-marketplace
   ```

2. **Remove the repo-root orientation file:**
   ```
   rm AGENTS.md
   ```
   The per-directory `AGENTS.md` files inside `bootstrap/` and
   `brainstorming/` stay in place — they describe directories that
   themselves stay.

3. **Verify isolation:** confirm nothing in production code paths
   references `bootstrap/` or `brainstorming/`. Mechanical check:

   ```
   grep -rn "bootstrap/\|brainstorming/" \
     .claude-plugin/ dev-tooling/ tests/ SPECIFICATION/ \
     pyproject.toml justfile lefthook.yml .mise.toml \
     .github/ NOTICES.md .vendor.jsonc 2>/dev/null \
     | grep -v _vendor
   ```

   Expected output: empty. If any references surface, file an
   issue and resolve before committing the Phase 11 commit.

4. **Commit and push:** the bootstrap skill walks through the
   commit (per §8). Suggested message:
   `phase-11: remove bootstrap-skill symlink and root AGENTS.md`.
   Push only on user confirmation.

5. **Update the bootstrap skill's STATUS.md** to reflect cleanup
   complete; the next invocation of `/livespec-bootstrap:bootstrap`
   would fail anyway (the symlink is gone), and that is intentional.

**Exit criterion:** `.claude/plugins/livespec-bootstrap/` does
not exist; `.claude-plugin/marketplace.json` does not exist;
repo-root `AGENTS.md` does not exist; the grep in step 3
produces no output; Phase 11 commit landed.

After Phase 11, the bootstrap is fully wound down. The `bootstrap/`
and `brainstorming/` directories remain as historical reference,
but the production app — `.claude-plugin/`, `SPECIFICATION/`,
`dev-tooling/`, `tests/`, `pyproject.toml`, `justfile`,
`lefthook.yml`, etc. — does not reference them, and the
`/livespec-bootstrap:bootstrap` slash command is no longer
available.

---

## 5. Out of scope for this plan

- Any change to `brainstorming/`, `prior-art/`, or
  `history/vNNN/` — those are immutable archives from this point
  forward.
- Publishing the plugin to a Claude Code plugin marketplace
  (v2 non-goal per PROPOSAL.md).
- `opencode` / `pi-mono` agent-runtime packaging (v2 non-goal).
- Windows native support (non-goal).
- Async or concurrency (non-goal).

---

## 6. Risks and mitigations

- **Phase 3 is the tightest bottleneck.** If the minimum-viable
  `seed` path has a bug, Phase 6 produces an unreviewable spec.
  Mitigation: Phase 5's tests cover the seed code path at 100%
  line+branch AND include a property-based test over
  `seed_input.schema.json` via `hypothesis-jsonschema` before
  Phase 6 runs.
- **Dogfooding amplifies mistakes.** A bug in `revise` while
  processing deferred-items in Phase 8 corrupts the audit trail.
  Mitigation: each Phase-8 revise is a separate git commit; any
  corruption is recoverable by `git revert` + re-file the
  propose-change.
- **Vendoring drift.** Re-running `just vendor-update <lib>`
  after the baseline is in place can silently widen the
  supported-version window. Mitigation: `.vendor.jsonc` records
  the exact ref; PR review explicitly diffs `_vendor/` + the
  vendor manifest.
- **E2E-real CI cost.** Every `master` commit invokes the real
  Anthropic API. Mitigation: the mock tier is the default for
  `just check`; `e2e-real.yml` runs only on merge-queue + master
  + manual dispatch. A future deferred item
  (`local-bundled-model-e2e`) tracks removing the API-key
  dependency.
- **Under-specified template sub-specs at Phase 6 seed time.**
  The Phase 6 seed intent for each template sub-spec is the
  only input shaping that template's eventual prompt interview
  flow and starter-content policies. A shallow sub-spec seed
  produces a sub-spec that passes doctor-static but gives
  Phase 7's agent-generation step weak guidance, yielding
  templates whose prompt behavior is inconsistent or thin.
  Mitigation: the Phase 6 seed intent enumerates every
  sub-spec file's required content explicitly (see the
  intent block in Phase 6); Phase 7's first propose-change
  against each sub-spec is a critique-driven widening pass
  that exposes and fills under-specified sections before any
  template content generation happens.

---

## 7. Execution prompt

Paste the block below into a fresh Claude Code session rooted at
`/data/projects/livespec/` to execute the plan. The prompt is
self-contained; it does not require the plan document itself as
context, but it assumes every file listed in §1 is readable.

---

```
Execute the livespec bootstrap plan documented at
`/data/projects/livespec/brainstorming/approach-2-nlspec-based/PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md`.

## Required reading

Load every file listed in that plan's §1 "Inputs (authoritative
sources)" section before doing any work:

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md` (frozen
  at the latest history/vNNN snapshot — per the plan's
  "Version basis" note, this is v023 (a critique-fix overlay
  against v022 introducing the `tmp/bootstrap/` ownership
  convention; PROPOSAL.md substance unchanged from v022). v022
  adopts every prior decision (v018 Q1-Q6, v019 Q1, v020 Q1-Q4,
  v021 Q1-Q3) plus the v022 critique-fix overlay (D1-D10)
  introducing the template-bundled prompt-reference-metadata
  file class, the Plan §3 cutover carve-out, the per-section
  split for the Phase 8 style-doc migration, the Phase 8 item
  14 forward-pointing closure, the Phase 3 narrowed-registry
  stub policy, the Phase 7 ordering preamble, the Phase 5
  wording fix, and the §8 execution-scaffolding section. See
  the plan's "Version basis" section for the full decision
  summary;
  `history/v022/proposed_changes/critique-fix-v021-revision.md`
  for v022 decision provenance; and
  `history/v023/proposed_changes/critique-fix-v022-revision.md`
  for v023 decision provenance.)
- `brainstorming/approach-2-nlspec-based/livespec-nlspec-spec.md`
- `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`
- `brainstorming/approach-2-nlspec-based/goals-and-non-goals.md`
- `brainstorming/approach-2-nlspec-based/subdomains-and-unsolved-routing.md`
- `brainstorming/approach-2-nlspec-based/prior-art.md`
- All four `2026-04-19-nlspec-*.md` lifecycle / terminology docs
- `prior-art/nlspec-spec.md`
- `brainstorming/approach-2-nlspec-based/history/README.md`
- Every `history/vNNN/PROPOSAL.md`, every
  `history/vNNN/proposed_changes/*.md`, and every
  `history/vNNN/conversation.json` that exists. Skim
  `history/vNNN/retired-documents/` READMEs to understand what was
  retired and why, but do NOT load retired docs themselves.

Treat PROPOSAL.md v032 as authoritative. Do not propose any
modification to it, to any companion doc under `brainstorming/`,
or to any file under `brainstorming/history/` during this
execution. Those are frozen.

**Use the `bootstrap` skill at
`.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md` to
drive execution.** Invocation: `/livespec-bootstrap:bootstrap`. The
skill reads `bootstrap/STATUS.md` to find your current phase and
sub-step, presents the next action, and gates every advance on
explicit confirmation. See plan §8 for the full scaffolding
contract. Do NOT run phases ad-hoc; route every sub-step through
the skill so progress, decisions, and discovered issues land in
the persistent log files.

## Execution rules

1. Work phase by phase, in order: Phase 0 → Phase 11. Do not
   skip forward. Each phase's exit criterion MUST be demonstrably
   met before starting the next. Demonstrate the exit criterion
   by running the relevant `just` target or the explicit check
   the plan names. (Phase 11 is bookkeeping cleanup of the
   bootstrap scaffolding; it follows the v1.0.0 tag from Phase 10.)

2. Every phase of work lands as one or more git commits. Commit
   messages follow the form `<phase>: <summary>` (e.g.,
   `phase-1: repo-root developer tooling`).

3. `brainstorming/` is immutable from Phase 0 onward EXCEPT the
   one-time header-note addition in Phase 0 Step 2. Any other
   edit under `brainstorming/` is a bug in execution; stop and
   ask.

4. From Phase 6 onward, every change to any spec tree —
   main `SPECIFICATION/` OR any template sub-spec under
   `SPECIFICATION/templates/<name>/` — MUST flow through
   `propose-change` → `revise` against the specific tree,
   selected via the `--spec-target <path>` flag (use the skill
   bundle's own sub-commands; dogfooding is mandatory per
   PROPOSAL.md §"Self-application"). Do not hand-edit
   any `.md` file under any spec tree after Phase 6. Template
   content files (`.claude-plugin/specification-templates/
   <name>/prompts/*.md`, `template.json`,
   `specification-template/`) are ALSO not hand-edited after
   Phase 6: they are agent-generated alongside the
   corresponding sub-spec revision.

5. Confirm with the user before:
   - Adding a dependency not already listed in the authority
     for the current phase: PROPOSAL.md's runtime /
     developer-tooling sections during Phases 0–5;
     `SPECIFICATION/` (spec.md / constraints.md) from Phase 6
     onward.
   - Deviating from the directory layout declared by the
     same phase-keyed authority (PROPOSAL.md pre-Phase-6,
     `SPECIFICATION/` post-Phase-6).
   - Resolving a `static-check-semantics` sub-question in a way
     that's not already codified in `deferred-items.md`.

6. Do NOT run `git push`, `git tag`, `git reset --hard`,
   `git commit --amend`, or any destructive git operation
   without explicit confirmation. The only tag operation
   (creating `v1.0.0` in Phase 10) requires explicit approval.

7. Do NOT add hooks, CI triggers, or automations beyond what
   PROPOSAL.md and the style doc already specify. The
   enforcement suite is defined; implement it, do not extend it.

8. If any phase's exit criterion fails, surface the failure with
   the exact `just` target output or check message and ask the
   user before proceeding.

## Tracking

Use TaskCreate / TaskUpdate to track phase-level and
sub-step-level progress. Surface the phase you're working on and
what's next at each meaningful turn. Keep responses focused on
the work; do not narrate internal deliberation.

Start at Phase 0. Proceed when I say "go".
```

---

## 8. Execution scaffolding (the `bootstrap/` directory)

The plan is the oracle for what to do. The `bootstrap/` directory
at repo root is the scaffolding for tracking what HAS been done
and what's next, across sessions. It is throwaway — created in the
bootstrap-authoring commit (alongside this section), populated
during execution, and archived or deleted at Phase 10 exit.

### Directory shape

The bootstrap scaffolding spans three locations in the repo —
matching Claude Code's expected plugin layout (verified against a
working reference at `~/workspace/openbrain/`):

```
bootstrap/                             # state files only
├── AGENTS.md                          # bootstrap-directory orientation
├── STATUS.md                          # current phase / sub-step / next action
├── open-issues.md                     # append-only-with-status-mutation drift log
└── decisions.md                       # append-only judgment-call log

.claude-plugin/
└── marketplace.json                   # marketplace manifest at repo root (auto-discovered)

.claude/
└── plugins/
    └── livespec-bootstrap/            # the plugin Claude Code loads
        ├── .claude-plugin/
        │   └── plugin.json            # plugin manifest
        └── skills/
            └── bootstrap/
                └── SKILL.md           # the skill prose
```

### Skill discovery via repo-root marketplace

Claude Code auto-discovers a `marketplace.json` at
`.claude-plugin/marketplace.json` (repo root) without any
`.claude/settings.json` registration. The marketplace's `plugins[]`
entries reference plugin directories by path (string-typed
`source` field, relative to `marketplace.json`'s directory).

For the bootstrap plugin:

- **`.claude-plugin/marketplace.json`** declares the
  `livespec-marketplace` (top-level `name` + `owner` + `metadata`)
  and lists one plugin (`livespec-bootstrap`) with
  `source: "./.claude/plugins/livespec-bootstrap"` (path relative
  to `.claude-plugin/`).
- **`.claude/plugins/livespec-bootstrap/.claude-plugin/plugin.json`**
  is the plugin manifest. Plugin name = `livespec-bootstrap`.
- **`.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md`**
  is the skill. Skill name = `bootstrap`. Slash command =
  `/livespec-bootstrap:bootstrap`.

Critical: the `source` field in `marketplace.json` is a
**string** path, not an object. Tried `{"type": "directory",
"path": "."}` initially; that shape produces a "Plugin not found
in marketplace" error. Tried symlinks under `.claude/plugins/`;
Claude Code's plugin loader does not follow them. The pattern
above is the supported one.

**One-time setup per machine.** Claude Code does NOT auto-register
a local marketplace from a committed `marketplace.json`; the user
must add it explicitly. Run these four commands once per machine:

```
/plugin marketplace add ./.claude-plugin/marketplace.json
/plugin marketplace update livespec-marketplace
/plugin install livespec-bootstrap@livespec-marketplace
/reload-plugins
```

When `/plugin install` asks where to install, choose
**repo-scoped (project scope)** — the plugin is throwaway
scaffolding specific to this repo, removed at Phase 11 cleanup.

After this setup, `/livespec-bootstrap:bootstrap` appears in the
slash-command menu and future `/reload-plugins` invocations pick
up SKILL.md edits without re-installing.

Phase 1 preconditions explicitly carve `.claude/` and
`.claude-plugin/` out of the "no such directory exists yet" rule
(see §2 above). Phase 2 adds `.claude/skills/` (sibling under
`.claude/`) and `.claude-plugin/plugin.json` (sibling under
`.claude-plugin/`) as Phase 2 work; both coexist with the
bootstrap entries until Phase 11 cleanup.

### Per-directory `AGENTS.md` orientation files

Fresh AI sessions need to find their bearings without the user
having to brief them every time. Six `AGENTS.md` files at strategic
locations cover this:

| Path | Purpose | Lifecycle |
|---|---|---|
| `AGENTS.md` (repo root) | High-level orientation: bootstrap mode, where to look, hard rules | Removed by Phase 11 |
| `bootstrap/AGENTS.md` | Bootstrap-directory orientation: file roles, don't/do, symlink mechanism | Stays after Phase 11 |
| `brainstorming/AGENTS.md` | Brainstorming-tree orientation: which approaches are active vs abandoned | Stays after Phase 11 |
| `brainstorming/approach-2-nlspec-based/AGENTS.md` | Active-approach orientation: key files, how the bootstrap consumes them, editing rules | Stays after Phase 11 |
| `brainstorming/approach-2-nlspec-based/history/AGENTS.md` | History-tree orientation: structure, latest version, immutability | Stays after Phase 11 |
| `brainstorming/approach-1-openspec-inspired/AGENTS.md` | Abandoned-approach orientation | Stays after Phase 11 |

The repo-root `AGENTS.md` is the one that points at bootstrap
scaffolding; it becomes stale after Phase 11 (the scaffolding it
references is removed) and is therefore deleted at cleanup. The
per-directory files inside `bootstrap/` and `brainstorming/`
describe directories that themselves persist as historical
reference, so they stay.

### The `bootstrap` skill

`.claude/plugins/livespec-bootstrap/skills/bootstrap/SKILL.md` is a
Claude Code skill that drives plan execution. Invocation:

```
/livespec-bootstrap:bootstrap
```

(or the user MAY ask in plain language: "continue the bootstrap",
"where am I in the bootstrap?", etc.) The skill is shallow — it
reads `STATUS.md`, opens the relevant phase section of THIS plan
file, presents the next sub-step, and gates every advancement on
explicit user confirmation via AskUserQuestion. It does not
encode plan content; every invocation re-reads the plan, so plan
corrections flow into execution naturally.

The skill's full behavior contract lives in its SKILL.md prose;
this section documents the contract at the plan level.

#### Skill-driven loop

1. **Read state.** `bootstrap/STATUS.md` (current phase, sub-step,
   last completed exit criterion, next action, last-updated
   timestamp, last-commit sha). Initialize on first invocation.
2. **Present current state.** One paragraph stating where the
   user is and what's next.
3. **Gate with AskUserQuestion.** Five options (single-select):
   *proceed with the next sub-step* (recommended), *pause for
   now*, *report an issue first* (writes to
   `bootstrap/open-issues.md`; on `blocking` severity, routes to
   the halt-on-blocking sub-flow described below — does NOT loop
   back to the main loop until resolved), *record a decision
   first* (writes to `bootstrap/decisions.md`), or *something
   else* (free-form redirect).
4. **Execute the sub-step** when the user selects proceed.
   Updates STATUS on success.
5. **At phase exit (two-gate).** Phase boundaries always require
   two distinct gates in this order:
   - **5a. Drift-review checkpoint.** Read
     `bootstrap/open-issues.md`, filter to entries with the
     current phase number AND `Status: open`, summarize by
     severity. Show the user. If any blocking entries remain
     unresolved, the skill MUST NOT proceed to 5b — it offers
     the halt-and-revise walkthrough or the propose-change
     walkthrough (whichever applies), or pause. Non-blocking
     entries can be deferred to the post-Phase-6 drain or
     carried forward as-is via user choice.
   - **5b. Exit-criterion check + advance gate.** Run the
     phase's exit-criterion check verbatim from this plan;
     show result; gate advancement on a second AskUserQuestion
     confirmation. Advance only on explicit user confirm.
6. **At Phase 10 exit.** Ask the user whether to archive
   `bootstrap/` to `brainstorming/bootstrap-archive/`
   (recommended), delete it, or leave it in place.

#### Drift-correction sub-flows

The skill carries two explicit sub-flows for closing blocking
drift discovered mid-execution. They are entered from step 3's
halt-on-blocking branch or step 5a's drift-review checkpoint;
never from the main-loop step 3 directly.

- **Halt-and-revise walkthrough (pre-Phase-6 path).** Drives a
  formal `vNNN/` revision against PROPOSAL.md, mirroring
  v018-v023 (v023 was the first instance executed live during
  the bootstrap via this walkthrough).
  Skill computes next vNNN, asks for revision shape (direct
  overlay vs full critique-and-revise), walks the user through
  authoring revision file(s), applies edits to PROPOSAL.md,
  snapshots to `history/vNNN/`, surgical-edits the plan's
  Version basis + Phase 0 + execution prompt, marks the
  originating open-issues entry resolved, commits, and (on user
  confirm) pushes. The full step list lives in the skill's
  SKILL.md prose; this entry documents the contract at the plan
  level.
- **Propose-change walkthrough (post-Phase-6 path).** Drives a
  dogfooded `propose-change` → `revise` cycle against the seeded
  `SPECIFICATION/`. Skill asks for the target spec tree (main /
  `livespec` sub-spec / `minimal` sub-spec / other), walks the
  user through composing the propose-change content, invokes
  `/livespec:propose-change` via the Skill tool with the right
  `--spec-target`, then `/livespec:revise` with the same target,
  marks the originating open-issues entry resolved, and resumes.
  Only valid when STATUS shows `current_phase >= 6`.

#### State files

- `bootstrap/STATUS.md` — overwritten on every update; contract:
  six fields (`Current phase`, `Current sub-step`, `Last
  completed exit criterion`, `Next action`, `Last updated`,
  `Last commit`).
- `bootstrap/open-issues.md` — append-only log of plan / PROPOSAL
  drift discovered during execution. Three severities (`blocking`,
  `non-blocking-pre-phase-6`, `non-blocking-post-phase-6`); three
  dispositions (`halt-and-revise-brainstorming`,
  `defer-to-spec-propose-change`, `resolved-in-session`).
- `bootstrap/decisions.md` — append-only log of executor judgment
  calls during phase work that weren't pre-decided here.

The skill is the only writer for these files. Hand-editing them
is permitted but unusual; the skill rewrites STATUS on every
update and treats unknown-shape entries as opaque pass-through.

### Drift-handling discipline during execution

When the executor encounters drift between the plan or PROPOSAL
as written and what's actually achievable / sensible, four paths
apply, classified first by which file the drift is in (PROPOSAL.md
is versioned; the plan is not), then by blocking vs non-blocking:

| Drift kind | Action | Cost |
|---|---|---|
| **PROPOSAL.md drift** (PROPOSAL.md text must change to match reality / decisions) | Halt; open a formal `vNNN/` revision via the bootstrap skill's halt-and-revise walkthrough; re-freeze; resume | High |
| **Plan-only drift** (PROPOSAL.md is unaffected; plan text needs correction) | Bootstrap skill's Case-B direct-fix gate: present finding to user via AskUserQuestion, edit + commit + `decisions.md` entry. Never enters `open-issues.md` | Low |
| **Non-blocking, pre-Phase-6** (drift in executor interpretation, neither plan nor PROPOSAL.md text needs changing yet) | Append to `bootstrap/open-issues.md` with disposition `defer-to-spec-propose-change`; carry the executor's interpretation forward | Low |
| **Non-blocking, post-Phase-6** | File a propose-change against `SPECIFICATION/` immediately (the dogfooded mechanism is now live) | Native plan mechanism |

The deferral row is the steady-state mechanism for executor-
interpretation drift during execution. PROPOSAL.md drift is
always blocking and produces a vNNN snapshot; plan-only drift is
always direct-fixed via the user-gated Case-B flow; only
executor-interpretation drift accumulates in
`bootstrap/open-issues.md`. Drain `bootstrap/open-issues.md`
post-Phase-6 by filing one propose-change per entry against the
seeded `SPECIFICATION/`, marking each entry resolved in the log
as its propose-change lands.

### Why a skill and not just files

The skill keeps the user from having to track which phase they're
on, which sub-step is next, and what the exit-criterion check
command is. It also enforces the never-auto-advance gate at
phase boundaries — by virtue of being an AskUserQuestion in the
loop, it cannot be silently skipped. Hand-managing the same
state across multi-week, multi-session bootstrap execution would
work in principle but reliably bleeds context every session
boundary. The skill is the cheapest way to keep state and
discipline coherent.

### Why throwaway

After Phase 10 lands `v1.0.0`, the entire `bootstrap/` directory
is archived (recommended: `brainstorming/bootstrap-archive/`) or
deleted. The production livespec plugin under `.claude-plugin/`
does NOT depend on the bootstrap skill, and the bootstrap skill
does NOT export anything reusable. Once livespec is dogfooding
itself via its own SPECIFICATION/-driven loop, the scaffolding
has no further role.

---
