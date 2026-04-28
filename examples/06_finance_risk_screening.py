# examples/06_finance_risk_screening.py

from arvis import CognitiveOS

os = CognitiveOS()

trade = {
    "desk": "FX_SPOT",
    "instrument": "EURUSD",
    "notional_usd": 500000,
    "market_volatility": 0.58,
    "risk": 0.62,
    "confidence": 0.74,
}

result = os.run("desk_a", trade)

data = result.to_dict()
decision = data["decision"]

allowed = "allowed=True" in decision
needs_confirm = "requires_user_validation=True" in decision

print("\nARVIS Example 06 — Finance Risk Screening")
print("-" * 46)
print("Desk          : FX_SPOT")
print("Instrument    : EURUSD")
print("Notional USD  : 500000")
print("Risk Score    : 0.62")
print("Confidence    : 0.74")
print("Decision      :", "APPROVED" if allowed else "REVIEW")
print("Escalation    :", "YES" if needs_confirm else "NO")
print("Audit Trace   :", "AVAILABLE" if data["has_trace"] else "NO")
print()
print("Takeaway      : Trades can be screened before execution.")
