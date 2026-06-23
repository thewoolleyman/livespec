# tests/claude/hooks/

Paired tests for the PreToolUse hook scripts in
`<repo-root>/.claude/hooks/`. Each test drives the script's real
stdin→stdout contract (JSON payload in; a `deny` decision or silence
out; always exit 0) end to end via a loaded module, asserting both
allow and deny paths to full line+branch coverage.
