"""no_inheritance — `class X(Y):` only allowed for allowlisted parents.

Per `python-skill-script-style-requirements.md` line 2088:

    AST: forbids `class X(Y):` in
    `.claude-plugin/scripts/livespec/**` where `Y` is not in
    the **direct-parent allowlist** `{Exception, BaseException,
    LivespecError, Protocol, NamedTuple, TypedDict}`.
    `LivespecError` subclasses are NOT acceptable bases (v013
    M5 tightening enforces leaf-closed intent); `class
    RateLimitError(UsageError):` is rejected even though
    `UsageError` is itself a `LivespecError` subclass.

The check walks `.claude-plugin/scripts/livespec/**.py`, parses
each AST, and for every `ClassDef` with at least one explicit
base, verifies that every base is one of the allowlisted names
(by Name-id; Attribute access like `typing.Protocol` is also
recognized via the rightmost attribute name). One structlog
diagnostic per offender; exit 1 if any class extends a
non-allowlisted parent.

A `class Foo:` with no explicit bases (implicit `object`) is
accepted — the rule's purview is explicit inheritance only.
Generic parameterization like `class Foo(Generic[T]):` is NOT
inheritance and is allowlist-free; this cycle does not specially
handle it because the only Generic-like base in livespec scope
expected is `Protocol`/`NamedTuple`/`TypedDict`, all already in
the allowlist.
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
_DIRECT_PARENT_ALLOWLIST = frozenset(
    {
        "Exception",
        "BaseException",
        "LivespecError",
        "Protocol",
        "NamedTuple",
        "TypedDict",
    }
)


def _base_name(*, base: ast.expr) -> str | None:
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    return None


def _find_violations(*, tree: ast.Module) -> list[tuple[int, str, str]]:
    offenders: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            name = _base_name(base=base)
            if name is None or name not in _DIRECT_PARENT_ALLOWLIST:
                offenders.append((node.lineno, node.name, name or "<complex-expr>"))
    return offenders


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
    log = structlog.get_logger("no_inheritance")
    cwd = Path.cwd()
    tree_root = cwd / _LIVESPEC_TREE
    if not tree_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=tree_root):
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        for lineno, class_name, base_name in _find_violations(tree=module_ast):
            log.error(
                "class extends non-allowlisted parent",
                path=str(py_file.relative_to(cwd)),
                line=lineno,
                class_name=class_name,
                base=base_name,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
