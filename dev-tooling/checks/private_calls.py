"""private_calls — no cross-module `_`-prefixed function calls in `livespec/**`.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-private-calls` row), no cross-module
calls to `_`-prefixed functions defined elsewhere are
permitted in `livespec/**`. Within a single module, calling
`_helper()` is fine; from another module, calling
`other_module._helper()` is banned.

The check walks every `.py` file under `.claude-plugin/
scripts/livespec/`, parses each via `ast`, and inspects every
`Call` whose function is an `Attribute` access. The check
flags violations when:

- The attribute name starts with `_` (and is not a dunder
  `__*__`).
- The receiver is a `Name` that is NOT `self` or `cls`
  (intra-class private access via `self._foo()` is fine).

Cycle 157 implements this minimum-viable structural check.
Subsequent cycles can tighten by verifying the receiver is
an imported module name (vs an arbitrary local variable
holding an instance).

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
_INTRA_CLASS_RECEIVERS = frozenset({"self", "cls"})


def _is_dunder(*, name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _is_offending_attribute_call(*, call: ast.Call) -> bool:
    func = call.func
    if not isinstance(func, ast.Attribute):
        return False
    if not func.attr.startswith("_") or _is_dunder(name=func.attr):
        return False
    receiver = func.value
    return not (isinstance(receiver, ast.Name) and receiver.id in _INTRA_CLASS_RECEIVERS)


def _find_offenders(*, source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_offending_attribute_call(call=node):
            attr = node.func
            assert isinstance(attr, ast.Attribute)  # noqa: S101 — narrowing for ast.unparse
            out.append((node.lineno, ast.unparse(attr)))
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
    log = structlog.get_logger("private_calls")
    cwd = Path.cwd()
    livespec_root = cwd / _LIVESPEC_TREE
    offenders: list[tuple[Path, int, str]] = []
    if livespec_root.is_dir():
        for py_file in sorted(livespec_root.rglob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            for lineno, attr_path in _find_offenders(source=source):
                offenders.append((py_file.relative_to(cwd), lineno, attr_path))
    if offenders:
        for path, lineno, attr_path in offenders:
            log.error(
                "cross-module call to `_`-prefixed name is banned",
                file=str(path),
                line=lineno,
                call=attr_path,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
