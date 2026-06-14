# tests/kernel_core/test_syscall_registry_descriptors.py

from __future__ import annotations

from typing import Any

import pytest

import arvis.kernel_core.syscalls  # noqa: F401  (force real syscall registration)
from arvis.errors.kernel_runtime import DuplicateSyscallRegistrationError
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallEffect,
    all_descriptors,
    get_descriptor,
    get_syscall,
    register_syscall,
)

_PREFIX = "test.descriptors."


def _ok(handler: Any, **_: Any) -> SyscallResult:
    return SyscallResult(success=True)


def test_default_effect_classifies_reads_and_effects() -> None:
    from arvis.kernel_core.syscalls.syscall_registry import _default_effect

    for read_name in ("vfs.list", "vfs.get", "vfs.tree", "memory.snapshot"):
        assert _default_effect(read_name) is SyscallEffect.READ

    for effect_name in ("vfs.move_item", "memory.put", "process.spawn"):
        assert _default_effect(effect_name) is SyscallEffect.EFFECT


def test_default_triggers_external_for_llm_and_tool() -> None:
    from arvis.kernel_core.syscalls.syscall_registry import (
        _default_triggers_external,
    )

    assert _default_triggers_external("llm.generate") is True
    assert _default_triggers_external("tool.execute") is True
    assert _default_triggers_external("vfs.list") is False


def test_registration_populates_descriptor_with_bootstrap_default() -> None:
    name = _PREFIX + "bootstrap"

    decorated = register_syscall(name)(_ok)

    assert get_syscall(name) is decorated  # unchanged lookup behavior
    descriptor = get_descriptor(name)
    assert descriptor is not None
    assert descriptor.name == name
    assert descriptor.fn is decorated
    assert descriptor.effect is SyscallEffect.EFFECT  # unknown name -> effect
    assert descriptor.triggers_external is False
    assert descriptor.summary == ""


def test_registration_honors_explicit_metadata() -> None:
    name = _PREFIX + "explicit"

    register_syscall(
        name,
        effect=SyscallEffect.READ,
        triggers_external=True,
        summary="probe summary",
    )(_ok)

    descriptor = get_descriptor(name)
    assert descriptor is not None
    assert descriptor.effect is SyscallEffect.READ
    assert descriptor.triggers_external is True
    assert descriptor.summary == "probe summary"


def test_duplicate_registration_still_raises() -> None:
    name = _PREFIX + "dup"
    register_syscall(name)(_ok)

    with pytest.raises(DuplicateSyscallRegistrationError):
        register_syscall(name)(_ok)


def test_all_descriptors_is_sorted_by_name() -> None:
    names = [d.name for d in all_descriptors()]
    assert names == sorted(names)


def test_live_registry_is_self_describing() -> None:
    # The real syscalls registered on import must each expose a descriptor
    # whose effect class matches their structural behavior.
    expected_reads = {"vfs.list", "vfs.get", "vfs.tree", "vfs.zip.analyze"}
    expected_effects = {"vfs.create_file", "vfs.move_item", "memory.put"}

    for name in expected_reads:
        descriptor = get_descriptor(name)
        if descriptor is not None:
            assert descriptor.effect is SyscallEffect.READ

    for name in expected_effects:
        descriptor = get_descriptor(name)
        if descriptor is not None:
            assert descriptor.effect is SyscallEffect.EFFECT

    for name in ("llm.generate", "tool.execute"):
        descriptor = get_descriptor(name)
        if descriptor is not None:
            assert descriptor.triggers_external is True
