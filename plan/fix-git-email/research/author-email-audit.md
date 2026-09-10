# Git author email audit and remediation scope

Recorded: 2026-09-10
Plan slug: fix-git-email

## Objective

Ensure that every commit representing Chad Woolley's work uses the canonical
Git author identity:

- Name: Chad Woolley
- Email: thewoolleyman@gmail.com

This includes commits produced or replayed through normal Git usage, repository
configuration, factory automation, Fabro workflows, pre-commit hooks, commit
replay/amend/rebase paths, release machinery, and any other livespec ecosystem
commit-producing path.

The author field is the primary concern. Legitimate committer identities,
third-party authors, fixture identities, and genuinely bot-authored work must
not be blindly rewritten. Automation acting on Chad's work must preserve or set
the canonical author rather than substituting a bot, host-local, obsolete, or
invalid address.

## Investigation and remediation areas

- Audit global, conditional, repository-local, and worktree-specific Git
  identity configuration on every participating host.
- Audit environment variables and command-line overrides, including
  GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, git commit --author, git commit-tree,
  cherry-pick, rebase, amend, and squash/replay behavior.
- Trace factory and Fabro author selection separately from committer selection,
  including sandbox bootstrap, adapters, merge/replay nodes, release jobs, and
  GitHub API or bot-created commits.
- Trace pre-commit and commit-refuse hooks for any commit reconstruction or
  environment propagation that could change author identity.
- Add enforcement that rejects Chad-attributed commits unless the exact author
  is Chad Woolley <thewoolleyman@gmail.com>, without rejecting legitimate
  third-party, bot, or test-fixture authors.
- Determine and execute the historical-remediation boundary across owned,
  non-fork repositories. If history is rewritten, coordinate the stop-the-world
  procedure, backup refs, tags and release branches, GitHub force updates,
  work-item SHA references, caches, worktrees, clones, and post-rewrite
  verification.
- Preserve prior built runtime artifacts as historical artifacts rather than
  attempting to mutate their embedded provenance.
- Verify the final state across every relevant ref and every future
  commit-producing path, not only the checked-out default branch.

## Baseline report: unique author emails by owned, non-fork repository

Method: first-class local clones under /data/projects whose GitHub owner is
thewoolleyman and whose GitHub metadata reports isFork=false. Emails are exact
values from the author field of commits reachable from each GitHub default
branch. Committer-only identities are excluded.

