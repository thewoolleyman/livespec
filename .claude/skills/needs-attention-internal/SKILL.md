---
name: needs-attention-internal
description: >-
  Compose the livespec-fleet-DEVELOPMENT signals a fleet maintainer must watch
  but an end user does NOT control — CI red on any fleet repo, fleet-conformance
  drift, stale cross-repo pins, cross-repo consistency drift, ledger
  status-conformance drift, a weakened fork-approval tier on a repo that
  routes gating CI to self-hosted capacity, a fleet member whose shared-library
  pin has fallen more than one release behind, a gating CI job queued against
  a runner pool that cannot serve it, and a release lane that is failing or a
  release that should have happened and did not — into one point-in-time
  attention list. It mostly
  reads signals already computed elsewhere (GitHub Actions for CI, the dev-tooling
  conformance and pin-freshness checks, `/livespec:doctor` for drift); the five
  exceptions are the ledger status-conformance scan, which runs a cheap per-tenant
  `ledger-normalize --dry-run` directly because no scheduled workflow computes it,
  the fork-approval tier, which is a live repo setting no workflow can read
  from CI, the pin-lag signal, which reads each member's committed pin over
  `git` because the machinery that would report it is exactly what fails, the
  pool-health signal, which classifies a stalled gating job against the live k3s
  cluster because a workflow token can never hold cluster credentials, and the
  release-lane signal's absence half, which is computed here because no workflow
  can observe a run that never ran.
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
invoked, you gather eight dev-tooling-facing signals across the fleet and compose
them into one flat, point-in-time attention list. Four are statuses another
system already produces (you READ them cheaply); the other four — ledger
status-conformance drift, the fork-approval tier, a member's pin lag, and
pool health behind a queued gating job — you determine yourself, because nothing
else computes them (the ledger scan runs only inside a dispatch, no CI workflow
can read a repo's fork-approval setting at all, the pin-lag machinery is exactly
what fails when a pin lags, and the pool classification needs a cluster read no
workflow token can make). Your job is to gather each
cheaply, normalize it into the shared `attention_item` shape, and render it for
the maintainer.

This is the **internal** half of the `needs-attention` family. Its shipped
sibling — the product `needs-attention` (in both orchestrator plugins) — answers
"is there anything actionable about livespec in THIS repo?" for an end user. This
skill answers the complementary question a fleet maintainer owns: "is anything
wrong with the fleet's own development machinery right now?"

## The product-vs-internal dividing test (why these eight are here)

The single test that sorts a signal into product-vs-internal is: **does an end
user have actionable control over it?**

- **Yes → product** (the shipped `needs-attention`): their plugin version is out
  of date (they can update), a stale worktree sits in their repo (they can
  reap). Those never appear here.
- **No → internal** (this skill): livespec CI is red, fleet-conformance has
  drifted, a cross-repo pin is stale, two repos have drifted out of consistency,
  a tenant's ledger holds a work-item at a non-lifecycle status, a repo routing
  gating CI to self-hosted capacity has had its fork-approval tier weakened, a
  member's shared-library pin has fallen behind, a gating job is queued against a
  pool that cannot serve it. An
  end user cannot act on any of these — only a fleet maintainer can — so they
  live here, local and unsynced, never shipped.

## The eight internal signals and how to gather each

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

