# livespec/schemas/dataclasses/

Hand-authored `@dataclass(frozen=True, kw_only=True, slots=True)`
classes paired 1:1 with `../<name>.schema.json`. Fields match the
schema one-to-one in name and Python type. Domain-meaningful
fields use the canonical NewType aliases from `livespec/types.py`
(enforced by `check-newtype-domain-primitives`).

The dataclass is the type that flows through the railway after
schema validation:
`Result[<Dataclass>, ValidationError]` from each validator.
