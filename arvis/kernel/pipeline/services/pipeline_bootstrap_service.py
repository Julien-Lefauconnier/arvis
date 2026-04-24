# arvis/kernel/pipeline/services/pipeline_bootstrap_service.py
from __future__ import annotations

import os
import warnings
from typing import Any, TYPE_CHECKING, cast

from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov

from arvis.cognition.decision.decision_evaluator import (
    DecisionEvaluator,
)
from arvis.cognition.bundle.cognitive_bundle_builder import (
    CognitiveBundleBuilder,
)
from arvis.cognition.core.cognitive_core_engine import (
    CognitiveCoreEngine,
)
from arvis.cognition.control.mode_hysteresis import (
    ModeHysteresis,
)
from arvis.cognition.control.exploration_controller import (
    ExplorationController,
)
from arvis.cognition.control.regime_policy import (
    CognitiveRegimePolicy,
)
from arvis.cognition.control.cognitive_control_runtime import (
    CognitiveControlRuntime,
)
from arvis.math.stability.regime_estimator import (
    CognitiveRegimeEstimator,
)
from arvis.math.control.irg_epsilon_controller import (
    IRGEpsilonController,
)
from arvis.math.control.eps_adaptive import (
    EpsAdaptiveParams,
)
from arvis.cognition.control.temporal_pressure import (
    TemporalPressure,
)
from arvis.cognition.control.temporal_regulation import (
    TemporalRegulation,
)
from arvis.action.action_policy import ActionPolicy
from arvis.cognition.conflict.conflict_evaluator import (
    ConflictEvaluator,
)
from arvis.cognition.conflict.default_rules import (
    default_conflict_rules,
)
from arvis.cognition.observability.observability_builder import (
    ObservabilityBuilder,
)
from arvis.cognition.conflict.conflict_pressure_engine import (
    ConflictPressureEngine,
)
from arvis.cognition.coherence.coherence_policy import (
    CoherencePolicy,
)
from arvis.cognition.coherence.coherence_observer import (
    CoherenceObserver,
)

from arvis.math.switching.global_stability_observer import (
    GlobalStabilityObserver,
)
from arvis.math.lyapunov.quadratic_lyapunov import (
    make_default_quadratic_family,
)
from arvis.math.adaptive.adaptive_kappa_eff import (
    AdaptiveKappaEffEstimator,
)

from arvis.kernel.projection.domain import (
    ProjectionDomain,
    NumericBounds,
)
from arvis.kernel.projection.validator import (
    ProjectionValidator,
)
from arvis.kernel.projection.pi_impl import PiImpl
from arvis.math.projection.pi_operator import PiOperator

from arvis.kernel.pipeline.stages import (
    ToolFeedbackStage,
    ToolRetryStage,
    DecisionStage,
    PassiveContextStage,
    BundleStage,
    ConflictStage,
    CoreStage,
    RegimeStage,
    TemporalStage,
    ConflictModulationStage,
    ControlStage,
    ProjectionStage,
    GateStage,
    ControlFeedbackStage,
    StructuralRiskStage,
    ConfirmationStage,
    ExecutionStage,
    ActionStage,
    IntentStage,
    RuntimeStage,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
    )


