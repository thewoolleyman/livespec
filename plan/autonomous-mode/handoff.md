# Autonomous-mode MVP — overall plan handoff (livespec core)

## OPERATING DIRECTIVES (standing — maintainer-declared 2026-07-12)
1. **Hand off at 50% context.** When driver/overseer context passes ~50%, STOP
   at a clean boundary and hand off to a fresh session by LANDING THE PLAN IN
   THIS HANDOFF DOCUMENT — do not push past it. **The hand-off artifact is THIS
   file's path (`plan/autonomous-mode/handoff.md`); the maintainer resumes by
   opening it. NEVER write a separate prose resume prompt — it is a banned,
   redundant duplicate of the handoff (maintainer-declared 2026-07-13, "Never
   ever do that").** Hand off by pointing at the path, nothing more.
2. **Delegate to sub-agents / the Fabro factory to preserve driver context.** Do
   the heavy lifting (repairs, authoring, multi-file work, live-run iteration
   where feasible) in scoped sub-agents or the factory; keep the driver session
   for plan / dispatch / synthesis.
3. **Dogfood the console TUI as the overseer's operator-steering surface
   (maintainer-declared 2026-07-12).** As soon as possible, drive operator work
   through the live console TUI myself — launched in a tmux session named
   EXACTLY `console-autonomous-mode` (so the maintainer can attach and watch),
   one pane per repo tenant when overseeing more than one. Launch per repo with
   `just tui` from that repo's checkout (builds the release binary + runs it
   under `with-livespec-env.sh -- … serve`). **Any operator-steering action I
   cannot cleanly drive through the TUI is a USABILITY HOLE** — log it and route
   it to the maintainer for a fix discussion, do NOT silently fall back to the
   CLI for it. See "## TUI dogfooding — scope boundary" below for the
   in-scope (holes) vs. by-design-CLI (not holes) split, agreed with the
   maintainer.

## TUI dogfooding — scope boundary (maintainer-declared + CORRECTED 2026-07-12)
The maintainer SHARPENED this boundary mid-session: **almost everything is
TUI-drivable, because almost everything is a groomed work-item the Fabro factory
runs — and the operator drives/observes the factory from the cockpit.** Code
authoring AND PR merges are NOT CLI-only work: they are the factory's OUTPUT for
groomed work-items, so the operator drives them from the TUI (dispatch → watch →
valve → observe merge). The ONLY off-factory exception is the narrow,
already-documented subset: repo/dev-tooling PLUMBING that is incompatible or
risky to run *through* the factory itself (e.g. the factory substrate, the
commit-refuse hooks). This FORCES disciplined decomposition — every plan
deliverable becomes a factory-runnable, groomed work-item — which is the point
of the whole livespec ecosystem, not a burden.

**Drive via the factory → TUI — a gap is a USABILITY HOLE:**
- Watch each track's ledger / factory / needs-attention state.
- Flip autonomous mode on/off (this IS the I2 acceptance).
- Per-item valves: approve / accept / reject / set-admission / set-acceptance.
- Drain the factory; observe auto-resolutions reflected.
- Triage a truly-unresolvable needs-attention item.
- **Code fixes, PR authoring + merge** — as groomed work-items dispatched
  through the factory; the operator dispatches/observes/valves from the cockpit.

**Off-factory / CLI — the NARROW documented exception, NOT a hole:**
- Repo/dev-tooling PLUMBING unsafe to self-run through the factory: the Track A
  golden-master substrate repair, the commit-refuse hooks, the dispatch
  machinery itself.
