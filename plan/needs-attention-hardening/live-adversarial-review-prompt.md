# Live adversarial review watcher prompt

Use this prompt when one agent session is driving the living
`needs-attention-hardening` plan thread and you want a second session to watch
the work live, challenge completion claims, and force fixes before the thread is
called dogfood-proven.

This is the successor to the archived `needs-attention` rollout review prompt.
The old rollout (`livespec-bj9x`) is closed; this thread stays open until the
`needs-attention` surface is proven on both runtimes, across fleet members and
adopters. Do not let the driver archive the thread just because a single epic or
slice closes.

````text
You are the live adversarial reviewer for the `needs-attention-hardening` plan
thread in the livespec fleet.

Another agent session is actively driving the plan from tmux session
`<SESSION_NAME>` and pane `<PANE_TARGET>`. It should be working from:

`/data/projects/livespec/plan/needs-attention-hardening/handoff.md`

Your job is to keep that session honest. Watch every claimed change, every
landed PR, every release, and every dogfood run. Try to refute completion until
the `needs-attention` surface is genuinely proven on the full runtime x repo
matrix.

Primary objective:

Verify that `needs-attention` and its adjacent local/fleet surfaces behave
correctly under BOTH Claude Code and Codex across every relevant repo:

- fleet members with orchestrator surfaces;
- fleet members that are pure libraries or drivers;
- core;
- adopters, including `openbrain` and `resume`;
- repos where the correct behavior is a real attention list;
- repos where the correct behavior is an explicit fail-soft/no-op, not a
  wrapper-resolution failure or wrong-plugin invocation.

Read first:

1. `/data/projects/livespec/plan/needs-attention-hardening/handoff.md`
2. `/data/projects/livespec/plan/archive/needs-attention/live-adversarial-review-prompt.md`
3. `/data/projects/livespec/plan/archive/needs-attention/handoff.md` for
   historical context only. It is archived, stale, and not the active plan.
4. The live ledger items named by the hardening handoff, especially the new
   headline item and any epic created by the driver:

   ```sh
   source /data/projects/1password-env-wrapper/with-livespec-env.sh
   bd -C /data/projects/livespec show <item-or-epic-id>
   ```

5. The active driver pane:

   ```sh
   tmux capture-pane -t <PANE_TARGET> -p -S -80
   ```

Operating stance:

- Treat the driver session's summary as a claim, not evidence.
- Findings should be concrete blockers: wrong runtime behavior, stale plugin
  cache, missing release, matrix cell not exercised, ambiguous fail-soft,
  wrapper confusion, spec drift, plan premature-archive risk, or tests that do
  not cover the bug class.
- Do not nitpick style.
- Do not accept "works in one repo" as proof for a fleet/runtime matrix.
- Do not accept "Codex works" unless the running Codex TUI or `codex exec`
  process loaded the fixed installed plugin cache after release.
- Do not accept "Claude works" unless the project-scoped plugin setting and
  Claude runtime path were actually exercised.
- If a result is supposed to fail soft, verify the message is correct and
  actionable. A Python import error, missing wrapper, stale plugin path, or
  wrong-plugin root is a failure, not fail-soft.

Message delivery discipline:

- Poll the watched pane every 15-30 seconds while it is active.
- If the watched session waits at a picker and the answer is clear, answer it
  only after verifying the pane is idle at that picker.
- If it stalls in analysis, force a checkpoint: ask for the branch, PR, blocker,
  or live evidence in your own chat/report unless the watched pane is idle and
  ready to receive input.
- Do NOT type into a busy Claude pane. `tmux send-keys ... Enter` is not an
  atomic "send message" operation while Claude is thinking, running a command,
  waiting on a sub-agent, or otherwise not at an idle prompt. The characters can
  land in the input composer and remain unsubmitted, confusing the next operator.
- Treat a tmux message as undelivered until you capture the pane and see that it
  was submitted and processed. If the note is still visible in the input field,
  it is NOT delivered. Do not keep sending more text. Either wait for an idle
  prompt and submit exactly once, or report the required directive in the
  controlling chat for the maintainer/session owner to send.
- Prefer not to send messages into the watched session at all during adversarial
  review. Observe, verify, and report in your own session. Only send into the
  watched pane when immediate coordination is necessary, the pane is idle, and
  you can verify submission.
- For a long note to an idle pane, use a tmux buffer, paste it, send Enter once,
  then capture the pane. If the note remains at the prompt, stop and report the
  failed delivery; do not assume repeated `Enter` will fix a busy-pane state.

Useful tmux commands:

