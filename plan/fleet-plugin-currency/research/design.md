# Phase 4 design — the fleet plugin-currency guarantee (FINAL)

> **STATUS: FINAL (2026-07-03).** Supersedes `design-draft.md`. The Phase 4
> maintainer design review PASSED; the D1 mechanism was revised to a
> verify-first "release-branch marketplace-ref" path and that path is now
> **VERIFIED empirically on BOTH runtimes** (Claude Code 2.1.199 + Codex
> 0.142.5) — experiment log at
> `tmp/fleet-plugin-currency/scratch/ref-exp/ref-experiment-log.md`. This
> document is the design Phase 5 implements against.

## Plain-language summary

We make plugin staleness **impossible to be silent** and we deliver the
research-plan's ORIGINAL invariant natively — "latest *released* pin," not a
watered-down "master HEAD." Three layers stack, each catching a regression of
the one below so no single failure is silent:

- **L0 — Release permanence.** Every `feat:`/`fix:` push must actually *become
  a release*. Today the release train is parked (the auto-merge gate skips the
  release-bot's PRs), so "latest release" silently lags master. We fix the
  gate and add a backstop that fails loud if a release PR ever ages open again.
- **L1 — Currency.** Each plugin repo carries a `release` branch that CI
  fast-forwards to every release tag; the fleet marketplaces register *at that
  ref*; and every surface's updater pulls the ref, not the default branch. A
  freshly-started session lands the latest released build before its first
  prompt, and the one-session apply lag is closed with a `/reload-plugins`
  nudge.
- **L2 — The gate.** A hard fail-loud chokepoint inside core's `_bootstrap.py`
  (a structural sibling of the credential self-heal) refuses to run any
  `/livespec:*` operation on a build older than the marketplace clone's
  pinned-ref tip, naming the exact fix command. It ships *inside core's
  plugin*, so it reaches every repo and both runtimes (interactive Claude,
  `codex exec`) with no per-repo adoption. It is offline-tolerant: both the
  running build id and the expected build id are read from disk.

The mechanism is built almost entirely from primitives we already control — a
CI-maintained branch, the existing `ensure-plugins` recipe, the existing
`_bootstrap.py` chokepoint, the existing marketplace registration surface. The
one genuinely new code artifact is a small `currency.py` pure decision brain
(mirroring the existing `credentials.py`); the rest is a per-repo `release`
branch, one reusable CI workflow, marketplace re-registration, and two
structural checks.

## The invariant (research-plan's original, delivered natively)

> Every NEW session, in EVERY fleet repo, on EVERY surface (interactive Claude
> Code, `codex exec`; Fabro is a separate docker-pin axis — see Out of scope),
> runs the LATEST RELEASED pin of EVERY livespec-ecosystem plugin, with a
> coherent cache; a `/livespec:*` operation that would run an older build FAILS
> LOUDLY naming the fix.

"Latest released pin" = the newest release-tag artifact per the fleet's
release-pin discipline (release-please cuts a release on every `feat:`/`fix:`
push; a release carries release-gate validation — mutation testing, full
heading coverage — that per-commit `just check` skips). The `release` branch is
the mechanism that makes "latest release tag" a *fetchable ref* the marketplace
tooling can pin to; L0 keeps that ref close to master by keeping the release
train unparked. This resolves the invariant-inversion the handoff flagged
(Finding A): with the train unparked, the pinned release is never the broken
build, because every `feat:`/`fix:` fix reaches a release promptly.

The invariant is verifiable **offline** — after the SessionStart hook's fetch,
both the running snapshot's build id and the marketplace clone's pinned-ref tip
are on disk — which is what makes the Layer-2 gate cheap and network-tolerant.

---

## Decisions record

### D1 — release-branch marketplace-ref mechanism (VERIFIED, both runtimes)

**Decision:** each livespec plugin repo carries a `release` branch that CI
fast-forwards to every release tag; the fleet marketplaces register *at that
ref*; and the gate compares the running build against that ref's tip. This is
the maintainer-approved "verify-release-branch-ref-first" path, and the
verification **succeeded**.

**Path to this decision:**

1. The draft first concluded tag-tracking was *unsatisfiable* and redefined
   "current" down to master HEAD.
2. A docs check refuted that: Claude Code catalog plugin entries *appear* to
   support `ref`/`sha`. The maintainer accepted a corrected D1 = "SHA-pin
   catalog entries to release commits."
3. **That was REFUTED empirically** (Claude Code 2.1.199;
   `tmp/fleet-plugin-currency/scratch/experiment-log.md`): a `github` plugin
   source *validates* `commit`/`branch`/`path` but the shipped installer
   **silently ignores all three**, always installing default-branch HEAD;
   `git-subdir` sources are runtime-rejected ("source type your Claude Code
   version does not support"). The docs describe a capability the runtime does
   not deliver. An upstream docs-vs-behavior report was filed (**c1k9.7**).
4. The maintainer then revised D1 to **verify the release-branch
   marketplace-ref path first**, with a master-HEAD fallback if it too failed,
   and extended the invariant's scope to the **Codex** driver path.
5. **That verification SUCCEEDED on both runtimes.** The marketplace-level ref
   pin (as opposed to the plugin-entry-level sha pin that was refuted) *is*
   honored, because the fleet plugins use RELATIVE (`./.claude-plugin`) plugin
   sources that resolve *inside* the ref-pinned marketplace clone.

**The verification verdicts** (from
`tmp/fleet-plugin-currency/scratch/ref-exp/ref-experiment-log.md`; method: a
local two-branch repo served over smart-HTTP — `release` = the pinned branch,
`master` = a trap the pin must never select):

*Claude Code (Target A):*

- **A1 — `marketplace add <git-url>#<ref>` registers the clone AT the ref → YES.**
  `known_marketplaces.json` persists `{ "source":"git", "url":"…", "ref":"release" }`;
  the clone HEAD sits at the release tip, single-branch shallow (only
  `origin/release` fetched).
- **A2 — `marketplace update` keeps the clone pinned to the ref, not default
  HEAD → YES.** Advancing both branches then updating fast-forwarded the
  *pinned ref's* new tip; it did NOT jump to master.
- **A3 — `plugin update` for a RELATIVE-source plugin resolves clone-at-ref →
  YES (decisive).** Because the plugin source is `./.claude-plugin`, it
  resolves *inside* the ref-pinned clone; install and update both track the
  release ref tip; master content was never selected.
- **A4 — cache naming + `gitCommitSha`.** `gitCommitSha` ALWAYS equals the
  resolved clone HEAD = the pinned ref tip (never master). (Cache-dir naming is
  version-keyed on install, sha-prefix-keyed on update — a minor upstream
  inconsistency, mitigated by reading `gitCommitSha` from the registry rather
  than parsing the dir name; see L2.)

*Codex (Target B):*

- **B1 — today's Codex livespec marketplaces carry NO `ref` key**, so they
  track the default branch snapshotted at `last_revision`; there is NO startup
  auto-update (the clone holds until an explicit `marketplace upgrade`).
- **B2 — `marketplace add <src> --ref release` persists a first-class ref →
  YES.** `config.toml` writes `ref = "release"`; the clone tracks
  `origin/release`, not master.
- **B3 — the release-branch mechanism works for Codex → YES.**
  `marketplace upgrade` alone refreshes the served plugin content to the
  release tip (no re-add needed), never selecting master.

**Decisive answer (verbatim from the log):** *"Release-branch MARKETPLACE-ref
pinning is VIABLE on BOTH runtimes for RELATIVE-source (`./.claude-plugin`)
plugins — which is exactly how the real livespec plugins are declared."* This
is the clean mechanism the plugin-entry-sha-pin experiment could not find.

### D2 — Stale hard-fails; Unknown warns with a fail lever

**Decision:** a confirmed-**Stale** build (running id known, expected id known,
they differ) ALWAYS fails hard — the `/livespec:*` op refuses to proceed,
naming the exact fix. An **Unknown** verdict (marketplace clone absent /
offline / an unpinned-transition state / a legacy snapshot whose id can't be
resolved) warns loudly to stderr and proceeds, under one self-documenting env
lever `LIVESPEC_CURRENCY_GATE=warn|fail` (default `warn`). CI and factory
dispatch set `LIVESPEC_CURRENCY_GATE=fail`, so Unknown fails hard there. This is
the established "carve-out is a severity lever, not an invariant relaxation"
pattern — the check is always wired and always invoked; only its severity on
the un-determinable case is levered.

### D3 — Host-level pre-session sweep DEFERRED

**Decision:** do NOT provision a host daemon (systemd timer / `claude` launch
wrapper) that pre-updates every governed repo before any session starts. Rely
on the uniform SessionStart hook + the `/reload-plugins` nudge + the hard gate.
Rationale: a host daemon is itself a *new unmanaged surface* that can silently
break, reintroducing the exact failure mode one layer down; it violates "prefer
primitives / ≤2 new artifacts"; and the hard gate makes it non-load-bearing
(staleness cannot be silent even if a timer is absent or broken). Revisit only
if operational data shows the `/reload-plugins` lag is painful.

---

## Mechanism, per layer

### L0 — Release permanence (feeds livespec-c1k9.1)

Three parts: the auto-merge fix, the fleet audit, and a park-staleness backstop.

**L0a — auto-enable-merge: shape-guarded release-PR path (not a bare allowlist
add).** The current gate
(`.github/workflows/auto-enable-merge.yml`) is:

```yaml
if: >-
  github.event.pull_request.draft == false
  && contains(fromJSON('["thewoolleyman"]'), github.event.pull_request.user.login)
  && !contains(github.event.pull_request.labels.*.name, 'do-not-merge')
```

The App bot `livespec-pr-bot` is not in the allowlist, so release-please PRs are
skipped and sit open until a human merges — that manual cadence lapsed after
~Jun 30, parking the train fleet-wide (Finding A). Add a SECOND `||` clause that
matches release-please PRs specifically:

```yaml
if: >-
  github.event.pull_request.draft == false
  && !contains(github.event.pull_request.labels.*.name, 'do-not-merge')
  && (
       contains(fromJSON('["thewoolleyman"]'), github.event.pull_request.user.login)
    || (
         github.event.pull_request.user.login == 'livespec-pr-bot[bot]'
         && startsWith(github.event.pull_request.head.ref, 'release-please--')
       )
     )
```

Guards: **author == the App bot** AND **release-please branch shape**
(`release-please--*`; title `chore(main): release *` is an equivalent guard)
AND the existing `do-not-merge` opt-out. This scopes the App bot's auto-merge
grant to release automation only — an arbitrary App-bot PR still would not
auto-merge. A bare allowlist add grants the App auto-merge on *any* PR it opens;
the shape guard costs ~4 lines and removes that surface. **Update the header
rationale block** (the "Author allowlist (initially)" comment) to document why
the App bot is trusted for release-please PRs specifically. This workflow ships
from `templates/orchestrator-plugin/.github/workflows/auto-enable-merge.yml.jinja`,
so the fix lands in the template AND is backfilled into each of the four plugin
repos (core, orchestrator, driver-claude, driver-codex) — verify per-repo (the
fleet is non-uniform).

**L0b — fleet audit.** `release-please.yml` + `auto-enable-merge.yml` live in
the four **plugin** repos (they cut plugin releases). Impl/console repos
(console, dev-tooling, runtime, git-jsonl) do not cut plugin releases and are
out of scope for the release-PR fix. The fleet audit already showed all four
plugin repos carrying open App-bot release PRs — all four need the fix.

**L0c — park-staleness backstop: `reusable-release-park.yml` (dev-tooling).**
The existing `pin-freshness.yml` guards *pin* staleness (are we consuming a
stale release), NOT release-*park* staleness (is there an unmerged release PR /
unreleased `feat`/`fix` commits) — a different question. Add a NEW reusable
workflow in `dev-tooling` mirroring the pin-freshness pattern (daily cron +
`workflow_dispatch`, one shim per plugin repo `uses:` it). Per plugin repo it
FAILS LOUDLY (fails the scheduled job → red on the Actions tab, and/or opens a
tracking issue) when EITHER an open `release-please--*` PR is older than a
threshold OR master carries `feat`/`fix` commits newer than the latest release
tag beyond the threshold. It does NOT auto-merge — that is L0a's job; this is
the backstop that catches a *regression of L0a* so "the release train parked"
can never again be silent. It rides the same daily schedule + reusable-workflow
convention pin-freshness establishes, so it is one justified new artifact, not a
new pattern.

### L1 — Currency mechanism (updates land before the session exists)

**L1a — each plugin repo carries a CI-fast-forwarded `release` branch.** Add to
each of the five plugin repos a CI step that, on every release tag, fast-forwards
a long-lived `release` branch to that tag's commit. (The five are core,
driver-claude, driver-codex, orchestrator-beads-fabro, and
orchestrator-git-jsonl — git-jsonl also ships release-please + a plugin
marketplace, so it carries the release branch too.) The natural home is the
existing release workflow (`release-tag.yml` / the release-please tag event):
after a release is cut, push `release` → the new tag. `release` therefore always
points at the latest release-tag commit — the fetchable ref the marketplaces
pin to. (Verified in the experiment as the pinned branch the clone tracks;
`marketplace update`/`upgrade` fast-forwards it — A2/B3.)

**L1b — fleet marketplace registrations pin the ref.** Re-register every fleet
marketplace *at* `release`:

- **Claude:** the ref is embedded in the source string — a git URL takes
  `…#release`, and the `github` shorthand takes `github@release` (there is NO
  `--ref` flag on `claude plugin marketplace add`; the ref lives in the source
  string). The ref persists in `known_marketplaces.json` as
  `{ "source":"git", "url":"…", "ref":"release" }` (A1). **Settings-declared
  `extraKnownMarketplaces`** (the committed project-scope
  `.claude/settings.json` form the fleet uses) must ALSO carry the ref — the
  implementer verifies the settings-schema shape for a ref-bearing marketplace
  source and updates every governed repo's committed settings + the CLAUDE.md
  install snippet accordingly.
- **Codex:** `codex plugin marketplace add <src> --ref release` (first-class
  `--ref` flag; persists `ref = "release"` in `config.toml` — B2).

**L1c — uniform SessionStart `ensure-plugins` hook + close the one-session
lag.** Two fixes to the existing primitive, no new daemon:

- **(i) Make the hook uniform fleet-wide.** It ships from
  `templates/orchestrator-plugin/.claude/settings.json`. Backfill it into the
  repos that lack it (console, dev-tooling, driver-claude, driver-codex,
  runtime — the five missing repos), and add a doctor / dev-tooling
  **presence check** that asserts each governed repo's `.claude/settings.json`
  carries the SessionStart `ensure-plugins` hook, so a repo that loses or never
  adopts it FAILS LOUDLY instead of silently never updating. Adoption is
  distributed by the template and enforced by a check, never left to per-repo
  memory. **Gotcha (rollout surprise 4):** the hook's `plugin update` leg must
  pass `--scope project` (the fleet uses committed project-scope installs);
  `plugin update` defaults to `--scope user`, which yields a confusing "not
  installed at scope user" and never moves the project-scope pointer.
- **(ii) Close the one-session lag (feeds livespec-c1k9.2).** Today
  `ensure-plugins` fetches, but the flip applies only next session (H1). Enhance
  the recipe so that AFTER the `install`/`update` leg it detects whether any
  active-snapshot pointer moved (diff the project-scope entries of
  `installed_plugins.json` pre/post) and, if so, emits a loud
  `hookSpecificOutput.additionalContext` + `systemMessage`: *"livespec plugins
  updated to <sha>; run `/reload-plugins` to apply in THIS session (otherwise it
  runs the previous build)."* This uses the documented mid-session-apply
  primitive to shrink the lag from "next session" to "one `/reload-plugins`,"
  with no restart and no new artifact. It is **soft** (the model must choose to
  run it) — which is exactly why it pairs with the **hard** Layer-2 gate that
  refuses to *proceed* stale.

**L1d — Codex leg (feeds livespec-c1k9.4).** Codex has no SessionStart-hook
analogue (host-wide `~/.codex/config.toml`), and — critically — it does NOT
self-refresh: the marketplace clone holds its snapshot until an explicit
`codex plugin marketplace upgrade` (rollout surprise 5). So the fleet currency
job for Codex must:

- register each marketplace with `--ref release` (L1b), and
- **explicitly RUN `codex plugin marketplace upgrade`** on the currency path
  (host-level periodic refresh, maintainer-side host provisioning, in the same
  class as the documented Beads-runtime prerequisites). `marketplace upgrade`
  alone refreshes the served plugin content to the release tip — no re-add
  needed (B3).

Honest posture: Codex currency is *weaker* than Claude's (no per-project session
hook) and **deliberately leans on the shared gate** (L2 fires on `codex exec`
for free) rather than inventing a Codex session-hook mechanism Codex does not
offer.

