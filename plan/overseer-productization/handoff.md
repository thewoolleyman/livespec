# Plan — overseer-productization

**Owning session:** livespec core, "overseer-productization". **Status:** OPEN —
**Phase 1 COMPLETE; Phase 2 committed and anchored to epic `livespec-b1uo`.**
**Ledger anchor (Phase 2):** epic `livespec-b1uo` (livespec CORE tenant), five
children. Status is READ from the ledger, never stored here.
**Decision (maintainer 2026-07-18):** *Gate now, ship as Phase 2.* Bring the overseer
fully inside the product gates as a first-class LOCAL module (Phase 1), then design
host-decoupling + adopter shipping (Phase 2). Phase 1's value is independent of Phase 2.

## ⚠️ Push blocker 2026-07-20 — GitHub partial API outage (diagnosis CORRECTED)

This branch could not be pushed. The `livespec-pr-bot` App credential helper
(`/home/ubuntu/.local/bin/livespec-agent-github-credential-helper` → the
`livespec-runtime` mint) fails with `HTTP 503 Service Unavailable`, so
`git push` never gets a credential and dies with
`could not read Username for 'https://github.com'`.

**An earlier note on this page diagnosed it as "an App-installations outage"
that was "transient", inferred from a plain `GET https://api.github.com/`
returning 200. Both halves were wrong, and the inference is the reusable
lesson: a 200 on the API ROOT does not rule out a partial outage of specific
API services.** What is actually happening, measured 2026-07-20:

- **It is a GitHub-side incident, confirmed on the status page**, not a repo,
  auth, or credential misconfiguration. `githubstatus.com/api/v2/summary.json`
  reports overall `Minor Service Outage` with **`API Requests` →
  `partial_outage`**, open since 2026-07-19T23:34Z. The 503 body is GitHub's
  own (`"No server is currently available to service your request"`) and
  carries an `X-GitHub-Request-Id`, so it is not a local proxy synthesizing it.
- **The credentials are sound — do not go looking for an auth bug.** Signing
  the App JWT by hand from the same wrapper environment and calling
  `GET /app/installations` returned **200** with exactly one installation
  (`livespec-pr-bot`, id `131208965`, `suspended_at: null`, `contents: write`).
- **BOTH App endpoints are affected, intermittently.** Over 8 consecutive mint
  attempts, 8 failed — but at DIFFERENT stages: some on the `GET
  /app/installations` discovery call, some after that call succeeded, on the
  `POST /app/installations/{id}/access_tokens` mint. So the earlier note naming
  `/app/installations` as *the* failing endpoint was reading one sample.
- Unrelated GitHub paths stayed healthy throughout (`gh api rate_limit` over
  the human OAuth token worked), which is what "partial" means here.

**Do NOT route around this with a personal token.** The App identity is a
chosen boundary. Retry the push; if it still fails, confirm against the status
page and report to the maintainer rather than swapping credentials.

**Side finding, NOT owned by this thread — the mint has no transient-5xx
retry.** `livespec-runtime`'s `livespec_runtime/github_auth/mint.py`
(`_request_json`, `:107`) turns any `urllib.error.URLError` — a 503 included —
straight into a terminal `GithubAppAuthError`. Because that helper is the
credential path for EVERY fleet repo's automated git operations, a partial
GitHub API outage hard-blocks every push fleet-wide with no retry. A 503 is an
environment/timing failure that a retry could fix, which is precisely the class
the repo's own Result-railway guidance says to treat as retryable.

**Swept 2026-07-20 — it is SIX sites across FIVE repos, in three distinct
implementations**, so the fix is a cross-repo epic, not a one-file change:

| Repo | Site | Kind |
|---|---|---|
| `livespec-runtime` | `livespec_runtime/github_auth/mint.py` | Python, source of truth |
| `livespec` | `.claude-plugin/scripts/_vendor/livespec_runtime/github_auth/mint.py` | vendored, byte-identical |
| `livespec-orchestrator-beads-fabro` | same vendored path | vendored, byte-identical |
| `livespec-orchestrator-git-jsonl` | same vendored path | vendored, byte-identical |
| `livespec-dev-tooling` | `ci-runner/supervisor/mint-jitconfig.sh` | independent shell mint |
| `livespec-dev-tooling` | `ci-runner/gate-runner/app-installation-token.sh` | independent shell mint |

Three facts that shape it. **The vendored copies do NOT self-sync** — each
consumer tracks `livespec_runtime` in its own `.vendor.jsonc` with a pinned
`upstream_ref` (`livespec` is on `v0.11.0`), gated by `check-vendor-manifest`,
so propagation is a deliberate ref bump plus re-copy per consumer. **The two
shell mints are a different failure mode** — they serve the self-hosted CI
runner, so their symptom is lost CI capacity rather than a blocked push. **The
prior-art `_app_token.py` is genuinely gone**, promoted into the runtime and
removed, so there is no fourth divergent copy.

**Do NOT wire in the existing `retry_with_backoff`**
(`livespec_runtime/cross_repo/retry.py`) as a drop-in: it catches broadly (so a
non-retryable 401 would burn three attempts) and returns `None` on exhaustion
(destroying the actionable diagnostic that made this outage diagnosable). The
fix is STATUS-AWARE retry — 5xx and 429 retried, 4xx failing fast.

The sharpest framing for whoever picks this up: CI's own
`actions/create-github-app-token@v1` DOES retry, and burned four attempts
during this same outage. Every mint the fleet wrote itself has none.

## Progress

