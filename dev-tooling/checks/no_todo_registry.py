"""no_todo_registry: reject `test: "TODO"` entries (v013 M8).

Per python-skill-script-style-requirements.md canonical target list:

    Rejects any `test: "TODO"` entry in `tests/heading-coverage.json`
    (v013 M8). Release-gate only; paired with `check-mutation` on
    release-tag CI workflow. Ensures every release ships with full
    rule-test coverage.

The v018 Q1 Option-A heading-coverage manifest entries shape:

    {
      "spec_root": "<tree>",
      "heading": "## Section",
      "test": "tests/x::test_name" | "TODO"
    }

The literal `"TODO"` string in the `test` field is the canonical
"this heading lacks a coverage test" placeholder. It's tolerated
day-to-day (heading_coverage's pre-Phase-6 vacuous-pass mode + the
non-release-gate dev cycle accept the placeholder), but a release
build MUST clear all TODOs — every shipped heading has a real test
attached.

Tolerates an absent `tests/heading-coverage.json` (pre-Phase-6).
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

__all__: list[str] = [
    "check_repo",
    "main",
]


log = logging.getLogger(__name__)

_COVERAGE_JSON = Path("tests/heading-coverage.json")
_TODO_SENTINEL = "TODO"


def main() -> int:
    """Verify no `test: TODO` entries; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures = check_repo(repo_root=repo_root)
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("no_todo_registry: %d violation(s)", len(failures))
        return 1
    return 0


def check_repo(*, repo_root: Path) -> list[str]:
    """Walk tests/heading-coverage.json; flag every `test: TODO` entry."""
    path = repo_root / _COVERAGE_JSON
    if not path.is_file():
        return []  # pre-Phase-6: file doesn't exist yet, vacuously passes
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"{path}: cannot read or parse: {e}"]
    if not isinstance(doc, list):
        return [f"{path}: expected a JSON array"]
    violations: list[str] = []
    for index, entry in enumerate(doc):
        if not isinstance(entry, dict):
            violations.append(f"{path}: entries[{index}] is not an object")
            continue
        if entry.get("test") == _TODO_SENTINEL:
            heading = entry.get("heading", "<unknown>")
            spec_root = entry.get("spec_root", "<unknown>")
            violations.append(
                f"{path}: entries[{index}] heading `{heading}` in spec_root "
                f"`{spec_root}` has `test: TODO`; release requires full coverage",
            )
    return violations


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
