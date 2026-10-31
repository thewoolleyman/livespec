# 003 — Cutting the releases that ship the wording fixes

Written 2026-10-30 by Claude Code session `ce19c72a-238e-4973-bbde-0a4f85197eb8` (plan owner).

## Why a release had to be cut by hand

Note 002 recorded that every carrier fix merged as a `docs(...)` commit, and that none of the five
repositories releases on `docs`. The coordinator (`gitops-fleet-capacity-monitoring`, repo
`livespec-dev-tooling`, item `livespec-dev-tooling-dfixhe`) then made this plan a tracked item under
the maintainer's attended direction of 2026-10-30 ~21:0xZ and asked for the release to be cut rather
than waited for. The fleet pattern for that is a `fix(release): release ... as vX.Y.Z` commit carrying
a `Release-As:` footer (precedent: `livespec-orchestrator-beads-fabro` commit `3ae29893b`).

## The first attempt changed nothing

The first attempt used EMPTY commits (`git commit --allow-empty`) carrying the footer, one pull request
per repository: `livespec` #2999, `livespec-driver-claude` #930, `livespec-driver-codex` #875,
`livespec-driver-pi` #421. All four report MERGED, and none of them changed master: GitHub's
rebase-merge drops an empty commit, so each pull request's recorded merge commit is the PREVIOUS
master tip (for example #2999's is `81fc4923`, the note-002 merge). No release-please run fired for
any of them.

Lesson: on a rebase-merging repository, a pull request whose only commit is empty merges as a no-op
while reporting MERGED. A `Release-As:` commit must carry a real change. The precedent commit carried a
research note for exactly that reason.

## The second attempt

Each release commit now carries a genuine, related change:

- `livespec`: this note.
- `livespec-driver-claude` and `livespec-driver-codex`: the README's one-line summary of `revise`,
  which still read "accept or reject pending proposed changes", now matches the shipped binding
  description (accept, modify, or reject, confirming with the user or deciding under the configured
  delegated mode).
- `livespec-driver-pi`: the same one-line summary in `AGENTS.md`'s operation table.

Target versions: `livespec` v0.44.3, `livespec-driver-claude` v0.12.1, `livespec-driver-codex` v0.8.4,
`livespec-driver-pi` v0.6.2. `livespec-orchestrator-beads-fabro` follows once `bd-ib-wlizdf` merges.
