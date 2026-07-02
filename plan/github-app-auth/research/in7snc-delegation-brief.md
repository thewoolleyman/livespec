# Delegation brief — livespec-in7snc (livespec-orchestrator-beads-fabro)

FIRST: switch this session's model if not already set (`/model` → Claude Fable 5,
xhigh reasoning effort) — track policy for github-app-auth.

WORK ITEM: `livespec-in7snc` in YOUR repo's beads tenant. The item description is
AUTHORITATIVE — read it first:
`/data/projects/1password-env-wrapper/with-livespec-env.sh -- bd -C /data/projects/livespec-orchestrator-beads-fabro show livespec-in7snc`

SUMMARY: Route ALL factory GitHub auth through the dispatch TARGET's own
`credential_wrapper` to the GitHub App installation-token provider (the
livespec-runtime primitive built by sibling item livespec-u67wdb — NOW MERGED;
see pointer below). Rework `orchestrator-image/real-work-dispatch.sh` (the :224
hard-require of LIVESPEC_FAMILY_GITHUB_TOKEN, :291 container forward, :473
hardcoded `export GH_TOKEN=...`), `orchestrator-entrypoint.sh` `provision_github`
(~line 102), and every other dispatch path so NO path exports the fleet PAT;
preflight works without the fleet secret; FAIL-CLOSED when the target repo has no
`credential_wrapper` (no silent fleet fallback). Update the v021 self-containment
contract + adopter docs in this repo's spec surface accordingly.

PROVIDER PRIMITIVE (dependency, merged + hard-reviewed ACCEPT by the overseer):
livespec-runtime PR #107, released in **v0.8.0**. Module
`livespec_runtime/github_auth/` — `config.py` (fail-closed env boundary:
GITHUB_APP_ID + GITHUB_PRIVATE_KEY, optional GITHUB_APP_INSTALLATION_ID /
GITHUB_API_URL, injected ONLY by the tenant's credential_wrapper),
`provider.py` (`InstallationTokenProvider`: process-memory cache, 55-min
horizon, transparent pre-expiry re-mint — survives >1h runs), and the git
credential helper console script `livespec-github-credential-helper`
(get answers username=x-access-token + minted token; store/erase no-ops).
Bump this repo's livespec-runtime pin to v0.8.0 as part of the slice if the
bump-pin fan-out has not already done it.

DESIGN RECORD: `plan/github-app-auth/research/01-design.md` in the livespec CORE
repo (`/data/projects/livespec`) — Pillars 1+2 apply. Epic: `livespec-2ef0`
(core tenant).

ACCEPTANCE (from the item): no dispatch path references
LIVESPEC_FAMILY_GITHUB_TOKEN; dispatching the console's ready item
`livespec-console-beads-fabro-idgql3` succeeds end-to-end via App token (first
real validation); survives the ~76-minute merge-poll (re-mint, NOT a
once-at-start export); `just check` + `/livespec:doctor` green.

ON LANDING: this item ABSORBS `bd-ib-gsl` (supersedes edge) — close BOTH
`livespec-in7snc` and `bd-ib-gsl` when the PR merges.

ADMISSION: careful SELF-MODIFICATION — present your admission picker as usual;
the core overseer session proxies it to the maintainer and delivers the answer
to this pane. Do NOT auto-dispatch blind.

DISCIPLINE (non-negotiable): all edits in a dedicated worktree from YOUR repo's
master → PR → merge; follow YOUR repo's own commit/TDD conventions and hooks;
always `mise exec -- git ...` for commit/push; NEVER pass `--no-verify` — on ANY
hook failure HALT and report; never touch worktrees/branches another session
created; secrets are probe-only (`printenv NAME | wc -c`, never echo values).

ON COMPLETION: after the PR merges — refresh your primary checkout, remove the
worktree, delete the branch, close `livespec-in7snc` + `bd-ib-gsl` in beads, and
report. The core github-app-auth overseer reads status from the ledger.