### L2 — The fail-loud staleness gate (feeds livespec-c1k9.3)

**The chokepoint: a currency decision in core's `bin/_bootstrap.py`, a
structural sibling of the credential self-heal.** Every `/livespec:*` op on both
runtimes shells a `bin/*.py` wrapper → `bootstrap()`; `codex exec` drives the
same wrappers. A gate there covers interactive Claude AND Codex from one code
site with no per-repo adoption. (Fabro does NOT reach it — its `implement.md`
invokes `just check`, never a `/livespec:*` skill — which is why Fabro is a
separate axis; see Out of scope.) It mirrors the credential self-heal's shape
exactly (pure brain + thin impure performer), keeping it exhaustively testable.

**L2a — pure brain `currency.py` (the ONE genuinely new code artifact).** Pure,
no I/O, never raises, discriminated `Literal`-keyed union — copy the
`CredentialDecision` shape verbatim:

```python
CurrencyDecision = Current | Stale | Unknown   # kind: Literal["current"|"stale"|"unknown"]

def decide_currency(*, running_build_id: str, expected_build_id: str | None,
                    plugin_name: str, update_hint: str) -> CurrencyDecision: ...
```

- `Current` — `running_build_id == expected_build_id` → proceed (no-op).
- `Stale` — both known and differ → carries an actionable `message` naming the
  plugin, the running vs expected SHA, and the exact fix (`/reload-plugins`, or
  `mise exec -- just ensure-plugins` then restart; for Codex,
  `codex plugin marketplace upgrade`).
