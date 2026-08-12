#!/usr/bin/env python3
"""Shebang wrapper for the spec-PR merge policy gate.

No logic; see livespec.commands.spec_pr_merge_policy. The wrapper exists
because a naked `python3 -c "import livespec..."` from a workflow fails
closed with ModuleNotFoundError: importing the package pulls in vendored
structlog, which resolves only once `_bootstrap` has put
`.claude-plugin/scripts/_vendor` on sys.path.
"""

from _bootstrap import bootstrap

bootstrap()

from livespec.commands.spec_pr_merge_policy import main

raise SystemExit(main())
