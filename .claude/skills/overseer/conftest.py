"""Test bootstrap for the host-only overseer modules.

These beside-tests are NOT part of the product ``tests/`` tree (the default
``pytest testpaths=["tests"]`` does not collect them). Run them explicitly:

    uv run pytest .claude/skills/overseer/ -q

Adding this directory to ``sys.path`` lets ``import registry`` / ``import
signals`` resolve when pytest collects the beside-tests.
"""

import sys
from pathlib import Path

_HERE = str(Path(__file__).parent)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
