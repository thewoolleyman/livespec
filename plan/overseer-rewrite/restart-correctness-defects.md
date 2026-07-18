# Overseer restart correctness — root-cause defects & fix spec (2026-07-18)

**IMPLEMENTED 2026-07-18 (branch `fix/overseer-restart-correctness`).** Both defects are
fixed and pinned by beside-tests (269 green), plus an independent Fable adversarial review
(NO BLOCKERS; 5 should-fix findings all addressed — SF1 re-point flip-flop guard, SF2 gate
wiring test, SF3 box-state retry branching, SF4 gate-keystroke guard, SF5 set-valued
`_claude_names`) and a maintainer-flagged live fix (the keep-going nudge now requires ≥1 hour
of continuous idle before firing). R1 (self-healing resume-submit + marker not
discarded on failed submit): `registry.set_resume_pending`/`read_resume_pending`,
`_do_restart` keeps the marker + marks `resume_pending` on a failed submit, `evaluate`
retries the SUBMIT ONLY (`_resend_enter`, never a re-respawn), `_await_input_box` hardens
the first paste. R2 (Claude gate `name == topic` parity + stale-mapping re-point):
`claude_sessions.sessions_by_tmux_session` → `_claude_name`, `_pane_is_managed_claude`
rejects a proven name-mismatch (positive-mismatch only, fail-soft on unknown),
`registry.repoint_tmux` + `adopt_sessions` re-points a moved session. Each new guard was
sabotage-verified (breaking it turns its test red). Docs updated: overseer `AGENTS.md`
(two mechanics bullets + invariant-7 (c)), `marker-protocol.md` (restart-mechanics
self-heal note), and the `_do_restart` docstring. The full-suite / no-regression run and
the daemon respawn onto the merged code are the acceptance legs.

