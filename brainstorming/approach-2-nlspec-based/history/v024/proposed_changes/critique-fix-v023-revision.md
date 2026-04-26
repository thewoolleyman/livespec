# v024 — critique-fix overlay against v023

## Origin

v024 lands as a direct critique-fix during Phase 1 sub-step 1 of
the in-flight bootstrap. The user, on inspecting the executor's
draft `.mise.toml`, observed that PROPOSAL.md §"Developer-time
dependencies (livespec repo only)" specifies the dev-tool list as
"managed via mise" without naming the underlying Python toolchain
manager. The executor had reflex-defaulted to mise's `pipx:`
backend; the user corrected: UV (astral-sh/uv) is the modern
Python toolchain manager and should be specified explicitly so
no future executor (LLM or human) reaches for pipx, poetry, or
pip-tools by default.

The bootstrap skill's consistency-scan rule (Case A — PROPOSAL.md
drift is auto-blocking) routed the gap directly into the
halt-and-revise walkthrough; this file is the resulting overlay.

This overlay records one architectural decision (UV as the Python
toolchain manager, with mise's role narrowed to non-Python
binaries) and its paired PROPOSAL.md and plan-text edits.

## Decisions captured in v024

1. **UV is livespec's Python toolchain manager.**
   `uv` (astral-sh/uv) manages the Python interpreter version
   (`uv python pin`) and every Python package the enforcement
   suite requires (`pytest`, `pytest-cov`, `pytest-icdiff`,
   `hypothesis`, `hypothesis-jsonschema`, `mutmut`,
   `import-linter`, `ruff`, `pyright`). Python packages are
   declared in `pyproject.toml` `[dependency-groups.dev]` and
   installed via `uv sync --all-groups` (or
   `uv sync --group dev`), which produces a reproducible
   project-local `.venv`. Rationale: a single Python-toolchain
   authority is cleaner than mixing mise-pipx-pip approaches;
   UV is the 2026 idiomatic default; lockfile-backed reproducible
   installs (`uv.lock`) match the spirit of the existing
   exact-version-pinning discipline. The user-provided principle
   verbatim: "UV is the modern tool that should be used for the
   entire Python toolchain."

2. **Mise's role narrows to non-Python binaries.** `.mise.toml`
   pins `uv`, `just`, `lefthook` only — three non-Python
   binaries. Mise no longer pins Python itself or any Python
   package. `mise install` provides the binaries; `uv sync`
   provides Python and Python packages. `python` no longer
   appears in `.mise.toml`. Rationale: with UV as the Python
   toolchain authority, mise pinning Python would be a redundant
   second source of truth that could drift; pinning Python in
   `pyproject.toml` `[project.requires-python]` plus
   `.python-version` (managed by `uv python pin`) is the single
   source of truth.

3. **First-time bootstrap sequence updated.** The two-command
   bootstrap (`mise install` then `just bootstrap`) becomes a
   three-step sequence: `mise install` (binaries), `uv sync
   --all-groups` (Python + Python deps), `just bootstrap`
   (lefthook install + other one-time setup). `just bootstrap`
   may invoke `uv sync` itself for ergonomics, but the
   conceptual step ordering is mise → uv → just.

4. **Vendored-libs license policy framing unchanged.** The MPL-2.0
   acceptance for `hypothesis` (PROPOSAL.md §566-575) was framed
   as "acceptable for mise-pinned dev-time deps". After v024,
   `hypothesis` is uv-managed, not mise-pinned; the framing
   updates to "acceptable for uv-managed dev-time deps" but the
   policy itself (vendored-libs license restriction MIT/BSD/
   Apache-2.0 does NOT apply to non-vendored uv-managed deps) is
   unchanged. Same logic applies to `mutmut`, `import-linter`,
   etc.

## PROPOSAL.md changes

Touchpoints in `brainstorming/approach-2-nlspec-based/PROPOSAL.md`:

