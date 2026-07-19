# examples/05_tool_authorization.py

from arvis import CognitiveOS
from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.tools.base import BaseTool
from arvis.tools.effect_context import AuthorizedEffectContext
from arvis.tools.spec import ToolSpec


class ReadStatusTool(BaseTool):
    """A low-risk, read-only, sovereign tool.

    It declares no provider, so it stays within the local trust boundary. Its
    spec caps the acceptable risk at 0.5, so a low-risk request is authorized
    while a high-risk one is denied by policy.
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


class PublishNoteTool(BaseTool):
    """A connected tool that sends data to a third party.

    Its manifest declares the provider, that it egresses the caller's data, the
    data sensitivity, the consent it needs and that the effect is irreversible.
    A host reads this manifest to govern sovereignty, egress and consent the
    same way for a local tool or an external (e.g. MCP) one.
    """

    name = "publish_note"
    spec = ToolSpec(
        name="publish_note",
        description="Publish a note to an external workspace.",
        side_effectful=True,
        reversible=False,
        provider="notion",
        data_egress=True,
        data_class="personal",
        required_consent="notion_access",
    )

    def execute(self, input_data):
        return {"published": True}


os = CognitiveOS()
os.register_tool(ReadStatusTool())
os.register_tool(PublishNoteTool())
registry = os.tool_registry


def authorize(tool_name: str, risk: float):
    invocation = ToolInvocation(
        tool_name=tool_name,
        payload={},
        effect_context=AuthorizedEffectContext(
            principal="example-user",
            tenant=None,
            authentication_source="example",
            authentication_strength="unattested",
            service_id=None,
            session_id_hash=None,
            process_id="demo",
            run_id=None,
        ),
        risk_score=risk,
    )
    return ToolPolicyEvaluator.evaluate(invocation, registry)


def label(decision) -> str:
    return "AUTHORIZED" if decision.allowed else f"DENIED ({decision.reason})"


def sovereignty(spec) -> str:
    if not spec.crosses_trust_boundary:
        return "sovereign (no third party)"
    flow = "egress" if spec.data_egress else "inbound read"
    return f"connected to {spec.provider} ({flow}, data: {spec.data_class})"


# Registered read-only tool, low risk -> within spec budget -> authorized.
low = authorize("read_status", 0.10)
# Same tool, but the request risk exceeds the tool's max_risk -> denied.
high = authorize("read_status", 0.90)
# A tool that was never registered -> denied.
unknown = authorize("delete_all", 0.10)

print("\nARVIS Example 05 - Tool Governance")
print("-" * 40)
print("Registered Tools :", os.list_tools())
print()
print("read_status @ risk 0.10 :", label(low))
print("read_status @ risk 0.90 :", label(high))
print("delete_all  @ risk 0.10 :", label(unknown))
print()
print("Capability manifest (sovereignty / egress / consent):")
for tool_name in ("read_status", "publish_note"):
    tool_spec = registry.get_spec(tool_name)
    if tool_spec is not None:
        consent = tool_spec.required_consent or "none"
        print(f"  {tool_name:13s}: {sovereignty(tool_spec)}; consent: {consent}")
print()
print("Takeaway      : Per-spec governance blocks over-budget/unknown tools,")
print("                and the manifest declares sovereignty, egress, consent.")
