# tests/kernel/test_gating_regime.py
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from arvis.kernel.pipeline.stages.gate.gating_regime import (
    GatingRegime,
    apply_answer_gate,
    select_gating_regime,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def _ctx(
    *,
    decision_kind: str | None,
    proposed_actions: list[str] | None = None,
    surface_kind: str | None = "linguistic",
) -> Any:
    ir_decision = SimpleNamespace(
        decision_kind=decision_kind,
        proposed_actions=proposed_actions or [],
    )
    return SimpleNamespace(
        decision_layer=SimpleNamespace(ir_decision=ir_decision),
        ir_input=SimpleNamespace(surface_kind=surface_kind),
        extra={},
    )


def test_informational_linguistic_no_action_is_answer_regime() -> None:
    assert select_gating_regime(_ctx(decision_kind="informational")) is (
        GatingRegime.ANSWER
    )


def test_conversational_is_answer_regime() -> None:
    assert select_gating_regime(_ctx(decision_kind="conversational")) is (
        GatingRegime.ANSWER
    )


def test_action_kind_is_action_regime() -> None:
    assert select_gating_regime(_ctx(decision_kind="action")) is GatingRegime.ACTION


def test_unknown_kind_falls_back_to_action_regime() -> None:
    assert select_gating_regime(_ctx(decision_kind="unknown")) is GatingRegime.ACTION


def test_informational_with_proposed_action_is_action_regime() -> None:
    regime = select_gating_regime(
        _ctx(decision_kind="informational", proposed_actions=["wire_transfer"])
    )
    assert regime is GatingRegime.ACTION


def test_non_linguistic_surface_is_action_regime() -> None:
    regime = select_gating_regime(
        _ctx(decision_kind="informational", surface_kind="tool")
    )
    assert regime is GatingRegime.ACTION


def test_missing_decision_layer_falls_back_to_action_regime() -> None:
    assert select_gating_regime(SimpleNamespace(extra={})) is GatingRegime.ACTION


def test_answer_gate_allows() -> None:
    ctx = _ctx(decision_kind="informational")
    verdict = apply_answer_gate(ctx, verdict=LyapunovVerdict.ABSTAIN)
    assert verdict is LyapunovVerdict.ALLOW
