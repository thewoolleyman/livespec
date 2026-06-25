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

## Status (refreshed 2026-06-25, post-3b-core + red-green epic gcp2)

**Run this track autonomously.** Standing maintainer directive (2026-06-25):
own the cuts (file children, draft, execute, land per increment), gate only
on a genuine architectural/intent question, and hand off to a fresh session
when context approaches budget. This supersedes the design doc's
per-cut approval gate for this track.

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

**Increment 3b CORE SLICE LANDED** (`livespec-zs22.5`; core PR `livespec#584`,
cut `v140`): core `contracts.md` §"Driver-shipped hooks" now REQUIRES the
no-shadow-ledger WARN-only `Stop` hook in BOTH Driver bundles, single-sourced
as a byte-identical `no_shadow_ledger.py` + thin per-runtime `hooks.json` Stop
adapters (maintainer chose option A, "identical copies now; Verifier in inc-5").
The canonical body is authored + smoke-tested (6 cases incl. the inline-`` `[ ]` ``
false-positive guard) and **pinned verbatim in §"Pinned canonical body" below**.

**Mid-3b detour, now DONE — epic `livespec-gcp2` (red-green-replay
fleet+adopter-wide).** Maintainer directive (2026-06-25): red-green-replay MUST
be enforced fleet+adopter-wide, regardless of any "no product Python"
self-classification. LANDED: both Python Drivers wired at lefthook **and**
authoritative CI (`livespec-driver-claude#40`, master `0107028`; codex master
`8abbea1`+`356aabc`); core policy `livespec#589`, cut `v141`; adopters already
covered by the `templates/impl-plugin/` copier scaffold. The Rust console
analogue is `livespec-1t17` (separate; not gcp2). The mechanical fleet-wide
Verifier is increment-5 Conformance-Pattern work. **Consequence for 3b:** the
Drivers now ENFORCE red-green, so the two driver-hook PRs below MUST follow the
Red→Green ritual (failing test first, then impl).

Open child: **`livespec-zs22.5`** — REMAINING: the two Driver hook impls (see
Next concrete action). Increments 4-5 are design-doc-sequenced, filed as they
ripen.

## Next concrete action

**Increment 3b — the two Driver hook impls (`livespec-zs22.5`).** The core
contract (`#584`/`v140`) is merged; what remains is to ship the byte-identical
canonical `no_shadow_ledger.py` (pinned below) in BOTH Drivers, each wired as a
`Stop` hook, **under the Red→Green ritual the Drivers now enforce** (gcp2).
Drive as ONE cross-repo epic; do NOT defer pieces.

- **`livespec-driver-claude`**: add `.claude-plugin/hooks/no_shadow_ledger.py`
  (verbatim from §"Pinned canonical body"); add `.claude-plugin/hooks/**` to
  `[tool.ruff]` `extend-exclude` (so ruff does not reformat it and break
  byte-identity — codex's `livespec/hooks/**` is already excluded); ADD a `Stop`
  entry to `.claude-plugin/hooks/hooks.json` invoking
  `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/no_shadow_ledger.py"` ALONGSIDE the
  existing `warn-plan-persistence.sh` Stop entry (both fire); update
  `SPECIFICATION/contracts.md` (its own) to realize the surface; add
  `tests/hooks/test_no_shadow_ledger.py` (model on `test_warn_plan_persistence.py`).
- **`livespec-driver-codex`**: add `livespec/hooks/no_shadow_ledger.py`
  (BYTE-IDENTICAL — `cmp` it); ADD a `Stop` entry to `livespec/hooks/hooks.json`
  (today PreToolUse-only); update `SPECIFICATION/contracts.md` §"Hook bundle"
  (was "carries ONE hook"); add the test (model on
  `test_livespec_footgun_guard.py`). **Codex Stop-input caveat:** the body reads
  the Claude Stop I/O shape (`transcript_path`); fail-open means a format
  mismatch is SAFE (inert, never breaks). Live-Codex Stop-input verification is a
  separate follow-up; if it differs, the contract-sanctioned fix is a thin Codex
  input-normalizer adapter, NOT a change to the shared body.

**Red→Green ritual (both repos now enforce it at lefthook + CI):** commit the
test FIRST (Red — failing, staged alone, no impl), then `git commit --amend`
adding the impl + ride-alongs (Green). The hook `.py` is product Python now under
`check-red-green-replay`. Validation: each repo's full `just check` + all PR
checks green. NO pyright in the Driver repos; the hook dir is ruff-excluded; so
the body ships verbatim. NOT in scope (design doc "do NOT fix defects tactically
ahead of the pattern"): reconciling the divergent footgun guards (228 vs 365) or
backfilling codex's missing warn-plan-persistence/block-auto-memory — increment-5
Conformance work.

**Then increment 4** (console control-plane contract: a NEW NON-normative
orchestrator/console-Plane `####` block in core
`non-functional-requirements.md`, modeled on the Dispatcher/grooming guidance,
+ the EXISTING `livespec-console-beads-fabro/SPECIFICATION/spec.md` diagram
extended — mermaid both sides) and **increment 5** (Conformance Pattern — file
the M0-M6 epic from
`research/factory-conformance/cross-repo-conformance-pattern.md` once
increment 3 lands). See §"Recon" for the verified cross-repo facts.

## Pinned canonical body (`no_shadow_ledger.py`)

The single source for the two 3b Driver hooks — ship BYTE-IDENTICAL in both
(`livespec-driver-claude/.claude-plugin/hooks/`,
`livespec-driver-codex/livespec/hooks/`). Authored + smoke-tested 2026-06-25
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
does-not-own) + an existing mermaid diagram (Console/LiveSpec/Orchestrator
nodes). Increment 4 EXTENDS this, not greenfield; it also has a `prompts/`
dir with handoff files.

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
and its Read-first chain can execute the next action (increment 3b) without
re-deriving anything. Status comes from the FIRST ACTION ledger query, never
from this file.

## Archive condition

When `livespec-zs22` closes (all increments landed, the Planning Lane
guidance in core NFR, the Conformance Pattern shipped), `git mv` this file
to `archive/prompts/` with a completion banner. The durable history then
lives in the spec, the spec history, the commits, and the ledger.
