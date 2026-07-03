# Design — github-app-auth

The design record for the **fleet GitHub App-token auth** track: why the
current credential model is wrong for automation, the decision to standardize
on GitHub App installation tokens, the research basis, and the four pillars +
mechanics the groom cuts into dependency-layered slices.

## Why — the problem

The fleet's GitHub credential model is fragmented across three identities, none
right for automation:

- **Factory dispatch** (Fabro sandbox creating PRs): projects a fleet
  fine-grained PAT `LIVESPEC_FAMILY_GITHUB_TOKEN` as `GH_TOKEN`.
  `orchestrator-image/real-work-dispatch.sh:224` hard-requires it, `:291`
  forwards it into the container, `:473` hardcodes
  `export GH_TOKEN="$LIVESPEC_FAMILY_GITHUB_TOKEN"`. The entrypoint
  (`orchestrator-image/orchestrator-entrypoint.sh` ~line 102, `provision_github`)
  ALREADY mints an App installation token (preferred) with PAT fallback via
  `.claude-plugin/scripts/bin/mint_app_token.py` — but `real-work-dispatch.sh`
  bypasses it. The PAT lacks `Pull requests: write` on some family repos (the
  console repo → "GraphQL: Resource not accessible by personal access token").
  It also can't preflight without the fleet secret (external adopters blocked)
  and would create adopter PRs with fleet creds.
- **Standalone / non-factory commits** (interactive agent sessions doing
  worktree→PR, e.g. plan-doc PRs): authenticate as the HUMAN maintainer —
  `gh auth` logged in as `thewoolleyman`, a long-lived `gho_` OAuth token
  (scopes `repo`, `workflow`, `read:org`, `gist`) via git credential helper
  `!/usr/bin/gh auth git-credential`. Broad, human-tied, account-wide — reaches
  every repo the account owns (including adopters). For isolation this is
  *worse* than the factory PAT.
- **CI**: the Actions `GITHUB_TOKEN` (separate concern; fine).

## Decision

Standardize the fleet on GitHub **App installation tokens** for ALL automated
GitHub operations — factory dispatch AND standalone agent commits. **Retire the
fleet PAT** (`LIVESPEC_FAMILY_GITHUB_TOKEN`) and **remove the human OAuth token
from the agent path**.

## Research basis (verified against primary GitHub documentation)

- App installation tokens are GitHub's recommended automation credential —
  *"Authenticating as an app installation is ideal for automation workflows that
  don't involve user input"*; *"for long-lived integrations, you should use a
  GitHub App."*
  ([about authentication with a GitHub App](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/about-authentication-with-a-github-app))
- Short-lived (~1 hour, revocable on demand).
  ([authenticating as a GitHub App installation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation))
- Least-privilege is structural: a token can't exceed the App's grants, can't
  reach un-granted repos, and can be scoped DOWN per mint.
  ([generating an installation access token for a GitHub App](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app))
- App-identity attribution (a `[bot]`, not human impersonation; commit
  attribution requires setting the bot noreply author email).
- Mint = sign a JWT (RS256) with the App private key →
  `POST /app/installations/{id}/access_tokens` → use the token as the git HTTP
  password. The durable secret is the App private key PEM; the token is
  ephemeral (mint on demand, never persist).
- **Honest caveats:** the steelman for keeping a PAT is operational only (no
  security case); multi-tenant "bring your own credential" is a design decision
  (no canonical GitHub guidance); some supporting claims were unverified due to
  GitHub-side rate-limiting (not refuted); note the April 2026 stateless
  `ghs_APPID_JWT` token format and the Feb 2024 scoped-token-limits changelog.

## Pillar 1 — first-class remint (HARD requirement)

Token acquisition MUST be a mint-or-refresh capability callable **at any time by
any factory machine/process**, transparent — NEVER a once-at-start
`export GH_TOKEN=...` that assumes the run finishes within an hour. Shape:

- (a) a **git credential helper** that mints/refreshes an installation token on
  demand (transparent to `git` clone/push, any duration);
- (b) a **token provider** for `gh`/REST/GraphQL that caches (~55 min) and
  refreshes before expiry; each machine holds the PEM via its own
  `credential_wrapper` (mints locally) or calls a broker.

