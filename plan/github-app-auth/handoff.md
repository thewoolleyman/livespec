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
    + core test. FACTORY-BUILT AND MERGED: PR #760 landed on master
    2026-07-02T02:15Z; Session 8 verified the template hook + paired
    `github_auth_guard.py` + `tests/test_template_github_auth_guard.py` on
    `origin/master` and ran the test green there (15 passed). The item is
    PARKED in `acceptance` (`ai-then-human` default) awaiting the
    maintainer's confirmation; the acceptance gate was presented Session 8
    (maintainer away — still open). Note for the maintainer: the dispatch
    itself involved a judgment call to review — the first dispatch HELD at
    admission (unset `admission_policy` → safe-default `manual`), and the
    core session added the `admission:auto` label and re-dispatched under
    this handoff's pre-authorization while the maintainer was away.
  - `livespec-u67wdb` (**livespec-runtime tenant**) — the App-token provider
    + git credential helper primitive (first-class remint; Pillar 1; the
    critical path). DELEGATED 2026-07-02 to the `livespec-runtime` tmux
    session; that session read the brief and is PAUSED at its human
    admission gate (AskUserQuestion: "Admit and start now?") awaiting the
    maintainer IN THAT PANE — the item deliberately stays `backlog` until
    admitted (`command tmux capture-pane -t livespec-runtime -p` to check;
    plain `tmux` may be shadowed by a zsh plugin shim in non-interactive
    shells — prefix with `command`). Read:
    `bd -C /data/projects/livespec-runtime show livespec-u67wdb`.
  - `livespec-in7snc` (**livespec-orchestrator-beads-fabro tenant**) —
    factory dispatch routes GitHub auth via target `credential_wrapper` →
    provider; retires the fleet-PAT export. Supersedes-edge to `bd-ib-gsl`
    (absorbed; closes when this lands). Blocked by `livespec-u67wdb` (sibling
    dep). Read: `bd -C /data/projects/livespec-orchestrator-beads-fabro show livespec-in7snc`.
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

**The track is blocked on two open maintainer gates; clear them, then unblock
the chain** — statuses read live from the ledger:

1. **Maintainer gate (critical path): `livespec-u67wdb` admission.** The
   `livespec-runtime` tmux session is paused at its AskUserQuestion admission
   gate ("Admit and start now?" — recommended). The maintainer answers IN THAT
   PANE; on admission that session drives the slice end-to-end (TDD, worktree
   → PR → merge, close). A resuming core session verifies the pane is still
   at the gate (`command tmux capture-pane -t livespec-runtime -p`) and
   re-surfaces this to the maintainer if stalled; do NOT self-approve — the
   item is explicitly human-admitted.
2. **Maintainer gate: `livespec-gwjnes` acceptance.** Merged and verified
   (see the slice bullet above); present/re-present the acceptance gate via
   AskUserQuestion (recommend: accept and close). On acceptance, close the
   item in the core ledger: `bd -C /data/projects/livespec close
   livespec-gwjnes` (under the wrapper).
3. When `livespec-u67wdb` CLOSES: delegate `livespec-in7snc` to the
   `livespec-orchestrator-beads-fabro` tmux session with a self-contained
   brief (same discipline block as the operating model; the item description
   is authoritative — read it from that repo's tenant first).
4. Then present the maintainer-gated children (`livespec-orslcm`,
   `livespec-uotocj`, `livespec-p3icf6`) one at a time via AskUserQuestion
   gates, in dependency order (orslcm and uotocj need the provider;
   p3icf6 needs D17).

## Read-first chain (in order)

1. `research/01-design.md` — the why, the decision, the research basis, the four
   pillars + mechanics, and open questions. The only companion; everything else
   needed is in this handoff.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan github-app-auth
```
