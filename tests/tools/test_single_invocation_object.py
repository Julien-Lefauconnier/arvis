# tests/tools/test_single_invocation_object.py
"""Single invocation object from authorization to the tool (P1-5-a6).

The executor receives the SAME `ToolInvocation` the policy evaluated:
identity, tenant, real turn risk, consent, audit and idempotency fields
travel to the tool without reconstruction. The deprecated
The a7 execute_authorized bypass is removed (D-7).
"""

from types import SimpleNamespace

import pytest

from arvis.errors.tool_runtime import ToolAuthorizationError
from arvis.kernel_core.access.models import Principal
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec
from tests.support.tool_execution import run_tool_for_tests


class _CapturingTool(BaseTool):
    name = "capture_tool"
    spec = ToolSpec(name="capture_tool", description="probe")

    def __init__(self) -> None:
        self.seen: list = []

    def execute_invocation(self, invocation):
        self.seen.append(invocation)
        return {"ok": True}

    def execute(self, input_data):  # pragma: no cover - invocation path used
        raise AssertionError("legacy path must not be used")


def _run_through_manager(ctx):
    registry = ToolRegistry()
    tool = _CapturingTool()
    registry.register(tool)
    manager = ToolManager(registry, ToolExecutor(registry))
    decision = SimpleNamespace(tool="capture_tool", tool_payload={"q": 1})
    result = SimpleNamespace(action_decision=decision)
    outcome = run_tool_for_tests(manager, result, ctx)
    return tool, outcome


def test_authorized_tool_receives_same_invocation_object():
    ctx = SimpleNamespace(extra={"input_risk": 0.4}, user_id="u1")
    tool, outcome = _run_through_manager(ctx)
    assert outcome is not None and outcome.success is True
    assert len(tool.seen) == 1
    invocation = tool.seen[0]
    # The enriched fields built by the manager reached the tool: this
    # object cannot be a bare reconstruction.
    assert invocation.user_id == "u1"
    assert invocation.risk_score == 0.4
    assert invocation.tool_name == "capture_tool"
    assert invocation.payload == {"q": 1}


def test_tool_receives_principal_tenant_and_risk():
    ctx = SimpleNamespace(
        extra={"input_risk": 0.3},
        user_id="u1",
        principal=Principal(user_id="u1", organization_id="org-7"),
    )
    tool, _ = _run_through_manager(ctx)
    invocation = tool.seen[0]
    assert invocation.principal == "u1"
    assert invocation.tenant == "org-7"
    assert invocation.risk_score == 0.3
    assert invocation.consent_granted == ()


def test_execute_authorized_bypass_path_is_removed():
    # D-7: the a7 execute_authorized rebuild-and-run bypass is gone.
    # There is no method that rebuilds an invocation and executes it
    # outside the manager's minted capability.
    executor = ToolExecutor(ToolRegistry())
    assert not hasattr(executor, "execute_authorized")


def test_direct_execution_stays_forbidden():
    executor = ToolExecutor(ToolRegistry())
    with pytest.raises(ToolAuthorizationError, match="forbidden"):
        executor.execute("capture_tool", {"q": 1})