- **§"Developer-time dependencies (livespec repo only)"** (lines
  534-545) — rewrite the opening paragraph to name UV as the
  Python toolchain manager and narrow mise's role:
  > Every tool the enforcement suite requires is managed by a
  > combination of `mise` ([github.com/jdx/mise](https://github.com/jdx/mise))
  > and `uv` ([github.com/astral-sh/uv](https://github.com/astral-sh/uv)),
  > pinned to exact versions in committed configs at the livespec
  > repository root. **Mise pins non-Python binaries only:**
  > `uv` itself, `just`, `lefthook` — recorded in `.mise.toml`.
  > **UV pins Python and every Python package:** the interpreter
  > version (recorded in `pyproject.toml`
  > `[project.requires-python]` + `.python-version`), and the dev
  > packages `ruff`, `pyright`, `pytest`, `pytest-cov`,
  > `pytest-icdiff`, `hypothesis`, `hypothesis-jsonschema`,
  > `mutmut`, `import-linter` — recorded in `pyproject.toml`
  > `[dependency-groups.dev]` and installed into a project-local
  > `.venv` via `uv sync --all-groups`. Running `mise install`
  > followed by `uv sync --all-groups` followed by `just bootstrap`
  > (which executes `lefthook install` and any other one-time setup)
  > produces a ready-to-run environment. Developer tooling is NOT
  > installed into user projects; it is purely livespec-maintainer-
  > facing.

- **§"Developer-time dependencies"** (lines 566-595) — language
  update: "v012-added dev tools (mise-pinned, NOT vendored in the
  bundle)" becomes "v012-added dev tools (uv-managed, NOT vendored
  in the bundle)". Each per-tool blurb keeps its content but the
  framing pivots from "mise-pinned" to "uv-managed". The MPL-2.0
  acceptance language for `hypothesis` (lines 572-575) updates
  "acceptable for mise-pinned dev-time deps" to "acceptable for
  uv-managed dev-time deps".

- **§"Developer-time dependencies"** (lines 590-595) — opening
  sentence "These are mise-pinned because they are test-time /
  dev-tool-only deps" becomes "These are uv-managed because they
  are test-time / dev-tool-only deps".

- **§"Developer-time dependencies"** (lines 596-600) — last
  paragraph "`typing_extensions` is NOT in this mise-pinned list"
  becomes "`typing_extensions` is NOT in this uv-managed list".

- **§"Bundle contents are runtime-only"** (line 346) — directory
  list "`justfile`, `.mise.toml`, `lefthook.yml`,
  `.github/workflows/`" extends to also mention `pyproject.toml`'s
  dependency-groups role (already mentioned in §3440 directory
  diagram; this bullet is fine as-is, no edit needed). NO EDIT.

- **§"Developer tooling layout" directory diagram** (line 3437) —
  current entry:
  > `.mise.toml` (pins python3 >=3.10, just, lefthook, pyright,
  > ruff, pytest, pytest-cov, pytest-icdiff, hypothesis,
  > hypothesis-jsonschema, mutmut, import-linter —
  > typing_extensions is vendored per v013 M1, NOT mise-pinned)

  becomes:
  > `.mise.toml` (pins `uv`, `just`, `lefthook` — non-Python
  > binaries only; Python and Python deps are uv-managed via
  > `pyproject.toml` `[dependency-groups.dev]` per v024)

  And `pyproject.toml` entry (line 3440) extends "ruff + pyright +
  pytest + coverage + import-linter config" with "+
  `[project.requires-python]` (Python version pin) +
  `[dependency-groups.dev]` (uv-managed dev tools per v024)".

  And a new entry: `.python-version` (uv-managed Python pin per
  v024; companion to `pyproject.toml` `[project.requires-python]`).

  And a new entry: `uv.lock` (UV lockfile recording exact
  resolved versions of every dev dep per v024).

- **§"Key conventions" first-time-bootstrap bullet** (line 3462) —
  current text: "First-time bootstrap: `mise install` then `just
  bootstrap`. `just bootstrap` runs `lefthook install` (registers
  git hooks) and any other one-time setup." Becomes:
  > **First-time bootstrap:** `mise install` then `uv sync
  > --all-groups` then `just bootstrap`. `just bootstrap` runs
  > `lefthook install` (registers git hooks) and any other
  > one-time setup.

- **§"Key conventions" Python-pinning bullet** (line 3467-3469) —
  current text: "Python is pinned to a specific 3.10+ release in
  `.mise.toml`". Becomes:
  > **Python is pinned to a specific 3.10+ release** in
  > `pyproject.toml` `[project.requires-python]` and
  > `.python-version` (uv-managed per v024) so developers and CI
  > run the same Python version.

- **§"Key conventions" tool-dependency-management line** (line
  3485) — current text: "tool-dependency management via mise"
  becomes "tool-dependency management via mise (binaries) + uv
  (Python and Python deps) per v024".

- **§"Definition of Done" item 12** (lines 3667-3695) — current
  parenthetical text "committed `.mise.toml` pinning every dev
  tool (including v012 additions: `hypothesis`, `hypothesis-
  jsonschema`, `mutmut`, `import-linter`; `typing_extensions` is
  vendored per v013 M1, NOT mise-pinned)" rewrites to:
  > committed `.mise.toml` pinning non-Python binaries (`uv`,
  > `just`, `lefthook`) per v024, with Python and the v012-added
  > dev packages (`hypothesis`, `hypothesis-jsonschema`, `mutmut`,
  > `import-linter`) plus `pytest`, `pytest-cov`, `pytest-icdiff`,
  > `ruff`, `pyright` declared in `pyproject.toml`
  > `[dependency-groups.dev]` and resolved by `uv sync` per v024;
  > `typing_extensions` is vendored per v013 M1, NOT in either
  > config

- **§"Definition of Done" item 12 NOTICES.md trailer** (line
  3694-3695) — current text "`typing_extensions` PSF-2.0 per
  v013 M1; mise-pinned dev tools are NOT in NOTICES.md" becomes
  "`typing_extensions` PSF-2.0 per v013 M1; mise-pinned binaries
  and uv-managed Python dev tools are NOT in NOTICES.md (per
  v024)".

- **Frozen-status header** (line 3) — current text
  "Frozen at v023" bumps to "Frozen at v024".

## Plan-level decisions paired with v024

The bootstrap plan is edited in the same commit:

- **Plan "Version basis" — active pointer bumps** (lines 138-141)
  — "PROPOSAL.md v023 is now the frozen basis ... Phase 0 freezes
  at v023" updated to point at v024 as the latest snapshot.
  Existing v023 lineage (line 140 "v023 is a critique-fix overlay
  against v022 with no PROPOSAL.md substance change") stays as
  historical narrative; v024 is described as a critique-fix
  overlay against v023 WITH PROPOSAL.md substance change (the UV
  decision).

- **Plan "Version basis" — v024 decision block** — new block
  appended after the v023 block summarizing v024 D1-D4 and
  pointing at this overlay.

- **Plan Phase 0 step 1** (lines 405-417) — byte-identity check
  reference bumped from `history/v023/PROPOSAL.md` to
  `history/v024/PROPOSAL.md`. Lineage description updated to:
  "v023 substance plus v024's UV-toolchain decision".

- **Plan Phase 0 step 2** (line 420) — frozen-status header
  literal bumps from "Frozen at v023" to "Frozen at v024".

- **Plan Execution-prompt block** (line 2082) — "Treat PROPOSAL.md
  v023 as authoritative" bumps to v024.

- **Plan Phase 1 first bullet** (lines 455-459) — current text:
  > `.mise.toml` pinning `python@3.10.x`, `just`, `lefthook`,
  > `ruff`, `pyright`, `pytest`, `pytest-cov`, `pytest-icdiff`,
  > `hypothesis`, `hypothesis-jsonschema`, `mutmut`,
  > `import-linter` to exact versions. (`typing_extensions` is
  > vendored, NOT mise-pinned.)

  rewrites to:
  > `.mise.toml` pinning `uv`, `just`, `lefthook` to exact
  > versions — non-Python binaries only, per v024. Python and
  > every Python dev dependency are managed by `uv` via
  > `pyproject.toml` (see next bullet).

- **Plan Phase 1 — new bullet** inserted immediately after the
  `.mise.toml` bullet:
  > `.python-version` recording the exact Python 3.10.x patch
  > (managed by `uv python pin`, per v024). `pyproject.toml`'s
  > `[project.requires-python]` declares the same.

- **Plan Phase 1 `pyproject.toml` bullet** (lines 460-504) —
  add a new sub-bullet after `[tool.importlinter]`:
  > `[project]` table with `name = "livespec"`,
  > `version = "0.0.0"` (placeholder; livespec is not published),
  > and `requires-python = ">=3.10,<3.11"` per v024. NO `[project]
  > .dependencies]` (livespec ships nothing as a runtime dep —
  > the bundle's `_vendor/` is the runtime).
  >
  > `[dependency-groups]` table with a `dev` group listing
  > `ruff`, `pyright`, `pytest`, `pytest-cov`, `pytest-icdiff`,
  > `hypothesis`, `hypothesis-jsonschema`, `mutmut`,
  > `import-linter` to exact versions per v024. UV resolves and
  > installs these into a project-local `.venv` via `uv sync
  > --all-groups`.

- **Plan Phase 1 exit criterion** (lines 571-575) — current text:
  > **Exit criterion:** `mise install` succeeds; `just bootstrap`
  > (which at this stage is a placeholder no-op per the deferral
  > above) succeeds; `just --list` shows every target from the
  > canonical table.

  rewrites to:
  > **Exit criterion:** `mise install` succeeds; `uv sync
  > --all-groups` succeeds and produces a project-local `.venv`
  > with the dev dep set; `just bootstrap` (placeholder no-op at
  > this stage) succeeds; `just --list` shows every target from
  > the canonical table.

- **Plan §"Preconditions"** (line 248) — current bullet "No
  `.mise.toml`, `justfile`, `lefthook.yml`, `pyproject.toml`,
  ..." extends to also mention `.python-version`, `uv.lock` as
  things-that-must-not-yet-exist before Phase 1.

- **Plan §"Tooling references" / any prose mentioning mise
  installs** — survey for "mise install" references; update to
  "mise install + uv sync" where the context is end-to-end
  bootstrap. Internal phase-test invocations stay as-is unless
  they need uv.

- **Plan Phase 11 grep (lines 1944-1948)** — current isolation
  grep includes `.mise.toml`. Add `pyproject.toml` to the grep
  target list (it's already there) and `.python-version` /
  `uv.lock` if those become bootstrap-isolation-relevant. NO
  EDIT — the grep is already pointed at `pyproject.toml` and
  the new files (`.python-version`, `uv.lock`) live at repo
  root and are out of the bootstrap-isolation scope.

- **Live PROPOSAL.md** — frozen-status header updated from
  "Frozen at v023" to "Frozen at v024" to match the bumped plan
  instruction. The v024 snapshot copies the post-bump live file.

## Why no formal critique-and-revise

A single uncontested architectural decision (UV as the Python
toolchain manager) gated via AskUserQuestion 2026-04-26. The
user already picked the "UV-managed Python, mise pins binaries
only" option from a two-option presentation; the decision is not
in dispute. Spinning up a full critique-and-revise paperwork
cycle to consider alternatives the user has already excluded
would be ceremonial overhead disproportionate to scope. The
disciplined version-snapshot lives at `history/v024/PROPOSAL.md`;
this file documents the decision provenance.
