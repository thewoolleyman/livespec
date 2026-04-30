# Bootstrap status

**Current phase:** 5
**Current sub-step:** Phase 5 §"Retroactive TDD redo of Phase 3 + Phase 4 work — second attempt (v033 D5b)" — D5b cycles 62-76 complete (seed.main 5-stage railway through parse_argv → read_text → jsonc.loads → read_text → jsonc.loads → validate_seed_input)
**Last completed exit criterion:** phase 4
**Next action:** v033 D5b cycle batch 1 complete via TDD sub-agent. 15 cycles authored (62-76), each under strict Red→Green discipline + paired test + `## Red output` block; every commit passed all four lefthook gates (commit-pairs + red-output + thinned `just check`). Latest commit `d0596f1`. Test inventory: 24 passing (was 9; +15 new).

**Modules authored in cycles 62-76:**

- `bin/seed.py` — first sub-command shebang wrapper (canonical 6-statement shape).
- `livespec/commands/seed.py` — build_parser + main + supervisor pattern with `assert_never`-terminated match on the railway result.
- `livespec/errors.py` — `LivespecError` + `UsageError` + `PreconditionError` + `ValidationError` (compliant with check-no-inheritance allowlist).
- `livespec/io/cli.py` — `parse_argv` with `@impure_safe(exceptions=(ArgumentError, SystemExit))` (SystemExit catch needed per Python issue 41255).
- `livespec/io/fs.py` — `read_text` with `@impure_safe(exceptions=(OSError,))` mapping FileNotFoundError → PreconditionError.
- `livespec/parse/jsonc.py` — `loads(text)` with `@safe` and `.alt` mapping to ValidationError.
- `livespec/schemas/dataclasses/seed_input.py` — `SeedInput` dataclass (frozen=True, kw_only=True, slots=True).
- `livespec/validate/seed_input.py` — factory-shape validator (currently inlines fastjsonschema.compile; facade pending).

**Aggregate target list (current):** `check-imports-architecture` + `check-tests` (unchanged from spawn — no `dev-tooling/checks/*.py` scripts authored yet; those come during Phase-4-parity cycles after Phase-3 parity completes).

**Sub-agent surfaced concerns (worth attention but not blocking):**

1. `@impure_safe` exception widening to catch `SystemExit` for argparse (Python issue 41255 — `exit_on_error=False` only suppresses `ArgumentError`-class errors). Cycle 69 documented this. Possible spec-drift evaluation when `check-types` returns.
2. `livespec/errors.py` uses `class ValidationError(LivespecError):` — allowed per the check-no-inheritance allowlist; no drift.
3. `check-lint` (ruff) and `check-types` (pyright) deferred from aggregate per Path-2 thinning. Agent-authored Python may carry pyright-strict-mode errors not currently checked.
4. Mirror-pairing gaps: `errors.py` and `schemas/dataclasses/seed_input.py` have no dedicated tests in `tests/livespec/` (behavior exercised transitively via consumer tests). When `check-tests-mirror-pairing` returns to aggregate, those gaps need filling.
5. No `livespec/types.py` yet (NewType aliases pending). When `check-newtype-domain-primitives` returns, refactor cycle needed for `SeedInput.template` (currently raw `str`, should be `TemplateName` NewType).
6. `check-coverage` deferred. Several success-arm branches not yet exercised (e.g., seed.main's success path still returns stub `1`).

**Phase 3 work still ahead:** file-write stages (`fs.write_text`), history/v001/ materialization, auto-captured seed proposed-change emission, post-step doctor invocation; then propose-change/critique/revise/prune-history wrappers + stub mains; then doctor static minimum subset (4-5 static checks). After Phase 3 parity → Phase 4 parity (re-author the 25 deleted dev-tooling/checks/*.py scripts under TDD with paired tests, each cycle re-adding its target to the `just check` aggregate).

**Sub-agent context:** A835ec21efbb16cd8 is paused via report-back; can be resumed via SendMessage if the user wants to continue with the same agent (preserves context but inflates per-cycle cost). Alternative: spawn fresh agent with the same briefing pointing at `d0596f1`.

Open issues: zero unresolved.
**Last updated:** 2026-04-30T03:00:00Z
**Last commit:** d0596f1
