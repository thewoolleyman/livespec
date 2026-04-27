"""public_api_result_typed: enforce Result/IOResult on every public def.

Per python-skill-script-style-requirements.md canonical target list
line 1884 (`just check-public-api-result-typed`):

    AST: every public function (per `__all__` declaration; see
    `check-all-declared`) returns `Result` or `IOResult` per
    annotation, except supervisors at the side-effect boundary
    (`main()` in `commands/**.py` and `doctor/run_static.py`)
    and the `build_parser` factory in `commands/**.py`.

The rule encodes v012 L9: every published function in livespec/**
that participates in the Railway-Oriented-Programming pipeline
returns a `Result` or `IOResult` carrier. The implementation
recognizes two ways the railway envelope can be present:

1. **Direct annotation** — return type is `Result[...]` or
   `IOResult[...]` (bare or subscripted).
2. **Decorator-wrapped** — function carries
   `@impure_safe(...)` (returns library lifts the bare
   annotation into `IOResult[X, <known-exceptions>]`) or
   `@safe(...)` (lifts into `Result`). The source-level
   annotation shows the inner type; the runtime return type
   is the wrapped carrier.

Documented exemptions (functions that legitimately do NOT
return a railway carrier because they construct artifacts
the railway then composes around):

- `main` in `commands/**.py` and `doctor/run_static.py`:
  supervisor at the side-effect boundary; collapses
  IOResult into an integer exit code.
- `build_parser` in `commands/**.py` and
  `doctor/run_static.py`: argparse factory; the parsing step
  itself is wrapped in `livespec.io.cli.parse_args`.
- `make_validator` in `validate/**.py`: validator factory;
  returns a `TypedValidator[T]` Protocol whose `__call__`
  returns `Result`.
- `get_logger` in `io/structlog_facade.py`: structlog
  facade factory; returns a `Logger`.
- `compile_schema` in `io/fastjsonschema_facade.py`:
  fastjsonschema facade factory; returns a `Validator`.
- `rop_pipeline` in `types.py`: class decorator returning
  the decorated class unchanged.

Package-private helper modules (filename matching `_*.py`,
e.g., `commands/_seed_helpers.py`) are skipped — their
public surface is consumed only within the same directory
by callers that ARE on the railway, and the helpers
themselves are typically pure render/format functions that
cannot fail and don't need a railway envelope.

A missing return annotation IS a violation (the rule is about
the annotated surface — pyright strict mode also requires it).
"""

from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path

__all__: list[str] = [
    "check_file",
    "main",
]


log = logging.getLogger(__name__)

_LIVESPEC_DIR = Path(".claude-plugin/scripts/livespec")
_COMMANDS_DIR = Path(".claude-plugin/scripts/livespec/commands")
_DOCTOR_RUN_STATIC = Path(".claude-plugin/scripts/livespec/doctor/run_static.py")
_VALIDATE_DIR = Path(".claude-plugin/scripts/livespec/validate")
_STRUCTLOG_FACADE = Path(".claude-plugin/scripts/livespec/io/structlog_facade.py")
_FASTJSON_FACADE = Path(".claude-plugin/scripts/livespec/io/fastjsonschema_facade.py")
_TYPES_MODULE = Path(".claude-plugin/scripts/livespec/types.py")
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"

_RAILWAY_TYPES: frozenset[str] = frozenset({"Result", "IOResult"})
_RAILWAY_DECORATORS: frozenset[str] = frozenset({"impure_safe", "safe"})


