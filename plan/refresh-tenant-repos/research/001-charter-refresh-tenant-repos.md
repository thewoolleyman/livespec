# Charter — refresh-tenant-repos (livespec)

Opened 2026-10-01 at the maintainer's direction (autonomous, pre-authorized
brief; coordinated by a Codex session on the maintainer's Mac). This plan adds
a `just refresh-tenant-repos` recipe to livespec core.

## Requirements

1. A justfile recipe named `refresh-tenant-repos` in livespec.
2. For ALL repos the livespec configuration names, clone the missing ones as
   PEERS of this livespec primary clone (the directory that contains the
   primary checkout), never at a configured absolute `local_clone` path —
   those carry VPS paths (`/data/projects/...`) that do not exist on the Mac.
3. Registry scope is the UNION of every registry livespec carries, so no
   requested repo is omitted:
   - `.livespec.jsonc` `cross_repo_targets` (6 repos; the planning registry);
   - `.livespec.jsonc` `cross_repo_conformance_targets` (a strict subset);
   - `.livespec-fleet-manifest.jsonc` `fleet` (10 repos) and `adopters`
     (4 repos: openbrain, dolt-server, resume, homelab).
   Union today: 14 repos. `cross_repo_targets` alone would omit the three
   driver repos, livespec-runtime, and all four adopters.
4. `gh` must be on PATH and authenticated (`gh auth status`); clones use
   `gh repo clone`, and fetches route HTTPS credentials through
   `gh auth git-credential` for that one command (no global git-config edit).
5. Refresh each existing primary clone to its default branch safely: the
   configured `default_branch` where a registry declares one, otherwise the
   forge's default branch (`gh repo view`).
6. Before changing anything, inspect: uncommitted / staged / untracked files,
   an in-progress merge / rebase / cherry-pick / revert / bisect, the current
   branch's unpushed commits, and local-default-branch divergence from origin.
   Mutate only mechanically-provably-safe state:
   - delete untracked files whose basename is exactly `.DS_Store` (macOS
     Finder metadata; regenerated on demand, never authored content);
   - switch branches only when the tree is clean and the current branch has
     no commit absent from every remote-tracking ref;
   - update the default branch by fast-forward only.
   Anything else is preserved untouched and reported with explicit manual
   cleanup instructions, and the run exits non-zero.
7. Deterministic Python, no LLM, under this repo's normal tooling, typing,
   error-handling, and test disciplines.

## Design

`dev-tooling/refresh_tenant_repos.py` (+ split helper modules to stay under
the LLOC ceiling), invoked by `just refresh-tenant-repos`. Exit codes: 0 all
repos refreshed; 1 one or more repos blocked (preserved, instructions
printed); 2 preflight failure (gh absent / unauthenticated, config
unreadable). Location of the peer root is derived from
`git rev-parse --git-common-dir`, so a run from a linked worktree still
targets the primary's peers.

## Factory route

Implementation goes through this repo's factory: a self-contained child
work-item under the plan epic, dispatched via `drive --action impl:<id>`
(Fabro sandbox -> janitor gate -> PR -> required checks -> rebase merge).
Live host acceptance (VPS run here, Mac run by the Codex coordinator) follows
the merge; it does not make the implementation factory-ineligible.

## Live acceptance cases (Mac preflight, 2026-10-01)

- `livespec-driver-pi` is absent on the Mac — the missing-clone path.
- `livespec-driver-codex` on the Mac carries exactly two untracked files,
  `.DS_Store` and `livespec/.DS_Store` — the safe-junk cleanup path.
