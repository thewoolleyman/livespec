"""livespec.commands.resolve_template — supervisor for `bin/resolve_template.py`.

Stub at v032 TDD redo cycle 18. Returns 0 so the wrapper imports
cleanly and the outside-in integration test
(`tests/bin/test_resolve_template.py`) advances past the
"wrapper file does not exist" failure mode to the next failure:
the path-emit stdout assertion. Subsequent cycles drive that
assertion forward by authoring the actual resolution pipeline
per PROPOSAL.md §"Template resolution contract" lines 1424-1503.

Phase 3 minimum-viable scope per PROPOSAL.md §"Template
resolution contract":

1. Parse `--project-root <path>` (default `Path.cwd()`) and
   `--template <value>` (optional; v017 Q2 pre-seed flag).
2. When `--template` is supplied:
   - If value is `"livespec"` or `"minimal"`, resolve to the
     bundle's built-in path
     `<bundle-root>/specification-templates/<name>/` where
     `<bundle-root>` = `Path(__file__).resolve().parents[3]`
     (commands/ → livespec/ → scripts/ → .claude-plugin/).
   - Otherwise, treat as a path relative to `--project-root`,
     resolve to absolute, validate (a) directory exists and
     (b) contains `template.json`. Validation failure exits 3
     (`PreconditionError`).
3. When `--template` is NOT supplied, walk upward from
   `--project-root` looking for `.livespec.jsonc`; read the
   `template` field; resolve as in step 2 (built-in name or
   user-provided path).
4. Emit the resolved absolute POSIX path on stdout as exactly
   one line followed by `\\n`. Stdout contract is frozen in v1
   per PROPOSAL.md lines 1495-1503.
5. Exit 0 on success; 3 on any of {`.livespec.jsonc` not found,
   `.livespec.jsonc` malformed/schema-invalid, resolved path
   missing, resolved path lacks `template.json`}; 2 on bad CLI
   usage; 127 on too-old Python (handled by `_bootstrap.py`).

Out of Phase 3 scope (deferred to later cycles or Phase 7
widening): `.livespec.jsonc` upward-walk + JSONC parsing
(deferred until a non-`--template` test exercises the default
flow), JSONC schema validation, full doctor pre/post lifecycle
(per PROPOSAL.md line 1485-1487 `resolve_template` has neither
pre-step nor post-step doctor static — already correct here by
construction), ROP plumbing.
"""

from __future__ import annotations

__all__: list[str] = ["main"]


def main() -> int:
    return 0
