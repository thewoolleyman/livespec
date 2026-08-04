# GitHub request-budget discipline — design record

Thread anchor: ledger epic `livespec-httc` (this repo's tenant, `livespec`).
Status is never recorded here; read it from the ledger.

## The problem in one paragraph

GitHub API request-budget best practices are observed by convention, not by
mechanism. Nothing in any governed repository prevents an unconditional poll
loop or an unpaced bulk-mutation burst from exhausting a request budget. The one
wiring mechanism the fleet currently uses for shared agent guards — an entry in
each repository's committed `.claude/settings.json` — reaches only the population
that authors it, and has already drifted along the fleet/adopter boundary.

## The triggering incident (2026-08-04)

A cross-repo mission hit GitHub 403 responses during a time-critical window. Two
DISTINCT failure modes were present. Conflating them is the main analytical trap,
because they have different limits, different arithmetic, and different fixes.

**Mode 1 — unconditional polling (primary limit).** Waiting on a ~77-minute CI
run by re-reading run status on a short interval spends one request per poll for
data that is unchanged on almost every read. The primary limit for an
authenticated user token is 5,000 requests/hour.

**Mode 2 — unpaced bulk mutation (SECONDARY limit).** A cache-prune step intended
to issue ~191 REST `DELETE` calls. Mutations cost 5 points against a secondary
limit of 900 points per minute, so ~191 deletes is ~955 points — over the
per-minute ceiling BY ITSELF, independent of how much primary hourly budget
remained.

Mode 2 matters disproportionately because the pre-existing ledger item
`livespec-j49m` explicitly EXCLUDES it: that item characterises a PRIMARY-limit
exhaustion and records "NOT a secondary rate limit" as one of its distinguishing
tests. So before this thread, the secondary-limit hazard class was unowned by any
item in any tenant.

## Verified GitHub facts (checked 2026-08-04 against docs.github.com)

Recorded here because the design depends on them and they are easy to
misremember.

| Limit | Value |
|---|---|
| Unauthenticated | 60 requests/hour per IP |
| Authenticated user token / personal access token | 5,000 requests/hour |
| GitHub App installation | 5,000/hour base, +50/hour per repo above 20 and +50/hour per user above 20, capped at 12,500/hour |
| GitHub App installation, Enterprise Cloud | 15,000/hour |
| `GITHUB_TOKEN` inside GitHub Actions | **1,000/hour per repository** |
| Secondary: points per minute | 900 REST, 2,000 GraphQL |
| Secondary: concurrent requests | 100 across REST and GraphQL |
| Point cost | GET/HEAD/OPTIONS = 1; POST/PATCH/PUT/DELETE = **5** |

Two properties do the most work in the design:

1. **A conditional request that returns `304` is free.** GitHub's wording: "Making
   a conditional request does not count against your primary rate limit if a
   `304` response is returned and the request was made while correctly authorized
   with an `Authorization` header." No governed repository currently sends
   `If-None-Match` on any polling path. This is the single largest available
   reduction and needs no measurement to justify.
2. **GraphQL is a SEPARATE bucket.** Measured on the maintainer host 2026-08-04:
   `core` at 116/5000 used, `graphql` at 3/5000 used. The contended bucket is
   `core`; the GraphQL bucket sits essentially idle. Moving fan-out status reads
   to GraphQL both collapses N REST calls into one query AND draws on the idle
   bucket.

There is no purchasable rate-limit increase for github.com. The only tier lever
is GitHub Enterprise Cloud (organization accounts only), which raises 5,000 to
15,000 — a 3x, not an order of magnitude. Support and Sales exceptions are
case-by-case and rare. **Buying capacity is not an available strategy; the
techniques above are.**

## The measured propagation defect

The fleet's existing shared agent guard `pretooluse_background_guard` (module
`livespec_dev_tooling.agent_hooks`, owned by the `livespec-dev-tooling`
repository) is wired through each repository's committed `.claude/settings.json`.
Measured 2026-08-04 by reading each repository's committed settings file:

| Repository | Class | Guard wired |
|---|---|---|
| `livespec` | fleet | yes |
| `livespec-dev-tooling` | fleet | yes |
| `livespec-overseer` | fleet | yes |
| `livespec-orchestrator-beads-fabro` | fleet | yes |
| `homelab` | adopter | **no** |
| `openbrain` | adopter | **no** |
| `resume` | adopter | **no** |

