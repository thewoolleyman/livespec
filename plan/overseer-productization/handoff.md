# Plan — overseer-productization

**Owning session:** livespec core, "overseer-productization". **Status:** OPEN,
EXECUTING Phase 1.
**Decision (maintainer 2026-07-18):** *Gate now, ship as Phase 2.* Bring the overseer
fully inside the product gates as a first-class LOCAL module (Phase 1), then design
host-decoupling + adopter shipping (Phase 2). Phase 1's value is independent of Phase 2.

## Progress

| Gate | State | Where |
|---|---|---|
| A — tests in `just check`/CI | **DONE, live-exercised** | livespec PR [#1387](https://github.com/thewoolleyman/livespec/pull/1387), merged 2026-07-19 |
| C — ruff lint + format | **DONE, live-exercised** | livespec PR [#1396](https://github.com/thewoolleyman/livespec/pull/1396), merged 2026-07-19 |
| D — pyright strict | **DONE, live-exercised** | livespec PR [#1408](https://github.com/thewoolleyman/livespec/pull/1408), merged 2026-07-19 |
| B — coverage | NEXT — needs D1 decided | — |
| E — ROP railway | BLOCKED on D2 — see below | — |

## Gate D — pyright strict (PR #1408, merged 2026-07-19)

**Live-exercise evidence.** Post-merge master CI run
[29679815083](https://github.com/thewoolleyman/livespec/actions/runs/29679815083):
`check-types`, `check-lint`, `check-format`, and `check-overseer` all passed against
combined master. Sabotage-verified — a function returning `int` from a `-> str`
signature turned `just check-types` red.

**Clean under strict mode with NO pragma and NO suppression anywhere.** 174 product-module
errors → 0, no behavior change (344 beside-tests pass; 304 pre-existing + 40 new).

**The scope decision, which was NOT in the plan and matters most.** The plan estimated
163 errors. The true first measurement was **3116** — because the beside-tests are
unannotated (`def test_x(tmp_path):`) and generate ~2942 `reportMissingParameterType` and
friends. The resolution is not a carve-out: **pyright checks SOURCE, not tests,
repo-wide** — the product `tests/` tree is out of scope simply by never appearing in
`[tool.pyright].include`. The overseer's tests live BESIDE their source, so applying the
identical rule takes an explicit `exclude` entry rather than an omission. Do not read
that exclude as an overseer exemption; it is the repo's existing rule, spelled out.

| step | errors |
|---|---|
| baseline (product modules only) | 174 |
| `PaneDriver` Protocol for the tmux seam | 57 |
| `_codex` / `out` given their real types | 24 |
| `jsonio` narrowing at the JSON boundary | 2 |
| final two narrowings | **0** |

What each step was, so Gate B/E does not re-derive it:

- **`tmux: object` was over half the total.** `tmuxio.PaneDriver` is a `Protocol`
  declaring the TWELVE methods `Supervisor` calls, not all nineteen `TmuxIO` exposes.
  `TmuxIO` and `FakeTmux` satisfy it structurally — what a Protocol is for, and where the
  no-inheritance rule points. The narrow surface states what a substitute must implement
  to BE substitutable, so a future test double is complete when it satisfies this.
- **`_codex` and `out` already had real types.** `_codex` is
  `dict[tuple[str, str], CodexSession]`; typing it retired a `# type: ignore[attr-defined]`
  that existed only to paper over `object`. `out` is `IO[str]` and is no longer Optional:
  nothing ever passed `None`, so `__post_init__` existed solely to re-default it. A
  `default_factory` resolves it at construction, keeping the late binding tests rely on.
- **New `jsonio.py`** (stdlib-only, 40 beside-tests) narrows parsed JSON at the boundary.
  `json.loads` returns `Any` and `isinstance(x, dict)` narrows only to
  `dict[Unknown, Unknown]`, so every `.get()` went unknown and the per-field isinstance
  guards the call sites ALREADY performed stopped meaning anything to the checker.
  `as_object` / `as_list` / `as_float` fix it once. Two deliberate details: `as_object` is
  separate from `parse_object` so the two registry readers that report malformed-file and
  non-object-file with DIFFERENT diagnostics keep them; `as_float` rejects `bool` because
  it is an `int` subclass and a bare numeric check would turn `true` into `1.0`.
  The rejected alternative was the file-level `# pyright: reportUnknown...=none` pragma
  the product tree uses in one helpers module — right there (a pure-helper module),
  wrong here (a few parsing lines inside modules full of unrelated logic).
- **One source change rather than a type change:** `eff_ctx` is guarded by
  `has_context_left`, but pyright cannot narrow through an intermediate boolean, so the
  `is not None` is spelled out at the branch. VERIFIED not a latent bug — the guard
  already made `None` unreachable.
- The remaining 24 were `reportUnusedCallResult`, discharged with `_ =`.

**Trap for whoever automates a bulk edit here.** A script that rewrote lines via
`re.match(r"^(\s*)(\S.*)$", line)` silently DROPPED each line's trailing newline, merging
it with the next and producing syntax errors across two modules. Recovery was only cheap
because the other edits to those files were few and re-appliable from a clean `git
checkout`. Preserve the line terminator explicitly (`^([ \t]*)(.*?)(\r?\n?)$`), and
prefer per-file verification after any scripted rewrite.

## Gate C — ruff (PR #1396, merged 2026-07-19)

**Live-exercise evidence.** Post-merge master CI run
[29677133101](https://github.com/thewoolleyman/livespec/actions/runs/29677133101):
`check-lint`, `check-format`, and `check-overseer` all ran and passed against
combined master. Sabotage-verified before the PR — adding a `print` to `tmuxio.py`
turned `just check-lint` red; removing it turned it green.

**Measured outcome.** 929 raw findings → zero, with NO behavior change (the 304
beside-tests passed unchanged throughout). The handoff's 2026-07-18 estimate held up:
the cost really was concentrated in a handful of places, not spread thin.

How they resolved, so Gate D does not re-litigate any of it:

- **35 ambiguous-unicode** → `[tool.ruff.lint].allowed-confusables = ["❯", "›"]`.
  These are domain vocabulary (the prompt glyphs Claude Code and Codex print), and a
  two-codepoint repo-wide whitelist is NARROWER than a per-file-ignore, which would
  disable RUF001/2/3 across whole files and hide a genuinely confusable character
  introduced later. The repo was at zero findings for those rules, so it masks nothing.
- **~790 test-file findings** → one per-file-ignore for `.claude/skills/overseer/test_*.py`
  inheriting the `tests/**.py` rationale, plus three beside-test-specific entries:
  SLF001 (testing private decision helpers directly IS the point of a beside-test),
  ARG001/2 (signature-matching test doubles must accept args they do not use), S108
  (the real `/tmp` tmux socket paths are the fixture).
- **12 `print`** → refactored away, NOT exempted. The repo has zero T201 escapes and
  `SPECIFICATION/constraints.md` names ruff `T20` as the mechanical enforcement of its
  stdout-reservation rule. New stdlib-only `.claude/skills/overseer/streams.py` mirrors
  the product's `livespec/io/streams.py` one-hop indirection, with 5 beside-tests. The
  daemon's table render already used an injectable stream and was untouched.
- **~25 genuine fixes** → pathlib over `os.path`, named constants for the `/proc` stat
  field indices and the `list-panes` row width, `contextlib.suppress`, a keyword-only
  bool arg, line wraps, and three inline `# noqa: <CODE> — <reason>` escapes for cases
  correct as written (PATH `git`, the uid-scoped `/tmp` tmux socket namespace, the
  daemon loop's outermost bug-catcher boundary).

**The `evaluate` decision (maintainer-chosen 2026-07-19): split observe from decide.**
A new `Supervisor._observe` gathers the 16 facts the guard cascade reads and returns a
frozen `_Observation`. That took `evaluate` from 106 statements / 38 branches /
complexity 34 to **83 / 33 / 31** — a real reduction, but NOT under the thresholds
(10 branches, 30 statements). The residual is the decision cascade itself, whose
ORDERING is the design: the cardinal rule is enforced by which guard comes first. So
C901/PLR0911/PLR0912/PLR0915 are suppressed on that ONE function via an inline noqa,
with the full reasoning in its docstring; every other function in the module is still
held to them. Full decomposition was considered and rejected — it would scatter the
precedence order across call sites where no reader can verify it in one pass.

**Two facts Gate D should know:**

1. **`check-doctor-static` ALREADY reaches `.claude/skills/overseer/`.** It rejected a
   heading-level spec citation (`§"…"`) in the new `streams.py` docstring — the folder
   was never as far outside the gates as its own docs claimed. Cite spec FILES, not
   headings, in overseer code.
2. **Never `git checkout <file>` to undo a sabotage probe.** It reverts to HEAD, not to
   your working state, and silently discarded a whole file's worth of Gate C edits mid-run.
   Copy to the scratch dir and restore from there.

**Gate A live-exercise evidence (not merely merged + CI-green).** The post-merge master
CI run [29673873687](https://github.com/thewoolleyman/livespec/actions/runs/29673873687)
carried a `check-overseer` job that ran and passed against combined master — so the gate
is real in the environment it exists to protect, not only in a PR sandbox. Sabotage was
verified locally before the PR: appending a failing beside-test turned
`just check-overseer` red with a non-zero recipe exit; restoring it turned it green.

**Gate A (2026-07-19, PR #1387).** Adds a livespec-private `check-overseer` justfile
target (`uv run pytest .claude/skills/overseer/ -q`, **no coverage**), makes it a literal
member of the `just check` aggregate, and adds the matching `check-python` CI matrix leg
(`py_changed`-gated). Sabotage-verified. Also rewrites the overseer `AGENTS.md` paragraph
that documented the now-reversed "deliberately outside the product gates" design (D3).

Wiring facts learned (do NOT re-derive): `check-overseer` is a **livespec-private**
slug — it is not a module under `livespec_dev_tooling/checks/`, so
`canonical_check_slugs()` never emits it and the canonical meta-checks are inert. Only
two things are mandatory: the justfile recipe, and aggregate membership **anywhere after
the last canonical slug** (`check-aggregate-completeness` only enforces alphabetical
order WITHIN the canonical block, plus "no extras interleaved before it"). The CI matrix
leg is required by intent, not by a gate (`check-ci-matrix-completeness` is
canonical-scoped; `check-tool-backed-check-completeness` uses a fixed 4-slug policy).
`branch-protection.json` needs NO change — `ci-green` is the sole live required context,
and a matrix leg absent from the required list is a warning, exit 0. No test asserts over
the live justfile target list or CI matrix; `tests/heading-coverage.json` has no
justfile-target dimension.

The target deliberately runs WITHOUT `--cov` so host-glue modules never enter the
`fail_under = 100` gate, and it sorts after `check-coverage`/`check-per-file-coverage` in
the aggregate — keep it there if it ever moves.

Two operational lessons from landing it, both worth carrying into Gates C/D:

- **A conflicting PR gets NO CI run at all.** GitHub only creates a `pull_request` run
  when it can compute the merge ref, so a branch that conflicts with master silently
  reports zero checks rather than a failure — it looks like CI never fired. Master moves
  fast here (three unrelated threads landed commits during this one PR), so rebase onto
  `origin/master` and re-push the moment `gh pr view --json mergeStateStatus` reports
  `DIRTY`/`CONFLICTING`.
- **`.claude/skills/overseer/AGENTS.md` is contended surface.** The `overseer-known-defects`
  thread edited the same paragraph concurrently. Its addition — the *combined-master-state*
  warning (two overseer branches merging git-clean can still leave the folder red) — was
  PRESERVED and rewritten, not dropped: master CI now catches that case post-merge, but
  auto-merge lands before the master run finishes, so the manual combined-state re-run is
  still the advice while another overseer branch is in flight.

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

1. ~~**Gate A — wire the hermetic beside-tests into `just check`.**~~ **DONE** (PR #1387).
2. ~~**Gate C — ruff.**~~ **DONE** (PR #1396). Landed as planned, with one deviation worth
   noting: the `print`-in-daemon *allowance* the plan offered as an option was NOT taken —
   the prints were refactored through a new `streams.py` sink instead, because the repo has
   zero T201 escapes and the spec names `T20` as the enforcement of a normative rule. See
   the Gate C section above.
3. ~~**Gate D — pyright strict.**~~ **DONE** (PR #1408). The plan's prediction was right
   about the shape — a `Protocol` for the tmux boundary and typed session maps WERE the
   bulk — and wrong about the count only because it did not anticipate the beside-tests.
   See the Gate D section above.
4. **Gate B + E — coverage + ROP railway.** The real design decision (below): how
   host-glue reaches 100% and whether it goes on the `Result` railway. B needs D1; E is
   blocked on D2's remaining scope question.

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
- **D3 — does "inside the gates" change the LOCAL-ONLY status?** RESOLVED (no, by
  default): gate coverage (quality) is independent of distribution. The folder stays
  local-only in Phase 1. The AGENTS.md paragraph asserting "deliberately outside the
  product gates … the discipline lives in the developer's hands" was REWRITTEN in
  PR #1387 (it was the documented decision being reversed).

**Cross-thread input for D2 — read `plan/rop-sweep-fleet-policy/handoff.md` before
resolving it.** That thread's ratified fleet policy (livespec PR #1321, merged;
`non-functional-requirements.md` v165) mandates the FULL `Result`/`IOResult` railway for
every Python-carrying fleet repo — Drivers and dev-tooling included — with the sole
exemption being a repo with zero first-party Python.

⚠️ **Gate C invalidated one of that thread's stated facts — tell it.** The rop-sweep
audit recorded that the "noqa the fail-open/supervisor catchers" step was moot because
those catchers sit in ruff-EXCLUDED directories, and it listed
`.claude/skills/overseer/**` among them. **That is no longer true as of PR #1396**:
the overseer is inside ruff now, `BLE` reaches it, and its single blind catch — the
daemon loop's outermost bug-catcher — already carries an explicit
`# noqa: BLE001 — outermost supervisor boundary`. The other listed directories
(`.claude/hooks/**`, `.claude-plugin/hooks/**`, `livespec/hooks/**`) are unaffected.

So D2's remaining question is narrower than it was: not "will `BLE` ever reach the
overseer" (it does, and the one site is resolved), but whether the repo-level full-ROP
bar is intended to reach a `.claude/skills/` host-tooling folder at all, or only the
`livespec` package.

Both facts were RELAYED to the live `rop-sweep-fleet-policy` tmux session on 2026-07-19
(pane idle, bracketed-paste). Nothing here was edited on their behalf.

### ✅ D2 marker blocker — RESOLVED by the rop-sweep thread (2026-07-19)

The gap below was relayed to the `rop-sweep-fleet-policy` session, which **adopted a
fifth marker** in commit `98dfb144`, using the suggested wording verbatim:

> `— sole loop-iteration bug-catcher: log traceback, continue`

Its contract: a daemon supervising N independent units MAY carry ONE ADDITIONAL broad
catch as a direct child of its supervision-loop body; it MUST log the FULL traceback
(a silent `pass` is forbidden), MUST NOT exit, and its cardinality is one per
SUPERVISION LOOP rather than one per entry artifact — so an entry artifact running such
a loop may carry both its `main()` boundary handler and this one, and no more. The
proposal now cites the overseer as the worked example for the category.

The overseer's marker was updated to the conforming wording in PR #1408's second commit,
so the worked example no longer contradicts the text citing it. The proposal is still
UNRATIFIED, so nothing is binding yet.

Two follow-ups the proposal itself flags, neither owned by this thread:

1. `check-supervisor-discipline` scopes on `source_tree_prefixes`, which does NOT include
   `.claude/skills/`, so nothing mechanically enforces this over the overseer. The
   proposal explicitly tracks extending that scope separately.
2. The proposal ALSO resolves a spec-versus-implementation divergence it found on the
   way: the current text mandates an explicit `try/except Exception` bug-catcher in every
   supervisor, but shipped core supervisors carry none and CI is green.

**What remains open for D2** is only the original scope question, unchanged: whether the
repo-level full-ROP bar reaches a `.claude/skills/` host-tooling folder at all, or only
the `livespec` package. Gate E stays blocked on that.

### The original gap (kept for the record)

⚠️ **The overseer's daemon catch fit none of the FOUR original markers**

`SPECIFICATION/proposed_changes/rop-broad-except-boundary-rule.md` (filed by the
rop-sweep thread, commit `985a4322`, under Fable review at the time of writing) defines a
**closed set of four** standardized `# noqa: BLE001` markers and rules that any other
wording "marks a violation, not an escape":

1. `— sole supervisor bug-catcher: log traceback, exit 1`
2. `— sole fail-open hook boundary: silent pass-through, exit 0`
3. `— sole fail-closed guard boundary: deny per policy, exit 0`
4. `— foreign-code isolation: <surface> crash captured as <ErrorType>, reported`

The overseer's one broad catch (`supervisor.py`, inside `Supervisor.run`'s `while True`)
matches NONE of them. It logs the full traceback and **continues the loop** — it does not
exit 1, and it is not a direct child of `main()`:

```python
except Exception:  # noqa: BLE001 — outermost supervisor boundary
    self._log("tick error (continuing):\n" + traceback.format_exc())
```

That shape is the daemon's whole point: it supervises N independent tracks, and a bug
evaluating ONE track must not take the process down and strand the other N-1. "Log and
exit 1" is the wrong contract for it.

So the proposal, as written, has no category for a long-running supervisor's
**per-iteration resilience catch**. If it ratifies unchanged, the overseer becomes
non-conforming immediately, and the only conforming moves would be to mis-label it as
marker 1 (a lie — it does not exit 1) or to change the daemon's behavior (wrong).

Note the conflict would be **spec-text-only, not mechanical**: `check-supervisor-discipline`
scopes on `source_tree_prefixes`, which does not include `.claude/skills/`, so nothing
would actually flag it. That is precisely why it needs a human ruling rather than a gate.

**Do not resolve this here.** It is the rop-sweep thread's proposal and its reviewer's
pass; the gap was relayed to that session with two options to weigh (add a fifth marker
such as `— sole loop-iteration bug-catcher: log traceback, continue`, or rule that the
bar does not reach `.claude/skills/` at all). Gate B/E work stays blocked until that
lands, because the answer determines whether the overseer goes on the `Result` railway.

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