| Repository | Author emails |
|---|---|
| 1password-env-wrapper | chad@thewoolleyman.com; thewoolleyman@gmail.com |
| claude-code-ntfy | chad@thewoolleyman.com; thewoolleyman@gmail.com |
| cxdb-graph-ui | chad@thewoolleyman.com; cwoolley@gitlab.com |
| dolt-server | chad@thewoolleyman.com; e2e-test@example.com; noreply@fabro.sh; thewoolleyman@gmail.com |
| fabro-hosts | chad@thewoolleyman.com; thewoolleyman@gmail.com |
| gmktec-xubuntu-info | chad@thewoolleyman.com; thewoolleyman@gmail.com |
| hp-xubuntu-info | chad@thewoolleyman.com; thewoolleyman@gmail.com |
| livespec | 283469463+livespec-pr-bot[bot]@users.noreply.github.com; 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com; chad@thewoolleyman.com; e2e-test@example.com; fixture@example.com; livespec-pr-bot[bot]@users.noreply.github.com; noreply@fabro.sh; thewoolleyman-factory-bot[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| livespec-console-beads-fabro | 283469463+livespec-pr-bot[bot]@users.noreply.github.com; 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com; anthropic-api-2@thewoolleyweb.com; chad@thewoolleyman.com; livespec-pr-bot[bot]@users.noreply.github.com; noreply@fabro.sh; thewoolleyman-factory-bot[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| livespec-dev-tooling | 283469463+livespec-pr-bot[bot]@users.noreply.github.com; 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com; 41898282+github-actions[bot]@users.noreply.github.com; anthropic-api-2@thewoolleyweb.com; chad@thewoolleyman.com; livespec-pr-bot[bot]@users.noreply.github.com; noreply@fabro.sh; test@example.com; test@test.test; thewoolleyman-factory-bot[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| livespec-driver-claude | 283469463+livespec-pr-bot[bot]@users.noreply.github.com; 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com; chad@thewoolleyman.com; livespec-pr-bot[bot]@users.noreply.github.com; noreply@fabro.sh; thewoolleyman-factory-bot[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| livespec-driver-codex | 283469463+livespec-pr-bot[bot]@users.noreply.github.com; 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com; anthropic-api-1@thewoolleyweb.com; chad@thewoolleyman.com; livespec-pr-bot[bot]@users.noreply.github.com; noreply@fabro.sh; thewoolleyman-factory-bot[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| livespec-driver-pi | 283469463+livespec-pr-bot[bot]@users.noreply.github.com; 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com; chad@thewoolleyman.com; livespec-pr-bot[bot]@users.noreply.github.com; noreply@fabro.sh; thewoolleyman-factory-bot[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| livespec-orchestrator-beads-fabro | 283469463+livespec-pr-bot[bot]@users.noreply.github.com; 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com; chad@thewoolleyman.com; livespec-pr-bot[bot]@users.noreply.github.com; noreply@fabro.sh; thewoolleyman-factory-bot[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| livespec-orchestrator-git-jsonl | 283469463+livespec-pr-bot[bot]@users.noreply.github.com; 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com; chad@thewoolleyman.com; livespec-pr-bot[bot]@users.noreply.github.com; noreply@fabro.sh; thewoolleyman-factory-bot[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| livespec-overseer | 283469463+livespec-pr-bot[bot]@users.noreply.github.com; 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com; chad@thewoolleyman.com; livespec-pr-bot[bot]@users.noreply.github.com; noreply@fabro.sh; noreply@openai.com; thewoolleyman-factory-bot[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| livespec-runtime | 283469463+livespec-pr-bot[bot]@users.noreply.github.com; 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com; 41898282+github-actions[bot]@users.noreply.github.com; livespec-pr-bot[bot]@users.noreply.github.com; noreply@fabro.sh; thewoolleyman-factory-bot[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| local-llm | chad@thewoolleyman.com; thewoolleyman@gmail.com |
| macbook-m4-max-info | thewoolleyman@users.noreply.github.com |
| openbrain | 41898282+github-actions[bot]@users.noreply.github.com; chad@thewoolleyman.com; noreply@fabro.sh; thewoolleyman@gmail.com |
| openclaw-info | chad@thewoolleyman.com; openclaw@macmini.local; thewoolleyman@gmail.com |
| personal-knowledge-base | chad@thewoolleyman.com; github-actions[bot]@users.noreply.github.com; thewoolleyman@gmail.com |
| poweredge-xubuntu-info | anthropic-api-2@thewoolleyweb.com; anthropic-api-4@thewoolleyweb.com |
| resume | 41898282+github-actions[bot]@users.noreply.github.com; chad@thewoolleyman.com; thewoolleyman@gmail.com |
| tab-groups-windows-list | action@github.com; chad@thewoolleyman.com; cwoolley@gitlab.com; github-actions[bot]@users.noreply.github.com; manus@example.com; noreply@anthropic.com; thewoolleyman@gmail.com |
| tailscale-admin | chad@thewoolleyman.com; cwoolley@gitlab.com; cwoolley@macbook-m4-max.perch-rudd.ts.net; thewoolleyman@gmail.com |
| tsvmtunnel | cwoolley@gitlab.com; thewoolleyman@gmail.com |
| vps-info | chad@thewoolleyman.com; thewoolleyman@gmail.com |

## Union of baseline author emails

The 28 repositories contain 24 exact author-email strings:

- 283469463+livespec-pr-bot[bot]@users.noreply.github.com
- 283469463+thewoolleyman-factory-bot[bot]@users.noreply.github.com
- 41898282+github-actions[bot]@users.noreply.github.com
- action@github.com
- anthropic-api-1@thewoolleyweb.com
- anthropic-api-2@thewoolleyweb.com
- anthropic-api-4@thewoolleyweb.com
- chad@thewoolleyman.com
- cwoolley@gitlab.com
- cwoolley@macbook-m4-max.perch-rudd.ts.net
- e2e-test@example.com
- fixture@example.com
- github-actions[bot]@users.noreply.github.com
- livespec-pr-bot[bot]@users.noreply.github.com
- manus@example.com
- noreply@anthropic.com
- noreply@fabro.sh
- noreply@openai.com
- openclaw@macmini.local
- test@example.com
- test@test.test
- thewoolleyman-factory-bot[bot]@users.noreply.github.com
- thewoolleyman@gmail.com
- thewoolleyman@users.noreply.github.com

## Baseline interpretation

The list is an inventory, not a rewrite map. Each non-canonical identity must
be classified by the person or process it represents before any rewrite or
enforcement change. In particular, test fixtures, third-party/tool authors,
GitHub Actions, factory bots, release bots, and Chad-authored commits currently
carrying host-local or obsolete addresses require different dispositions.
