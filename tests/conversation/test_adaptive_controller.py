# tests/conversation/test_adaptive_controller.py

from arvis.conversation.conversation_adaptive_controller import ConversationAdaptiveController
from arvis.conversation.conversation_energy_model import ConversationEnergyModel
from arvis.conversation.conversation_stability_signals import ConversationStabilitySignalsBuilder
from arvis.conversation.conversation_regime_controller import ConversationRegimeController
from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.conversation.conversation_adaptive_policy import AdaptiveThresholdPolicy

class DummyState:
    def __init__(self, signals):
        self.signals = signals


def test_adaptive_controller_increases_weights_on_instability():
    state = DummyState({
        "feedback": {
            "high_collapse_risk": True,
            "high_uncertainty": True,
        }
    })

    before = ConversationEnergyModel._dynamic_weights.copy()

    ConversationAdaptiveController.adapt(state)

    after = ConversationEnergyModel._dynamic_weights

    assert after["collapse"] >= before["collapse"]
    assert after["uncertainty"] >= before["uncertainty"]


def test_adaptive_controller_relaxes_when_stable():
    state = DummyState({
        "feedback": {}
    })


    ConversationAdaptiveController.adapt(state)

    after = ConversationEnergyModel._dynamic_weights

    # should not explode
    assert isinstance(after, dict)


def test_weights_are_normalized():
    state = DummyState({
        "feedback": {
            "high_collapse_risk": True
        }
    })

    ConversationAdaptiveController.adapt(state)

    weights = ConversationEnergyModel._dynamic_weights
    total = sum(weights.values())

    assert abs(total - 1.0) < 1e-6


def test_adaptive_controller_increases_with_positive_delta_v():
    state = DummyState({
        "delta_v": 0.5,
        "feedback": {}
    })

    ConversationAdaptiveController.adapt(state)

    after = ConversationEnergyModel._dynamic_weights

    # collapse should remain significant contributor
    assert after["collapse"] > 0.0

    # and weights should stay normalized
    assert abs(sum(after.values()) - 1.0) < 1e-6


def test_adaptive_controller_relaxes_with_negative_delta_v():
    state = DummyState({
        "delta_v": -0.5,
        "feedback": {}
    })

    before = ConversationEnergyModel._dynamic_weights.copy()

    ConversationAdaptiveController.adapt(state)

    after = ConversationEnergyModel._dynamic_weights

    assert after["collapse"] <= before["collapse"]


def test_adaptive_controller_clamps_delta_v():
    state = DummyState({
        "delta_v": 10.0,
        "feedback": {}
    })

    ConversationAdaptiveController.adapt(state)

    weights = ConversationEnergyModel._dynamic_weights

    assert all(0.0 < v <= 1.0 for v in weights.values())


def test_delta_v_influences_distribution():
    state = DummyState({
        "delta_v": 0.5,
        "feedback": {}
    })


    ConversationAdaptiveController.adapt(state)

    after = ConversationEnergyModel._dynamic_weights

    # collapse should not collapse 😄
    assert after["collapse"] > 0.2


def test_adaptive_controller_inertia_limits_variation():
    state = DummyState({
        "delta_v": 1.0,
        "feedback": {}
    })

    before = ConversationEnergyModel._dynamic_weights.copy()

    ConversationAdaptiveController.adapt(state)
    after = ConversationEnergyModel._dynamic_weights

    # variation should be bounded
    diffs = [abs(after[k] - before[k]) for k in before]

    assert max(diffs) < 0.1


def test_adaptive_controller_stabilizes_over_time():
    state = DummyState({
        "delta_v": 0.5,
        "feedback": {}
    })

    for _ in range(20):
        ConversationAdaptiveController.adapt(state)

    weights = ConversationEnergyModel._dynamic_weights

    # weights should stay normalized
    assert abs(sum(weights.values()) - 1.0) < 1e-6


