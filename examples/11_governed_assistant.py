"""A minimal governed-assistant integration.

The example models two turns from the reference architecture:

1. search local knowledge (read-only, low declared risk);
2. send a digest externally (side effect, confirmation required).

It registers and freezes the tool surface, then exercises the public decision
contract. It deliberately performs no tool effect. Production effects must go
through the governed syscall path documented in
docs/architecture/EFFECT_PATH.md; calling ``tool.execute`` directly would
bypass the guarantee this example is meant to teach.
"""

from dataclasses import dataclass

from arvis import ArvisEngine, DecisionStatus
from arvis.host_api.tools import BaseTool, ToolSpec


class SearchKnowledgeTool(BaseTool):
    name = "search_knowledge"
    spec = ToolSpec(
        name="search_knowledge",
        description="Search documents already authorized by the host.",
        side_effectful=False,
        max_risk=0.3,
        data_class="personal",
    )

    def execute(self, input_data):
        return {"matches": []}


class SendDigestTool(BaseTool):
    name = "send_digest"
    spec = ToolSpec(
        name="send_digest",
        description="Send a prepared digest to an external recipient.",
        side_effectful=True,
        reversible=False,
        requires_confirmation=True,
        audit_required=True,
        provider="mail-provider",
        data_egress=True,
        data_class="personal",
        required_consent="mail.send",
    )

    def execute(self, input_data):
        return {"sent": True}


@dataclass(frozen=True)
class ProposedTurn:
    tool_name: str
    risk: float
    purpose: str


def build_engine() -> tuple[ArvisEngine, str]:
    """Host factory: one configured engine per governed turn."""
    engine = ArvisEngine()
    engine.register_tool(SearchKnowledgeTool())
    engine.register_tool(SendDigestTool())
    registry_fingerprint = engine.freeze_tools()
    return engine, registry_fingerprint


def govern(turn: ProposedTurn) -> tuple[DecisionStatus, str]:
    engine, registry_fingerprint = build_engine()
    if engine.get_tool_spec(turn.tool_name) is None:
        raise RuntimeError(f"unregistered tool: {turn.tool_name}")

    # This minimal example uses the documented explicit-risk input contract.
    # The selected tool and purpose remain host-side proposal data until the
    # full authorization boundary binds them to an invocation.
    result = engine.run("reference-user", {"risk": turn.risk})
    return result.status, registry_fingerprint


def main() -> None:
    turns = (
        ProposedTurn(
            tool_name="search_knowledge",
            risk=0.10,
            purpose="Find an authorized document",
        ),
        ProposedTurn(
            tool_name="send_digest",
            risk=0.50,
            purpose="Send its summary outside the trust boundary",
        ),
    )

    print("\nARVIS Example 11: Governed Assistant")
    print("-" * 46)
    for turn in turns:
        status, fingerprint = govern(turn)
        next_step = {
            DecisionStatus.ALLOWED: "eligible for governed authorization",
            DecisionStatus.REQUIRES_CONFIRMATION: "wait for bound user confirmation",
            DecisionStatus.BLOCKED: "stop; no effect",
            DecisionStatus.NONE: "stop; no decision",
        }[status]
        print(f"{turn.tool_name:17s} {status.value:22s} {next_step}")
        print(f"{'':17s} registry={fingerprint[:12]}... purpose={turn.purpose}")

    print()
    print("No tool was executed directly.")
    print("Takeaway: model proposals become effects only through ARVIS governance.")


if __name__ == "__main__":
    main()
