# arvis/api/os.py

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, Optional, Callable, cast, List
import json
from hashlib import sha256


from arvis.reflexive.snapshot.reflexive_snapshot import ReflexiveSnapshot
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext

from arvis.api.stability import StabilityView
from arvis.api.trace import DecisionTraceView
from arvis.api.timeline import TimelineView
from arvis.api.version import API_VERSION, API_FINGERPRINT
from arvis.api.ir import build_ir_view
from arvis.adapters.kernel.timeline_from_signals import signal_journal_to_timeline_snapshot
from veramem_kernel.signals.signal_journal import SignalJournal
from arvis.kernel.replay_engine import ReplayEngine
from arvis.ir.cognitive_ir import CognitiveIR
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec
from arvis.cognition.state.cognitive_state import CognitiveState

from arvis.runtime import (
    CognitiveRuntimeState,
    CognitiveScheduler,
    PipelineExecutor,
)
from arvis.runtime.process_hooks import ProcessHookManager
from arvis.kernel_core.process import (
    CognitiveBudget,
    CognitivePriority,
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
)
from arvis.kernel_core.process.process_factory import ProcessFactory

from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler


# =====================================================
# CONFIG
# =====================================================

@dataclass
class CognitiveOSConfig:
    enable_trace: bool = True
    strict_mode: bool = False

    # OS-level extensions
    adapter_registry: Optional[Dict[str, Any]] = None
    runtime_mode: str = "local"  # local | replay | distributed

@dataclass(frozen=True)
class RuntimeExecutionResult:
    result: Any
    state: Optional[CognitiveState]

# =====================================================
# RUNTIME
# =====================================================

class CognitiveRuntime:
    """
    Runtime layer for CognitiveOS.

    Responsible for:
    - executing pipeline
    - hosting adapters
    - future scheduling / multi-agent
    """

    def __init__(
        self,
        pipeline: CognitivePipeline,
        adapters: Optional[Dict[str, Any]] = None,
        tool_executor: Optional[Any] = None,
    ):
        self.pipeline = pipeline
        self.adapters = adapters or {}
        self.tool_executor = tool_executor
        self.runtime_state = CognitiveRuntimeState()

        self.hooks = ProcessHookManager(runtime_state=self.runtime_state)

        self.process_executor = PipelineExecutor(self.pipeline)

        self.scheduler = CognitiveScheduler(
            runtime_state=self.runtime_state,
            process_executor=self.process_executor,
            hooks=self.hooks,
        )

        self.syscall_handler = SyscallHandler(
            runtime_state=self.runtime_state,
            scheduler=self.scheduler,
            tool_executor=self.tool_executor,
        )

    def execute(self, ctx: CognitivePipelineContext) -> Any:
        if self.adapters:
            ctx.extra["adapters"] = self.adapters

        # -----------------------------------------
        # CREATE PROCESS
        # -----------------------------------------
        process = ProcessFactory.create(
            process_id=CognitiveProcessId(
                f"proc::{ctx.user_id}::{len(self.runtime_state.processes)}"
            ),
            kind=CognitiveProcessKind.USER_REQUEST,
            status=CognitiveProcessStatus.READY,
            priority=CognitivePriority(50.0),
            budget=CognitiveBudget(
                reasoning_steps=2 * len(list(self.pipeline.iter_stages())),
                time_slice_ms=100,
            ),
            created_tick=self.runtime_state.scheduler_state.tick_count,
            user_id=ctx.user_id,
            local_state=ctx,
        )

        # -----------------------------------------
        # ENQUEUE
        # -----------------------------------------
        self.scheduler.enqueue(process)

        # -----------------------------------------
        # EXECUTION LOOP (until completion)
        # -----------------------------------------
        result = None

        for _ in range(100):  # safety guard
            decision = self.scheduler.tick()

            selected_id = decision.selected_process_id

            if selected_id is None:
                break

            proc = self.runtime_state.get_process(selected_id)

            # -----------------------------------------
            # TERMINAL STATE → source of truth
            # -----------------------------------------
            if proc.status == CognitiveProcessStatus.COMPLETED:
                result = proc.last_result
                break

            if proc.status == CognitiveProcessStatus.ABORTED:
                error = proc.last_error or "unknown_error"
                raise RuntimeError(f"Process aborted: {error}")

            if proc.status == CognitiveProcessStatus.WAITING_CONFIRMATION:
                result = proc.last_result
                break

            if decision.result is not None:
                result = decision.result
                break

            if proc.last_result is not None:
                result = proc.last_result
                break

        if result is None:
            raise RuntimeError("Execution did not produce any result")

        # -------------------------------------------------
        # TOOL EXECUTION
        # -------------------------------------------------
        action = getattr(result, "action_decision", None)
        effective_result = result

        # -------------------------------------------------
        # FORCE EXECUTION (TEST / DEBUG MODE)
        # -------------------------------------------------
        force_tool = ctx.extra.get("force_tool")
        force_execution = ctx.extra.get("_force_execution", False)

        if action and force_tool and action.tool == force_tool and force_execution:
            forced_action = SimpleNamespace(**dict(action.__dict__))
            forced_action.allowed = True
            forced_action.requires_confirmation = False
            forced_action.can_execute = True

            effective_result = SimpleNamespace(**dict(result.__dict__))
            effective_result.action_decision = forced_action

            action = forced_action

        if action and getattr(action, "tool", None) and getattr(action, "allowed", False):
            syscall_result = self.syscall_handler.handle(
                Syscall(
                    name="tool.execute",
                    args={
                        "result": effective_result,
                        "ctx": ctx,
                    },
                )
            )
            if not syscall_result.success:
                ctx.extra.setdefault("errors", []).append("tool_execution_failure")

        return RuntimeExecutionResult(
            result=result,
            state=ctx.cognitive_state,
        )