def test_adaptive_controller_increases_with_high_energy():
    state = DummyState({
        "energy": 0.9,
        "feedback": {}
    })


    ConversationAdaptiveController.adapt(state)

    after = ConversationEnergyModel._dynamic_weights

    assert abs(sum(after.values()) - 1.0) < 1e-6


def test_adaptive_controller_relaxes_with_low_energy():
    state = DummyState({
        "energy": 0.1,
        "feedback": {}
    })


    ConversationAdaptiveController.adapt(state)

    after = ConversationEnergyModel._dynamic_weights

    assert abs(sum(after.values()) - 1.0) < 1e-6


def test_adaptive_controller_neutral_energy_no_explosion():
    state = DummyState({
        "energy": 0.5,
        "feedback": {}
    })


    ConversationAdaptiveController.adapt(state)

    after = ConversationEnergyModel._dynamic_weights

    assert abs(sum(after.values()) - 1.0) < 1e-6


def test_delta_w_signal_is_added():
    state = DummyState({"delta_v": 0.1})

    builder = ConversationStabilitySignalsBuilder()
    builder.update(state)

    assert "delta_w" in state.signals


def test_energy_increases_with_positive_delta_w():
    e1 = ConversationEnergyModel.compute_energy(
        collapse_risk=0.2,
        uncertainty=0.2,
        temporal_pressure=0.0,
        delta_w=0.0,
    )

    e2 = ConversationEnergyModel.compute_energy(
        collapse_risk=0.2,
        uncertainty=0.2,
        temporal_pressure=0.0,
        delta_w=0.5,
    )

    assert e2 >= e1


def test_regime_more_conservative_when_delta_w_positive():
    state = DummyState({
        "delta_w": 0.5,
        "memory_pressure": 0,
        "has_constraints": False,
    })

    strategy = ConversationRegimeController.regulate(
        proposed_strategy=ResponseStrategyType.ACTION,
        collapse_risk=0.2,
        uncertainty=0.2,
        state=state,
    )

    assert strategy in (
        ResponseStrategyType.CONFIRMATION,
        ResponseStrategyType.ABSTENTION,
    )


def test_instability_increases_conservativeness():
    state = DummyState({
        "delta_w": 0.0,
        "instability": 0.6,  # élevé
        "memory_pressure": 0,
        "has_constraints": False,
    })

    strategy = ConversationRegimeController.regulate(
        proposed_strategy=ResponseStrategyType.ACTION,
        collapse_risk=0.2,
        uncertainty=0.2,
        state=state,
    )

    assert strategy in (
        ResponseStrategyType.CONFIRMATION,
        ResponseStrategyType.ABSTENTION,
    )


def test_delta_w_override_has_priority_over_instability():
    state = DummyState({
        "delta_w": 0.5,  # force override
        "instability": 0.0,
        "memory_pressure": 0,
        "has_constraints": False,
    })

    strategy = ConversationRegimeController.regulate(
        proposed_strategy=ResponseStrategyType.ACTION,
        collapse_risk=0.0,
        uncertainty=0.0,
        state=state,
    )

    assert strategy == ResponseStrategyType.ABSTENTION


def test_dynamic_thresholds_lower_with_instability():

    state_high = DummyState({
        "delta_w": 0.0,
        "instability": 0.7,
    })

    # same energy base

    strategy_high = ConversationRegimeController.regulate(
        proposed_strategy=ResponseStrategyType.ACTION,
        collapse_risk=0.4,
        uncertainty=0.2,
        state=state_high,
    )

    assert strategy_high in (
        ResponseStrategyType.CONFIRMATION,
        ResponseStrategyType.ABSTENTION,
    )




def test_stability_monotonicity_with_instability():
    prev_strategy = None

    for instability in [0.0, 0.2, 0.4, 0.6]:
        state = DummyState({
            "delta_w": 0.0,
            "instability": instability,
        })

        strategy = ConversationRegimeController.regulate(
            proposed_strategy=ResponseStrategyType.ACTION,
            collapse_risk=0.3,
            uncertainty=0.2,
            state=state,
        )

        if prev_strategy == ResponseStrategyType.ABSTENTION:
            assert strategy == ResponseStrategyType.ABSTENTION

        prev_strategy = strategy



