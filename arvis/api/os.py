# arvis/api/os.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from arvis.api.os_internals import CognitiveOSInternals
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.api.views.cognitive_result_view import CognitiveResultView
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


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


# =====================================================
# COGNITIVE OS (REFactored)
# =====================================================

class CognitiveOS(CognitiveOSInternals):
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

        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry)
        self.pipeline = pipeline or CognitivePipeline()
        self.runtime = self._build_runtime()

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
        return self._run_single(
            user_id,
            cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

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
        return self._build_ir_from_input(
            user_id,
            cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

    # =====================================================
    #  REPLAY API
    # =====================================================

    def replay(
        self,
        ir: Dict[str, Any],
        *,
        expected_global_commitment: Optional[str] = None,
    ) -> CognitiveResultView:
        return self._verified_replay_view(
            ir,
            expected_global_commitment=expected_global_commitment,
        )

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
        return self._run_batch(
            inputs,
            user_id=user_id,
        )
