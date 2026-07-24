# arvis/api/engine.py

from __future__ import annotations

from typing import Any

from arvis.api.views.cognitive_result_view import CognitiveResultView
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.tools.base import BaseTool
from arvis.tools.spec import ToolSpec

from .os import CognitiveOS, CognitiveOSConfig


class ArvisEngine:
    """
    Friendly public runtime wrapper for ARVIS.

    ArvisEngine is the recommended high-level entrypoint for most users.
    Its surface is part of the beta contract: every method carries an
    explicit signature, and run-shaped methods return a single public
    type, CognitiveResultView.

    The input channels (``cognitive_input``, ``conversation_context``,
    ``timeline``, ``confirmation_result``, ``extra``) are host injection
    channels and deliberately typed ``Any``: their shape belongs to the
    host integration, not to this facade.

    Example:
        from arvis import ArvisEngine

        engine = ArvisEngine()
        result = engine.ask("Analyze this situation")
    """

    def __init__(
        self,
        config: CognitiveOSConfig | None = None,
        *,
        pipeline: CognitivePipeline | None = None,
        **kwargs: Any,
    ) -> None:
        """Build an engine.

        ``kwargs`` is a convenience channel: when ``config`` is None,
        keyword arguments are forwarded to ``CognitiveOSConfig`` (for
        example ``ArvisEngine(strict_mode=True)``). With an explicit
        ``config``, no extra keyword arguments are accepted.
        """
        if config is None:
            config = CognitiveOSConfig(**kwargs)
        elif kwargs:
            raise TypeError(
                "ArvisEngine: pass either an explicit config or keyword "
                "arguments for CognitiveOSConfig, not both"
            )

        self._os = CognitiveOS(
            config=config,
            pipeline=pipeline,
        )

    # -------------------------------------------------
    # Representations
    # -------------------------------------------------
    def __repr__(self) -> str:
        cfg = self.config
        return (
            "ArvisEngine("
            f"runtime_mode={cfg.runtime_mode!r}, "
            f"strict_mode={cfg.strict_mode!r})"
        )

    # -------------------------------------------------
    # Properties
    # -------------------------------------------------
    @property
    def os(self) -> CognitiveOS:
        """Low-level CognitiveOS instance."""
        return self._os

    @property
    def config(self) -> CognitiveOSConfig:
        """Runtime configuration."""
        return self._os.config

    @property
    def version(self) -> str:
        """ARVIS package version."""
        return self._os.version

    # -------------------------------------------------
    # Core Runtime
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
    ) -> CognitiveResultView:
        """Execute a cognitive request."""
        return self._os.run(
            user_id,
            cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

    def ask(
        self,
        prompt: str,
        *,
        user_id: str = "default",
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> CognitiveResultView:
        """
        Convenience method for prompt-style requests.
        """
        return self._os.run(
            user_id=user_id,
            cognitive_input=prompt,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

    # -------------------------------------------------
    # IR / Replay
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
        """Execute and export canonical IR."""
        return self._os.run_ir(
            user_id,
            cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

    def replay_verified(
        self,
        ir: dict[str, Any],
        *,
        expected_global_commitment: str,
    ) -> CognitiveResultView:
        """Replay and authenticate an IR against an external commitment."""
        return self._os.replay_verified(
            ir,
            expected_global_commitment=expected_global_commitment,
        )

    def replay_recomposed(
        self,
        ir: dict[str, Any],
    ) -> CognitiveResultView:
        """Recompose an IR without authenticating it."""
        return self._os.replay_recomposed(ir)

    # -------------------------------------------------
    # Inspection
    # -------------------------------------------------
    def inspect(self, result: CognitiveResultView) -> dict[str, Any]:
        """Inspect a CognitiveResultView."""
        return self._os.inspect(result)

    # -------------------------------------------------
    # Tools
    # -------------------------------------------------
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._os.register_tool(tool)

    def freeze_tools(self) -> str:
        """Freeze the tool registry after bootstrap (F-004)."""
        return self._os.freeze_tools()

    def list_tools(self) -> list[str]:
        """List registered tools."""
        return self._os.list_tools()

    def get_tool_spec(self, name: str) -> ToolSpec | None:
        """Get tool specification."""
        return self._os.get_tool_spec(name)

    def list_tool_specs(self) -> dict[str, ToolSpec]:
        """List all tool specifications."""
        return self._os.list_tool_specs()
