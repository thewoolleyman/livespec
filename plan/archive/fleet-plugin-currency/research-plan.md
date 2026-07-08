# Research plan — fleet plugin currency

Root-cause investigation + permanent fix for stale plugin builds across the
livespec fleet. Epic anchor: **`livespec-c1k9`** (core tenant). The resumable
entry point for the thread is `plan/fleet-plugin-currency/handoff.md`; this
file is the stable plan the handoff executes against.

## Problem statement

A session in `/data/projects/livespec-console-beads-fabro` (2026-07-03) invoked
`/next` and the skill routed to a STALE plugin cache snapshot
(`06e3e080ae19`) whose `_bootstrap.py` predates the credential self-heal
(`_self_heal_credentials()` + vendored `_vendor/livespec_runtime/credentials.py`).
A bare invocation therefore died with the raw `Access denied` failure the
self-heal exists to prevent — while the fixed `0.4.0` build was ALREADY
present in the cache. Feature shipped; routing stale.

This is one instance of a recurring class: fleet repos keep starting sessions
on outdated plugin builds even though newer releases exist. A structural
contributor was observed live in core the same day: the SessionStart updater
hook updates plugins but reports *"Restart to apply changes"* — i.e. every
session runs the build the PREVIOUS session fetched (a built-in one-session
lag), and a repo whose sessions are infrequent can stay stale indefinitely.

## The invariant this thread must establish

> Every NEW session, in EVERY fleet repo, on EVERY surface (interactive
> Claude Code, dispatched Fabro sandbox, `codex exec`), runs the LATEST
> RELEASED pin of EVERY livespec-ecosystem plugin, with a coherent cache.

Delivered as two independent layers, so a regression of the first can never
be silent:

1. **Currency mechanism** — updates land BEFORE the session exists (not
   during it), on every surface.
2. **Staleness gate** — a hard verification chokepoint (session start and/or
   dispatch pre-flight) that asserts running-build == latest-release for
   every livespec-ecosystem plugin and FAILS LOUDLY on mismatch. Best-effort
   updating without the gate is what already failed.

"Latest released pin" means the newest release-tag artifact per the fleet's
release-pin discipline (release-please cuts a release on every `feat:`/`fix:`
push; releases carry release-gate validation that per-commit `just check`
skips) — NOT raw master. Where current mechanisms track master instead, that
mismatch is itself a finding for Phase 3.

## Definitions

- **Snapshot** — one immutable copy of a plugin in the local plugin cache
  (e.g. `~/.claude/plugins/cache/.../<id>/`), identified by a content/commit
  id such as `06e3e080ae19`.
- **Active-snapshot pointer** — whatever on-disk registry entry makes a
  given scope (user, or project = one repo) resolve a plugin name to one
  specific snapshot. Phase 1 locates this empirically.
- **Surface** — a way a session comes into being: interactive `claude` in a
  repo; a Dispatcher-created Fabro sandbox session; a `codex exec`
  invocation (host-wide Codex config).
- **Livespec-ecosystem plugins** — `livespec@livespec` (core),
  `livespec@livespec-driver-claude`, the Codex driver
  (`livespec-driver-codex`), `livespec-orchestrator-beads-fabro`, and any
  per-repo impl/console plugin named by a governed repo's `.livespec.jsonc`.

## Candidate root causes (hypotheses — confirm or refute, mechanism-level)

- **H1 — one-session lag by design.** SessionStart updater fetches, but the
  new snapshot applies only at next restart; the current session stays stale.
- **H2 — stale activation despite fetch.** Newer snapshots exist in cache
  but the active-snapshot pointer (or the resolved slash-command's baked
  `${CLAUDE_PLUGIN_ROOT}` path) still targets an old snapshot — the console
  failure's proximate shape.
- **H3 — scope shadowing.** User-scope vs project-scope installs of the same
  plugin coexist and the stale one wins resolution.
- **H4 — master-vs-release mismatch.** Claude marketplaces installed from
  `{"source": "github", "repo": ...}` track the default branch, while fleet
  discipline pins to release tags; the two can disagree on what "latest"
  means, and neither is gated.
- **H5 — fleet non-uniformity.** Some repos lack the SessionStart updater
  hook and/or the committed `.claude/settings.json` enablement entirely, so
  nothing ever updates them.
- **H6 — unmanaged surfaces.** Fabro sandbox sessions and `codex exec`
  resolve plugins through their own paths (host-wide `~/.codex/config.toml`,
  sandbox-local caches) with no updater and no gate.
- **H7 — cache hygiene.** Multiple coexisting snapshots with no pruning and
  under-specified resolution order; stale snapshots remain resolvable
  indefinitely.

## Phases

### Phase 0 — evidence freeze

Forensic, read-only capture of the failing state BEFORE anything mutates it:
plugin cache trees + registries, the three named builds
(`06e3e080ae19`, `accbbd1415e1`, `0.4.0`) and what still references the stale
one, console-repo and core-repo `.claude/` config + hooks, Codex config,
marketplace caches, and remote truth (latest release tag + master SHA per
plugin repo). Raw capture lands in `tmp/fleet-plugin-currency/evidence/`
(untracked scratch); curated findings get committed under
`plan/fleet-plugin-currency/research/`.
**Exit:** SUMMARY.md fact table exists; the stale reference's provenance is
recorded.