```sh
tmux list-panes -a -F '#S:#I.#P #{pane_current_path} #{pane_current_command} #{pane_title}'
tmux capture-pane -t <PANE_TARGET> -p -S -80

# Only use these send commands after capture shows the watched pane is idle at
# an input prompt. Never send into a pane that is thinking/running/waiting.
tmux set-buffer "<LONG DIRECTIVE>"
tmux paste-buffer -t <PANE_TARGET>
tmux send-keys -t <PANE_TARGET> C-m
sleep 1
tmux capture-pane -t <PANE_TARGET> -p -S -20
```

Fleet and adopter repos to include in the dogfood matrix:

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
- `thewoolleyman/openbrain` at `/data/projects/openbrain`
- `thewoolleyman/resume` at `/data/projects/resume`
- `thewoolleyman/dolt-server` at `/data/projects/dolt-server` only when host or
  Dolt evidence is involved. Leave unrelated `tmp/` files alone.

Minimum matrix to demand before accepting "dogfood-proven":

| Repo class | Example | Claude | Codex | Expected behavior |
|---|---|---|---|---|
| Core | `livespec` | required | required | real attention items or no-item result; no wrapper confusion |
| Runtime library | `livespec-runtime` | required | required | correct fail-soft/no-op; no orchestrator wrapper mis-resolution |
| Driver plugin | `livespec-driver-codex` / `livespec-driver-claude` | required | required | correct fail-soft/no-op or real items as configured |
| Beads orchestrator | `livespec-orchestrator-beads-fabro` | required | required | real beads-backed items; spec-next inlined, not pointer |
| JSONL orchestrator | `livespec-orchestrator-git-jsonl` | required | required | real JSONL-backed items or no items; spec-next inlined, not pointer |
| Console adopter/fleet app | `livespec-console-beads-fabro` | required | required | expected plan/item attention; no stale TUI cache |
| External adopter | `openbrain`, `resume` | required | required | correct project-specific behavior or explicit fail-soft |

Basic fleet sweep:

```sh
for repo in livespec livespec-runtime livespec-driver-claude \
  livespec-driver-codex livespec-orchestrator-beads-fabro \
  livespec-orchestrator-git-jsonl livespec-dev-tooling \
  livespec-console-beads-fabro openbrain resume dolt-server
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

Open PR sweep:

```sh
for repo in livespec livespec-runtime livespec-driver-claude \
  livespec-driver-codex livespec-orchestrator-beads-fabro \
  livespec-orchestrator-git-jsonl livespec-dev-tooling \
  livespec-console-beads-fabro openbrain resume
do
  echo "== $repo open PRs =="
  gh pr list -R "thewoolleyman/$repo" --state open \
    --json number,title,headRefName,isDraft,author,url |
    jq -r '.[] | "#\(.number) \(.title) [\(.headRefName)] draft=\(.isDraft) author=\(.author.login) \(.url)"'
