"""SeedInput dataclass paired 1:1 with seed_input.schema.json.

Per style doc §"Skill layout — schemas/dataclasses/": fields
match the schema one-to-one in name and Python type. The
dataclass is the type that flows through the railway after
schema validation:
    Result[SeedInput, ValidationError]
from validate.seed_input.validate_seed_input.
"""

from __future__ import annotations

from dataclasses import dataclass

from livespec.types import TemplateName

__all__: list[str] = ["SeedInput"]


@dataclass(frozen=True, kw_only=True, slots=True)
class SeedInput:
    """The seed-input wire dataclass.

    Mirrors seed_input.schema.json: top-level `template` /
    `intent` / `files` / `sub_specs` (per v018 Q1 + v020 Q2).
    Per `check-newtype-domain-primitives` (v034 D7 drain
    cycle 2): `template` uses the `TemplateName` NewType from
    `livespec.types`.
    """

    template: TemplateName
    intent: str
    files: list[dict[str, str]]
    sub_specs: list[dict[str, object]]
