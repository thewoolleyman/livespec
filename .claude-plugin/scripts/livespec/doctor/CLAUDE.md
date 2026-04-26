# livespec/doctor/

Static-phase doctor orchestrator + per-check modules. The
LLM-driven doctor phase is skill-layer (no Python module here).

`run_static.py` is the supervisor: it composes the static-check
registry into a single ROP chain, derives the exit code per the
doctor static-phase output contract, and writes
`{"findings": [...]}` to stdout. It is one of three places where
`sys.stdout.write` is permitted (per the style doc §"Logging"
exemption list).

Per-check modules live under `static/`. Each is registered in
`static/__init__.py` per v022 D7 narrowed-registry policy
(Phase 3: 8 implemented checks; Phase 7: remaining four).