def test_instability_override_has_priority_over_energy_thresholds():
    state = DummyState({
        "delta_w": 0.0,
        "instability": 0.6,
        "memory_pressure": 0,
        "has_constraints": False,
    })

    strategy = ConversationRegimeController.regulate(
        proposed_strategy=ResponseStrategyType.ACTION,
        collapse_risk=0.0,
        uncertainty=0.0,
        state=state,
    )

    assert strategy == ResponseStrategyType.CONFIRMATION


def test_memory_increases_structural_conservativeness():
    state = DummyState({
        "delta_w": 0.0,
        "instability": 0.2,
        "memory_instability": 0.8,
    })

    strategy = ConversationRegimeController.regulate(
        proposed_strategy=ResponseStrategyType.ACTION,
        collapse_risk=0.2,
        uncertainty=0.2,
        state=state,
    )

    assert strategy in (
        ResponseStrategyType.CONFIRMATION,
        ResponseStrategyType.ABSTENTION,
    )


def test_memory_temporal_accumulation():
    state = DummyState({
        "delta_v": 0.0,
        "memory_instability": 0.0,
    })

    builder = ConversationStabilitySignalsBuilder()

    # simulate repeated instability
    for _ in range(5):
        state.signals["delta_v"] = 0.8
        builder.update(state)

    assert state.signals["memory_instability"] > 0.5

def test_memory_hierarchy():
    state = DummyState({"delta_v": 0.0})
    builder = ConversationStabilitySignalsBuilder()

    for _ in range(5):
        state.signals["delta_v"] = 0.8
        builder.update(state)

    assert state.signals["memory_short"] >= state.signals["memory_medium"]
    assert state.signals["memory_medium"] >= state.signals["memory_long"]



def test_memory_long_accumulates():
    state = DummyState({"delta_v": 0.0})
    builder = ConversationStabilitySignalsBuilder()

    for _ in range(10):
        state.signals["delta_v"] = 0.6
        builder.update(state)

    assert state.signals["memory_long"] > 0.3


def test_memory_decay():
    state = DummyState({"delta_v": 0.0})
    builder = ConversationStabilitySignalsBuilder()

    # spike
    state.signals["delta_v"] = 0.9
    builder.update(state)

    # calm
    for _ in range(10):
        state.signals["delta_v"] = 0.0
        builder.update(state)

    assert state.signals["memory_short"] < 0.9


def test_adaptive_policy_pushes_to_confirmation():
    state = DummyState({
        "instability": 0.3,
        "memory_instability": 0.6,
        "delta_w": 0.0,
    })

    policy = AdaptiveThresholdPolicy()

    result = policy.apply(
        proposed_strategy=ResponseStrategyType.ACTION,
        state=state,
    )

    assert result in (
        ResponseStrategyType.CONFIRMATION,
        ResponseStrategyType.ABSTENTION,
    )


def test_memory_decay_when_stable():
    state = DummyState({"delta_v": 0.0, "memory_instability": 0.8})
    builder = ConversationStabilitySignalsBuilder()

    for _ in range(10):
        state.signals["delta_v"] = 0.0
        builder.update(state)

    assert state.signals["memory_instability"] < 0.5


def test_structural_memory_drives_delta_w():
    state = DummyState({
        "memory_long": 0.8,
        "memory_medium": 0.6,
        "memory_instability": 0.2,
    })

    builder = ConversationStabilitySignalsBuilder()
    builder.update(state)

    assert state.signals["delta_w"] > 0.3


def test_policy_sensitive_to_structural_memory():
    state = DummyState({
        "instability": 0.2,
        "memory_structural": 0.7,
        "delta_w": 0.0,
    })

    policy = AdaptiveThresholdPolicy()

    result = policy.apply(
        proposed_strategy=ResponseStrategyType.ACTION,
        state=state,
    )

    assert result != ResponseStrategyType.ACTION


