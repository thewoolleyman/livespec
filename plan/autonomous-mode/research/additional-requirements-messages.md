# Additional requirements — maintainer messages, verbatim (autonomous-mode MVP)

**Purpose.** This file is a durable, verbatim capture of the maintainer's
requirement-bearing messages for the autonomous-mode MVP, extracted directly from
the session transcripts under
`/home/ubuntu/.claude/projects/-data-projects-livespec/*.jsonl`. It exists because
a compaction on 2026-07-16 dropped the console-side and documentation requirements
from a resuming session's working context, and the driver wrongly treated
"11/11 orchestrator children done" as "MVP done." These are the maintainer's OWN
WORDS, quoted exactly, so no future session loses them again. Each block records
the source session id, the UTC timestamp, and the current DONE / NOT-DONE status.

**Scope note.** The orchestrator-side machinery (the six `dispatcher.*` settings,
the API, the retirement of Full autonomous mode, the AI acceptance pass, the caps,
auto-disposition journaling) is DONE — epic `bd-ib-24j5uy` in
`thewoolleyman/livespec-orchestrator-beads-fabro`, children O0–O10. The
**console-side surface + documentation + release + the final end-to-end
acceptance** are the outstanding body of work this file re-anchors.

---

## 1. The standing meta-directive (repeated twice)

> **[ee28d0e0 · 2026-07-13T21:41:54]** "You have not done all of the requirements I
> gave you. Do not ask me for manual acceptance until everything that I told you to
> do is completely finished and you have validated it yourself."

Reinforced 2026-07-16 (this session): *"I don't know why you think you are done. I
gave you tons of requirements to write docs, and other things, and none of it is
done. Did you just lose all those requirements???"*

**Rule of record:** do not present for acceptance until the ENTIRE requirement set
below is finished AND self-validated.

---

## 2. The three (→ six) dispatcher settings + the console Settings surface + a docs page

> **[f0236eb0 · 2026-07-14T01:56:59]** "What do you mean by a third piece of
> orchestrator state? What are the first two? In any case I'm wanting these to be
> three independent autonomous settings in the orchestrator's livespec.jsonc.
>
> 1. automatically mark items ready
> 2. allow reviews that have failed past the cap to merge anyway or not
> 3. Accept AI only, AI-then-human, or human-only
>
> These should have meaningful names in the config.
>
> All three of these need to be controllable via the orchestrator exposed API, and
> all independenly controllable via the console.
>
> THis is also leading to a new requirement: THe console should have a "Settings"
> first class left-nav to control all these "orchestrator wide / dispatcher"
> settings. It will be a sub-menu based settings, with dispatcher settings being
> the first and only menu item.
>
> This should have a separate docs page and context-specific help just like we have
> documented in the plan for the rest of the app.
>
> So answer my one question and then tell me if this clears everything else up."

- The settings + orchestrator API: **DONE** (orchestrator O1/O10).
- Console "Settings" first-class left-nav (sub-menu; Dispatcher settings first/only
  item): **NOT DONE** — console item **W4** (`livespec-console-beads-fabro-j3ts23`).
- Separate docs page + context-specific help: **NOT DONE** — console **W4/W5**.

---

## 3. Retire outright; global + per-item, both controllable in the console; design the UX

> **[f0236eb0 · 2026-07-14T02:04:17]** "A. Yes, replaces it outright. B. Yes, global
> defaults, but allow per item overrides. AND THE CONSOLE TUI SHOULD ALLOW BOTH TO
> BE CONTROLLED. FIGURE OUT A SENSIBLE UX/UI FOR THIS.
>
> On the safety flag, yes, default all three to save value. FOr 3, default is
> "ai-then-human"."

- Retire outright + safe defaults + `acceptance_mode` default `ai-then-human` +
  per-item-beats-global: **DONE** (orchestrator O2/O1).
- The console UX for BOTH global and per-item control, actually IMPLEMENTED: **NOT
  DONE** — the mockup was designed and approved in the handoff (cont.12), but the
  console surface (**W4** global Settings + **W5** per-item override valves) was
  never built.

---

## 4. The API ⇒ Settings ⇒ help ⇒ docs principle + the acceptance rework cap

> **[f0236eb0 · 2026-07-14T02:18:22]** "… Or are you talking about a cap on the
> acceptance mode so it can't continually keep kicking it back to the factory? If so
> then yes that is a good point. We absolutely do need to have a separate cap for the
> number of times an acceptance can get rejected for the same item, just like the
> review, but it's a larger outer loop. And both of these need to have configurable
> values for the number of cap.
>
> Which brings up another point. Really anything that is possible to configure via
> the orchestrator API needs to show up under settings as well and be documented in
> the inline help and in the repo docs as Markdown in the settings doc."

