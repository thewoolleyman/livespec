"""RevisionFrontMatter dataclass paired 1:1 with revision_front_matter.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
    Result[RevisionFrontMatter, ValidationError]
from validate.revision_front_matter.validate_revision_front_matter.

Per `check-newtype-domain-primitives`: both `author_human` and
`author_llm` use the `Author` NewType.
"""

from __future__ import annotations

from dataclasses import dataclass

from livespec.types import Author

__all__: list[str] = ["RevisionFrontMatter"]


@dataclass(frozen=True, kw_only=True, slots=True)
class RevisionFrontMatter:
    """The revision YAML front-matter wire dataclass.

    Mirrors revision_front_matter.schema.json: required
    `proposal` (paired-file stem), `decision`
    ('accept'|'modify'|'reject'), `revised_at` UTC ISO-8601,
    `author_human`, `author_llm`.
    """

    proposal: str
    decision: str
    revised_at: str
    author_human: Author
    author_llm: Author