# =====================================================
# RESULT VIEW (UNCHANGED CORE)
# =====================================================

@dataclass(frozen=True)
class CognitiveResultView:
    decision: Any
    stability: Any
    stability_view: Optional[StabilityView]
    trace: Any
    trace_view: Optional[DecisionTraceView] = None
    timeline: Optional[Any] = None
    timeline_view: Optional[TimelineView] = None
    timeline_commitment: Optional[str] = None
    global_commitment: Optional[str] = None
    _ir: Optional[Dict[str, Any]] = None
    reflexive: Optional[Dict[str, Any]] = None

    @staticmethod
    def from_state(state: CognitiveState, result: Any) -> "CognitiveResultView":
        stability = getattr(result, "stability", None)
        trace = getattr(result, "trace", None)
        timeline_journal = state.timeline
        
        ir_payload = build_ir_view(state)

        try:
            ir_bytes = json.dumps(
                ir_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")

            ir_hash = sha256(ir_bytes).hexdigest()
        except Exception:
            ir_hash = None
        

        # -----------------------------------------
        #  SAFE TIMELINE HANDLING
        # -----------------------------------------
        if not isinstance(timeline_journal, SignalJournal):
            timeline_snapshot = None
            timeline_commitment = None
        else:
            timeline_snapshot = signal_journal_to_timeline_snapshot(timeline_journal)
            try:
                from veramem_kernel.journals.timeline.timeline_commitment import (
                    TimelineCommitment,
                )

                commitment = TimelineCommitment.from_snapshot(timeline_snapshot)
                timeline_commitment = commitment.commitment
            except Exception:
                # safety fallback (never crash API)
                timeline_commitment = None
        
        # -----------------------------------------
        # GLOBAL COMMITMENT (timeline + IR)
        # -----------------------------------------
        if timeline_commitment and ir_hash:
            try:
                global_commitment = sha256(
                    (timeline_commitment + ir_hash).encode("utf-8")
                ).hexdigest()
            except Exception:
                global_commitment = None
        else:
            global_commitment = None
        

        # reflexive snapshot (safe)
        reflexive_payload = None
        try:
            from arvis.api.reflexive import get_reflexive_snapshot

            typed_get_snapshot = cast(
                Callable[[Any], ReflexiveSnapshot],
                get_reflexive_snapshot,
            )

            snapshot = typed_get_snapshot(state)
            reflexive_payload = snapshot.to_dict()

        except Exception:
            reflexive_payload = None

        return CognitiveResultView(
            decision=getattr(result, "action_decision", None),
            stability=stability,
            stability_view=(
                StabilityView.from_snapshot(stability) if stability else None
            ),
            trace=trace,
            trace_view=DecisionTraceView.from_trace(trace) if trace else None,
            timeline=timeline_snapshot,
            timeline_view=(
                TimelineView.from_snapshot(timeline_snapshot)
                if timeline_snapshot is not None
                else None
            ),
            timeline_commitment=timeline_commitment,
            global_commitment=global_commitment,
            _ir=ir_payload,
            reflexive=reflexive_payload,
        )

    # -------------------------
    # SERIALIZATION
    # -------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": API_VERSION,
            "fingerprint": API_FINGERPRINT,
            "decision": str(self.decision),
            "stability": {
                "score": self.stability_view.stability_score
                if self.stability_view else None,
                "risk": self.stability_view.risk_level
                if self.stability_view else None,
                "regime": self.stability_view.regime
                if self.stability_view else None,
            },
            "has_trace": self.trace is not None,
            "has_timeline": self.timeline is not None,
            "timeline_commitment": self.timeline_commitment,
            "global_commitment": self.global_commitment,
            "trace": self.trace_view.to_dict() if self.trace_view else None,
            "timeline": self.timeline_view.to_dict() if self.timeline_view else None,
        }

    def to_ir(self) -> Optional[Dict[str, Any]]:
        return self._ir

    def summary(self) -> str:
        if not self.stability_view:
            return "No stability data"

        return (
            f"Decision={self.decision} | "
            f"Stability={self.stability_view.stability_score:.2f} | "
            f"Risk={self.stability_view.risk_level:.2f} | "
            f"Regime={self.stability_view.regime}"
        )


