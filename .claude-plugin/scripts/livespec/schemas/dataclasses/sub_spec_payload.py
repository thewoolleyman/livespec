"""SubSpecPayload dataclass paired 1:1 with sub_spec_payload.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
    Result[SubSpecPayload, ValidationError]
from validate.sub_spec_payload.validate_sub_spec_payload.

Per v018 Q1 + v020 Q2: each sub-spec payload entry inside
`seed_input.sub_specs[]` carries the sub-spec template's
directory name + the spec-file content for atomic emission
alongside the main spec tree. `template_name` is a
`TemplateName` NewType (semantically; the
check-newtype-domain-primitives field-name lookup is exact-
match on `template`, not `template_name`, so the check doesn't
mechanically require it — but using TemplateName here matches
the field's semantic role).
"""

from __future__ import annotations

from dataclasses import dataclass

from livespec.types import TemplateName

__all__: list[str] = ["SubSpecPayload"]


@dataclass(frozen=True, kw_only=True, slots=True)
class SubSpecPayload:
    """A single sub-spec payload entry inside SeedInput.sub_specs[].

    Mirrors sub_spec_payload.schema.json: required `template_name`
    + `files` (list of {path, content} dicts).
    """

    template_name: TemplateName
    files: list[dict[str, str]]
