# Bootstrap status

**Current phase:** 7
**Current sub-step:** Phase 7 sub-step 4 (critique widening). Sub-steps 4.a (file propose-change) ✓ at `659fa95` and 4.b (revise accepts) ✓ at `30c9631` complete this session. Next: sub-step 4.c — implementation widening via Red→Green cycle(s) per v033 D5b + v034 D2-D3 contracts to bring `livespec/commands/critique.py` to v010 spec parity.
**Last completed exit criterion:** phase 6
**Next action:** Begin sub-step 4.c — Red→Green cycle widening `livespec/commands/critique.py`. Two entangled behavioral changes; combined into one cycle since the second depends on the first's resolved value:

  (A) **Author resolution: 2-step → 4-step.** Current `_resolve_author(*, namespace)` (critique.py line 83-95) only handles CLI-flag → `"unknown-llm"` fallback. The v010 spec edit + spec.md §"Author identifier resolution" (codified at v009) demand the full unified precedence: `--author <id>` (CLI) > `LIVESPEC_AUTHOR_LLM` (env) > payload-level `author` field > `"unknown-llm"`. Reference impl is propose_change._resolve_author (propose_change.py lines 222-244) with signature `(*, namespace, payload, env_lookup)`.

  (B) **Topic delegation: pre-attached → reserve-suffix-parameter.** Current main() line 127-128: `topic = f"{_resolve_author(namespace=namespace)}-critique"` followed by `delegated_argv: list[str] = ["--findings-json", str(namespace.findings_json), topic]`. The v010 spec edit (spec.md §"Sub-command lifecycle" "**`critique` internal delegation...**") demands: pass un-slugged resolved-author stem as topic-hint AND pass `--reserve-suffix=-critique` separately AND pass `--author=<resolved>` so propose_change's own front-matter author resolution short-circuits at step 1.

**Suggested cycle 1 plan (one Red→Green pair):**

Red commit (extending `tests/livespec/commands/test_critique.py` per v037 D1 broadened `--diff-filter=AM` classifier; one test file modified, zero impl files):
- `test_critique_main_resolves_author_via_env_var_when_no_cli_or_payload` — sets `LIVESPEC_AUTHOR_LLM=env-author` via `monkeypatch.setenv`, no `--author`, no payload-level author; asserts file at `<spec-target>/proposed_changes/env-author-critique.md`.
- `test_critique_main_resolves_author_via_payload_when_no_cli_or_env` — `monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)`, payload top-level `"author": "payload-author"`, no `--author`; asserts file at `<spec-target>/proposed_changes/payload-author-critique.md`.
- `test_critique_main_cli_author_wins_over_env_and_payload` — env set + payload set + `--author=cli-author`; asserts CLI wins, file at `<spec-target>/proposed_changes/cli-author-critique.md`.
- `test_critique_main_truncates_long_author_stem_preserving_critique_suffix` — `--author=("a"*70)` (70 chars; canonical of 70-`a` alone = 64 chars; would overflow with pre-attachment); asserts post-widening filename = `("a"*55)+"-critique.md"` proving reserve-suffix-parameter delegation kicked in (propose_change canonicalizes non-suffix portion to 55 then re-appends `-critique`).
- Also add `monkeypatch.delenv("LIVESPEC_AUTHOR_LLM", raising=False)` to the existing fallback tests at lines 86-111 and 186-213 for env-isolation (prevents user-shell `LIVESPEC_AUTHOR_LLM` from polluting the "unknown-llm" assertion).
- Subject: `feat: red — critique resolves author per 4-step precedence + reserve-suffix-parameter delegation`

Green amend (impl files only — `livespec/commands/critique.py`):
- Widen `_resolve_author` to signature `(*, namespace, payload, env_lookup)` matching propose_change._resolve_author, implementing the 4-step precedence. The body is identical to propose_change's reference impl (DRY-violation accepted between two private module-internal helpers; not extracting to shared module per "don't add features beyond what the task requires" guidance).
- Refactor `main()` to thread the validated payload + `os.environ.get` through to `_resolve_author`. Critical: the payload already lives on the validated railway IOResult; main() needs to either thread it past the existing pre_delegation_exit pattern-match OR re-parse it post-validation. Cleanest path: pattern-match the railway IOResult to extract the validated payload as `ProposalFindings` (Success arm) or exit early (Failure arm).
- Replace delegated_argv composition: `delegated_argv = ["--findings-json", str(namespace.findings_json), "--reserve-suffix", "-critique", "--author", resolved_author, ...spec-target/project-root..., resolved_author]` — the resolved-author stem is the trailing positional topic-hint; `--reserve-suffix=-critique` is the separate parameter; `--author=<resolved>` ensures propose_change's front-matter author matches critique's resolved value.

**Pre-cycle invariants to confirm before authoring tests:**
- v037 D1 Red-mode classifier (`--diff-filter=AM`) is wired in `justfile` `check-pre-commit` recipe (verify by reading lines 208-219 area; STATUS resolution at 2026-05-03T03:20:23Z confirms PROPOSAL+plan landed at v037, but should double-check the implementation commit).
- propose_change's reserve-suffix canonicalization handles the long-stem truncation case correctly per cycle 2 of sub-step 3.c (`8004263`); test #4's expected output of `("a"*55)+"-critique.md"` follows from the v016 P3 / v017 Q1 algorithm: canonicalize "a"*70 → "a"*64 (truncate-only), strip non-suffix portion to 64-len("-critique")=55 chars, re-append "-critique" → "a"*55+"-critique" (64 chars total).

