"""CLI parsing wrappers (`@impure_safe`, `exit_on_error=False`).

Phase 2 placeholder. Per-sub-command argparse builders land at later
phases. `exit_on_error=False` keeps usage errors on the railway as
`UsageError` instead of letting argparse `sys.exit` outside supervisor
scope.
"""

__all__: list[str] = []
