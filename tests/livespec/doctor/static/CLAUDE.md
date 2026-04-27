# tests/livespec/doctor/static/

Per-check tests for the static-phase doctor checks under
`livespec/doctor/static/`. Each `test_<name>.py` covers the
matching `static/<name>.py`:

- the check function returns the expected `Findings` value for
  a fixture matching the check's rule;
- the check function returns the expected `Findings` value for
  a fixture violating the rule (exact `Finding` payload —
  severity, location, message — asserted);
- edge cases the check explicitly handles (missing files,
  empty input, &c.) produce the correct `Findings` outcome.

Phase 3 narrowed-registry policy (v022 D7): only the 8
implemented checks have populated test files at Phase 5; the
remaining four checks are stubs and gain real test coverage at
Phase 7.
