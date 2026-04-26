#!/usr/bin/env python3
"""Shebang wrapper for prune-history. No logic; see livespec.commands.prune_history for implementation."""
from _bootstrap import bootstrap
bootstrap()
from livespec.commands.prune_history import main

raise SystemExit(main())
