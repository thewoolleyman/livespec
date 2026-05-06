"""File-shaping railway stages for the `revise` sub-command.

Extracted from `revise.py` at cycle 5.c.4 so the parent file's
LLOC stays under the 250-LLOC hard ceiling enforced by
`dev-tooling/checks/file_lloc.py`. The split is purely
organizational; the behavior is identical to the inline original.
Companion to the pure `_revise_helpers.py`.

Stages: precondition check on `proposed_changes/`, next-history-
version-dir resolution, per-decision write + move + resulting-
files materialization, working-spec snapshot to `history/vNNN/`.
"""

from __future__ import annotations

from pathlib import Path

from returns.io import IOResult

from livespec.commands._revise_helpers import _compose_revision_body
from livespec.errors import LivespecError, PreconditionError
from livespec.io import fs
from livespec.schemas.dataclasses.revise_input import RevisionInput

__all__: list[str] = [
    "_bind_resulting_files",
    "_check_proposed_changes_nonempty",
    "_copy_files_into",
    "_format_next_version_name",
    "_next_history_version_dir",
    "_process_decisions",
    "_snapshot_working_spec_files",
    "_verify_in_flight_proposals_present",
    "_write_and_move_per_decision",
]


def _process_decisions(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
    author_human: str,
    author_llm: str,
    revised_at: str,
) -> IOResult[RevisionInput, LivespecError]:
    """Run the file-shaping railway: precondition -> per-decision -> snapshot.

    For each decision: (1) compose `<stem>-revision.md` with the
    v011-spec-codified full 5-key front-matter + per-decision-type
    sections and write it under `<spec-target>/history/vNNN/
    proposed_changes/`; (2) move `<spec-target>/proposed_changes/
    <stem>.md` byte-identically into the new history directory;
    (3) on accept/modify, materialize `resulting_files[]` into the
    working-spec files. After all decisions, snapshot every
    spec-root file byte-identically into `<spec-target>/history/
    vNNN/` per v011 Proposal 3 item d / v038 D1 Statement B.
    Threads `author_human`, `author_llm`, and `revised_at` into
    every per-decision body composition.
    """
    return (
        _check_proposed_changes_nonempty(spec_target=spec_target)
        .bind(
            lambda _value: _next_history_version_dir(spec_target=spec_target),
        )
        .bind(
            lambda version_dir: _write_and_move_per_decision(
                revise_input=revise_input,
                spec_target=spec_target,
                version_dir=version_dir,
                author_human=author_human,
                author_llm=author_llm,
                revised_at=revised_at,
            ).bind(
                lambda _value, version_dir=version_dir: _snapshot_working_spec_files(
                    spec_target=spec_target,
                    version_dir=version_dir,
                ).map(lambda _: revise_input),
            ),
        )
    )


def _check_proposed_changes_nonempty(
    *,
    spec_target: Path,
) -> IOResult[None, LivespecError]:
    """Fail with PreconditionError when proposed_changes/ has no in-flight proposals.

    Per v011 Proposal 3 item a: revise MUST fail hard with
    PreconditionError (exit 3) when `<spec-target>/proposed_changes/`
    contains no in-flight proposal files. The skill-owned
    `proposed_changes/README.md` does not count as an in-flight
    proposal. The check fires at the railway boundary BEFORE any
    `history/vNNN/` materialization, so a precondition fail leaves
    the spec tree byte-identical.
    """
    proposed_changes_dir = spec_target / "proposed_changes"
    return fs.list_dir(path=proposed_changes_dir).bind(
        lambda children: _verify_in_flight_proposals_present(
            children=children,
            proposed_changes_dir=proposed_changes_dir,
        ),
    )


def _verify_in_flight_proposals_present(
    *,
    children: list[Path],
    proposed_changes_dir: Path,
) -> IOResult[None, LivespecError]:
    """Pass when `children` has at least one non-`README.md` file; else fail."""
    in_flight = [c for c in children if c.is_file() and c.name != "README.md"]
    if in_flight:
        return IOResult.from_value(None)
    return IOResult.from_failure(
        PreconditionError(
            f"revise: {proposed_changes_dir} contains no in-flight "
            f"proposal files (README.md does not count)",
        ),
    )


def _next_history_version_dir(
    *,
    spec_target: Path,
) -> IOResult[Path, LivespecError]:
    """Compute `<spec-target>/history/v(max+1)/` from existing v* dirs.

    Lists the spec-target's `history/` directory, filters for
    entries matching `v\\d+`, computes the next version number,
    and returns the path. When `history/` is missing or empty,
    defaults to v001 (the seed-baseline case never reaches revise
    because revise requires an in-flight proposed-change which
    presupposes a v001 already exists, but the bootstrap-friendly
    default keeps the helper safe).
    """
    history_dir = spec_target / "history"
    return fs.list_dir(path=history_dir).map(
        lambda children: history_dir / _format_next_version_name(children=children),
    )


