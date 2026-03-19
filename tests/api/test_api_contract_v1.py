# tests/api/test_api_contract_v1.py


from arvis.api import CognitiveOS
from arvis.api.version import compute_api_fingerprint
from arvis.api import API_VERSION
from arvis.api import CognitiveOSConfig

def test_api_contract_shape():

    os = CognitiveOS()

    result = os.run(
        user_id="test_user",
        cognitive_input="hello"
    )

    data = result.to_dict()

    # Structure minimale garantie
    assert "version" in data
    assert "fingerprint" in data
    assert "decision" in data
    assert "stability" in data
    assert "has_trace" in data
    assert "has_timeline" in data

    assert isinstance(data["stability"], dict)


def test_api_version_locked():
    assert API_VERSION == "1.0.0"


def test_api_fingerprint_stable():

    f1 = compute_api_fingerprint()
    f2 = compute_api_fingerprint()

    assert f1 == f2
    assert isinstance(f1, str)
    assert len(f1) == 64



def test_result_view_consistency():

    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input="test"
    )

    d1 = result.to_dict()
    d2 = result.to_dict()

    assert d1 == d2


def test_summary_does_not_crash():

    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input="test"
    )

    summary = result.summary()

    assert isinstance(summary, str)


def test_timeline_optional():

    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input="test",
        timeline=None,
    )

    data = result.to_dict()

    assert "timeline" in data


def test_disable_trace_mode():

    os = CognitiveOS(config=CognitiveOSConfig(enable_trace=False))

    result = os.run(
        user_id="u1",
        cognitive_input="test"
    )

    assert isinstance(result, dict)
    assert "action" in result

