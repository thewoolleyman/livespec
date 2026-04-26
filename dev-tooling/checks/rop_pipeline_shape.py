"""rop_pipeline_shape: enforce single-public-method on @rop_pipeline classes.

Per python-skill-script-style-requirements.md §"ROP pipeline
shape":

A class decorated with `@rop_pipeline` MUST carry exactly ONE
public method (the entry point). Every other method MUST be
`_`-prefixed (private). Dunder methods (`__init__`, `__call__`,
etc., name matches `^__.+__$`) are not counted toward the
public-method quota — they are Python-mandated structural
surfaces.

Rationale: the rule encodes the Command / Use Case Interactor /
Trailblazer Operation lineage — each pipeline class encapsulates
one cohesive railway chain with a single entry point; internal
steps are bounded by the class body. Statically enforcing the
shape prevents the public surface from drifting as new chain
steps are added; agent-authored code that grows a second public
method gets caught at check time, not at review.

Helper classes and helper modules (anything NOT carrying the
`@rop_pipeline` decorator) are exempt and may export multiple
public methods/functions.

Implementation:

1. Walk every `ast.ClassDef`.
2. Find classes whose `decorator_list` contains a bare-name
   `@rop_pipeline` decorator (or `@livespec.types.rop_pipeline`
   attribute form). Other decorators are ignored.
3. For each such class, count direct-child methods
   (`ast.FunctionDef` / `ast.AsyncFunctionDef`) whose name is
   neither dunder (`^__.+__$`) nor underscore-prefixed.
4. If the count is not exactly 1, flag.

Scope: `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, `<repo-root>/dev-tooling/**`.
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
_DECORATOR_NAME = "rop_pipeline"


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
            for v in check_file(path=path):
                failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("rop_pipeline_shape: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not _has_rop_pipeline_decorator(class_def=node):
            continue
        public_methods = _public_method_names(class_def=node)
        if len(public_methods) != 1:
            violations.append(
                f"line {node.lineno}: @rop_pipeline class `{node.name}` has "
                f"{len(public_methods)} public methods ({sorted(public_methods)}); "
                f"exactly one required",
            )
    return violations


def _has_rop_pipeline_decorator(*, class_def: ast.ClassDef) -> bool:
    """True iff the class carries a `@rop_pipeline` decorator (bare or attribute form)."""
    for decorator in class_def.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == _DECORATOR_NAME:
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == _DECORATOR_NAME:
            return True
    return False


def _public_method_names(*, class_def: ast.ClassDef) -> list[str]:
    """Names of direct-child methods that are neither dunder nor `_`-prefixed."""
    names: list[str] = []
    for child in class_def.body:
        if not isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if _is_dunder(name=child.name):
            continue
        if child.name.startswith("_"):
            continue
        names.append(child.name)
    return names


def _is_dunder(*, name: str) -> bool:
    return len(name) >= 4 and name.startswith("__") and name.endswith("__")


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
