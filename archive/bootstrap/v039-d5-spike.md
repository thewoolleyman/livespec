# v039 D5 spike — pytest-cov path-scoped instrumentation

**Date:** 2026-05-04
**Outcome branch:** (a) — configuration knob found; D3 falls into the
"path-scoped runs work via post-hoc include filter" shape, NOT the
"full suite + post-hoc filter" fallback. Wall-clock target (under 10
seconds for a typical single-file pair) is met empirically: ~4 seconds
on this machine for `tests/dev-tooling/checks/test_all_declared.py`
exercising `dev-tooling/checks/all_declared.py`.

## Reproduction

```sh
$ uv run pytest --cov=dev-tooling/checks/all_declared --cov-branch \
    tests/dev-tooling/checks/test_all_declared.py
...
6 passed in 5.48s
CoverageWarning: Module dev-tooling/checks/all_declared was never
imported. (module-not-imported)
CoverageWarning: No data was collected. (no-data-collected)
FAIL Required test coverage of 100.0% not reached. Total coverage: 0.00%
```

Reproduced as advertised: 0% despite the test (which spawns the impl
via `subprocess.run` with `cwd=tmp_path`) clearly exercising it.

## Root cause

Coverage parses `--cov=<arg>` per `pytest_cov.embed.init()`'s
`coverage.Coverage(source=cov_source.split(os.pathsep), ...)`. The
`source=` parameter accepts EITHER:

- A directory path (resolved relative to current working directory at
  Coverage construction time), OR
- A dotted Python module name.

Three failure modes appear:

