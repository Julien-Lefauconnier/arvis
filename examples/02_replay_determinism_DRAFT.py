# examples/02_replay_determinism.py

from arvis.api.cognitive_os import CognitiveOS

os = CognitiveOS()

input_data = {
    "numeric_signals": {
        "risk": 0.1,
        "instability": 0.05,
        "confidence": 0.9,
    },
    "projection": {
        "domain_valid": True,
        "boundedness_ok": True,
        "lipschitz_ok": True,
        "noise_robustness_ok": True,
        "mode_stability_ok": True,
        "lyapunov_compatibility_ok": True,
    },
}

result1 = os.run(input_data)
result2 = os.run(input_data)

print("Run 1:", result1)
print("Run 2:", result2)

assert result1 == result2

print("✅ Deterministic behavior confirmed")