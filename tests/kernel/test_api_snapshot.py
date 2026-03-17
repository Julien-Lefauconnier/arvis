# tests/kernel/test_api_snapshot.py

import arvis


EXPECTED_API_MIN = {
    "CognitiveBundleSnapshot",
    "CognitivePolicyResult",
    "CognitiveSignalSnapshot",
    "ChangeBudget",
}


def test_api_snapshot():

    current = set(arvis.__all__)

    # Ensure critical API surface remains stable
    assert EXPECTED_API_MIN.issubset(current)