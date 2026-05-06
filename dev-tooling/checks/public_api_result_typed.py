"""public_api_result_typed — pure-layer public APIs return Result/IOResult or carry decorator.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-public-api-result-typed` row),
every public function (per `__all__` declaration) returns
`Result` or `IOResult` per annotation OR carries a railway-
lifting decorator (`@impure_safe(...)` lifts to `IOResult`,
`@safe(...)` lifts to `Result`).

Cycle 169 implements minimum-viable: scope is
`livespec/parse/` and `livespec/validate/` (the pure layers).
For each `.py`, parse via `ast`, extract `__all__`, then
inspect each top-level FunctionDef whose name is in
`__all__`. A function passes if EITHER:

- Its return annotation's terminal name is `Result` or
  `IOResult` (also matching `Result[...]` / `IOResult[...]`
  / `livespec.types.Result` etc.).
- It carries a decorator whose terminal name is `safe` or
  `impure_safe` (call form or bare).

Documented exemptions (a-f from the canonical row) — the
supervisor `main()`, `build_parser`, `make_validator`,
`get_logger`, `compile_schema`, `rop_pipeline` — are NOT
yet wired in; subsequent cycles widen as concrete files
trigger them. Package-private modules (filename matching
`_*.py`) are skipped.

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


_PURE_TREES = (
    Path(".claude-plugin") / "scripts" / "livespec" / "parse",
    Path(".claude-plugin") / "scripts" / "livespec" / "validate",
)
_RESULT_NAMES = frozenset({"Result", "IOResult"})
_RAILWAY_LIFTING_DECORATORS = frozenset({"safe", "impure_safe"})


def _decorator_terminal_name(*, decorator: ast.expr) -> str:
    if isinstance(decorator, ast.Call):
        decorator = decorator.func
    return ast.unparse(decorator).rsplit(".", maxsplit=1)[-1]


def _annotation_head_name(*, annotation: ast.expr) -> str:
    rendered = ast.unparse(annotation)
    head = rendered.split("[", maxsplit=1)[0]
    return head.rsplit(".", maxsplit=1)[-1]


def _all_value_names(*, tree: ast.Module) -> list[str]:
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__all__"
            and isinstance(node.value, ast.List)
        ):
            return [
                elt.value
                for elt in node.value.elts
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
    return []


def _is_railway_compliant(*, func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in func.decorator_list:
        if _decorator_terminal_name(decorator=decorator) in _RAILWAY_LIFTING_DECORATORS:
            return True
    if func.returns is None:
        return False
    return _annotation_head_name(annotation=func.returns) in _RESULT_NAMES


def _find_offenders(*, source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    declared = set(_all_value_names(tree=tree))
    out: list[tuple[int, str]] = []
    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name in declared
            and not _is_railway_compliant(func=node)
        ):
            out.append((node.lineno, node.name))
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
    log = structlog.get_logger("public_api_result_typed")
    cwd = Path.cwd()
    offenders: list[tuple[Path, int, str]] = []
    for tree_rel in _PURE_TREES:
        root = cwd / tree_rel
        if not root.is_dir():
            continue
        for py_file in sorted(root.rglob("*.py")):
            if py_file.name.startswith("_"):
                continue
            source = py_file.read_text(encoding="utf-8")
            for lineno, name in _find_offenders(source=source):
                offenders.append((py_file.relative_to(cwd), lineno, name))
    if offenders:
        for path, lineno, name in offenders:
            log.error(
                "public function not Result-typed and not railway-lifting-decorated",
                file=str(path),
                line=lineno,
                function=name,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
