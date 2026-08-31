# tests/docs/test_readme_outputs.py
"""The README's shown outputs are executed, not asserted by hand.

For nine releases the README displayed a fabricated output block: the
wrong method's format, the wrong number of lines, and a status
combination (BLOCKED with Approval Need: YES) that the decision model
cannot produce (audit B1, 2026-08). The example smoke discards stdout,
so nothing caught it.

This ratchet closes that hole:

- every ``python`` fence in README.md that ends with a ``print(...)``
  and is immediately followed by a ``text`` fence is EXECUTED, and its
  stdout must equal the shown block (commitment hashes normalized,
  since they change whenever the IR content legitimately changes);
- the documented input-risk thresholds must be the code's constants;
- the finance example really prints the refusal it narrates.

Editing the README's examples therefore means re-running them, which is
the point.
"""

from __future__ import annotations

import contextlib
import io
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"

_FENCE = re.compile(r"```(\w+)\n(.*?)```", re.DOTALL)
_COMMITMENT = re.compile(r"\b[0-9a-f]{16}\.\.\.")


def _paired_snippets() -> list[tuple[str, str]]:
    """(python_code, shown_output) pairs: a python fence that prints,
    immediately followed by a text fence."""
    fences = _FENCE.findall(README.read_text(encoding="utf-8"))
    pairs: list[tuple[str, str]] = []
    for (lang_a, body_a), (lang_b, body_b) in zip(fences, fences[1:], strict=False):
        if lang_a == "python" and lang_b == "text" and "print(" in body_a:
            pairs.append((body_a, body_b))
    return pairs


def _normalize(text: str) -> str:
    text = _COMMITMENT.sub("<commitment>", text)
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines)


def _run_snippet(code: str) -> str:
    buffer = io.StringIO()
    namespace: dict[str, object] = {}
    with contextlib.redirect_stdout(buffer):
        exec(compile(code, "<readme>", "exec"), namespace)  # noqa: S102
    return buffer.getvalue()


def test_readme_shown_outputs_are_real() -> None:
    pairs = _paired_snippets()
    assert pairs, "README lost its executable example/output pairs"
    for code, shown in pairs:
        produced = _run_snippet(code)
        assert _normalize(produced) == _normalize(shown), (
            "README shows an output its own code does not produce.\n"
            f"--- code ---\n{code}\n--- shown ---\n{shown}\n"
            f"--- produced ---\n{produced}"
        )


def test_readme_summary_line_is_real() -> None:
    """The abridged summary() one-liner shown in the README carries
    labels the method really produces on the documented run."""
    from arvis import CognitiveOS

    produced = (
        CognitiveOS().run(user_id="demo", cognitive_input={"risk": 0.92}).summary()
    )
    for token in ("Stability=n/a", "Risk=n/a", "Regime=n/a", "DeclaredRisk=0.92"):
        assert token in produced, (
            f"summary() lost its documented label {token!r}:\n{produced}"
        )


def test_readme_thresholds_are_the_code_constants() -> None:
    from arvis.kernel.gate.input_risk import (
        INPUT_RISK_ABSTAIN_THRESHOLD,
        INPUT_RISK_CONFIRM_THRESHOLD,
    )

    text = README.read_text(encoding="utf-8")
    assert f"`risk < {INPUT_RISK_CONFIRM_THRESHOLD}`" in text, (
        "README no longer documents the confirm threshold the code uses"
    )
    assert f"`risk >= {INPUT_RISK_ABSTAIN_THRESHOLD}`" in text, (
        "README no longer documents the abstain threshold the code uses"
    )


def test_finance_example_prints_the_refusal_it_narrates() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples" / "06_finance_risk_screening.py")],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert "BLOCKED" in result.stdout, (
        "example 06 is documented as a refusal demonstration; its stdout "
        "no longer shows one"
    )
