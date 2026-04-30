"""Finding dataclass paired 1:1 with finding.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the value-object every static-phase doctor check
returns; the orchestrator collects findings per tree into the
canonical doctor-findings JSON payload.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__: list[str] = ["Finding"]


@dataclass(frozen=True, kw_only=True, slots=True)
class Finding:
    """The single-check Finding wire dataclass.

    Mirrors finding.schema.json: `check_id` is the
    `doctor-<slug>` canonical id; `status` is one of
    `pass` / `fail` / `skipped`; `message` is human-readable;
    `path` and `line` are optional file-locality fields (None
    when the check is tree-level rather than file-level);
    `spec_root` discriminates per-tree origin per v018 Q1.
    """

    check_id: str
    status: str
    message: str
    path: str | None
    line: int | None
    spec_root: str
