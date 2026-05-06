"""Shared sys.path setup for tests/e2e/.

Adds `tests/e2e/` to `sys.path` so test modules can `import fake_claude`
without per-module sys.path manipulation. Mirrors the tests/prompts/conftest.py
pattern per SPECIFICATION/contracts.md §"E2E harness contract".
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__: list[str] = []


sys.path.insert(0, str(Path(__file__).resolve().parent))
