---
name: needs-attention-internal
description: >-
  Compose the livespec-fleet-DEVELOPMENT signals a fleet maintainer must watch
  but an end user does NOT control — CI red on any fleet repo, fleet-conformance
  drift, stale cross-repo pins, and cross-repo consistency drift — into one
  point-in-time attention list. It DETECTS NOTHING NEW: it reads signals already
  computed elsewhere (GitHub Actions for CI, the dev-tooling conformance and
  pin-freshness checks, `/livespec:doctor` for drift) and normalizes them into
  the shared `attention_item` shape with `kind: "internal"`. This is the
  internal sibling of the shipped product `needs-attention`: the dividing test
  is *does an end user have actionable control?* — yes routes to the shipped
  `needs-attention` (plugin version, their repo's hygiene), no routes here
  (fleet CI/conformance/pins/drift). LOCAL-ONLY to livespec core, maintainer-only,
  UNSYNCED — it is not part of the livespec plugin, the spec, the copier
  template, or any fleet-propagated surface, and never ships to the plugin or to
  adopters. Emits nothing when the fleet is green.
---

# needs-attention-internal — the livespec-fleet-dev attention composer

You are `needs-attention-internal`: a **maintainer-only, local/unsynced**
awareness surface for the livespec fleet's own *development* health. When
invoked, you gather four already-computed dev-tooling-facing signals across the
fleet and compose them into one flat, point-in-time attention list. You detect
nothing new — every signal is a status another system already produces; your job
is to READ it cheaply, normalize it into the shared `attention_item` shape, and
render it for the maintainer.

This is the **internal** half of the `needs-attention` family. Its shipped
sibling — the product `needs-attention` (in both orchestrator plugins) — answers
"is there anything actionable about livespec in THIS repo?" for an end user. This
skill answers the complementary question a fleet maintainer owns: "is anything
wrong with the fleet's own development machinery right now?"

## The product-vs-internal dividing test (why these four are here)

The single test that sorts a signal into product-vs-internal is: **does an end
user have actionable control over it?**

- **Yes → product** (the shipped `needs-attention`): their plugin version is out
  of date (they can update), a stale worktree sits in their repo (they can
  reap). Those never appear here.
- **No → internal** (this skill): livespec CI is red, fleet-conformance has
  drifted, a cross-repo pin is stale, two repos have drifted out of consistency.
  An end user cannot act on any of these — only a fleet maintainer can — so they
  live here, local and unsynced, never shipped.

## The four internal signals and how to gather each

Read the fleet member list LIVE from
`/data/projects/livespec/.livespec-fleet-manifest.jsonc` (the `fleet` array of
`{repo, class}` entries) — do NOT hardcode the member list, so this skill stays
correct as the manifest changes. Parse the JSONC by stripping `//` line comments
(or use the vendored `jsoncomment`). Every checkout is `/data/projects/<repo>`
by the workspace convention. Keep every query LIGHTWEIGHT: prefer reading a
workflow's last run status over re-running the heavy check itself.

Secrets are probe-only (`printenv NAME | wc -c`, never echo a value).

### Signal 1 — CI red on a fleet repo

The `CI` workflow (named exactly `CI`) is the load-bearing safety net; a failed
latest run on `master` is a real broken state. For each fleet member, read the
latest master CI conclusion:

```bash
gh run list --repo thewoolleyman/<repo> --workflow CI --branch master --limit 1
```

A `completed  success` conclusion is healthy — emit nothing. A `failure`,
`cancelled`, `timed_out`, or `startup_failure` conclusion is an attention item.
Query with `--workflow CI` explicitly: a bare `gh run list` is masked by non-CI
workflows and reports a misleading green.

### Signal 2 — fleet-conformance drift

Fleet-conformance lives in the sibling `livespec-dev-tooling` repo
(`just check-fleet-conformance` → `livespec_dev_tooling.fleet.fleet_conformance`),
run on a schedule by the `Fleet conformance` workflow. Read its latest status
rather than re-running the heavy assert:

```bash
gh run list --repo thewoolleyman/livespec-dev-tooling --workflow "Fleet conformance" --branch master --limit 1
```

A failed conclusion means a fleet repo has drifted from its per-class
obligations — one internal attention item.

### Signal 3 — stale cross-repo pins

The `Pin freshness sweep` scheduled workflow (`pin-freshness.yml`, delegating to
dev-tooling's reusable pin-freshness) detects pins lagging the latest release. It
files bump PRs when it finds staleness. Read both its status AND any open bump
PRs it filed:

```bash
gh run list --repo thewoolleyman/livespec --workflow "Pin freshness sweep" --branch master --limit 1
# open bump PRs, read by the bump-PR BRANCH convention (precise), not free text:
gh pr list --repo thewoolleyman/livespec --state open \
  --json number,title,headRefName \
  --jq '.[] | select(.headRefName | startswith("chore/bump-"))'
```

A failed sweep is one item; each OPEN bump PR is one item (the pin is stale until
that PR merges). Read the open bump PRs by their **head-branch convention**
(`chore/bump-*`, the branch name the pin-freshness automation uses) — NOT a
free-text `--search "bump pin"`, which false-positives on any unrelated PR whose
title or body merely mentions those words (verified: it matched an unrelated
skills PR during this skill's own live-exercise). Repeat the query per fleet repo
whose pins you want covered, or scope it to the repos the sweep targets.

### Signal 4 — cross-repo consistency drift

`/livespec:doctor` is the per-repo consistency check. Running it across every
fleet repo inline is too heavy for a point-in-time scan, so surface it as a
**handoff** the maintainer runs, rather than executing it here. Prefer pointing
the maintainer at the per-repo doctor command (a `livespec-op` handoff), or, if
cheap, reading recent recorded findings. Do not run doctor across the whole fleet
inline.

## Shaping each signal into an `attention_item`

Normalize every fired signal into the shared shape (defined in
`livespec-runtime`'s `livespec_runtime/attention_item.py`), all with
`kind: "internal"`:

- **`id`** — a stable natural key of the form `internal:<signal>:<repo>`, e.g.
  `internal:ci-red:livespec-runtime`, `internal:conformance-drift:livespec-dev-tooling`,
  `internal:pin-stale:livespec`, `internal:drift:livespec-console-beads-fabro`.
  For an open bump PR, key on the PR to stay stable across runs, e.g.
  `internal:pin-stale:livespec#916`.
  - **Grammar note (verified).** `validate_attention_item_id` in
    `livespec-runtime` currently accepts only the two-part prefixes `impl` /
    `plan` and the three-part prefixes `valve` / `hygiene` / `spec`; it REJECTS
    an `internal:` prefix (returns `False`). This skill is PROSE with no runtime
    schema validation, so nothing here calls that validator — the
    `internal:<signal>:<repo>` shape is deliberately consistent with the
    accepted three-part `hygiene:<type>:<resource>` form (non-empty,
    non-numeric components) even though the validator's prefix allow-list has no
    `internal` entry yet. If strict validation is ever wanted for internal
    items, the right fix is to add `internal` to `_THREE_PART_PREFIXES` in
    `livespec-runtime` (and the `kind: "internal"` literal is already
    first-class there) — never to reshape the id away from its meaning.
- **`kind`** — always `"internal"`.
- **`urgency`** — `high` for CI red and conformance drift (the fleet is broken);
  `medium` for a stale pin or an open bump PR; `low`/`medium` for a doctor-drift
  handoff (a consistency check to run, not a known break).
- **`summary`** — one line naming the repo and what broke, e.g.
  "livespec-runtime CI is red on master (run 289…)".
- **`source_ref`** — `{repo: "<repo>", path: <workflow-or-file>|null,
  work_item: null}`. The repo carries the fleet-member name.
- **`handoff`** — `{kind, command}`:
  - `kind: "shell"` for a `gh` / `just` / `git` command (e.g. re-run CI, open the
    failed run, merge the bump PR).
  - `kind: "livespec-op"` for the `/livespec:doctor` drift handoff.
  - `command` is a ready-to-run string for the maintainer (e.g.
    `gh run view --repo thewoolleyman/<repo> <run-id>`,
    `gh pr merge --repo thewoolleyman/livespec <pr> --rebase`, or the per-repo
    doctor invocation).

## Fail-soft — name the offender, never crash the scan

If any signal query fails for one repo (network down, `gh` unauthenticated, a
workflow not present in that repo, a repo missing from the checkout tree), SKIP
that repo/signal and NAME it in the output — e.g. "skipped: `<repo>` (CI query
failed: <reason>)" — then continue the rest of the scan. A single unreachable
repo must never abort the whole composition. This mirrors the fleet's
"readers fail soft; name the offender" discipline.

## Rendering — Markdown for the maintainer

Render a Markdown list grouped by signal (CI / conformance / pins / drift) or by
urgency (high first). Under each group, one row per item: the summary, the
owning repo named explicitly, and the ready-to-run `handoff.command`. Put any
`skipped:` notes in their own short section so nothing strands silently.

**The healthy case emits nothing.** When every fleet CI run is green,
conformance passed, no pins are stale / no bump PRs are open, and there is no
drift to chase, say so in one line ("fleet-dev is green — nothing internal needs
attention") and stop. Emitting an empty list is the normal, expected outcome most
of the time.

## This skill is local-only

It lives at `.claude/skills/needs-attention-internal/SKILL.md` in *this* repo
(livespec core) and is **not** part of the livespec plugin, the spec, the copier
template, the fleet manifest's shipped surface, or any fleet-propagated artifact.
It is maintainer-only and UNSYNCED — the `overseer` precedent. Do NOT add it to
any plugin manifest, marketplace, conformance check, `.livespec-fleet-manifest.jsonc`,
copier template, or other repo. Its internal signals are livespec-fleet-development
facts an end user does not control, which is exactly why it never ships to the
plugin or to adopters.