**Architectural notes:**
- The `_resolve_author` extraction-to-shared-module question was considered and rejected: each module's `_resolve_author` is private; cross-module calls into private helpers violate the module-private boundary; the cleaner path is identical inline impls.
- Critique calls `propose_change.main(argv=...)` (CLI re-entry), not the internal Python logic directly. The spec edit's "delegates to `propose-change`'s **internal Python logic**" wording is aspirational — full Phase-7 widening could refactor to a Python-level `propose_change.run(*, payload, topic_hint, reserve_suffix, author, ...) -> IOResult` API and have critique call that. For sub-step 4.c, CLI re-entry suffices and matches the existing Phase-3-min shape; the doctor-cycle-skip rule is moot until propose_change has a doctor cycle to skip (Phase-7 propose_change widening for that lands separately if at all).
- The "does not run revise" rule (spec.md §"Sub-command lifecycle" "**`critique` internal delegation...**" closing sentence) is already satisfied — critique.main() returns propose_change.main()'s exit code without invoking revise. No code change.

**Phase-7 architectural follow-up logged in `decisions.md` 2026-05-03T10:50:00Z:** `heading_coverage.py` treats `## Proposal:` headings under `proposed_changes/` as spec content; PROPOSAL.md §"Coverage registry" lines 3795-3798 narrowly define `spec_root` as tree-root only. Pre-existing PROPOSAL drift accepted at Phase 6; deferred to Phase 7 propose-change cycle or Phase 8 deferred-items entry. Not blocking sub-step 4.c.

**Sub-step 3.c implementation summary (preserved from prior session):**
- Cycle 1 — topic canonicalization (v015 O3): added `_canonical_alnum_run_strip(*, text)` shared primitive + `_canonicalize_topic(*, hint, reserve_suffix=None)`.
- Cycle 2 — reserve-suffix (v016 P3 / v017 Q1): widened `_canonicalize_topic` with `reserve_suffix` keyword.
- Cycle 3 — author resolution + YAML front-matter: added `_resolve_author(*, namespace, payload, env_lookup)` implementing 4-step precedence in propose_change.py.
- Cycle 4 — slug transformation (v014 N5): structural no-op (decisions.md 2026-05-04T02:10:00Z).
- Cycle 5 — collision disambiguation (v014 N6): added `_resolve_target_path(*, proposed_changes_dir, canonical_topic, existing_filenames)`.

**Cycle 3 amend hiccup (codified):** Cycle 3's first amend failed `check-newtype-domain-primitives` because `ProposalFindings.author` was annotated `str | None` instead of `Author | None`. Lesson: when widening a wire dataclass with a canonical-name field, check the NewType mapping in `dev-tooling/checks/newtype_domain_primitives.py` BEFORE coverage check. Sub-step 4.c does NOT widen any schema dataclass (only the wrapper helper), so this lesson does NOT apply to 4.c.

**v034 scope (eight decisions):** D1 Conventional Commits + semantic-release adoption ✓; D2 TDD-Red/Green trailer schema ✓; D3 replay-based enforcement contract via `dev-tooling/checks/red_green_replay.py` ✓; D4 `refs/notes/commits` as advisory operational cache ✓; D5 plan-text + dev-tooling enumeration housekeeping ✓; D6 baseline-grandfathered-violations TOML mechanism (deferred indefinitely per v035 D1); D7 Phase 5 §"Aggregate-restoration drain" ✓; D8 branch protection on master ✓.

**Pre-v034 cycle history preserved as-is:** v033 D5b second-redo cycles 1-172 used the v033 discipline (`## Red output` honor system; `phase-N: cycle N — ...` commit prefix). Grandfathered: commitlint excludes pre-v034-codification ancestor SHAs.

**Cascading-impact scan (post-4.b, 2026-05-04):** PROPOSAL.md frozen at v037 (post sub-step 4.b's spec edits, the SPECIFICATION/ tree is at v010). All v010 edits derive from PROPOSAL §"`critique`" lines 2350-2403 verbatim — no drift. Plan Phase 7 lines 3375-3378 ("widen the Phase-3 minimum-viable internal-delegation shape to full reserve-suffix-aware delegation, accepting `--spec-target` and routing delegation with the same target") is consistent with what landed: contracts.md row enumerates the full flag set including `--spec-target`, spec.md codifies the reserve-suffix-parameter delegation. No drift detected.

**Last updated:** 2026-05-04T02:45:00Z
**Last commit:** `30c9631` on phase-7-widen-sub-commands (sub-step 4.b: `chore: phase-7 sub-step 4.b — revise accepts critique widening`). Sub-step 4 commit chain so far (oldest→newest): `659fa95` (4.a propose-change file) → `30c9631` (4.b revise + v010 cut). Sub-step 3.c commits at `deb48f5` (cycle 1), `8004263` (cycle 2), `be2beef` (cycle 3), `9c42ccd` (cycle 4 decision-only), `4112ded` (cycle 5). Sub-step 3.a `c8a6be2`, 3.b `92468a6`. Branch is 38 commits ahead of origin/phase-7-widen-sub-commands.

**Pause note (2026-05-04, after sub-step 4.b):** sub-steps 4.a + 4.b COMPLETE; STATUS written. Resume with `/livespec-bootstrap:bootstrap --ff` to begin sub-step 4.c (Red→Green cycle widening critique.py per the plan above). Untracked file `.claude/scheduled_tasks.lock` is harness-side scheduled-task lock noise; not a livespec artifact. The lefthook "Can't rename pre-commit/commit-msg/pre-push to .old" warnings during commit are also harness noise (lefthook trying to re-sync hooks during commit-time on top of an existing install) and not blocking — the actual hook runs (`00-lint-autofix-staged`, `01-commit-pairs-source-and-test`, `02-check-pre-commit`, `01-red-green-replay`) all execute and pass.
