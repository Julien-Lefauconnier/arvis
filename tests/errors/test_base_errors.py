# tests/errors/test_error_base.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisDomainError,
    ArvisErrorCategory,
    ArvisErrorSeverity,
    ArvisExternalError,
    ArvisKernelError,
    ArvisReplayError,
    ArvisRuntimeError,
    ArvisSecurityError,
    ErrorDomain,
    ErrorPolicy,
    ErrorSemantics,
)


def test_arvis_error_metadata(runtime_error):
    metadata = runtime_error.metadata

    assert metadata.code == "TEST_ERROR"
    assert metadata.domain == ErrorDomain.CORE
    assert metadata.category == ArvisErrorCategory.RUNTIME
    assert metadata.severity == ArvisErrorSeverity.ERROR
    assert metadata.policy == ErrorPolicy.HALT_PROCESS
    assert metadata.retryable is False
    assert metadata.deterministic is True
    assert metadata.replay_safe is True
    assert metadata.degraded is False

    assert ErrorSemantics.DETERMINISTIC in metadata.semantics
    assert ErrorSemantics.REPLAY_SAFE in metadata.semantics


def test_arvis_error_to_dict(runtime_error):
    payload = runtime_error.to_dict()

    assert payload["code"] == "TEST_ERROR"
    assert payload["category"] == "runtime"
    assert payload["severity"] == "error"
    assert payload["message"] == "error"
    assert payload["type"] == type(runtime_error).__name__


def test_invariant_violation_defaults(invariant_error):
    assert invariant_error.category == ArvisErrorCategory.INVARIANT
    assert invariant_error.severity == ArvisErrorSeverity.FATAL
    assert invariant_error.replay_safe is False
    assert invariant_error.retryable is False


def test_external_error_flags(external_error):
    assert external_error.category == ArvisErrorCategory.EXTERNAL
    assert external_error.retryable is True
    assert external_error.deterministic is False
    assert external_error.replay_safe is False


def test_degraded_error_flags(degraded_error):
    assert degraded_error.category == ArvisErrorCategory.DEGRADED
    assert degraded_error.severity == ArvisErrorSeverity.WARNING
    assert degraded_error.degraded is True
    assert degraded_error.retryable is True


def test_runtime_error_category():
    error = ArvisRuntimeError("runtime")

    assert error.category == ArvisErrorCategory.RUNTIME
    assert error.policy == ErrorPolicy.HALT_PROCESS


def test_domain_error_category():
    error = ArvisDomainError("domain")

    assert error.category == ArvisErrorCategory.DOMAIN
    assert error.policy == ErrorPolicy.FAIL_CLOSED


def test_replay_error_category():
    error = ArvisReplayError("replay")

    assert error.category == ArvisErrorCategory.REPLAY
    assert error.domain == ErrorDomain.REPLAY


def test_security_error_category():
    error = ArvisSecurityError("security")

    assert error.category == ArvisErrorCategory.SECURITY
    assert error.domain == ErrorDomain.SECURITY


def test_kernel_error_category():
    error = ArvisKernelError("kernel")

    assert error.category == ArvisErrorCategory.KERNEL
    assert error.domain == ErrorDomain.KERNEL
    assert error.policy == ErrorPolicy.FAIL_CLOSED


def test_clone_preserves_runtime_flags():
    error = ArvisRuntimeError(
        "boom",
        retryable=True,
        deterministic=False,
        replay_safe=False,
        degraded=True,
        policy=ErrorPolicy.RETRY,
    )

    cloned = error.clone()

    assert cloned.retryable is True
    assert cloned.deterministic is False
    assert cloned.replay_safe is False
    assert cloned.degraded is True
    assert cloned.policy == ErrorPolicy.RETRY


def test_error_clone_can_override_replay_safe() -> None:
    error = ArvisExternalError(
        "timeout",
        replay_safe=False,
    )

    cloned = error.clone(
        replay_safe=True,
    )

    assert cloned.replay_safe is True


def test_error_clone_can_override_domain() -> None:
    error = ArvisExternalError(
        "timeout",
    )

    cloned = error.clone(
        domain=ErrorDomain.KERNEL,
    )

    assert cloned.domain == ErrorDomain.KERNEL


def test_error_clone_preserves_subclass_with_overrides() -> None:
    error = ArvisExternalError(
        "timeout",
    )

    cloned = error.clone(
        replay_safe=True,
    )

    assert isinstance(cloned, ArvisExternalError)


def test_error_clone_merges_details() -> None:
    error = ArvisExternalError(
        "timeout",
        details={
            "provider": "openai",
            "retry_count": 1,
        },
    )

    cloned = error.clone(
        details={
            "retry_count": 2,
            "region": "eu-west",
        },
    )

    assert cloned.details == {
        "provider": "openai",
        "retry_count": 2,
        "region": "eu-west",
    }
