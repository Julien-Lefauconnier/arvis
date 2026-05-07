# tests/kernel/test_root_api_surface.py

import arvis


def test_root_api_is_minimal():
    assert set(arvis.__all__) == {
        "ArvisEngine",
        "CognitiveOS",
        "CognitiveOSConfig",
    }
