---
topic: claude-code-marketplace-json-for-plugin-discovery
author: thewoolleyman
created_at: 2026-05-06T18:48:13Z
---

## Proposal: claude-code-marketplace-json-for-plugin-discovery

### Target specification files

(Author to confirm against the livespec repo's own spec layout —
the change touches the **plugin distribution contract** and the
**repo top-level layout**, so whichever file documents either of
those should be the target. If livespec's spec is currently silent
on plugin distribution, the proposal also asks the spec to acquire
that surface.)

### Summary

The repo declares a Claude Code plugin via `.claude-plugin/plugin.json`
but does not publish a marketplace catalog (`.claude-plugin/marketplace.json`).
As a result, end users have **no supported install path**:

- `/plugin marketplace add thewoolleyman/livespec` fails — Claude Code's
  marketplace fetcher requires `.claude-plugin/marketplace.json` at the
  repo root and does not auto-promote a single `plugin.json` to a
  one-plugin marketplace.
- There is no `claude plugin install <github-url>` direct-from-git command.
- The `--plugin-dir` flag is not a documented public surface.

This proposal adds `.claude-plugin/marketplace.json` to the repo root so
users can install the plugin via the standard, documented Claude Code flow,
and (if the livespec spec covers distribution at all) lifts that flow into
the spec as the normative install contract.

### Motivation

The plugin is effectively undiscoverable today. The asymmetry between
"plugin manifest is published" and "no install path is published" is
operationally invisible — the maintainer's own machine works (local
clone + `--plugin-dir` style flows), but a fresh end user hits the
`marketplace.json: 404` wall and has no clear next step short of forking
the repo to add the file themselves.

Verified state at the time of this proposal:

```
$ curl -sI https://raw.githubusercontent.com/thewoolleyman/livespec/master/.claude-plugin/plugin.json     | head -1
HTTP/2 200
$ curl -sI https://raw.githubusercontent.com/thewoolleyman/livespec/master/.claude-plugin/marketplace.json | head -1
HTTP/2 404
```

### Proposed change

#### 1. Add `.claude-plugin/marketplace.json` to the repo root

The file lists the existing `plugin.json` as the (only) plugin in the
marketplace. Sketch (final shape per Claude Code's marketplace schema —
schema fields are authoritative, the values below are illustrative):

```jsonc
{
  "name": "livespec",
  "owner": {
    "name": "Chad Woolley",
    "url": "https://github.com/thewoolleyman"
  },
  "plugins": [
    {
      "name": "livespec",
      "source": ".",
      "description": "Spec-driven development workflow with proposal / critique / revise / doctor / prune-history lifecycle commands."
    }
  ]
}
```

After landing, the documented install path becomes:

```
/plugin marketplace add thewoolleyman/livespec
/plugin install livespec@thewoolleyman-livespec
```

#### 2. Document the install path in the spec

If the livespec spec currently does not name a plugin-distribution
contract, this proposal additionally asks for one short normative
section that pins:

- The marketplace name (`thewoolleyman-livespec`, derived from
  `<owner>-<repo>` per Claude Code's auto-naming).
- The plugin name as it appears post-install (`livespec`).
- The set of slash commands the plugin exposes (`/livespec:propose-change`,
  `/livespec:critique`, `/livespec:revise`, `/livespec:doctor`,
  `/livespec:prune-history`) — so consumers of the spec can rely on
  command-name stability.

Rationale for spec-side coverage: the install path and slash-command
names are an externally observable contract. End-user documentation
(README, downstream tutorials) will hard-code them; that's fine, but
they should also live in the spec so any future rename of the
marketplace or commands triggers a propose-change cycle rather than
silent breakage.

### Acceptance criteria

- `curl -sI https://raw.githubusercontent.com/thewoolleyman/livespec/master/.claude-plugin/marketplace.json`
  returns HTTP 200.
- A fresh Claude Code session can run
  `/plugin marketplace add thewoolleyman/livespec` without error and the
  marketplace appears in `/plugin marketplace list`.
- `/plugin install livespec@thewoolleyman-livespec` installs the plugin
  and it appears under `/plugin` → Installed.
- Each documented slash command (`/livespec:propose-change`,
  `/livespec:critique`, `/livespec:revise`, `/livespec:doctor`,
  `/livespec:prune-history`) is invocable after install and produces
  the behavior its skill description promises.
- The existing `.claude-plugin/plugin.json` is unchanged — no contract
  drift for any consumer that already references the manifest directly.

### Tradeoffs and risks

- **Marketplace name lock-in.** Once `thewoolleyman-livespec` ships
  and tutorials cite it, renaming requires a coordinated deprecation —
  Claude Code does not (yet) provide marketplace aliases. Mitigation:
  pick the name once, document it in the spec, and treat any future
  rename as a normal propose-change with a deprecation window.
- **Schema dependency on Claude Code.** `marketplace.json` is a
  third-party contract owned by Anthropic. A future Claude Code
  schema bump could require updates here. Mitigation: track Claude
  Code's marketplace docs; pin to a documented schema version
  if/when the schema becomes versioned.
- **Scope.** This proposal addresses the *upstream public* install
  path only. Private/internal distribution (forks with extra
  plugins, monorepo plugin layouts, pinned-commit installs) is
  out of scope and would be a separate proposal if it ever becomes
  load-bearing.
- **Doing nothing.** The cost of *not* landing this is real but
  diffuse: users either fork and add `marketplace.json` themselves,
  or give up. Both outcomes hide install friction from the
  maintainer (no error telemetry surfaces it) and slow adoption.

### Open questions for /critique

1. Is the marketplace-name choice (`thewoolleyman-livespec`, the
   automatic owner-repo dasherized form) the right default, or
   should the proposal request a custom marketplace name (e.g.
   plain `livespec`) via an explicit field?
2. Should the spec also cover *uninstall* and *update* paths, or
   is install-only sufficient for v1?
3. Should the `description` field in `marketplace.json` be the
   single source of truth, or should the spec require it to be
   generated from the plugin's own `plugin.json` `description`
   to avoid drift?
