---
topic: proposal-critique-v15
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-23T18:30:00Z
---

# Proposal-critique v15

A recreatability-and-cross-doc-consistency critique pass over v015
`PROPOSAL.md`, with targeted checks against
`deferred-items.md` and
`python-skill-script-style-requirements.md`.

The critique is grounded in the recreatability test: could a
competent implementer, reading the current brainstorming docs alone
and the v015 PROPOSAL.md, produce a working livespec without being
forced to guess between conflicting rules or invent semantics that
the docs leave unspecified?

v015 was a tight 4-item pass (O1-O4) focused on path
parameterization, central topic canonicalization, and retry
de-over-specification. Several of those v015 changes interact with
older decisions in ways that surface fresh recreatability gaps,
which this v16 pass surfaces.

Findings in this pass:

- **Major gaps (2 items):** P1-P2
- **Significant gaps (2 items):** P3-P4
- **Smaller cleanups (1 item):** P5

## Proposal: P1 — `anchor-reference-resolution` scope under `minimal`'s `spec_root: "./"` walks the entire repo root

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: incorrectness (with cross-template malformation).**

The `anchor-reference-resolution` doctor-static check (PROPOSAL.md
lines ~2089-2102) is defined as:

> All Markdown links in all files under `<spec-root>/` (spec files,
> READMEs, proposed-change files, revision files) with anchor
> references resolve to existing headings in the referenced files.

Under v009 I7 every doctor-static check parameterizes path
references against `DoctorContext.spec_root`. Under the `minimal`
template added in v014 N1, `spec_root: "./"` resolves to the
project root.

Composing those two rules, this check walks "all files under the
project root" for every minimal-template-using project. That
sweeps in:

- the project's own top-level `README.md` (unrelated to the
  livespec spec),
- any other markdown the user keeps at repo root (CONTRIBUTING.md,
  CHANGELOG.md, design notes, etc.),
- markdown anywhere in user source trees (`src/**/*.md`,
  `docs/**/*.md`),
- markdown inside `.github/`, `node_modules/` if present, etc.

The parenthetical "(spec files, READMEs, proposed-change files,
revision files)" reads as either a scope limitation or an
enumeration of expected categories — it is genuinely ambiguous.
Even if interpreted as a scope limitation, "READMEs" still pulls in
the project's top-level README, and "spec files" requires defining
which files at repo root count as spec files (which the check
itself currently has no way to know under minimal).

This is a recreatability defect because two competent implementers
will not converge:

- one will treat the parenthetical as a scope limit and walk
  `README.md` + the canonical spec file set;
- another will treat it as an enumeration and walk every markdown
  file under `<spec-root>/`;
- a third will scope-limit to spec files only by introspecting
  the active template's `specification-template/` walk.

All three claim to satisfy the current text; only one is sensible
behavior under minimal.

The same scoping ambiguity arguably affects `out-of-band-edits`
(though there the comparison is over template-declared spec files,
which gives a tighter natural scope), and any future doctor-static
check that walks `<spec-root>/` recursively.

### Motivation

This is the largest recreatability blocker introduced — incidentally
— by v014 N1's introduction of `minimal` plus v015 O1's
generic-path parameterization. v015 cleanly fixed the prose layer,
but the path semantics question for already-defined checks under
the new spec_root setting was not re-examined. Under v015, an
implementer of `minimal` cannot tell whether `doctor` should
warn about anchor references in their project README.

The NLSpec guidelines require unambiguous interfaces; here the
"interface" — what set of files this check inspects — depends on
which interpretation the implementer reaches.

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** Scope every `<spec-root>/`-walking
doctor-static check (today, just `anchor-reference-resolution`;
also clarify for any future) to a precisely defined set:

- the active template's declared spec files (resolved from the
  template's `specification-template/` walk + the spec-root-relative
  paths),
- the spec-root `README.md` (when the template declares one),
- every file under `<spec-root>/proposed_changes/`,
- every file under `<spec-root>/history/**/proposed_changes/`,
- every file under `<spec-root>/history/**/<spec-file>` for each
  template-declared spec file.

