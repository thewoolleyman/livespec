---
name: needs-attention-fleet
description: >-
  Aggregate the whole livespec fleet's attention into ONE flat merged list. It
  fans out over `.livespec-fleet-manifest.jsonc` (fleet members + adopters),
  invokes each repo's shipped product `needs-attention --json`, folds in the
  local `needs-attention-internal` fleet-dev signals, and concatenates every
  item into a single flat `attention[]` reusing the SAME `attention_item` schema
  — each item attributable to its repo via `source_ref.repo`. It is a PURE
  AGGREGATOR: NO cross-repo re-ranking (the same restraint impl-`next` has); it
  preserves each repo's own item order and never reorders across repos. Grouping
  (by repo or urgency) is a renderer concern only — the Markdown human view
  groups; the JSON stays flat. Adopters contribute product `needs-attention`
  ONLY; `-internal` is livespec-fleet-dev-specific. Fail-soft: a repo without a
  reachable surface is skipped and named, never crashing the fan-out. LOCAL-ONLY
  to livespec core, maintainer-only, UNSYNCED — not part of the plugin, the
  spec, the copier template, or any fleet-propagated surface.
---

# needs-attention-fleet — the pure cross-fleet attention aggregator

You are `needs-attention-fleet`: a **maintainer-only, local/unsynced** surface
that answers "across the ENTIRE livespec fleet, what needs attention right now?"
You are a **strict superset** of the per-repo product `needs-attention` and the
local `needs-attention-internal`: you consume both and merge their outputs into
one flat list. The two inputs are orthogonal — product `needs-attention` is a
per-repo *content category* (what is actionable in a repo), `-internal` is a
fleet-dev *scope* (what is wrong with the fleet's own machinery) — so they
compose without collision.

You are a **pure aggregator**. You run no ranker, apply no cross-repo priority,
and re-detect nothing. You call each source, tag every item with its repo, and
concatenate. This is the deliberate restraint impl-`next` already embodies:
ranking within a repo is that repo's job; ranking ACROSS repos is a renderer's
optional grouping, not a computed order.

## Step 1 — read the fleet manifest LIVE

Read `/data/projects/livespec/.livespec-fleet-manifest.jsonc` at run time and
iterate its two arrays; do NOT hardcode the member list, so this skill stays
correct as the manifest changes. Parse the JSONC by stripping `//` line comments
(or use the vendored `jsoncomment`):

- **`fleet`** — `{repo, class}` entries (core / enforcement-suite / impl-plugin /
  driver-plugin / library / console). These contribute product `needs-attention`
  AND (for the internal fold in Step 3) their fleet-dev signals.
- **`adopters`** — `{repo, profile, posture}` entries (governed repos that
  adopted the workflow but are not fleet — e.g. `openbrain`, `resume`). Adopters
  contribute **product `needs-attention` only**.

Every checkout is `/data/projects/<repo>` by the workspace convention (there is
no `path` field). Secrets are probe-only (`printenv NAME | wc -c`, never echo a
value).

## Step 2 — invoke each repo's product `needs-attention --json`

For every fleet member AND every adopter, invoke that repo's shipped product
`needs-attention` in JSON mode and collect its `attention[]`.

**Resolve the surface per repo.** A repo's product `needs-attention` is supplied
by whichever orchestrator plugin it uses, named in its
`/data/projects/<repo>/.livespec.jsonc` under `implementation.plugin` (one of
`livespec-orchestrator-beads-fabro` or `livespec-orchestrator-git-jsonl`). Both
orchestrators have source checkouts at `/data/projects/<orchestrator>`, so
resolve the wrapper there and point it at the target repo:

```bash
# beads-fabro–backed repo (needs the credential wrapper for the ledger read):
source /data/projects/1password-env-wrapper/with-livespec-env.sh \
  python3 /data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/bin/needs_attention.py \
  --json --project-root /data/projects/<repo> --repo-name <repo>

# git-jsonl–backed repo (git-backed store, no credential wrapper needed):
python3 /data/projects/livespec-orchestrator-git-jsonl/.claude-plugin/scripts/bin/needs_attention.py \
  --json --project-root /data/projects/<repo> --repo-name <repo>
```

The `--json` envelope is `{"attention": [ ...attention_item... ]}`. Collect its
`attention[]` and **confirm each item's `source_ref.repo` is the member repo** —
the wrapper already sets it from `--repo-name`, so it should already read
`<repo>`; the flat merged list stays attributable through that field alone.

Only a repo with an orchestrator plugin resolvable AND a reachable ledger has
this surface. See the fail-soft rule below for the rest.

## Step 3 — fold in `needs-attention-internal`

Invoke the sibling `needs-attention-internal` skill and append its
`kind: "internal"` items to the merged list. These are the fleet-dev signals (CI
red, fleet-conformance drift, stale pins, cross-repo drift) that no per-repo
product surface covers.

**Adopters are excluded from the internal fold** — `-internal` is
livespec-fleet-dev-specific, so it composes signals only for `fleet` members, not
adopters. Adopters contribute their product `needs-attention` (Step 2) and
nothing else.

## Step 4 — merge into ONE flat `attention[]` (no re-ranking)

Concatenate every collected list — each repo's product items in that repo's own
order, then the internal items — into a single flat `attention[]`. **Do NOT
re-rank across repos**: preserve each repo's own order; the flat list is a plain
concatenation, and every item stays repo-attributable through `source_ref.repo`.
The schema is identical to the per-repo shape — `needs-attention-fleet` reuses
`attention_item` verbatim, adding only breadth, never a new field.

## Step 5 — render

- **JSON (machine).** Emit the flat `{"attention": [ ... ]}` array, order
  preserved, un-grouped. This is the canonical output; the console port and any
  other machine consumer bind to it.
- **Markdown (human).** Group the SAME flat list for reading — by repo (a section
  per member/adopter) and/or by urgency (high first within each). Grouping is a
  **renderer concern only**: it reorders nothing in the underlying flat list, it
  just presents it. Under each group, one row per item: the summary, the owning
  repo named explicitly, and the ready-to-run `handoff.command`.

State explicitly, when rendering Markdown, that the grouping is presentation and
the JSON remains the flat source of truth.

## Fail-soft — skip and name, never crash the fan-out

For any repo whose surface cannot be reached — no `.livespec.jsonc` /
no `implementation.plugin`, the orchestrator wrapper missing, the ledger
unreachable (e.g. an adopter whose Dolt tenant registration is still deferred, or
any non-zero wrapper exit / `BeadsCommandError`) — **SKIP it and NAME it** in the
output, e.g. "skipped: `openbrain` (needs-attention surface unreachable: ledger
access denied)". Never let one unreachable member abort the whole fan-out. This
mirrors the design's graceful-degrade ethos and the fleet's "readers fail soft;
name the offender" discipline. Collect the skip list into its own short section
under the merged output so nothing strands silently.

**The healthy case** is a short flat list (or empty) plus, ideally, an empty skip
list. When every reachable repo is quiet and no internal signal fired, say so in
one line and stop.

## This skill is local-only

It lives at `.claude/skills/needs-attention-fleet/SKILL.md` in *this* repo
(livespec core) and is **not** part of the livespec plugin, the spec, the copier
template, the fleet manifest's shipped surface, or any fleet-propagated artifact.
It is maintainer-only and UNSYNCED — the `overseer` precedent. Do NOT add it to
any plugin manifest, marketplace, conformance check, `.livespec-fleet-manifest.jsonc`,
copier template, or other repo. It is a cross-fleet maintainer console over
per-repo surfaces that DO ship; the aggregator itself never ships to the plugin
or to adopters.
