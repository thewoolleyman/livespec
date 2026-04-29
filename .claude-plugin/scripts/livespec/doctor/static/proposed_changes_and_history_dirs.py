"""livespec.doctor.static.proposed_changes_and_history_dirs — directory presence check.

Verifies that `<spec-root>/proposed_changes/` and
`<spec-root>/history/` directories both exist and contain their
skill-owned `README.md` files. Per PROPOSAL.md §"`doctor` →
Static-phase checks" lines 2695-2698 and Plan §"Phase 3" line
1481, this is the fourth of the eight Phase-3 minimum-subset
checks.

Per PROPOSAL.md lines 992-994, the directory READMEs are
skill-owned: hard-coded inside the skill (i.e., this Python
package — see `livespec/commands/seed.py` for the literal
canonical content), written by `seed` only, NOT regenerated on
every `revise`. Per PROPOSAL.md lines 1065-1068, the README
content is template-agnostic (same for `livespec` and `minimal`;
only the `<spec-root>/` base differs).

v032 TDD redo cycle 24: minimal authoring under outside-in
consumer pressure. The cycle-24 test seeds a livespec-template
tree and asserts a `pass` Finding. Therefore this cycle handles
only the happy path: both directories exist + both READMEs
exist as files. The full failure-path branches (each missing
directory or README emits a path-and-name-specific fail
Finding) and bootstrap lenience (v014 N3) defer until specific
failure-path tests force them.

`spec_root` is hardcoded to `"SPECIFICATION"` (the `livespec`
template's default). The data-driven `spec_root` resolution
from `template.json` lands when a `minimal`-template test
exercises the `spec_root: "./"` value, OR when sub-spec
iteration drives the orchestrator to pass `spec_root` through
`DoctorContext` per its full PROPOSAL shape.

The check is uniform across spec trees per PROPOSAL.md §"Per-
tree check applicability" — runs unconditionally for every
spec tree, no main-tree-only restriction.
"""

from __future__ import annotations

from livespec.context import DoctorContext
from livespec.schemas.dataclasses.finding import Finding

__all__: list[str] = ["SLUG", "run"]


SLUG: str = "proposed-changes-and-history-dirs"


def run(*, ctx: DoctorContext) -> Finding:
    proposed_changes_dir = ctx.spec_root / "proposed_changes"
    proposed_changes_readme = proposed_changes_dir / "README.md"
    history_dir = ctx.spec_root / "history"
    history_readme = history_dir / "README.md"
    missing: list[str] = []
    if not proposed_changes_dir.is_dir():
        missing.append("proposed_changes/")
    elif not proposed_changes_readme.is_file():
        missing.append("proposed_changes/README.md")
    if not history_dir.is_dir():
        missing.append("history/")
    elif not history_readme.is_file():
        missing.append("history/README.md")
    if not missing:
        return Finding(
            check_id=f"doctor-{SLUG}",
            status="pass",
            message=(
                "proposed_changes/ and history/ exist with skill-owned README.md"
            ),
            path=None,
            line=None,
            spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
        )
    return Finding(
        check_id=f"doctor-{SLUG}",
        status="fail",
        message=(
            "missing required artifact(s) under <spec-root>/: "
            + ", ".join(missing)
        ),
        path=None,
        line=None,
        spec_root=ctx.spec_root.relative_to(ctx.project_root).as_posix(),
    )
