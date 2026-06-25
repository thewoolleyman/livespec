"""Livespec E2E real harness — claude-agent-sdk against the live Claude Code CLI.

Per SPECIFICATION/contracts.md:
this module is the `real` tier counterpart to `fake_claude.py`. Each LLM-driven
function constructs a single-shot prompt that asks the model to emit a
JSON-schema-constrained payload conforming to the corresponding wire-contract
schema, calls `claude_agent_sdk.query()` (one-shot; stateless; fresh client
per call), parses the emitted JSON, writes it to a temp file, and invokes the
real `bin/<cmd>.py` wrapper — identical to the mock tier from that point on.

The non-LLM helpers (`doctor_static`, `prune_history`, `propose_change_invalid`,
`seed_required_workflow_files`) are re-exported from `fake_claude` unchanged
because they perform no LLM round-trip; the mock and real tiers are equivalent
for those operations.

Requirements:
- `ANTHROPIC_API_KEY` env var (consumed by the Claude Code CLI under the hood).
- `claude` CLI (`@anthropic-ai/claude-code`) on PATH — installed via
  `npm install -g @anthropic-ai/claude-code` (the GH workflow handles this; for
  local invocations the developer is responsible).

Model: Haiku 4.5 (`claude-haiku-4-5-20251001`) per li-949's cost analysis.
"""

from __future__ import annotations

import json
import re
import subprocess  # documented integration-test usage
import sys
import tempfile
from pathlib import Path
from typing import cast

import anyio  # transitive dep of claude-agent-sdk

# Re-exported non-LLM helpers (identical between tiers). The mock and real
# tiers diverge ONLY on the LLM-driven payload-generation step; `doctor_static`,
# `prune_history`, `propose_change_invalid` (deliberately-invalid payload to
# exercise the wrapper's exit-4 path), and `seed_required_workflow_files`
# (fixture stub) all perform identical work in both tiers. Single-line
# `import X as X` form (the `as X` rebind suppresses ruff's I001 / F401
# complaints about the re-export pattern).
import fake_claude as _fake
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

doctor_static = _fake.doctor_static
propose_change_invalid = _fake.propose_change_invalid
prune_history = _fake.prune_history
seed_required_workflow_files = _fake.seed_required_workflow_files

__all__ = [
    "critique",
    "doctor_static",
    "propose_change",
    "propose_change_invalid",
    "prune_history",
    "revise",
    "seed",
    "seed_required_workflow_files",
]

# Haiku 4.5 — cost-optimized per work-item li-949. If Haiku proves
# unable to satisfy the multi-step skill flows, surface the failure
# and escalate to Sonnet rather than silently switching.
_MODEL: str = "claude-haiku-4-5-20251001"

# Repo + bin dir constants mirror the values in fake_claude.py. Duplicated
# (rather than imported as `_`-prefixed names) so the SLF001 / cross-module
# private-access discipline stays clean — both modules are at the same depth
# (`tests/e2e/`) so the parents[2] arithmetic is identical.
_REPO_ROOT: Path = Path(__file__).resolve().parents[2]
_BIN_DIR: Path = _REPO_ROOT / ".claude-plugin" / "scripts" / "bin"
_MINIMAL_PROMPTS_DIR: Path = (
    _REPO_ROOT / ".claude-plugin" / "specification-templates" / "minimal" / "prompts"
)
_SCHEMAS_DIR: Path = _REPO_ROOT / ".claude-plugin" / "scripts" / "livespec" / "schemas"
_HARNESS_COMMAND_PATTERN = re.compile(r"<!--\s*livespec-harness-command:\s*([a-z-]+)\s*-->")


def _command_from_prompt_file(*, prompt_file: Path) -> str:
    """Extract the livespec-harness-command from a minimal template prompt file.

    Mirrors `fake_claude._command_from_prompt_file`; duplicated here to keep
    each module self-contained and pass the cross-module private-access
    discipline (SLF001 / `check-private-calls`).
    """
    text = prompt_file.read_text(encoding="utf-8")
    match = _HARNESS_COMMAND_PATTERN.search(text)
    if match is None:
        raise ValueError(f"no livespec-harness-command found in {prompt_file}")
    return match.group(1)


