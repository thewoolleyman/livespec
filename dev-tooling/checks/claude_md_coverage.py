"""claude_md_coverage — every required directory carries a `CLAUDE.md`.

Per `python-skill-script-style-requirements.md` §"Agent-oriented
documentation: CLAUDE.md coverage" (lines 2142-2176) and the
canonical-target table line 2094:

    Every directory under `scripts/` (with the entire `_vendor/`
    subtree explicitly excluded), `<repo-root>/tests/` (with the
    entire `fixtures/` subtree excluded at any depth — e.g.,
    `tests/fixtures/`, `tests/e2e/fixtures/` per v014 N9), and
    `<repo-root>/dev-tooling/` MUST contain a `CLAUDE.md`.

The check walks each of the three roots, skips the carve-outs,
skips `__pycache__` (build artifact), and reports any directory
that lacks `CLAUDE.md`. Cycle 51 covers the
`.claude-plugin/scripts/` root canonically; the same logic
extends to `tests/` and `dev-tooling/` via the same walker.
"""

from __future__ import annotations

import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_SCRIPTS_ROOT = Path(".claude-plugin") / "scripts"
_TESTS_ROOT = Path("tests")
_DEV_TOOLING_ROOT = Path("dev-tooling")
_VENDOR_NAME = "_vendor"
_FIXTURES_NAME = "fixtures"
_PYCACHE_NAME = "__pycache__"
_CLAUDE_MD = "CLAUDE.md"


def _is_carved_out(*, dir_path: Path, root: Path) -> bool:
    parts = dir_path.relative_to(root).parts
    if _PYCACHE_NAME in parts:
        return True
    # _vendor is only carved under scripts/.
    if root.name == "scripts" and (_VENDOR_NAME in parts or dir_path.name == _VENDOR_NAME):
        return True
    # fixtures is carved at any depth under tests/ (its subtree, not the
    # fixtures dir itself which gets the optional carve-out per spec).
    if root == _TESTS_ROOT and _FIXTURES_NAME in parts:
        return True
    return False


def _iter_required_dirs(*, root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    if not _is_carved_out(dir_path=root, root=root):
        out.append(root)
    for d in sorted(root.rglob("*")):
        if not d.is_dir():
            continue
        if _is_carved_out(dir_path=d, root=root):
            continue
        out.append(d)
    return out


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("claude_md_coverage")
    cwd = Path.cwd()
    found_any = False
    for rel_root in (_SCRIPTS_ROOT, _TESTS_ROOT, _DEV_TOOLING_ROOT):
        abs_root = cwd / rel_root
        if not abs_root.is_dir():
            continue
        for d in _iter_required_dirs(root=abs_root):
            if (d / _CLAUDE_MD).is_file():
                continue
            log.error(
                "directory missing CLAUDE.md",
                path=str(d.relative_to(cwd)),
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
