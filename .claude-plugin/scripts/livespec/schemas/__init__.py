"""livespec.schemas: JSON Schema Draft-7 files + paired dataclasses.

Phase 2 placeholder. Each `*.schema.json` (the wire contract validated
at boundary by fastjsonschema) pairs 1:1 with a hand-authored
`dataclasses/<name>.py` (the Python type threaded through the railway)
and a `validate/<name>.py` factory. Drift across the three directions
is enforced by `check-schema-dataclass-pairing` (v013 M6).

The schema JSON files themselves land at later phases as their
consumer code paths need them; the package directory is reserved
here so import paths resolve.
"""

__all__: list[str] = []