> **⛔ RUNNING THAT COMMAND ONCE PER MEMBER IS DENIED — use the ONE-CALL SCREEN
> below first.** Nine per-repo `gh` reads is a *looped GitHub read*, and
> `github_rate_limit_guard` refuses it. It also refuses its own prescribed
> remedy: `gh api --cache 20s` inside the loop is denied by the same message that
> just recommended `--cache` (`livespec-driver-claude-mu5`, journaled there
> 2026-08-11). **Do NOT restructure the command to slip past the matcher** —
> writing the loop into a script file to change what the guard sees is evasion,
> however defective the guard. Ask GitHub *once* instead:
>
> **GENERATE the query from the manifest — do NOT hand-write the aliases**, or the
> member list silently forks from `.livespec-fleet-manifest.jsonc` the moment a
> member is added. Write this to a file and run it (the generator itself is local
> Python — no `gh`, so it trips nothing):
>
> ```python
> # genquery.py — emits the one-call fleet query.
> # `ci` for Signal 1, `prs` for Signal 3, `queued` for Signal 8,
> # `release` for Signal 9.
> import json, re, sys
> from pathlib import Path
>
> OWNER = "thewoolleyman"
> QUEUED_RUNS = ("checkSuites(first: 5) { nodes { createdAt "
>                "checkRuns(first: 30, filterBy: {status: QUEUED}) { nodes { name } } } }")
> SELECTIONS = {
>     "ci":  "defaultBranchRef { name target { ... on Commit { oid statusCheckRollup { state } } } }",
>     "prs": "pullRequests(states: OPEN, first: 50) { nodes { number headRefName createdAt } }",
>     "queued": (f"defaultBranchRef {{ target {{ ... on Commit {{ {QUEUED_RUNS} }} }} }} "
>                f"pullRequests(states: OPEN, first: 20) {{ nodes {{ number headRefName "
>                f"commits(last: 1) {{ nodes {{ commit {{ {QUEUED_RUNS} }} }} }} }} }}"),
>     "release": ("defaultBranchRef { name target { ... on Commit { oid } } } "
>                 "latestRelease { tagName createdAt tagCommit { oid checkSuites"
>                 "(first: 20) { nodes { conclusion workflowRun { workflow { name "
>                 "} } } } } } "
>                 'rel: ref(qualifiedName: "refs/heads/release") { target { oid } } '
>                 "pullRequests(states: OPEN, first: 20) { nodes { number title "
>                 "createdAt mergeable } }"),
> }
>
> raw = Path("/data/projects/livespec/.livespec-fleet-manifest.jsonc").read_text()
> txt = "\n".join(l for l in raw.splitlines() if not l.strip().startswith("//"))
> members = json.loads(re.sub(r",(\s*[}\]])", r"\1", txt))["fleet"]
> names = [m["repo"] if isinstance(m, dict) else m for m in members]
>
> selection = SELECTIONS[sys.argv[1] if len(sys.argv) > 1 else "ci"]
> print("query {")
> for index, repo in enumerate(names):
>     print(f'  r{index}: repository(owner: "{OWNER}", name: "{repo}") '
>           f"{{ nameWithOwner {selection} }}")
> print("}")
> print(f"# members: {len(names)}", file=sys.stderr)   # CONTROL — expect the manifest's count
> ```
>
> ```bash
> python3 genquery.py ci > /tmp/q.graphql          # prints "# members: N" to stderr as a control
> gh api graphql -f query="$(cat /tmp/q.graphql)" > /tmp/fleetci.json
> ```
>
> One call, no loop, and **fewer** API reads than the per-repo form — which is the
> guard's own stated concern. Parse the JSON in a SEPARATE call (a comprehension
> in the same command as a `gh` invocation is itself denied — the matcher keys on
> the `for` token).
>
> **Live-exercised 2026-08-11, both selections**, generated → executed → parsed.
> The `ci` run returned all 9 members and its result was identical to a
> hand-written equivalent except for one repo's HEAD, which had genuinely moved
> mid-session — i.e. the delta was real-world state, not a query defect. The `prs`
> run fed the Signal 3 parser unchanged and reproduced 4 bump PRs against 10 open
> PRs fleet-wide.
>
> **THIS SCREEN IS NOT EQUIVALENT TO SIGNAL 1, IN BOTH DIRECTIONS, AND BOTH
> MATTER:**
>
> - **BROADER.** `statusCheckRollup` aggregates *every* check on the HEAD commit,
>   not just the workflow named `CI`. A non-`CI` workflow red on that commit turns
>   it non-`SUCCESS` — which is coverage this skill's own gap note says Signal 1
>   lacks. So treat non-`SUCCESS` as **"drill into this repo"** with the per-repo
>   `gh run list` above (now a handful of one-shot calls, not a loop), never as
>   "the `CI` workflow is red".
> - **BLIND.** The rollup hangs off a COMMIT, so it cannot see a **scheduled**
>   workflow's failure at all — that failure attaches to no commit. Verified
>   2026-08-11: all nine members read `SUCCESS` while `Fleet conformance` (Signal
>   2) was red on its third consecutive scheduled run. It is equally blind to a
>   red run on an EARLIER commit, which is how a required gate can go red on
>   master and be invisible an hour later once a green commit lands on top.
>
> **So a green screen means "no member's HEAD commit has a failing check right
> now" — nothing more.** Signal 2 is what covers the scheduled tier, and neither
> covers a red run that a later green commit has buried.

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

