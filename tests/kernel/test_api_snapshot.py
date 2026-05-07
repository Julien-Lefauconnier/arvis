# tests/kernel/test_api_snapshot.py

import arvis.api as api

EXPECTED_API_MIN = {
    "CognitiveBundleSnapshot",
    "CognitivePolicyResult",
    "CognitiveSignalSnapshot",
    "ChangeBudget",
}


def test_api_snapshot():
    current = set(api.__all__)

    # Ensure advanced API surface remains stable
    assert EXPECTED_API_MIN.issubset(current)