**Deliverable status:** ready to fold into the overseer-rewrite plan. This is a
fix-spec, not a change — nothing in `.claude/skills/overseer/` was edited while
producing it. It slots in beside `design.md` as the "restart correctness" work
item, and it EXTENDS the Codex-full-citizen adversarial review (PR #1308) rather
than contradicting it — Defect 1 below is the CLAUDE analogue of the two
should-fix findings that review raised on the Codex restart leg.

Written by an investigation session (livespec core) at the maintainer's request,
using: the maintainer's live report, the daemon log
(`/data/projects/livespec/tmp/overseer/daemon.log`), the mapping store
(`~/.livespec-overseer.jsonl`), the Claude session registry
(`~/.claude/sessions/<pid>.json`), the overseer source, and Honeycomb
(`agent-activity` env, `claude-code` dataset — Claude Code logs every pasted
prompt as a `user_prompt` span tagged with `session.id`, which the registry's
`sessionId` field bridges back to a tmux pane).

---

## 1. Bottom line

Two independent defects in the daemon's restart path make it "do incorrect
actions when sessions are restarted." Both are proven from live telemetry, not
inferred.

1. **Defect 1 (CONFIRMED, reproduced 4× live in one day) — a restarted session is left
   stranded with its handoff prompt pasted but never submitted, and the daemon
   then throws away the one thing that would let it retry.** After
   `respawn-pane -k`, the fresh Claude TUI drops the `Enter`, so the resume line
   sits un-submitted; `_do_restart` nonetheless deletes the `ready` marker and
   logs "restarted" as success, so the daemon never tries again. Result: a live
   but idle session holding an un-run handoff prompt until a human presses Enter.
   This is the exact "stuck with the handoff prompt, BUT DIDN'T HIT ENTER" the
   maintainer reported.

2. **Defect 2 (architectural hazard) — the Claude identity gate verifies the
   repo but not WHICH topic's session occupies a pane, and a topic→tmux mapping
   is never corrected once stored.** With generic, reused tmux window names
   (`livespec1`…`livespec5`), this lets the daemon drive the wrong same-repo
   session — inject topic A's wrap-up into topic B's Claude, and on a `ready`
   respawn-kill B as A. This is the "left pointing at an incorrect claude code
   session" class. The Codex path was ALREADY hardened against exactly this
   (pane-scoped `name == topic` check); the Claude path was left asymmetric.

Not a defect: the "wrong path / home dir" symptom for `livespec1` was NOT the
daemon (see §5). Its restart primitive always sets `-c <repo>`, and it never
auto-creates sessions (`recover=False`).

---

## 2. Evidence — moment-by-moment (all times UTC, 2026-07-17)

Session ids are the Claude session UUIDs; each is bridged to its tmux pane via
the registry `sessionId` field.

| Time | Event | Source |
|---|---|---|
| 05:47:33 | wrap-up injected into **fabro-ci-image-factoring** (ctx 49%), pasted into session `e6d65758` (genuinely fabro: 17 prompts, all fabro, 0 factory-safe) | Honeycomb + daemon.log |
| 05:55:06 | daemon `respawn-pane -k` fabro pane `%78` (tmux `livespec1`); **resume NOT submitted**; marker cleared; "restarted" logged | daemon.log |
| — | fresh fabro session **never submits its resume** (no `…/plan/fabro-ci-image-factoring/handoff.md and follow it` span exists in 05:00–21:00); stays idle; tmux `livespec1` later vanishes → fresh fabro becomes a live-Claude-with-no-tmux orphan | Honeycomb (absence) + registry |
| 06:10:32 | daemon respawns **overseer-rewrite** (pane `%75`); **resume submitted OK at 06:11:08** (session `55d5e480`) | Honeycomb |
| 09:52:19 | wrap-up injected into **autonomous-mode** (ctx 33%), pasted into session `1ee23d79` (genuinely autonomous-mode) | Honeycomb + daemon.log |
| 09:59:31 | daemon `respawn-pane -k` autonomous-mode pane `%66` (tmux `livespec-autonomous-mode`) → fresh session `4c18b119` born; **resume NOT submitted**; marker cleared; "restarted" logged | daemon.log + registry `startedAt`=09:59:31 |
| 09:59:31 → 19:18:20 | fresh session `4c18b119` sits **IDLE for 9h19m** — `interaction.sequence` never leaves 0, resume line un-submitted | Honeycomb |
| 19:18:20 | first interaction (seq 1) on `4c18b119`: the resume line **finally submitted** — a human pressed Enter | Honeycomb |
| 22:07:49 | wrap-up injected into **overseer-rewrite** (ctx 50%) | daemon.log |
| 22:09:44 | daemon respawns **overseer-rewrite** (pane `%75`, tmux `livespec`) → fresh session `bc33b738` (`startedAt`=22:09:44); **resume NOT submitted** — verified live in the pane: `❯ read …/overseer-rewrite/handoff.md and follow it` idle in the box | daemon.log + registry + live pane capture |
| 22:52:40 | **autonomous-mode** respawned AGAIN (pane `%66`); **resume NOT submitted** a SECOND time on the same track (after the 19:18 hand-rescue, it re-crossed threshold and re-stranded) | daemon.log |

**Two facts this pins down:**

- The wrap-up injections were **topic-correct** — each topic's wrap-up reached
  the right session; no session ever received two different topics' wrap-ups. So
  at these two restart moments the mapping was consistent with reality and the
  fault was purely the un-submitted resume (Defect 1). Defect 2 is the latent
  hazard that bites at a DIFFERENT moment — when a generic window is reused for a
  different topic than the store recorded.
- The overseer-rewrite restart (06:10) submitted fine, so the submit mechanism
  works on a **steady** idle TUI. It is specifically the **freshly-respawned**
  TUI (still drawing its welcome/news screen when the Enter arrives) that drops
  the key. Both observed failures (fabro, autonomous-mode) were fresh respawns;
  the one success (overseer-rewrite) evidently caught its TUI already settled.

---

## 3. Defect 1 — stranded resume + discarded marker

### What the code does

`supervisor.py` `_do_restart` (the ONLY restart path):

```python
resume = track.resume or default_resume(track.repo, track.topic)
if not self._submit_prompt(target, resume):
    self._alert(..., message="resume line NOT submitted after restart — the fresh session is idle")
self._clear_state(track)                                   # deletes the `ready` marker + stamp
self._inject.pop(_key(track.repo, track.topic), None)
self._log(f"restarted {track.repo}::{track.topic} (pane {target})")   # logs SUCCESS regardless
```

- `_submit_prompt` pastes the resume line, then sends `Enter` up to
  `_SUBMIT_MAX_ENTERS` times, checking the input box cleared each time. On a
  fresh respawn the box never clears within the retries → returns `False`.
- `_clear_state` and the "restarted" log then run **unconditionally**. Deleting
  the `ready` marker removes the SOLE authorization for a restart, so the daemon
  cannot retry the submit on a later tick — the session is stranded. The daemon
  reports the restart as done.

### Why this is a real defect, not the accepted tradeoff

This clearing-on-failed-submit is the historically-documented "Codex #2
tradeoff" (commit `23e23347`): keeping the marker was rejected because it would
let the still-valid `ready` re-fire `respawn-pane -k` and kill the fresh Claude
in a loop. That reasoning correctly rules out "keep the marker AND keep
re-respawning" — but it wrongly concluded "therefore discard the marker and give
up." The fresh Claude IS already up; what failed is only the final `Enter`. The
right behavior is to **retry the submit (the Enter) without re-respawning**,
which is safe and needs no marker.

The live cost of the current behavior is not hypothetical, and it is not rare:
on 2026-07-17 alone it stranded fabro (05:55, orphaned entirely), autonomous-mode
**twice** (09:59 → unusable for 9h19m until a human pressed Enter; then again at
22:52), and overseer-rewrite (22:09, verified live in the pane). Four strandings
in one day on one host — this is the daemon's dominant failure mode, not an edge
case.

### Required fix

Separate the two facts the current code conflates — "is the fresh Claude up?"
and "did the resume submit?" — and make the submit self-healing:

1. In `_do_restart`, once the pane is confirmed a live fresh Claude
   (`_await_claude`), attempt `_submit_prompt`. **On submit success**, clear the
   marker + round as today. **On submit failure**, do NOT clear the marker and do
   NOT log a clean "restarted"; leave a distinct state so the next tick retries
   ONLY the submit.
2. Add a post-respawn state (e.g. an in-memory `_pending_resume[key] = (pane,
   text)` plus a durable breadcrumb, since the in-memory map dies with the
   daemon) such that on a subsequent tick, if the pane is a live Claude whose
   input box still holds un-submitted text, the daemon re-sends `Enter`
   (never re-pastes, never re-respawns) until the box clears — then closes the
   round. Re-`respawn-pane -k` MUST remain gated on a fresh `ready` only, so this
   retry can never escalate to a kill.
3. Never log `restarted … (success)` when the resume did not submit. The
   operator alert must persist (edge-triggered, per invariant 10) until the
   session is actually resumed, not fire once and clear.

Harden the submit itself so retries rarely happen:

4. `_submit_prompt` should treat the fresh-TUI case explicitly: after paste,
   wait for the pane to look like a ready Claude input box (not just sleep a
   fixed interval) before the first Enter, and anchor the "box cleared" read to
   the tail rows (the same tail-anchoring the review recommended for the Codex
   submit-confirm nit). This closes the drop-the-first-Enter window that both
   live failures hit.

### Acceptance / tests (beside-tests — the ONLY gate on this folder)

- `test_fresh_respawn_dropped_enter_is_retried_next_tick_without_respawn`: fake a
  respawn whose first Enter does not clear the box; assert (a) NO second
  `respawn-pane` is issued, (b) a later tick re-sends Enter and clears it, (c)
  the round closes only after the box clears, (d) the marker is NOT deleted while
  the submit is outstanding.
- `test_restart_does_not_log_success_when_resume_unsubmitted`.
- `test_submit_retry_never_kills_the_fresh_session` (the loop-safety property the
  Codex #2 reasoning was protecting — keep it green under the new retry path).
- Mirror the Codex sibling the PR #1308 review asked for (assert state-file gone
  + no second respawn on the success leg) so both runtimes are pinned
  symmetrically.

---

## 4. Defect 2 — topic-blind Claude gate + frozen mapping

### What the code does

The mapping store keys each track by `(repo, topic)` and records a `tmux` field.
Two facts combine into a hazard:

- **Adoption never re-points an existing mapping.** `adopt_sessions` does
  `if (repo, topic) in existing: continue`. Once `topic → livespec1` is stored,
  it is frozen — even if that topic's live `claude -n <topic>` session later
  moves to a different tmux window, or `livespec1` is reused for another topic.
  Nothing re-derives the binding. (`auto_link` only ever fires on an
  `is_unassigned` row; `_upsert` is manual-CLI only.)
- **The Claude act-gate checks the repo, not the topic.**
  `_pane_is_managed_claude` verifies only that the pane runs `claude`/`node` and
  its cwd is inside the repo. It does NOT check that the pane's Claude session
  `name` equals the track's `topic` — even though the daemon already computes
  that mapping every tick (`claude_sessions.map_named_sessions` →
  `(tmux_session, name, cwd)`; `_claude_status` is keyed by tmux session).

### The asymmetry to fix

The Codex path was hardened for exactly this failure on 2026-07-17:
`_is_codex_track` requires `live.name == topic and path_in_repo(live.cwd, repo)`
at the PANE level, precisely so a codex process that resolves into a track's tmux
session but belongs to a different plan cannot be mis-driven. The Claude path
never got the equivalent `name == topic` pane check. So when a generic window the
store maps to topic A actually runs topic B's Claude (same repo), the daemon
treats B as A: it injects A's wrap-up into B (B, handed A's wrap-up instructions,
may itself write A's `ready`), and can then `respawn-pane -k` B and relaunch it as
A — destroying B's live work. That is the "over-exited … pointing at an incorrect
claude code session" class.

Generic reused tmux names make this reachable, not exotic: `livespec1`…
`livespec5` are the fleet's scratch windows, cycled through many topics; this
very investigation session is `livespec-29`. The store still maps
`fabro-ci-image-factoring → livespec1` even though `livespec1` no longer exists.

### Required fix

1. **Bring the Claude gate to parity with Codex.** In `_pane_is_managed_claude`
   (or a wrapper used by every ACT), additionally require that the live Claude
   session occupying `target`'s tmux session has `name == topic`. The daemon
   already has this per tick — thread the registry `name` (not just `status`)
   through `map_named_sessions`/`_claude_status` so the gate can compare it.
   Fail-closed: if the pane's live Claude name ≠ topic, it is NOT ours → route to
   `session-gone` (as a foreign pane already does), never keystroke/respawn it.
2. **Re-point a stale mapping instead of freezing it.** Each tick, when a topic's
   live named session resolves to a tmux session DIFFERENT from the stored `tmux`
   field, update the store to the current one (the data is already in
   `map_named_sessions`). This is the "re-mapping is a separate concern" the code
   comments defer — it is the concern. Keep it fail-soft and idempotent; log each
   re-point like an adoption.

### Acceptance / tests

- `test_claude_act_refuses_pane_whose_live_name_differs_from_topic`: map
  `topic-A → livespecN`; put a live `claude -n topic-B` (same repo) in
  `livespecN`; assert the topic-A track never injects/respawns into it and
  renders `session-gone`.
- `test_stale_tmux_mapping_is_repointed_when_topic_session_moves`: topic's live
  session moves `livespecN → livespecM`; assert the store's `tmux` is rewritten
  to `livespecM` within one tick and acts on the right pane.
- Keep the existing Codex collision test green (the two gates must stay
  symmetric).

---

## 5. Not a defect — the "home dir / wrong path" symptom

The daemon's restart primitive is `respawn-pane -k -c <repo> …` — it ALWAYS sets
the new process's cwd to the track's repo — and `run_daemon` starts the loop with
`recover=False`, so the daemon never creates a session at startup. A tmux session
sitting in `$HOME` therefore did not come from the overseer; it points to
`livespec1` being restarted **out-of-band / manually** (a bare `tmux new-session`
defaults to `$HOME`). Worth stating so this is not chased as a daemon bug. The
genuine daemon contribution to the `livespec1` chaos is Defect 1 (the fresh fabro
session stranded there, un-resumed, until the window was torn down).

---

## 6. How this composes with the Codex full-citizen review (PR #1308)

The 2026-07-17 Fable review of the Codex-full-citizen work raised, as should-fix:
(a) the Codex restart's success leg (await + round-close) is completely unpinned —
a dropped `_clear_state` would loop respawn-kills undetected; (b) the Codex launch
passes no autonomy flag, unlike Claude's required `--dangerously-skip-permissions`.
Defect 1 here is the CLAUDE mirror of (a): the Claude success/failure legs of the
resume-submit are under-pinned and mis-handled. The fix work should pin BOTH
runtimes' restart legs with symmetric beside-tests in one pass, so the daemon's
one destructive operation (`respawn-pane -k`) and its post-respawn resume are
equally covered for Claude and Codex.

---

## 7. Suggested work-item shape

One epic, "Overseer restart correctness," with two slices:

- **R1 — resume-submit is self-healing; marker not discarded on failed submit**
  (Defect 1). Highest priority: it caused a 9h stranding today and orphaned a
  track.
- **R2 — Claude identity gate checks `name == topic`; stale tmux mapping is
  re-pointed** (Defect 2). Closes the wrong-session hazard and removes the
  Claude/Codex asymmetry.

Both are folder-local (`.claude/skills/overseer/`), stdlib-only, gated solely by
the beside-tests (`uv run pytest .claude/skills/overseer/ -q`) — run them before
any push per the AGENTS.md rule; `just check`/CI do NOT exercise this folder.
