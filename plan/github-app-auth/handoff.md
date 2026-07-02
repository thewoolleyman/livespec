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
    provider; retires the fleet-PAT export. DONE + HARD-REVIEWED: landed
    via that repo's PR #235 (+ follow-through PR #236, master `db856f9`);
    item CLOSED and `bd-ib-gsl` CLOSED with it (absorbed). The overseer
    approved the admission picker as the recorded judgment call. Overseer
    review verdict: **ACCEPT, all 6 acceptance criteria pass** — zero live
    PAT reads (static-guard-pinned), fail-closed exit-3 with a present PAT
    refused-not-used, per-subprocess re-mint (`GithubTokenEnvRunner`) with
    behavior-asserting tests, vendored `github_auth/` byte-identical to
    upstream v0.8.0, `just check` all 53 targets green, v022 spec revision
    accepted. LIVE-VALIDATED: console item
    `livespec-console-beads-fabro-idgql3` dispatched end-to-end — PR
    livespec-console-beads-fabro#79 created + auto-merge-armed by
    `app/livespec-pr-bot` and MERGED (sha `8fc8a71f759b`), the exact
    operation the PAT could never do; `idgql3` is parked in `acceptance`
    (console tenant, `ai-then-human`) awaiting maintainer confirmation.
    Review findings dispositions (all non-blocking): filed in the
    beads-fabro tenant — (1) tree-wide PAT-absence guard (current guard is
    per-file; stale `tier2-dispatch-proof.md` doc refresh rides along),
    (2) post-verdict fail-open stages ride ambient `GH_TOKEN` instead of
    the provider accessor (wrap with `GithubTokenEnvRunner`), (3) e2e
    golden-master now needs a GitHub App installation covering the
    `livespec-e2e` org (host-only tier), (4) three prose filing snippets
    still say `WorkItem(priority=...)` but the vendored v0.8.0 runtime is
    rank-based. By-design/no-action: `LIVESPEC_E2E_GITHUB_TOKEN` (separate
    org-scoped token for HOST-side e2e repo lifecycle) and the PEM in the
    fabro SERVER env (allowlist blocks sandbox propagation; contract
    honored). Read:
    `bd -C /data/projects/livespec-orchestrator-beads-fabro show livespec-in7snc`.
  - `livespec-orslcm` (core, Pillar 3) — WIRED 2026-07-02 (maintainer
    approved "wire it now"; overseer executed as the maintainer-proxy
    host session): all 8 fleet clones' repo-local git config now RESETS
    the credential-helper list and substitutes
    `~/.local/bin/livespec-agent-github-credential-helper` (a shim that
    execs the livespec-runtime v0.8.0 `livespec-github-credential-helper`
    under `/usr/local/bin/with-livespec-env.sh`) — worktrees inherit it;
    `git credential fill` in a fleet clone yields
    `username=x-access-token` + a `ghs_` token; human `gh` untouched;
    `~/.local/bin/livespec-agent-env.sh` + `~/.config/livespec-agent-gh/`
    (no auth) provide the agent-env launcher (no ambient
    GH_TOKEN/GITHUB_TOKEN existed to scrub). Close with the live
    worktree→PR push evidence (this handoff's own PR push rides the new
    helper).
  - `livespec-uotocj` (core) — App install scope VERIFIED restricted:
    the installation (App id 3668528) covers EXACTLY the 8
    fleet-manifest repos (listed via a minted installation token).
    Zero live PAT consumers fleet-wide (git grep all 8 repos: only
    planning docs + spec history; host sweep of /usr/local/bin,
    systemd, crontab: clean). Superseded `bd-ib-p2e` is CLOSED.
    REMAINING (maintainer-manual): remove `LIVESPEC_FAMILY_GITHUB_TOKEN`
    from the livespec 1Password Environment (op CLI here has only
    `environment read`) and REVOKE the fine-grained PAT at GitHub →
    Settings → Developer settings. On completion re-probe
    (`with-livespec-env.sh -- sh -c 'printenv LIVESPEC_FAMILY_GITHUB_TOKEN | wc -c'`
    → 0) and close the item.
  - **Fabro host token (maintainer directive 2026-07-02): RESOLVED.**
    Host fabro's vault (`~/.fabro/storage/vaults/default/secrets.json`)
    stored a 40-char `gho_` human OAuth as `GITHUB_TOKEN` with
    `[server.integrations.github] strategy = "token"`. Verified unused
    (workflows carry no `secrets.` refs; the container factory
    provisions its own App integration; C-mode overlay supplies per-run
    tokens), DELETED it (vault now empty), switched the host server to
    `strategy = "app"` + `app_id = "3668528"` with
    `GITHUB_APP_PRIVATE_KEY` in the server process env only (started
    under the wrapper; `env -i` does not survive fabro's daemon
    re-exec — the wrapper-env start is the working shape); `fabro
    doctor`: GitHub App configured. POST-DELETION SMOKE TEST GREEN:
    `bd-ib-3hgprw` dispatched through the HOST factory → PR
    livespec-orchestrator-beads-fabro#238 by `app/livespec-pr-bot`,
    auto-merged `fa190ab`, post-merge janitor green; item
    overseer-reviewed (diff = exactly the priority→rank prose fix) and
    CLOSED. (First dispatch attempt failed `not in the ready set` —
    the `ready` LABEL is bookkeeping; the Dispatcher keys off STATUS:
    `bd update <id> --status ready` first.)
  - `livespec-p3icf6` (openbrain adopter dogfood, Pillar 2; folds
    fleet-followups C16, gated on the D17 decision — D17 is recorded in
    the sibling thread's `plan/fleet-followups/handoff.md`, group D).
  - **Triple-check sweep (2026-07-02, post-everything): GREEN.**
    `just check`: core 58/58, runtime 47/47, beads-fabro 53/53; master
    CI green on core, runtime, beads-fabro, console. BOTH core and
    runtime had stale gitignored `mutants/` mutmut scratch tripping
    `doctor-no-spec-section-citation-in-code` — deleted (regenerable;
    evidence for the runtime-tenant doctor-static-gitignore item).
    Console `idgql3` CLOSED (accepted; PR #79 evidence). Beads-fabro
    follow-up filing ids: `bd-ib-ls32yb` (tree-wide PAT guard),
    `bd-ib-umno37` (post-verdict remint wrap), `bd-ib-3hgprw`
    (prose rank refresh — CLOSED via the smoke test), `bd-ib-w4iaaf`
    (e2e App installation for the livespec-e2e org, host-only tier).
- **Working model.** This is a **CORE coordination thread** — resume it from a
  core session. The code slices are **cross-tenant**: each is admitted + built
  from ITS OWN repo's tmux session (per the operating model above). Factory
  changes are careful **self-modifications** — human-approved admission
  (AskUserQuestion gate with recommendation), never auto-dispatch blind.
- **Core factory dispatch shape** (POST-in7snc, 2026-07-02): the PAT alias
  is RETIRED — the Dispatcher self-heals through the target's
  `credential_wrapper`, which injects `GITHUB_APP_ID` +
  `GITHUB_PRIVATE_KEY` (a set `LIVESPEC_FAMILY_GITHUB_TOKEN` is refused,
  never used). Only `fabro` (`~/.local/bin`) on PATH is still needed —
  `/usr/local/bin/with-livespec-env.sh -- sh -c 'export
  PATH="$HOME/.local/bin:$PATH"; exec python3
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

**Finish the wrap: three items stand between here and epic close +
archive** — statuses read live from the ledger:

1. **Close `livespec-orslcm`.** The wiring is done and validated (see
   its slice bullet); the merged PR that carried THIS handoff refresh
   was pushed from a worktree of the wired core clone through the
   App-token helper — cite that push (plus the `git credential fill`
   evidence) and `bd -C /data/projects/livespec close livespec-orslcm`
   with the evidence in the reason.
2. **Maintainer-manual, then close `livespec-uotocj`:** the maintainer
   removes `LIVESPEC_FAMILY_GITHUB_TOKEN` from the livespec 1Password
   Environment AND revokes the fine-grained PAT at GitHub (Settings →
   Developer settings → Fine-grained personal access tokens). Then
   re-probe (`/usr/local/bin/with-livespec-env.sh -- sh -c 'printenv
   LIVESPEC_FAMILY_GITHUB_TOKEN | wc -c'` → 0) and close the item with
   the full evidence chain (App scope = exactly the 8 fleet repos;
   zero live consumers; factory + fabro + host git all App-only).
3. **Maintainer gate: D17 → `livespec-p3icf6` disposition.** D17
   (register openbrain + dolt-server as adopters in
   `.livespec-fleet-manifest.jsonc`; recorded in
   `plan/fleet-followups/handoff.md`, group D) is a genuine fleet/core
   product decision. Present it; p3icf6 (openbrain via its OWN GitHub
   App with fleet secrets unreadable) either proceeds as the adopter
   dogfood or is re-scoped/deferred by the maintainer's answer — the
   epic close needs an explicit disposition either way (close-complete,
   or split p3icf6 out to its own thread with maintainer consent).
4. **Then close the epic + archive the thread** (plan operation Step 5):
   close `livespec-2ef0` via the ledger, then in a worktree
   `git mv plan/github-app-auth/ plan/archive/github-app-auth/` →
   PR → merge. The thread is DONE when the epic is closed and the
   directory is archived.

## Read-first chain (in order)

1. `research/01-design.md` — the why, the decision, the research basis, the four
   pillars + mechanics, and open questions. The only companion; everything else
   needed is in this handoff.

## Resume command

```
/livespec-orchestrator-beads-fabro:plan github-app-auth
```
