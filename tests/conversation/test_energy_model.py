# tests/conversation/test_energy_model.py

from arvis.conversation.conversation_energy_model import ConversationEnergyModel


def test_energy_computation_basic():
    energy = ConversationEnergyModel.compute_energy(
        collapse_risk=0.5,
        uncertainty=0.5,
        temporal_pressure=0.5,
    )

    assert 0.0 <= energy <= 1.0


def test_energy_includes_memory_and_constraints():
    energy = ConversationEnergyModel.compute_energy(
        collapse_risk=0.2,
        uncertainty=0.2,
        temporal_pressure=0.2,
        memory_pressure=0.8,
        has_constraints=True,
    )

    assert energy > 0.2  # boosted by memory + constraints


def test_energy_clamped():
    energy = ConversationEnergyModel.compute_energy(
        collapse_risk=10.0,
        uncertainty=10.0,
        temporal_pressure=10.0,
        memory_pressure=10.0,
        has_constraints=True,
    )

    assert energy <= 1.0


def test_energy_uses_dynamic_weights():
    from arvis.conversation.conversation_energy_model import ConversationEnergyModel

    weights = {
        "collapse": 1.0,
        "uncertainty": 0.0,
        "pressure": 0.0,
        "memory": 0.0,
        "constraint": 0.0,
        "delta_v": 0.0,
    }

    energy = ConversationEnergyModel.compute_energy(
        collapse_risk=1.0,
        uncertainty=0.0,
        temporal_pressure=0.0,
        dynamic_weights=weights,
    )

    assert abs(energy - 1.0) < 1e-6


def test_energy_increases_with_positive_delta_v():
    from arvis.conversation.conversation_energy_model import ConversationEnergyModel

    e1 = ConversationEnergyModel.compute_energy(
        collapse_risk=0.0,
        uncertainty=0.0,
        temporal_pressure=0.0,
        delta_v=0.0,
    )

    e2 = ConversationEnergyModel.compute_energy(
        collapse_risk=0.0,
        uncertainty=0.0,
        temporal_pressure=0.0,
        delta_v=0.5,
    )

    assert e2 > e1


def test_energy_ignores_negative_delta_v():
    from arvis.conversation.conversation_energy_model import ConversationEnergyModel

    e1 = ConversationEnergyModel.compute_energy(
        collapse_risk=0.0,
        uncertainty=0.0,
        temporal_pressure=0.0,
        delta_v=0.0,
    )

    e2 = ConversationEnergyModel.compute_energy(
        collapse_risk=0.0,
        uncertainty=0.0,
        temporal_pressure=0.0,
        delta_v=-0.5,
    )

    assert e2 == e1


def test_energy_clamps_large_delta_v():
    from arvis.conversation.conversation_energy_model import ConversationEnergyModel

    e = ConversationEnergyModel.compute_energy(
        collapse_risk=0.0,
        uncertainty=0.0,
        temporal_pressure=0.0,
        delta_v=10.0,
    )

    # should not explode
    assert 0.0 <= e <= 1.0


def test_energy_respects_delta_v_weight():
    from arvis.conversation.conversation_energy_model import ConversationEnergyModel

    weights = {
        "collapse": 0.0,
        "uncertainty": 0.0,
        "pressure": 0.0,
        "memory": 0.0,
        "constraint": 0.0,
        "delta_v": 1.0,
    }

    e = ConversationEnergyModel.compute_energy(
        collapse_risk=0.0,
        uncertainty=0.0,
        temporal_pressure=0.0,
        delta_v=0.5,
        dynamic_weights=weights,
    )

    assert abs(e - 0.5) < 1e-6


def test_energy_weights_are_normalized():
    weights = {
        "collapse": 2.0,
        "uncertainty": 2.0,
        "pressure": 2.0,
        "memory": 2.0,
        "constraint": 2.0,
        "delta_v": 2.0,
    }

    e = ConversationEnergyModel.compute_energy(
        collapse_risk=1.0,
        uncertainty=0.0,
        temporal_pressure=0.0,
        dynamic_weights=weights,
    )

    # collapse weight becomes 1/6
    assert abs(e - (1.0 / 6.0)) < 1e-6
