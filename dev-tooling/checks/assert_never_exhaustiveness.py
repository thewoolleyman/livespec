"""assert_never_exhaustiveness — every `match` ends with `case _: assert_never(<subject>)`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-assert-never-exhaustiveness` row),
every `match` statement in `livespec/**` MUST terminate with
a `case _: assert_never(<subject>)` arm where `<subject>` is
the match-statement's subject expression. Conservative scope:
every match, regardless of subject type.

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, and inspects every
`Match` node. The final case (`node.cases[-1]`) MUST be:

- A wildcard pattern (`case _:`) — `MatchAs(pattern=None,
  name=None)`.
- A body that is exactly one `Expr` statement whose value is
  a `Call` to a name `assert_never` with one positional arg.

Cycle 156 implements the structural check (final case is
wildcard + body is `assert_never(...)` call). Subsequent
cycles can tighten to verify the call's argument equals the
match subject.

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


def _is_wildcard_pattern(*, pattern: ast.pattern) -> bool:
    return isinstance(pattern, ast.MatchAs) and pattern.pattern is None and pattern.name is None


def _is_assert_never_call(*, body: list[ast.stmt]) -> bool:
    if len(body) != 1 or not isinstance(body[0], ast.Expr):
        return False
    expr = body[0].value
    return (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Name)
        and expr.func.id == "assert_never"
    )


def _is_compliant_terminator(*, case: ast.match_case) -> bool:
    return _is_wildcard_pattern(pattern=case.pattern) and _is_assert_never_call(body=case.body)


def _find_offending_match_lines(*, source: str) -> list[int]:
    tree = ast.parse(source)
    out: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Match) and (
            len(node.cases) == 0 or not _is_compliant_terminator(case=node.cases[-1])
        ):
            out.append(node.lineno)
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
    log = structlog.get_logger("assert_never_exhaustiveness")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    offenders: list[tuple[Path, int]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            for lineno in _find_offending_match_lines(source=source):
                offenders.append((py_file.relative_to(cwd), lineno))
    if offenders:
        for path, lineno in offenders:
            log.error(
                "match must terminate with `case _: assert_never(<subject>)`",
                file=str(path),
                line=lineno,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
