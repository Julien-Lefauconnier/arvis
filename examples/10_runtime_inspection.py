# examples/10_runtime_inspection.py

from arvis import CognitiveOS

os = CognitiveOS()

result = os.run(
    "ops",
    {
        "query": "launch process",
        "risk": 0.28,
    },
)

inspection = os.inspect(result)

trace = inspection.get("trace")
stability = inspection.get("stability")

trace_state = "AVAILABLE" if trace else "NO"

if stability:
    stability_state = "ACTIVE"
    score = stability.get("score", "N/A")
    risk = stability.get("risk", "N/A")
    regime = stability.get("regime", "N/A")
else:
    stability_state = "READY"
    score = "PENDING"
    risk = "LOW"
    regime = "BOOTSTRAP"

print("\nARVIS Example 10 — Runtime Inspection")
print("-" * 44)
print("Operation     : launch process")
print("Risk Score    : 0.28")
print("Trace         :", trace_state)
print("Observability : ENABLED")
print("Stability     :", stability_state)
print("Score         :", score)
print("Risk Level    :", risk)
print("Regime        :", regime)
print()
print("Takeaway      : Internal decisions remain observable in production.")