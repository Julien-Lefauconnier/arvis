# tests/api/test_production_profile.py

"""Closed PRODUCTION profile contract (lot B5).

Doctrine: deny-by-default is an attribute of the PRODUCTION profile,
not of the library. F-002: the permissive global stability default is a
research setting and is overridden in production. F-017/F-018: a tool
declaring required_consent or data_egress is denied when the matching
gate is missing. F-019: the tool registry freezes automatically at the
first run. Plus the one-registry coherence fix: the runtime and its
tool manager govern the same registry the host registered tools on.
"""

from types import SimpleNamespace

import pytest

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.api.audit import AuditCommitmentPolicy
from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.api.runtime_mode import RuntimeMode
from arvis.errors.base import ArvisSecurityError
from arvis.tools.base import BaseTool
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec

# ---------------------------------------------------------------
# Profile factory
# ---------------------------------------------------------------


def test_production_factory_fixes_mode_and_audit_policy():
    config = CognitiveOSConfig.production()
    assert config.runtime_mode is RuntimeMode.PRODUCTION
    assert config.audit_commitment_policy is AuditCommitmentPolicy.REQUIRED


def test_production_factory_accepts_field_overrides():
    config = CognitiveOSConfig.production(strict_mode=True)
    assert config.strict_mode is True
    assert config.runtime_mode is RuntimeMode.PRODUCTION


def test_production_factory_refuses_runtime_mode_override():
    with pytest.raises(ValueError, match="fixes runtime_mode"):
        CognitiveOSConfig.production(runtime_mode="local")


# ---------------------------------------------------------------
# F-002 / A4: production context posture
# ---------------------------------------------------------------


def test_production_context_posture():
    os = CognitiveOS(CognitiveOSConfig.production())
    ctx = os._build_context("u1", {})
    assert ctx.global_stability_action == "confirm"
    assert ctx.switching_envelope_mode == "enforce"


def test_local_context_posture_unchanged():
    os = CognitiveOS()
    ctx = os._build_context("u1", {})
    assert ctx.global_stability_action == "ignore"
    assert ctx.switching_envelope_mode == "soft"


# ---------------------------------------------------------------
# F-019: automatic registry freeze at first run
# ---------------------------------------------------------------


class _InertTool(BaseTool):
    name = "inert_tool"

    def execute(self, input_data):
        return {"ok": True}


def test_registry_freezes_at_first_run_in_production():
    os = CognitiveOS(CognitiveOSConfig.production())
    os.register_tool(_InertTool())

    os.run(user_id="u1", cognitive_input={})

    assert os.tool_registry.frozen is True
    with pytest.raises(ArvisSecurityError, match="frozen"):
        os.register_tool(_InertTool())


def test_registry_stays_open_outside_production():
    os = CognitiveOS()
    os.run(user_id="u1", cognitive_input={})
    assert os.tool_registry.frozen is False


# ---------------------------------------------------------------
# One registry: runtime and manager govern the host registry
# ---------------------------------------------------------------


def test_runtime_shares_the_host_registry():
    os = CognitiveOS()
    assert os.runtime.tool_registry is os.tool_registry
    assert os.runtime.tool_manager.registry is os.tool_registry


# ---------------------------------------------------------------
# F-017/F-018: deny-by-default gates
# ---------------------------------------------------------------


class _GatedTool(BaseTool):
    name = "gated_tool"

    def __init__(self, spec: ToolSpec) -> None:
        self.spec = spec

    def execute(self, input_data):
        return {"ok": True}


def _registry_with(spec: ToolSpec) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(_GatedTool(spec))
    return registry


def _invocation(name: str) -> ToolInvocation:
    return ToolInvocation(tool_name=name, payload={}, process_id="p1")


def test_declared_consent_without_gate_is_denied_when_gates_required():
    spec = ToolSpec(
        name="gated_tool",
        description="",
        required_consent="calendar.write",
    )
    decision = ToolPolicyEvaluator.evaluate(
        _invocation("gated_tool"),
        _registry_with(spec),
        require_gates=True,
    )
    assert decision.allowed is False
    assert decision.reason == "consent_gate_missing"


def test_declared_consent_without_gate_stays_host_concern_by_default():
    spec = ToolSpec(
        name="gated_tool",
        description="",
        required_consent="calendar.write",
    )
    decision = ToolPolicyEvaluator.evaluate(
        _invocation("gated_tool"),
        _registry_with(spec),
    )
    assert decision.allowed is True


def test_data_egress_without_gate_is_denied_when_gates_required():
    spec = ToolSpec(name="gated_tool", description="", data_egress=True)
    decision = ToolPolicyEvaluator.evaluate(
        _invocation("gated_tool"),
        _registry_with(spec),
        require_gates=True,
    )
    assert decision.allowed is False
    assert decision.reason == "egress_gate_missing"


def test_installed_gates_are_still_consulted_when_gates_required():
    spec = ToolSpec(
        name="gated_tool",
        description="",
        required_consent="calendar.write",
        data_egress=True,
    )
    granting_consent = SimpleNamespace(is_granted=lambda invocation, key: True)
    allowing_egress = SimpleNamespace(is_allowed=lambda invocation, spec: True)
    decision = ToolPolicyEvaluator.evaluate(
        _invocation("gated_tool"),
        _registry_with(spec),
        consent_gate=granting_consent,
        egress_gate=allowing_egress,
        require_gates=True,
    )
    assert decision.allowed is True


def test_denying_gate_wins_regardless_of_require_gates():
    spec = ToolSpec(
        name="gated_tool",
        description="",
        required_consent="calendar.write",
    )
    denying_consent = SimpleNamespace(is_granted=lambda invocation, key: False)
    decision = ToolPolicyEvaluator.evaluate(
        _invocation("gated_tool"),
        _registry_with(spec),
        consent_gate=denying_consent,
    )
    assert decision.allowed is False
    assert decision.reason == "consent_required"


def test_production_os_threads_deny_by_default_to_the_manager():
    os = CognitiveOS(CognitiveOSConfig.production())
    assert os.runtime.tool_manager._require_gates is True


def test_local_os_keeps_permissive_manager():
    os = CognitiveOS()
    assert os.runtime.tool_manager._require_gates is False
