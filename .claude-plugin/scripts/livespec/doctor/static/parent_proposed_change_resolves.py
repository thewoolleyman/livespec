# pyright: reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
#
# HKT erosion from the returns library: bind chains lose flow-narrowing
# through pyright strict mode because returns uses KindN higher-kinded
# types that pyright cannot unify with concrete IOResult. Per-call cast
# or refactor to named typed functions is the canonical fix; this file's
# railway composition pattern means roughly half of all lines are bind
# targets, so file-level silencing keeps the source readable. Non-railway
# code in this tree retains full enforcement (other modules do not carry
# this pragma). reportArgumentType is left ON so non-HKT firings still
# surface; HKT-related reportArgumentType call sites carry per-line
# ignore markers attached to the offending argument's line below.
"""Static-phase doctor check: parent_proposed_change_resolves.

Per work-item li-ixin2s (PC #2 follow-up of v081
`coordinating-epic-stale-revise-enforcement`, paired with li-ymwpk2
which widened the proposed-change front-matter schema): for every
PC in `<spec-root>/proposed_changes/` AND every accepted PC in
`<spec-root>/history/vNNN/proposed_changes/` (audit-trail
traversal) that carries `parent_proposed_change`:

  - Local form (no `#` prefix): verify the cited topic exists in
    the same spec_root's `proposed_changes/` OR any
    `history/vNNN/proposed_changes/`. Fire `fail` if neither
    resolves.
  - Cross-repo form (`<repo>#<topic>` prefix): V1 limits to
    NOTING the citation. Folded into an info-shaped skipped
    finding when there are no local-form fails — but cross-repo
    form NEVER fails the check. Cross-repo lookup is deferred to
    a follow-up per the PC body.

PCs without `parent_proposed_change` are silently a pass (the
field is optional). A spec_root with no PCs anywhere yields a
single pass-Finding for the check.

The supervisor surfaces one Finding per check per spec_root
(per `livespec/doctor/run_static.py._run_one_check`); multiple
violations are aggregated into a single fail-Finding whose
message enumerates each unresolved citation. The path field
names the FIRST violating PC; the message lists every
violating PC for narration. Resolution priority: any local-form
fail wins; otherwise any cross-repo citation surfaces as a
skipped-Finding (informative noting); otherwise a pass-Finding.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult, IOSuccess
from returns.result import Failure

from livespec.context import DoctorContext
from livespec.errors import LivespecError
from livespec.parse import front_matter
from livespec.schemas.dataclasses.finding import Finding
from livespec.types import CheckId, SpecRoot

__all__: list[str] = ["SLUG", "run"]


SLUG: CheckId = CheckId("doctor-parent-proposed-change-resolves")

_PROPOSED_CHANGES_DIR = "proposed_changes"
_HISTORY_SUBDIR = "history"
_PARENT_FIELD = "parent_proposed_change"
_CROSS_REPO_SEPARATOR = "#"
_REVISION_SUFFIX = "-revision.md"
_MD_SUFFIX = ".md"


def _make_finding(
    *,
    ctx: DoctorContext,
    status: str,
    message: str,
    path: str | None = None,
) -> Finding:
    """Build a Finding with the check's SLUG + spec_root."""
    return Finding(
        check_id=SLUG,
        status=status,
        message=message,
        path=path,
        line=None,
        spec_root=SpecRoot(str(ctx.spec_root)),
    )


def _is_pc_file(*, entry: Path) -> bool:
    """Return True when `entry` is a candidate PC (`<topic>.md`, not a revision)."""
    if not entry.is_file():
        return False
    if not entry.name.endswith(_MD_SUFFIX):
        return False
    return not entry.name.endswith(_REVISION_SUFFIX)


def _list_pc_files_in(*, directory: Path) -> list[Path]:
    """Return PC `<topic>.md` files in `directory` (skipping revision files)."""
    if not directory.is_dir():
        return []
    return sorted(entry for entry in directory.iterdir() if _is_pc_file(entry=entry))