1. **`--cov=dev-tooling/checks/all_declared`** — no `.py` suffix, not
   a directory. Coverage falls through to "module name"
   interpretation, can't import `dev-tooling.checks.all_declared`
   (the dir has no `__init__.py`, AND `dev-tooling` has a hyphen
   which isn't a valid Python module-name character anyway), warns
   `module-not-imported`, records nothing → 0%.
2. **`--cov=$(pwd)/dev-tooling/checks/all_declared.py`** — the `.py`
   suffix means the path isn't a directory. Same fallthrough → 0%.
3. **`--cov=dev-tooling/checks` (relative)** — coverage stores `source`
   as the relative path. The pytest-cov `.pth` startup hook (loaded
   in EVERY subprocess via the `COV_CORE_*` env-var protocol)
   constructs `coverage.Coverage(source=["dev-tooling/checks"], ...)`
   inside the subprocess. The subprocess runs with `cwd=tmp_path`
   (the test's pytest tmp_path fixture), so coverage's relative-path
   resolution treats `dev-tooling/checks` as
   `<tmp_path>/dev-tooling/checks` — which doesn't exist. No file
   under measurement matches the source filter, so subprocess
   coverage data is silently dropped on save.
4. **`--cov=$(pwd)/dev-tooling/checks` (absolute)** — works for
   subprocess instrumentation: the absolute source path resolves
   identically inside the subprocess regardless of cwd. The impl
   under test shows 100% coverage. BUT the report includes EVERY
   `.py` file in the directory; only the mirror-paired test exercises
   the one impl, so all sibling files show 0%, failing the
   `[tool.coverage.report].fail_under = 100` gate. Reporting needs
   to be filtered to the impacted impl files only.

`[tool.coverage.paths]` mapping was tested as a possible fix and does
NOT help: paths-mapping applies at `coverage combine` time to
canonicalize per-worker data files, NOT at measurement time to
canonicalize source-filter resolution. The subprocess hook still
constructs `Coverage(source=...)` with the unmapped (relative) path
before any combine happens.

## Working configuration

Drop the path-scoped `--cov=<path>` filter entirely. Run pytest with
bare `--cov` (which uses the pyproject.toml `[tool.coverage.run]`
omit-only blocklist — the existing config already correctly handles
subprocess instrumentation by NOT setting a relative `source`
allowlist). Then apply per-file scoping at REPORT time via
`coverage report --include=<impl_paths> --fail-under=100`.

```sh
# Step 1: collect coverage with no source-filter — full omit-only
# config from pyproject.toml. --cov-report= suppresses inline
# report; --cov-fail-under=0 suppresses the global 100% gate so
# the run doesn't fail on uncovered sibling files.
$ uv run pytest --cov --cov-branch --cov-report= --cov-fail-under=0 \
    tests/dev-tooling/checks/test_all_declared.py
6 passed in 3.97s

# Step 2: post-hoc per-file gate via --include filter on the
# already-written .coverage data file.
$ uv run coverage report \
    --include="dev-tooling/checks/all_declared.py" --fail-under=100
Name                                 Stmts   Miss Branch BrPart  Cover
--------------------------------------------------------------------------
dev-tooling/checks/all_declared.py      67      0     36      0   100%
--------------------------------------------------------------------------
TOTAL                                   67      0     36      0   100%
# exit code 0
```

When coverage IS missing, step 2 emits a non-zero exit (verified:
`exit=2` for partial coverage) AND surfaces the missing-line
locations in the report — the EXACT defensive-branch enumeration the
v039 D4 discipline calls for.

Total wall-clock: ~4 seconds for a single-file pair. Well under the
"under 10 seconds" D3 target.

## D3 contract (final)

`just check-coverage-incremental --paths <impl_paths>` runs:

```sh
# 1. Resolve mirror-paired tests for each impl path.
#    `dev-tooling/checks/<name>.py`         → `tests/dev-tooling/checks/test_<name>.py`
#    `.claude-plugin/scripts/livespec/<sub>/<name>.py`
#                                            → `tests/livespec/<sub>/test_<name>.py`
#    `.claude-plugin/scripts/bin/<name>.py` → `tests/bin/test_<name>.py`
#    (per v033 D1 mirror-pairing rules)
#
# 2. Run pytest with full coverage, no source filter, no inline gate:
uv run pytest --cov --cov-branch --cov-report= --cov-fail-under=0 \
    <resolved_test_paths...>
#
# 3. Apply the per-file 100% gate via include filter:
uv run coverage report --include=<impl_path_1>,<impl_path_2>,... \
    --fail-under=100
```

Wall-clock for typical single-pair: ~4 seconds (pytest ~4s, coverage
report ~0.1s).

The implementation script lives at
`dev-tooling/checks/check_coverage_incremental.py` and the recipe at
`justfile` `check-coverage-incremental:`. The script:

- Parses `--paths <p1> <p2> ...` argv (positional after the flag).
- For each `<p>`, computes the mirror-paired test path per the v033
  D1 mapping table; bails if any test file is missing.
- Composes the pytest invocation per step 2 above.
- Subprocess-runs pytest. If it exits non-zero, surface the failure
  (test failures, not coverage gaps).
- Subprocess-runs `coverage report --include=...`. If it exits
  non-zero, surface the coverage gap with the missing-line list per
  v039 D4's "defensive-branch enumeration via missing-line list"
  expectation.
- Exits 0 only on both steps clean.

## Notes on `-n auto` for D3

`pytest -n auto` (xdist) was tested and works correctly with this
contract — coverage data from xdist workers auto-combines into a
single `.coverage` file. HOWEVER, for SINGLE-test-file invocations
(the typical incremental case), xdist's worker-startup overhead
dominates and INCREASES wall-clock from ~4s to ~7.4s. Therefore
`check-coverage-incremental` should NOT pass `-n auto` by default;
xdist parallelism is reserved for the full-suite `check-coverage`
target (D2's win).

## Style-doc edit needed

The placeholder language for `check-coverage-incremental` row in
`python-skill-script-style-requirements.md` §"Canonical target list"
gets replaced with the finalized contract above. Per the v039 D5
deferred-spike entry's acceptance criteria, this is a single-line
companion-doc edit — no v040 codification needed because v039 D3
already authorizes the contract.