> **⛔ BOTH LINES ABOVE ARE DENIED AS WRITTEN — and for two DIFFERENT reasons, so
> fixing one does not fix the other.**
>
> 1. Repeating the `gh pr list` per fleet repo is a *looped GitHub read*
>    (`github_rate_limit_guard`), the same denial Signal 1 hits.
> 2. **The `--jq` above is denied on its own, un-looped, purely for containing
>    the token `select(`.** That is `livespec-driver-claude-mu5`: the guard
>    matches substrings, not behaviour. So even a single-repo invocation of the
>    command as written fails.
>
> Sweep all members in ONE call and filter locally instead, reusing the SAME
> manifest-driven generator Signal 1 defines above — its `prs` selection exists
> for exactly this, so the member list cannot fork between the two signals:
>
> ```bash
> python3 genquery.py prs > /tmp/q.graphql         # prints "# members: N" to stderr as a control
> gh api graphql -f query="$(cat /tmp/q.graphql)" > /tmp/fleetprs.json
> ```
>
> Then match `^chore/(freshness-)?bump-` in a SEPARATE call (Python/`jq` over the
> file — no `gh` in that command, so neither trigger fires).
>
> **ALWAYS PRINT THE TOTAL OPEN-PR COUNT BESIDE THE BUMP COUNT.** A bump count of
> zero means nothing if the query saw zero PRs at all — the same
> count-without-its-listing trap that produced a false "the lockstep broke" and a
> false "a CI runner exists" elsewhere in this fleet on 2026-08-11. Verified live
> that day: 4 bump PRs against 10 open PRs fleet-wide, so the 4 is a real subset
> rather than a filter artifact.

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
> 2026-08-11 by ad-hoc sweeps, not by this skill. **Two are now CLOSED by
> Signal 9** and are kept here, struck through in prose rather than deleted, so
> the record of what was once invisible survives:
>
> - **~~A failing RELEASE gate.~~ CLOSED by Signal 9 (2026-08-21.)** Signal 1
>   reads only the workflow named `CI`. livespec's release gate is
>   `release-tag.yml`, which fires on TAG PUSH; it failed on four consecutive
>   published releases (v0.29.0 → v0.30.0) while every `CI` run stayed green.
>   It then did it AGAIN — five consecutive cuts, v0.34.2 → v0.37.0 — which is
>   what finally motivated Signal 9.
> - **~~A blocked `release-please` PR.~~ CLOSED by Signal 9 (2026-08-21.)**
>   Signal 3 matches only bump branches, so a release PR stuck on a red check is
>   invisible. The `livespec-console-beads-fabro` instance that sat **18.6 days**
>   when this gap was written had reached **30 days** by 2026-08-22.
> - **An adopter's gating workflow under a different name. STILL OPEN.** The
>   fleet is non-uniform: `resume`'s gating workflow is `check.yml`, not
>   `ci.yml`. Signal 9 does not close this — it reads release lanes, not gating
>   lanes, and Signal 1 still hardcodes the name `CI`.
>
> The remaining gap is a design decision, not a bug fix, and belongs with
> `livespec-39h1` (whose thesis is precisely that nothing reads these). Until
> then, **a clean run of this skill means "the nine signals are green", not "the
> fleet is healthy"** — say the former when reporting.

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
for that repo — emit nothing and make NO second call.

**The guard no longer short-circuits, and an earlier version of this paragraph
said it did.** It used to state that every member was hosted-only or had no
variable, so the signal "normally costs one call per member and zero
follow-ups". The k3s cutover falsified that. As of 2026-08-21 NINE of the ten
fleet members route gating CI to a self-hosted k3s scale set — `livespec` →
`livespec-local-ci-k3s`, `livespec-dev-tooling` → `livespec-dev-tooling-k3s`,
and likewise for `livespec-overseer`, `livespec-driver-claude`,
`livespec-driver-codex`, `livespec-driver-pi`,
`livespec-orchestrator-git-jsonl`, `livespec-runtime`, and
`livespec-console-beads-fabro`. Only `livespec-orchestrator-beads-fabro` has no
variable at all. So the second step now runs for nine members, and this signal
costs two calls per member rather than one.

That stale sentence was not merely inaccurate — it described the signal as
effectively a no-op, which is the reading that stops anyone running it. When it
was finally run on 2026-08-21, `livespec-overseer` and `livespec-driver-pi` were
BOTH sitting at `first_time_contributors` while gating merges on self-hosted
capacity: the precise violation this signal exists to catch, live and unnoticed
since their cutovers. Both were repaired to `all_external_contributors` the same
day; the systemic gap — the cutover engages the precondition and verifies
nothing — is tracked as `livespec-s43svm.39`.

The general lesson, worth more than this one signal: **a guard whose cheapness
is asserted from a measured snapshot of the world will silently become a guard
that never fires when the world moves.** State what makes the guard short-circuit,
not how often you expect it to.

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

### Signal 7 — a fleet member's shared-library pin is more than one release behind

Signal 3 watches the pin-staleness MACHINERY: the freshness sweep's status, and
the bump PRs it files. Both are events. This signal watches the CONSEQUENCE —
what each member's `master` actually pins, right now — and fires when a member
has fallen more than one release behind.

