"""Type stubs for the installed `livespec_dev_tooling` package.

The upstream `livespec-dev-tooling` package does not ship a `py.typed`
marker, so pyright treats every import as untyped (`Unknown`). These
stubs declare the minimal public surface livespec consumes from
`livespec_dev_tooling.canonical_checks` so the strict-mode
`reportMissingTypeStubs` diagnostic does not fire at the
`copier_extensions.canonical_checks` and
`dev-tooling/checks/copier_template_smoke.py` import sites.

Scope: only the modules livespec imports directly are declared.
Other modules (`livespec_dev_tooling.checks.<slug>`,
`livespec_dev_tooling.cross_repo.*`, etc.) are consumed exclusively
via `python -m` subprocess invocations and need no stubs.

When upstream livespec-dev-tooling ships its own `py.typed` marker
in a future release, this stub package should be removed and the
import sites left untouched.
"""
