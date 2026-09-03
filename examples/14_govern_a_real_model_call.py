# examples/14_govern_a_real_model_call.py
"""Govern a real model's proposals: the fifteen-minute integration.

The pattern every host uses: the model (any provider) PROPOSES an
action, the host maps the proposal onto its OWN risk policy, and
ARVIS decides whether the act may happen. The model never holds the
pen on risk: a model-declared risk would be untrusted input, and the
kernel only lets a declared risk harden a verdict (F-001-a5).

Offline by default so this file runs in the smoke gate with no
network and no key: a deterministic canned model stands in. Run with
``--live`` and OPENAI_API_KEY or ANTHROPIC_API_KEY set to let a real
model produce the proposals; the governance path is byte-for-byte
the same, which is the point of the pattern.

The narrated walkthrough of this file is docs/FIRST_REAL_CALL.md.
"""

import os
import sys

from arvis import ArvisEngine, DecisionStatus

LIVE = "--live" in sys.argv

# ----------------------------------------------------------------- #
# 1. The host's own risk policy                                      #
# ----------------------------------------------------------------- #
# The host decides what each action class costs. This table is YOUR
# policy: the model proposes an action name, never its risk.
RISK_POLICY: dict[str, float] = {
    "read_report": 0.05,
    "email_summary": 0.50,
    "wire_transfer": 0.95,
}

EXPECTED_BAND = {
    "read_report": DecisionStatus.ALLOWED,
    "email_summary": DecisionStatus.REQUIRES_CONFIRMATION,
    "wire_transfer": DecisionStatus.BLOCKED,
}

PROMPT = (
    "You are an operations assistant. Reply with exactly one word, "
    "the next action to take, chosen from: read_report, "
    "email_summary, wire_transfer."
)


def canned_model(step: int) -> str:
    """Deterministic stand-in model: proposes each action once."""
    return ["read_report", "email_summary", "wire_transfer"][step % 3]


def live_model(step: int) -> str:
    """One real completion call, if a key is present. Any failure
    falls back to the canned model, loudly: governance must not
    depend on the model being reachable."""
    try:
        if os.environ.get("ANTHROPIC_API_KEY"):
            import anthropic

            client = anthropic.Anthropic()
            message = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=8,
                messages=[{"role": "user", "content": PROMPT}],
            )
            text = message.content[0].text
        elif os.environ.get("OPENAI_API_KEY"):
            import openai

            client = openai.OpenAI()
            completion = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": PROMPT}],
            )
            text = completion.choices[0].message.content or ""
        else:
            print("  (--live but no API key found; using the canned model)")
            return canned_model(step)
    except Exception as error:  # arvis-broad: example fallback, reported
        print(f"  (live call failed: {type(error).__name__}; canned model)")
        return canned_model(step)
    proposal = text.strip().split()[0].strip(".,")
    if proposal not in RISK_POLICY:
        print(f"  (model proposed {proposal!r}, outside the policy; canned)")
        return canned_model(step)
    return proposal


propose = live_model if LIVE else canned_model

print("\nARVIS Example 14: govern a real model's proposals")
print("=" * 60)
print("model:", "live" if LIVE else "canned (run with --live for a real one)")

# ----------------------------------------------------------------- #
# 2. Propose, map to YOUR risk, govern; one engine per turn          #
# ----------------------------------------------------------------- #
blocked_run = None
for step in range(3):
    action = propose(step)
    declared_risk = RISK_POLICY[action]
    engine = ArvisEngine()
    result = engine.run("ops", {"risk": declared_risk})
    print(
        f"\n[step {step + 1}] model proposes: {action}"
        f"\n  host risk policy : {declared_risk:.2f}"
        f"\n  verdict          : {result.status.value}"
    )
    # The verdict is a function of the governed risk, whatever the
    # model chose to propose: same bands offline and live.
    assert result.status is EXPECTED_BAND[action]
    if result.status is DecisionStatus.BLOCKED:
        blocked_run = result
        print("  effect           : none. The act never runs.")
    elif result.status is DecisionStatus.REQUIRES_CONFIRMATION:
        print("  effect           : held for a bound human validation.")
    else:
        print("  effect           : host may proceed with", action)

# ----------------------------------------------------------------- #
# 3. The incident, replayed                                          #
# ----------------------------------------------------------------- #
# The blocked wire_transfer is exactly the turn an auditor asks
# about. The host stored the commitment as its external anchor;
# replaying the exported IR against that anchor reproduces the
# decision bit for bit or raises.
assert blocked_run is not None, "the canned sequence always blocks once"
anchor = blocked_run.global_commitment
replayed = ArvisEngine().os.replay_verified(
    blocked_run.to_ir(), expected_global_commitment=anchor
)
print("\n[audit] the blocked step, replayed from its exported record")
print("  original commitment :", anchor[:16] + "...")
print("  replayed commitment :", replayed.global_commitment[:16] + "...")
print("  authenticated       : YES (against the stored anchor)")
assert replayed.global_commitment == anchor

print("\nTakeaway: bring your own model; keep your own risk policy;")
print("ARVIS decides per turn, blocks what your policy calls")
print("dangerous, and every decision replays for the auditor.")
