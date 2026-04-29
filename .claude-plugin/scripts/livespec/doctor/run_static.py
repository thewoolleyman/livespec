"""livespec.doctor.run_static — supervisor for `bin/doctor_static.py`.

Per PROPOSAL.md §"`doctor` → Static-phase output contract" lines
2610-2643, the orchestrator writes `{"findings": [...]}` JSON to
stdout conforming to `doctor_findings.schema.json`. Each finding
entry is a `Finding` dataclass instance per
`livespec/schemas/dataclasses/finding.py` (paired 1:1 with
`finding.schema.json`), serialized via `dataclasses.asdict`.

v032 TDD redo cycle 29: orchestrator now iterates over every
`(spec_root, template_name)` pair per PROPOSAL.md lines 2513-
2542. At startup it enumerates pairs: the main spec tree first
(template_name sentinel `"main"`), then each sub-spec tree under
`<main-spec-root>/templates/<sub-name>/` discovered via directory
listing. For each pair the orchestrator builds a per-tree
`DoctorContext` (with `spec_root` set to the tree's root and
`template_name` set to the tree's marker) and runs the
applicable check subset.

Per-tree applicability table (PROPOSAL.md lines 2526-2540 / v021
Q1):

- `template-exists` and `template-files-present` are
  main-tree-only checks. Sub-spec trees do NOT re-run them
  (a sub-spec IS a spec tree, not a template payload).
- Every other Phase-3 check runs uniformly per tree.

The applicability table lives in `_MAIN_TREE_ONLY_SLUGS` below.
Future per-tree narrowings (e.g., `gherkin-blank-line-format`'s
template-conditional logic per PROPOSAL.md lines 2528-2533) land
when those Phase-7 checks are authored.

The main-tree spec_root is hardcoded to `<project_root>/SPECIFICATION/`
per the `livespec` template's default. Data-driven `spec_root`
resolution from `template.json` lands when a `minimal`-template
test (which uses `spec_root: "./"`) forces it. Same transitional
collapse pattern as cycles 21-28.

Out of cycle-29 scope (deferred per outside-in walking direction,
each driven by a specific test):

- Data-driven `spec_root` resolution via `template.json` parse.
- Bootstrap lenience (v014 N3) for `template_load_status` /
  `config_load_status` flags on `DoctorContext`.
- Exit-code 3 path for `status: "fail"` findings per PROPOSAL.md
  §"Exit codes".
- Argparse usage error (exit 2) for `--skip-pre-check` /
  `--run-pre-check` per PROPOSAL.md lines 832-836.
- ROP plumbing (`@impure_safe`, `IOResult`, `Fold.collect_all`).

`sys.stdout.write` is the sanctioned seam at supervisor scope per
`livespec/doctor/CLAUDE.md` ("`run_static.py` is the supervisor:
... it is one of three places where `sys.stdout.write` is permitted")
and `python-skill-script-style-requirements.md` §"Output channels".
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

from livespec.context import DoctorContext
from livespec.doctor.static import CHECKS
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["main"]


_MAIN_TREE_ONLY_SLUGS: frozenset[str] = frozenset(
    {"template-exists", "template-files-present"}
)
"""Slugs for checks that run ONLY when `template_name == "main"`
per PROPOSAL.md lines 2534-2538. All other Phase-3 checks run
uniformly per tree."""

_MAIN_TEMPLATE_NAME = "main"


def _enumerate_pairs(*, project_root: Path) -> list[tuple[Path, str]]:
    """Return `(spec_root, template_name)` pairs: main first, then sub-specs.

    Main-spec `spec_root` is hardcoded to `<project_root>/SPECIFICATION/`
    per the `livespec` template's default; data-driven resolution
    via `template.json` lands when a `minimal`-template test forces
    it. Sub-specs are discovered by listing
    `<main-spec-root>/templates/<name>/` directories.
    """
    main_spec_root = project_root / "SPECIFICATION"
    pairs: list[tuple[Path, str]] = [(main_spec_root, _MAIN_TEMPLATE_NAME)]
    sub_specs_dir = main_spec_root / "templates"
    if sub_specs_dir.is_dir():
        for sub_dir in sorted(sub_specs_dir.iterdir()):
            if sub_dir.is_dir():
                pairs.append((sub_dir, sub_dir.name))
    return pairs


def _runs_for_tree(*, slug: str, template_name: str) -> bool:
    if slug in _MAIN_TREE_ONLY_SLUGS:
        return template_name == _MAIN_TEMPLATE_NAME
    return True


def main() -> int:
    project_root = Path.cwd()
    findings: list[Finding] = []
    for spec_root, template_name in _enumerate_pairs(project_root=project_root):
        ctx = DoctorContext(
            project_root=project_root,
            spec_root=spec_root,
            template_name=template_name,
        )
        for slug, run_fn in CHECKS:
            if not _runs_for_tree(slug=slug, template_name=template_name):
                continue
            findings.append(run_fn(ctx=ctx))
    findings_dicts = [dataclasses.asdict(f) for f in findings]
    sys.stdout.write(json.dumps({"findings": findings_dicts}) + "\n")
    return 0
