# compliance/blackbox/test_blackbox_contract.py

"""Normative black-box compliance suite (audit a13, P1-01).

This suite exercises the installed package through its public surface
only: ``arvis`` top-level exports and ``arvis.host_api``. It imports no
internal module, no test fixture, no repository file: it is designed to
run against the built wheel in a pristine environment
(``scripts/run_blackbox_against_wheel.sh``), where the repository is not
importable at all.

When the environment variable ``BLACKBOX_REQUIRE_WHEEL=1`` is set, the
suite refuses to run against a source checkout: the arvis it imports
must come from an installed distribution. Without the variable, the
suite also runs in the normal repository gate, as a plain part of the
compliance tree.

Scenario tables are versioned: changing them is changing what ARVIS
promises a host, and must be deliberate.
"""

import os
from types import SimpleNamespace

import pytest

import arvis
import arvis.host_api
from arvis import ArvisEngine, DecisionStatus

BLACKBOX_SCENARIOS_VERSION = 1

# Declared-risk gradation: the documented three-band policy of the
# 0.1.0-beta gate (README quick start, examples 01/06/09).
RISK_SCENARIOS: tuple[tuple[float, DecisionStatus], ...] = (
    (0.10, DecisionStatus.ALLOWED),
    (0.50, DecisionStatus.REQUIRES_CONFIRMATION),
    (0.90, DecisionStatus.BLOCKED),
)

NON_FINITE_RISKS = (
    pytest.param(float("nan"), id="nan"),
    pytest.param(float("inf"), id="positive-infinity"),
    pytest.param(float("-inf"), id="negative-infinity"),
)

# The host integration surface, as promised (NOTE_DECISION 2026-07-24).
# Deliberately duplicated from the repository contract test: this suite
# must stay self-contained, since the repository is absent when running
# against the wheel.
# Counts at HOST_API_VERSION 1.1 (campaign SURFACE, DM-S2: engine,
# access and tools grew additively).
HOST_API_MODULES: dict[str, int] = {
    "engine": 7,
    "access": 3,
    "services": 3,
    "vfs": 9,
    "tools": 8,
    "memory": 12,
    "knowledge": 4,
    "conversation": 3,
    "cognition": 1,
    "control": 5,
    "llm": 1,
    "telemetry": 2,
}


def test_runs_against_an_installed_distribution_when_required() -> None:
    if os.environ.get("BLACKBOX_REQUIRE_WHEEL") != "1":
        pytest.skip("wheel provenance check only enforced by the wheel runner")
    assert "site-packages" in (arvis.__file__ or ""), (
        "BLACKBOX_REQUIRE_WHEEL=1 but arvis was imported from a source "
        f"checkout: {arvis.__file__}"
    )


def test_reflexive_attestation_verifies_from_the_wheel() -> None:
    """b1 (audit a17, 13.4): the exact artifact carries the corrected
    verification: the final payload verifies through the root API, and
    a forged attestation field fails."""
    import copy

    from arvis import CognitiveOS, verify_reflexive_attestation

    payload = CognitiveOS().run(user_id="blackbox", cognitive_input="test").reflexive
    assert payload is not None
    assert verify_reflexive_attestation(payload) is True

    forged = copy.deepcopy(payload)
    forged["attestation"]["authority"] = "user"
    assert verify_reflexive_attestation(forged) is False


def test_unknown_canonicalization_version_is_refused_from_the_wheel() -> None:
    import copy

    from arvis import CognitiveOS, verify_reflexive_attestation

    payload = CognitiveOS().run(user_id="blackbox", cognitive_input="test").reflexive
    assert payload is not None
    stale = copy.deepcopy(payload)
    stale["attestation"]["canon_version"] = "1.0"
    assert verify_reflexive_attestation(stale) is False


def test_no_trace_result_conforms_to_the_shipped_schema() -> None:
    """a17 (audit a16, blocker 1): the public no-trace path used to
    emit a payload the shipped schema rejected; the wheel must prove
    every public result path conforms, this one included."""
    import jsonschema

    from arvis import CognitiveOS, CognitiveOSConfig, load_result_schema

    payload = (
        CognitiveOS(CognitiveOSConfig(enable_trace=False))
        .run("blackbox", "hello")
        .to_dict()
    )
    jsonschema.Draft202012Validator(load_result_schema()).validate(payload)
    assert payload["commitment_reason"] == "trace_disabled"


