# compliance/core/test_yaml_scenarios.py

import pytest

from arvis.ir.gate import CognitiveGateVerdictIR
from compliance.helpers import run_ctx
from compliance.scenarios.builders import build_context_from_yaml
from compliance.scenarios.loader import load_scenario

SCENARIOS = [
    "validity_invalid",
    "projection_invalid",
    "kappa_violation",
    "nominal_local",
    "nominal_exponential",
]


@pytest.mark.parametrize("name", SCENARIOS)
def test_yaml_scenarios(name):
    scenario = load_scenario(name)

    ctx = build_context_from_yaml(scenario["input"])
    result = run_ctx(ctx)

    expected = scenario["expected"]

    # =====================================================
    # 🔎 DEBUG BLOCK (CRITICAL FOR DIAGNOSIS)
    # =====================================================
    print("\n==============================")
    print(f"[SCENARIO] {name}")
    print("==============================")

    print("\n--- GATE ---")
    print("verdict:", result.ir_gate.verdict)
    print("reason_codes:", getattr(result.ir_gate, "reason_codes", None))

    print("\n--- VALIDITY ---")
    print("validity:", result.ir_validity)

    print("\n--- PROJECTION ---")
    print("projection:", result.ir_projection)

    print("\n--- EXECUTION ---")
    print("requires_confirmation:", result.requires_confirmation)
    print("can_execute:", result.can_execute)

    print("\n--- RAW CONTEXT SIGNALS ---")
    print("extra:", ctx.extra)

    print("\n--- INTERNAL STATE ---")
    print("delta_w:", getattr(ctx, "delta_w", None))
    print("stable:", getattr(ctx, "stable", None))
    print("projection_domain_valid:", getattr(ctx, "projection_domain_valid", None))
    print("projection_margin:", getattr(ctx, "projection_margin", None))

    print("==============================\n")
    # =====================================================

    # -------------------------
    # Gate assertions (pure decision layer)
    # -------------------------
    if "gate" in expected:
        verdict = expected["gate"]["verdict"]

        if verdict == "ABSTAIN":
            assert result.ir_gate.verdict == CognitiveGateVerdictIR.ABSTAIN

        elif verdict == "not_allow":
            assert result.ir_gate.verdict != CognitiveGateVerdictIR.ALLOW

        elif verdict == "ALLOW":
            assert result.ir_gate.verdict == CognitiveGateVerdictIR.ALLOW

    # -------------------------
    # Validity assertions
    # -------------------------
    if "validity" in expected:
        assert result.ir_validity["valid"] == expected["validity"]["valid"]

    # -------------------------
    # Projection assertions
    # -------------------------
    if "projection" in expected:
        if "available" in expected["projection"]:
            assert (
                result.ir_projection["available"] == expected["projection"]["available"]
            )

    # -------------------------
    # Execution layer assertions
    # -------------------------
    if "execution" in expected:
        if "requires_confirmation" in expected["execution"]:
            assert (
                result.requires_confirmation
                == expected["execution"]["requires_confirmation"]
            )

    # -------------------------
    # Consistency checks (gate ↔ execution)
    # -------------------------
    if "gate" in expected:
        verdict = expected["gate"]["verdict"]

        # ALLOW => fully executable
        if verdict == "ALLOW":
            assert result.requires_confirmation is False
            assert result.can_execute is True

        # not_allow / ABSTAIN => not directly executable
        elif verdict in ("not_allow", "ABSTAIN"):
            assert result.can_execute is False
