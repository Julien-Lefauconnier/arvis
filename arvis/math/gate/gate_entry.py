# arvis/math/gate/gate_entry.py

from typing import Any

from arvis.math.gate.gate_kernel import compute_gate_kernel
from arvis.math.gate.gate_types import GateKernelInputs


def run_gate_kernel(inputs: GateKernelInputs) -> Any:
    return compute_gate_kernel(inputs)
