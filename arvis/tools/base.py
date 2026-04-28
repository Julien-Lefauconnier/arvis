# arvis/tools/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict

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

    def validate(self, input_data: Dict[str, Any]) -> None:
        """
        Optional validation hook.
        Raise Exception if invalid.
        """
        return None

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Any:
        pass
