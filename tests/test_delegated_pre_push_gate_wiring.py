"""Lockstep tests for this repository's DELEGATED pre-push gate opt-in.

livespec delegates its pre-push gate to the `gates` namespace of the
self-hosted k3s pool (work-item `livespec-bwzu5t`, a child of the
livespec-dev-tooling plan `delegated-gate-fleet-rollout`). The contract is the
delegated-gate-execution clause of `SPECIFICATION/non-functional-requirements.md`,
realized in the pre-push part of `SPECIFICATION/contracts.md`; the client the
recipe calls is `livespec_dev_tooling.gate_remote_delegate`, whose own contract
is that repository's `SPECIFICATION/contracts.md`. The named properties quoted
below — *The host*, *The verdict* — are that clause's own, cited by name rather
than by heading because a heading-level citation rots on rename.

Four facts are asserted, and each is read out of the artifact that OWNS it
rather than out of a copy of it here:

1. **The opt-in.** Read through the shipped `load_delegated_gate` — the same
   reader the client itself consults — so a key renamed or re-homed upstream
   reds this test rather than silently switching delegation back off while
   `pyproject.toml` still carries a line that looks like an opt-in.

2. **The recipe's delegated path.** *The verdict* forbids an automatic
   fall-back: once delegation has been selected, a run that reaches no verdict
   MUST refuse the push rather than quietly become a local one. The `exec` is
   therefore load-bearing rather than an optimization — it replaces the shell,
   so no later statement in the recipe can run — and the test reads BOTH halves
   of that, because `exec` alone would still be defeated by a `just check`
   written inside the same branch ahead of it.

3. **The local fall-through.** *The host* requires a host holding no credential
   to run the repository's gate recipe, so the bare `just check` must still be
   there and must sit AFTER the delegation branch: ahead of it, a delegating
   host would run the aggregate it had just delegated.

4. **This host's own answer.** Asserted as the AGREEMENT between the probe's
   exit status and whether this host can read the gates kubeconfig, which is
   non-vacuous on either kind of host and so needs no skip. From a Fabro
   sandbox, which holds no credential, the probe must refuse delegation AND say
   that the push gated locally — *The host* requires a non-delegating host to
   report as much, and a silent refusal is the one shape an operator cannot
   tell apart from a delegated pass afterwards. From the VPS, which does hold
   the credential, the same assertion reads the other way and requires the
   probe to select delegation.

   The local-gating report is asserted as the one IMPLICATION "this host
   delegates, or it said it gated locally" rather than as a host-conditional
   branch. The two say the same thing, and the implication says it on one host:
   a branch has an arm that no single host can take, which would leave this
   test short of the full coverage the repository requires of its own tests and
   would invite a skip where no assertion is actually inapplicable.

The probe is driven IN-PROCESS rather than spawned, per the shared
`tests_no_subprocess_spawn` gate: `main()` reads its command from `sys.argv`,
its repository from the working directory, and writes its report to the
`sys.stderr` it binds at call time, so all three are reachable with
`monkeypatch` and `capsys` and no instrumented child is started.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from livespec_dev_tooling import gate_remote_delegate
from livespec_dev_tooling.config import load_delegated_gate
from livespec_dev_tooling.gate_credential import gates_kubeconfig_readable

__all__: list[str] = []


_REPO_ROOT = Path(__file__).resolve().parents[1]
_JUSTFILE = _REPO_ROOT / "justfile"

_RECIPE_NAME = "check-pre-push"
_CLIENT_MODULE = "livespec_dev_tooling.gate_remote_delegate"
_LOCAL_AGGREGATE = "just check"


def _recipe_body(*, name: str) -> list[str]:
    """The indented body lines of one justfile recipe, comments stripped.

    A recipe opens at column zero and its body is the indented run that
    follows, so the extraction needs no `just` parse. Comment and blank lines
    are dropped because the surrounding prose legitimately NAMES the local
    aggregate while explaining why the delegated branch never reaches it, and a
    reader that counted those would convict the recipe of the very fall-through
    the comment says it does not take.

    The body is SLICED between two indices rather than accumulated through a
    loop that breaks, so every arc of this helper is taken on every call — a
    `break` the justfile always reaches leaves the loop's own exit arc
    unexercised, and this repository requires full coverage of its tests too.
    The end-of-file index is appended as a sentinel for the same reason: a
    recipe that is the last thing in the file is a shape the justfile does not
    currently have, and a conditional for it would never be taken either.
    """
    lines = _JUSTFILE.read_text(encoding="utf-8").splitlines()
    opener = re.compile(rf"^{re.escape(name)}\s*:")
    opens = [index for index, line in enumerate(lines) if opener.match(line) is not None]
    assert len(opens) == 1, (
        f"the justfile must declare the {name} recipe exactly once; found "
        f"{len(opens)} declarations"
    )
    start = opens[0] + 1
    ends = [
        index
        for index in range(start, len(lines))
        if lines[index].strip() and not lines[index][:1].isspace()
    ] + [len(lines)]
    return [
        line for line in lines[start : ends[0]] if line.strip() and not line.strip().startswith("#")
    ]


def _delegated_branch(*, body: list[str]) -> list[str]:
    """The lines between the delegation probe's `then` and its closing `fi`.

    The branch is BOUNDED rather than searched for a keyword, because what the
    second assertion needs to know is what cannot run on this path — and an
    unbounded search answers only what can.
    """
    opened = [
        index + 1
        for index, line in enumerate(body)
        if f"{_CLIENT_MODULE} enabled" in line and line.rstrip().endswith("then")
    ]
    assert len(opened) == 1, (
        f"the {_RECIPE_NAME} recipe must branch exactly once on the "
        f"delegated-gate probe `python -m {_CLIENT_MODULE} enabled`; without it "
        "this repository's opt-in selects nothing at push time. Found: " + repr(body)
    )
    closers = [index for index in range(opened[0], len(body)) if body[index].strip() == "fi"]
    assert closers, f"the delegated-gate branch of the {_RECIPE_NAME} recipe is never closed"
    return body[opened[0] : closers[0]]


def test_repository_configuration_opts_in_to_delegation() -> None:
    """This repository's version-controlled configuration opts it in."""
    assert load_delegated_gate(repo_root=_REPO_ROOT) is True, (
        "`delegated_gate = true` is absent from the [tool.livespec_dev_tooling] "
        f"block of {_REPO_ROOT}/pyproject.toml, so every push runs the local "
        "aggregate however the pre-push recipe is wired"
    )


