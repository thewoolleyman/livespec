#!/usr/bin/env python3
"""Shebang wrapper for propose-change. No logic; see livespec.commands.propose_change for implementation."""

from _bootstrap import bootstrap

bootstrap()
from livespec.commands.propose_change import main

raise SystemExit(main())
