"""main_guard — no `if __name__ == "__main__":` in `livespec/**`.

Per `python-skill-script-style-requirements.md` line 2084:

    AST: no `if __name__ == "__main__":` in
    `.claude-plugin/scripts/livespec/**`.

The livespec runtime modules are imported by the shebang-wrapper
layer (`.claude-plugin/scripts/bin/*.py`); they MUST NOT carry
self-execution guards because that pattern conflates library and
script roles. The wrapper layer (out of scope here) uses the
canonical 6-statement shape `raise SystemExit(main())` and
exists for exactly the entry-point purpose `__main__` would
otherwise serve.

Scope is the `livespec` package only:

- `.claude-plugin/scripts/livespec/**.py` is in scope.
- `bin/*.py` is exempt (the wrappers don't use `__main__`
  either, by separate contract enforced via `wrapper_shape.py`).
- `dev-tooling/**` and `tests/**` are NOT in scope; both
  legitimately use `if __name__ == "__main__":` to invoke their
  `main()` from the CLI.

The check walks only `.claude-plugin/scripts/livespec/**`,
parses each file's AST, and flags any top-level `If` node whose
test is the literal `__name__ == "__main__"` comparison.
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


def _is_main_guard(*, node: ast.stmt) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    if not isinstance(test, ast.Compare):
        return False
    if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
        return False
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    if len(test.comparators) != 1:
        return False
    right = test.comparators[0]
    return isinstance(right, ast.Constant) and right.value == "__main__"


def _find_main_guards(*, tree: ast.Module) -> list[int]:
    return [node.lineno for node in tree.body if _is_main_guard(node=node)]


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
    log = structlog.get_logger("main_guard")
    cwd = Path.cwd()
    tree_root = cwd / _LIVESPEC_TREE
    if not tree_root.is_dir():
        return 0
    found_any = False
    for py_file in _iter_python_files(root=tree_root):
        source = py_file.read_text(encoding="utf-8")
        module_ast = ast.parse(source, filename=str(py_file))
        for lineno in _find_main_guards(tree=module_ast):
            log.error(
                "forbidden __main__ guard in livespec module",
                path=str(py_file.relative_to(cwd)),
                line=lineno,
            )
            found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
