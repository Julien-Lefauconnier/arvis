# tests/kernel_core/test_host_declaration.py
"""Host-declared governance context and component manifests (campaign 5).

Two properties: the opaque host context (D-1) is transported and stamped
without interpretation, byte-identical to a run without it when absent;
and injected components declaring a governance_manifest() are bound in
full, closing the audit constat-17 collision where two differently
configured components of the same class shared a fingerprint.
"""

from __future__ import annotations

import pytest

from arvis.kernel_core.canonicalization import NonCanonicalizableError
from arvis.kernel_core.host_declaration import (
    INSTANCE_LABEL_KEY,
    GovernanceManifestProvider,
    component_fingerprint_material,
    instance_label_of,
    resolve_host_context,
)

# ---------------------------------------------------------------
# resolve_host_context: opaque, injective, fail-closed
# ---------------------------------------------------------------


def test_none_context_stays_none():
    assert resolve_host_context(None) is None


def test_context_is_transported_verbatim():
    ctx = {"instance_label": "tool_runner", "region": "eu-west", "shard": 3}
    resolved = resolve_host_context(ctx)
    assert resolved == {
        "instance_label": "tool_runner",
        "region": "eu-west",
        "shard": 3,
    }


def test_context_is_canonicalized_deterministically():
    ctx = {"b": 2, "a": 1}
    assert resolve_host_context(ctx) == resolve_host_context({"a": 1, "b": 2})


def test_non_string_key_is_refused():
    with pytest.raises(NonCanonicalizableError):
        resolve_host_context({1: "x"})


def test_non_canonicalizable_value_is_refused():
    def gen():
        yield 1

    with pytest.raises(NonCanonicalizableError):
        resolve_host_context({"bad": gen()})


def test_non_mapping_context_is_refused():
    with pytest.raises(NonCanonicalizableError):
        resolve_host_context(["not", "a", "mapping"])


# ---------------------------------------------------------------
# instance_label_of: the one conventional key, read only
# ---------------------------------------------------------------


def test_instance_label_extracted_when_string():
    ctx = resolve_host_context({INSTANCE_LABEL_KEY: "vfs_writer"})
    assert instance_label_of(ctx) == "vfs_writer"


def test_instance_label_none_when_absent():
    ctx = resolve_host_context({"region": "eu"})
    assert instance_label_of(ctx) is None


def test_instance_label_none_when_not_a_string():
    ctx = resolve_host_context({INSTANCE_LABEL_KEY: 42})
    assert instance_label_of(ctx) is None


def test_instance_label_of_none_context():
    assert instance_label_of(None) is None


# ---------------------------------------------------------------
# component_fingerprint_material: manifest binding (constat 17)
# ---------------------------------------------------------------


def test_none_component_is_none():
    assert component_fingerprint_material(None) is None


def test_component_without_manifest_falls_back_to_qualname():
    class PlainGate:
        pass

    material = component_fingerprint_material(PlainGate())
    # Fallback is the class qualname (a plain string), whatever the
    # enclosing scope; the point is it is the type identity, not a
    # manifest mapping.
    assert isinstance(material, str)
    assert material.endswith("PlainGate")


def test_two_plain_components_of_same_class_share_material():
    class PlainGate:
        pass

    assert component_fingerprint_material(
        PlainGate()
    ) == component_fingerprint_material(PlainGate())


def test_manifest_components_of_same_class_are_distinguished():
    class ManifestGate:
        def __init__(self, region: str) -> None:
            self.region = region

        def governance_manifest(self) -> dict:
            return {"region": self.region}

    eu = component_fingerprint_material(ManifestGate("eu"))
    us = component_fingerprint_material(ManifestGate("us"))
    assert eu != us


def test_manifest_binds_class_identity_too():
    # Two different classes with the same manifest content stay
    # distinct: the class qualname is part of the material.
    class GateA:
        def governance_manifest(self) -> dict:
            return {"k": "v"}

    class GateB:
        def governance_manifest(self) -> dict:
            return {"k": "v"}

    assert component_fingerprint_material(GateA()) != component_fingerprint_material(
        GateB()
    )


def test_manifest_provider_protocol_is_runtime_checkable():
    class Good:
        def governance_manifest(self) -> dict:
            return {}

    class Bad:
        pass

    assert isinstance(Good(), GovernanceManifestProvider)
    assert not isinstance(Bad(), GovernanceManifestProvider)


def test_non_canonicalizable_manifest_is_refused():
    class BadManifestGate:
        def governance_manifest(self) -> dict:
            def gen():
                yield 1

            return {"bad": gen()}

    with pytest.raises(NonCanonicalizableError):
        component_fingerprint_material(BadManifestGate())