**Why a seventh signal rather than widening Signal 3.** A bump that HARD-FAILS
opens no pull request at all, so there is nothing for Signal 3's `gh pr list` to
find; and a bump that succeeds merges in about a minute, so it is absent from
`--state open` almost immediately too. Signal 3 therefore reports the same
silence for "bumping cleanly" and "cannot bump at all". That is not a bug in
Signal 3 — an open bump PR is a real item — it is that the question "is this
member CURRENT?" cannot be answered by looking at pull requests. Five consumers
sat two releases behind across two release cycles, in red, and neither Signal 1
(scoped to the workflow named `CI`) nor Signal 3 (scoped to open bump PRs) could
see it (`livespec-s43svm.34`, `.35`).

**This signal uses NO GitHub API.** It reads committed state out of the local
clones over `git`, which is worth stating plainly given how much of this file is
guard-denial workarounds: there is no rate-limit budget to spend, no `select(`
or loop token to trip `github_rate_limit_guard`, no `--state` semantics to get
wrong, and no commit anchoring to fail on a `repository_dispatch` run. A pin on
`master` is a durable fact that does not stop being true because nobody looked
in time.

Latest release of the shared library, and each member's pinned tag:

```bash
# 1. the producer's newest RELEASE tag (pins track releases, not master)
git -C /data/projects/livespec-dev-tooling fetch origin master --tags --quiet
git -C /data/projects/livespec-dev-tooling tag --sort=-v:refname | head -1

# 2. one member's pinned tag, read from committed state, NOT the working tree
git -C /data/projects/<member> fetch origin master --quiet
git -C /data/projects/<member> show origin/master:pyproject.toml \
  | grep -E '^livespec-dev-tooling = \{' \
  | grep -oE 'tag = "[^"]+"'
```

Enumerate members from `.livespec-fleet-manifest.jsonc` rather than a hardcoded
list. A member with no `livespec-dev-tooling = {` line is NOT stale — it is a
non-consumer; skip it and say so, never report it as missing a pin. Do not
assume which members those are: verified 2026-08-20, ALL NINE non-producer fleet
members carry the pin, including `livespec-console-beads-fabro`, which is the
Rust console and carries no canonical check aggregate yet still pins the shared
library for its Python tooling. An earlier draft of this section asserted that
member pinned nothing; the live exercise below falsified it.

**Firing rule.** Count the release tags strictly newer than the member's pinned
tag. Fire when that count is **2 or more**. One release behind is the normal
window between a release and its fan-out landing, so firing at one would emit an
item on every member on every release for a few minutes; two or more means at
least one fan-out wave did not reach this member.

**Print the pinned tag and the latest tag on every member, including the current
ones, before reporting any conclusion.** A zero count means nothing if the read
returned an empty pin on every member — the same count-without-its-listing trap
Signal 3 records. An empty pin is a FAILED READ (wrong path, renamed file,
member not cloned), not a current member; treat it as fail-soft and name it.

