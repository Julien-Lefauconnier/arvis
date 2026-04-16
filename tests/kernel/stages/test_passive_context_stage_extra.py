# tests/kernel/stages/test_passive_context_stage_extra.py


from arvis.kernel.pipeline.stages.passive_context_stage import PassiveContextStage


# ============================================================
# Helpers
# ============================================================

class DummyCtx:
    pass


class DummyPipeline:
    pass


class DummyGovernance:
    def evaluate(self, decision):
        return {"ok": True}


class BrokenGovernance:
    def evaluate(self, decision):
        raise ValueError


class DummyCoherenceObserver:
    def observe(self, ctx):
        class Snap:
            change_count = 3
            max_change_budget = 10
        return Snap()


class DummyCoherencePolicy:
    def evaluate(self, snapshot, budget):
        return {"policy": "ok"}


class BrokenCoherencePolicy:
    def evaluate(self, *a, **k):
        raise ValueError


class DummyConversationState:
    def __init__(self):
        self.turn_count = 5
        self.momentum = 0.7


class DummyConversationContext:
    def __init__(self):
        self.proposed_strategy = "test"
        self.state = DummyConversationState()


# ============================================================
# 1. FULL HAPPY PATH
# ============================================================

def test_full_passive_context():
    ctx = DummyCtx()
    ctx.decision_result = {}
    ctx.conversation_context = DummyConversationContext()

    pipeline = DummyPipeline()
    pipeline.governance = DummyGovernance()
    pipeline.coherence_observer = DummyCoherenceObserver()
    pipeline.coherence_policy = DummyCoherencePolicy()

    PassiveContextStage().run(pipeline, ctx)

    assert ctx.governance == {"ok": True}
    assert ctx.pending_actions == []
    assert ctx.events == []
    assert isinstance(ctx.coherence_policy, list)
    assert ctx.coherence_policy[0]["policy"] == "ok"

    assert ctx.conversation_signal is not None
    assert ctx.extra["conversation_turn"] == 5
    assert ctx.extra["conversation_momentum"] == 0.7


# ============================================================
# 2. GOVERNANCE ABSENT
# ============================================================

def test_governance_absent():
    ctx = DummyCtx()
    ctx.decision_result = {}

    pipeline = DummyPipeline()

    PassiveContextStage().run(pipeline, ctx)

    assert ctx.governance is None


# ============================================================
# 3. GOVERNANCE EXCEPTION
# ============================================================

def test_governance_exception():
    ctx = DummyCtx()
    ctx.decision_result = {}

    pipeline = DummyPipeline()
    pipeline.governance = BrokenGovernance()

    PassiveContextStage().run(pipeline, ctx)

    assert ctx.governance is None


# ============================================================
# 4. PENDING EXCEPTION
# ============================================================

def test_pending_exception():
    ctx = DummyCtx()

    # force attribute error
    def broken_setattr(*a, **k):
        raise ValueError

    ctx.__setattr__ = broken_setattr  # hack

    pipeline = DummyPipeline()

    # should not crash
    PassiveContextStage().run(pipeline, ctx)


# ============================================================
# 5. EVENTS EXCEPTION
# ============================================================

def test_events_exception():
    ctx = DummyCtx()

    def broken_setattr(*a, **k):
        raise ValueError

    ctx.__setattr__ = broken_setattr

    pipeline = DummyPipeline()

    PassiveContextStage().run(pipeline, ctx)


# ============================================================
# 6. COHERENCE WITHOUT OBSERVER
# ============================================================

def test_coherence_no_observer():
    ctx = DummyCtx()

    pipeline = DummyPipeline()
    pipeline.coherence_policy = DummyCoherencePolicy()

    PassiveContextStage().run(pipeline, ctx)

    assert ctx.coherence_policy == [{"policy": "ok"}]


# ============================================================
# 7. COHERENCE POLICY EXCEPTION
# ============================================================

def test_coherence_policy_exception():
    ctx = DummyCtx()

    pipeline = DummyPipeline()
    pipeline.coherence_observer = DummyCoherenceObserver()
    pipeline.coherence_policy = BrokenCoherencePolicy()

    PassiveContextStage().run(pipeline, ctx)

    assert ctx.coherence_policy is None


# ============================================================
# 8. NO CONVERSATION CONTEXT
# ============================================================

def test_no_conversation_context():
    ctx = DummyCtx()

    pipeline = DummyPipeline()

    PassiveContextStage().run(pipeline, ctx)

    assert not hasattr(ctx, "conversation_signal")


# ============================================================
# 9. CONVERSATION WITH PARTIAL STATE
# ============================================================

def test_conversation_partial_state():
    class PartialState:
        pass

    class PartialContext:
        proposed_strategy = "test"
        state = PartialState()

    ctx = DummyCtx()
    ctx.conversation_context = PartialContext()

    pipeline = DummyPipeline()

    PassiveContextStage().run(pipeline, ctx)

    assert ctx.conversation_signal.turn_count == 0
    assert ctx.conversation_signal.momentum == 0.0


# ============================================================
# 10. EXTRA AUTO-CREATION
# ============================================================

def test_extra_auto_created():
    ctx = DummyCtx()
    ctx.extra = None

    pipeline = DummyPipeline()

    PassiveContextStage().run(pipeline, ctx)

    assert isinstance(ctx.extra, dict)


# ============================================================
# 11. SNAPSHOT INJECTION
# ============================================================

def test_memory_snapshot_injection():
    ctx = DummyCtx()
    ctx.memory_snapshot = {"records": ["a"]}

    pipeline = DummyPipeline()

    PassiveContextStage().run(pipeline, ctx)

    assert ctx.memory_snapshot["records"] == ["a"]

# ============================================================
# 12. PROJECTION FALLBACK
# ============================================================

def test_memory_projection_from_long_memory():
    ctx = DummyCtx()
    ctx.long_memory = {"preferences": {"lang": "fr"}}

    pipeline = DummyPipeline()

    PassiveContextStage().run(pipeline, ctx)

    assert ctx.memory_projection["preferences"]["lang"] == "fr"


# ============================================================
# 13. PROJECTION PRIORITY
# ============================================================

def test_memory_projection_priority():
    ctx = DummyCtx()
    ctx.memory_projection = {"p": 1}
    ctx.long_memory = {"p": 2}

    pipeline = DummyPipeline()

    PassiveContextStage().run(pipeline, ctx)

    assert ctx.memory_projection["p"] == 1

# ============================================================
# 14. SNAPSHOT PRIORITY
# ============================================================

def test_memory_snapshot_priority_over_projection():
    ctx = DummyCtx()
    ctx.memory_snapshot = {"records": ["snap"]}
    ctx.memory_projection = {"records": ["proj"]}

    pipeline = DummyPipeline()

    PassiveContextStage().run(pipeline, ctx)

    assert ctx.memory_snapshot["records"] == ["snap"]