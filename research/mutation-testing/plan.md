# Stand up functional mutation testing across the livespec family

Epic: **livespec-mutreal** — execution plan + child-item decomposition.

Mutation testing is NON-FUNCTIONAL family-wide today. This document is the
research/design pass: it diagnoses the root cause (a two-layer mutmut layout
bug in the nested-layout repos), proposes the per-repo `paths_to_mutate`,
fixes the baseline-capture policy, identifies the release-tag-workflow gaps,
and decomposes the work into filed child items. It does NOT implement the
fix (the epic spans 4 repos and needs sequencing).

The lever wiring already exists and is NOT re-litigated here:
`LIVESPEC_RUN_MUTATION` RUN/SKIP, livespec's `release-tag.yml`, and
`check_mutation`'s ratchet-with-80%-floor + first-run-captures-baseline
mechanics are all in place. This epic makes the underlying mutation ENGINE
actually run.

---

## 1. Current-state diagnosis

### 1.1 The shared `check_mutation` mechanics (already correct)

`check_mutation` lives in the shared library at
`livespec_dev_tooling.checks.check_mutation` and is wired into all 4 repos as
the `check-mutation` / `check-check-mutation` justfile targets. Its logic is
sound:

- **RUN/SKIP lever:** unset `LIVESPEC_RUN_MUTATION` → logs "skipped", exits 0
  (per-commit `just check` stays green). Set to non-empty (release-tag CI sets
  `"true"`) → runs `mutmut run` + `mutmut results`.
- **Ratchet-with-floor:** kill_rate MUST be `>= 80.0%` (hard floor) AND
  `>= recorded baseline` (no regression). Improvements above baseline rewrite
  the baseline.
- **First-run capture:** when `.mutmut-baseline.json` records
  `mutants_total: 0` (the placeholder), the check runs mutmut, saves the
  result as the new baseline, exits 0 — so the first release-tag run captures
  a real baseline without a hard fail.

**The silent no-op:** `_derive_exit_code` returns 0 unconditionally when
`total == 0` ("nothing to kill"). Every repo's mutmut run currently yields
**0 mutants** (see §1.2), so `check_mutation` has been a guaranteed PASS
that gates nothing. The committed `.mutmut-baseline.json` files are all the
`{"kill_rate_percent": 0.0, "mutants_surviving": 0, "mutants_total": 0}`
placeholder (impl-git-jsonl has no baseline file at all).

`check_mutation` itself needs **no change** — it is correct and will start
gating the moment mutmut produces real mutants.

### 1.2 The livespec mutmut layout bug — TWO layers (the keystone)

The epic framed this as `ModuleNotFoundError: No module named
'livespec.commands._next_ranking'`. That error is **real and reproducible**,
but it is only the FIRST of two layers. The deeper layer is a mutant-key vs.
module-name mismatch that `tests_dir`/path tuning alone cannot fix. Both stem
from one structural fact: **livespec's package lives at the nested path
`.claude-plugin/scripts/livespec/`, not at a flat import root or under
`src/`.** mutmut 3.2.3 assumes a flat-or-`src/` layout.

#### Layer A — `ModuleNotFoundError` (test-collection failure)

`[tool.mutmut]` sets:

```toml
paths_to_mutate = [
    ".claude-plugin/scripts/livespec/parse",
    ".claude-plugin/scripts/livespec/validate",
]
tests_dir = "tests"
```

mutmut 3.2.3 hard-copies the WHOLE `tests/` tree into `mutants/tests/`
(confirmed: `read_config()` in `mutmut/__main__.py` unconditionally appends
`Path('tests/')`, `Path('test/')`, `setup.cfg`, `pyproject.toml` to
`also_copy`; the `tests_dir` config key is a mutmut-2.x vestige and is
**ignored** in 3.x). It copies only `paths_to_mutate` source —
`parse/` + `validate/` — into `mutants/.claude-plugin/scripts/livespec/`,
NOT `commands/`, `io/`, `doctor/`, `schemas/`, or the package `__init__.py`.

When mutmut runs the stats pass it invokes `pytest -x -q` from inside
`mutants/` with no explicit paths, so pytest falls back to
`testpaths = ["tests"]` (copied from the repo `pyproject.toml`) and collects
the ENTIRE copied tree — including `tests/livespec/commands/`, whose modules
do `from livespec.commands._next_ranking import ...`. That source was never
copied, so collection dies with
`ModuleNotFoundError: No module named 'livespec.commands._next_ranking'`,
the stats pass returns non-zero, mutmut prints `failed to collect stats`,
and **0 mutants** are recorded → `total == 0` → placeholder baseline →
silent PASS.

