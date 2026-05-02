"""ProposedChangeFrontMatter dataclass paired 1:1 with proposed_change_front_matter.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
    Result[ProposedChangeFrontMatter, ValidationError]
from validate.proposed_change_front_matter.validate_proposed_change_front_matter.

Per `check-newtype-domain-primitives`: `topic` uses the
`TopicSlug` NewType (added at cycle 3d) and `author` uses the
`Author` NewType (added at cycle 2). `created_at` is plain
`str` (ISO 8601 datetime; no canonical NewType for timestamps
in this iteration).
"""

from __future__ import annotations

from dataclasses import dataclass

from livespec.types import Author, TopicSlug

__all__: list[str] = ["ProposedChangeFrontMatter"]


@dataclass(frozen=True, kw_only=True, slots=True)
class ProposedChangeFrontMatter:
    """The proposed-change YAML front-matter wire dataclass.

    Mirrors proposed_change_front_matter.schema.json: required
    `topic` (kebab-case slug), `author` identifier, and
    `created_at` UTC ISO-8601 datetime.
    """

    topic: TopicSlug
    author: Author
    created_at: str
