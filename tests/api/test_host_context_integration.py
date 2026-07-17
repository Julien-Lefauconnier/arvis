# tests/api/test_host_context_integration.py
"""Host context end to end through CognitiveOS (campaign 5, D-1).

The opaque host context declared on the config reaches the kernel
service registry; the conventional instance label is extracted and
available to stamp intents; config-level component manifests reach the
config fingerprint. When no host context is declared, the resolved
context and label are absent, so a run stays byte-identical to a run
without them.
"""

from __future__ import annotations

from arvis import CognitiveOS, CognitiveOSConfig
from arvis.api.commitment import config_fingerprint


def test_host_context_reaches_the_service_registry():
    os_ = CognitiveOS(
        CognitiveOSConfig(
            runtime_mode="local",
            host_context={"instance_label": "tool_runner", "region": "eu-west"},
        )
    )
    runtime = os_._build_runtime()
    assert runtime.services.instance_label == "tool_runner"
    assert runtime.services.host_context == {
        "instance_label": "tool_runner",
        "region": "eu-west",
    }


def test_absent_host_context_leaves_registry_fields_none():
    os_ = CognitiveOS(CognitiveOSConfig(runtime_mode="local"))
    runtime = os_._build_runtime()
    assert runtime.services.host_context is None
    assert runtime.services.instance_label is None


def test_host_context_without_label_yields_no_label():
    os_ = CognitiveOS(
        CognitiveOSConfig(runtime_mode="local", host_context={"region": "eu"})
    )
    runtime = os_._build_runtime()
    assert runtime.services.instance_label is None
    assert runtime.services.host_context == {"region": "eu"}


def test_config_fingerprint_distinguishes_manifested_components():
    class ManifestGate:
        def __init__(self, region: str) -> None:
            self.region = region

        def governance_manifest(self) -> dict:
            return {"region": self.region}

    eu = config_fingerprint(
        CognitiveOSConfig(runtime_mode="local", consent_gate=ManifestGate("eu"))
    )
    us = config_fingerprint(
        CognitiveOSConfig(runtime_mode="local", consent_gate=ManifestGate("us"))
    )
    assert eu != us


def test_config_fingerprint_unchanged_for_components_without_manifest():
    class PlainGate:
        pass

    a = config_fingerprint(
        CognitiveOSConfig(runtime_mode="local", consent_gate=PlainGate())
    )
    b = config_fingerprint(
        CognitiveOSConfig(runtime_mode="local", consent_gate=PlainGate())
    )
    assert a == b


def test_host_context_does_not_change_the_config_fingerprint():
    # host_context is provenance, not a governance component: it must
    # not enter the config fingerprint (which binds WHAT governs).
    plain = config_fingerprint(CognitiveOSConfig(runtime_mode="local"))
    labeled = config_fingerprint(
        CognitiveOSConfig(runtime_mode="local", host_context={"instance_label": "x"})
    )
    assert plain == labeled
