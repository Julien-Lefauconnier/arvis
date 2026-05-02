# arvis/tools/base.py

from abc import ABC, abstractmethod
from typing import Any

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.tools.spec import ToolSpec


class BaseTool(ABC):
    """
    input_data contains:
    - decision
    - context
    """

    # legacy support (optional)
    name: str = "base"
    description: str = ""

    # new spec (preferred)
    spec: ToolSpec | None = None

    @property
    def tool_name(self) -> str:
        if self.spec:
            return self.spec.name
        return self.name

    def validate(self, input_data: dict[str, Any]) -> None:
        """
        Optional validation hook.
        Raise Exception if invalid.
        """
        return None

    @abstractmethod
    def execute(self, input_data: dict[str, Any]) -> Any:
        pass

    # -----------------------------
    # API (optional)
    # -----------------------------

    def execute_invocation(self, invocation: ToolInvocation) -> Any:
        """
        New structured execution path.
        Default fallback to legacy.
        """
        return self.execute(
            {
                "tool_payload": invocation.payload,
                "invocation": invocation,
                "context": getattr(invocation, "context", None),  # 👈 FIX
            }
        )
