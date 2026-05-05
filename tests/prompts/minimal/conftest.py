"""Shared sys.path setup for tests/prompts/minimal/.

Adds `tests/prompts/minimal/` to `sys.path` so test modules in
this subdirectory can `import _assertions` (the per-template
`ASSERTIONS` dict). Mirrors the `tests/prompts/livespec/conftest.py`
pattern; per SPECIFICATION/contracts.md §"Prompt-QA harness
contract" (v014), per-template assertion registries live under
`tests/prompts/<template>/_assertions.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__: list[str] = []


sys.path.insert(0, str(Path(__file__).resolve().parent))
