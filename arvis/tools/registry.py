# arvis/tools/registry.py

from typing import Dict, List, Optional

from arvis.tools.base import BaseTool
from arvis.tools.spec import ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool  

    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found")
        return self._tools[name]

    def list(self) -> List[str]:
        return list(self._tools.keys())

    # -------------------------
    # SPEC API
    # -------------------------

    def get_spec(self, name: str) -> Optional[ToolSpec]:
        tool = self.get(name)
        return getattr(tool, "spec", None)

    def list_specs(self) -> Dict[str, ToolSpec]:
        specs: Dict[str, ToolSpec] = {}

        for name, tool in self._tools.items():
            spec = getattr(tool, "spec", None)
            if spec is not None:
                specs[name] = spec

        return specs