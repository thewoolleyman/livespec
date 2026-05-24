# scripts/_stubs/fastjsonschema-stubs/

Type stubs for the vendored `fastjsonschema` package.

Public surface covered:

- `compile(definition: dict[str, Any], ...) -> Callable[[dict[str, Any]], dict[str, Any]]`
- `JsonSchemaValueException(message, value, name, definition, rule)`

Consumers (compiled validator + raised exception type) live in
`livespec/validate/*.py`. The factory shape is:

```python
@safe(exceptions=(fastjsonschema.JsonSchemaValueException,))
def _raw_validate(*, payload, schema) -> <Dataclass>:
    validator = fastjsonschema.compile(schema)
    validated = validator(payload)
    return <Dataclass>(...)
```

The stub types the `validator` callable so downstream
`validated["key"]` index access flows as `Any` (from
`dict[str, Any]`) rather than reportIndexIssue against Unknown.
