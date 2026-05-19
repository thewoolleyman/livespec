#!/usr/bin/env python3
"""Shebang wrapper for next. No logic; see livespec.commands.next."""

from _bootstrap import bootstrap

bootstrap()

from livespec.commands.next import main

raise SystemExit(main())
