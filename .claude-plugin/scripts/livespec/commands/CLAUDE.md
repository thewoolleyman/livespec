# livespec/commands/

One module per sub-command (`seed`, `propose-change`, `critique`,
`revise`, `resolve-template`, `prune-history`). Each module exports
`run()` (the railway entry returning `IOResult`) and `main()` (the
supervisor returning `int`).

Doctor is intentionally absent here: its supervisor lives at
`livespec/doctor/run_static.py`. Help is also absent —
`/livespec:help` is a SKILL.md-only sub-command with no Python
wrapper.

Supervisor `main()` functions are the only place outside `bin/` and
`livespec/doctor/run_static.py` where `sys.stdout.write` is
permitted (for documented stdout contracts: `HelpRequested.text`,
the resolved-path single-line output of `resolve_template`). The
exemption is per-`main()` only, not per-helper.
