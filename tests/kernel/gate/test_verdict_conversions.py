# tests/kernel/gate/test_verdict_conversions.py
"""The verdict conversions are total, exhaustive and fail-closed.

Campaign SURFACE (DM-S5, 2026-09-02). The conversions between the
gate verdict vocabularies used to live as scattered string
comparisons with an implicit fail-open else branch (pi_override fell
to ALLOW on anything unrecognized). The typed mappings are locked by
exhaustive tables here: every member of each enum is covered, the
compositions round-trip, and every non-member input lands on ABSTAIN.
"""

from __future__ import annotations

import pytest

from arvis.cognition.gate.cognitive_gate_verdict import CognitiveGateVerdict
from arvis.ir.gate import CognitiveGateVerdictIR
from arvis.kernel.gate.verdict_conversions import (
    GATE_IR_TO_LYAPUNOV,
    LYAPUNOV_TO_GATE_IR,
    gate_ir_from_lyapunov,
    lyapunov_from_gate_ir,
    parse_gate_verdict_wire,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

EXPECTED_PAIRS = [
    (CognitiveGateVerdictIR.ALLOW, LyapunovVerdict.ALLOW),
    (
        CognitiveGateVerdictIR.REQUIRE_CONFIRMATION,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
    ),
    (CognitiveGateVerdictIR.ABSTAIN, LyapunovVerdict.ABSTAIN),
]


def test_the_tables_are_exhaustive_over_both_enums() -> None:
    assert set(GATE_IR_TO_LYAPUNOV) == set(CognitiveGateVerdictIR)
    assert set(LYAPUNOV_TO_GATE_IR) == set(LyapunovVerdict)


@pytest.mark.parametrize(("gate_ir", "lyapunov"), EXPECTED_PAIRS)
def test_the_mapping_is_name_faithful_both_ways(
    gate_ir: CognitiveGateVerdictIR, lyapunov: LyapunovVerdict
) -> None:
    assert lyapunov_from_gate_ir(gate_ir) is lyapunov
    assert gate_ir_from_lyapunov(lyapunov) is gate_ir


@pytest.mark.parametrize("gate_ir", list(CognitiveGateVerdictIR))
def test_round_trip_through_lyapunov(gate_ir: CognitiveGateVerdictIR) -> None:
    assert gate_ir_from_lyapunov(lyapunov_from_gate_ir(gate_ir)) is gate_ir


@pytest.mark.parametrize("bogus", [None, "Allow", "unknown", 0, 1.0, object()])
def test_non_members_fail_closed_to_abstain(bogus: object) -> None:
    assert lyapunov_from_gate_ir(bogus) is LyapunovVerdict.ABSTAIN  # type: ignore[arg-type]
    assert gate_ir_from_lyapunov(bogus) is CognitiveGateVerdictIR.ABSTAIN  # type: ignore[arg-type]
    assert parse_gate_verdict_wire(bogus) is CognitiveGateVerdictIR.ABSTAIN


def test_each_direction_tolerates_only_its_own_wire_values() -> None:
    """StrEnum members hash as their wire values, so an exact wire
    string resolves in its own vocabulary; the OTHER vocabulary's
    casing still fails closed (no cross-vocabulary aliasing)."""
    assert lyapunov_from_gate_ir("ALLOW") is LyapunovVerdict.ABSTAIN  # type: ignore[arg-type]
    assert gate_ir_from_lyapunov("allow") is CognitiveGateVerdictIR.ABSTAIN  # type: ignore[arg-type]


@pytest.mark.parametrize("gate_ir", list(CognitiveGateVerdictIR))
def test_the_wire_parser_accepts_every_wire_value(
    gate_ir: CognitiveGateVerdictIR,
) -> None:
    assert parse_gate_verdict_wire(gate_ir.value) is gate_ir
    assert parse_gate_verdict_wire(gate_ir) is gate_ir


@pytest.mark.parametrize("lyapunov", list(LyapunovVerdict))
def test_the_cognition_enum_owns_its_total_conversion(
    lyapunov: LyapunovVerdict,
) -> None:
    converted = CognitiveGateVerdict.from_lyapunov(lyapunov)
    assert converted.name == lyapunov.name


def test_the_cognition_conversion_fails_closed() -> None:
    assert (
        CognitiveGateVerdict.from_lyapunov("bogus")  # type: ignore[arg-type]
        is CognitiveGateVerdict.ABSTAIN
    )


def test_wire_values_are_unchanged() -> None:
    """DM-S5 boundary: this refactor moves conversions, it never moves
    a serialized value (the IR vocabulary is part of canonical bytes)."""
    assert [v.value for v in CognitiveGateVerdictIR] == [
        "allow",
        "require_confirmation",
        "abstain",
    ]
    assert [v.value for v in LyapunovVerdict] == [
        "ALLOW",
        "REQUIRE_CONFIRMATION",
        "ABSTAIN",
    ]
    assert [v.value for v in CognitiveGateVerdict] == [
        "allow",
        "require_confirmation",
        "abstain",
    ]
