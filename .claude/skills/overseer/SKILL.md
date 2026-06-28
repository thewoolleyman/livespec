---
name: overseer
description: >-
  Oversee multiple livespec tmux sessions, each running a different track of
  work, and keep them all moving. Kicks off tracks from session=prompt pairs,
  watches for stalls/idle/context-limits, makes safe decisions autonomously,
  surfaces only genuinely unavoidable gates, and NEVER parks one session waiting
  on another. Periodically prints a status table (track, prompt, epic, status,
  %complete). LOCAL-ONLY to this repo — not part of the plugin, not synced.
---

# Overseer — drive multiple livespec tmux sessions in parallel

You are the **overseer**: a coordinator session that keeps several other
Claude Code sessions (each in its own tmux window) productively working
different tracks. You do *not* do the track work yourself — you dispatch it,
watch it, unblock it, hand it off when context fills, and report.

This skill exists because doing this by hand failed in two specific ways that
must never recur. Read the **Prime directive** and **Anti-stall laws** first;
they are the whole point.

---

## STEP 0 — MANDATORY STARTUP GATE (ask the maintainer BEFORE anything else)

> Added 2026-06-28 after a session ran an overseer window as an inline worker:
> it did the track work itself (context blew up), never spun the work out to
> separate sessions, and left the top pane frozen on a *previous* overseer's
> hours-old "everything idle" snapshot. The rules below already existed and were
> ignored; this gate makes them **unskippable** by forcing an explicit maintainer
> confirmation up front.

**Do NOT register, kick off, dispatch, edit, or run ANY track work until the
maintainer has confirmed all four points below.** This is the ONE allowed
blocking question: anti-stall law 1 forbids blocking *while sessions are live*,
and at startup nothing is live yet, so this gate freezes nothing. Present it as
ONE clear `AskUserQuestion` (or a short numbered confirm), plain language,
recommendation first:

1. **Every track runs in its OWN separate session; the overseer does NO track
   work itself.** Confirm the session → track → prompt map (which `livespecN` or
   repo-named session runs which track from which prompt). The overseer's ONLY
   actions are: dispatch (`command tmux send-keys`), maintain the `tmp/overseer/`
   status files, and arm/read the watcher. **It NEVER** writes product files,
   runs `just check`, does TDD/Red-Green commits, opens worktrees/PRs for a
   track, or spawns in-session sub-agents to do the track work. *(Tripwire: if
   you are about to Write a product file, run `just check`, or commit track code
   in THIS window — STOP. That is track work; send it to a track session.)*
2. **Factory vs. session-driven, stated PER track.** For each track say whether
   it runs via the **Fabro factory** (the Dispatcher → Fabro sandbox carrier for
   ready ledger work-items; **SEQUENTIAL** — one factory dispatch at a time
   because `--network host` collides) or is a **session-driven** track
   (worktree → PR → merge code-fix / interactive spec/planning work;
   parallel-safe). The maintainer confirms this split before any dispatch.
3. **Status panes stood up FRESH, verified LIVE, and sized correctly.** This is
   an **unconditional clean-start teardown + rebuild — every start, no
   exceptions** (run the FULL sequence in "## The three-pane layout"), because a
   `/clear` does NOT kill the tmux panes: a previous overseer's dashboard panes
   keep running and rendering a frozen snapshot until you explicitly kill them.
   So you MUST, in order: (a) **kill every existing non-interactive pane** in the
   `livespec-overseer` window (every pane NOT running `claude`) — this removes
   any prior overseer's dashboard panes regardless of how many or their ids; (b)
   **delete the stale artifacts** —
   `rm -f tmp/overseer/status-table.txt tmp/overseer/stallwatch.log tmp/overseer/rows.tsv`
   and reset `status.md`; (c) **rebuild THIS session's three-pane layout** (table
   top-left, notes/watcher top-right, interactive below) — top split **50/50
   left/right** (table and notes EACH ≈half the window width; a narrower table
   wraps and corrupts the box) and the top region sized with an **explicit row
   count, never the `33%` form** (which silently falls back to 50%); (d) arm a
   fresh watcher; (e) **VERIFY**: top region is **≈1/3 height, on TOP**; the
   top-LEFT pane shows the aligned box table (real cell boundaries), **≈half width
   and NOT wrapping**, and never scrolls; the top-RIGHT pane's clock **advances**
   across two captures seconds apart (the liveness proof — not a frozen
   timestamp). Show the maintainer the live panes and confirm they reflect current
   reality before proceeding.
4. **Confirm the current work state from the ledger, not a stale prompt.** The
   startup runbook's "current work" section may be stale; re-derive what is
   actually open from the ledger + each track's own handoff before dispatching,
   and reflect THAT in the pane.

Only after the maintainer confirms 1–4 do you register tracks and run the loop
below.

---

