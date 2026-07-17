# arvis/api/os_internals.py

from __future__ import annotations

from typing import Any

from arvis.api.audit import AuditCommitmentPolicy
from arvis.api.commitment import (
    config_fingerprint,
    policies_fingerprint,
    syscall_journal_digest,
)
from arvis.api.ir import build_ir_view
from arvis.api.runtime.cognitive_runtime import CognitiveRuntime
from arvis.api.runtime_mode import RuntimeMode
from arvis.api.views.cognitive_result_view import CognitiveResultView
from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.ir.cognitive_ir import CognitiveIR
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
    apply_runtime_postures,
)
from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.replay_engine import ReplayEngine
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry


class CognitiveOSInternals:
    config: Any
    pipeline: CognitivePipeline
    runtime: CognitiveRuntime
    tool_executor: ToolExecutor
    tool_registry: ToolRegistry

    @staticmethod
    def _result_execution(result: Any) -> Any:
        return getattr(result, "execution", result)

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
        ctx = CognitivePipelineContext(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline or [],
            confirmation_result=confirmation_result,
            extra=extra if extra is not None else {},
        )

        runtime_policy = ctx.runtime_policy

        # F-001: host controls come from composition (config), never
        # from the request-facing extra channel.
        controls = getattr(self.config, "runtime_controls", None)
        if controls is not None:
            runtime_policy.force_tool = controls.force_tool
            runtime_policy.force_execution = controls.force_execution
            ctx.gate_overrides = GateOverrides(
                force_safe_projection=controls.force_safe_projection,
                force_safe_switching=controls.force_safe_switching,
            )
        # Postures are applied through the shared helper so the replay
        # context builder reproduces the exact same block from the
        # recorded profile (D-a; single source of truth).
        apply_runtime_postures(ctx, self.config.runtime_mode.value)

        runtime_policy.retry_requested = bool(ctx.extra.get("retry_tool", False))
        runtime_policy.retry_count = int(ctx.extra.get("tool_retry_count", 0) or 0)

        return ctx

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
            # One registry: the runtime and its tool manager govern the
            # same tool surface the host registered on (previously the
            # runtime built its own empty registry and the policy was
            # evaluated against it).
            tool_registry=self.tool_registry,
            consent_gate=self.config.consent_gate,
            egress_gate=self.config.egress_gate,
            # F-017/F-018: deny-by-default gates in the PRODUCTION profile.
            require_gates=self.config.runtime_mode is RuntimeMode.PRODUCTION,
            audit_intent_sink=self.config.audit_intent_sink,
        )

    def _format_run_output(
        self,
        state: CognitiveState | None,
        result: Any,
    ) -> CognitiveResultView | dict[str, Any]:
        # legacy mode explicite
        if not self.config.enable_trace:
            execution = self._result_execution(result)
            return {
                "action": getattr(result, "action_decision", None),
                "can_execute": getattr(execution, "can_execute", None),
            }

        # trace mode normal
        if state is not None:
            return self._build_trace_result(state, result)

        # fallback fake executors/tests
        execution = self._result_execution(result)
        return {
            "action": getattr(result, "action_decision", None),
            "can_execute": getattr(execution, "can_execute", None),
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
        state, result = self._execute(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )
        exported = self._export_ir(
            self._require_state(
                state,
                message=(
                    "IR export requires a CognitiveState, but execution returned none."
                ),
            ),
        )
        # D-a: run_ir carries the same commitment_inputs block as the
        # result view export (public contract: run_ir == to_ir).
        inputs = self._build_commitment_inputs(result)
        if inputs is not None and isinstance(exported, dict):
            exported = {**exported, "commitment_inputs": inputs}
        return exported

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

        # D-a: on replay the non-cognitive components are reused
        # verbatim from the exported IR, never recomputed from the
        # replayer's environment. A divergent environment stays
        # detectable by comparing the declared block to the local one.
        declared = ir.get("commitment_inputs")
        return CognitiveResultView.from_state(
            typed_state,
            result,
            commitment_policy=self._commitment_policy(),
            commitment_inputs=declared if isinstance(declared, dict) else None,
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
            commitment_policy=self._commitment_policy(),
            commitment_inputs=self._build_commitment_inputs(result),
        )

    def _build_commitment_inputs(self, result: Any) -> dict[str, Any] | None:
        """Non-cognitive commitment components, from the live environment.

        F-007-a5: registry manifest fingerprint, effective config
        fingerprint, active policy tables, and the digest of the
        redacted syscall journals (intents and results). Returns None
        when a component cannot be produced: the commitment machinery
        then records the absence (REQUIRED refuses, DEGRADED flags),
        never a partially bound commitment.
        """
        try:
            execution = getattr(result, "execution", result)
            execution_state = getattr(execution, "execution_state", None)
            intents = getattr(execution_state, "syscall_intents", None)
            results = getattr(execution_state, "syscall_results", None)
            return {
                "registry_fingerprint": self.tool_registry.fingerprint(),
                "config_fingerprint": config_fingerprint(self.config),
                "policies_fingerprint": policies_fingerprint(),
                "syscall_journal_sha256": syscall_journal_digest(intents, results),
            }
        except Exception:  # arvis-broad: commitment absence is governed
            return None

    def _commitment_policy(self) -> AuditCommitmentPolicy:
        policy = getattr(self.config, "audit_commitment_policy", None)
        if isinstance(policy, AuditCommitmentPolicy):
            return policy
        return AuditCommitmentPolicy.DEGRADED

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
