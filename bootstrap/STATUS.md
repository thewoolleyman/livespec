# Bootstrap status

**Current phase:** 3
**Current sub-step:** 7
**Last completed exit criterion:** phase 2
**Next action:** Phase 3 sub-step 7 — author `livespec/io/fastjsonschema_facade.py`: typed facade over the vendored `fastjsonschema`, with `compile()` cached on schema `$id` via `functools.lru_cache` per style doc §"Purity and I/O isolation" line 681-685. The facade's pure surface is the typed validator function; the impure surface (reading the schema dict from disk) is upstream of the lru_cache. Sub-step 6 closed: authored `livespec/io/cli.py` with `parse_args(*, parser: ArgumentParser, argv: Sequence[str]) -> IOResult[Namespace, UsageError | HelpRequested]` per style doc §"CLI argument parsing seam"; `-h`/`--help` detected before `parse_args` runs to short-circuit with `HelpRequested(text=parser.format_help())` (avoids argparse's implicit `sys.exit(0)`); `argparse.ArgumentError` and `ArgumentTypeError` mapped to `UsageError`; `exit_on_error=False` invariant asserted. ruff clean.
**Last updated:** 2026-04-26T09:10:59Z
**Last commit:** a8a1f73