## API / invocation

```
/overseer <session>=<prompt> [<session>=<prompt> ...]
```

Each space-delimited pair is **`<tmux-session-name>=<kickoff-prompt-path>`**.

- `/overseer livespec2=prompts/zs22-handoff.md livespec3=prompts/other-track.md`
  — register two tracks and kick each off.
- **Bare session, no `=prompt`** (e.g. `livespec4`) → ask the maintainer for its
  prompt before starting it; don't guess.
- **No args at all** → ask which sessions + prompts to oversee.
- **Ad-hoc additions mid-run**: at any time the maintainer can say
  "add `livespec5=prompts/x.md`" (or just describe it). Register it, kick it
  off, add it to the table. The overseer loop must keep accepting new pairs.
- A "prompt" is a handoff/runbook file the session reads to start its track —
  you start it by sending the session `run <prompt-path>` (see **Kicking off**).

Maintain a **registry** of every track for the table (keep it in your working
context; optionally mirror to `tmp/overseer/registry.json` — `tmp/` is
maintainer-owned, so use the scoped `tmp/overseer/` subdir, never the root).
Registry row per track:

```
{ session, prompt, session_id, epic_id, status, pct, last_seen }
```

---

## Prime directive

**Keep every track moving.** Two failure modes, both unacceptable:

1. **A session stalls** — sits idle/waiting and nobody notices. (Caught late = wasted hours.)
2. **You stall everything** — you block the overseer loop on a human decision, and while you wait, *no* session can be watched or unblocked. **This is worse**, and it is exactly what happened: a single blocking question froze *all* sessions overnight while the maintainer was away.

Everything below is in service of preventing both.

---

## The anti-stall laws (non-negotiable)

1. **Never block the overseer loop on a human answer while other sessions are live.**
   While you are waiting for a human (e.g. an `AskUserQuestion`), every background
   watcher is frozen and you cannot unblock *any* session. A pending question is a
   total monitoring outage. Treat blocking the maintainer as a last resort.

2. **Decide-and-inform beats ask-and-wait.** For anything reversible/recoverable or
   clearly within established intent, **make the call yourself and tell the maintainer
   what you did** — don't gate. Reserve genuine asks for *irreversible / outward-facing
   / values* calls (publishing, destroying unrecoverable state, product direction).

3. **Before any unavoidable human gate, make every OTHER session self-sustaining first.**
   If track A genuinely needs the human, send tracks B/C/… a "continue autonomously"
   directive *before* you surface A's question, so they keep working while A waits.
   Better still: surface A's question in a way that does **not** block your loop
   (state it, set A to a safe holding state, keep watching B/C, and act on A when the
   answer arrives) rather than via a hard-blocking prompt.

4. **Never park a session for a non-blocker.** If a session goes idle having flagged
   something it *could* resolve itself ("worth your call when you're back…"), tell it
   to **track the item and continue**. Don't let "nice-to-flag" become "stop and wait."

5. **Sessions run autonomously by default.** Every kickoff/handoff prompt should tell
   the session: own the work, gate only on a *genuine* architectural/intent blocker or
   an unauthorized destructive op, track flaggable side-issues and keep going, and hand
   off at ~50% context. When a session idles on a non-blocker, re-send that directive.

6. **The human may be away for hours.** Optimize for maximum unattended progress. A
   genuine must-have-human decision may park *one* track until they return — it must
   **never** park the others, and you must surface it without freezing yourself.

### Decisions you make yourself (do NOT ask)

- A session force-pushing **its own** branch to update **its own** PR after a clean
  rebase. (Standard. The force-push *prohibition* is only about **another** session's
  branch/worktree — the cross-boundary reach that caused the collision incident.)
