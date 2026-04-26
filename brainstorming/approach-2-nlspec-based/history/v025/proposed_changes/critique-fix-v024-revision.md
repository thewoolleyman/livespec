# critique-fix v024 → v025 revision

## Origin

Bootstrap-skill consistency scan at the start of Phase 2 sub-step
5 (vendoring) cloned `dry-python/returns` at tag `v0.25.0` to
execute the v018 Q3 initial-vendoring procedure for
`returns_pyright_plugin`. The plugin source could not be located
in the repo. A subsequent thorough upstream search
(`bootstrap/decisions.md` 2026-04-26 entry; sub-agent report
preserved in conversation transcript) confirmed two independent
falsifications of the v018 Q4 premise:

1. **Pyright has no plugin system, by deliberate maintainer
   decision.** Eric Traut (microsoft/pyright maintainer) rejected
   plugin support in microsoft/pyright#607 (2020), formalized that
   decision in 2021, and reaffirmed it in 2024. Pyright's
   `[tool.pyright]` config schema has no `pluginPaths` key — that
   field exists only in the user's PROPOSAL.md and pyproject.toml
   (authored at Phase 1 sub-step 3 from the spec text), not in
   pyright's own configuration grammar. Pyright's strategy is
   declarative PEPs (PEP 681 `dataclass_transform`, etc.), not
   imperative plugins.

2. **dry-python/returns explicitly will not support pyright.**
   Issue dry-python/returns#1513 (Oct 2022) was closed same-day
   by maintainer sobolevn: *"I don't think it is possible,
   because we use way too many mypy plugins. And pyright does
   not support them."* Confirmed unchanged in dry-python/returns#2295
   (Nov 2025, still open). The dry-python org has 10 public
   repos; none mention pyright. Zero `pyright` references in the
   `returns` codebase. PyPI has no `returns-pyright-plugin` or
   similar package. The artifact `returns_pyright_plugin` does
   not exist anywhere on GitHub or PyPI except in this repo's
   own files.

The v018 Q4 author appears to have inferred false parity from
the existence of `returns/contrib/mypy/` and assumed a pyright
counterpart must exist (or could be assumed into existence). Both
the upstream artifact AND pyright's plugin mechanism were
invented; neither is real.

This is Case A (PROPOSAL.md drift) auto-blocking per the
bootstrap skill rule, requiring a v025 PROPOSAL.md snapshot. A
companion cosmetic license-label correction (BSD-2 → BSD-3-Clause
for `returns`, surfaced from the same scratch clone's
`pyproject.toml`) rides along in this revision per the
"one-finding-per-gate discipline" rule (the cosmetic correction
is not its own blocker; it sweeps with whatever substantive
revision happens for the real reason).

## Decisions captured in v025

### D1 — Drop `returns_pyright_plugin` from the canonical vendored-libs list; remove `pluginPaths` claim from `[tool.pyright]`; update typechecker rationale

**Decision.** The v018 Q4 closure of the
`returns-pyright-plugin-disposition` deferred item is rescinded.
Re-close the deferred item in v025 with the revised disposition:
**no pyright plugin is vendored, because no such plugin exists
upstream and pyright does not support plugins by design.** The
canonical vendored-libs list shrinks from six entries to five
(`returns`, `fastjsonschema`, `structlog`, `jsoncomment`,
`typing_extensions`). PROPOSAL.md's `[tool.pyright]` reference
to `pluginPaths = ["_vendor/returns_pyright_plugin"]` is struck;
that key is invalid in pyright's config schema regardless of
what the spec said.

**Rationale.** The v018 Q4 rationale for vendoring the plugin
was to provide pyright strict-mode `Result` / `IOResult`
inference akin to what dry-python's mypy plugin offers for mypy.
With the upstream + pyright realities documented in §"Origin"
above, that rationale is unrealizable. The fallback that v018 Q4
named is the load-bearing one: **the seven strict-plus
diagnostics (v012 L1 + L2 manually enabled) provide the actual
guardrails against agent-authored-code failure patterns.**
`reportUnusedCallResult = "error"` in particular prevents silent
`Result` / `IOResult` discards — the main risk a plugin would
have addressed. Without the plugin, pyright will still type-check
`Result[T, E]` generic parameters via standard generic inference;
it will simply not flow-narrow as aggressively in `bind` chains
and pipeline composition. That is a one-time call-site annotation
friction (occasional explicit annotations or `cast()` calls at
combinator boundaries), not an ongoing safety regression. The
friction is bounded and visible: unnecessary casts get caught by
`reportUnnecessaryCast` (already enabled), and unnecessary
type-ignores by `reportUnnecessaryTypeIgnoreComment` (already
enabled), so the friction surfaces at the call site rather than
hiding in opaque `# type: ignore` debt.

The two rejected alternatives:

- **Switch typechecker to mypy.** Would reverse v018 Q4's
  pyright-not-mypy decision, conflict with the style-doc explicit
  non-goal "mypy compatibility is a non-goal", and lose the
  specific strict-plus diagnostics chosen for agent guardrails.
  Mypy has an official returns plugin (`returns.contrib.mypy.returns_plugin`),
  but the architectural premise of "deliberately chose pyright
  for the strict-plus guardrails" does not survive the swap.
  Larger PROPOSAL change in the wrong direction.
