"""heading_coverage: every `##` spec heading has a coverage-test entry.

Per python-skill-script-style-requirements.md canonical target list
line 1897:

    Validates that every `##` heading in every spec tree — main +
    each sub-spec under `SPECIFICATION/templates/<name>/` — has a
    corresponding entry in `tests/heading-coverage.json` whose
    `spec_root` field matches the heading's tree. Tolerates an
    empty `[]` array pre-Phase-6, before any spec tree exists;
    from Phase 6 onward emptiness is a failure if any spec tree
    exists.

`tests/heading-coverage.json` shape (per v018 Q1 Option-A):

    [
      {
        "spec_root": "SPECIFICATION/" | "SPECIFICATION/templates/<name>/" | "" (minimal),
        "heading": "## Section title",
        "test": "tests/<path>::test_name"
      },
      ...
    ]

Behavior:

1. Locate every spec tree:
   - Main: `SPECIFICATION/` if it exists
   - Sub-spec: each `SPECIFICATION/templates/<name>/` directory
   - Minimal-template: `<repo-root>/SPECIFICATION.md` (single file)

2. For each spec tree, walk every `*.md` file and extract every
   line beginning with `## ` (level-2 headings).

3. Load `tests/heading-coverage.json` (initially `[]` per Phase
   1 author). Build the set of `(spec_root, heading)` pairs the
   coverage data declares.

4. For each `(spec_root, heading)` discovered in step 2, verify
   the pair appears in the coverage data. Otherwise: violation.

5. If `tests/heading-coverage.json` is missing entirely, the
   check passes pre-Phase-6 (no spec trees exist). Post-Phase-6,
   missing-or-empty + non-empty spec trees = failure.
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

_SPECIFICATION_DIR = Path("SPECIFICATION")
_TEMPLATES_SUBDIR = Path("templates")
_COVERAGE_JSON = Path("tests/heading-coverage.json")
_HEADING_PREFIX = "## "
_SUBSPEC_MIN_PARTS = 2


def main() -> int:
    """Walk spec trees + coverage data; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures = check_repo(repo_root=repo_root)
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("heading_coverage: %d violation(s)", len(failures))
        return 1
    return 0


def check_repo(*, repo_root: Path) -> list[str]:
    """Verify every `## ` heading in every spec tree has a coverage-data pair."""
    spec_trees = _enumerate_spec_trees(repo_root=repo_root)
    if not spec_trees:
        return []  # pre-Phase-6: no spec trees yet
    coverage_path = repo_root / _COVERAGE_JSON
    declared = _load_coverage_pairs(coverage_path=coverage_path)
    if declared is None:
        return [
            f"{coverage_path}: cannot load (must be a JSON array of "
            f"{{spec_root, heading, test}} objects)",
        ]
    discovered = _discover_heading_pairs(spec_trees=spec_trees)
    violations: list[str] = []
    for spec_root_label, heading, source_file in sorted(discovered):
        if (spec_root_label, heading) not in declared:
            violations.append(
                f"{source_file}: heading `{heading}` in spec_root "
                f"`{spec_root_label}` has no entry in {_COVERAGE_JSON}",
            )
    return violations


def _enumerate_spec_trees(*, repo_root: Path) -> list[tuple[str, Path]]:
    """Return [(spec_root_label, abs_dir_or_file), ...] for every spec tree."""
    trees: list[tuple[str, Path]] = []
    main_dir = repo_root / _SPECIFICATION_DIR
    if main_dir.is_dir():
        trees.append((f"{_SPECIFICATION_DIR}/", main_dir))
        templates_dir = main_dir / _TEMPLATES_SUBDIR
        if templates_dir.is_dir():
            for sub in sorted(templates_dir.iterdir()):
                if sub.is_dir():
                    trees.append(
                        (f"{_SPECIFICATION_DIR}/{_TEMPLATES_SUBDIR}/{sub.name}/", sub),
                    )
    minimal_file = repo_root / "SPECIFICATION.md"
    if minimal_file.is_file() and not main_dir.is_dir():
        trees.append(("", minimal_file))
    return trees


def _discover_heading_pairs(
    *,
    spec_trees: list[tuple[str, Path]],
) -> set[tuple[str, str, Path]]:
    """Return {(spec_root_label, heading_line, source_file_path), ...}.

    For the main spec tree (`SPECIFICATION/`), files under
    `SPECIFICATION/templates/<name>/` are EXCLUDED — they belong to
    their own sub-spec walk. Each `(spec_root, heading)` pair is
    attributed to exactly one tree.
    """
    pairs: set[tuple[str, str, Path]] = set()
    for spec_root_label, location in spec_trees:
        if location.is_file():
            files: list[Path] = [location]
        else:
            files = [
                p
                for p in sorted(location.rglob("*.md"))
                if not _is_inside_subspec(file_path=p, tree_root=location)
            ]
        for md_file in files:
            for line in md_file.read_text(encoding="utf-8").splitlines():
                if line.startswith(_HEADING_PREFIX):
                    pairs.add((spec_root_label, line.rstrip(), md_file))
    return pairs


def _is_inside_subspec(*, file_path: Path, tree_root: Path) -> bool:
    """True iff `file_path` lives under `<tree_root>/templates/<anything>/`.

    Used to exclude sub-spec files from the main-spec walk so each
    file is attributed to exactly one spec_root.
    """
    try:
        relative = file_path.relative_to(tree_root)
    except ValueError:
        return False
    parts = relative.parts
    return len(parts) >= _SUBSPEC_MIN_PARTS and parts[0] == _TEMPLATES_SUBDIR.name


def _load_coverage_pairs(*, coverage_path: Path) -> set[tuple[str, str]] | None:
    """Load coverage JSON; return {(spec_root, heading), ...} or None on shape error."""
    if not coverage_path.is_file():
        return set()
    try:
        doc = json.loads(coverage_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(doc, list):
        return None
    pairs: set[tuple[str, str]] = set()
    for entry in doc:
        if not isinstance(entry, dict):
            return None
        spec_root = entry.get("spec_root")
        heading = entry.get("heading")
        if not (isinstance(spec_root, str) and isinstance(heading, str)):
            return None
        pairs.add((spec_root, heading))
    return pairs


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
