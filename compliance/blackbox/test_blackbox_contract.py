# compliance/blackbox/test_blackbox_contract.py

"""Normative black-box compliance suite (audit a13, P1-01).

This suite exercises the installed package through its public surface
only: ``arvis`` top-level exports and ``arvis.host_api``. It imports no
internal module, no test fixture, no repository file: it is designed to
run against the built wheel in a pristine environment
(``scripts/run_blackbox_against_wheel.sh``), where the repository is not
importable at all.

When the environment variable ``BLACKBOX_REQUIRE_WHEEL=1`` is set, the
suite refuses to run against a source checkout: the arvis it imports
must come from an installed distribution. Without the variable, the
suite also runs in the normal repository gate, as a plain part of the
compliance tree.

Scenario tables are versioned: changing them is changing what ARVIS
promises a host, and must be deliberate.
"""

import os

import pytest

import arvis
import arvis.host_api
from arvis import ArvisEngine

BLACKBOX_SCENARIOS_VERSION = 1

# Declared-risk gradation: the documented three-band policy of the
# 0.1.0-alpha gate (README quick start, examples 01/06/09).
RISK_SCENARIOS: tuple[tuple[float, str], ...] = (
    (0.10, "APPROVED"),
    (0.50, "REVIEW"),
    (0.90, "BLOCKED"),
)

# The host integration surface, as promised (NOTE_DECISION 2026-07-24).
# Deliberately duplicated from the repository contract test: this suite
# must stay self-contained, since the repository is absent when running
# against the wheel.
HOST_API_MODULES: dict[str, int] = {
    "engine": 4,
    "access": 2,
    "services": 3,
    "vfs": 9,
    "tools": 5,
    "memory": 12,
    "knowledge": 4,
    "conversation": 3,
    "cognition": 1,
    "control": 5,
    "llm": 1,
    "telemetry": 2,
}


def test_runs_against_an_installed_distribution_when_required() -> None:
    if os.environ.get("BLACKBOX_REQUIRE_WHEEL") != "1":
        pytest.skip("wheel provenance check only enforced by the wheel runner")
    assert "site-packages" in (arvis.__file__ or ""), (
        "BLACKBOX_REQUIRE_WHEEL=1 but arvis was imported from a source "
        f"checkout: {arvis.__file__}"
    )


def _status(result) -> str:
    decision = result.to_dict()["decision"]
    allowed = "allowed=True" in decision
    needs_confirm = "requires_user_validation=True" in decision
    if allowed and not needs_confirm:
        return "APPROVED"
    if needs_confirm:
        return "REVIEW"
    return "BLOCKED"


@pytest.mark.parametrize(("risk", "expected"), RISK_SCENARIOS)
def test_declared_risk_gradation(risk: float, expected: str) -> None:
    engine = ArvisEngine()
    result = engine.run("blackbox", {"risk": risk})
    assert _status(result) == expected


def test_run_view_carries_a_commitment_and_an_ir() -> None:
    engine = ArvisEngine()
    view = engine.run("blackbox", {"risk": 0.10})
    assert view.global_commitment
    exported = view.to_ir()
    assert isinstance(exported, dict) and exported


def test_replay_authenticates_against_the_run_commitment() -> None:
    engine = ArvisEngine()
    view = engine.run("blackbox", {"risk": 0.10})

    replayed = engine.replay_verified(
        view.to_ir(),
        expected_global_commitment=view.global_commitment,
    )
    assert replayed.global_commitment == view.global_commitment


def test_replay_refuses_a_wrong_external_commitment() -> None:
    engine = ArvisEngine()
    view = engine.run("blackbox", {"risk": 0.10})
    with pytest.raises(RuntimeError):
        engine.replay_verified(
            view.to_ir(),
            expected_global_commitment="0" * 64,
        )


def test_tool_surface_freezes_to_a_stable_fingerprint() -> None:
    engine = ArvisEngine()
    pinned = engine.freeze_tools()
    assert isinstance(pinned, str) and len(pinned) == 64
    assert engine.freeze_tools() == pinned
    assert engine.list_tools() == []


def test_host_api_surface_resolves_as_promised() -> None:
    import importlib

    assert arvis.host_api.HOST_API_VERSION == "1.0"
    assert arvis.host_api.PROVISIONAL_MODULES == frozenset({"control"})

    total = 0
    for module_name, expected_count in HOST_API_MODULES.items():
        module = importlib.import_module(f"arvis.host_api.{module_name}")
        exported = list(module.__all__)
        assert len(exported) == expected_count, (
            f"host_api.{module_name} promises {expected_count} symbols, "
            f"exposes {len(exported)}"
        )
        for symbol in exported:
            assert hasattr(module, symbol)
        total += len(exported)
    assert total == 51
