#!/usr/bin/env python3
"""Shebang wrapper for critique. No logic; see livespec.commands.critique."""

from _bootstrap import bootstrap

bootstrap()

from livespec.commands.critique import main

raise SystemExit(main())
