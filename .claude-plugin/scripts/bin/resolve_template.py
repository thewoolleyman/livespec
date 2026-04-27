#!/usr/bin/env python3
"""Shebang wrapper for resolve-template. No logic; see livespec.commands.resolve_template for implementation."""

from _bootstrap import bootstrap

bootstrap()
from livespec.commands.resolve_template import main

raise SystemExit(main())
