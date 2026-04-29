"""file_lloc — file ≤ 200 logical lines (Phase 4 enforcement).

Per `python-skill-script-style-requirements.md` §"Complexity
thresholds" (lines 1689-1711) and Plan Phase 4 line 1677, every
Python file under the in-scope trees
(`.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, `<repo-root>/dev-tooling/**`)
MUST be ≤ 200 logical lines.

A "logical line" is the canonical Python language definition: a
`tokenize.NEWLINE` token terminates one logical line. Blank lines
and comment-only physical lines emit `tokenize.NL` (not
`NEWLINE`) and are NOT counted. Multi-physical-line statements
(triple-quoted strings spanning lines, parenthesized
continuations, etc.) emit exactly ONE `NEWLINE` and count as one
logical line.

The script is invoked as `python3 dev-tooling/checks/file_lloc.py`
with no CLI flags; it walks the trees rooted at the current
working directory and exits 0 if every file is ≤ 200 LLOC, exits
1 otherwise (emitting one structured-log diagnostic per offender
via the vendored structlog).

Output discipline: per spec lines 1738-1762, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time
(dev-tooling/checks scripts deliberately do NOT import
`livespec`, so they cannot reuse the package's structlog
configuration).
"""

from __future__ import annotations

import sys
import tokenize
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_LLOC_CEILING = 200
_IN_SCOPE_TREES: tuple[Path, ...] = (
    Path(".claude-plugin") / "scripts" / "livespec",
    Path(".claude-plugin") / "scripts" / "bin",
    Path("dev-tooling"),
)


def _count_logical_lines(*, path: Path) -> int:
    with path.open("rb") as handle:
        return sum(
            1 for token in tokenize.tokenize(handle.readline) if token.type == tokenize.NEWLINE
        )


def _iter_python_files(*, root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("file_lloc")
    cwd = Path.cwd()
    offenders: list[tuple[Path, int]] = []
    for tree in _IN_SCOPE_TREES:
        tree_root = cwd / tree
        if not tree_root.is_dir():
            continue
        for py_file in _iter_python_files(root=tree_root):
            lloc = _count_logical_lines(path=py_file)
            if lloc > _LLOC_CEILING:
                offenders.append((py_file.relative_to(cwd), lloc))
    if offenders:
        for rel_path, lloc in offenders:
            log.error(
                "file exceeds LLOC ceiling",
                path=str(rel_path),
                lloc=lloc,
                ceiling=_LLOC_CEILING,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
