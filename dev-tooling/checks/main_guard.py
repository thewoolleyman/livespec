"""main_guard: bans `if __name__ == "__main__":` blocks in livespec/**.

Per python-skill-script-style-requirements.md line 1808:
no `if __name__ == "__main__":` in `.claude-plugin/scripts/livespec/**`.

Rationale: livespec/** is library code. Entry points live in
`.claude-plugin/scripts/bin/*.py` shebang wrappers (which DO have
the main guard implicitly via `raise SystemExit(main())` at module
level — no `if __name__ ==` block needed) and in
`livespec/commands/<cmd>.py::main()` and
`livespec/doctor/run_static.py::main()` supervisors. Adding an
`if __name__ ==` block inside livespec/ would create a second
entry point, conflicting with the bin/<cmd>.py-as-sole-entry-point
discipline.

This check applies ONLY to `livespec/**`. The `bin/*.py` wrappers
and `dev-tooling/**` scripts are not in scope (the latter need
`if __name__ ==` to be runnable as standalone scripts).
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
        log.error("%s does not exist; cannot check main_guard", livespec_dir)
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
        log.error("main_guard: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return a list of violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    violations: list[str] = []
    for node in tree.body:
        if _is_main_guard(node=node):
            violations.append(
                f'line {node.lineno}: `if __name__ == "__main__":` block forbidden in livespec/**',
            )
    return violations


def _is_main_guard(*, node: ast.stmt) -> bool:
    """True if `node` is a top-level `if __name__ == "__main__":` statement."""
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
    rhs = test.comparators[0]
    return (
        isinstance(rhs, ast.Constant)
        and isinstance(rhs.value, str)
        and rhs.value == "__main__"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