Four of four fleet members sampled, zero of three adopters — and the triggering
incident occurred in `homelab`, an adopter. This is a fifth instance of the class
recorded in ledger item `livespec-j5i9` ("the repo that enforces the fleet is
systematically the least enforced"), on a different axis: there the unenforced
population is the OWNING repo, here it is the ADOPTERS. Same structural cause —
enforcement machinery ends up armed where it was authored rather than where it is
needed.

## Propagation surfaces — which ones actually reach an adopter

This is the load-bearing analysis of the thread. Four channels exist; they do NOT
have equal reach, and picking the wrong one is what produced the table above.

1. **Per-repo `.claude/settings.json`.** Reaches only repositories that hand-wire
   it. Demonstrated above to reach zero adopters. **Do not use for this concern.**
2. **A Driver plugin's shipped hook manifest** —
   `livespec-driver-claude/.claude-plugin/hooks/hooks.json`. Auto-loads in every
   repository that enables the Driver plugin. `homelab`'s committed
   `.claude/settings.json` enables `livespec@livespec-driver-claude`, so `homelab`
   already receives `tmux_fleet_guard`, `block_auto_memory`,
   `warn_plan_persistence`, and `no_shadow_ledger` with no per-repo wiring at all.
   **Reaches all fleet members and all adopters.**
3. **Code vendored into livespec core's plugin** —
   `.claude-plugin/scripts/_vendor/livespec_runtime/`. Ships to every repository
   that installs the `livespec` plugin. **Reaches all fleet members and all
   adopters**, and is how correct default BEHAVIOUR (as opposed to a guard) gets
   to an adopter.
4. **The copier scaffold channel** — `templates/orchestrator-plugin/`, per
   `SPECIFICATION/non-functional-requirements.md` §"Shared content sync — copier
   template". Static scaffolding flows to template-born repos; drift surfaces via
   CI's `copier update --dry-run --vcs-ref=master` check. Reaches template-born
   repos at scaffold time plus drift-reporting.

Note for anyone reading the older precedent: ledger item `livespec-gcp2` cites
this channel as `templates/impl-plugin/`. That path no longer exists — the tree
now carries `templates/orchestrator-plugin/`, which is what
`non-functional-requirements.md` names. Cite the current path.

A fifth channel — `livespec-dev-tooling` checks running in `just check` — reaches
fleet members only, because adopters do not run the fleet's `just check`.

## The reframing that changes the epic: this is a Conformance-Pattern concern

`SPECIFICATION/non-functional-requirements.md` §"Conformance Pattern" already
records the fleet's single repeatable recipe for keeping a cross-cutting
operational policy consistent and provable across every governed repository, and
it binds a hard rule: **"Reuse the Conformance Pattern spine; never fork it"** —
new dimensions are added as new obligation rows in the shared table, "NEVER as a
parallel mechanism."

So the three-layer structure this thread's epic was originally filed with must be
re-expressed in the pattern's five slots. Per the spec, **a concern is not adopted
until all five slots are filled**:

| Slot | Definition (spec) | This concern |
|---|---|---|
| **Contract** | the normative invariant, stated once, spec-side | **NOT YET FILED — see gap below** |
| **Mechanism** | the one canonical executable that satisfies it | the chokepoint GitHub client (`livespec-runtime-lzq`) |
| **Installer** | the idempotent `just` recipe that puts the Mechanism in place | Driver hook manifest registration (`livespec-driver-claude-6xj`) plus the governed-repo lifecycle reconcile |
| **Verifier** | the mechanical, fail-closed check wired into `just check` | the AST ban (`livespec-dev-tooling-t2q4`), plus its fleet-conformance sweep mirror |
| **Exemption** | the explicit, declared opt-out for legitimate variation | the token-mint module's documented `urllib` use; a declared severity lever |

**The gap this analysis surfaced: the Contract slot is empty.** No spec amendment
states the normative invariant. Under the five-slot rule the concern is therefore
not adopted, no matter how many slices land. Filing that amendment against
`SPECIFICATION/non-functional-requirements.md` via `/livespec:propose-change` is
the thread's next planning action.

## How the No-Circular-Dependency Directive actually resolves here

An earlier pass concluded that a conformance check verifying adopter wiring was
both banned and unnecessary. The first half is right and the second half was
imprecise; record the correction so it is not re-derived.

**Banned, correctly.** Per `.ai/no-circular-dependency.md` (maintainer-declared
2026-07-12), `livespec-dev-tooling` is canonical UPSTREAM and every adopter is
DOWNSTREAM. A check living in `livespec-dev-tooling` that reads an adopter's
committed `.claude/settings.json` is exactly the banned shape — the upstream
repository's CI would have to fetch a downstream repository to run it, and that
fetch IS the cycle.

**But a Verifier is not thereby unnecessary — it has a sanctioned home.** The
fleet-conformance sweep described in §"Fleet membership contract" already iterates
fleet members plus opt-in adopters and already carries `posture`-based exemption
machinery. That is where a cross-repo Verifier legitimately lives. The correct
statement is therefore: the Verifier belongs in the existing sweep inventory, NOT
in a new bespoke check inside `livespec-dev-tooling` reading downstream.

Separately, the directive's PREFERRED resolution (design the drift away rather
than add the Nth guard) still applies to the Installer slot and is genuinely
satisfied: once the guard ships in the Driver's own hook manifest, no repository
holds per-repo wiring, so no per-repo state CAN drift. The 4-of-4 versus 0-of-3
split is a property of the per-repo `.claude/settings.json` path specifically and
cannot arise on the plugin path.