def _format_next_version_name(*, children: list[Path]) -> str:
    """Compute the next `vNNN` directory name from existing children.

    Walks the children list looking for `vNNN` patterns; tracks
    the maximum N found; returns `v(max+1)` zero-padded to three
    digits. When no `vNNN` children are present, returns "v001".
    """
    max_version = 0
    for child in children:
        if not child.is_dir():
            continue
        name = child.name
        if not name.startswith("v"):
            continue
        suffix = name[1:]
        if not suffix.isdigit():
            continue
        version = int(suffix)
        max_version = max(max_version, version)
    return f"v{max_version + 1:03d}"


def _write_and_move_per_decision(
    *,
    revise_input: RevisionInput,
    spec_target: Path,
    version_dir: Path,
    author_human: str,
    author_llm: str,
    revised_at: str,
) -> IOResult[RevisionInput, LivespecError]:
    """For each decision, write revision + move proposal + materialize resulting_files.

    Fold-style accumulator: each per-decision triple (revision-
    write + proposed-change-move + (for accept/modify)
    resulting-files-materialize) binds onto the previous IOResult
    so any failure short-circuits the rest via the typed Failure
    surface. Mirrors seed.py's `_write_main_spec_files` shape.
    """
    accumulator: IOResult[RevisionInput, LivespecError] = IOResult.from_value(
        revise_input,
    )
    for decision in revise_input.decisions:
        topic = str(decision.get("proposal_topic", ""))
        revision_target = version_dir / "proposed_changes" / f"{topic}-revision.md"
        revision_body = _compose_revision_body(
            decision=decision,
            author_human=author_human,
            author_llm=author_llm,
            revised_at=revised_at,
        )
        proposed_source = spec_target / "proposed_changes" / f"{topic}.md"
        proposed_target = version_dir / "proposed_changes" / f"{topic}.md"
        accumulator = accumulator.bind(
            lambda _value, target=revision_target, body=revision_body: fs.write_text(
                path=target,
                text=body,
            ).map(lambda _: revise_input),
        )
        accumulator = accumulator.bind(
            lambda _value, source=proposed_source, target=proposed_target: fs.move(
                source=source,
                target=target,
            ).map(lambda _: revise_input),
        )
        accumulator = _bind_resulting_files(
            accumulator=accumulator,
            decision=decision,
            spec_target=spec_target,
            revise_input=revise_input,
        )
    return accumulator


def _bind_resulting_files(
    *,
    accumulator: IOResult[RevisionInput, LivespecError],
    decision: dict[str, object],
    spec_target: Path,
    revise_input: RevisionInput,
) -> IOResult[RevisionInput, LivespecError]:
    """Append resulting_files writes to the accumulator for accept/modify.

    Per: only `accept`
    and `modify` decisions materialize resulting_files into the
    working spec; `reject` decisions produce no working-spec
    changes (just the audit-trail revision file).
    """
    decision_value = str(decision.get("decision", ""))
    if decision_value not in ("accept", "modify"):
        return accumulator
    resulting_files = decision.get("resulting_files", [])
    if not isinstance(resulting_files, list):
        return accumulator
    for entry in resulting_files:
        if not isinstance(entry, dict):
            continue
        target = spec_target / str(entry["path"])
        text = str(entry["content"])
        accumulator = accumulator.bind(
            lambda _value, target=target, text=text: fs.write_text(
                path=target,
                text=text,
            ).map(lambda _: revise_input),
        )
    return accumulator


def _snapshot_working_spec_files(
    *,
    spec_target: Path,
    version_dir: Path,
) -> IOResult[list[Path], LivespecError]:
    """Snapshot every immediate spec-root file byte-identically into `version_dir`.

    Per v011 Proposal 3 item d ("on every cut, `<spec-target>/
    history/vNNN/` snapshots every template-declared spec file
    byte-identically"). "Template-declared" is approximated as
    every immediate file child of `<spec-target>/` — directory
    children (`history/`, `proposed_changes/`, `templates/`) are
    not template-declared spec files and are skipped.
    """
    return fs.list_dir(path=spec_target).bind(
        lambda children: _copy_files_into(
            sources=children,
            target_dir=version_dir,
        ),
    )


def _copy_files_into(
    *,
    sources: list[Path],
    target_dir: Path,
) -> IOResult[list[Path], LivespecError]:
    """For each file in `sources` (skipping directories), read+write into `target_dir`.

    Composes `fs.read_text` -> `fs.write_text` per source. Bytes
    are preserved through UTF-8 round-trip (the spec contract
    requires `.md` text files only). Directory children are
    skipped via `is_file()` since the spec-root carries
    sibling subdirs (`history/`, `proposed_changes/`,
    `templates/`) that are not template-declared spec files.
    """
    accumulator: IOResult[list[Path], LivespecError] = IOResult.from_value([])
    for source in sources:
        if not source.is_file():
            continue
        target = target_dir / source.name
        accumulator = accumulator.bind(
            lambda _value, source=source, target=target: fs.read_text(path=source)
            .bind(
                lambda text, target=target: fs.write_text(path=target, text=text),
            )
            .map(lambda _: []),
        )
    return accumulator
