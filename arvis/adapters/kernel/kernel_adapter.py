# arvis/adapters/kernel/kernel_adapter.py

from typing import List


from veramem_kernel.signals.signal_journal import get_signal_journal
from veramem_kernel.api.signals import Signal

from .mappers.ir_to_canonical import ir_to_canonical
from .canonical_to_event import canonical_to_event
from .event_to_signal import event_to_signal
from arvis.ir.cognitive_ir import CognitiveIR


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

    def ingest_ir(self, ir: CognitiveIR) -> List[Signal]:
        canonicals = ir_to_canonical(ir)

        signals: List[Signal] = []
        for c in canonicals:
            event = canonical_to_event(c)
            signal = event_to_signal(event)
            self.journal.append(signal)
            signals.append(signal)

        return signals