Note also that the directive puts LEDGER records out of scope entirely: work-item
dependencies may point in either direction across repos. Cross-tenant links in
this thread are prose only because beads cannot resolve a foreign-tenant id
(`bd-ib-dvmh`), never because of the directive.

## Relationship to the pre-existing ledger items

- **`livespec-j49m`** (P1, `livespec` tenant) — the fleet App installation's
  5,000/hour `core` budget as a finite shared resource across the 9 fleet repos,
  observed fully exhausted, with consumption unattributable after the fact. Its
  disposition is **MEASURE BEFORE MITIGATING**. This thread honours that by
  ordering the Mechanism's measurement/attribution half FIRST. The key insight
  reconciling the two: `livespec-j49m` records that GitHub "does not attribute
  primary-limit consumption per endpoint or per caller" — true of GitHub's
  accounting, but the reason no caller is identifiable IN THIS FLEET is that calls
  originate from many independent call sites. A chokepoint client makes
  attribution structural, so the Mechanism is the VEHICLE for that item's
  acceptance rather than a competing mitigation.
- **`livespec-j5i9`** (P1, `livespec` tenant) — the enforcement-drift class the
  4-of-4-versus-0-of-3 measurement is a fifth instance of.
- **`livespec-gcp2`** (P1, `livespec` tenant) — the direct precedent: enforcing
  red-green-replay across fleet AND adopters. Its resolution is the template to
  copy — a core policy statement in `non-functional-requirements.md`, wiring in
  each Driver, and adopter coverage through the copier scaffold. It also records
  that the mechanical fleet-wide Verifier belongs to the Conformance Pattern's
  Verifier slot rather than to a bespoke check, which is the same conclusion this
  thread reached independently.

## Why a 403 must never be read as a negative result

Both the triggering incident and `livespec-j49m` produced this lesson
independently, which is why it is recorded as a design constraint rather than an
implementation note.

A rate-limited read returns 403. Code that treats that as "no results" reports a
confident false negative. `livespec-j49m` records a bucket reading healthy 68
seconds after exhaustion, so an after-the-fact check finds nothing wrong. The
incident's prune script would have printed `DONE deleted=0 failed=0` having read
nothing, with its safety guard passing vacuously over an empty list — the guard
was strongest-looking exactly when it was proving nothing.

Every consumer of the Mechanism MUST therefore receive a three-valued outcome —
OK / EMPTY / UNMEASURABLE — with UNMEASURABLE aborting, never collapsing to a
falsy empty collection. Per this repository's error conventions these are EXPECTED
failures (external, retryable) and belong on the `Result` failure track rather
than being raised.

Distinguishing the two 403 shapes matters, and `livespec-j49m` records the test: a
PRIMARY exhaustion zeroes `x-ratelimit-remaining`; a SECONDARY limit also returns
403 but carries a secondary-limit message body and does NOT zero `remaining`. A
malformed or expired credential returns 401, not 403.

This is the same discipline as `.ai/verifying-against-the-right-source.md`, and
that file should gain an entry for it. A worked instance occurred while filing
this thread's epic: a ledger dedup sweep was run with `bd list --search`, which is
not a real flag. It returned nothing for all seven queries, which would have
supported a confident "no duplicates exist" conclusion and a duplicate filing over
`livespec-j49m`. The real flag is `--desc-contains`.

## Deliberately out of scope

- Purchasing or requesting a higher limit — established above as unavailable.
- Per-tenant App installations — already recorded on `livespec-j49m` as a
  post-measurement mitigation; it stays there rather than being duplicated here.
- Anything that would lint or constrain an adopter's own first-party code. Per
  `SPECIFICATION/non-functional-requirements.md` §"Boundary" this is fleet
  self-application infrastructure, and per the repository's extension-author rule
  livespec imposes nothing on user-provided extension code beyond the calling-API
  contract.
