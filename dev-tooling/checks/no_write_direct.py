"""no_write_direct — bans `sys.stdout.write`/`sys.stderr.write` outside exemption surface.

Per `python-skill-script-style-requirements.md` §"Canonical
target list" (the `check-no-write-direct` row),
`sys.stdout.write(...)` and `sys.stderr.write(...)` calls are
banned in `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, and
`<repo-root>/dev-tooling/**`. Pairs with ruff `T20` (which
bans `print` / `pprint`).

The check walks every `.py` file under the three covered
subtrees, parses each via `ast`, and inspects every `Call`
node whose function unparses to `sys.stdout.write` or
`sys.stderr.write`. Any match emits a structlog ERROR
carrying the file path and line number; the script exits 1.
With no violations, exits 0.

Cycle 150 implements the core ban plus the three documented
exemption surfaces, all file-scope (each supervisor file owns
the private helpers that its `main()` dispatches to, e.g.,
`_emit_findings_json` in `run_static.py`):

- `bin/_bootstrap.py` (pre-import version-check stderr — no
  structlog available pre-bootstrap).
- `livespec/doctor/run_static.py` (findings JSON stdout
  contract — `main()` dispatches to a private
  `_emit_findings_json` helper).
- Every `.py` under `livespec/commands/**` (each supervisor's
  `main()` + the private helpers it dispatches to —
  HelpRequested rendering, resolve_template path emission,
  etc.).

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


_COVERED_TREES = (
    Path(".claude-plugin") / "scripts" / "livespec",
    Path(".claude-plugin") / "scripts" / "bin",
    Path("dev-tooling"),
)
_BANNED_CALL_TARGETS = frozenset({"sys.stdout.write", "sys.stderr.write"})

# File-scope exemption: the three supervisor surfaces that own
# documented stdout/stderr contracts. Per the canonical target
# list row's prose: `bin/_bootstrap.py` (pre-import version-check
# stderr); `livespec/doctor/run_static.py` (findings JSON stdout
# + private helpers it dispatches to); `livespec/commands/<cmd>.py`
# (each supervisor's main() + private helpers it dispatches to).
# File-scope is the practical reading: each supervisor file owns
# its private helpers (`_emit_findings_json`, `_render_help`,
# etc.) which are called from main() and inherit the exemption.
_FILE_SCOPE_EXEMPT_PATHS = frozenset(
    {
        Path(".claude-plugin") / "scripts" / "bin" / "_bootstrap.py",
        Path(".claude-plugin") / "scripts" / "livespec" / "doctor" / "run_static.py",
    }
)
_COMMANDS_TREE = Path(".claude-plugin") / "scripts" / "livespec" / "commands"


def _is_file_scope_exempt(*, rel_path: Path) -> bool:
    if rel_path in _FILE_SCOPE_EXEMPT_PATHS:
        return True
    return _COMMANDS_TREE in rel_path.parents


def _find_banned_calls(*, source: str) -> list[int]:
    tree = ast.parse(source)
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and ast.unparse(node.func) in _BANNED_CALL_TARGETS
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
    log = structlog.get_logger("no_write_direct")
    cwd = Path.cwd()
    offenders: list[tuple[Path, int]] = []
    for tree_rel in _COVERED_TREES:
        root = cwd / tree_rel
        if not root.is_dir():
            continue
        for py_file in sorted(root.rglob("*.py")):
            rel = py_file.relative_to(cwd)
            if _is_file_scope_exempt(rel_path=rel):
                continue
            source = py_file.read_text(encoding="utf-8")
            for lineno in _find_banned_calls(source=source):
                offenders.append((rel, lineno))
    if offenders:
        for path, lineno in offenders:
            log.error(
                "`sys.stdout.write`/`sys.stderr.write` banned outside exemption surface",
                file=str(path),
                line=lineno,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
