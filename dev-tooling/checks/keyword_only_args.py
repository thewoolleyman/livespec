"""keyword_only_args — every `def` uses `*` separator.

Per `python-skill-script-style-requirements.md` line 2086:

    AST: every `def` in livespec scope uses `*` as first
    separator (all params keyword-only); every `@dataclass`
    declares the strict-dataclass triple `frozen=True,
    kw_only=True, slots=True`. Exempts Python-mandated dunder
    signatures and `__init__` of Exception subclasses that
    forward to `super().__init__(msg)`.

This module pins the FIRST responsibility: every `def` (and
`async def`) in `.claude-plugin/scripts/livespec/**` declares
its parameters as keyword-only via a leading `*` separator. AST
shape: `args.posonlyargs` is empty AND `args.args` is empty
(except the implicit `self`/`cls` for instance/class methods);
all real parameters live in `args.kwonlyargs`. Equivalently, in
`ast.arguments`, a function is keyword-only-conformant iff every
non-`self`/`cls` parameter is in `kwonlyargs` rather than `args`.

Dunder names (`__name__` shape) are exempt — Python's call
protocol fixes their signatures. The dataclass-triple
responsibility is deferred to a subsequent cycle per v032 D1
one-pattern-per-cycle.
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
_IMPLICIT_SELF_NAMES = frozenset({"self", "cls"})


def _is_dunder_name(*, name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _has_positional_params(*, args: ast.arguments) -> bool:
    if args.posonlyargs:
        return True
    non_self_positional = [a for a in args.args if a.arg not in _IMPLICIT_SELF_NAMES]
    return bool(non_self_positional)


def _find_violations(*, tree: ast.Module) -> list[tuple[int, str]]:
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if _is_dunder_name(name=node.name):
            continue
        if _has_positional_params(args=node.args):
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
    log = structlog.get_logger("keyword_only_args")
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
                "function has positional parameters; declare keyword-only via `*`",
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
