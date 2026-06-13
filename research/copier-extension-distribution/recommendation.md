# Copier extension-distribution gap — design recommendation

Work-item: **livespec-2jsj** (DESIGN DECISION; user ratifies before any
implementation). This document leads with the recommendation, then explains the
mechanism, evaluates all three candidate options, and ends with a migration
sketch and open questions.

## Recommendation (lead)

**Adopt Option 3 — pre-render the canonical-slug set into a template asset at
template-release time — but realize it as Option 3′: stamp the canonical set
into the template's `.copier-answers.yml.jinja` defaults (an answers-file
*default*, computed once when the template is authored, not per-consumer at
render time).** Concretely: a release-time step in `livespec` writes the current
`canonical_check_slugs()` tuple into a committed template data file
(`templates/impl-plugin/canonical-slugs.yml` or a `_jinja` default), and
`justfile.jinja` iterates *that committed value* instead of the
extension-provided Jinja global. The copier Jinja extension is then deleted
entirely.

This is a blend of Options 2 and 3 in framing, but its defining property is
Option 3's: **the canonical block is already-rendered content the consumer
receives, computed once at the template's single source of truth, with zero
import dependency at `copier update` time.** It is the only option that
simultaneously (a) keeps `livespec_dev_tooling.canonical_checks` as the one
source of truth, (b) makes `copier update` import-free and therefore correct on
the consumer side, and (c) restores the spec's "3-way merge surfaces canonical
drift" contract that the current extension silently breaks.

Rationale in three sentences: the extension can never be importable on the
consumer `copier update` path by construction (the root `copier.yml`
deliberately omits `_jinja_extensions`, and copier clones the template to an
ephemeral checkout with no PYTHONPATH injection), so the canonical block renders
empty and drift can never propagate. Vendoring the extension into every consumer
(Option 1) re-introduces exactly the kind of hand-synced executable-in-scaffold
duplication the family's `copier`/`dev-tooling` channel partition forbids, and
adds a second place the canonical logic lives. Pre-rendering moves the
computation to the one place that already owns the source of truth — the
`livespec` template release — so consumers receive a concrete, mergeable,
already-correct block and need no import at all.

## Problem statement

`livespec/templates/impl-plugin/justfile.jinja` stamps the family's canonical
enforcement-check aggregate into each generated repo's `check:` recipe:

```jinja
targets=(
{%- for slug in canonical_check_slugs %}
        {{ slug }}
{%- endfor %}
)
```

`canonical_check_slugs` is a Jinja global injected by a copier extension,
`copier_extensions.canonical_checks:CanonicalChecksExtension`
(`dev-tooling/copier_extensions/canonical_checks.py`). That extension calls the
single source of truth, `livespec_dev_tooling.canonical_checks.canonical_check_slugs()`
(today: 39 slugs, alphabetically sorted, dynamically discovered from
`livespec_dev_tooling/checks/*.py`).

Per `SPECIFICATION/contracts.md` §"Shared code sync — livespec-dev-tooling"
(the **Template gate**, layer 2 of the three-layer wiring-completeness
invariant): the template MUST derive the stamped list from
`livespec_dev_tooling.canonical_checks` at copy time, NOT from a hand-maintained
list, "so that template-generated repos pick up canonical-set growth
automatically as new checks land," and "For existing siblings, `copier update`'s
3-way merge surfaces canonical-set drift as merge conflicts in the regenerated
`justfile`."

### Why the extension is unimportable on the consumer side

There are two distinct copier flows, and they read two different configs:

1. **Smoke-check flow (works).** `dev-tooling/checks/copier_template_smoke.py`
   points copier directly at `templates/impl-plugin/` and injects
   `<repo-root>/dev-tooling` onto the subprocess `PYTHONPATH`
   (`_build_copier_env`). That config (`templates/impl-plugin/copier.yml`)
   *does* declare `_jinja_extensions: [copier_extensions.canonical_checks:…]`,
   and because `dev-tooling/` is on `PYTHONPATH`, the dotted path resolves and
   the block renders correctly. The smoke check then asserts the generated
   justfile contains all 39 slugs in order. This path is healthy.

