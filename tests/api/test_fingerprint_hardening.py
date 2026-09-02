# tests/api/test_fingerprint_hardening.py
"""Fingerprints cannot collide across modules nor omit governance.

Campaign HARDEN (DM-H5, audit P1-15e, 2026-09-02). Two defects in the
commitment fingerprint chain:

- ``component_fingerprint_material`` bound ``type(obj).__qualname__``
  WITHOUT the module, so two homonymous classes from different
  modules produced the same material (the canonicalization layer, by
  contrast, binds module + qualname exactly to prevent this);
- ``config_fingerprint`` omitted ``confirmation_registry``
  (governance-relevant: the registry of accepted confirmation formats
  governs): two configs differing only there shared a fingerprint.

Two exclusions are deliberate and stay pinned: ``host_context`` is
provenance, not governance (pinned by
test_host_context_integration), and ``telemetry_sink`` is
observe-only; the docstring names both doctrines.
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.api.commitment import config_fingerprint
from arvis.kernel_core.host_declaration import component_fingerprint_material


def _config(**overrides):
    base = {
        "enable_trace": True,
        "strict_mode": False,
        "runtime_mode": "local",
        "audit_commitment_policy": "none",
        "runtime_controls": None,
        "consent_gate": None,
        "egress_gate": None,
        "audit_intent_sink": None,
        "core_model": None,
        "adapter_registry": None,
        "host_context": None,
        "confirmation_registry": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_homonymous_classes_from_different_modules_do_not_collide() -> None:
    class Gate:  # noqa: N801 (probe class)
        pass

    probe_a = Gate()

    # A second class with the SAME qualname, minted as if from another
    # module: only the module distinguishes them.
    class_b = type(Gate.__name__, (), {})
    class_b.__qualname__ = Gate.__qualname__
    class_b.__module__ = "some.other.module"
    probe_b = class_b()

    material_a = component_fingerprint_material(probe_a)
    material_b = component_fingerprint_material(probe_b)
    assert material_a != material_b, (
        "two homonymous classes from different modules share fingerprint "
        "material: the binding must include the module (DM-H5)"
    )


def test_config_fingerprint_sees_the_confirmation_registry() -> None:
    class Registry:
        pass

    without = config_fingerprint(_config())
    with_registry = config_fingerprint(_config(confirmation_registry=Registry()))
    assert without != with_registry, (
        "two configs differing only in confirmation_registry share a "
        "config_fingerprint (DM-H5)"
    )


def test_the_telemetry_sink_stays_excluded_on_purpose() -> None:
    """Observe-only doctrine: a sink swap must never move the
    governance fingerprint (emission happens after the result is
    finalized and cannot influence determinism or replay)."""

    class SinkA:
        pass

    class SinkB:
        pass

    assert config_fingerprint(_config(telemetry_sink=SinkA())) == config_fingerprint(
        _config(telemetry_sink=SinkB())
    )
