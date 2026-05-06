"""no_inheritance — direct-parent allowlist for `class X(Y):` in `livespec/**`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-inheritance` row), `class X(Y):`
inside `.claude-plugin/scripts/livespec/**` is forbidden when
`Y` is not in the closed direct-parent allowlist:
`{Exception, BaseException, LivespecError, Protocol,
NamedTuple, TypedDict}`. This codifies the flat-composition
direction and the v013 M5 leaf-closed tightening:
`LivespecError` subclasses themselves are NOT acceptable
bases — `class RateLimitError(UsageError):` is rejected even
though `UsageError` is itself a `LivespecError` subclass.
`LivespecError` itself remains an open extension point.

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, and inspects every
`ClassDef` node's `bases` list. Each base is rendered via
`ast.unparse` and the rightmost name (e.g., `typing.Protocol`
→ `Protocol`) is checked against the allowlist. Any base
outside the allowlist emits a structlog ERROR carrying the
file path, line number, class name, and offending base; the
script exits 1. With no violations, exits 0.

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_LIVESPEC_TREE = Path(".claude-plugin") / "scripts" / "livespec"
_ALLOWED_PARENTS = frozenset(
    {"Exception", "BaseException", "LivespecError", "Protocol", "NamedTuple", "TypedDict"}
)


def _base_terminal_name(*, base: ast.expr) -> str:
    rendered = ast.unparse(base)
    return rendered.rsplit(".", maxsplit=1)[-1]


def _find_disallowed_inheritances(*, source: str) -> list[tuple[int, str, str]]:
    tree = ast.parse(source)
    out: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            terminal = _base_terminal_name(base=base)
            if terminal not in _ALLOWED_PARENTS:
                out.append((node.lineno, node.name, ast.unparse(base)))
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
    log = structlog.get_logger("no_inheritance")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    offenders: list[tuple[Path, int, str, str]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            for lineno, class_name, base in _find_disallowed_inheritances(source=source):
                offenders.append((py_file.relative_to(cwd), lineno, class_name, base))
    if offenders:
        for path, lineno, class_name, base in offenders:
            log.error(
                "class base outside direct-parent allowlist",
                file=str(path),
                line=lineno,
                class_name=class_name,
                base=base,
                allowlist=sorted(_ALLOWED_PARENTS),
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
