# arvis/kernel/kernel_contract.py

from typing import Protocol

from arvis.interfaces.cognitive_bundle import CognitiveBundle


class CognitiveKernelContract(Protocol):
    """
    Core cognitive kernel contract.

    Stateless, pure cognitive transformation.
    """

    def run(self, bundle: CognitiveBundle) -> CognitiveBundle: ...