def test_delegated_path_runs_the_client_in_place_of_the_local_gate() -> None:
    """The delegated path `exec`s the client and can reach no local gate run."""
    branch = _delegated_branch(body=_recipe_body(name=_RECIPE_NAME))
    execed = [
        line
        for line in branch
        if f"{_CLIENT_MODULE} run" in line and line.strip().startswith("exec ")
    ]
    assert len(execed) == 1, (
        "the delegated path of the pre-push recipe must run the client exactly "
        f"once, as `exec ... -m {_CLIENT_MODULE} run`; without `exec` the shell "
        "survives the client and the statements after the branch run, which is "
        "the automatic fall-back the delegated-gate clause forbids. Found: " + repr(branch)
    )
    after_exec = branch[branch.index(execed[0]) + 1 :]
    assert not [line for line in after_exec if line.strip()], (
        "the delegated path carries a statement after the client, so the recipe "
        "is written as though the client's result continued the script: " + repr(after_exec)
    )
    assert not [line for line in branch if _LOCAL_AGGREGATE in line], (
        f"the delegated path runs `{_LOCAL_AGGREGATE}`, so a delegated run's "
        "result leads back to a local run of the gate: " + repr(branch)
    )


def test_local_fall_through_runs_the_gate_recipe_on_the_pushing_host() -> None:
    """Past the delegation branch, the recipe still runs the gate locally."""
    body = _recipe_body(name=_RECIPE_NAME)
    fall_through = [line for line in body if line.strip() == _LOCAL_AGGREGATE]
    assert len(fall_through) == 1, (
        f"the {_RECIPE_NAME} recipe must end in a single bare "
        f"`{_LOCAL_AGGREGATE}` fall-through, which is what a host holding no "
        "gates credential runs: " + repr(body)
    )
    assert body.index(fall_through[0]) > body.index(_delegated_branch(body=body)[-1]), (
        "the local fall-through precedes the delegation branch, so a delegating "
        "host would run the aggregate it had just delegated"
    )


def test_probe_agrees_with_this_host_and_reports_a_local_gating(
    *, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The probe delegates exactly when this host can read the credential."""
    monkeypatch.chdir(_REPO_ROOT)
    monkeypatch.setattr(gate_remote_delegate.sys, "argv", ["gate_remote_delegate", "enabled"])
    code = gate_remote_delegate.main()
    reported = capsys.readouterr().err
    readable = gates_kubeconfig_readable()
    assert (code == 0) is readable, (
        f"the delegated-gate probe exited {code} while this host's gates "
        f"kubeconfig readability is {readable}; a push must delegate from "
        "exactly the hosts that hold the credential. Reported: " + reported
    )
    assert readable or gate_remote_delegate.GATED_LOCALLY in reported, (
        "this host holds no gates credential and the probe refused delegation "
        "without reporting that the push gates locally, so a locally-gated push "
        "is indistinguishable from a delegated one afterwards. Reported: " + reported
    )