2. **Consumer flow (broken).** A generated repo re-syncs via
   `copier update --vcs-ref=master` with `_src_path:
   gh:thewoolleyman/livespec`. Copier reads ONLY the **repo-root**
   `copier.yml`, which routes to the subdirectory via `_subdirectory:
   templates/impl-plugin` but **deliberately does NOT declare
   `_jinja_extensions`**. The root config's own header documents why: copier
   *extend-merges* `_jinja_extensions` across `!include`d documents, so the key
   cannot be declared in the shared include and then neutralized at the root —
   if it were declared anywhere reachable from the root config, copier would try
   to import `copier_extensions.canonical_checks` from the ephemeral clone it
   makes of the template, where `dev-tooling/` is not on `sys.path` and the
   dotted path cannot resolve (copier does no PYTHONPATH injection on the
   consumer path). The chosen workaround is to omit the extension entirely on
   the consumer config.

The consequence: on `copier update`, `canonical_check_slugs` is an **undefined**
Jinja global. Copier's sandboxed Jinja environment leaves it undefined
(ChainableUndefined-style), the `{%- for slug in canonical_check_slugs %}` loop
iterates zero times, and the regenerated `justfile` carries an **empty**
`targets=(...)` array.

### Why this matters (the real failure)

Because the regenerated block is empty, copier's 3-way merge sees "consumer had
39 slugs, template now produces 0 slugs" and the conflict (or clean overwrite,
depending on the merge) pushes toward dropping the consumer's slugs. The
`justfile.jinja` header and the work-item both note resolvers MUST manually keep
the consumer-side 39 slugs. **The Template-gate contract is therefore
defeated:** canonical-set GROWTH can never propagate to existing siblings via
`copier update`, because the re-rendered canonical content is empty rather than
"the new larger set." Affected re-syncs called out in the work-item: `smc`/`0lt`
(their justfile conflict renders the canonical block empty on the "after
updating" side). The single source of truth (`canonical_checks`) is correct; the
*delivery channel* to existing consumers is broken.

## The three options

### Option 1 — Vendor the extension into consumers

**Mechanism.** Ship `copier_extensions/canonical_checks.py` (and a path/packaging
shim so it's importable) into every generated consumer repo, so that when
`copier update` runs from within the consumer checkout, the dotted extension
path resolves. The root `copier.yml` would then declare `_jinja_extensions`, and
the extension would re-read `livespec_dev_tooling.canonical_checks` from the
consumer's own pinned `livespec-dev-tooling` dependency.

**Pros.**
- Keeps render-time dynamism: the consumer computes the slug set from *its own*
  pinned `livespec-dev-tooling`, so the stamped set always matches the checks
  the consumer actually has installed.
- No new release-time step in `livespec`.

**Cons.**
- **Directly violates the channel-partition contract.**
  `SPECIFICATION/contracts.md` §"Shared content sync — copier template" and
  §"Shared code sync — livespec-dev-tooling" mandate that `copier` "MUST NOT
  deliver executable Python or shell code" — the two channels partition shared
  content along the static-vs-executable axis. Vendoring a `.py` extension *via
  the copier template* is exactly the boundary violation the partition forbids.
- **Two sources of canonical logic.** The extension would now live in `livespec`
  (for the smoke-check flow) AND in every consumer (vendored), a hand-synced
  duplicate that drifts — the precise anti-pattern the family's "single source of
  truth" and "minimize dependencies / no second-source-of-truth" conventions
  reject.
- **Fragile import surface on the update path.** Making a vendored module
  reliably importable under copier's ephemeral-clone + `uv run` execution model
  is the same class of brittleness that produced this bug; it trades a
  guaranteed-empty render for a sometimes-failing import (`ExtensionNotFoundError`
  aborts the whole `copier update`, which is arguably worse than an empty block).
- Bloats every consumer with template-mechanism code that has nothing to do with
  the consumer's own purpose.

**Verdict: reject.** This is the "fix the symptom by spreading the mechanism"
option; it multiplies the source of truth and breaks the channel partition.

### Option 2 — Replace extension-computed content with answers-file data

**Mechanism.** Bake the canonical slug set into the copier *answers* data — i.e.
record the slug list as an answered question (or template data value) in
`.copier-answers.yml`, and have `justfile.jinja` iterate that answer instead of
the extension global.

**Pros.**
- No copier extension and no import on any flow — the answers file is plain data
  copier always reads.
- The data travels with the consumer, so `copier update` re-renders from a
  concrete value.

**Cons.**
- **Wrong home for the source of truth.** The canonical set is a *property of
  `livespec-dev-tooling`*, not a per-consumer answer the user supplies or should
  edit. Modelling it as an answer makes 39 machine-derived slugs into
  user-facing answer data — a category error that invites hand-editing and
  drift, and pollutes `.copier-answers.yml` (which is meant to track the
  consumer's *choices*, not the template's derived constants).
- **Still needs a sync mechanism.** For canonical-set growth to propagate, the
  answer would have to be *re-derived and re-written* on each `copier update` —
  which either requires the extension again (back to square one) or a manual
  re-answer, defeating the automatic-propagation goal.
- Per-consumer answer copies multiply the source of truth across every consumer's
  answers file, same drift problem as Option 1 minus the executable-code
  violation.

**Verdict: reject as framed.** Putting derived, machine-owned data into the
user-answer channel is the wrong abstraction. (Its one good idea — "stop relying
on a render-time import" — is precisely what Option 3′ keeps, but it stamps the
value as a *template default* owned by the release, not as a user answer.)

### Option 3 — Pre-render the canonical set into the template at release time (RECOMMENDED, as 3′)

**Mechanism.** Compute `canonical_check_slugs()` ONCE in `livespec` — at the
moment the template is authored/released — and commit the result as a static
template asset. Two concrete shapes:

- **3a (committed data file):** a release-time `just`/CI step runs
  `python -m livespec_dev_tooling.canonical_checks --json` and writes
  `templates/impl-plugin/canonical-slugs.yml` (a committed list). `copier.yml`
  loads it via copier's `external_data`/`_data` mechanism (or a tiny `!include`),
  and `justfile.jinja` iterates the loaded list. No extension; no import on any
  flow; the block is concrete data the consumer always renders.
- **3b (pre-stamped block):** the release step renders the `targets=(...)` block
  itself and commits it as a `.jinja`-free partial that `justfile.jinja`
  includes verbatim. Even simpler, but couples the data shape to bash formatting.

Either way the extension (`dev-tooling/copier_extensions/canonical_checks.py`) is
**deleted**, and the smoke check is updated to assert against the committed asset
instead of the live extension.

**Pros.**
- **Single source of truth preserved.** `livespec_dev_tooling.canonical_checks`
  stays the one origin; the release-time step is a *projection* of it into a
  committed artifact, regenerated mechanically — not a hand-maintained second
  list. A cheap enforcement check (analogous to today's smoke check) asserts the
  committed asset equals `canonical_check_slugs()` so the projection can never
  silently drift.
- **`copier update` becomes import-free and correct.** The consumer renders a
  concrete, non-empty block on every re-sync. Canonical-set growth propagates the
  moment a new template release is cut, and `copier update`'s 3-way merge
  surfaces it as a real diff against the consumer's current block — **restoring
  the Template-gate contract** the extension silently broke.
- **Honors the channel partition.** `copier` ships a static data file (allowed);
  no executable code crosses the copier channel. The dynamic computation lives in
  `livespec-dev-tooling` (the executable channel) and runs only inside `livespec`
  at release time.
- **Removes the smoke-check PYTHONPATH hack and the dual-config `_jinja_extensions`
  asymmetry** — the brittle part of the current design disappears.
- **Minimizes dependencies.** No render-time extension, no per-consumer vendored
  code; the consumer needs nothing beyond stock copier.

**Cons / costs.**
- A release-time regeneration step must exist and be enforced (so the committed
  asset can't go stale). This is a modest, well-understood pattern (the existing
  smoke check already does an equivalent comparison; it converts from "assert the
  extension stamps correctly" to "assert the committed asset matches the source
  of truth").
- The canonical set propagates at **template-release** granularity, not at the
  consumer's own `livespec-dev-tooling` pin. This is actually *aligned* with the
  spec: the Template gate is about what the template stamps, and re-sync is
  expected to flow through `copier update --vcs-ref=master`. (See open question
  #2 on whether release-time vs. pin-time granularity matters for any consumer.)

**Verdict: adopt (as 3′).** This is the only option that keeps one source of
truth, removes all render-time import fragility, and restores the broken
propagation contract.

## Migration sketch (recommended Option 3′ / 3a)

1. **Add a release-time projection step in `livespec`.** A `just` target (e.g.
   `just stamp-canonical-slugs`) runs
   `python -m livespec_dev_tooling.canonical_checks --json` and writes
   `templates/impl-plugin/canonical-slugs.yml` (alphabetically sorted, already
   guaranteed by the source). Wire it into the release/`copier`-template path and
   into CI.
2. **Wire the data into copier.** Have the template configs load
   `canonical-slugs.yml` as template data (copier `external_data`/`_data` or a
   YAML `!include`) so `canonical_check_slugs` is a plain rendered value on BOTH
   the smoke-check flow AND the consumer `copier update` flow. `justfile.jinja`'s
   loop body is unchanged.
3. **Delete the extension.** Remove
   `dev-tooling/copier_extensions/canonical_checks.py`, drop `_jinja_extensions`
   from `templates/impl-plugin/copier.yml`, and remove the PYTHONPATH-injection
   special-casing in `copier_template_smoke.py`.
4. **Repoint the enforcement check.** Update `copier_template_smoke.py` (or add a
   sibling check) to assert the committed `canonical-slugs.yml` equals
   `canonical_check_slugs()` AND that the generated justfile stamps exactly that
   set — preserving the "no silent drift" guarantee with no live extension.
5. **Update the spec.** `SPECIFICATION/contracts.md` §"Shared code sync —
   livespec-dev-tooling" Template-gate paragraph currently says "via a copier
   `_jinja_extension` or equivalent" — the "or equivalent" already permits this;
   tighten the prose to describe the release-time-projection mechanism and the
   anti-drift check, and note that the consumer `copier update` path renders the
   stamped set without any import. (This is a `/livespec:propose-change` →
   `/livespec:revise` cycle, not part of this doc.)
6. **Re-sync existing consumers.** Run `copier update --vcs-ref=master` against
   `smc`/`0lt` (and any other impl-* siblings); the regenerated block is now the
   concrete current canonical set, so the 3-way merge produces a real, reviewable
   diff instead of an empty array.

This is a contract-touching change (the Template-gate mechanism wording), so the
implementing work-item should sequence the `propose-change`/`revise` spec update
alongside the code change.

## Open questions for the user

1. **3a vs 3b.** Commit the slug *data* (`canonical-slugs.yml`, loaded as copier
   data — keeps `justfile.jinja` as the single place the bash array shape lives)
   vs. commit the pre-rendered *block* (simplest, but bakes bash formatting into a
   committed partial)? Recommendation: **3a** — data file — to keep the bash
   shape in one templated place.
2. **Propagation granularity.** Pre-rendering fixes the canonical set at
   template-release time, so a consumer pinned to an older `livespec-dev-tooling`
   could theoretically receive a slug for a check its pin doesn't ship. In
   practice the family bumps pins in lockstep and the Template gate is explicitly
   about template-time stamping, so this is expected — but confirm no consumer
   intentionally lags the canonical set.
3. **Enforcement strictness.** Should the anti-drift check (committed asset ==
   `canonical_check_slugs()`) be a hard `fail` in `just check`/CI (recommended,
   matching today's smoke-check rigor), or a `warn`?
4. **Extension deletion.** Confirm the copier extension has no other consumer
   beyond `justfile.jinja` before deletion (grep confirms it is referenced only
   by `templates/impl-plugin/copier.yml` `_jinja_extensions` and the smoke check;
   safe to remove).
