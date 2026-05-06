# scripts/

The plugin's shared Python surface. `bin/` carries the shebang
wrappers invoked by Claude Code; `livespec/` is the package the
wrappers import; `_vendor/` carries vendored pure-Python libraries
(read-only — no local edits).

Per-subdirectory rules live alongside each subdirectory. Global
rules live in `SPECIFICATION/constraints.md`. Do not
duplicate global rules here.
