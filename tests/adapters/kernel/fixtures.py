# tests/adapters/kernel/fixtures.py

class DummyState:
    stable = True
    early_warning = False


class DummyDecision:
    decision_kind = "informational"
    conflicts = ()
    uncertainty_frames = ()


class DummyGate:
    class Verdict:
        value = "allow"

    verdict = Verdict()
    instability_score = 0.0


class DummyIR:
    def __init__(self):
        self.state = DummyState()
        self.decision = DummyDecision()
        self.gate = DummyGate()


def dummy_ir():
    return DummyIR()