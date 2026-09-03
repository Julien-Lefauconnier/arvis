# arvis/api/os.py

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from arvis.adapters.tools.gates import ConsentGate, EgressGate
from arvis.api.audit import AuditCommitmentPolicy
from arvis.api.commitment import (
    config_fingerprint,
    policies_fingerprint,
    syscall_journal_digest,
)
from arvis.api.ir import build_ir_view
from arvis.api.runtime.cognitive_runtime import CognitiveRuntime
from arvis.api.runtime_controls import TrustedRuntimeControls
from arvis.api.runtime_mode import RuntimeMode, coerce_runtime_mode
from arvis.api.views.cognitive_result_view import CognitiveResultView
from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.ir.cognitive_ir import CognitiveIR
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
    apply_runtime_postures,
)
from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.replay_engine import ReplayEngine
from arvis.kernel_core.access.models import AuthenticatedPrincipal
from arvis.kernel_core.host_declaration import resolve_host_context
from arvis.kernel_core.syscalls.audit_sink import DurableAuditSink
from arvis.kernel_core.syscalls.intent_result_bijection import (
    verify_intent_result_bijection,
)
from arvis.math.core.contraction_monitor_core import ContractionMonitorCore
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
    # Campaign MATH-A (M1, decision DM2): the default engine measures
    # its own science. The contraction monitor is the default core
    # model, so every governed run carries a measured Lyapunov state,
    # energy, drift, PAC risk ceiling and regime instead of constructor
    # zeros. An explicit ``core_model=None`` remains the documented
    # opt-out (measure nothing); a host may inject its own calibrated
    # monitor, as the reference host integration does. The monitor
    # measures the COGNITION only: a caller-declared risk scalar stays
    # governed by the input-risk gate and never feeds the measured axes
    # (decision DM1).
    core_model: Any | None = field(default_factory=ContractionMonitorCore)
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
class CognitiveOS:
    """The governed runtime: one instance runs ONE cognitive turn.

    The host constructs an instance (optionally with a
    CognitiveOSConfig), registers and freezes its tool surface, and
    calls :meth:`run` once; parallelism and cross-turn continuity
    belong to the host by instantiation (one engine per governed
    turn). Every verdict composes a hashed commitment binding the
    tool registry, the effective configuration, the active policy
    tables and the redacted effect journals (F-007), so what ran is
    what can be proven. :class:`ArvisEngine` is the recommended
    facade; this class is the runtime it delegates to.
    """

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
        """Register a tool (a BaseTool with a ToolSpec manifest).

        Bootstrap-time only: after :meth:`freeze_tools` (or the first
        run in the PRODUCTION profile, F-019) registration is
        refused by the frozen registry.
        """
        self.tool_registry.register(tool)

    def freeze_tools(self) -> str:
        """Freeze the tool registry after bootstrap (F-004).

        Returns the registry fingerprint for host-side pinning.
        """
        return self.tool_registry.freeze()

    def list_tools(self) -> list[str]:
        """Names of the registered tools, in registry order."""
        return self.tool_registry.list()

    def get_tool_spec(self, name: str) -> ToolSpec | None:
        """Defensive copy of one tool's declared manifest, or None."""
        return self.tool_registry.get_spec(name)

    def list_tool_specs(self) -> dict[str, ToolSpec]:
        """Defensive copies of every declared manifest, by name."""
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
    ) -> CognitiveResultView:
        """Govern one turn and return its full result view.

        ``cognitive_input`` follows the documented input contracts: a
        dict carrying an explicit ``risk`` float rides the graded
        three-band policy, and a bare string is governed with a
        minimal projection (conservative by construction; see
        docs/PATH_TO_ALLOW.md). Thread the previous turn's
        ``view.next_scientific_state`` back in through
        ``extra={"scientific_state": ...}`` to make the trajectory
        measurable (DM-S4). The view carries the verdict
        (``status``), the stability assessment, the exported IR and
        the composed ``global_commitment``.
        """
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

    def run_as(
        self,
        principal: AuthenticatedPrincipal,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> CognitiveResultView:
        """Run with a host-authenticated identity on the trusted channel.

        ARVIS validates the explicit stamp and derives the turn owner from it;
        the host remains responsible for authenticating the session or service.
        """
        if type(principal) is not AuthenticatedPrincipal:
            raise TypeError("principal must be an exact AuthenticatedPrincipal")
        self._ensure_production_ready()
        return self._run_single(
            user_id=principal.user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
            principal=principal,
        )

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
        """Govern one turn and return only the exported canonical IR.

        Same contract as :meth:`run`; the return value is the
        portable, replayable record (docs/IR.md) rather than the
        full result view.
        """
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
        """One dict with a result's summary, trace, stability and IR.

        A convenience for operators and debuggers; every field is
        also reachable directly on the view.
        """
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
    # Properties
    # -------------------------------------------------
    @property
    def version(self) -> str:
        from arvis.api.version import PACKAGE_VERSION

        return PACKAGE_VERSION

    # -------------------------------------------------
    # Internals (merged from api/os_internals, campaign STRUCT LOT S3)
    # -------------------------------------------------
    def _build_context(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
        principal: AuthenticatedPrincipal | None = None,
    ) -> CognitivePipelineContext:
        ctx = CognitivePipelineContext(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline or [],
            confirmation_result=confirmation_result,
            extra=extra if extra is not None else {},
        )
        if principal is not None:
            ctx.principal = principal

        runtime_policy = ctx.runtime_policy

        # F-001: host controls come from composition (config), never
        # from the request-facing extra channel.
        controls = getattr(self.config, "runtime_controls", None)
        if controls is not None:
            runtime_policy.force_tool = controls.force_tool
            runtime_policy.force_execution = controls.force_execution
            ctx.gate_overrides = GateOverrides(
                force_safe_projection=controls.force_safe_projection,
                force_safe_switching=controls.force_safe_switching,
            )
        # Postures are applied through the shared helper so the replay
        # context builder reproduces the exact same block from the
        # recorded profile (D-a; single source of truth).
        apply_runtime_postures(ctx, coerce_runtime_mode(self.config.runtime_mode).value)

        runtime_policy.retry_requested = bool(ctx.extra.get("retry_tool", False))
        runtime_policy.retry_count = int(ctx.extra.get("tool_retry_count", 0) or 0)

        return ctx

    def _execute(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
        principal: AuthenticatedPrincipal | None = None,
    ) -> tuple[CognitiveState | None, Any]:
        execution = self.runtime.execute(
            self._build_context(
                user_id=user_id,
                cognitive_input=cognitive_input,
                conversation_context=conversation_context,
                timeline=timeline,
                confirmation_result=confirmation_result,
                extra=extra,
                principal=principal,
            )
        )
        return execution.state, execution.result

    def _build_runtime(self) -> CognitiveRuntime:
        return CognitiveRuntime(
            pipeline=self.pipeline,
            adapters=self.config.adapter_registry,
            tool_executor=self._tool_executor,
            # One registry: the runtime and its tool manager govern the
            # same tool surface the host registered on (previously the
            # runtime built its own empty registry and the policy was
            # evaluated against it).
            tool_registry=self.tool_registry,
            consent_gate=self.config.consent_gate,
            egress_gate=self.config.egress_gate,
            # F-017/F-018: deny-by-default gates in the PRODUCTION profile.
            require_gates=self.config.runtime_mode is RuntimeMode.PRODUCTION,
            audit_intent_sink=self.config.audit_intent_sink,
            confirmation_registry=self.config.confirmation_registry,
            # D4-e: effectful production requires a durable sink; the
            # refusal happens at the first effect, not at boot, so a
            # production profile without effects stays valid.
            require_durable_intent_sink=(
                self.config.runtime_mode is RuntimeMode.PRODUCTION
            ),
            require_authenticated_principal=(
                self.config.runtime_mode is RuntimeMode.PRODUCTION
            ),
            # Campaign 5 (D-1): opaque host-declared governance context,
            # resolved (canonical) and threaded to the kernel service
            # registry; the conventional instance label is stamped on
            # every governed intent.
            host_context=resolve_host_context(self.config.host_context),
        )

    def _format_run_output(
        self,
        state: CognitiveState | None,
        result: Any,
    ) -> CognitiveResultView:
        """Single public return type (beta contract, BETA-02).

        Trace mode builds the full view. The legacy no-trace mode and
        the fake-executor fallback return a minimal view carrying the
        decision only: with enable_trace=False no trace and no
        commitment can exist, and the view says so by construction.
        """
        if not self.config.enable_trace:
            return self._minimal_result_view(
                result, self.config.audit_commitment_policy
            )

        # trace mode normal
        if state is not None:
            return self._build_trace_result(state, result)

        # fallback fake executors/tests
        return self._minimal_result_view(result, self.config.audit_commitment_policy)

    @staticmethod
    def _minimal_result_view(
        result: Any, policy: AuditCommitmentPolicy
    ) -> CognitiveResultView:
        """Minimal no-trace view, in contract (audit a16, blocker 1).

        With enable_trace=False no commitment can exist; the view says
        so explicitly instead of falling back to out-of-contract
        defaults: it carries the policy actually configured, the reason
        trace_disabled, and the F-015 degradation semantics (REQUIRED
        is already rejected at config construction; DEGRADED marks the
        absence, OPTIONAL tolerates it).
        """
        return CognitiveResultView(
            decision=getattr(result, "action_decision", None),
            stability=None,
            stability_view=None,
            trace=None,
            commitment_policy=policy.value,
            commitment_reason="trace_disabled",
            commitment_degraded=policy is AuditCommitmentPolicy.DEGRADED,
        )

    def _run_single(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
        principal: AuthenticatedPrincipal | None = None,
    ) -> CognitiveResultView:
        state, result = self._execute(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
            principal=principal,
        )
        return self._format_run_output(state, result)

    def _export_ir(
        self,
        state: CognitiveState,
    ) -> dict[str, Any]:
        return build_ir_view(state)

    def _build_ir_from_input(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state, result = self._execute(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )
        exported = self._export_ir(
            self._require_state(
                state,
                message=(
                    "IR export requires a CognitiveState, but execution returned none."
                ),
            ),
        )
        # D-a: run_ir carries the same commitment_inputs block as the
        # result view export (public contract: run_ir == to_ir).
        inputs, _unavailable_reason = self._build_commitment_inputs(result)
        if inputs is not None and isinstance(exported, dict):
            exported = {**exported, "commitment_inputs": inputs}
        return exported

    def _replay_ir(
        self,
        ir: dict[str, Any],
    ) -> Any:
        parsed = CognitiveIR.from_dict(ir)
        engine = ReplayEngine()
        return engine.replay_ir(
            parsed,
            pipeline=self.pipeline,
        )

    def _replay_view(
        self,
        ir: dict[str, Any],
    ) -> CognitiveResultView:
        result = self._replay_ir(ir)
        state = getattr(result, "cognitive_state", None)

        typed_state = self._require_state(
            state,
            message="Replay result missing cognitive_state",
        )

        # D-a: on replay the non-cognitive components are reused
        # verbatim from the exported IR, never recomputed from the
        # replayer's environment. A divergent environment stays
        # detectable by comparing the declared block to the local one.
        declared = ir.get("commitment_inputs")
        return CognitiveResultView.from_state(
            typed_state,
            result,
            commitment_policy=self._commitment_policy(),
            commitment_inputs=declared if isinstance(declared, dict) else None,
        )

    def _verify_replay_view(
        self,
        replay_view: CognitiveResultView,
        *,
        expected_global_commitment: str,
    ) -> CognitiveResultView:
        self._verify_replay_commitment(
            replay_view,
            expected_global_commitment,
        )
        return replay_view

    def _verified_replay_view(
        self,
        ir: dict[str, Any],
        *,
        expected_global_commitment: str,
    ) -> CognitiveResultView:
        return self._verify_replay_view(
            self._replay_view(ir),
            expected_global_commitment=expected_global_commitment,
        )

    def _recomposed_replay_view(
        self,
        ir: dict[str, Any],
    ) -> CognitiveResultView:
        """Recompose without authentication (D-6, explicitly unverified)."""
        return self._replay_view(ir)

    def _verify_replay_commitment(
        self,
        replay_view: CognitiveResultView,
        expected_global_commitment: str,
    ) -> None:
        # Campaign 5 (D-6): the expected commitment is mandatory and
        # must come from OUTSIDE the IR. There is no early return: a
        # caller reaching here has asked for authentication, so a
        # missing external anchor or a missing replay commitment is a
        # verification failure, never a silent pass.
        if not expected_global_commitment:
            raise RuntimeError(
                "Replay verification failed: no expected_global_commitment "
                "supplied. Authentication requires an external anchor; use "
                "replay_recomposed() to recompose without authenticating."
            )

        replay_commitment = replay_view.global_commitment

        if replay_commitment is None:
            raise RuntimeError(
                "Replay verification failed: replay global_commitment is missing"
            )

        if replay_commitment != expected_global_commitment:
            raise RuntimeError(
                "Replay verification failed: global_commitment mismatch "
                f"(expected={expected_global_commitment}, "
                f"got={replay_commitment})"
            )

    def _build_trace_result(
        self,
        state: CognitiveState | None,
        result: Any,
    ) -> CognitiveResultView:
        typed_state = self._require_state(
            state,
            message=(
                "Trace mode requires a CognitiveState, but execution "
                "returned none. Use enable_trace=False for fake "
                "executors/tests, or ensure the pipeline builds "
                "the run's cognitive state."
            ),
        )

        inputs, unavailable_reason = self._build_commitment_inputs(result)
        return CognitiveResultView.from_state(
            typed_state,
            result,
            commitment_policy=self._commitment_policy(),
            commitment_inputs=inputs,
            commitment_inputs_reason=unavailable_reason,
        )

    def _build_commitment_inputs(
        self, result: Any
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Non-cognitive commitment components, from the live environment.

        F-007-a5: registry manifest fingerprint, effective config
        fingerprint, active policy tables, and the digest of the
        redacted syscall journals (intents and results).

        P0-1-a6 (decision D4-c): the intent/result bijection is
        verified here, where the journals are read, before any
        composition. An effect intent without its journaled result, or
        an execution marked audit-incomplete by the handler, yields no
        commitment with the dedicated reason "audit_incomplete": the
        effect happened, and arvis refuses to pretend it proved it.

        Returns (inputs, unavailable_reason); (None, None) when a
        component cannot be produced for any other cause. The
        commitment machinery records the absence (REQUIRED refuses,
        DEGRADED flags), never a partially bound commitment.
        """
        try:
            execution = getattr(result, "execution", result)
            execution_state = getattr(execution, "execution_state", None)
            # An ABSENT journal is not an EMPTY one (campaign KERNEL,
            # LOT K2). Coercing a missing attribute to [] made an
            # unreadable journal satisfy the strict D-5 bijection
            # vacuously, so a run that proved nothing was committed as
            # if it had. A present-and-empty journal stays legitimate:
            # most turns invoke no effect syscall at all.
            if execution_state is not None:
                intents = getattr(execution_state, "syscall_intents", None)
                results = getattr(execution_state, "syscall_results", None)
                if not isinstance(intents, list) or not isinstance(results, list):
                    return None, "audit_incomplete"
            else:
                intents = []
                results = []

            metadata = getattr(execution_state, "metadata", None)
            if isinstance(metadata, dict) and metadata.get("audit_incomplete"):
                return None, "audit_incomplete"

            # D-5: strict one-to-one intent/result bijection. The a7
            # membership check missed duplicate intents, orphan results
            # and syscall mismatches; the dedicated verifier requires an
            # exact correspondence and fails closed on any deviation.
            bijection = verify_intent_result_bijection(intents, results)
            if not bijection.ok:
                return None, "audit_incomplete"

            return {
                "registry_fingerprint": self.tool_registry.fingerprint(),
                "config_fingerprint": config_fingerprint(self.config),
                "policies_fingerprint": policies_fingerprint(),
                "syscall_journal_sha256": syscall_journal_digest(intents, results),
            }, None
        except Exception:  # arvis-broad: commitment absence is governed
            return None, None

    def _commitment_policy(self) -> AuditCommitmentPolicy:
        policy = getattr(self.config, "audit_commitment_policy", None)
        if isinstance(policy, AuditCommitmentPolicy):
            return policy
        return AuditCommitmentPolicy.DEGRADED

    def _require_state(
        self,
        state: CognitiveState | None,
        *,
        message: str = (
            "IR export requires a CognitiveState, but execution returned none."
        ),
    ) -> CognitiveState:
        if state is None:
            raise RuntimeError(message)
        return state
