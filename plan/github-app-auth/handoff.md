# Handoff — github-app-auth

The single resumable entry point for the **fleet GitHub App-token auth**
coordination epic. A fresh session can execute the next action from this file
alone via the read-first chain — no chat history required.

## Track operating model (maintainer directive, 2026-07-02 — THIS track only)

Standing instructions for EVERY session resuming this thread; carry them
forward verbatim in every future handoff refresh.

- **Drive autonomously.** Sessions on this track drive end-to-end without
  waiting for prompts: execute the next action, then keep going (spec revise,
  delegation, monitoring, follow-ups) until the track is blocked on the
  maintainer or done. Reserve maintainer gates for genuine decisions
  (approvals, credential/host actions, destructive ops); present EVERY such
  gate as a structured multiple-choice question (Claude Code: the
  AskUserQuestion tool) with a clearly-recommended FIRST option — never a
  free-form prose question.
- **Delegate cross-repo work to per-repo tmux sessions.** Each target repo's
  work is driven in the tmux session NAMED AFTER THAT REPO (e.g.
  `livespec-runtime`, `livespec-orchestrator-beads-fabro`); the maintainer has
  these sessions open and monitors them. Do NOT hand-code sibling-repo slices
  inline in the core session — send the work to the repo's own session with a
  self-contained brief (forbid `--no-verify`; halt-and-report on hook
  failure; never touch another session's worktrees/branches).
- **Parallelize safely.** When slices are independent and non-conflicting
  (different repos, no unmet dependency edge, no overlapping files), drive
  them in parallel across their per-repo sessions; sequence only work joined
  by a dependency edge or overlapping files.
- **Model policy.** All sessions and sub-sessions on this track run **Claude
  Fable 5 at extra-high reasoning effort**. When starting a fresh Claude Code
  session for delegation, switch it FIRST (`/model` → Fable 5, xhigh effort)
  before driving any work.
- **Overseer-proxy: ALL gates surface in the core session** (added
  2026-07-02, Session 8). The core session is the OVERSEER and runs the
  delegated agents on the maintainer's behalf. When a delegated per-repo
  session pauses at a picker (admission, acceptance, anything), the overseer
  captures that pane, presents the gate HERE via AskUserQuestion, and
  delivers the answer back to the pane (`command tmux send-keys -t <session>
  <keys>` — verify the picker is still showing and which option is
  highlighted BEFORE sending). Never expect the maintainer to visit a
  delegated pane.
- **Maximal autonomy** (added 2026-07-02, Session 8). Do not stop to ask the
  maintainer unless the decision genuinely needs their input; self-resolve
  with best judgment and RECORD each judgment call in this handoff for
  review. At every accept/revise point, review the changes hard (read the
  merged diff, re-run the tests, check acceptance criteria) before
  accepting. Keep driving until the overseer session's context passes ~50%,
  then refresh this handoff and hand off to a fresh session. Implementation
  is always delegated (factory or per-repo session) — never hand-coded in
  the overseer.
- **Scope.** This operating model is TRACK-SCOPED to github-app-auth — a
  per-track maintainer directive, not a permanent or fleet-wide decision.

## For a fresh session — read first

- **What this is.** The coordination anchor for standardizing the fleet on
  GitHub **App installation tokens** for ALL automated GitHub operations —
  factory dispatch AND standalone agent worktree commits — **retiring the fleet
  PAT** (`LIVESPEC_FAMILY_GITHUB_TOKEN`) and **removing the human OAuth token
  from the agent path**. See `research/01-design.md` for the why + the four
  pillars.
- **Epic anchor:** `livespec-2ef0` (core tenant). Status is READ from the
  ledger, never from this file:
  ```bash
  /data/projects/1password-env-wrapper/with-livespec-env.sh -- bd -C /data/projects/livespec show livespec-2ef0
  ```
  Every `bd` command in this handoff runs under this same wrapper (the bare
  `bd ...` forms below omit it for brevity); `/usr/local/bin/with-livespec-env.sh`
  is the installed copy of the same wrapper.
- **Spec side: DONE (2026-07-02).** The proposed change
  `github-app-token-standardization` was ACCEPTED by `/livespec:revise` —
  history **v153** cut, PR #756 merged to master. The fleet
  automation-credential contract now lives at
  `SPECIFICATION/non-functional-requirements.md` §"Fleet secrets — 1Password
  Environment as canonical source" → the **GitHub automation credential.**
  block. The revise post-step `capture-impl-gaps --since-version v152`
  surfaced exactly one new rule, gap id **`gap-illb2rtn`** (the new block);
  it was deliberately NOT filed as a new gap-tied item because the epic's
  groomed slices below already carry that work — cite this gap id if a
  future pass asks.
- **Groomed slice ids (cite read-only; status lives in the ledger).**
  - `livespec-gwjnes` (core) — impl-plugin template `github-auth-guard` hook
    + core test. DONE: factory-built, PR #760 merged 2026-07-02T02:15Z;
    Session 8 verified the template hook + paired `github_auth_guard.py` +
    `tests/test_template_github_auth_guard.py` on `origin/master` and ran
    the test green there (15 passed); the maintainer ACCEPTED via the
    proxied acceptance gate and the item is CLOSED in the core ledger
    (epic 1/4). The acceptance also ratified the earlier judgment call
    (first dispatch HELD at admission on unset `admission_policy`; the core
    session added the `admission:auto` label and re-dispatched).
  - `livespec-u67wdb` (**livespec-runtime tenant**) — the App-token provider
    + git credential helper primitive (first-class remint; Pillar 1; the
    critical path). DONE + HARD-REVIEWED: livespec-runtime PR #107 merged
    2026-07-02T03:33Z, item CLOSED; released in **v0.8.0** (the overseer
    merged release-please PR #108 as a recorded judgment call — cutting the
    release is the documented steady-state and the pin chain needs it).
    Overseer review verdict: **ACCEPT, all 7 acceptance criteria pass** —
    the mid-sequence forced-expiry re-mint test is genuine behavioral
    verification (injected clock, real provider + mint railway, token
    VALUES asserted across a 130-min sequence), fail-closed is tested at
    config + helper boundaries and was exercised live under `env -i`, no
    fleet-fallback paths exist, the token never persists, CI green on the
    merge commit. Module: `livespec_runtime/github_auth/`
    (`InstallationTokenProvider`, console script
    `livespec-github-credential-helper`). Two recorded side dispositions:
    (a) the overseer deleted the stale gitignored `mutants/` mutmut scratch
    in `/data/projects/livespec-runtime` (it broke local `just check`
    there; regenerable tool scratch, dated 2026-05-30); (b) the runtime
    session was asked to file two follow-ups in ITS tenant — the
    urllib-vs-no-HTTP-client spec-tension propose-change (file only;
    revise is a later gate) and a work-item for doctor-static not honoring
    gitignore. The pre-existing `bd` auto-backup warning is
    correct-by-design (tenant-level DOLT_BACKUP denial; hourly systemd
    timer does real backups) — no item.
  - `livespec-in7snc` (**livespec-orchestrator-beads-fabro tenant**) —
    factory dispatch routes GitHub auth via target `credential_wrapper` →
    provider; retires the fleet-PAT export. Supersedes-edge to `bd-ib-gsl`
    (absorbed; close BOTH when this lands). Dependency `livespec-u67wdb`
    is now satisfied (v0.8.0). DELEGATED 2026-07-02: the overseer cleared
    the `livespec-orchestrator-beads-fabro` session, confirmed Fable 5
    xhigh, and sent it a self-contained brief (pinned verbatim at
    `research/in7snc-delegation-brief.md` for re-delegation); its admission
    picker is proxied to the overseer per the operating model (the overseer
    MAY approve it as a recorded judgment call — the slices were
    maintainer-groomed and the maintainer admitted the critical path).
    Read: `bd -C /data/projects/livespec-orchestrator-beads-fabro show livespec-in7snc`.
  - Epic children (core, maintainer-gated — deliberately NOT `ready` so the
    Dispatcher never drains them): `livespec-orslcm` (standalone
    agent-context wiring, Pillar 3), `livespec-uotocj` (retire the fleet PAT +
    restrict fleet App install scope; superseded `bd-ib-p2e` is CLOSED),
    `livespec-p3icf6` (openbrain adopter dogfood, Pillar 2; folds
    fleet-followups C16, gated on the D17 decision — D17 is recorded in
    the sibling thread's `plan/fleet-followups/handoff.md`, group D).
- **Working model.** This is a **CORE coordination thread** — resume it from a
  core session. The code slices are **cross-tenant**: each is admitted + built
  from ITS OWN repo's tmux session (per the operating model above). Factory
  changes are careful **self-modifications** — human-approved admission
  (AskUserQuestion gate with recommendation), never auto-dispatch blind.
- **Core factory dispatch shape** (until `livespec-in7snc` retires it): the
  Dispatcher process needs the fleet PAT aliased into `GH_TOKEN` under the
  wrapper AND `fabro` (`~/.local/bin`) on PATH —
  `/usr/local/bin/with-livespec-env.sh -- sh -c 'export
  PATH="$HOME/.local/bin:$PATH"; export
  GH_TOKEN="$LIVESPEC_FAMILY_GITHUB_TOKEN"; exec python3
  /data/projects/livespec-orchestrator-beads-fabro/.claude-plugin/scripts/bin/orchestrate.py
  run --repo /data/projects/livespec --action impl:<work-item-id> --json'`
  (a bare `orchestrate run` fails at `run-config-overlay`; without the PATH
  prepend the fabro launch dies and STRANDS the item in `active` — reset it
  with `bd update <work-item-id> --status ready` before re-dispatching). The
  Dispatcher journal is
  `/data/projects/livespec/tmp/fabro-dispatch-journal.jsonl` (JSONL, one
  stage record per line; read its tail for the last dispatch's stages).
- **⚑ Golden rule.** FILE + GROOM ripe work; DISPATCH ready, factory-safe slices
  through the factory under the janitor gate; NEVER hand-code inline. Every repo
  change is worktree→PR→merge, never `--no-verify`.
- **Resume command:** `/livespec-orchestrator-beads-fabro:plan github-app-auth`.

## The next action

**Shepherd `livespec-in7snc` to a reviewed close, then unblock the tail** —
statuses read live from the ledger, all gates proxied through the overseer
per the operating model:

1. **Monitor the `livespec-orchestrator-beads-fabro` session** until
   `livespec-in7snc` closes: watch the pane (`command tmux capture-pane -t
   livespec-orchestrator-beads-fabro -p`) and the ledger status. Proxy any
   picker it raises into the overseer; its ADMISSION picker may be approved
   by the overseer as a recorded judgment call (see the slice bullet).
   Route only genuine product/credential/destructive calls to the
   maintainer.
2. **On `livespec-in7snc` close: hard-review before treating it as
   accepted.** Review the merged PR against the item's acceptance criteria
   (NO dispatch path references `LIVESPEC_FAMILY_GITHUB_TOKEN`; the
   console's ready item `livespec-console-beads-fabro-idgql3` — console
   repo `/data/projects/livespec-console-beads-fabro`, same-named tmux
   session — dispatches end-to-end via App token; survives the ~76-minute
   merge-poll via re-mint; `just check` + `/livespec:doctor` green, run in
   the beads-fabro repo) and record the verdict here. Verify `bd-ib-gsl`
   was closed with it (absorbed).
3. **Shepherd the runtime session's two follow-up filings** (check its
   pane / that repo's `SPECIFICATION/proposed_changes/` + tenant): the
   urllib-vs-no-HTTP-client spec-tension propose-change (filed only — its
   revise/accept is a later gate, run from a livespec-runtime session) and
   the doctor-static-gitignore work-item.
4. **Then the remaining children in dependency order** (the provider is
   now available in v0.8.0): `livespec-orslcm` (Pillar 3, standalone
   agent-context wiring) then `livespec-uotocj` (retire the fleet PAT +
   restrict fleet App install scope — sequence it LAST among the code
   slices, after in7snc and orslcm stop consuming the PAT). Mark ready /
   delegate as recorded judgment calls. `livespec-p3icf6` stays gated on
   D17 (`plan/fleet-followups/handoff.md`, group D) — D17 (register
   openbrain + dolt-server as adopters in `.livespec-fleet-manifest.jsonc`)
   is a genuine fleet/core product decision: surface it to the maintainer
   when p3icf6 is otherwise ripe.

## Read-first chain (in order)

1. `research/01-design.md` — the why, the decision, the research basis, the four
   pillars + mechanics, and open questions. The only companion; everything else
   needed is in this handoff.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan github-app-auth
```