- *Spec ratification keeps its DESIGNED human gate* (independent Fable review +
  the maintainer's accept) and grooming is a maintainer-owned cut — deliberate
  human touchpoints, not TUI holes.

The discipline this imposes: if a plan deliverable "can't" be a factory
work-item, that is a smell — re-groom it until it can, or confirm it is the
narrow plumbing exception.

## SESSION UPDATE — 2026-07-13 (cont. 6): Stage-1 cockpit-readiness COMPLETE — Findings A–G ALL MERGED + verified live; Stage 2 next

Fresh session resumed from cont.5. Drove Stage-1 cockpit-readiness to near-completion:
**all four cont.5 findings PLUS three NEW findings surfaced by live dogfooding (E, F,
G) are fixed — **A–G ALL MERGED + verified live.** The cockpit LAUNCHES clean, OBSERVES
real work correctly, FITS at 112, shows a unified Attention view, and its Detail pane
scrolls to the true wrapped bottom. **Stage 1 (cockpit-readiness) is COMPLETE. RESUME:
Stage 2 — groom `86k`+`e0t` → drive them end-to-end through the TUI with the maintainer
on the valves.** The cockpit is LEFT RUNNING in tmux `console-autonomous-mode` (112×28,
fresh scratchpad store).

### DONE — all fixes in `livespec-console-beads-fabro`, via scoped sub-agents (Stage-1 = sub-agents, NOT the factory: Fabro sandbox has no Rust)
- **A (P1, resolver flattened layout) — MERGED** console PR #187 (`2ea64f8`). A
  `plugin_bin_dir` helper makes `validate_plugin_root`/`programs_from_plugin_bin`
  accept BOTH `.claude-plugin/scripts/bin/` (source) AND `scripts/bin/` (flattened
  installed cache). Unblocked `just tui`/`serve` launch on a normal host — NO override.
  Verified live.
- **B+D (P2, header fit + list scroll) — MERGED** console PR #189 (`f95cf87`).
  `fit_header_line` degrades gracefully at 112 (never drops repo/autonomous/source-
  count); stateful `ListState` scroll-to-selection + scrollbar for Attention/Lanes.
  (D's Detail-pane free-scroll deferred → became Finding F.)
- **E (P1, NEW — python3 exec) — MERGED** console PR #191 (`409dc99`). The console
  exec'd resolved backing CLIs DIRECTLY, but the installed cache ships
  `needs_attention.py` + **`drive.py` (the valve CLI)** NON-executable → `Permission
  denied` → sources degraded to "unavailable" → cockpit blind to attention AND valves
  broken. Fix: `python_normalized_invocation` wraps `.py` programs as `python3
  <script>`. This was WHY `serve --preview` showed attention:0 despite the CLI
  returning 6.
- **F (P2, NEW — from maintainer's live bug report) — MERGED** console PR #194
  (`8d01e64`). left/right now move focus across the 3 panes (Views→Content→Detail,
  clamped); up/down act within the focused pane; the Detail pane is reachable + scrolls
  (`detail_scroll` + scrollbar). View-switching moved to up/down on the focused Views
  nav (judgment call — maintainer may later want a dedicated view-switch key).
- **C (P2, repo dimension + unify attention) — MERGED** console PR #197 (3 commits
  `bbcce1d`/`a82994f`/`f1cca09`, rebased onto F). Read-only investigator root-caused it
  (NOT cwd-scoping). Three defects: (1) `repo_id` took the substring after the LAST
  colon → mis-parsed needs-attention stream ids `attention_item:{repo}:{colon-bearing-
  id}` → 7-way jumble; fixed to read `source_ref.repo` from payload for attention
  events + prefix-parse for pull-sources. (2) `console_repo()` hardcoded
  `livespec-console-beads-fabro`; now `resolve_console_repo(cwd basename)` — matches
  upstream `needs_attention.py`'s `source_ref.repo = project_root.name`. (3) TUI
  Attention showed ONLY work-item-gated attention, NOT the needs-attention items —
  **maintainer chose UNIFY**; `unified_attention_entries` merges both (deduped by
  work-item id). **Spec-CONFORMANCE** — `scenarios.md` Scenario 1 + `spec.md`
  §"needs-attention" already mandated the unified inbox; code just wasn't wired.
  Follow-up test PR #198 CLOSED (it locked the logical-line-count clamp invariant that
  Finding G must change).
- **G (P2, NEW — Detail scroll clamp) — MERGED** console PR #199 (`911fa66`). Proven
  live at 112×16: the Detail scroll clamped SHORT on WRAPPING details — the reducer used
  `AttentionDetail::rendered_line_count()` (LOGICAL: `4 + actions + 1 + timeline.len()`),
  but long `evt:...` ids wrap + timeline entries render multi-line, so the wrapped render
  is ~2.5× longer and the clamp capped below the true bottom. Fix makes the RENDER the
  single authority: `render_scrollable_detail` returns the wrapped max
  (`content_rows − viewport` from the same `Paragraph::line_count` that sizes the
  scrollbar), stored into `TuiInteractionState.detail_max_scroll` each frame
  (measure-on-render, clamp-on-next-input); the superseded logical-count path
  (`detail_content_len`/`rendered_line_count`) was REMOVED, not papered over.
  **Verified live post-merge:** at 112×16 the Detail scrolls to the last timeline line
  (`Source completeness finding`), where pre-G it stranded at ~line 8.

### COCKPIT STATE — verified live at 112×28 from the orchestrator cwd (NO override)
Launch: `mise exec -- cargo build --release`, then FROM
`/data/projects/livespec-orchestrator-beads-fabro` cwd:
`/usr/local/bin/with-livespec-env.sh -- /data/projects/livespec-console-beads-fabro/target/release/livespec-console-beads-fabro serve`
(Finding A killed the interim `LIVESPEC_CONSOLE_ORCHESTRATOR_PLUGIN_ROOT` override).
tmux session `console-autonomous-mode` pinned 112×28. Verified: header `repo:
livespec-orchestrator-beads-fabro` ✓; Repos observed → 1 ✓; Attention → 6 unified
(blocked work-item + stale-branch + 3 plan-reviews + prune-history), correct repos ✓;
pane-focus ✓; Detail scroll reaches the true wrapped bottom (G) ✓.
- **Store staleness RESOLVED via a fresh store.** An earlier run showed the work-item
  Detail with the OLD `Repo: livespec-console-beads-fabro` (a work-item snapshot
  persisted BEFORE the fix). Relaunching with a FRESH store made every repo label
  correct. `tmp/` is maintainer-owned scratch → do NOT `rm` it; instead relaunch with
  `env LIVESPEC_CONSOLE_STORE_PATH=<scratchpad>/console-store.sqlite` (a fresh file
  outside `tmp/`) for a clean re-ingest. The default store path is
  `tmp/livespec-console.sqlite` (relative to the launch cwd), overridable by that env.

### DECISIONS (maintainer, 2026-07-13)
- **Unify the Attention view** (surface needs-attention items alongside valve-
  actionable work-items) — aligned with the existing spec (Scenario 1).
- **Stage-2 targets = `bd-ib-86k` + `bd-ib-e0t`** (orchestrator tenant; both
  small/Python/`deps=0`/off-active-track — verified against the 25-item backlog, which
  is otherwise dominated by active tracks: token-refresh, telemetry, image-factoring,
  decomposition, adopter). `86k` = restore the finalize-invokes-cost-gate test
  assertion; `e0t` = point post-merge janitor worktrees at `~/.worktrees` + teardown.
  Groom REAL backlog (maintainer's chosen sourcing).

### OPEN WORKTREES — reaped this session (all 6 cockpit-fix worktrees merged; agents exited)
console `fix-cockpit-finding-{a-resolver-layout, b-d-tui-scroll, e-python-exec,
f-detail-nav-scroll, c-repo-dimension, g-detail-scroll-clamp}` — reaped. core
`docs-autonomous-mode-cont6-gdone` (this update) — reap after its PR merges.

### RESUME ORDER (fresh session) — Stage 1 is DONE; go straight to Stage 2
1. **Stage 2 (the MVP dogfooding acceptance).** The cockpit is operator-ready and LEFT
   RUNNING (tmux `console-autonomous-mode`, 112×28, fresh scratchpad store; if it needs
   relaunch, use `env LIVESPEC_CONSOLE_STORE_PATH=<scratchpad>/console-store.sqlite
   /usr/local/bin/with-livespec-env.sh -- … serve` from the orchestrator cwd — Finding A
   removed the plugin-root override). Present `86k`/`e0t` for the maintainer's grooming
   cut → `ready`; dispatch each through the TUI (`:` drain / `a` autonomous); observe in
   Lanes; drive the valve loop (accept via `c`) with the maintainer as human-in-the-loop
   in `orchestrator-autonomous-mode`. **FIRST verify valve-targeting hits the orchestrator
   tenant** — the `gu4` `--repo` id→path fix + E's python3-drive + C's tenant label
   should make it correct, but confirm live on a safe item before real accepts (the
   maintainer-declared "done means exercised live, incl. every cross-boundary shape").
2. That live proof (multiple real items end-to-end SOLELY through the TUI, maintainer on
   the valves) = MVP "done" (I2).

### CARRY-OVER FINDINGS (not blocking; log for Stage 2 / follow-up)
- **Valve-targeting is UNVERIFIED end-to-end.** E (python3 `drive.py`) + C (tenant
  label = cwd basename) + `gu4` (id→path) should make `drive --repo` hit the orchestrator
  tenant, but no valve has been exercised live through the TUI yet. Verify on a safe item
  first (the `set-acceptance`/`set-admission` policy valves, or a reversible one).
- **Minor cosmetic (console-tui, optional):** needs-attention items render their operator
  command in the Detail "Attach:" slot, which reads slightly off for non-`fabro`
  commands (e.g. a `codex exec … plan` handoff). A dedicated field would be a small
  console-tui polish; not filed.
- **Scrollbar thumb** at max Detail scroll sits slightly above the very bottom edge
  (content bottom IS reached; functional). Cosmetic only.

## SESSION UPDATE — 2026-07-12 (cont. 5): TUI-DOGFOODING phase OPENED; cockpit is NOT operator-ready — 4 blocking findings; two-stage acceptance

**Supersedes the "I2 = flip-and-accept" framing.** The maintainer (2026-07-12)
directed that the MVP is NOT done until I (the driver) drive MULTIPLE real
cross-repo work-items end-to-end SOLELY through the live console TUI, dropping the
maintainer in as the human-in-the-loop. I had NOT been dogfooding the TUI at all
(everything ran via `dispatcher.py`/`bd`/`gh`/sub-agents) — a miss against
standing directive #3. First real dogfooding immediately proved the cockpit is not
yet operator-usable.

### DOGFOODING mechanics (LOCKED, maintainer-declared 2026-07-12)
- **I (this driver session) operate the console TUI DIRECTLY** via `tmux
  send-keys`/`capture-pane` — NO separate loop session. Every operator-steering
  action (dispatch → observe → valve → accept → observe-merge → close) goes
  through the TUI; a step I can't do in the TUI is a USABILITY HOLE (log + fix),
  never a silent CLI fallback.
- **Two distinct top-level TMUX sessions, exact names:** `console-autonomous-mode`
  (my operator cockpit — runs the console TUI) and `orchestrator-autonomous-mode`
  (the human-in-the-loop seat). These are separate tmux SESSIONS, not panes.
- **All Claude sessions start with `claude --dangerously-skip-permissions`.** The
  human seat is a `--dangerously-skip-permissions` Claude session NAMED
  `orchestrator-autonomous-mode`, run inside the `orchestrator-autonomous-mode`
  tmux session; I spin it up when a step needs the maintainer, who attaches to it.
- **`console-autonomous-mode` pinned to 112×28** (`tmux set-window-option -t
  console-autonomous-mode window-size manual` + `resize-window -x 112 -y 28`) —
  derived from the maintainer's Samsung Fold: narrowest width 114 (portrait) +
  landscape height, with a safety margin. Pinning also FORCES small-screen UI
  usability. Maintainer may attach/detach/resize freely (won't disrupt driving);
  the pin neutralizes resize. Use `/usr/bin/tmux` (the zsh alias shadows `tmux`).

### COCKPIT LAUNCH currently needs a WORKAROUND (Finding A is why)
Shipped `just tui` does NOT launch on a normal host. Interim launch used:
```
/usr/local/bin/with-livespec-env.sh -- \
  env LIVESPEC_CONSOLE_ORCHESTRATOR_PLUGIN_ROOT=/data/projects/livespec-orchestrator-beads-fabro \
  /data/projects/livespec-console-beads-fabro/target/release/livespec-console-beads-fabro serve
```
run FROM the orchestrator checkout cwd (so the work-items adapter observes the
orchestrator tenant — see Finding C). ALWAYS rebuild first (`just tui` runs
`cargo build --release`); the cockpit can silently run a STALE binary (the
pre-existing session ran a days-old build via the now-removed interim PATH shims).

### FOUR BLOCKING FINDINGS (Stage-1 cockpit fixes — all console-Rust)
- **A (P1 — cockpit unusable out-of-box): the resolver rejects the installed
  marketplace-cache plugin layout.** `crates/console-cli/src/backing_cli.rs`
  `validate_plugin_root` requires the SOURCE layout
  `<root>/.claude-plugin/scripts/bin/needs_attention.py`, but the installed cache
  is FLATTENED `<root>/scripts/bin/…`. So `just tui` dies loudly ("orchestrator
  plugin root …/cache/…/<sha> is missing …/.claude-plugin/scripts/bin/needs_attention.py").
  The `003` resolver "fails loudly" (its designed behavior) against a VALID
  installed plugin. FIX: accept BOTH layouts (source `.claude-plugin/scripts/bin/`
  AND flattened cache `scripts/bin/`). Same fragility 3 sub-agents hit in `just
  check`; now a hard LAUNCH crash. Root cause the retired `consolebin/` PATH shims
  had papered over.
- **B (P2 — small-screen UX): the header truncates at 112 cols.** `d6f`'s
  `sources: N unavailable (…)` segment pushes the header past 112; repo/autonomous/
  view/attention get cut off (observed `… | sources: 5 unavailable (dispatcher,
  fabro, github, livespec, orchestrator) | rep`). Header must fit/degrade
  gracefully at 112 (abbreviate or drop lower-priority fields, not truncate mid).
- **C (P2 — design clarity): observation is CWD-scoped.** The work-items
  (orchestrator) adapter observes a tenant only when the cockpit is launched FROM
  that tenant's cwd (header flipped 5→4 unavailable — `orchestrator` dropped — when
  relaunched from the orchestrator checkout; confirms `gkh`'s fix works there). So
  the "fleet" view is not fleet-wide for work-items. Settle the intended model.
- **D (P2 — no scroll affordances; acute at 112×28): overflowing pane content is
  UNREACHABLE.** The TUI has NO scroll machinery (`crates/console-tui/src/lib.rs`:
  no `ListState`/`StatefulWidget`/`.scroll(offset)`/scrollbar; panes render as
  stateless `List`/`Paragraph` with `Wrap { trim: true }`). Content past a pane's
  edge is clipped: lists render from the TOP and do NOT scroll to the selection
  (selecting an off-screen item leaves it invisible); a wrapped `Paragraph` (Detail)
  taller than the pane clips; a wide single-line field (header) truncates. Arrow
  keys don't rescue it — up/down move a selection with NO scroll-to-selection,
  left/right switch views / step in-out of the content pane (NO horizontal scroll).
  So on the pinned 112×28 (where overflow is the norm) the operator literally cannot
  see clipped rows/text. FIX: stateful lists that scroll to keep the selection
  visible + a scroll offset + scrollbar on content panes; responsive
  abbreviate/scroll for wide single-line content. Same family as Finding B but
  broader (every overflow-capable pane).

### TWO-STAGE ACCEPTANCE (the honest structure)
- **Stage 1 (prerequisite — SUB-AGENTS, not the factory):** fix A (the P1
  blocker), B, D, and settle C. All are console-Rust → the Fabro factory can't build
  them (the `d6f` sandbox-Rust wall). Route: scoped sub-agents (worktree → Rust
  RGR → PR → driver review). Only when the cockpit LAUNCHES clean + OBSERVES real
  work + FITS at 112 is it operator-usable.
- **Stage 2 (the actual dogfooding acceptance):** with a usable cockpit, drive
  MULTIPLE real **orchestrator-tenant Python** work-items (factory-buildable)
  end-to-end SOLELY through the TUI, dropping the maintainer in via
  `orchestrator-autonomous-mode` for human valves/decisions. That live proof =
  MVP "done."

### WHERE THE BLOCKING WORK LIVES (dependency map)
- MVP done (`plan/autonomous-mode/`) ← **I2 / Stage-2 dogfooding** ← **Stage-1
  cockpit fixes A/B/C** (NEW, UNFILED; live in the **livespec-console-beads-fabro**
  repo; cockpit-readiness theme — epic `g06` is CLOSED, so file a NEW epic/items).
  **Finding A is the critical-path blocker.**
- Stage-1 items are console-Rust → the FACTORY route for them is blocked by epic
  **`3lev` / `plan/fabro-ci-image-factoring/`** ("drop per-run rustup / bake Rust
  into the console sandbox image"). Stage 1 sidesteps this via sub-agents; the
  factory route only matters if Stage-1 fixes must ALSO go through the cockpit.
- The **factory OTel trace-egress gap** (also `3lev`, P-factory) leaves the
  dispatcher/fabro layer unobservable in Honeycomb — a Stage-2 confidence risk.

### RESUME ORDER (fresh session)
1. **File + fix Finding A (P1)** via a scoped sub-agent (resolver accepts the
   installed-cache flattened layout) → unblocks `just tui` on a normal host. Then
   B (header fits/degrades at 112) and D (add scroll affordances — stateful
   scroll-to-selection lists + scroll offset + scrollbar), then settle C.
2. Rebuild + relaunch the cockpit cleanly (no override once A lands) in
   `console-autonomous-mode` (112×28), from the tenant cwd you want to drive.
3. **Stage 2:** drive multiple real orchestrator-tenant Python items end-to-end
   through the TUI; maintainer as human-in-the-loop in `orchestrator-autonomous-mode`.
- Reap: core `docs-plan-autonomous-mode-dogfood` (this update). Cockpit left
  running (override-launched from the orchestrator cwd).

---

## SESSION UPDATE — 2026-07-12 (cont. 4): `fz4` DONE+proven-live; console cockpit-readiness all-but-`ecu` landed; `ecu` in flight → then I2

Driver session `autonomous-mode`. Cleared the `fz4` top priority AND drove the
console cockpit-readiness epic `g06` to near-completion. **RESUME: review+merge
`ecu`'s PR when it lands → then I2.**

### DONE this session
- **`fz4` (bump-pin docker format) — DONE + PROVEN LIVE.** dev-tooling PR #332
  merged → cut **v0.40.0**; the v0.40.0 fan-out bumped BOTH consumers' sandbox
  docker pins ATOMICALLY (orchestrator `v0.39.0→v0.40.0`, console
  `sha-ea684ad→v0.40.0`) alongside pyproject/compat. Grooming corrected the item
  (it was really a **5th** format, not 4th) and found the true surface = **3
  places**: the discovery walker (`pin_autodiscovery.py`, globs BOTH consumer
  roots), the composite-action rewrite `case` (`.github/actions/bump-pin-rewrite/action.yml`),
  and `SPECIFICATION/contracts.md`. Implemented via scoped sub-agent (not the
  factory — see below).
- **Interim lockstep check RETIRED.** orchestrator PR #533 merged (deleted
  `check-fabro-sandbox-image-pin-lockstep` + module + tests, rewrote the false
  workflow.toml PIN SURFACE NOTE); **`bd-ib-wwe` CLOSED**. `just check` 60→59.
- **Ledger status-conformance drift — FOUND + spun off (maintainer now DRIVING
  it).** The dispatcher's `ledger-check` rejects non-lifecycle statuses; a survey
  of all 8 fleet members found 2 drifted (dev-tooling 7×`open`; core 3×`in_progress`
  = the live `3lev` epic), the rest clean. NOT a blocker for autonomous-mode.
  Seeded `plan/ledger-status-conformance/handoff.md` (core PR #1101); the
  maintainer has since started driving it (master `c23133e`, "Scope 1 done").
- **Console cockpit-readiness (epic `g06`):**
  - **`003` (S1 resolver ladder) — CLOSED**, proven live (`serve --preview`
    resolves the orchestrator CLIs; observe→emit pipeline works).
  - **`gkh` (NEW, filed this session) — DONE.** The console couldn't observe real
    work-items: `parse_orchestrator_observation` rejected a present JSON `null` on
    `admission_policy`/`acceptance_policy` (`#[serde(default)]` only rescues a
    MISSING key). Fixed (`Option<_>`) + a SECOND blocker found via live-verify (a
    `lane:"open"` status-anchor record sank the whole array) → fail-soft per-record
    parsing. **LIVE-VERIFIED: orchestrator adapter now observes 206 work-items
    (was 0).** console PR #173 merged.
  - **`nyh` (S4) SPLIT** (maintainer-approved; it was oversized like `003`):
    `gu4` (S4a, `drive --repo` id→path invariant + guarding test — the prod fix
    was already in `003`; PR #172 MERGED, closed) → `ecu` (S4b, bind 5 valve
    keys; **IN FLIGHT via sub-agent**). `nyh` superseded/closed.
  - **`d6f` (S2 header source-unavailability indicator) — DONE.** Header now shows
    `sources: N unavailable (...)`; added a normative `contracts.md` clause +
    full console co-edit (counts→38/124, Scenario 13, history/v020). console PR
    #174 merged.

### KEY DECISIONS (maintainer-approved this session)
- **Console items go via SUB-AGENTS, not the factory.** The console Fabro sandbox
  has NO Rust toolchain, so `d6f`'s factory dispatch FAILED: the RGR commit's
  `just check-format` → `cargo fmt` pre-commit hook blocked it (no `cargo`;
  `--no-verify` forbidden). Root-caused from the fabro run log. **`fz4` exonerated**
  — both `sha-ea684ad` and `v0.40.0` images lack Rust equally; the console
  provisions Rust per-run (the "live-work tax" that epic **`3lev`** targets:
  "drop per-run rustup / bake Rust"). Until `3lev` bakes Rust, factory-dispatching
  console (Rust) items is unreliable → use sub-agents.
- **dev-tooling is NOT a lifecycle dispatch tenant** (raw `open` statuses fail
  `ledger-check`), so `fz4` went via sub-agent too, not the factory.

### FINDINGS worth follow-up (NOT filed as items; captured here)
- **Factory OTel trace-egress is BROKEN** (the deferred P-factory gap in `3lev`).
  Honeycomb `livespec` env has ONLY `github-ci`; the dispatcher/fabro
  orchestration layer emits NO spans anywhere (the ACP agents themselves emit to
  the `agent-activity` env, but not the fabro layer). So the factory is currently
  unobservable in Honeycomb — a real gap for diagnosing dispatch failures.
- **Orchestrator `list_work_items.py` lane-derivation gap:** it emitted `lane:"open"`
  (a raw beads status) for a status-anchor row (`bd-ib-98c`) — the second blocker
  `gkh` fail-soft-handled console-side. Real fix is orchestrator-side; likely
  related to the ledger-status-conformance drift the maintainer is driving.
- **Console local-gate fragility (3 sub-agents independently hit it):** on any dev
  host with an installed orchestrator-plugin cache, `just check` fails — 3
  non-hermetic `console-cli` tests + 1 coverage line, because `backing_cli`'s
  resolver only accepts a SOURCE layout (`.claude-plugin/scripts/bin/`) and
  rejects the flattened marketplace-cache layout (`scripts/bin/`). CI is green
  only because a fresh runner has no installed plugin. Workaround: run the gate
  under a mirror HOME excluding `~/.claude`. **Worth a console work-item** (accept
  the flattened cache layout OR make the 3 tests hermetic).

### OPEN WORKTREES to reap (deferred — `ecu` sub-agent is active in a console worktree)
Reap after `ecu` lands: dev-tooling `fz4-docker-pin` (PR #332 merged); orchestrator
`retire-fabro-image-pin-lockstep` (PR #533 merged); console `fix-gu4-drive-repo-path`,
`fix-gkh-null-policy-parse`, `feat-d6f-source-unavail-indicator` (all merged) +
`feat-ecu-valve-keys` (after it merges). core `docs-plan-autonomous-mode-session15`
(this update). Do NOT run the reaper while `ecu` is active.

### RESUME ORDER (fresh session)
1. **Review + merge `ecu`'s PR** (S4b valve keys) when the sub-agent reports —
   verify the 5 valves are TUI-invocable + confirm-modal for reject + the clause
   co-edit counts; then close `ecu` and the `g06` epic. `ecu` is the LAST
   cockpit-readiness slice.
2. **Reap the merged worktrees** (list above) once `ecu` is done.
3. **I2 — the maintainer-gated live autonomous-mode acceptance (the sole MVP
   step).** Now unblocked: cockpit observes real work (`gkh`), surfaces source
   unavailability (`d6f`), the 5 valves are TUI-bound (`ecu`), the resolver works
   (`003`). Recommended plant: a ledger-level `human-only` acceptance item (per the
   older I2 plan below). Flip autonomous mode ON from the TUI → engine drives ready
   work to `done` → console observes/reflects → a truly-unresolvable item surfaces
   in-TUI as an actionable needs-attention item. The maintainer's TUI acceptance IS
   the MVP "done."

---

## SESSION UPDATE — 2026-07-12 (cont. 3): Track A COMPLETE (golden master GREEN, merged, w4iaaf closed); bump-pin fix `fz4` is the NEW TOP PRIORITY

### ⇒ FIRST THING TO FIX (maintainer-directed 2026-07-12): `livespec-dev-tooling-fz4`
`livespec-dev-tooling-fz4` (P1, **dev-tooling tenant**) — teach `bump-pin`
(`pin_autodiscovery.py`) to rewrite the `workflow.toml` fabro-sandbox **docker image
tag** as the missing 4th pin format, so a dev-tooling release moves BOTH the pyproject
pin AND the sandbox image tag atomically (must cover BOTH `livespec-orchestrator-beads-fabro`
AND `livespec-console-beads-fabro`). This is the ROOT CAUSE of the recurring
`check-fabro-sandbox-image-pin-lockstep` local-red (v0.37, then v0.38→v0.39). Once it
lands, the orchestrator's private interim lockstep check can RETIRE, and the
orchestrator-tenant symptom tracker `bd-ib-wwe` can close (already prose-linked → `fz4`).
It's a groomable, factory-dispatchable dev-tooling work-item — **do this first.**

### Track A — COMPLETE ✅
The live golden-master is GREEN end-to-end and the factory is proven. **PR #530**
(`livespec-orchestrator-beads-fabro`) MERGED — 5 commits (custom-statuses, e2e-creds,
gate #6 dev-tooling dep, gate #7 harnesses, gate #10 uv/mise-exec). `bd-ib-w4iaaf`
CLOSED with live evidence. Verified `GM_EXIT=0` **on the actual merge state** (rebased
current on master → `v0.39.0` sandbox + 0.254.0 orchestrator image): dispatch →
implement → janitor → PR → MERGE → `asserted greeting: Hello, Ada!`, across throwaway
repos `livespec-e2e-{dl2b1h5j,nsmshwko,uub5ht1d,pm5nvuye}#1`. `just check` = all 60
targets pass. Worktree reaped; orchestrator primary clean on master.
- **Gate #8 was fabro-version IMAGE DRIFT, not a factory break** (0.290-nightly baked
  vs the 0.254 host); fixed by rebuilding `livespec-orchestrator:dev` with the
  `0.254+#568` fork. **CORRECTION:** the acp.command `{{ }}` item I filed (`bd-ib-41k`)
  was a DUPLICATE of pre-existing `bd-ib-6qu` — CLOSED, recipe folded. The plan (epic
  `bd-ib-2nq`, Rec A) deliberately STAYS on the 0.254+#568 fork because 0.254 PRESERVES
  `{{ }}` templating; the preferred exit is `bd-ib-2nq.4` (revert to canonical when
  upstream fabro #568 merges), NOT the 0.290 migration. See `plan/fabro-token-refresh/`.
- **The "lockstep decision" was a non-issue** — a transient bump-pin gap; master already
  had both pins at `v0.39.0` (folded into dispatcher-refactor `456e40e`); my branch was
  just stale and rebasing fixed it. The durable fix is `fz4` above.

### Cockpit-readiness (console tenant, epic `g06`) — partial
- **`fpo` (S3): ✅ done** (accepted; live evidence journaled).
- **`003` (S1, resolver ladder): WORK LANDED but NEEDS RECONCILIATION.** The 3-rung
  resolver merged via console **PR #169**; but the heavy-item dispatch didn't converge
  (re-opened a stale PR #170 — driver CLOSED it; dispatch STOPPED; `003` left orphaned
  `active`). Reconciliation context is journaled ON `003`. **Next: verify #169 satisfies
  003's full Definition-of-Ready LIVE** (`serve --preview` Lanes view actually POPULATES,
  not just merged — "done means exercised live"), then transition `003` out of `active`
  (do NOT re-dispatch). LESSON: re-groom heavy items finer before factory-feeding (the
  sizing WARN was right).
- After 003 is reconciled: dispatch **S2 `d6f`** + **S4 `nyh`** (parallel; both gate on S1).

### RESUME ORDER (fresh session)
1. **`fz4` — the bump-pin fix (maintainer's top priority).** Groom + implement/dispatch.
2. **Reconcile `003`** (verify #169's DoD live → transition out of `active`), then dispatch
   S2 `d6f` + S4 `nyh`.
3. **I2** (maintainer-gated live acceptance) — now unblocked by Track A green; also needs
   cockpit S4 (the "actionable in-TUI" DoD). Recommended plant: ledger-level `human-only`
   acceptance item (sidesteps orchestrator bug `bd-ib-18r`).
- Side-findings still open (not filed): the **root-owned `.pyc` pollution hazard** (every
  golden-master run writes root-owned bytecode into the host worktree → breaks `just check`
  until sudo-cleaned) and the **orphaned console items `6tn`/`6sf`** (reap at a boundary).

## SESSION UPDATE — 2026-07-12 (cont. 2): gates #6/#7 FIXED; gate #8 = golden-master IMAGE DRIFT (NOT a factory break); fpo ACCEPTED + S1 dispatched

Continuation. Big Track-A progress + the golden-master red decisively root-caused
as a benign fabro-version image drift, NOT a broken factory. Two background jobs
were IN FLIGHT at handoff — **re-verify their outcomes from ground truth (ledger +
throwaway-repo PR), do NOT trust this session's scratch logs (they don't survive).**

### Track A — golden-master substrate (the sole I2 prerequisite)
- **Gate #6 (dev-tooling dep): ✅ FIXED + committed** (`5083989` on branch
  `fix-golden-master-custom-statuses`). The e2e-skeleton `pyproject.toml` had
  `dependencies = []`; the UNMODIFIED production Fabro prepare chain runs
  `python -m livespec_dev_tooling.install_commit_refuse_hooks`, so the sandbox
  died `ModuleNotFoundError`. Added `livespec-dev-tooling` to the dev group +
  `[tool.uv.sources]` git pin `v0.39.0`. Pre-flight-verified (`uv sync` resolves +
  imports). Live-confirmed (re-run advanced PAST it).
- **Gate #7 (`harnesses` declaration): ✅ FIXED + committed** (`ad0c945`). Next
  prepare verifier `livespec_dev_tooling.checks.plugin_resolution` fleet-wide
  REQUIRES a top-level `harnesses` block in `.livespec.jsonc`. Added claude/codex
  `exempt` (a throwaway greeting skeleton has no interactive `/livespec:*` surface;
  `exempt` PASSes the verifier with no smoke run). Pre-flight-verified.
- **Gate #8 = IMAGE DRIFT, NOT a real factory break (decisively investigated).**
  The implement node died `/bin/bash: line 1: {{: command not found` (exit 127).
  Root cause: two different fabro binaries. Host + server + ALL real/shadow
  dispatches run fabro **0.254.0** (where `acp.command="{{ inputs.acp_adapter }}"`
  templating WORKS) — that is why `fpo` (PR #168, merged 04:57) and `003`/S1 are
  healthy. But the `livespec-orchestrator:dev` image accidentally baked fabro
  **0.290.0-nightly.0** (built 07-11 08:07 when `~/.fabro/bin/fabro` was
  momentarily the nightly; host later rolled back to 0.254.0), and fabro ≥0.290
  deprecates `{{ }}` templating outside `prompt`/`goal` → the literal `{{` is run
  as a shell command. `fabro validate` does NOT catch it (only a full `fabro run`
  does — which is why the earlier "non-fatal" read was wrong). **Fix = rebuild the
  image with the now-0.254.0 host fabro.** Host fabro IS 0.254.0 now (verified,
  matches `Dockerfile FABRO_VERSION=0.254.0`).
- **REBUILD DONE → factory GREEN (gate #8 resolved).** `acceptance-live-golden-master.sh
  --build-image --run` rebuilt `livespec-orchestrator:dev` with fabro 0.254.0 (image
  `78f8a2c02a90`, `ENV FABRO_VERSION=0.254.0`) and the golden master then **dispatched
  → implemented → janitored → opened AND MERGED a PR**: `merged PR #1` on throwaway
  `livespec-e2e-dl2b1h5j`, reflection `1 green / 0 failed`. The implement node
  templated `acp.command` correctly (no more literal `{{`). **The Beads/Dolt+Fabro
  factory demonstrably produces a merged PR end-to-end on 0.254.0.** This was the
  scary "is the factory broken?" question — answer: NO, it works.
- **Two POST-dispatch harness/env gaps remain (NOT factory failures):**
  - **Gate #9 (non-fatal WARN):** the post-merge janitor ran `just
    install-commit-refuse-hooks` in the merged throwaway repo, but the e2e-skeleton's
    `justfile` lacks that recipe → `janitor-env-degraded` warn (merge still confirmed
    green). Skeleton-fidelity follow-up: add an `install-commit-refuse-hooks` recipe
    to `orchestrator-image/e2e-skeleton/justfile` (calling
    `uv run python -m livespec_dev_tooling.install_commit_refuse_hooks`, now that the
    skeleton carries the dep). NON-BLOCKING.
  - **Gate #10 (FIXED + committed `e170e46`):** the golden master's FINAL host-side
    greeting assertion ran `uv run …` and died `uv: command not found` — the credential
    wrapper `with-livespec-env.sh` resets PATH to a base set that drops mise's tool dirs
    (verified: inside the wrapper `uv`=NOTFOUND but `mise`=`/usr/bin/mise`). Fix: route
    the assertion through `mise exec -- uv run` (cd `REPO_ROOT` so mise reads this
    repo's `.mise.toml`). This leg was only reached once the dispatch went green, so it
    surfaced only after gate #8.
- **✅ GOLDEN MASTER FULLY GREEN — `GM_EXIT=0`, verified live 3× (final run with the
  gate-#10 fix).** Each of three full runs drove a MERGED PR on a fresh throwaway repo
  (`livespec-e2e-{dl2b1h5j,nsmshwko,uub5ht1d}#1`), reflection `1 green / 0 failed`; the
  final run passed the greeting assertion (`asserted greeting: Hello, Ada! ==
  greet("Ada")`, `1 passed`) → `=== live golden-master PROOF COMPLETE ===`. The runs
  exercised the FULL flow: dispatch → implement → janitor → PR → merge → item parked in
  `acceptance` under `ai-then-human`. **Gate #8 resolved; the Beads/Dolt+Fabro factory
  is proven end-to-end.** Branch `fix-golden-master-custom-statuses` = 5 commits
  (custom-statuses, e2e-creds, #6 dep, #7 harnesses, #10 uv/mise-exec), rebased current
  on master, tracked-clean.
- **Recurrence-prevention TODO (NOT yet done — include in the Track-A PR):** add a
  build-time guard in `orchestrator-image/build-and-verify.sh` (after line 56,
  `"$HERE/fabro" version`) asserting the staged binary version == the Dockerfile
  `FABRO_VERSION`. Without it any future `~/.fabro/bin` drift re-poisons the image.
- **CORRECTION (2026-07-12): the `{{ }}`-in-`acp.command` breakage was already tracked;
  the item I filed for it (`bd-ib-41k`) was a DUPLICATE and is now CLOSED, folded into
  the pre-existing `bd-ib-6qu`.** `bd-ib-6qu` (P3, backlog — "Deferred: migrate
  self-hosted fabro 0.254 → 0.290, needs workflow migration") already owned this exact
  breakage (fabro #474, which removes `acp.command` templating, shipped v0.256-nightly)
  as its first scope bullet; the env-indirection migration recipe was folded there.
  **Framing correction — the plan does NOT migrate off `{{ }}`:** per epic `bd-ib-2nq`
  (maintainer Rec A), the fleet runs a self-hosted **fabro 0.254 + backported upstream
  #568 fork** (`~/.fabro/bin/fabro`, still reports `0.254.0`) PRECISELY BECAUSE 0.254
  preserves `{{ }}` templating (the fork does not contain fabro #474). The PREFERRED
  exit is `bd-ib-2nq.4` — revert the orchestrator image to canonical fabro once upstream
  fabro **#568** (a GitHub-App-token-refresh PR, unrelated to templating) merges + a
  release ships — NOT modernizing to 0.290. The 0.290 migration (`bd-ib-6qu`) is the
  deferred, non-preferred track. **So the gate-#8 `0.254.0` image rebuild above is
  CORRECT and plan-aligned** (the image should stage the `0.254+#568` fork binary; the
  drift to 0.290-nightly was a transient accident), not a workaround. See the
  `plan/fabro-token-refresh/` thread (`bd-ib-2nq`) for the fork/self-host design.

### Track A remaining (golden master is GREEN — package into the PR)
> The substantive work is DONE + proven live. What's left is mechanical PACKAGING
> plus ONE cross-thread decision (the lockstep, step 3) surfaced to the maintainer.
1. Add the build-and-verify.sh fabro-version guard (above). [optional-but-recommended]
2. **Clean the root-owned `.pyc` pollution** the golden-master run leaves in the
   worktree, or `just check` fails: `sudo find .claude-plugin/scripts -name
   __pycache__ -type d -prune -exec rm -rf {} +` (the sandbox runs as root and
   writes bytecode into the bind-mounted worktree; passwordless sudo is available).
3. **Resolve the LOCKSTEP pre-push blocker.** `check-fabro-sandbox-image-pin-lockstep`
   fails LOCALLY (pre-push) but master CI is GREEN — a pre-existing MASTER condition
   from the dev-tooling-flip thread: pyproject pins dev-tooling `v0.39.0` but
   `workflow.toml` line 153 pins sandbox image `livespec-fabro-sandbox:v0.38.1`. The
   `v0.39.0` image EXISTS on GHCR → bump line 153 to `v0.39.0`. (Cross-thread: this is
   the `fleet-check-coverage`/dev-tooling-flip domain; bumps to the same tag converge,
   so low collision risk. Also repairs master's local-red.) **CAVEAT: this changes the
   sandbox for EVERY dispatch, and the current `GM_EXIT=0` was with the `v0.38.1`
   sandbox — so after the bump, RE-RUN the golden master to confirm green with the
   `v0.39.0` sandbox before pushing** (the merge state owes its own live-verify). This
   coupling (lockstep bump ⇒ golden-master re-verify) is exactly why it's a
   maintainer-surfaced decision, not a silent self-resolve.
4. Push (`--force-with-lease` — my thread's own branch, no PR) → open PR → merge
   (rebase) → **close `bd-ib-w4iaaf`** → refresh primary. → **I2 unblocked.**

### Cockpit-readiness (console tenant, epic `g06`)
- **`fpo` (S3): ✅ ACCEPTED → done.** Journaled live-exercise evidence onto the item
  first (PR #168/`041343d` on master + Rust Red-Green pair + prior live repro), then
  accepted via `drive --action accept:livespec-console-beads-fabro-fpo --repo
  <console>` (CLI, because S4 valve keys aren't bound yet — the known hole; this CLI
  accept IS the documented bootstrap + a live demo of it).
- **`003` (S1, resolver ladder): promoted backlog→ready + DISPATCHED** via
  `dispatcher.py dispatch --repo <console> --item ...-003` (background `b7o17zqt3`).
  Still `active`/`fabro`, `updated_at` unchanged since 06:18 at handoff (~48+ min).
  The dispatcher WARNed it is a heavy item (2555 chars, "3 enumerated parts" = the 3
  resolver rungs) that may exceed one unattended ACP turn. **WATCH: if it stalls/
  orphans rather than merging a PR, S1 needs a finer maintainer-owned re-groom.**
  VERIFY its outcome from the ledger + console PRs. (Explicit `--item` dispatch
  bypasses the WIP cap, so the stale `active` `6tn` didn't block it.)
- After S1 lands: dispatch **S2 `d6f`** (header/status source-unavailability
  indicator) + **S4 `nyh`** (bind the 5 valves to TUI keys + fix `drive --repo`
  id→path) — parallel (both depend only on S1). S1's DoD requires the Lanes view to
  actually populate, not just PATH-resolve.

### Side-findings (logged, not acted on)
- **Recurring root-`.pyc` pollution hazard:** every golden-master run leaves
  root-owned bytecode in the worktree (breaks `just check` until sudo-cleaned).
  Worth a durable fix (sandbox shouldn't write root-owned files into the host
  worktree, or auto-clean post-run). Not filed yet.
- **Orphaned console items `6tn` (active) + `6sf` (ready)** — fabro-assigned,
  created 2026-07-08, trivial doc-comment tasks, stale factory cruft. Reap at a
  clean boundary — NOT while S1's dispatch is active.

### State at handoff
- Branch `fix-golden-master-custom-statuses` (orchestrator): **5 commits** — `4c07449`
  (custom statuses), `7918506` (e2e `*_E2E` creds), `5083989` (gate #6 dep),
  `ad0c945` (gate #7 harnesses), `e170e46` (gate #10 uv/mise-exec). Rebased current on
  master, tracked-clean, **golden master GM_EXIT=0**, NO PR yet (blocked on the
  lockstep, step 3).
- Worktrees: KEEP orch `fix-golden-master-custom-statuses` (Track A). REAP after
  merge: core `docs-plan-autonomous-mode-gate8` (this handoff PR). Not mine, leave:
  orch `fix-embedded-ledger-credential-precheck`, `plan-codex-factory-telemetry`.
- Background jobs do NOT survive the session — re-verify `b7o17zqt3` (S1) from the
  ledger / console PRs, not scratch logs. (The golden-master runs already completed
  green; nothing pending there.)

### RESUME ORDER (fresh session)
1. **Golden master is GREEN (GM_EXIT=0, verified 3×) — go straight to packaging:**
   Track-A remaining steps 1–4 above. Step 3 (the lockstep bump) is the ONE
   cross-thread decision surfaced to the maintainer — resolve that, then clean
   pollution, push (`--force-with-lease`), open PR, merge, **close `bd-ib-w4iaaf`**.
2. **Verify S1 `003` outcome**; if stalled/orphaned, re-groom (maintainer-owned cut).
3. After S1 green: dispatch S2 `d6f` + S4 `nyh` (parallel).
4. **I2** (maintainer-gated live acceptance) after the golden master is green AND S4
   lands (the "actionable in-TUI" DoD depends on S4).

## SESSION UPDATE — 2026-07-12 (cont.): cockpit-readiness FILED + fpo through factory + e2e App created; golden-master at gate #6

Continuation of the DOGFOODING SESSION below. Big progress on BOTH tracks; the
sole remaining Track-A blocker is now a NEW substrate gate (#6), fully diagnosed.

**Cockpit-readiness epic — FILED + first slice landed (console tenant):**
- Groomed cut (maintainer-approved) filed to the console ledger: epic
  **`livespec-console-beads-fabro-g06`** + **S1 `003`** (orchestrator-plugin
  resolver ladder) / **S2 `d6f`** (header/status source-unavailability
  indicator) / **S4 `nyh`** (bind the 5 valves to TUI keys + fix `drive --repo`
  id→path). **S3 reconciled to the pre-existing `fpo`** (u64→i64 stream_seq
  overflow + per-record backfill isolation). Layering `fpo → 003 → {d6f, nyh}`.
  Decisions baked in: S1 = resolver ladder (env→governed-checkout→installed-cache,
  like the Drivers resolve core) + loud "not observed"; S2 = header/status
  indicator; S3 = 63-bit mask + isolation; S4 id→path via S1's resolver.
- **`fpo` (S3) went fully through the factory:** dispatched via
  `dispatcher.py dispatch --repo <console> --item <fpo> --json` → **PR #168**
  merged + post-merge janitor green (`041343d fix: cover source adapter append
  isolation`). VERIFIED LIVE: rebuilt the console binary, re-ran the Finding-#3
  repro (`serve --preview` from the orchestrator-repo cwd) → **crash gone**
  (`store ready, backfill events: 5`). fpo is now PARKED in `acceptance` under
  the `ai-then-human` policy — **awaits a HUMAN accept** to reach `done` and
  unblock S1. (Accepting it is itself a valve → blocked from the TUI by Track
  D/S4 — a live demonstration of the hole; drive it CLI-side for now.)
- Refined finding for S1: making the CLIs resolve on PATH is NECESSARY BUT NOT
  SUFFICIENT — with read-shims in place the cockpit's **Lanes view still showed
  0**; S1 must wire the full observation path + verify views populate, not just
  PATH-resolve.

**Track A — the e2e GitHub App is CREATED + wired (bd-ib-w4iaaf provisioning DONE):**
- Created **`livespec-e2e-pr-bot`** (org-owned by the `livespec-e2e` org), **App
  ID `4277313`**, **installation `146007016`**, **All-repositories** install
  (covers dynamically-created throwaway repos), permissions matching the fleet
  App `livespec-pr-bot` exactly (contents/pull_requests/workflows=write,
  metadata=read), webhook off. Done in the maintainer's Chrome via Playwright
  (manifest flow failed on a serialization quirk; used the UI form + direct
  hidden-input permission setting + `form.submit()`).
- Creds imported (by the maintainer) into the livespec 1Password environment
  (`fufpvkvatwkmqjzvilvfnemsue`) under **`GITHUB_APP_ID_E2E` /
  `GITHUB_PRIVATE_KEY_E2E` / `GITHUB_APP_INSTALLATION_ID_E2E`** — verified
  present; fleet generics untouched (no collision). Raw PEM at
  `/tmp/livespec-e2e-app/private-key.pem`; `.env` at `/tmp/livespec-e2e-app.env`.
- Golden-master wired to PREFER the `_E2E` vars over the fleet generics: `chore`
  commit **`5d7ca36`** on branch `fix-golden-master-custom-statuses` (pushed).
  Container contract unchanged (`GITHUB_APP_ID` etc. per contracts.md
  §"Self-contained plugin dispatch") → **no spec change**.
- **SECURITY:** a bad `mint_app_token.py --help` call (that CLI has no `--help`;
  it MINTS + prints a token) exposed a live FLEET App installation token; it was
  **revoked (204)** immediately. LESSON: never run `mint_app_token.py` to "check
  help" — it emits a real token.

**Golden-master live run (`bix746u20`) — PASSED the App gate, FAILED at gate #6:**
The e2e App WORKS: preflight green, throwaway repo created + seeded + pushed
(host-side via `LIVESPEC_E2E_GITHUB_TOKEN`), dispatch reached the Fabro sandbox
which **cloned + pushed the repo using the e2e App**. It then failed at the
sandbox SETUP step: `uv run python -m livespec_dev_tooling.install_commit_refuse_hooks`
→ **`ModuleNotFoundError: No module named 'livespec_dev_tooling'`**. Root cause:
the e2e-skeleton (`orchestrator-image/e2e-skeleton/pyproject.toml`) carries
`dependencies = []`, so the fleet-default prepare chain (which assumes
`livespec_dev_tooling`) can't run. This IS the v024-flagged "prepare steps are
per-target facts, not fleet constants" gap — tracked as **`bd-ib-z2ctra`**. Also
observed: `workflow.fabro` `acp.command="{{ inputs… }}"` triggers
`detemplated_attribute` warnings (current Fabro deprecated templating outside
`prompt`/`goal`) — a currency issue to fix alongside.

**RESUME ORDER (fresh session):**
1. **Gate #6 (Track A):** fix the e2e-skeleton prepare chain so the sandbox setup
   succeeds — either add `livespec_dev_tooling` to the e2e-skeleton deps, OR give
   the skeleton a target-local workflow with a prepare step that doesn't assume
   the fleet toolchain (v024 escape hatch / `bd-ib-z2ctra`); also refresh
   `workflow.fabro`'s deprecated `acp.command` templating. Re-run from the
   `fix-golden-master-custom-statuses` worktree:
   `/usr/local/bin/with-livespec-env.sh -- bash orchestrator-image/acceptance-live-golden-master.sh --run --poll-attempts 80`.
   When green → open+merge that PR → close `bd-ib-w4iaaf` → I2 unblocked.
2. **Cockpit-readiness:** CLI-accept `fpo` (unblocks S1) → dispatch S1 `003`
   (`dispatcher.py dispatch --repo <console> --item …-003`) → then S2 `d6f` / S4
   `nyh`. Continue driving via the TUI in `console-autonomous-mode`.
3. **I2** (maintainer-gated live acceptance) after the golden-master is green.
4. Interim dogfooding tooling (scratch, LOCAL): `…/scratchpad/consolebin*/` shims
   + `launch-cockpit-{orch,console}.sh`; delete once S1 lands. Console-tenant
   cockpit works; orchestrator-tenant cockpit's Finding-#3 crash is now fixed on
   master.

## DOGFOODING SESSION — 2026-07-12 (driver `livespec-autonomous-mode`): cockpit-readiness epic opened

Resumed under directive #3 (dogfood the console TUI). Launched the live console
TUI in tmux session `console-autonomous-mode` (`just tui`; builds + runs under
`with-livespec-env.sh`). Driving it immediately forced THREE usability holes.
This supersedes "A→D→C→B" ordering: the cockpit itself is not yet drivable, so a
new **console "cockpit-readiness" epic** is opened and (maintainer-chosen)
runs **in PARALLEL** with Track A.

**Findings (from driving the real TUI):**
- **#1 blind cockpit.** The console's backing CLIs (`needs-attention`,
  `list-work-items`, `livespec-orchestrator-drive`, `livespec-dispatcher-drain`,
  `livespec`) don't resolve on PATH — even under the wrapper — so live views
  (Attention/Lanes/Spec) silently show empty; only event-store views
  (Events/Repos) populate. **Decision (maintainer): fix via a RESOLVER LADDER** —
  the console locates the orchestrator plugin the SAME way livespec Drivers
  resolve core (env override → governed checkout → installed cache) and invokes
  its scripts directly; no PATH shims; serves Track C (downloadable deliverable).
  Sub-finding: degradation is SILENT (no "not observed" surfaced).
- **#2 valves unbound (== Track D).** `?` help confirms only `a` (autonomous
  toggle), `:` (drain), and nav are bound; the five per-item valves
  (approve/accept/reject/set-admission/set-acceptance) have NO TUI key.
- **#3 hard crash on backfill (NEW).** `serve` from the orchestrator-repo cwd
  dies at startup with `Adapter(AppendFailed)` during its journal backfill;
  `doctor` (no backfill) is fine. Isolated: console-cwd works, orchestrator-cwd
  fails, repo-id-alone is fine. A HARD crash, not the README's promised graceful
  "not observed" degradation — so the cockpit can't even START against the
  data-rich tenant.

**Cockpit-readiness epic (console tenant) — 4 slices, groomed (maintainer-owned
cut) + factory-dispatched:** S1 resolver ladder (#1) · S2 loud "not observed"
(#1 sub) · S3 backfill robustness (#3) · S4 valve keybindings (#2/Track D). A
read-only grooming-DRAFT sub-agent was dispatched (root-cause #3 + draft slices
w/ Definition-of-Ready + console clause-gap-id co-edit discipline) for maintainer
approval before any `capture-work-item` filing. These are console-repo work-items
dispatchable through the factory NOW (factory works for the console tenant);
bootstrap: dispatch/observe via the orchestrator CLI until the cockpit drives
itself.

**Track A status: BLOCKED on a HUMAN valve.** `bd-ib-w4iaaf` (orchestrator
tenant) is `blocked` = "provision a GitHub App installation covering the
livespec-e2e throwaway repos" — a GitHub org-settings act, NOT factory-executable
(surfaced live as a `set-admission:bd-ib-w4iaaf:manual` needs-attention valve).
The golden-master live run canNOT go green until the maintainer provisions this
Fabro App installation. Track A's branch `fix-golden-master-custom-statuses`
(orch, `a102190`, unverified, no PR) waits behind it.

**Interim dogfooding tooling (scratch-only, LOCAL, not committed):** under the
session scratchpad `…/scratchpad/` — `consolebin/` (shims resolving the backing
CLIs to the orchestrator plugin `.venv` scripts, the Finding #1 workaround) +
`launch-cockpit-orch.sh` (console TUI vs the orchestrator tenant). NOTE the
orch-tenant launcher currently trips Finding #3 (backfill crash); the
console-tenant cockpit (`just tui` from the console repo) launches clean but is
data-light (attention 0). Delete this scratch when S1/S3 land.

**Resume order (this session):** (1) synthesize the grooming-draft sub-agent's
output → present slices for maintainer approval → `capture-work-item` the epic +
S1–S4 in the console tenant → factory-dispatch. (2) Surface `bd-ib-w4iaaf` to the
maintainer as the Track A human gate. (3) I2 stays last + maintainer-gated; its
"actionable in-TUI" DoD now depends on S4. Tracks B/C unchanged (delegate).

## WIND-DOWN STATE — 2026-07-12 (superseded by the DOGFOODING SESSION above; kept for prior context)

Track A (repair the embedded golden-master → run I2) is mid-repair; Tracks B/C/D
pending; two doc PRs merged; two sub-agents were in flight at wind-down.
Everything below this section is prior context.

**Landed / in-flight this session:**
- **Embedded beads-client fix — MERGED** (`livespec-orchestrator-beads-fabro`
  PR #489 credential precheck; PR #508 `connection.prefix` + `invoke`
  embedded-awareness; releases 0.17.15 / 0.17.23).
- **Golden-master staleness repair — UNVERIFIED, on branch
  `fix-golden-master-custom-statuses` (orchestrator, commit `a102190`, NO PR
  yet).** Adds gate #4 (register custom statuses after `bd init`) + gate #5 (seed
  the item as `ready` + read `--status ready`). **NEXT: run it live to verify**,
  from its worktree
  (`~/.worktrees/livespec-orchestrator-beads-fabro/fix-golden-master-custom-statuses`):
  `/usr/local/bin/with-livespec-env.sh -- bash orchestrator-image/acceptance-live-golden-master.sh --run --poll-attempts 80`.
  Open question the run answers: does a `ready` item clear the
  Definition-of-Ready ledger checks, or need more fields? If green → open+merge
  that PR, then the autonomous I2. If a gate #6 appears → keep going (maintainer:
  "whatever it takes").
- **Console TUI docs — MERGED** (`livespec-console-beads-fabro` PR #165 TUI
  guide; core PR #1077 README blurb + the SESSION UPDATE below).
- **TUI usability PR — IN FLIGHT at wind-down** (delegated console sub-agent:
  `just tui` recipe + `?` help overlay + ↑/↓ focus-nav). Check
  `livespec-console-beads-fabro` for its PR and merge if green. (Maintainer's
  live-test "pathing error" on run 2 = a copy-paste hyphen-split of the long
  binary name, not a bug; `just tui` fixes it.)

**Embedded golden-master gate ledger (context):** credential precheck ✓(#489) ·
`connection.prefix` ✓(#508) · `invoke` embedded ✓(#508) · custom-statuses
✓(branch `a102190`, unverified) · seed-as-ready ✓(branch `a102190`, unverified) ·
[next live run reveals a gate #6 if any].

**Open worktrees:** `fix-golden-master-custom-statuses` (orch — the live repair,
keep) and `docs-plan-handoff-winddown` (core — this update). The stale
`fix-embedded-ledger-credential-precheck` (orch, merged branch + now-redundant
uncommitted edits) can be reaped.

**Resume order (A→D→C→B, maintainer-chosen):**
1. Verify + land the golden-master repair (branch above) → live golden-master GREEN.
2. **Autonomous I2:** parameterize the golden-master with `--mode autonomous` +
   the VALIDATED human-only plant (`bd config set status.custom …`; `bd update
   <id> --status acceptance`; `bd update <id> --add-label acceptance:human-only`);
   assert ready→`done` + `autonomous-decision` audit records + the human-only
   item rests in `Lane::Acceptance`; then the console observe/reflect leg + the
   MAINTAINER's TUI acceptance (the human core of I2 "done").
3. Track D (wire TUI valves), Track C (console release-binary publishing via
   release-please + CI), Track B (golden-master anti-rot cadence: daily +
   pre-release blocking gate, capped whole-test retry-backoff 1min→10min→fail).
   DELEGATE these per directive #2.

## SESSION UPDATE — 2026-07-12 (driver `autonomous-mode`): I2 unblocking + new deliverables

**"ONLY I2 remains" is superseded.** Driving I2 live surfaced that the
disposable-tenant factory substrate had bit-rotted and that the console is not
yet a real (downloadable) deliverable. The MVP now carries FOUR tracked
additions (A–D). **Landed this session:**
- **Orchestrator credential precheck fix — MERGED** (`livespec-orchestrator-beads-fabro`
  PR #489, release 0.17.15): the dispatcher bootstrap demanded
  `BEADS_DOLT_PASSWORD` even for EMBEDDED ledgers (which need none); now derived
  from `.beads/config.yaml` `dolt.mode: server`. Exercised live.
- **Orchestrator test-hermeticity fixes — MERGED** (`livespec-orchestrator-beads-fabro`
  PR #488): two non-hermetic tests that reddened local `just check` on a
  dogfooding host (codex-resolution reading real `~/.codex`; a reflector line
  needing `claude` absent).
- **Console TUI docs — IN FLIGHT**: console README "Running the console (TUI)"
  guide (`livespec-console-beads-fabro` PR #165, up); main livespec README
  console blurb (the PR carrying this update).

### Track A — repair the embedded factory substrate (I2 prerequisite)
The core beads CLIENT dropped embedded-ledger support (accumulated
server-mode-assuming gates). Gates found in the dispatch path:
1. bootstrap credential precheck — **FIXED** (`livespec-orchestrator-beads-fabro` PR #489).
2. `resolve_store_config` requires `connection.prefix`, absent from the
   e2e-skeleton — **FIXED in a worktree, NOT yet committed/PR'd.** The 2
   recoverable edits: `orchestrator-image/e2e-skeleton/.livespec.jsonc`
   connection block gains `"prefix": "e2egreet"`; `acceptance-live-golden-master.sh`
   `bd init --prefix "e2egreet"` (was `"${rand}greet"`).
3. `_beads_client_shell.py::invoke` demands `BEADS_DOLT_PASSWORD` AND asserts a
   SERVER tenant identity match — both meaningless for embedded — **PENDING.**
Maintainer chose **option 1 (holistic)**: make the beads client embedded-aware
(embedded → skip the password + tenant-match; server path untouched), with the
fix's own ritual tests. Capped per gate: if fixing #3 reveals yet another
embedded gate, reassess vs. the server-tenant-pivot alternative.

### Track B — anti-rot cadence for the live golden-master (NEW, maintainer-directed)
The live golden-master (`acceptance-live-golden-master.yml`) is NON-BLOCKING +
operator-triggered only, so it rotted silently while the dispatcher's
credential/config layers evolved (the per-PR `acceptance` check is a HERMETIC
mirror that never exercised the embedded path). Close the gating hole with
BOTH a **daily** scheduled run that REDS master on failure AND a **pre-release
blocking gate** — engineered against transient live-infra flake: tight inner
retries around infra calls PLUS a capped whole-test retry-with-backoff (fail →
wait 1 min → retry → fail → wait 10 min → retry → then real failure). Red ONLY
on a genuine dispatch/merge/greeting-assert failure. Token burn per run is
small.

### Track C — console release-binary publishing (NEW, maintainer-directed)
`livespec-console-beads-fabro` has **no release pipeline**: no release-please,
no CI build-and-attach job, zero published releases — the only way to get it is
a source build. Per the maintainer, "it's not a real deliverable until it's
published on the version schedule via release-please." Deliverable: add
release-please + a CI job that cross-compiles the standalone binary and
attaches it to each GitHub Release on the version schedule. **Gates the MVP
being a REAL deliverable** (the operator must download the cockpit, not compile
Rust). File as a console-repo epic.

### Track D — wire the operator valves into the TUI (NEW, verified gap)
The per-item valves (approve / accept / reject / set-admission / set-acceptance)
are server-side command handlers but are NOT bound to any TUI key (verified:
`console-tui` constructs none of the valve command types; the command palette
recognizes only `drain`). I2's DoD requires the truly-unresolvable item to
surface in-TUI as an **actionable** needs-attention item; today it surfaces
(flagged + shown in Detail) but is not TUI-actionable. Likely an additional MVP
deliverable — confirm scope with the maintainer.

### Next-session resume order
1. Finish Track A: commit the `connection.prefix` fix + land the beads-client
   `invoke` embedded fix (option 1), then run the live golden-master GREEN
   (from a checkout carrying the fixes — the dispatcher runs from the
   bind-mounted repo, no image rebuild).
2. Build + run the autonomous I2 on the now-green substrate (embedded tenant +
   `--mode autonomous` + the VALIDATED human-only plant: `bd config set
   status.custom "..."`, `bd update <id> --status acceptance`, `bd update <id>
   --add-label acceptance:human-only`). Assert ready→done + `autonomous-decision`
   audit records + the human-only item rests in `Lane::Acceptance`.
3. Land Tracks B, C, D (each its own PR/epic). Track D likely blocks the full
   I2 "actionable in-TUI" DoD; Track C blocks "real deliverable."
4. The MAINTAINER's TUI acceptance is the human core of I2 "done."

Everything below predates this update; trust this section for current state.

---

**Status: C3 COMPLETE (2026-07-11) — ONLY I2 (end-to-end live exercise = MVP
"done") REMAINS. Step 0 + O1 + C1 ratified; O2 (orchestrator engine, 4/4)
COMPLETE; C2 (console command foundation, 5/5) COMPLETE; persistence-seam
RATIFIED to console v018; and now C3 (console autonomous feature — 3/3 slices
`rt4.1/.2/.3` + folded finding `d6o`) COMPLETE, all merged, post-merge-reviewed
SOUND, console master green (`e749a6c`). The maintainer CHECKPOINTED AGAIN at
C3-complete (2026-07-11) before I2 — the maintainer-gated MVP acceptance. See
"## Build phase progress" (the C3 record) + "## Remaining to MVP" (the I2 plan +
recommendation) below for the next session's resume pointers.** The Step-0
fable-review loop exited (round-6 NOTHING-BLOCKING + maintainer certification, in
the Loop state below); the driver dispatched O1 and C1 as scoped subagents and
drove each through propose-change → independent read-only Fable review → revise.

**Ratification record (2026-07-10):**
- **O1 → orchestrator v033 (RATIFIED).** Two propose-changes (irreducible human
  touchpoints; arming/audit contract): filed by the delegate (orchestrator
  PR #415), reconciled by the driver toward a fuller parallel maintainer/Fable
  draft (folded amendments K/L/O + the Scenario-33 routine qualifier; PR #416),
  Fable-reviewed NOTHING-BLOCKING, revised accept/accept to v033 (PR #417).
  **Arming/audit contract FROZEN → overall I1 SATISFIED** → console C3 and
  orchestrator O2 unblocked. On master: `drive --mode autonomous`=0;
  `loop --mode autonomous` is the mode surface; the design-human-gated set +
  `human-only` carve-out + single-persistent-permission key are live.
- **C1 → console v017 (RATIFIED).** Two propose-changes (citation-currency;
  autonomous-resolution delegation): filed (console PR #147), Fable-reviewed
  NOTHING-BLOCKING, revised accept/accept to v017 (PR #149) with a
  behavioral-coverage lockstep co-edit (process note below). MAIN ratification
  done; the persistence-seam amendment stays DEFERRED but is now I1-unblocked.
  `rt4` version pointer refreshed v013→v016.
- Reaped two stale/absorbed branches: orchestrator
  `o1-autonomous-mode-touchpoints-arming` (absorbed parallel draft; source at
  git 1f25529 + driver scratchpad), console `autonomous-mode-c1-spec-currency`
  (empty stale).

**PROCESS NOTE (carry forward) — console behavioral-coverage co-edit.** The
console repo's coverage gate binds normative-CLAUSE gap-ids (content-hashes of
each MUST/SHOULD line) to scenarios — NOT H2 names. ANY console spec revise that
adds/removes/rewords a normative clause REQUIRES a lockstep co-edit
(`tests/heading-coverage.json` clause-gap-id rebinding + the
`crates/console-spec-check/src/tests.rs` ground-truth count refresh) even with
zero `## ` H2 changes — the console analogue of core's H2 heading-coverage
co-edit (precedent: console v016 CN1 + v014). Future console propose-changes
should carry this in their `resulting_files`.

## Build phase progress (2026-07-11 — driver session `autonomous-mode`)

The maintainer resumed the build phase 2026-07-11. Both grooming cuts were
drafted by scoped read-only delegates, ACCEPTED by the maintainer, and FILED:

- **Orchestrator `bd-ib-82a` → 4 slices** (`.1` two-factor arm / `.2` per-decision
  audit record + published read surface / `.3` two-valve collapse / `.4` in-band
  LLM `needs-human` resolve-or-escalate). Epic re-based v025→v033, surface
  `loop --mode autonomous`. Backstop for the spec-change tier = option (a): a
  conservative guard on the existing `spec_commitment_hint` signal, NO new field.
- **Console `pke3y3` → 4 slices** (`.1` shared `drive` port + approve / `.2`
  accept+reject / `.3` set-admission / `.4` set-acceptance), re-based onto the
  v017 valve model; the 4 still-contract factory/spec commands split to new
  sibling `8aw`; the 3 v014-retired commands dropped. All five commands ride ONE
  shared `drive` port + a single `work_item.action.*` event family (thin console
  validation; orchestrator is state-legality authority). `mb64bv` was already
  landed (rename in `3eca905`) → CLOSED as already-fixed; con-S4's supposed block
  was illusory.

**Merge posture (maintainer-approved 2026-07-11): auto-merge-on-green +
post-merge review.** The approved intent is NO pre-merge gate: a green PR merges
and the driver reviews AFTER, reverting only on a real problem (revert is
driver-held). CORRECTION (found during C3): the
`livespec-console-beads-fabro` repo has NO auto-merge bot and NO `livespec-pr-bot`
(only `ci.yml` + `bump-pin-from-dispatch.yml`); its green PRs merge by the
delegate/driver running `gh pr merge --rebase` (recent PRs showed `autoMerge=yes`
only because someone's token ENABLED auto-merge — the `mergedBy: thewoolleyman`
just reflects who enabled it). So under the approved posture the merger IS the
delegate/driver, not a bot; each C3 slice delegate rebase-merged its own green PR
and the driver post-merge-reviewed the diff on master. Do NOT wait on a
nonexistent bot. Full worktree/TDD/`just check` discipline unchanged; delegates
halt-and-report on any red.

**O2 (orchestrator engine): COMPLETE.** All four `bd-ib-82a` slices merged,
reviewed sound, closed; master CI green; releases 0.14.0–0.17.0. orch-S4's
in-band LLM `needs-human` stage (`resolution_resolves`) fails safe toward
escalation on every branch (not-confident / design-gated / `human-only`), the
production resolver fail-safes to escalate on any subprocess/parse error, and
not-armed behavior is exactly the pre-existing bounce.

**C2 (console command foundation): COMPLETE — 5/5 commands merged** (con-S1
drive-port+approve / con-S2 accept+reject / con-S3 set-admission / con-S4
set-acceptance, which extended read-side `AcceptancePolicy` to
`{ai-only,human-only,ai-then-human}`). All reviewed sound; Scenario 11 fully
bound; `pke3y3` epic + all children closed. One follow-up FILED for C3:
`livespec-console-beads-fabro-d6o` — `requires_attention_from_lane`
(`console-application/src/lib.rs`) flags `AiThenHuman` in the Acceptance lane but
NOT `HumanOnly`; VERIFY where a `human-only` item lands and, if the Acceptance
lane, extend the arm (latent until C3 wires policy-setting into the TUI).

**Persistence-seam amendment: RATIFIED → console v018** (`e741af8`). Dropped the
console's own `autonomous_mode.enabled` persistence clause; the console now
derives/reflects the mode from — and writes it through — the orchestrator's
single `dispatcher.autonomous_mode` permission key (per O1 v033). Independent
Fable review = NO-BLOCKERS (gap-ids + counts verified computationally); the
revise folded two Fable advisories (`console-spec-check` total 123→122 + comment;
Scenario-9 `reason` reword). This CLOSES the last residual of cross-repo risk #1
(persistence-model seam).

**Orchestrator repo hygiene: one flaky test fixed (parallel, unrelated).**
`test_receiver_oversized_body_is_bad_request` (OTLP receiver) was root-caused as a
REAL socket RST race (a hard close with an unread request body emits RST not FIN)
and fixed with a lingering close + a bounded/timed/fail-open drain (PR #448,
release 0.17.2), verified by 325 repeated runs — not `@flaky`/skipped.

**Operational learnings (carry forward):**
- Dispatching build executors as context-inheriting FORKS spikes tokens (a fork
  inherits the parent delegate's large context) and hit a session rate limit
  mid-build. Prefer LIGHT self-contained general-purpose agents for executors.
- An idle subagent does NOT self-wake on external CI completion — the driver (or
  the delegate's own Monitor) must watch master CI and nudge/close the slice.
- Concurrent slices editing the same file (orch-S3/S4 both touched
  `dispatcher.py`) need the second-to-merge to rebase-own-branch +
  `--force-with-lease`; the bot will NOT auto-merge a CONFLICTING PR. Sequence,
  or accept the rebase on the second.
- Two session rate-limit interruptions cost only build/coordination time — no
  landed work was lost (committed slices + unpushed local branches all recovered;
  a merged-but-not-yet-closed slice is normal serialized-close lag, not failure).

## Remaining to MVP — I2 only (C3 is DONE)

**C3 — console autonomous feature: COMPLETE (2026-07-11).** Groomed
(maintainer-approved 3-slice cut) from epic `rt4` into `rt4.1/.2/.3`; all merged,
post-merge-reviewed SOUND, console master green (`e749a6c`); epic + all children +
folded finding `d6o` CLOSED:
- **`rt4.1` (console PR #160, `395fa87`)** — the Configuration context:
  `config.autonomous_mode_set` (confirmed-guard rejects an unconfirmed enable with
  NO effect — no port call, no key write, no audit event); the
  `factory.autonomous_mode_{enable,disable}_requested` commands +
  `LivespecJsoncArmingPort` that writes the orchestrator `dispatcher.autonomous_mode`
  key DIRECTLY in the consumer `.livespec.jsonc` (declarative shared config;
  comment-preserving minimal edit); the `config.autonomous_mode.{enabled,disabled}`
  audit events; `read_autonomous_mode_from_jsonc` derive-on-read (absent = disabled).
  `not_wired` honesty, never fabricated success.
- **`rt4.2` (console PR #162, `e749a6c`)** — the TUI surface: autonomous toggle,
  "dangerous / use with caution" label, type-to-confirm modal (enable only; disable
  no-confirm; submits `confirmed:true`), header mode indicator DERIVED-and-reflected
  (never owned).
- **`rt4.3` (console PR #161, `747a81c`)** — the autonomous RUN: the factory-drain
  launcher passes `--mode autonomous` to `loop` (re-derived per drain from the key;
  NOT `drive`); observe/reflect via `JournalAutonomousDecisionsPort` mirroring the
  orchestrator's published `read_autonomous_decisions`, reflecting each
  auto-resolution through the console's OWN command+outcome-event path
  (`factory.autonomous_decision_reflected` + `attention_item.resolved`; idempotent;
  NO console-side resolver, no double-resolution); truly-unresolvable left in the
  inbox; folded `d6o` (VERIFIED: a `human-only` acceptance item rests in
  `Lane::Acceptance`, so `requires_attention_from_lane`'s Acceptance arm extended to
  `AiThenHuman | HumanOnly`, AiOnly unflagged).

**I2 — end-to-end live exercise (MVP "done"): the SOLE remaining step;
maintainer-gated.** Gate: C3 ✓ + O2 ✓ AND the design.md §9 operability conditions —
BOTH now MET: the cost ceiling is real and fail-closed (`cost_gate_decision`, LIVE in
the orchestrator), and the failure-surfacing path is C3's observe/reflect/
needs-attention. On a REAL tenant: flip autonomous mode ON from the TUI → the
orchestrator engine drives ready work to `done` unattended → the console
observes/reflects each auto-resolution → a truly-unresolvable item surfaces in-TUI as
an actionable needs-attention item. "Done means rolled out and exercised live" — this
live evidence IS the MVP acceptance.

**RECOMMENDED I2 approach (driver-drafted; the maintainer CHECKPOINTED at C3-complete
2026-07-11 BEFORE choosing an I2 approach — so this is a recommendation, not a
decision):** run I2's truly-unresolvable plant at the LEDGER LEVEL — seed a
`human-only` acceptance item, which the engine will NOT collapse (deliberate gate), so
it rests in `Lane::Acceptance` and the console surfaces it as needs-attention via the
`d6o` fix `rt4.3` shipped. This AVOIDS the in-loop-park path that orchestrator bug
`bd-ib-18r` breaks (`bd-ib-18r` + `bd-ib-6vu` BOTH still OPEN/backlog as of 2026-07-11)
— no park, so the bug never bites. The alternative is to triage `bd-ib-18r`
(blocked-as-first-class + ledger write-back on park) first, then I2 with a genuine
mid-run park — more faithful to long unattended runs but pulls engine bug-fixing into
the MVP critical path. `bd-ib-18r`/`bd-ib-6vu` affect LONG unattended runs, not the MVP
demonstration; keep them tracked follow-ups.

**I2 tenant (recommended target) — run on a DISPOSABLE `livespec-e2e-*` tenant, NOT a
fleet/production tenant.** I2 auto-drives ready work to `done`, so it MUST NOT consume a
real backlog. The `livespec-e2e-*` throwaway repos (in the disposable `livespec-e2e`
GitHub org) are genuine "real tenants" — real GitHub repo + real beads/Dolt tenant + real
Fabro factory dispatch — but disposable, which is exactly what "done means exercised live
on a real tenant" needs without touching production. They are created by the dark-factory
acceptance harness `livespec-orchestrator-beads-fabro/orchestrator-image/acceptance-live-golden-master.sh`
(host-side create/clone/delete use `LIVESPEC_E2E_GITHUB_TOKEN`, injected by the 1Password
env wrapper). Sweep orphans with the fail-safe reaper
`orchestrator-image/reap-e2e-repos.sh` (or `just reap-e2e-repos`), run ONLY at boundaries
(session-start / post-confirmed-merge / deliberate teardown), NEVER mid-dispatch. CAVEAT:
provisioning a Fabro GitHub-App installation over the e2e throwaway repos is a HUMAN act in
GitHub org settings, NOT factory-executable (orchestrator `bd-ib-w4iaaf`) — confirm that
installation exists before the I2 run, or surface it to the maintainer. Running I2 against
a live fleet/production tenant is an outward-facing, side-effecting act; get explicit
maintainer authorization for the specific tenant before any non-disposable target.

**SEAM to assert at I2 (flagged by the `rt4.3` delegate):** if the needs-attention
surface lags the ledger (still lists an item the engine already auto-resolved), ingest
re-appears it and idempotent reflect won't re-resolve it; in practice the engine updates
the ledger → the surface drops it, and reflect runs AFTER ingest so it wins on first
sighting. I2 may want to assert surface/ledger convergence.

**Checkpoint note (2026-07-11):** the build phase ran end-to-end in one long
driver session through two token-limit interruptions with zero lost work; the
maintainer chose to checkpoint here so C3/I2 get a fresh full-context session. All
delegates (`console-autonomous-mode`, `orchestrator-autonomous-mode`) and their
worktrees are wound down; both sibling repos are clean on master and green.

The Step-0 loop rules are kept below for the historical record: each round, a
FRESH Fable session reviewed ALL THREE plans AND FIXED every problem it found
(via worktree → PR → merge); a session that landed fixes could not clear the
gate (no self-certification) — the clean verdict always came from the NEXT fresh
session.

**Loop state:**
- Round 1 (2026-07-10, Fable session `livespec-autonomous-mode`): Step-0
  validation of the ORIGINAL plans → NO-BLOCKERS with 9 observations
  (`research/step0-fable-verdict.md`); the SAME session then FIXED every
  finding in all three plans (orchestrator PR #395, console PR #134, core
  PRs #1000 + this one) and wrote
  `research/fable-revising-session-self-assessment.md` — which does NOT
  clear the gate, because reviser and reviewer were the same session.
- Round 2 (2026-07-10, fresh Fable session, this repo's session
  `livespec-autonomous-mode` pane): first fresh-session review-AND-FIX over the
  REVISED plans → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-2.md`; core PR #1014, console PR #141,
  orchestrator PR #404). All round-1 revisions re-verified against live state;
  fixes were currency + internal-soundness precision (stale `orchestrate run`
  in core C2 step text; C2-gate two-phase-C1 ambiguity; fabro-token-refresh
  state moved; mb64bv type; O2 done-surface pin). Because fixes landed, this
  round does NOT clear the gate.
- Round 3 (2026-07-10, fresh Fable session): second fresh-session
  review-AND-FIX → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-3.md`; orchestrator PR #410 + the core PR
  carrying that record). Every rounds-1-2 revision re-verified against live
  state; no structural defect anywhere; the two fixes were small currency/
  precision (stale "PR #136 cleanup" pending-decision in core §9 +
  orchestrator §5 — the validation vehicle auto-merged 2026-07-10;
  `livespec-zs22.6` is a closed task, not an epic). The CONSOLE plan passed
  clean — its first no-fix round. Because fixes landed, this round does NOT
  clear the gate.
- Round 4 (2026-07-10, fresh Fable session spawned by the driver): third
  fresh-session review-AND-FIX → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-4.md`; fixes in core PR #1022, record +
  loop state in core PR #1023). Every rounds-1-3
  revision re-verified against live state; the two fixes were small
  consistency/currency, both in the overall plan (design §7 graph missing
  the `I1 ─► C1 persistence-seam` edge its own prose asserts; stale
  "revised rounds 1-2" Read-first annotation). BOTH sibling plans passed
  clean (console's second consecutive clean round; orchestrator's first).
  Because fixes landed, this round does NOT clear the gate.
- Round 5 (2026-07-10, fresh Fable session spawned by the driver): fourth
  fresh-session review-AND-FIX → FIXES LANDED (verdict + fixes:
  `research/fable-review-round-5.md`; fix in core PR #1024, record + loop
  state in the core PR carrying this bullet). One currency fix, in the
  overall plan's own Loop state (the round-4 bullet omitted its
  record-carrying PR #1023). BOTH sibling plans passed clean again
  (console's third consecutive clean round; orchestrator's second).
  Because a fix landed, this round does NOT clear the gate.
- Round 6 (2026-07-10, fresh Fable session spawned by the driver): fifth
  fresh-session review → **NOTHING-BLOCKING** (verdict:
  `research/fable-review-round-6.md`; a purely read-only round — no fix
  was warranted, none was landed, so the no-self-certification rule is
  satisfied). Every load-bearing claim in all three plans re-verified
  first-hand as true; both sibling plans clean for the fourth/third
  consecutive round (console/orchestrator); the convergence trajectory
  (9 obs → 6 → 2 → 2 → 1 fixes) reaches zero. The verdict affirmatively
  certifies all three plans SOLID, EXECUTABLE, and MVP-MEETING.
- Maintainer certification: **GIVEN 2026-07-10** — the maintainer
  certified round 6's NOTHING-BLOCKING verdict in the driver session
  (recorded here by the driver). THE STEP-0 LOOP IS EXITED; C1/O1
  dispatch is unblocked (Next actions, step 4). → Dispatching C1 and O1
  in parallel is the next action.

**Thread role:** the OVERALL cross-repo plan. Ties together the console operator
surface and the orchestrator decision engine, owns the dependency graph, and
defines the driver + per-repo delegate-context delegation model (design.md §8).
livespec core authors no product code here.

## Read first
1. This file, then `design.md` in this directory (the full plan).
2. For the review loop: `research/fable-review-brief.md` (the brief each
   fresh reviewer runs), then the prior rounds
   (`research/step0-fable-verdict.md`,
   `research/fable-revising-session-self-assessment.md`,
   `research/fable-review-round-N.md` as they accumulate).
3. The two sibling repo plans this coordinates (both carry the accumulated
   review-round findings in their own step texts, kept current across the
   review-loop rounds):
   - `livespec-console-beads-fabro/plan/autonomous-mode/design.md`
   - `livespec-orchestrator-beads-fabro/plan/autonomous-mode/design.md`

## Goal (one line)
A human flips per-repo **full autonomous mode** from the
`livespec-console-beads-fabro` **TUI** (GUI out of scope) and the Beads/Dolt +
Fabro factory drives ready work to `done` unattended — LLM-resolving the human
gates, auditing every decision, surfacing only the truly-unresolvable back to the
operator.

## The spine (see design.md §7 for the full step catalogue)
```
Step 0 (fable-review LOOP — HARD GATE) ✓ MET 2026-07-10 (round 6 NOTHING-BLOCKING + maintainer certification)
  status (2026-07-11): O1 ✓ (orch v033, I1) · C1 ✓ (console v017) · O2 ✓ · C2 ✓ · persistence-seam ✓ (console v018) · C3 ✓ (rt4.1/.2/.3 + d6o; console master e749a6c) · ONLY I2 remains (maintainer-gated).
  ├─ Console track (delegate console-autonomous-mode):  C1 spec fixes ✓ ─► C2 command foundation ─► C3 autonomous feature
  └─ Orchestrator track (delegate orchestrator-autonomous-mode): O1 spec fixes + arming contract ✓ ─► O2 build engine (bd-ib-82a)
                          O1 arming contract (I1) ✓ ─► C3 (and C1's persistence-seam portion, now I1-unblocked)
  Integration (driver session autonomous-mode): I2 end-to-end live exercise on a real tenant = MVP "done"
```
Console C2 and orchestrator O1→O2 run in parallel — but ONLY after the Step-0
loop exits. Contract-first: O1 publishes the arming/audit contract before C3
builds on it.

## Next actions (exact steps for a new session — the BUILD phase)

Step 0 + O1 + C1(main) are DONE (Ratification record at top). The build phase is
COMPLETE (see "## Build phase progress"): **step 1 (O2) COMPLETE; step 2 (C2)
COMPLETE; step 3 (persistence-seam) RATIFIED to v018.** The ONLY live remaining
steps are **4 (C3)** and **5 (I2)** — the fresh session's work. Steps 1–3 below
are kept as the executed record; steps 4–6 are the forward work:

1. **O2 — implement the orchestrator engine (`bd-ib-82a`).** FIRST groom
   `bd-ib-82a` into dependency-layered slices — grooming is a MAINTAINER-OWNED
   cut (`/livespec-orchestrator-beads-fabro:groom`; the front-end drafts, the
   maintainer owns the acceptance), so set it up FOR the maintainer, do NOT
   auto-slice. Then build: the `dispatcher.autonomous_mode` key + `loop --mode
   autonomous` gate-collapse + the NEW LLM `needs-human` resolution stage +
   truly-unresolvable escalation + per-decision audit journal, composing the
   shipped valve/escalation/cost-gate machinery. Sequence the auto-admit slice
   around `livespec-nrdk` (factory-safe admission gate; design.md §9). Gate: O1
   (met). Refresh `bd-ib-82a`'s stale v025 spec pointer to v033 as it opens.
2. **C2 — console command foundation.** Add the five `work_item.*` valve/policy
   `CommandType` variants + handlers + a port onto the orchestrator's published
   `drive` action surface + the Scenario-11 test (TDD, console Red-Green ritual).
   Folds `pke3y3` (regroom against the current valve model — MAINTAINER-OWNED
   cut). Gate: C1's MAIN ratification (met). Runs concurrently with O2.
3. **Persistence-seam amendment (console, now I1-unblocked).** File the small
   console propose-change that drops/derives the console's own
   `livespec-console-beads-fabro.autonomous_mode.enabled` block so ONLY the
   orchestrator's `dispatcher.autonomous_mode` key persists (the C1 persistence
   portion deferred to I1; O1 froze the arming contract at v033). Route
   propose-change → independent read-only Fable review → revise, and per the
   PROCESS NOTE at top carry the `tests/heading-coverage.json` clause-rebinding +
   `console-spec-check` ground-truth co-edit in `resulting_files`. Gates C3.
4. **C3 — console autonomous feature.** Gate: C1 + C2 + I1 (I1 met; needs C2 +
   the persistence-seam amendment). Build `config.autonomous_mode_set` +
   `.livespec.jsonc` persistence/audit + `factory.autonomous_mode_*_requested` +
   TUI toggle/confirm-modal/dangerous-label/header + the Scenario-10
   enable/observe/reflect/escalate loop (NOT a console-side resolver — the engine
   owns resolution, per the ratified delegation re-scope).
5. **I2 — end-to-end live exercise (MVP "done").** Gate: C3 + O2 AND the
   design.md §9 operability conditions (verified cost ceiling + a real
   failure-surfacing path — note orchestrator bug `bd-ib-18r`: an in-loop park
   today orphans without ledger write-back, so I2's truly-unresolvable plant
   must be ledger-level or `bd-ib-18r` triaged first).
6. Every spec change routes propose-change → independent read-only Fable review →
   revise; core H2 changes co-edit `tests/heading-coverage.json`; CONSOLE
   normative-clause changes carry the clause-rebinding co-edit (PROCESS NOTE).
   Ratification is DRIVER-held: a delegate FILES + halts; the driver runs the
   Fable review and dispatches the revise on a NO-BLOCKERS verdict.

## Delegation model (design.md §8)
Driver + per-repo delegate contexts; the driver dispatches each delegate as a
scoped subagent (NOT a tmux pane — that mechanism is retired). Delegate contexts
are named for their repo so cross-plan status references resolve.
- Driver: Claude session `autonomous-mode` (cwd `/data/projects/livespec`) — owns
  the plan, gates, dispatch, synthesis, and the ratification review gate.
- Delegate `console-autonomous-mode` (cwd console repo) → C1/C2/C3.
- Delegate `orchestrator-autonomous-mode` (cwd orchestrator repo) → O1/O2.
- Reviewer: a FRESH Fable session per round for the Step-0 loop (review-AND-FIX —
  it lands its own fixes; no continuity with sessions whose fixes it reviews).
  For per-step ratification (C1/O1 etc.), the DRIVER spawns the read-only
  independent Fable review after a delegate files its propose-change.

## Ledger items in play (per repo tenant)
> **Currency note (2026-07-11):** several descriptions below are superseded by
> "## Build phase progress" — `bd-ib-82a` is groomed into `.1`–`.4` and CLOSED
> (O2 complete); `pke3y3` is re-based onto the v017 valve model (`.1`–`.4`, con-S4
> in flight), NOT "7 unimplemented commands"; the factory/spec split lives in new
> sibling `8aw`; `mb64bv` is CLOSED (already-fixed via `3eca905`). Trust the Build
> phase progress section for current slice/close state.

- Core: `livespec-bvuy4w` — this thread's epic anchor (driver filed it
  2026-07-10 via the `capture-work-item` operation, closing the round-2
  finding; epic-shaped → `backlog` per the intake Definition-of-Ready
  checklist; edges: `livespec-nrdk` blocks, `livespec-0jxs` related — bd
  refuses an epic→task `blocks` edge by design, so the task dependency
  carries a `related` edge instead).
- Console: `rt4` (operator surface → C3; version pointer refreshed v013→v016 during C1, but its description substance still reads pre-re-scope — refresh at C3 grooming), `pke3y3` (epic, "7 unimplemented commands" — regroom + split for C2, maintainer-owned cut), `ipi` (attention-stream TUI migration), `mb64bv` (chore: backlog-bounce vocab rename — verify the rename target against the orchestrator's actual journal field `bounced_to_regroom` before landing).
- Orchestrator: `bd-ib-82a` (the engine → O2; stale v025 pointer — refresh to v033 when O2 opens).
- Core deps TRACKED not re-owned: `livespec-nrdk` (factory-safe admission gate), `livespec-0jxs` (operability preconditions); orchestrator `plan/fabro-token-refresh` (long-run publish robustness); orchestrator bugs `bd-ib-18r` / `bd-ib-6vu` (unattended-run robustness — sequence around).

## Key cross-repo risks (design.md §6) — ALL THREE now RESOLVED by O1/C1 ratification
1. Persistence-model seam: RESOLVED at O1 v033 — the arming contract pins the
   orchestrator `dispatcher.autonomous_mode` key as the single persistent
   permission, the console factory-drain path as launcher, and `loop` (not
   `drive`) as the `--mode autonomous` surface. (Residual: the console still
   drops/derives its own duplicate block — the I1-unblocked persistence-seam
   amendment, Next actions step 3.)
2. Division of resolution: RESOLVED at C1 v017 — the Scenario-10 re-scope makes
   the engine own ALL gate resolution; the console enables/observes/reflects; the
   double-resolution race is explicitly killed (console-side resolver deferred).
3. Vocab drift: RESOLVED at C1 v017 — all four citation sites swept
   (`orchestrate`/`orchestrate run` → `drive`; lane-vocab ownership → orchestrator).

## Next action
**C3 COMPLETE (2026-07-11); the maintainer CHECKPOINTED at C3-complete before I2.**
All of Step 0, O1 (orch v033), C1 (console v017), O2 (`bd-ib-82a`), C2 (`pke3y3`),
the persistence-seam (console v018), and C3 (`rt4` → `rt4.1/.2/.3` + `d6o`) are
landed, reviewed sound, and green. The SOLE remaining step is **I2 — the end-to-end
live exercise on a real tenant = MVP "done"** (maintainer-gated; needs the maintainer
for the live acceptance). Its gate (C3 + O2 + §9 operability — cost ceiling +
failure-surfacing path) is MET; the ONE open decision is the
truly-unresolvable-plant approach — see "## Remaining to MVP" for the driver's
RECOMMENDATION (a ledger-level `human-only`-acceptance plant that sidesteps still-open
orchestrator bug `bd-ib-18r`) and the alternative (triage `bd-ib-18r` first). Merge
posture: green PRs merge by the delegate/driver via `gh pr merge --rebase` (the console
repo has NO auto-merge bot — see the corrected merge-posture note above) + driver
post-merge review. All C3 delegates + worktrees are wound down; core, console, and
orchestrator are clean on master and green.

## Pointers
- Ledger read (per tenant): `bd list --json` (or `bd show <id> --json`) run from
  inside the repo, via the credential wrapper
  `/usr/local/bin/with-livespec-env.sh -- bd …`; prefer it over the shared
  `list_work_items.py` cache path, which can mis-resolve the tenant.
- Repo mutation: worktree → PR → merge → cleanup; `mise exec -- git …`; never `--no-verify`; plan docs are `docs(plan):` commits.
