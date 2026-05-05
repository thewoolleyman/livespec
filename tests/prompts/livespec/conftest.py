"""Shared sys.path setup for tests/prompts/livespec/.

Adds `tests/prompts/livespec/` to `sys.path` so test modules in
this subdirectory can `import _assertions` (the per-template
`ASSERTIONS` dict). Per SPECIFICATION/contracts.md §"Prompt-QA
harness contract" (v014), per-template assertion registries
live under `tests/prompts/<template>/_assertions.py`; this
conftest mirrors the parent `tests/prompts/conftest.py` to keep
imports flat at the test-module level.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__: list[str] = []


sys.path.insert(0, str(Path(__file__).resolve().parent))