**`attention_item` shape.** `id` is `internal:pin-lag:<repo>`; `urgency` is
`high` — unlike an open bump PR (Signal 3, `medium`, which is self-resolving
once it merges), a lagging pin means the automatic path has already failed and
will not retry itself. `summary` names both versions and the gap, e.g.
"livespec-overseer pins livespec-dev-tooling v1.28.13, 4 releases behind
v1.29.3". `source_ref` is `{repo: "<repo>", path: "pyproject.toml",
work_item: null}`. `handoff` is `kind: "shell"` with the command that shows why
the member did not take the bump:

```
gh run list --repo thewoolleyman/<repo> --workflow "Bump pin from sibling dispatch" --limit 5
```

That handoff is deliberately the EVENT query: the signal detects the state
because state is reliable, and hands the maintainer the event because the event
is where the diagnosis lives.

**Live-exercised 2026-08-20.** Run against real fleet state during the v1.29.3
wave, this signal emits exactly one item — `livespec-overseer`, pinning
v1.28.13, four releases behind a latest release of v1.29.3 — and nothing on the
other eight members, which all reached v1.29.3. That member is frozen by
`livespec-s43svm.36`, so the demonstrating condition is real rather than
constructed, and persists until .36 is resolved. Before .34's fix, the same
signal would have emitted five items across two release cycles, which is
precisely the outage it exists to have caught.

### Signal 8 — a gating job is queued against a pool that cannot serve it

A gating CI job sitting `queued` with no runner assigned has at least FOUR
distinct causes, and at the moment an operator looks they are indistinguishable:

  (a) **Queued and scaling up.** NORMAL. Observed gate times on this cluster run
      4s to 293s, so anything inside a few minutes is the system working.
  (b) **The pool does not exist.** The job requests a scale set no cluster
      provides. GitHub never assigns it and never errors — it queues forever.
      Observed live as `livespec-s43svm.38`.
  (c) **The pool holds a wedged runner.** A pod is `Running` and `ready=true`
      but its server-side registration is gone, so it occupies the replica slot
      the queued job's own demand created and never claims work. Observed live
      as `livespec-s43svm.30`.
  (d) **Genuine capacity exhaustion.** Kueue has pending workloads and the
      cohort has nothing left to borrow.

This is ONE signal answering "does this queued job's pool exist, is it
reachable, and can it actually serve this job — and if not, which cause is it?"
It replaces three proposed half-detectors (`.30` scope item 2, `.38`'s detection
half, and `.9`'s re-derivation), because three partial answers to one question
would each look authoritative.

**Two-step and guarded, in Signal 6's shape.** Step one is GitHub-only; step two
is the cluster read.

**STEP 1 — GUARD, one call, no loop.** Reuse Signal 1's `genquery.py` with a
third selection. The guard short-circuits when the fleet-wide query returns ZERO
queued check runs. That is the CONDITION — not a claim about how often it holds.
Do not write "on today's fleet this is normally free" into this section: Signal 6
carried exactly that sentence, the k3s cutover falsified it, and the signal went
unrun through a live violation (`livespec-s43svm.39`).

Signal 1's `genquery.py` already carries the `queued` selection — one generator,
one member list, so this signal cannot silently fork from the manifest:

```bash
python3 genquery.py queued > /tmp/q.graphql
gh api graphql -f query="$(cat /tmp/q.graphql)" > /tmp/queued.json
```

**The GraphQL answers "is anything queued", NOT "for how long".** A queued
`CheckRun` carries no reliable queue timestamp, and the enclosing suite's
`createdAt` is the suite's age, not the run's wait — on an old PR whose checks
were re-run, those differ by days. Step 1 is therefore a screen, not a
measurement. Age comes from step 1b, and only for the repos step 1 named.
Verified live 2026-08-21: the query is accepted, `filterBy: {status: QUEUED}` is
a valid `CheckRunFilter` field, and it returns empty `nodes` when nothing is
queued.

**STEP 1b — AGE AND POOL, per firing repo only.** For each repo step 1 named:

```bash
gh api "repos/thewoolleyman/<repo>/actions/runs?status=queued&per_page=20" \
  --jq '.workflow_runs[] | "\(.id) \(.name) \(.run_started_at)"'
gh api "repos/thewoolleyman/<repo>/actions/runs/<run-id>/jobs" \
  --jq '.jobs[] | select(.status != "completed") | {name, status, started_at, runner_name, labels}'
```

`labels` is the RESOLVED `runs-on` — verified live 2026-08-21, a real job
returned `"labels": ["livespec-dev-tooling-k3s"]`. Use it directly. Do NOT try
to derive the requested pool by parsing workflow YAML: across the fleet's 155
committed `runs-on` declarations, essentially every one is the indirection
`${{ fromJSON(vars.CI_RUNNER_LABELS || '["ubuntu-latest"]') }}`, so the file
never names a pool. The variable does, and the resolved job record does.

> **Two field shapes verified against real queued jobs, both easy to get wrong.**
> `started_at` IS populated on a `queued` job and carries the QUEUE time, so the
> wait is `now - started_at` with no fallback needed — do not reach for the run's
> `run_started_at` instead. And `runner_name` on a queued job is the EMPTY STRING,
> not null, so `.runner_name // "<none>"` does NOT substitute: jq treats `""` as
> truthy and only `null`/`false` trigger `//`. Test emptiness explicitly.


Fire only on jobs past **300 seconds** without a runner. That threshold is the
top of the observed 4–293s gate range, rounded up; re-derive it if the range
moves rather than treating 300 as a constant.

**STEP 2 — CLASSIFY**, in this order, because each test is cheaper and more
decisive than the next.

**(b) POOL DOES NOT EXIST — test first; it is static and unambiguous.**

```bash
ssh poweredge-xubuntu 'sudo KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl \
  -n arc-runners get autoscalingrunnersets \
  -o jsonpath="{range .items[*]}{.metadata.name}{\"\n\"}{end}"'
```

No match for the job's `labels` → cause (b), urgency **high**: this job can
never run.

> **One allowance, and it is not a bug.** `[self-hosted, livespec-orchestrator]`
> in `livespec-orchestrator-beads-fabro`'s `acceptance-live-golden-master.yml` is
> the deliberately-privileged GATE RUNNER on the separate podman/JIT path. It is
> not an ARC scale set, never appears in `autoscalingrunnersets`, and must NEVER
> be reported as cause (b). Verified 2026-08-21: it is the ONLY literal
> self-hosted `runs-on` in the fleet — every other repo reaches its pool through
> `CI_RUNNER_LABELS`.

