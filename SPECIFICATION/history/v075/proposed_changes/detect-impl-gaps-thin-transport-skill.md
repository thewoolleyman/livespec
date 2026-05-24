---
topic: detect-impl-gaps-thin-transport-skill
author: claude-opus-4-7
created_at: 2026-05-24T08:00:00Z
---

## Proposal: factor-detect-impl-gaps-as-thin-transport-skill

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Factor the read-only spec→impl gap-detection phase out of the heavyweight `capture-impl-gaps` skill and into a new thin-transport sibling skill `detect-impl-gaps` (parallel naming). Doctor's two gap-detection-dependent cross-boundary invariants (`gap-tracking-one-to-one`, `no-stale-gap-tied`) consume the new surface directly; `capture-impl-gaps` consumes it as its detection step, then layers the interactive per-gap consent + JSONL-filing workflow on top. The implementation-plugin contract grows from a 9-skill surface (6 heavyweight + 3 thin-transport) to a 10-skill surface (6 heavyweight + 4 thin-transport).

### Motivation

`no-stale-gap-tied` is the only cleanup invariant in the §"Doctor cross-boundary invariants" catalogue that has not yet been implemented (work-item li-qt7t5t). Implementing it requires invoking the impl-plugin's gap-detection logic in a non-mutating, machine-readable form at check time. The current spec text in §"gap-tracking-one-to-one" parenthetically commits this to "invoking the active impl-plugin's `capture-impl-gaps` skill in a non-mutating dry-run mode at check time" — but `capture-impl-gaps` is a heavyweight authored skill whose contract is "for each detected gap, present to user, ask consent, append work-item JSONL record." A "non-mutating dry-run mode" of a heavyweight interactive skill is an architectural smell: it mixes the mechanical detection path and the interactive filing path inside one SKILL.md, with mode-conditional behavior that contradicts the SKILL.md's primary contract.

The heavyweight/thin-transport distinction is load-bearing in this contract (per §"Implementation-plugin contract — the 9-skill surface" and §"Thin-transport skill doctrine"). Thin-transport skills are CLI pass-throughs over `bin/<skill>.py` with no LLM in the path; doctor subprocesses them to consume their JSON output. Heavyweight skills carry SKILL.md dialogue prose. The detection phase is mechanical (Spec Reader read + MUST/SHOULD enumeration); it belongs on the thin-transport side. Factoring it out lets `capture-impl-gaps` stay a clean heavyweight skill (its SKILL.md narrates the user-facing filing workflow only), while `detect-impl-gaps` becomes the canonical machine surface for "give me the current gap-id set" — consumed identically by doctor and by `capture-impl-gaps`.

The "10-skill surface" rename of the cross-reference section is a deliberate count-pinning choice consistent with the existing convention (the section is named for its arity). Future skill additions would require the same kind of rename; that's expected.

### Proposed Changes

Coordinated edits across the upstream `contracts.md` and `constraints.md` to introduce `detect-impl-gaps` as a thin-transport sibling of `capture-impl-gaps`, update every reference to the gap-detection mechanism, and adjust the skill-count name. A separate propose-change cycle in `livespec-impl-plaintext/SPECIFICATION/proposed_changes/` declares the plugin's per-implementation realization of the new surface.

#### `SPECIFICATION/contracts.md` §"Doctor cross-boundary invariants" intro

Add `detect-impl-gaps` to the machine-surface listing:

```diff
-Doctor's responsibilities MUST include structural invariants that cross the spec / impl boundary by querying the active impl-plugin's machine surface (the `<impl-plugin>:list-work-items --json` and `<impl-plugin>:capture-impl-gaps` thin-transport / heavyweight skills defined by §"Implementation-plugin contract — the 9-skill surface"), plus a cross-repo coordination invariant that reads the active impl-plugin's `compat` block from `.livespec.jsonc` per §"Cross-repo coordination — pin-and-bump".
+Doctor's responsibilities MUST include structural invariants that cross the spec / impl boundary by querying the active impl-plugin's machine surface (the `<impl-plugin>:list-work-items --json` and `<impl-plugin>:detect-impl-gaps --json` thin-transport skills defined by §"Implementation-plugin contract — the 10-skill surface"), plus a cross-repo coordination invariant that reads the active impl-plugin's `compat` block from `.livespec.jsonc` per §"Cross-repo coordination — pin-and-bump".
```

