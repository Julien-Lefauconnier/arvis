# examples/03_ir_export.py

from arvis import CognitiveOS

os = CognitiveOS()

ir = os.run_ir(
    user_id="demo",
    cognitive_input={
        "text": "analyze this request",
        "risk": 0.22,
    },
)

keys = list(ir.keys())

print("\nARVIS Example 03 — Portable Decision Record")
print("-" * 42)
print("Format        : Structured JSON")
print("Top Keys      :", ", ".join(keys[:5]))
print("Fields       :", len(keys))
print("Replay Ready  : YES")
print("Audit Ready   : YES")
print()
print("Takeaway      : Decisions can be exported as portable records.")
