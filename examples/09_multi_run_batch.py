# examples/09_multi_run_batch.py

from arvis import CognitiveOS

os = CognitiveOS()

# Each request is a pure declared-risk payload, graded by the governed
# three-band policy (F-001-a5: mixed payloads are harden-only).
request_ids = ["REQ-001", "REQ-002", "REQ-003"]
payloads = [
    {"risk": 0.10},
    {"risk": 0.50},
    {"risk": 0.90},
]

results = os.run_multi(
    payloads,
    user_id="batch_engine",
)

approved = 0
review = 0
blocked = 0

rows = []

for i, r in enumerate(results, start=1):
    data = r.to_dict()
    decision = data["decision"]

    allowed = "allowed=True" in decision
    needs_confirm = "requires_user_validation=True" in decision

    if allowed and not needs_confirm:
        status = "APPROVED"
        approved += 1
    elif needs_confirm:
        status = "REVIEW"
        review += 1
    else:
        status = "BLOCKED"
        blocked += 1

    rows.append(
        (
            i,
            request_ids[i - 1],
            payloads[i - 1]["risk"],
            status,
            r.global_commitment[:10] + "...",
        )
    )

print("\nARVIS Example 09 — Batch Decision Engine")
print("-" * 46)

for row in rows:
    idx, req, risk, status, commit = row
    print(f"{idx}. {req:<8} Risk={risk:<4} {status:<9} {commit}")

print()
print("Approved     :", approved)
print("Review Queue :", review)
print("Blocked      :", blocked)
print("Traceability : PER ITEM")
print()
print("Takeaway      : Large decision flows can be screened consistently.")
