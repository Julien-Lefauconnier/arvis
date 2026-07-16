# arvis/api/os.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.adapters.tools.gates import ConsentGate, EgressGate
from arvis.api.audit import AuditCommitmentPolicy
from arvis.api.os_internals import CognitiveOSInternals
from arvis.api.runtime_controls import TrustedRuntimeControls
from arvis.api.runtime_mode import RuntimeMode, coerce_runtime_mode
from arvis.api.views.cognitive_result_view import CognitiveResultView
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.stability.stability_snapshot import StabilitySnapshot
from arvis.telemetry.adapters.stability import stability_event
from arvis.telemetry.sink import NullTelemetrySink, TelemetrySink
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


# -----------------------------------------------------
# Runtime Configuration
# -----------------------------------------------------
# F-007: frozen so the construction-time validation cannot be bypassed
# by mutating the configuration after the runtime is built.
@dataclass(frozen=True, slots=True)
class CognitiveOSConfig:
    enable_trace: bool = True
    # Strict stability profile. When True, stability bootstrap
    # invariant violations raise instead of warning. Monotone with
    # the ARVIS_STRICT_STABILITY env var: either channel can enable
    # strict mode, neither can disable the other. Applies to the
    # pipeline built by CognitiveOS; an injected pipeline keeps its
    # own setting.
    strict_mode: bool = False
    adapter_registry: dict[str, Any] | None = None
    runtime_mode: RuntimeMode | str = RuntimeMode.LOCAL
    telemetry_sink: TelemetrySink | None = None
    core_model: Any | None = None
    # F-001: host-only controls injected by composition; never read
    # from request payloads or ctx.extra. Rejected in the production
    # runtime profile.
    runtime_controls: TrustedRuntimeControls | None = None
    # F-017/F-018: host-provided tool gates. In the PRODUCTION profile a
    # tool declaring required_consent or data_egress is denied when the
    # matching gate is missing (deny-by-default); other profiles leave
    # enforcement to the host (documented fail-open).
    consent_gate: ConsentGate | None = None
    egress_gate: EgressGate | None = None
    # F-015: how a missing audit commitment is handled. Set REQUIRED
    # for profiles where runs have effects: an unauditable run must
    # not pass.
    audit_commitment_policy: AuditCommitmentPolicy = AuditCommitmentPolicy.DEGRADED

    def __post_init__(self) -> None:
        # F-008: the runtime mode set is closed; unknown values are
        # refused instead of silently running with a permissive posture.
        object.__setattr__(self, "runtime_mode", coerce_runtime_mode(self.runtime_mode))
        # F-012: REQUIRED audit commitment needs the trace machinery.
        # With enable_trace=False no commitment can ever be produced, so
        # the combination is a configuration contradiction.
        if (
            not self.enable_trace
            and self.audit_commitment_policy is AuditCommitmentPolicy.REQUIRED
        ):
            raise ValueError(
                "audit_commitment_policy=REQUIRED requires enable_trace=True: "
                "without the trace no audit commitment can be produced"
            )

    @classmethod
    def production(cls, **overrides: Any) -> CognitiveOSConfig:
        """Closed production profile.

        Doctrine: deny-by-default is an attribute of the PRODUCTION
        profile, not of the library. The factory fixes
        runtime_mode=PRODUCTION and defaults the audit commitment
        policy to REQUIRED; every other field can be overridden.
        """
        if "runtime_mode" in overrides:
            raise ValueError(
                "CognitiveOSConfig.production() fixes runtime_mode; "
                "use CognitiveOSConfig(...) directly for other modes"
            )
        params: dict[str, Any] = {
            "audit_commitment_policy": AuditCommitmentPolicy.REQUIRED,
        }
        params.update(overrides)
        params["runtime_mode"] = RuntimeMode.PRODUCTION
        return cls(**params)


