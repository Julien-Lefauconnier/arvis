# examples/04_human_confirmation.py

from arvis import CognitiveOS

os = CognitiveOS()

# A medium declared risk (pure {"risk": x} payload) is graded by the
# governed policy and routed to human confirmation.
result = os.run(
    "user_1",
    {
        "risk": 0.55,
    },
)

data = result.to_dict()
decision = data["decision"]  # structured public block (a15): status + flags

needs_confirm = bool(decision["requires_user_validation"])
allowed = decision["status"] == "ALLOWED"

print("\nARVIS Example 04: Human Approval Gate")
print("-" * 44)
print("Declared Risk : 0.55")
print("Auto Execute  :", "YES" if allowed else "NO")
print("Approval Need :", "YES" if needs_confirm else "NO")
print("Trace         :", "AVAILABLE" if data["has_trace"] else "NO")
print("Timeline      :", "VERIFIED" if data["has_timeline"] else "NO")
print()
print("Takeaway      : Medium-risk decisions require human approval.")