class PipelineBootstrapService:
    @staticmethod
    def run(
        pipeline: "CognitivePipeline",
        core_model: Any | None,
    ) -> None:
        strict_mode = (
            os.getenv(
                "ARVIS_STRICT_STABILITY",
                "false",
            ).lower()
            == "true"
        )

        comp = CompositeLyapunov()

        if not comp.check_small_gain(
            eta=0.05,
            alpha=0.3,
            L_T=1.0,
        ):
            msg = (
                "Potentially unstable system configuration: "
                "small-gain not satisfied"
                "(adjust eta, alpha or L_T)"
            )
            if strict_mode:
                raise RuntimeError(msg)
            warnings.warn(msg, RuntimeWarning)

        pipeline.decision = DecisionEvaluator()
        pipeline.bundle_builder = CognitiveBundleBuilder()
        pipeline.core = CognitiveCoreEngine(
            core_model=core_model
        )

        pipeline.hysteresis = ModeHysteresis()
        pipeline.exploration = ExplorationController()
        pipeline.regime_policy = (
            CognitiveRegimePolicy()
        )
        pipeline.regime_estimator = (
            CognitiveRegimeEstimator()
        )

        pipeline.epsilon_controller = (
            IRGEpsilonController(
                adaptive_params=EpsAdaptiveParams(
                    enabled=True
                )
            )
        )

        pipeline.temporal_pressure = (
            TemporalPressure()
        )
        pipeline.temporal_regulation = (
            TemporalRegulation()
        )
        pipeline.action_policy = ActionPolicy()

        pipeline.conflict_evaluator = (
            ConflictEvaluator(
                rules=default_conflict_rules()
            )
        )

        pipeline.observability = (
            ObservabilityBuilder()
        )
        pipeline.conflict_pressure_engine = (
            ConflictPressureEngine()
        )
        pipeline.coherence_observer = (
            CoherenceObserver()
        )
        pipeline.coherence_policy = (
            CoherencePolicy()
        )

        pipeline.control_runtimes = cast(
            dict[str, CognitiveControlRuntime],
            {},
        )

        pipeline.tool_feedback_stage = (
            ToolFeedbackStage()
        )
        pipeline.tool_retry_stage = (
            ToolRetryStage()
        )
        pipeline.decision_stage = DecisionStage()
        pipeline.passive_stage = (
            PassiveContextStage()
        )
        pipeline.bundle_stage = BundleStage()
        pipeline.conflict_stage = (
            ConflictStage()
        )
        pipeline.core_stage = CoreStage()
        pipeline.regime_stage = RegimeStage()
        pipeline.temporal_stage = (
            TemporalStage()
        )
        pipeline.conflict_modulation_stage = (
            ConflictModulationStage()
        )
        pipeline.control_stage = (
            ControlStage()
        )
        pipeline.projection_stage = (
            ProjectionStage()
        )
        pipeline.gate_stage = GateStage()
        pipeline.control_feedback_stage = (
            ControlFeedbackStage()
        )
        pipeline.structural_risk_stage = (
            StructuralRiskStage()
        )
        pipeline.confirmation_stage = (
            ConfirmationStage()
        )
        pipeline.execution_stage = (
            ExecutionStage()
        )
        pipeline.action_stage = ActionStage()
        pipeline.intent_stage = IntentStage()
        pipeline.runtime_stage = RuntimeStage()

        pipeline.global_stability_observer = (
            GlobalStabilityObserver()
        )

        pipeline.quadratic_lyapunov_family = (
            make_default_quadratic_family(
                dim=4
            )
        )

        pipeline.quadratic_comparability = (
            pipeline.quadratic_lyapunov_family
            .comparability()
        )

        pipeline.tool_executor = None

        pipeline.adaptive_kappa_estimator = (
            AdaptiveKappaEffEstimator()
        )

        pipeline.pi_impl = PiImpl()
        pipeline.pi_operator = PiOperator()

        pipeline.projection_domain = (
            ProjectionDomain(
                bounds={
                    "state.system_tension":
                    NumericBounds(
                        0.0, 100.0
                    ),
                    "state.coherence_score":
                    NumericBounds(
                        0.0, 1.0
                    ),
                    "risk.conflict_pressure":
                    NumericBounds(
                        0.0, 100.0
                    ),
                    "control.control_signal":
                    NumericBounds(
                        0.0, 100.0
                    ),
                    "trace.adaptive_kappa_eff":
                    NumericBounds(
                        0.0, 1.0
                    ),
                },
                max_payload_size=10000,
            )
        )

        pipeline.projection_validator = (
            ProjectionValidator(
                pipeline.projection_domain
            )
        )