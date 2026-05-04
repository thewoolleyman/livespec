"""file_lloc — per-file LLOC two-tier policy (soft warn at 200, hard fail at 250).

Per `SPECIFICATION/constraints.md` §"File LLOC ceiling" (post-v005),
every `.py` file under `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, and `<repo-root>/dev-tooling/**`
SHOULD have at most 200 logical lines of code (LLOC) and MUST have
at most 250 LLOC.

LLOC excludes blank lines, comment-only lines, and module/class/
function docstrings — it counts only executable statements. The
check tokenizes each `.py` via the standard library `tokenize`
module and filters docstring lines via `ast`.

Two-tier policy:

- 201-250 LLOC — SOFT ceiling. The file passes the check (exit 0)
  but a `warning`-level structured diagnostic is emitted to stderr
  flagging the file for refactoring.
- > 250 LLOC — HARD ceiling. The file fails the check (exit 1)
  with an `error`-level structured diagnostic.

The two-tier split removes the mid-Green-amend wedge where an
in-progress refactor naturally pushes LLOC above 200 and would
otherwise force a sibling-module extraction in the same amend.

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
    """Return line numbers covered by module/class/function docstrings."""
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
    log = structlog.get_logger("file_lloc")
    cwd = Path.cwd()
    soft_offenders: list[tuple[Path, int]] = []
    hard_offenders: list[tuple[Path, int]] = []
    for tree_rel in _COVERED_TREES:
        root = cwd / tree_rel
        if not root.is_dir():
            continue
        for py_file in sorted(root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            lloc = _count_lloc(source=source)
            if lloc > _LLOC_HARD_CEILING:
                hard_offenders.append((py_file.relative_to(cwd), lloc))
            elif lloc > _LLOC_SOFT_CEILING:
                soft_offenders.append((py_file.relative_to(cwd), lloc))
    for path, lloc in soft_offenders:
        log.warning(
            "file LLOC exceeds 200-line soft ceiling — flag for refactor",
            file=str(path),
            lloc=lloc,
            soft_ceiling=_LLOC_SOFT_CEILING,
            hard_ceiling=_LLOC_HARD_CEILING,
        )
    for path, lloc in hard_offenders:
        log.error(
            "file LLOC exceeds 250-line hard ceiling",
            file=str(path),
            lloc=lloc,
            hard_ceiling=_LLOC_HARD_CEILING,
        )
    if hard_offenders:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
