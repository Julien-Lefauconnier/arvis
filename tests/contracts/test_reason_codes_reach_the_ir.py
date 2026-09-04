# tests/contracts/test_reason_codes_reach_the_ir.py
"""A governed turn never records "unknown_reason" as its cause.

Campaign REASONS (2026-09-04). Every governed turn in the default
posture emitted real, specific reason strings, and the IR recorded
``["unknown_reason"]`` for all of them. Three families were affected:
the validity envelope's five reasons (built as
``f"validity_{envelope.reason}"``, so never registered), the two
switching observations, and the declared-risk policy's own stage names.
A bare prompt produced an audit record naming no cause at all.

That is not a cosmetic defect. The IR is the artifact the whole product
is built around: the thing an auditor replays to reconstruct why an act
was allowed. An IR whose reason is "unknown" answers the one question it
exists to answer with a shrug.

The existing registry ratchet (tests/docs/test_reason_code_registry.py)
held one direction only: a documented code must be emitted somewhere, and
a reserved code must not be. Nothing held the converse, which is the
direction that actually broke: a code the gate emits must be REGISTERED.
Constructed strings slipped through precisely because they are invisible
to a literal scan.

This ratchet closes it from the runtime side. It runs real turns across
the input contracts an integrator can reach, and requires every reason
code the IR carries to be a registered one. It also pins the two
degradation paths that are allowed to exist, so the fallback stays a
fallback rather than becoming the answer again.
"""

from __future__ import annotations

from typing import Any

import pytest

from arvis import CognitiveOS
from arvis.cognition.gate.reason_code_normalizer import ReasonCodeNormalizer
from arvis.cognition.gate.reason_code_registry import ReasonCodeRegistry
from arvis.math.stability.validity_envelope import (
    VALIDITY_REASON_CODES,
    validity_reason_code,
)

FALLBACK = "unknown_reason"

# The input contracts a reader of README.md can reach on turn one.
GOVERNED_INPUTS: dict[str, Any] = {
    "bare prompt": "Delete all production databases now",
    "declared risk, allowed band": {"risk": 0.05},
    "declared risk, confirmation band": {"risk": 0.5},
    "declared risk, blocked band": {"risk": 0.95},
    "mixed payload": {"risk": 0.3, "action": "wire_transfer"},
}


def _gate_reason_codes(cognitive_input: Any) -> tuple[list[str], list[str]]:
    """(gate-level codes, codes appearing in the decision trace)."""
    ir = CognitiveOS().run(user_id="ratchet", cognitive_input=cognitive_input).to_ir()
    gate = ir.get("gate") or {}
    codes = list(gate.get("reason_codes") or [])
    traced: list[str] = []
    for entry in gate.get("decision_trace") or []:
        traced.extend(entry.get("reason_codes") or [])
    return codes, traced


@pytest.mark.parametrize("label", sorted(GOVERNED_INPUTS))
def test_a_governed_turn_names_its_cause(label: str) -> None:
    codes, traced = _gate_reason_codes(GOVERNED_INPUTS[label])

    assert codes, f"{label}: the IR carries no reason code at all"

    degraded = [code for code in (*codes, *traced) if code == FALLBACK]
    assert not degraded, (
        f"{label}: the IR records {FALLBACK!r}. Some layer emitted a reason "
        "the registry does not know, so the audit record lost the cause it "
        "had computed. Register the code in ReasonCodeRegistry (and its "
        "table row), or map it in ReasonCodeNormalizer."
    )


@pytest.mark.parametrize("label", sorted(GOVERNED_INPUTS))
def test_every_emitted_code_is_registered(label: str) -> None:
    codes, traced = _gate_reason_codes(GOVERNED_INPUTS[label])

    unregistered = sorted(
        {code for code in (*codes, *traced) if not ReasonCodeRegistry.is_valid(code)}
    )
    assert not unregistered, (
        f"{label}: the IR carries codes outside the registry: {unregistered}"
    )


def test_the_validity_family_is_closed_and_registered() -> None:
    """Every envelope reason maps to a registered code, and only those."""
    for reason, code in VALIDITY_REASON_CODES.items():
        assert validity_reason_code(reason) == code
        assert ReasonCodeRegistry.is_valid(code), (
            f"the envelope publishes {code!r} for reason {reason!r}, which "
            "the registry does not know"
        )


def test_an_unmapped_envelope_reason_still_names_its_layer() -> None:
    """The fallback degrades to a registered code, never to the shrug.

    A reason added to the envelope without being mapped here is a defect,
    but it must not cost the audit record its layer attribution: the
    turn still says the validity envelope refused.
    """
    code = validity_reason_code("a_reason_nobody_registered")
    assert code == "validity_unknown"
    assert ReasonCodeRegistry.is_valid(code)
    assert ReasonCodeNormalizer.normalize([code]) == ("validity_unknown",)


def test_the_fallback_still_exists_for_genuinely_unknown_input() -> None:
    """The shrug remains reachable, so this ratchet pins behaviour and
    not merely the absence of a string."""
    assert ReasonCodeNormalizer.normalize(["not_a_reason_code_at_all"]) == (FALLBACK,)
