# livespec/parse/

Pure parsers (Result-returning). No I/O — every function takes an
in-memory `str` and returns `Result[<Dataclass>, ValidationError]`
or similar. Importing from `livespec/io/` is banned in this
directory (enforced by `import-linter`'s `parse-and-validate-are-pure`
contract).

`jsonc.py` wraps the vendored `jsoncomment` shim (per v026 D1) and
is the canonical JSONC entry point for the rest of the package.
`front_matter.py` is deferred until the restricted-YAML
deferred-items decision lands.
