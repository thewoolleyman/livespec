"""all_declared: verify every livespec/** module declares __all__.

Per python-skill-script-style-requirements.md lines 876-891:
every module in `.claude-plugin/scripts/livespec/**` MUST declare a
module-top `__all__: list[str]` listing the public API names. Every
name in `__all__` MUST actually be defined in the module (catches
stale entries after a rename).

Scope: `livespec/**.py` only, excluding `_vendor/` and
`__pycache__/`. Bin/ wrappers have no room for `__all__` per the
6-statement shape; dev-tooling scripts use a different convention
(standalone scripts, not library code).

Two violation types:
- "missing": no module-level `__all__: list[str] = [...]` assignment.
- "undefined name 'X'": a name listed in `__all__` doesn't appear
  as a module-top binding (def, class, assign, or import).
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
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"


def main() -> int:
    """Walk livespec/**.py; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    livespec_dir = repo_root / _LIVESPEC_DIR
    if not livespec_dir.is_dir():
        log.error("%s does not exist; cannot check all_declared", livespec_dir)
        return 1
    failures: list[str] = []
    for path in sorted(livespec_dir.rglob("*.py")):
        if _VENDOR_SUBSTR in path.parts or _PYCACHE_SUBSTR in path.parts:
            continue
        violations = check_file(path=path)
        for v in violations:
            failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("all_declared: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return a list of violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]

    all_node = _find_all_assignment(tree=tree)
    if all_node is None:
        return ["missing module-level `__all__: list[str] = [...]` assignment"]

    listed_names = _extract_string_list(node=all_node)
    if listed_names is None:
        return ["`__all__` value must be a list of string literals"]

    module_bindings = _module_bindings(tree=tree)
    return [
        f"`__all__` lists undefined name '{name}'"
        for name in listed_names
        if name not in module_bindings
    ]


def _find_all_assignment(*, tree: ast.Module) -> ast.AnnAssign | None:
    """Return the module-level `__all__: list[str] = ...` AnnAssign node, or None.

    Required form: annotated assignment with target `__all__` and
    annotation `list[str]`. Plain `__all__ = [...]` (no annotation) is
    rejected because the style doc mandates the typed form.
    """
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__all__"
            and _is_list_str_annotation(annotation=node.annotation)
        ):
            return node
    return None


def _is_list_str_annotation(*, annotation: ast.expr) -> bool:
    """True iff `annotation` is `list[str]` syntactically."""
    return (
        isinstance(annotation, ast.Subscript)
        and isinstance(annotation.value, ast.Name)
        and annotation.value.id == "list"
        and isinstance(annotation.slice, ast.Name)
        and annotation.slice.id == "str"
    )


def _extract_string_list(*, node: ast.AnnAssign) -> list[str] | None:
    """Return the string values inside `__all__ = [...]`, or None if non-literal."""
    value = node.value
    if not isinstance(value, ast.List):
        return None
    names: list[str] = []
    for element in value.elts:
        if not (isinstance(element, ast.Constant) and isinstance(element.value, str)):
            return None
        names.append(element.value)
    return names


def _module_bindings(*, tree: ast.Module) -> set[str]:
    """Return the set of names bound at module top-level (def, class, assign, import)."""
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                _collect_assignment_target(target=target, names=names)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Import | ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def _collect_assignment_target(*, target: ast.expr, names: set[str]) -> None:
    """Walk an assignment target (potentially tuple/list-destructured) collecting bound names."""
    if isinstance(target, ast.Name):
        names.add(target.id)
    elif isinstance(target, ast.Tuple | ast.List):
        for sub in target.elts:
            _collect_assignment_target(target=sub, names=names)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