- **Switch to basedpyright.** Pyright fork; inherits the same
  no-plugins stance per microsoft/pyright#607's logic. Doesn't
  solve the inference problem.

**Source-doc impact list.**

- `PROPOSAL.md` line 100 (vendored-libs directory tree) — drop
  the `returns_pyright_plugin/` entry.
- `PROPOSAL.md` line 453-456 (vendoring section detail on the
  pyright plugin) — drop the entire paragraph; rewrite the
  preceding `returns` paragraph to stand alone without
  introducing the plugin.
- `PROPOSAL.md` line 3700-3708 (typechecker section) — strike
  the `pluginPaths` claim; update the rationale to drop the
  plugin justification while preserving the "pyright over
  basedpyright per v018 Q4" decision and the strict-plus
  diagnostic enumeration.
- `PROPOSAL.md` typechecker decision body (the v018 Q4 closure
  text) — re-close the `returns-pyright-plugin-disposition`
  deferred item with the v025 disposition (no plugin vendored;
  see §"Origin" above for upstream falsifications).

### D2 — Cosmetic: `returns` license is BSD-3-Clause, not BSD-2

**Decision.** Correct the license-label mismatch for the
`returns` library. Upstream `dry-python/returns` v0.25.0
`pyproject.toml` declares `license = "BSD-3-Clause"`; PROPOSAL.md
and downstream companion docs state BSD-2. The library is in
policy at either BSD-2 or BSD-3 (style doc line 133 explicitly
allows both BSD-2-Clause and BSD-3-Clause), so this is a
metadata correction with zero architectural implication.

**Rationale.** Cosmetic ride-along per the bootstrap skill's
"one-finding-per-gate discipline" — the label correction is not
its own blocker, but it sweeps cleanly into v025 because v025 is
already touching every doc that carries the wrong label.

**Source-doc impact list.**

- `PROPOSAL.md` line 99-100 (directory tree comment for
  `returns/`) — `BSD-2` → `BSD-3-Clause`.
- `PROPOSAL.md` line 453 (vendoring section detail) — fix the
  license citation if any.

## Plan-level decisions paired with v025

The plan is unversioned per the v018-rule-refactor decision; plan
edits do not enter v025's overlay record but ride in the same
commit as the v025 snapshot. Paired plan edits:

- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` §"Version basis"**
  — bump version label to v025; add decision summary for v025
  (D1: drop returns_pyright_plugin; D2: BSD-3 cosmetic).
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` Phase 0 step 1
  byte-identity check** — bump reference from v024 to v025.
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` execution prompt
  block** — bump the "Treat PROPOSAL.md vNNN as authoritative"
  line from v024 to v025.
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` Phase 1
  sub-step 3 (`pyproject.toml`)** — strike the `pluginPaths`
  bullet; update the pyright config description to drop the
  plugin reference; update the comment-block rationale.
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` Phase 1
  sub-step 9 (`.vendor.jsonc`)** — drop `returns_pyright_plugin`
  from the six-entry enumeration (now five entries); update
  Phase 2's placeholder-replacement note correspondingly.
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` Phase 1
  sub-step 11 (`NOTICES.md`)** — drop the
  `returns_pyright_plugin` entry from the six-library
  enumeration.
- **`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` Phase 2
  sub-step 5 (`.claude-plugin/scripts/_vendor/`)** — drop the
  `returns_pyright_plugin/` bullet from the vendoring sub-list;
  update the lib count.
- **Anywhere the plan or style doc cites
  `returns_pyright_plugin` or pyright `pluginPaths`** — strike
  the reference.

## Companion-doc + repo-state changes paired with v025

These are downstream of PROPOSAL.md but already-authored at
Phase 1 / Phase 2; they get edited in the same commit as the
v025 snapshot:

- **`python-skill-script-style-requirements.md`** — strike
  references to `returns_pyright_plugin` in the vendored-libs
  section (line 145-155 area), the pyright config section
  (line 750-752 area), and the vendor list (line 212/218 area).
- **`NOTICES.md`** — drop the `returns_pyright_plugin` entry
  (originally written at Phase 1 sub-step 11). Fix the
  `returns` license citation from `BSD-2-Clause` to
  `BSD-3-Clause`. Update the prologue's "six libraries" framing
  to "five libraries".
- **`.vendor.jsonc`** — drop the `returns_pyright_plugin`
  entry (originally written at Phase 1 sub-step 9). The file
  now holds 5 library entries.
- **`pyproject.toml`** — strike `pluginPaths = ["_vendor/returns_pyright_plugin"]`
  from `[tool.pyright]`; remove the leading-comment paragraph
  about the returns pyright plugin; update the v018 Q4
  authoritative-source citation in the comment header to
  reflect v025 closure of the `returns-pyright-plugin-disposition`
  deferred item.

## Why no formal critique-and-revise

This is a single substantive architectural decision (D1) plus a
single cosmetic ride-along (D2). The decision was already made
in conversation (the user reviewed the sub-agent's findings, the
three-option analysis, and the executor's recommendation, and
selected option (a) — drop the plugin — explicitly). No
option-picker discussion remains for the revision file to walk
through. Direct overlay matches the v022/v023/v024 precedent for
narrow single-architectural-decision fixes.
