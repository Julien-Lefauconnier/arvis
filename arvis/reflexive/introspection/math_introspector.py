# arvis/reflexive/introspection/math_introspector.py

from typing import Any


class MathIntrospector:
    """Describes the mathematical stability layer, as it actually is.

    This is a hand-maintained declaration (``kind: static_declaration``),
    not a derivation from the code. Its previous version described a
    ``global_stability_monitor`` module that does not exist, and at the
    time of the audit the Lyapunov machinery did not drive the default
    decision path at all (audit A3 / M1, 2026-08; wired by campaign
    MATH-A). Every module named here exists, under its real import
    path, with an honest execution status:

    - ``default_path``: exercised by the default engine on a governed run
      (since MATH-A M1 the contraction monitor is the default core
      model, so the Lyapunov measurement chain is engine-driven; the
      trajectory branch needs host-threaded ``scientific_state``);
    - ``host_driven``: present and tested, but only evaluated when the
      host supplies the required state.
    """

    def describe(self) -> dict[str, Any]:
        return {
            "name": "stability_system",
            "kind": "static_declaration",
            "description": (
                "Measured Lyapunov energy, PAC risk ceiling and regime "
                "on every governed run (default contraction monitor), "
                "with threshold-based gating of caller-declared risk; "
                "the delta-V trajectory branch runs on threaded turns."
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
                    "status": "default_path",
                },
                {
                    "module": "arvis.math.lyapunov.lyapunov_gate",
                    "role": (
                        "local stability gating using delta-V bounds; "
                        "live from the second turn when the host "
                        "threads scientific_state"
                    ),
                    "status": "default_path",
                },
                {
                    "module": "arvis.math.core.contraction_monitor_core",
                    "role": (
                        "builds the Lyapunov state, energy, PAC risk "
                        "ceiling and regime from observations; the "
                        "default core model since MATH-A M1"
                    ),
                    "status": "default_path",
                },
                {
                    "module": "arvis.math.adaptive.adaptive_kappa_eff",
                    "role": "empirical contraction-factor estimation",
                    "status": "host_driven",
                },
            ],
        }
