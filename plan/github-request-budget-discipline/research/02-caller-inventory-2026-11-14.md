# 02 — Who spends the shared identity's REST budget: first inventory (2026-11-14)

Seat opened 2026-11-14 on hetzner-xubuntu at the throughput coordinator's direction
(track rank 10, livespec-dev-tooling `plan/throughput-track-organization/research/005`,
PR livespec-dev-tooling#4586). The plan anchor was completed to the existing epic
`livespec-httc` rather than filing a second epic; 005 names that epic as this plan's own.

## The coordinator's scope, verbatim

Scope: the shared GitHub identity's REST budget. On 2026-11-13 core read 0/5000 from 21:56Z to
22:30Z, held factory launches about 35 min, and refused commit gates on check-master-ci-green.
About 30 seats plus the launch preflight poll one identity unmetered. First: MEASURE who spends it
(per caller, per hour), then propose.

## The identity is NOT the App installation `livespec-j49m` measured

The exhausted identity is the `gh` CLI login `thewoolleyman`: a personal user token with its own
5,000-request-per-hour `core` bucket. `livespec-j49m` characterised the `livespec-pr-bot` App
installation (ID 131208965), which is a DIFFERENT bucket. That item's per-command bucket table (for example,
`gh pr view --json` spends GraphQL, not `core`) still holds. Its measurement target does not: a
sampler run under an installation token would not have seen this incident at all.

## Measurement status

Everything below is a static inventory plus a look-back on ONE host. It is not yet the per-caller,
per-hour account the plan's Definition of Done requires. Nothing in the fleet records per-caller
spend: the budgeted client's per-call log is written only when the response carries rate-limit
headers, and plain `gh api` hides them.

Scratch-script references in the original agent output have been removed; the method is described
in prose.

---

# Who spends the shared `thewoolleyman` REST `core` budget — caller inventory

Scope: read-only research on hetzner-xubuntu, 2026-11-14 ~00:00Z. Incident: `core` read 0/5000 from
21:56Z to 22:30Z (reset 22:30:43Z) on 2026-11-13. "Measured" means it was counted from a log or transcript
on this host. "Estimated" means it was derived from code and an assumed duty cycle.

## 0. Bottom line

1. **This host was NOT the drain. (Measured.)** In the window 20:00–23:00Z, every Claude Code session on
   hetzner-xubuntu together issued about **60 direct REST calls**, plus about **20–40 more through the
   commit and push gates**, for roughly **100–150 in 3 hours (about 1% of the hourly budget)**. There
   were zero `gh run watch`, zero `gh pr checks --watch`, and zero sleep-poll loops calling `gh`. No
   Codex activity on this host fell inside the window.
2. **A live reading confirms the spend is elsewhere. (Measured.)** At 00:00:47Z on 2026-11-14,
   `gh api rate_limit` showed core `used=1057` in a window that resets at 00:31:02Z. That is about 1,057
   calls in about 30 minutes (roughly 2,100 per hour). This session was the only GitHub-active thing on
   this host at the time. So over 95% of the current spend comes from other hosts, daemons or sandboxes.
3. **Top suspects, ranked by REST requests per hour (estimated from code, not measured):**

