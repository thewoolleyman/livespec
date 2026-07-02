"""livespec_runtime.github_auth — the fleet-wide GitHub App-token auth primitive.

Pillar 1 of the github-app-auth track (design record:
livespec core repo, plan/github-app-auth/research/01-design.md): GitHub
App installation tokens are the fleet's automation credential for ALL
automated GitHub operations — factory dispatch AND standalone agent
worktree commits alike (the fleet contract in livespec core's
SPECIFICATION/non-functional-requirements.md, v153). The durable secret is the App
private key PEM, supplied SOLELY via the calling tenant's
`credential_wrapper` environment injection; installation tokens are
ephemeral — minted on demand, re-minted transparently for operations
that outlive a token's ~1-hour validity, never persisted at rest.

- `livespec_runtime.github_auth.errors` — `GithubAppAuthError`, the
  single expected-failure domain error (missing/rejected credentials,
  App API rejections), always carrying an actionable `detail`.
- `livespec_runtime.github_auth.signing` — App JWT assembly (RS256
  header + backdated claims), PEM re-normalization for
  secrets-manager-flattened keys, and the openssl-subprocess RS256
  production signer.
- `livespec_runtime.github_auth.config` — `GithubAppConfig` +
  `load_github_app_config`: the env-only, fail-closed input boundary
  (`GITHUB_APP_ID` + `GITHUB_PRIVATE_KEY`; NEVER a fleet fallback).
- `livespec_runtime.github_auth.mint` — the installation-token mint
  railway over injectable sign/HTTP seams (installation discovery +
  `POST /app/installations/{id}/access_tokens`).
- `livespec_runtime.github_auth.provider` —
  `InstallationTokenProvider`: caches ~55 minutes and re-mints BEFORE
  the ~60-minute token expiry, transparently to callers of any
  duration.
- `livespec_runtime.github_auth.credential_helper` — the
  `git credential` helper entry point (get/store/erase protocol;
  answers `get` with `username=x-access-token` and the minted token as
  the password).

The package namespace itself stays empty (`__all__: list[str] = []`)
so the import contract is explicit at the sub-module level; this
matches the discipline applied throughout `livespec_runtime.cross_repo`
and `livespec_runtime.work_items`.
"""

__all__: list[str] = []
