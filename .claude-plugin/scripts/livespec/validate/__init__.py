"""livespec.validate: pure validators (Result-returning, factory shape).

Each validator pairs 1:1 with a `schemas/*.schema.json` file and a
`schemas/dataclasses/<name>.py` dataclass per v013 M6. Validators
follow the factory shape: `make_validator()` returns a function
`(payload: dict) -> Result[<Dataclass>, ValidationError]` with the
fastjsonschema-compiled validator captured in the closure.
"""

__all__: list[str] = []
