# tests/adapters/kernel/test_kernel_adapter_integration.py


from tests.adapters.kernel.fixtures import dummy_ir
from arvis.adapters.kernel.mappers.ir_to_canonical import ir_to_canonical


def test_ir_mapping_is_deterministic():
    ir = dummy_ir()

    s1 = ir_to_canonical(ir)
    s2 = ir_to_canonical(ir)

    assert len(s1) == len(s2)

    for a, b in zip(s1, s2):
        assert a.key == b.key
        assert a.state == b.state


def test_empty_ir_produces_signal():
    class EmptyIR:
        pass

    ir = EmptyIR()

    canonicals = ir_to_canonical(ir)

    assert isinstance(canonicals, list)
    assert len(canonicals) > 0
