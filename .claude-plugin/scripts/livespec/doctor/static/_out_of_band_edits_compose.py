"""Private composition helpers for `out_of_band_edits` auto-backfill writes."""

from __future__ import annotations

from datetime import datetime, timezone

__all__: list[str] = [
    "_compose_proposed_change_body",
    "_compose_revision_body",
    "_next_version_label",
    "_now_utc_field_timestamp",
    "_now_utc_filename_timestamp",
    "_resulting_files_listing",
]


_DOCTOR_AUTHOR: str = "livespec-doctor"
_TIMESTAMP_FILENAME_FORMAT: str = "%Y-%m-%dt%H-%M-%Sz"
_TIMESTAMP_FIELD_FORMAT: str = "%Y-%m-%dT%H:%M:%SZ"
_VERSION_DIR_PREFIX: str = "v"
_VERSION_DIR_PADDING: int = 3


def _next_version_label(*, latest_version_label: str) -> str:
    """Compute the v(N+1) directory name from the current latest label.

    Latest is `vNNN` (e.g., `v001`); next is `v(NNN+1)` (e.g.,
    `v002`), zero-padded to 3 digits. Mirrors the
    `_format_next_version_name` helper in `_revise_railway_emits.py`
    but keyed off the already-resolved latest label rather than a
    fresh `list_dir` walk — by the time this code runs, the
    out_of_band_edits comparison has already resolved the latest
    version via `_latest_committed_version_at_head`.
    """
    suffix = latest_version_label[len(_VERSION_DIR_PREFIX) :]
    next_n = int(suffix) + 1
    return f"{_VERSION_DIR_PREFIX}{next_n:0{_VERSION_DIR_PADDING}d}"


def _now_utc_filename_timestamp() -> str:
    """Format the current UTC time for the filename portion of the OOB artifact."""
    return datetime.now(timezone.utc).strftime(_TIMESTAMP_FILENAME_FORMAT)


def _now_utc_field_timestamp() -> str:
    """Format the current UTC time for the canonical ISO-8601 field value."""
    return datetime.now(timezone.utc).strftime(_TIMESTAMP_FIELD_FORMAT)


def _compose_proposed_change_body(
    *,
    topic: str,
    created_at: str,
    diff_text: str,
) -> str:
    """Compose the proposed-change file body with front-matter + diff section.

    Front-matter conforms to proposed_change_front_matter.schema.json
    (required keys: topic, author, created_at). Body has one
    `## Proposal: <topic>` section explaining the auto-backfill
    rationale and a `### Proposed Changes` subsection carrying the
    unified diff per file.
    """
    return (
        "---\n"
        f"topic: {topic}\n"
        f"author: {_DOCTOR_AUTHOR}\n"
        f"created_at: {created_at}\n"
        "---\n"
        "\n"
        f"## Proposal: {topic}\n"
        "\n"
        "doctor detected drift between HEAD-active spec content and the\n"
        "HEAD-history-vN snapshot; this auto-backfill records the active\n"
        "state as the new canonical version.\n"
        "\n"
        "### Proposed Changes\n"
        "\n"
        "```diff\n"
        f"{diff_text}"
        "```\n"
    )


def _compose_revision_body(
    *,
    proposal_filename: str,
    revised_at: str,
    resulting_files_listing: str,
) -> str:
    """Compose the revision file body with front-matter + decision sections.

    Front-matter conforms to revision_front_matter.schema.json
    (required keys: proposal, decision, revised_at, author_human,
    author_llm). Body has `## Decision and Rationale` (always) and
    `## Resulting Changes` (because decision is `accept` per
    PROPOSAL §"Backfill on drift").
    """
    return (
        "---\n"
        f"proposal: {proposal_filename}\n"
        "decision: accept\n"
        f"revised_at: {revised_at}\n"
        f"author_human: {_DOCTOR_AUTHOR}\n"
        f"author_llm: {_DOCTOR_AUTHOR}\n"
        "---\n"
        "\n"
        "## Decision and Rationale\n"
        "\n"
        "doctor detected out-of-band drift between HEAD-active spec\n"
        "content and the HEAD-history-vN snapshot; this auto-backfill\n"
        "records the active spec as the new canonical version.\n"
        "\n"
        "## Resulting Changes\n"
        "\n"
        f"{resulting_files_listing}\n"
    )


def _resulting_files_listing(*, enumerated_files: tuple[str, ...]) -> str:
    """Render the `## Resulting Changes` body lines as a Markdown bullet list.

    `enumerated_files` is non-empty in every reachable call site —
    `route_drift_outcome` only invokes the writer on a non-empty
    `diverging_files`, and divergence presupposes a non-empty
    enumeration union — so the empty-list `(none)` fallback that
    `_compose_resulting_changes_section` carries in
    `_revise_helpers.py` is unreachable here and intentionally
    omitted.
    """
    return "\n".join(f"- {name}" for name in enumerated_files)