A cheap PREFLIGHT of the same comparison, needing no queued job, is each repo's
variable against that same list. Measured 2026-08-21: nine of ten members route
to a k3s scale set and all nine match a live one; `livespec-orchestrator-beads-fabro`
has no variable (404). Two live scale sets are referenced by nobody —
`local-ci-k3s` (the orphan, `livespec-s43svm.28`) and `poweredge-xubuntu-k3s`.
Unreferenced is fine; unresolvable is cause (b).

> **Read that 404 with the exit status, never the output.** Running the variable
> read across members with `$(gh api … || echo '(absent)')` printed BOTH the
> error object and the fallback on the one absent member, because `gh api --jq`
> writes `{"message":"Not Found",…,"status":"404"}` to STDOUT before exiting
> non-zero. Reproduced live 2026-08-21. Use
> `if ! value=$(gh api … 2>/dev/null); then` — the same rule Signal 6 states.

**(c) POOL HOLDS A WEDGED RUNNER — consume the host sweeper; do NOT reimplement.**
`scan-wedged-runners.timer` already sweeps every five minutes for the
`Registration ... was not found` signature.

```bash
ssh poweredge-xubuntu 'sudo journalctl -u scan-wedged-runners.service \
  --since "1 hour ago" --no-pager' | grep -E "pod=.*scale-set=|ESCALATION"
ssh poweredge-xubuntu 'sudo cat /var/lib/ci-runner-k3s/wedged-runner-streak'
```

A `pod=… scale-set=<the job's pool>` line inside the window → cause (c),
urgency **high**.

> **The timer runs in `--clear` mode** (verified live 2026-08-21:
> `ExecStart=…/scan-wedged-runners.sh --clear`), so by the time you look the pod
> is usually already deleted and ARC has replaced it. The JOURNAL is the record,
> not the cluster — querying pods finds nothing and proves nothing.
>
> **The streak file counts CONSECUTIVE sweeps, not occurrences.** The two real
> wedges of 2026-08-19 landed 15 minutes apart, so each recorded
> `consecutive runs with findings: 1` and the file now reads `0`. A zero streak
> means "the last sweep was clean", never "this has not happened".

**(d) CAPACITY EXHAUSTION — Kueue-side, not GitHub-side.**

```bash
ssh poweredge-xubuntu 'sudo KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl \
  get clusterqueue -o custom-columns=NAME:.metadata.name,PENDING:.status.pendingWorkloads,ADMITTED:.status.admittedWorkloads'
ssh poweredge-xubuntu 'sudo KUBECONFIG=/etc/rancher/k3s/k3s.yaml kubectl get node \
  -o jsonpath="{.items[*].status.allocatable.ci-runner\.io/churn-slot}"'
```

Pending workloads on the repo's ClusterQueue with no borrowable cohort capacity
→ cause (d), urgency **low**: the system is correctly saying "wait".

> **Key (d) on `pendingWorkloads`, NEVER on admitted-versus-quota.** Measured
> live 2026-08-21 under real load: `livespec-cq` carried `ADMITTED 9` against a
> `nominalQuota` of 3, with `PENDING 0`. That is Fair Sharing working exactly as
> designed — the queue borrowed six slots from the cohort — and a test comparing
> admitted against nominal quota would have reported capacity exhaustion at the
> precise moment the cluster was serving every job it had been given. The quota
> is a fair-share weight, not a ceiling.

**(a) SCALING UP — the residual.** None of (b), (c), (d) fired → scaling up.
Emit nothing.

**Two fields that look like health readings and are not.** ARC's "Calculated
target runner count" log line reports `currentRunnerCount`, which is
`w.targetRunners` — the listener's own last-patched target, not an observation of
live runners. And ARC 0.14.2's `updateRunStatusFromPod` derives EphemeralRunner
status from pod phase and readiness only; it never re-validates a Running
runner's registration, which is why the host-side sweeper exists at all. Neither
can answer (c).

