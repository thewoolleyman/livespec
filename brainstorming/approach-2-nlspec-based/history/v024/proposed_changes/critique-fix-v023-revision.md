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

## v024 companion-doc reconciliation (follow-up)

After the initial v024 commit (`351aa67`) landed, a sweep of
the live brainstorming/ tree found three companion-doc files
still using the pre-v024 "mise-pinned" framing for the dev
packages that v024 moved to uv-managed. Per the user's
"halt-and-revise on any inconsistency" principle, v024's scope
expanded to include companion-doc reconciliation, gated via
AskUserQuestion 2026-04-26 (option: "Expand v024 to also fix
companion docs"). The companion-doc edits do NOT change v024's
substantive decisions (D1-D7) — they propagate the "uv-managed"
framing into supporting material so PROPOSAL.md and its
companions are internally consistent at the v024 logical
version.

Files touched in the follow-up commit:

- **`deferred-items.md`** lines 282-311 — three bullet entries
  under §"task-runner-and-ci-config" → "v012 additions"
  describing hypothesis / hypothesis-jsonschema / mutmut /
  Import-Linter:
  - "Hypothesis + hypothesis-jsonschema mise pins (L12)" →
    "Hypothesis + hypothesis-jsonschema dev pins (L12;
    uv-managed per v024)"; body "`.mise.toml` adds ... NOT
    vendored in bundle; mise-pinned only" rewrites to
    "`pyproject.toml` `[dependency-groups.dev]` adds ... NOT
    vendored in bundle; uv-managed only (per v024; pre-v024
    framing was mise-pinned)".
  - "mutmut mise pin + release-gate workflow (L13)" →
    "mutmut dev pin + release-gate workflow (L13; uv-managed
    per v024)"; body updated analogously.
  - "Import-Linter mise pin + pyproject config" →
    "Import-Linter dev pin + pyproject config (...; uv-managed
    per v024)"; body updated analogously.
  - L15b-principle bullet "are mise-pinned only" →
    "are uv-managed only (per v024; pre-v024 framing was
    mise-pinned)".
  - Line 207's parenthetical "no new mise-pinned tool" is left
    unchanged — historical commentary about v018's scope, not
    a current claim about the system.

- **`python-skill-script-style-requirements.md`** lines
  1107-1145 — three §-blocks describing PBT and mutation
  testing:
  - §"Property-based testing for pure modules" intro
    paragraph "MPL-2.0; mise-pinned, NOT vendored" →
    "MPL-2.0; uv-managed per v024, NOT vendored"; first rule
    bullet "are mise-pinned in `.mise.toml` as test-time deps"
    → "are uv-managed (per v024) via `pyproject.toml`
    `[dependency-groups.dev]` as test-time deps".
  - §"Mutation testing as release-gate" intro "(MIT;
    mise-pinned, NOT vendored)" →
    "(MIT; uv-managed per v024, NOT vendored)"; first rule
    bullet "is mise-pinned in `.mise.toml` as a release-gate
    dep" → "is uv-managed (per v024) via `pyproject.toml`
    `[dependency-groups.dev]` as a release-gate dep".

- **`python-skill-script-style-requirements.md`** line 1774
  (canonical justfile target table) — `just check-tools` row
  description "Verify every mise-pinned tool" →
  "Verify every pinned tool ... — both mise-pinned binaries
  (`uv`, `just`, `lefthook`) and uv-managed Python deps from
  `pyproject.toml` `[dependency-groups.dev]` per v024".

The v024 PROPOSAL.md snapshot at `history/v024/PROPOSAL.md`
is unchanged by these edits (PROPOSAL.md was not re-touched in
the follow-up; the snapshot stays byte-identical to live
PROPOSAL.md). No paired plan edits needed: the plan does not
reference these specific companion-doc passages.

The follow-up commit is squashed-style: a single commit
`Revise proposal to v024 (cont): companion-doc UV reconciliation`
that lands the three companion-doc files plus the appended
section in this overlay file.

## v024 companion-doc reconciliation (round 2)