# Strip ```json ... ``` and ``` ... ``` fences if the model emits them despite
# the json_schema output-format constraint. Tolerated as a defensive fallback.
_FENCE_PATTERN = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def seed(*, project_root: Path, intent: str) -> subprocess.CompletedProcess[str]:
    """Invoke bin/seed.py with an LLM-generated seed payload.

    The prompt instructs the model to emit a single-file `files[]` entry at
    `SPECIFICATION/spec.md` (two-part path) per the seed-payload path
    convention in `SPECIFICATION/contracts.md`,
    overriding the minimal template's `SPECIFICATION.md` default so the
    downstream wrappers + doctor checks resolve the spec root identically to
    the mock tier.
    """
    assert _command_from_prompt_file(prompt_file=_MINIMAL_PROMPTS_DIR / "seed.md") == "seed"
    schema = _load_schema(name="seed_input.schema.json")
    prompt = _build_prompt(
        sub_command="seed",
        intent=intent,
        extra_instructions=(
            "Emit a JSON payload that:\n"
            '- Has `template` set to the literal string `"minimal"`.\n'
            "- Has `intent` set to the verbatim user intent below.\n"
            "- Has exactly one entry in `files[]`, with `path` set to the literal\n"
            '  string `"SPECIFICATION/spec.md"` (NOT `"SPECIFICATION.md"`).\n'
            "- Has `sub_specs` set to the empty list `[]`.\n"
            "- The `content` field MUST embed two HTML-comment regions:\n"
            "  `<!-- region:project-intent -->` ... `<!-- /region:project-intent -->`\n"
            "  and `<!-- region:dod -->` ... `<!-- /region:dod -->`.\n"
            "- The H1 heading MUST be derived from the user intent.\n"
            "- BCP14 keywords (MUST, SHOULD, MAY — uppercase only) should appear\n"
            "  in the region content where natural.\n"
        ),
    )
    payload = _llm_generate_json(prompt=prompt, schema=schema)
    return _invoke_with_json(
        wrapper="seed.py",
        flag="--seed-json",
        payload=payload,
        extra_args=["--project-root", str(project_root)],
    )


def propose_change(
    *,
    project_root: Path,
    intent: str,
    topic: str,
) -> subprocess.CompletedProcess[str]:
    """Invoke bin/propose_change.py with an LLM-generated findings payload."""
    assert (
        _command_from_prompt_file(prompt_file=_MINIMAL_PROMPTS_DIR / "propose-change.md")
        == "propose-change"
    )
    schema = _load_schema(name="proposal_findings.schema.json")
    prompt = _build_prompt(
        sub_command="propose-change",
        intent=intent,
        extra_instructions=(
            "Emit a JSON payload that:\n"
            "- Has `findings[]` with at least one entry.\n"
            "- For every finding: `target_spec_files` MUST equal exactly\n"
            '  `["SPECIFICATION/spec.md"]`.\n'
            "- For every finding: `proposed_changes` MUST contain at least one\n"
            "  BCP14 keyword in uppercase (MUST, MUST NOT, SHOULD, SHOULD NOT, MAY).\n"
            "- Do NOT include `spec_commitments` or `author` fields.\n"
            f"- The proposed-change topic is `{topic}`; treat it as context.\n"
        ),
    )
    payload = _llm_generate_json(prompt=prompt, schema=schema)
    return _invoke_with_json(
        wrapper="propose_change.py",
        flag="--findings-json",
        payload=payload,
        extra_args=[
            "--spec-target",
            str(project_root / "SPECIFICATION"),
            "--project-root",
            str(project_root),
            topic,
        ],
    )


def critique(
    *,
    project_root: Path,
    intent: str,
) -> subprocess.CompletedProcess[str]:
    """Invoke bin/critique.py with an LLM-generated findings payload."""
    assert _command_from_prompt_file(prompt_file=_MINIMAL_PROMPTS_DIR / "critique.md") == "critique"
    schema = _load_schema(name="proposal_findings.schema.json")
    prompt = _build_prompt(
        sub_command="critique",
        intent=intent,
        extra_instructions=(
            "Emit a JSON payload that:\n"
            "- Has `findings[]` with at least one entry that critiques the spec.\n"
            "- For every finding: `target_spec_files` MUST equal exactly\n"
            '  `["SPECIFICATION/spec.md"]`.\n'
            "- For every finding: `proposed_changes` MUST contain at least one\n"
            "  BCP14 keyword (uppercase only).\n"
            "- Do NOT include `spec_commitments` or `author` fields.\n"
        ),
    )
    payload = _llm_generate_json(prompt=prompt, schema=schema)
    return _invoke_with_json(
        wrapper="critique.py",
        flag="--findings-json",
        payload=payload,
        extra_args=[
            "--spec-target",
            str(project_root / "SPECIFICATION"),
            "--project-root",
            str(project_root),
        ],
    )


def revise(*, project_root: Path) -> subprocess.CompletedProcess[str]:
    """Invoke bin/revise.py, asking the LLM to accept all pending proposals.

    The LLM is asked to emit one `accept` decision per pending proposal topic
    with empty `resulting_files` (accept without spec-file modification). The
    set of pending topics is discovered from the filesystem before the prompt
    is sent, then injected into the prompt as a closed list — the LLM does
    not need to discover proposals via tools.
    """
    assert _command_from_prompt_file(prompt_file=_MINIMAL_PROMPTS_DIR / "revise.md") == "revise"
    spec_target = project_root / "SPECIFICATION"
    proposed_changes_dir = spec_target / "proposed_changes"
    topics = sorted(
        p.stem
        for p in proposed_changes_dir.glob("*.md")
        if p.name != "README.md" and not p.stem.endswith("-revision")
    )
    schema = _load_schema(name="revise_input.schema.json")
    topics_listing = "\n".join(f"  - {t}" for t in topics) if topics else "  (none)"
    prompt = _build_prompt(
        sub_command="revise",
        intent="Accept every pending proposal as-is for an end-to-end test.",
        extra_instructions=(
            "Emit a JSON payload that:\n"
            "- Has `decisions[]` with exactly one entry per pending topic below.\n"
            '- For every decision: `decision` MUST be `"accept"`.\n'
            "- For every decision: `proposal_topic` MUST match a topic from the list below.\n"
            "- For every decision: `resulting_files` MUST be omitted or set to `[]`.\n"
            "- For every decision: `rationale` MUST be a short sentence explaining acceptance.\n"
            "- Do NOT include `author`.\n\n"
            f"Pending topics ({len(topics)}):\n{topics_listing}\n"
        ),
    )
    payload = _llm_generate_json(prompt=prompt, schema=schema)
    return _invoke_with_json(
        wrapper="revise.py",
        flag="--revise-json",
        payload=payload,
        extra_args=[
            "--spec-target",
            str(spec_target),
            "--project-root",
            str(project_root),
        ],
    )


