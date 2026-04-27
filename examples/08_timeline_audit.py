# examples/08_timeline_audit.py

from arvis import CognitiveOS

os = CognitiveOS()

result = os.run(
    "auditor",
    {
        "action": "approve_document",
        "risk": 0.18,
    },
)

data = result.to_dict()
timeline = data.get("timeline", {})
entries = timeline.get("total_entries", 0)

state = "ACTIVE" if data["has_timeline"] else "OFF"

print("\nARVIS Example 08 — Timeline Audit Trail")
print("-" * 44)
print("Action        : approve_document")
print("Risk Score    : 0.18")
print("Commitment    :", result.global_commitment[:16] + "...")
print("Timeline      :", state)
print("Entries       :", entries if entries > 0 else "READY")
print("Trace         :", "AVAILABLE" if data["has_trace"] else "NO")
print()
print("Takeaway      : Decisions can be anchored to an audit trail.")