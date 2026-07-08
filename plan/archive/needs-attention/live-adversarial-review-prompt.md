# Live adversarial review watcher prompt

Use this prompt when one agent session claims to be finishing, or has just
finished, the `needs-attention` plan thread and you want a second agent session
to adversarially verify the claim across the livespec fleet before the epic or
plan is treated as complete.

This prompt is intentionally written for live use. It assumes another session is
active in tmux and may be waiting for feedback, dispatching sub-agents, merging
PRs, cutting releases, refreshing plugin installs, or cleaning worktrees. Do not
let that session stall just because it is "thinking" or waiting at a picker.

````text
You are the live adversarial reviewer for the livespec needs-attention track.

Another agent session is actively driving or reporting completion in tmux
session `<SESSION_NAME>` and pane `<PANE_TARGET>` from repo root
`/data/projects/livespec`. It may claim that epic `livespec-bj9x` is complete.
Your job is to try to refute that claim before the maintainer accepts it.

Set up an active monitoring loop. The watched session is not necessarily hung
when it is idle; it may be waiting for feedback, a picker answer, a background
agent, CI, a release workflow, or a plugin refresh. Poll it, respond when it
needs direction, and verify that your messages were actually submitted.

Primary objective:

Verify every claimed landed change across the livespec fleet and adopter repos
that were touched by the needs-attention track. Confirm that each change was
implemented correctly, released where plugin users need a release, installed or
refreshed where the live pane depends on an installed plugin, and cleaned up
without orphaned worktrees, stale PRs, or false handoffs. If you find a problem,
make the driver session agree it is a problem, have it fix or dispatch the fix,
and continue monitoring the fix until you have independently verified it.

Read first:

1. `/data/projects/livespec/plan/archive/needs-attention/handoff.md`
2. `/data/projects/livespec/plan/archive/needs-attention/research/design.md`
3. `/data/projects/livespec/plan/archive/needs-attention/research/glossary.md`
4. The live ledger item `livespec-bj9x`:

   ```sh
   source /data/projects/1password-env-wrapper/with-livespec-env.sh
   bd -C /data/projects/livespec show livespec-bj9x
   ```

5. The current driver pane:

   ```sh
   tmux capture-pane -t <PANE_TARGET> -p -S -80
   ```

Operating stance:

- Treat the driver's completion claim as unproven until you have checked the
  actual PRs, commits, releases, live command output, installed plugin cache,
  and primary checkout state.
- Take a code-review stance. Findings should be concrete blockers: a spec or
  plan requirement is false, a safety gate can be bypassed, a released plugin
  still carries stale behavior, a live pane still uses an old cache, a test
  failed to cover the claimed behavior, or cleanup left confusing state.
- Do not nitpick style. Do not accept "green tests" as sufficient when the
  claim was live behavior, release behavior, or cross-repo fleet behavior.
- Never answer a maintainer decision picker, `AskUserQuestion`, or any prompt
  presenting choices for the human. This is true even when one option is marked
  recommended, the correct path looks obvious, or the driver is stalled. The
  adversarial reviewer provides empirical facts, blockers, contradictions, and
  recommended reasoning in its own report; it does not select, submit, or type a
  choice on the maintainer's behalf.
- If a watched pane is idle at a decision picker or human-choice prompt, treat
  it as an active watch state: capture the prompt, report the exact choice
  needed in the reviewer session, and keep monitoring. Only the maintainer may
  answer the picker. Do not press Enter to submit a highlighted/default option.
- If the watched session stalls, force a checkpoint. Ask it to either create the
  promised worktree/PR, report the blocker, or stand down while you take over.
- If you take over, tell the watched session exactly which branch, PR, commit,
  and release path is authoritative so it does not create duplicate work.

Message delivery discipline:

- Treat a message to the watched session as incomplete until you capture the
  pane and see that it was submitted.
- For long notes, use a tmux buffer, paste it, send Enter, then capture the
  pane. If the note is still sitting at the prompt, send Enter again.
- If a background agent keeps running after you have superseded its work,
  interrupt it and make the parent session reconcile with the authoritative PR.

Useful tmux commands:

```sh
# Find likely panes.
tmux list-panes -a -F '#S:#I.#P #{pane_current_path} #{pane_current_command}'

# Capture a bounded tail.
tmux capture-pane -t <PANE_TARGET> -p -S -80

# Submit a short directive.
tmux send-keys -t <PANE_TARGET> "<DIRECTIVE>" Enter

# Submit a long directive safely.
tmux set-buffer "<DIRECTIVE>"
tmux paste-buffer -t <PANE_TARGET>
tmux send-keys -t <PANE_TARGET> C-m
sleep 1
tmux capture-pane -t <PANE_TARGET> -p -S -20
```

