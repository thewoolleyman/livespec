# Phase 4 design — the fleet plugin-currency guarantee

> **STATUS: DRAFT — Phase 4 maintainer design review PENDING (2026-07-03).** Three maintainer decisions are open (recorded in `../handoff.md` §"The next action"); the design is not final until they are answered and this doc is revised to `design.md`. Do not implement from this draft.

## CORRECTION (2026-07-03) — catalog-level sha pinning IS supported; §1's premise is refuted

> **This correction section GOVERNS the rest of this draft.** §1 below (and the
> facts §0 leans on for it) was written from a premise the official Claude Code
> docs refute. Read this section first; where it conflicts with §1, this section
> wins. The rest of the draft is deliberately NOT rewritten — only §1's
> invariant *choice* changes; every other layer survives as drafted (see
> "Layers unaffected" below).

**Plain-language bottom line.** The draft concluded that Claude Code simply
*cannot* pin a plugin to a released version, so it redefined "current" down to
"whatever master HEAD happens to be." That conclusion is wrong. Claude Code
*does* support pinning a plugin entry in a marketplace catalog to an exact
commit — so the fleet CAN deliver the research-plan's original "latest
*released* pin" invariant natively, without redefining anything. The corrected
recommendation (D1, recorded in `../handoff.md` §"The next action") is
therefore: **SHA-pin every fleet catalog entry to the latest release-tag commit
and let CI auto-bump the pin on each release** — the same shape the fleet's
`bump-pin` discipline already uses for code pins.

### The facts (from the official docs at `code.claude.com/docs` — `plugin-marketplaces.md` §"Plugin sources" and `plugins-reference.md` §"Version management")

1. **Git-based PLUGIN-ENTRY sources support both `ref` AND `sha`.** A plugin
   entry in `marketplace.json` whose source is git-based (`github`, `url`, or
   `git-subdir`) accepts BOTH a `ref` (a branch or tag) AND a `sha` (a full
   40-character commit hash). When both are set, **`sha` wins** — "Claude Code
   fetches and checks out the pinned commit directly." This is the exact
   capability §1 claimed did not exist.
2. **MARKETPLACE sources support `ref` but not `sha`.** The source that says
   where the *catalog itself* is fetched from supports `ref` (branch/tag) but
   NOT `sha`. So the pin lives on the plugin ENTRY inside the catalog, not on
   the marketplace-of-the-catalog — and the plugin-entry level is exactly the
   level the fleet controls in its own committed `marketplace.json`.
3. **`plugin.json.version` is the consumer cache key.** Consumers re-fetch a
   plugin only when its `version` string changes. release-please bumps that
   `version` exactly at release commits, so a `sha` pin *at a release commit*
   composes cleanly with cache invalidation: the pin moves and the version
   string changes together, at the release, and consumers pick the new build up.
4. **Ecosystem precedent.** Anthropic's own community marketplace pins each
   approved plugin to a commit `sha` in the catalog, with CI bumping the pin
   automatically — precisely the pattern the fleet's `bump-pin` discipline
   already embodies for its code pins.
5. **Why the fleet doesn't get this today.** Every fleet catalog entry uses
   `"source": "./.claude-plugin"` — a *relative path*, which resolves to
   "whatever the marketplace clone has checked out," i.e. default-branch (master)
   HEAD. That is why master-HEAD tracking looked like the only option. The draft
   correctly verified the CLI surface (no pin flags on `claude plugin
   install`/`update` — still true) and the current catalog *shape* (relative-path
   sources — still true), but **missed the catalog *schema* fields** (`ref`/`sha`
   on git-based entry sources), which is where the pin actually lives.
