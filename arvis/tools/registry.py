# arvis/tools/registry.py


import hashlib

from arvis.errors.base import ArvisSecurityError
from arvis.tools.base import BaseTool
from arvis.tools.spec import ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._frozen: bool = False

    def register(self, tool: BaseTool, *, replace: bool = False) -> None:
        """Register a tool under its declared name.

        F-004: a governed registry is never mutated silently. A
        frozen registry refuses any registration, and re-registering
        an existing name requires an explicit replace=True.
        """
        name = tool.name
        if self._frozen:
            raise ArvisSecurityError(
                f"tool registry is frozen; cannot register {name!r}",
                details={"tool": name},
            )
        if name in self._tools and not replace:
            raise ArvisSecurityError(
                f"tool {name!r} is already registered; explicit "
                "replace=True is required to replace it",
                details={"tool": name},
            )
        self._tools[name] = tool

    def freeze(self) -> str:
        """Freeze the registry after bootstrap.

        Returns the registry fingerprint so the host can pin and
        audit the frozen tool surface.
        """
        self._frozen = True
        return self.fingerprint()

    @property
    def frozen(self) -> bool:
        return self._frozen

    def fingerprint(self) -> str:
        """Deterministic hash of the registered tool surface."""
        digest = hashlib.sha256()
        for name in sorted(self._tools):
            tool = self._tools[name]
            digest.update(name.encode("utf-8"))
            digest.update(b"\x00")
            digest.update(type(tool).__qualname__.encode("utf-8"))
            digest.update(b"\x01")
        return digest.hexdigest()

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
