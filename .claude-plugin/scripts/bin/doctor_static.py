#!/usr/bin/env python3
"""Shebang wrapper for doctor_static. No logic; see livespec.doctor.run_static."""

from _bootstrap import bootstrap

bootstrap()

from livespec.doctor.run_static import main

raise SystemExit(main())
