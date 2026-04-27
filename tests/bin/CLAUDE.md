# tests/bin/

Tests for the shebang wrappers under
`.claude-plugin/scripts/bin/`. Three test groups:

- `test_wrappers.py` — meta-test asserting every wrapper file
  (`<cmd>.py`, excluding `_bootstrap.py`) matches the canonical
  6-statement shape required by `check-wrapper-shape` and
  `python-skill-script-style-requirements.md` §"Wrapper shape":
  shebang → docstring → `from _bootstrap import bootstrap` →
  `bootstrap()` → `from livespec.<...> import main` → `raise
  SystemExit(main())`. The optional blank line per v016 P5 is
  permitted between statements 4 and 5.
- `test_<cmd>.py` — per-wrapper coverage tests. Each test
  imports the wrapper file with `monkeypatch`-stubbed
  `bootstrap` (so the runtime version check is a no-op) and
  `monkeypatch`-stubbed `livespec.commands.<cmd>.main` (so we
  exercise the wrapper's plumbing without invoking the real
  command), then catches the wrapper's `raise SystemExit(...)`
  via `pytest.raises(SystemExit)` and asserts the exit-code
  threading. Required for 100% line+branch coverage of the
  wrappers per `check-coverage`.
- `test_bootstrap.py` — covers `_bootstrap.bootstrap()`. Both
  branches of the `sys.version_info < (3, 10)` check are
  exercised via `monkeypatch.setattr(sys, "version_info",
  ...)`. Pragma exclusions on `bin/*.py` are forbidden by
  v011 K3, so branch coverage of the exit-127 path is
  achieved exclusively through monkeypatching.
