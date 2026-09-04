# tests/docs/test_readme_front_matter.py
"""The first screen of the README tells the truth, or the gate fails.

Campaign L1 (external audit #4, finding C-01, 2026-09-04). The README
opened with "The Cognitive Operating System for Governed AI Systems"
and ran 642 lines; the first sentence saying that ARVIS does not judge
CONTENT was line 443. An auditor ran three prompts, got one identical
verdict, and concluded the product did not work. He was not wrong to
conclude that: nothing he had read warned him.

The defect was not the absence of the caveats. They were written, in
detail, and they were true. The defect was ORDER: a reader decides in
the first screen, and the first screen sold something the package does
not deliver. Prose drifts back upward release after release, one
enthusiastic sentence at a time, which is exactly what a ratchet is
for.

What is pinned here:

- the README declares what the package IS (a runtime assurance kernel)
  in its opening lines, not what it aspires to become;
- the three decisive caveats (content is not read, ``production``
  refuses everything, ``ALLOW`` is conditional) appear inside the
  first ``FRONT_MATTER_LINES`` lines;
- "cognitive operating system" may still appear there, but only
  qualified as an ambition, never as the definition of the package;
- the whole file stays short enough to be read (``MAX_LINES``), which
  is what makes the ordering matter at all.

The executable proof of the first caveat lives next door in
test_readme_outputs.py: the two-prompt snippet shown in that section is
run, and its identical verdicts must be what the engine really
produces.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"

# The reader decides here. Everything decisive fits above this line.
FRONT_MATTER_LINES = 50

# One-way: the README may get shorter, never longer than this.
MAX_LINES = 305

# Each caveat, with the regex that recognizes it however it is reworded.
REQUIRED_CAVEATS: dict[str, str] = {
    "content is not read": r"does not read your content|not from what the text says",
    "production refuses everything": r"`production` profile refuses everything",
    "ALLOW is conditional": r"`ALLOW` is conditional",
}

# The package is defined by what it is, in the opening lines.
DEFINITION = r"runtime assurance kernel"

# The ambition may appear, but never as the definition.
AMBITION = re.compile(r"cognitive operating system", re.IGNORECASE)
AMBITION_QUALIFIER = re.compile(
    r"long-term ambition is a cognitive operating system", re.IGNORECASE
)


def _readme_lines() -> list[str]:
    if not README.is_file():
        pytest.skip("source checkout required (README.md not found)")
    return README.read_text(encoding="utf-8").splitlines()


def _front_matter() -> str:
    return "\n".join(_readme_lines()[:FRONT_MATTER_LINES])


def test_the_readme_stays_readable() -> None:
    lines = _readme_lines()
    assert len(lines) <= MAX_LINES, (
        f"README.md is {len(lines)} lines, ceiling is {MAX_LINES}. This "
        "ratchet only ever moves down: cut a section rather than raise it."
    )


def test_the_opening_says_what_the_package_is() -> None:
    front = _front_matter()
    assert re.search(DEFINITION, front, re.IGNORECASE), (
        f"the first {FRONT_MATTER_LINES} lines of README.md no longer "
        f"define ARVIS as a {DEFINITION!r}"
    )


def test_the_decisive_caveats_are_on_the_first_screen() -> None:
    front = _front_matter()
    missing = [
        name
        for name, pattern in REQUIRED_CAVEATS.items()
        if not re.search(pattern, front)
    ]
    assert not missing, (
        f"these caveats left the first {FRONT_MATTER_LINES} lines of "
        f"README.md: {missing}. A reader decides on the first screen; a "
        "caveat below it is a caveat nobody reads (audit #4, C-01)."
    )


def test_the_ambition_is_never_the_definition() -> None:
    front = _front_matter()
    for match in AMBITION.finditer(front):
        line_start = front.rfind("\n", 0, match.start()) + 1
        line_end = front.find("\n", match.end())
        line = front[line_start : line_end if line_end != -1 else len(front)]
        assert AMBITION_QUALIFIER.search(line), (
            "README.md calls ARVIS a cognitive operating system without "
            f"marking it as the long-term ambition:\n  {line.strip()}"
        )
