"""rop_pipeline_shape — `@rop_pipeline` classes have exactly one public method.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-rop-pipeline-shape` row), every class
in `livespec/**` decorated with `@rop_pipeline` carries
exactly one public (non-underscore-prefixed) method (the
entry point); every other method is `_`-prefixed; dunders
aren't counted. Enforces the Command / Use Case Interactor
pattern at the class level.

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, inspects every
`ClassDef` whose `decorator_list` includes a decorator whose
terminal name is `rop_pipeline`. For each such class, count
the methods (FunctionDef/AsyncFunctionDef) by name shape:
dunders (`__*__`) are exempt; underscore-prefixed are
"private"; everything else is "public". Exactly one public
method must exist; otherwise the class fails the check.

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


_LIVESPEC_TREE = Path(".claude-plugin") / "scripts" / "livespec"


def _decorator_terminal_name(*, decorator: ast.expr) -> str:
    if isinstance(decorator, ast.Call):
        decorator = decorator.func
    return ast.unparse(decorator).rsplit(".", maxsplit=1)[-1]


def _is_dunder(*, name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _has_rop_pipeline_decorator(*, cls: ast.ClassDef) -> bool:
    return any(_decorator_terminal_name(decorator=d) == "rop_pipeline" for d in cls.decorator_list)


def _count_public_methods(*, cls: ast.ClassDef) -> int:
    count = 0
    for stmt in cls.body:
        if not isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if _is_dunder(name=stmt.name):
            continue
        if not stmt.name.startswith("_"):
            count += 1
    return count


def _find_offenders(*, source: str) -> list[tuple[int, str, int]]:
    tree = ast.parse(source)
    out: list[tuple[int, str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and _has_rop_pipeline_decorator(cls=node):
            public = _count_public_methods(cls=node)
            if public != 1:
                out.append((node.lineno, node.name, public))
    return out


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
    livespec_root = cwd / _LIVESPEC_TREE
    offenders: list[tuple[Path, int, str, int]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            for lineno, class_name, public_count in _find_offenders(source=source):
                offenders.append((py_file.relative_to(cwd), lineno, class_name, public_count))
    if offenders:
        for path, lineno, class_name, public_count in offenders:
            log.error(
                "@rop_pipeline class must have exactly 1 public method",
                file=str(path),
                line=lineno,
                class_name=class_name,
                public_method_count=public_count,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
