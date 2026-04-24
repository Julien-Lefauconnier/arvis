# examples/01_basic_gate_refusal.py

from arvis.api.cognitive_os import CognitiveOS

os = CognitiveOS()

input_data = {
    "numeric_signals": {
        "risk": 0.05,
        "instability": 0.4,
        "confidence": 0.95,
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

result = os.run(input_data)

print("=== ARVIS RESULT ===")
print(result)