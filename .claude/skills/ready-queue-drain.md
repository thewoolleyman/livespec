---
name: ready-queue-drain
description: >-
  PROTOTYPE / PLACEHOLDER prompt (not an auto-discovered skill, not
  fleet-synced). Invoke by handing its ABSOLUTE PATH to a fresh repo-scoped
  session running INSIDE the fleet repo whose ready queue you want cleared.
  It drives that repo's impl-side ready work-item queue to done autonomously,
  one item at a time in rank order, through the beads/Fabro Dispatcher:
  dispatch -> land (merge PR) -> AI-approve -> accept-on-behalf -> close,
  verifying every landing and halting the line on any real failure. Temporary
  scaffolding until the needs-attention track of development work exists.
---

# Prototype — autonomous ready-queue drain (one repo, one session)

> **What this is.** A copy-pasteable operating prompt, reconciled from two live
> maintainer sessions that were each draining a fleet repo's ready queue
> (`livespec-orchestrator-beads-fabro` and `livespec-console-beads-fabro`).
> It is a **prototype/placeholder**: a single `.md` file, NOT a `<name>/SKILL.md`
> (so Claude Code does not auto-discover it), NOT part of the plugin, the spec,
> or any fleet-propagated surface. You invoke it by giving a fresh session its
> absolute path, e.g. `read <abs-path> and follow it against THIS repo. Start now.`
> It is repo-agnostic — it derives the target repo from the session's cwd.
> Retire it once the needs-attention development track lands a real surface.

You are running inside ONE fleet-member repo (your cwd is its primary
checkout). Your job: **drive every ready impl-side work-item to `done`**,
autonomously, in rank order, one at a time — dispatch it through the
Dispatcher/Fabro factory, land its PR, let the AI acceptance pass run, accept
it on the maintainer's behalf, and close it. Verify each landing for real, and
**halt the whole line** the moment one item fails or blocks.

You do **not** hand-code anything. The factory (Dispatcher → Fabro) writes the
code, gated by the janitor (`just check` + `/livespec:doctor`). You are the
operator driving the loop and confirming outcomes.

---

## 0. One-time setup (do this before the loop)

Resolve the repo, the installed factory binaries, and the credential wrapper.

```bash
# The target repo = this session's primary checkout.
REPO="$(git rev-parse --show-toplevel)"

# The orchestrator plugin is installed once per host; resolve the NEWEST cache
# build (the sha in the path changes with every plugin release — never hard-code it).
# Use `command ls` (or `find`) — a plain `ls` may be shell-aliased (e.g. to lsd),
# which decorates the output and corrupts the captured path.
CACHE=/home/ubuntu/.claude/plugins/cache/livespec-orchestrator-beads-fabro/livespec-orchestrator-beads-fabro
BIN="$(find "$CACHE" -maxdepth 3 -type d -name bin -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)"
DISP="$BIN/dispatcher.py"       # the factory engine (admit -> Fabro -> verify -> merge -> accept)
ORCH="$BIN/orchestrate.py"      # plan enumeration + the human-delegable policy VALVES

# The credential wrapper injects the tenant BEADS_DOLT_PASSWORD + the GitHub App
# env. Authoritative source is THIS repo's `.livespec.jsonc` `credential_wrapper`;
# the fleet default is the shared 1Password wrapper below. An INDEPENDENT tenant
# uses its own `with-<project>-env.sh`.
WRAP=/data/projects/1password-env-wrapper/with-livespec-env.sh

# The Fabro engine binary. Pass it EXPLICITLY to the dispatcher (see the fabro-bin
# gotcha) — do not trust PATH resolution under the wrapper.
FABRO=/home/ubuntu/.fabro/bin/fabro
```

Sanity-confirm before looping (report and stop if any fails):

