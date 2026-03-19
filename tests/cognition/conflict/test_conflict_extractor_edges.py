# test/cognition/conflict/test_conflict_extractor_edges.py


from arvis.cognition.conflict.conflict_extractor import extract_conflicts_from_bundle


class Dummy:
    pass


def test_no_fields():
    bundle = Dummy()
    assert extract_conflicts_from_bundle(bundle) == []


def test_none_values():
    bundle = Dummy()
    bundle.decision_reason = None
    bundle.explanation = None
    assert extract_conflicts_from_bundle(bundle) == []


def test_reason_not_in_explanation():
    bundle = Dummy()
    bundle.decision_reason = "A"
    bundle.explanation = "B"
    conflicts = extract_conflicts_from_bundle(bundle)
    assert len(conflicts) == 1


def test_reason_in_explanation():
    bundle = Dummy()
    bundle.decision_reason = "A"
    bundle.explanation = "contains A inside"
    conflicts = extract_conflicts_from_bundle(bundle)
    assert conflicts == []


def test_unserializable_objects():
    class Bad:
        def __str__(self):
            raise Exception()

    bundle = Dummy()
    bundle.decision_reason = Bad()
    bundle.explanation = "test"

    # must not crash
    assert extract_conflicts_from_bundle(bundle) == []