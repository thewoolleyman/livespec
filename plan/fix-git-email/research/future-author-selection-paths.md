# Future Git author paths and rewrite cutover constraints

Recorded: 2026-09-10

## Decision frame

The target identity for work owned by Chad is exactly:

- Name: `Chad Woolley`
- Email: `thewoolleyman@gmail.com`

“Owned by Chad” includes feature, fix, documentation, specification, planning,
and test work performed interactively or by a coding agent/factory on Chad's
behalf. Agent identity belongs in `Co-Authored-By` trailers when the workflow
uses them; a GitHub App used to transport a push belongs in the committer or
forge audit trail, not as the author.

Mechanical release, dependency-pin, backup, tripwire, and similar autonomous
jobs remain bot-authored. Genuine third-party work also retains its original
author. The rewrite therefore requires a reviewed classification manifest; it
must not replace every non-Gmail address indiscriminately.

## Measured author populations

The default-branch census in `author-email-audit.md` was refined to exact
name/email pairs. Across the 28 owned, non-fork repositories it found:

| Population | Default-branch commits | Initial disposition |
|---|---:|---|
| `Chad Woolley <thewoolleyman@gmail.com>` | 764 | Already canonical |
| `thewoolleyman <thewoolleyman@gmail.com>` | 231 | Normalize the name |
| Any name with `chad@thewoolleyman.com` | 8,500 | Rewrite to canonical |
| `cwoolley@gitlab.com` | 102 | Rewrite to canonical |
| Host-local `cwoolley@macbook-m4-max...` | 4 | Rewrite to canonical |
| `thewoolleyman@users.noreply.github.com` | 1 | Rewrite if confirmed Chad-owned |
| `anthropic-api-*@thewoolleyweb.com` | 30 | Factory work; rewrite |
| `Fabro <noreply@fabro.sh>` | 1,823 | Coding-agent/factory work; rewrite |
| `E2E Test`, `Test`, `Test User`, or `Fixture User` fixture-like emails | 537 | Real repository work, not fixture commits; rewrite |
| Claude, Codex, OpenClaw, or Manus author identities | 65 | Classify by commit; rewrite Chad-directed work |
| livespec PR/factory bot release and pin-bump identities | 5,317 | Retain bot authors |
| GitHub Actions / GitHub Action identities | 805 | Retain mechanical bot authors unless commit review proves otherwise |

The fixture-like identities are not harmless test data in history. Samples
include ordinary product work such as `chore: rename livespec fleet manifest`,
`fix: reroute source_trees structural checks...`, and the initial Codex Driver
implementation. Likewise, Fabro-authored commits overwhelmingly contain real
features and fixes. Both populations represent the same attribution defect as
the obsolete address.

The bot distinction is supported by subject distributions: the two generations
of `livespec-pr-bot` and `thewoolleyman-factory-bot` authors are release commits
(`chore(master): release ...`) or dependency pin bumps (`chore(deps): bump ...`).
Those are autonomous mechanical changes and are not rewritten as Chad.

## Future author-selection paths

### Interactive Git and worktrees

The current host's global config now resolves to the canonical name and email,
and the `livespec` and `livespec-runtime` local overrides are canonical. No live
worktree-specific `user.name` or `user.email` override was found. Worktrees
normally share the primary clone's common config, so one local override affects
every attached worktree.

Two noncanonical local overrides remain outside the exact obsolete-address fix:

- `/data/projects/poweredge-xubuntu-info`: `user.email` is
  `anthropic-api-2@thewoolleyweb.com`.
- `/data/projects/homelab`: `user.name`/`user.email` are
  `test <test@example.com>`; this clone was outside the owned-non-fork history
  report but is still a future-commit risk on this host.

`user.useConfigOnly` is not set globally. Adding it prevents Git from inventing
an identity when configuration is absent, but does not defend against a stale
environment or an explicit command-line author.

### Environment and long-lived runtimes

`GIT_AUTHOR_NAME` and `GIT_AUTHOR_EMAIL` override corrected config. The current
session has no such variables, but two orphaned pytest tmux servers still carry
`thewoolleyman <chad@thewoolleyman.com>` from their August launch environments.
They run in deleted fixture directories and are not production committers, but
prove that a long-lived tmux/service process can preserve a stale author after
the files on disk are fixed. All real agent, overseer, factory, and terminal
runtimes must therefore be stopped and restarted after identity remediation.

### Red-Green-Replay, amend, rebase, and hooks

