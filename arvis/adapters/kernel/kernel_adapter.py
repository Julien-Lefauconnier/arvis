# arvis/adapters/kernel/kernel_adapter.py


from arvis.ir.cognitive_ir import CognitiveIR
from arvis.signals.canonical.canonical_signal import CanonicalSignal
from arvis.signals.signal_journal import get_signal_journal

from .mappers.ir_to_canonical import ir_to_canonical


class KernelAdapter:
    def __init__(self, *, deterministic_mode: bool = False) -> None:
        """
        KernelAdapter orchestrates IR → canonical → event → signal projection.

        Determinism model:
        ------------------
        - Semantic determinism is guaranteed:
            identical IR → identical signal semantics

        - Runtime metadata is NOT deterministic:
            signal_id (UUID)
            event_id (UUID)
            timestamps

        deterministic_mode:
            Reserved for future strict replay support where metadata may be overridden.
        """
        self.journal = get_signal_journal()
        self.deterministic_mode = deterministic_mode

    def ingest_ir(self, ir: CognitiveIR) -> list[CanonicalSignal]:
        canonicals = ir_to_canonical(ir)

        for canonical in canonicals:
            self.journal.append(canonical)

        return canonicals
