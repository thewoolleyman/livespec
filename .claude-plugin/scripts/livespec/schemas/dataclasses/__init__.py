"""livespec.schemas.dataclasses: paired hand-authored dataclasses.

Phase 2 placeholder. Each dataclass is
`@dataclass(frozen=True, kw_only=True, slots=True)` per the style doc
§"Dataclass authorship", with fields matching its paired schema
one-to-one in name and Python type. Domain-meaningful fields use
NewType aliases from `livespec/types.py`.

Concrete dataclasses (`livespec_config`, `seed_input`, `revise_input`,
`proposal_findings`, `doctor_findings`, `finding`, `template_config`,
`proposed_change_front_matter`, `revision_front_matter`) land
alongside the validators that use them.
"""

__all__: list[str] = []
