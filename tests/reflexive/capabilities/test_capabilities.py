# tests/reflexive/capabilities/test_capabilities.py

def test_import_capabilities_modules():
    pass


def test_capability_registry_instantiation():
    from arvis.reflexive.capabilities.capability_registry import CapabilityRegistry

    registry = CapabilityRegistry()
    assert registry is not None