After the round-1 follow-up commit (`04272ef`) landed, the
bootstrap skill's mandatory consistency scan at the start of
Phase 1 sub-step 3 found five additional pre-v024 "mise-pinned"
framing slips in `python-skill-script-style-requirements.md`
that the round-1 sweep missed. Per the user's "halt-and-revise
on any inconsistency" principle (v024 origin) and the round-1
precedent, v024's scope expands again to land a round-2
companion-doc reconciliation, gated via AskUserQuestion
2026-04-26 (option: "Extend v024 with a second cont follow-up
(Recommended)"). Like round 1, these edits do NOT change v024's
substantive decisions (D1-D7) — they propagate the "uv-managed"
framing into supporting material so PROPOSAL.md and its
companions remain internally consistent at the v024 logical
version.

Files touched in the round-2 follow-up commit:

- **`python-skill-script-style-requirements.md`** lines 103-105
  (§"Interpreter and Python version") — the bullet "The
  `.mise.toml` at the repo root pins the developer and CI Python
  version to an exact 3.10+ release; developers use `mise install`
  to match" rewrites to "`​.python-version` at the repo root pins
  the developer and CI Python version to an exact 3.10.x release,
  managed by `uv python pin` per v024. `pyproject.toml`'s
  `[project.requires-python]` declares the same constraint.
  `.mise.toml` pins only the non-Python binaries (`uv`, `just`,
  `lefthook`); developers run `mise install` then `uv sync
  --all-groups` to match." Per v024 D1-D2.

- **`python-skill-script-style-requirements.md`** line 1000
  (§"Linter and formatter" intro) — "`ruff` ... Pinned via mise."
  rewrites to "`ruff` ... Uv-managed per v024 via `pyproject.toml`
  `[dependency-groups.dev]`." Per v024 D4.

- **`python-skill-script-style-requirements.md`** line 1066
  (§"Testing" intro) — "Tests use **`pytest`** with mandatory
  plugins `pytest-cov` and `pytest-icdiff`. Pinned via mise."
  rewrites to "Tests use **`pytest`** with mandatory plugins
  `pytest-cov` and `pytest-icdiff`. Uv-managed per v024 via
  `pyproject.toml` `[dependency-groups.dev]`." Per v024 D4.

- **`python-skill-script-style-requirements.md`** lines
  1710-1714 (§"Dev tooling and task runner" bullet list) —
  "`.mise.toml` pins every dev tool listed in PROPOSAL.md
  §'Runtime dependencies — Developer-time dependencies.' Single
  source of truth lives in PROPOSAL.md (v013 C2); this document
  does NOT duplicate the enumeration to eliminate drift risk."
  rewrites to "`.mise.toml` pins the non-Python binaries (`uv`,
  `just`, `lefthook`) listed in PROPOSAL.md §'Runtime
  dependencies — Developer-time dependencies.' Per v024, the
  Python dev packages in that same PROPOSAL.md section are
  uv-managed via `pyproject.toml` `[dependency-groups.dev]`
  (single source of truth still lives in PROPOSAL.md per v013
  C2; this document does NOT duplicate the enumeration to
  eliminate drift risk)." Per v024 D4 + the mise/uv split
  established in D1-D2.

