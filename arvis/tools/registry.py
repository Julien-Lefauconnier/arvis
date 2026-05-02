# arvis/tools/registry.py


from arvis.tools.base import BaseTool
from arvis.tools.spec import ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list(self) -> list[str]:
        return list(self._tools.keys())

    # -------------------------
    # SPEC API
    # -------------------------

    def get_spec(self, name: str) -> ToolSpec | None:
        tool = self.get(name)
        if tool is None:
            return None
        return getattr(tool, "spec", None)

    def list_specs(self) -> dict[str, ToolSpec]:
        specs: dict[str, ToolSpec] = {}

        for name, tool in self._tools.items():
            spec = getattr(tool, "spec", None)
            if spec is not None:
                specs[name] = spec

        return specs
