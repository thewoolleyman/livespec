---
name: needs-attention-internal
description: >-
  Compose the livespec-fleet-DEVELOPMENT signals a fleet maintainer must watch
  but an end user does NOT control — CI red on any fleet repo, fleet-conformance
  drift, stale cross-repo pins, cross-repo consistency drift, ledger
  status-conformance drift, and a weakened fork-approval tier on a repo that
  routes gating CI to self-hosted capacity — into one point-in-time attention
  list. It mostly
  reads signals already computed elsewhere (GitHub Actions for CI, the dev-tooling
  conformance and pin-freshness checks, `/livespec:doctor` for drift); the two
  exceptions are the ledger status-conformance scan, which runs a cheap per-tenant
  `ledger-normalize --dry-run` directly because no scheduled workflow computes it,
  and the fork-approval tier, which is a live repo setting no workflow can read
  from CI.
  All are normalized into the shared `attention_item` shape with `kind: "internal"`.
  This is the
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
invoked, you gather six dev-tooling-facing signals across the fleet and compose
them into one flat, point-in-time attention list. Four are statuses another
system already produces (you READ them cheaply); the remaining two — ledger
status-conformance drift and the fork-approval tier — you determine yourself
with a cheap per-tenant or per-repo query, because nothing else computes them
(the ledger scan runs only inside a dispatch, and no CI workflow can read a
repo's fork-approval setting at all). Your job is to gather each
cheaply, normalize it into the shared `attention_item` shape, and render it for
the maintainer.

This is the **internal** half of the `needs-attention` family. Its shipped
sibling — the product `needs-attention` (in both orchestrator plugins) — answers
"is there anything actionable about livespec in THIS repo?" for an end user. This
skill answers the complementary question a fleet maintainer owns: "is anything
wrong with the fleet's own development machinery right now?"

## The product-vs-internal dividing test (why these six are here)

The single test that sorts a signal into product-vs-internal is: **does an end
user have actionable control over it?**

- **Yes → product** (the shipped `needs-attention`): their plugin version is out
  of date (they can update), a stale worktree sits in their repo (they can
  reap). Those never appear here.
- **No → internal** (this skill): livespec CI is red, fleet-conformance has
  drifted, a cross-repo pin is stale, two repos have drifted out of consistency,
  a tenant's ledger holds a work-item at a non-lifecycle status, a repo routing
  gating CI to self-hosted capacity has had its fork-approval tier weakened. An
  end user cannot act on any of these — only a fleet maintainer can — so they
  live here, local and unsynced, never shipped.

## The six internal signals and how to gather each

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
  --jq '.[] | select(.headRefName | test("^chore/(freshness-)?bump-"))'
```

A failed sweep is one item; each OPEN bump PR is one item (the pin is stale until
that PR merges). Read the open bump PRs by their **head-branch convention** — NOT
a free-text `--search "bump pin"`, which false-positives on any unrelated PR whose
title or body merely mentions those words (verified: it matched an unrelated
skills PR during this skill's own live-exercise). Repeat the query per fleet repo
whose pins you want covered, or scope it to the repos the sweep targets.

> **THERE ARE TWO BUMP-BRANCH CONVENTIONS, AND MATCHING ONLY THE OBVIOUS ONE
> MISSES HALF THE PRs.** This filter read `startswith("chore/bump-")` until
> 2026-08-11, when a fleet stale-PR sweep found four lingering bump PRs and this
> query would have surfaced exactly two of them:
>
> ```
> chore/bump-livespec-runtime-v0.18.0             MATCHED
> chore/freshness-bump-livespec-runtime-v0.18.0   MISSED
> chore/bump-livespec-v0.30.2                     MATCHED
> chore/freshness-bump-livespec-v0.10.1           MISSED
> ```
>
> Both `chore/bump-<pkg>-<ver>` and `chore/freshness-bump-<pkg>-<ver>` are minted
> for the SAME bump, roughly twelve minutes apart, so a half-blind filter reports
> a repo as having one stale pin when it has two branches outstanding. The `test`
> form above matches both. **Note the trap's shape: the previous wording was a
> CORRECTION — it had just replaced a false-positive-prone free-text search with a
> "precise" prefix — and precision on the wrong axis reintroduced the miss in the
> other direction.** Narrowing a query is not the same as making it right; check
> the narrowed form against real values before trusting it. This is the same
> failure as hardcoding `ci.yml` when one fleet repo's gating workflow is
> `check.yml` (see `.ai/verifying-against-the-right-source.md` instance 22).
>
> **A lingering bump PR is also `livespec-dev-tooling-xdyh`'s arming condition** —
> while its branch sits on origin, the next sweep cannot fast-forward over it — so
> an item here is worth more than "a pin is stale": it marks a window in which the
> stale-pin safety net can silently disable itself.

> **KNOWN COVERAGE GAPS — this skill does NOT currently see these, and the
> omission is recorded rather than implied away.** All three were found on
> 2026-08-11 by ad-hoc sweeps, not by this skill:
>
> - **A failing RELEASE gate.** Signal 1 reads only the workflow named `CI`.
>   livespec's release gate is `release-tag.yml`, which fires on TAG PUSH; it
>   failed on four consecutive published releases (v0.29.0 → v0.30.0) while every
>   `CI` run stayed green. Nothing here would have said so.
> - **A blocked `release-please` PR.** Signal 3 matches only bump branches, so a
>   release PR stuck on a red check is invisible. One sat open **18.6 days** in
>   `livespec-console-beads-fabro` with auto-merge armed and unable to fire.
> - **An adopter's gating workflow under a different name.** The fleet is
>   non-uniform: `resume`'s gating workflow is `check.yml`, not `ci.yml`.
>
> Adding signals for these is a design decision, not a bug fix, and belongs with
> `livespec-39h1` (whose thesis is precisely that nothing reads these). Until then,
> **a clean run of this skill means "the six signals are green", not "the fleet is
> healthy"** — say the former when reporting.

### Signal 4 — cross-repo consistency drift

`/livespec:doctor` is the per-repo consistency check. Running it across every
fleet repo inline is too heavy for a point-in-time scan, so surface it as a
**handoff** the maintainer runs, rather than executing it here. Prefer pointing
the maintainer at the per-repo doctor command (a `livespec-op` handoff), or, if
cheap, reading recent recorded findings. Do not run doctor across the whole fleet
inline.

### Signal 5 — ledger status-conformance drift

Every fleet tenant's work-item ledger must hold each LIVE item at one of the seven
livespec lifecycle statuses (`acceptance, active, backlog, blocked, closed,
pending-approval, ready`). Beads' built-in `open` (a raw `bd create` default) or
`in_progress` (a raw `bd --claim`), or any ad-hoc status, parks work in an unknown
lane. Unlike Signals 1-4, NOTHING computes this outside a dispatch — the
dispatcher's `ledger-check` runs the `status-conformance` invariant only at
dispatch time — so this signal runs the check DIRECTLY (it is cheap: a `bd list` +
status filter per tenant, comparable to Signal 1's per-repo `gh run list`).

For each fleet member, run the standalone normalizer in DRY-RUN (it detects without
mutating):

```bash
python3 /data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/bin/dispatcher.py \
  ledger-normalize --project-root /data/projects/<repo> --dry-run --json
```

The JSON is `{"dry_run": true, "remapped": [{item_id, from, to, reason}, …],
"residual": [{check, item_id, message}, …]}`:

- **`remapped`** — items at an auto-healable built-in (`open`→`backlog`,
  `in_progress`→`active`). One-command-fixable → **medium** urgency.
- **`residual`** — items at a non-lifecycle status the normalizer will NOT
  auto-touch (`deferred`/`hooked`/`pinned`/any ad-hoc). Needs a maintainer's lane
  decision → **high** urgency.

Empty `remapped` AND empty `residual` for a tenant = healthy (emit nothing). Any
non-empty yields one attention item for that tenant. The `handoff.command` for a
remappable drift is the SAME command WITHOUT `--dry-run` — it self-heals the
auto-mappable items and re-reports any residual:

```bash
python3 /data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/bin/dispatcher.py \
  ledger-normalize --project-root /data/projects/<repo>
```

For a residual (non-auto-mappable) drift, the handoff is the `bd update <id>
--status <lifecycle>` the maintainer runs after deciding the right lane. This is
the fleet-hygiene surface that catches ledger drift on ANY tenant WITHOUT needing
a dispatch — the durable fix for the silent-accumulation gap (only the
dispatcher's `ledger-check` used to catch it, and only for dispatch tenants).

### Signal 6 — fork-approval tier weakened while self-hosted CI is routed

`SPECIFICATION/non-functional-requirements.md` states a **fork-exclusion
precondition** on self-hosted CI runner hosts that makes the whole
containment-floor
reduction CONDITIONAL, not unconditional: self-hosted capacity may carry a
repository's merge gate ONLY while no workflow originating from a fork of that
repository can execute on it, and that exclusion MUST be enforced by the
repository's fork-pull-request workflow-approval setting **at its strictest
tier**. The strict tier matters specifically because under the weaker ones a
*returning* outside contributor's fork pull request runs its fork-controlled
workflow definition with no approval event. If that setting is quietly weakened
while a self-hosted runner is registered, the basis for self-hosted gating is
gone and nothing else in the fleet notices.

This is a two-step query, and the FIRST step is a guard that usually ends it.
For each fleet member, read whether the repo actually routes gating jobs to
self-hosted capacity:

```bash
gh api repos/thewoolleyman/<repo>/actions/variables/CI_RUNNER_LABELS --jq '.value'
```

A 404 (variable absent), or a value whose every label is hosted (each entry
beginning `ubuntu`, `windows`, or `macos`), means the precondition is not engaged
for that repo — emit nothing and make NO second call. On today's fleet every
member is hosted-only or has no variable at all, so this signal normally costs
one call per member and zero follow-ups.

> **Branch on `gh`'s EXIT CODE, never on whether its output is empty.** On a 404
> `gh api --jq '.value'` writes the error object
> (`{"message":"Not Found",…,"status":"404"}`) to **stdout** and exits 1 — so an
> emptiness test like `[ -z "$v" ]` does not fire, that error JSON flows into the
> hosted-label test, fails it (it does not begin `ubuntu`), and the repo is
> misreported as routing self-hosted. Verified live on
> `livespec-orchestrator-beads-fabro`, whose variable is genuinely absent: the
> emptiness form raised a spurious high-urgency alert, the exit-code form
> correctly emitted nothing. A false positive here is a phantom security alarm,
> so use `if ! value=$(gh api … --jq '.value' 2>/dev/null); then` — treat a
> non-zero exit as "not engaged" and stop.

Only when the value names a non-hosted label, read the tier:

```bash
gh api repos/thewoolleyman/<repo>/actions/permissions/fork-pr-contributor-approval --jq '.approval_policy'
```

`all_external_contributors` is the strict tier — healthy, emit nothing. Anything
else (`first_time_contributors`, `first_time_contributors_new_to_github`, `none`)
is a **high**-urgency attention item: a repo is gating merges on self-hosted
capacity that fork-controlled code can now reach.

**Why this is an attention signal and not a `just check` gate.** That endpoint
requires fine-grained `Administration: read`. The workflow `permissions:` key does
not expose `administration` at all, so the default `GITHUB_TOKEN` can never be
granted it; a CI-resident detector would mean escalating the shared fleet GitHub
App's permissions across every repo it is installed in and injecting a stronger
credential into a job — the opposite of what v192's Credential-separation clause
asks for. The maintainer's shell already holds a credential that can read it, and
the setting only changes when a human changes it, so a maintainer-facing signal is
the proportionate home. If this ever needs to become a hard gate, escalate the App
deliberately as its own decision — never implicitly as a side effect of adding a
check.

## Shaping each signal into an `attention_item`

Normalize every fired signal into the shared shape (defined in
`livespec-runtime`'s `livespec_runtime/attention_item.py`), all with
`kind: "internal"`:

- **`id`** — a stable natural key of the form `internal:<signal>:<repo>`, e.g.
  `internal:ci-red:livespec-runtime`, `internal:conformance-drift:livespec-dev-tooling`,
  `internal:pin-stale:livespec`, `internal:drift:livespec-console-beads-fabro`,
  `internal:ledger-drift:livespec`, `internal:fork-approval:livespec`.
  For an open bump PR, key on the PR to stay stable across runs, e.g.
  `internal:pin-stale:livespec#916`. For per-item ledger granularity, suffix the
  work-item id, e.g. `internal:ledger-drift:livespec:livespec-3lev.8`.
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
  handoff (a consistency check to run, not a known break); `medium` for a
  remappable ledger drift (`open`/`in_progress`, one-command fixable) and `high`
  for a residual ledger drift (a non-lifecycle status needing a lane decision);
  `high` for a weakened fork-approval tier (a live repo is gating merges on
  self-hosted capacity that fork-controlled code can reach).
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
    doctor invocation). For a remappable ledger drift, `kind: "shell"` with the
    `dispatcher.py ledger-normalize --project-root /data/projects/<repo>` command
    (self-heals the auto-mappable items); for a residual ledger drift, the
    `bd update <id> --status <lifecycle>` the maintainer runs after choosing a lane.

