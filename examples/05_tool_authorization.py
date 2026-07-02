# examples/05_tool_authorization.py

from arvis import CognitiveOS
from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.tools.base import BaseTool
from arvis.tools.spec import ToolSpec


class ReadStatusTool(BaseTool):
    """A low-risk, read-only tool.

    Its spec caps the acceptable risk at 0.5, so a low-risk request is
    authorized while a high-risk one is denied by policy.
    """

    name = "read_status"
    spec = ToolSpec(
        name="read_status",
        description="Read a service status (read-only, no side effects).",
        side_effectful=False,
        max_risk=0.5,
    )

    def execute(self, input_data):
        return {"status": "ok"}


os = CognitiveOS()
os.register_tool(ReadStatusTool())
registry = os.tool_registry


def authorize(tool_name: str, risk: float):
    invocation = ToolInvocation(
        tool_name=tool_name,
        payload={},
        process_id="demo",
        risk_score=risk,
    )
    return ToolPolicyEvaluator.evaluate(invocation, registry)


def label(decision) -> str:
    return "AUTHORIZED" if decision.allowed else f"DENIED ({decision.reason})"


# Registered read-only tool, low risk -> within spec budget -> authorized.
low = authorize("read_status", 0.10)
# Same tool, but the request risk exceeds the tool's max_risk -> denied.
high = authorize("read_status", 0.90)
# A tool that was never registered -> denied.
unknown = authorize("delete_all", 0.10)

print("\nARVIS Example 05 — Tool Governance")
print("-" * 40)
print("Registered Tools :", os.list_tools())
print()
print("read_status @ risk 0.10 :", label(low))
print("read_status @ risk 0.90 :", label(high))
print("delete_all  @ risk 0.10 :", label(unknown))
print()
print("Takeaway      : Per-spec tool governance blocks over-budget/unknown tools.")
