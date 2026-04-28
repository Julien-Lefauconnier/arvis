# arvis/api/engine.py

from __future__ import annotations

from typing import Any, Optional, cast

from .os import CognitiveOS, CognitiveOSConfig
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline


class ArvisEngine:
    """
    Friendly public runtime wrapper for ARVIS.

    ArvisEngine is the recommended high-level entrypoint for most users.

    Example:
        from arvis import ArvisEngine

        engine = ArvisEngine()
        result = engine.ask("Analyze this situation")
    """

    def __init__(
        self,
        config: Optional[CognitiveOSConfig] = None,
        *,
        pipeline: Optional[CognitivePipeline] = None,
        **kwargs: Any,
    ) -> None:
        if config is None:
            config = CognitiveOSConfig(**kwargs)

        self._os = CognitiveOS(
            config=config,
            pipeline=pipeline,
        )

    # -------------------------------------------------
    # Representations
    # -------------------------------------------------
    def __repr__(self) -> str:
        return (
            "ArvisEngine("
            f"runtime_mode={self.config.runtime_mode!r}, "
            f"strict_mode={self.config.strict_mode!r})"
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
        return cast(CognitiveOSConfig, self._os.config)

    # -------------------------------------------------
    # Core Runtime
    # -------------------------------------------------
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute a cognitive request."""
        return self._os.run(*args, **kwargs)

    def ask(
        self,
        prompt: str,
        *,
        user_id: str = "default",
        **kwargs: Any,
    ) -> Any:
        """
        Convenience method for prompt-style requests.
        """
        return self._os.run(
            user_id=user_id,
            cognitive_input=prompt,
            **kwargs,
        )

    def run_multi(self, *args: Any, **kwargs: Any) -> Any:
        """Execute multiple requests."""
        return self._os.run_multi(*args, **kwargs)

    # -------------------------------------------------
    # IR / Replay
    # -------------------------------------------------
    def run_ir(self, *args: Any, **kwargs: Any) -> Any:
        """Execute and export canonical IR."""
        return self._os.run_ir(*args, **kwargs)

    def replay(self, *args: Any, **kwargs: Any) -> Any:
        """Replay an IR payload."""
        return self._os.replay(*args, **kwargs)

    # -------------------------------------------------
    # Inspection
    # -------------------------------------------------
    def inspect(self, *args: Any, **kwargs: Any) -> Any:
        """Inspect a CognitiveResultView."""
        return self._os.inspect(*args, **kwargs)

    # -------------------------------------------------
    # Tools
    # -------------------------------------------------
    def register_tool(self, tool: Any) -> None:
        """Register a tool."""
        self._os.register_tool(tool)

    def list_tools(self) -> list[str]:
        """List registered tools."""
        return self._os.list_tools()

    def get_tool_spec(self, name: str) -> Any:
        """Get tool specification."""
        return self._os.get_tool_spec(name)

    def list_tool_specs(self) -> Any:
        """List all tool specifications."""
        return self._os.list_tool_specs()
