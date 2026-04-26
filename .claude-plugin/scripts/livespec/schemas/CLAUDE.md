# livespec/schemas/

JSON Schema Draft-7 wire contracts plus paired hand-authored
dataclasses (under `dataclasses/`). The schema is the wire contract
(validated at boundary by `fastjsonschema`); the dataclass is the
Python type threaded through the railway. They are co-authoritative.

No codegen; drift is caught by `check-schema-dataclass-pairing`.

`*.schema.json` filenames are snake_case + `.schema.json` matching
their paired dataclass file (e.g., `livespec_config.py` ↔
`livespec_config.schema.json`).