# -----------------------------------------------------
# Public Runtime Entrypoint
# -----------------------------------------------------
class CognitiveOS(CognitiveOSInternals):
    def __init__(
        self,
        config: CognitiveOSConfig | None = None,
        *,
        pipeline: CognitivePipeline | None = None,
    ):
        self.config = config or CognitiveOSConfig()
        if (
            self.config.runtime_controls is not None
            and self.config.runtime_mode is RuntimeMode.PRODUCTION
        ):
            raise ValueError(
                "TrustedRuntimeControls are not permitted in the "
                "production runtime profile"
            )
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry)
        self.pipeline = pipeline or CognitivePipeline(
            core_model=self.config.core_model,
            strict_mode=self.config.strict_mode,
        )
        self.telemetry_sink: TelemetrySink = (
            self.config.telemetry_sink
            if self.config.telemetry_sink is not None
            else NullTelemetrySink()
        )
        self.pipeline.telemetry_sink = self.telemetry_sink
        self.runtime = self._build_runtime()

    def _ensure_production_ready(self) -> None:
        """F-019: in the PRODUCTION profile the tool registry freezes
        automatically at the first run; late registration is then
        refused by the frozen registry itself."""
        if self.config.runtime_mode is not RuntimeMode.PRODUCTION:
            return
        if not self.tool_registry.frozen:
            self.tool_registry.freeze()

    # -------------------------------------------------
    # Tools API
    # -------------------------------------------------
    def register_tool(self, tool: Any) -> None:
        self.tool_registry.register(tool)

    def freeze_tools(self) -> str:
        """Freeze the tool registry after bootstrap (F-004).

        Returns the registry fingerprint for host-side pinning.
        """
        return self.tool_registry.freeze()

    def list_tools(self) -> list[str]:
        return self.tool_registry.list()

    def get_tool_spec(self, name: str) -> ToolSpec | None:
        return self.tool_registry.get_spec(name)

    def list_tool_specs(self) -> dict[str, ToolSpec]:
        return self.tool_registry.list_specs()

    # -------------------------------------------------
    # Core Execution
    # -------------------------------------------------
    def run(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> CognitiveResultView | dict[str, Any]:
        self._ensure_production_ready()
        result = self._run_single(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )
        return result

    def _emit_stability_telemetry(
        self,
        result: CognitiveResultView | dict[str, Any],
    ) -> None:
        """
        Emit a STABILITY telemetry event for a completed run.

        Observe-only and fail-safe: a misbehaving sink must never affect
        a cognitive run, and emission happens after the result (and its
        IR / commitment) are finalized, so it cannot influence
        determinism or replay. The default NullTelemetrySink makes this
        a no-op.
        """
        if isinstance(self.telemetry_sink, NullTelemetrySink):
            return
        if not isinstance(result, CognitiveResultView):
            return
        from arvis.cognition.core.cognitive_core_result import CognitiveCoreResult
        from arvis.telemetry.adapters.core import core_stability_event

        snapshot = result.stability
        if isinstance(snapshot, StabilitySnapshot):
            event = stability_event(snapshot)
        elif isinstance(snapshot, CognitiveCoreResult):
            event = core_stability_event(snapshot)
        else:
            return
        try:
            self.telemetry_sink.emit(event)
        except Exception:  # arvis-broad: observe-only telemetry sink
            return

    # -------------------------------------------------
    # IR Export
    # -------------------------------------------------
    def run_ir(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._ensure_production_ready()
        return self._build_ir_from_input(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

    # -------------------------------------------------
    # Replay
    # -------------------------------------------------
    def replay(
        self,
        ir: dict[str, Any],
        *,
        expected_global_commitment: str | None = None,
    ) -> CognitiveResultView:
        return self._verified_replay_view(
            ir,
            expected_global_commitment=expected_global_commitment,
        )

    def replay_verified(
        self,
        ir: dict[str, Any],
        *,
        expected_global_commitment: str | None = None,
    ) -> CognitiveResultView:
        return self.replay(
            ir,
            expected_global_commitment=expected_global_commitment,
        )

    # -------------------------------------------------
    # Inspection
    # -------------------------------------------------
    def inspect(self, result: CognitiveResultView) -> dict[str, Any]:
        return {
            "summary": result.summary(),
            "trace": result.trace_view.to_dict() if result.trace_view else None,
            "stability": (
                {
                    "score": result.stability_view.stability_score,
                    "risk": result.stability_view.risk_level,
                    "regime": result.stability_view.regime,
                }
                if result.stability_view
                else None
            ),
        }

    # -------------------------------------------------
    # Multi-run
    # -------------------------------------------------
    def run_multi(
        self,
        inputs: list[Any],
        *,
        user_id: str = "multi",
    ) -> list[CognitiveResultView | dict[str, Any]]:
        self._ensure_production_ready()
        return self._run_batch(
            inputs=inputs,
            user_id=user_id,
        )

    # -------------------------------------------------
    # Properties
    # -------------------------------------------------
    @property
    def version(self) -> str:
        from arvis.api.version import PACKAGE_VERSION

        return PACKAGE_VERSION
