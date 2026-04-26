#!/usr/bin/env python3
"""Shebang wrapper for doctor static phase. No logic; see livespec.doctor.run_static for implementation."""
from _bootstrap import bootstrap
bootstrap()
from livespec.doctor.run_static import main

raise SystemExit(main())