- `"$DISP"` and `"$ORCH"` exist (the plugin is installed).
- The repo is clean and on `master` (`git -C "$REPO" status --short --branch`).
- The beads tenant is reachable:
  `source "$WRAP" bd -C "$REPO" ready 2>&1 | head` returns items, not
  "no beads database found". If it errors, the backend is down — surface it,
  do not proceed.
- Secrets stay **probe-only** — `printenv NAME | wc -c`, never echo a value.

---

## 1. The drain loop

Re-enumerate the queue **every iteration** — accepting one item can unblock its
dependents, and the item you just closed leaves the queue.

### 1a. Enumerate ready items in rank order

```bash
source "$WRAP" python3 "$ORCH" plan --repo "$REPO" --json
```

This prints the ranked candidate set (rank keys like `a0`, `a1`, … — the
fractional rank IS the sole drain order, the same order `next` advertises). If
the ready set is **empty**, the queue is drained — print the final tally and
stop. Otherwise take the **top-ranked** ready item; call its id `$ID`. Note that
work-item id FORMAT is repo-specific (`bd-ib-<slug>` in one repo,
`<repo>-<slug>` in another) — always read ids from the ledger, never assume a shape.

### 1b. Clear the admission gate if the item is held

Autonomous mode only auto-admits items whose effective **admission policy** is
`auto`. An item with `manual` (or no) admission policy is **held at the gate** —
even in autonomous mode. Authorize it through the **sanctioned valve** (never by
hand-writing a beads `admission:*` label):

```bash
source "$WRAP" python3 "$ORCH" run --repo "$REPO" --action "set-admission:$ID:auto" --json
```

### 1c. Dispatch the item (one at a time, sequential)

Factory dispatch is **strictly sequential** — one Fabro run at a time; the
`--network host` sandboxes collide if parallelized. Hence `--budget 1
--parallel 1`. Launch it as a **background** Bash task (a full run is long:
admit → Fabro Red→Green → `just check` verify → merge PR → AI-accept) and
**wait for the completion notification — do NOT poll it**.

```bash
LOG="$(mktemp -p "${TMPDIR:-/tmp}" drain-$ID-XXXX.log)"
python3 "$DISP" loop \
  --repo "$REPO" \
  --budget 1 --parallel 1 \
  --mode autonomous \
  --item "$ID" \
  --fabro-bin "$FABRO" \
  --json >"$LOG" 2>&1
echo "log: $LOG"
```

Notes:
- **`--mode autonomous`, always.** With `--item` named, `shadow` and
  `autonomous` select the SAME item (the "requested" branch returns before the
  mode check). But if you ever drop `--item`, `shadow` dispatches **nothing**
  (a silent no-op) while `autonomous` drains the ready queue — so standardize on
  `autonomous` and never get bitten by the footgun.
- **You do not need to source `$WRAP` here.** The dispatcher self-heals: if the
  tenant/App creds are absent it re-execs under the credential wrapper
  (`required credential env absent; re-invoking under credential_wrapper`).
  Wrapping it is harmless (it just skips the re-exec).
- **Oversized items may not converge.** If the plan/dispatch warns
  `item-sizing … description is NNNN chars (> 1500): heavy items have exceeded
  one unattended ACP turn; consider splitting before loop-feeding`, the item is
  too big for one unattended Fabro turn. Do **not** keep re-feeding it — surface
  it for a `groom` (split into ready slices) and skip to the next item.

### 1d. Verify the REAL outcome — never trust the exit code

`exit 0` means "dispatched green," **not** "closed." Confirm all three:

```bash
# (1) the dispatcher's own JSON verdict (PR number, merge sha, per-item outcome):
tail -40 "$LOG"

# (2) the item's LIVE lane in the ledger:
source "$WRAP" bd -C "$REPO" show "$ID" 2>&1 | head -30

# (3) master actually advanced to include the merge (substitute the merge sha):
git -C "$REPO" fetch origin master -q && \
  git -C "$REPO" merge-base --is-ancestor <merge-sha> origin/master && echo "MERGED into master"
```

Branch on the item's live lane:

- **`done`** — full loop confirmed. Advance to the next item (go to 1a).
- **`acceptance`** (landed + AI-approved but parked) — this is the default
  `ai-then-human` acceptance policy: it lands and runs the AI acceptance pass but
  needs a human's final accept to close (only `ai-only` auto-closes). If the
  maintainer has authorized **accept-on-behalf for this batch**, close it via
  the accept valve, then re-verify it reached `done`:
  ```bash
  source "$WRAP" python3 "$ORCH" run --repo "$REPO" --action "accept:$ID" --json
  source "$WRAP" bd -C "$REPO" show "$ID" 2>&1 | head -5
  ```
  If accept-on-behalf is **not** authorized, stop and surface it (see §2).
- **`active` / `blocked` / failed / not-merged** — the line has hit a real
  problem. **HALT** — do not advance to the next item. Report the item, the
  `$LOG` tail, and the live lane, and stop for the maintainer.

### 1e. Report and continue

After each item, print a one-line tick: `ID → done (PR #N, merge <sha>)`. Then
re-enumerate (go to 1a). Keep going until the ready set is empty or the line
halts.

---

## 2. What to surface vs. decide yourself

- **Decide-and-inform** for everything routine: dispatch order, clearing an
  admission gate via the valve, accepting on-behalf **once the maintainer has
  authorized the batch**, skipping-and-flagging an oversized item.
- **Surface WITH a recommendation and STOP the line** only for: a genuine
  dispatch **failure/block** (Fabro couldn't land it green, or it parked at an
  in-loop human gate), the **first** accept-on-behalf decision (delegating final
  acceptance to you is the maintainer's call — ask once, then it holds for the
  batch), or an item that needs a `groom` cut (maintainer owns the slice).
- Do **not** freeze on reversible, clearly-in-intent calls.

---

## 3. Gotchas distilled (both sessions hit these)

1. **`exit 0` ≠ closed.** Always verify the live lane + master-ancestor. A green
   dispatch under `ai-then-human` lands and parks in `acceptance`; it is not done.
2. **`--mode shadow` + no `--item` = silent no-op.** Use `--mode autonomous`.
3. **`--fabro-bin` is not optional in practice.** The credential wrapper scrubs
   PATH; without an explicit `--fabro-bin` the dispatch dies "fabro engine binary
   not resolvable." Pass `/home/ubuntu/.fabro/bin/fabro`.
4. **Admission `manual` blocks even autonomous mode.** Authorize via
   `set-admission:<id>:auto` (the valve) — never hand-edit beads labels.
5. **Sequential only.** One Fabro run at a time (`--budget 1 --parallel 1`).
6. **Don't drive via `orchestrate run --action impl:<id>` for the drain.** It
   hardcodes `--mode shadow` in `build_dispatcher_argv` and had a fabro-launch
   PATH failure under the wrapper. Drive the dispatcher **directly** for the
   dispatch; use `orchestrate run --action <valve>` only for the policy valves
   (`set-admission:…`, `accept:…`, `reject:…:rework|regroom`).
7. **Never `--no-verify`; never hand-code.** The worktree→PR→rebase-merge
   discipline and the janitor gate run **factory-side** — trust them; if a hook
   or gate fails, that IS the halt signal, root-cause it, don't bypass it.
8. **Re-enumerate every iteration** — the queue shifts as items close and
   dependents unblock.

---

## 4. Provenance

Reconciled 2026-07-05 from two live `autonomous-ready-queue-drain` sessions.
Divergences found and resolved: mode (`autonomous` vs `shadow`), explicit
`--fabro-bin`, sanctioned `set-admission` valve vs. hand-written label, and
verify-the-lane vs. trust-the-exit-code. This prototype is the LEAN operating
prompt those sessions converged on. The coordinating layer that spawns a session
like this per repo and feeds it this file is the local `overseer` skill
(`.claude/skills/overseer/SKILL.md`, section "Driving per-repo autonomous
ready-queue drains").