- `Unknown` — `expected_build_id is None` (marketplace clone absent, or a
  running dir whose SHA can't be derived) → not determinable; the performer
  applies the D2 severity lever.

**L2b — impure performer wired into `bootstrap()`.** At the tail of
`bootstrap()` (where the orchestrator calls `_self_heal_credentials()`), a
`_verify_currency()` gathers the live inputs and performs the prescribed act:

- **`running_build_id`** = the running plugin's `gitCommitSha`, read from
  `installed_plugins.json` by matching the entry whose `installPath` ==
  `${CLAUDE_PLUGIN_ROOT}`. This is the robust source: A4 showed the running
  build's `gitCommitSha` ALWAYS equals the resolved clone HEAD (the pinned ref
  tip), whereas the cache *dir name* is version-keyed on install and
  sha-prefix-keyed on update — so parse the registry field, not the path
  basename. Fall back to the path basename only when it is a 12-hex SHA dir; if
  neither resolves → `Unknown`.
- **`expected_build_id`** = `git -C ~/.claude/plugins/marketplaces/<marketplace>
  rev-parse HEAD` (short) — read **from disk, no network**. Because the
  marketplace clone is ref-pinned (D1), its HEAD IS the `release`-branch tip =
  the latest release-tag commit (A1/A2). This is the corrected comparison
  target: the draft compared against master HEAD; the FINAL design compares
  against the **pinned-ref (release) tip**. This is why L1's ref-pinned fetch is
  a genuine prerequisite for the gate's precision — the two layers are
  complementary.
