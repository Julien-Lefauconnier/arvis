# tests/kernel/test_root_api_surface.py

import arvis


def test_root_api_is_minimal():
    assert set(arvis.__all__) == {
        "ArvisEngine",
        "AuditCommitmentPolicy",
        "CognitiveOS",
        "CognitiveOSConfig",
        # a15 lot 2 (A14-BETA-02): the central result type and its typed
        # status are part of the promised surface; both are frozen field
        # by field in the beta contract manifest.
        "CognitiveResultView",
        "DecisionStatus",
        # Lot B1 (F-008): deliberate extension, RuntimeMode is part of
        # the configuration-building family like AuditCommitmentPolicy.
        "RuntimeMode",
        "TrustedRuntimeControls",
    }
