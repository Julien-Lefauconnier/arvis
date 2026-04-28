# tests/api/test_engine.py

from arvis import ArvisEngine, CognitiveOS


def test_engine_boots():
    engine = ArvisEngine()
    assert isinstance(engine.os, CognitiveOS)


def test_engine_run_method_exists():
    engine = ArvisEngine()
    assert callable(engine.run)


def test_engine_replay_method_exists():
    engine = ArvisEngine()
    assert callable(engine.replay)


def test_engine_ask_method_exists():
    engine = ArvisEngine()
    assert callable(engine.ask)


def test_root_import():
    import arvis

    assert hasattr(arvis, "ArvisEngine")


def __repr__(self):
    return "ArvisEngine(core=CognitiveOS)"