## Fail-soft — name the offender, never crash the scan

If any signal query fails for one repo (network down, `gh` unauthenticated, a
workflow not present in that repo, a repo missing from the checkout tree), SKIP
that repo/signal and NAME it in the output — e.g. "skipped: `<repo>` (CI query
failed: <reason>)" — then continue the rest of the scan. A single unreachable
repo must never abort the whole composition. This mirrors the fleet's
"readers fail soft; name the offender" discipline.

## Rendering — Markdown for the maintainer

Render a Markdown list grouped by signal (CI / conformance / pins / drift /
ledger / fork-approval) or by urgency (high first). Under each group, one row per item: the
summary, the owning repo named explicitly, and the ready-to-run
`handoff.command`. Put any `skipped:` notes in their own short section so nothing
strands silently.

**The healthy case emits nothing.** When every fleet CI run is green,
conformance passed, no pins are stale / no bump PRs are open, there is no drift to
chase, every tenant's ledger is status-conformant, and no repo routing gating CI
to self-hosted capacity has a weakened fork-approval tier, say so in one line
("fleet-dev is green — nothing internal needs attention") and stop. Emitting an
empty list is the normal, expected outcome most of the time.

## This skill is local-only

It lives at `.claude/skills/needs-attention-internal/SKILL.md` in *this* repo
(livespec core) and is **not** part of the livespec plugin, the spec, the copier
template, the fleet manifest's shipped surface, or any fleet-propagated artifact.
It is maintainer-only and UNSYNCED — the `overseer` precedent. Do NOT add it to
any plugin manifest, marketplace, conformance check, `.livespec-fleet-manifest.jsonc`,
copier template, or other repo. Its internal signals are livespec-fleet-development
facts an end user does not control, which is exactly why it never ships to the
plugin or to adopters.
