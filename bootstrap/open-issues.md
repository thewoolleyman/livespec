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
