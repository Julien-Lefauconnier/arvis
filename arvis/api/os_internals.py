# arvis/api/os_internals.py

from __future__ import annotations

from typing import Any

from arvis.api.ir import build_ir_view
from arvis.api.runtime.cognitive_runtime import CognitiveRuntime
from arvis.api.views.cognitive_result_view import CognitiveResultView
from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.ir.cognitive_ir import CognitiveIR
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel.replay_engine import ReplayEngine
from arvis.tools.executor import ToolExecutor


class CognitiveOSInternals:
    config: Any
    pipeline: CognitivePipeline
    runtime: CognitiveRuntime
    tool_executor: ToolExecutor

    def _build_context(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> CognitivePipelineContext:
        return CognitivePipelineContext(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline or [],
            confirmation_result=confirmation_result,
            extra=extra if extra is not None else {},
        )

    def _execute(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> tuple[CognitiveState | None, Any]:
        execution = self.runtime.execute(
            self._build_context(
                user_id=user_id,
                cognitive_input=cognitive_input,
                conversation_context=conversation_context,
                timeline=timeline,
                confirmation_result=confirmation_result,
                extra=extra,
            )
        )
        return execution.state, execution.result

    def _build_runtime(self) -> CognitiveRuntime:
        return CognitiveRuntime(
            pipeline=self.pipeline,
            adapters=self.config.adapter_registry,
            tool_executor=self.tool_executor,
        )

    def _format_run_output(
        self,
        state: CognitiveState | None,
        result: Any,
    ) -> CognitiveResultView | dict[str, Any]:
        # legacy mode explicite
        if not self.config.enable_trace:
            return {
                "action": getattr(result, "action_decision", None),
                "can_execute": getattr(result, "can_execute", None),
            }

        # trace mode normal
        if state is not None:
            return self._build_trace_result(state, result)

        # fallback fake executors/tests
        return {
            "action": getattr(result, "action_decision", None),
            "can_execute": getattr(result, "can_execute", None),
        }

    def _run_single(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> CognitiveResultView | dict[str, Any]:
        state, result = self._execute(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )
        return self._format_run_output(state, result)

    def _run_batch(
        self,
        inputs: list[Any],
        *,
        user_id: str,
    ) -> list[CognitiveResultView | dict[str, Any]]:
        return [
            self._run_single(
                user_id=user_id,
                cognitive_input=cognitive_input,
            )
            for cognitive_input in inputs
        ]

    def _export_ir(
        self,
        state: CognitiveState,
    ) -> dict[str, Any]:
        return build_ir_view(state)

    def _build_ir_from_input(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state, _ = self._execute(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )
        return self._export_ir(
            self._require_state(
                state,
                message=(
                    "IR export requires a CognitiveState, but execution returned none."
                ),
            ),
        )

    def _replay_ir(
        self,
        ir: dict[str, Any],
    ) -> Any:
        parsed = CognitiveIR.from_dict(ir)
        engine = ReplayEngine()
        return engine.replay_ir(
            parsed,
            pipeline=self.pipeline,
        )

    def _replay_view(
        self,
        ir: dict[str, Any],
    ) -> CognitiveResultView:
        result = self._replay_ir(ir)
        state = getattr(result, "cognitive_state", None)

        typed_state = self._require_state(
            state,
            message="Replay result missing cognitive_state",
        )

        return CognitiveResultView.from_state(
            typed_state,
            result,
        )

    def _verify_replay_view(
        self,
        replay_view: CognitiveResultView,
        *,
        expected_global_commitment: str | None = None,
    ) -> CognitiveResultView:
        self._verify_replay_commitment(
            replay_view,
            expected_global_commitment,
        )
        return replay_view

    def _verified_replay_view(
        self,
        ir: dict[str, Any],
        *,
        expected_global_commitment: str | None = None,
    ) -> CognitiveResultView:
        return self._verify_replay_view(
            self._replay_view(ir),
            expected_global_commitment=expected_global_commitment,
        )

    def _verify_replay_commitment(
        self,
        replay_view: CognitiveResultView,
        expected_global_commitment: str | None,
    ) -> None:
        if expected_global_commitment is None:
            return

        replay_commitment = replay_view.global_commitment

        if replay_commitment is None:
            raise RuntimeError(
                "Replay verification failed: replay global_commitment is missing"
            )

        if replay_commitment != expected_global_commitment:
            raise RuntimeError(
                "Replay verification failed: global_commitment mismatch "
                f"(expected={expected_global_commitment}, "
                f"got={replay_commitment})"
            )

    def _build_trace_result(
        self,
        state: CognitiveState | None,
        result: Any,
    ) -> CognitiveResultView:
        typed_state = self._require_state(
            state,
            message=(
                "Trace mode requires a CognitiveState, but execution "
                "returned none. Use enable_trace=False for fake "
                "executors/tests, or ensure the pipeline builds "
                "ctx.cognitive_state."
            ),
        )

        return CognitiveResultView.from_state(
            typed_state,
            result,
        )

    def _require_state(
        self,
        state: CognitiveState | None,
        *,
        message: str = (
            "IR export requires a CognitiveState, but execution returned none."
        ),
    ) -> CognitiveState:
        if state is None:
            raise RuntimeError(message)
        return state
