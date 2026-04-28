# examples/09_multi_run_batch.py

from arvis import CognitiveOS

os = CognitiveOS()

payloads = [
    {"request_id": "REQ-001", "risk": 0.10},
    {"request_id": "REQ-002", "risk": 0.50},
    {"request_id": "REQ-003", "risk": 0.90},
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
            payloads[i - 1]["request_id"],
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