def _load_schema(*, name: str) -> dict[str, object]:
    """Load a wire-contract JSON schema from `.claude-plugin/scripts/livespec/schemas/`."""
    schema_path = _SCHEMAS_DIR / name
    parsed = cast("object", json.loads(schema_path.read_text(encoding="utf-8")))
    if not isinstance(parsed, dict):
        raise TypeError(f"schema {name} did not parse to a dict: type={type(parsed).__name__}")
    typed: dict[str, object] = {str(k): v for k, v in parsed.items()}  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    return typed


def _build_prompt(
    *,
    sub_command: str,
    intent: str,
    extra_instructions: str,
) -> str:
    """Construct the single-shot prompt for a sub-command's payload-generation call.

    The prompt asks the model to emit ONLY the JSON payload (no commentary, no
    code fence) conforming to the schema enforced by the SDK's `--json-schema`
    flag. The schema-constrained output mode is the primary discipline; the
    prose instructions are a redundancy belt for cases where the model still
    needs domain context the schema cannot express.
    """
    return (
        f"You are the livespec `{sub_command}` payload generator for an automated\n"
        "end-to-end test. Emit ONLY the JSON payload — no prose, no Markdown\n"
        "fences, no commentary. The JSON MUST conform to the wire-contract\n"
        "schema enforced by the runtime.\n\n"
        f"User intent: {intent!r}\n\n"
        f"{extra_instructions}"
    )


def _llm_generate_json(*, prompt: str, schema: dict[str, object]) -> dict[str, object]:
    """One-shot SDK call returning the parsed JSON payload.

    Each invocation creates a fresh conversation (stateless per Q1 of li-949's
    architecture decision). The `output_format={"type": "json_schema", ...}`
    option threads the schema down to the CLI's `--json-schema` flag, which
    constrains the model's output at decode time.
    """
    options = ClaudeAgentOptions(
        model=_MODEL,
        max_turns=1,
        permission_mode="bypassPermissions",
        output_format={"type": "json_schema", "schema": schema},
    )

    async def _collect() -> str:
        chunks: list[str] = []
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        chunks.append(block.text)
            elif isinstance(message, ResultMessage):
                if message.is_error:
                    raise RuntimeError(
                        "claude-agent-sdk reported error: "
                        f"subtype={message.subtype!r} result={message.result!r}"
                    )
                if message.structured_output is not None:
                    return json.dumps(message.structured_output)
        return "".join(chunks)

    raw = anyio.run(_collect)
    cleaned = _strip_fences(text=raw)
    return _parse_json_loosely(text=cleaned)


def _strip_fences(*, text: str) -> str:
    """Strip ```json fences if present; tolerated as a defensive fallback."""
    match = _FENCE_PATTERN.match(text)
    if match is not None:
        return match.group(1)
    return text.strip()


def _parse_json_loosely(*, text: str) -> dict[str, object]:
    """Parse the model's JSON; raise with the raw text on failure for debuggability."""
    try:
        parsed = cast("object", json.loads(text))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"LLM emitted non-JSON output (len={len(text)}); first 500 chars: {text[:500]!r}"
        ) from exc
    if not isinstance(parsed, dict):
        raise TypeError(f"LLM emitted JSON but it is not an object: type={type(parsed).__name__}")
    # JSON object keys are spec-bound to strings; the cast on the line above
    # erased json.loads's `Any` return so the type-checker has nothing to
    # warn about, but defensively coerce anyway for runtime safety.
    typed: dict[str, object] = {str(k): v for k, v in parsed.items()}  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    return typed


def _invoke_with_json(
    *,
    wrapper: str,
    flag: str,
    payload: dict[str, object],
    extra_args: list[str],
) -> subprocess.CompletedProcess[str]:
    """Write payload to a temp file and invoke the wrapper with flag pointing at it."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        json.dump(payload, tmp)
        tmp_path = tmp.name
    return _run_wrapper(
        argv=[sys.executable, str(_BIN_DIR / wrapper), flag, tmp_path, *extra_args],
        cwd=_REPO_ROOT,
    )


def _run_wrapper(
    *,
    argv: list[str],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Invoke a wrapper subprocess. check=False so tests can assert on returncode."""
    return subprocess.run(
        argv,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