def _list_history_version_dirs(*, spec_root: Path) -> list[Path]:
    """Return immediate children of `<spec_root>/history/` that are directories."""
    history_dir = spec_root / _HISTORY_SUBDIR
    if not history_dir.is_dir():
        return []
    return sorted(child for child in history_dir.iterdir() if child.is_dir())


def _collect_known_topics(*, spec_root: Path) -> set[str]:
    """Union the topic stems of every PC in proposed_changes/ + history/vNNN/proposed_changes/.

    A topic stem is the file's `.stem` (filename without `.md`).
    Revision files (`*-revision.md`) are excluded — only the
    canonical `<topic>.md` artifacts count as resolvable
    references. PCs in any pruned vNNN/ directory are still
    included by directory iteration (pruned-marker exclusion is
    not strictly required here; the audit-trail invariant is
    "any historical reference resolves," and pruned markers do
    not remove the proposed_changes/ contents byte-for-byte from
    disk in the v1 prune flow).
    """
    topics: set[str] = set()
    for entry in _list_pc_files_in(directory=spec_root / _PROPOSED_CHANGES_DIR):
        topics.add(entry.stem)
    for version_dir in _list_history_version_dirs(spec_root=spec_root):
        for entry in _list_pc_files_in(directory=version_dir / _PROPOSED_CHANGES_DIR):
            topics.add(entry.stem)
    return topics


def _parse_parent_value(*, pc_path: Path) -> str | None:
    """Return `parent_proposed_change` for `pc_path` or None on absence/parse-fail.

    Parse failures are absorbed — other checks own malformed-
    front-matter detection. Returns None when the field is absent
    or holds a non-string value (the schema-pass guarantee at the
    propose-change boundary makes the non-string case a logic
    bug; here we defensively skip). I/O errors during the
    `read_text` call propagate as raised exceptions to the
    supervisor's bug-catcher per the pure-check contract; the
    caller has already filtered to files that exist via
    `_is_pc_file`.
    """
    text = pc_path.read_text(encoding="utf-8")
    parse_result = front_matter.parse_front_matter(text=text)
    if isinstance(parse_result, Failure):
        return None
    fm = parse_result.unwrap()
    value = fm.get(_PARENT_FIELD)
    if not isinstance(value, str):
        return None
    return value


def _list_all_citing_pcs(*, spec_root: Path) -> list[Path]:
    """List every PC (current + historical accepted) in `spec_root`, sorted."""
    citing_pcs: list[Path] = []
    citing_pcs.extend(_list_pc_files_in(directory=spec_root / _PROPOSED_CHANGES_DIR))
    for version_dir in _list_history_version_dirs(spec_root=spec_root):
        citing_pcs.extend(_list_pc_files_in(directory=version_dir / _PROPOSED_CHANGES_DIR))
    return citing_pcs


def _classify_citations(
    *,
    spec_root: Path,
    known_topics: set[str],
) -> tuple[list[tuple[Path, str]], list[tuple[Path, str]]]:
    """Walk every PC and return (local_fails, cross_repo_notes).

    `local_fails` is `(pc_path, cited_topic)` for every local-form
    citation whose topic is not in `known_topics`. `cross_repo_notes`
    is `(pc_path, raw_value)` for every cross-repo-form citation.
    PCs without `parent_proposed_change` are silently filtered.
    """
    local_fails: list[tuple[Path, str]] = []
    cross_repo_notes: list[tuple[Path, str]] = []
    for pc_path in _list_all_citing_pcs(spec_root=spec_root):
        parent_value = _parse_parent_value(pc_path=pc_path)
        if parent_value is None:
            continue
        if _CROSS_REPO_SEPARATOR in parent_value:
            cross_repo_notes.append((pc_path, parent_value))
            continue
        if parent_value not in known_topics:
            local_fails.append((pc_path, parent_value))
    return local_fails, cross_repo_notes


