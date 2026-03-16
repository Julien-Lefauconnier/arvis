# arvis/kernel/kernel_invariants.py

def assert_kernel_invariants(bundle):
    """
    Global ARVIS invariants.
    """

    assert bundle.stability_score >= 0
    assert bundle.stability_score <= 1

    if bundle.reasoning_gap is not None:
        assert bundle.reasoning_intent is not None

