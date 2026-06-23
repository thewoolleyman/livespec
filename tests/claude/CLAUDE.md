# tests/claude/

Tests for agent-runtime hook scripts under the repo's `.claude/`
tree (e.g. `.claude/hooks/`). These scripts are excluded from ruff
and pyright (per `pyproject.toml`) as agent-runtime infra, so their
tests load them by file path via
`importlib.util.spec_from_file_location` rather than importing a
package. Importing a guard here brings it under coverage, so each
covered guard is tested to the repo's full line+branch bar.