- **`python-skill-script-style-requirements.md`** lines
  1724-1727 (§"Dev tooling and task runner" → "First-time
  bootstrap" paragraph) — "**First-time bootstrap:** `mise
  install` then `just bootstrap`." rewrites to "**First-time
  bootstrap:** `mise install`, then `uv sync --all-groups` (per
  v024; resolves Python dev deps into a project-local `.venv`
  and commits `uv.lock`), then `just bootstrap`." Per v024 D5
  (uv.lock committed; project-local `.venv`).

The v024 PROPOSAL.md snapshot at `history/v024/PROPOSAL.md`
remains byte-identical (PROPOSAL.md was not re-touched). No
paired plan edits needed: the plan's Phase 1 entries already
cite v024 explicitly and the canonical bootstrap order
(`mise install` then `uv sync --all-groups` then
`just bootstrap`) is already accurate in Phase 1's exit
criterion.

The round-2 follow-up commit is squashed-style: a single commit
`Revise proposal to v024 (cont 2): companion-doc UV reconciliation (round 2)`
that lands the style-doc edits plus the appended section in
this overlay file.

## v024 companion-doc reconciliation (round 3)

Round 2 surfaced UV-framing slips. Round 3 surfaces an unrelated
companion-doc gap caught by the bootstrap skill's pre-execution
scan at the start of Phase 1 sub-step 4 (justfile authoring):
the style doc's canonical target table at §"Enforcement suite —
Canonical target list" is missing two rows that the plan calls
out by name. Plan Phase 1 sub-step 4 enumerates `just
check-heading-coverage` and `just check-vendor-manifest` as part
of the canonical target list, and plan Phase 4 enumerates the
underlying enforcement scripts (`heading_coverage.py` and
`vendor_manifest.py`) with substantive bodies. The style doc
table lists every other check the plan calls for but missed
these two. Per the user's "halt-and-revise on any inconsistency"
principle and the rounds 1-2 precedent, the style doc gets
two new rows to bring the table back into sync with the plan.
PROPOSAL.md is unaffected (no PROPOSAL.md text references either
target). Gated via AskUserQuestion 2026-04-26 (option: "Extend
v024 with round 3").

Files touched in the round-3 follow-up commit:

- **`python-skill-script-style-requirements.md`** §"Enforcement
  suite" → "Canonical target list" — two new rows inserted
  between the existing `check-claude-md-coverage` and
  `check-no-direct-tool-invocation` rows. Row bodies sourced
  verbatim from plan Phase 4's enumeration of
  `heading_coverage.py` and `vendor_manifest.py`:

  - `just check-heading-coverage` — "Validates that every `##`
    heading in every spec tree — main + each sub-spec under
    `SPECIFICATION/templates/<name>/` — has a corresponding
    entry in `tests/heading-coverage.json` whose `spec_root`
    field matches the heading's tree. Tolerates an empty `[]`
    array pre-Phase-6, before any spec tree exists; from Phase
    6 onward emptiness is a failure if any spec tree exists."

  - `just check-vendor-manifest` — "Validates `.vendor.jsonc`
    against a schema that forbids placeholder strings — every
    entry has a non-empty `upstream_url`, a non-empty
    `upstream_ref`, a parseable-ISO `vendored_at`, and the
    `shim: true` flag is present on `typing_extensions` and
    absent on every other entry."

The v024 PROPOSAL.md snapshot at `history/v024/PROPOSAL.md`
remains byte-identical (PROPOSAL.md was not re-touched). No
paired plan edits needed: the plan's enumeration of these
targets in Phase 1 sub-step 4 and Phase 4 already correctly
references them — the style doc table was the lagging artifact.

The round-3 follow-up commit is squashed-style: a single commit
`Revise proposal to v024 (cont 3): companion-doc UV reconciliation (round 3)`
that lands the style-doc edits plus the appended section in
this overlay file.

## v024 companion-doc reconciliation (round 4)

Round 4 surfaces an off-by-one count slip in coordinated text
between the plan and the style doc, caught by the bootstrap
skill's pre-execution scan at the start of Phase 1 sub-step 3
(pyproject.toml authoring) when sourcing the `[tool.pyright]`
strict-plus diagnostic list. Plan line 523 says "the six
strict-plus diagnostics" but enumerates seven; style doc line
758 likewise says "These six diagnostics are above the strict
baseline" but enumerates seven below at lines 761-784. The
list-of-seven is the substantive enumeration in both docs;
"six" is a count word slip in both. PROPOSAL.md does not
carry a count (only references "v012 L1 + L2 strict-plus
diagnostics manually enabled"), so PROPOSAL.md is unaffected.
Gated via AskUserQuestion 2026-04-26 (option: "List of 7 is
authoritative; fix the count to 'seven' (Recommended)").

Files touched in the round-4 follow-up commit:

- **`python-skill-script-style-requirements.md`** line 758
  (§"Type safety" intro to the strict-plus diagnostic list) —
  "These six diagnostics are above the strict baseline" rewrites
  to "These seven diagnostics are above the strict baseline".
  No body changes; the seven enumerated bullets at lines
  761-784 remain unchanged.

The paired plan edit at
`PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md` line 523 ("the
six strict-plus diagnostics" → "the seven strict-plus
diagnostics") lands as a separate Case-B plan-fix commit
(plan is unversioned per the v018-rule-refactor decision; plan
edits do not enter v024's overlay record). The two commits
together resolve the count slip across both docs.

The v024 PROPOSAL.md snapshot at `history/v024/PROPOSAL.md`
remains byte-identical (PROPOSAL.md was not re-touched).

The round-4 follow-up commit is squashed-style: a single commit
`Revise proposal to v024 (cont 4): companion-doc strict-plus count fix (round 4)`
that lands the style-doc edit plus the appended section in this
overlay file.
