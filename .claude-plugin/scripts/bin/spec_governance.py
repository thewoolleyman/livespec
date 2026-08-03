#!/usr/bin/env python3
"""Shebang wrapper for spec-governance. No logic; see livespec.commands.spec_governance."""

from _bootstrap import bootstrap

bootstrap()

from livespec.commands.spec_governance import main

raise SystemExit(main())
