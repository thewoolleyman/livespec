"""comment_line_anchors — ban line-number anchors in docstrings + comments.

Line-number anchors silently rot on any edit to the referenced
file: a single inserted paragraph above shifts every downstream
reference without any compiler / linter / test signal. Comments
should explain WHY (non-obvious constraints, hidden invariants,
surprising behavior) — not WHAT (already obvious from well-named
identifiers + signatures). Cross-references to specs or other
code should use section names or symbol names, never line
numbers.

Walks `.py` files under `.claude-plugin/scripts/`, `dev-tooling/`,
and `tests/` from CWD (excluding `_vendor/`). For each file,
extracts module/class/function docstrings via AST and `#`
comment tokens via tokenize. Applies the anchor regex against
those text spans only — string literals, identifiers, and code
are not in scope. Emits a structured JSON diagnostic for each
hit and exits non-zero on any match.

Output discipline: per spec, `print` and direct `sys.stderr.write`
are banned in dev-tooling/**; diagnostics flow through structlog
(JSON to stderr) per the vendor-path-aware import below.
"""

from __future__ import annotations

import ast
import re
import sys
import tokenize
from pathlib import Path
from typing import cast

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_TARGET_DIRS = (
    Path(".claude-plugin") / "scripts",
    Path("dev-tooling"),
    Path("tests"),
)
_VENDOR_MARKER = "_vendor"
_LINE_ANCHOR_RE = re.compile("\\b[Ll]ines?\\s+~?\\d+(?:[-\\u2013\\u2014]\\d+)?")
_REMINDER = (
    "Comments should explain WHY (non-obvious constraints, hidden "
    "invariants, surprising behavior) — not WHAT (already obvious "
    "from well-named identifiers + signatures). Line-number anchors "
    "rot on any edit; use section names or symbol names instead, "
    "never line numbers."
)
_AST_DOCSTRING_HOSTS = ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


def _configure_logger() -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    return structlog.get_logger("comment_line_anchors")


def _docstring_hits(*, source: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, _AST_DOCSTRING_HOSTS):
            continue
        docstring = ast.get_docstring(node, clean=False)
        if docstring is None:
            continue
        first = cast(ast.Expr, node.body[0])
        for line_idx, line_text in enumerate(docstring.splitlines()):
            for match in _LINE_ANCHOR_RE.finditer(line_text):
                hits.append((first.lineno + line_idx, match.group(0)))
    return hits


def _comment_hits(*, source: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    tokens = list(
        tokenize.generate_tokens(iter(source.splitlines(keepends=True)).__next__),
    )
    for tok in tokens:
        if tok.type != tokenize.COMMENT:
            continue
        for match in _LINE_ANCHOR_RE.finditer(tok.string):
            hits.append((tok.start[0], match.group(0)))
    return hits


def _scan_file(*, path: Path) -> list[tuple[int, str]]:
    source = path.read_text(encoding="utf-8")
    return _docstring_hits(source=source) + _comment_hits(source=source)


def _walk_targets(*, cwd: Path) -> list[Path]:
    paths: list[Path] = []
    for target in _TARGET_DIRS:
        target_root = cwd / target
        if not target_root.is_dir():
            continue
        for path in sorted(target_root.rglob("*.py")):
            if _VENDOR_MARKER in path.parts:
                continue
            paths.append(path)
    return paths


def main() -> int:
    log = _configure_logger()
    cwd = Path.cwd()
    offenders = 0
    for path in _walk_targets(cwd=cwd):
        for lineno, matched in _scan_file(path=path):
            offenders += 1
            log.error(
                "line-number anchor in docstring or comment",
                check_id="comment-line-anchor",
                path=str(path.relative_to(cwd)),
                lineno=lineno,
                matched=matched,
                hint=_REMINDER,
            )
    if offenders:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
