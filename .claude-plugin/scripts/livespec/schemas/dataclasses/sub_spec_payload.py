"""Dataclass paired with `sub_spec_payload.schema.json`.

Represents one entry inside `SeedInput.sub_specs[]`. Per v018 Q1 +
v020 Q2, the seed wrapper consumes each entry independently to
materialize one sub-spec tree under
`SPECIFICATION/templates/<template_name>/`.

The `SubSpecFile` shape mirrors `SeedFile` from
`schemas/dataclasses/seed_input.py`. They are intentionally
separate types so that schema-validation drift between the two
wire-protocol leaves is detected by `check-schema-dataclass-pairing`.
A single shared `FilePayload` could be authored later if a third
schema also needs it; the v1 minimum-viable scope keeps them
distinct.

Three-way pairing: this dataclass, `sub_spec_payload.schema.json`,
and `validate/sub_spec_payload.py` are co-authoritative.
"""

from dataclasses import dataclass

__all__: list[str] = [
    "SubSpecFile",
    "SubSpecPayload",
]


@dataclass(frozen=True, kw_only=True, slots=True)
class SubSpecFile:
    """A single `{path, content}` entry inside `SubSpecPayload.files`."""

    path: str
    content: str


@dataclass(frozen=True, kw_only=True, slots=True)
class SubSpecPayload:
    template_name: str
    files: list[SubSpecFile]