#### `SPECIFICATION/contracts.md` §"gap-tracking-one-to-one"

Replace the parenthetical mechanism description to name `detect-impl-gaps` and drop the "non-mutating dry-run mode" framing (no longer needed — `detect-impl-gaps` is intrinsically non-mutating):

```diff
-Every gap surfaced by a fresh impl-plugin gap-detection run (i.e., invoking the active impl-plugin's `capture-impl-gaps` skill in a non-mutating dry-run mode at check time) MUST correspond to exactly one tracked work item across all statuses (open, in-progress, closed).
+Every gap surfaced by a fresh impl-plugin gap-detection run (i.e., invoking the active impl-plugin's `detect-impl-gaps --json` thin-transport skill at check time) MUST correspond to exactly one tracked work item across all statuses (open, in-progress, closed).
```

#### `SPECIFICATION/contracts.md` §"no-stale-gap-tied"

No textual change required — the existing prose uses the generic phrase "fresh impl-plugin gap-detection run," which now resolves through the updated §"gap-tracking-one-to-one" mechanism description. The invariant's `warn`-classification, narration shape, and acceptance criteria are unchanged.

#### `SPECIFICATION/contracts.md` line 230 cross-reference

Update the count name in the cross-reference:

```diff
-The impl-plugin contract's work-item record schema (per §"Implementation-plugin contract — the 9-skill surface") gains a typed object shape for entries in the existing `depends_on` array, replacing the prior string-only `<work-item-id>` shape.
+The impl-plugin contract's work-item record schema (per §"Implementation-plugin contract — the 10-skill surface") gains a typed object shape for entries in the existing `depends_on` array, replacing the prior string-only `<work-item-id>` shape.
```

#### `SPECIFICATION/contracts.md` §"Implementation-plugin contract — the 9-skill surface" section header + intro

Rename the section and update the intro count:

```diff
-## Implementation-plugin contract — the 9-skill surface
-
-Every `livespec-impl-*` plugin MUST expose these nine skills under its own namespace prefix (`/livespec-impl-<X>:<skill>`). Six are heavyweight authored skills (dialogue, detection logic, judgment calls); three are thin-transport skills (CLI pass-through per §"Thin-transport skill doctrine"). Consumer projects, doctor's cross-boundary invariants, and the project-local orchestration layer all consume the surface uniformly via skills.
+## Implementation-plugin contract — the 10-skill surface
+
+Every `livespec-impl-*` plugin MUST expose these ten skills under its own namespace prefix (`/livespec-impl-<X>:<skill>`). Six are heavyweight authored skills (dialogue, judgment calls); four are thin-transport skills (CLI pass-through per §"Thin-transport skill doctrine"). Consumer projects, doctor's cross-boundary invariants, and the project-local orchestration layer all consume the surface uniformly via skills.
```

#### `SPECIFICATION/contracts.md` `capture-impl-gaps` heavyweight skill description

Update to reference the new thin-transport sibling as the detection source:

```diff
-- **`capture-impl-gaps`** — detect spec → impl gaps mechanically via the Spec Reader; file gap-tied work items into the plugin's Work Items store with per-gap user consent. Collapses the prior `refresh-gaps` + `plan` skill pair into one ephemeral-detection skill. Detection state is in-memory and discarded at skill exit; no persistent intermediate artifact.
+- **`capture-impl-gaps`** — file gap-tied work items into the plugin's Work Items store with per-gap user consent. The detection step MUST consume the plugin's `detect-impl-gaps --json` thin-transport sibling (no in-skill duplication of the detection logic); the filing step is the interactive, judgment-bearing workflow that `capture-impl-gaps` owns. Detection state is in-memory and discarded at skill exit; no persistent intermediate artifact.
```

#### `SPECIFICATION/contracts.md` `implement` heavyweight skill description

Update the gap-tied closure-verification step to invoke `detect-impl-gaps` directly:

