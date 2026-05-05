# arvis/kernel/pipeline/stages/gate_stage.py

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.stages.gate.stage import GateStage

# ======== PUBLIC API COMPAT ========
from arvis.math.gate.gate_entry import run_gate_kernel as _run_gate_kernel
from arvis.math.gate.gate_fusion import run_fusion as _run_fusion
from arvis.math.gate.gate_policy import apply_gate_policy as _apply_gate_policy
from arvis.math.switching.global_stability_observer import GlobalStabilityObserver

from .gate.adaptive import AdaptiveRuntimeObserver
from .gate.composite import CompositeLyapunov
from .gate.pi_override import PiBasedGate
from .gate.stability import GlobalStabilityGuard
from .gate.stability import build_validity_envelope as _build_validity_envelope
from .gate.switching import switching_condition

# ---- monkeypatch-safe wrappers ----


def run_gate_kernel(*args: Any, **kwargs: Any) -> Any:
    return _run_gate_kernel(*args, **kwargs)


def run_fusion(*args: Any, **kwargs: Any) -> Any:
    return _run_fusion(*args, **kwargs)


def apply_gate_policy(*args: Any, **kwargs: Any) -> Any:
    return _apply_gate_policy(*args, **kwargs)


def build_validity_envelope(*args: Any, **kwargs: Any) -> Any:
    return _build_validity_envelope(*args, **kwargs)


__all__ = [
    "GateStage",
    "run_gate_kernel",
    "run_fusion",
    "apply_gate_policy",
    "build_validity_envelope",
    "CompositeLyapunov",
    "GlobalStabilityGuard",
    "GlobalStabilityObserver",
    "AdaptiveRuntimeObserver",
    "PiBasedGate",
    "switching_condition",
]