Reproduced verbatim in a clean worktree (`mutmut run` →
`ERROR collecting tests/livespec/commands/test_next_ranking.py … E
ModuleNotFoundError: No module named 'livespec.commands._next_ranking'`).

#### Layer B — mutant-key vs. module-name mismatch (the deeper bug)

Even after fixing Layer A so the paired suite collects cleanly (152 paired
tests pass), **every mutant comes back "no tests" / unkillable.** Root cause,
confirmed in `mutmut/__main__.py`:

- mutmut derives each mutant's KEY from the **file path**, dotted, stripping
  only a literal `src.` prefix (`create_mutants_for_file`, line ~271):
  `str(filename)[:-suffixlen].replace(os.sep, '.')` →
  `.claude-plugin.scripts.livespec.validate.next_output.<fn>`.
- the runtime trampoline records test→function hits keyed by the **import
  module name** (`record_trampoline_hit(orig.__module__ + '.' + orig.__name__)`,
  line ~200) → `livespec.validate.next_output.<fn>`.

These two namespaces never intersect (`.claude-plugin.scripts.livespec.…`
vs. `livespec.…`), so no test is ever mapped to any mutant. Confirmed
empirically: instrumented module's `__module__` is `livespec.validate.
next_output`, while the mutant id is `.claude-plugin.scripts.livespec.
validate.next_output.x_validate_next_output`.

mutmut also only ever adds `mutants/src`, `mutants/source`, or `mutants/`
itself to `sys.path` (line ~1232) — never a nested `mutants/.claude-plugin/
scripts`. The nested layout is structurally unsupported.

### 1.3 The EXACT fix for the nested-layout repos (livespec + impl-git-jsonl)

**Run mutmut with cwd = the import root** (`.claude-plugin/scripts/`), so that
the file-path-dotted name equals the import module name AND `mutants/` on
`sys.path` makes the package importable. From that cwd:

- `paths_to_mutate = ["livespec/parse", "livespec/validate"]` → mutant key
  `livespec.parse.front_matter.<fn>` == runtime `__module__`. **Match.**
- `mutants/` lands on `sys.path`; `import livespec` resolves to the
  instrumented copy.
- mutmut's hard-copied `tests/` is whatever lives at `<cwd>/tests/`, so a
  small `mutmut`-scoped tests layout under the import root copies ONLY the
  paired tests, dodging Layer A.

**Validated end-to-end in the worktree** (cwd = `.claude-plugin/scripts/`,
`paths_to_mutate = ["livespec/parse"]`, paired parse tests only): mutmut
mapped **10 functions to tests** (was 0), and mutants returned REAL
killed/survived verdicts (mutation testing executing at ~9 mutants/sec) —
i.e. the engine is functional. Before the fix: `failed to collect stats`,
0 mutants. After: real verdicts.

**Concrete mechanism for the recipe.** Because `check_mutation` calls
`mutmut run` with `cwd = Path.cwd()` (the repo root) and `mutmut` reads
`[tool.mutmut]` from the cwd's `pyproject.toml`, the implementation needs ONE
of these (to be chosen at implementation time; recommend the first):

- **(Recommended) Drive mutmut from `.claude-plugin/scripts/`** via a tiny
  `mutmut`-only config rooted there (a `setup.cfg`/`pyproject` fragment under
  `.claude-plugin/scripts/` with `paths_to_mutate = livespec/parse,
  livespec/validate` and a `tests/` subtree containing only the paired
  parse+validate tests), and have the `check-mutation` recipe `cd` into that
  root before invoking mutmut. The baseline JSON stays at repo root (the
  recipe passes the path).
- **(Alternative) Make the file-path dotted name == module name by stripping
  the nested prefix** — not supported by mutmut config (only `src.` is
  stripped), so it would require a mutmut plugin/patch. Rejected: more
  fragile than relocating the cwd.

**Two instrumentation-fragility carve-outs** surfaced while validating the
paired suite under mutmut and MUST be handled in the livespec leg:

1. **Source-introspection test.**
   `tests/livespec/parse/test_front_matter.py::
   test_front_matter_module_declares_hkt_erosion_pragma` calls
   `inspect.getsource(front_matter)` and asserts the file's FIRST line is the
   HKT-erosion pragma. mutmut prepends its trampoline boilerplate to the
   instrumented copy, so the assertion fails during the (unmutated) stats/clean
   run → `failed to collect stats`. Fix: guard the test with
   `@pytest.mark.skipif(os.environ.get("MUTANT_UNDER_TEST"), …)` — mutmut sets
   `MUTANT_UNDER_TEST` in the environment for every run, so the test still runs
   normally under `just check` and only skips under mutation.
2. **Repo-root-relative fixture reads.** ~11 `tests/livespec/validate/test_*.py`
   anchor `Path(__file__).resolve().parents[3]` (= repo root) and read
   `.claude-plugin/scripts/livespec/schemas/*.schema.json` and
   `.claude-plugin/specification-templates/*/template.json`. Under mutmut these
   resolve into `mutants/…`, which only contains the copied subset. Fix: add the
   support closure to `also_copy` so the fixtures exist in `mutants/`:
   `livespec/__init__.py`, `errors.py`, `types.py`, `context.py`, `schemas/`,
   `_vendor/`, and `specification-templates/` (transitive closure verified:
   `parse/`+`validate/` import only `livespec.errors`/`types`/`schemas`; none
   reach into `io/`/`commands/`/`doctor/`).

These three (cwd relocation, the skipif guard, the also_copy closure) are the
complete, mechanical livespec fix.

### 1.4 The other 3 repos — config absent, layout varies

| Repo | Layout | Key-mismatch bug? | `[tool.mutmut]` | Baseline file | release-tag.yml |
|---|---|---|---|---|---|
| **livespec** | nested (`.claude-plugin/scripts/livespec/`) | YES (fix per §1.3) | present, broken | 0/0 placeholder | YES (sets `LIVESPEC_RUN_MUTATION=true`) |
| **livespec-dev-tooling** | flat (`livespec_dev_tooling/` at root) | NO | absent | 0/0 placeholder | NO |
| **livespec-impl-git-jsonl** | nested (`.claude-plugin/scripts/livespec_impl_git_jsonl/`) | YES (same as livespec) | absent | absent | NO |
| **livespec-runtime** | flat (`livespec_runtime/` at root) | NO | absent | 0/0 placeholder | NO |

The two **flat-layout** repos (dev-tooling, runtime) do NOT have the
key-mismatch bug — for them `paths_to_mutate` is relative to the repo root,
the dotted file path equals the module name, and `mutants/` on `sys.path`
resolves the package. They simply lack `[tool.mutmut]` config (mutation is a
no-op placeholder), so configuring `paths_to_mutate` is the whole fix. They
must still verify their paired tests have no source-introspection /
root-relative-fixture fragilities (audit during their legs).

All 4 repos already carry the shared `check-mutation` / `check-check-mutation`
justfile targets and `mutants/` is gitignored everywhere.

---

## 2. Per-repo `paths_to_mutate` proposal

Mirror livespec's choice: focus on **core pure-logic modules**, NOT the whole
package. Pure logic is the highest-value mutation target (deterministic,
no I/O, exhaustively unit-tested) and keeps runtime bounded.

| Repo | `paths_to_mutate` | Rationale |
|---|---|---|
| **livespec** | `livespec/parse`, `livespec/validate` (relative to `.claude-plugin/scripts/` cwd) | Existing choice — pure parsing + schema validation. Already correct in intent; only the layout/cwd is broken. |
| **livespec-dev-tooling** | `livespec_dev_tooling/config.py`, `livespec_dev_tooling/green_token.py`, `livespec_dev_tooling/red_leg_scope.py` (candidates; confirm at impl time) | Pure-logic check helpers. The `checks/` AST/text scanners and `cross_repo/` ref resolution are also candidates — pick the deterministic, heavily-unit-tested core, exclude subprocess/git-shelling `tdd_commit.py`, `parallel_check_dispatcher.py`, `fleet/`. **Open question** flagged in §6. |
| **livespec-impl-git-jsonl** | `livespec_impl_git_jsonl/spec_reader.py`, `livespec_impl_git_jsonl/_ids.py`, `livespec_impl_git_jsonl/types.py` (relative to `.claude-plugin/scripts/` cwd) | Pure modules: gap-detection spec reader, id minting, typed dataclasses. EXCLUDE `store.py` (touches `io/`) and `io/`, `commands/`, `migration/`. Same nested-layout fix as livespec applies. |
| **livespec-runtime** | `livespec_runtime/cross_repo` | The single pure-logic surface: the typed `DependsOnEntry` union + `resolve_ref` that doctor's cross-boundary invariants import. |

The exact module set for dev-tooling and the final pure/impure split for the
others must be confirmed during each repo's leg by reading the import-linter
contracts (where present) and running the paired tests under mutmut to catch
fragilities. The decomposition treats each repo's `paths_to_mutate` selection
as part of that repo's child item.

---

## 3. Baseline-capture, 80%-floor, under-floor-decision policy

The mechanics already exist in `check_mutation` (§1.1). The epic policy layered
on top:

1. **First real run captures the baseline.** With a functional engine, the
   first release-tag CI run on each repo flips the placeholder
   (`mutants_total: 0`) to a real `{kill_rate_percent, mutants_surviving,
   mutants_total}` and exits 0. That captured baseline is committed.
2. **80% hard floor.** Once captured, every subsequent run must keep
   `kill_rate >= 80.0` AND `>= baseline`. A repo whose first real run lands
   **below 80%** would, on the SECOND run, hard-fail the release gate.
3. **Under-floor → DECISION, not auto-backlog.** Per the epic: surface any
   repo whose captured kill_rate is `< 80%` for a gap-closing DECISION rather
   than auto-writing a large test backlog. Concretely, each repo's leg runs
   mutation locally (`LIVESPEC_RUN_MUTATION=true just check-mutation`),
   records the measured kill_rate in the child item, and:
   - `>= 80%`: commit the captured baseline; done.
   - `< 80%`: do NOT commit a baseline that would immediately gate red.
     Instead file a follow-up DECISION item ("repo X mutation kill-rate is
     N% < 80% — close gap by adding tests to survivors, or lower the floor
     for this repo, or narrow `paths_to_mutate`") and capture the baseline
     only after the decision. This keeps the first baseline honest and avoids
     committing a known-red gate.

Measuring the real kill_rate per repo is therefore a deliverable of each
repo's child item, feeding either a clean baseline commit or a surfaced
DECISION.

---

## 4. Release-tag workflow gaps

Only **livespec** has `release-tag.yml`. It runs on `push: tags: ['v*']`, sets
job-wide `env: LIVESPEC_RUN_MUTATION: "true"` (plus the two heading-coverage /
LLOC levers), and runs a matrix of release-gate targets including
`check-mutation`. The 3 siblings (dev-tooling, impl-git-jsonl, runtime) have
NO `release-tag.yml`.

**Gap:** add a `release-tag.yml` to each of the 3 siblings, modeled on
livespec's, scoped to the release-gate targets that repo actually has. At
minimum each sibling's workflow must set `LIVESPEC_RUN_MUTATION: "true"` and
run `just check-mutation` (or `check-check-mutation`) on tag push. Whether a
sibling also needs the heading-coverage / LLOC levers depends on which
release-gate targets it carries (audit per repo; do not blindly copy
livespec's matrix). Each sibling already has the shared `check-mutation`
target, so the workflow is the missing piece.

---

## 5. CI wiring of `LIVESPEC_RUN_MUTATION` per repo

The epic says "wire `LIVESPEC_RUN_MUTATION` into PR+master+release CI per
repo." The lever's semantics: unset → skip (cheap), set → run (slow). The
intended wiring, per the existing `check_mutation` self-management design:

- **Release-tag CI:** `LIVESPEC_RUN_MUTATION: "true"` — the strict gate
  (already done in livespec's `release-tag.yml`; add to each sibling's new
  workflow per §4).
- **PR + master CI:** `check-mutation` is NOT in `just check`, so it does not
  run per-commit. The lever stays UNSET on PR/master so the slow suite does
  not run on every push (mutation is gated by runtime cost, not severity).
  This matches the established pattern: mutation is a release-gate, not a
  per-commit check.

  Net: "wire into PR+master CI" means ensuring the lever is **deliberately
  unset** there (so `check-mutation`, if ever invoked, self-skips), and the
  authoritative run is the release-tag workflow. If a repo's CI explicitly
  invokes `check-mutation` outside release context, confirm the lever is unset
  so it self-skips rather than running unbounded mutation on every PR. No repo
  currently runs `check-mutation` in PR/master CI; the work is to NOT
  accidentally turn it on, and to document the release-tag workflow as the one
  place it runs.

---

## 6. Open questions

- **dev-tooling `paths_to_mutate` exact set.** dev-tooling has no
  parse/validate split and no import-linter pure-layer contract surfaced in
  its pyproject; the pure-logic core must be chosen by reading the modules.
  Candidates: `config.py`, `green_token.py`, `red_leg_scope.py`,
  `canonical_checks.py`, parts of `checks/` and `cross_repo/`. Confirm the
  deterministic, fully-unit-tested subset at impl time; exclude
  subprocess/git-shelling modules. This does not block the epic — it is
  resolved inside the dev-tooling child item.
- **Per-repo paired-test fragilities.** livespec's two fragility classes
  (§1.3) are confirmed; dev-tooling / impl-git-jsonl / runtime must be audited
  for the same `inspect.getsource` and root-relative-fixture patterns during
  their legs. Each child item owns that audit.

---

## 7. Child-item decomposition

Numbered, one item per repo or coherent unit. Each notes the repo and whether
the change is product `.py` / config / CI. None of these add NEW product `.py`
logic — they are config + workflow + test-guard changes (item 1 touches a test
file's skip guard; no product `.py` semantics change), so most legs are
`chore(...)` and skip the Red-Green-Replay ritual. Sequencing: item 1
(livespec keystone) and item 5 (dev-tooling shared check, if any change is
even needed there) are independent; items 2-4 each depend only on the shared
`check_mutation` already being correct.

1. **livespec — fix the nested-layout mutmut bug + capture real baseline.**
   Repo: `livespec`. Type: **config + test-guard** (`[tool.mutmut]` rework,
   `check-mutation` recipe `cd`s into `.claude-plugin/scripts/`, `also_copy`
   support closure, the `skipif(MUTANT_UNDER_TEST)` guard on the one
   `inspect.getsource` test, and the captured `.mutmut-baseline.json`). The
   keystone — see §1.3. Run mutation locally, capture baseline or surface
   under-floor DECISION per §3. Subject `fix:`/`chore:` per the changeset (the
   test-guard edit is a one-line skip marker, not a logic change → `chore`).

2. **livespec-impl-git-jsonl — configure mutmut (nested layout) + baseline +
   release-tag workflow + CI lever.** Repo: `livespec-impl-git-jsonl`. Type:
   **config + CI**. Add `[tool.mutmut]` with the nested-layout fix mirroring
   item 1 (cwd = `.claude-plugin/scripts/`, `paths_to_mutate = spec_reader.py,
   _ids.py, types.py`, support `also_copy`); audit paired tests for the two
   fragility classes; add `release-tag.yml` (set `LIVESPEC_RUN_MUTATION=true`);
   capture baseline or surface under-floor DECISION. **Depends on item 1**
   (reuses the validated nested-layout fix pattern).

3. **livespec-dev-tooling — configure mutmut (flat layout) + baseline +
   release-tag workflow + CI lever.** Repo: `livespec-dev-tooling`. Type:
   **config + CI**. Add `[tool.mutmut]` (flat layout — no cwd relocation
   needed) with the chosen pure-logic `paths_to_mutate` (§2, resolve open
   question §6); audit paired tests for fragilities; add `release-tag.yml`
   (set `LIVESPEC_RUN_MUTATION=true`, scope matrix to this repo's release-gate
   targets); capture baseline or surface under-floor DECISION. Independent of
   the nested-layout fix.

4. **livespec-runtime — configure mutmut (flat layout) + baseline +
   release-tag workflow + CI lever.** Repo: `livespec-runtime`. Type:
   **config + CI**. Add `[tool.mutmut]` (flat layout) with
   `paths_to_mutate = livespec_runtime/cross_repo`; audit paired tests; add
   `release-tag.yml` (set `LIVESPEC_RUN_MUTATION=true`); capture baseline or
   surface under-floor DECISION. Independent.

5. **(Conditional) shared `check_mutation` / docs hardening.** Repo:
   `livespec-dev-tooling`. Type: **product `.py` (only if needed) + docs**.
   `check_mutation` is already correct, so this item is likely a no-op for the
   engine. IF any leg discovers a shared-check shortcoming (e.g. the
   `total == 0` silent-pass should warn loudly once the engine is functional,
   or the baseline-path handling needs the cwd-relocation accommodation for
   nested repos), file it here. Any change to `check_mutation.py` itself is
   product `.py` and MUST follow the Red-Green-Replay ritual in
   livespec-dev-tooling. Hold as a placeholder; promote to real work only on
   evidence from items 1-4.

6. **(Doc) record the family mutation-testing contract.** Repo: `livespec`.
   Type: **docs/spec**. Once the engine is functional in all 4 repos, capture
   the durable architectural commitment (mutation = release-gate; nested-layout
   repos run mutmut from the import root; pure-logic-only `paths_to_mutate`;
   80% floor + ratchet) in the appropriate `SPECIFICATION/` section or a
   contract note, so the family rule is discoverable rather than living only in
   per-repo `[tool.mutmut]` blocks. `chore(spec):` / `docs(...)`. Depends on
   items 1-4 landing.

**Suggested wave plan:** item 1 first (keystone, validates the nested-layout
pattern) → items 2/3/4 in parallel (2 reuses 1's pattern; 3/4 are independent
flat-layout configs) → items 5/6 last (5 conditional on evidence, 6 ratifies
the contract).
