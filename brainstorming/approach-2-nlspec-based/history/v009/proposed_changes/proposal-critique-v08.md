---
topic: proposal-critique-v08
author: Claude Opus 4.7 (1M context)
created_at: 2026-04-22T21:00:00Z
---

# Critique scope

This critique evaluates **v008 PROPOSAL.md** plus its companion
`python-skill-script-style-requirements.md` against the embedded
`livespec-nlspec-spec.md` guidelines. Primary focus: the recreatability
test over v008 — given only PROPOSAL.md, the Python style doc,
`livespec-nlspec-spec.md`, and `deferred-items.md`, can a competent
implementer produce a working v008 livespec plugin?

The v008 revision (`history/v008/proposed_changes/proposal-critique-v07-revision.md`)
locked in 16 dispositions (H1-H16) covering bootstrap sys.path fix,
JSONC vendoring (jsoncomment), argparse seam in `io/cli.py`, the
canonical SKILL.md body shape, ruff `PLR0913 + PLR0917` at 6, explicit
`--seed-json` / `--revise-json` wrapper inputs, context-dataclass
minimum fields, doctor allowed-tools honesty (`Bash + Read + Write`),
factory-validator compile cache in `fastjsonschema_facade.py`,
`proposal_findings` / `doctor_findings` schema split, out-of-band-edits
pre-backfill guard, frozen directory-README paragraphs, widened
`static-check-semantics` deferred item, GFM anchor algorithm inline,
`tests/fixtures/` CLAUDE.md carve-out, and canonical seed auto-capture
content. This critique does **not** reopen any of those decisions.

The recreatability test over v008 surfaces gaps in four clusters:

1. **Lifecycle chain semantics vs seed's file-creation purpose.** The
   wrapper-side ROP chain (pre-step doctor static + sub-command logic
   + post-step doctor static) is codified for "every sub-command except
   `help` and `doctor`" — including `seed`. But `seed`'s purpose is to
   produce the very files that `template-files-present` and
   `proposed-changes-and-history-dirs` check for. On first invocation,
   pre-step fails before `seed_run` ever executes. The lifecycle
   invariant and seed's creation-from-empty contract contradict.
2. **ROP composition types left implicit.** `run_static(ctx) ->
   IOResult[FindingsReport, DoctorInternalError]` composed as
   `flow(ctx, run_static, bind(<cmd>_run), bind(run_static))` requires
   `<cmd>_run` to accept a `FindingsReport` (not a context). And
   `Result`-returning pure functions (`parse/`, `validate/`) are shown
   chained into `IOResult` flows via plain `bind(...)`, which doesn't
   type-check under dry-python/returns without `bind_result`. Two
   load-bearing composition gaps.
3. **Schema ↔ dataclass generation path unspecified.** Contexts depend
   on `LivespecConfig`, `SeedInput`, `ProposalFindings`, `ReviseInput`
   — "dataclasses generated from the corresponding `*.schema.json`
   files." No generator is named, no hand-authoring is stated, and no
   deferred-items entry covers it. `fastjsonschema` validates; it does
   not emit dataclasses.
4. **LLM↔Python interface seams that have no wire protocol.** SKILL.md
   prose names `livespec.validate.<name>.validate` as the schema
   validation entry point — but the LLM can only invoke Python through
   the Bash tool, and no shell invocation shape (argv, stdin, stdout,
   exit-code contract) is specified. `reviser_human` wants `git config
   user.name` + `user.email`, which is NOT in PROPOSAL.md's
   "documented git reader" allowlist. `reviser_llm` wants a
   "host-provided LLM id," but no host API is named.

Items are labelled `I1`–`I14` (the `I` prefix distinguishes
"v008 gap" findings from prior critiques' `G`- and `H`-prefixed
items). Each item carries one of the four NLSpec failure modes:

- **ambiguity** — admits multiple incompatible interpretations.
- **malformation** — self-contradiction within or across documents.
- **incompleteness** — missing information needed to act.
- **incorrectness** — internally consistent but specifies behavior
  that cannot work as written.

Major gaps appear first (block recreatability outright), then
significant gaps (force load-bearing guesses), then smaller cleanup.

---

## Major gaps

These items would block a competent implementer from producing a
working v008 livespec without filing additional propose-changes.

---