| Gate | State | Where |
|---|---|---|
| A — tests in `just check`/CI | **DONE, live-exercised** | livespec PR [#1387](https://github.com/thewoolleyman/livespec/pull/1387), merged 2026-07-19 |
| C — ruff lint + format | **DONE, live-exercised** | livespec PR [#1396](https://github.com/thewoolleyman/livespec/pull/1396), merged 2026-07-19 |
| D — pyright strict | **DONE, live-exercised** | livespec PR [#1408](https://github.com/thewoolleyman/livespec/pull/1408), merged 2026-07-19 |
| B — coverage | **DONE, live-exercised** | livespec PR [#1440](https://github.com/thewoolleyman/livespec/pull/1440), merged 2026-07-19 (`198c62dc` + `108009b5`) |
| E — ROP railway | **CONFORMANT — verified, zero code changes needed.** Ruled broad-only; the one broad catch already carries the exact ratified marker. Remaining work is a role-key DECLARATION sequenced after `cvz` — see §"Gate E" | — |

**Phase 1 is effectively complete.** Gates A, C, D, and B are merged and
live-exercised. Gate E needs no code: the ruling landed broad-only and the
overseer already conforms (verified mechanically — see §"Gate E"). All that is
left is a role-key declaration that must wait on the rop-sweep thread's `cvz`.

**Phase 2 is now the live work**: decisions D4/D5/D6 were resolved on
2026-07-19, it is anchored to epic `livespec-b1uo`, and it was then RESHAPED the
same day by D7 (the overseer is Control Plane, not Spec Plane).

# ✅ START HERE — the home question is RULED; here is what is left

**`livespec-b1uo.1` — where does the overseer live? RULED 2026-07-20:** its own
dedicated repo, registered under **`fleet`** in
`.livespec-fleet-manifest.jsonc`, under a **NEW pin-consuming repo class**, as a
full fleet member following the same development discipline as every other
member (worktree → PR → merge, `just check`, factory-driven changes). Read
§"D9 RULED" for the reasoning and the obligations that follow; read §"D8 — the
home question" for the measured dependency analysis behind it, which you should
NOT re-derive.

**⚠️ §"THE 9th-FLEET-REPO PRICE WAS WRONG" is itself partly wrong** — two of its
four clauses are mechanically right but framed as savings when they are
exemptions the overseer should DECLINE (the beads tenant and pin-web
participation are both things it WANTS). §"D9 RULED" carries the corrected
table. Do not act on the earlier one alone.

**Both names are RULED (maintainer 2026-07-20):**

- **Repo class: `control-plane-tool`.** Chosen over `operator-tool`,
  `console-tool`, and `control-plane-daemon`. It anchors to the plane
  vocabulary the spec and diagram conventions already require, reads as a PEER
  of `console` rather than a component of it, and does not over-narrow the way
  `control-plane-daemon` would (a future purely-interactive Control-Plane
  member would not be a daemon).
- **Repo name: `livespec-overseer`.** Chosen over `livespec-overseer-tmux`,
  `livespec-control-plane-overseer`, and `livespec-session-overseer`. It keeps
  the name every existing artifact already uses — `.claude/skills/overseer/`,
  `overseerd`, `overseer-start`, `~/.livespec-overseer.jsonl`,
  `~/.livespec-overseer-stamps.json` — so nothing needs renaming, and it
  carries no shared suffix, so it can never be ambiguously abbreviated.

  **The bare name is deliberate — do NOT "fix" it by adding a `-tmux` suffix.**
  The fleet's suffixes (`livespec-driver-claude` / `-codex`,
  `livespec-orchestrator-beads-fabro` / `-git-jsonl`) mark places where
  multiple interchangeable realizations genuinely coexist. D4 ruled Linux+tmux
  a DECLARED REQUIREMENT and explicitly rejected abstracting the host boundary
  as speculative generality, so a suffix would advertise a variance the ruling
  says will not exist.

**The immediate next steps, in order:**

1. **Add the class value** in `livespec-dev-tooling` (`REPO_CLASSES`,
   `_contract_rows.py:65`) — a spec-backed change, so it goes through that
   repo's propose-change → independent Fable review → revise cycle, NOT a
   unilateral edit. Both subtraction sets (`_PIN_WEB_CLASSES`,
   `_DEV_TOOLING_PIN_CLASSES`) pick the new class up automatically.
2. **Then** create `livespec-overseer`, register it in
   `.livespec-fleet-manifest.jsonc` under `fleet` with
   `"class": "control-plane-tool"`, and move the folder — the relocation
   blocker is the positional path traversal in `_default_manifest`
   (`supervisor.py`, ~:2686 — cite the SYMBOL, not the line; see the drift note
   in §"The ONE real coupling"); see
   §"The ONE real coupling, and it is shallow".

Do NOT start `b1uo.4` / `b1uo.5` (the Driver bindings) — they are BLOCKED and
likely superseded by D7. An earlier version of this page told you to start at
`b1uo.1` because "the two Driver bindings have nothing to bind to"; that framing
predates D7 and is wrong.

# ✅ Gate B — DONE (was blocked all of 2026-07-19; the blocker is gone)

**Live-exercise evidence.** Post-merge master CI run
[29700273133](https://github.com/thewoolleyman/livespec/actions/runs/29700273133)
ran `check-overseer` against COMBINED master and it passed, alongside
`check-coverage`, `check-types`, `check-lint`, and `check-per-file-coverage`.
That is the bar — a green PR is not evidence; the post-merge master run is.

**What unblocked it.** The `check-doctor-static` red that blocked every local
push in this repo was resolved by another session's revert, which landed as
`333e5263` (a REBASED re-apply — the original `6bdccd04` is not an ancestor of
master, so the same change exists under two SHAs). Nothing about Gate B itself
was ever wrong.

**A real defect CI caught after the rebase, worth carrying forward.** The branch
went green locally and RED in CI: six beside-tests simulated permission denial
with `chmod`, and **CI runs its container steps as ROOT, where mode bits deny
nothing** — 6 failed, 432 passed. Reproduced deterministically with
`sudo -n env "PATH=$PATH" "HOME=$HOME" uv run pytest .claude/skills/overseer/ -q --no-cov`,
which is the cheapest way to check this class of thing before pushing.

The irony is instructive: THIS BRANCH'S OWN commit message already reasoned
about that exact hazard for one site (the `# pragma: no cover` on
`_clear_idle_nudge_state`'s `except OSError`, whose stated rationale is "CI runs
its container steps as root, where chmod denies nothing"). The reasoning was
right and was applied to one branch while six siblings kept relying on the
assumption it refutes.

Fixed by injecting the denial at the call the implementation actually makes
(`Path.open` / `read_text` / `iterdir` / `is_dir` raising `PermissionError`)
rather than at the filesystem. That is NOT a new idiom — the same file already
had `monkeypatch.setattr(registry.os, "fsync", _boom)` and a
directory-where-a-file-belongs test, both root-proof; the chmod tests were the
outliers. Verified 438 passed as root AND as an unprivileged user, 100.00%
coverage held both ways.

**If you write a permission-denial test in this folder, do not use `chmod`.**
Patch the call. Otherwise it passes locally and silently stops testing anything
in CI, which is worse than no test.

> **This handoff was rescued from the primary checkout on 2026-07-19.** It had
> been left UNCOMMITTED on disk at `/data/projects/livespec` — 153 unversioned
> lines, one `git checkout` from oblivion — because the session that wrote it
> believed the push blocker "prevents committing anything". That belief was
> false at both the commit AND the push step (post-mortem lesson 3 below).
> **Keep this file committed; update it in-session as findings land, not at
> session end.** The root-cause fix for that whole class of failure is its own
> thread now: `plan/archive/plan-thread-integrity/` (ARCHIVED 2026-07-20;
> epic `livespec-nr5h`).

## Blocker post-mortem (2026-07-19) — resolved, kept for the lesson

The operational "is the blocker gone / how to land Gate B" steps that stood here
are DELETED: Gate B is merged and the blocker is gone. What is worth keeping is
why it happened, because the shape recurs.

`check-doctor-static` went red on livespec master with 53
`(sibling, missing-canonical-slug)` drift pairs, all
`livespec-console-beads-fabro`, blocking every LOCAL push in the repo while
master CI stayed GREEN. Cause: commit `7107be6c` added that repo to
`.livespec.jsonc`'s `cross_repo_targets` so a cross-tenant work-item reference
would resolve — a PLANNING purpose. But `cross_repo_targets` is DUAL-PURPOSE: it
is also the input to `doctor-wiring-completeness-cross-repo`, which requires
every listed sibling to wire all 54 canonical PYTHON check slugs.
`livespec-console-beads-fabro` carries ZERO first-party `.py` and 30 `.rs` files,
so it could not satisfy them at any version.

Resolved by revert, landed as `333e5263` (a REBASED re-apply, so the original
`6bdccd04` is not an ancestor of master and the same change exists under two
SHAs — do not search for the original).

**The durable lessons, none of which are about this one bug:**

1. **A green master CI is not evidence that local `just check` is green.** CI
   clones siblings from a HARDCODED list in `.github/workflows/ci.yml` that is
   not derived from `.livespec.jsonc` and has drifted from it in both
   directions, so a newly-registered sibling is never cloned in CI and the check
   cannot evaluate it there. This is filed on the fleet-pin-propagation side as
   `livespec-i6pyy6` ("derive the CI sibling-clone list from `.livespec.jsonc`"),
   which carries the drift table and the derive-from-source fix. **NOT
   `livespec-fxxfq6`** — that item was regroomed out and CLOSED on 2026-07-19.
2. **A red `doctor-static` freezes the SPEC LIFECYCLE, not just pushes.**
   propose-change runs doctor static at BOTH its pre-step and post-step, and
   `--skip-pre-check` suppresses only the pre-step. The proposed-change file
   still lands on disk and the CLI then reports exit 3 — so the operation cannot
   complete cleanly, though the artifact is not lost.
3. **Doc-only work was never blocked at all.** `check-pre-commit-doc-only` runs
   seven targets and `check-doctor-static` is not among them (`justfile:518`),
   and `check-pre-push` routes a zero-`.py` push to that same subset
   (`justfile:548`). The belief that the blocker "prevents committing anything"
   was false at BOTH steps, and acting on it is what left this handoff
   unversioned for 153 lines. See `plan/archive/plan-thread-integrity/` (ARCHIVED 2026-07-20), the thread
   spun out to fix that class of failure.
4. **Never infer another session's liveness from `tmux ls`.** It reads only the
   socket namespace named by `TMUX_TMPDIR`; the fleet's sessions live on the
   default socket at `/tmp/tmux-1000/default`. This page previously asserted a
   session was gone on that basis and was wrong — it was alive and committing
   throughout. Read commit trailers instead:
   `git log -1 --format=%B <sha> | grep session_`.

## What Gate B contained (merged as `198c62dc`)

100.00% coverage — statements AND branches — on every module; 344 → 438 tests; full
`just check` green (all 71 targets); no behavior change. Sabotage-verified three ways.

- **Boundary extraction** (the D1 option the maintainer chose over a scoped threshold).
  The premise that host-glue is untestable proved mostly false. `overseer-start` was the
  real case: its `main()` constructed its own `TmuxIO`, so the whole bootstrap
  orchestration could only run against a live tmux window and therefore never ran. It now
  takes `io` / `build_supervisor` / `core_root` seams defaulting to the real
  implementations. `core_root` specifically keeps the daemon's marker-dir `mkdir` out of
  the real checkout when a test drives the split path. 49% → 100%.
- **`tmuxio.WindowLayoutDriver`** — a second Protocol for the six window-LAYOUT methods,
  the counterpart to Gate D's `PaneDriver` and the reason that one declares only twelve
  of `TmuxIO`'s methods.
- **Two `# pragma` annotations, the FIRST in first-party code** (all 33 pre-existing ones
  are vendored), each with its reasoning inline: `_clear_idle_nudge_state`'s
  `except OSError` (`no cover` — only reachable via a permission-denied parent, and CI
  runs as root where chmod denies nothing, so a test would pass locally and silently stop
  exercising it in CI); and `elif claude_status == "busy"` (`no branch` — provably always
  True there, but KEPT as an `elif` rather than demoted to `else` because the proof
  depends on the current contents of `_CLAUDE_BUSY_STATUSES`, which exists to be extended).
- **Beside-tests omitted from measurement**, mirroring `[tool.pyright].exclude`: coverage
  measures the code under test, not the test code.
- **Also closes a hole in Gates C AND D.** `ruff check .` and pyright's `include` both
  resolve files by EXTENSION, so `overseer-start` and `overseerd` — Python with a shebang,
  invoked by bare name — were never linted or type-checked at all. Explicitly they carried
  17 ruff findings (including 7 `print` calls Gate C claimed to have eliminated) and 5
  pyright errors. `[tool.ruff].extend-include` now matches the folder's `overseer*` naming
  convention; pyright names the two files individually; the launcher's output goes through
  the `streams` sink.

## Verified daemon findings — ✅ NOW FILED as work-items (2026-07-19)

All three were independently verified in source, not taken on trust. None is a live
defect. **They are now tracked in the ledger rather than only on this page**, so they
survive this thread closing:

- **`livespec-ail8`** (bug, P3) — findings 1 and 2 below, filed TOGETHER because they
  are the same "topic is not globally unique" root shape in the same function, gated
  behind the same unset flag; fixing either alone leaves the trap armed. Re-verified at
  master before filing: `run()` carries `recover: bool = False` (`supervisor.py`, `def run`, ~:2622)
  and `grep -n 'recover' .claude/skills/overseer/overseerd` returns nothing, so the
  recovery path is genuinely unreachable in production.
- **`livespec-3rj4`** (task, P3) — finding 3 below. Filed as a task, not a bug, because
  the fix changes the fail-soft contract's shape and so needs a decision; three options
  are laid out on the item with a recommendation.

The ledger is now the source of truth for their status; the text below is kept as the
analysis that produced them.

1. **`recover_missing_sessions` derives session names with an EMPTY collision set.**
   `_colliding` is only populated inside `build_rows` (supervisor.py), but `run()` calls
   recovery BEFORE the first `tick()`. A mapping row with no stored `tmux` would derive
   the bare topic instead of `<slug>-<topic>`.
2. **Codex reboot-recovery dispatch keys on topic alone.** `recover_missing_sessions`
   calls `codex_sessions.latest_session_for_thread_name(track.topic, …)` with no repo
   scoping, so two watched repos sharing a plan topic could resume the wrong rollout in
   the wrong repo.
   **SEVERITY CORRECTION for both:** the shipped daemon calls
   `supervisor.run(..., recover=False)` — deliberately and documented ("keeps the daemon a
   pure surface-only watcher"). So `recover_missing_sessions` is **unreachable in
   production today**. These are traps for whoever enables recovery, not active bugs. A
   sub-agent reported #2 as "reachable rather than exotic"; that framing is wrong.
3. **`rewrite_mapping` / `repoint_tmux` return a claim, not a fact.** Both return a count
   computed from the in-memory diff, but `_atomic_write` beneath them swallows `OSError`
   into a warning by design (the documented B7 fail-soft). So both can report "dropped N
   rows" when nothing persisted. Self-correcting (archive-GC re-drops next tick), but the
   return value is unreliable. Fixing means `_atomic_write` returning a success flag —
   a change to the fail-soft contract's shape, hence a decision, not a fix.

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

## Gate E — the only remaining Phase 1 gate

**Scope is settled (D2 above): the overseer goes on the railway.** What is being
coordinated with `rop-sweep-fleet-policy` is the responsibility split and the
ordering, because getting the ordering wrong turns core master red.

### Measured facts about the target (2026-07-19, master)

- The overseer is 8 product modules under `.claude/skills/overseer/`, **FLAT** —
  there is NO `io/` subdirectory and no pure-versus-impure layer split.
  Command: `ls .claude/skills/overseer/`.
- **2 `raise`** statements and **36 `except`** handlers
  (registry 11, supervisor 8, claude_sessions 6, codex_sessions 6, tmuxio 3,
  jsonio 2, signals 1). Command:
  an AST walk over the 8 product modules counting `ast.Raise` / `ast.ExceptHandler` nodes. **Do NOT use the `grep -c 'raise \|except '` this page used to recommend** — it produced BOTH of the wrong numbers it reported: it counted 4 prose/docstring uses of the English word "raise" as statements, and its trailing-space pattern silently MISSED `registry.py`'s bare `raise` re-raise. The real statements are `registry.py:310` and `supervisor.py:2929` (a `raise SystemExit(main())`).
- **Three of the five ROP checks currently scan ZERO files in core.**
  `check-no-raise-outside-io`, `check-no-except-outside-io`, and
  `check-public-api-result-typed` each log `"role key absent — check no-ops"` and
  return 0, because `source_trees` and `io_trees` are both empty tuples.
  `check-rop-pipeline-shape` and `check-supervisor-discipline` ARE active.
  Command: `uv run python -c "from livespec_dev_tooling.config import load_config;
  import pathlib; c = load_config(repo_root=pathlib.Path('.')); print(c.source_trees, c.io_trees)"`.

  This is **already owned by the rop-sweep thread** as
  `livespec-dev-tooling-cvz` ("`source_trees` undeclared → check scans ZERO files
  in core + both Drivers"). Do NOT file a duplicate; it was checked before this
  was written.

### The ordering hazard — read before touching either side

If `source_trees` is declared INCLUDING `.claude/skills/` before the overseer is
refactored, core master goes RED immediately: 37 excepts and 5 raises in a tree
with no `io/` to legalize them. That is textbook enforcement-before-adoption,
which `.ai/ci-gate-discipline.md` names as the thing that creates revert-worthy
breakage — "an enforcement check must not land at error severity before the
rollout it asserts has completed."

### ✅ AGREED SPLIT AND ORDERING — settled with `rop-sweep-fleet-policy` 2026-07-19

Encoded in BOTH plans per the maintainer's instruction; their side is committed
as `2333a773` (livespec PR
[#1451](https://github.com/thewoolleyman/livespec/pull/1451)).

1. **Theirs (`livespec-dev-tooling-cvz`)**: declare core's `source_trees` /
   `io_trees` **WITHOUT** `.claude/skills/`.
2. **Ours (Gate E)**: bring the overseer folder to conformance.
3. **Either thread, ONLY AFTER (2)**: add `.claude/skills/` to `source_trees` —
   enforcement arrives after adoption, per `.ai/ci-gate-discipline.md`.

They confirmed step 1 does NOT need to wait on us: simulating the check over
core's main tree yields 3 narrow offenses under the strict rule and **0 under
broad-only**, so their work proceeds independently.

### ✅ RULED broad-only (2026-07-19) — and the overseer ALREADY CONFORMS

The maintainer delegated the flat-package rule to the `rop-sweep-fleet-policy`
thread, which **settled it as broad-only**. Gate E therefore went from 35 sites
to 1 — and that 1 site turns out to need **NO code change at all**.

**The rule was already ratified text**, which is worth knowing before anyone
re-opens it. `non-functional-requirements.md:649`: "In a repo without an `io/`
layered tree (`io_trees` unset …), that check MUST still run rather than no-op,
but in that mode it polices catch BREADTH rather than Try-node POSITION: a BROAD
catch outside the `supervisor_entry_files` / `commands_trees` exemptions is an
offense, while a NARROW, ENUMERATED catch in an entry artifact's helper function
is PERMITTED and MUST NOT be flagged. Position-policing is a layered-architecture
concern that does not apply to a flat package."

**Verified conformance, mechanically, not by eye** (AST walk over
`.claude/skills/overseer/*.py` excluding beside-tests):

| Requirement (source) | Overseer | Verdict |
|---|---|---|
| At most one broad catch per supervision loop (`:673`) | exactly **1** broad; 35 narrow | ✅ |
| Marker from the closed set of five (`:781`) | `— sole loop-iteration bug-catcher: log traceback, continue` | ✅ byte-exact match to form 4 |
| Direct child of the supervision-loop body (`:673`) | `Try` is a direct child of `while True` (`supervisor.py`, ~:2659-2660) | ✅ |
| MUST log the FULL traceback (`:673`) | `traceback.format_exc()` | ✅ |
| Silent `pass` forbidden (`:673`) | logs, does not pass | ✅ |
| MUST NOT exit (`:673`) | continues; no raise/exit in the handler | ✅ |

The 35 narrow typed catches are **explicitly permitted** and MUST NOT be
flagged — under breadth mode they are the "very seam lifts this section
prescribes".

**Be precise about what is and is not enforced.** `:649` also says the breadth
mode "is a spec rule enforced by REVIEW today — the shipped check still no-ops
when `io_trees` is unset; mechanizing it is tracked follow-up work and MUST NOT
be described as already enforced." So the table above is conformance with the
RATIFIED RULE, verified by hand-run AST; the checker itself cannot yet confirm
it. Do not claim Gate E is mechanically gated until the breadth mode ships.

### What actually remains for Gate E

Measured: core declares **NONE** of the four role keys — `source_trees`,
`io_trees`, `supervisor_entry_files`, and `commands_trees` are all empty tuples
in `pyproject.toml`. So the remaining work is declaration, not refactor:

1. **Blocked on theirs**: `cvz` declares core's role keys WITHOUT
   `.claude/skills/` (agreed step 1). **Re-verified STILL BLOCKED 2026-07-20** —
   all four keys remain empty tuples. Re-run the check before assuming otherwise:

   ```bash
   mise exec -- uv run python -c "
   from livespec_dev_tooling.config import load_config
   import pathlib
   c = load_config(repo_root=pathlib.Path('.'))
   print(c.source_trees, c.io_trees, c.supervisor_entry_files, c.commands_trees)"
   ```

   Do NOT pre-empt this by declaring the keys from THIS thread — the agreed split
   gives step 1 to `rop-sweep-fleet-policy`, and declaring them here would land
   enforcement before their adoption sweep, which is the exact
   `.ai/ci-gate-discipline.md` failure the split exists to avoid.
2. **Then ours**: when `.claude/skills/` is added to `source_trees` (agreed step
   3), `supervisor.py` must ALSO be covered by `supervisor_entry_files` (or the
   equivalent exemption of the day), or the one sanctioned loop-iteration catch
   will read as an offense in breadth mode. **That is the whole of Gate E's
   remaining risk** — a missing declaration, not missing conformance.

### Superseded: the pre-ruling analysis (kept so the range is not re-derived)

**Their answer to our design question: declaring the whole folder an `io` tree is
NOT acceptable.** `io_trees` entries are WHOLESALE EXEMPT, so declaring
`.claude/skills/overseer/` an io tree would make every handler instantly legal
and the check vacuous over that tree — "a bypass wearing a declaration's
clothes", the same move already rejected for `livespec-dev-tooling`, and
forbidden by `.ai/ci-gate-discipline.md`'s "fix the gate, not the bypass". That
option is CLOSED.

**Gate E's size depends entirely on an unresolved rule, and the range is 1 site
versus 35.** Their measurement, which corrects the count on this page (36
handlers, not the 37 a cruder `grep -c` reported here): the overseer carries
**36 `except` handlers of which exactly ONE is broad** — `supervisor.py`'s
`except Exception`. The other 35 are narrow typed catches (registry 11,
claude_sessions 6, codex_sessions 6, supervisor 6, tmuxio 3, jsonio 2,
signals 1).

- Under **broad-only**: Gate E is **1 site** — declare `supervisor.py`'s sole
  `except Exception` as a boundary. No `io/` layer, no refactor.
- Under **strict**: **35 sites** need an `io/` split or equivalent.

**The unresolved rule** (their §"THE OPEN DESIGN QUESTION", which also blocks
their `qm5`, `cvz`, and `6vz`): v169 ratified "narrow at the seam; broad only at
the boundary", but `no_except_outside_io` bans ALL `try/except` outside `io/`,
narrow included. That is coherent for a LAYERED package, where the narrow seam
catches live in `io/`. For a FLAT package there is no `io/`, so the strict
reading bans the very form v169 sanctions. The counter-argument is that
~~`contracts.md:213` says "no `try/except` is wholesale exempt"~~ — **that
citation is FABRICATED and MUST NOT be relied on.** Verified 2026-07-20: the
phrase "wholesale exempt" appears NOWHERE in `SPECIFICATION/`
(`git grep -n 'wholesale exempt' -- 'SPECIFICATION/*.md'` returns nothing), and
`contracts.md:213` is mid-paragraph about plugin-install verification. The phrase
exists exactly once in the whole repo — as `plan/rop-sweep-fleet-policy/handoff.md`'s
OWN prose, i.e. another plan document's paraphrase, which got copied here and
promoted into a spec quote. The underlying question (does "wholesale" mean
TREE-level or per-catch?) was real, but it is MOOT: the rop-sweep thread settled
the rule broad-only, which is what §"RULED broad-only" above records.

**So do not begin Gate E's refactor until that is ruled on**, or risk doing 35
sites of work the ruling makes unnecessary. If it lands broad-only, Gate E is
close to trivial.

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
- **D2 — ROP railway for host-glue (Gate E). ✅ RESOLVED 2026-07-19 by maintainer
  ruling: `.claude/skills/` is IN SCOPE and follows the discipline — it is NOT
  exempt.** The question put was whether to exclude `.claude/skills/` when core
  declares `source_trees`. The answer was "DO NOT EXCLUDE IT, IT SHOULD FOLLOW
  DISCIPLINE", with a direction to coordinate the responsibility split and
  dependency ordering with the `rop-sweep-fleet-policy` session and encode the
  result in BOTH plans.

  **This session had recommended the opposite** (exempt it, on the
  `.claude/hooks/` precedent) and was overruled. Do not resurrect the exemption
  argument from the earlier text on this page; it is settled.
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

### ✅ ALL THREE PHASE 2 DECISIONS RESOLVED (maintainer, 2026-07-19)

**Phase 2 is COMMITTED and anchored to epic `livespec-b1uo`** (livespec CORE
tenant), with five children filed. Status is READ from the ledger, never stored
here.

- **D4 — portability. RESOLVED: Linux + tmux is a DECLARED REQUIREMENT.** Do not
  abstract the host boundary; that option was considered and rejected as
  speculative generality. Measured coupling: `claude_sessions.py` reads
  `/proc/<pid>/stat` (macOS has no `/proc` AT ALL — this is absent, not merely
  different), all six product modules touch tmux, and it reads
  `~/.claude/sessions/<pid>.json` plus Codex rollout files. → `livespec-b1uo.2`.
- **D5 — manifest boundary. RESOLVED: stays FLEET-SELF-APPLICATION.** A shipped
  overseer MUST NOT depend on `.livespec-fleet-manifest.jsonc` as a functional
  contract. `non-functional-requirements.md:205` binds that machinery to "the
  livespec fleet, its adopters, and the reference orchestrators, never a
  third-party `livespec` consumer or the `/livespec:*` plugin skills core ships"
  — shipped code reading it would cross that line and need a spec amendment. An
  adopter FAMILY may still run it against its own manifest, which the spec
  already contemplates ("an adopter MAY be a fleet itself"). → `livespec-b1uo.3`.
- **D6 — RESOLVED: drive it now as an epic.** This overrode the recommendation
  to park Phase 2 until an adopter asked.

### ⚠️ D7 — PLANE RULED: the overseer is CONTROL PLANE (maintainer, 2026-07-19)

**This reshaped Phase 2 within hours of filing it, and it is the most important
thing on this page for anyone picking the epic up.**

The first Phase 2 breakdown assumed a SPEC-PLANE home — ship from livespec core,
bind from both Drivers, following the `/livespec:*` pattern. Checking that
premise against the spec before writing code showed it was wrong.

`spec.md:283` defines three planes and states: "conflating them is the recurring
design error. Each plane owns a distinct concern, and every artifact and skill
belongs to exactly one." The **Control Plane** is "the operator experience:
observe every plane's state, surface what needs attention, and coordinate the
human through multi-session work." That is the overseer's job description
almost verbatim. The Spec Plane is "concerned with WHAT the system should do" —
which the overseer is not.

The overseer READS `plan/<topic>/`, which IS Spec-Plane-owned; that is what made
the wrong answer tempting. But reading is not owning, and "observe every plane's
state" is precisely the Control Plane's defined job.

### Phase 2 work breakdown — epic `livespec-b1uo`, as reshaped

| Item | State | What |
|---|---|---|
| `livespec-b1uo.1` | **RE-SCOPED, foundational** | Choose the Control-Plane home, THEN implement the move. Design-first — the answer is genuinely open |
| `livespec-b1uo.2` | unchanged | Declare + enforce the Linux/tmux precondition (D4) |
| `livespec-b1uo.3` | unchanged | Decouple the shipped overseer from the fleet manifest (D5) |
| `livespec-b1uo.4` | **BLOCKED, likely superseded** | Targeted `livespec-driver-claude` — a SPEC-plane Driver surface |
| `livespec-b1uo.5` | **BLOCKED, likely superseded** | Targeted `livespec-driver-codex` — same reason |

`.2` and `.3` survive untouched because they are properties of the TOOL, not of
its home. `.4` and `.5` are blocked rather than closed because the overseer does
have an interactive half today (the bottom pane), so some per-runtime binding
may still be needed — the open question is from whose surface, which `.1`
decides.

### D8 — the home question (THE live question; measured 2026-07-19)

**Maintainer's leaning, not yet a ruling: a SEPARATE DEDICATED REPO** — "loosely
coupled, cohesive, keeps bloat out of core." They asked for the dependencies and
their DIRECTION to be worked out carefully before committing. That analysis was
done and is below. **Do not re-derive it; extend it.**

#### Measured dependency facts (re-runnable commands in parentheses)

- **Zero third-party packages. Zero imports from livespec core.** Pure stdlib
  (`argparse`, `json`, `pathlib`, `subprocess`, `fcntl`, `re`, `os`, `sys`,
  `time`, `traceback`, `dataclasses`, `typing`, `contextlib`, `datetime`,
  `itertools`, `shlex`, `tempfile`, `collections`) plus its own 8 modules.
  (AST walk over `.claude/skills/overseer/*.py` collecting `Import`/`ImportFrom`.)
- **Binaries it shells out to:** `tmux` (INJECTABLE — `tmux_bin: str = "tmux"`,
  `tmuxio.py:150`), `git` (one `check-ignore` call), and the `claude` / `codex`
  CLIs when restarting a session.
- **Orchestrator dependency: NONE.** Zero beads / fabro / dolt references; the
  single "fabro" hit (`registry.py:917`) is a comment naming a tmux session.
  (`grep -rn -i 'beads\|fabro\|dolt' .claude/skills/overseer/*.py`)
- **Driver dependency: NONE, in either direction.** It observes the agent
  RUNTIMES (`~/.claude/sessions/<pid>.json`, `~/.codex/sessions/…`) and invokes
  their CLIs. It never imports or resolves `livespec-driver-*`. It runs with
  neither Driver installed.
- **State lives in `$HOME`, not in any repo** — `~/.livespec-overseer.jsonl`,
  `~/.livespec-overseer-stamps.json` (`registry.py:111`).

#### The ONE real coupling, and it is shallow

`_default_manifest` (`supervisor.py`, ~:2686) resolves the fleet manifest by
POSITIONAL PATH TRAVERSAL — `Path(__file__).resolve().parents[3] /
".livespec-fleet-manifest.jsonc"`, i.e. "three directories up is the repo root".
**That breaks the instant the folder moves anywhere**, so it is the concrete
relocation blocker.

**📌 CITE `supervisor.py` BY SYMBOL, NOT BY LINE.** An independent drift sweep
found this ONE fact cited at THREE different line numbers on this page, every one
of them wrong — including the value written the same morning it was "re-verified",
which PR #1523 invalidated hours later by inserting a method earlier in the file.
`supervisor.py` is ~2900 lines and changes most days, so any line number written
here is stale on arrival. Every `supervisor.py` citation on this page has been
rewritten to name the SYMBOL with an approximate line (`~:2686`); keep that form.
The lesson generalizes: line citations into a fast-moving file are a maintenance
liability, and the sweep found ALL of this page's citation drift concentrated in
exactly this one file — every citation into the three sibling repos verified
clean. Re-verified 2026-07-20; every `supervisor.py` line number in
this section was re-measured at the same time, because they had ALL drifted by
~15 lines.

But the fix is small, and this RESIZES `livespec-b1uo.3` — it is not the refactor
that item was filed as. The manifest is used for exactly ONE thing: deriving the
watch-set of repos. And `watch_repos: list[str] | None = None` is ALREADY an
injectable field (`supervisor.py`, ~:570) that short-circuits the manifest entirely
(`supervisor.py`, ~:727). Today only the beside-tests inject it — the CLI
deliberately exposes no knob ("de-gold-plated 2026-07-13").

#### ⚠️ CORRECTION 2026-07-20 — "just expose the seam on the CLI" is NOT available

The sentence that stood here — *"So b1uo.3 is exposing an existing seam on the
CLI, not building one"* — is **wrong as a plan**, and re-measuring the code is
what showed it. Exposing a watch-set flag would REVERSE a deliberate design
decision recorded in two places:

- `_build_supervisor`'s docstring (`supervisor.py`, ~:2691-2695): *"Build the
  daemon's `Supervisor` for the CLI — with NO tunable surface. The invocation
  surface carries no watch-set / store / stamp knobs (they were de-gold-plated
  2026-07-13)."*
- `.claude/skills/overseer/AGENTS.md` §"Build / toolchain facts", which
  enumerates the deliberately-absent flags by name — `--store` / `--stamp` /
  `--repos` / `--repos-only` / `--manifest` — and states that the injectable
  dataclass fields exist for the BESIDE-TESTS only.

So `b1uo.3` is a genuine design decision, not a mechanical seam-exposure, and it
is constrained from three sides at once: **D5** says a shipped overseer MUST NOT
depend on `.livespec-fleet-manifest.jsonc` as a functional contract; the
**de-gold-plating** says do not add CLI config knobs; and the **relocation**
breaks `parents[3]` regardless, so doing nothing is not an option either.

**Recommended: a watch-set config in `$HOME`, NOT a CLI flag.** The overseer's
state ALREADY lives in `$HOME` and not in any repo (`~/.livespec-overseer.jsonl`,
`~/.livespec-overseer-stamps.json`), so a watch-set that lives beside them is
consistent with the existing shape, keeps the invocation surface knob-free
(honoring the de-gold-plating), and removes the manifest dependency (satisfying
D5) in one move. It also generalizes to the adopter case for free: a third party
supplies their own watch-set without a livespec install and without a fleet
manifest.

Alternatives, with why each is weaker: a **CLI flag** directly reverses the
de-gold-plating; an **env var** is the same knob with worse discoverability and
no natural default; **deriving the watch-set from the JSONL store's assigned
rows** cannot work alone, because discovery must scan repos that have NO assigned
track yet in order to surface `unassigned` plans (invariant 4), so it would make
an unassigned plan undiscoverable until someone had already assigned it.

**This is a maintainer decision, not self-resolvable** — it trades against two
previously-recorded decisions. Do NOT implement a `--watch-repos` flag on the
strength of the superseded sentence above.

#### Dependency DIRECTION — the part the maintainer asked to weigh

After `b1uo.3`, every arrow points OUTWARD and nothing points in:

    overseer -> livespec core     NONE (the manifest edge is what b1uo.3 removes)
    overseer -> Drivers           NONE
    overseer -> orchestrator      NONE
    anything -> overseer          NONE

It satisfies the No-Circular-Dependency Directive trivially, because it would
depend on nothing in the fleet at all. That is the strongest argument for the
separate-repo instinct: it is not loosely coupled, it is UNCOUPLED.

#### The question that falls out — decide this deliberately

**If it depends on nothing, what makes it a FLEET MEMBER rather than an
independent tool that merely understands livespec's plan convention?** Membership
would be by CONVENTION-CONSUMPTION, which is a different basis from every one of
the current eight members. Worth an explicit answer rather than a default.

#### What a 9th fleet repo actually costs (priced 2026-07-19)

The manifest currently lists eight members, each with a `class`; a member's
profile is DERIVED from its class. A ninth would need a new class and inherits:
the `baseline` conformance profile, the copier scaffold, the
`livespec-dev-tooling` pin and enforcement suite, **its own beads tenant** (Dolt
DB, SQL user, DB-scoped grant, a tenant password in the 1Password Environment,
`.beads/` pointers), its own CI and branch protection, and permanent
participation in every future cross-repo pin bump — standing overhead for ~1832
statements.

An earlier turn recommended "a standalone tool" WITHOUT pricing this, then
withdrew the recommendation once it was priced. Do not re-make that mistake:
whatever is chosen, price it first.

#### Adopter usability (the maintainer's last question) — YES, cleanly

Full requirement list for a third party: follow the `plan/<topic>/handoff.md`
convention, run Linux with tmux, use Claude Code and/or Codex, and supply a
watch-set (once `b1uo.3` exposes it). **No livespec install required at all** —
there are no core imports to satisfy. That is a materially larger addressable
audience than Phase 2's original "adopters with a fleet manifest" framing.

#### Skill-confusion risk (also asked) — judgment, not measurement

Mechanically there is no collision: a separate repo installs as its own plugin
under its own namespace, not `/livespec:*`. The residual risk is conceptual — a
user seeing a third livespec-ish plugin and not knowing which supplies what.
Mitigable by naming and docs, and meaningfully LESS confusing than today, where
the overseer is invisible to everyone but the maintainer.

### The three candidate homes (superseded framing — kept for the costs)

The reference Control-Plane implementation, `livespec-console-beads-fabro`, is a
**Rust** application carrying **zero** first-party Python (measured 2026-07-19:
0 `.py`, 30 `.rs`). The overseer is Python plus tmux, ~1832 statements across 8
modules. Candidate homes, none yet chosen:

1. A Control-Plane-owned **standalone Python tool**. The spec writes the
   Control-Plane reference as `livespec-console-*` — a wildcard — so more than
   one console realization is already contemplated.
2. A Python sidecar **inside** `livespec-console-beads-fabro`. Awkward, and it
   makes that repo bilingual, which has real conformance consequences: it is
   currently exempt from the Python check surface precisely BECAUSE it carries
   no Python.
3. **Reimplementation in Rust** inside the existing console. Highest cost, and
   it discards a folder that just earned 100% coverage, pyright strict, and ROP
   conformance — but it is the only option leaving ONE Control-Plane artifact
   rather than two. Do not dismiss it without argument.

**Still true regardless of home:** adding a ninth operation to core's
contract-fixed set of eight (`spec.md:233`, and `contracts.md:220` requires a
propose-change cycle even to RENAME one) would be a spec amendment. Under the
Control-Plane ruling that is probably moot — the overseer no longer joins that
set — but confirm rather than assume.

### ✅ THE 9th-FLEET-REPO PRICE WAS WRONG — re-measured 2026-07-20

§"What a 9th fleet repo actually costs (priced 2026-07-19)" above says a ninth
member "would need a new class and inherits: the `baseline` conformance
profile, the copier scaffold, the `livespec-dev-tooling` pin and enforcement
suite, **its own beads tenant**, its own CI and branch protection, and
**permanent participation in every future cross-repo pin bump**." **Four of
those clauses are false**, and they are exactly the clauses that made the
separate-repo option look expensive. Every correction below is
evidence-cited; the earlier text is kept above so the two can be compared.

| Clause in the 2026-07-19 price | Verdict | Evidence |
|---|---|---|
| "would need a NEW class" | **FALSE** | `REPO_CLASSES` already has six values including **`console`** (`livespec-dev-tooling/livespec_dev_tooling/fleet/_contract_rows.py:65`). D7 ruled the overseer Control Plane, so it fits `console` — no new class |
| "the copier scaffold" | **FALSE** | `_TEMPLATE_BORN_CLASSES = frozenset({"impl-plugin"})` (`_contract_rows.py:77`) — only impl-plugins owe a `copier-answers` row |
| "its own beads tenant" | **FALSE** | the beads row returns `RowSkip` when `.beads/config.yaml` is absent (`_rows_beads.py`) — it checks CONSISTENCY if a tenant exists, it does not REQUIRE one |
| "permanent participation in every future cross-repo pin bump" | **FALSE for `console`** | `_PIN_WEB_CLASSES = _ALL_CLASSES - {"console"}` (`_contract_rows.py:76`). `livespec-dev-tooling/SPECIFICATION/contracts.md:340` names the console the first *non-pin-consuming member*: it carries the dev-tooling pin for its own toolchain but never receives a bump-pin PR |

**What a `console`-class ninth member DOES owe** — the `_ALL_CLASSES` rows:
`workflow-ci`, `no-tracked-gitlinks`, `claude-plugin-currency`, `secret-names`,
`app-installation`, `branch-protection`, `merge-settings`,
`delete-branch-on-merge`, `topic-livespec-sibling`, `agent-ai-references-resolve`,
`baseline-harnesses`, plus `dev-tooling-pin`. Real, but far short of the
2026-07-19 framing.

**Also corrected: there is no class→profile lookup table.**
`non-functional-requirements.md:1053` asserts a member's profile "is DERIVED
from its `class`", but no code maps a class to a `PROFILE_LAYERS` value.
`PROFILE_LAYERS` (`fleet/contract.py:41`) is read ONLY to validate an
**adopter's** explicitly-declared `profile` array. The sole code realization of
"derivation" is the per-row `applies_to` class partition in
`_contract_rows.py:108-256`. So reasoning about a new member should enumerate
OBLIGATION ROWS, not profile names.

#### The `adopters` array is a third option the earlier framing missed

`fleet` and `adopters` are NOT two grades of the same membership — they are
read by different code. Measured: **`Manifest.adopters` is parsed and then
never read again anywhere in `livespec-dev-tooling`'s non-test code.**

| Reader | Reads `fleet` | Reads `adopters` |
|---|---|---|
| `fleet_conformance` (obligation rows) — `fleet/fleet_conformance.py:71-147` | yes | **no** |
| release / bump-pin fan-out — `livespec-dev-tooling/.github/workflows/reusable-release-dispatch.yml:127` (`jq` on `.fleet // .members`) | yes | **no** |
| Dispatcher sandbox sibling clones — `livespec-orchestrator-beads-fabro`'s `_dispatcher_sibling_clones.py:63-101` | yes | **no** (empty clone plan) |
| the overseer's own `registry.py:642-659` | yes | yes (flat, undifferentiated) |

Live corroboration that adopters really are unbound: `homelab` has **no
`.github/` directory at all** and `delete_branch_on_merge: false`, and none of
`openbrain`/`resume`/`homelab` carries the three pin-web shim workflows —
none of which trips anything, because `fleet_conformance` never walks them.
`non-functional-requirements.md:1057` states the exemption deliberately:
"Adopters are deliberately NOT bound: the `adopters` array is not consulted."

**So the membership question in §"The question that falls out" now has three
answers to choose between, not two** — `fleet` member (`console` class),
`adopters` entry, or unlisted. The trade is real and runs the other way from
the earlier framing: `fleet` costs the twelve `_ALL_CLASSES` rows but BUYS
mechanically-asserted CI/branch-protection/secret conformance and inclusion in
the maintainer-only fleet-dev attention sweep; `adopters` costs nothing and
buys nothing enforced. Given the overseer just earned 100% coverage, pyright
strict, and ROP conformance, the thing worth asking is which option KEEPS
those gates rather than which is cheapest.

### ✅ D9 RULED (maintainer 2026-07-20): separate repo, FLEET member, NEW class

**The ruling.** `livespec-b1uo.1` is settled: the overseer moves to its own
dedicated repo, registered in `.livespec-fleet-manifest.jsonc` under **`fleet`**
(not `adopters`, not unlisted), under a **NEW pin-consuming repo class**. It is
a full fleet member and follows the same development discipline as every other
member — worktree → PR → merge, `just check` as the gate, and factory-driven
changes through the Dispatcher.

**⚠️ This ruling CORRECTS the section immediately above, which is wrong in its
framing. Read this before acting on that table.** Two of its four "FALSE"
clauses are mechanically accurate but were presented as SAVINGS, and they are
not savings — they are exemptions the overseer should DECLINE:

| Clause | Mechanically | But for the overseer |
|---|---|---|
| "its own beads tenant" | correctly FALSE — the row `RowSkip`s when `.beads/config.yaml` is absent, checking CONSISTENCY not presence (`_rows_beads.py:62`) | **it needs one anyway.** A fleet member developed through the factory needs a tenant to hold its work-items: Dolt DB, SQL user + DB-scoped grant, tenant password in the 1Password Environment, committed `config.yaml` + gitignored `metadata.json`. "Nothing forces it" is not "it doesn't need one" |
| "permanent participation in every future cross-repo pin bump" | correctly FALSE **for the `console` class** | **it WANTS that participation.** The overseer's ruff / pyright-strict / coverage / ROP gates all come FROM `livespec-dev-tooling`, so a dev-tooling release directly determines whether its repo stays green — exactly the case auto-bump exists for |

**And the "NEW class" clause flips back to TRUE** — for a reason the
2026-07-19 pricing never stated. It is not that no class exists; it is that the
one Control-Plane class carries a pin-web exemption designed for a PURE-RUST
repo.

**Be precise about what the console exemption actually is** (this page
previously over-stated it as "not pinned"). Per `livespec-dev-tooling`'s
`SPECIFICATION/contracts.md` §"Bump-pin policy", a *non-pin-consuming member*
"carries a `livespec-dev-tooling` pin for its own developer toolchain … but
ships none of the three shims, is sent no bump-pin PR, and has its pin freshness
monitored centrally — at *warning* severity — by the `dev-tooling-pin` row's
staleness leg rather than auto-bumped." So the console IS pinned and IS
monitored; it just receives no automatic bump PR, because it is Rust and uses
dev-tooling for only three thin Python checks.

**Why `console` cannot simply be reused.** `_PIN_WEB_CLASSES` is defined by
SUBTRACTION — `_ALL_CLASSES - {"console"}` (`_contract_rows.py:76`). A
`console`-class repo therefore cannot join the auto-bump web without dragging
`livespec-console-beads-fabro` in with it, which would be wrong for the Rust
console. None of the five pin-consuming classes fits either: the overseer ships
an operator tool, not a `library`, and is neither a plugin nor the
`enforcement-suite`.

**The change is small, because the subtraction design does the right thing for
free.** Adding a name to `REPO_CLASSES` (`_contract_rows.py:65`) puts the new
class into BOTH `_PIN_WEB_CLASSES` and `_DEV_TOOLING_PIN_CLASSES`
automatically. The cost is that one entry plus the spec text describing the
class — not a rework of the partition.

**What the new repo then owes:** the twelve `_ALL_CLASSES` obligation rows
(`workflow-ci`, `no-tracked-gitlinks`, `claude-plugin-currency`, `secret-names`,
`app-installation`, `branch-protection`, `merge-settings`,
`delete-branch-on-merge`, `topic-livespec-sibling`,
`agent-ai-references-resolve`, `baseline-harnesses`,
`beads-tenant-connection-consistency`), PLUS the separately-scoped
`dev-tooling-pin` row, the three pin-web shim workflows, and its own beads
tenant.

**⚠️ An earlier version of this list was wrong twice** (caught by an independent
drift sweep 2026-07-20): it included `dev-tooling-pin` among the `_ALL_CLASSES`
rows — it is actually scoped to `_DEV_TOOLING_PIN_CLASSES`, which excludes
`enforcement-suite` — and it OMITTED `beads-tenant-connection-consistency`, a
genuine `_ALL_CLASSES` row that has existed since 2026-06-21 and so predates the
analysis rather than drifting into it. Re-derive this list from
`_contract_rows.py`'s `applies_to` fields rather than copying it. The `copier-answers`
row still does NOT apply — that binds `impl-plugin` only
(`_TEMPLATE_BORN_CLASSES`, `:77`), which is the one clause of the four that
stands unamended.

**Both names are now RULED** (maintainer 2026-07-20) — class
`control-plane-tool`, repo `livespec-overseer`. See §"START HERE" for the
choices, the alternatives they beat, and why the repo name deliberately carries
NO `-tmux` suffix. Adding the class value is still a `livespec-dev-tooling`
change with spec text, so it goes through that repo's propose-change →
independent Fable review → revise cycle; it is not a unilateral edit.

### Proposal FILED and REVIEWED — awaiting ratification (2026-07-20)

The spec half is filed as
`SPECIFICATION/proposed_changes/fleet-control-plane-tool-repo-class.md`
(livespec core). It has been through TWO independent Fable reviews: the first
returned BLOCKERS FOUND (1) — two unamended enumerations of the closed class set
— which was FIXED, not waived; the re-review of the amended text returned
**NO BLOCKERS** with four non-blocking concerns, all since folded in.
**Ratification (`/livespec:revise`) is the maintainer's gate and has NOT been
driven.**

**When you drive the accept, the payload MUST carry three `resulting_files[]`
entries**, and the two co-edits MUST be spelled spec-target-relative — a
project-root spelling joins to `SPECIFICATION/<path>` and fails the
require-existing-target check with exit 3:

- `non-functional-requirements.md` (the main target)
- `../.livespec-fleet-manifest.jsonc`
- `../.claude/skills/needs-attention-fleet/SKILL.md`

### ⏭️ Deferred follow-up — the Control-Plane gloss in `spec.md`

Recorded HERE deliberately: the proposal file becomes a frozen `history/` record
at ratification, so it must not carry the only copy of this.

`spec.md` still describes the Control Plane as "the operator console; reference:
`livespec-console-*`" and as "a **single operator interface**", and its Mermaid
subgraph labels read `CONTROL PLANE: operator console`. All of that reads as
console-only once `livespec-overseer` becomes a second, non-console
Control-Plane member. It is NOT a contradiction today (the new class is
unpopulated at ratification), which is why it was deliberately left out of the
class proposal rather than bundled into it.

**Fire this once `livespec-overseer` is registered**, as its own proposal, and
re-check `tests/test_workflow_planes_terminology.py` — it scopes to the planes
section and those Mermaid labels, so it is the mechanical gate on the change.

### ✅ `livespec-b1uo.2` — DONE and live-exercised (2026-07-20)

D4 is RULED (Linux + tmux is a declared requirement, host boundary deliberately
NOT abstracted), so this needs no further decision — only implementation. It was
scoped 2026-07-20 and stood down only for session budget, so do NOT re-derive:

- **Mirror the EXISTING startup-refusal pattern**, do not invent one.
  `Supervisor.unignored_tmp_repos` + its check at the top of
  `Supervisor.run` is the precedent: a predicate returning offenders, a
  `self._surface(...)` naming the actionable fix, then `return` — refusing to
  start rather than failing deep in a tick.
- **Check two things:** `/proc` is a directory (macOS does not have it AT ALL —
  `claude_sessions` reads `/proc/<pid>/stat`), and `tmux` resolves on PATH.
- **Both MUST be injectable seams** (`proc_root`, and a `which` callable
  defaulting to `shutil.which`), matching how every other host coupling in the
  dataclass is injected.
- **⚠️ The trap that makes this non-trivial:** the beside-tests' `_sup` factory
  MUST default those seams to a SUPPORTED-looking host. Without that, adding the
  gate to `run()` breaks every existing `run()` test on any runner lacking
  `tmux` — the same hermeticity rule the Codex seams already follow
  (`codex_pids_of_comm` defaults to an empty scan). Check the real `tmux` NAME,
  not an injected `tmux_bin`: the gate asks "is this host supported at all?",
  and the tests' fake tmux must not satisfy it.

**Landed as livespec PR [#1523](https://github.com/thewoolleyman/livespec/pull/1523)**
(`chore(overseer):`, merged 2026-07-20). `Supervisor.unsupported_host_reasons()`
+ a refusal at the top of `run()`, ordered BEFORE the gitignore gate. Full
`just check` green across all 71 targets; 445 beside-tests (439 + 6 new).

**Sabotage-verified**, per this folder's discipline: short-circuiting the
predicate to always report a supported host turned 5 of the 6 new tests red (the
sixth asserts the SUPPORTED path and correctly stayed green); restoring turned
them green. The probe was restored from a scratch copy, NOT `git checkout` —
which reverts to HEAD, not to your working state.

**Live-exercise evidence** (the bar is the SHIPPED behavior driven in its real
environment, not merged + CI-green). Both legs were driven against the merged
code on master, in-process, using the REAL default `which=shutil.which` seam
rather than an injected fake:

| Leg | How it was driven | Result |
|---|---|---|
| supported | the real Linux + tmux host | `unsupported_host_reasons() -> []` — no false refusal, so the daemon is not broken on the real fleet |
| refusal | `os.environ['PATH']` repointed at an empty temp dir — a genuinely tmux-less PATH | surfaced `refusing to start: unsupported host — tmux is not on PATH …`, and `ticks performed -> []` — it returned from `run()` before any tick |

The refusal leg is the one that matters: it proves the gate fires on the real
entry point and stops the loop, rather than merely returning a list a test
asserts on.

**⚠️ Self-caught over-claim, corrected same day.** This section first declared
b1uo.2 DONE on the strength of PR #1523 alone. That was WRONG: the item's
ledger ACCEPTANCE has THREE clauses, and #1523 satisfied only two — (1) refuses
and names the failed precondition, and (3) introduces no portability
abstraction. Clause (2), *"the requirement is stated in the shipped
documentation, not only in code"*, was UNMET; `SKILL.md` mentioned neither Linux
nor tmux anywhere. Closed by a follow-up adding a §"Requirements" section to
`SKILL.md`.

**The transferable lesson: read the work-item's own ACCEPTANCE clauses before
declaring completion, not just the plan text.** The handoff described b1uo.2 as
"declare + enforce the Linux/tmux precondition", which reads as satisfied by the
code gate alone; only the ledger item spelled out the documentation clause. A
green `just check` and live-exercise evidence cannot detect a missing doc
sentence, so nothing mechanical would ever have caught this.

### ⚠️ Why all five are in the LIVESPEC tenant — do NOT "fix" this

The epic spans three repos, so the instinct is per-tenant items linked by
cross-tenant `sibling_work_item` refs. **Do not.** Those refs resolve through
`.livespec.jsonc`'s `cross_repo_targets`, which is DUAL-PURPOSE: it is also the
input to `doctor-wiring-completeness-cross-repo`, which demands every listed
sibling wire all 54 canonical PYTHON check slugs. Registering a repo for a
PLANNING purpose silently enrols it in a CODE-CONFORMANCE check it may not
satisfy.

That exact mistake red-lined `check-doctor-static` on master for most of
2026-07-19 and blocked every local push in this repo while CI stayed green — see
§"Blocker post-mortem". **The defect is still open, but NO LONGER as
`livespec-fxxfq6`** — verified against the ledger 2026-07-20, that item is CLOSED
(regroomed out 2026-07-19) and was replaced by TWO successors: `livespec-2hya5g`
(split the dual-purpose registry + re-land the two reverted entries) and
`livespec-i6pyy6` (derive the CI sibling-clone list; depends on `2hya5g`). Track
those two. Verified
2026-07-19: `cross_repo_targets` registers only `livespec` and
`livespec-orchestrator-git-jsonl`; **neither Driver is listed, and neither should
be added for this epic.** Revisit only once `livespec-2hya5g` separates the
planning registry from the conformance registry — that is the successor now
carrying the work.

## Spun out — handoff-durability root-cause fix (maintainer-chosen 2026-07-19)

Prompted by this thread losing 153 unversioned lines: **why did nothing catch a dirty
handoff?** Root cause found, and it is a SCOPE GAP in an existing proven invariant, not
a missing concept.

`SPECIFICATION/contracts.md` §"master-direct-uncommitted-spec-edits" already mandates
that every worktree whose HEAD is the default branch MUST NOT carry uncommitted
modifications — enumerating worktrees, running `git status --porcelain`, firing `warn`
with corrective narration. It is scoped to `<spec-root>/` ONLY. Demonstrated live: in
this session's first `check-doctor-static` run it reported
*"no worktrees on master carry uncommitted spec-tree edits (1 worktree(s) scanned)"* —
`pass` — while that very worktree carried the dirty handoff. The guard ran and looked
straight past it.

`plan/` is already first-class to the check suite (`check-plan-thread-anchor-declared`,
`check-plan-thread-epic-parity` are canonical slugs), so widening scope is not a
boundary violation.

**Maintainer chose: extend the check AND add a SessionStart surface.** Two moments, two
mechanisms — the check makes it an enforced invariant in `just check`/CI; the hook
catches it at session start, the one moment the damage is still preventable. Neither
alone suffices: the check is `warn` and only fires when someone runs doctor, which no
one does at session start.

Sequencing constraints found while scoping it:

- The check is **spec-backed**, and `contracts.md:105` cites it BY NAME as the canonical
  example of the `warn` status. Extending the implementation past its contract would be
  exactly the drift livespec exists to catch, so it needs propose-change → independent
  Fable review → revise. **Blocked**: the spec lifecycle is frozen by the blocker above.
- Its name would then misdescribe it. Recommend renaming the slug (touches
  `contracts.md:105`, the `### ` heading at `:153`, the registry in
  `doctor/static/__init__.py`, the module filename, `check_id`, and tests) over keeping
  a stale name. Not yet decided.
- The **SessionStart hook half needs no spec change** — it is project-local config in
  `.claude/settings.json` — and is the part that can move first.

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
- **This handoff is an owned artifact, not a read-only inbox.** A session working this
  track updates it AS findings land and commits it — never accumulating them in
  conversation context to be written at session end (a session can die first; that is
  how 153 lines ended up unversioned on 2026-07-19). If a claim here is disproved,
  correct it in place and say so; a stale handoff actively misleads, and two of this
  document's own claims sent a later session down wrong paths before being caught.
  Doc-only commits are NOT gated by `check-doctor-static` — there is no blocker excuse
  for leaving it dirty.
- **Work-item IDs written here ROT, and in the opposite direction from everything
  else.** This page says "Status is READ from the ledger, never stored here" —
  correct, but it still STORES work-item *identifiers*, and an item can be
  regroomed out from under a citation. That happened: `livespec-fxxfq6` was cited
  in three places as "still open" while the ledger had CLOSED it on 2026-07-19 and
  split it into `livespec-2hya5g` + `livespec-i6pyy6`. **The ledger was more
  current than this page.** A file-and-line drift sweep cannot catch this class —
  every citation was internally consistent and pointed at a real id. Re-check any
  work-item id you are about to rely on with `bd show <id>` before acting on it,
  and prefer citing the id PLUS its one-line title, so a regroomed successor is
  recognizable when the id stops resolving to what you expected.
