#!/usr/bin/env python3
"""Shebang wrapper for prune_history. No logic; see livespec.commands.prune_history."""

from _bootstrap import bootstrap

bootstrap()

from livespec.commands.prune_history import main

raise SystemExit(main())