- On `Current` → return. On `Stale` → `sys.stderr.write(message)` +
  `raise SystemExit(<code>)` (a stale op *refuses to proceed*). On `Unknown` →
  D2 severity lever (`LIVESPEC_CURRENCY_GATE=warn|fail`, default `warn`).

`${CLAUDE_PLUGIN_ROOT}` and the marketplace-clone path are read from env / a
fixed `~/.claude/plugins/marketplaces/<name>` location; both tolerate absence
(→ `Unknown`, never a crash), mirroring `_read_credential_wrapper()`'s
fail-open.

**L2c — SessionStart-hook gate variant: the SAME brain, soft site.** The
SessionStart hook enhancement in L1c(ii) is the *soft* invocation of the same
`decide_currency` brain: at session start it compares and injects a loud
`additionalContext`/`systemMessage` (+ the `/reload-plugins` instruction) if
`Stale`. So the gate lives at **two sites, one brain** — soft at session start
(drives the reload before any op), hard at the CLI chokepoint (refuses to run
stale). No third artifact.

**L2d — negative test (Phase 5 exit gate).** Unit-test `decide_currency`
exhaustively (Current/Stale/Unknown across matching/differing/None inputs).
Integration-test the performer by pointing `${CLAUDE_PLUGIN_ROOT}` at a
deliberately-old snapshot (or a scratch marketplace clone whose pinned-ref HEAD
differs) and asserting a `/livespec:*` invocation exits non-zero with the
diagnostic naming the fix; assert the `Unknown` lever warns by default and fails
under `LIVESPEC_CURRENCY_GATE=fail`.

