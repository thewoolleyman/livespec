---
name: feedback-livespec-commit-prefixes
description: Conventional Commits prefix rules vary across livespec sibling repos. livespec and livespec-impl-plaintext enforce stricter classification via red-green-replay.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 48850880-6a8c-4e3b-a8e3-798911468efd
---

The 4 livespec sibling repos enforce DIFFERENT commit-message
classification rules:

- **livespec + livespec-impl-plaintext** run a `red-green-replay`
  check in the commit-msg hook that REJECTS `feat:` / `fix:`
  commits whose staged paths are ONLY config/CI/docs (no product
  code under the impl-prefix paths or tests under `tests/`). On
  rejection, the check directs the user to one of the exempt
  prefixes: `chore`, `docs`, `build`, `ci`, `style`, `test`,
  `refactor`, `perf`, `revert`.

- **livespec-dev-tooling + livespec-runtime** do NOT enforce the
  same check. `feat:` is accepted there even for pure-config or
  CI-only commits (e.g., livespec-dev-tooling PR #6 landed
  `feat(cross-repo):` for what was mostly YAML + Python additions
  to support a new surface).

**Why:** The red-green-replay check enforces that `feat:`/`fix:`
commits actually exercise the impl-or-tests product surface, which
is the right invariant for the parent libraries (livespec is the
spec-driver, livespec-impl-plaintext is the canonical impl plugin).
The other two repos haven't picked up the check yet, but may in the
future.

**How to apply:** For any CI/workflow/config-only change targeting
livespec or livespec-impl-plaintext, use `ci(scope):` (for
workflows), `docs(scope):` (for documentation), `chore(scope):`
(for build/tool config), or `build(scope):` (for dependency/
toolchain changes). NEVER `feat:` unless the change actually
touches product code under that repo's impl-prefix layout (e.g.,
`livespec/.claude-plugin/scripts/livespec/` or
`livespec-impl-plaintext/.claude-plugin/scripts/`).

For dev-tooling and runtime, `feat:` is fine even for non-product
changes — but using a more specific exempt prefix is still good
hygiene if the change really is just CI/docs.

If the commit-msg hook fires and rejects, the commit did NOT
happen — fix the prefix and re-run `git commit` (a fresh commit,
NOT `--amend`).

Related: [[feedback-revise-payload-format]],
[[feedback-heading-coverage-pairing]]
