"""The unified `WorkItem` model + `AuditRecord` + the schema enums/aliases.

The work-item record schema is codified HERE, in this repo's own
`### livespec_runtime.work_items.types` (SPECIFICATION/contracts.md):
livespec CORE's `SPECIFICATION/` delegates the work-item schema to the
runtime + orchestrator spec trees and hosts no normative copy of it.
Every field below has an entry there; the field types here are the
Python-level realization.

This is the SHARED lift of the model both `livespec-impl-git-jsonl`
and `livespec-impl-beads` re-implemented identically. The unified
shape is a 22-field record: 15 required fields (including the `rank`
ordering key) followed by 7 optional-on-read fields. `rank` is the
sole ordering authority — the prior `priority: int` is REMOVED (two
order sources are two conflicting truths). The `spec_commitment_hint`
/ `acceptance_criteria` / `notes` / `supersedes` pointers and the
`admission_policy` / `acceptance_policy`
/ `blocked_reason` policy fields all follow the blessed `… | None`
optional-on-read pattern: legacy records lacking them read back as
`None`, with no in-place migration.

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
    "AcceptancePolicy",
    "AdmissionPolicy",
    "AuditRecord",
    "DependsOnRaw",
    "Origin",
    "Resolution",
    "StoredBlockedReason",
    "WorkItem",
    "WorkItemStatus",
    "WorkItemType",
]

DependsOnRaw = str | dict[str, Any]

WorkItemStatus = Literal[
    "backlog",
    "pending-approval",
    "ready",
    "active",
    "acceptance",
    "blocked",
    "done",
]
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
AdmissionPolicy = Literal["auto", "manual"]
AcceptancePolicy = Literal["ai-only", "human-only", "ai-then-human"]
StoredBlockedReason = Literal["needs-human", "infra-external"]


@dataclass(frozen=True, slots=True, kw_only=True)
class AuditRecord:
    """Audit-trail fields captured at completed-resolution closure time.

    `merge_sha` and `pr_number` are the merge-evidence fields landed for
    li-tenpup (the `work-item-merge-evidence` child PC). Per this repo's
    `### livespec_runtime.work_items.types` -> `AuditRecord`, `merge_sha`
    is the required, non-empty SHA of the merge commit on the canonical
    branch that introduced the work; `pr_number` is the optional GitHub
    PR number (int or `None`) for traceability. Audit objects authored
    before `pr_number` landed read back as `None` without firing a schema
    violation; `merge_sha` is required-on-read for any audit object the
    merge-evidence static check will later attest.
    """

    verification_timestamp: str
    commits: tuple[str, ...]
    files_changed: tuple[str, ...]
    merge_sha: str
    pr_number: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkItem:
    """A single work-item record (the unified git-jsonl/beads shape).

    `rank` is the fractional/lexicographic ordering key — the SOLE
    ordering authority. Strictly required, non-null, no default: a field
    this library owns is set on every record it writes. Legacy pre-`rank`
    lines on disk read back through a store-adapter bottom-sentinel (see
    `### livespec_runtime.work_items.rank`), NOT through nullability in
    the domain type; `priority: int` is removed (two order sources are
    two conflicting truths).

    `assignee` is REUSED in place as the claimed-by/owner field (beads
    has no native `owner`; `assignee` maps 1:1 to its native field). It
    is set by the Dispatcher on `admit` and is REQUIRED once
    `status == "active"` (the `active ⟹ assignee` invariant). The
    dataclass cannot enforce that conditional requirement; the
    orchestrators' doctor does, at L1.

    `spec_commitment_hint` is the OPTIONAL pairing field landed for
    livespec PC #4 sub-proposal 3 (livespec v083). When the work-item
    is filed in response to a spec-side `spec_commitments.impl_followups[]`
    declaration, this field carries the originating `id_hint` verbatim.
    For freeform work-items unrelated to any spec commitment, it is
    `None`. Legacy records lacking the field on disk read back as `None`
    (no in-place migration required); the field is OPTIONAL on the read
    path but always written explicitly on append (as `null` or the value).

    `acceptance_criteria` carries first-class operator-authored acceptance
    criteria for the work-item. `notes` carries first-class operator notes
    that should survive store-to-WorkItem reads and downstream rendering.
    Both fields follow the same blessed `… | None` optional-on-read
    pattern as `spec_commitment_hint`: legacy records lacking the field on
    disk read back as `None` with no in-place migration required.

    `supersedes` is the append-only supersession pointer (per this repo's
    `### livespec_runtime.work_items.reduce` and the append-only store
    disciplines). `None` marks an original record; a non-None value
    carries the stable per-record identity (`work_item_record_identity`)
    of the single prior record this record amends. Required-on-write,
    optional-on-read with the same legacy-record treatment as
    `spec_commitment_hint`. The canonical head reduction in
    `livespec_runtime.work_items.reduce` consumes this pointer; a
    substrate whose records are inherently one-per-id (e.g. beads) simply
    leaves it `None`, the degenerate (identity-collection) case of the
    same reducer.

    `admission_policy` / `acceptance_policy` / `blocked_reason` follow
    the same blessed `… | None` optional-on-read pattern. `None` means
    inherit from the nearest ancestor epic, else the system safe default
    (`manual` admission, `ai-then-human` acceptance). `blocked_reason`
    stores ONLY `{needs-human, infra-external}` (`StoredBlockedReason`);
    the third reason `dependency` is DERIVED, never stored — it appears
    only as a rendered `Lane.reason` (see
    `### livespec_runtime.work_items.lifecycle`).
    """

    id: str
    type: WorkItemType
    status: WorkItemStatus
    title: str
    description: str
    origin: Origin
    gap_id: str | None
    rank: str
    assignee: str | None
    depends_on: tuple[DependsOnRaw, ...]
    captured_at: str
    resolution: Resolution | None
    reason: str | None
    audit: AuditRecord | None
    superseded_by: str | None
    spec_commitment_hint: str | None = None
    acceptance_criteria: str | None = None
    notes: str | None = None
    supersedes: str | None = None
    admission_policy: AdmissionPolicy | None = None
    acceptance_policy: AcceptancePolicy | None = None
    blocked_reason: StoredBlockedReason | None = None