### Structural guards

- **Relative-source check (NEW).** The ref-pinning mechanism hinges on every
  fleet catalog plugin `source` staying RELATIVE (`./.claude-plugin`) — a
  `github`-TYPE plugin source silently ignores the pin and clones default HEAD
  (rollout surprise 3; the refuted sha-pin experiment proved the silent-ignore).
  Add a check (doctor / dev-tooling) asserting every fleet catalog's
  `plugins[].source` is a relative `./…` path, failing loud if any entry ever
  switches to a `github`/`git`/`git-subdir` type — which would silently break
  ref pinning.
- **Hook-presence check (NEW).** Per L1c(i): assert each governed repo's
  `.claude/settings.json` carries the SessionStart `ensure-plugins` hook.
- **Cache-dir ambiguity — mitigated by mechanism, plus an upstream report.**
  Claude's version-vs-sha cache-dir naming inconsistency (A4) is mitigated by
  the L2b design decision to read `gitCommitSha` from the registry rather than
  parse the dir name — so the gate is immune to the naming ambiguity. The
  separate upstream *pin-fields-silently-ignored* defect (the refuted sha-pin
  experiment: `github` plugin sources validate `commit`/`branch`/`path` but the
  installer ignores all three) is captured in the upstream docs-vs-behavior
  report (**c1k9.7**, already filed).