6. **One capability still unverified (flagged, in flight).** Whether a
   `git-subdir` source combined with `sha` works end-to-end for a plugin rooted
   in a `.claude-plugin/` subdirectory (the fleet's layout) is being verified in
   a scratch experiment. The recommendation below depends on this; it is the one
   open capability check.

### What this changes

- **§1's invariant reconciliation (master-HEAD tracking) was derived from a
  false premise.** Its central claim — that the tooling *cannot express* the
  "latest released pin" because there is "no marketplace ref-pin, no
  install-at-tag" — is refuted at the catalog (plugin-entry) level. The
  two-axes table and the "master ≈ latest release is good enough" argument no
  longer decide the invariant.
- **The corrected D1 (recorded in `../handoff.md` §"The next action") now
  RECOMMENDS SHA-pinning catalog entries to release-tag commits with CI
  auto-bumping the pin.** This rides the existing `bump-pin` discipline (extend
  the freshness guard to cover a *parked* pin-bump, exactly as it already covers
  a parked code-pin) and **preserves the research-plan's ORIGINAL "latest
  *released* pin" invariant natively** — no redefinition of "current" required.

### Layers unaffected by this correction (they survive as drafted)

- **The fail-loud gate shape (§4).** The gate still fails loudly on a stale
  build; only its *comparison target* changes — from "the freshly-fetched
  marketplace-clone master HEAD" to "the catalog's pinned `sha`." That target is
  SIMPLER (a fixed value committed in the catalog, not a just-fetched moving
  HEAD) and STILL offline-verifiable (the pinned sha is on disk in the catalog).
- **Release permanence (§2).** Unchanged.
- **Hook uniformity (§3a).** Unchanged.
- **The reload-nudge (§3b).** Unchanged.
- **Fabro out-of-scope (§5).** Unchanged.
- **Cache hygiene.** Unchanged.

Everything below this section is the ORIGINAL draft, preserved for its
still-valid layers. Where §1 conflicts with this correction, this correction
governs.

---

**Plain-language bottom line.** We make plugin staleness *impossible to be
silent* with two layers that share one small pure decision brain, and we
redefine "current" to something the tooling can actually deliver. Layer 1
lands updates before/at session start on every surface that has a session
hook, using primitives already present (the `ensure-plugins` recipe + the
copier template + the documented mid-session `/reload-plugins` apply). Layer 2
is a hard fail-loud chokepoint in core's `_bootstrap.py` — a sibling of the
credential self-heal — that refuses to run any `/livespec:*` operation on a
build older than the freshly-fetched marketplace clone, naming the exact fix.
The gate ships *inside core's plugin*, so it reaches every repo and every
surface (interactive Claude, `codex exec`) automatically with no per-repo
adoption. The one genuinely new artifact is a `currency.py` pure brain
(mirroring `credentials.py`); everything else is wiring into existing files.

This document honors `research-plan.md` §"Design constraints (bind Phase 4)"
and reconciles the invariant-inversion the handoff flagged (Finding A).

---

## 0. Verified Claude Code capability facts (load-bearing — do not re-guess)

Confirmed against `code.claude.com/docs/en/plugins-reference`, `/hooks`, the
Phase 0 evidence, and live repo state. Each is load-bearing for a decision below.

1. **No git-ref pinning on a marketplace `github` source.** `{"source":"github",
   "repo":"owner/repo"}` has no `ref`/`branch`/`tag` field (confirmed:
   `evidence/04-known_marketplaces.json` carries only `source`+`repo`; the docs'
   github source schema exposes none). The marketplace clone tracks the repo's
   **default branch (master)**. There is **no way to point a marketplace at a
   release tag**.
2. **No native install-at-tag.** `claude plugin install <plugin>@<marketplace>`
   takes no version selector; you cannot install a chosen tag/version. (docs
   §CLI; `evidence/14-claude-plugin-cli.txt`.)
3. **`plugin.json.version` is the declarative cache-key / pin.** If set, the
   *passive/auto* update path skips when the version string matches ("already at
   the latest version"); if omitted, every commit is a new SHA-keyed version
   (docs §"Version management", lines 1201–1218). **But** an *explicit* `claude
   plugin update` (what the `ensure-plugins` recipe runs) force-fetches master
   HEAD and keys the snapshot dir by the **commit SHA** — this is why Jun30–Jul3
   updates produced SHA-named active pointers (`semantics.md` §1) even though
   every livespec plugin sets a `version`. *(Capability nuance: the passive-skip
   vs explicit-force distinction is inferred from doc text + live evidence, not a
   controlled scratch run; the design below does not depend on which path fires —
   it compares SHAs either way.)*
4. **release-please model ⇒ master.version ≡ latest-release.version between
   releases.** The version bump commit and the git tag both land at the release
   PR's merge, so master's declared `version` equals the newest release's version
   at all times; post-release `feat`/`fix` commits move master *content* ahead
   while the version string stays fixed until the next release merges. Verified:
   core master `plugin.json` = `0.6.0` (its current latest release), orchestrator
   = `0.4.0`. This is the root of the **semver-dir content-ambiguity trap**
   (`semantics.md` §2): a fresh `install` of a post-release master commit lands in
   dir `0.4.0` and collides last-writer-wins with the release-tag `0.4.0` content.
5. **`/reload-plugins` applies a plugin update MID-SESSION** for skills, hooks,
   MCP and LSP servers (monitors still need a restart) — docs line 637. This is
   the lever that closes the H1 one-session lag *without* a restart. A hook
   **cannot auto-run** a slash command; it can only inject text that instructs
   the model/operator to run it (docs §Hooks Q5).
6. **SessionStart hooks can inject context and warn, but cannot block.** Exit-0
   stdout and `hookSpecificOutput.additionalContext` are added to the session
   before the first prompt; `systemMessage` shows a warning to the operator.
   SessionStart is "Context only" — no block/deny (docs §Hooks Q1–Q3).
7. **PreToolUse and UserPromptSubmit hooks CAN block** (`permissionDecision:deny`
   / `decision:block`) and inject context — they fire before every tool call /
   prompt (docs §Hooks Q4). Available as a harder gate site if the CLI chokepoint
   is judged insufficient (it is not — see §4).
8. **The `_bootstrap.py` chokepoint is universal.** Every `/livespec:*` op on
   both runtimes shells a `bin/*.py` wrapper → `bootstrap()`; `codex exec` drives
   the same wrappers. A gate there covers interactive Claude **and** Codex from
   one code site. Fabro does **not** reach it (its `implement.md` invokes `just
   check`, never a `/livespec:*` skill — `semantics.md` §5), which is why Fabro is
   a different axis (§5).

---

## 1. The invariant, reconciled: what "current" targets

**Recommendation (maintainer decision #1): currency targets the freshly-fetched
marketplace-clone master HEAD, and the gate asserts running-snapshot SHA ==
marketplace-clone HEAD SHA. Keep the release train unparked so master ≈ latest
release; keep release-tag tracking ONLY on the separate code-pin axis
(`bump-pin`/`compat.pinned`), which is unaffected.**

Why the research-plan's literal "latest RELEASED pin" cannot be the plugin-
currency target as written:

- The tooling **cannot express it** (facts 1–2): no marketplace ref-pin, no
  install-at-tag. The only thing Claude Code installs is the marketplace default
  branch.
- Finding A **inverted it in practice**: during the release stall the latest
  release (orchestrator v0.4.0 = `06e3e080`) was the *broken, pre-self-heal*
  build; only **master** carried the fix. A literal release-tracking gate would
  have *delivered the broken build to the console* and blocked the working one.
- With c1k9.1 fixed (release train auto-merges on green; release-please cuts on
  every `feat`/`fix`), **master ≈ latest release** continuously. Master-tracking
  is therefore *never staler* than release-tracking and is *fresher* across the
  `refactor:`/`perf:` no-release seam — capturing fixes that cut no release.
  "Fresher than the last release" is not a staleness defect for the *interactive
  tool surface*; release-gate validation (mutation testing etc.) still governs
  the **code-pin** axis, which is a different mechanism and stays tag-based.

**The two axes are different and must not be conflated** — conflating them is
what made the stated invariant unsatisfiable:

| Axis | What it governs | Correct target | Mechanism |
|---|---|---|---|
| **Plugin currency** (this thread) | which build of the live `/livespec:*` skill surface an operator/agent runs | freshest coherent build the marketplace serves = **master HEAD** | marketplace clone + `ensure-plugins` + the gate |
| **Code-pin discipline** (unchanged) | which vendored-lib / docker-image version a repo's *code* depends on | **latest release tag** (carries release-gate validation) | `compat.pinned`, `bump-pin`, `pin-freshness.yml` |

So the operational invariant becomes:

> At session start, in every governed repo, on every surface with a session
> hook, the marketplace clone is freshly fetched and every livespec-ecosystem
> plugin's active snapshot resolves the marketplace-clone master HEAD; a
> `/livespec:*` op that would run an older snapshot FAILS LOUDLY naming the fix.

This is verifiable **offline** (both SHAs are on disk after the hook's fetch),
which is what makes the Layer-2 gate cheap and network-tolerant.

**Rejected alternative — make `plugin.json.version` the source of truth and drop
the explicit `update` leg (rely on the passive version-pin skip).** Tempting
because fact 3's passive path already "pins," but: (a) it pins to whatever
content first landed in the `version`-named dir — the semver-dir trap means that
can be *post-release master content*, not the release tag (fact 4), so the pin is
not even release-faithful; (b) it can't be verified without a SHA comparison
anyway; (c) it re-introduces exactly the silent-stale-content collision this
thread exists to kill. Keep the version field for release-please + human display;
let the plugin cache track SHA.

**Rejected alternative — drop `version` from `plugin.json` (commit-SHA
versioning, fact 3).** Cleanly makes every dir SHA-named and content-stable, but
breaks release-please's version management, the `plugin list` human-facing
version, and the code-pin discipline's release-tag references. Net loss.

---

## 2. Release-pipeline permanence (feeds livespec-c1k9.1)

Three parts: the auto-merge fix, the fleet audit, and a park-staleness backstop.

### 2a. auto-enable-merge fix — SELF-RESOLVED: shape-guarded release-PR path (not a bare allowlist add)

Current gate (`.github/workflows/auto-enable-merge.yml:75`):
```yaml
if: >-
  github.event.pull_request.draft == false
  && contains(fromJSON('["thewoolleyman"]'), github.event.pull_request.user.login)
  && !contains(github.event.pull_request.labels.*.name, 'do-not-merge')
```
The App bot `livespec-pr-bot` is not in the allowlist, so release-please PRs are
skipped and sit open (`fleet-audit.md` §Q1).

**Fix (self-resolved per "fix the gate correctly"): add a SECOND `if`-branch /
`||` clause that matches release-please PRs specifically**, rather than adding
the App bot to the general allowlist:

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
(`release-please--*`; title `chore(main): release *` is an equivalent guard) AND
the existing `do-not-merge` opt-out. This keeps the App bot's grant scoped to
release automation only — an arbitrary App-bot PR still would not auto-merge. A
bare allowlist add (`["thewoolleyman","livespec-pr-bot[bot]"]`) is simpler but
grants the App auto-merge on *any* PR it opens; the shape guard costs ~4 lines
and removes that surface. **Update the header rationale block** (the "Author
allowlist (initially)" comment) to document why the App bot is trusted for
release-please PRs specifically.

Fleet-wide: this workflow ships from `templates/orchestrator-plugin/.github/
workflows/auto-enable-merge.yml.jinja`, so the fix lands in the template AND is
backfilled into each of the four plugin repos (core, orchestrator, driver-claude,
driver-codex) — verify per-repo (fleet is non-uniform).

### 2b. Fleet audit — which repos carry the workflow + release-please

`release-please.yml` + `auto-enable-merge.yml` live in the four **plugin** repos
(they cut plugin releases). Impl/console repos (console, dev-tooling, runtime,
git-jsonl) do not cut plugin releases and are out of scope for the release-PR
fix. Confirm each of the four plugin repos carries the identical stalled gate
(`fleet-audit.md` §Q1 already shows all four with open App-bot release PRs — all
four need the fix).

### 2c. Park-staleness backstop — NEW reusable workflow (survey first: pin-freshness does NOT cover this)

Surveyed `pin-freshness.yml`: it runs daily (13:00 UTC), delegates to
dev-tooling's `reusable-pin-freshness.yml`, and opens bump PRs when a *consumed*
pin lags its source's latest **release tag**. That guards *pin* staleness (are we
consuming a stale release), **not** release-*park* staleness (is there an
unmerged release PR / unreleased feat/fix commits). Different question.

**Recommendation: a NEW `reusable-release-park.yml` in dev-tooling, mirroring the
pin-freshness pattern** (daily cron + `workflow_dispatch`, one shim per plugin
repo `uses:` the reusable). Per plugin repo it FAILS LOUDLY (fails the scheduled
job → surfaces red on the Actions tab, and/or opens a tracking issue) when
EITHER an open `release-please--*` PR is older than a threshold (e.g. 6h) OR
master carries `feat`/`fix` commits newer than the latest release tag by more
than the threshold. It does **not** auto-merge — auto-merge is 2a's job; this is
the backstop that catches *regression of 2a* so "the release train parked" can
never again be silent (the "enforce, don't hope" + "Layer-1 regression never
silent" constraints applied to the release pipeline itself). It rides the same
daily schedule and reusable-workflow convention pin-freshness already
establishes, so it is one justified new artifact, not a new pattern.

---

## 3. Layer 1 — currency mechanism (updates land before the session exists), per surface

### 3a. Interactive Claude Code — uniform SessionStart hook + close the one-session lag

Two fixes to the existing primitive; **no new daemon**.

**(i) Make the SessionStart `ensure-plugins` hook uniform fleet-wide (fixes H5).**
It already ships from `templates/orchestrator-plugin/.claude/settings.json`
(verified present). Backfill it into the repos that lack it (console,
dev-tooling, driver-claude, driver-codex, runtime — `evidence/16`), and add a
**doctor / dev-tooling presence check** that asserts each governed repo's
`.claude/settings.json` carries the SessionStart `ensure-plugins` hook, so a
repo that *loses* or never adopts it **fails loudly** instead of silently never
updating. This is the "automatic at source, and the gate catches missing
adoption" resolution of the fleet-non-uniformity constraint — adoption is
distributed by the template and enforced by a check, never left to per-repo
memory. (Cross-tenant backfill maps to console-vfd + the
driver/dev-tooling/runtime hook-adoption items.)

**(ii) Close the one-session lag inside the hook (feeds livespec-c1k9.2).** Today
`ensure-plugins` fetches, but the flip applies only next session (H1, fact 5).
Enhance the recipe so that AFTER the `install`/`update` leg it detects whether
any active-snapshot pointer moved (diff the project-scope entries of
`installed_plugins.json` pre/post, or compare the new marketplace HEAD to the
resolved snapshot) and, if so, emits a loud `hookSpecificOutput.additionalContext`
+ `systemMessage`: *"livespec plugins updated to <sha>; run `/reload-plugins` to
apply in THIS session (otherwise it runs the previous build)."* This uses the
documented mid-session-apply primitive (fact 5) to shrink the lag from "next
session" to "one `/reload-plugins`," with no restart and no new artifact. It is
**soft** (the model must choose to run it) — which is exactly why it pairs with
the **hard** Layer-2 gate (§4) that refuses to *proceed* stale.

**Rejected/deferred alternative (maintainer decision #3): a host-level
pre-session sweep (systemd timer / `claude` launch wrapper) that runs
`ensure-plugins` across all governed repos BEFORE any session starts.** It would
eliminate the lag entirely (the first prompt already runs current). But it (a) is
a new host daemon — a *new unmanaged surface* that can itself silently break,
reintroducing exactly the silent-staleness failure mode one layer down; (b)
violates "prefer primitives / ≤2 new artifacts"; and (c) is made **non-load-
bearing** by the hard gate — staleness cannot be silent even if the timer is
absent or broken. **Recommend: do NOT provision it now; the uniform hook + gate
suffice.** Revisit only if operational data shows the `/reload-plugins` lag is
painful. (This is a real values/posture call — surfaced in the decision list.)

### 3b. Codex (`codex exec`) — leans on the gate; a periodic host sweep for currency (feeds livespec-c1k9.4)

Codex has **no SessionStart-hook analogue** (host-wide `~/.codex/config.toml`,
fact 8 / `semantics.md` §6), so there is no in-session updater to fix. Two parts:

- **Gate coverage is FREE.** The Layer-2 `_bootstrap.py` chokepoint (§4) fires on
  `codex exec` because Codex drives the same `bin/*.py` wrappers (fact 8). So
  Codex gets the *fail-loud staleness gate* with zero Codex-specific code — this
  is the primary safety guarantee for the Codex surface.
- **Currency (updater):** provide a documented host-level periodic refresh — a
  small `codex plugin update`-equivalent sweep (cron/systemd, maintainer-side
  host provisioning, in the same class as the Beads-runtime prerequisites the
  CLAUDE.md already documents as "what bootstrap does NOT provision"). Honest
  posture: Codex currency is *weaker* than Claude's (no per-project session hook)
  and **deliberately leans on the gate** rather than pretending to match Claude's
  session-scoped updater. Self-resolved: scope the Codex updater to a host sweep +
  the shared gate; do not invent a Codex session-hook mechanism Codex does not
  offer. Cross-tenant item: livespec-c1k9.4.

### 3c. Fabro sandbox — OUT OF SCOPE for plugin machinery (confirmed)

Fabro resolves **no host plugins**: fresh clone + pinned docker image
`sha-ea684ad` + `uv.lock` pins (`semantics.md` §5). Its `implement.md` invokes
`just check`, never a `/livespec:*` skill, so the `_bootstrap.py` gate never
fires there and would be meaningless. Fabro's currency is entirely the
**docker-image pin under `bump-pin` discipline** — cross-tenant item **bd-ib-mwz**
(bring `sha-ea684ad` under the pin-autodiscovery formats). Do **not** design
plugin machinery for Fabro; keep its slice scoped to bd-ib-mwz. Stated crisply so
Phase 5 does not accidentally widen it.

---

## 4. Layer 2 — the fail-loud staleness gate (feeds livespec-c1k9.3)

**The chokepoint: a currency decision in core's `bin/_bootstrap.py`, a structural
sibling of the credential self-heal.** It mirrors that pattern exactly (pure
brain + thin impure performer), which keeps it exhaustively testable and
consistent with the orchestrator's `_self_heal_credentials()` shape.

### 4a. Pure brain — `currency.py` (the ONE genuinely new artifact)

New module `livespec/…/currency.py` (or vendored `_vendor/livespec_runtime/
currency.py` if it must be shared into siblings, matching `credentials.py`'s
home). Pure, no I/O, never raises, discriminated `Literal`-keyed union — copy the
`CredentialDecision` shape verbatim:

```python
CurrencyDecision = Current | Stale | Unknown   # kind: Literal["current"|"stale"|"unknown"]

def decide_currency(*, running_build_id: str, expected_build_id: str | None,
                    plugin_name: str, update_hint: str) -> CurrencyDecision: ...
```

- `Current` — `running_build_id == expected_build_id` → proceed (no-op).
- `Stale` — both known and differ → carries an actionable `message` naming the
  plugin, the running vs expected SHA, and the exact fix (`/reload-plugins`, or
  `mise exec -- just ensure-plugins` then restart).
- `Unknown` — `expected_build_id is None` (marketplace clone absent, or a
  legacy **semver-named** running dir whose SHA can't be derived) → not
  determinable; the *performer* applies the severity lever (§4c).

### 4b. Impure performer — wired into `bootstrap()`

At the tail of `bootstrap()` (after the sys.path inserts, exactly where the
orchestrator calls `_self_heal_credentials()`), a `_verify_currency()` gathers
the live inputs and performs the prescribed act:

- **`running_build_id`** = basename of `${CLAUDE_PLUGIN_ROOT}` (= the cache
  `<id>` = the commit SHA for SHA-named dirs). For a semver-named dir the SHA is
  not in the path → `expected_build_id`-side resolves to `Unknown` (see 4c).
  *(Because Layer 1 forces the SHA-keyed `update` path and c1k9.5 pushes toward
  SHA-named dirs, the steady state is SHA-named and this derivation just works.)*
- **`expected_build_id`** = `git -C ~/.claude/plugins/marketplaces/<marketplace>
  rev-parse HEAD` (short) — read **from disk, no network** (the marketplace clone
  was freshly fetched by the SessionStart hook's `marketplace add/update`). This
  is why Layer 1's fetch is a genuine *prerequisite* for the gate's precision, not
  redundant with it — the two layers are complementary.
- On `Current` → return. On `Stale` → `sys.stderr.write(message)` +
  `raise SystemExit(<code>)` (a stale `/livespec:*` op *refuses to proceed*, per
  "enforce don't hope"). On `Unknown` → §4c.

`${CLAUDE_PLUGIN_ROOT}` and the marketplace-clone path are read from env / a
fixed `~/.claude/plugins/marketplaces/<name>` location; both tolerate absence
(→ `Unknown`, never a crash), mirroring `_read_credential_wrapper()`'s fail-open.

### 4c. `Unknown` handling — the severity lever (maintainer decision #2)

When "expected" is not determinable (no marketplace clone / network-off /
semver-named running dir), **default to WARN-not-fail** (emit the diagnostic to
stderr, proceed) with one self-documenting env lever
(`LIVESPEC_CURRENCY_GATE=warn|fail`, default `warn`) that CI/dispatch contexts
set to `fail`. This is the established "carve-out as a severity lever" pattern
(warn-vs-fail for a fast check, wired and always invoked, never silently
skipped). The values tension — a stale-unverifiable build could still run under
the default — is surfaced in the decision list.

### 4d. SessionStart-hook gate variant — the SAME brain, soft site

The SessionStart hook enhancement in §3a(ii) is the *soft* invocation of the same
`decide_currency` brain: at session start it compares and injects a loud
`additionalContext`/`systemMessage` (+ the `/reload-plugins` instruction) if
`Stale`. So the gate lives at **two sites, one brain**: soft at session start
(catches it before any op, drives the reload), hard at the CLI chokepoint
(refuses to run stale). No third artifact.

### 4e. Negative test (Phase 5 exit gate)

Unit-test `decide_currency` exhaustively (pure → trivial: Current/Stale/Unknown
across matching/differing/None inputs). Integration-test the performer by
pointing `${CLAUDE_PLUGIN_ROOT}` at a deliberately-old snapshot dir (or a scratch
marketplace clone whose HEAD differs) and asserting a `/livespec:*` invocation
exits non-zero with the diagnostic naming the fix — the research-plan Phase 5
negative test. Mirrors how the credential self-heal is tested.

---

## 5. Cache hygiene (feeds livespec-c1k9.5) — SELF-RESOLVED

- **Force the SHA-keyed update path.** `ensure-plugins` already runs explicit
  `claude plugin update` (SHA-keyed, fact 3). Keep it; that is what makes active
  pointers content-stable and avoids the semver-dir collision. The gate's
  path-derived `running_build_id` (§4b) relies on this. No change needed beyond
  documenting it as load-bearing.
- **Semver-dir ambiguity (the manifest-version trap).** Inherent to Claude Code's
  version-as-cache-key (fact 3) crossed with release-please's version-at-release
  model (fact 4); not fully fixable in-repo. Mitigation = force SHA-keyed (above)
  so the *active* pointer is never a semver dir. **Upstream report to Anthropic
  is warranted** (low cost, documents the trap): "a marketplace `install` of a
  `github` source keys the cache dir by `plugin.json.version`; post-release master
  commits reuse the same version string, so content collides last-writer-wins in
  the `version`-named dir — SHA-keying or content-hashing the cache dir would
  prevent silent stale-content collisions." Self-resolved: file the report; it
  feeds nobody's critical path but records the defect.
- **Snapshot pruning.** The `.in_use/<pid>` sweep + 7-day orphan cleanup (docs
  716) are conservative-by-design and safe; 51 retained orchestrator snapshots is
  expected, not a leak. No aggressive pruning. The duplicate *enabled*
  `installed_plugins.json` entries (`evidence/15`: 5× `livespec@livespec` at
  different versions all "enabled") are a separate minor hygiene wart — resolution
  still picks one active pointer per scope, so it is **not** load-bearing for the
  invariant; note it, low priority, possibly folded into the existing reaper
  path-gone sweep (livespec-jcc6.4).

---

## 6. Contract commitments (feeds livespec-c1k9.6)

Per "spec is for contracts, tracking stays in the ledger," codify via
`/livespec:propose-change` into `SPECIFICATION/` ONLY the durable contracts:

1. **The plugin-currency invariant** (§1, the reconciled master-HEAD form) and
   the **two-axis distinction** (plugin currency = master HEAD; code-pin =
   release tag) — likely `non-functional-requirements.md` §"Plugin distribution"
   or a new §"Plugin currency guarantee."
2. **The staleness-gate contract**: every `/livespec:*` op verifies running-build
   == expected at the `_bootstrap.py` chokepoint and fails loud on `Stale`, with
   the `Unknown` severity lever — as an *architectural commitment* (what is
   guaranteed), not the mechanism.
3. **The SessionStart-hook presence requirement** for governed repos + its
   enforcement check.

Do NOT codify: the copier-template mechanics, the exact YAML of the auto-merge
guard, the park-staleness cron — those are working-note / ledger tracking, not
contracts (they would not still make sense after the workflow stabilizes).

---

## 7. Work-item mapping

| Design piece | Item (filed) | Tenant |
|---|---|---|
| auto-enable-merge shape-guarded release-PR path + header rationale + 4-repo backfill | **livespec-c1k9.1** | core (fleet-wide) |
| Park-staleness backstop `reusable-release-park.yml` | **NEW** (dev-tooling tenant) — file under c1k9 as cross-tenant | dev-tooling |
| One-session-lag close: hook detects pointer move → injects `/reload-plugins` | **livespec-c1k9.2** | core |
| Layer-2 gate: `currency.py` pure brain + `_bootstrap.py` performer + negative test | **livespec-c1k9.3** | core |
| Codex: gate-covers-free + host refresh sweep | **livespec-c1k9.4** | Codex/host |
| Cache hygiene: force SHA-keyed (document) + upstream report | **livespec-c1k9.5** | core + upstream |
| Contract codification via propose-change | **livespec-c1k9.6** | core (SPECIFICATION) |
| SessionStart hook backfill + doctor presence check | **console-vfd** + driver/dev-tooling/runtime hook-adoption items (+ NEW doctor-check item, core) | cross-tenant |
| Fabro docker-image pin under bump-pin | **bd-ib-mwz** | orchestrator (Fabro) |

**NEW items to file:** (a) `reusable-release-park.yml` (dev-tooling); (b) the
doctor/dev-tooling **SessionStart-hook presence check** (core) — the enforcement
half of §3a(i), without which H5 non-uniformity can silently recur.

---

## 8. Verification plan (Phase 5 exit — closes the epic)

1. **Release train unparked:** all four plugin repos' release PRs auto-merge on
   green (observe one cycle each); `reusable-release-park.yml` goes green (no
   parked PR / no unreleased backlog).
2. **Uniform currency:** every governed repo's `.claude/settings.json` carries the
   SessionStart `ensure-plugins` hook; the presence check passes fleet-wide.
3. **Positive assertion (mechanized, every repo × surface):** a script that, per
   governed repo, resolves each livespec-ecosystem plugin's active-snapshot SHA
   and asserts it == that marketplace clone's freshly-fetched HEAD SHA — for
   interactive Claude and `codex exec`. (Fabro asserted separately via its
   docker-image pin, not plugin snapshots.)
4. **Negative assertion (the hard proof):** deliberately stale a cache (point
   `${CLAUDE_PLUGIN_ROOT}` at an old snapshot, or a scratch marketplace clone
   ahead of the snapshot) and assert a `/livespec:*` op exits non-zero with the
   diagnostic naming the fix; assert the `Unknown` lever warns by default and
   fails under `LIVESPEC_CURRENCY_GATE=fail`.
5. Both recorded in `handoff.md`; epic closed only on both.

---

## Appendix — decisions I self-resolved (reported, not gated)

- **auto-enable-merge fix shape** → shape-guarded release-PR branch (§2a), not a
  bare allowlist add. Clear "fix the gate correctly" call.
- **Cache hygiene posture** → force SHA-keyed (already does) + file the upstream
  report; no aggressive pruning (§5).
- **Codex** → lean on the shared gate + a host refresh sweep; do not invent a
  Codex session-hook mechanism Codex does not offer (§3b).
- **Fabro** → out of scope for plugin machinery; stays on bd-ib-mwz (§3c).
- **Contract scope** → codify only the invariant, the gate guarantee, and the
  hook-presence requirement; leave mechanics in the ledger (§6).