def test_serialized_result_conforms_to_the_shipped_schema() -> None:
    """A15-BETA-01: the consumer contract is validated from the
    installed package: the schema a consumer loads from the wheel
    accepts the payload the same wheel produces."""
    import jsonschema

    from arvis import RESULT_SCHEMA_VERSION, load_result_schema

    schema = load_result_schema()
    payload = ArvisEngine().run("blackbox", {"risk": 0.10}).to_dict()
    jsonschema.Draft202012Validator(schema).validate(payload)
    assert payload["schema_version"] == RESULT_SCHEMA_VERSION


@pytest.mark.parametrize(("risk", "expected"), RISK_SCENARIOS)
def test_declared_risk_gradation(risk: float, expected: DecisionStatus) -> None:
    """The public verdict is result.status, typed: no consumer, and no
    compliance scenario, derives it from the repr of an internal object
    anymore (audit a14, A14-BETA-02)."""
    engine = ArvisEngine()
    result = engine.run("blackbox", {"risk": risk})
    assert result.status is expected
    assert result.to_dict()["decision"]["status"] == expected.value


@pytest.mark.parametrize("risk", NON_FINITE_RISKS)
def test_non_finite_declared_risk_fails_closed_from_the_wheel(
    risk: float,
) -> None:
    """b2: malformed public risk values never become an ALLOWED decision,
    and the installed artifact still emits strict JSON and a verifiable
    reflexive payload."""
    import json

    from arvis import verify_reflexive_attestation

    result = ArvisEngine().run("blackbox", {"risk": risk})
    assert result.status is DecisionStatus.BLOCKED
    assert result.to_ir()["input"]["metadata"]["risk"] is None
    json.loads(result.to_json())
    assert result.reflexive is not None
    assert verify_reflexive_attestation(result.reflexive) is True


def test_run_view_carries_a_commitment_and_an_ir() -> None:
    engine = ArvisEngine()
    view = engine.run("blackbox", {"risk": 0.10})
    assert view.global_commitment
    exported = view.to_ir()
    assert isinstance(exported, dict) and exported


def test_replay_authenticates_against_the_run_commitment() -> None:
    engine = ArvisEngine()
    view = engine.run("blackbox", {"risk": 0.10})

    replayed = engine.replay_verified(
        view.to_ir(),
        expected_global_commitment=view.global_commitment,
    )
    assert replayed.global_commitment == view.global_commitment


def test_replay_refuses_a_wrong_external_commitment() -> None:
    engine = ArvisEngine()
    view = engine.run("blackbox", {"risk": 0.10})
    with pytest.raises(RuntimeError):
        engine.replay_verified(
            view.to_ir(),
            expected_global_commitment="0" * 64,
        )


def test_tool_surface_freezes_to_a_stable_fingerprint() -> None:
    engine = ArvisEngine()
    pinned = engine.freeze_tools()
    assert isinstance(pinned, str) and len(pinned) == 64
    assert engine.freeze_tools() == pinned
    assert engine.list_tools() == []


def test_host_api_surface_resolves_as_promised() -> None:
    import importlib

    assert arvis.host_api.HOST_API_VERSION == "1.1"
    assert arvis.host_api.PROVISIONAL_MODULES == frozenset({"control"})

    total = 0
    for module_name, expected_count in HOST_API_MODULES.items():
        module = importlib.import_module(f"arvis.host_api.{module_name}")
        exported = list(module.__all__)
        assert len(exported) == expected_count, (
            f"host_api.{module_name} promises {expected_count} symbols, "
            f"exposes {len(exported)}"
        )
        for symbol in exported:
            assert hasattr(module, symbol)
        total += len(exported)
    assert total == 58


def test_vfsitem_b2_positional_constructor_from_the_wheel() -> None:
    """b3/A-01: the additive scope field does not shift the b2 constructor."""
    from arvis.host_api.vfs import VFSItem

    item = VFSItem(
        "id-1",
        "probe.txt",
        "file",
        None,
        "alice",
        "acme",
        "text/plain",
        123,
        456,
    )

    assert item.mime == "text/plain"
    assert item.file_size == 123
    assert item.created_at == 456
    assert item.resource_scope is None


class _BlackboxScopedVFS:
    """Minimal host service built only from public host-api types."""

    def get_item(self, *, user_id: str, item_id: str):
        from arvis.host_api.vfs import VFSItem

        return VFSItem(
            item_id=item_id,
            display_name="matter.txt",
            item_type="file",
            parent_id=None,
            owner_id="alice",
            organization_id="acme",
            resource_scope="scope:A",
        )


