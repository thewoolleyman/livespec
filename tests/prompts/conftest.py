"""Shared sys.path setup for tests/prompts/.

Adds `tests/prompts/` to `sys.path` so child test modules can
`import _harness` without per-module sys.path manipulation. Per
SPECIFICATION/contracts.md §"Prompt-QA harness contract" (v014),
the harness is a dedicated test-infrastructure module at
`tests/prompts/_harness.py`; placing the directory on the import
path lets test modules consume it via a simple top-level import.

Per-template subdirectories (`tests/prompts/livespec/`,
`tests/prompts/minimal/`) ship their own `conftest.py` that adds
the per-template directory so per-template test modules can
`import _assertions` likewise.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__: list[str] = []


sys.path.insert(0, str(Path(__file__).resolve().parent))