`livespec_dev_tooling.tdd_commit` creates the Red commit and then amends it for
Green. It intentionally removes repository-routing variables such as `GIT_DIR`
from child calls, but passes `GIT_AUTHOR_*` through. The Red commit therefore
selects the environment/config author and the Green amend carries that author
forward. The current pre-commit/commit-msg machinery validates worktree
discipline and TDD evidence but does not validate author identity.

Ordinary cherry-pick and rebase preserve the original author. That is correct
for third-party commits but also preserves a bad author until the history
rewrite. `--reset-author`, `--author`, `git commit-tree`, and author environment
variables are separate override paths and need direct tests in the new guard.
The guard must inspect the effective pending author, not merely read
`git config user.email`.

Core's `livespec.io.git.get_git_user()` currently reads `git config user.name`
and `user.email` directly for revision metadata. It can therefore record the
canonical config identity while the actual commit uses a conflicting
`GIT_AUTHOR_*` override. The metadata and commit-author paths must share one
effective-identity rule or fail on disagreement.

### Fabro and the livespec factory

Fabro has a first-class `[run.git.author]` setting. At run initialization it
writes that identity into the sandbox clone, and the same value is used for
Fabro checkpoint and metadata commits. The livespec implementation and grooming
workflows do not declare the setting, so Fabro falls back to
`Fabro <noreply@fabro.sh>` for both author and committer. This directly explains
the 1,823 Fabro-authored default-branch commits.

The shared sandbox image also installs a system fallback of
`E2E Test <e2e-test@example.com>`. Modern Fabro runs overwrite it locally, but
older/direct commit paths have allowed that fallback to become the author of
real work. A reusable base image should have no plausible production identity:
the workflow must set one explicitly and a missing setting should fail closed.

The two livespec workflow graphs also create a needs-human preservation commit
with an explicit `fabro <fabro@livespec.invalid>` override. The ref is normally
run-scoped, but recovered work can carry that commit into a later branch. It
must use the configured run author rather than bypassing it.

The reserved workflow bundle is the authority used by the Dispatcher; any
registered peer workflow must carry the same author contract. This change does
not require changing upstream Fabro's generic default for every adopter. The
livespec-owned workflow configuration supplies Chad's identity, while the
generic contract requires each operator to declare its own intended author.

### GitHub and release automation

The authenticated GitHub profile publicly reports `Chad Woolley` and
`thewoolleyman@gmail.com`. The current token cannot enumerate private account
email settings, so the cutover checklist must manually verify that the Gmail
address is verified/primary and that web commits are not forced to the GitHub
noreply address.

GitHub rebase merge preserves the feature commit's author while the App/server
can be the committer; the plan-creation merge demonstrated the desired split.
The shared pin-rewrite Action deliberately configures the GitHub App as author
for its mechanical dependency-bump commit, and release jobs similarly author
mechanical release commits as bots. Those paths are allowed exceptions and
must be regression-tested as such.

## Enforcement shape

The existing core contract says agent-path authorship “SHOULD” be preserved via
Git config. The observed Fabro behavior satisfies neither the intent nor a
fail-closed guarantee. A spec change should make the following enforceable:

1. An agent/factory path that produces operator-owned work MUST declare and use
   the operator's intended author identity; transport credentials MUST NOT
   replace it.
2. A missing or conflicting author identity MUST fail before a commit is
   published.
3. A local opt-in policy (installed on Chad's hosts/factory sandboxes, not
   imposed on outside contributors) checks the effective author in pre-commit
   and commit-msg paths. It allows explicitly declared mechanical bot jobs.
4. Fleet verification scans every published ref for forbidden Chad aliases and
   verifies the exact canonical identity for commits classified as Chad-owned.

The host-side setting should also enable `user.useConfigOnly=true`. A shared
guard must cover initial commit, amend, Red-Green-Replay, cherry-pick, rebase,
`--author`, and `GIT_AUTHOR_*`, and it must demonstrate that third-party and
declared bot authors remain possible.

## History-rewrite cutover constraints

The rewrite changes only selected commits' author name/email bytes. Commit
messages, trees, author dates, committer name/email/date, and parent order stay
unchanged. Parent SHA changes necessarily cascade through every descendant.
A deterministic old-to-new commit map is a required cutover artifact.

The current clones are not ready for an in-place rewrite:

- The ten core fleet repos currently expose many remote feature branches and
  hundreds of release tags; `release` is a branch in most plugin repos.
