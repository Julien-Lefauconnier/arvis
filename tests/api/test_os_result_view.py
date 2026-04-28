# tests/api/test_os_result_view.py

from arvis.api.os import CognitiveResultView


def test_result_view_to_dict():
    view = CognitiveResultView(
        decision="test",
        stability=None,
        stability_view=None,
        trace=None,
        timeline=None,
    )

    d = view.to_dict()

    assert "decision" in d
    assert "stability" in d
