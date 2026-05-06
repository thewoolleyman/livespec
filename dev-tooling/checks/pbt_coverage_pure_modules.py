"""pbt_coverage_pure_modules — `@given`-decorated function in every pure-layer test module.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-pbt-coverage-pure-modules` row), each
test module under `tests/livespec/parse/` and `tests/livespec/
validate/` declares at least one `@given(...)`-decorated test
function. Hypothesis property-based testing is the canonical
PBT mechanism for pure layers (the parse and validate layers
return `Result` and have no I/O — their behavior is amenable
to property-based exploration).

The check walks each `tests/livespec/parse/test_*.py` and
`tests/livespec/validate/test_*.py` file, parses via `ast`,
and inspects every `FunctionDef` / `AsyncFunctionDef`'s
`decorator_list`. A module passes if at least one function
carries a decorator whose terminal name is `given` (e.g.,
`@given(...)` or `@hypothesis.given(...)`).

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
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


_PURE_TEST_TREES = (
    Path("tests") / "livespec" / "parse",
    Path("tests") / "livespec" / "validate",
)


def _decorator_terminal_name(*, decorator: ast.expr) -> str:
    if isinstance(decorator, ast.Call):
        decorator = decorator.func
    return ast.unparse(decorator).rsplit(".", maxsplit=1)[-1]


def _module_has_given_decorated_test(*, source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if _decorator_terminal_name(decorator=decorator) == "given":
                return True
    return False


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
    offenders: list[Path] = []
    for tree_rel in _PURE_TEST_TREES:
        root = cwd / tree_rel
        if not root.is_dir():
            continue
        for py_file in sorted(root.glob("test_*.py")):
            source = py_file.read_text(encoding="utf-8")
            if not _module_has_given_decorated_test(source=source):
                offenders.append(py_file.relative_to(cwd))
    if offenders:
        for path in offenders:
            log.error(
                "pure-layer test module missing `@given(...)` PBT function",
                file=str(path),
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
