# tests/livespec/validate/

Tests for the pure validation layer at `livespec/validate/`.
Each `make_validator()` factory produces a callable returning
`Result[<wire-dataclass>, ValidationError]`. Coverage:

- well-formed input: factory output's `__call__` returns
  `Success(<wire-dataclass>)` with all fields populated.
- malformed input: factory output's `__call__` returns
  `Failure(<ValidationError>)` with the diagnostic naming the
  offending field/path.
- the factory accepts a pre-compiled fastjsonschema validator;
  tests pass a real compiled validator from
  `livespec.io.fastjsonschema_facade` via the test fixture rather
  than constructing one inline.

Imports from `livespec.io` are forbidden in this tree
(enforced by the import-linter pure-layer contract); the
compiled validator is provided by the test setup that lives
at the supervisor level.
