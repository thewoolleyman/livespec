# Installing livespec on a project

This guide takes a project from zero to governed-by-livespec: the
plugins it must enable, the configuration it must declare, the
orchestrator backend it must choose, and — for the parallel
Beads/Dolt + Fabro backend — the host-level runtime that must be in
place before work-items can flow.

It is written for **any** project that wants livespec governance, not
just the livespec family repos. Where the livespec family uses a
specific convention (a shared Dolt server, a 1Password secret
wrapper), that is called out as *the family's reference setup* — your
project supplies the equivalent.

Authoritative contract surface: `SPECIFICATION/contracts.md`
§"Plugin distribution" and `SPECIFICATION/non-functional-requirements.md`.
This document is the procedural narrative that stitches those rules
into one ordered path; the spec wins on any conflict.

---

## 1. The three pieces you install

livespec governance is always **three plugins**, selected
independently:

| Piece | What it is | For Claude Code |
|---|---|---|
| **Core** | The contract: harness-neutral driving prose, the reference spec-side CLIs, the schemas, the built-in templates. Exposes no slash commands itself. | `livespec@livespec` |
| **Driver** | The thin per-agent-runtime binding that exposes the interactive `/livespec:*` surface and resolves core at runtime. | `livespec@livespec-driver-claude` |
| **Orchestrator** | The pluggable producer whose work product is the implementation — it owns the work-item ledger, the loop, and the dispatcher. Named by your `.livespec.jsonc`. | one of the `livespec-impl-*` plugins (see §2) |

There are **zero direct dependencies** between the Driver and the
orchestrator. The Driver binds core's CLIs and prose only; everything
orchestrator-interactive ships with the orchestrator. You can swap
either independently.

---

## 2. Choosing an orchestrator backend

Two reference orchestrators ship today. Pick by your concurrency
needs.

### git-jsonl — serial, zero infrastructure

- Plugin: **`livespec-impl-git-jsonl`**.
- Work-items and memos live in committed JSONL files
  (`work-items.jsonl`, `memos.jsonl`) in the repo.
- No external services. Serial by construction — one writer at a time.
- **Choose this** for a single-maintainer project, low work-item
  volume, or when you do not want to stand up any backing service.

### Beads/Dolt + Fabro — parallel, concurrency-safe

