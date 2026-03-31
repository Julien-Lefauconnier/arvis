# arvis/reflexive/introspection/math_introspector.py

from typing import Dict, Any
class MathIntrospector:
    """
    Explains the mathematical stability layer of ARVIS.
    """

    def describe(self)-> Dict[str, Any]:

        return {
            "name": "stability_system",
            "description": (
                "ARVIS uses a multi-layer stability system combining "
                "Lyapunov analysis, predictive stability observers, "
                "trajectory monitoring and probabilistic risk estimation."
            ),
            "components": [
                {
                    "module": "lyapunov",
                    "role": "constructive stability energy function V(x)",
                    "signals": [
                        "budget_used",
                        "risk",
                        "uncertainty",
                        "governance",
                    ],
                },
                {
                    "module": "lyapunov_gate",
                    "role": "local stability gating using ΔV bounds",
                },
                {
                    "module": "predictive_stability",
                    "role": "short-horizon slope estimation and risk prediction",
                },
                {
                    "module": "global_stability",
                    "role": "multi-signal stability fusion",
                },
                {
                    "module": "global_stability_monitor",
                    "role": "empirical monitoring using running statistics",
                },
            ],
        }