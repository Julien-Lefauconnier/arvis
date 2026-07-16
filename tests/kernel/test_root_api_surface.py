# tests/kernel/test_root_api_surface.py

import arvis


def test_root_api_is_minimal():
    assert set(arvis.__all__) == {
        "ArvisEngine",
        "AuditCommitmentPolicy",
        "CognitiveOS",
        "CognitiveOSConfig",
        # Lot B1 (F-008): deliberate extension, RuntimeMode is part of
        # the configuration-building family like AuditCommitmentPolicy.
        "RuntimeMode",
        "TrustedRuntimeControls",
    }