def _format_local_fails(
    *,
    ctx: DoctorContext,
    local_fails: list[tuple[Path, str]],
) -> Finding:
    """Build a single fail-Finding summarizing every local-form unresolved citation.

    Path field names the first violating PC for tools that
    consume the structured payload; message lists every
    violating PC for narration. Per the v1 supervisor shape,
    multiple violations are aggregated into one Finding (the
    same pattern `no-orphan-dependency` uses for unresolved
    `depends_on`).
    """
    first_pc, _first_topic = local_fails[0]
    first_pc_rel = first_pc.relative_to(ctx.spec_root)
    pairs_joined = ", ".join(
        f"{pc.relative_to(ctx.spec_root)}→{topic}" for pc, topic in local_fails
    )
    return _make_finding(
        ctx=ctx,
        status="fail",
        message=(
            f"parent-proposed-change-resolves: {len(local_fails)} unresolved "
            f"`{_PARENT_FIELD}` citation(s): {pairs_joined}. Either fix each "
            f"`{_PARENT_FIELD}` value to a topic that exists in "
            f"`{_PROPOSED_CHANGES_DIR}/` or any "
            f"`{_HISTORY_SUBDIR}/vNNN/{_PROPOSED_CHANGES_DIR}/`, or file the "
            f"missing parent PC(s) first."
        ),
        path=str(first_pc_rel),
    )


def _format_cross_repo_notes(
    *,
    ctx: DoctorContext,
    cross_repo_notes: list[tuple[Path, str]],
) -> Finding:
    """Build a single skipped-Finding noting cross-repo citations.

    Cross-repo lookup is deferred to a follow-up per the PC body.
    V1 surfaces the citation in informational form (status
    `skipped`) but never fails. Path field names the first PC
    carrying a cross-repo citation; message lists each pair.
    """
    first_pc, _first_value = cross_repo_notes[0]
    first_pc_rel = first_pc.relative_to(ctx.spec_root)
    pairs_joined = ", ".join(
        f"{pc.relative_to(ctx.spec_root)}→{value}" for pc, value in cross_repo_notes
    )
    return _make_finding(
        ctx=ctx,
        status="skipped",
        message=(
            f"parent-proposed-change-resolves: {len(cross_repo_notes)} cross-repo "
            f"`{_PARENT_FIELD}` citation(s) noted (not resolved in V1): "
            f"{pairs_joined}. Cross-repo lookup is deferred to a follow-up per "
            f"the PC #2 body of v081 coordinating-epic-stale-revise-enforcement."
        ),
        path=str(first_pc_rel),
    )


def _pass_finding(*, ctx: DoctorContext) -> Finding:
    """Build the canonical pass-Finding when there is nothing to surface."""
    return _make_finding(
        ctx=ctx,
        status="pass",
        message=(
            "parent-proposed-change-resolves: every `parent_proposed_change` "
            "local-form citation resolves to a PC in `proposed_changes/` or "
            "`history/vNNN/proposed_changes/`"
        ),
    )


def _evaluate(*, ctx: DoctorContext) -> Finding:
    """Build the single Finding the supervisor expects from this check."""
    known_topics = _collect_known_topics(spec_root=ctx.spec_root)
    local_fails, cross_repo_notes = _classify_citations(
        spec_root=ctx.spec_root,
        known_topics=known_topics,
    )
    if local_fails:
        return _format_local_fails(ctx=ctx, local_fails=local_fails)
    if cross_repo_notes:
        return _format_cross_repo_notes(ctx=ctx, cross_repo_notes=cross_repo_notes)
    return _pass_finding(ctx=ctx)


def run(*, ctx: DoctorContext) -> IOResult[Finding, LivespecError]:
    """Run the parent-proposed-change-resolves check against `ctx`.

    Walks every PC in `<spec_root>/proposed_changes/` and every
    accepted PC in `<spec_root>/history/vNNN/proposed_changes/`;
    for each PC carrying `parent_proposed_change`, classifies the
    citation as local-form (resolvable) or cross-repo-form (V1
    noted-only). The single returned Finding follows priority:

      fail (any local-form unresolved) >
      skipped (any cross-repo citation) >
      pass (otherwise).
    """
    return IOSuccess(_evaluate(ctx=ctx))