Rewrite the `anchor-reference-resolution` check description to
spell out this scope explicitly. Add a corresponding subsection to
`deferred-items.md`'s `static-check-semantics` entry codifying the
walk algorithm so the implementer pass cannot diverge.

**Option B:** Add an explicit rule that for the `minimal` template
specifically, doctor-static checks restrict their walk to
`SPECIFICATION.md`, `proposed_changes/`, and `history/`, treating
those as the "spec tree" carve-out. This is narrower but still
relies on per-template special-casing rather than a uniform
spec-root semantic.

**Option C:** Constrain the `minimal` template to live under a
`spec_root` that is NOT `"./"` (e.g., default it to
`"livespec-spec/"` or similar). This avoids the issue but reverses
v014 N1's explicit "single-file at repo root" decision.

---

## Proposal: P2 — Seed's `.livespec.jsonc` creation timing under N1's pre-seed dialogue is unspecified

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: ambiguity / incompleteness.**

v014 N1 introduces a pre-seed SKILL.md-prose dialogue that prompts
the user to choose a template when `.livespec.jsonc` is absent.
PROPOSAL.md states (paraphrased from §"seed"):

- "writes `.livespec.jsonc` at the end of the seed flow with
  `template: "<chosen-value>"`" (lines 1432-1434),
- "Creates `.livespec.jsonc` with full commented defaults if
  absent, using the user-chosen `template` value from the
  pre-seed dialogue" (lines 1444-1446),
- the wrapper input schema `seed_input.schema.json` is
  `{files: [{path, content}], intent}` — no `template` field,
- `bin/seed.py --seed-json <path>` "reads the JSON, writes each
  file to its specified path, creates `<spec-root>/history/v001/`
  ..." (lines 1475-1485) — no explicit mention of writing
  `.livespec.jsonc`,
- post-step doctor-static runs after the wrapper completes,
  including the `livespec-jsonc-valid` and `template-exists`
  checks.

Three plausible implementations satisfy the current text:

1. The LLM includes `.livespec.jsonc` as a `files[]` entry in
   the seed-input payload (with the chosen template embedded).
   The wrapper writes it like any other file. Post-step
   doctor-static then sees a coherent `.livespec.jsonc`.
2. `bin/seed.py` writes `.livespec.jsonc` directly from a
   hardcoded skeleton, but the schema gives it no `template`
   value to embed — so the wrapper would have to default to
   `"livespec"`, which contradicts the user's pre-seed choice
   when the user picked `minimal` or a custom path.
3. The LLM writes `.livespec.jsonc` separately via the Write
   tool AFTER `bin/seed.py` exits, so the wrapper never sees
   it. Under this interpretation, post-step doctor-static runs
   with the file still absent. v014 N3 bootstrap lenience
   would emit a `skipped` finding (or a fail Finding for
   `template-exists`, depending on `template_load_status`),
   defeating the purpose of post-step validation on a fresh
   seed.

Interpretation #1 is the only one that produces a coherent
post-step state, but the spec doesn't say so. The wrapper
contract for `.livespec.jsonc` ownership is silent.

This also interacts with v014 N3's bootstrap lenience: lenience
was designed to let `livespec-jsonc-valid` emit a fail Finding
when `.livespec.jsonc` is broken, NOT to silently mask seed's
failure to bootstrap configuration. If interpretation #3 is
allowed, every fresh seed produces a "skipped" `livespec-jsonc-valid`
finding, which is wrong on a successful seed.

### Motivation

This is a recreatability blocker for the most fundamental
sub-command in the system. An implementer can't write a working
seed without choosing one of the three interpretations and
silently committing to it.

The interaction with N1's pre-seed dialogue also affects what
`bin/seed.py` knows at invocation time: without a `template`
field in the payload, the wrapper has no way to know which
template's `specification-template/` to use as a reference for
post-step `template-files-present`. So either the wrapper must
infer it from the payload's `files[]` paths (fragile), or
`.livespec.jsonc` must exist by the time post-step runs, or
`seed_input.schema.json` must carry a `template` field.

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** Codify that `.livespec.jsonc` is
written by the wrapper as part of `bin/seed.py`'s deterministic
file-shaping work, BEFORE post-step doctor-static runs. Extend
`seed_input.schema.json` with a top-level required field
`template: string` carrying the chosen template name (built-in
or user-provided path). The wrapper:

