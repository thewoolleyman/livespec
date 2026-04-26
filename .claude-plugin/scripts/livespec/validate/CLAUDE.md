# livespec/validate/

Pure validators (Result-returning, factory shape). No I/O. Each
validator pairs 1:1 with a `schemas/*.schema.json` file and a
`schemas/dataclasses/<name>.py` dataclass per v013 M6.

Factory shape: `make_validator()` returns a closure
`(payload: dict) -> Result[<Dataclass>, ValidationError]` with the
fastjsonschema-compiled validator captured. Compilation cost is
paid once per process; the closure is a pure function thereafter.

Drift between schema, dataclass, and validator is enforced
mechanically by `check-schema-dataclass-pairing` (three-way AST
walker per v013 M6).
