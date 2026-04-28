# examples/07_memory_governed_context.py

from arvis import CognitiveOS

os = CognitiveOS()

result = os.run(
    "user_42",
    {"query": "recommend next action"},
    conversation_context={
        "history": [
            "opened support ticket",
            "requested refund",
        ]
    },
)

data = result.to_dict()

print("\nARVIS Example 07 — Governed Memory Context")
print("-" * 46)
print("User ID       : user_42")
print("Memory Events : 2")
print("Query         : recommend next action")
print("Context Used  : YES")
print("Trace         :", "AVAILABLE" if data["has_trace"] else "NO")
print("Timeline      :", "VERIFIED" if data["has_timeline"] else "NO")
print()
print("Takeaway      : Prior context can guide decisions safely.")
