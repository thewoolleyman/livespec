"""The unified `WorkItem` model + `AuditRecord` + the schema enums/aliases.

The work-item schema is codified by livespec/SPECIFICATION/contracts.md
§"Work-items JSONL record schema" (and the beads-side mapping
§"Work-item beads-issue mapping"). Every field below has an entry
there; the field types here are the Python-level realization.

This is the SHARED lift of the model both `livespec-impl-git-jsonl`
and `livespec-impl-beads` re-implemented identically. The unified
shape is the git-jsonl 16-field record: it carries the extra
`supersedes` append-only-supersession pointer (the sixteenth schema
key); beads' historical WorkItem was byte-identical to this MINUS that
one field, so adopting the superset is lossless for both consumers.

Transitive type closure: the only non-primitive type reachable from
`WorkItem` is `AuditRecord` (via the `audit` field). `AuditRecord`'s
fields are all primitives (`str`, `tuple[str, ...]`, `int | None`).
The Spec-Reader return types (`SpecSnapshot`/`SpecDiff`/`FileDiff`) are
NOT reachable from `WorkItem`, so they are deliberately NOT lifted into
this shared package — they stay per-impl with the Spec Reader.
"""

from dataclasses import dataclass
from typing import Any, Literal

__all__: list[str] = [
    "AuditRecord",
    "DependsOnRaw",
    "Origin",
    "Resolution",
    "WorkItem",
    "WorkItemStatus",
    "WorkItemType",
]

DependsOnRaw = str | dict[str, Any]

WorkItemStatus = Literal["open", "in_progress", "blocked", "closed", "deferred"]
WorkItemType = Literal["bug", "feature", "task", "chore", "epic"]
Origin = Literal["gap-tied", "freeform"]
Resolution = Literal[
    "completed",
    "wontfix",
    "duplicate",
    "spec-revised",
    "no-longer-applicable",
    "resolved-out-of-band",
]


@dataclass(frozen=True, slots=True, kw_only=True)
class AuditRecord:
    """Audit-trail fields captured at completed-resolution closure time.

    `merge_sha` and `pr_number` are the merge-evidence fields landed for
    li-tenpup (the `work-item-merge-evidence` child PC). Per
    livespec/SPECIFICATION/contracts.md "Work-items JSONL record schema"
    -> audit, `merge_sha` is the required, non-empty SHA of the merge
    commit on the canonical branch that introduced the work; `pr_number`
    is the optional GitHub PR number (int or `None`) for traceability.
    Audit objects authored before `pr_number` landed read back as `None`
    without firing a schema violation; `merge_sha` is required-on-read
    for any audit object the merge-evidence static check will later
    attest.
    """

    verification_timestamp: str
    commits: tuple[str, ...]
    files_changed: tuple[str, ...]
    merge_sha: str
    pr_number: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkItem:
    """A single work-item record (the unified git-jsonl/beads shape).

    `spec_commitment_hint` is the OPTIONAL pairing field landed for
    livespec PC #4 sub-proposal 3 (livespec v083). When the work-item
    is filed in response to a spec-side `spec_commitments.impl_followups[]`
    declaration, this field carries the originating `id_hint` verbatim.
    For freeform work-items unrelated to any spec commitment, it is
    `None`. Legacy records lacking the field on disk read back as
    `None` (no in-place migration required); the field is OPTIONAL on
    the read path but always written explicitly on append (as `null`
    or the value).

    `supersedes` is the append-only supersession pointer (the sixteenth
    schema key, per livespec/SPECIFICATION/contracts.md "Work-items JSONL
    record schema" -> supersedes and "Append-only store disciplines").
    `None` marks an original record; a non-None value carries the stable
    per-record identity (`work_item_record_identity`) of the single prior
    record this record amends. Required-on-write, optional-on-read with
    the same legacy-record treatment as `spec_commitment_hint`. The
    canonical head reduction in `livespec_runtime.work_items.reduce`
    consumes this pointer; a substrate whose records are inherently
    one-per-id (e.g. beads) simply leaves it `None`, which is the
    degenerate (identity-collection) case of the same reducer.
    """

    id: str
    type: WorkItemType
    status: WorkItemStatus
    title: str
    description: str
    origin: Origin
    gap_id: str | None
    priority: int
    assignee: str | None
    depends_on: tuple[DependsOnRaw, ...]
    captured_at: str
    resolution: Resolution | None
    reason: str | None
    audit: AuditRecord | None
    superseded_by: str | None
    spec_commitment_hint: str | None = None
    supersedes: str | None = None
