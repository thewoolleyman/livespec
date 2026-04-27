"""Dataclass paired with `seed_input.schema.json`.

Represents the parsed JSON payload that the active template's
`prompts/seed.md` produces and that `bin/seed.py` consumes via
`--seed-json`. Per v018 Q1 + v020 Q2, the payload carries main-spec
files plus an optional `sub_specs[]` array of per-template
`SubSpecPayload` entries for atomic multi-tree seed.

`SeedFile` is the inlined `{path, content}` shape used both at
the top-level `files[]` and inside each `SubSpecPayload.files[]`.
It is co-defined here (not in its own schema/dataclass triple)
because the structure is purely a wire-protocol leaf — a 2-field
record with no other consumers in v1.

`SubSpecPayload` has its own paired schema and validator
(`sub_spec_payload.schema.json` + `validate/sub_spec_payload.py`)
because the seed wrapper consumes each entry independently per
v018 Q1 / v020 Q2.

Three-way pairing: this dataclass, `seed_input.schema.json`, and
`validate/seed_input.py` are co-authoritative.
"""

from dataclasses import dataclass

from livespec.schemas.dataclasses.sub_spec_payload import SubSpecPayload
from livespec.types import TemplateName

__all__: list[str] = [
    "SeedFile",
    "SeedInput",
]


@dataclass(frozen=True, kw_only=True, slots=True)
class SeedFile:
    """A single `{path, content}` entry in `SeedInput.files` or
    `SubSpecPayload.files`. The `path` is relative to the project
    root; the wrapper resolves it before writing."""

    path: str
    content: str


@dataclass(frozen=True, kw_only=True, slots=True)
class SeedInput:
    template: TemplateName
    intent: str
    files: list[SeedFile]
    sub_specs: list[SubSpecPayload]
