"""claude_md_coverage — every in-scope directory has a CLAUDE.md.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-claude-md-coverage` row), every
directory under `.claude-plugin/scripts/` (excluding the
`_vendor/` subtree), `<repo-root>/tests/` (excluding the
`fixtures/` subtree at any depth), and `<repo-root>/dev-
tooling/` MUST contain a `CLAUDE.md` file describing the
local constraints an agent working in that directory must
satisfy.

The check walks each in-scope root, descends every
subdirectory, and surfaces any directory missing its
`CLAUDE.md`. Exemptions are matched by directory-path
ancestry: any directory whose path includes a `_vendor/`,
`fixtures/`, or `__pycache__/` component is skipped, along
with all descendants.

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_COVERED_ROOTS = (
    Path(".claude-plugin") / "scripts",
    Path("tests"),
    Path("dev-tooling"),
)
_EXEMPT_PATH_COMPONENTS = frozenset({"_vendor", "fixtures", "__pycache__"})


def _is_exempt_directory(*, path: Path) -> bool:
    return any(part in _EXEMPT_PATH_COMPONENTS for part in path.parts)


def _iter_in_scope_dirs(*, repo_root: Path, scope_root: Path) -> list[Path]:
    """Return every in-scope directory under scope_root (including scope_root itself)."""
    if not scope_root.is_dir():
        return []
    out: list[Path] = [scope_root]
    for path in sorted(scope_root.rglob("*")):
        if not path.is_dir():
            continue
        rel_to_repo = path.relative_to(repo_root)
        if _is_exempt_directory(path=rel_to_repo):
            continue
        out.append(path)
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
    offenders: list[Path] = []
    for root_rel in _COVERED_ROOTS:
        scope_root = cwd / root_rel
        for directory in _iter_in_scope_dirs(repo_root=cwd, scope_root=scope_root):
            claude_md = directory / "CLAUDE.md"
            if not claude_md.is_file():
                offenders.append(directory.relative_to(cwd))
    if offenders:
        for path in offenders:
            log.error(
                "directory missing required CLAUDE.md",
                directory=str(path),
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
