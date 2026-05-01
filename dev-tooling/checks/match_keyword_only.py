"""match_keyword_only — keyword-pattern destructuring on livespec classes.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-match-keyword-only` row), every
`match` statement's class pattern resolving to a livespec-
authored class binds via keyword sub-patterns (`Foo(x=x)`),
not positional (`Foo(x)`). Third-party library class
destructures (the `returns` package's types — `Success`,
`Failure`, `IOSuccess`, `IOFailure`) are permitted
positionally because their `__match_args__` is fixed by
upstream.

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, and inspects every
`MatchClass` pattern (the AST node for a class destructure
inside a `match`/`case` statement). The class-name terminal is
extracted via `ast.unparse(node.cls).rsplit(".", maxsplit=1)
[-1]` (so `IOSuccess` matches whether bare or
`returns.io.IOSuccess`). Positional sub-patterns are recorded
in `node.patterns`; keyword sub-patterns are in
`node.kwd_patterns` / `node.kwd_attrs`. A class pattern with
non-empty `node.patterns` and a class name OUTSIDE the
third-party allowlist surfaces as a violation.

Output discipline: per spec lines 1738-1762, `print` (T20) and
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
_THIRD_PARTY_POSITIONAL_OK = frozenset(
    {"Success", "Failure", "IOSuccess", "IOFailure"}
)


def _terminal_class_name(*, cls_node: ast.expr) -> str:
    return ast.unparse(cls_node).rsplit(".", maxsplit=1)[-1]


def _find_offending_match_classes(*, source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.MatchClass) or len(node.patterns) == 0:
            continue
        terminal = _terminal_class_name(cls_node=node.cls)
        if terminal not in _THIRD_PARTY_POSITIONAL_OK:
            out.append((node.cls.lineno, terminal))
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
    log = structlog.get_logger("match_keyword_only")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    offenders: list[tuple[Path, int, str]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            for lineno, class_name in _find_offending_match_classes(source=source):
                offenders.append((py_file.relative_to(cwd), lineno, class_name))
    if offenders:
        for path, lineno, class_name in offenders:
            log.error(
                "positional class pattern requires keyword binding",
                file=str(path),
                line=lineno,
                class_name=class_name,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
