# arvis/kernel/pipeline/gate_overrides.py

from dataclasses import dataclass


@dataclass
class GateOverrides:
    force_safe_projection: bool = False
    force_safe_switching: bool = False
    disable_validity_envelope: bool = False
    disable_projection_hard_block: bool = False
