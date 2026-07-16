# arvis/api/runtime_controls.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrustedRuntimeControls:
    """Host-only runtime controls, injected by composition.

    These knobs influence tool selection and gate posture, so they
    belong to the embedding host (the composition root), never to the
    public run() surface: they are not read from request payloads nor
    from ctx.extra, and they are rejected in the production runtime
    profile. Gate overrides can only skip additional hardening; they
    can never relax a verdict that is already stricter.
    """

    force_tool: str | None = None
    force_execution: bool = False
    force_safe_projection: bool = False
    force_safe_switching: bool = False
