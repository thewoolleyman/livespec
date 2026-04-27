"""global_writes: ban module-level mutable state writes from functions.

Per python-skill-script-style-requirements.md line 1802:
"no module-level mutable state writes from functions."

Detects writes from inside function bodies that target a
module-level binding via:

- Subscript: `_MODULE_VAR[key] = value` or
  `_MODULE_VAR[key] op= value` where `_MODULE_VAR` is bound at
  module top-level.
- Attribute: `_MODULE_VAR.attr = value` (less common; included
  for completeness).
- Direct rebind via `global`: `global X` followed by `X = ...`.

Exemptions per style doc lines 1497-1506:

- `livespec/__init__.py`: `structlog.configure(...)` and
  `structlog.contextvars.bind_contextvars(run_id=...)` —
  configure third-party library state at module-import time
  (these are at module top-level, not inside functions, so
  they're not flagged anyway; included here for documentation).
- `livespec/io/fastjsonschema_facade.py`: the module-level
  `_COMPILED: dict[str, Validator]` cache and its mutation via
  `compile_schema` — explicit cache by `$id` for compile
  deduplication.

Phase 4 minimum-viable: detects subscript and attribute writes
inside function bodies. The `global` statement detection is
included but rare in livespec code.
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

_SCOPE_DIRS: tuple[Path, ...] = (
    Path(".claude-plugin/scripts/livespec"),
    Path(".claude-plugin/scripts/bin"),
    Path("dev-tooling"),
)
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"

_FASTJSONSCHEMA_FACADE = Path(
    ".claude-plugin/scripts/livespec/io/fastjsonschema_facade.py",
)


def main() -> int:
    """Walk scoped trees; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures: list[str] = []
    for scope in _SCOPE_DIRS:
        scope_dir = repo_root / scope
        if not scope_dir.is_dir():
            continue
        for path in sorted(scope_dir.rglob("*.py")):
            if _VENDOR_SUBSTR in path.parts or _PYCACHE_SUBSTR in path.parts:
                continue
            relative = path.relative_to(repo_root)
            violations = check_file(path=path, relative=relative)
            for v in violations:
                failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("global_writes: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path, relative: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    module_bindings = _module_top_bindings(tree=tree)
    exempted_names = _exempted_names_for_file(relative=relative)
    violations: list[str] = []
    for func in _iter_function_defs(tree=tree):
        _walk_function_body(
            func=func,
            module_bindings=module_bindings,
            exempted_names=exempted_names,
            violations=violations,
        )
    return violations


def _module_top_bindings(*, tree: ast.Module) -> set[str]:
    """Names bound at module top-level (assigns + AnnAssigns + imports + def/class)."""
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Import | ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def _exempted_names_for_file(*, relative: Path) -> set[str]:
    """Per-file exemption list for known intentional global mutation."""
    if relative == _FASTJSONSCHEMA_FACADE:
        return {"_COMPILED"}
    return set()


def _iter_function_defs(*, tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Return every FunctionDef / AsyncFunctionDef in the tree (top-level + nested)."""
    funcs: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            funcs.append(node)
    return funcs


def _walk_function_body(
    *,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    module_bindings: set[str],
    exempted_names: set[str],
    violations: list[str],
) -> None:
    """Walk `func`'s body for assigns that mutate module-level state."""
    for node in ast.walk(func):
        if isinstance(node, ast.Assign | ast.AugAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                violation = _violation_for_target(
                    target=target,
                    lineno=node.lineno,
                    module_bindings=module_bindings,
                    exempted_names=exempted_names,
                )
                if violation is not None:
                    violations.append(violation)


def _violation_for_target(
    *,
    target: ast.expr,
    lineno: int,
    module_bindings: set[str],
    exempted_names: set[str],
) -> str | None:
    """Return a violation message if `target` mutates a module-level name."""
    base_name = _extract_base_name(target=target)
    if base_name is None:
        return None
    if base_name not in module_bindings:
        return None
    if base_name in exempted_names:
        return None
    return (
        f"line {lineno}: function-body mutation of module-level `{base_name}` "
        f"via {_describe_target(target=target)}"
    )


def _extract_base_name(*, target: ast.expr) -> str | None:
    """For Subscript/Attribute targets, return the underlying Name's id, or None."""
    cur: ast.expr = target
    while isinstance(cur, ast.Subscript | ast.Attribute):
        cur = cur.value
    if isinstance(cur, ast.Name):
        return cur.id
    return None


def _describe_target(*, target: ast.expr) -> str:
    """Render the target shape for diagnostic messages."""
    if isinstance(target, ast.Subscript):
        return "subscript assignment"
    if isinstance(target, ast.Attribute):
        return "attribute assignment"
    if isinstance(target, ast.Name):
        return "direct name rebind"
    return "non-Name target"


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
