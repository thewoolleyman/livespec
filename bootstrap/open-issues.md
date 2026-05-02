# Open issues

Append-only-with-status-mutation log of plan / PROPOSAL drift
discovered during bootstrap execution. The bootstrap skill is the
only writer.

Each entry's heading carries the timestamp, phase, severity, and
disposition. Severity is one of: `blocking`,
`non-blocking-pre-phase-6`, `non-blocking-post-phase-6`. Disposition
(intent) is one of: `halt-and-revise-brainstorming`,
`defer-to-spec-propose-change`, `resolved-in-session`. Status
(lifecycle) is one of: `open`, `resolved`, `superseded`.

Existing entries' bodies are written once; the `Status:` field MAY
be mutated in place, and a `**Resolved:** ...` line MAY be appended
on resolution. Never rewrite or delete entries without explicit
user direction.

Entry format:

```markdown
## <UTC ISO 8601> — phase N — <severity> — <disposition>

**Status:** open

**Description:** <description, 1-3 sentences>
```

On resolution, the skill mutates `Status:` to `resolved` and
appends:

```markdown
**Resolved:** <UTC ISO 8601> — <one-line resolution summary>
```

## 2026-04-25T23:33:20Z — phase 0 — non-blocking-pre-phase-6 — resolved-in-session

**Status:** resolved

**Description:** Plan Phase 0 step 3 directs deleting `tmp/` on the premise that it is empty stale scaffolding from earlier brainstorming passes. User reports `tmp/` is in active use as personal scratch space and must not be deleted. Convention adopted: any future bootstrap-owned scratch goes under `tmp/bootstrap/` (creatable on demand, freely deletable by the bootstrap); `tmp/` root is user-owned and off-limits. `tmp/` is git-untracked, so the Phase 0 exit-criterion commit (only header-note addition + `tmp/` removal) is naturally satisfied since the deletion would be git-invisible.

**Resolved:** 2026-04-25T23:33:20Z — convention established (`tmp/bootstrap/` for bootstrap scratch, `tmp/` root user-owned); sub-step 3 no-op since no bootstrap scratch exists to delete.

**Resolved:** 2026-04-25T23:52:51Z — codified in v023; see `history/v023/proposed_changes/critique-fix-v022-revision.md` (decision D1) and the paired plan-text edits at Phase 0 step 3 + exit criterion.

## 2026-04-26T01:52:47Z — phase 1 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** PROPOSAL.md §"Developer-time dependencies (livespec repo only)" (lines 534-545) and §3437's directory-shape diagram say developer tooling is "managed via `mise`" with `.mise.toml` pinning the 12 dev tools, but neither PROPOSAL nor the plan specifies the underlying Python toolchain manager. User-established convention 2026-04-26: UV (astral-sh/uv) is the Python toolchain manager; mise's role narrows to pinning non-Python binaries only (`uv` itself, `just`, `lefthook`); UV manages Python via `uv python pin` and all Python packages via `pyproject.toml` `[dependency-groups.dev]` + `uv sync`. PROPOSAL.md and plan must be revised to codify UV explicitly so the executor doesn't reflex-default to pipx or pip. Picking UV-managed-Python with mise-pins-binaries-only architecture (gated via AskUserQuestion 2026-04-26).

**Resolved:** 2026-04-26T04:34:25Z — codified in v024; see `history/v024/proposed_changes/critique-fix-v023-revision.md` (decisions D1-D4) and the paired plan-text edits at Phase 1 first bullet, new `.python-version` bullet, `pyproject.toml` `[project]` + `[dependency-groups.dev]` sub-bullets, Phase 1 exit criterion, Phase 0 byte-identity references, and Preconditions file list.

## 2026-04-26T07:05:00Z — phase 2 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** PROPOSAL.md §"Runtime dependencies — Vendored pure-Python libraries" lists `returns_pyright_plugin` as the sixth vendored lib (v018 Q4 decision: "vendor the returns pyright plugin alongside the library at `.claude-plugin/scripts/_vendor/returns_pyright_plugin/`"). Verified against upstream dry-python/returns at v0.25.0 (latest tag): the repo ships `returns/contrib/{mypy,pytest,hypothesis}/` plugins but NO pyright plugin. Zero references to "pyright" in the entire codebase. The v018 Q4 decision was based on the mistaken premise that a returns pyright plugin existed upstream. References in: PROPOSAL.md (line 100 directory tree, line 453-456 vendoring section, line 3700-3708 typechecker section), PLAN_TO_BOOTSTRAP_SPECIFICATION_AND_REPO.md (line 529, 614, 686-691), python-skill-script-style-requirements.md (line 145-155 vendored libs section, line 750-752 pyright config section, line 212/218 vendor list), .vendor.jsonc (entry at sub-step 9), NOTICES.md (entry from sub-step 11), pyproject.toml (pluginPaths value from sub-step 3). Resolution requires v025 PROPOSAL.md snapshot dropping the entry from the canonical six-lib list (or replacing with another mechanism for `Result`/`IOResult` strict-mode inference).

