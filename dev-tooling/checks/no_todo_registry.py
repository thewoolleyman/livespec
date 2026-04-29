"""no_todo_registry — release-gate: no `test: "TODO"` entries in registry.

Per `python-skill-script-style-requirements.md` line 2116:

    Rejects any `test: "TODO"` entry in
    `tests/heading-coverage.json` (v013 M8). Release-gate only;
    paired with `check-mutation` on release-tag CI workflow.
    Ensures every release ships with full rule-test coverage.

The check is a release-gate (NOT in `just check`); the
`check-no-todo-registry` justfile target is wired only in
`.github/workflows/release-tag.yml`'s matrix. This script
exists at Phase 4 so the gate is operational at release time;
its activation cadence is per release tag, not per commit.

The check tolerates a missing `tests/heading-coverage.json`
file (vacuous pass — the registry hasn't been authored yet at
Phase 4); the v013 M8 release-gate semantics apply once the
registry exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_REGISTRY_PATH = Path("tests") / "heading-coverage.json"
_TODO_LITERAL = "TODO"


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("no_todo_registry")
    cwd = Path.cwd()
    registry_file = cwd / _REGISTRY_PATH
    if not registry_file.is_file():
        return 0
    payload = json.loads(registry_file.read_text(encoding="utf-8"))
    entries = cast("list[dict[str, object]]", payload)
    found_any = False
    for index, entry in enumerate(entries):
        if entry.get("test") != _TODO_LITERAL:
            continue
        log.error(
            'registry entry has `test: "TODO"` (release-gate fail)',
            path=str(registry_file.relative_to(cwd)),
            index=index,
            heading=entry.get("heading"),
            spec_root=entry.get("spec_root"),
        )
        found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
