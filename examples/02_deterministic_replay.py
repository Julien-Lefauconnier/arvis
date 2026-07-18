# examples/02_deterministic_replay.py

from arvis import CognitiveOS

os = CognitiveOS()

# A payload exclusively dedicated to a declared risk scalar is graded by
# the governed three-band policy (F-001-a5: any other content makes the
# declared risk harden-only).
payload = {
    "risk": 0.10,
}

# Original execution.
r1 = os.run("u1", payload)

# The global commitment of the original run is the anchor a host records
# in durable storage (a signed record, an append-only journal). Replay
# authentication checks the recomposed run against THAT external anchor,
# not against the commitment the IR carries about itself: replaying an
# IR and trusting its own commitment proves nothing.
external_anchor = r1.global_commitment

# Authenticated replay from the exported IR against the external anchor.
# A mismatch (a forged IR, a divergent environment) would raise; a clean
# return means the decision recomposed identically to the recorded one.
r2 = os.replay_verified(r1.to_ir(), expected_global_commitment=external_anchor)

same = r1.global_commitment == r2.global_commitment

print("\nARVIS Example 02 — Authenticated Deterministic Replay")
print("-" * 52)
print("Input Risk    : 0.10")
print("Original Run  :", r1.global_commitment[:16] + "...")
print("Replay Run    :", r2.global_commitment[:16] + "...")
print("Authenticated : YES (against external anchor)")
print("Match         :", "YES" if same else "NO")
print("Traceability  :", "FULL")
print()
print("Takeaway      : Decisions replay identically and are")
print("                authenticated against a durable external anchor.")
