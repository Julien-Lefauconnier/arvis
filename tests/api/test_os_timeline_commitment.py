# tests/api/test_os_timeline_commitment.py


def test_timeline_commitment_present_and_valid():
    from arvis.api import CognitiveOS

    os = CognitiveOS()

    result = os.run(user_id="u1", cognitive_input={})

    assert result.timeline_commitment is not None
    assert isinstance(result.timeline_commitment, str)
    assert len(result.timeline_commitment) == 64  # sha256 hex


def test_timeline_commitment_deterministic():
    from arvis.api import CognitiveOS

    os = CognitiveOS()

    r1 = os.run(user_id="u1", cognitive_input={"text": "hello"})
    r2 = os.run(user_id="u1", cognitive_input={"text": "hello"})

    assert r1.timeline_commitment == r2.timeline_commitment


def test_commitment_changes_with_different_runtime_events():
    from arvis.adapters.kernel.timeline_from_signals import (
        signal_journal_to_timeline_snapshot,
    )
    from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
    from arvis.timeline.timeline_commitment import TimelineCommitment

    state = CognitiveRuntimeState()
    state.append_event("process_enqueued", {"process_id": "p1"})
    state.append_event("process_aborted", {"process_id": "p1"})

    snap1 = signal_journal_to_timeline_snapshot(state.timeline)
    commit1 = TimelineCommitment.from_snapshot(snap1).commitment

    state2 = CognitiveRuntimeState()
    state2.append_event("process_enqueued", {"process_id": "p1"})

    snap2 = signal_journal_to_timeline_snapshot(state2.timeline)
    commit2 = TimelineCommitment.from_snapshot(snap2).commitment

    assert commit1 != commit2


def test_commitment_matches_timeline_snapshot():
    from arvis.api import CognitiveOS
    from arvis.timeline.timeline_commitment import TimelineCommitment

    os = CognitiveOS()

    result = os.run(user_id="u1", cognitive_input={})
    snapshot = result.timeline

    commitment = TimelineCommitment.from_snapshot(snapshot)

    assert commitment.commitment == result.timeline_commitment


def test_commitment_exposed_in_dict():
    from arvis.api import CognitiveOS

    os = CognitiveOS()

    result = os.run(user_id="u1", cognitive_input={})
    data = result.to_dict()

    assert "timeline_commitment" in data
    assert data["timeline_commitment"] == result.timeline_commitment


def test_no_timeline_safe_fallback():
    from arvis.api.os import CognitiveResultView

    view = CognitiveResultView(
        decision=None,
        stability=None,
        stability_view=None,
        trace=None,
        timeline=None,
        timeline_view=None,
        timeline_commitment=None,
    )

    d = view.to_dict()

    assert d["timeline_commitment"] is None


def test_commitment_failure_does_not_crash(monkeypatch):
    from arvis.api import CognitiveOS

    def broken_commitment(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "arvis.timeline.timeline_commitment.TimelineCommitment.from_snapshot",
        broken_commitment,
    )

    os = CognitiveOS()

    result = os.run(user_id="u1", cognitive_input={})

    assert result.timeline_commitment is None


def test_commitment_stable_across_runs_same_order():
    from arvis.api import CognitiveOS

    os = CognitiveOS()

    commits = [
        os.run(user_id="u1", cognitive_input={"i": i}).timeline_commitment
        for i in range(3)
    ]

    commits2 = [
        os.run(user_id="u1", cognitive_input={"i": i}).timeline_commitment
        for i in range(3)
    ]

    assert commits == commits2


def test_commitment_does_not_break_api_contract():
    from arvis.api import CognitiveOS

    os = CognitiveOS()

    result = os.run(user_id="u1", cognitive_input={})
    data = result.to_dict()

    assert "decision" in data
    assert "timeline" in data
    assert "trace" in data
    assert "timeline_commitment" in data


def test_no_trace_mode_no_commitment():
    from arvis.api import CognitiveOS

    os = CognitiveOS()
    os.config.enable_trace = False

    result = os.run(user_id="u1", cognitive_input={})

    assert isinstance(result, dict)


def test_global_commitment_present():
    from arvis.api import CognitiveOS

    os = CognitiveOS()
    result = os.run(user_id="u1", cognitive_input={})

    assert result.global_commitment is not None
    assert len(result.global_commitment) == 64


def test_global_commitment_deterministic():
    from arvis.api import CognitiveOS

    os = CognitiveOS()

    r1 = os.run(user_id="u1", cognitive_input={"text": "hello"})
    r2 = os.run(user_id="u1", cognitive_input={"text": "hello"})

    assert r1.global_commitment == r2.global_commitment


def test_global_commitment_changes_with_input():
    from arvis.api import CognitiveOS

    os = CognitiveOS()

    r1 = os.run(user_id="u1", cognitive_input={"text": "hello"})
    r2 = os.run(user_id="u1", cognitive_input={"text": "different"})

    assert r1.global_commitment != r2.global_commitment


def test_global_commitment_recomputable():
    import json
    from hashlib import sha256

    from arvis.api import CognitiveOS

    os = CognitiveOS()

    result = os.run(user_id="u1", cognitive_input={})

    ir = result.to_ir()

    ir_bytes = json.dumps(
        ir,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()

    ir_hash = sha256(ir_bytes).hexdigest()

    recomputed = sha256((result.timeline_commitment + ir_hash).encode()).hexdigest()

    assert recomputed == result.global_commitment
