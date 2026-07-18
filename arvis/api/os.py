# arvis/api/os.py

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from arvis.adapters.tools.gates import ConsentGate, EgressGate
from arvis.api.audit import AuditCommitmentPolicy
from arvis.api.os_internals import CognitiveOSInternals
from arvis.api.runtime_controls import TrustedRuntimeControls
from arvis.api.runtime_mode import RuntimeMode, coerce_runtime_mode
from arvis.api.views.cognitive_result_view import CognitiveResultView
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel_core.syscalls.audit_sink import DurableAuditSink
from arvis.stability.stability_snapshot import StabilitySnapshot
from arvis.telemetry.adapters.stability import stability_event
from arvis.telemetry.sink import NullTelemetrySink, TelemetrySink
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


# -----------------------------------------------------
# Runtime Configuration
# -----------------------------------------------------
# F-007: frozen so the construction-time validation cannot be bypassed
# by mutating the configuration after the runtime is built.
@dataclass(frozen=True, slots=True)
class CognitiveOSConfig:
    enable_trace: bool = True
    # Strict stability profile. When True, stability bootstrap
    # invariant violations raise instead of warning. Monotone with
    # the ARVIS_STRICT_STABILITY env var: either channel can enable
    # strict mode, neither can disable the other. Applies to the
    # pipeline built by CognitiveOS; an injected pipeline keeps its
    # own setting.
    strict_mode: bool = False
    adapter_registry: dict[str, Any] | None = None
    runtime_mode: RuntimeMode | str = RuntimeMode.LOCAL
    telemetry_sink: TelemetrySink | None = None
    core_model: Any | None = None
    # F-001: host-only controls injected by composition; never read
    # from request payloads or ctx.extra. Rejected in the production
    # runtime profile.
    runtime_controls: TrustedRuntimeControls | None = None
    # F-017/F-018: host-provided tool gates. In the PRODUCTION profile a
    # tool declaring required_consent or data_egress is denied when the
    # matching gate is missing (deny-by-default); other profiles leave
    # enforcement to the host (documented fail-open).
    consent_gate: ConsentGate | None = None
    egress_gate: EgressGate | None = None
    # F-015: how a missing audit commitment is handled. Set REQUIRED
    # for profiles where runs have effects: an unauditable run must
    # not pass.
    audit_commitment_policy: AuditCommitmentPolicy = AuditCommitmentPolicy.DEGRADED
    # P1-10-a6: host registry of bound tool confirmations. When set,
    # a spec-declared confirmation requirement becomes satisfiable: the
    # manager consumes a record matching the exact invocation (tool,
    # canonical payload hash, principal, tenant; single use, optional
    # expiry) whose id travels on the trusted composition channel
    # (run(confirmation_result=...)).
    confirmation_registry: Any | None = None
    # F-008-a5: host sink for durable audit intents (outbox). When set,
    # it is called synchronously with the intent entry BEFORE any effect
    # syscall runs; a failing sink refuses the syscall (fail-closed).
    # None keeps the intent journal in-memory only (the host owns real
    # durability).
    # Campaign 6 (Lot 6): a DurableAuditSink (returning receipts) or a
    # legacy callable; profiles requiring durability refuse the latter.
    audit_intent_sink: DurableAuditSink | Callable[[dict[str, Any]], None] | None = None
    # Campaign 5 (D-1): opaque host-declared governance context. A
    # JSON-safe mapping of declarative attributes the host attaches to
    # every governed intent (the boundary instance label today, other
    # provenance tomorrow). ARVIS never interprets it beyond reading the
    # conventional `instance_label` key to stamp it; every other key is
    # transported verbatim, canonicalized injectively. None keeps
    # intents byte-identical to a run without it.
    host_context: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        # F-008: the runtime mode set is closed; unknown values are
        # refused instead of silently running with a permissive posture.
        object.__setattr__(self, "runtime_mode", coerce_runtime_mode(self.runtime_mode))
        # F-012: REQUIRED audit commitment needs the trace machinery.
        # With enable_trace=False no commitment can ever be produced, so
        # the combination is a configuration contradiction.
        if (
            not self.enable_trace
            and self.audit_commitment_policy is AuditCommitmentPolicy.REQUIRED
        ):
            raise ValueError(
                "audit_commitment_policy=REQUIRED requires enable_trace=True: "
                "without the trace no audit commitment can be produced"
            )
        # F-002/F-003/F-004-a5: production invariants hold whatever the
        # constructor. Enforced here as the single source of truth, so
        # neither direct construction nor factory overrides can weaken
        # the profile; violations fail closed at construction.
        if self.runtime_mode is RuntimeMode.PRODUCTION:
            if self.audit_commitment_policy is not AuditCommitmentPolicy.REQUIRED:
                raise ValueError(
                    "the production profile requires "
                    "audit_commitment_policy=REQUIRED: an unauditable run "
                    "must not pass (use CognitiveOSConfig.production())"
                )
            if self.runtime_controls is not None:
                raise ValueError(
                    "TrustedRuntimeControls are not permitted in the "
                    "production runtime profile"
                )

    @classmethod
    def production(cls, **overrides: Any) -> CognitiveOSConfig:
        """Closed production profile.

        Doctrine: deny-by-default is an attribute of the PRODUCTION
        profile, not of the library. The factory fixes
        runtime_mode=PRODUCTION and defaults the audit commitment
        policy to REQUIRED. Other fields can be overridden, but the
        production invariants enforced by __post_init__ cannot be
        weakened: an override that relaxes them is refused at
        construction (F-003-a5).
        """
        if "runtime_mode" in overrides:
            raise ValueError(
                "CognitiveOSConfig.production() fixes runtime_mode; "
                "use CognitiveOSConfig(...) directly for other modes"
            )
        params: dict[str, Any] = {
            "audit_commitment_policy": AuditCommitmentPolicy.REQUIRED,
        }
        params.update(overrides)
        params["runtime_mode"] = RuntimeMode.PRODUCTION
        return cls(**params)


