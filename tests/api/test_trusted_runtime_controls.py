# tests/api/test_trusted_runtime_controls.py

"""Host-controls boundary contract (F-001).

TrustedRuntimeControls are injected by composition through
CognitiveOSConfig. The request-facing extra channel can never carry
them, the production runtime profile rejects them, and gate overrides
can never relax a verdict that is already stricter than ALLOW.
"""

from types import SimpleNamespace

import pytest

from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.api.runtime_controls import TrustedRuntimeControls
from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.pipeline.stages.gate.context import resolve_overrides
from arvis.kernel.pipeline.stages.gate.enforcement import (
    apply_projection_enforcement,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def test_extra_injection_of_host_control_keys_is_inert():
    os = CognitiveOS()
    ctx = os._build_context(
        "u1",
        {},
        extra={
            "force_tool": "evil_tool",
            "_force_execution": True,
            "force_safe_projection": True,
            "force_safe_switching": True,
        },
    )
    assert ctx.runtime_policy.force_tool is None
    assert ctx.runtime_policy.force_execution is False
    overrides = resolve_overrides(ctx)
    assert overrides.force_safe_projection is False
    assert overrides.force_safe_switching is False


def test_resolve_overrides_never_reads_extra():
    ctx = SimpleNamespace(
        extra={
            "force_safe_projection": True,
            "force_safe_switching": True,
        }
    )
    overrides = resolve_overrides(ctx)
    assert overrides == GateOverrides()


def test_injected_controls_reach_policy_and_gates():
    os = CognitiveOS(
        CognitiveOSConfig(
            runtime_controls=TrustedRuntimeControls(
                force_tool="host_tool",
                force_execution=True,
                force_safe_projection=True,
                force_safe_switching=True,
            )
        )
    )
    ctx = os._build_context("u1", {}, extra={})
    assert ctx.runtime_policy.force_tool == "host_tool"
    assert ctx.runtime_policy.force_execution is True
    overrides = resolve_overrides(ctx)
    assert overrides.force_safe_projection is True
    assert overrides.force_safe_switching is True


def test_production_profile_rejects_controls():
    with pytest.raises(ValueError, match="production"):
        CognitiveOS(
            CognitiveOSConfig(
                runtime_mode="production",
                runtime_controls=TrustedRuntimeControls(force_execution=True),
            )
        )


def test_override_cannot_relax_abstain_verdict():
    cert = SimpleNamespace(
        domain_valid=True,
        margin_to_boundary=1.0,
        is_projection_safe=True,
        lyapunov_compatibility_ok=True,
    )
    ctx = SimpleNamespace(
        extra={},
        projection_certificate=cert,
        projection_view=None,
        projected_state=None,
    )
    pipeline = SimpleNamespace(projection_boundary_threshold=0.1)
    verdict = apply_projection_enforcement(
        pipeline,
        ctx,
        LyapunovVerdict.ABSTAIN,
        GateOverrides(
            force_safe_projection=True,
            force_safe_switching=True,
        ),
        delta_w=0.0,
        global_safe=True,
        switching_safe=True,
    )
    assert verdict is LyapunovVerdict.ABSTAIN
