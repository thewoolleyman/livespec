"""public_api_result_typed — `__all__`-listed publics return Result/IOResult.

Per `python-skill-script-style-requirements.md` §"Module API surface"
(lines 943-960) and the canonical-target table line 2082:

    AST: every public function (per `__all__` declaration) returns
    `Result` or `IOResult` per annotation, OR carries a railway-
    lifting decorator that wraps the source-level annotation
    (`@impure_safe(...)` lifts to `IOResult`, `@safe(...)` lifts to
    `Result` — both recognized by name regardless of bare or
    parameterized form).

Cycle 47 pins ONE narrow violation pattern per v032 D1
one-pattern-per-cycle:

    A public function (listed in `__all__`) annotated `-> int`
    with no `@safe`/`@impure_safe` railway-lifting decorator
    AND whose name is neither `main` (the spec's documented
    supervisor exemption per line 2082) nor `run_*` (the
    in-process command-entry convention per
    `commands/CLAUDE.md`; tightening to require the convention's
    railway return-type is itself deferred to a subsequent
    cycle, NOT cycle 47's responsibility).

`int` is the canonical primitive-Result-incompatible shape that
should never appear on the railway-public surface unwrapped. The
broader return-type catalogue (`-> str`, `-> Path`, `-> None`,
domain dataclass shapes), the rest of the spec exemption list
(`build_parser`, `make_validator`, `get_logger`,
`compile_schema`, `rop_pipeline`), and the `_*.py`
package-private helper carve-out are deferred to subsequent
cycles per v032 D1. The current source tree's `-> int` publics
are all named `main` or `run_propose_change` (a `run_*` function
that ought to return `IOResult` per `commands/CLAUDE.md`; the
ought-IOResult tightening is deferred), so the rule passes
against the existing repo today; the check exists to catch the
next agent who introduces a non-`main`, non-`run_*` `-> int`
public without lifting.
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
_RAILWAY_DECORATORS = frozenset({"safe", "impure_safe"})
_NAME_EXEMPT_EXACT = frozenset({"main"})


def _is_name_exempt(*, fn_name: str) -> bool:
    if fn_name in _NAME_EXEMPT_EXACT:
        return True
    return fn_name.startswith("run_")


def _decorator_name(*, decorator: ast.expr) -> str | None:
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator=decorator.func)
    return None


def _has_railway_decorator(*, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for d in fn.decorator_list:
        name = _decorator_name(decorator=d)
        if name is not None and name in _RAILWAY_DECORATORS:
            return True
    return False


def _is_int_return(*, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return isinstance(fn.returns, ast.Name) and fn.returns.id == "int"


def _all_names(*, tree: ast.Module) -> list[str]:
    for node in tree.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        target = node.target
        if not isinstance(target, ast.Name) or target.id != "__all__":
            continue
        if not isinstance(node.value, ast.List):
            continue
        return [
            elt.value
            for elt in node.value.elts
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        ]
    return []


def _find_violations(*, tree: ast.Module) -> list[tuple[int, str]]:
    declared = set(_all_names(tree=tree))
    if not declared:
        return []
    offenders: list[tuple[int, str]] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.name not in declared:
            continue
        if _is_name_exempt(fn_name=node.name):
            continue
        if not _is_int_return(fn=node):
            continue
        if _has_railway_decorator(fn=node):
            continue
        offenders.append((node.lineno, node.name))
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
    log = structlog.get_logger("public_api_result_typed")
    cwd = Path.cwd()
    tree_root = cwd / _LIVESPEC_TREE
    if not tree_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=tree_root):
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        for lineno, fn_name in _find_violations(tree=module_ast):
            log.error(
                "public function annotated `-> int` without railway-lifting decorator",
                path=str(py_file.relative_to(cwd)),
                line=lineno,
                function=fn_name,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