1. writes `.livespec.jsonc` with full commented schema +
   `template: "<value>"`,
2. writes each `files[]` entry,
3. writes `<spec-root>/history/v001/` and the seed
   auto-capture artifacts,
4. runs post-step doctor-static against a fully-bootstrapped
   project tree.

The `wrapper-input-schemas` deferred entry is widened to add
the `template` field to `seed_input.schema.json`.

**Option B:** Codify that `.livespec.jsonc` is written by the
LLM as a `files[]` entry in the seed-input payload. The
SKILL.md prose for `seed` MUST instruct the LLM to include it.
This is simpler at the wrapper layer (no schema change) but
puts more burden on the SKILL.md prose authoring (which is
itself deferred), and trusts the LLM to emit a valid
`.livespec.jsonc` payload — including the full commented
schema PROPOSAL.md says seed creates.

**Option C:** Codify that `.livespec.jsonc` is written by the
LLM via Write tool AFTER `bin/seed.py` exits, and mark seed
as ALSO exempt from post-step doctor-static (alongside its
existing pre-step exemption). This is the weakest option
because it abandons post-step validation on the most critical
bootstrap moment.

---

## Proposal: P3 — Author-derived topic-hint truncation can chop the `-critique` suffix

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: incompleteness.**

v015 O3 centralized topic canonicalization at `bin/propose_change.py`'s
boundary. `critique` passes the raw topic hint
`<resolved-author>-critique` into that shared rule (PROPOSAL.md
lines ~1689-1700, 1568-1581).