- Local clones contain large numbers of old worktree branches plus stashes and,
  in `livespec-overseer`, archive/backup/tmp refs.
- `git-filter-repo` is not currently installed, so the chosen rewrite engine
  must be pinned and rehearsed in fresh mirror clones.
- Almost all tags are lightweight; `livespec-dev-tooling` has one annotated
  tag. Rewriting signed commits or annotated tags invalidates/removes their
  signatures and requires an explicit re-sign-or-document disposition.
- Changelogs contain direct links to old commit SHAs. They may remain valid
  because the old graph is deliberately retained, but they will not point at
  the rewritten equivalents unless a separate content rewrite is chosen.

A tag named `before-author-cleanup` pointing only at the old default-branch tip
preserves all ancestors of that tip, not every disconnected tag/release/archive
tip. Before deleting or replacing refs, the cutover must prove all retained old
tips are reachable from that one commit. If not, either dispose the disconnected
refs explicitly or create one synthetic umbrella commit whose parents are every
old tip and point the single backup tag at that commit. That preserves the
single-tag operator surface while keeping every intended old SHA reachable.

### Required stop-the-world sequence

1. Land and release the future-author protections first; refresh every active
   plugin/workflow cache and prove a new interactive commit and a new Fabro run
   both use the canonical author.
2. Stop Dispatcher, overseer-driven implementation, release/pin automation,
   terminals, and agents. Cancel in-flight runs. Inventory all hosts, clones,
   worktrees, local branches, stashes, remote branches, PRs, tags, release
   branches, and nonstandard refs. Resolve or archive them before rewriting.
3. Disable GitHub Actions and other tag/push-triggered automation for every
   repository. Temporarily arrange an audited branch/ruleset bypass for force
   updates; record the exact settings for restoration.
4. Freeze a fresh mirror of each remote, classify every author pair/commit,
   obtain the human approval of ambiguous tool/third-party identities, and
   create the single backup tag with proven whole-old-graph reachability.
5. Run the pinned author-only rewrite in mirrors. Verify commit/tree counts,
   byte-identical trees, unchanged messages/committer fields/dates, the author
   policy, tag/release targets, and the complete old-to-new map before pushing.
6. Force-update the default branch, retained `release` branch, and every tag as
   one controlled repository operation. Never run ordinary release workflows
   during this push. Verify GitHub refs before moving to the next repository.
7. Restore rulesets and Actions, manually dispatch post-rewrite CI, and verify
   releases, plugin resolution, default branches, tags, and cross-repo pins.
8. Delete/reclone stale local clones and caches on every participating host.
   A normal pull cannot reconcile rewritten history; cached branch-ref and tag
   installs can silently retain old objects.
9. Resume the factory only after an all-repository author census and one live
   Fabro canary are green.

## Expected immutable fallout

Some GitHub and artifact records cannot be edited into the new SHA universe.
Merged-PR event records, review anchors, old checks/statuses, Actions logs,
deployments, attestations, SBOM/provenance statements, package metadata, OCI
labels, and prior built runtime artifacts can continue to name old SHAs. This is
why preserving the old graph and the old-to-new map is required. New CI/status
records attach to rewritten tips; old records remain historical evidence.

Moving a release tag makes the tag name resolve to the rewritten commit while
an already-published artifact may still attest that it was built from the old
equivalent SHA. Prior built artifacts are explicitly excluded from rebuilding;
the mapping and backup tag document that equivalence instead of pretending the
old provenance changed.

Open forks and outside clones will diverge and must rebase/reclone manually.
GitHub PR associations and “merged commit” metadata may continue to reference
the old SHA even when it remains reachable. The cleanup can preserve those
references; it cannot make every historical GitHub record mutable.

## Planned delivery layers

1. Ratify the operator-author/transport-committer contract and the fail-closed
   enforcement boundary.
2. Fix Fabro workflow author configuration and emergency commits, harden the
   sandbox fallback, and release/roll out the corrected factory path.
3. Add the effective-author guard and host/fleet reconciliation, including
   `user.useConfigOnly`, local override repair, long-lived-runtime restart, and
   core revision-metadata alignment.
4. Build the deterministic classification/rewrite/verification tool and rehearse
   it against mirrors without touching GitHub.
5. Perform the human-gated stop-the-world GitHub cutover across the 28 owned,
   non-fork repositories.
6. Reclone/refresh every host and cache, run the all-ref census and Fabro canary,
   then resume automation.
