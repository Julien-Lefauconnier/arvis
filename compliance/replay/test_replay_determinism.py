# compliance/replay/test_replay_determinism.py

from compliance.helpers import replay_from_ir, run_ctx
from compliance.scenarios.builders import build_nominal_context


def test_replay_is_deterministic():
    ctx = build_nominal_context()

    result1 = run_ctx(ctx)
    result2 = replay_from_ir(result1.cognitive_ir)

    assert result1.ir_hash == result2.ir_hash


def test_replay_global_commitment_is_deterministic():
    from arvis.api import CognitiveOS

    os = CognitiveOS()

    original = os.run(user_id="u1", cognitive_input={"text": "hello"})
    replayed = os.replay(
        original.to_ir(),
    )

    assert replayed.to_ir() == original.to_ir()
