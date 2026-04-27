"""Dataclass paired with `proposed_change_front_matter.schema.json`.

Represents the YAML front-matter at the top of a proposed-change
file. Per PROPOSAL.md §"Proposed-change file format" lines
2933-2989.

Three-way pairing: this dataclass,
`proposed_change_front_matter.schema.json`, and
`validate/proposed_change_front_matter.py` are co-authoritative.
"""

from dataclasses import dataclass

from livespec.types import Author, TopicSlug

__all__: list[str] = [
    "ProposedChangeFrontMatter",
]


@dataclass(frozen=True, kw_only=True, slots=True)
class ProposedChangeFrontMatter:
    topic: TopicSlug
    author: Author
    created_at: str
