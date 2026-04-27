# examples/01_gate_refusal.py

from arvis import CognitiveOS

os = CognitiveOS()

result = os.run(
    user_id="demo",
    cognitive_input={
        "risk": 0.98,
        "action": "wire_transfer",
    },
)

data = result.to_dict()
decision = data["decision"]

blocked = "allowed=False" in decision
needs_confirm = "requires_user_validation=True" in decision

print("\nARVIS Example 01 — Safe Runtime Gate")
print("-" * 42)
print("Action        : wire_transfer")
print("Risk Score    : 0.98")
print("Status        :", "BLOCKED" if blocked else "ALLOWED")
print("Approval      :", "REQUIRED" if needs_confirm else "NO")
print("Audit Trace   :", "YES" if data["has_trace"] else "NO")
print("Timeline      :", "VERIFIED" if data["has_timeline"] else "NO")
print("Commitment    :", data["global_commitment"][:16] + "...")
print()
print("Takeaway      : High-risk actions are blocked before execution.")