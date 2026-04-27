# tests/livespec/doctor/

Tests for `livespec/doctor/`. The supervisor at `run_static.py`
gets per-branch coverage of:

- registry composition (every check in
  `static/__init__.py.STATIC_CHECKS` is invoked exactly once);
- ROP-chain pattern-match (the final `IOResult` is decoded into
  the doctor static-phase output contract);
- exit-code derivation (0 = no findings, 1 = at least one
  finding, 2 = usage error, &c.).

Per-check tests live in `tests/livespec/doctor/static/`,
mirroring the source layout.