```diff
-- **`implement`** — drive Red → Green for a single work item. For gap-tied items, verify closure by re-running `capture-impl-gaps` in dry-run mode and confirming the `gap-id` is no longer detected; for freeform items, close with a simple `--reason`. Closure branches on origin × disposition: gap-tied fix (verify + audit fields), freeform fix (simple reason), non-fix (administrative — `wontfix`, `duplicate`, `spec-revised`, `no-longer-applicable`, `resolved-out-of-band`).
+- **`implement`** — drive Red → Green for a single work item. For gap-tied items, verify closure by invoking `detect-impl-gaps --json` and confirming the `gap-id` is no longer present in the returned set; for freeform items, close with a simple `--reason`. Closure branches on origin × disposition: gap-tied fix (verify + audit fields), freeform fix (simple reason), non-fix (administrative — `wontfix`, `duplicate`, `spec-revised`, `no-longer-applicable`, `resolved-out-of-band`).
```

#### `SPECIFICATION/contracts.md` §"Thin-transport skills (3) — required machine query surface"

Rename the section header and add the new `detect-impl-gaps` bullet:

```diff
-### Thin-transport skills (3) — required machine query surface
+### Thin-transport skills (4) — required machine query surface

 - **`list-memos`** — required (promoted from discretionary). Supports `--filter` flags (most notably `--filter=untriaged`) and `--json` output. Consumed by doctor's memo-hygiene invariant and by users for queue inspection.
 - **`list-work-items`** — required (new). Supports filter flags (`--gap-tied`, `--blocked`, `--with-gap-id`, etc.) and `--json` output. Consumed by doctor's five work-item structural invariants (defined by a subsequent propose-change cycle), by the project-local loop driver for routing decisions, and by users for queue inspection. Work-items carry a typed `depends_on` array per §"Cross-repo dependency awareness"; the prior string-only `<work-item-id>` shape and the parallel `blocked_by` field are NOT v1 valid forms. The impl-plugin's data-migration step MUST convert prior records before this contract takes effect.
 - **`next`** — required (new). Ranks the most ripe impl-side action using whatever native primitives the backend provides (e.g., `bd ready` for a beads-backed impl, JSONL traversal for a plaintext impl, GitLab API for a gitlab impl). Pure function of impl-side state; no LLM in the ranking path. Asymmetric counterpart to `/livespec:next`. The ranker MUST consult `livespec_runtime.cross_repo.resolve_ref` for every candidate work-item's `depends_on` entries and MUST exclude any candidate with at least one entry resolving to `open`. Excluded candidates do NOT appear in the ranked list (they are not surfaced with a lower urgency; they are absent entirely). MUST accept the same `--limit <count>` (default `5`) and `--offset <count>` (default `0`) flags as the spec-side `next` skill, with the same validation rules and exit-2-on-bad-flags behavior. MUST emit a JSON object of the same shape as the spec-side `next` skill's output (per §"`/livespec:next` spec-side thin-transport skill" → "Output schema"): top-level `candidates[]` and `pagination` keys. Each candidate object MUST carry at minimum `action`, `reason`, `urgency`, AND the impl-side-specific `work_item_ref` field. The candidate object MAY include additional impl-side-specific fields (e.g., `blocked_by`, `epic`) provided they are documented by the impl-plugin's own per-implementation contract. The cross-plugin contract MUST NOT prescribe `additionalProperties` discipline on the candidate object: impl-plugin authors own their per-implementation schema, and the cross-plugin contract surface MUST remain agnostic to per-implementation field additions.
+- **`detect-impl-gaps`** — required (new). Reads the live Specification via the Spec Reader and emits the current set of spec → impl gap-ids as JSON. Pure function of spec state and the gap-rule enumeration; no LLM in the detection path; no mutation of any impl-side store. The skill is the canonical gap-detection surface — both doctor (for `gap-tracking-one-to-one` and `no-stale-gap-tied` invariants) and the heavyweight `capture-impl-gaps` sibling consume the same surface uniformly. Wrapper CLI surface: `detect-impl-gaps [--spec-target <path>] [--project-root <path>] [--json]`. The `--json` output shape is a top-level object `{"gap_ids": ["<gap-id>", ...]}`; default human output is a one-line-per-gap summary. The skill MUST exclude `<spec-root>/proposed_changes/` content from detection (the Spec Reader already enforces this exclusion at its boundary; the skill MUST NOT bypass it).
```