- `acceptance_rework_cap` (+ `review_fix_cap`), configurable: **DONE** (orchestrator
  O6/O8).
- The API⇒Settings⇒help⇒docs principle *realized on the console side* (every
  API-configurable key present in Settings + inline help + a Markdown settings doc)
  and the **mechanical completeness check** that enforces it: **NOT DONE** — console
  **W6** (`livespec-console-beads-fabro-zmunjo`) + the docs/help surfaces.

---

## 5. The review-gate exit + the review cap = 3

> **[ee28d0e0 · 2026-07-14T00:08:44]** "OK on number 1 that is wrong. If a reviewer
> says "fix up to the cap" then it should not approve. It should get an exit out for
> human intervention. … yes we need to go ahead and backfill the missing AI review
> and mechanism to reject it back into the factory. And as for the console's Flip to
> Autonomous mode, that should … only switch to the AI only For all review steps.
> The non-autonomous mode should always switch to AI than human. There is no setting
> in the console to switch to human only. I am not going to use that now. It is
> merely an availability knob …"

> **[ee28d0e0 · 2026-07-14T01:01:03]** "Increase the cap number to three. Otherwise
> we are good to go."

- Blocking review gate + escalate-to-human + AI review backfill + reject-to-factory:
  **DONE** (orchestrator O8/O5/O3/O4).
- `review_fix_cap` default 3: **DONE** (orchestrator O1).

---

## 6. Observability data-gathering on reviewer-gate escapes

> **[ee28d0e0 · 2026-07-14T00:24:09]** "I want you to look at the current and
> historical observability for the factory and find out how many things actually got
> let out of the factory even though they failed the reviewer gate two times. That
> will give us a data point on whether we need to look closer at this in order to not
> have the factory stall on everything. So you need to add a Step to the plan to
> gather that data from Honeycomb and present it for discussion. And if it looks bad
> then we need to look at ways to mitigate this, either by allowing more passes or
> having multiple reviewers or modifying the prompt to ensure that it does not
> nit-pick."

> **[ee28d0e0 · 2026-07-14T00:28:44]** "… dig directly into the FABRO logs to figure
> it out. … I have one other question about these three levers … Where do those
> levers actually live and how are they controlled? Are they CLI or what? … Give me a
> summary and ideally an ASCII graph of how that all works."

- **DONE.** Mined from Fabro run logs (Honeycomb lacked the instrumentation):
  ship-on-cap = **2 of 91 gate-era PRs = 2.2%** across 150 `implement-work-item`
  runs, so a blocking review will not stall the factory (mitigations optional). The
  levers control-surface summary was captured in the handoff (cont.11).

---

## 7. Console README + main livespec README blurb

> **[2026-07-11]** "… before you start that track, I want you to ensure that you have
> updated the README in the console with detailed instructions on how to use the TUI.
> Has this been done so I can go ahead and test it myself? From the console app
> itself"

> **[2026-07-11]** "There should really also be a blurb in the main livespec readme
> that mentions the console and the TUI and how to invoke it and gives a pointer to
> the console app's readme for more instructions."