# =====================================================
# COGNITIVE OS (REFactored)
# =====================================================

class CognitiveOS:
    """
    Public entrypoint for ARVIS Cognitive OS.

    Now upgraded to:
    - runtime-enabled
    - adapter-ready
    - replay-capable
    - multi-agent-ready
    """

    def __init__(
        self,
        config: Optional[CognitiveOSConfig] = None,
        *,
        pipeline: Optional[CognitivePipeline] = None,
    ):
        self.config = config or CognitiveOSConfig()

        # -------------------------------------------------
        # TOOLS 
        # -------------------------------------------------
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry)

        # pipeline injection
        self.pipeline = pipeline or CognitivePipeline()

        # runtime layer 
        self.runtime = CognitiveRuntime(
            pipeline=self.pipeline,
            adapters=self.config.adapter_registry,
            tool_executor=self.tool_executor,
        )

    # =====================================================
    # TOOLS API
    # =====================================================

    def register_tool(self, tool: Any) -> None:
        self.tool_registry.register(tool)

    def list_tools(self) -> list[str]:
        return self.tool_registry.list()
    
    def get_tool_spec(self, name: str) -> Optional[ToolSpec]:
        return self.tool_registry.get_spec(name)

    def list_tool_specs(self) -> Dict[str, ToolSpec]:
        return self.tool_registry.list_specs()

    # =====================================================
    # CORE EXECUTION
    # =====================================================

    def run(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Any:

        ctx = self._build_context(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

        execution = self.runtime.execute(ctx)
        state = execution.state
        result = execution.result

        if self.config.enable_trace:
            if state is None:
                raise RuntimeError(
                    "Trace mode requires a CognitiveState, but execution returned none. "
                    "Use enable_trace=False for fake executors/tests, or ensure the pipeline "
                    "builds ctx.cognitive_state."
                )

        if self.config.enable_trace:
            return CognitiveResultView.from_state(
                state,
                result
            )

        return {
            "action": getattr(result, "action_decision", None),
            "can_execute": getattr(result, "can_execute", None),
        }

    # =====================================================
    # IR API
    # =====================================================

    def run_ir(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        ctx = self._build_context(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

        execution = self.runtime.execute(ctx)
        if execution.state is None:
            raise RuntimeError(
                "IR export requires a CognitiveState, but execution returned none."
            )
        return build_ir_view(execution.state)

    # =====================================================
    #  REPLAY API
    # =====================================================

    def replay(
        self,
        ir: Dict[str, Any],
        *,
        expected_global_commitment: Optional[str] = None,
    ) -> CognitiveResultView:

        parsed = CognitiveIR.from_dict(ir)
        engine = ReplayEngine()
        result = engine.replay_ir(parsed, pipeline=self.pipeline)
        state = getattr(result, "cognitive_state", None)

        if state is None:
            raise RuntimeError("Replay result missing cognitive_state")

        replay_view = CognitiveResultView.from_state(
            state,
            result
        )

        # -------------------------------------------------
        # VERIFIED REPLAY (optional)
        # -------------------------------------------------
        if expected_global_commitment is not None:
            replay_commitment = replay_view.global_commitment

            if replay_commitment is None:
                raise RuntimeError(
                    "Replay verification failed: replay global_commitment is missing"
                )

            if replay_commitment != expected_global_commitment:
                raise RuntimeError(
                    "Replay verification failed: global_commitment mismatch "
                    f"(expected={expected_global_commitment}, got={replay_commitment})"
                )

        return replay_view

    def replay_verified(
        self,
        ir: Dict[str, Any],
        *,
        expected_global_commitment: Optional[str] = None,
        ) -> CognitiveResultView:

        return self.replay(
            ir,
            expected_global_commitment=expected_global_commitment,
        )

    # =====================================================
    #  INSPECT
    # =====================================================

    def inspect(self, result: CognitiveResultView) -> Dict[str, Any]:
        return {
            "summary": result.summary(),
            "stability": (
                {
                    "score": result.stability_view.stability_score,
                    "risk": result.stability_view.risk_level,
                    "regime": result.stability_view.regime,
                }
                if result.stability_view else None
            ),
            "trace": (
                result.trace_view.to_dict()
                if result.trace_view else None
            ),
        }

    # =====================================================
    #  MULTI AGENT (V1)
    # =====================================================

    def run_multi(
        self,
        inputs: List[Any],
        *,
        user_id: str = "multi",
    ) -> List[CognitiveResultView]:

        results = []
        for inp in inputs:
            result = self.run(user_id=user_id, cognitive_input=inp)
            results.append(result)

        return results

    # =====================================================
    # INTERNAL
    # =====================================================

    def _build_context(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> CognitivePipelineContext:

        ctx = CognitivePipelineContext(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline or [],
            confirmation_result=confirmation_result,
            extra=extra if extra is not None else {}
        )

        return ctx