@pytest.mark.parametrize(
    ("grants", "allowed"),
    [
        (frozenset({"read", "scope:A"}), True),
        (frozenset({"read"}), False),
        (frozenset({"read", "scope:B"}), False),
    ],
)
def test_vfs_scope_authorization_from_the_wheel(
    grants: frozenset[str],
    allowed: bool,
) -> None:
    """b3: organization, capability and exact scope are cumulative."""
    from arvis.host_api.access import OrganizationScopedAuthorization, Principal
    from arvis.host_api.services import KernelServiceRegistry, Syscall, SyscallHandler

    services = KernelServiceRegistry(
        vfs_service=_BlackboxScopedVFS(),
        authorization_service=OrganizationScopedAuthorization(),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    ctx = SimpleNamespace(
        extra={},
        principal=Principal(
            user_id="bob",
            organization_id="acme",
            grants=grants,
        ),
    )

    result = handler.handle(
        Syscall(name="vfs.get", args={"ctx": ctx, "user_id": "bob", "item_id": "i1"})
    )

    assert result.success is allowed
    if not allowed:
        assert result.error is not None
        assert result.error.details.get("reason_code") == "access_denied"


class _BlackboxExpectedFailureThenForeignVFS:
    """Expected first failure followed by a foreign resource on a second read."""

    def __init__(self) -> None:
        self.calls = 0
        self.deleted = False

    def get_item(self, *, user_id: str, item_id: str):
        from arvis.host_api.vfs import VFSItem, VFSItemNotFoundError

        self.calls += 1
        if self.calls == 1:
            raise VFSItemNotFoundError(f"item not found: {item_id}")
        return VFSItem(
            item_id=item_id,
            display_name="secret.txt",
            item_type="file",
            parent_id=None,
            owner_id="someone_else",
            organization_id="acme",
            resource_scope="scope:A",
        )

    def delete_item(self, *, user_id: str, item_id: str) -> None:
        self.deleted = True


def test_vfs_expected_lookup_failure_never_reaches_a_second_lookup_from_the_wheel() -> (
    None
):
    """b4 single-read: an expected first failure (not-found) must never reach a
    second body lookup that a live store could answer with a FOREIGN resource.

    Under single-read the resolver captures the expected exception and the body
    maps it WITHOUT re-reading, so the second (foreign) read never happens:
    ``calls == 1`` and no resource is returned. The precise code is
    vfs_item_not_found (finesse restored: fail-closed is not fail-opaque), not
    an opaque authorization_failure. The security property is the absence of a
    second lookup and of any returned resource, exactly what closes the TOCTOU
    an absorbed expected failure would otherwise reopen (counter-audit
    B3-VFS-01). Anti-enumeration is preserved by the denied case, not by erasing
    not-found."""
    from arvis.host_api.access import OrganizationScopedAuthorization, Principal
    from arvis.host_api.services import KernelServiceRegistry, Syscall, SyscallHandler

    vfs = _BlackboxExpectedFailureThenForeignVFS()
    services = KernelServiceRegistry(
        vfs_service=vfs,
        authorization_service=OrganizationScopedAuthorization(),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    ctx = SimpleNamespace(extra={}, principal=Principal(user_id="bob"))

    result = handler.handle(
        Syscall(name="vfs.get", args={"ctx": ctx, "user_id": "bob", "item_id": "i1"})
    )

    assert result.success is False, "a resource was returned after a not-found"
    assert vfs.calls == 1, "the body performed a second lookup, reopening the TOCTOU"
    assert result.result is None, "a foreign resource leaked through the retry"
    assert result.error is not None
    assert result.error.code == "vfs_item_not_found"


def test_vfs_expected_lookup_failure_never_reaches_an_effect_from_the_wheel() -> None:
    """b4 effect handoff: a captured not-found is mapped without dispatching
    the VFS mutation, even if the live service would act on the identifier."""
    from arvis.host_api.access import OrganizationScopedAuthorization, Principal
    from arvis.host_api.services import KernelServiceRegistry, Syscall, SyscallHandler

    vfs = _BlackboxExpectedFailureThenForeignVFS()
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            vfs_service=vfs,
            authorization_service=OrganizationScopedAuthorization(),
        ),
    )
    ctx = SimpleNamespace(extra={}, principal=Principal(user_id="bob"))

    result = handler.handle(
        Syscall(
            name="vfs.delete_item",
            args={"ctx": ctx, "user_id": "bob", "item_id": "i1"},
        )
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "vfs_item_not_found"
    assert vfs.calls == 1
    assert vfs.deleted is False
