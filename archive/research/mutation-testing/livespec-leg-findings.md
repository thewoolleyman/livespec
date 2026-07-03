# livespec keystone leg (livespec-mutreal.1) — execution findings

Implementation pass for epic item **livespec-mutreal.1** (the keystone:
make mutation testing actually functional in the livespec repo). This
addendum records what was VALIDATED end-to-end, the MEASURED kill rate, the
exact `mutants/` layout that produced real verdicts, and a NEW cross-repo
blocker the design pass did not anticipate. It complements `plan.md` (the
design pass); it does not supersede it.

## TL;DR

- The two-layer nested-layout diagnosis in `plan.md` §1.2 is CONFIRMED and
  the fix WORKS. Mutant keys now equal module names (Layer B), and the
  paired parse+validate suite collects cleanly (Layer A).
- **Measured kill rate: 90.55% — 201 mutants, 182 killed, 19 survived, 0
  timeout/suspicious/skipped.** Above the 80% floor.
- **NEW BLOCKER (not in `plan.md`): the shared `check_mutation` cannot
  consume mutmut 3.2.3's output.** `check_mutation._parse_mutmut_results`
  scans for `Killed:` / `Total:` text lines; mutmut 3.2.3's `results`
  command emits NEITHER (it prints only the surviving mutants, one
  `<key>: survived` line each, with no summary; killed mutants are
  suppressed unless `--all`). So the shared check parses `(killed=0,
  total=0)`, hits its `total == 0 → return 0` branch, and stays a silent
  PASS even when 201 real verdicts exist. `plan.md` §1.1 asserted
  "`check_mutation` itself needs no change" — that is FALSE against the
  pinned mutmut 3.2.3. The gate cannot go green until `check_mutation` is
  taught mutmut-3.x's output format. That is product `.py` in
  livespec-dev-tooling (Red-Green-Replay there) — this leg did NOT make
  that change.

Because of the blocker, this leg ships the validated livespec-side pieces
(the `inspect.getsource` skip guard + the `[tool.mutmut]` nested-layout
documentation) as a DRAFT PR and does NOT commit a real baseline (a
non-placeholder `.mutmut-baseline.json` would be a value the current shared
check can never re-derive, so it would be immediately misleading).

## The validated `mutants/` layout (cwd = an import-root staging dir)

mutmut must run with cwd = a staging dir that is simultaneously the import
root AND carries the root-relative fixtures + ONLY the paired tests. The
layout that produced the 90.55% result:

```
<staging-root>/
  livespec/                      # full package copy: parse/+validate/ are the
                                 #   mutation targets; errors.py, types.py,
                                 #   context.py, __init__.py, schemas/ are the
                                 #   import closure for the paired tests
  .claude-plugin/
    scripts/livespec/schemas/    # validate fixtures read parents[3] /
                                 #   ".claude-plugin"/"scripts"/"livespec"/
                                 #   "schemas"/<name>.schema.json
    specification-templates/     # test_template_config reads parents[3] /
                                 #   ".claude-plugin"/"specification-templates"
  tests/
    conftest.py                  # the autouse GIT_* scrub fixture
    livespec/parse/              # paired parse tests (front_matter, jsonc,
                                 #   cross_repo)
    livespec/validate/           # paired validate tests
  _vendor -> .../scripts/_vendor # symlink; vendored returns/structlog/etc.
  pyproject.toml                 # [tool.mutmut] paths_to_mutate =
                                 #   ["livespec/parse","livespec/validate"];
                                 #   also_copy = ["livespec/__init__.py",
                                 #   "livespec/errors.py","livespec/types.py",
                                 #   "livespec/context.py","livespec/schemas",
                                 #   ".claude-plugin"]; pytest
                                 #   import-mode=importlib + pythonpath=[".","_vendor"]
```

Why a STAGING dir and not the real repo root or `.claude-plugin/scripts/`:

- From the **repo root**, `paths_to_mutate` would dot to
  `.claude-plugin.scripts.livespec.parse.X` (key mismatch, Layer B), and
  mutmut's unconditional copy of `Path('tests/')` would drag in the WHOLE
  `tests/` tree — including `tests/livespec/commands/` whose modules import
  source mutmut never copies → `ModuleNotFoundError` at collection → 0
  mutants (Layer A).
- From **`.claude-plugin/scripts/`**, the key matches and imports resolve,
  but there is no `tests/` under `scripts/`, so mutmut's auto-`Path('tests/')`
  copies nothing and the root-relative fixture reads
  (`parents[3] / ".claude-plugin" / ...`) cannot be reconstructed via
  `also_copy` (which copies paths RELATIVE TO CWD into `mutants/<same
  path>` — it cannot reach a sibling `.claude-plugin/` above the cwd).

A purpose-built import-root staging dir is the only layout that satisfies
all three constraints at once (key match + fixture reads + scoped tests).

## Reproduction (what was actually run)

cwd = staging root; `PYTHONPATH=<root>:<root>/_vendor`; the worktree venv's
`python -m mutmut run` then `python -m mutmut results`. The run reported the
emoji summary `201/201  🎉 182  🫥 0  ⏰ 0  🤔 0  🙁 19  🔇 0` at
~11 mutations/second. The paired suite (151 passed, 1 skipped — the guarded
getsource test) collects cleanly under `MUTANT_UNDER_TEST` set.

## The 19 surviving mutants

19 / 201 survived (kill rate 90.55%, comfortably above the 80% floor), so NO
gap-closing test backlog is warranted per the epic policy (`plan.md` §3) —
the survivors are recorded for the eventual baseline, not for immediate
remediation. Survivors cluster in `parse/front_matter.py`
(`_split_front_matter`, `_parse_quoted`, `_parse_value`) and
`validate/livespec_config.py` (`_build_spec_clis`). Capture the precise
survivor list from `mutmut results` when the baseline is committed (after
the `check_mutation` parser fix lands).

## Remaining work to make the gate GREEN (two parts, both out of this leg's
## "config + test-guard + baseline" scope)

1. **dev-tooling: teach `check_mutation` mutmut-3.x output.** Replace the
   `Killed:` / `Total:` line scan with parsing of mutmut 3.2.3's actual
   summary (the `run` emoji line `N/N  🎉 K ... 🙁 S ...`, or count
   `results --all` lines by `: killed` / `: survived`). Product `.py` →
   Red-Green-Replay in livespec-dev-tooling. This is the conditional
   `plan.md` §7 item 5 — and this leg is the EVIDENCE that promotes it from
   "hold as placeholder" to "required".
2. **livespec: a `check-mutation` recipe that runs mutmut from the staging
   root.** The shared `check_mutation` invokes `mutmut run`/`results` with
   `cwd = Path.cwd()` and writes the baseline to `cwd/.mutmut-baseline.json`.
   To run from a staging import-root without forking the shared check, the
   livespec `check-mutation` recipe must build the staging dir (above),
   invoke the check with that cwd, and relocate the captured baseline back
   to the repo root. Whether that staging construction belongs in the
   livespec recipe or in a shared `check_mutation` accommodation for
   nested-layout repos is an architecture call for the orchestrator — both
   nested-layout repos (livespec + impl-git-jsonl) need it, which argues for
   a shared accommodation over per-repo recipe duplication.

Until both land, `LIVESPEC_RUN_MUTATION=true just check` stays a silent
no-op (the engine produces real verdicts, but the shared check reads 0/0
and passes). The DRAFT PR carries the parts that are unambiguously
livespec-side and non-product-`.py`; it does NOT pretend the gate is green.
