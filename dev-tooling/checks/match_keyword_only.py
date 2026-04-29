"""match_keyword_only — match patterns use keyword sub-patterns for livespec classes.

Per `python-skill-script-style-requirements.md` line 2087:

    AST: every `match` statement's class pattern resolving to a
    livespec-authored class binds via keyword sub-patterns
    (`Foo(x=x)`), not positional (`Foo(x)`). Third-party
    library class destructures (`returns`-package types) are
    permitted positionally.

Positional class destructures rely on `__match_args__`
ordering, which is fragile and tightly couples the producer's
field order to every consumer call site. Keyword destructures
decouple them.

The check walks the livespec tree, finds every
`MatchClass` AST node, and rejects any with positional
sub-patterns (non-empty `patterns` list) UNLESS the class name
is in the third-party-exemption set (the `returns`-package ROP
types: `IOResult`, `IOSuccess`, `IOFailure`, `Result`,
`Success`, `Failure`).

Cycle 41 pins the canonical violation: a `case Foo(x):`
positional pattern on a livespec-authored class is rejected.
The exemption for `returns`-package types is verified by a
companion pass-case test.
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
_RETURNS_EXEMPT_NAMES = frozenset(
    {"IOResult", "IOSuccess", "IOFailure", "Result", "Success", "Failure"}
)


def _class_pattern_name(*, cls_node: ast.expr) -> str | None:
    if isinstance(cls_node, ast.Name):
        return cls_node.id
    if isinstance(cls_node, ast.Attribute):
        return cls_node.attr
    return None


def _find_violations(*, tree: ast.Module) -> list[tuple[int, str]]:
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.MatchClass):
            continue
        if not node.patterns:
            continue
        name = _class_pattern_name(cls_node=node.cls)
        if name is not None and name in _RETURNS_EXEMPT_NAMES:
            continue
        offenders.append((node.cls.lineno, name or "<complex-expr>"))
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
    log = structlog.get_logger("match_keyword_only")
    cwd = Path.cwd()
    tree_root = cwd / _LIVESPEC_TREE
    if not tree_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=tree_root):
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        for lineno, class_name in _find_violations(tree=module_ast):
            log.error(
                "positional class match-pattern (use keyword sub-patterns)",
                path=str(py_file.relative_to(cwd)),
                line=lineno,
                class_name=class_name,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
