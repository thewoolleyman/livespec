# Governed-repository activity report

This directory contains the generated, fleet-wide activity report requested by
the maintainer. The source of truth is `update-activity.sh`; do not hand-edit
`livespec-governed-repo-activity.md` or the three `activity-*.svg` charts.

## Reproduce the report

Prerequisites:

- authenticated `gh` access to every repository in
  `.livespec-fleet-manifest.jsonc`;
- `git` and Python 3.10 or newer;
- a local clone of every manifest `fleet` and `adopters` entry. The generator
  searches an explicit workspace root first, then the report checkout's parent,
  `~/workspaces`, `~/workspace`, and `/data/projects`.

From the livespec repository root, run:

```bash
docs/activity/update-activity.sh
```

The default interval starts on 2026-06-01 and ends on the UTC generation date.
The following interfaces are stable for future refreshes:

```bash
docs/activity/update-activity.sh \
  --since 2026-06-01 \
  --through 2026-09-09 \
  --workspace-root /data/projects
```

The equivalent environment variables are `LIVESPEC_ACTIVITY_SINCE`,
`LIVESPEC_ACTIVITY_THROUGH`, and `LIVESPEC_ACTIVITY_WORKSPACE_ROOT`. Set
`SOURCE_DATE_EPOCH` to pin the generated-at timestamp when checking a
byte-for-byte reproduction. Arguments take precedence over the activity
environment variables.

The command rewrites all four generated artifacts atomically:

- `livespec-governed-repo-activity.md`;
- `activity-closed-pull-requests.svg`;
- `activity-modified-lines.svg`;
- `activity-existing-lines.svg`.

It deliberately keeps no repository-local cache. For each governed repository,
it creates a temporary bare repository whose object database borrows from the
local clone, fetches current GitHub branch refs and relevant pull-request refs,
computes the report, and removes the temporary repository. This keeps every
primary clone's branch, refs, index, and working tree unchanged.

## Accounting rules

The repository set and ordering come directly from the manifest's `fleet`
array followed by its `adopters` array. GitHub repository identity is derived
from each clone's `origin`, not assumed from the manifest-level owner, because
an adopter can live in a different organization. The default branch comes from
`origin/HEAD`, falling back to `gh repo view`.

The three metrics have different semantics:

1. **Pull requests closed** counts every PR by GitHub `closed_at`, including
   merged and closed-unmerged PRs. No automation filtering applies to this
   metric.
2. **Eligible lines modified** sums additions plus deletions from non-merge
   commits reachable from all current remote branches and every PR updated in
   the reporting window. Stable Git patch IDs deduplicate rebases,
   cherry-picks, and the original PR-head copy. When copies span months, the
   earliest copy determines the month. Binary changes contribute no lines.
3. **Eligible lines currently existing** counts physical lines in eligible
   files at each completed month end and at the through-date for the final
   month. `Overall` is the final snapshot, not a sum of snapshots.

AI generation is in scope. Do not exclude Fabro, Codex, Claude, or another AI
author merely because the author name is automated. Line exclusions apply only
to known dependency/release automation, deterministic dependency or generated
paths, and explicit automated copier/template-sync activity.

The generator's constants are authoritative for exact classification. In
summary, included content is prose documentation; programming, query,
web/template, and infrastructure languages; shell and other scripts; standard
script entry files; and workflow/infrastructure YAML, JSON, or TOML. Excluded
content includes lock/dependency files, vendored/third-party trees,
generated/build/cache/output trees, source maps, minified files, snapshots, and
commits or PRs deterministically classified as dependency, release, pin-bump,
or automated template-sync activity.

Pure renames count as zero modified lines because Git rename detection stays
enabled. Merge commits are omitted so branch patches are not counted again.
Physical-line stock counts include comments and blank lines, matching the unit
used by Git additions and deletions.

## Verification before committing a refresh

Run the generator once normally, then validate the generated artifacts and the
repository gate:

```bash
bash -n docs/activity/update-activity.sh
git diff --check
mise exec -- just check
```

For a deterministic replay, note the report's generated-at epoch, set
`SOURCE_DATE_EPOCH` and `--through` to the same values, rerun, and confirm that
`git diff` is empty. A live rerun without a pinned timestamp is expected to
change the generated-at line and can also incorporate newly closed PRs or newly
pushed refs.

When classification rules change, review the explanatory final section of the
generated report in the same commit. The generator owns that prose, so update
its report template rather than editing the Markdown output.
