# Hand-off: make core's release gate green (heading-coverage TODOs)

**Standing hand-off — do not delete until `check-no-todo-registry` is green
in release-gate mode.** Each session that advances this MUST refresh this
file and the beads state before stopping.

## State (2026-06-25)

core's `release-tag.yml` release gate runs `check-no-todo-registry`, which
fails while any `test: "TODO"` entry remains in `tests/heading-coverage.json`.
It does **not** block releases (the gate runs on `v*` tag push, after the
release publishes), but it leaves a red check on every release. The
maintainer **accepted the red gate** (2026-06-25) and wants it resolved ASAP.

Down from 14 → 10 → **5 remaining**. Resolved this session (all merged):
besm.3 (Behavior-clause → integration marker), besm.1 (Renderer
non-vendoring check, #587), besm.2 (CLI shape → `cli-explicit-project-root`
check, #592), B3 (Doctor disposition prose → five-option contract + test,
#593 — also fixed a real 3-vs-5 prose drift), arch-diagram single-source
for `## Contract + reference implementations architecture` (#594).

**Maintainer directive (2026-06-25): NO coverage escape hatch.** Each
remaining heading is either tested HERE (even in a mocked way) OR its real
test is added in the sibling repo that owns it (relocate). There is no
exemption sentinel and none will be added. Never force a heading green with
a fabricated or non-exercising test id.

Tracking: **`livespec-besm`** (P1) + children. The 3 original ready
children (`.1`/`.2`/`.3`) are **CLOSED**. New children below.

## Validated recipe — a new private dev-tooling check

`check + test + justfile + ci.yml + heading flip + Red→Green ritual`:

1. `dev-tooling/checks/<name>.py` — standalone module, structlog JSON to
   stderr (copy the config block from an existing check), reads `Path.cwd()`,
   `__all__: list[str] = []`, `if __name__ == "__main__": raise SystemExit(main())`.
2. `tests/dev-tooling/checks/test_<name>.py` — **in-process** (NOT subprocess
   — `check-tests-no-subprocess-spawn` forbids it): `monkeypatch.chdir(tmp_path)`
   + `capsys`, load via `importlib.util.spec_from_file_location`, `rc = module.main()`.
   Keyword-only `*,` params. Cover every branch (100% coverage gate).
3. `justfile`: add a `check-<slug>:` recipe near the other
   `uv run python3 dev-tooling/checks/...` recipes, AND add `check-<slug>` to
   the `check:` aggregate's **livespec-private block** (after the canonical
   block — `aggregate_completeness` requires extras after canonical), in
   alphabetical position.
4. `.github/workflows/ci.yml`: add the slug to the `check-metadata`
   `matrix.target` list (mirrors `check-behavior-scenario-link`).
5. `tests/heading-coverage.json`: flip the entry from `TODO` to the test id.
6. **Red→Green ritual** (a new dev-tooling check IS product `.py`): author
   the full GREEN state, run `just check-pre-commit` to confirm green
   (it validates 100% coverage). Then: copy the real impl aside; replace it
   with a **style-clean stub** (`def main() -> int: return 0`) so the
   fail-case tests genuinely ASSERT-fail; `git add` the TEST ALONE; commit
   `feat(dev-tooling): …` (hook records `TDD-Red-*`). Restore the real impl;
   `git add -A`; `git commit --amend --no-edit` (preserves Red trailers;
   hook records `TDD-Green-*`). Verify the final commit carries BOTH
   `TDD-Red-Test-File-Checksum:` and `TDD-Green-Verified-At:`. Push → PR →
   `gh pr merge <n> --auto --rebase`.

**Prose/JSON/test-only headings** (no product `.py`) skip the ritual: a
single commit with a non-red-intent subject (`docs:` / `test:` / `chore:`)
takes the suite-green leg (the test must already pass). `fix:`/`feat:`
declare red-intent and a passing test trips `test-passed-at-red`. Examples
this session: B3 (`docs(prose):`), arch-diagram (`test:`).

## Remaining 5 — beads work-items

1. **`## Reference discipline`** → **`livespec-e58y`** (P2). Author 2 NEW
   **doctor-static** checks (different pattern — `.claude-plugin/scripts/
   livespec/doctor/static/<name>.py`, registered in `static/__init__.py`
   `STATIC_CHECKS` + `APPLICABILITY_BY_TREE_KIND`, paired tests at
   `tests/livespec/doctor/static/test_<name>.py`):
   `doctor-no-cross-spec-reference` (a `SPECIFICATION/<file>.md` `§"…"`
   citation outside its own tree, except the `.livespec.jsonc`
   `external_references` allowlist, fails) and
   `doctor-no-spec-section-citation-in-code` (any source file under the impl
   tree / `skills/` with a `§"…"` heading-level spec citation fails;
   file-level refs are fine). Make e58y's acceptance flip the
   heading-coverage entry.
2. **`## Error path 3 — version-contiguity gap`** → **`livespec-besm.4`**
   (P1, ready). Implement the STUB fail arm of
   `doctor/static/version_contiguity.py` (`_evaluate` ignores `version_paths`
   and always passes — a real latent bug; the scenario can't fire) + a unit
   fail-arm test + an **integration-tier** e2e test modeled on
   `tests/e2e/test_doctor_fail_then_fix.py` (seed `history/v001/`+`v003/`,
   no `v002/`; assert doctor fails referencing v002). Product Red→Green.
3. **`## Workflow planes and the Planning Lane`** → **`livespec-besm.5`**
   (P2, ready). A terminology-guard test (console ≠ Driver) on core's own
   prose/diagrams — the section's only normative claim; rest is framing.
   **Weakest** of the set; keep the assertion honest (no false-positive NLP)
   or surface to the maintainer.
4. **`## Interactive dialogue ownership` + `## CLI end-to-end harness
   contract`** → **`livespec-besm.6`** (P2 epic). Genuinely sibling-owned
   (a core mock would be vacuous — the front-ends / driver-claude skills /
   dev-tooling harness are not in core). Add the real tests in
   `livespec-orchestrator-beads-fabro` (front-ends-don't-call-Driver) and
   `livespec-driver-claude` (the claude-CLI e2e harness, harness from
   `livespec-dev-tooling`); relocate each contract statement into the
   sibling spec; remove the core heading + heading-coverage entry via
   `/livespec:revise`. Cross-repo epic — file per-repo children in the
   sibling beads stores at pickup. Open sub-decision: relocate the contract
   text entirely vs keep a one-line core pointer.

## Done when

`LIVESPEC_FAIL_IF_HEADING_COVERAGE_TODOS_EXIST=true just check-no-todo-registry`
exits 0. Then close `livespec-besm` + remaining children and delete this file.

## Discipline

Worktree → PR → rebase-merge per repo; `mise exec -- git …`; never
`--no-verify`; new checks follow Red-Green-Replay; prose/JSON/marker/test-only
edits use a non-red-intent subject and skip the ritual. Never force a heading
green with a fabricated or non-exercising test id, and never add a coverage
exemption hatch.
