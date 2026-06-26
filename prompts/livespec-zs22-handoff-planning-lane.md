# Handoff: Formalize the livespec blessed workflow (epic livespec-zs22)

**Track:** planning-lane · **Epic:** `livespec-zs22` · **Tenant:** livespec

This is the resumable runbook for the Planning Lane + Conformance Pattern
formalization. It carries *instructions*; the *rationale* lives in
`research/planning-workflow-gap/planning-lane-design.md`, and the
*authoritative status* lives in the ledger — never in this file.

## FIRST ACTION — print live status (do not trust this file for status)

```
/data/projects/1password-env-wrapper/with-livespec-env.sh bd show livespec-zs22
```

Derive every "what's done / what's next" answer from that, plus
`bd ready` and `git log`. This file lists the *plan*, not the *state*.

## Read first

1. `research/planning-workflow-gap/planning-lane-design.md` — the design,
   the three planes, the locked decisions, the increment sequence, and the
   three FINAL diagrams (§"Architecture diagrams") ready to land in the spec.
2. `research/factory-conformance/cross-repo-conformance-pattern.md` — the
   companion Conformance Pattern (files its milestones through this lane).
3. `research/planning-workflow-gap/missing-planning-workflow-thread.md` —
   the original gap note.

## Objective

Re-adopt livespec's own deferred planning design as a codified, disciplined
convention, place each piece on the plane that owns it (Spec /
Orchestrator / Control), and mechanically enforce the no-shadow-ledger
rule — then build the Conformance Pattern on top of it. Locked decisions
(see the design doc): handoff skill **orchestrator-side**; **`baseline`**
profile (not "factory"); **`just` mandated non-functionally only** (never
in core's public functional surface); fleet pins track **latest RELEASE**
not HEAD; the **console** is the Control-Plane runner.

## Status (refreshed 2026-06-26, increment-5 M3 COMPLETE; next is M4)

**Run this track autonomously.** Standing maintainer directive (2026-06-25):
own the cuts (file children, draft, execute, land per increment), gate only
on a genuine architectural/intent question, and hand off to a fresh session
when context approaches budget. This supersedes the design doc's
per-cut approval gate for this track.

**⚠ CONCURRENCY — another worker is on this epic's ready queue (2026-06-26).**
M3 (`livespec-zs22.7.4`) was landed by a CONCURRENT session as console commit
`76c9fc2` while a parallel interactive session was independently implementing
the SAME milestone — duplicated effort (the parallel PR was closed). The likely
cause: the dark-factory Dispatcher polls the Beads ledger and dispatches ready
items, so `zs22.7`'s ready queue is being worked by the factory in parallel with
any interactive session. BEFORE implementing ANY item: (1) re-run the FIRST
ACTION ledger query AND `bd ready`, (2) `git fetch` + read each target repo's
`origin/master` tip, and (3) confirm the item is still open and unstarted — an
item can land on master mid-implementation. If the factory is actively pulling
this epic, prefer to let it; an interactive session should claim an item
(`bd update <id> --status in_progress`) and check master freshness immediately
before each commit.

Landed: increment 0 + design refinements (PRs #568, #572; `livespec-zs22.1`
closed). **Increment 1** (`livespec-zs22.2`, PR #575, cut `v137`): the
`## Workflow planes and the Planning Lane` framing + planes/skills diagrams.
**Increment 2** (`livespec-zs22.4`, PR #577, cut `v138`): the NON-normative
`#### Planning Lane guidance` block in `non-functional-requirements.md`.
**Increment 3a** (orchestrator PR `livespec-orchestrator-beads-fabro#167`,
cut `v016`; core PR `livespec#579`, cut `v139`): the orchestrator-side
`plan` skill (`prose/plan.md` + Claude/Codex bindings + e2e-cli fixture) and
the `## Planning Lane realization` contract — `plan` is the SIXTH heavyweight
op — PLUS the core NFR `Handoff self-sufficiency` pattern paragraph.
`livespec-zs22.3` (the 3a acceptance harness: cold-open test, one path,
fail-closed dangling-reference) is **CLOSED**. Epic is **4/5 children
complete**.

**Increment 3 COMPLETE** (`livespec-zs22.5` CLOSED). 3a = the orchestrator
`plan` skill (landed earlier). 3b = the no-shadow-ledger WARN-only `Stop` hook,
now landed in BOTH Drivers byte-identical: core contract `livespec#584` (`v140`);
`livespec-driver-claude#42` (master `06044b4`); `livespec-driver-codex#17`
(master `d6a4f88`); both bodies sha256 `5beb62c5…` (= the canonical source, noqa
preserved). Maintainer chose option A (identical copies now via the gate's
suite-green `chore:` path; the mechanical byte-identity Verifier is increment-5
Conformance work). The hooks landed via suite-green, not Red→Green, because the
red-green classifier doesn't impl-classify Driver hook paths (`livespec-kvzt`).

**Increment 4 COMPLETE** (`livespec-zs22.6` CLOSED) — the console control-plane
contract, landed as one cross-repo epic. CORE (`livespec` PR #598, cut `v142`):
a NEW NON-normative top-level `### Control-Plane console guidance` section in
`non-functional-requirements.md` — a PEER of `### Orchestrator plugin ecosystem`,
NOT nested under it (the console is the Control Plane, a plane distinct from the
Orchestrator; nesting would contradict the plane separation this track codifies;
the earlier "sibling under Orchestrator plugin ecosystem" wording was imprecise —
an H3 peer respects the planes and, since heading-coverage tracks H2 only, costs
nothing mechanically). It records what the console reads / composes / coordinates
/ never owns, that it is not a required dependency, not a Driver, and the `just`
boundary — framed identically to the Dispatcher / grooming / Planning Lane
guidance blocks. CONSOLE (`livespec-console-beads-fabro` PR #34, cut `v006`): a
`Control-Plane realization` paragraph in `spec.md` §"Scope Boundary" plus the
Scope-Boundary mermaid diagram extended to the three-plane framing (console =
CONTROL PLANE; livespec core under a SPEC PLANE subgraph; orchestrator + Fabro
under an ORCHESTRATOR PLANE subgraph; GitHub a host source). Both landed via the
governed propose-change → revise lifecycle.

**Increment 5 FILED + M0/M1 COMPLETE — the Conformance Pattern.** Increment 5 is
now a filed SUB-EPIC `livespec-zs22.7` (under `livespec-zs22`, which is now 6/7
children) holding milestones **M0–M6** (`livespec-zs22.7.1`…`.7`), chained
M0→M6, with see-also links to the fold-in follow-ups (`gcp2`, `kvzt`, `i6rc`,
`8njn` on the epic; `qtjd`↔M2; `mjnv`↔M5). **M0** (`zs22.7.1`) CLOSED — decisions
locked in the design docs + `zs22.1`, no code. **M1 COMPLETE** (`zs22.7.2`, PR
#602, rebase merge `9c7c87c`, cut `v143`): a NEW NON-normative top-level
`### Conformance Pattern` section in `non-functional-requirements.md` (after
`### Control-Plane console guidance`, before `### Codex dogfooding compatibility`)
— the five-slot anatomy (Contract / Mechanism / Installer / Verifier / Exemption),
the reuse-by-default delivery rule, the consolidated `just` keystone + its
functional/non-functional boundary, the profile + declarative
`.livespec-fleet-manifest.jsonc` `adopters`/`posture` boundary, the four-tier
enforcement, the explicit-exemptions/default-fail-closed hard rule, and the
concern registry (concern #1 worktree-discipline + concern #2 cross-harness
plugin-resolution in full five-slot form; No-shadow-ledger / Terminology-guard /
Ledger-closure / Pin-freshness / Archive-on-epic-close named). It NAMES +
GENERALIZES existing fleet machinery (§Fleet membership contract, copier,
dev-tooling, pin-and-bump) rather than duplicating it. `just check` green;
doctor-static green. The pattern is now SPEC; the machinery is M2→M6.

**Mid-increment-3 detour, DONE — epic `livespec-gcp2` (red-green-replay
fleet+adopter-wide).** Maintainer directive (2026-06-25): red-green-replay MUST
be enforced fleet+adopter-wide, regardless of any "no product Python"
self-classification. LANDED: both Python Drivers wired at lefthook **and**
authoritative CI (`livespec-driver-claude#40`; codex `8abbea1`+`356aabc`); core
policy `livespec#589` (`v141`); adopters covered by the `templates/impl-plugin/`
copier; `h3e7` (commit-pairs no-op) fixed in both Drivers. gcp2 was RE-OPENED as
the **Driver-hook enforcement umbrella** to hold the conformance follow-ups this
session surfaced (below).

**Open conformance follow-ups (filed this session; status from the ledger, not
here; mostly increment-5 Conformance-Pattern work).**
`livespec-co9h` (block-auto-memory deny-reason reword — claude part LANDED
`ee8ec92`; codex has no such hook; part-3 = `livespec-8njn`, the family AGENTS.md
durable-memory capture convention, default-tracked pending a maintainer draft-now
call); `livespec-kvzt` (`red_green_replay._IMPL_PREFIXES` hardcoded → Driver hook
changes dodge Red→Green; make impl-classification config-driven); `livespec-i6rc`
(`lint-autofix-staged` mutates ruff-excluded files → `--force-exclude` needed in
the canonical orchestrator + copier template, not just the Drivers);
`livespec-qtjd` (fresh clones can have dormant local git gates until
`just bootstrap`); `livespec-mjnv` (live codex picker fails-on-timeout vs
skips-on-unavailable); `livespec-1t17` (Rust red-green analogue for the console).

## Next concrete action

**M4 (`livespec-zs22.7.5`) is next — read its ledger notes (FIRST ACTION +
`bd show livespec-zs22.7.5`); confirm it is still open + unstarted FIRST (see
the concurrency warning above).** M4 = adopter dogfood: migrate Open Brain
(`/data/projects/openbrain`) to `just` as sole runner (lefthook→`just`,
pnpm→1:1 wrappers/recipes), register it as `adopter`/`baseline`, and reconcile
its hand-rolled commit-refuse hook to the canonical STRUCTURAL body via the SAME
shared livespec-dev-tooling machinery M3 proved (reuse, not re-impl). Open Brain
is an ADOPTER (not a fleet member), so it belongs in the manifest's `adopters`
section, not `members` — but the `adopters` section + the `profile`/`posture`
fields do NOT exist in `.livespec-fleet-manifest.jsonc` yet (current schema is a
flat `members` array with `class` only), so M4 either adds them or scopes around
them; that manifest-schema work overlaps `zs22.7.8` and M6. Re-survey Open Brain
(not surveyed by the M3 session) and start clean.

**M3 (`livespec-zs22.7.4`) — DONE on console master via `76c9fc2`** (a CONCURRENT
session; live status from the ledger). The Rust Control-Plane console now carries
`baseline`: the canonical STRUCTURAL commit-refuse hook + the shared dev-tooling
verifier wired into `just check` + CI, REUSED not re-implemented — `76c9fc2`
consumes dev-tooling via a minimal `pyproject.toml` `[tool.uv.sources]` git+tag
v0.19.0 pin (+ `.python-version`, `uv.lock`), the bump-automatable approach.
Fail-closed proven (a commit on the console primary master is refused, HEAD
unchanged, primaryPath unset); console master CI green. Console work-item
`livespec-console-beads-fabro-d5c` CLOSED. Two follow-ups: `zs22.7.8` was REFINED
— the console now HAS a pyproject `[tool.uv.sources]` dev-tooling pin, so the
eventual `console` repo class should INCLUDE (not exclude) the `dev-tooling-pin`
obligation; and `livespec-console-beads-fabro-e8y` (P3) — remove the
now-redundant lefthook `00-no-commit-on-master` that `76c9fc2` left (the
structural hook is the single Mechanism).

**M2 (`livespec-zs22.7.3`) — what landed (mechanism FLEET-MIGRATED; live status
from the ledger, not here):** the maintainer-confirmed **Option A** (one uniform
commit-refuse wrapper installed everywhere + an explicit `livespec.sandboxExempt`
marker the hook BODY reads; structural refuse when `git-dir == git-common-dir`;
armed-on-install; `primaryPath` retired) is now the single canonical Mechanism
for concern #1, migrated across the fleet:
- **M2-1 `livespec-dev-tooling#165` (MERGED, v0.18.0)** — canonical structural
  body + verifier accepts BOTH structural and legacy bodies through migration.
- **PR-1 `livespec-orchestrator-beads-fabro#169` (MERGED)** — Fabro prepare arms
  `livespec.sandboxExempt true` (folds `livespec-qtjd`).
- **M2-2 core `livespec#609` (MERGED, `4c7849a`, cut v144)** — core wrapper →
  structural body; shared `install-commit-refuse-hooks` recipe + bootstrap
  delegate; `primaryPath` retired; governed NFR/contracts spec cycle.
- **Template `livespec#612` (MERGED, `4f37f75`)** — RESOLVED the architectural
  divergence: the single-wrapper is canonical (it is the latest + the deliberate
  M2 Mechanism + has `sandboxExempt` + satisfies the canonical check + is
  armed-on-install). Template now installs the structural body via
  `install-commit-refuse-hooks`; `refuse-primary-commit.sh` deleted + unwired;
  KEPT `worktree-lib.sh` lifecycle pack + ecosystem profiles + branch-protection
  (orthogonal, adopter-proven).
- **M2-3 orchestrator `livespec-orchestrator-beads-fabro#171` (MERGED, `1bd35b5`)**
  — orchestrator body → structural at pre-commit/pre-push/commit-msg; `primaryPath`
  retired; recipe aligned.

**M2-1b — the reusable installer MODULE — is DONE (dev-tooling v0.19.0, `#167`
+ spec cycle `#169`).** `livespec_dev_tooling.install_commit_refuse_hooks` is the
single wheel-shipped canonical-body carrier (installs pre-commit/pre-push/
commit-msg), and `canonical_checks.baseline_check_slugs()` ships the `baseline`
check-profile accessor. **MODULE ADOPTION:** dev-tooling, the orchestrator
(`#173`, which retired its vendored `.sh`), and the console (`#43`) now REUSE the
module; **core + the copier template still `cp` the interim body (core M2-1b
DEFERRED per maintainer call)**. So M2's "no per-repo copies" goal is met for the
repos on the module; core/template adoption is the remaining tail. (Do NOT
re-build the module — it exists in v0.19.0.)

**Still open / deferred under M2 (live status in the `zs22.7.3` ledger notes):**
- **`baseline` tag** — the accessor SHIPS (v0.19.0) but the full profile/partition
  + manifest wiring is deferred to M4 (where Open Brain first imports it).
- **git-jsonl follow-up** — `livespec-orchestrator-git-jsonl` does NOT dispatch
  into Fabro (no `.fabro/`), has NO `sandboxExempt` arming, and still carries the
  LEGACY body. Do NOT migrate it to structural until its dispatch path is
  confirmed to arm `sandboxExempt` (a structural body would refuse legitimate
  in-sandbox commits). The verifier still accepts its legacy body, so not urgent.
- **dev-tooling structlog runtime deps (NEW)** — dev-tooling vendors structlog
  but declares no `[project.dependencies]`, so a minimal consumer (the console)
  had to add `typing-extensions` on Python <3.11; the systemic fix is for
  dev-tooling to declare structlog's transitive runtime deps so every consumer
  gets them.

**Side observation (NOT acted on):** the two pre-migration planning docs
`prompts/worktree-discipline-pack-{epic,prompt}.md` still reference the now-deleted
`refuse-primary-commit.sh` (the only remaining stale refs in core). Candidate to
archive to `archive/prompts/` (the pack landed; the refuse half is superseded) —
maintainer's call.

After M4: M5 (concern #2 cross-harness plugin-resolution; folds `mjnv`), M6
(four-tier wiring). M4 itself seeds the `baseline` tag (the partition deferred
from M2, where Open Brain first imports it). Each is its own PR. The fold-in follow-ups (`kvzt`, `i6rc`, `qtjd` [folded by M2's
armed-on-install], `mjnv`, the gcp2 byte-identity Verifier, `8njn`) are
see-also-linked to `zs22.7` and its milestones — pull each into the milestone
whose concern it sharpens; do NOT re-parent them off `gcp2`.

**Also pending a maintainer call:** `co9h` part-3 (`livespec-8njn`) — document
the durable-memory capture convention in the family AGENTS.md (impl-plugin
template + core). Default-tracked; the maintainer may opt to draft it now (it has
a design element on the AGENTS.md-section vs. referenced-instruction-file
mechanism).

## Pinned canonical body (`no_shadow_ledger.py`)

**LANDED — historical reference** (now committed byte-identical at sha256
`5beb62c5…` in `livespec-driver-claude/.claude-plugin/hooks/no_shadow_ledger.py`
and `livespec-driver-codex/livespec/hooks/no_shadow_ledger.py`; read those for
the live copy). It was the single source for the two 3b Driver hooks. Authored
+ smoke-tested 2026-06-25
(WARN on a `*handoff*.md` / `plan/` / `prompts/` `.md` write carrying ≥3 `[ ]`/`[x]`
checkbox items; SILENT on clean artifacts incl. inline `` `[ ]` `` in prose, on
non-planning paths, on malformed stdin, on `stop_hook_active`). It lives here
(not as a committed `.py`) because core runs pyright-strict on tracked `.py`; the
Driver repos run neither pyright nor ruff on their ruff-excluded hook dirs, so it
ships verbatim there.

```python
#!/usr/bin/env python3
"""
livespec no-shadow-ledger — Stop hook warning on planning artifacts that
embed a checkbox task queue instead of deriving status from the ledger.

Shipped BYTE-IDENTICALLY by both Drivers (livespec-driver-claude at
.claude-plugin/hooks/, livespec-driver-codex at livespec/hooks/) as the
single-sourced neutral body; each Driver's hooks.json Stop entry is the
thin per-runtime adapter that invokes it. Codex consumes the Claude Stop
hook I/O format, so this one body serves both runtimes.

Declared on the `Stop` event. Scans the agent's last turn (the transcript
entries after the last REAL user message — tool-result deliveries do NOT
reset the window) for file-persisting tool calls (Write / Edit /
MultiEdit) that wrote a PLANNING ARTIFACT — a handoff, or any markdown
file under a plan/ or prompts/ directory. When such an artifact's written
content carries markdown checkbox task-list items ([ ] / [x]) at or above
a mechanical threshold, it emits a `systemMessage` WARNING on stdout.

WARN-ONLY BY CONTRACT (livespec core non-functional-requirements
§"Planning Lane guidance" → "No shadow ledger"; contracts.md
§"Driver-shipped hooks"): this hook NEVER blocks the stop — it never
emits a `decision` key and never exits non-zero — and it never auto-edits
anything. The mechanical detection internals (the planning-artifact path
predicate, the checkbox threshold, the persisting-tool set) are Driver
implementation detail and MAY be tuned without a core spec cycle, per the
contract, provided the WARN-only Stop posture holds.

Fail-open contract: ANY failure (no python3 on PATH, malformed stdin,
missing/unreadable transcript, malformed transcript lines) is a silent
pass-through with exit 0.
"""

import json
import re
import sys
from pathlib import Path

# Mechanical "shadow-ledger smell" threshold: number of markdown checkbox
# task-list items in a single persisted planning artifact.
CHECKBOX_THRESHOLD = 3

# Tool calls that persist content to disk (NotebookEdit is excluded — a
# planning handoff is never a notebook).
PERSISTING_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})

# A markdown task-list item: a list bullet followed by a [ ] / [x] box. The
# anchor at line start keeps inline prose like `[ ]` (e.g. a rule quoting
# the forbidden syntax) from matching — only real list items count.
_CHECKBOX_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[[ xX]\]")


def _is_real_user_entry(*, entry: dict) -> bool:
    """A user entry typed by the human — NOT a tool_result delivery."""
    if entry.get("type") != "user":
        return False
    message = entry.get("message")
    if not isinstance(message, dict):
        return False
    content = message.get("content")
    if isinstance(content, str):
        return bool(content.strip())
    if not isinstance(content, list):
        return False
    has_text = False
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "tool_result":
            return False
        if block.get("type") == "text":
            has_text = True
    return has_text


def _written_text(*, name: str, tool_input: dict) -> str:
    """The content a persisting tool call wrote, aggregated to one string."""
    if name == "Write":
        text = tool_input.get("content")
        return text if isinstance(text, str) else ""
    if name == "Edit":
        text = tool_input.get("new_string")
        return text if isinstance(text, str) else ""
    if name == "MultiEdit":
        edits = tool_input.get("edits")
        parts: list[str] = []
        if isinstance(edits, list):
            for edit in edits:
                if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
                    parts.append(edit["new_string"])
        return "\n".join(parts)
    return ""


def _last_turn_writes(*, entries: list[dict]) -> list[tuple[str, str]]:
    """(path, written-text) pairs persisted after the last real user message."""
    start = 0
    for index, entry in enumerate(entries):
        if _is_real_user_entry(entry=entry):
            start = index + 1
    writes: list[tuple[str, str]] = []
    for entry in entries[start:]:
        if entry.get("type") != "assistant":
            continue
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            if name not in PERSISTING_TOOLS:
                continue
            tool_input = block.get("input")
            if not isinstance(tool_input, dict):
                continue
            path = tool_input.get("file_path")
            if not isinstance(path, str) or not path:
                continue
            writes.append((path, _written_text(name=name, tool_input=tool_input)))
    return writes


def _is_planning_artifact(*, path: str) -> bool:
    """A handoff, or any markdown file under a plan/ or prompts/ directory."""
    lowered = path.lower()
    if not lowered.endswith(".md"):
        return False
    name = lowered.rsplit("/", 1)[-1]
    if "handoff" in name:
        return True
    segments = lowered.split("/")
    return "plan" in segments or "prompts" in segments


def _checkbox_count(*, text: str) -> int:
    return sum(1 for line in text.splitlines() if _CHECKBOX_RE.match(line))


def _warning() -> str | None:
    """Return the systemMessage JSON, or None for a silent pass-through."""
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict) or payload.get("stop_hook_active"):
        return None
    transcript_path = payload.get("transcript_path")
    if not isinstance(transcript_path, str) or not transcript_path:
        return None
    transcript = Path(transcript_path)
    if not transcript.is_file():
        return None
    entries: list[dict] = []
    for line in transcript.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except ValueError:
            continue  # fail-open per line: skip malformed transcript lines
        if isinstance(parsed, dict):
            entries.append(parsed)
    for path, text in _last_turn_writes(entries=entries):
        if not _is_planning_artifact(path=path):
            continue
        count = _checkbox_count(text=text)
        if count >= CHECKBOX_THRESHOLD:
            message = (
                "livespec no-shadow-ledger WARN: this turn wrote a planning "
                f"artifact ({path}) carrying {count} checkbox task items "
                "([ ]/[x]). The no-shadow-ledger rule (livespec "
                'non-functional-requirements §"Planning Lane guidance") '
                "requires a handoff to derive status from the work-item ledger "
                "as its first action: each checklist item is a session-local "
                "step OR a pointer to a real ledger id, never a parallel work "
                "queue that shadows the ledger. Replace the embedded checkbox "
                "queue with ledger-id pointers and a ledger-status query."
            )
            return json.dumps({"systemMessage": message})
    return None


try:
    warning = _warning()
except Exception:  # noqa: BLE001 — fail-open by contract
    warning = None
if warning is not None:
    sys.stdout.write(warning + "\n")
sys.exit(0)
```

## Recon — cross-repo facts for increments 3-5 (verified 2026-06-25)

Baked in so a fresh session does not re-run the survey. Verify before relying
(repos move; this is a snapshot).

**3b currency note (post-gcp2):** the no-shadow-ledger approach is now SETTLED —
see §"Pinned canonical body" and Status, not the warn-plan-persistence-shape
framing below. The driver-layout facts below remain useful for wiring the new
`Stop` hook, but BOTH Drivers now ALSO carry the red-green-replay gate (gcp2:
lefthook + CI), so the hook PRs run under the Red→Green ritual. The footgun-guard
reconciliation (228 vs 365) named below is explicitly increment-5 Conformance
work, NOT part of 3b.

**Driver repos (both exist; NOT DRY — the increment-3b gap).**

- `livespec-driver-claude`: skills at `.claude-plugin/skills/<name>/SKILL.md`;
  plugin hooks at `.claude-plugin/hooks/hooks.json` (PreToolUse:Write →
  `block-auto-memory.sh`; Stop → `warn-plan-persistence.sh`, 6 KB) PLUS
  repo-scoped `.claude/settings.json` whose PreToolUse:Bash CHAINS
  `livespec_dev_tooling.agent_hooks.pretooluse_background_guard` THEN
  `.claude/hooks/livespec_footgun_guard.py` (228 lines), and whose
  SubagentStop wires `…agent_hooks.subagent_stop_guard`. (Re-verified
  2026-06-25 post-3a.) 3b's no-shadow-ledger Stop hook must chain AFTER any
  existing Stop hook and preserve exit status per NFR §"Hook chaining".
- `livespec-driver-codex`: skills at `livespec/skills/<name>/SKILL.md`; hooks at
  `livespec/hooks/hooks.json` wiring ONLY PreToolUse:Bash →
  `livespec_footgun_guard.py`. NO `.sh` hooks (no block-auto-memory, no
  warn-plan-persistence).
- The two footgun guards are NOT byte-identical (228 vs 365 lines) — the
  cross-Driver DRY defect. Mirror the orchestrator's `prose/<name>.md` +
  thin-binding single-sourcing and core NFR §"Codex dogfooding constraints".
- `warn-plan-persistence.sh` is the literal shape to extend for the
  no-shadow-ledger hook: a Stop hook, WARN-ONLY (emits a `systemMessage`, never
  a decision key, never non-zero, fail-open), scanning the last turn for a
  planning artifact written with no persisting/ledger call.

**Orchestrator (`livespec-orchestrator-beads-fabro`).** 9 skills under
`.claude-plugin/skills/`; prose for the 5 heavyweight ops under
`.claude-plugin/prose/`. NO `plan`/`handoff` skill, NO `plan/` or `prompts/`
dir yet. `groom` is the closest analogue (heavyweight, stateful, re-entered):
copy its `SKILL.md` frontmatter; `groom` is `allowed-tools: Bash, Read, Grep,
Glob`, `capture-work-item` adds `Write` — `plan` needs `Write` too.

**Console (`livespec-console-beads-fabro`).** EXISTS (Rust), full
`SPECIFICATION/` tree. Already control-plane content in `spec.md`:
owns/does-not-own lists (`/livespec:* spec mutation semantics` is in
does-not-own) + a mermaid diagram. Increment 4's console side LANDED
(PR #34, cut `v006`): added the `Control-Plane realization` paragraph +
extended the Scope-Boundary diagram to the three-plane framing. The console
runs its OWN spec-refinement track (`prompts/spec-refinement-critique-handoff.md`)
and a `prompts/` dir with handoff files; drive the lifecycle against fixed core
with `LIVESPEC_CORE_PLUGIN_ROOT=/data/projects/livespec/.claude-plugin`.

**Core NFR integration.** The zs22.4 Planning Lane guidance sits as a `####`
under `### Orchestrator plugin ecosystem`, sibling to `#### Orchestrator-internal
Dispatcher guidance` (the NON-normative template). Increment 4's core side uses
the SAME template. `just` is referenced piecemeal (`### Toolchain pins`,
`### Enforcement-suite invocation`, `### Developer-tooling layout`) but has NO
consolidated mandate — increment 5 lands the "`just` keystone" NFR mandate.
`### Hook chaining` constrains 3b.

**Conformance Pattern (increment 5) skeleton**
(`research/factory-conformance/cross-repo-conformance-pattern.md`). Five slots:
**Contract / Mechanism / Installer (`just` recipe) / Verifier (fail-closed, in
`just check`) / Exemption**. `baseline` profile (every governed repo) + additive
layers (`fleet-infra`, `orchestrator-plugin`, `app`); declarative `adopters`
manifest in `.livespec-fleet-manifest.jsonc` (`fleet`/`adopters` arrays, each
`profile` + `posture` = `released`/`pinned`/`none`). Four tiers: author-time
(copier) / commit-time (lefthook→`just check`) / dispatch-time (orchestrator
runs installer+verifier pre-dispatch) / fleet-time (`just conformance` + drift
CI). Named concerns: Plugin-resolution, Terminology-guard, Worktree-discipline,
No-shadow-ledger, Ledger-closure, Pin-freshness. Milestones M0-M6 (M3 dogfoods
on `livespec-console-beads-fabro`; M4 on Open Brain).

## Constraints / non-negotiables

- **Dogfood the discipline.** All work in a worktree under
  `~/.worktrees/livespec/<branch>`; land via PR → rebase-merge; never
  commit on the primary checkout. `mise exec -- git …`; never
  `--no-verify`; halt and report on any hook failure.
- **No shadow ledger.** This handoff and every artifact point at ledger
  ids for status; they never embed a `[ ]`/`[x]` task queue.
- **Respect the planes.** The handoff/coordination skill is
  orchestrator-side; the reasoning capture is a Spec-Plane convention; the
  console is the Control Plane. `just` never leaks into core's functional
  surface or the `/livespec:*` skills.
- **Increment discipline.** Small, cohesive, independently mergeable,
  nothing breaks. One increment per PR.

## Handoff refresh

If context approaches budget mid-increment: wrap the in-flight increment
to a committed+pushed state, update the ledger (`bd`), print the closing
status table, and refresh this file (same epic id) with the exact
remaining work. End every session by naming the literal next-session
command.

**Literal next-session command (one path — per the self-sufficiency rule
this track codified):**

```
run prompts/livespec-zs22-handoff-planning-lane.md
```

That single path is sufficient: a fresh session opening only this handoff
and its Read-first chain can execute the next action (increment 5 / M4,
`livespec-zs22.7.5`) without re-deriving anything — AFTER confirming via the
FIRST ACTION ledger query + `bd ready` + a `git fetch` that M4 is still open and
unstarted (another worker is on this epic; see the concurrency warning in
§Status). Status comes from the FIRST ACTION ledger query, never from this file.

## Archive condition

When `livespec-zs22` closes (all increments landed, the Planning Lane
guidance in core NFR, the Conformance Pattern shipped), `git mv` this file
to `archive/prompts/` with a completion banner. The durable history then
lives in the spec, the spec history, the commits, and the ledger.