| Rank | Caller | Per instance | Fleet-wide guess | Bucket and credential |
|---|---|---|---|---|
| 1 | Agent-seat CI watchers on other hosts: `gh run watch` (default 3 s) | ~1,200/h (≥2 calls per poll: run plus jobs) | 3 at once already empties 5,000/h | REST, user's `gh` login |
| 1b | The sanctioned `gh run watch --interval 30` (see `.ai/factory-dispatch-preflight-and-triage.md` in livespec-orchestrator-beads-fabro) | ~120–240/h | 20 seats → 2,400–4,800/h | REST, user's `gh` login |
| 2 | `gh pr checks --watch` (10 s) | ~360/h | — | The brief counts it as REST; gh's `pr checks` may read the `statusCheckRollup` through GraphQL, which would make it GraphQL. Unverified. User's login. |
| 3 | Factory launcher master-CI preflight (`_dispatcher_ci_preflight_wait.py`): 60 s poll, 30 min bound, each round 2–6 REST | 120–360/h for each dispatch waiting on a pending master | Scales with how many launches are waiting at once | REST, host `gh` (the user's login; see §1.2) |
| 4 | Commit and push gates: `check-master-ci-green` (2 REST per run) plus `check-branch-protection-alignment` on push (~4–6 REST) | 2–8 per commit or push | ~30 seats × a few gates/h ≈ 100–500/h | REST, user's `gh` login |
| 5 | Overseer `drain-backlog/engine-on-green.sh` gate 2: `gh api --cache 60s` plus `sleep 60` | ~60/h while waiting | 1 per detached launcher | REST, user's `gh` login |

The ranking is a hypothesis. Only one source on this host could have attributed spend per caller: the
budgeted client's durable JSONL file. **That file does not exist here** (see §1.5).

## 1. Static inventory (first-party, non-test code)

### 1.1 `livespec-dev-tooling/livespec_dev_tooling/checks/master_ci_green.py` (just check `check-master-ci-green`)
- **Calls per invocation: 2 REST**, both `gh api` GETs:
  1. `repos/{o}/{r}/commits/master/check-runs?check_name=ci-green`
  2. `repos/{o}/{r}/actions/runs?branch=master&event=push&head_sha=<sha>` (from `_fetch_master_push_suite_ids`)
- Each call is retried up to 2 more times on HTTP 429 or 5xx (`_read_check_runs_with_transient_retry`), so the worst case is 6.
- `gh auth token` is local and makes no network call. The result is not cached: `budgeted_gh.gh_read`
  builds a NEW `GithubBudgetedClient` on every call, and that client's ETag cache is an in-memory dict.
  The conditional (304) path therefore never hits across invocations, or even between the two calls.
- **Trigger and frequency:** it is a member of the `just check` aggregate in every fleet repo (livespec
  `justfile:230`, dev-tooling `justfile:299`). It runs:
  - on every full pre-commit (non-Red, non-doc-only);
  - on every pre-push, including the token-match path, where world-reading members still run
    (`scripts/just/check-pre-push.sh` ~L125–150);
  - on the delegated k3s gate Job;
  - in CI.
- **Credential:** depends on where it runs.
  - Host hooks use the user's `gh` login.
  - The delegated k3s gate pod uses `GH_TOKEN` from the `gate-forge-token` Secret. That token is a
    **fine-grained PAT** (`ci-runner/k3s/secret-reinjection/seed-gate-forge-cred.sh`). A fine-grained PAT
    counts against its owning user's 5,000/h, so if it was minted by thewoolleyman it shares the same bucket.
  - CI uses `github.token`, which has its own per-repo bucket (`reusable-check-matrix.yml:132,156`).
- **Measured (this host):** gate run `livespec-dev-tooling/tmp/gate-runs/20261113T220107Z-463291` (venue
  `host_local`) hit `check-master-ci-green [FAILED] … gh: API rate limit exceeded for user ID 158 …
  2026-11-13 22:02:36 UTC`. This is direct evidence that host gates run on the exhausted identity.
- **Gates run on this host:** 12 commit or push gates in the window, all under dev-tooling `tmp/gate-runs`.
  4 of them were pushes, and each push takes 10–36 min of wall time.
- **Companion check:** `check-branch-protection-alignment` (`_branch_protection_api.py`,
  `_branch_protection_rulesets.py`) makes ~4–6 REST calls: `repos/X`, `required_status_checks`,
  `enforce_admins`, `rules` (paginated), and one per ruleset. Delegated Jobs skip it, and it runs on the
  pushing host instead, using the user's login.

### 1.2 Factory launcher preflight — livespec-orchestrator-beads-fabro
- Files: `commands/_dispatcher_ci_preflight.py`, `_dispatcher_ci_preflight_wait.py`, and
  `_dispatcher_ci_preflight_lookups.py`. The entry point is `_dispatcher_step_gate.py` →
  `master_ci_preflight`, which runs once per dispatch, in the dispatch preamble.
- **Calls:**
  - `gh run list --branch master --limit 1 --workflow <wf> --json …`. **This is REST** (`actions/runs`)
    even though it uses `--json`. The `--workflow` name resolution likely adds another workflows GET.
  - While the latest run is pending: `gh run list --limit 100`, which is REST.
  - `gh api repos/{o}/{r}/compare/<sha>...master`, which is REST.
  - `gh run view <id> --json jobs`, which is REST (run plus jobs).
  - So each round costs about 2–6 REST.
- **Poll:** `POLL_INTERVAL_SECONDS = 60`, `WAIT_BOUND_SECONDS = 1800`. That is up to 30 rounds per
  dispatch, roughly 60–180 REST per waiting dispatch, or **120–360/h for each concurrently-waiting launch**.
  There is no rate_limit or 403 handling in the preflight modules (grep for `rate_limit|403` found
  nothing). A 403 is classified as an unprovable failure, so the launch refuses. That matches
  "launches gokm2v, k3ij72 bounced at master-CI preflight (rc=1, HTTP 403)", recorded in a
  dev-tooling session's notes.
- **Credential:** the host `gh`, which means the user's login.
  - Caveat: `_dispatcher_credentials.materialize_overlay` later sets the in-process `GH_TOKEN` to a
    **GitHub App installation token** (comment: "Refresh the ambient GH_TOKEN so the host-side `gh api`…").
    Host `gh` calls made after the overlay in the same process (fleet-manifest fetch, merge polling,
    reconciliation) therefore run on the App's bucket.
  - The preflight is in the preamble, so it most likely runs before that switch and on the user's login.
    The ordering was not traced end to end.
- **Other dispatcher forge reads:** about 40 modules each make one-shot calls per dispatch, such as
  `pr view --json` (GraphQL), `gh api` (REST), and `pr merge` / `update-branch`. The merge poll
  (`_dispatcher_engine_merge.py`) uses `gh pr view --json … statusCheckRollup`, which is GraphQL.
- `bd-ib-zdqshg` (the launcher back-off item) has no code reference in the repo yet. The same session's
  notes say a back-off item was "being filed under bd-ib-ynnykl".

### 1.3 livespec-overseer
- **overseerd:** its only forge read is `_supervisor_wait_target_forge.py`, which calls
  `gh pr list --state all --head <b> --json …`. That is **GraphQL**, with a 5 s timeout, on the user's
  login, and it runs once per wait-target verification. There is no REST loop.
- **`.claude-plugin/scripts/drain-backlog/engine-on-green.sh`:**
  - Gate 1 is a credential probe every 300 s with no GitHub call.
  - Gate 2 loops `gh api --cache 60s repos/$r/actions/workflows/ci.yml/runs?branch=master&per_page=1`
    plus `sleep 60` until master completes.
  - `--cache` is a local TTL cache, not a conditional request (believed; not verified against gh
    source). With TTL equal to the sleep, it is about **60 REST/h for each waiting launcher**, on the
    user's login.
  - It is exempt from the guard because the guard treats `--cache` as the sanctioned form.
- **`drain-backlog/tick.py`:** `gh pr list --json` every 60 s, which is GraphQL (~60/h).
- **`homelab_charter_scan.py`:** one-shot `gh repo view` (GraphQL) plus a recursive `gh api git/trees` (REST).
- No overseer or livespec systemd timer on this host calls `gh`. The only active one is
  `hxi-host-health` at 1 min, and it has no `gh`.

### 1.4 `livespec-driver-claude/.claude-plugin/hooks/github_rate_limit_guard.py`
- This is a PreToolUse hook on the **Bash tool only**. It denies a `gh run`, `gh pr` or uncached
  `gh api` read when ANY of these holds:
  - it is inside `while`, `until` or `select`;
  - it is inside a `for` that is not a literal list of 10 or fewer items;
  - a `sleep` appears inside a loop body.
- It also denies loops or `xargs` that contain a mutating `gh api`.
- **It allows:**
  - a single `gh run watch` at any interval, including the 3 s default (about 1,200/h);
  - `gh pr checks --watch`;
  - any loop over `gh api --cache …` (exempt even when unbounded);
  - one-off `sleep N; gh …`;
  - `gh` reached through a script, a `python3 -c`, or a `just` recipe;
  - calls from the Monitor tool, which is not matched by the `Bash` hook.
- `livespec-driver-claude-32a`: the guard looks for `sleep` in loop **bodies**. A loop whose sleep
  sits in the condition, or comes before the body (for example `while sleep 30; do gh …; done`), can
  escape it. It does nothing about in-process pollers (`gh run watch`), which are the shapes that drain
  the budget fastest.
- No hook in the Driver itself calls GitHub.

### 1.5 livespec-runtime `GithubBudgetedClient`
- Users: `livespec_runtime/cross_repo/providers/github*.py`, `hygiene_scan_context.py`, dev-tooling
  `budgeted_gh.py` (and through it `master_ci_green`, branch-protection, the fleet modules and incident
  readers), and `incident_recovery_app.py`.
- **The durable per-call signal is effectively off.**
  - The client writes `tmp/github-rate-limit.jsonl`, relative to the cwd, or the path in
    `$LIVESPEC_GITHUB_BUDGET_LOG`, which is unset here.
  - It writes only when the response carried `x-ratelimit-*` headers, and plain `gh api` without
    `--include` does not surface them.
  - Searching every filesystem on this host (`find / -xdev`) found no such file.
- This is why per-caller attribution is impossible today.

### 1.6 Other repeated callers (lower or unconfirmed)
- livespec doctor `wiring_completeness_cross_repo` / `_wiring_completeness_resolve.py`: one
  `gh api contents/justfile` per sibling, but only when no local clone exists. REST, user's login,
  once per doctor run.
- dev-tooling `fleet/*` reconcilers, the `reusable-*` workflows and `github-rate-budget-token`: these
  run in Actions on App or `github.token` credentials, so they are **not** on the user's bucket.
- livespec `.claude/skills/needs-attention-internal/fleet-runner-inventory.py` and
  `docs/activity/update-activity.sh`: run on demand on the user's login. Not loops.

## 2. Look-back from transcripts on hetzner-xubuntu (2026-11-13 20:00–23:00Z)

  (outputs `lookback.out` and `lookback_v.out` in the same dir).
- Coverage: 22 transcript files, which hold 320 Bash calls in the window, from 6 active sessions or
  subagents. `~/.codex/sessions` is absent, and `~/.codex/logs_2.sqlite` has no rows in the window.
- The script's automatic watcher hits were all **false positives**. The strings "gh run watch" and
  "pr checks --watch" appeared inside heredoc notes and regexes that sessions were writing, not in
  commands they ran. After hand review: **0 watchers and 0 sleep-poll loops** were executed.

Direct REST calls, counted per command and checked by hand:

| Hour (UTC) | Session (project/uuid) | Direct REST | Shapes |
|---|---|---|---|
| 20Z | orchestrator 018c4d6d | ~10 | `gh run list` / `gh run view` (REST despite `--json`) |
| 20Z | dev-tooling c301216a | ~35–45 | `gh api` org, user and package reads; 2 bounded `for r in <~9 repos>` loops of `gh api` |
| 21Z | orchestrator 04500363 | ~10 | `gh run list` / `gh run view` |
| 21Z | dev-tooling 62dc7a17 | ~3 | `gh pr checks` ×3 (bucket uncertain); the rest is `pr view` / `pr list --json` (GraphQL, 12 calls) |
| 22Z | dev-tooling 3d96df40 and subagent | ~2 | 2× `gh api rate_limit` (free), 1 `gh api graphql`, 1 `run view` |
| 22Z | dev-tooling 62dc7a17 | ~2 | `pr create`, `pr merge`, `pr checks` |

Gate-driven REST (estimated from the 12 gate runs in `livespec-dev-tooling/tmp/gate-runs/20261113T2*`):
- about 8 full-check commits × 2, plus 4 pushes × (2 + ~5), comes to **~40 REST**;
- 1 measured 403, at 22:02:36Z;
- by hour: 20Z ≈ 0, 21Z ≈ 15, 22Z ≈ 25.

**Host total: about 100–150 REST over 3 hours (about 35–50/h), roughly 1% of 5,000/h. (Measured,
with estimated gate counts.)**

## 3. What this look-back cannot see

- **Other hosts' seats.** The notes record "~30 seats on one identity running gh run watch / gh pr
  checks --watch", on gmktec, the gaming PC, other VPSes, and any Codex or pi seats there. All use the
  user's `gh` login (`gh auth` token, `gho_`). Their transcripts are on those hosts.
- **Factory launches and preflight on the launcher host,** which is likely not this one ("hold-gmktec").
  The preflight uses the host `gh` user login. Its journals are on that host.
- **Fabro sandboxes.** They receive a GitHub App installation token in `GITHUB_TOKEN`
  (`_dispatcher_credentials.py`), which is a separate bucket. Not on the user's 5,000, unless a
  sandbox is handed `gh` login state.
- **The k3s delegated gate Jobs.** They use the `gate-forge-token` fine-grained PAT. If it is owned by
  thewoolleyman, it **shares the user bucket**. Pod logs are not on this host.
- **Detached daemons** (overseerd, drain `engine-on-green.sh`, dispatcher `loop`) on any host. They
  write no transcript. They use the user's login, except dispatcher calls made after the App-token overlay.
- **GitHub Actions.** They use `github.token` or App tokens, which are separate buckets and irrelevant here.
- **Commands run through scripts, `just` recipes and Python.** Transcripts show only the outer command,
  so their internal REST counts are estimated from code.
- **No per-call ground truth anywhere.** The `x-ratelimit` JSONL signal is never written (§1.5).

## 4. Measurement gaps worth closing (for whoever owns the plan)
- Make the budget JSONL actually record: use `gh api --include`, or read the `X-RateLimit-Used` delta
  around each call, write to a fixed absolute path, and tag the caller.
- Sample `gh api rate_limit` (free) once a minute on every host. Then the per-host delta in `used` gives
  per-host attribution, even though GitHub itself does not attribute spend.
