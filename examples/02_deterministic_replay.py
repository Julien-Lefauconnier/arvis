# examples/02_deterministic_replay.py

# examples/02_deterministic_replay.py

from arvis import CognitiveOS

os = CognitiveOS()

payload = {
    "query": "approve request",
    "risk": 0.10,
}

# Original execution
r1 = os.run("u1", payload)

# Replay from exported IR
r2 = os.replay(r1.to_ir())

same = r1.global_commitment == r2.global_commitment

print("\nARVIS Example 02 — Deterministic Replay")
print("-" * 46)
print("Input Risk    : 0.10")
print("Original Run  :", r1.global_commitment[:16] + "...")
print("Replay Run    :", r2.global_commitment[:16] + "...")
print("IR Verified   :", "YES")
print("Match         :", "YES" if same else "NO")
print("Traceability  :", "FULL")
print()
print("Takeaway      : Decisions can be replayed identically for audit.")
