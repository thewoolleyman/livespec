"""main_guard — bans `if __name__ == "__main__":` inside `livespec/**`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-main-guard` row), no `.py` file under
`.claude-plugin/scripts/livespec/**` may contain an
`if __name__ == "__main__":` guard at any nesting level.
livespec's runnable entry points live in `bin/*.py` (the
shebang wrappers); a `__main__` guard inside `livespec/**`
indicates a wrapper-style file in the wrong tree.

The check walks every `.py` file under `.claude-plugin/scripts/
livespec/`, parses each via `ast`, and inspects every `If`
node whose test unparses to the canonical `__name__ ==
"__main__"` string (either operand order). Any match emits a
structlog ERROR carrying the file path and line number, and
the script exits 1. With no violations, exits 0.

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
_MAIN_GUARD_TEXTS = frozenset(
    {
        "__name__ == '__main__'",
        '__name__ == "__main__"',
        "'__main__' == __name__",
        '"__main__" == __name__',
    }
)


def _find_main_guard_lines(*, source: str) -> list[int]:
    tree = ast.parse(source)
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.If) and ast.unparse(node.test) in _MAIN_GUARD_TEXTS
    ]


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
    livespec_root = cwd / _LIVESPEC_TREE
    offenders: list[tuple[Path, int]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            for lineno in _find_main_guard_lines(source=source):
                offenders.append((py_file.relative_to(cwd), lineno))
    if offenders:
        for path, lineno in offenders:
            log.error(
                "`__main__` guard banned in livespec/**",
                file=str(path),
                line=lineno,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
