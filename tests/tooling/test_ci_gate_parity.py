# tests/tooling/test_ci_gate_parity.py
"""Campaign CI, RED-first: the workflows run the gate, they do not
reimplement it.

CONTRIBUTING promises "one command runs everything CI runs" and the
pull-request template asks contributors to tick that the gate is
green. The lint-and-type job nevertheless hand-copied the gate's
static commands (ruff, mypy, check_md_refs, check_path_headers) and
invoked the script only for `security`. Every new check therefore had
to be added in two places, and the newest one, the broad-except
ratchet that guards against silently swallowed failures, was added in
one: a pull request introducing a silent swallower merged green and
the failure surfaced only at tag time.

These pins make the parity structural rather than a promise. The gate
script owns each check exactly once; the workflows select which modes
to run, and may not spell a check's command out themselves.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "scripts" / "run_quality_gate.sh"
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))

# Commands that define a check. A workflow naming one of these
# directly has forked the definition instead of calling the gate.
_GATE_OWNED_COMMANDS = (
    "ruff check",
    "ruff format",
    "mypy arvis",
    "bandit -r",
    "check_md_refs.py",
    "check_path_headers.py",
    "check_broad_excepts.py",
    "check_module_coverage.py",
    "run_examples_smoke.sh",
)


def _gate_modes() -> set[str]:
    """The modes the script accepts, read from its case statement."""
    body = GATE.read_text()
    case_block = body.split("case ", 1)[1]
    return set(re.findall(r"^\s{2}([a-z]+)\)", case_block, re.MULTILINE))


def _workflow_text() -> str:
    return "\n".join(path.read_text() for path in WORKFLOWS)


def test_the_gate_exposes_the_granularity_ci_needs() -> None:
    """CI parallelizes into separate jobs, so a single all-or-nothing
    entry point cannot be reused without running the suite several
    times. The script offers one mode per job instead."""
    modes = _gate_modes()

    assert {"all", "static", "security", "tests", "examples"} <= modes, modes


def test_every_gate_mode_is_invoked_by_a_workflow() -> None:
    """A mode nobody runs is a check nobody runs."""
    text = _workflow_text()

    for mode in sorted(_gate_modes()):
        assert f"run_quality_gate.sh {mode}" in text, mode


def test_no_workflow_reimplements_a_gate_owned_command() -> None:
    """The defect this campaign closes: a workflow spelling out a
    check's command forks its definition, and the fork drifts."""
    offenders: list[str] = []

    for path in WORKFLOWS:
        for number, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for command in _GATE_OWNED_COMMANDS:
                if command in stripped and "run_quality_gate.sh" not in stripped:
                    offenders.append(f"{path.name}:{number}: {stripped}")

    assert not offenders, "\n".join(offenders)


def test_the_broad_except_ratchet_actually_runs_in_ci() -> None:
    """The concrete regression: this check existed in the gate and in
    no workflow. It is covered by the two pins above, and named here
    so the reason survives them."""
    text = _workflow_text()

    assert "run_quality_gate.sh static" in text
    assert "check_broad_excepts.py" in GATE.read_text()
