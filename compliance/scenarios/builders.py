# compliance/scenarios/builders.py

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel.projection.certificate import (
    ProjectionCertificate,
    ProjectionCertificationLevel,
)
from arvis.math.gate.gate_adapter import ensure_lyapunov_state
from tests.fixtures.projection_cases import (
    high_risk_case,
    invalid_case,
    nominal_case,
)


def _ctx(obs):
    return CognitivePipelineContext(
        user_id="test-user",
        cognitive_input={
            "numeric_signals": obs.numeric_signals,
            "structured_signals": obs.structured_signals,
            "external_signals": obs.external_signals,
        },
    )


def build_nominal_context():
    return _ctx(nominal_case())


def build_projection_invalid_context():
    return _ctx(invalid_case())


def build_kappa_violation_context():
    return _ctx(high_risk_case())


def build_validity_invalid_context():
    return _ctx(invalid_case())


def build_context_from_yaml(data):
    ctx = CognitivePipelineContext(
        user_id="test_user",
        cognitive_input={
            "numeric_signals": data.get("numeric_signals", {}),
            "structured_signals": data.get("structured_signals", {}),
            "external_signals": data.get("external_signals", {}),
        },
    )

    # -----------------------------------------
    # Lyapunov
    # -----------------------------------------
    lyap = data.get("lyapunov")
    if lyap:
        prev = lyap.get("prev")
        cur = lyap.get("current")

        # Use the canonical gate adapter so the injected type matches
        # what GateStage / CompositeLyapunov expect.
        ctx.prev_lyap = ensure_lyapunov_state(float(prev)) if prev is not None else None
        ctx.cur_lyap = ensure_lyapunov_state(float(cur)) if cur is not None else None

        # Helpful hint for the rest of the pipeline / observability
        if prev is not None and cur is not None:
            ctx.stable = float(cur) < float(prev)
            ctx.extra["preserve_injected_lyapunov"] = True

    # -----------------------------------------
    # Projection
    # -----------------------------------------
    proj = data.get("projection")
    if proj:
        level_raw = str(proj.get("certification_level", "NONE")).upper()

        try:
            level = ProjectionCertificationLevel[level_raw]
        except KeyError:
            level = ProjectionCertificationLevel.NONE

        ctx.projection_certificate = ProjectionCertificate(
            domain_valid=bool(proj.get("domain_valid", True)),
            boundedness_ok=bool(proj.get("boundedness_ok", True)),
            lipschitz_ok=bool(proj.get("lipschitz_ok", True)),
            noise_robustness_ok=bool(proj.get("noise_robustness_ok", True)),
            mode_stability_ok=bool(proj.get("mode_stability_ok", True)),
            lyapunov_compatibility_ok=bool(proj.get("lyapunov_compatibility_ok", True)),
            margin_to_boundary=float(proj.get("margin_to_boundary", 1.0)),
            local_lipschitz_estimate=float(proj.get("local_lipschitz_estimate", 1.0)),
            noise_gain_estimate=float(proj.get("noise_gain_estimate", 0.0)),
            certification_level=level,
            checks_detail=proj.get("checks_detail", {}),
        )

    # -----------------------------------------
    # Switching
    # -----------------------------------------
    switching = data.get("switching")
    if switching:

        class DummyRuntime:
            def dwell_time(self):
                return float(switching.get("tau_d", 1.0))

        ctx.switching_runtime = DummyRuntime()
    # -----------------------------------------
    # Optional test overrides
    # -----------------------------------------
    if data.get("force_safe_switching", False):
        ctx.extra["force_safe_switching"] = True

    if data.get("force_safe_projection", False):
        ctx.extra["force_safe_projection"] = True

    return ctx
