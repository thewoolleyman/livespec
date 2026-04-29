"""pbt_coverage_pure_modules — every parse/validate test module has @given.

Per `python-skill-script-style-requirements.md` §"Property-based
testing for pure modules" (lines 1216-1247) and the canonical-
target table line 2093:

    AST: each test module under `tests/livespec/parse/` and
    `tests/livespec/validate/` declares at least one
    `@given(...)`-decorated test function.

Pure Result-returning modules (`livespec/parse/` and
`livespec/validate/`) are mandatory PBT targets via `hypothesis`.
The check walks every `*.py` file under the two test trees
(excluding `__init__.py`) and verifies at least one function in
the module is decorated with `@given(...)` (recognized by
decorator name regardless of bare or parameterized form).

The current repo's `tests/livespec/parse/` and
`tests/livespec/validate/` contain only `CLAUDE.md` (no `*.py`
test modules). The rule passes vacuously today; the check
catches the next agent who lands a `test_*.py` in either tree
without at least one `@given(...)`-decorated function.
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


_PARSE_TESTS = Path("tests") / "livespec" / "parse"
_VALIDATE_TESTS = Path("tests") / "livespec" / "validate"
_INIT_FILENAME = "__init__.py"
_GIVEN_NAME = "given"


def _decorator_name(*, decorator: ast.expr) -> str | None:
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator=decorator.func)
    return None


def _has_given(*, tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for d in node.decorator_list:
            if _decorator_name(decorator=d) == _GIVEN_NAME:
                return True
    return False


def _iter_test_files(*, root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file() and p.name != _INIT_FILENAME)


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("pbt_coverage_pure_modules")
    cwd = Path.cwd()
    found_any = False
    for tree_root_rel in (_PARSE_TESTS, _VALIDATE_TESTS):
        tree_root = cwd / tree_root_rel
        if not tree_root.is_dir():
            continue
        for py_file in _iter_test_files(root=tree_root):
            source = py_file.read_text(encoding="utf-8")
            module_ast = ast.parse(source, filename=str(py_file))
            if _has_given(tree=module_ast):
                continue
            log.error(
                "test module has no `@given(...)`-decorated function",
                path=str(py_file.relative_to(cwd)),
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