---

## Out of scope

- **Fabro sandbox.** Fabro resolves NO host plugins: fresh clone + pinned docker
  image (`sha-ea684ad`) + `uv.lock` pins. Its `implement.md` invokes `just
  check`, never a `/livespec:*` skill, so the `_bootstrap.py` gate never fires
  there and would be meaningless. Fabro's currency axis is entirely the
  **docker-image pin under `bump-pin` discipline** — cross-tenant item
  **bd-ib-mwz** (bring `sha-ea684ad` under the pin-autodiscovery formats). Do
  NOT design plugin machinery for Fabro; keep its slice scoped to bd-ib-mwz so
  Phase 5 does not accidentally widen it.
- **openbrain.** The adopter repo is intentionally `posture: "pinned"`; its
  stale snapshot is a deliberate adopter choice, not a defect. RESPECT it — it
  is out of scope for the currency fix and must not be "helpfully" updated.

---

## Rollout gotchas (carried verbatim-faithfully from the ref-experiment log)

These five surprises from
`tmp/fleet-plugin-currency/scratch/ref-exp/ref-experiment-log.md` §"Surprises
affecting rollout" bind Phase 5:

1. **Claude REJECTS `file://` and does SHALLOW clones** — a real registry needs
   a fetchable git URL (github owner/repo or https) serving smart-HTTP; a bare
   local dir won't even test ref. (Implication: the `release` branch must be a
   real pushable branch on the real GitHub remote; there is no local-path
   shortcut for the pinned ref.)
2. **`impl-plaintext` HEAD was renamed to `livespec-orchestrator-git-jsonl`**
   (a name collision with a live marketplace) — do NOT register impl-plaintext
   at/near HEAD. (Relevant only if any rollout step touches that marketplace.)
3. **The mechanism hinges on the plugin `source` being RELATIVE
   (`./.claude-plugin`).** A `github`-TYPE plugin source still ignores pins
   (prior experiment) and clones default HEAD. livespec uses relative sources,
   so it's fine — but any future switch to a github-type plugin source would
   silently break ref pinning. (Enforced by the relative-source structural
   check above.)
4. **Claude `plugin update` defaults to `--scope user`;** the fleet's committed
   project-scope installs require `--scope project` (or local) on update, else a
   confusing "not installed at scope user". (The `ensure-plugins` hook must pass
   the matching scope.)
