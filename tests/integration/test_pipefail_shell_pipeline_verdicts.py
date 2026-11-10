"""Integration-tier coverage for `SPECIFICATION/scenarios.md`.

Covers the H2 section "A pipefail shell script reports a match in a
large input as a match" — the property
`SPECIFICATION/non-functional-requirements.md` ratifies in its shell
discipline constraints: a governed shell file whose effective option
policy enables pipefail judges a pipeline's success only from a reader
that consumes the pipeline's whole input.

Two halves, matching the two ways the defect is reached:

- A sweep reads every tracked governed shell file (the ratified
  universe: tracked `.sh` files and `.sh.jinja` template sources,
  outside frozen archive paths) and fails naming the file and line of
  each pipeline whose status the file uses and that ends in an
  early-exiting reader while pipefail is enabled. A `||` list is not a
  pipe, so `cmd || grep -q PAT` is never reported.
- A runtime check runs the three sanctioned reader forms under
  `bash -o pipefail` — a here-string membership test, a reader that
  drains its input, and a grouping whose status excludes the writer's —
  and proves each keeps the verdict it gives for a 200-byte input on an
  input larger than a pipe buffer (64 KiB) with the pattern near its
  start. A control runs the unsafe form on the same inputs and shows it
  flips, so the large input is demonstrably one that triggers the
  writer's SIGPIPE rather than one too small to matter.

How the sweep decides that a file "uses a pipeline's status" follows the
ratified definition: the status is tested (an `if`/`elif`/`while`/
`until` condition, behind `!`, or an operand of `&&` or `||`), captured
(`$?` or `PIPESTATUS`), the last command of a function, or reaches
errexit (including a plain assignment of a command substitution, but not
one behind `local`, `export` or `declare`). A pipeline whose status the
file does not use, and one that runs where pipefail is off, are out of
scope.
"""

from __future__ import annotations

import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest

__all__: list[str] = []

