#!/usr/bin/env python3
"""Shebang wrapper for revise. No logic; see livespec.commands.revise for implementation."""

from _bootstrap import bootstrap

bootstrap()

from livespec.commands.revise import main

raise SystemExit(main())
