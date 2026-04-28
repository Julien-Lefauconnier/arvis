# tests/runtime/test_process_hooks.py
from dataclasses import dataclass

from arvis.api.os import CognitiveOS, CognitiveOSConfig

# =====================================================
# HELPERS
# =====================================================


@dataclass
class DummyResult:
    can_execute: bool = True
    requires_confirmation: bool = False
    action_decision: object | None = None


@dataclass
class DummyOutcome:
    completed: bool
    result: object
    consumption: object
    stage_name: str = "test"


class DummyConsumption:
    reasoning_steps = 0
    attention_tokens = 0
    uncertainty_spent = 0.0
    elapsed_ms = 0
    memory_span_used = 0

    def validate(self) -> None:
        return None


class FakeExecutorComplete:
    def execute_process(self, process):
        return DummyOutcome(
            completed=True,
            result=DummyResult(),
            consumption=DummyConsumption(),
        )


class FakeExecutorBlocked:
    def execute_process(self, process):
        return DummyOutcome(
            completed=True,
            result=DummyResult(can_execute=False),
            consumption=DummyConsumption(),
        )


class FakeExecutorConfirmation:
    def execute_process(self, process):
        return DummyOutcome(
            completed=True,
            result=DummyResult(requires_confirmation=True),
            consumption=DummyConsumption(),
        )


def _make_os_with_fake_executor(executor) -> CognitiveOS:
    """
    With fake executors we bypass the real pipeline finalization path,
    so trace rendering must be disabled to avoid requiring ctx.cognitive_state.
    """
    os = CognitiveOS(config=CognitiveOSConfig(enable_trace=False))
    os.runtime.scheduler.process_executor = executor
    return os


def _signal_code(entry) -> str | None:
    """
    CanonicalSignal code may live on entry.key.code instead of entry.code.
    """
    direct = getattr(entry, "code", None)
    if isinstance(direct, str):
        return direct

    key = getattr(entry, "key", None)
    key_code = getattr(key, "code", None)
    if isinstance(key_code, str):
        return key_code

    return None


# =====================================================
# TESTS
# =====================================================


def test_hook_called_on_selected():
    calls = {"count": 0}

    class Hook:
        def on_process_enqueued(self, process):
            pass

        def on_process_selected(self, process, score):
            calls["count"] = 1

        def on_process_completed(self, process, result):
            pass

        def on_process_aborted(self, process, error):
            pass

        def on_process_blocked(self, process, reason):
            pass

        def on_process_suspended(self, process, reason):
            pass

        def on_process_waiting_confirmation(self, process):
            pass

    os = _make_os_with_fake_executor(FakeExecutorComplete())
    os.runtime.hooks.register(Hook())

    result = os.run(user_id="u1", cognitive_input={})

    assert result is not None
    assert calls["count"] >= 1


def test_hook_called_on_completed():
    calls = {"count": 0}

    class Hook:
        def on_process_enqueued(self, process):
            pass

        def on_process_selected(self, process, score):
            pass

        def on_process_completed(self, process, result):
            calls["count"] = 1

        def on_process_aborted(self, process, error):
            pass

        def on_process_blocked(self, process, reason):
            pass

        def on_process_suspended(self, process, reason):
            pass

        def on_process_waiting_confirmation(self, process):
            pass

    os = _make_os_with_fake_executor(FakeExecutorComplete())
    os.runtime.hooks.register(Hook())

    result = os.run(user_id="u1", cognitive_input={})

    assert result is not None
    assert calls["count"] == 1


def test_hook_called_on_blocked():
    class Hook:
        def __init__(self):
            self.called = False

        def on_process_enqueued(self, process):
            pass

        def on_process_selected(self, process, score):
            pass

        def on_process_completed(self, process, result):
            pass

        def on_process_aborted(self, process, error):
            pass

        def on_process_blocked(self, process, reason):
            self.called = True

        def on_process_suspended(self, process, reason):
            pass

        def on_process_waiting_confirmation(self, process):
            pass

    os = _make_os_with_fake_executor(FakeExecutorBlocked())
    hook = Hook()
    os.runtime.hooks.register(hook)

    result = os.run(user_id="u1", cognitive_input={})

    assert result is not None
    assert hook.called is True


def test_hook_called_on_waiting_confirmation():
    class Hook:
        def __init__(self):
            self.called = False

        def on_process_enqueued(self, process):
            pass

        def on_process_selected(self, process, score):
            pass

        def on_process_completed(self, process, result):
            pass

        def on_process_aborted(self, process, error):
            pass

        def on_process_blocked(self, process, reason):
            pass

        def on_process_suspended(self, process, reason):
            pass

        def on_process_waiting_confirmation(self, process):
            self.called = True

    os = _make_os_with_fake_executor(FakeExecutorConfirmation())
    hook = Hook()
    os.runtime.hooks.register(hook)

    result = os.run(user_id="u1", cognitive_input={})

    assert result is not None
    assert hook.called is True


def test_hook_failure_is_isolated():
    class BadHook:
        def on_process_enqueued(self, process):
            pass

        def on_process_selected(self, process, score):
            pass

        def on_process_completed(self, process, result):
            raise Exception("boom")

        def on_process_aborted(self, process, error):
            pass

        def on_process_blocked(self, process, reason):
            pass

        def on_process_suspended(self, process, reason):
            pass

        def on_process_waiting_confirmation(self, process):
            pass

    os = _make_os_with_fake_executor(FakeExecutorComplete())
    os.runtime.hooks.register(BadHook())

    result = os.run(user_id="u1", cognitive_input={})

    assert result is not None


def test_hook_error_event_emitted():
    class BadHook:
        def on_process_enqueued(self, process):
            pass

        def on_process_selected(self, process, score):
            pass

        def on_process_completed(self, process, result):
            raise Exception("boom")

        def on_process_aborted(self, process, error):
            pass

        def on_process_blocked(self, process, reason):
            pass

        def on_process_suspended(self, process, reason):
            pass

        def on_process_waiting_confirmation(self, process):
            pass

    os = _make_os_with_fake_executor(FakeExecutorComplete())
    os.runtime.hooks.register(BadHook())

    os.run(user_id="u1", cognitive_input={})

    timeline = os.runtime.runtime_state.timeline
    snapshot = list(timeline._signals)

    found = any(_signal_code(entry) == "ghost_signal" for entry in snapshot)

    assert found is True


def test_no_hooks_safe():
    os = _make_os_with_fake_executor(FakeExecutorComplete())

    result = os.run(user_id="u1", cognitive_input={})

    assert result is not None


def test_hook_manager_is_bound_to_runtime_state():
    os = CognitiveOS(config=CognitiveOSConfig(enable_trace=False))

    assert os.runtime.hooks.runtime_state is os.runtime.runtime_state
