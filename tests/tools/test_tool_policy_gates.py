# tests/tools/test_tool_policy_gates.py

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.tools.base import BaseTool
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _GatedTool(BaseTool):
    name = "gated"

    def __init__(self, spec: ToolSpec) -> None:
        self.spec = spec

    def execute(self, input_data):  # pragma: no cover - not run here
        return None


def _registry(spec: ToolSpec) -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(_GatedTool(spec))
    return reg


def _invocation() -> ToolInvocation:
    return ToolInvocation(tool_name="gated", payload={}, process_id="p")


class _DenyConsent:
    def is_granted(self, invocation, consent_key):
        return False


class _AllowConsent:
    def is_granted(self, invocation, consent_key):
        return True


class _DenyEgress:
    def is_allowed(self, invocation, spec):
        return False


def test_consent_gate_denies_when_not_granted():
    spec = ToolSpec(name="gated", description="d", required_consent="mail_read")
    decision = ToolPolicyEvaluator.evaluate(
        _invocation(), _registry(spec), consent_gate=_DenyConsent()
    )
    assert decision.allowed is False
    assert decision.reason == "consent_required"


def test_consent_gate_allows_when_granted():
    spec = ToolSpec(name="gated", description="d", required_consent="mail_read")
    decision = ToolPolicyEvaluator.evaluate(
        _invocation(), _registry(spec), consent_gate=_AllowConsent()
    )
    assert decision.allowed is True


def test_no_consent_gate_leaves_consent_to_the_host():
    # Declaring a required_consent without supplying a gate does not deny here.
    spec = ToolSpec(name="gated", description="d", required_consent="mail_read")
    decision = ToolPolicyEvaluator.evaluate(_invocation(), _registry(spec))
    assert decision.allowed is True


def test_egress_gate_denies_a_data_egress_tool():
    spec = ToolSpec(name="gated", description="d", data_egress=True, provider="notion")
    decision = ToolPolicyEvaluator.evaluate(
        _invocation(), _registry(spec), egress_gate=_DenyEgress()
    )
    assert decision.allowed is False
    assert decision.reason == "egress_denied"


def test_egress_gate_ignored_for_non_egress_tool():
    spec = ToolSpec(name="gated", description="d", data_egress=False)
    decision = ToolPolicyEvaluator.evaluate(
        _invocation(), _registry(spec), egress_gate=_DenyEgress()
    )
    assert decision.allowed is True
