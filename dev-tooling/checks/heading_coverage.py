"""heading_coverage — every spec-tree-root NLSpec heading has a coverage entry.

Per `SPECIFICATION/constraints.md` §"Heading taxonomy" (post-v004),
the registry at `tests/heading-coverage.json` maps `(spec_root,
spec_file, heading)` triples to pytest test identifiers. The check
walks ONLY the template-declared NLSpec files at each spec-tree
root — for the `livespec` template, the four files `spec.md`,
`contracts.md`, `constraints.md`, and `scenarios.md`. It does NOT
recurse into `proposed_changes/`, `history/`,
`templates/<name>/history/`, or any other subdirectory; it does NOT
include the skill-owned `README.md`.

The check fails on three directions:

1. Uncovered heading — a `(spec_root, spec_file, heading)` triple
   appears in some spec file but no matching registry entry exists.
2. Orphan registry entry — a registry entry's triple does not match
   any heading in any template-declared spec file.
3. Missing `reason` on a TODO entry — entry carries `test: "TODO"`
   but no non-empty `reason` field.

The check SKIPS `##` headings whose text begins with the literal
`Scenario:` prefix.

Pre-Phase-6 the check tolerates an empty `[]` array; from the
Phase 6 seed forward, emptiness is a failure if any spec tree
exists.

Output discipline: per spec, `print` (T20) and
`sys.stderr.write` (`check-no-write-direct`) are banned in
dev-tooling/**. Diagnostics flow through structlog (JSON to
stderr); the vendored copy under `.claude-plugin/scripts/
_vendor/structlog` is added to `sys.path` at module import time.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_VENDOR_DIR = Path(__file__).resolve().parents[2] / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.

__all__: list[str] = []


_MAIN_SPEC_ROOT = Path("SPECIFICATION")
_SUB_SPEC_PARENT = Path("SPECIFICATION") / "templates"
_COVERAGE_PATH = Path("tests") / "heading-coverage.json"
_TREE_ROOT_NLSPEC_FILES = ("spec.md", "contracts.md", "constraints.md", "scenarios.md")
_SCENARIO_PREFIX = "Scenario:"


def _enumerate_tree_roots(*, repo_root: Path) -> list[Path]:
    main = repo_root / _MAIN_SPEC_ROOT
    if not main.is_dir():
        return []
    out = [main]
    sub_parent = repo_root / _SUB_SPEC_PARENT
    if sub_parent.is_dir():
        for child in sorted(sub_parent.iterdir()):
            if child.is_dir():
                out.append(child)
    return out


def _enumerate_tree_root_spec_files(*, tree_root: Path) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for name in _TREE_ROOT_NLSPEC_FILES:
        candidate = tree_root / name
        if candidate.is_file():
            out.append((name, candidate))
    return out


def _extract_h2_headings(*, source: str) -> list[str]:
    out: list[str] = []
    for raw in source.splitlines():
        stripped = raw.rstrip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            out.append(stripped)
    return out


def _is_scenario_heading(*, heading: str) -> bool:
    return heading.removeprefix("## ").startswith(_SCENARIO_PREFIX)


def _spec_triples(*, repo_root: Path) -> set[tuple[str, str, str]]:
    out: set[tuple[str, str, str]] = set()
    for tree_root in _enumerate_tree_roots(repo_root=repo_root):
        spec_root_str = str(tree_root.relative_to(repo_root))
        for spec_file_name, spec_file_path in _enumerate_tree_root_spec_files(tree_root=tree_root):
            source = spec_file_path.read_text(encoding="utf-8")
            for heading in _extract_h2_headings(source=source):
                if _is_scenario_heading(heading=heading):
                    continue
                out.add((spec_root_str, spec_file_name, heading))
    return out


def _registry_triples_and_todo_violations(
    *, entries: list[dict[str, object]]
) -> tuple[set[tuple[str, str, str]], list[dict[str, object]]]:
    triples: set[tuple[str, str, str]] = set()
    todo_missing_reason: list[dict[str, object]] = []
    for entry in entries:
        spec_root = entry.get("spec_root")
        spec_file = entry.get("spec_file")
        heading = entry.get("heading")
        test_id = entry.get("test")
        if not (
            isinstance(spec_root, str) and isinstance(spec_file, str) and isinstance(heading, str)
        ):
            continue
        triples.add((spec_root, spec_file, heading))
        if test_id == "TODO":
            reason = entry.get("reason")
            if not (isinstance(reason, str) and reason.strip()):
                todo_missing_reason.append(entry)
    return triples, todo_missing_reason


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
    coverage_path = cwd / _COVERAGE_PATH
    coverage_entries: list[dict[str, object]] = []
    if coverage_path.is_file():
        text = coverage_path.read_text(encoding="utf-8")
        parsed = json.loads(text)
        if isinstance(parsed, list):
            coverage_entries = [e for e in parsed if isinstance(e, dict)]
    spec_set = _spec_triples(repo_root=cwd)
    registry_set, todo_missing_reason = _registry_triples_and_todo_violations(
        entries=coverage_entries
    )
    uncovered = sorted(spec_set - registry_set)
    orphan = sorted(registry_set - spec_set)
    if not uncovered and not orphan and not todo_missing_reason:
        return 0
    for spec_root, spec_file, heading in uncovered:
        log.error(
            "spec heading missing coverage entry",
            spec_root=spec_root,
            spec_file=spec_file,
            heading=heading,
        )
    for spec_root, spec_file, heading in orphan:
        log.error(
            "registry entry orphaned — no matching spec heading",
            spec_root=spec_root,
            spec_file=spec_file,
            heading=heading,
        )
    for entry in todo_missing_reason:
        log.error("TODO registry entry missing reason", entry=entry)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
