# arvis/api/os.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.api.os_internals import CognitiveOSInternals
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
@dataclass(slots=True)
class CognitiveOSConfig:
    enable_trace: bool = True
    strict_mode: bool = False
    adapter_registry: dict[str, Any] | None = None
    runtime_mode: str = "local"
    telemetry_sink: TelemetrySink | None = None
    core_model: Any | None = None


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
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry)
        self.pipeline = pipeline or CognitivePipeline(core_model=self.config.core_model)
        self.telemetry_sink: TelemetrySink = (
            self.config.telemetry_sink
            if self.config.telemetry_sink is not None
            else NullTelemetrySink()
        )
        self.pipeline.telemetry_sink = self.telemetry_sink
        self.runtime = self._build_runtime()

    # -------------------------------------------------
    # Tools API
    # -------------------------------------------------
    def register_tool(self, tool: Any) -> None:
        self.tool_registry.register(tool)

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
        except Exception:
            # Telemetry is observe-only; never propagate sink failures.
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