5. **Codex is HOST-WIDE (no project scope) and holds the snapshot until an
   explicit `marketplace upgrade`** — so a fleet currency job must RUN `codex
   plugin marketplace upgrade` (against the `release`-ref targets); it will not
   self-refresh.

---

## Work-item mapping

| Design piece | Item | Tenant | Disposition |
|---|---|---|---|
| L0a auto-enable-merge shape-guarded release-PR path + header rationale + 4-repo backfill | **livespec-c1k9.1** | core (fleet-wide) | re-groom to shape-guard form |
| L1c(ii) one-session-lag close: hook detects pointer move → `/reload-plugins` nudge | **livespec-c1k9.2** | core | resolution = reload nudge |
| L2 gate: `currency.py` brain + `_bootstrap.py` performer + negative test | **livespec-c1k9.3** | core | comparison target now the pinned-ref (release) tip |
| L1d Codex leg: `--ref release` + explicit `marketplace upgrade` on the currency path | **livespec-c1k9.4** | Codex/host | expand to the verified Codex mechanism |
| Cache-dir ambiguity | **livespec-c1k9.5** | core | mitigated by L2b registry-read; keep for cache-pruning posture |
| Contract codification | **livespec-c1k9.6** | core (SPECIFICATION) | single-source the invariant + gate guarantee in core `non-functional-requirements.md`; mechanical enforcement (the two structural checks) per repo |
| Upstream docs-vs-behavior report (pin fields silently ignored) | **livespec-c1k9.7** | upstream | filed |
| SessionStart hook backfill (5 missing repos) | **console-vfd** + `driver-claude-nm9` / `driver-codex-045` / `dev-tooling-6da` / `runtime-m2u` | cross-tenant | L1c(i) rollout |
| Fabro docker-image pin under bump-pin | **bd-ib-mwz** | orchestrator (Fabro) | Out of scope for plugin machinery |

**NEW items to file (next session):**

- **Per-plugin-repo `release` branch + CI fast-forward** (L1a) — one item per
  the four plugin repos (or a core-anchored epic slice with per-repo children).
- **Marketplace ref-pin re-registration rollout** (L1b) — re-register every
  fleet marketplace at `release`; update committed `.claude/settings.json`
  `extraKnownMarketplaces` in every governed repo + the CLAUDE.md install
  snippet + the Codex `--ref release` registrations.
- **Release-park guard** (L0c) — `reusable-release-park.yml` in `dev-tooling` +
  per-repo `uses:` wiring in the four plugin repos.
- **Relative-source structural check** (Structural guards) — doctor /
  dev-tooling check asserting every fleet catalog `plugins[].source` is a
  relative `./…` path.
- **Codex `marketplace upgrade` step in the currency path** (L1d) — the
  host-level periodic refresh that runs `codex plugin marketplace upgrade`
  against the ref targets.

---

## Verification plan (Phase 5 exit — closes the epic)

1. **Release train unparked (L0):** all four plugin repos' release PRs
   auto-merge on green (observe one cycle each); `reusable-release-park.yml`
   goes green (no parked PR, no unreleased backlog).
2. **`release` branch tracks the latest release tag (L1a):** per plugin repo,
   `git rev-parse release` == the latest release-tag commit after a release
   cycle.
3. **Uniform currency (L1c):** every governed repo's `.claude/settings.json`
   carries the SessionStart `ensure-plugins` hook (and the relative-source +
   hook-presence checks pass fleet-wide).
4. **Positive assertion (mechanized, every repo × surface):** a script that,
   per governed repo, resolves each livespec-ecosystem plugin's running-snapshot
   `gitCommitSha` and asserts **running `gitCommitSha` == the marketplace
   clone's pinned-ref (release) tip == the latest release tag** — for
   interactive Claude AND `codex exec`. (Fabro asserted separately via its
   docker-image pin, not plugin snapshots.)
5. **Negative assertion (the hard proof):** deliberately stale a cache (point
   `${CLAUDE_PLUGIN_ROOT}` at an old snapshot, or a scratch marketplace clone
   whose pinned-ref HEAD is ahead of the snapshot) and assert a `/livespec:*` op
   exits non-zero with the diagnostic naming the fix; assert the `Unknown` lever
   warns by default and fails under `LIVESPEC_CURRENCY_GATE=fail`.
6. Both recorded in `handoff.md`; epic closed only on both.
