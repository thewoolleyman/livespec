"""Dataclass paired with `revision_front_matter.schema.json`.

Represents the YAML front-matter at the top of a revision file
(<spec-root>/history/vNNN/proposed_changes/<topic>-revision.md).
Per PROPOSAL.md §"Revision file format" lines 3027-3050.

Three-way pairing with `revision_front_matter.schema.json` and
`validate/revision_front_matter.py`.
"""
from dataclasses import dataclass
from typing import Literal

from livespec.types import Author

__all__: list[str] = [
    "Decision",
    "RevisionFrontMatter",
]


Decision = Literal["accept", "modify", "reject"]
"""The three v1 per-proposal decisions. Mirrors the schema's
`decision` enum."""


@dataclass(frozen=True, kw_only=True, slots=True)
class RevisionFrontMatter:
    proposal: str
    decision: Decision
    revised_at: str
    author_human: str
    author_llm: Author
