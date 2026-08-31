# arvis/reflexive/introspection/math_introspector.py

from typing import Any


class MathIntrospector:
    """Describes the mathematical stability layer, as it actually is.

    This is a hand-maintained declaration (``kind: static_declaration``),
    not a derivation from the code. Its previous version described a
    ``global_stability_monitor`` module that does not exist and implied
    the Lyapunov machinery drives the default decision path; it does not
    (audit A3 / M1, 2026-08). Every module named here exists, under its
    real import path, with an honest execution status:

    - ``default_path``: exercised by the default engine on a governed run;
    - ``host_driven``: present and tested, but only evaluated when the
      host supplies the required state (the default engine does not).
    """

    def describe(self) -> dict[str, Any]:
        return {
            "name": "stability_system",
            "kind": "static_declaration",
            "description": (
                "Threshold-based input-risk gating on the default path, "
                "with a composite Lyapunov energy layer that is evaluated "
                "only when a host supplies the Lyapunov state."
            ),
            "components": [
                {
                    "module": "arvis.kernel.gate.input_risk",
                    "role": (
                        "three-band grading of an explicit top-level risk "
                        "scalar (the decisive policy on the default path)"
                    ),
                    "status": "default_path",
                },
                {
                    "module": "arvis.math.gate.gate_kernel",
                    "role": (
                        "refusal-first pre-verdict: explicit instability, "
                        "collapse risk and CRITICAL mode refuse before any "
                        "acceptance path"
                    ),
                    "status": "default_path",
                },
                {
                    "module": "arvis.math.gate.gate_policy",
                    "role": (
                        "policy layer: strict veto, global instability "
                        "policy, bounded recovery relaxation"
                    ),
                    "status": "default_path",
                },
                {
                    "module": "arvis.math.switching.global_stability_observer",
                    "role": "switching/global stability observation",
                    "status": "default_path",
                },
                {
                    "module": "arvis.math.lyapunov.lyapunov",
                    "role": (
                        "constructive stability energy V(x) over "
                        "budget_used, risk, uncertainty, governance"
                    ),
                    "status": "host_driven",
                },
                {
                    "module": "arvis.math.lyapunov.lyapunov_gate",
                    "role": "local stability gating using delta-V bounds",
                    "status": "host_driven",
                },
                {
                    "module": "arvis.math.core.contraction_monitor_core",
                    "role": (
                        "builds the Lyapunov state from observations; "
                        "instantiated by hosts, not by the default engine"
                    ),
                    "status": "host_driven",
                },
                {
                    "module": "arvis.math.adaptive.adaptive_kappa_eff",
                    "role": "empirical contraction-factor estimation",
                    "status": "host_driven",
                },
            ],
        }