**`attention_item` shape.** `id` is `internal:pool-health:<repo>:<run-id>` —
keyed on the run so it stays stable while the job remains queued and does not
collide when two repos stall at once. `urgency` per cause above. `summary` names
the repo, the pool, the wait, and the CAUSE, e.g. "livespec-driver-pi: job
`check-types` queued 22m against `livespec-driver-pi-k3s`; pool holds a wedged
runner (cleared 21:05)". `source_ref` is `{repo: "<repo>", path: null,
work_item: null}`. `handoff` is `kind: "shell"`, chosen by cause: for (b) the
`set-ci-runner-labels.sh --dry-run` that shows the mis-set pool; for (c)
`ssh poweredge-xubuntu 'sudo journalctl -u scan-wedged-runners.service -n 50 --no-pager'`;
for (d) the `kubectl get clusterqueue` above.

**This signal adds a new dependency class to this skill, deliberately and
visibly.** Signals 1–7 read GitHub, `git`, and `bd`. This one also needs **SSH to
`poweredge-xubuntu` and `kubectl`** against the k3s cluster. That is a real
widening, stated here rather than slipped in. When the host is unreachable, this
signal FAILS SOFT like every other: emit
`skipped: pool-health (poweredge-xubuntu unreachable: <reason>)`, keep whatever
step 1/1b established, and never abort the scan. A job queued past the threshold
with an unreachable cluster is reported as UNCLASSIFIED, not as healthy — the
absence of a classification is itself worth the maintainer's attention.

**Why here and not a CI gate.** The classification needs a cluster read, so a
CI-resident detector would mean injecting cluster credentials into a job — the
same escalation Signal 6 rejects for the fork-approval endpoint, and the opposite
of the Credential-separation clause. The maintainer's shell already holds both
credentials. And a stuck job is not a property of a CHANGE, so no per-commit
check should assert it; it is a property of the world, which is what this surface
is for. This answer and Signal 6's must stay consistent — if one is revisited,
revisit both (`livespec-s43svm.39`, `livespec-s43svm.41`).

**Live-exercised 2026-08-21, in BOTH guard states.** Step 1 was run twice from
the generator above, against real fleet state:

- **Short-circuiting.** Ten repos returned (matching the manifest's control
  count), zero queued check runs fleet-wide → no step 1b, no cluster call.
- **Firing.** Re-run while this signal's own pull request was queuing, it
  returned exactly one hit — `thewoolleyman/livespec` PR #2454,
  `check-metadata-batch`. Step 1b on that run returned nine jobs at
  `status=queued` with empty `runner_name` and `labels=livespec-local-ci-k3s`.
  Classification: `livespec-local-ci-k3s` IS in the live scale-set list, so not
  (b); no wedge in the journal window, so not (c); `livespec-cq` showed
  `PENDING 0`, so not (d); residual → **(a) scaling up, emit nothing**. Which was
  correct: every job started within seconds.

The (b) preflight ran across all ten members against the live 11-scale-set list
with no mismatch. The (c) consumer ran against the host journal, which holds
THREE real findings in fourteen days — the two genuine wedges of 2026-08-19 on
`livespec-driver-claude-k3s` and `livespec-overseer-k3s`
(`livespec-s43svm.30`), plus one deliberate `wedgeprobe-timer` probe. Those are
real sweeper output, not fixtures.

**Cause (d) has never been observed firing, and this section does not claim it
has.** Both (d) reads — idle, and under a nine-job load — returned zero pending.
The load read is the more useful of the two, because it is what exposed the
admitted-versus-quota false positive recorded above; but neither is a positive
observation of (d), and the first real one should be journalled on
`livespec-s43svm.41` when it happens.

### Signal 9 — a release lane is failing, or a release that should have happened did not

A merged change is not a delivered one. This signal answers the delivery
question directly: **did the last release publish through a passing gate, and is
a release that should have happened actually happening?**

It exists because BOTH halves have now failed unread, in different repos, at the
same time:

- **`livespec`**: `Release tag` failed on FIVE consecutive published cuts,
  v0.34.2 → v0.37.0. The releases published anyway — the gate fires on tag push,
  after the release object exists — so nothing was blocked and nothing was read.
- **`livespec-console-beads-fabro`**: no release at all since `v0.3.0`
  (2026-07-21). Release PR #404 sat MERGEABLE-but-BLOCKED for **30 days**.

**THE TWO HALVES ARE COMPLEMENTARY AND NEITHER SUBSUMES THE OTHER. This is the
whole reason the signal has two shapes, so do not collapse them:**

|  | Releases still happening? | Gate result | Caught by |
|---|---|---|---|
| `livespec` | YES — tags kept advancing | RED | Shape A only |
| `livespec-console-beads-fabro` | NO — none for 30 days | n/a, never ran | Shape B only |

A lane-failure detector would have stayed silent on the console (no failing run
exists — the run never happens). An absence detector would have stayed silent on
`livespec` (releases were publishing on schedule; only the gate was red).

**SHAPE A — the last release published through a failing gate.** The release
gate's check suite attaches to the TAG COMMIT, so it is reachable from the
one-call screen. This was NOT obvious: the fleet-sweep guidance assumed release
run history needed the per-repo REST Actions endpoint, and it does for *history*
— but for "how did the latest release's gate conclude?" GraphQL answers it with
no loop and no per-repo call.

**SHAPE B — a release that should have happened did not.** Three absence
conditions, none of which involve a failing run:

  - a `release-please` PR (title starts `chore(master): release`) open beyond a
    threshold — treat **7 days** as attention-worthy, since a healthy one merges
    in minutes;
  - `defaultBranchRef` HEAD far ahead of `latestRelease`;
  - a repo whose `release` ref has not advanced to match.

**ONE CALL, NO LOOP.** Reuse Signal 1's `genquery.py` with the `release`
selection — same generator, same member list, so this signal cannot silently
fork from the manifest:

```bash
python3 genquery.py release > /tmp/q.graphql
gh api graphql -f query="$(cat /tmp/q.graphql)" > /tmp/fleetrel.json
```

Parse the JSON in a SEPARATE call. A comprehension in the same command as the
`gh` invocation is denied — the matcher keys on a loop token at command
position, and a `for` at the start of a line inside a quoted `python3 -c` counts.
That fired three times while this signal was being authored, on commands
containing exactly one un-looped `gh` read. Splitting the PARSING out is the
sanctioned move (it performs zero network calls, so it cannot be evasion);
splitting the READS across calls would be evasion. See
`.ai/ci-gate-discipline.md`.

**WHAT THIS SIGNAL CANNOT SEE, recorded rather than implied away:**

- **Lane HISTORY.** Shape A reads only the LATEST release's gate. It cannot say
  "9 consecutive cuts failed" or "last green was 16 days ago". That depth needs
  per-workflow run history, which is REST-only and per-repo. The prior art is
  `livespec-overseer`'s `scripts/release-lane-watch.py` +
  `overseer/release_lane_watch.py` (`overseer-hgq4wi.15`): stdlib-`urllib`, the
  workflow-scoped `actions/workflows/<file>/runs` endpoint, three-valued
  (0 healthy / 1 failing / 2 **cannot measure**), with `lane_state()` a pure
  function of run history and therefore replay-testable. **Propagating that
  per-repo watcher fleet-wide is the depth half of this signal and is tracked
  under `livespec-n33rwg`. Do not reimplement it here.**
- **Repos that publish no releases.** The four adopters (`openbrain`,
  `dolt-server`, `resume`, `homelab`) carry no tags and no release branch. They
  consume rather than publish, so both shapes are meaningless for them and they
  are OUT OF SCOPE — not silently green.
- **Whether a stalled release SHOULD have cut.** A repo with only
  `docs:`/`chore:` commits since its last tag is correctly not releasing.
  Shape B's HEAD-ahead condition will read that as lag. That is not a false
  positive to suppress — it is precisely the commit-type deliverability defect
  (a shipped-surface fix under a non-releasing commit type reaches zero running
  seats), tracked as carrier R6 under `livespec-n33rwg`.

## Shaping each signal into an `attention_item`

Normalize every fired signal into the shared shape (defined in
`livespec-runtime`'s `livespec_runtime/attention_item.py`), all with
`kind: "internal"`:

- **`id`** — a stable natural key of the form `internal:<signal>:<repo>`, e.g.
  `internal:ci-red:livespec-runtime`, `internal:conformance-drift:livespec-dev-tooling`,
  `internal:pin-stale:livespec`, `internal:drift:livespec-console-beads-fabro`,
  `internal:ledger-drift:livespec`, `internal:fork-approval:livespec`.
  For an open bump PR, key on the PR to stay stable across runs, e.g.
  `internal:pin-stale:livespec#916`. For the release-lane signal, key the two
  shapes apart so a repo can carry both at once, e.g.
  `internal:release-gate-red:livespec` (Shape A, the last release published
  through a failing gate) and `internal:release-stalled:livespec-console-beads-fabro`
  (Shape B, a release that should have happened and did not). For per-item ledger granularity, suffix the
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
  self-hosted capacity that fork-controlled code can reach); for pool health,
  the cause decides — `high` for a pool that does not exist or holds a wedged
  runner (the job can never run, or is blocked by a dead replica), `low` for
  genuine capacity exhaustion (the system is correctly saying "wait"), and
  nothing at all for a job that is simply scaling up; `high` for a release lane
  in either shape — a red gate means every consumer is installing an artifact
  that was never validated, and a stalled release means siblings cannot consume
  this repo's work at all.
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
ledger / fork-approval / pin-lag / pool-health) or by urgency (high first). Under each group, one row per item: the
summary, the owning repo named explicitly, and the ready-to-run
`handoff.command`. Put any `skipped:` notes in their own short section so nothing
strands silently.

**The healthy case emits nothing.** When every fleet CI run is green,
conformance passed, no pins are stale / no bump PRs are open, there is no drift to
chase, every tenant's ledger is status-conformant, no repo routing gating CI
to self-hosted capacity has a weakened fork-approval tier, no member's pin has
fallen behind, and no gating job is queued past the threshold, say so in one line
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