### Phase 1 — empirical resolution semantics

Establish exactly how plugin install/update/cache/activation works per
runtime — from the Phase 0 evidence, controlled experiments in a scratch
project (never against live fleet caches), and Claude Code / Codex
documentation. Must answer: where the active-snapshot pointer lives and when
it flips; what `claude plugin update` changes at which scope; how a
skill's `${CLAUDE_PLUGIN_ROOT}` is resolved at session start; what
marketplace refresh actually fetches (branch? tag?); the Codex analogues;
what Fabro sandbox provisioning installs.
**Exit:** each of H1–H7 is CONFIRMED or REFUTED with a mechanism, written to
`research/semantics.md`.

### Phase 2 — fleet audit

The full matrix: every fleet repo × every livespec-ecosystem plugin × every
surface — enablement source, updater presence, active snapshot, newest cached
snapshot, latest release. Verify per-repo state directly in each repo (fleet
is non-uniform; treat assumptions as hypotheses).
**Exit:** `research/fleet-audit.md` matrix, staleness highlighted.

### Phase 3 — root-cause synthesis

Compose Phases 0–2 into (a) the complete causal chain for the console
failure and (b) the enumerated set of independent defects that permit the
staleness class. Each defect becomes a child work-item under `livespec-c1k9`
(same-tenant children in core; cross-tenant items filed in their owning
repos and prose-linked, per the fleet pattern).
**Exit:** `research/root-causes.md`; ledger children filed and groomed.

### Phase 4 — design the guarantee

Design the two layers (currency mechanism + staleness gate) against the
constraints below. Candidates to evaluate — not pre-decided: host-level
pre-session update (systemd timer / shell-entry hook), Dispatcher pre-flight
gate in the orchestrator, a runtime chokepoint in core's `_bootstrap.py`
(sibling of the credential self-heal: assert own build == latest release,
self-heal or fail with an actionable diagnostic), marketplace/source changes
to track release tags, cache pruning, and removal of the restart-lag window.
Contract-level commitments go through `/livespec:propose-change` into
`SPECIFICATION/` (spec is for contracts; tracking stays in the ledger).
**Exit:** `research/design.md`; maintainer design review PASSED (this is the
one deliberate maintainer gate); spec proposals filed where contractual.

### Phase 5 — implement + verify fleet-wide

Implement per-repo under the epic. Ready, factory-safe implementation is
factory-dispatched (`/livespec-orchestrator-beads-fabro:orchestrate`), never
hand-coded inline; host-only self-machinery stays maintainer-side.
**Exit (the epic's exit gate):** a mechanized fresh-session assertion run in
EVERY fleet repo × surface proves running-build == latest-release for every
livespec-ecosystem plugin, AND the staleness gate demonstrably fails loudly
when fed a deliberately-staled cache (negative test). Both recorded in the
handoff; epic closed only on both.

## Design constraints (bind Phase 4)

- **Fix the gate, not the bypass.** No skip flags, no "install-but-neuter";
  if two systems conflict (e.g. restart-lag vs the invariant), fix the
  mis-designed one.
- **Automatic at source.** Plugin staleness is a *normal, recurring* failure
  mode — it MUST be handled automatically (derive/refresh/verify), never by
  procedure, memory, or per-repo manual steps.
- **Enforce, don't hope.** The gate fails loudly; a stale session refuses to
  proceed rather than silently misbehaving.
- **Release-tag discipline.** Currency targets the latest RELEASE, not raw
  master, consistent with the fleet's `bump-pin` / release-please model.
- **Every surface or it doesn't count.** Interactive Claude, Fabro sandbox,
  `codex exec` — a mechanism that covers only one surface fails the
  invariant.
- **Prefer primitives.** Existing hooks, wrappers, `_bootstrap.py`
  chokepoints, and naming conventions before new schemas/skills; if the
  design sprouts more than ~2 new artifacts, re-check whether a convention
  suffices.
- **Carve-outs are severity levers.** If some check genuinely cannot behave
  identically everywhere, it stays wired and invoked with one
  self-documenting env lever — never silently skipped.

## Work-item mapping

- Epic anchor: **`livespec-c1k9`** (core tenant, P0). Status is read from the
  ledger, never from this file.
- Children: filed per Phase 3 defect / Phase 5 repo-slice as they ripen;
  cross-tenant items live in their owning repos with cross-repo links.

## Overseer protocol

- The driving session COORDINATES: dispatches sub-agents for heavy
  investigation/authoring, factory-dispatches ready implementation, and
  synthesizes. It does not hand-code.
- **Rotate before ~50% context.** Refresh `handoff.md` (state, in-flight
  agents, next action), then end the recap with the resume command verbatim
  as the last line.
- Resume command: `/livespec-orchestrator-beads-fabro:plan fleet-plugin-currency`
- Investigation phases are READ-ONLY toward every plugin cache, registry,
  and settings file: do not "helpfully" update, reinstall, or prune anything
  before Phase 3 closes — that destroys evidence and masks root causes. The
  one exception is a controlled experiment in a scratch project.
