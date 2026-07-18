# Plan — overseer-productization

**Owning session:** livespec core, "overseer-productization". **Status:** OPEN, planning.
**Decision (maintainer 2026-07-18):** *Gate now, ship as Phase 2.* Bring the overseer
fully inside the product gates as a first-class LOCAL module (Phase 1), then design
host-decoupling + adopter shipping (Phase 2). Phase 1's value is independent of Phase 2.

## Why this thread exists

The `overseer-tmux-runtime-column` work (merged: PRs #1345, #1351 — now archived under
`plan/archive/`) exposed a structural gap and prompted a bigger question:

1. **The overseer is outside every product gate.** Its beside-tests
   (`.claude/skills/overseer/`) are the SOLE gate on the folder but are a *manual*
   pre-push step — not wired into `just check`/CI. This is deliberate today (AGENTS.md:
   "outside the product gates… the discipline lives here, in the developer's hands").
   The cost: a broken overseer merges green. It happened **twice today** — the runtime
   column landed with no gate exercising it, and a concurrent `_codex` re-key
   (`a24e3e13`) + this thread's Codex test merged green independently but broke `pytest`
   on master (fixed by #1351). That is the exact "merges green with nothing exercising
   its behavior" failure the AGENTS.md warns about.
2. **Should it be shipped like everything else — usable by adopters?** (maintainer:
   "isn't it all just code? … explore making it part of the plugin and usable from the
   drivers for any adopter that wants to use it, as long as there is a fleet manifest.")

## Grounded findings (measured 2026-07-18 — do NOT re-measure, verify if stale)

### The gate-cost is far lower than first claimed ("many carve-outs" was WRONG)

Ruff, against the project's real ruleset:
- **All overseer `.py`: 929 findings — but 76% (705) are `assert` in TEST files** (S101),
  plus 52 private-member-access + 41 magic-values, almost all in tests. The product
  `tests/` tree already silences exactly these via per-file-ignores → ONE config line.
- **Product modules only (`supervisor`/`signals`/`registry`/`tmuxio`/`claude_sessions`/
  `codex_sessions`): ~70 findings**, clustering into: **35 ambiguous-unicode** (the `—`,
  `❯`, `›`, box-drawing glyphs the overseer literally parses out of real TUIs — one
  legitimate allowance, not a smell), **12 `print`** (the daemon's stderr log + table
  render — a daemon's output IS print), and **~20 genuine trivial fixes** (3 long lines,
  3 magic values, 2 pathlib, 2 "function too complex" on `evaluate`).

Pyright STRICT (project config: `typeCheckingMode = "strict"` + 7 strict-plus
diagnostics + the `returns` plugin), product modules: **163 errors** — the real work
(the `tmux: object` injectable seam, the duck-typed `FakeTmux`, the dynamic session
maps). Bounded, but this is where Phase 1's effort actually is.

### Per-gate honest cost

| Gate | Cost | What it is |
|---|---|---|
| A — tests run in `just check`/CI | **free** | beside-tests are hermetic (FakeTmux, fake `/proc`) → run anywhere. Add a separate `check-overseer` slug (no coverage). **Closes the regression that bit us twice.** |
| C — ruff lint | small | one unicode-glyph allowance + `print`-in-daemon policy + ~20 trivial fixes |
| B — coverage 100% | medium | host-glue (subprocess/`/proc`/daemon-loop/`main`) isn't unit-testable → needs a thin I/O-boundary extraction + `# pragma: no cover`, or a scoped threshold |
| D — pyright strict | real (163) | the injectable/duck-typed seams |
| E — dev-tooling ROP railway + AST style | judgment call | fleet-wide `Result`/no-`raise`-outside-`io` (spec §"ROP railway is fleet+adopter-wide"). Maintainer leans "treat it like everything else" → include it. |

### Fleet-manifest is an official spec contract (answers Phase 2's key question)

Live `SPECIFICATION/non-functional-requirements.md`:
- §"Fleet membership contract" → **Fleet manifest**: `.livespec-fleet-manifest.jsonc`
  enumerates `fleet` members and MAY carry an `adopters` array.
- §"Adopters": each adopter names `repo`, a conformance `profile`, and a `posture`
  (`released`/`pinned`/`none`); "an adopter … MAY be a fleet itself."

Two caveats that shape Phase 2:
1. It's ONE central manifest **hosted in livespec core** listing adopters — NOT a
   per-adopter file each ships (though an adopter *family* can host its own).
2. It is specified as **non-functional, fleet-self-application infrastructure**, bound
   to "the livespec fleet, its adopters, and the reference orchestrators, **never a
   third-party `livespec` consumer or the `/livespec:*` plugin skills core ships**."

So if a shipped overseer read a fleet manifest, that either (a) makes the manifest a
**functional shipped contract** — a deliberate spec-boundary change — or (b) keeps it a
fleet-self-application tool adopters MAY run within the same manifest model. (b) fits
today's boundary; (a) is a real spec change. (Note: a live `register-homelab-adopter`
thread is exercising the adopter path right now.)

## Phase 1 — inside the gates (the committed near-term)

Goal: the overseer folder is a first-class module — `just check`/pre-push/CI run its
lint, types, tests, and a coverage policy — with NO special local-only exemption beyond
what the code's host-glue nature genuinely requires (and each such exemption is a
documented severity lever, not a silent skip, per the enforcement discipline).