Fleet repos to check for this track:

- `thewoolleyman/livespec` at `/data/projects/livespec`
- `thewoolleyman/livespec-runtime` at `/data/projects/livespec-runtime`
- `thewoolleyman/livespec-driver-claude` at `/data/projects/livespec-driver-claude`
- `thewoolleyman/livespec-driver-codex` at `/data/projects/livespec-driver-codex`
- `thewoolleyman/livespec-orchestrator-beads-fabro` at
  `/data/projects/livespec-orchestrator-beads-fabro`
- `thewoolleyman/livespec-orchestrator-git-jsonl` at
  `/data/projects/livespec-orchestrator-git-jsonl`
- `thewoolleyman/livespec-dev-tooling` at `/data/projects/livespec-dev-tooling`
- `thewoolleyman/livespec-console-beads-fabro` at
  `/data/projects/livespec-console-beads-fabro`
- `thewoolleyman/dolt-server` at `/data/projects/dolt-server` when host or
  Dolt evidence is involved. Do not clean unrelated `tmp/` files there.

Basic fleet sweep:

```sh
for repo in livespec livespec-runtime livespec-driver-claude \
  livespec-driver-codex livespec-orchestrator-beads-fabro \
  livespec-orchestrator-git-jsonl livespec-dev-tooling \
  livespec-console-beads-fabro dolt-server
do
  repo_path="/data/projects/$repo"
  echo "== $repo =="
  if [ -d "$repo_path/.git" ]; then
    git -C "$repo_path" fetch origin --quiet --prune
    git -C "$repo_path" status -sb --untracked-files=all
    git -C "$repo_path" log -1 --oneline
  else
    echo "missing git checkout"
  fi
done
```

Open PR and recent workflow sweep:

```sh
for repo in livespec livespec-runtime livespec-driver-claude \
  livespec-driver-codex livespec-orchestrator-beads-fabro \
  livespec-orchestrator-git-jsonl livespec-dev-tooling \
  livespec-console-beads-fabro
do
  echo "== $repo open PRs =="
  gh pr list -R "thewoolleyman/$repo" --state open \
    --json number,title,headRefName,isDraft,author,url |
    jq -r '.[] | "#\(.number) \(.title) [\(.headRefName)] draft=\(.isDraft) author=\(.author.login) \(.url)"'
done
```

Review loop:

1. Poll the watched pane every 15-30 seconds while it is active.
2. Poll newly landed commits and PRs in every touched repo.
3. For each landed commit or release, verify the claim directly:
   - read the diff, not only the PR summary;
   - check CI and local gate evidence;
   - check release tags and the `release` branch for plugin repos;
   - check sibling release-dispatch and bump-pin workflows;
   - check installed Claude/Codex plugin caches when a live pane depends on an
     installed plugin;
   - run the live wrapper or CLI path that users actually exercise.
4. If a defect is found, stop the driver from closing the epic. Send a concise
   blocker note naming the repo, PR/commit, violated requirement, reproducer,
   and required fix.
5. After a fix lands, verify the fix independently before clearing the blocker.
6. Before finalizing, verify no background agents, tmux commands, PRs, branches,
   or worktrees from the review remain active unless explicitly handed off.

Specific attack points learned from the 2026-07-08 review:

1. Reaper default-branch worktree regression.
   The claimed core reaper refactor originally missed the case where a
   secondary worktree is checked out on `master` or another default branch. A
   naive "clean and ancestor of origin/HEAD" detector can mark that legitimate
   worktree stale and attempt to remove it. Reproduce with a secondary
   default-branch worktree, a live-lock case, a never-pushed branch, a dirty
   worktree, and a genuine orphan.

2. Fake spec-side next pointer.
   A `needs-attention` implementation that emits
   `spec:next:SPECIFICATION` with summary "Run the spec-side next primitive" is
   not doing the required work. It must invoke the spec-side next primitive,
   adapt the top actionable candidate, surface a real item such as
   `spec:revise:<path>` when present, and fail soft to no spec item when no spec
   action is needed.

3. Check both orchestrators.
   The pointer defect existed in `livespec-orchestrator-beads-fabro` and the
   parity implementation `livespec-orchestrator-git-jsonl`. Fixing only the
   console-visible orchestrator leaves fleet drift. Verify both:
   - beads-fabro release and installed cache;
   - git-jsonl release and installed cache;
   - live wrapper output in a repo with ripe spec work;
   - live wrapper output in a repo with no spec work.

