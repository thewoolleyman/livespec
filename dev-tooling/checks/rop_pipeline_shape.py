"""rop_pipeline_shape — `@rop_pipeline` classes carry exactly one public method.

Per `python-skill-script-style-requirements.md` §"ROP pipeline shape"
(lines 581-618) and the canonical-target table line 2078:

    AST: every class decorated with `@rop_pipeline` carries
    exactly one public method (the entry point); other methods
    are `_`-prefixed; dunders aren't counted. Enforces the
    Command / Use Case Interactor pattern at the class level.

The decorator itself is a runtime no-op declared in
`livespec.types`. Recognized at the AST level by name — either
bare (`@rop_pipeline`) or attribute (`@types.rop_pipeline`) or
parameterized (`@rop_pipeline(...)`). Helper classes and helper
modules NOT carrying the decorator are exempt.

A "public method" means a `FunctionDef` (or `AsyncFunctionDef`)
inside the class body whose name does not start with `_` and
does not match the dunder pattern `^__.+__$`. Two or more such
methods on a single `@rop_pipeline` class fails the check.

The check walks `.claude-plugin/scripts/livespec/**.py`. One
structlog diagnostic per offender; exit 1 if any
`@rop_pipeline` class has more than one public method.
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
_DECORATOR_NAME = "rop_pipeline"


def _decorator_matches(*, decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Name):
        return decorator.id == _DECORATOR_NAME
    if isinstance(decorator, ast.Attribute):
        return decorator.attr == _DECORATOR_NAME
    if isinstance(decorator, ast.Call):
        return _decorator_matches(decorator=decorator.func)
    return False


_DUNDER_MIN_LENGTH = 4


def _is_dunder(*, name: str) -> bool:
    return name.startswith("__") and name.endswith("__") and len(name) >= _DUNDER_MIN_LENGTH


def _public_method_names(*, class_node: ast.ClassDef) -> list[str]:
    names: list[str] = []
    for stmt in class_node.body:
        if not isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if stmt.name.startswith("_"):
            continue
        if _is_dunder(name=stmt.name):
            continue
        names.append(stmt.name)
    return names


def _find_violations(*, tree: ast.Module) -> list[tuple[int, str, list[str]]]:
    offenders: list[tuple[int, str, list[str]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(_decorator_matches(decorator=d) for d in node.decorator_list):
            continue
        publics = _public_method_names(class_node=node)
        if len(publics) > 1:
            offenders.append((node.lineno, node.name, publics))
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
    log = structlog.get_logger("rop_pipeline_shape")
    cwd = Path.cwd()
    tree_root = cwd / _LIVESPEC_TREE
    if not tree_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=tree_root):
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        for lineno, class_name, publics in _find_violations(tree=module_ast):
            log.error(
                "@rop_pipeline class has more than one public method",
                path=str(py_file.relative_to(cwd)),
                line=lineno,
                class_name=class_name,
                public_methods=publics,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
