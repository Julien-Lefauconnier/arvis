# tests/action/test_action_resolver.py

from arvis.action.action_resolver import resolve_action
from arvis.action.action_template import ActionTemplate


class DummyDecision:
    reason = "test"


def test_resolver_returns_template():
    decision = DummyDecision()

    template = resolve_action(decision)

    assert isinstance(template, ActionTemplate)
    assert template.action_id is not None


def test_resolver_is_deterministic():
    decision = DummyDecision()

    t1 = resolve_action(decision)
    t2 = resolve_action(decision)

    assert t1 == t2


def test_resolver_default_is_safe():
    decision = DummyDecision()

    template = resolve_action(decision)

    assert template.reads_data is True
    assert template.writes_data is False
    assert template.triggers_external is False