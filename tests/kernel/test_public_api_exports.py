# tests/kernel/test_public_api_exports.py

import arvis


def test_public_api_has_expected_symbols():

    expected = {
        "CognitiveBundleSnapshot",
        "CognitiveBundleBuilder",
        "CognitiveState",
        "MemoryIntent",
        "MemoryGate",
        "MemoryLongSnapshot",
        "MemoryLongType",
        "ReasoningIntent",
        "ReasoningIntentType",
        "UncertaintyAxis",
        "UncertaintyFrame",
        "UncertaintyFrameRegistry",
        "LyapunovState",
        "LyapunovWeights",
        "lyapunov_value",
        "lyapunov_delta",
        "clamp",
        "clamp01",
        "normalize_weights",
        "HoeffdingRiskBound",
        "RiskBoundSnapshot",
        "ChangeBudget",
        "ControlInertia",
        "StabilityObserver",
        "StabilitySnapshot",
    }

    exported = set(getattr(arvis, "__all__", []))

    missing = expected - exported

    assert not missing, f"Missing public exports: {sorted(missing)}"