The canonicalization rule (PROPOSAL.md §"Topic canonicalization"
and `deferred-items.md`'s `static-check-semantics` entry):

1. lowercase
2. replace runs of non-`[a-z0-9]` characters with single hyphen
3. strip leading/trailing hyphens
4. truncate to 64 characters
5. empty result → `UsageError` (exit 2) per O3

Step 4 truncates the WHOLE composite string, including the
`-critique` suffix. If the slugified `<resolved-author>` portion
exceeds ~55 characters, the suffix is sliced off mid-word; if it
exceeds 64, the suffix is fully eliminated.

Plausible long author values are not pathological:

- `"Claude Opus 4.7 (1M context)"` slugifies to
  `"claude-opus-4-7-1m-context"` (26 chars; safe today),
- `"Claude Opus 4.7 (1M context, livespec-eval-mode)"` slugifies
  to `"claude-opus-4-7-1m-context-livespec-eval-mode"` (45 chars;
  safe with `-critique` appended → 54 chars total),
- `"Claude Opus 4.7 (1M context, livespec-evaluation-mode-internal)"`
  slugifies to ~60 chars; `-critique` appended exceeds 64 and is
  truncated to `-critiqu` or fully cut depending on whose-author
  string.

This produces three concrete defects:

1. **Critique-vs-propose-change filename collision.** A critique
   from author `X` and a propose-change with `<topic>` matching
   the truncated form of `<X-slug>-critique` collide in
   `<spec-root>/proposed_changes/`. Collision disambiguation
   (N6 `-2`, `-3` suffixes) hides the semantic difference: the
   user can no longer tell from the filename whether a file is
   author-X's critique or author-X's same-name propose-change.

2. **Truncated `-critique` suffix on near-boundary cases.** A
   55-char author slug + `-critique` (9 chars) = 64 chars,
   accepted intact. A 56-char author + `-critique` truncates to
   `<author>-critiqu` (64 chars). The filename is no longer
   recognizable as a critique artifact.

3. **Future audit-trail breakage.** Tools downstream of livespec
   (e.g., per-author critique counts, review dashboards) can no
   longer reliably extract `<author>` and `-critique` from the
   `topic` field; the suffix may or may not be present.

The rule also doesn't say which order: does propose-change
canonicalize and THEN truncate, or canonicalize WITH truncation
applied to the full inbound? The deferred entry lists the steps
in order including step 4 truncation, suggesting truncation is
applied to the full canonicalized string. This is the source of
the suffix-loss.

### Motivation

This is a semantic-precision defect for a v015-just-codified
boundary. v015 O3's centralization was the right architectural
choice, but the truncation interaction with critique's raw
topic-hint composition wasn't examined.

### Proposed Changes

Three candidate resolutions:

**Option A (recommended):** Reserve a fixed-suffix budget at
canonicalization. When `propose-change` (or any future raw-hint
caller) supplies a topic hint with the conventional `-critique`
suffix, the wrapper canonicalizes by applying steps 1-3 to the
full string, then truncates the AUTHOR portion (everything before
the final `-critique` suffix) to `64 - len("-critique") = 55`
characters, then re-appends `-critique`. The suffix is preserved
verbatim. Generalize: any caller that wants suffix preservation
passes a `--reserve-suffix <text>` flag to `bin/propose_change.py`,
or `critique` uses a dedicated wrapper-internal API path that
encodes the same reservation. Document the rule in PROPOSAL.md
§"Topic canonicalization" and codify the algorithm in the
`static-check-semantics` deferred entry.

**Option B:** Tighten the algorithm so truncation occurs BEFORE
suffix re-application: canonicalize `<resolved-author>` (without
the `-critique`) to 64 chars, then `critique` appends `-critique`
post-canonicalization, accepting that the result may exceed 64.
PROPOSAL.md's topic canonicalization stops enforcing the 64-char
cap on caller-assembled hints. Simpler, but breaks O3's
single-rule cleanliness.

**Option C:** Lower the practical limit so collisions are rare:
keep the 64-char rule, but also document an advisory limit
("authors with slugs over 50 characters will see their critique
suffix truncated; SHOULD use shorter author identifiers"). This
is the weakest option — it documents the bug without fixing it.

---

## Proposal: P4 — `topic` YAML front-matter field is unspecified for `out-of-band-edit-` files

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/deferred-items.md`

### Summary

**Failure mode: ambiguity.**

The `out-of-band-edits` doctor-static check creates
`<spec-root>/proposed_changes/out-of-band-edit-<UTC-seconds>.md`
files (PROPOSAL.md lines ~2059-2071). These files are
proposed-change files and MUST conform to the proposed-change
file format (lines 2227-2289), which requires YAML front-matter:

```yaml
---
topic: <kebab-case-topic>
author: <author-id>
created_at: <UTC ISO-8601 seconds>
---
```

PROPOSAL.md says (lines 2238-2241):

> The `topic` value is the wrapper-canonicalized kebab-case form
> of the inbound topic hint supplied to `propose-change`
> directly or delegated by `critique`.

But `out-of-band-edits` does NOT route through `propose-change`'s
canonicalization rule (v015 O3 explicitly scopes to
`propose-change` and `critique`). The file is created by the
`doctor-out-of-band-edits` check directly. So what value is
written into the `topic` field?

Three plausible implementations:

1. The literal filename stem: `out-of-band-edit-1729707000`.
   This already happens to be kebab-case, so it satisfies the
   format. But it's a wrapper-internal convention rather than a
   canonicalization output.
2. A hardcoded constant: `out-of-band-edit`. Multiple back-to-
   back backfill events would all share this `topic` value,
   which weakens the field's semantic value as a per-file
   identifier.
3. The `<UTC-seconds>` suffix with a prefix: `oob-1729707000`
   or similar shorter form.

The doctor-out-of-band-edits behavior must define this — but
PROPOSAL.md is silent. The proposed-change format rule about
`topic` was written assuming all proposed-change files come
through `propose-change`'s canonicalization; v014 N6's
codification of `out-of-band-edit-<UTC-seconds>.md` as a
SEPARATE filename convention surfaced (but did not resolve)
that the front-matter rule needs a parallel.

The same gap applies to v014 N6's note that the
out-of-band-edit timestamped form is "not unified" with
propose-change/critique's monotonic-counter convention — that
disunification was specified at the filename layer but not at
the front-matter layer.

### Motivation

This is a recreatability gap for a low-frequency but real flow.
`out-of-band-edits` runs on every doctor invocation; on a
project that's seen out-of-band edits, the backfill creates a
proposed-change file that doctor's other static checks (notably
the proposed-change format checker, when implemented) will then
inspect. An implementer can't write the backfill code without
knowing what `topic` value to emit.

### Proposed Changes

Two candidate resolutions:

**Option A (recommended):** Codify in PROPOSAL.md §"Static-phase
checks → out-of-band-edits" that the auto-backfilled
proposed-change file's front-matter `topic` field takes the
verbatim value `out-of-band-edit-<UTC-seconds>` (matching the
filename stem). Update §"Proposed-change file format" to note
this exception: the `topic` field is canonicalized when the
file is created via `propose-change`/`critique`; for skill-
auto-generated artifacts (today: out-of-band-edits backfill;
also the seed auto-capture, which already uses `topic: seed`),
the wrapper assigns a documented constant or convention
value. Codify both conventions in the `static-check-semantics`
deferred entry's "out-of-band-edits semantics" subsection.

**Option B:** Route `out-of-band-edits` backfill through
`propose-change`'s shared canonicalization: pass topic hint
`out-of-band-edit-<UTC-seconds>` as input. This unifies the
canonicalization path but reintroduces the v014 N6 unification
that the spec explicitly rejected (the timestamped form is
intentionally distinct from monotonic-counter collision
disambiguation). Reject as architecturally regressive.

---

## Proposal: P5 — Shebang-wrapper "6-line shape" contradicts the 7-line example

### Target specification files

- `brainstorming/approach-2-nlspec-based/PROPOSAL.md`
- `brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md`

### Summary

**Failure mode: malformation (self-contradiction in the same
section).**

PROPOSAL.md §"Shebang-wrapper contract" (lines ~341-352) says:

> Each `bin/<cmd>.py` MUST consist of exactly the following
> 6-line shape (no other lines, no other statements):

followed by an example with a blank line between the import
block and the `raise SystemExit(main())` statement. Counting
visible lines:

1. `#!/usr/bin/env python3`
2. `"""Shebang wrapper for ..."""`
3. `from _bootstrap import bootstrap`
4. `bootstrap()`
5. `from livespec.<module>.<submodule> import main`
6. (blank line)
7. `raise SystemExit(main())`

That's 7 lines. The contract says "6-line shape (no other
lines, no other statements)". The blank line is itself a line.

The same contradiction is present verbatim in the style doc's
§"Shebang-wrapper contract".

Three downstream consequences:

1. `check-wrapper-shape` (the AST-lite check codifying this
   rule) cannot tell whether to enforce 6-line literally
   (rejecting wrappers with the blank — including the
   ones the example shows) or 7-line accepting the blank.
2. `tests/bin/test_wrappers.py` meta-test has the same
   ambiguity.
3. v011 K3 wrapper coverage tests already import wrappers
   matching the example's 7-line shape; if the AST check
   later enforces strict 6-line, the wrappers break.

### Motivation

Pure cleanup, but a real malformation that has propagated
through every revision since v007 introduced the 6-line
contract (v007 G2 → v011 K3 hardened it).

### Proposed Changes

Two candidate resolutions:

**Option A (recommended):** Rewrite the contract as "exactly
the following shape, comprising 6 statements (no other lines
beyond the optional blank between the imports and `raise
SystemExit`, and no other statements)". Codify the optional
blank in `check-wrapper-shape`'s semantics (in
`deferred-items.md`'s `static-check-semantics` entry). Keep
the example as shown.

**Option B:** Drop the blank line from the canonical example;
update PROPOSAL.md and the style doc to render the wrapper as
6 literal lines; tighten `check-wrapper-shape` to reject any
wrapper with a blank line inside the body. This is stricter
but contradicts the existing example's readability.
