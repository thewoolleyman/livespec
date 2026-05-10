# tests/e2e/

End-to-end integration tests for the livespec wrapper chain. Two tiers
were *designed* (selected by the `LIVESPEC_E2E_HARNESS` env var) but only
the `mock` tier is implemented today:

- `mock` — `fake_claude.py` provides deterministic payloads; wrappers run
  for real. Invoked by `just e2e-test-claude-code-mock` (in `just check`).
- `real` — *DESIGN INTENT, NOT YET IMPLEMENTED.* Was meant to run real
  `claude-agent-sdk` + live Anthropic API via `just
  e2e-test-claude-code-real` and the `e2e-real.yml` CI workflow. In
  practice no code reads `LIVESPEC_E2E_HARNESS`, so both modes execute
  the same `fake_claude.py` mock harness. The `real` recipe + workflow
  exist but are functionally identical to the `mock` path; setting
  `ANTHROPIC_API_KEY` does not change behavior. Tracked as a separate
  beads issue (the successor to li-7c0) for actual implementation.

## Files

- `fake_claude.py` — mock harness module. One function per sub-command.
- `conftest.py` — adds `tests/e2e/` to sys.path so tests can `import fake_claude`.
- `test_happy_path.py` — seed → propose-change → critique → revise → doctor → prune.
- `test_retry_on_exit_4.py` — schema-invalid payload → exit 4 → retry succeeds. Mock-only.
- `test_doctor_fail_then_fix.py` — bad spec trips doctor; fix via propose-change + revise.
- `test_prune_history_noop.py` — v001-only → prune-history skipped Finding.

## Conventions

- Each test initializes a fresh `tmp_path` git repo via `_git(["init"])`.
- Steps that change committed spec state MUST be followed by `git add && git commit`
  so the `out-of-band-edits` doctor check sees HEAD-committed state.
- `fake_claude.py` uses `SPECIFICATION/spec.md` (two path parts) as the seed file
  per the seed-payload path convention.
- Coverage measurement does NOT apply to `tests/e2e/`.
