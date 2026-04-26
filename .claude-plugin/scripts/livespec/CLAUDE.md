# livespec/

The Python package the shebang wrappers import. Subdirectories
follow the layered architecture in
`python-skill-script-style-requirements.md` §"Skill layout":
`io/` is the only impure layer; `parse/` and `validate/` are pure;
`commands/` and `doctor/` orchestrate the railway and pattern-match
the final `IOResult`.

Module-level invariants:

- Every module declares `__all__: list[str]` enumerating its public
  surface (enforced by `check-all-declared`).
- `__init__.py` runs the structlog configuration + `run_id` bind
  exactly once per process; do not configure structlog elsewhere.
- `errors.py` holds the `LivespecError` hierarchy + `HelpRequested`;
  domain errors flow as `IOFailure(<LivespecError>)` payloads on
  the railway, bugs propagate as raised exceptions to the supervisor.
- `if __name__ == "__main__":` blocks are banned in this tree
  (enforced by `check-main-guard`); supervisors live at
  `commands/<cmd>.main()` and `doctor/run_static.main()`.
