# tests/livespec/schemas/dataclasses/

Per-dataclass tests for the wire dataclasses under
`livespec/schemas/dataclasses/`. Each `test_<name>.py` covers
the matching `<name>.py`:

- field invariants (`frozen=True`, `kw_only=True`,
  `slots=True` per the strict-dataclass triple) hold;
- the `validate/<name>.py` factory + the wire dataclass shape
  are paired (`check-schema-dataclass-pairing` enforces this
  three-way relationship at AST-level; tests cover the
  validate-side round-trip);
- domain-primitive newtypes (`Author`, `TopicSlug`,
  `TemplateName`, `SpecRoot`, `SchemaId`) appear at the
  expected fields per `check-newtype-domain-primitives`.
