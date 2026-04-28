# tests/kernel/stages/test_gate_stage_memory.py

from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def test_memory_pressure_hard_abstain():
    stage = GateStage()

    ctx = type("Ctx", (), {})()
    ctx.extra = {}
    ctx.bundle = type(
        "B",
        (),
        {
            "memory_features": {
                "memory_pressure": 0.9,
                "has_constraints": False,
            }
        },
    )()

    verdict = stage._apply_memory_policy(ctx, LyapunovVerdict.ALLOW)

    assert verdict == LyapunovVerdict.ABSTAIN
    assert "memory_pressure_hard" in ctx.extra["fusion_reasons"]


def test_memory_pressure_moderate_confirmation():
    stage = GateStage()

    ctx = type("Ctx", (), {})()
    ctx.extra = {}
    ctx.bundle = type(
        "B",
        (),
        {
            "memory_features": {
                "memory_pressure": 0.6,
                "has_constraints": False,
            }
        },
    )()

    verdict = stage._apply_memory_policy(ctx, LyapunovVerdict.ALLOW)

    assert verdict == LyapunovVerdict.REQUIRE_CONFIRMATION


def test_memory_constraints_force_confirmation():
    stage = GateStage()

    ctx = type("Ctx", (), {})()
    ctx.extra = {}
    ctx.bundle = type(
        "B",
        (),
        {
            "memory_features": {
                "memory_pressure": 0.0,
                "has_constraints": True,
            }
        },
    )()

    verdict = stage._apply_memory_policy(ctx, LyapunovVerdict.ALLOW)

    assert verdict == LyapunovVerdict.REQUIRE_CONFIRMATION


def test_memory_policy_safe_no_bundle():
    stage = GateStage()

    ctx = type("Ctx", (), {})()
    ctx.extra = {}
    ctx.bundle = None

    verdict = stage._apply_memory_policy(ctx, LyapunovVerdict.ALLOW)

    assert verdict == LyapunovVerdict.ALLOW