It MUST survive the ~76-min merge-poll (`bd-ib-asp`) and any >1-hour operation.

**Hard acceptance criterion: "survives a >1-hour run / re-mints transparently."
Do not assume anything finishes in an hour.**

## Pillar 2 — tenant-scoped resolution + adopter isolation ("fleet = adopter #0")

The credential is resolved ONLY through the dispatch/worktree TARGET's own
`credential_wrapper`: fleet → `with-livespec-env.sh` → fleet App
(`livespec-pr-bot`); openbrain → `with-openbrain-env.sh` → openbrain's OWN App.
**Fail-closed**: no `credential_wrapper` → hard error, never a silent fleet
fallback. The fleet App is installed on **fleet repos ONLY** (audit installation
`131208965`; keep it off adopter repos — else the leak reappears one layer up).
Each adopter brings its own App + PEM in its own secret store. The fleet is just
"adopter #0" — no privileged path.

**Dogfood acceptance:** dispatch openbrain through the factory via its own App
with the fleet Environment UNREADABLE → openbrain's App opens the PR.

## Pillar 3 — one primitive for factory AND standalone

The credential provider + git credential helper is the fleet-wide GitHub-auth
primitive, used by BOTH factory dispatch and standalone agent worktree commits.
Standalone agent commits stop borrowing the human OAuth: the agent-context git
`credential.helper` is reset to ONLY the App-token helper (drop the inherited
`!gh auth git-credential`), `GH_TOKEN`/`GITHUB_TOKEN` scrubbed, `GH_CONFIG_DIR`
pointed at a tenant gh config with no human auth. Commit AUTHORSHIP is preserved
via git config (human name + `Co-Authored-By`); the App (`[bot]`) is only the
transport. Genuine human interactive work MAY keep the human's own `gh`.

## Pillar 4 — enforcement (the boundary is the OS, not a hook)

Real prevention of "agents using the ambient human OAuth" comes from a
**per-tenant unprivileged OS user**, not a hook. Grounding: today every session
runs as `ubuntu` (uid 1000), which is in `sudo` + `docker` + ALL tenant groups
and owns `~/.config/gh` — effectively root and every-tenant at once, so
in-session controls are advisory.

**Maintainer's decision (2026-07-02): this will run on a dedicated VPS where the
maintainer is NOT globally authenticated** — that environment (no ambient human
OAuth; per-tenant identity) provides the OS boundary and IS the external-adopter
environment.

On-host defense-in-depth (guardrails, not boundaries): a PreToolUse
`github_auth_guard` hook (sibling of the existing `beads_access_guard`) blocking
bare `gh`/`git push` that would fall through to ambient OAuth; scrubbed git/gh
config.

**The code side MUST fail-closed and wire only the blessed path, so it is
correct regardless of host.**

## Mechanics

- **Permissions:** `Contents: write` + `Pull requests: write` only.
- **Fleet App install scope:** fleet repos only.
- **Attribution:** bot noreply author email; branch-protection allowlist if
  required-reviews are ever enabled (fleet-followups inventory D10).
- **PEM custody:** probe-only, never committed to `.livespec.jsonc`/`.beads/`.

## Existing items to fold in during groom (prose-link; cite read-only)

- `bd-ib-gsl` (beads-fabro, "Factory PR-create auth: App installation token +
  parameterize entrypoint token source") → reshape/absorb into the factory
  slice.
- `bd-ib-p2e` (beads-fabro, grant the PAT + audit) → close as
  OBSOLETE/superseded by standardization.
- `C16` (fleet-followups inventory — wire openbrain's `credential_wrapper` to
  `with-openbrain-env.sh`) → folds in as dogfooding.
- `livespec-zd8h` (core, the just-CLOSED credential-wrapper epic) → this track
  is its successor.
- The console's stranded `idgql3` work-item → reset `active`→`ready`; its
  unblock is the first real validation of the App-token path.

## Open questions

- Home for the shared credential provider (`livespec_runtime` library vs a fleet
  tool).
- Can `actions/create-github-app-token` or an SDK be reused outside GitHub
  Actions inside the sandboxes?
- App-authored commits vs branch-protection / required-reviews interaction.
- Per-adopter PEM custody model.
