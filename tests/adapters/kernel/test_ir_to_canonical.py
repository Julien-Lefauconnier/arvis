# tests/adapters/kernel/test_ir_to_canonical.py

from arvis.adapters.kernel.mappers.ir_to_canonical import ir_to_canonical
from tests.adapters.kernel.fixtures import dummy_ir


def test_ir_to_canonical_returns_signals():
    ir = dummy_ir()

    canonicals = ir_to_canonical(ir)

    assert isinstance(canonicals, list)
    assert len(canonicals) > 0

    for c in canonicals:
        assert c.key is not None
        assert c.state == "ACTIVE"