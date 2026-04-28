# tests/api/test_engine_standard.py

from arvis import ArvisEngine


def test_engine_repr():
    engine = ArvisEngine()
    assert "ArvisEngine" in repr(engine)


def test_engine_has_config():
    engine = ArvisEngine()
    assert engine.config.runtime_mode == "local"


def test_engine_list_tools():
    engine = ArvisEngine()
    assert isinstance(engine.list_tools(), list)
