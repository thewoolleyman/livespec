"""claude_md_coverage: every scoped directory carries a CLAUDE.md.

Per python-skill-script-style-requirements.md canonical target list
line 1896:

    Every directory under `scripts/` (excluding `_vendor/`
    subtree), `tests/`, and `dev-tooling/` contains a `CLAUDE.md`.

The rule is the strict DoD-13: per-directory CLAUDE.md is the
agent-orientation surface; absent CLAUDE.md means an agent
operating in that directory has no scoped guidance.

Scope: directories under
- `.claude-plugin/scripts/livespec/**` (the package tree)
- `.claude-plugin/scripts/bin/`
- `tests/**` (excluding `tests/fixtures/` subtrees per the
  CLAUDE.md convention — fixtures are payload, not orientable code)
- `dev-tooling/**`

Excluded:
- `_vendor/` subtrees (vendored-library content has its own
  upstream LICENSE; agent-orientation does not apply).
- `__pycache__/` directories.
- `tests/fixtures/` subtrees at any depth.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

__all__: list[str] = [
    "check_directory",
    "main",
]


log = logging.getLogger(__name__)

_SCOPE_DIRS: tuple[Path, ...] = (
    Path(".claude-plugin/scripts/livespec"),
    Path(".claude-plugin/scripts/bin"),
    Path("tests"),
    Path("dev-tooling"),
)
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"
_FIXTURES_SUBSTR = "fixtures"


def main() -> int:
    """Walk scope dirs; return 0 on pass, 1 on any directory missing CLAUDE.md."""
    repo_root = Path.cwd()
    failures: list[str] = []
    for scope in _SCOPE_DIRS:
        scope_dir = repo_root / scope
        if not scope_dir.is_dir():
            continue
        for d in sorted(_walk_directories(root=scope_dir)):
            for v in check_directory(directory=d):
                failures.append(f"{d}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("claude_md_coverage: %d violation(s)", len(failures))
        return 1
    return 0


def _walk_directories(*, root: Path) -> list[Path]:
    """Yield every directory at or under `root` that should carry a CLAUDE.md.

    Excludes `_vendor/`, `__pycache__/`, and any directory whose path
    contains a `fixtures` segment (covers `tests/fixtures/` subtrees
    at any depth).
    """
    out: list[Path] = []
    if not root.is_dir():
        return out
    for path in [root, *root.rglob("*")]:
        if not path.is_dir():
            continue
        parts = path.parts
        if _VENDOR_SUBSTR in parts or _PYCACHE_SUBSTR in parts:
            continue
        if _FIXTURES_SUBSTR in parts:
            continue
        out.append(path)
    return out


def check_directory(*, directory: Path) -> list[str]:
    """Return a one-element violation list if CLAUDE.md is missing; empty if present."""
    if (directory / "CLAUDE.md").is_file():
        return []
    return ["lacks CLAUDE.md"]


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
