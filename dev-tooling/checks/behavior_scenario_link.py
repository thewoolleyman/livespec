"""behavior_scenario_link — every behavior clause links to a scenario.

Guardrail #1a (the mechanical clause→scenario link). For each
`MUST` / `MUST NOT` / `SHOULD` / `SHOULD NOT` behavior clause in
the live core spec, this check verifies that
`tests/heading-coverage.json` carries a `clauses[]` link binding
the clause's gap-id to an EXISTING `scenarios.md` H2 section. A
clause with no such link is surfaced.

The clause-extractor + gap-id derivation are single-sourced from
the shared `dev-tooling/spec_clauses.py` primitive, so the gap-ids
this check derives are byte-identical to the ones the
`livespec-impl-beads` detector derives (a vendored copy of the same
module). That single-sourcing is what lets one `clauses[]` link map
across the family.

ALWAYS-WIRED, ALWAYS-RUNNING with a self-documenting per-check
severity lever (the "carve-out = severity lever, not invariant
relax" discipline): `LIVESPEC_BEHAVIOR_SCENARIO_LINK` selects the
behavior on an unlinked clause.

- `warn` (DEFAULT): emit a per-clause warning + a summary, exit 0.
  The check still runs in full on every `just check`; it just does
  not block. This is the advisory-first posture while the
  clause→scenario backlog is backfilled.
- `fail`: emit a per-clause error + a summary, exit 1 if any
  behavior clause is unlinked. The lever flips to `fail` once the
  backlog is cleared (a separate, deferred step).

An unset / unrecognized value defaults to `warn`.

The `scenario` value in a `clauses[]` entry targets a
`scenarios.md` **H2 section heading** (the existing
`tests/heading-coverage.json` registry key), matched with or
without the leading `## ` and surrounding whitespace. A link whose
`scenario` does NOT resolve to a live `scenarios.md` H2 section is
treated as NOT-a-link (the clause stays surfaced) so a stale or
typo'd scenario name cannot silently satisfy the guardrail.

Output discipline: per spec, `print` (T20) and `sys.stderr.write`
(`check-no-write-direct`) are banned in dev-tooling/**. Diagnostics
flow through structlog (JSON to stderr); the vendored copy under
`.claude-plugin/scripts/_vendor/structlog` is added to `sys.path`
at module import time.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import cast

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VENDOR_DIR = _REPO_ROOT / ".claude-plugin" / "scripts" / "_vendor"
if str(_VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VENDOR_DIR))
_DEV_TOOLING_DIR = _REPO_ROOT / "dev-tooling"
if str(_DEV_TOOLING_DIR) not in sys.path:
    sys.path.insert(0, str(_DEV_TOOLING_DIR))

import structlog  # noqa: E402  — vendor-path-aware import after sys.path insert.
from spec_clauses import extract_rules_from_file  # noqa: E402  — dev-tooling-path import.

__all__: list[str] = []


_ENV_LEVER = "LIVESPEC_BEHAVIOR_SCENARIO_LINK"
_MODE_WARN = "warn"
_MODE_FAIL = "fail"

_SPEC_ROOT = Path("SPECIFICATION")
_HEADING_COVERAGE = Path("tests") / "heading-coverage.json"
_SCENARIOS_FILE = "scenarios.md"

# The behavior-bearing core spec files clauses are extracted from.
# `scenarios.md` is the link TARGET registry, not a clause source;
# `README.md` is non-normative front matter.
_CLAUSE_SOURCE_FILES = (
    "spec.md",
    "contracts.md",
    "constraints.md",
    "non-functional-requirements.md",
)


def _resolve_mode(*, raw: str | None) -> str:
    """Resolve the severity lever; unset/unrecognized defaults to warn."""
    if raw is not None and raw.strip().lower() == _MODE_FAIL:
        return _MODE_FAIL
    return _MODE_WARN


def _normalize_scenario(*, value: str) -> str:
    """Normalize a scenario reference for matching.

    Accepts the H2 form (`## Foo`) or the bare section name (`Foo`)
    and returns the bare, whitespace-stripped name.
    """
    stripped = value.strip()
    while stripped.startswith("#"):
        stripped = stripped[1:]
    return stripped.strip()


def _live_scenario_sections(*, scenarios_text: str) -> set[str]:
    """Return the set of normalized `scenarios.md` H2 section names."""
    sections: set[str] = set()
    for raw_line in scenarios_text.splitlines():
        if raw_line.startswith("## "):
            sections.add(_normalize_scenario(value=raw_line))
    return sections


def _linked_gap_ids(*, coverage_entries: object, live_scenarios: set[str]) -> set[str]:
    """Collect gap-ids with a `clauses[]` link to a live scenario.

    A `clauses[]` entry counts only when its `scenario` resolves to
    a live `scenarios.md` H2 section; a link to a stale/typo'd
    scenario name does NOT count.

    `coverage_entries` is the freshly-`json.loads`-ed map (typed
    `object`); the per-level `isinstance` guards + casts are the
    single typed parse boundary, mirroring `vendor_manifest`'s
    defensive parse — a malformed entry is skipped, never crashes
    the whole pass.
    """
    linked: set[str] = set()
    if not isinstance(coverage_entries, list):
        return linked
    entries = cast("list[object]", coverage_entries)
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        clauses = cast("dict[str, object]", entry).get("clauses")
        if not isinstance(clauses, list):
            continue
        for clause in cast("list[object]", clauses):
            if not isinstance(clause, dict):
                continue
            clause_map = cast("dict[str, object]", clause)
            gap_id = clause_map.get("gap_id")
            scenario = clause_map.get("scenario")
            if not isinstance(gap_id, str) or not isinstance(scenario, str):
                continue
            if _normalize_scenario(value=scenario) in live_scenarios:
                linked.add(gap_id)
    return linked


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("behavior_scenario_link")
    mode = _resolve_mode(raw=os.environ.get(_ENV_LEVER))
    cwd = Path.cwd()
    spec_root = cwd / _SPEC_ROOT
    if not spec_root.is_dir():
        return 0

    scenarios_path = spec_root / _SCENARIOS_FILE
    scenarios_text = scenarios_path.read_text(encoding="utf-8") if scenarios_path.is_file() else ""
    live_scenarios = _live_scenario_sections(scenarios_text=scenarios_text)

    coverage_path = cwd / _HEADING_COVERAGE
    coverage_entries: object = []
    if coverage_path.is_file():
        coverage_entries = json.loads(coverage_path.read_text(encoding="utf-8"))
    linked = _linked_gap_ids(coverage_entries=coverage_entries, live_scenarios=live_scenarios)

    unlinked_count = 0
    for spec_file in _CLAUSE_SOURCE_FILES:
        source_path = spec_root / spec_file
        if not source_path.is_file():
            continue
        content = source_path.read_text(encoding="utf-8")
        for rule in extract_rules_from_file(spec_file=spec_file, content=content):
            if rule.gap_id in linked:
                continue
            unlinked_count += 1
            emit = log.error if mode == _MODE_FAIL else log.warning
            emit(
                "behavior clause not linked to a scenario",
                check_id="behavior-scenario-link-unlinked",
                spec_file=spec_file,
                heading_path=rule.heading_path,
                gap_id=rule.gap_id,
                clause=rule.line_text,
                mode=mode,
            )

    if unlinked_count == 0:
        return 0
    summary = log.error if mode == _MODE_FAIL else log.warning
    summary(
        "behavior clauses lacking a scenario link",
        check_id="behavior-scenario-link-summary",
        unlinked_count=unlinked_count,
        mode=mode,
        lever=_ENV_LEVER,
    )
    return 1 if mode == _MODE_FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
