"""RevisionInput dataclass paired 1:1 with revise_input.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
    Result[RevisionInput, ValidationError]
from validate.revise_input.validate_revise_input.
"""

from __future__ import annotations

from dataclasses import dataclass

from livespec.types import Author

__all__: list[str] = ["RevisionInput"]


@dataclass(frozen=True, kw_only=True, slots=True)
class RevisionInput:
    """The revise-input wire dataclass.

    Mirrors revise_input.schema.json: optional `author` string +
    required `decisions` list of objects. Each decision object
    carries `proposal_topic`, `decision` ("accept"|"modify"|
    "reject"), `rationale`, optional `modifications`, and
    optional `resulting_files` (list of `{path, content}`
    objects).

    Per `check-newtype-domain-primitives` (v034 D7 drain
    cycle 2): `author` uses the `Author` NewType from
    `livespec.types`.
    """

    author: Author | None
    decisions: list[dict[str, object]]
