# tests/e2e/

End-to-end integration tests for the livespec wrapper chain. Two harness
tiers, selected by `LIVESPEC_E2E_HARNESS`:

- `mock` (default) — `fake_claude.py` provides deterministic payloads;
  wrappers run for real. Invoked by `just e2e-test-claude-code-mock`
  (in `just check`).
- `real` — `real_claude.py` uses `claude-agent-sdk` against the
  `@anthropic-ai/claude-code` CLI and the live Anthropic API. Invoked by
  `just e2e-test-claude-code-real` (NOT in `just check`); runs weekly via
  `.github/workflows/e2e-real.yml` and on-demand via `workflow_dispatch`.
  Requires `ANTHROPIC_API_KEY`; defaults to model `claude-haiku-4-5-20251001`.

Tests import `harness` — the selector module — and the same test bodies run
under both tiers. `@pytest.mark.mock_only` items are auto-skipped in real
mode via `conftest.py`. The flagship multi-sub-command flows carry
`@pytest.mark.e2e_golden`; the real-tier `just` recipe runs only those by
default for cost control (override with `JUST_E2E_PYTEST_ARGS='-m ""'`).

## Files

- `fake_claude.py` — mock harness module. One function per sub-command.
- `real_claude.py` — real harness module; mirrors `fake_claude`'s public
  surface; each LLM-driven function performs a one-shot
  `claude_agent_sdk.query()` with a `--json-schema`-constrained output
  format (per the matching wire-contract schema). Non-LLM helpers
  (`doctor_static`, `prune_history`, `propose_change_invalid`,
  `seed_required_workflow_files`) are re-exported from `fake_claude`
  unchanged.
- `harness.py` — selector. Re-exports the matching tier's surface based on
  `LIVESPEC_E2E_HARNESS`.
- `conftest.py` — adds `tests/e2e/` to sys.path; scrubs inherited `GIT_*`
  env vars; auto-skips `mock_only` tests when `LIVESPEC_E2E_HARNESS=real`.
- `test_happy_path.py` — seed → propose-change → critique → revise →
  doctor → prune. Marked `e2e_golden`.
- `test_retry_on_exit_4.py` — schema-invalid payload → exit 4 → retry
  succeeds. `mock_only` (no LLM round-trip variant).
- `test_doctor_fail_then_fix.py` — bad spec trips doctor; fix via
  propose-change + revise. Marked `e2e_golden`.
- `test_prune_history_noop.py` — v001-only → prune-history skipped Finding.

## Conventions

- Each test initializes a fresh `tmp_path` git repo via `_git(["init"])`.
- Steps that change committed spec state MUST be followed by `git add &&
  git commit` so the `out-of-band-edits` doctor check sees HEAD-committed
  state.
- Both harness tiers use `SPECIFICATION/spec.md` (two path parts) as the
  seed file per the seed-payload path convention (`SPECIFICATION/contracts.md`
  §"Seed-payload path convention"). The real harness's seed prompt
  explicitly instructs the LLM to emit the two-part path, overriding the
  minimal template's `SPECIFICATION.md` default — the e2e fixture is a
  custom integration-test surface, not the user-facing flow.
- Coverage measurement does NOT apply to `tests/e2e/`.
