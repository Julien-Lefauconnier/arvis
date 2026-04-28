# tests/adapters/kernel/test_signal_semantics.py

from arvis.adapters.kernel.kernel_adapter import KernelAdapter
from arvis.adapters.kernel.signals.signal_semantics import SignalSemantics
from tests.adapters.kernel.fixtures import dummy_ir


def test_semantic_determinism_same_ir():
    adapter = KernelAdapter()

    ir = dummy_ir()

    signals_1 = adapter.ingest_ir(ir)
    signals_2 = adapter.ingest_ir(ir)

    fp1 = [SignalSemantics.fingerprint(s) for s in signals_1]
    fp2 = [SignalSemantics.fingerprint(s) for s in signals_2]

    assert fp1 == fp2


def test_metadata_is_not_deterministic():
    adapter = KernelAdapter()

    ir = dummy_ir()

    signals_1 = adapter.ingest_ir(ir)
    signals_2 = adapter.ingest_ir(ir)

    ids_1 = [s.signal_id for s in signals_1]
    ids_2 = [s.signal_id for s in signals_2]

    assert ids_1 != ids_2


def test_fingerprint_ignores_runtime_metadata():
    adapter = KernelAdapter()

    ir = dummy_ir()

    signals_1 = adapter.ingest_ir(ir)
    signals_2 = adapter.ingest_ir(ir)

    for s1, s2 in zip(signals_1, signals_2, strict=True):
        assert s1.signal_id != s2.signal_id
        assert SignalSemantics.fingerprint(s1) == SignalSemantics.fingerprint(s2)
