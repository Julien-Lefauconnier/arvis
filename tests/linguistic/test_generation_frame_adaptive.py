# tests/linguistic/test_generation_frame_adaptive.py

from dataclasses import dataclass
from datetime import datetime

from arvis.conversation.act_strategy_mapper import map_strategy_to_act
from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.linguistic.acts.act_types import LinguisticActType
from arvis.linguistic.acts.linguistic_act import LinguisticAct
from arvis.linguistic.generation.frame_builder import build_generation_frame
from arvis.linguistic.generation.generation_frame import LinguisticGenerationFrame
from arvis.linguistic.lexicon.lexicon_entry import LexiconEntry
from arvis.linguistic.lexicon.lexicon_snapshot import LexiconSnapshot

# ---------------------------------------------------------
# Dummy helpers
# ---------------------------------------------------------


@dataclass
class DummyState:
    signals: dict


def make_entry(canonical: str):
    return LexiconEntry(
        entry_id=f"id_{canonical}",
        canonical_form=canonical,
        description=f"{canonical} description",
        status="preferred",
    )


def build_lexicon(entries):
    return LexiconSnapshot(
        snapshot_id="test_snapshot",
        author="test",
        created_at=datetime.utcnow(),
        scope="test",
        entries=entries,
    )


# ---------------------------------------------------------
# Strategy → Act mapping
# ---------------------------------------------------------


def test_strategy_to_act_mapping():
    act = map_strategy_to_act(ResponseStrategyType.CONFIRMATION)
    assert act.act_type == LinguisticActType.REQUEST_CONFIRMATION

    act = map_strategy_to_act(ResponseStrategyType.ACTION)
    assert act.act_type == LinguisticActType.DECISION

    act = map_strategy_to_act(ResponseStrategyType.ABSTENTION)
    assert act.act_type == LinguisticActType.ABSTENTION


# ---------------------------------------------------------
# Frame memory injection
# ---------------------------------------------------------


def test_frame_includes_memory_constraints():
    state = DummyState({"constraints": ["no_financial_advice"]})

    lexicon = build_lexicon(
        [
            make_entry("Available information"),
        ]
    )

    frame = build_generation_frame(
        act=LinguisticAct(LinguisticActType.INFORMATION),
        lexicon=lexicon,
        state=state,
    )

    assert frame.constraints is not None
    assert "no_financial_advice" in frame.constraints


def test_frame_includes_preferences():
    state = DummyState({"preferences": {"language": True}})

    lexicon = build_lexicon(
        [
            make_entry("Available information"),
        ]
    )

    frame = build_generation_frame(
        act=LinguisticAct(LinguisticActType.INFORMATION),
        lexicon=lexicon,
        state=state,
    )

    assert frame.preferences is not None
    assert frame.preferences.get("language") is True


# ---------------------------------------------------------
# Adaptive tone / verbosity
# ---------------------------------------------------------


def test_frame_adapts_to_instability():
    state = DummyState({"instability": 0.7})

    lexicon = build_lexicon(
        [
            make_entry("Available information"),
        ]
    )

    frame = build_generation_frame(
        act=LinguisticAct(LinguisticActType.INFORMATION),
        lexicon=lexicon,
        state=state,
    )

    assert frame.tone == "cautious"
    assert frame.verbosity == "low"


def test_frame_adapts_to_memory_instability():
    state = DummyState({"memory_instability": 0.7})

    lexicon = build_lexicon(
        [
            make_entry("Available information"),
        ]
    )

    frame = build_generation_frame(
        act=LinguisticAct(LinguisticActType.INFORMATION),
        lexicon=lexicon,
        state=state,
    )

    assert frame.tone == "reflective"
    assert frame.verbosity in ("medium", "minimal")


# ---------------------------------------------------------
# Canonical filtering safety
# ---------------------------------------------------------


def test_frame_filters_other_act_canonicals():
    lexicon = build_lexicon(
        [
            make_entry("Available information"),
            make_entry("Decision"),
        ]
    )

    frame = build_generation_frame(
        act=LinguisticAct(LinguisticActType.INFORMATION),
        lexicon=lexicon,
    )

    assert "Available information" in frame.allowed_entries
    assert "Decision" not in frame.allowed_entries


# ---------------------------------------------------------
# Frame invariants
# ---------------------------------------------------------


def test_frame_is_valid_dataclass():
    lexicon = build_lexicon(
        [
            make_entry("Available information"),
        ]
    )

    frame = build_generation_frame(
        act=LinguisticAct(LinguisticActType.INFORMATION),
        lexicon=lexicon,
    )

    assert isinstance(frame, LinguisticGenerationFrame)
    assert frame.act == LinguisticActType.INFORMATION