- **DONE** (merged): console TUI README (`livespec-console-beads-fabro` PR #165) and
  the main livespec README console blurb (core PR #1077). NOTE: W5 calls for a README
  *rewrite* that supersedes the initial version.

---

## 8. Standalone console binary published via release-please / CI

> **[2026-07-11]** "These instructions had better not include telling somebody to
> manually build Rust. That's fine for a developer install but the actual binary
> should be stand-alone and downloaded from a release which is published via GitHub
> from CI. Did you do that? If not that needs to be added to this track of work. It's
> not a real deliverable until it's published on the version schedule via release
> please."

- **NOT DONE.** `livespec-console-beads-fabro/.github/workflows/` has only `ci.yml`
  and `bump-pin-from-dispatch.yml`; there is no release-please/binary-publish
  workflow, and `gh release list` is empty. Per the maintainer, this is not a real
  deliverable until the standalone binary is published on the version schedule.

---

## 9. Stage-2 — the MVP acceptance, driven solely through the live TUI

> **[2026-07-13]** "I don't think we're even close to done. I had previously told you
> that as soon as possible you should start dogfooding the TUI yourself to drive all
> of your work. Using the console-autonomous-mode tmux Session. Did you do that? If
> not then we are not anywhere near acceptance. You need to drive multiple real items
> through the entire workflow solely using the TUI yourself and prove that the entire
> workflow works before we can call this done. First of all answer the question of
> whether you have done any of that yet. And if not then we need to insert a
> completely new phase in this plan, which identifies some real tracks of work and
> plans across multiple of the existing livespec fleet repos. You drive them fully to
> completion using the TUI solely. And yes you can drop me into the loop as the human
> whenever I need to answer anything by Opening up an appropriate clod session in the
> orchestrator-autonomous-mode TMUx session that I can then connect to and drive
> whatever human input is needed. Confirm that you understand and that all of this
> makes sense."

- **NOT DONE.** This is the MVP's final acceptance and is gated on the console-side
  surface existing. It must be re-run "the correct way" (a supervised dispatch that
  parks in `acceptance`, maintainer accepts via the TUI) across real fleet
  work-items, driven SOLELY through the live TUI.

---

## 10. NEW (2026-07-16) — individual work-item status control in the TUI

> **[current session · 2026-07-16]** "I don't see any way to actually move an item to
> ready. For an individual workitem, the TUI should allow you to move it to ANY
> status. Right now you can't even select individual items, only lanes."

- **NOT DONE (new).** Today the TUI can only SELECT LANES, not individual
  work-items. Requirement: the TUI must let the operator (a) SELECT an individual
  work-item, and (b) MOVE IT TO ANY STATUS — not just the lane-scoped operations,
  and specifically including moving a `pending-approval` item to `ready`. This
  generalizes the per-item valves (W5) into arbitrary per-item status transitions
  and requires item-level selection/navigation in the TUI. **To be filed as a new
  console work-item** (e.g. W7) under the console epic
  `livespec-console-beads-fabro-yvikqp`, and reflected in the Settings/valves UX.

---

## Consolidated status matrix

| # | Requirement | Owner repo | Status |
|---|---|---|---|
| 2 | Six dispatcher settings + orchestrator API | orchestrator | DONE (O1/O10) |
| 2 | Console "Settings" left-nav surface | console | **NOT DONE (W4)** |
| 2/4 | Settings docs page (Markdown) + context help | console | **NOT DONE (W4/W5)** |
| 3 | Retire autonomous mode; safe defaults; per-item-beats-global | orchestrator | DONE (O2/O1) |
| 3 | Console UX for global + per-item control (implemented) | console | **NOT DONE (W4/W5)** |
| 4 | `acceptance_rework_cap` / `review_fix_cap` configurable | orchestrator | DONE (O6/O8) |
| 4 | API⇒Settings⇒help⇒docs mechanical completeness check | console/dev-tooling | **NOT DONE (W6)** |
| 5 | Blocking review gate + escalate + AI review + reject-to-factory | orchestrator | DONE (O8/O5/O3/O4) |
| 6 | Reviewer-gate-escape observability data-gathering | (analysis) | DONE (2.2%) |
| 7 | Console TUI README + main README blurb | console/core | DONE (#165/#1077); W5 = rewrite |
| 8 | Standalone console binary via release-please/CI | console | **NOT DONE** |
| 9 | Stage-2 MVP acceptance driven solely via the live TUI | (cross-repo) | **NOT DONE** |
| 10 | TUI: select an individual item + move to ANY status | console | **NOT DONE (new; W7)** |

## The console work-items (filed, `pending-approval`, tenant `livespec-console-beads-fabro`)

- **W3** `livespec-console-beads-fabro-636m46` — config port → orchestrator API; DELETE the direct-JSONC writer.
- **W4** `livespec-console-beads-fabro-j3ts23` — the `TuiView::Settings` left-nav surface (+ delete the retiring arming surface).
- **W5** `livespec-console-beads-fabro-2ctzhm` — per-item override valves + context-specific help + README rewrite.
- **W6** `livespec-console-beads-fabro-zmunjo` — the mechanical API⇒Settings⇒docs completeness check.
- **W7** (to file) — individual-item selection + move-to-any-status in the TUI (requirement #10 above).
- Plus: the **console binary release-please/CI pipeline** (requirement #8), and **Stage-2** end-to-end TUI acceptance (requirement #9).

Dependency order: **W3 → W4 + W5 → W6**; W7 folds into the item-selection/valves work (after W4); the release pipeline is independent; Stage-2 is last (needs all of the above).
