# livespec/io/

The only impure layer of the package. Every operation that touches
the filesystem, the git working tree, or the CLI surface lives here
under `@impure_safe` so the railway can flow through `IOResult`.

Vendored libraries (`returns`, `fastjsonschema`, `structlog`)
reach the rest of the codebase only through the typed facades in
this directory. `Any` from those vendored libs is confined here;
everywhere else uses the facade's typed surface.

Local rules:

- `LivespecError` raise-sites are restricted to this package
  (enforced by `check-no-raise-outside-io`). Pure layers convert
  exceptions into `Failure(<LivespecError>)` only after `IOResult`
  produces a concrete value.
- `argparse` wrappers MUST set `exit_on_error=False`; usage errors
  flow as `UsageError`, not `argparse.ArgumentError` or `SystemExit`.
