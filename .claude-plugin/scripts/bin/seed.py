#!/usr/bin/env python3
"""Shebang wrapper for seed. No logic; see livespec.commands.seed for implementation."""

from _bootstrap import bootstrap

bootstrap()
from livespec.commands.seed import main

raise SystemExit(main())
