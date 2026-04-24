# examples/03_stability_vs_llm.py

from arvis.api.cognitive_os import CognitiveOS

os = CognitiveOS()

input_data = {
    "numeric_signals": {
        "risk": 0.2,
        "instability": 0.3,
        "confidence": 0.99,  # suspiciously high
    },
    "projection": {
        "domain_valid": True,
        "boundedness_ok": True,
        "lipschitz_ok": True,
        "noise_robustness_ok": False,  # key trigger
        "mode_stability_ok": True,
        "lyapunov_compatibility_ok": True,
    },
}

result = os.run(input_data)

print("=== STABILITY CHECK ===")
print(result)