pytestmark = pytest.mark.integration

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FROZEN_ARCHIVE_PREFIXES = ("archive/", "plan/archive/")
_SHELL_SUFFIXES = (".sh", ".sh.jinja")
_PIPE_BUFFER_BYTES = 64 * 1024
_SMALL_INPUT_BYTES = 200
_LARGE_INPUT_BYTES = 4 * _PIPE_BUFFER_BYTES
_PATTERN = "needle"
_DECLARATION_BUILTINS = frozenset({"local", "export", "declare", "typeset", "readonly"})
_STATUS_CAPTURES = ("$?", "PIPESTATUS")
_CONDITION_KEYWORDS = frozenset({"if", "elif", "while", "until"})
_HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*(?P<quote>['\"]?)(?P<tag>[A-Za-z_]\w*)(?P=quote)")
_SED_QUIT = re.compile(r"(?:^|[\s;{'\"/0-9$])[qQ]\d*(?:$|[\s;}'\"])")
_NEUTRALISED_GROUP = "<neutralised group>"
_GROUP_STATUS_NEUTRALISERS = frozenset({"true", ":"})
_GREP_OPTIONS_TAKING_AN_ARGUMENT = "efABCdD"


@dataclass(frozen=True, kw_only=True)
class _Token:
    """One lexical piece of a logical line: a command's text, or a control operator."""

    kind: str
    text: str


@dataclass(kw_only=True)
class _Scan:
    """The lexed form of one logical line, and the nesting it ended inside of."""

    tokens: list[_Token] = field(default_factory=list)
    open_nesting: bool = False


@dataclass(frozen=True, kw_only=True)
class _Pipeline:
    """A run of commands joined by `|`, with what surrounds it in its line."""

    stages: tuple[str, ...]
    writer_is_neutralised_group: bool
    negated: bool
    in_command_substitution: bool
    adjacent_to_list_operator: bool


def _is_word_boundary(*, text: str, index: int) -> bool:
    return index < 0 or index >= len(text) or text[index] in " \t;|&()"


@dataclass(kw_only=True)
class _Lexer:
    """Walks one logical line, tracking quote and command-substitution nesting."""

    line: str
    scan: _Scan = field(default_factory=_Scan)
    modes: list[str] = field(default_factory=lambda: ["cmd"])
    buffer: list[str] = field(default_factory=list)
    index: int = 0

    def flush(self) -> None:
        text = "".join(self.buffer).strip()
        self.buffer.clear()
        if text:
            self.scan.tokens.append(_Token(kind="seg", text=text))

    def operator(self, *, text: str, width: int = 1) -> None:
        self.flush()
        self.scan.tokens.append(_Token(kind="op", text=text))
        self.index += width

    def keep(self, *, width: int = 1) -> None:
        self.buffer.append(self.line[self.index : self.index + width])
        self.index += width

    def enter(self, *, mode: str, width: int = 1) -> None:
        self.modes.append(mode)
        self.keep(width=width)

    def step_single_quoted(self) -> None:
        if self.line[self.index] == "'":
            self.modes.pop()
        self.keep()

    def step_double_quoted(self) -> None:
        if self.line.startswith("$(", self.index):
            self.operator(text="$(", width=2)
            self.modes.append("cmd")
            return
        if self.line[self.index] == '"':
            self.modes.pop()
        self.keep()

    def step_command(self) -> None:
        char = self.line[self.index]
        pair = self.line[self.index : self.index + 2]
        if char in "'\"":
            self.enter(mode="sq" if char == "'" else "dq")
        elif pair == "$(" or char == "(":
            self.operator(
                text=pair if pair == "$(" else char, width=len(pair) if pair == "$(" else 1
            )
            self.modes.append("cmd")
        elif char == ")":
            self.operator(text=")")
            self.modes = self.modes[:-1] if len(self.modes) > 1 else self.modes
        else:
            self.step_control()

    def step_control(self) -> None:
        char = self.line[self.index]
        pair = self.line[self.index : self.index + 2]
        previous = self.line[self.index - 1] if self.index else " "
        if pair in ("||", "&&", ";;"):
            self.operator(text=pair, width=2)
        elif pair == "|&":
            self.operator(text="|", width=2)
        elif char in "|;`":
            self.operator(text=char)
        elif char == "&" and previous not in "<>" and pair != "&>":
            self.operator(text="&")
        elif char in "{}" and _is_standalone_brace(line=self.line, index=self.index):
            self.operator(text=char)
        else:
            self.keep()

    def step(self) -> None:
        mode = self.modes[-1]
        if mode != "dq" and self.line[self.index] == "\\":
            self.keep(width=2)
        elif mode == "sq":
            self.step_single_quoted()
        elif mode == "dq":
            if self.line[self.index] == "\\":
                self.keep(width=2)
            else:
                self.step_double_quoted()
        else:
            self.step_command()

    def starts_comment(self) -> bool:
        before = self.line[self.index - 1] if self.index else " "
        return self.modes[-1] == "cmd" and self.line[self.index] == "#" and before in " \t"


def _scan(*, line: str) -> _Scan:
    """Lex one logical line into command segments and control operators.

    Quoted text stays inside its segment, but a `$(` inside double quotes
    still opens a nested command context, because `x="$(a | grep -q b)"`
    holds a pipeline. A `#` that starts a word ends the line.
    """
    lexer = _Lexer(line=line)
    while lexer.index < len(line) and not lexer.starts_comment():
        lexer.step()
    lexer.flush()
    lexer.scan.open_nesting = len(lexer.modes) > 1
    return lexer.scan


def _is_standalone_brace(*, line: str, index: int) -> bool:
    """A `{` or `}` that is a whole shell word, as opposed to part of `${var}`."""
    return _is_word_boundary(text=line, index=index - 1) and _is_word_boundary(
        text=line, index=index + 1
    )


def _logical_lines(*, text: str) -> list[tuple[int, str]]:
    """Join continuations and unterminated nesting; drop heredoc bodies and template tags."""
    physical = text.splitlines()
    logical: list[tuple[int, str]] = []
    index = 0
    while index < len(physical):
        start = index + 1
        parts: list[str] = []
        while index < len(physical):
            raw = physical[index].rstrip()
            index += 1
            stripped = raw.strip()
            if not parts and (stripped.startswith(("{%", "{#"))):
                break
            parts.append(stripped.removesuffix("\\") if stripped.endswith("\\") else stripped)
            joined = " ".join(parts)
            continues = stripped.endswith(("\\", "|", "&&", "||"))
            if not continues and not _scan(line=joined).open_nesting:
                break
        joined = " ".join(parts).strip()
        if joined:
            logical.append((start, joined))
        heredoc = _HEREDOC.search(joined)
        if heredoc:
            while index < len(physical) and physical[index].strip() != heredoc.group("tag"):
                index += 1
            index += 1
    return logical


@dataclass(kw_only=True)
class _Collector:
    """Accumulates the stages of the pipeline being read, and the finished ones."""

    tokens: list[_Token]
    found: list[_Pipeline] = field(default_factory=list)
    stages: list[str] = field(default_factory=list)
    neutralised: bool = False
    start: int = 0
    depth: int = 0
    depth_at_start: int = 0
    in_backticks: bool = False

    def begin(self, *, position: int) -> None:
        self.start = position
        self.neutralised = False
        self.depth_at_start = self.depth

    def finish(self, *, end: int) -> None:
        if len(self.stages) >= 2:
            before = self.tokens[self.start - 1].text if self.start > 0 else ""
            after = self.tokens[end].text if end < len(self.tokens) else ""
            self.found.append(
                _Pipeline(
                    stages=tuple(self.stages),
                    writer_is_neutralised_group=self.neutralised,
                    negated=self.stages[0].startswith("!"),
                    in_command_substitution=self.depth_at_start > 0,
                    adjacent_to_list_operator=bool({before, after} & {"&&", "||"}),
                )
            )
        self.stages.clear()

    def segment(self, *, position: int) -> None:
        if not self.stages:
            self.begin(position=position)
        self.stages.append(self.tokens[position].text)

    def pipe(self, *, position: int) -> None:
        closer = position - 1
        if not self.stages and closer >= 0 and self.tokens[closer].text in ("}", ")"):
            label = _group_label(tokens=self.tokens, closer=closer)
            self.begin(position=closer)
            self.neutralised = label == _NEUTRALISED_GROUP
            self.stages.append(label)

    def operator(self, *, position: int) -> None:
        text = self.tokens[position].text
        if text == "|":
            self.pipe(position=position)
            return
        self.finish(end=position)
        if text in ("$(", "("):
            self.depth += 1
        elif text == ")":
            self.depth = max(0, self.depth - 1)
        elif text == "`":
            self.depth += -1 if self.in_backticks else 1
            self.in_backticks = not self.in_backticks


def _pipelines(*, tokens: list[_Token]) -> list[_Pipeline]:
    """Group a line's tokens into pipelines of two or more stages."""
    collector = _Collector(tokens=tokens)
    for position, token in enumerate(tokens):
        if token.kind == "seg":
            collector.segment(position=position)
        else:
            collector.operator(position=position)
    collector.finish(end=len(tokens))
    return collector.found


def _group_label(*, tokens: list[_Token], closer: int) -> str:
    """Name a closed group as the writer of a pipe, noting whether it hides its own status."""
    commands = [token.text for token in tokens[:closer] if token.kind == "seg"]
    last = commands[-1] if commands else ""
    neutralised = last in _GROUP_STATUS_NEUTRALISERS or last == "exit 0"
    return _NEUTRALISED_GROUP if neutralised else "<group>"


def _words(*, stage: str) -> list[str]:
    try:
        return shlex.split(stage)
    except ValueError:
        return stage.split()


def _command_words(*, stage: str) -> list[str]:
    """The stage's words with leading `!`, keywords and `VAR=value` assignments removed."""
    words = _words(stage=stage)
    if words and words[0] in ("while", "until"):
        return []
    while words and (
        words[0] in ("!", "then", "do", "else", "time", "command")
        or words[0] in _CONDITION_KEYWORDS
        or re.fullmatch(r"[A-Za-z_]\w*=.*", words[0])
    ):
        words = words[1:]
    return words


def _grep_exits_early(*, arguments: list[str]) -> bool:
    for argument in arguments:
        if argument == "--":
            return False
        if argument in ("--quiet", "--silent") or argument.startswith("--max-count"):
            return True
        if argument.startswith("--") or not argument.startswith("-") or len(argument) == 1:
            continue
        for letter in argument[1:]:
            if letter in "qm":
                return True
            if letter in _GREP_OPTIONS_TAKING_AN_ARGUMENT:
                break
    return False


def _head_exits_early(*, arguments: list[str]) -> bool:
    """`head` reads a bounded prefix, unless the count is negative (all but the last N)."""
    for position, argument in enumerate(arguments):
        following = arguments[position + 1] if position + 1 < len(arguments) else ""
        if re.fullmatch(r"-n-\d+|-c-\d+|--lines=-\d+|--bytes=-\d+", argument):
            return False
        if argument in ("-n", "-c", "--lines", "--bytes") and following.startswith(("-", "+")):
            return False
    return True


def _sed_exits_early(*, arguments: list[str]) -> bool:
    return any(_SED_QUIT.search(argument) for argument in arguments)


def _awk_exits_early(*, arguments: list[str]) -> bool:
    return any(re.search(r"\bexit\b", argument) for argument in arguments)


_EARLY_READERS = {
    "grep": _grep_exits_early,
    "egrep": _grep_exits_early,
    "fgrep": _grep_exits_early,
    "head": _head_exits_early,
    "sed": _sed_exits_early,
    "awk": _awk_exits_early,
    "gawk": _awk_exits_early,
    "mawk": _awk_exits_early,
}


def _reader_exits_early(*, stage: str) -> bool:
    words = _command_words(stage=stage)
    if words[:1] == ["read"]:
        return True
    reader = _EARLY_READERS.get(words[0]) if words else None
    return reader is not None and reader(arguments=words[1:])


@dataclass(kw_only=True)
class _Options:
    """The shell options a file has switched on so far, as the sweep reads them."""

    errexit: bool = False
    pipefail: bool = False

    def apply(self, *, stage: str) -> None:
        words = _words(stage=stage)
        if not words or words[0] != "set":
            return
        position = 1
        while position < len(words):
            word = words[position]
            position += 1
            if len(word) < 2 or word[0] not in "-+" or word.startswith("--"):
                continue
            enable = word[0] == "-"
            for letter in word[1:]:
                if letter == "e":
                    self.errexit = enable
                elif letter == "o" and position < len(words):
                    name = words[position]
                    position += 1
                    if name == "errexit":
                        self.errexit = enable
                    elif name == "pipefail":
                        self.pipefail = enable


def _status_is_used(
    *,
    pipeline: _Pipeline,
    line: str,
    next_line: str,
    options: _Options,
) -> bool:
    first_word = line.split(None, 1)[0] if line.split() else ""
    tested = first_word in _CONDITION_KEYWORDS or pipeline.negated
    captured = any(marker in line or marker in next_line for marker in _STATUS_CAPTURES)
    last_of_function = next_line == "}"
    masked = pipeline.in_command_substitution and first_word in _DECLARATION_BUILTINS
    reaches_errexit = options.errexit and not masked
    return (
        tested
        or pipeline.adjacent_to_list_operator
        or captured
        or last_of_function
        or reaches_errexit
    )


def _early_reader_violations(*, text: str, name: str) -> tuple[str, ...]:
    """Name `file:line` for each used-status pipeline that ends in an early-exiting reader."""
    violations: list[str] = []
    options = _Options()
    lines = _logical_lines(text=text)
    for position, (line_number, line) in enumerate(lines):
        next_line = lines[position + 1][1] if position + 1 < len(lines) else ""
        scan = _scan(line=line)
        for pipeline in _pipelines(tokens=scan.tokens):
            if (
                options.pipefail
                and not pipeline.writer_is_neutralised_group
                and _reader_exits_early(stage=pipeline.stages[-1])
                and _status_is_used(
                    pipeline=pipeline, line=line, next_line=next_line, options=options
                )
            ):
                violations.append(f"{name}:{line_number}: {line}")
        for token in scan.tokens:
            if token.kind == "seg":
                options.apply(stage=token.text)
    return tuple(violations)


def _governed_shell_paths() -> tuple[Path, ...]:
    """Every tracked shell file outside the frozen archive paths, read from git's index."""
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(
        _REPO_ROOT / name
        for name in completed.stdout.split("\0")
        if name.endswith(_SHELL_SUFFIXES)
        and not name.startswith(_FROZEN_ARCHIVE_PREFIXES)
        and (_REPO_ROOT / name).is_file()
        and not (_REPO_ROOT / name).is_symlink()
    )


def _verdict(*, program: str, stdin: str) -> int:
    """Run `program` under `bash -o pipefail` with `stdin`, returning its exit status."""
    return subprocess.run(
        ["bash", "-o", "pipefail", "-c", program],
        check=False,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=60,
    ).returncode


def _input_of(*, size: int, matched: bool) -> str:
    """Input of at least `size` bytes with the pattern, if any, on its first line."""
    first = f"{_PATTERN}\n" if matched else "other\n"
    return first + "x" * (size - len(first) - 1) + "\n"


_READ_INPUT = "value=$(cat); "
_FORMS = {
    "here-string": _READ_INPUT + 'grep -q needle <<<"$value"',
    "draining-reader": _READ_INPUT + 'printf "%s" "$value" | grep needle >/dev/null',
    "writer-status-excluded": (
        _READ_INPUT
        + 'first=$({ printf "%s" "$value" || true; } | head -n 1); [ "$first" = needle ]'
    ),
}
_UNSAFE_FORM = _READ_INPUT + 'printf "%s" "$value" | grep -q needle'


@pytest.mark.parametrize("form", sorted(_FORMS))
def test_a_sanctioned_reader_reports_a_match_in_a_large_input_as_a_match(form: str) -> None:
    """Each sanctioned form gives its 200-byte verdict on an input past a pipe buffer."""
    for matched in (True, False):
        small = _input_of(size=_SMALL_INPUT_BYTES, matched=matched)
        large = _input_of(size=_LARGE_INPUT_BYTES, matched=matched)

        small_verdict = _verdict(program=_FORMS[form], stdin=small)
        large_verdict = _verdict(program=_FORMS[form], stdin=large)

        assert small_verdict == (0 if matched else 1)
        assert large_verdict == small_verdict


def test_an_early_exiting_reader_loses_the_match_in_a_large_input() -> None:
    """The control: the unsafe form flips only on the large input, which is why the form matters."""
    small = _input_of(size=_SMALL_INPUT_BYTES, matched=True)
    large = _input_of(size=_LARGE_INPUT_BYTES, matched=True)

    assert _verdict(program=_UNSAFE_FORM, stdin=small) == 0
    assert _verdict(program=_UNSAFE_FORM, stdin=large) == 141


def test_no_governed_pipefail_shell_file_ends_a_used_pipeline_in_an_early_exiting_reader() -> None:
    """The sweep over this repository's tracked governed shell files finds nothing."""
    paths = _governed_shell_paths()
    violations: list[str] = []
    for path in paths:
        violations.extend(
            _early_reader_violations(
                text=path.read_text(encoding="utf-8"),
                name=path.relative_to(_REPO_ROOT).as_posix(),
            )
        )

    assert paths, "the governed shell-file universe must not be empty"
    assert not violations, "\n".join(violations)


_SWEEP_PREAMBLE = "#!/usr/bin/env bash\nset -euo pipefail\n"


@pytest.mark.parametrize(
    "statement",
    [
        "if printf 'needle\\n' | grep -q needle; then :; fi",
        "if printf 'needle\\n' | grep --quiet needle; then :; fi",
        "if printf 'needle\\n' | grep -m 1 needle; then :; fi",
        "if printf 'needle\\n' | grep --max-count=1 needle; then :; fi",
        "if printf 'needle\\n' | grep -qE needle; then :; fi",
        "first=$(printf 'needle\\n' | head -n 1)",
        "first=$(printf 'needle\\n' | head -1)",
        "first=$(printf 'needle\\n' | head -c 4)",
        "first=$(printf 'needle\\n' | sed -n '1p;q')",
        "first=$(printf 'needle\\n' | sed 1q)",
        "first=$(printf 'needle\\n' | awk '{print; exit}')",
        "printf 'needle\\n' | read -r first",
        "printf 'needle\\n' | grep -q needle && echo present",
        "printf 'needle\\n' | grep -q needle || true",
        "printf 'needle\\n' | grep -q 'a|b'",
        "printf 'needle\\n' |& grep -q needle",
        "first=`printf 'needle\\n' | head -n 1`",
        "if printf 'needle\\n' | LC_ALL=C grep -q needle; then :; fi",
        "first=$({ printf 'needle\\n'; } | head -n 1)",
        "! printf 'needle\\n' | grep -q needle",
        "printf 'needle\\n' | grep -q needle; status=$?",
        "present=\"$(printf 'needle\\n' | grep -q needle)\"",
    ],
)
def test_the_sweep_names_the_line_of_an_early_exiting_reader_whose_status_is_used(
    statement: str,
) -> None:
    """Each early-exiting reader form is reported with its file and line."""
    text = f"{_SWEEP_PREAMBLE}{statement}\n"

    assert _early_reader_violations(text=text, name="sample.sh") == (f"sample.sh:3: {statement}",)


def test_the_sweep_joins_a_pipeline_broken_across_lines() -> None:
    """A reader on the line after its writer's trailing pipe is reported at the first line."""
    text = f"{_SWEEP_PREAMBLE}if git diff --name-only |\n    grep -qxE 'needle'; then\n  :\nfi\n"

    assert _early_reader_violations(text=text, name="sample.sh") == (
        "sample.sh:3: if git diff --name-only | grep -qxE 'needle'; then",
    )


@pytest.mark.parametrize(
    "statement",
    [
        "if printf 'needle\\n' | grep needle >/dev/null; then :; fi",
        'if grep -q needle <<<"$value"; then :; fi',
        "if printf 'needle\\n' | grep -c needle; then :; fi",
        "first=$({ printf 'needle\\n' || true; } | head -n 1)",
        "first=$({ printf 'needle\\n'; true; } | head -n 1)",
        "last=$(printf 'a\\nb\\n' | head -n -1)",
        "if cmd || grep -qs needle file; then :; fi",
        "cmd || grep -q needle file",
        "printf 'needle\\n' | sed -n 's/q/x/p'",
        "printf 'needle\\n' | awk '{print $1}'",
        "printf 'needle\\n' | while IFS= read -r line; do :; done",
        "sleep 1 & printf 'needle\\n' | grep needle >/dev/null",
        "if printf 'needle\\n' | grep -- -q; then :; fi",
        "if printf 'needle\\n' | grep -A3 needle; then :; fi",
        "last=$(printf 'a\\nb\\n' | head -n-1)",
        "# printf 'needle\\n' | grep -q needle",
        "echo hi # printf 'needle\\n' | grep -q needle",
    ],
)
def test_the_sweep_leaves_a_safe_form_alone(statement: str) -> None:
    """A draining reader, a read loop, a here-string, a neutralised group and a `||` list pass."""
    text = f"{_SWEEP_PREAMBLE}{statement}\n"

    assert _early_reader_violations(text=text, name="sample.sh") == ()


@pytest.mark.parametrize(
    "preamble",
    [
        "#!/usr/bin/env bash\nset -eu\n",
        "#!/bin/sh\nset -eu\n",
        "#!/usr/bin/env bash\nset -euo pipefail\nset +o pipefail\n",
    ],
)
def test_the_sweep_ignores_a_pipeline_where_pipefail_is_off(preamble: str) -> None:
    """Without pipefail the writer's SIGPIPE does not reach the status, so nothing is reported."""
    text = f"{preamble}if printf 'needle\\n' | grep -q needle; then :; fi\n"

    assert _early_reader_violations(text=text, name="sample.sh") == ()


@pytest.mark.parametrize(
    ("options", "body"),
    [
        ("set -o pipefail", "printf 'needle\\n' | grep -q needle"),
        ("set -euo pipefail", "local first=$(printf 'needle\\n' | head -n 1)"),
        ("set -euo pipefail", "export first=$(printf 'needle\\n' | head -n 1)"),
        ("set -euo pipefail\nset +e", "printf 'needle\\n' | grep -q needle"),
    ],
)
def test_the_sweep_ignores_a_pipeline_whose_status_the_file_does_not_use(
    options: str, body: str
) -> None:
    """With no test, capture, function tail or errexit reaching it, the pipeline is out of scope."""
    text = f"#!/usr/bin/env bash\n{options}\n{body}\n"

    assert _early_reader_violations(text=text, name="sample.sh") == ()


def test_the_sweep_reports_the_last_command_of_a_function_whose_caller_tests_it() -> None:
    """A pipeline that ends a function hands its status to the caller."""
    text = (
        "#!/usr/bin/env bash\nset -o pipefail\n"
        "has_needle() {\n  printf 'needle\\n' | grep -q needle\n}\n"
    )

    assert _early_reader_violations(text=text, name="sample.sh") == (
        "sample.sh:4: printf 'needle\\n' | grep -q needle",
    )


def test_the_sweep_skips_heredoc_bodies_and_template_tags() -> None:
    """Text inside a here-document, and Jinja tags, are not shell commands."""
    text = (
        f"{_SWEEP_PREAMBLE}"
        "{% if enabled %}\n"
        "cat <<'EOF'\n"
        "printf 'needle' | grep -q needle\n"
        "EOF\n"
        "{% endif %}\n"
    )

    assert _early_reader_violations(text=text, name="sample.sh") == ()


def test_the_governed_universe_excludes_frozen_archive_paths_and_keeps_template_sources() -> None:
    """The sweep reads template sources, and never a frozen archive."""
    relative = {path.relative_to(_REPO_ROOT).as_posix() for path in _governed_shell_paths()}

    assert "templates/orchestrator-plugin/dev-tooling/worktree-hydrate.sh.jinja" in relative
    assert not any(name.startswith(_FROZEN_ARCHIVE_PREFIXES) for name in relative)


def test_the_sweep_follows_option_changes_by_long_name_and_ignores_positional_arguments() -> None:
    """`set -o errexit` turns errexit on; `set -o nounset` and `set -- args` change neither."""
    text = (
        "#!/usr/bin/env bash\nset -o pipefail\nset -o nounset\nset -- one two\n"
        "first=$(printf 'needle\\n' | head -n 1)\n"
        "set -o errexit\n"
        "first=$(printf 'needle\\n' | head -n 1)\n"
    )

    assert _early_reader_violations(text=text, name="sample.sh") == (
        "sample.sh:7: first=$(printf 'needle\\n' | head -n 1)",
    )


def test_the_sweep_keeps_an_unfinished_final_pipeline_for_diagnostics() -> None:
    """A file that ends on a trailing pipe still yields its last logical line."""
    assert _logical_lines(text="set -o pipefail\nprintf 'needle\\n' |\n") == [
        (1, "set -o pipefail"),
        (2, "printf 'needle\\n' |"),
    ]