## Proposal: I1-seed-prestep-contradicts-seed-purpose

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**malformation** (self-contradiction between the universal
lifecycle invariant and seed's creation-from-empty contract).

### Summary

PROPOSAL.md §"Sub-command lifecycle orchestration" says pre-step +
post-step doctor static runs for "every sub-command except `help`
and `doctor`" — including `seed`. But `seed`'s whole purpose is to
create the template-declared spec files. On the first-ever
invocation, none of those files exist yet, so the pre-step
`template-files-present` check fails and `seed_run` is never
reached. Two mutually incompatible requirements coexist in v008.

### Motivation

PROPOSAL.md lines 396-410 (lifecycle):

> For sub-commands that have a pre-step and post-step doctor static
> (every sub-command except `help` and `doctor`), `bin/<cmd>.py` →
> `livespec.commands.<cmd>.main()` composes:
>
> ```
> run_static(ctx)            # pre-step
>    |> bind(<sub_command_run>)
>    |> bind(run_static)     # post-step
> ```

PROPOSAL.md lines 1253-1260 (static-phase checks):

> **`template-files-present`** — All template-required files
> (derived by walking the template's `specification-template/`
> directory) are present at their expected repo-root-relative paths.
>
> **`proposed-changes-and-history-dirs`** — `proposed_changes/` and
> `history/` directories exist under `SPECIFICATION/` and contain
> their skill-owned `README.md`.

PROPOSAL.md lines 979-985 (seed idempotency):

> If any template-declared target file already exists at its target
> path, `seed` MUST refuse and list the existing files.

So `seed`'s contract is "fail if files exist"; pre-step doctor's
contract is "fail if files are missing." Pre-step is the blocker on
a green-field repo, and `seed`'s idempotency is the blocker on a
seeded repo. Seed can never pass pre-step on its happy path without
the user passing `--skip-pre-check`, which PROPOSAL.md line 658-660
describes as an "emergency recovery" flag, not the normal first-run
workflow.

`seed_run` can also NOT produce the files during sub-command logic
and let post-step catch up: post-step also runs `template-files-
present`, and if `seed_run` somehow produced them, post-step would
pass — but pre-step already killed the chain before `seed_run` ran.

This also breaks `out-of-band-edits`: `git_head_available` may be
false on a fresh repo (no HEAD commit yet), in which case the check
skips — that one's OK. But every other file-presence check is hit.

### Proposed Changes

Decide on one of the following and codify it in PROPOSAL.md:

- **A. Seed is exempt from pre-step doctor static.** Only post-step
  runs. `seed`'s ROP chain becomes `seed_run(ctx) |>
  bind(run_static)`. PROPOSAL.md §"Sub-command lifecycle
  orchestration" adds seed to the pre-step exemption list alongside
  `help` and `doctor`. Rationale: pre-step cannot meaningfully run
  before the spec exists.

- **B. Pre-step for seed runs a DIFFERENT static-check subset.**
  Only checks that apply in a pre-seed world (e.g.,
  `livespec-jsonc-valid` if present, template-exists). Introduces a
  "pre-seed applicable checks" subset in the registry and requires
  static checks to declare which phases they apply in.

- **C. Pre-step runs but conditionally skips checks when the spec
  doesn't exist.** Each file-presence check emits `status:
  "skipped"` when its target directory isn't there yet.
  `status: "skipped"` already doesn't cause a fail exit (PROPOSAL.md
  line 1362-1363). Effectively pre-step becomes a no-op for seed,
  by construction of the checks.

- **D. First-run seed is documented as requiring `--skip-pre-check`.**
  PROPOSAL.md explicitly states the first invocation always passes
  that flag; subsequent invocations (on a re-seed) are refused
  anyway per idempotency. Demotes `--skip-pre-check` from
  emergency-only to a documented seed-time flow.

Recommend **A** (seed exempt). The entire purpose of pre-step is to
verify spec invariants before mutating; pre-seed there is no spec
to verify, so the exemption matches reality. B and C add complexity
that doesn't buy anything (the subset of checks that *would* pass
pre-seed is trivial). D muddles the meaning of `--skip-pre-check`.

The `deferred-items.md` `static-check-semantics` entry (already
covers doctor-cycle semantics) should mention that `seed` has no
pre-step.

---

## Proposal: I2-run-static-return-type-in-lifecycle-chain

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**ambiguity** (composition types unstated; two plausible readings
produce incompatible implementations).

### Summary

`run_static(ctx: DoctorContext) -> IOResult[FindingsReport,
DoctorInternalError]` (style doc line 396) is composed in the
wrapper's lifecycle chain as `run_static(ctx) |> bind(<cmd>_run) |>
bind(run_static)`. The `bind` semantics require `<cmd>_run` to
accept `run_static`'s success value (a `FindingsReport`) — but
`<cmd>_run` needs a `DoctorContext` (or the specialized sub-command
context that embeds it). And the post-step `run_static` requires a
`DoctorContext` as input, so `<cmd>_run` must produce one. Two
incompatible readings of the same chain.

### Motivation

Style doc lines 396-402 (orchestrator):

> ```python
> def run_static(ctx: DoctorContext) -> IOResult[FindingsReport, DoctorInternalError]:
>     from livespec.doctor.static import REGISTRY
>     results = [run_fn(ctx) for _slug, run_fn in REGISTRY]
>     return Fold.collect(results, IOSuccess(())).map(
>         lambda findings: FindingsReport(findings=list(findings))
>     )
> ```

Style doc lines 404-412 (wrapper composition):

> ```python
> def main() -> int:
>     ctx = build_context()
>     chain = flow(
>         ctx,
>         run_static,                       # pre-step (skipped if --skip-pre-check)
>         bind(seed_run),                   # sub-command logic
>         bind(run_static),                 # post-step
>     )
>     return derive_exit_code(chain)
> ```

Under `dry-python/returns`, `bind(f)` applied to an `IOResult[A,
E]` requires `f: A -> IOResult[B, E]`. The chain above passes
`IOResult[FindingsReport, ...]` into `seed_run`, so `seed_run` must
take a `FindingsReport`. But the documented signature is
`seed_run(ctx: SeedContext) -> IOResult[...]`, and a
`FindingsReport` is not a `SeedContext`.

Worse, even if `seed_run(FindingsReport)` somehow worked, it would
then need to produce a `DoctorContext` (or similar) to feed into
post-step `run_static` — meaning `seed_run` becomes context-aware
in a way that contradicts the pure railway payload discipline.

There's also a second, related gap: in the sub-command wrapper
case, pre-step and post-step findings ARE produced but there is no
defined contract for where they go. `bin/doctor_static.py` has an
explicit stdout contract (`{"findings": [...]}`). Sub-command
wrappers (`bin/seed.py` etc.) have NO findings stdout contract
defined. Do the findings go to stderr via structlog? Are they
accumulated and emitted as JSON on failure only? Silent on success?

### Proposed Changes

Decide on one of the following and codify the exact signatures in
both PROPOSAL.md §"Sub-command lifecycle orchestration" and the
style doc §"Railway-Oriented Programming" and §"Sub-command
lifecycle composition":

- **A. `run_static` is context-pass-through for lifecycle use.**
  Introduce a second, narrower orchestrator — e.g.,
  `run_static_gated(ctx) -> IOResult[DoctorContext,
  DoctorInternalError]` — that runs the registry, on any
  `status: "fail"` finding converts to `IOFailure(PreconditionError(
  findings=...))`, on all-pass returns `IOSuccess(ctx)` (passing
  context through). Sub-command chains use `run_static_gated`;
  `bin/doctor_static.py` uses `run_static` (keeps FindingsReport
  stdout contract). Emit the report via structlog before gating so
  findings are not lost.

- **B. `run_static`'s success value IS the context, plus a side-
  effect structlog emission.** Drop `FindingsReport` from the
  success track. `run_static(ctx) -> IOResult[DoctorContext,
  DoctorInternalError]`. `bin/doctor_static.py` replaces its
  stdout-findings contract with a dedicated writer function that
  runs the registry, emits JSON to stdout, and exits — separate
  function from `run_static`. Simpler but requires rewriting
  `doctor_static` to not compose through `run_static`.

- **C. The wrapper chain is NOT `flow(ctx, run_static,
  bind(cmd_run), bind(run_static))`.** Rewrite the chain shape in
  PROPOSAL.md and the style doc to something like `flow(ctx,
  run_static, bind(lambda report: gate_on_failure(report, ctx)),
  bind(cmd_run), bind(run_static_and_gate))` — explicit gate
  functions that extract findings for emission, check for
  failures, and pass context through on success.

- **D. The lifecycle chain is illustrative pseudocode; the actual
  Python code is hand-written per-sub-command without using
  `flow` / `bind`.** Honesty about the compositional limits of
  Python + dry-python/returns in this specific chain shape.

Recommend **A** (introduce `run_static_gated`). Preserves the
`bin/doctor_static.py` stdout contract unchanged (so the v008 H10
findings-schema split stays coherent); gives sub-command wrappers
a clean type signature; keeps the railway intact. The sub-command
wrapper findings-emission question (where do pre/post findings go
when the wrapper isn't `doctor_static`?) is resolved the same way:
they are logged to stderr via structlog as `info`-level findings,
and the gate only fails the chain on `status: "fail"`. This also
means every sub-command's pre/post findings are visible to the user
through the LLM's stderr reading (the LLM narrates from structlog
lines, not from a stdout contract).

Update the `static-check-semantics` deferred item to also cover the
gate function's exact semantics (what `status: "fail"` maps to on
the railway; how `status: "skipped"` is surfaced).

---

## Proposal: I3-schema-to-dataclass-generation-unspecified

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**incompleteness** (the mechanism that produces dataclasses from
schemas is undefined, and no deferred-items entry covers it).

### Summary

Style doc §"Context dataclasses" says:

> `LivespecConfig`, `SeedInput`, `ProposalFindings`, and `ReviseInput`
> are dataclasses generated from the corresponding `*.schema.json`
> files; each schema carries a `$id` naming the dataclass.

But no generator is named. `fastjsonschema` validates instances
against schemas; it does not emit Python dataclass definitions. No
vendored library produces dataclasses from schemas. No
`deferred-items.md` entry covers authoring or generating these
dataclasses. The `wrapper-input-schemas` deferred entry covers
authoring the four schemas but not the paired dataclasses.

An implementer reading v008 is left to guess: do they hand-author
four dataclasses (one per schema) and trust the CI to catch drift?
Or do they stand up a codegen step? If codegen, which tool (there
are candidates: `datamodel-code-generator`, `json-schema-to-dataclass`,
etc.) — and does it get added as a dev-time dependency? Does it
run at commit time, or at `just check`, or offline?

This is a recreatability-blocker because the style doc's type
system and railway contracts depend on these dataclass types
existing with specific fields.

### Motivation

Style doc lines 304-308:

> `LivespecConfig`, `SeedInput`, `ProposalFindings`, and `ReviseInput`
> are dataclasses generated from the corresponding `*.schema.json`
> files; each schema carries a `$id` naming the dataclass. Fields are
> filled at validation time (via the factory-shape validators under
> `livespec/validate/`).

PROPOSAL.md lines 124-131 (schemas/ directory) and the context
dataclasses at style doc lines 264-302 all depend on these
dataclasses being real Python types with concrete fields.

Factory-shape validators under `livespec/validate/` return
`Result[T, ValidationError]` where `T` is one of these dataclasses
— so the validator has to produce a dataclass instance. Without a
defined generation path, the validator can't be written.

### Proposed Changes

Decide between:

- **A. Hand-author the dataclasses.** Add a style-doc subsection
  "Dataclass authorship" stating that each `$id` schema has a
  paired hand-authored dataclass at a canonical location (e.g.,
  `livespec/schemas/__init__.py` re-exports every dataclass;
  per-schema files under `livespec/schemas/dataclasses/`). A new
  AST/runtime check `check-schema-dataclass-pairing` asserts every
  `schemas/*.schema.json` has a matching dataclass with the same
  `$id`-derived name and every field listed in the schema, and
  vice versa. Drift between schema and dataclass fails the check.
  No codegen step; the schema is the wire contract and the
  dataclass is the type. Tests validate instances against BOTH.

- **B. Codegen at `just check` / build time.** Add a vendored (or
  pinned dev-time) tool like `datamodel-code-generator`. Add a
  recipe `just gen-dataclasses` that regenerates dataclasses from
  schemas; `just check-generated-up-to-date` fails if the
  committed generated files disagree with a fresh regeneration.
  Generated files live under `livespec/schemas/_generated/` and
  are excluded from hand-edit via `check-generated-no-edit`. More
  tool-weight; removes drift risk.

- **C. Skip dataclasses; use `dict` in the railway payload.** Drop
  the "dataclasses generated from schemas" claim entirely.
  `SeedContext.seed_input` is a `dict`, not a `SeedInput`.
  Validators return `Result[dict, ValidationError]` and the caller
  reads dict keys. Loses pyright strict's structural type narrowing
  through the railway (pyright can't enforce schema shape on a
  `dict`).

- **D. Skip dataclasses; use `TypedDict`.** Similar to C but with
  `TypedDict` so pyright sees the shape. TypedDicts can be hand-
  authored concisely and enforce field presence / types in strict
  mode. Validators return `Result[SeedInput, ValidationError]`
  where `SeedInput` is a `TypedDict`. Less runtime ceremony than
  dataclasses.

Recommend **A** (hand-author dataclasses + paired `check-schema-
dataclass-pairing`). Rationale: v006-v008 established strongest-
possible guardrails (pyright strict + ROP + AST enforcement); a
mechanical pairing check aligns with that philosophy without
introducing a codegen toolchain that complicates vendoring. The
hand-authoring surface is small (four dataclasses plus
`LivespecConfig`); drift is an AST check away.

Add a new deferred-items entry `dataclass-schema-pairing` (or
widen `wrapper-input-schemas` to include the paired dataclass
authorship). Add `check-schema-dataclass-pairing` to the canonical
`just` target list. Update PROPOSAL.md and style doc to state
"each schema has a paired hand-authored dataclass with the same
fields; pairing enforced by `check-schema-dataclass-pairing`."

---

## Significant gaps

These items don't block recreatability outright, but they force an
implementer to make load-bearing guesses that could produce
behaviors incompatible across independent implementations.

---

## Proposal: I4-supervisor-return-rule-self-contradictory

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**malformation** (self-contradiction within one sentence).

### Summary

Style doc §"Type safety" states:

> Every public function's return annotation MUST be `Result[_, _]` or
> `IOResult[_, _]` unless it returns `None` for a deliberate side-effect
> boundary (e.g., `main() -> int` supervisors in `commands/*.py`).

The sentence says the exception is for functions that return
`None`, then cites `main() -> int` as the exemplar. `int` is not
`None`. The exception clause and its example are mutually
incompatible.

### Motivation

The supervisors in `commands/<cmd>.py` return `int` (the exit
code). Style doc lines 331-348 show `main() -> int`. If the rule
is literally "only `None`-returning functions are exempt," pyright
strict + `check-public-api-result-typed` will flag every `main() ->
int` as a violation — reading the sentence strictly. If the rule is
"supervisors at the side-effect boundary are exempt regardless of
return type," the sentence wording is wrong.

### Proposed Changes

Rewrite the sentence to match the intent. Options:

- **A. "Supervisors at the side-effect boundary are exempt,
  regardless of return type."** E.g., rewrite to:
  > ...unless the function is a supervisor at a deliberate
  > side-effect boundary (e.g., `main() -> int` in `commands/*.py`,
  > or a function returning `None`). The rule excludes only such
  > supervisors.

- **B. "Only `int`- and `None`-returning supervisors are exempt."**
  Enumerate the allowed return types.

- **C. Drop the exception; supervisor `main()` always returns
  `IOResult[int, Never]`.** Stricter, but the supervisor is at
  the railway boundary; unwrapping-to-int is idiomatic for this
  library; awkward to wrap it.

Recommend **A** (boundary-based exception, regardless of return
type). Matches the established pattern (`main() -> int`
supervisors), preserves idiomatic exit-code return, and is how
`check-public-api-result-typed` must behave in practice anyway.
Add to the `static-check-semantics` deferred item: the precise AST
scope for `check-public-api-result-typed` (exempt functions named
`main` in `commands/**.py` and `doctor/run_static.py`).

---

## Proposal: I5-git-config-read-outside-documented-allowlist

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**malformation** (revision file schema requires a git-read path
that the PROPOSAL.md git section explicitly disallows).

### Summary

PROPOSAL.md §"Git" restricts git reads to "only where documented"
and names a single documented reader:

> The single documented reader in v1 is the `doctor-out-of-band-edits`
> check (out-of-band edit detection), which uses `git show HEAD:`
> to compare committed spec state to history.

But the revision-file front-matter requires populating
`reviser_human: <git user.name and user.email, or "unknown">`.
Producing that field requires reading `git config user.name` and
`git config user.email` — a second read path not in the allowlist.
`seed`'s auto-generated `seed-revision.md` hits the same
requirement.

### Motivation

PROPOSAL.md lines 975-977 (seed auto-capture):

> `reviser_human: <git user or "unknown">`

PROPOSAL.md line 1477 (revision file format):

> `reviser_human: <git user.name and user.email, or "unknown">`

PROPOSAL.md lines 343-350 (git):

> `livespec` MAY read git state (read-only `git status` /
> `git show HEAD:…` / `git ls-files`) only where documented. The
> single documented reader in v1 is the `doctor-out-of-band-edits`
> check...

Reading `git config` is arguably outside "`git status` / `git
show HEAD:` / `git ls-files`" anyway — `git config` is a fourth
command. The allowlist is phrased as exhaustive, and
`git config --get user.name` isn't in it.

`revise` is the sub-command that writes revision files, so `revise`
would have to read git. Same for `seed` (auto-generating
seed-revision.md).

### Proposed Changes

Decide between:

- **A. Extend the git-read allowlist to include `git config
  user.name` + `git config user.email` for the `revise` and
  `seed` wrappers.** PROPOSAL.md §"Git" names both readers
  (out-of-band-edits + revise/seed's author-identity capture).
  `livespec/io/git.py` exposes `get_git_user() -> IOResult[str,
  ...]` returning `"<name> <email>"` or "unknown" on failure.

- **B. Defer the git-read-for-author.** `reviser_human` becomes
  "`<user handle from host, or 'unknown'>`" — the LLM or host
  provides the identity through some other channel (env var,
  Claude Code user context, etc.). Not git. Preserves the narrow
  git allowlist.

- **C. Require the user (or LLM) to provide the identity at
  invocation.** The LLM prompts: "who is authoring this revision?"
  and passes it in the wrapper's `--revise-json` payload. Adds a
  field `reviser_human` to `revise_input.schema.json` and
  `seed_input.schema.json`. The wrapper never reads git.

Recommend **A** (extend the allowlist). Reason: `git config
user.name` / `user.email` is read-only and non-destructive, exactly
the discipline the §"Git" section exists to preserve. It's also
the ergonomic path — the information IS in git and the user
typically expects it to be picked up automatically. Add
`io/git.py::get_git_user` as a new documented reader and update
the §"Git" paragraph to list both readers explicitly.

B is a UX regression (authors typed out for every revision). C
adds a layer of dialogue that isn't in the v008 interactive flow
and complicates wrapper input schemas.

Add to `static-check-semantics` deferred item: the exact fallback
behavior when git is not available or `user.name` isn't set
(returns "unknown" literal; never raises; never leaves the field
empty).

---

## Proposal: I6-result-ioresult-lifting-in-rop-chains

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incorrectness** (the composition idiom as shown does not
type-check under dry-python/returns and cannot be implemented
verbatim).

### Summary

Style doc §"Railway-Oriented Programming" shows:

```python
def run(ctx: DoctorContext) -> IOResult[Finding, DoctorInternalError]:
    return flow(
        ctx.project_root / ".livespec.jsonc",
        read_file,                 # IOResult[str, IOError]
        bind(parse_jsonc),         # Result[dict, ParseError]
        bind(lambda d: validate_config(d, schema)),  # Result[Config, ValidationError]
    ).map(...).lash(...)
```

`bind` on an `IOResult[...]` expects the bound function to return
an `IOResult[...]`. `parse_jsonc` returns a pure `Result[dict,
ParseError]` per the pure-directory discipline, so `bind(parse_jsonc)`
doesn't type-check. The correct dry-python/returns idiom is
`bind_result(parse_jsonc)` (or lift via `IOResult.from_result`).

### Motivation

`dry-python/returns` documents distinct `bind`, `bind_result`,
`bind_ioresult`, `bind_io`, etc., precisely because `Result` and
`IOResult` are different container types and cannot be mixed
through plain `bind`. Style doc lines 390-395 uses plain `bind` on
a mixed chain; the example as written is a type error.

An implementer copying the example verbatim will get pyright
errors under strict mode. They'll then need to decide: use
`bind_result`, or lift `parse_jsonc` to `impure_safe` wrapping
(changing its purity classification), or rewrite with `.map`
differently. Each choice has different downstream implications for
`check-purity`.

### Proposed Changes

- **A. Rewrite the example to use `bind_result` explicitly.**
  Style doc §"Railway-Oriented Programming" Composition idioms
  block:
  ```python
  return flow(
      ctx.project_root / ".livespec.jsonc",
      read_file,                      # IOResult[str, IOError]
      bind_result(parse_jsonc),       # Result[dict, ParseError] lifted
      bind_result(lambda d: validate_config(d, schema)),  # lifted
  ).map(...).lash(...)
  ```
  State explicitly: "Composing `Result`-returning pure functions
  inside an `IOResult` chain MUST use `bind_result`, `map_result`,
  or explicit `IOResult.from_result(...)`. Plain `bind` accepts
  only `IOResult`-returning functions." Cite dry-python/returns
  documentation.

- **B. Rewrite to avoid mixed chains.** Wrap pure parsers with a
  thin impure shim that produces `IOResult`. Trades purity
  semantics: `parse/` and `validate/` still return `Result`, but
  every use site inside an `IOResult` chain goes through an
  `io/`-layer helper. Duplication of the pure/impure boundary at
  every call site.

- **C. Drop the `bind` / `flow` compositional style where mixed.**
  Use explicit `match` statements unwrapping each step. Verbose
  but type-clear.

Recommend **A**. Minimal change; matches dry-python/returns'
intended usage; preserves the purity-by-directory discipline.
Update every PROPOSAL.md and style-doc example that mixes
`IOResult` and `Result` chains (pre-step / post-step composition,
the doctor-check `run()` shape, `io/cli.py` argparse chain).

Add to the `returns-pyright-plugin-disposition` deferred item:
whether the returns pyright plugin gives usable diagnostics for
mis-lifted chains, and whether `bind_result` / `bind_ioresult` are
always the correct lifters for the livespec pure-vs-impure split.

---

## Proposal: I7-specification-path-vs-custom-template-root

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (doctor-static check definitions hard-code
`SPECIFICATION/` literal while the template contract explicitly
allows repo-root or arbitrary-subdirectory layouts).

### Summary

PROPOSAL.md §"Templates" (lines 744-750) says a template MAY place
spec files at the repo root or under any subdirectory structure.
But §"Static-phase checks" references `SPECIFICATION/` literally in
check semantics (e.g., `proposed-changes-and-history-dirs`:
"directories exist under `SPECIFICATION/`"). For a custom template
that doesn't use `SPECIFICATION/`, these checks are either
ill-defined or always fail.

### Motivation

PROPOSAL.md lines 744-750:

> A template MAY place spec files directly at the repo root (e.g.,
> `specification-template/SPEC.md` mirrors to `<repo-root>/SPEC.md`)
> or under any subdirectory structure.

PROPOSAL.md lines 1257-1260:

> **`proposed-changes-and-history-dirs`** —
> `proposed_changes/` and `history/` directories exist under
> `SPECIFICATION/` and contain their skill-owned `README.md`.

PROPOSAL.md line 523-524 (cross-file references):

> Cross-file references in any file inside `SPECIFICATION/` MUST
> use the GitHub-flavored anchor form...

Reading PROPOSAL.md strictly: only the `livespec` built-in template
uses `SPECIFICATION/`. Custom templates may use something different
— so `proposed-changes-and-history-dirs`, `version-directories-
complete`, `version-contiguity`, `anchor-reference-resolution`, and
`out-of-band-edits` either silently treat any template as
`SPECIFICATION/`-based (wrong for custom templates) or must become
template-aware (not specified how).

`gherkin-blank-line-format` already handles template conditionality
(line 1320-1324: "**(Conditional: only when the active template is
`livespec`.)**"). But no other check states whether it's
livespec-only or template-agnostic.

### Proposed Changes

Decide between:

- **A. Declare most doctor-static checks livespec-template-only
  for v1.** PROPOSAL.md §"Static-phase checks" marks each check
  with its template applicability. `template-exists` and
  `template-files-present` remain template-agnostic; the rest are
  "livespec-template only" for v1. Custom-template authors get no
  static-check coverage until they provide template-specific
  checks. Add a non-goal: "Custom-template doctor-static checks"
  for v2.

- **B. Make checks template-aware via config.** Each template
  declares (in `template.json`) its spec-root path relative to
  repo. Doctor reads the config and parameterizes check paths.
  The skill itself stays template-agnostic; every "SPECIFICATION/"
  in check prose becomes "<spec-root>/" parameterized by config.
  Requires `template.json` schema extension (`spec_root: string`,
  default `"SPECIFICATION/"`).

- **C. Hard-code `SPECIFICATION/` as the universal spec root.**
  Remove the "template MAY place spec files at the repo root"
  language from §"Templates." All templates use `SPECIFICATION/`.
  Simpler but reduces template flexibility — arguably against the
  goals-and-non-goals #2 "separate lifecycle from on-disk format."

Recommend **B** (template-aware via config). Rationale: preserves
the template-flexibility goal (which is load-bearing per
`goals-and-non-goals.md` #2, #3, #6); the config extension is
small (one optional field in `template.json`); every check becomes
`<spec-root>/...` parameterized from `DoctorContext`. Custom
templates declare `spec_root: "mydir/"` or `spec_root: "./"` and
everything Just Works.

Add `DoctorContext.spec_root: Path` to the style doc's context
dataclass (already has `project_root` and `template_root`;
`spec_root` derives from the template's `template.json`).
Template authors who omit `spec_root` get the default
`"SPECIFICATION/"`. The `static-check-semantics` deferred item
covers the exact path-parameterization semantics.

Update the `livespec-nlspec-spec.md` NLSpec-conformance prose and
the `anchor-reference-resolution` algorithm to use `<spec-root>/`.

---

## Proposal: I8-llm-python-validator-invocation-protocol

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**incompleteness** (SKILL.md body shape names a Python entry point
for LLM-side schema validation but no wire protocol exists for the
LLM to invoke it).

### Summary

PROPOSAL.md §"Per-sub-command SKILL.md body structure" (line 201-203)
says a SKILL.md step can "Validate output against a schema (name
the `livespec.validate.<name>.validate` entry point)." But the
LLM's only mechanism for invoking Python code is the Bash tool.
`livespec.validate.<name>.validate` is a Python function, not a CLI
entry point. No shebang wrapper exposes it, no CLI invocation
shape is specified, and no finding/exit-code contract governs
validator success vs failure at the shell boundary.

### Motivation

PROPOSAL.md lines 997-1001 (propose-change):

> The freeform `<intent>` path is driven by the LLM per
> `propose-change/SKILL.md`: the LLM invokes the active template's
> `prompts/propose-change.md`, captures the output, validates it
> via `livespec.validate.proposal_findings.validate` (factory
> shape with the loaded `proposal_findings.schema.json`), writes
> the validated JSON to a temp file, then invokes
> `bin/propose_change.py --findings-json <tempfile> <topic>`.

The LLM's tools (per skill frontmatter) are `Bash + Read + Write`.
Nothing in that set can call a Python function directly. Even via
Bash, `python3 -c "from livespec.validate.proposal_findings import
validate; ..."` would need to:

1. Set up `sys.path` (currently only `bin/_bootstrap.py` knows how).
2. Pass the LLM-produced JSON payload into Python somehow.
3. Pass the schema dict in (the factory shape requires it).
4. Read the Result[...] back out to determine pass / fail.
5. Convert success into a written tempfile for the wrapper.

None of this is specified. An implementer writing `propose-change/
SKILL.md` (deferred item `skill-md-prose-authoring`) is left to
invent a protocol.

The same gap applies to `seed` (`livespec.validate.seed_input.
validate`), `critique` (`livespec.validate.proposal_findings.
validate`), and `revise` (`livespec.validate.revise_input.
validate`).

### Proposed Changes

Decide between:

- **A. Expose validators via CLI shebang wrappers.** Add
  `bin/validate_proposal_findings.py`, `bin/validate_seed_input.py`,
  `bin/validate_revise_input.py`. Each takes `--json <path>`, runs
  the factory-shape validator with the matching schema, and exits
  `0` on success / `3` on validation failure, emitting structured
  findings to stderr via structlog. SKILL.md prose invokes the
  validator wrapper via Bash, checks exit code, and on `0` invokes
  the main sub-command wrapper.

- **B. Fold validation into the main wrapper.** `bin/propose_
  change.py --findings-json <path>` validates internally. The LLM
  invokes the main wrapper directly without a separate validation
  step; on validation failure, the wrapper exits `3` and the LLM
  re-prompts the template prompt with the error context. Drops
  the two-step validate-then-invoke flow from SKILL.md.

- **C. No Python-side validation for LLM-produced JSON.** The LLM
  is trusted to produce schema-valid JSON; the wrapper takes the
  JSON at face value and fails with a parse/type error if it's
  malformed. Retry semantics live in skill prose.

Recommend **B** (fold into wrapper). Rationale: one wrapper call
per LLM step, deterministic exit-code-based feedback loop, no new
executables; the v008 H6 / H10 wrapper-input-schema work already
specifies that each wrapper accepts a JSON payload and validates
it. The "validate-then-invoke" split from v008's PROPOSAL.md prose
was speculative; folding validation into the wrapper matches how
the validator is already located (`livespec/validate/<name>.py` is
imported from `livespec/commands/<cmd>.py` via the ROP chain).
SKILL.md prose gets simpler: one wrapper call; on exit `3` with
findings, re-invoke the template prompt and re-try (up to 3
retries per PROPOSAL.md line 772).

Update PROPOSAL.md § "propose-change", § "seed", § "critique",
§ "revise" to state "wrapper validates input internally; on
exit 3 the LLM re-invokes the template prompt with error context,
up to 3 retries." Drop "the LLM validates this output against the
schema via `livespec.validate.<name>.validate`" from PROPOSAL.md
in all four sub-commands. Rewrite § "Per-sub-command SKILL.md body
structure" step shape "Validate output against a schema" to
"Re-invoke on wrapper exit 3" as the retry step.

The `skill-md-prose-authoring` deferred item covers the concrete
retry prose per sub-command. The `wrapper-input-schemas` deferred
item covers schema-validation error-message shapes.

---

## Proposal: I9-reviser-llm-and-author-id-semantics

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (`reviser_llm` is defined as a model ID but used as a
skill-tool identity; `author` is similarly dual-purpose).

### Summary

PROPOSAL.md §"Revision file format" (line 1478) defines:

> `reviser_llm: <host-provided LLM id, or "unknown-llm">`

But PROPOSAL.md § "seed" (line 974-975) populates `reviser_llm:
livespec-seed` for the auto-generated seed revision. `livespec-seed`
is not a host-provided LLM id; it's an identifier for "the seed
wrapper wrote this, no LLM was involved."

The same thing happens for `author`: `author: <author-id> # LLM
identifier or human handle` (line 1429) but seed's auto-capture
writes `author: livespec-seed` (line 961). Same for
`doctor-out-of-band-edits` auto-backfill (line 1312: "Author
identifier: `livespec-doctor`").

Readers and validators can't distinguish:

- "A human authored this" (`author: thewoolleyman`).
- "An LLM authored this" (`author: claude-opus-4-7`).
- "A deterministic skill tool authored this" (`author: livespec-
  seed`, `author: livespec-doctor`).

Validation is loose enough that `front_matter.schema.json` can't
enforce a namespace distinction, and downstream tooling (the LLM
reading revisions) can't reliably identify automated vs
human-driven entries.

### Motivation

PROPOSAL.md lines 974-975:

> front-matter `proposal: seed.md`, `decision: accept`, ...,
> `reviser_llm: livespec-seed`, `reviser_human: <git user or
> "unknown">`

PROPOSAL.md line 1311-1313 (out-of-band-edits backfill):

> Author identifier: `livespec-doctor`.

PROPOSAL.md line 1429:

> author: <author-id> # LLM identifier or human handle

The field definitions don't reserve a namespace for skill-tool
identities. A competent implementer building tooling that groups
revisions by author-type has no deterministic way to recognize
"this was autogenerated."

### Proposed Changes

- **A. Introduce a skill-tool prefix namespace and widen the
  field definitions.** Redefine:
  - `author: <author-id>` where `<author-id>` is one of
    `livespec-<tool>` (skill-tool: seed, doctor, etc.) | LLM
    identifier | human handle.
  - `reviser_llm: <llm-or-tool-id>` where accepted forms include
    host-provided LLM id, `unknown-llm`, or `livespec-<tool>` for
    skill-authored revisions.
  State the namespace conventions explicitly in the
  proposed-change and revision format sections. The
  `front_matter.schema.json` uses a pattern with `livespec-`
  prefix reserved.

- **B. Split into two distinct fields for automated vs
  human/LLM-authored.** Add `reviser_tool: <skill-tool-id or
  null>` alongside `reviser_llm` and `reviser_human`. For
  automated entries, both `reviser_llm` and `reviser_human` go
  "unknown"; `reviser_tool` is `livespec-seed` / `livespec-doctor`.
  More fields, cleaner provenance.

- **C. Model the three cases as a sum type.** Front-matter has a
  `provenance: human | llm | tool` discriminator plus exactly
  the fields that case requires. Best conceptual fidelity per
  `livespec-nlspec-spec.md` (sum types for mutually exclusive
  cases) but requires a schema and parser that handle
  discriminated unions — a larger departure from the current
  scalar-only restricted-YAML front-matter.

Recommend **A** (prefix namespace, widen field definitions).
Smallest change; preserves the restricted-YAML scalar constraint;
allows the pattern-based schema to validate "no collision between
reserved `livespec-` prefix and human-supplied identities." The
skill itself always writes `livespec-<tool>` for auto-capture;
other authors are free to use arbitrary identifiers that don't
start with `livespec-`.

Update PROPOSAL.md § "Proposed-change file format" and
§ "Revision file format" to state:
- Identifiers starting with `livespec-` are reserved for automated
  skill-tool authorship (e.g., `livespec-seed`, `livespec-doctor`).
  Other callers MUST NOT use this prefix.
- Human authors use any non-`livespec-`-prefixed identifier.
- LLM authors use a host-provided LLM id (e.g.,
  `claude-opus-4-7-1m`); if unavailable, `unknown-llm`.

The `front-matter-parser` deferred item picks up the pattern-based
prefix check in `front_matter.schema.json`.

---

## Proposal: I10-doctor-internal-error-undefined

### Target specification files

- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md

### Failure mode

**incompleteness** (type referenced throughout the style doc but
not defined in the `errors.py` hierarchy).

### Summary

`DoctorInternalError` appears as a failure-track type for every
doctor static check (PROPOSAL.md line 1172, style doc line 231) and
for the orchestrator (style doc line 396). But style doc §"Exit
code contract" (lines 733-751) defines the `LivespecError` hierarchy
— `LivespecError`, `UsageError`, `PreconditionError`,
`PermissionDeniedError`, `ToolMissingError` — with no
`DoctorInternalError`. An implementer can't know whether
`DoctorInternalError` is meant to be `LivespecError` (exit code 1),
`PreconditionError` (exit code 3), or something else.

### Motivation

Style doc line 231:

> Exports `SLUG` constant and `run(ctx) -> IOResult[Finding, DoctorInternalError]`.

Style doc line 396:

> def run_static(ctx: DoctorContext) -> IOResult[FindingsReport, DoctorInternalError]:

PROPOSAL.md line 1172:

> Exports `run(ctx: DoctorContext) -> IOResult[Finding,
> DoctorInternalError]`.

PROPOSAL.md lines 1349-1354 (static-phase exit codes):

> `0`: all checks pass...
> `1`: script-internal failure (bug in `run_static` or any
> individual check)...
> `3`: at least one check failed...

So `DoctorInternalError` represents "exit `1` — bug in the check."
It's conceptually the "script-internal failure" class. But the
hierarchy at style doc lines 733-751 doesn't include it.

### Proposed Changes

- **A. Add `DoctorInternalError` to the hierarchy.** Update style
  doc §"Exit code contract" `errors.py` block:
  ```python
  class DoctorInternalError(LivespecError):
      exit_code: ClassVar[int] = 1
      # Raised/returned when a doctor static check has an internal bug
      # (not a check failure, which is represented as a pass-or-fail
      # Finding instead).
  ```
  Cross-reference from PROPOSAL.md § "Sub-command lifecycle
  orchestration" and § "Static-phase structure."

- **B. Replace `DoctorInternalError` with `LivespecError`
  everywhere.** The base class already has `exit_code = 1`; no new
  subclass is strictly needed. Smaller hierarchy; less semantic
  specificity at the type level.

- **C. Introduce `DoctorError` as a hierarchy root for every
  doctor-specific error.** `DoctorInternalError(DoctorError)`,
  `DoctorCheckFailed(DoctorError)`, etc. Heaviest; arguably
  over-engineered for one type.

Recommend **A**. Smallest, most faithful change: the type is
already used by name, the exit semantics are already defined
(exit `1`), and adding it to the hierarchy closes the gap without
restructuring. Update the `errors.py` block in the style doc.

---

## Smaller gaps

Cleanup items — enumerate / freeze / rename.

---

## Proposal: I11-dogfood-symlink-direction

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (English phrasing of "symlinked to" leaves direction
undetermined).

### Summary

PROPOSAL.md line 32-34:

> During dogfooded development in the livespec repo,
> `.claude-plugin/skills/` is symlinked to `.claude/skills/` so the
> live plugin skills are usable in-repo without an install step.

"X is symlinked to Y" could mean either:
- X is a symlink pointing at Y, OR
- Y is a symlink pointing at X.

An implementer setting up the repo needs to know which
direction, which will be committed to git as a symlink, and
whether the symlink is relative or absolute.

### Proposed Changes

- **A. Specify the direction: `.claude/skills/` is a relative
  symlink to `.claude-plugin/skills/`.** Update PROPOSAL.md to
  read: "a relative symlink `.claude/skills/ → ../.claude-plugin/
  skills/` makes the live plugin skills available to Claude Code
  in-repo." The plugin-delivery path (`.claude-plugin/skills/`) is
  the committed source; the Claude-Code-consumption path
  (`.claude/skills/`) is the symlink target. Matches the
  convention that `.claude-plugin/` is the plugin's own canonical
  location.

- **B. Reverse: `.claude-plugin/skills/ → .claude/skills/`.** The
  plugin-delivery directory is a symlink into the Claude-Code
  skills location. Implies Claude-Code skills are the source of
  truth; less coherent with the plugin-delivery story.

- **C. Drop the symlink; tell developers to invoke via
  `.claude-plugin/...` directly.** Requires Claude Code plugin-
  installation at dev time, which contradicts the "without an
  install step" phrasing.

Recommend **A**. The plugin directory is canonical; the
Claude-Code directory is the consumption point; a relative symlink
is portable. Add to `just bootstrap`: create the symlink if
missing (idempotent). Update PROPOSAL.md prose explicitly.

---

## Proposal: I12-front-matter-schema-single-vs-plural

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md
- brainstorming/approach-2-nlspec-based/python-skill-script-style-requirements.md
- brainstorming/approach-2-nlspec-based/deferred-items.md

### Failure mode

**ambiguity** (one schema file listed, two distinct schema shapes
required).

### Summary

PROPOSAL.md line 131 (schemas/ layout):

> │       │   └── front_matter.schema.json (deferred; see deferred-items.md)

Singular. But proposed-change front-matter has fields `topic`,
`author`, `created_at`; revision front-matter has `proposal`,
`decision`, `revised_at`, `reviser_human`, `reviser_llm`. These
are distinct shapes that one JSON Schema can unify only via a
discriminated union (which the restricted-YAML scalar constraint
can't easily express).

`front-matter-parser` deferred item says "Author the JSON Schema
for proposed-change front-matter and revision front-matter" —
singular "Schema" despite two shapes.

### Proposed Changes

- **A. Split into two schemas.** Rename `front_matter.schema.json`
  → `proposed_change_front_matter.schema.json` +
  `revision_front_matter.schema.json`. Each validator reads the
  correct schema. Update the layout diagram in PROPOSAL.md and
  style doc; update the `front-matter-parser` deferred item to
  enumerate both schemas.

- **B. Keep one schema with a discriminated union.** Use JSON
  Schema `oneOf` to express "either proposed-change shape or
  revision shape," keyed on which fields are present (e.g.,
  `proposal` present → revision shape). Works under JSON Schema
  Draft-7 but produces less specific error messages.

- **C. One schema with optional fields + a prose invariant.**
  Violates `livespec-nlspec-spec.md`'s conceptual-fidelity
  principle (prose invariants are "a rarer analogue of intentional
  ambiguity" and sum types are the faithful model for mutually
  exclusive cases).

Recommend **A** (split into two). Sum-type fidelity over the
domain is the right choice per `livespec-nlspec-spec.md`;
`fastjsonschema` handles distinct schemas well; validator names
(`validate_proposed_change_front_matter`,
`validate_revision_front_matter`) are clearer.

Update PROPOSAL.md §"Proposed-change file format" and §"Revision
file format" to name their respective schemas. Update the style
doc layout. Update the `front-matter-parser` deferred item to
enumerate both schemas.

---

## Proposal: I13-host-provided-llm-id-mechanism

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**incompleteness** (no documented API or convention for obtaining
the "host-provided LLM id" the revision / critique contracts
reference).

### Summary

PROPOSAL.md line 1038-1040 (critique):

> `<author>` defaults to a string identifying the current LLM
> context, derived from the host's available metadata. If no
> identifier is available, the literal `unknown-llm` MUST be used
> and a warning surfaced.

PROPOSAL.md line 1478 (revision front-matter):

> `reviser_llm: <host-provided LLM id, or "unknown-llm">`

But the proposal never states HOW the LLM obtains its own
identifier. Claude Code doesn't expose a formal "which model am I"
API. The LLM may know its own model name via training, but that's
not deterministic and not "host-provided." An env var? Claude
Code prompt metadata? The LLM asking the user? Not specified.

### Proposed Changes

- **A. Use env var convention + fallback.** The LLM reads
  `LIVESPEC_REVISER_LLM` from the environment (via Bash tool); if
  empty, uses `unknown-llm`. The user / host can set it once per
  project (e.g., `export LIVESPEC_REVISER_LLM="claude-opus-4-7"`).
  Document it in PROPOSAL.md's config section and reference it
  from the critique and revision sections.

- **B. Accept LLM-as-self-declaration.** The LLM emits its own
  identifier as a string in the JSON wrapper-input payload.
  `revise_input.schema.json` and critique's invocation accept a
  `reviser_llm` field populated by the LLM from its own model
  knowledge. Non-deterministic but pragmatic.

- **C. Always use `unknown-llm`; drop the host-provided language.**
  The revision-front-matter `reviser_llm` is always `unknown-llm`
  in v1; future versions may introduce a host-integration API.

Recommend **A** (env var). Matches the rest of livespec's
configuration discipline (env var + CLI flag pattern already
established for log level); the LLM can read env vars via Bash;
it's deterministic when set; falls back cleanly when unset. Add
to PROPOSAL.md's environment-variable contract a new var
`LIVESPEC_REVISER_LLM` with documented fallback to `unknown-llm`.

Also update the `static-check-semantics` deferred item to cover
the env-var-read implementation in the revise + critique wrapper
paths.

---

## Proposal: I14-doctor-static-disposition-of-skip-pre-check

### Target specification files

- brainstorming/approach-2-nlspec-based/PROPOSAL.md

### Failure mode

**ambiguity** (`--skip-pre-check` is wrapper-parsed, but
`bin/doctor_static.py` has no pre/post structure; behavior when
the flag is passed to doctor_static is undefined).

### Summary

PROPOSAL.md §"Sub-command lifecycle orchestration" (lines 418-422)
says `--skip-pre-check` is "parsed by the wrapper and elides the
first `run_static` from the chain." But `bin/doctor_static.py` IS
the static phase — it has no pre-step to elide. If a user passes
`--skip-pre-check` to doctor_static, is it a usage error (exit
`2`), silently ignored, or accepted as a no-op?

### Proposed Changes

- **A. Reject with `UsageError` (exit 2).** `bin/doctor_static.py`
  does not accept `--skip-pre-check`; passing it fails with an
  actionable error. Matches argparse's default behavior and
  `livespec-io-cli` seam. Clearest signal.

- **B. Silently accept as a no-op.** `bin/doctor_static.py`
  accepts `--skip-pre-check` for symmetry with other wrappers but
  ignores it (there's nothing to skip). Looser; may confuse users.

- **C. Accept and emit a warning via structlog.** Same as B but
  logs a `warning`-level message.

Recommend **A** (reject). `--skip-pre-check` is semantically about
the outer sub-command's lifecycle chain, not the static phase
itself. Rejecting it surfaces the semantic mismatch immediately.

Add to PROPOSAL.md §"Sub-command lifecycle orchestration" a
sentence: "`bin/doctor_static.py` does not accept
`--skip-pre-check`; it IS the static phase and has no pre/post
wrap." Update the exit-code narration in the canonical SKILL.md
body to include exit `2` for usage errors including this one.

---

## Summary

Total items: 14 (I1-I14).

- **Major (recreatability-blocking):** 3 — I1 (seed pre-step
  contradicts seed's purpose), I2 (run_static return type in
  lifecycle chain), I3 (schema→dataclass generation unspecified).
- **Significant (load-bearing guesses):** 7 — I4 (supervisor
  return rule self-contradictory), I5 (git config read outside
  allowlist), I6 (Result/IOResult lifting), I7 (SPECIFICATION/
  path vs custom template), I8 (LLM→validator protocol),
  I9 (reviser_llm / author semantics), I10 (DoctorInternalError
  undefined).
- **Smaller (enumerate / freeze / rename):** 4 — I11 (symlink
  direction), I12 (front_matter schema plural), I13 (host-
  provided LLM id mechanism), I14 (doctor_static vs
  `--skip-pre-check`).

Several items interact with existing deferred items:
- I1 → updates `static-check-semantics` (seed exemption).
- I2 → adds gate-function semantics to `static-check-semantics`.
- I3 → new deferred entry `dataclass-schema-pairing` (or widens
  `wrapper-input-schemas`).
- I5, I13 → widens `static-check-semantics` with env-var /
  git-config read semantics.
- I7 → widens `static-check-semantics` with spec-root
  parameterization.
- I8 → updates `skill-md-prose-authoring` (retry prose) and
  `wrapper-input-schemas` (error-shape).
- I9 → updates `front-matter-parser` (reserved prefix pattern).
- I12 → updates `front-matter-parser` (two schemas).

The dispositions from v008 (H1-H16) are NOT reopened by any item.
