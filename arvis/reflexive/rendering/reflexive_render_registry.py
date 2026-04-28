# arvis/reflexive/rendering/reflexive_render_registry.py

from typing import Any, Dict, cast

from arvis.reflexive.core.reflexive_mode import ReflexiveMode
from arvis.reflexive.rendering.reflexive_renderer import ReflexiveRenderer


class ReflexiveRenderRegistry:
    _REGISTRY: Dict[ReflexiveMode, ReflexiveRenderer] = {}

    @classmethod
    def for_mode(cls, mode: ReflexiveMode) -> ReflexiveRenderer:
        if mode not in cls._REGISTRY:
            cls._REGISTRY[mode] = cls._build_renderer(mode)
        return cls._REGISTRY[mode]

    @staticmethod
    def _observation_only_renderer() -> ReflexiveRenderer:
        def render(snapshot: Any) -> Dict[str, Any]:
            data = cast(Dict[str, Any], snapshot.to_dict())
            # SAFE: create filtered copy without mutating attested fields
            filtered = dict(data)
            filtered["timeline_views"] = {}
            # invalidate attestation if structure changed
            if "attestation" in filtered:
                filtered["attestation"] = None
            return filtered

        return ReflexiveRenderer(render_fn=render)

    @staticmethod
    def _explanatory_renderer() -> ReflexiveRenderer:
        def render(snapshot: Any) -> Dict[str, Any]:
            return cast(Dict[str, Any], snapshot.to_dict())

        return ReflexiveRenderer(render_fn=render)

    @staticmethod
    def _compliance_renderer() -> ReflexiveRenderer:
        def render(snapshot: Any) -> Dict[str, Any]:
            data = cast(Dict[str, Any], snapshot.to_dict())
            filtered = dict(data)
            filtered.setdefault("compliance", {})
            if "attestation" in filtered:
                filtered["attestation"] = None
            return filtered

        return ReflexiveRenderer(render_fn=render)

    @classmethod
    def _build_renderer(cls, mode: ReflexiveMode) -> ReflexiveRenderer:
        if mode == ReflexiveMode.OBSERVATION_ONLY:
            return cls._observation_only_renderer()
        if mode == ReflexiveMode.EXPLANATORY:
            return cls._explanatory_renderer()
        if mode in (
            ReflexiveMode.COMPLIANCE_CHAIN_READY,
            ReflexiveMode.AUDITABLE,
        ):
            return cls._compliance_renderer()

        raise ValueError(f"Unknown reflexive mode: {mode}")
