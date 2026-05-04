"""no_lloc_soft_warnings — release-gate rejecting any 201-250 LLOC soft-band file.

Per `SPECIFICATION/constraints.md` §"File LLOC ceiling" (post-v008),
this is the release-gate analog of `check-no-todo-registry`: not in
`just check`, runs only on the release-tag CI workflow
(`.github/workflows/release-tag.yml`, fires on `v*` tag push). It
rejects any first-party `.py` file in the 201-250 LLOC soft band,
forcing refactor work to land before any release tag.

The check tokenizes each `.py` via the same algorithm as
`file_lloc.py` (the per-commit two-tier check). Helpers are
duplicated rather than imported because each `dev-tooling/checks/
<name>.py` is a self-contained Python module per the directory's
CLAUDE.md.

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import ast
import sys
import tokenize
from io import BytesIO
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_COVERED_TREES = (
    Path(".claude-plugin") / "scripts" / "livespec",
    Path(".claude-plugin") / "scripts" / "bin",
    Path("dev-tooling"),
)
_LLOC_SOFT_CEILING = 200
_LLOC_HARD_CEILING = 250
_NON_LLOC_TOKEN_TYPES = frozenset(
    {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
    }
)


def _docstring_lines(*, source: str) -> set[int]:
    tree = ast.parse(source)
    out: set[int] = set()
    holders: list[ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            holders.append(node)
    for holder in holders:
        body = holder.body
        if (
            len(body) > 0
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            first = body[0]
            assert first.end_lineno is not None  # noqa: S101 — narrowing for arithmetic
            out.update(range(first.lineno, first.end_lineno + 1))
    return out


def _count_lloc(*, source: str) -> int:
    docstring_lines = _docstring_lines(source=source)
    code_lines: set[int] = set()
    tokens = tokenize.tokenize(BytesIO(source.encode("utf-8")).readline)
    for tok in tokens:
        if tok.type in _NON_LLOC_TOKEN_TYPES:
            continue
        line = tok.start[0]
        if line in docstring_lines:
            continue
        code_lines.add(line)
    return len(code_lines)


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("no_lloc_soft_warnings")
    cwd = Path.cwd()
    soft_band_offenders: list[tuple[Path, int]] = []
    for tree_rel in _COVERED_TREES:
        root = cwd / tree_rel
        if not root.is_dir():
            continue
        for py_file in sorted(root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            lloc = _count_lloc(source=source)
            if _LLOC_SOFT_CEILING < lloc <= _LLOC_HARD_CEILING:
                soft_band_offenders.append((py_file.relative_to(cwd), lloc))
    if soft_band_offenders:
        for path, lloc in soft_band_offenders:
            log.error(
                "file in 201-250 LLOC soft band (release-gate violation)",
                file=str(path),
                lloc=lloc,
                soft_ceiling=_LLOC_SOFT_CEILING,
                hard_ceiling=_LLOC_HARD_CEILING,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