#### `SPECIFICATION/contracts.md` §"Cross-boundary handoffs"

Add a new red-edge handoff for the gap-detection invariants:

```diff
 1. `<impl-plugin>:capture-spec-drift` → `/livespec:propose-change` (drift findings).
 2. `<impl-plugin>:process-memos` → `/livespec:propose-change` (spec-bound memo disposition).
 3. `/livespec:doctor` → `<impl-plugin>:list-memos --filter=untriaged --json` (memo-hygiene invariant).
 4. `/livespec:doctor` → `<impl-plugin>:list-work-items --json` (work-item structural invariants).
-5. The project-local Layer 3 loop driver invokes both `/livespec:next` and `<impl-plugin>:next` to compose cross-side recommendations; the cross-side composition itself is defined by a separate propose-change cycle for the orchestration layer.
+5. `/livespec:doctor` → `<impl-plugin>:detect-impl-gaps --json` (gap-detection invariants `gap-tracking-one-to-one` and `no-stale-gap-tied`).
+6. The project-local Layer 3 loop driver invokes both `/livespec:next` and `<impl-plugin>:next` to compose cross-side recommendations; the cross-side composition itself is defined by a separate propose-change cycle for the orchestration layer.
```

#### `SPECIFICATION/contracts.md` §"Spec Reader required-capability surface" consumer listing

Replace `capture-impl-gaps` with `detect-impl-gaps` in the consumer list. `capture-impl-gaps` no longer reads the Spec Reader directly; it consumes the detection result through `detect-impl-gaps`:

```diff
-Skills that consume the Spec Reader include `capture-impl-gaps` (gap-rule enumeration; also uses the version query to detect what has changed since the skill's own last-checked marker, an impl-internal state), `capture-spec-drift` (comparison baseline), `implement` (work-item context resolution), and `process-memos` (spec-vs-impl disposition decisions). Other impl-side operations MAY consume it as needed.
+Skills that consume the Spec Reader include `detect-impl-gaps` (gap-rule enumeration; also uses the version query to detect what has changed since the impl's last-checked marker, an impl-internal state), `capture-spec-drift` (comparison baseline), `implement` (work-item context resolution), and `process-memos` (spec-vs-impl disposition decisions). Other impl-side operations MAY consume it as needed.
```

#### `SPECIFICATION/contracts.md` Spec Reader closing paragraph

Update the count:

```diff
-The Spec Reader is NOT a Claude Code skill (no slash command, no namespace surface); it is an internal API within each `livespec-impl-*` plugin. This distinguishes it from the nine cross-boundary contract skills defined in §"Implementation-plugin contract — the 9-skill surface".
+The Spec Reader is NOT a Claude Code skill (no slash command, no namespace surface); it is an internal API within each `livespec-impl-*` plugin. This distinguishes it from the ten cross-boundary contract skills defined in §"Implementation-plugin contract — the 10-skill surface".
```

#### `SPECIFICATION/constraints.md` line 285 cross-boundary check mechanism

Update the parenthetical mechanism description to name `detect-impl-gaps` and drop the "in-process dry-run" framing:

```diff
-The five work-item structural invariants codified in `contracts.md` §"Doctor cross-boundary invariants" (`gap-tracking-one-to-one`, `no-orphan-dependency`, `no-stale-gap-tied`, `no-duplicate-gap-id`, `no-stalled-epic`) are cross-boundary checks: each queries the active impl-plugin's machine surface (the `list-work-items --json` thin-transport skill, plus an in-process dry-run of `capture-impl-gaps` for snapshot gap-id enumeration) rather than livespec-internal state.
+The five work-item structural invariants codified in `contracts.md` §"Doctor cross-boundary invariants" (`gap-tracking-one-to-one`, `no-orphan-dependency`, `no-stale-gap-tied`, `no-duplicate-gap-id`, `no-stalled-epic`) are cross-boundary checks: each queries the active impl-plugin's machine surface (the `list-work-items --json` and `detect-impl-gaps --json` thin-transport skills) rather than livespec-internal state.
```
