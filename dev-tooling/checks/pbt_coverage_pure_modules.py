"""pbt_coverage_pure_modules: enforce v012 L12 PBT-coverage discipline.

Per python-skill-script-style-requirements.md canonical target list
line 1895:

    AST: each test module under `tests/livespec/parse/` and
    `tests/livespec/validate/` declares at least one
    `@given(...)`-decorated test function.

Property-based testing via Hypothesis is the canonical coverage
mechanism for the pure layers (`parse/` and `validate/`). The
rule ensures every pure-module test file carries at least one PBT
case rather than falling back exclusively to example-based
assertions, which would miss boundary conditions PBT discovers.

Scope: `tests/livespec/parse/**/test_*.py` and
`tests/livespec/validate/**/test_*.py`. Conftest, helper, and
fixture files (filename not matching `test_*.py`) are skipped.

A test function is considered PBT-decorated if it carries a
`@given(...)` decorator OR `@hypothesis.given(...)` (attribute
form). The decorator's argument shape is not validated here —
presence is sufficient.
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
    Path("tests/livespec/parse"),
    Path("tests/livespec/validate"),
)
_PYCACHE_SUBSTR = "__pycache__"


def main() -> int:
    """Walk scoped tests/ trees; return 0 on pass, 1 on any violation.

    Tolerates absent scope directories — they are populated in Phase
    5 of the bootstrap; pre-Phase-5 the check is a no-op (vacuously
    passes).
    """
    repo_root = Path.cwd()
    failures: list[str] = []
    for scope in _SCOPE_DIRS:
        scope_dir = repo_root / scope
        if not scope_dir.is_dir():
            continue
        for path in sorted(scope_dir.rglob("test_*.py")):
            if _PYCACHE_SUBSTR in path.parts:
                continue
            for v in check_file(path=path):
                failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("pbt_coverage_pure_modules: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    if _has_given_decorated_test(tree=tree):
        return []
    return ["lacks any `@given(...)`-decorated test function"]


def _has_given_decorated_test(*, tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if not node.name.startswith("test_"):
            continue
        if _has_given_decorator(func=node):
            return True
    return False


def _has_given_decorator(
    *,
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """True iff `func` carries a `@given(...)` decorator (bare or attribute form)."""
    for decorator in func.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Name) and target.id == "given":
            return True
        if isinstance(target, ast.Attribute) and target.attr == "given":
            return True
    return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
