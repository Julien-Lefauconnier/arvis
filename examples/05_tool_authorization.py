# examples/05_tool_authorization.py

from arvis import CognitiveOS

os = CognitiveOS()

tools = os.list_tools()

result = os.run(
    "ops",
    {
        "tool": "email_sender",
        "action": "send_email",
        "risk": 0.15,
    },
)

data = result.to_dict()
decision = data["decision"]

allowed = "allowed=True" in decision

print("\nARVIS Example 05 — Tool Governance")
print("-" * 40)
print("Requested Tool:", "email_sender")
print("Action        :", "send_email")
print("Risk Score    : 0.15")
print("Execution     :", "AUTHORIZED" if allowed else "DENIED")
print("Registry Size :", len(tools))
print("Trace         :", "AVAILABLE" if data["has_trace"] else "NO")
print()
print("Takeaway      : Tools require explicit authorization before execution.")