done
```

Review loop:

1. Track the active driver pane and any sub-agent panes it spawns.
2. Watch every PR it opens and every commit that lands on `master` in touched
   repos.
3. For every implementation PR:
   - read the diff;
   - verify tests cover the named failure mode, not only a happy path;
   - verify `just check`/doctor/CI state;
   - verify release-please if a plugin repo changed;
   - verify sibling release-dispatch and bump-pin effects if a release happened;
   - verify installed plugin caches and restarted runtimes when live behavior is
     claimed.
4. For every spec/prose change:
   - verify the spec says architecture and contract, not only mechanism;
   - verify any heading changes update `tests/heading-coverage.json`;
   - require independent adversarial review before ratification.
5. For every claimed live run:
   - capture command, repo, runtime, plugin version/cache path, and output;
   - distinguish old scrollback from fresh output;
   - rerun at least suspicious cases yourself.
6. If a blocker is found, message the driver with the exact repo, PR/commit,
   violated requirement, reproducer, and required red coverage/live fixture.
7. After the driver fixes it, review the red and green evidence separately and
   rerun your fixture.

Specific attack points for this hardening track:

1. Codex-in-library wrapper confusion.
   The reported bug is `needs-attention` under Codex in `livespec-runtime`, a
   library repo that does not ship its own `needs-attention` surface. The
   correct behavior is not to chase a nonexistent local wrapper or resolve the
   wrong plugin root. Demand a live Codex proof in `livespec-runtime`.

2. Runtime asymmetry.
   Claude plugins are project-scoped; Codex plugins are host-wide. A fix that
   works in Claude can still be wrong in Codex if the Codex skill preamble,
   `$PLUGIN_ROOT` tiers, installed cache path, or TUI restart path is wrong.

3. Repo-class asymmetry.
   Core, runtime libraries, driver plugins, orchestrator plugins, console apps,
   and adopters do not all have the same `.livespec.jsonc`, work-items backend,
   wrapper paths, or plugin manifests. Verify each class.

4. "Fail soft" ambiguity.
   A real fail-soft should explain that the repo has no applicable
   needs-attention backend or no attention items. It should not be a stack trace,
   import error, missing `bd`, missing JSONL store crash, stale cache path, or
   misleading handoff.

5. Spec-next pointer regression.
   The previous review fixed `spec:next:SPECIFICATION` pointer output in both
   orchestrators. Re-test that no hardening change reintroduces it.

6. Local core skills.
   The core repo has local, unsynced `.claude/skills/needs-attention-internal`
   and `needs-attention-fleet` skills. Re-audit them under Codex as well as
   Claude. Their known seam is `internal:<signal>:<repo>` ids being rejected by
   `livespec-runtime` until `livespec-runtime-dnu` lands.

7. `internal:` id validation.
   Do not let a fix rely on invalid attention ids. `kind="internal"` is
   first-class; `validate_attention_item_id` must accept the matching prefix if
   shipped skills emit it.

8. Console TUI render path.
   `livespec-console-beads-fabro-ipi` should migrate rendering from lane-derived
   state to the `attention_item.*` stream. Verify the TUI reads the intended
   source, not only that a CLI emits plausible output.

9. Stream sequence overflow.
   `livespec-console-beads-fabro-fpo` is a signed SQLite integer overflow class.
   Check for a real 63-bit mask or equivalent, not a one-case clamp.

10. Git-jsonl skill-count drift.
    README/contracts/constraints must converge via governed spec change, not an
    ad hoc wording tweak. Verify the count and skill list across Claude and
    Codex manifests.

11. Factory blockers are separate but can block "done".
    Token TTL and worktree-pack hydration live on separate tracks, but if the
    driver claims factory-clean completion for a path still blocked by those,
    challenge the claim. Fabro PR #552 is not the token-refresh fix.

12. Premature archive risk.
    The hardening thread must stay open until the runtime x repo matrix is
    proven. If the driver tries to archive after filing an epic, merging one
    release, or closing the first work-item, block it.

Plugin/cache verification patterns:

```sh
# List installed Codex plugin state.
codex plugin list --json -m livespec
codex plugin list --json -m livespec-driver-codex
codex plugin list --json -m livespec-orchestrator-beads-fabro
codex plugin list --json -m livespec-orchestrator-git-jsonl

# Refresh and inspect an installed Codex plugin after a release.
codex plugin marketplace upgrade <marketplace>
codex plugin add <plugin>@<marketplace>
codex plugin list --json -m <marketplace>

# Grep installed caches for stale pointer behavior.
grep -R "spec:next:SPECIFICATION\|Run the spec-side next primitive" -n \
  /home/ubuntu/.codex/plugins/cache/livespec-orchestrator-beads-fabro/ \
  /home/ubuntu/.codex/plugins/cache/livespec-orchestrator-git-jsonl/ || true
```

Suggested blocker-note shape:

```text
BLOCKING hardening-review note for <repo> <PR-or-commit> / <human-readable task>:

I found a concrete failure in the runtime x repo matrix. Reproducer:
<runtime, repo, command, and short output>. Expected: <real attention item or
explicit fail-soft>. Actual: <wrong wrapper, stack trace, stale pointer, stale
cache, missing release, or untested matrix cell>.

This is blocking because the plan requires `needs-attention` to be
dogfood-proven on both Claude and Codex across fleet + adopters before this
thread can close. Please add red coverage or a live acceptance fixture for this
case, fix it, and hold closure until I rerun the reproducer.
```

Exit checklist:

- The watched session is not waiting for feedback, a picker, CI, a release, or
  a background agent.
- Every spawned sub-agent/subprocess from your review is stopped.
- Every worktree you created is removed after merge.
- Every PR you opened is merged or explicitly handed off.
- All touched primary checkouts are clean/current on `master`.
- Plugin repos that changed have a published release and `release` branch at the
  release commit.
- Installed plugin caches used by live panes contain the fixed source.
- Claude and Codex live runs are recorded for every required repo class.
- The final report says whether each matrix cell passed, failed soft correctly,
  or remains blocked with a named repo/item/PR.
- The hardening plan remains open unless the full matrix is dogfood-proven and
  the maintainer explicitly accepts archival.
````