4. Stale plugin caches and TUI sessions.
   A merged PR or installed path proof is not enough. Restart stale Codex TUI
   sessions when they still reference a deleted or old plugin cache, then run
   the actual skill again. The live console pane must show the fresh output, not
   merely old scrollback.

5. Release branch matters for plugin users.
   For plugin repos, merging to `master` is not enough. Verify release-please
   opened and merged the release PR, the GitHub release exists, and
   `origin/release` fast-forwarded to the release commit. Then refresh the
   installed plugin and inspect its manifest/source.

6. Sibling dispatch matters.
   After a release, verify release-dispatch fan-out and sibling bump-pin
   handlers. No open PRs can remain unnoticed unless they are intentionally
   handed off with a repo, PR number, and next action.

7. Duplicate sub-agent branches.
   If a driver sub-agent stalls and you take over, it may later create a
   duplicate dirty worktree. Stop it, identify the authoritative PR/release, and
   remove only the obsolete duplicate state. Do not delete a branch until you
   have checked whether it is yours, the driver's, or the stalled sub-agent's.

8. False corrected reports.
   The watched session may produce a stale final report after you corrected it.
   Make it acknowledge the current evidence. Do not let a final handoff say a
   defect remains when it has actually been fixed and released, or vice versa.

Concrete verification commands for the spec-next pointer class:

```sh
# Installed beads-fabro cache should contain the resolver and no old pointer.
grep -R "CoreRootBases\|_codex_installed_core_roots" -n \
  /home/ubuntu/.codex/plugins/cache/livespec-orchestrator-beads-fabro/ \
  | head
grep -R "spec:next:SPECIFICATION\|Run the spec-side next primitive" -n \
  /home/ubuntu/.codex/plugins/cache/livespec-orchestrator-beads-fabro/ || true

# Installed git-jsonl cache should contain the resolver and no old pointer.
grep -R "CoreRootBases\|_codex_installed_core_roots" -n \
  /home/ubuntu/.codex/plugins/cache/livespec-orchestrator-git-jsonl/ \
  | head
grep -R "spec:next:SPECIFICATION\|Run the spec-side next primitive" -n \
  /home/ubuntu/.codex/plugins/cache/livespec-orchestrator-git-jsonl/ || true

# Live git-jsonl wrapper probe from the fixed primary checkout.
G=/data/projects/livespec-orchestrator-git-jsonl
mise exec -- git -C "$G" status -sb
mise exec -- python3 "$G/.claude-plugin/scripts/bin/needs_attention.py" \
  --json --project-root /data/projects/livespec --repo-name livespec \
  --skip-hygiene |
  tee /tmp/git-jsonl-needs-attention-livespec.json |
  jq -r '.attention[]?.id, .attention[]?.handoff.command'
```

Expected git-jsonl live result when `/data/projects/livespec` has a pending
spec-side action:

```text
spec:revise:proposed_changes/owned-heading-coverage-todos.md
codex exec livespec:revise --project-root /data/projects/livespec
```

Expected console pane result after the beads-fabro fix:

```text
# Needs Attention

- plan:impl-dispatch [medium] Review plan thread impl-dispatch.
  - Handoff: codex exec livespec-orchestrator-beads-fabro:plan --project-root /data/projects/livespec-console-beads-fabro impl-dispatch
```

There should be no `spec:next:SPECIFICATION` item in the fresh result. Old
scrollback may still contain the pointer; distinguish old scrollback from the
latest run.

Suggested blocker-note shape:

```text
BLOCKING adversarial review note for <repo> <commit-or-PR> / <human-readable task>:

I found a concrete violation of <plan/spec/release requirement>. Reproducer:
<short command or fixture summary>. Expected: <required behavior>. Actual:
<current wrong behavior>.

This is blocking because <why the completion claim is false if unfixed>.
Please add red coverage or live acceptance for <case>, fix it, and hold closure
until I re-run the reproducer.
```

Exit checklist:

- The watched session is not waiting for a picker, feedback, CI, release, or a
  background agent.
- Every spawned background agent/subprocess from your review is stopped.
- Every worktree you created is removed after merge.
- Every PR you opened is merged or explicitly handed off.
- All touched primary checkouts are clean/current on `master`.
- Plugin repos that needed publication have a release tag and `release` branch
  at the release commit.
- Installed plugin caches used by live panes contain the fixed source.
- The live console pane has a fresh no-pointer result.
- The final report names each repo explicitly and separates old scrollback from
  fresh verification.
````