- Plugin: **`livespec-impl-beads`**.
- Work-items live in a [beads](https://github.com/steveyegge/beads)
  ledger backed by a **Dolt SQL server** (not git). The Fabro loop
  dispatches each ready work-item into its own sandbox; a Dispatcher
  gates, merges, and closes unattended.
- Requires host-level runtime (§4): a `bd` CLI, a reachable Dolt
  server, a per-tenant secret, and `.beads/` pointer files.
- **Choose this** when multiple agents (or an unattended dispatch
  loop) must write the ledger concurrently.

> **git-backed beads is *not* this backend.** Beads can also be run
> against a plain git-committed store; that mode serialises every
> write through git and suffers write contention under concurrency.
> The Beads/Dolt backend exists specifically to remove that
> contention by putting the ledger on a real SQL server. If you tried
> beads before and hit concurrency pain, it was almost certainly the
> git-backed mode — Dolt-server mode is the fix, not a repeat of it.

You can start on git-jsonl and migrate to Beads/Dolt later; the
spec-side surface (`/livespec:*`) is identical across backends.

---

## 3. Enable the plugins — `.claude/settings.json`

Commit a `.claude/settings.json` **at project scope** so the skills
(and the Driver's bundled hooks) load only in this project, never
machine-wide. Clones, CI, and sandboxes then all resolve the same
remote marketplaces.

Substitute the orchestrator plugin you chose in §2 for the
`livespec-impl-*` entries in **both** blocks.

```jsonc
{
  "extraKnownMarketplaces": {
    "livespec":               { "source": { "source": "github", "repo": "thewoolleyman/livespec" } },
    "livespec-driver-claude": { "source": { "source": "github", "repo": "thewoolleyman/livespec-driver-claude" } },
    "livespec-impl-beads":    { "source": { "source": "github", "repo": "thewoolleyman/livespec-impl-beads" } }
  },
  "enabledPlugins": {
    "livespec@livespec": true,
    "livespec@livespec-driver-claude": true,
    "livespec-impl-beads@livespec-impl-beads": true
  }
}
```

For the serial backend, replace the `livespec-impl-beads` keys with
`livespec-impl-git-jsonl` (repo `thewoolleyman/livespec-impl-git-jsonl`).

After committing, restart Claude Code or run `/reload-plugins`. The
eight `/livespec:*` commands become available with the `livespec:`
namespace prefix.

A machine-wide `/plugin install livespec@livespec` (+ the Driver and
orchestrator) also works, but it enables the plugins in **every**
project on the host. The committed project-scoped form above is the
contract default.

---

## 4. Declare configuration — `.livespec.jsonc`

`.livespec.jsonc` at the project root names the template, the spec
location, and the orchestrator. Its schema root is
`additionalProperties: true`: each plugin owns a top-level section
named for itself, validates its own section on read, and tolerates
unknown sections.

**Secrets MUST NOT live in `.livespec.jsonc`.** Anything needing a
credential reads it from a separate channel (environment variable, OS
keyring, secret manager).

### git-jsonl

```jsonc
{
  "template": "livespec",
  "spec_root": "SPECIFICATION",
  "implementation": { "plugin": "livespec-impl-git-jsonl" },
  "livespec-impl-git-jsonl": {
    "format": "jsonl",
    "compat": { "livespec_core": ">=0.1.0,<1.0.0", "pinned": "master" },
    "work_items_path": "work-items.jsonl",
    "memos_path": "memos.jsonl"
  }
}
```

### Beads/Dolt + Fabro

The `connection` block carries the per-repo Dolt tenant identity. The
load-bearing identity rule is `prefix == tenant == database ==
server_user` (all equal to the repo name). The tenant **password is
deliberately absent** — it is supplied only via an environment
variable at `bd`-call time (§4.1). TCP-only, so there is **no**
`socket` key.

```jsonc
{
  "template": "livespec",
  "spec_root": "SPECIFICATION",
  "implementation": { "plugin": "livespec-impl-beads" },
  "livespec-impl-beads": {
    "format": "beads",
    "compat": { "livespec": ">=0.1.0,<1.0.0", "pinned": "master" },
    "connection": {
      "tenant": "myproject",
      "prefix": "myproject",
      "database": "myproject",
      "server_user": "myproject",
      "server_host": "127.0.0.1",
      "server_port": 3307,
      "fake": false
    }
  }
}
```

---

## 5. (Beads/Dolt + Fabro only) provision the host runtime

`just bootstrap` / plugin enablement installs the *plugin* but cannot
provision host-level runtime. The Beads/Dolt backend connects only
when **all four** of the following are present. (Skip this entire
section for the git-jsonl backend.)

1. **`bd` CLI, pinned v1.0.5**, at a known path (the family uses
   `/usr/local/bin/bd`), with `LIVESPEC_BD_PATH` pointing at it — the
   beads wrappers shell out to `$LIVESPEC_BD_PATH`.

2. **A running Dolt `sql-server`** reachable over **TCP**
   (the family forces `127.0.0.1:3307`; the unix socket is
   deliberately unreachable by sandboxed callers, which is why
   `.livespec.jsonc` and `.beads/config.yaml` carry `dolt.*` host/port
   keys with **no** `socket` key).

3. **The per-tenant password in the environment** as
   `BEADS_DOLT_PASSWORD_<tenant_with_underscores>` (tenant == repo
   name; hyphens become underscores). The beads wrappers map this to
   the bare `BEADS_DOLT_PASSWORD` they consume. The family injects it
   via a 1Password Environment wrapper (`with-livespec-env.sh`); your
   project supplies the equivalent. Secrets are **probe-only** —
   verify with `printenv NAME | wc -c`, never echo the value — and
   are never committed to `.livespec.jsonc` or `.beads/`.

4. **The `.beads/` pointer files** in the repo:
   - `config.yaml` — **committed**; carries the `dolt.*` server
     host/port keys (no `socket` key).
   - `metadata.json` — **gitignored** but **regenerable**:
     `project_id` is server-stable, so re-running `bd init --server …`
     in a `/tmp` scratch dir with the repo's `config.yaml` yields the
     identical `project_id`; copy the resulting `metadata.json` into
     the repo.

### Generating `.beads/` safely

**Never run `bd init` inside a primary checkout or worktree** — it
auto-commits and clobbers `.beads/`. Run it in a `/tmp` scratch dir
that holds a copy of the repo's `config.yaml`, then copy the
generated `metadata.json` back.

Always pass **`bd init --skip-agents --skip-hooks`**. Without those
flags `bd init` auto-commits to the default branch and injects
opinionated `CLAUDE.md` / `AGENTS.md` / `settings.json` content.

Without the Dolt server + `bd` binary + tenant secret + `.beads/`
pointers, `bd list` fails with "no beads database found" even though
the plugin is installed. This is the bridge between *plugin installed*
and *backend actually connects*.

---

## 6. Author or migrate the spec

- **New project (empty spec):** run `/livespec:seed` to author the
  initial natural-language specification into the template's
  `spec_root` layout (`spec.md`, `contracts.md`, `constraints.md`,
  `scenarios.md`, `history/`).
- **Existing spec:** if `SPECIFICATION/` already exists (for example,
  a project already governed on another backend), do **not** re-seed
  — the spec carries across backends unchanged. Migrating the
  *work-item ledger* between backends is a separate operation owned by
  the orchestrators.

Then validate: `/livespec:doctor` runs the static phase plus the
LLM-driven objective and subjective phases against the spec tree.

---

## 7. (Optional) run the Dispatcher for unattended work

The Beads/Dolt + Fabro orchestrator ships a **Dispatcher**
(`dispatcher.py`) that carries routine cross-repo work unattended: it
polls the ledger, dispatches each ready work-item into its own Fabro
sandbox, runs `just check` plus `/livespec:doctor` as a hard janitor
gate, verifies the merge, and closes the item. Its invocation surface
(`mode`, `budget`), janitor hard-gate, and structured iteration
journal are codified in the orchestrator repo's own specification.

The git-jsonl orchestrator carries the serial equivalent. Neither is
required: spec-side `/livespec:*` lifecycle work runs the same with or
without a loop driver.

---

## 8. Verify the install

| Check | git-jsonl | Beads/Dolt + Fabro |
|---|---|---|
| Plugins loaded | `/livespec:help` lists the eight commands | same |
| Spec readable | `/livespec:doctor` runs clean | same |
| Ledger connects | `work-items.jsonl` present and readable | `bd list` returns (under the env wrapper) without "no beads database found" |
| Next action ranks | `/livespec:next` and the orchestrator's `:next` | same |

---

## Quick reference — the ordered path

1. Choose the orchestrator backend (§2).
2. Commit `.claude/settings.json` enabling core + Driver + orchestrator (§3).
3. Commit `.livespec.jsonc` declaring template, spec_root, and the orchestrator section (§4).
4. **Beads/Dolt only:** provision `bd` CLI + Dolt server + tenant secret + `.beads/` pointers (§5).
5. Reload plugins, then `/livespec:seed` (new) or carry the existing spec (§6).
6. Validate with `/livespec:doctor`; optionally wire the Dispatcher (§7).
7. Verify (§8).
