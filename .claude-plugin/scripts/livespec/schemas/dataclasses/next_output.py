"""NextOutput dataclass paired 1:1 with next_output.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway from the
ranker into the supervisor's JSON-emit stage:
    Result[NextOutput, ValidationError]
from validate.next_output.validate_next_output.

`action` and `urgency` are typed as `str` (not `Literal[...]`)
because fastjsonschema enforces the enum membership at schema-
validation time; the schema is the wire contract and the
dataclass mirrors its plain shape. No NewType applies under
`check-newtype-domain-primitives`: neither field's name matches
the registered canonical-target list.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__: list[str] = ["NextOutput"]


@dataclass(frozen=True, kw_only=True, slots=True)
class NextOutput:
    """The `/livespec:next` stdout payload wire dataclass.

    Mirrors next_output.schema.json: required `action`, `reason`,
    `urgency`. Constructed by the ranker stage; serialized to
    JSON on stdout by the supervisor.
    """

    action: str
    reason: str
    urgency: str