def main() -> int:
    """Walk livespec/**.py; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    livespec_dir = repo_root / _LIVESPEC_DIR
    if not livespec_dir.is_dir():
        log.error("%s does not exist; cannot check public_api_result_typed", livespec_dir)
        return 1
    failures: list[str] = []
    for path in sorted(livespec_dir.rglob("*.py")):
        if _VENDOR_SUBSTR in path.parts or _PYCACHE_SUBSTR in path.parts:
            continue
        if _is_private_module(path=path):
            continue
        relative = path.relative_to(repo_root)
        for v in check_file(path=path, relative=relative):
            failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("public_api_result_typed: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path, relative: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    listed = _public_names(tree=tree)
    if listed is None:
        return []  # all_declared catches missing/malformed __all__
    funcs = _module_functions(tree=tree)
    violations: list[str] = []
    for name in listed:
        func = funcs.get(name)
        if func is None:
            continue
        if _is_exempt(name=name, relative=relative):
            continue
        if _has_railway_decorator(func=func):
            continue
        message = _check_return_annotation(func=func)
        if message is not None:
            violations.append(f"line {func.lineno}: public def `{name}` {message}")
    return violations


def _is_private_module(*, path: Path) -> bool:
    """True iff the filename starts with `_` (other than `__init__.py`)."""
    name = path.name
    return name.startswith("_") and name != "__init__.py"


def _public_names(*, tree: ast.Module) -> list[str] | None:
    """Extract the names listed in module-top `__all__: list[str] = [...]`."""
    for node in tree.body:
        if not (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__all__"
        ):
            continue
        value = node.value
        if not isinstance(value, ast.List):
            return None
        names: list[str] = []
        for element in value.elts:
            if not (isinstance(element, ast.Constant) and isinstance(element.value, str)):
                return None
            names.append(element.value)
        return names
    return None


def _module_functions(
    *,
    tree: ast.Module,
) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    """Map of module-top function-name → FunctionDef node."""
    funcs: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            funcs[node.name] = node
    return funcs


def _is_exempt(*, name: str, relative: Path) -> bool:
    """True iff `(name, relative)` matches one of the documented exemptions."""
    is_command = _is_under(relative=relative, scope=_COMMANDS_DIR)
    is_doctor_run_static = relative == _DOCTOR_RUN_STATIC
    is_validate = _is_under(relative=relative, scope=_VALIDATE_DIR)
    if name == "main" and (is_command or is_doctor_run_static):
        return True
    if name == "build_parser" and (is_command or is_doctor_run_static):
        return True
    if name == "make_validator" and is_validate:
        return True
    if name == "get_logger" and relative == _STRUCTLOG_FACADE:
        return True
    if name == "compile_schema" and relative == _FASTJSON_FACADE:
        return True
    return name == "rop_pipeline" and relative == _TYPES_MODULE


def _has_railway_decorator(
    *,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """True iff `func` carries `@impure_safe(...)` or `@safe(...)`.

    Recognizes both bare-name (`@impure_safe`) and parameterized
    (`@impure_safe(exceptions=(...))`) forms.
    """
    for decorator in func.decorator_list:
        target: ast.expr = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Name) and target.id in _RAILWAY_DECORATORS:
            return True
        if isinstance(target, ast.Attribute) and target.attr in _RAILWAY_DECORATORS:
            return True
    return False


def _check_return_annotation(
    *,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    """Return None if the annotation is Result/IOResult, else a violation message."""
    annotation = func.returns
    if annotation is None:
        return "lacks a return annotation; expected Result[...] or IOResult[...]"
    if _is_railway_annotation(annotation=annotation):
        return None
    rendered = ast.unparse(annotation)
    return f"returns `{rendered}`; expected Result[...] or IOResult[...]"


def _is_railway_annotation(*, annotation: ast.expr) -> bool:
    """True iff annotation is `Result` / `IOResult` (bare or subscripted)."""
    if isinstance(annotation, ast.Name):
        return annotation.id in _RAILWAY_TYPES
    if isinstance(annotation, ast.Subscript) and isinstance(annotation.value, ast.Name):
        return annotation.value.id in _RAILWAY_TYPES
    return False


def _is_under(*, relative: Path, scope: Path) -> bool:
    return (
        len(relative.parts) >= len(scope.parts) + 1
        and Path(*relative.parts[: len(scope.parts)]) == scope
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
