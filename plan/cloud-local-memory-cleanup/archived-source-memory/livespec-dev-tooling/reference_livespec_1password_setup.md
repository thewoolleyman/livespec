---
name: reference-livespec-1password-setup
description: Where the livespec GitHub App credentials live + how to retrieve them via the 1password-env-wrapper on this machine.
metadata: 
  node_type: memory
  type: reference
  originSessionId: 48850880-6a8c-4e3b-a8e3-798911468efd
---

The `livespec-pr-bot` GitHub App credentials (used by
`auto-enable-merge.yml`, the cross-repo coordination shim workflows,
and any future App-token-driven automation) live in a livespec
1Password Environment, NOT on disk.

**Authoritative locations on this machine:**

- 1Password Environment ID: `fufpvkvatwkmqjzvilvfnemsue`
- Service account token: encrypted at
  `/etc/credstore.encrypted/1password-env-wrapper-livespec`
- Installed wrapper: `/usr/local/bin/with-livespec-env.sh`
  (root:livespec, mode 0750)
- Factory repo (for re-rendering): `/data/projects/1password-env-wrapper/`

**Environment variables in the livespec 1Password Environment:**

- `GITHUB_APP_ID` — the App's numeric ID (3668528)
- `GITHUB_CLIENT_ID` — OAuth client id (Iv23li1jYFFYrpVjeLxJ)
- `GITHUB_CLIENT_SECRET` — OAuth client secret (40 chars)
- `GITHUB_PRIVATE_KEY` — RSA private key in PEM format. CAUTION:
  stored as a single-line string in 1Password (no newlines). Reformat
  with proper newlines before passing to `jwt.encode` or
  `actions/create-github-app-token@v1`. Regex pattern to split:
  `(-----BEGIN [A-Z ]+-----)(.+?)(-----END [A-Z ]+-----)` then wrap
  the body at 64 chars.

**UPDATE 2026-06-29:** the wrapper now WORKS when invoked directly —
`source /data/projects/1password-env-wrapper/with-livespec-env.sh <cmd>`
(and `with-livespec-env.sh <cmd>` via `/usr/local/bin`) both run the
command with the 1Password env injected. Confirmed by probe: it injects
`BEADS_DOLT_PASSWORD` for the beads/Dolt tenants (used for every L2
tenant migration command). The old `env --` bug below is no longer
hit (uutils env updated and/or the wrapper re-rendered). Probe-only: a
trivial `bash -c 'test -n "$BEADS_DOLT_PASSWORD" && echo INJECTED'`
confirms injection without echoing the secret.

**(Historical) Bypass for the broken `env --` separator:**

The system HAD `uutils env` 0.2.2 which didn't accept the `--` separator.
The wrapper at `/usr/local/bin/with-livespec-env.sh` used to fail when
invoked directly because both its stage-0 (`exec env WRAPPER_STAGE=1 -- ...`)
and stage-2 (`op run ... -- env -u OP_SERVICE_ACCOUNT_TOKEN -- "$@"`)
hit this bug.

**How to retrieve credentials without the wrapper:**

```bash
TOKEN=$(sudo -n systemd-creds decrypt \
  --name=1password-env-wrapper-livespec \
  /etc/credstore.encrypted/1password-env-wrapper-livespec -)
OP_SERVICE_ACCOUNT_TOKEN="$TOKEN" op run --no-masking \
  --environment fufpvkvatwkmqjzvilvfnemsue \
  -- /bin/bash -c '<command using $GITHUB_*>'
```

The `op` binary on this system is 2.35.0-beta.01 which supports
Environments. The service account has access only to env vars (no
vault item access — vault list returns empty).

**App installation:**

- Installation ID: `131208965` on user `thewoolleyman`
- Settings page: https://github.com/settings/installations/131208965
- All 4 sibling repos are added: livespec, livespec-dev-tooling,
  livespec-runtime, livespec-impl-plaintext
- Permissions: contents: write, pull_requests: write, metadata: read

**Why:** Centralizing the App credentials in 1Password lets the
operator rotate keys + push the new value once, and every machine /
agent with access to the SA token picks it up automatically. Beats
pasting PEMs into chat or storing them on disk.

**How to apply:** When a livespec automation needs to mint an App
installation token, use the `with-livespec-env.sh` wrapper (or the
direct decrypt path above if the wrapper hits the env-- bug),
reformat the PEM with proper newlines, mint a JWT via PyJWT, and call
`POST /app/installations/131208965/access_tokens` to get a short-lived
installation token.

Related: [[project-livespec-sibling-family-cross-repo-coordination]]