# -----------------------------------------------------
# Public Runtime Entrypoint
# -----------------------------------------------------
class CognitiveOS(CognitiveOSInternals):
    def __init__(
        self,
        config: CognitiveOSConfig | None = None,
        *,
        pipeline: CognitivePipeline | None = None,
    ):
        self._config = config or CognitiveOSConfig()
        if (
            self.config.runtime_controls is not None
            and self.config.runtime_mode is RuntimeMode.PRODUCTION
        ):
            raise ValueError(
                "TrustedRuntimeControls are not permitted in the "
                "production runtime profile"
            )
        self.tool_registry = ToolRegistry()
        self._tool_executor = ToolExecutor(self.tool_registry)
        self.pipeline = pipeline or CognitivePipeline(
            core_model=self.config.core_model,
            strict_mode=self.config.strict_mode,
        )
        self.telemetry_sink: TelemetrySink = (
            self.config.telemetry_sink
            if self.config.telemetry_sink is not None
            else NullTelemetrySink()
        )
        self.pipeline.telemetry_sink = self.telemetry_sink
        self.runtime = self._build_runtime()

    @property
    def config(self) -> CognitiveOSConfig:
        """Effective runtime configuration (F-004-a5).

        Frozen at construction and not reassignable: the configuration
        the runtime was built with is the configuration it governs
        under, for the whole lifetime of the instance.
        """
        return self._config

    def _ensure_production_ready(self) -> None:
        """F-019: in the PRODUCTION profile the tool registry freezes
        automatically at the first run; late registration is then
        refused by the frozen registry itself."""
        if self.config.runtime_mode is not RuntimeMode.PRODUCTION:
            return
        if not self.tool_registry.frozen:
            self.tool_registry.freeze()

    # -------------------------------------------------
    # Tools API
    # -------------------------------------------------
    def register_tool(self, tool: Any) -> None:
        self.tool_registry.register(tool)

    def freeze_tools(self) -> str:
        """Freeze the tool registry after bootstrap (F-004).

        Returns the registry fingerprint for host-side pinning.
        """
        return self.tool_registry.freeze()

    def list_tools(self) -> list[str]:
        return self.tool_registry.list()

    def get_tool_spec(self, name: str) -> ToolSpec | None:
        return self.tool_registry.get_spec(name)

    def list_tool_specs(self) -> dict[str, ToolSpec]:
        return self.tool_registry.list_specs()

    # -------------------------------------------------
    # Core Execution
    # -------------------------------------------------
    def run(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> CognitiveResultView | dict[str, Any]:
        self._ensure_production_ready()
        result = self._run_single(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )
        return result

    def _emit_stability_telemetry(
        self,
        result: CognitiveResultView | dict[str, Any],
    ) -> None:
        """
        Emit a STABILITY telemetry event for a completed run.

        Observe-only and fail-safe: a misbehaving sink must never affect
        a cognitive run, and emission happens after the result (and its
        IR / commitment) are finalized, so it cannot influence
        determinism or replay. The default NullTelemetrySink makes this
        a no-op.
        """
        if isinstance(self.telemetry_sink, NullTelemetrySink):
            return
        if not isinstance(result, CognitiveResultView):
            return
        from arvis.cognition.core.cognitive_core_result import CognitiveCoreResult
        from arvis.telemetry.adapters.core import core_stability_event

        snapshot = result.stability
        if isinstance(snapshot, StabilitySnapshot):
            event = stability_event(snapshot)
        elif isinstance(snapshot, CognitiveCoreResult):
            event = core_stability_event(snapshot)
        else:
            return
        try:
            self.telemetry_sink.emit(event)
        except Exception:  # arvis-broad: observe-only telemetry sink
            return

    # -------------------------------------------------
    # IR Export
    # -------------------------------------------------
    def run_ir(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._ensure_production_ready()
        return self._build_ir_from_input(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

    # -------------------------------------------------
    # Replay
    # -------------------------------------------------
    def replay_verified(
        self,
        ir: dict[str, Any],
        *,
        expected_global_commitment: str,
    ) -> CognitiveResultView:
        """Replay an IR and AUTHENTICATE it against an external commitment.

        Campaign 5 (D-6): ``expected_global_commitment`` is MANDATORY.
        The IR is recomposed and its global commitment is checked
        against the value the caller supplies from a source OUTSIDE the
        IR (a signed record, an append-only journal, a host attestation).
        A missing or mismatched commitment raises. Replaying an IR and
        trusting the commitment it carries about itself proves nothing;
        authentication requires an external anchor. The host owns that
        anchor's durability (documented host requirement).

        This intentionally has no default: a caller with nothing to
        check against wants :meth:`replay_recomposed`, which says so.
        """
        return self._verified_replay_view(
            ir,
            expected_global_commitment=expected_global_commitment,
        )

    def replay_recomposed(
        self,
        ir: dict[str, Any],
    ) -> CognitiveResultView:
        """Recompose an IR into a view WITHOUT authenticating it.

        Campaign 5 (D-6): the recomposed view carries a freshly computed
        commitment, but nothing here proves it matches the commitment of
        the original run: no external anchor is checked. The name says
        so. Use this to inspect or rebuild an IR; use
        :meth:`replay_verified` when you have an external commitment to
        authenticate against and want a trust decision.
        """
        return self._recomposed_replay_view(ir)

    # -------------------------------------------------
    # Inspection
    # -------------------------------------------------
    def inspect(self, result: CognitiveResultView) -> dict[str, Any]:
        return {
            "summary": result.summary(),
            "trace": result.trace_view.to_dict() if result.trace_view else None,
            "stability": (
                {
                    "score": result.stability_view.stability_score,
                    "risk": result.stability_view.risk_level,
                    "regime": result.stability_view.regime,
                }
                if result.stability_view
                else None
            ),
        }

    # -------------------------------------------------
    # Multi-run
    # -------------------------------------------------
    def run_multi(
        self,
        inputs: list[Any],
        *,
        user_id: str = "multi",
    ) -> list[CognitiveResultView | dict[str, Any]]:
        self._ensure_production_ready()
        return self._run_batch(
            inputs=inputs,
            user_id=user_id,
        )

    # -------------------------------------------------
    # Properties
    # -------------------------------------------------
    @property
    def version(self) -> str:
        from arvis.api.version import PACKAGE_VERSION

        return PACKAGE_VERSION