**Resolved:** 2026-04-26T07:55:00Z — codified in v025 D1; see `history/v025/proposed_changes/critique-fix-v024-revision.md`. Sub-agent investigation (preserved in conversation transcript) confirmed pyright has no plugin system by design (microsoft/pyright#607) and dry-python/returns explicitly does not support pyright (dry-python/returns#1513), so option (a) — drop the plugin entry, stay on pyright with the seven strict-plus diagnostics — was the only viable resolution. The cosmetic BSD-2 → BSD-3-Clause license correction (paired entry 2026-04-26T07:05:01Z, superseded) rode along as v025 D2. Companion-doc + repo-state files (style doc, NOTICES.md, .vendor.jsonc, pyproject.toml) were updated in the same v025 commit.

## 2026-04-26T07:05:01Z — phase 2 — blocking — halt-and-revise-brainstorming

**Status:** superseded

**Description:** PROPOSAL.md §"Runtime dependencies — Vendored pure-Python libraries" line 99-100 (and downstream NOTICES.md, .vendor.jsonc) declare the `returns` library license as BSD-2. Verified against upstream dry-python/returns v0.25.0 `pyproject.toml`: the upstream-declared license is `BSD-3-Clause`. Drift is a license misclassification across PROPOSAL.md, plan Phase 2 vendoring sub-step (line 686), python-skill-script-style-requirements.md vendored-libs section (line 143), NOTICES.md (sub-step 11 entry). Resolution requires v025 PROPOSAL.md snapshot fixing the license to BSD-3-Clause (and removing the parallel BSD-2 reference for `returns_pyright_plugin` if that entry is dropped per the paired blocking entry above).

**Superseded:** 2026-04-26T07:25:00Z — should not have been logged as a separate blocking entry per the bootstrap skill's new "one-finding-per-gate discipline" (added 2026-04-26 in the same session as this entry). This is a cosmetic license-label correction with zero architectural implications: style doc line 133 explicitly allows both BSD-2-Clause and BSD-3-Clause. The library is in policy at either license; the spec just mislabels it. The fix rides along with whatever PROPOSAL revision happens for the paired pyright-plugin blocker (2026-04-26T07:05:00Z), or as a small overlay reconciliation if that blocker resolves without a PROPOSAL revision. Captured here so the BSD-2 → BSD-3-Clause sweep is not forgotten when the substantive revision lands.

## 2026-04-26T08:30:00Z — phase 2 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** PROPOSAL.md §"Runtime dependencies — Vendored pure-Python libraries" picks `jsoncomment` as the JSONC parser (line 482) and §"Initial-vendoring exception (one-time, v018 Q3)" (lines 506-526) mandates a git-based initial-vendoring procedure (`git clone <upstream>` + `git checkout <ref>` + copy source tree + copy LICENSE). Verification at Phase 2 sub-step 5: jsoncomment's canonical upstream homepage on PyPI is `bitbucket.org/Dando_Real_ITA/json-comment` which returns HTTP 404 (bitbucket sunset Mercurial repos circa 2020); the GitHub URL hard-coded in `.vendor.jsonc` (`Dmitry-Me/JsonComment`) also returns 404; GitHub search returns no active mirrors. PyPI still serves the sdist tarball for jsoncomment 0.4.2 (last release 2019-02-08, MIT-licensed via `COPYING` file, ~240 LOC across `jsoncomment/__init__.py` (48 lines), `comments.py` (177 lines), `wrapper.py` (15 lines)). The v018 Q3 procedure as written cannot be executed for jsoncomment because no live upstream git repo exists to clone. Resolution requires a PROPOSAL.md revision — either (a) extend the v018 Q3 procedure to allow sdist-tarball as alternate upstream type and proceed with jsoncomment 0.4.2 from PyPI sdist (with a checksum/url-of-record convention); (b) replace jsoncomment with an actively-maintained alternative (e.g., `NickolaiBeloguzov/jsonc-parser` 17★ updated 2025-10-17, or `jfcarter2358/jsonc` 7★ updated 2026-02-17 — both license + API would need re-evaluation); or (c) hand-author a livespec-internal JSONC parser shim (similar to typing_extensions, ~30-50 lines stripped from jsoncomment's `comments.py` core stripping logic). Decision affects the Phase 2 vendoring step, the v018 Q3 procedure text, the §"Vendoring discipline" section, and possibly the lib selection itself.

**Resolved:** 2026-04-26T09:00:00Z — codified in v026 D1; see `history/v026/proposed_changes/critique-fix-v025-revision.md`. User selected option (c): hand-authored shim per the v013 M1 pattern. PROPOSAL.md and companion docs (NOTICES.md, .vendor.jsonc, style doc) were updated in the same v026 commit; plan-level edits paired (Version basis, Phase 0 byte-identity, execution prompt, Phase 1 sub-step 9 / 11, Phase 2 sub-step 5). The actual shim authoring + LICENSE capture happens at Phase 2 sub-step 5 execution (now resuming post-v026).

## 2026-04-26T09:45:00Z — phase 2 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** During Phase 2 sub-step 5 vendoring (post-v026), the v013 M1 typing_extensions minimal-shim assumption was falsified by actual vendored-lib import behavior. The shim was widened in-band per the v013 M1 "MAY widen" clause to re-export Never, ParamSpec, Self, TypeVarTuple, TypedDict, and Unpack (six additions beyond the original override + assert_never). On Python 3.13 (system) the smoke test passes — all 5 libs import and the deep paths (returns.io.IOResult, returns.result.Result, fastjsonschema.compile, structlog.get_logger, jsoncomment.JsonComment) all work. On Python 3.10.16 (the pinned dev-env per `.python-version`), the deep import `from returns.io import IOResult` fails because `returns/primitives/hkt.py` uses `Generic[_InstanceType_co, Unpack[_TypeVars]]` where `_TypeVars = TypeVarTuple("_TypeVars")` — variadic generics that require Python 3.11+ stdlib (or a real typing_extensions backport, which the shim cannot provide because Generic on 3.10 rejects non-TypeVar/non-ParamSpec arguments regardless of stub subscriptability). The shim's try/except fallbacks (`Never = NoReturn`, `_TypeVarTupleStub`, `_UnpackStub`) cover *type-hint-only* usage but cannot satisfy `Generic[..., Unpack[_TypeVars]]` at class-definition time on 3.10. Phase 2's stub contract requires `IOFailure(<DomainError>(...))` return statements (which transitively imports returns.primitives.hkt), so Phase 2 cannot proceed on the pinned 3.10 dev env without a fix. Three resolution paths: (a) vendor full typing_extensions upstream — the explicit "scope-widening decision" PROPOSAL.md anticipated at v013 M1, replacing the hand-authored shim with verbatim upstream content (~3000-line single .py file, PSF-2.0 LICENSE already in place verbatim); (b) bump the user-facing Python minimum from 3.10+ to 3.11+ — `_bootstrap.py:11` and `pyproject.toml [project.requires-python]` and `.python-version` get updated; the existing widened shim's try-branches succeed and the fallbacks become dead code; (c) keep 3.10 minimum and find some other resolution (no realistic option — Generic[..., Unpack[X]] fundamentally requires 3.11+ stdlib semantics for runtime evaluation). Decision affects PROPOSAL.md §"Runtime dependencies — Vendored pure-Python libraries" (typing_extensions characterization), the v013 M1 exhibit, the user-facing Python minimum (option b only), and possibly `_vendor/typing_extensions/__init__.py` content (option a).

**Resolved:** 2026-04-26T10:00:00Z — codified in v027 D1; see `history/v027/proposed_changes/critique-fix-v026-revision.md`. User selected option (a): vendor full typing_extensions upstream. PROPOSAL.md and companion docs (NOTICES.md, .vendor.jsonc, style doc) updated in same v027 commit; plan-level edits paired (Version basis, v027 decisions block, Phase 0 byte-identity, execution prompt, Phase 1 sub-step 9 / 11, Phase 2 sub-step 5). The hand-authored shim at `_vendor/typing_extensions/__init__.py` (95 lines) was replaced with verbatim upstream content (3641 lines) at tag `4.12.2`. Smoke test now passes on both Python 3.10.16 (uv-managed venv) and Python 3.13.7 (system): all 5 vendored libs import successfully, deep paths (returns.io.IOResult, returns.result.Result, fastjsonschema.compile, structlog.get_logger, jsoncomment.JsonComment) all work. The user-facing 3.10+ Python minimum is preserved.

## 2026-04-26T15:27:59Z — phase 3 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** PROPOSAL.md §"Template resolution contract" line 1466 specifies that the resolve_template wrapper computes its bundle-root via `Path(__file__).resolve().parent.parent` and then emits `<bundle-root>/specification-templates/<name>/` as stdout for built-in template resolution. Verified against the actual repo layout: from `bin/resolve_template.py`, `Path(__file__).resolve().parent.parent` = `.claude-plugin/scripts/`, but `specification-templates/` lives at `.claude-plugin/specification-templates/` (a SIBLING of `scripts/`, per the directory tree at PROPOSAL lines 88 + 172, and confirmed by `ls .claude-plugin/`). Following the formula literally yields `.claude-plugin/scripts/specification-templates/<name>/`, which does not exist. The correct formula is `Path(__file__).resolve().parent.parent.parent` from `bin/resolve_template.py` (one extra `.parent` to reach `.claude-plugin/`). This blocks Phase 3 sub-step 12 (resolve_template implementation) — every consumer of resolve_template's stdout (seed/SKILL.md prose for prompts/seed.md lookup; doctor's template-exists check) would receive a non-existent path. Resolution requires a v028 PROPOSAL.md snapshot fixing the formula.

**Resolved:** 2026-04-26T15:30:00Z — codified in v028 D1; see `history/v028/proposed_changes/critique-fix-v027-revision.md`. PROPOSAL.md line 1466 replaced with verbal description "the `.claude-plugin/` directory of the installed plugin (the parent of the `scripts/` subtree)" + concrete formula `Path(__file__).resolve().parents[3]` anchored to the `livespec/commands/resolve_template.py` implementation file (where parents[0]=commands/, parents[1]=livespec/, parents[2]=scripts/, parents[3]=.claude-plugin/). Plan-level edits paired (Version basis, v028 decisions block, Phase 0 step 1 byte-identity, Phase 0 step 2 frozen-status quote, Execution-prompt block authoritative-version line). No companion-doc impact (style doc, NOTICES.md, .vendor.jsonc, pyproject.toml carry no bundle-root formula references).

## 2026-04-28T00:20:00Z — phase 4 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** PROPOSAL.md `dev-tooling/checks/` directory listing (lines 3496-3520) is missing five check filenames that exist in the justfile and the rest of the spec: `heading_coverage.py`, `vendor_manifest.py`, `check_tools.py`, `check_mutation.py` (release-gate), and `rop_pipeline_shape.py` (newly authored at Phase 4 sub-step 13 to enforce single-public-method on `@rop_pipeline`-decorated classes). Additionally, the `keyword_only_args.py` annotation enumerates "frozen=True + slots=True" on @dataclass but omits `kw_only=True` (the actual full strict-dataclass triple per style doc lines 1311-1320 and the implementation in dev-tooling/checks/keyword_only_args.py). Surfaced during Phase 4 sub-step 13 cascading-impact scan after authoring rop_pipeline_shape.py. Resolution requires a v029 PROPOSAL.md snapshot.

**Resolved:** 2026-04-28T00:35:00Z — codified in v029 D1; see `history/v029/proposed_changes/critique-fix-v028-revision.md`. PROPOSAL.md lines 3496-3520 directory listing replaced with the corrected enumeration (5 missing filenames added; keyword_only_args.py annotation updated to full triple). Plan-level edits paired (Version basis preamble + v029 decisions block, Phase 0 step 1 byte-identity reference, Phase 0 step 2 frozen-status header, Execution-prompt block authoritative-version line, Phase 4 enforcement-script enumeration carrying `rop_pipeline_shape.py` adjacent to `supervisor_discipline.py`).

## 2026-04-27T00:26:40Z — phase 4 — blocking — halt-and-revise-brainstorming

**Status:** superseded

**Superseded:** 2026-04-27T00:26:40Z — misclassified as PROPOSAL.md drift; the actual divergence is purely in `python-skill-script-style-requirements.md` line 1884 (style-doc canonical target list rule wording). PROPOSAL.md text is unaffected — line 3503's parenthetical "(rescoped per v012 L9 to use __all__ for public-API detection)" describes the public-API detection mechanism (`__all__`-based), not the exemption set. Per the v029 D1 revision file's "style doc edits ride freely with the implementation — not gated by halt-and-revise" convention, this drift takes the lighter Case-B direct-fix path: style doc edited in-place, executor-decision recorded in `bootstrap/decisions.md` at the same timestamp, no v030 bump. The implementation work (`dev-tooling/checks/public_api_result_typed.py` + paired test + `just` wiring) lands in the same sub-step 15 commit as the style-doc edit.

**Description:** PROPOSAL.md `python-skill-script-style-requirements.md` §"Canonical target list" line 1884 (`just check-public-api-result-typed`) describes the rule as: "AST: every public function (per `__all__` declaration; see `check-all-declared`) returns `Result` or `IOResult` per annotation, except supervisors at the side-effect boundary (`main()` in `commands/**.py` and `doctor/run_static.py`) and the `build_parser` factory in `commands/**.py`." Authoring `public_api_result_typed.py` at Phase 4 sub-step 15 surfaced that the rule as written would flag 28 violations against the existing post-Phase-3 codebase, all of which are legitimate non-Result returns the canonical-list wording does not anticipate. Three categories: (a) `@impure_safe(...)`-decorated functions in `io/cli.py`, `io/fs.py`, `io/git.py` whose source-level annotation is the inner type (the dry-python/returns decorator wraps the return into `IOResult[X, <known-exceptions>]` at runtime — there is no way to write the wrapped type at the def site); (b) factory functions that construct railway-participating callables but themselves return non-Result types: `make_validator` in every `validate/*.py` module returns `TypedValidator[T]` (whose `__call__` returns Result), `get_logger` in `io/structlog_facade.py` returns `Logger`, `compile_schema` in `io/fastjsonschema_facade.py` returns the structlog/fastjsonschema facade callable, `rop_pipeline` in `types.py` is a class decorator returning `type`; (c) `build_parser` in `doctor/run_static.py` is the same argparse factory pattern as `commands/**/build_parser` but lives in `doctor/` (the canonical wording exempts only `commands/**`). Additionally, package-private helper modules (filename matching `_*.py`, e.g., `commands/_seed_helpers.py`, `commands/_revise_helpers.py` introduced at sub-step 14a/14b) export pure render/format helpers that cannot fail and don't need a railway envelope; the canonical list says nothing about them. Resolution requires a v030 PROPOSAL.md snapshot that updates the canonical list line 1884 to capture the implementation realities — minimally documenting `@impure_safe`/`@safe` decorator recognition, the four additional name-based exemptions (`make_validator` in `validate/**`, `get_logger` in `io/structlog_facade.py`, `compile_schema` in `io/fastjsonschema_facade.py`, `rop_pipeline` in `types.py`), the `build_parser` exemption widening to include `doctor/run_static.py`, and a private-module skip rule for `_*.py` filenames. Working draft of the check at `dev-tooling/checks/public_api_result_typed.py` is uncommitted pending the revision; `python3 dev-tooling/checks/public_api_result_typed.py` against the current tree exits 0 with the proposed exemption set and 1 (28 violations) with the literal canonical-list wording.

## 2026-04-29T02:44:18Z — phase 5 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** Commit abd0cdd added `case _:` to `[tool.coverage.report].exclude_also` in `pyproject.toml` and extended the style-doc enumeration of structural coverage-exclusion patterns from 3 to 4. PROPOSAL.md §"Testing approach" lines 3372-3375 explicitly enumerate the three structural exclusions: "the only structural exclusions are `if TYPE_CHECKING:`, `raise NotImplementedError`, and `@overload` blocks via `[tool.coverage.report].exclude_also`." The pyproject + style-doc edits are now inconsistent with PROPOSAL.md — PROPOSAL says 3 patterns, the implementation + companion doc carry 4. Operator error: the AskUserQuestion gate at 2026-04-29 claimed "PROPOSAL.md verified unaffected" based on a grep that searched only for the keyword "exclude_also" without picking up the literal 3-pattern enumeration on adjacent lines. The exclude_also addition is substantive (changes coverage-gate semantics, not a label/typo), so the cosmetic-rides-along carve-out does NOT apply per the "Severity judgment over rule-following" memory rule. Resolution requires a v031 PROPOSAL.md snapshot bringing the §"Testing approach" enumeration into alignment with the implementation (3 patterns → 4 patterns; 4th pattern justified by the universal-assert_never mandate at style-doc lines 1054-1066 + AST-level enforcement at `dev-tooling/checks/assert_never_exhaustiveness.py`). Plan-level paired edits: §"Version basis" v031 decision block + Phase 0 step 1/2 + Execution-prompt block authoritative-version line bump. Companion-doc edits already landed at abd0cdd via the v028-D1-style overlay precedent; the v031 revision file documents the PROPOSAL-side reconciliation and references the implementation commit.

**Resolved:** 2026-04-29T02:44:18Z — codified in v031 D1; see `history/v031/proposed_changes/critique-fix-v030-revision.md`. PROPOSAL.md §"Testing approach" lines 3372-3375 now enumerate 4 structural exclusion patterns; plan-level edits at v031 D2 paired (Version basis preamble v031 decision block, Phase 0 step 1 byte-identity, Phase 0 step 2 frozen-status, Execution-prompt block authoritative-version line). Companion-doc + pyproject already shipped at abd0cdd.

## 2026-04-29T07:03:25Z — phase 5 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** Phase 3 and Phase 4 produced impl-first code with tests authored afterward in Phase 5 sub-step 3 ("characterization-style backfill"). User-flagged design concern: characterization-backfill produces covered code, not designed code; the load-bearing TDD benefits (loose coupling, high cohesion, unnecessary-code elimination, good architecture) require Red→Green-per-behavior authoring with each Red observed firing for the right reason. PROPOSAL.md §"Test-Driven Development discipline" line 3105 had a temporal carve-out ("non-negotiable from Phase 5 exit onward") that read as permitting pre-Phase-5-exit characterization mode. v032 closes the carve-out (D1) and authorizes a one-time retroactive redo: stash all Phase 3 / Phase 4 / Phase 5-so-far Python artifacts as a committed binary blob (`bootstrap/scratch/pre-redo.zip` — under SCM, not source-readable, must not be `unzip`-ed during authoring), then walk the PROPOSAL-prescribed module enumeration in dependency order under Red→Green-per-behavior (D2). At the end, the executor authors `bootstrap/v032-quality-report.md` measuring the post-redo tree against the pre-redo zip on architecture, coupling, cohesion, and unnecessary-code elimination dimensions with concrete quantitative metrics + a behavioral-equivalence audit (D3). Per-commit `## Red output` block discipline enforced by a new `dev-tooling/checks/red_output_in_commit.py` check (D4). Plan housekeeping bumps Version basis preamble v032 decision block, Phase 0 byte-identity to `history/v032/`, Phase 0 frozen-status to "Frozen at v032", Execution-prompt block authoritative-version line to v032 (D5). This entry tracks the redo as in-progress; it gets `Status: resolved` once the v032 D3 quality-comparison report passes its acceptance criteria and the user gates Phase 5 advance.

**Resolved:** 2026-04-29T20:45:00Z — superseded by v033's second-redo authorization. The v032 first redo reached "integration-test-green parity" with 90 tests passing but produced zero unit tests under `tests/livespec/**` (every authored test landed under `tests/bin/` or `tests/dev-tooling/checks/`). User flagged the gap; v033 codifies four hard mechanical guardrails (D1 mirror-pairing, D2 per-file 100% coverage, D3 commit-pairs-source-and-test, D4 red-output-in-commit hard-gate promotion) plus moves lefthook activation forward to v033-codification (D5a) and authorizes a second retroactive redo (D5b) under the new guardrails. See `history/v033/proposed_changes/critique-fix-v032-revision.md` for the full decision provenance. The second redo will resolve the v032-redo gap mechanically; the first-redo's audit trail is preserved in `bootstrap/scratch/pre-second-redo.zip` (authored at v033 D5b execution time).

## 2026-05-02T07:00:00Z — phase 5 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** PROPOSAL.md §"Baseline-grandfathered violations (v034 D6)" (lines 4096-4180) describes a `phase-5-deferred-violations.toml` baseline file mechanism + per-check baseline-loading that was deferred indefinitely at the v034 step-3 activation commit (`chore!: activate v034 replay hook + remove v033 hook`, sha 495e5ce). User authorized the deferral via AskUserQuestion 2026-05-02 (slim activation). The thinned `just check` aggregate stays in place; the v034 D7 drain proceeds against it via the existing v033 D5b pattern (each fix-cycle rejoins its now-passing target). PROPOSAL text currently describes a mechanism that won't exist; future drain-cycle agents reading PROPOSAL would look for the file, find it absent, and be confused. Resolution requires v035 PROPOSAL snapshot rewriting §"Baseline-grandfathered violations" to reflect the slim-activation reality (mark deferred + cross-reference the actual thinned-aggregate mechanism in §"Aggregate-restoration drain"). Plan §"v034 transition" step 3 + §"Aggregate-restoration drain" carry paired drift.

**Resolved:** 2026-05-02T08:00:00Z — codified in v035 D1; see `history/v035/proposed_changes/critique-fix-v034-revision.md`.

## 2026-05-02T07:00:01Z — phase 5 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** PROPOSAL.md §"v034 D2-D3 Red→Green replay contract" line 3517 calls the replay hook "the pre-commit hook". The actual design is fundamentally a `commit-msg` git hook: the hook writes trailers via `git interpret-trailers --in-place` (requires the commit-message file path as argv[1]); distinguishes Red vs Green amend by inspecting HEAD~0's commit message (only meaningful at commit-msg stage; pre-commit fires before HEAD updates). Cycles 173-183 + the v034 step-3 activation commit (sha 495e5ce) all wired the hook at lefthook `commit-msg` stage, not pre-commit. Plan §"v034 transition" step 3 carries paired wording drift ("pre-commit ordering"). Resolution requires v035 PROPOSAL snapshot fixing line 3517 wording + plan §"v034 transition" step 3 wording.

**Resolved:** 2026-05-02T08:00:00Z — codified in v035 D2; see `history/v035/proposed_changes/critique-fix-v034-revision.md`.

## 2026-05-02T07:00:02Z — phase 5 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** PROPOSAL.md §"v034 D2-D3 Red→Green replay contract" §"Anti-cheat" (lines ~3585+) describes a reflog-inspection mechanism that rejects amends whose `TDD-Green-Parent-Reflog` SHA either does not appear in the local reflog OR appears but does not carry a Red marker + matching checksum. The mechanism was deferred per the cycle-183 commit body (sha ec2d3e6) on the rationale that "the local Red→Green amend pattern is already mechanically airtight without it for honest workflows" + user-approved fast-forward through the activation. PROPOSAL text describes a check that doesn't exist in `dev-tooling/checks/red_green_replay.py`; future drain-cycle agents reading PROPOSAL might try to trigger anti-cheat behavior or assume the hook handles adversarial scenarios. Resolution requires v035 PROPOSAL snapshot marking §"Anti-cheat" as deferred (or cross-referencing post-v1.0.0 hardening as the implementation venue). Hook docstring already reflects the deferral; PROPOSAL needs the paired update.

**Resolved:** 2026-05-02T08:00:00Z — codified in v035 D3; see `history/v035/proposed_changes/critique-fix-v034-revision.md`.

## 2026-05-02T07:00:03Z — phase 5 — blocking — halt-and-revise-brainstorming

**Status:** resolved

**Description:** PROPOSAL.md §"Trailer schema" (lines 3548-3554) specifies `TDD-Red-Test-File-Checksum: sha256:<hex>` as a singular field, and §"Red mode (initial commit)" (lines 3522-3531) describes "the test file's SHA-256" (singular). The implementation in `dev-tooling/checks/red_green_replay.py` (cycle 179, sha 446b96b) enforces single-test-file Red commits via a structured `red-green-replay-multi-test-file` rejection diagnostic when multiple test files are staged. PROPOSAL doesn't explicitly state this rejection — the per-file constraint is implicit from the singular schema. Future agent reading PROPOSAL might author a Red commit staging multiple test files and be confused by the rejection. Resolution requires v035 PROPOSAL snapshot adding an explicit per-file constraint sentence in §"Red mode (initial commit)" or §"Trailer schema" that codifies the multi-test-file rejection.

**Resolved:** 2026-05-02T08:00:00Z — codified in v035 D4; see `history/v035/proposed_changes/critique-fix-v034-revision.md`.