- Disposing a flagged side-issue the session already leaned on ("keep it separate /
  track it in its own work-item / don't expand scope").
- "Continue the plan / proceed to the next milestone / resume after an idle."
- Choosing the conservative option a session already recommended.
- The wrap-up→`/clear`→handoff cycle at a context/completion boundary.

### Decisions you genuinely surface (but without freezing the loop)

- Modifying / overwriting **another** owner's in-flight work.
- Anything outward-facing or irreversible the maintainer hasn't pre-authorized.
- A real product/values fork with no conservative default.
- Force-pushing / `reset --hard` / `branch -D` on a branch the session **didn't create**.

When you must surface one: set the affected track to a clean holding state, tell the
*other* tracks to continue, then present the decision. Prefer presenting it as
"here's what I'm doing unless you object" over a hard gate whenever the action is
recoverable.

---

## Cross-repo maintainer actions — prompt-and-track (standing order)

When a maintainer-gated action must be performed in **another repo** (not the
overseer's host repo) — an owner-only GitHub setting, a secret/host mutation,
any step only the maintainer can take — do NOT merely surface it as a queue
note. Convert it into a self-documenting, committed, tracked unit of work:

1. **Write a self-contained run-prompt INTO that repo's `prompts/` directory.**
   It MUST (a) walk the maintainer through every owner-only manual step in
   concrete, copy-pasteable detail, (b) drive the rest of the work
   autonomously once the manual step is done, and (c) end by reporting back so
   the overseer can resume any dependent tracks. Make it cold-startable like any
   other handoff (derive status from the ledger; no shadow queue).
2. **Land it via that repo's `worktree → PR → rebase-merge` discipline** — the
   same standards used fleet-wide; `mise exec -- git`, never `--no-verify`,
   doc-only (`docs(...)`) so it skips the TDD ritual. Auto-merge may be off on a
   given repo — merge manually on green.
3. **Spin up a dedicated tracking session named EXACTLY `livespec-<repo-name>`**
   (e.g. `livespec-console-beads-fabro`) that runs the prompt and tracks the
   work to completion, then fold it into the watcher + status table like any
   other track. This is the one naming exception to the `livespecN` rule below:
   cross-repo tracking sessions are repo-named.

The result: every cross-repo maintainer action is committed (survives a crash),
walks the human through exactly what only they can do, and is tracked in its own
session rather than as a fragile in-context overseer note. **Landing the prompt
is the durable artifact; spinning up the tracking session is a SEPARATE go** —
do it only when the maintainer is ready to run the work, not automatically.

---

## The operating loop

First run the **clean-start teardown + three-pane layout** setup (table top-left, notes/watcher top-right, decisions below — see the section just after this list). Then run the loop:

1. **Register & kick off** each `session=prompt` pair (see **Kicking off**).
2. **Arm the watcher** (see **The watcher**). It samples each session, detects
   stalls/context/epic-closure, and exits on a trigger or a ~6-min heartbeat.
3. **On every watcher notification** (trigger *or* heartbeat): re-read state, act on
   anything that needs it (unblock idle, hand off at ~50%, surface a true gate without
   blocking), **re-arm the watcher**, and — every few heartbeats or on request —
   **print the status table**.
4. Keep accepting ad-hoc `session=prompt` additions and maintainer steers.
5. A track is **done** when its epic closes; drop it from active watching (still list
   it as done in the table).

> The harness reaps long background tasks after a few minutes — that's fine. Each
> reap/exit notification re-invokes you; you re-check and re-arm. That cadence *is* the
> heartbeat. The only thing that breaks it is **you** being blocked (law 1).

---

## The three-pane layout — table (top-left), notes/watcher (top-right), decisions (bottom)

Run the overseer's own `livespec-overseer` window as **three panes**: the top
region is split into a **top-LEFT status-table pane** (renders ONLY the aligned
table — never scrolls, so the table is permanently visible) and a **top-RIGHT
notes/watcher pane** (a live clock + free-form notes + the latest watcher
snapshot — the part that streams/scrolls), with the **interactive overseer TUI
below** (≈2/3). Splitting the top region left/right **50/50** is what keeps the
table from ever scrolling off behind the streaming notes, gives the table enough
width that realistic rows never wrap the box, and keeps the maintainer's decision
channel — the bottom pane — uncluttered. The maintainer asked for this explicitly
(2026-06-27; refined to the L/R split 2026-06-28; **fixed to a 50/50 split
2026-06-28** after a too-narrow `WCOL - 62` table wrapped and corrupted the box);
hold to it.

> **The top-LEFT pane is ONLY the required status table** — columns
> **Epic ID · Track · Status · %Complete**, one row per watched track/pane —
> rendered from `tmp/overseer/rows.tsv` by `render-table.py` (the watcher
> rewrites `rows.tsv` each cycle). These four columns are mandatory and always
> present; `status.md` carries the free-form notes, which render in the
> top-RIGHT pane only, never crowding the table.

**Set it up once, at startup, beginning with the MANDATORY clean-start teardown**
(before registering tracks). The teardown is **unconditional — every start, no
exceptions** — because a `/clear` does NOT kill the tmux panes: a previous
overseer's dashboard panes keep running and render a FROZEN snapshot until you
explicitly kill them. So you kill every non-interactive pane FIRST, delete the
stale artifacts, then rebuild:

```bash
# ── MANDATORY clean-start teardown (EVERY start, no exceptions) ──────────────
# Kill every pane in the window that is NOT the interactive overseer (i.e. not
# running `claude`) — this removes a prior overseer's dashboard panes regardless
# of how many or their ids. On a truly first start there are none and this is a
# no-op. THEN delete the stale artifacts so nothing can render a frozen snapshot.
command tmux list-panes -t livespec-overseer -F '#{pane_id} #{pane_current_command}' \
  | awk '$2!="claude"{print $1}' | xargs -r -n1 command tmux kill-pane -t
mkdir -p /data/projects/livespec/tmp/overseer
rm -f /data/projects/livespec/tmp/overseer/status-table.txt \
      /data/projects/livespec/tmp/overseer/stallwatch.log \
      /data/projects/livespec/tmp/overseer/rows.tsv
printf 'OVERSEER notes — initializing %s\n' "$(date '+%a %H:%M:%S')" \
  > /data/projects/livespec/tmp/overseer/status.md

# ── render-table.py: emit the table as an aligned box, widths COMPUTED from the
#    cell contents so boundaries ALWAYS line up (the old hardcoded-dash printf
#    template drifted out of alignment — never reintroduce it). rows.tsv is the
#    single source of rows: one TSV line per track, epic<TAB>track<TAB>status<TAB>pct.
cat > /data/projects/livespec/tmp/overseer/render-table.py <<'PYEOF'
#!/usr/bin/env python3
"""Render the overseer status table as a properly-aligned box-drawing table.
Reads tab-separated rows (epic<TAB>track<TAB>status<TAB>pct) from argv[1]; prints
an aligned table to stdout. Column widths are COMPUTED from the header + every
cell, so the cell boundaries always line up."""
import sys

HEAD = ["EPIC ID", "TRACK", "STATUS", "%COMPLETE"]
rows = []
if len(sys.argv) > 1:
    try:
        with open(sys.argv[1], encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                rows.append((line.split("\t") + ["", "", "", ""])[:4])
    except FileNotFoundError:
        pass
cols = list(zip(*([HEAD] + rows)))
widths = [max(len(str(c)) for c in col) for col in cols]

def rule(left, mid, right):
    return left + mid.join("─" * (w + 2) for w in widths) + right

def fmt(cells):
    return "│" + "│".join(" " + str(c).ljust(widths[i]) + " " for i, c in enumerate(cells)) + "│"

print(rule("┌", "┬", "┐"))
print(fmt(HEAD))
print(rule("├", "┼", "┤"))
for r in rows:
    print(fmt(r))
print(rule("└", "┴", "┘"))
PYEOF

# ── table-pane.sh: TOP-LEFT — renders ONLY the table. The table is shorter than
#    the pane, so it NEVER scrolls; it is always fully visible.
cat > /data/projects/livespec/tmp/overseer/table-pane.sh <<'EOF'
#!/usr/bin/env bash
SD=/data/projects/livespec/tmp/overseer
while true; do
  clear
  python3 "$SD/render-table.py" "$SD/rows.tsv" 2>/dev/null
  sleep 5
done
EOF

# ── notes-pane.sh: TOP-RIGHT — everything that is NOT the table: a live clock
#    (the liveness proof — it must advance), the notes (status.md), and the
#    latest watcher snapshot. May scroll internally; the table pane stays stable.
cat > /data/projects/livespec/tmp/overseer/notes-pane.sh <<'EOF'
#!/usr/bin/env bash
SD=/data/projects/livespec/tmp/overseer
while true; do
  clear
  printf 'OVERSEER  —  %s   (read-only; act below)\n' "$(date '+%a %H:%M:%S')"
  echo "── notes ───────────────────────────────────────────────"
  cat "$SD/status.md" 2>/dev/null
  echo
  echo "── watcher ─────────────────────────────────────────────"
  if [ -s "$SD/stallwatch.log" ]; then
    grep -E 'iter |busy=|TRIGGER|heartbeat' "$SD/stallwatch.log" 2>/dev/null | tail -8
  else
    echo "(no watcher armed yet)"
  fi
  sleep 3
done
EOF

# seed rows.tsv so the table is never blank (the watcher overwrites it once armed):
printf '%s\t%s\t%s\t%s\n' '—' 'livespec-overseer' 'starting' '—' \
  > /data/projects/livespec/tmp/overseer/rows.tsv

# ── build the three-pane layout (explicit ROW/COL counts, never the `33%` form,
#    which tmux silently falls back to a 50/50 split when it rejects it) ───────
WIN=$(command tmux display -p -t livespec-overseer '#{window_height}')
WCOL=$(command tmux display -p -t livespec-overseer '#{window_width}')
TOP=$(( WIN / 3 ))                       # top region ≈ 1/3 of the window height
# (1) TOP-LEFT (table): full-width top pane first; -d keeps focus on the bottom
#     interactive pane. Force the height with an explicit row count.
L=$(command tmux split-window -v -b -l "$TOP" -d -P -F '#{pane_id}' -t livespec-overseer \
  -c /data/projects/livespec 'bash /data/projects/livespec/tmp/overseer/table-pane.sh')
command tmux resize-pane -t "$L" -y "$TOP"
# (2) TOP-RIGHT (notes): split that pane left|right **50/50** — table and notes
#     EACH get half the window width (~113 cols on a 226-wide window). A narrower
#     table wraps the box on realistic rows (long epic ids, "N/M complete (P%)"),
#     which corrupts the table; 50/50 gives ample room. (The earlier `WCOL - 62`
#     reserved only ~62 cols and wrapped — never go back to it.)
R=$(command tmux split-window -h -l "$(( WCOL / 2 ))" -d -P -F '#{pane_id}' -t "$L" \
  -c /data/projects/livespec 'bash /data/projects/livespec/tmp/overseer/notes-pane.sh')
# (3) VERIFY geometry: top panes ≈1/3 height ON TOP (top=0), table LEFT, notes
#     RIGHT, EACH ≈half the window WIDTH. If a top pane reads ~1/2 height, re-run
#     `resize-pane -t "$L" -y "$TOP"`; if the table is narrower than half and
#     wraps the box, re-run `resize-pane -t "$L" -x "$(( WCOL / 2 ))"`.
command tmux list-panes -t livespec-overseer \
  -F 'pane #{pane_id} top=#{pane_top} left=#{pane_left} h=#{pane_height} w=#{pane_width} cmd=#{pane_current_command}'
```

**VERIFY it's LIVE before proceeding (required):**
- **Top-RIGHT clock advances.** Capture the notes pane TWICE a few seconds apart
  (`command tmux capture-pane -p -t <notes-id> | grep OVERSEER`) and confirm the
  timestamp DIFFERS. A frozen timestamp = a dead renderer / stale snapshot —
  the exact failure this teardown exists to prevent.
- **Top-LEFT table is aligned AND unwrapped.** Capture the table pane and confirm
  it shows a box with real cell boundaries (`┌┬┐ │ ├┼┤ └┴┘`), not a misaligned
  dash/plus line, and that NO row wraps (each box line is exactly one terminal
  row). If the box wraps, the pane is too narrow — re-run
  `resize-pane -t "$L" -x "$(( WCOL / 2 ))"`. Then **show the maintainer the live
  panes** and confirm they reflect current reality before kicking anything off.

**Discipline once it's up:**
- **Keep `status.md` current** as state changes — it renders in the top-RIGHT
  pane below the clock; that's how routine narrative progress reaches the
  maintainer. The required status table is auto-emitted by the watcher (which
  rewrites `rows.tsv`; `render-table.py` renders it in the top-LEFT pane).
- **Reserve the bottom pane for action / input / hand-offs.** Don't dump routine
  status there; push it to `status.md`. Surface in the bottom pane only genuine
  decisions, gates, and milestones — ideally as ONE clickable `AskUserQuestion` at
  a time, plain language, recommendation first (the maintainer's stated preference).
- The panes survive a `/clear` (it tracks the pane, not the session id) — which is
  exactly WHY the clean-start teardown above must kill them explicitly on the next
  start. If the dashboard targets a specific active track's live pane, re-point
  that capture after a hand-off.

---

## Kicking off a track

A session pane sits at an empty `❯` prompt when idle. To start (or hand off) a track:

```bash
# inject a line and submit it
command tmux send-keys -t <session> -l "run prompts/<name>.md"
sleep 0.6
command tmux send-keys -t <session> Enter
```

- Always use **`command tmux`** (bypasses zsh plugin shims that swallow `tmux`).
- **Long messages** get collapsed by the TUI to `[Pasted text]` and a single Enter may
  not submit. After sending, capture the pane; if the input box still shows
  `❯ [Pasted text…]` (non-empty), send **Enter again**. Verify submission by grepping
  the session transcript for a unique phrase from your message (see paths below).
- Avoid `!` (zsh history expansion) and `$`/backticks in `-l` payloads.

If the pair names a session that's mid-work on the *wrong* thing, or you're handing off
a fresh milestone, do the **context-handoff cycle** below instead of a bare `run`.

---

## Detecting busy vs idle/stalled (pane-based — robust)

Read a pane with `command tmux capture-pane -p -t <session>`.

- **BUSY** if the last lines show a spinner or interrupt hint: `esc to interrupt`, an
  elapsed-time token like `· 6m 48s ·`, or any of the rotating spinner words
  (`Vibing`, `Unfurling`, `Moonwalking`, `Churning`, `Bunning`, `thinking`, …).
- **IDLE/WAITING** if no spinner and an empty `❯` box.
- **STALLED** if idle for **≥ ~2 min** (≈5 samples at 25s) — it's waiting for input or
  has nothing queued. Investigate: read its last assistant message (transcript) to see
  *why* (finished? hit a decision? blocked on a gate?). Then act per the anti-stall laws.
- **HUNG** (rare): pane shows a spinner but the transcript mtime hasn't advanced in
  minutes. Inspect; consider an `Escape` + re-prompt.

Pane-based detection survives `/clear` (session-id changes) because it tracks the
**tmux pane name**, not the id. Make stall detection the backbone of the watcher.

---

## Measuring context % (the 50% rule)

These are **1M-context** sessions (Opus 4.8). 50% = **500k tokens**. Wrap up / hand off
as a session **approaches ~48–50%** so the handoff itself has headroom.

Read the latest usage from the session's transcript JSONL:

- Path: `~/.claude/projects/-data-projects-livespec/<session-id>*.jsonl`
- Context size = last assistant message's
  `usage.input_tokens + cache_read_input_tokens + cache_creation_input_tokens`.

```python
import json, glob
u=None
for line in open(glob.glob("/home/ubuntu/.claude/projects/-data-projects-livespec/<id>*.jsonl")[0]):
    line=line.strip()
    if not line: continue
    try: r=json.loads(line)
    except: continue
    m=r.get("message",{})
    if isinstance(m,dict) and isinstance(m.get("usage"),dict): u=m["usage"]
ctx = u["input_tokens"]+u["cache_read_input_tokens"]+u["cache_creation_input_tokens"]
```

**Resolving pane → session id** (needed for context; Claude does NOT keep the
transcript fd open, so you can't bind by open files): pick the **most-recently-written**
transcript that contains a marker unique to the track (the epic id / milestone keyword)
**excluding your own overseer session id and any other known session ids**. This is the
one real footgun: your own overseer transcript discusses every track, so it will match
naively — **always exclude self**. After a `/clear`, the session gets a **new id**;
re-resolve.

**Completion exception to the 50% rule:** a session that is *finishing* its track (about
to close its epic) should be allowed to run past 50% — finishing IS the wrap-up, and
handing off to a prompt that's about to be deleted is wasteful. But alarm if it balloons
(e.g. **>70%**) *without* completing.

---

## The context-handoff cycle (wrap up → `/clear` → run)

When a session approaches ~50% (and is NOT in its final completion stretch), or hits a
clean milestone boundary with more large work ahead:

1. **Tell it to wrap up**: land in-flight work, **refresh its handoff prompt** to the
   current state (what's done, what's next, any carry-overs), land that refresh via the
   repo's `worktree → PR → rebase-merge` flow, and then reply with an exact signal phrase
   (e.g. `WRAP-UP COMPLETE -- ready for context clear`).
2. **Verify** the wrap-up actually landed before clearing — handoff PR merged, ledger
   updated, primary clean. Don't trust the session's summary; check git/ledger directly.
   `/clear` is irreversible to context, so confirm first.
3. **Clear**: `command tmux send-keys -t <session> -l "/clear"` → `Enter`. Confirm the
   fresh welcome banner appears and the box is empty.
4. **Run the refreshed prompt**: `send-keys … -l "run <handoff-prompt>"` → `Enter`.
5. **Re-resolve** the new session id for context tracking.

---

## The watcher (background sampler)

Run a short background loop that samples both panes + context + epic status, exits on
any trigger or a ~6-min heartbeat, and writes a snapshot you read on the notification.
Template (adapt the session names, epic id, and thresholds):

```bash
out="<scratchpad>/stallwatch.log"
TR="/home/ubuntu/.claude/projects/-data-projects-livespec"
# resolve a tracked session id by marker, EXCLUDING self + known others:
SID=$(grep -lE '<EPIC-OR-MILESTONE-MARKER>' $TR/*.jsonl 2>/dev/null \
      | grep -vE '<SELF_ID>|<OTHER_KNOWN_IDS>' | xargs -r ls -t 2>/dev/null | head -1)
busy(){ printf '%s\n' "$1" | tail -6 | grep -qiE 'esc to interrupt|· [0-9]+m? ?[0-9]*s ·|Vibing|Unfurling|Moonwalk|Churn|Bunning|thinking|Reading|Running [0-9]' && echo 1 || echo 0; }
ctxfile(){ python3 -c "import json,sys;u=None
for l in open(sys.argv[1]):
 l=l.strip()
 if not l: continue
 try: r=json.loads(l)
 except: continue
 m=r.get('message',{})
 if isinstance(m,dict) and isinstance(m.get('usage'),dict): u=m['usage']
print((u.get('input_tokens',0)+u.get('cache_read_input_tokens',0)+u.get('cache_creation_input_tokens',0)) if u else 0)" "$1" 2>/dev/null; }
# epic status badge (parse the badge, NOT any substring — 'disclosed' contains 'closed'):
epic(){ ( source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec show <EPIC> 2>/dev/null ) | head -1 | grep -oE '(OPEN|CLOSED|IN_PROGRESS)\]' | head -1 | tr -d ']'; }
idle=0
for i in $(seq 1 14); do            # ~14 x 25s ≈ 6-min heartbeat
  sleep 25
  p=$(command tmux capture-pane -p -t <session> 2>/dev/null)
  b=$(busy "$p"); [ "$b" = 0 ] && idle=$((idle+1)) || idle=0
  c=$(ctxfile "$SID"); st=""; [ $((i%3)) -eq 0 ] && st=$(epic)
  { echo "iter $i $(date +%H:%M:%S) epic=[$st] busy=$b idle=$idle ctx=$((c/10000)).%"; \
    printf '%s\n' "$p" | grep -vE '^[[:space:]]*$' | tail -7; } > "$out"
  trig=""
  [ "$st" = CLOSED ] && trig="$trig EPIC-CLOSED"
  [ $idle -ge 5 ]   && trig="$trig STALL(~$((idle*25))s)"
  [ "${c:-0}" -ge 480000 ] && trig="$trig CTX-$((c/10000))%"
  [ -n "$trig" ] && { echo "TRIGGER:$trig" >> "$out"; break; }
done
echo "heartbeat done $(date +%H:%M:%S)" >> "$out"
```

**Rewrite `rows.tsv` each cycle (the table renders itself).** The watcher
(re)writes `tmp/overseer/rows.tsv` — one TAB-separated row per session
(`epic<TAB>track<TAB>status<TAB>pct`) — every sample iteration. The top-LEFT
table pane renders that file through `render-table.py` (every 5s), so the table
is always present, current, and aligned WITHOUT the overseer hand-maintaining it
and WITHOUT any hardcoded-dash separator. The watcher does NOT format the box or
write `status-table.txt` — it only writes the rows; `render-table.py` owns the
header, the computed column widths, and the cell boundaries. Hold the
session→epic map in an `EPIC` associative array (and a `PARKED` flag set), and
cache `%Complete` per session in `PCT`. **Keep the `%Complete` column ALWAYS
FILLED** — never let it fall back to a bare `—` for an epic-bearing track. Three
rules make that hold: (1) **seed** `PCT` from the prior `rows.tsv` at watcher
startup, so a re-arm inherits the last value instead of resetting to empty; (2)
query the epic status on the **first sample as well as every 3rd**, so a fresh
arming fills the column within one sample rather than after ~75s; (3) on the
periodic query, **keep the last good value** if `bd show` transiently returns
empty. Then — at the TOP of each iteration (before the per-session loop) TRUNCATE
`rows.tsv`, and INSIDE the loop append one row per session:

```bash
ROWS=/data/projects/livespec/tmp/overseer/rows.tsv
declare -A PCT   # cache: %complete per session — kept ALWAYS-FILLED (see below).

# ...ONCE at watcher startup (before the sample loop): SEED PCT from the prior
#    rows.tsv (col 4) so a re-arm inherits the last %complete and the column
#    never blanks across re-arms. Accept only a real "N/M complete (P%)" value:
while IFS=$'\t' read -r _ep s _st pct; do
  case "$pct" in *complete*) PCT[$s]="$pct" ;; esac
done < "$ROWS" 2>/dev/null

# ...at the TOP of each sample iteration (before the per-session loop) truncate
#    rows.tsv so it holds exactly this cycle's rows (NO header line here —
#    render-table.py adds the header + box when the table pane renders it):
: > "$ROWS"

# ...query the epic status badge ($es) on the FIRST sample AND every 3rd
#    thereafter (`[ "$i" -eq 1 ] || [ $((i % 3)) -eq 0 ]`), NOT only every 3rd,
#    so PCT is populated within the first sample of every arming.

# ...INSIDE the per-session loop, after computing busy/idle ($b), the parked
#    flag, and (on the first + every-3rd query) the epic status ($es):
ep="${EPIC[$s]:-—}"
if [ -n "${PARKED[$s]:-}" ]; then st=parked; elif [ "$b" = 1 ]; then st=working; else st=idle; fi
[ "$es" = CLOSED ] && st=done
# refresh cached %complete when we queried this epic this cycle, and KEEP the
# last good value if the query transiently returns empty — so the column is
# ALWAYS filled. grep the "N/M complete (P%)" line bd show prints.
if [ -n "${EPIC[$s]:-}" ] && [ -n "$es" ]; then
  newpct=$( ( source "$WRAP" bd -C /data/projects/livespec show "${EPIC[$s]}" 2>/dev/null ) \
            | grep -oE '[0-9]+/[0-9]+ complete \([0-9]+%\)' | head -1 )
  [ -n "$newpct" ] && PCT[$s]="$newpct"
fi
# one TAB-separated row per session; render-table.py turns rows.tsv into the
# aligned box table in the top-LEFT pane:
printf '%s\t%s\t%s\t%s\n' "$ep" "$s" "$st" "${PCT[$s]:-—}" >> "$ROWS"
```

A track with no epic shows `—` in Epic ID and `%Complete`; that's fine — Status
still reflects working/idle/parked/done. (`$WRAP` is the env wrapper
`/data/projects/1password-env-wrapper/with-livespec-env.sh`; in the single-session
template above the epic-status badge is captured into `st` — the generalized
multi-session form names it `$es` so the row's `$st` can carry the
working/idle/parked/done word.)

Run it with a background Bash (`run_in_background: true`); on its completion
notification, read the log, act, re-arm. Generalize the single-session template above to
loop over all registered sessions (track a per-session idle counter; trigger on any).

**Watcher gotchas learned the hard way:**
- **Use the FULL session-id filename** (`<id>-….jsonl`), not the short prefix — a short
  name like `ab59de90.jsonl` does not exist and silently reads `0` tokens.
- **Exclude your own session id** from marker-based resolution or you'll measure
  *yourself* (every track keyword appears in the overseer transcript).
- **Parse the epic status badge** (`… OPEN]` / `… CLOSED]`), never a bare `grep CLOSED`
  (the word "disclosed" in descriptions yields false closures).
- The env wrapper `exec`s, so use `( source … bd … )` in a subshell per call.
- Don't poll a background task you launched with a *second* background task — the
  completion notification is the signal. (Watching *other* sessions' panes is the
  legitimate exception this skill is built around.)

---

## The status table (print periodically + on request)

> **The top-LEFT pane ALWAYS shows the required status table** — columns
> **Epic ID · Track · Status · %Complete**, one row per watched track/pane —
> rendered by `render-table.py` from `tmp/overseer/rows.tsv` (which the watcher
> rewrites each cycle). These four columns are mandatory and always present;
> `status.md` carries only free-form notes, shown in the top-RIGHT pane.

That required four-column table is what the top-LEFT pane renders from the
`rows.tsv` the **watcher** rewrites each cycle (see **The watcher** → *Rewrite
`rows.tsv` each cycle*) so the table never goes stale. The richer, on-request
print below is a superset for the bottom-pane reader: same tracks, more columns.

Every few heartbeats, and whenever asked, print a table of all tracks. Derive
`%complete` from the ledger: `bd show <epic>` lists children with ✓/◐/○ glyphs — use
`closed_children / total_children` (the epic line also prints `N/M complete (P%)`).

```
TRACK / SESSION     PROMPT                              EPIC          STATUS        CTX    ~%DONE
livespec2           prompts/zs22-handoff.md             livespec-zs22 working M6    37%    6/7 (86%)
livespec3           prompts/conformance-handoff.md      livespec-7xx  blocked:gate  41%    2/5 (40%)
livespec-runtime    prompts/ai-convention.md            livespec-hso8 completing    56%    4/5 (80%)
```

Columns: **track/session**, **prompt**, **epic id**, **status** (working / idle /
stalled / blocked:<why> / completing / done), **context %**, **est %complete**
(closed/total children). Add a one-line note under the table for anything needing the
maintainer's eventual attention — but keep working; the note is not a gate.

---

## Verify before you act (trust, but check)

- Before `/clear`: confirm the wrap-up landed (handoff PR **merged**, ledger updated,
  primary clean on `master`). `/clear` is irreversible to context.
- Before authorizing a force-push: confirm it's the session's **own** branch (the one it
  created), not another's.
- Read git / PR / ledger state **directly** (`git show origin/master:…`, `gh pr view`,
  `bd show`) rather than trusting a session's self-summary.
- When a session reports "done," verify the epic actually closed before marking it done.

---

## Boundaries to enforce on the sessions you drive

- **Worktree ownership**: every session/subagent operates only in the worktree it
  created; never `cd`/commit/push/PR into another track's worktree or branch; never
  force-push a branch it didn't create. (This is the collision that started all of this —
  see work-item `livespec-9msu`.)
- When a session dispatches its own subagents, its brief must carry that fence verbatim
  and must not run them unmonitored.
- Own-branch force-push to update an own-PR after a rebase is fine and pre-authorized by
  you (the overseer); a not-owned branch is never, without explicit maintainer sign-off.

---

## House rules (this repo)

- Repo mutations go `worktree → PR → rebase-merge`; never commit on the primary checkout;
  never `--no-verify`. (The sessions know this; don't undercut it.) **This skill itself
  was landed that way.**
- Beads via the env wrapper: `source /data/projects/1password-env-wrapper/with-livespec-env.sh bd -C /data/projects/livespec <args>`.
- Secrets are probe-only (`printenv NAME | wc -c`); never echo values.
- Scratch under `tmp/overseer/` (never the `tmp/` root; it's maintainer-owned).

---

## This skill is local-only

It lives at `.claude/skills/overseer/SKILL.md` in *this* repo and is **not** part of the
livespec plugin, the spec, the copier template, or any fleet-propagated surface — do not
add it to manifests, conformance checks, or other repos. It's a maintainer tool we may
evolve in place.
