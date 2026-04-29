"""heading_coverage — every `##` spec heading has a registry entry.

Per `python-skill-script-style-requirements.md` line 2095:

    Validates that every `##` heading in every spec tree —
    main + each sub-spec under `SPECIFICATION/templates/<name>/`
    — has a corresponding entry in
    `tests/heading-coverage.json` whose `spec_root` field
    matches the heading's tree. Tolerates an empty `[]` array
    pre-Phase-6, before any spec tree exists; from Phase 6
    onward emptiness is a failure if any spec tree exists.

Spec-tree discovery:

- Main spec tree: `SPECIFICATION/` (if present at cwd root).
- Sub-spec trees: each direct subdirectory of
  `SPECIFICATION/templates/` (if present).

For each spec tree, every `*.md` file is parsed for `^## `
headings. The registry-entry match is keyed on
`(spec_root, spec_file, heading)` per PROPOSAL.md
§"Coverage registry" (lines 3520-3552). Missing entries
fail the check.

Cycle 54 pins the canonical "uncovered heading" violation.
The reverse (orphan registry entries) and `test: "TODO"`
without `reason` are deferred to subsequent cycles per
v032 D1.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import cast

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_SPEC_ROOT = Path("SPECIFICATION")
_SUB_SPEC_PARENT = _SPEC_ROOT / "templates"
_REGISTRY_PATH = Path("tests") / "heading-coverage.json"
_HEADING_PATTERN = re.compile(r"^## (?P<heading>.+?)\s*$")


def _iter_spec_roots(*, cwd: Path) -> list[Path]:
    out: list[Path] = []
    main_root = cwd / _SPEC_ROOT
    if main_root.is_dir():
        out.append(main_root)
    sub_parent = cwd / _SUB_SPEC_PARENT
    if sub_parent.is_dir():
        out.extend(sorted(p for p in sub_parent.iterdir() if p.is_dir()))
    return out


def _iter_md_files(*, root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.is_file())


def _extract_headings(*, md_text: str) -> list[str]:
    out: list[str] = []
    for line in md_text.splitlines():
        match = _HEADING_PATTERN.match(line)
        if match:
            out.append(match.group("heading"))
    return out


def _registry_keys(*, registry: list[dict[str, object]]) -> set[tuple[str, str, str]]:
    out: set[tuple[str, str, str]] = set()
    for entry in registry:
        spec_root = entry.get("spec_root")
        spec_file = entry.get("spec_file")
        heading = entry.get("heading")
        if isinstance(spec_root, str) and isinstance(spec_file, str) and isinstance(heading, str):
            out.add((spec_root, spec_file, heading))
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
    log = structlog.get_logger("heading_coverage")
    cwd = Path.cwd()
    registry_file = cwd / _REGISTRY_PATH
    if registry_file.is_file():
        registry = cast("list[dict[str, object]]", json.loads(registry_file.read_text(encoding="utf-8")))
    else:
        registry = []
    keys = _registry_keys(registry=registry)
    found_any = False
    for spec_tree_root in _iter_spec_roots(cwd=cwd):
        spec_root_rel = str(spec_tree_root.relative_to(cwd).as_posix())
        for md_file in _iter_md_files(root=spec_tree_root):
            spec_file_rel = str(md_file.relative_to(spec_tree_root).as_posix())
            for heading in _extract_headings(md_text=md_file.read_text(encoding="utf-8")):
                if (spec_root_rel, spec_file_rel, heading) in keys:
                    continue
                log.error(
                    "heading has no matching registry entry",
                    spec_root=spec_root_rel,
                    spec_file=spec_file_rel,
                    heading=heading,
                )
                found_any = True
    if found_any:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
