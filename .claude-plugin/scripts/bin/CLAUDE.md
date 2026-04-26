# bin/

Shebang-wrapper executables (`#!/usr/bin/env python3`). Each wrapper
is a 6-statement supervisor entry point that imports
`livespec.commands.<cmd>.main` (or `livespec.doctor.run_static.main`)
and calls `raise SystemExit(main())`. Shape is mechanically enforced
by `check-wrapper-shape`.

`_bootstrap.py` is the one exception to the wrapper shape: it carries
the pre-livespec sys.path setup + Python version check, and is the
only file outside supervisor scope where `sys.stderr.write` is
permitted (the version-check error message; structlog has not yet
been configured at that point).

`raise SystemExit(...)` is permitted in this directory. Everywhere
else, the supervisor pattern-matches an `IOResult` and returns the
exit code; bare `sys.exit` is banned.
