"""livespec.commands: one module per sub-command (run + main pair).

Doctor has no command module here — its supervisor lives at
`livespec/doctor/run_static.py`. Help has no command module
either — `/livespec:help` is a SKILL.md-only sub-command with no
Python wrapper.
"""

__all__: list[str] = []