Proposed sequence (each its own small PR; Gate A first for the immediate win):

1. **Gate A — wire the hermetic beside-tests into `just check`.** Add a `check-overseer`
   justfile slug (`uv run pytest .claude/skills/overseer/ -q`, NO coverage) and make it
   a literal member of `check`, so a red overseer test blocks pre-push + CI + every
   merge. Cheapest, highest-value, closes today's regression. Land standalone.
2. **Gate C — ruff.** Remove `.claude/skills/overseer/**` from `[tool.ruff].extend-exclude`;
   add the unicode-glyph allowance (scoped, self-documenting) and a `print`-in-daemon
   allowance (or route daemon output through a single sink); fix the ~20 trivial items.
   Add a `test_*`-scoped per-file-ignore mirroring the product `tests/` treatment.
3. **Gate D — pyright strict.** Add the folder to `[tool.pyright].include`; work the 163
   errors (mostly typing the injectable seams — a `Protocol` for the tmux boundary
   instead of `object`, typed session maps).
4. **Gate B + E — coverage + ROP railway.** The real design decision (below): how
   host-glue reaches 100% and whether it goes on the `Result` railway.

### OPEN DECISIONS (resolve one at a time)

- **D1 — coverage strategy for host-glue.** Options: (a) *boundary extraction* — isolate
  every real-world side effect (subprocess/tmux/`/proc`/`main`/daemon-loop) behind the
  existing `tmuxio`/`claude_sessions` seams so the pure logic hits 100% and only the thin
  I/O shell is `# pragma: no cover`d [Recommended — matches the product's io/ boundary
  discipline]; (b) a scoped per-file coverage threshold for the folder; (c) keep coverage
  out and enforce only lint+types+tests. Recommend (a).
- **D2 — ROP railway for host-glue (Gate E).** Maintainer leans "treat it like
  everything else" → put the overseer on the `Result`/`IOResult` railway with the fleet's
  `reportUnusedCallResult`/`BLE` guardrails, the single outermost supervisor bug-catcher
  boundary. Confirm scope: is the overseer "product logic" for the railway rule, or
  host-glue like the `.claude/hooks/` footgun-guard (which is NOT on the railway)? The
  spec's railway rule is fleet+adopter-wide for "first-party Python"; the overseer is
  `.claude/skills/` host tooling. RESOLVE before Gate B/E work.
- **D3 — does "inside the gates" change the LOCAL-ONLY status?** No, by default: gate
  coverage (quality) is independent of distribution. The folder stays local-only in
  Phase 1; the AGENTS.md paragraph asserting "deliberately outside the product gates …
  the discipline lives in the developer's hands" must be REWRITTEN (it's the documented
  decision being reversed).

## Phase 2 — ship it (design exploration, not yet committed)

Goal: an adopter with a fleet manifest can run the overseer. Architecturally plausible
(stdlib-only, `python3`-invokable — fits the plugin model), but real coupling to resolve:

- **Host coupling.** Scans `/proc` (Linux-only), drives real tmux, reads
  `~/.claude/sessions/` (Claude registry) + Codex rollout fds. macOS/non-tmux adopters
  can't run it unchanged. Needs a portability boundary (or a declared "Linux+tmux only"
  requirement).
- **Driver split.** Per the architecture, the interactive `/overseer` *skill* would ship
  from the Driver repos (`livespec-driver-claude`/`-codex`), with the daemon + prose in
  CORE — the established prose-in-core / thin-binding-in-driver pattern used by every
  `/livespec:*` operation.
- **The fleet-manifest boundary decision (from findings above).** (a) promote the
  manifest to a functional shipped contract, or (b) keep it fleet-self-application and
  ship the overseer as a tool adopters-as-families MAY run. Recommend deciding this
  early — it gates the whole Phase 2 shape.

### OPEN DECISIONS (Phase 2 — deferred until Phase 1 lands)

- **D4 — portability target.** "Linux+tmux only, declared requirement" vs. abstract the
  host boundary for macOS/other. Recommend declared-requirement first (the fleet is
  Linux+tmux), abstract later if an adopter needs it.
- **D5 — manifest boundary** (functional shipped contract vs. fleet-self-application).
- **D6 — anchor a ledger epic?** Phase 2 is multi-repo (CORE + both Drivers) → an epic
  with per-repo work-items + cross-repo links is the right shape IF Phase 2 proceeds.
  Phase 1 is single-repo/local and can run as this plan thread without an epic.

## Discipline (this folder)

- **Worktree → PR → merge → cleanup for EVERY change** (learned the hard way this
  session: edits were first made in the primary checkout — the live daemon reads the
  primary, so in-place edits risk it importing half-finished code. Do edits in a
  worktree from the start).
- Beside-tests remain the correctness gate; run `uv run pytest .claude/skills/overseer/ -q`
  before every push. Once Gate A lands, `just check` runs them too.
- Overseer `.py` is exempt from Red-Green-Replay (not an `_IMPL_PREFIXES` path) — use
  `fix(overseer):` / `chore(overseer):` with test+impl in one commit; never `--no-verify`.
- Sabotage-verify any new guard (break it → watch its test go red → restore).
