# tests/kernel_core/test_meta_syscalls_describe_self.py

from __future__ import annotations

from typing import Any

import arvis.kernel_core.syscalls  # noqa: F401  (force real syscall registration)
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall_registry import (
    SYSCALL_DESCRIPTORS,
    SyscallEffect,
    get_descriptor,
)


def _describe_self() -> SyscallResult:
    handler = SyscallHandler(runtime_state=None, scheduler=None)
    return handler.handle(Syscall(name="arvis.describe_self", args={}))


def test_describe_self_is_registered_as_read() -> None:
    descriptor = get_descriptor("arvis.describe_self")
    assert descriptor is not None
    assert descriptor.effect is SyscallEffect.READ
    assert descriptor.triggers_external is False


def test_describe_self_mirrors_the_living_registry() -> None:
    result = _describe_self()
    assert result.success is True

    model: Any = result.result
    assert model is not None
    assert model["kind"] == "arvis.self_model"
    assert model["version"] == "v0"

    names = {cap["name"] for cap in model["capabilities"]}
    # ANTI-CONFABULATION: the self-model lists exactly the registered syscalls.
    assert names == set(SYSCALL_DESCRIPTORS.keys())
    assert model["capability_count"] == len(names)
    assert "arvis.describe_self" in names  # self-referential completeness

    for cap in model["capabilities"]:
        assert set(cap.keys()) == {
            "name",
            "effect",
            "triggers_external",
            "summary",
        }
        assert cap["effect"] in ("read", "effect")
        assert isinstance(cap["triggers_external"], bool)

    assert len(model["limitations"]) >= 1


def test_describe_self_never_invents_absent_capabilities() -> None:
    result = _describe_self()
    names = {cap["name"] for cap in result.result["capabilities"]}
    assert "vfs.format_disk" not in names
    assert "memory.wipe_everything" not in names


def test_describe_self_reports_external_effects_truthfully() -> None:
    result = _describe_self()
    external = {
        cap["name"] for cap in result.result["capabilities"] if cap["triggers_external"]
    }
    # If these syscalls are registered, they must be flagged external.
    for name in ("llm.generate", "tool.execute"):
        if name in SYSCALL_DESCRIPTORS:
            assert name in external


def test_describe_self_explains_its_architecture() -> None:
    # arvis can describe HOW it works (its mathematics + governance) as
    # authored facts, and must stay explicit about what it does NOT claim.
    model = _describe_self().result
    architecture = model["architecture"]

    assert architecture["kind"] == "governed cognitive kernel"
    assert isinstance(architecture["summary"], str) and architecture["summary"]

    mechanisms = architecture["mechanisms"]
    assert len(mechanisms) >= 1
    for mechanism in mechanisms:
        assert set(mechanism.keys()) == {"name", "summary"}
        assert mechanism["name"] and mechanism["summary"]
    names = {mechanism["name"] for mechanism in mechanisms}
    assert {"contraction monitor", "anytime-valid risk bound"} <= names

    # HONESTY: the kernel discloses the boundary of its guarantee rather
    # than overclaiming a global proof or factual correctness.
    assert architecture["not_claimed"]
    not_claimed = " ".join(architecture["not_claimed"]).lower()
    assert "global lyapunov" in not_claimed
    assert "violation rate" in not_claimed
