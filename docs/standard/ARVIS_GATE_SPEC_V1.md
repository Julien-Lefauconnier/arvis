# ARVIS Gate Specification v1

## Status
- Version: v1
- Scope: Normative (Core)
- Component: ARVIS Core / Gate Layer

---

## 1. Purpose

The ARVIS Gate is the canonical decision layer responsible for producing a
deterministic cognitive verdict from stability, projection, validity,
adaptive, and policy constraints.

Its responsibilities are to:

- aggregate gate-relevant constraints from the pipeline,
- produce a canonical verdict,
- expose normalized reason codes,
- emit a deterministic decision trace,
- remain auditable and replay-compatible.

The Gate is normative at the verdict level.
Observability extensions are allowed only if they remain deterministic and do
not modify verdict semantics.

---

## 2. Canonical Verdict Space

The Gate MUST operate on the following ordered verdict lattice:

```text
ABSTAIN > REQUIRE_CONFIRMATION > ALLOW
```

### Interpretation:

- ALLOW → execution is gate-permitted
- REQUIRE_CONFIRMATION → execution is not autonomous and requires explicit confirmation
- ABSTAIN → execution is blocked at gate level

### Rules:

- A stricter verdict dominates a weaker verdict.
- Unsafe silent promotion is forbidden.
- Any explicit promotion MUST be externally justified, traceable, and exposed in context.

---

## 3. Normative Inputs

The Gate MUST evaluate structured pipeline artifacts.

### 3.1 Required canonical inputs

An implementation MUST evaluate, when available:

- local gate verdict inputs,
- projection certificate state,
- validity envelope state,
- stability state and/or global stability metrics,
- adaptive snapshot state,
- switching safety state,
- normalized conflict / policy signals relevant to the verdict.

### 3.2 Implementation-aligned input families

In the current ARVIS v1 implementation, the Gate is aligned around the following families:

- projection_certificate
- validity_envelope
- adaptive_snapshot
- global_stability_metrics / stability_projection
- switching_safe
- delta_w, w_prev, w_current
- gate policy / overrides
- confirmation outcome (post-gate override layer)

### 3.3 Optional inputs

Implementations MAY additionally use:

- disturbance summaries,
- historical traces,
- prior verdict context,
- observability summaries,

provided that:

- determinism is preserved,
- verdict semantics remain unchanged,
- the behavior remains replay-compatible.

---

### 4. Normative Output

The Gate MUST produce a canonical result equivalent to:

```yaml
GateResult:
  verdict: Enum(ALLOW, REQUIRE_CONFIRMATION, ABSTAIN)
  reason_codes: list[str]
  decision_trace: GateDecisionTrace | null
```

The canonical gate result MUST be representable by the public Gate IR.

### 4.1 Public IR alignment

The final exposed Gate representation MUST remain consistent with:

- CognitiveGateResult
- CognitiveGateIR

including:

- normalized verdict,
- normalized reason codes,
- deterministic trace projection.

---

## 5. Normative Constraints

### 5.1 Projection constraints

- If projection domain validity is false, final verdict MUST be ABSTAIN.
- If projection and Lyapunov compatibility is false, final verdict MUST NOT be ALLOW.
- If projection boundary safety is degraded, the verdict MAY be downgraded to REQUIRE_CONFIRMATION.
- Projection observability MUST NOT silently override stronger vetoes.

### 5.2 Validity constraints
- If the validity envelope is invalid, final verdict MUST NOT remain ALLOW.
- If validity indicates a critical violation, final verdict MUST be downgraded at least to REQUIRE_CONFIRMATION, and MAY be ABSTAIN depending on implementation policy.
- Kappa-unsafety exposed through validity or hard veto layers MUST NOT coexist with final ALLOW.

### 5.3 Adaptive constraints
- If adaptive instability is detected, final verdict MUST be ABSTAIN.
- If adaptive band is critical or margin is in warning range, final verdict MUST NOT remain silently permissive.
- Adaptive vetoes MUST emit deterministic reason codes.

### 5.4 Global stability constraints

- Global instability MUST affect the final verdict.
- A global instability policy MAY downgrade to REQUIRE_CONFIRMATION or ABSTAIN, but MUST do so explicitly and traceably.
- Global policy behavior MUST remain deterministic.

### 5.5 Confirmation constraints
- Confirmation is a distinct post-gate decision layer.
- A confirmed override MAY promote a previously blocked verdict.
- Such promotion MUST be explicit, traceable, and propagated into canonical IR context.
- A rejected confirmation MUST result in ABSTAIN.

---

6. Evaluation Model

The Gate MUST be evaluated as an ordered deterministic process.

In ARVIS v1, the implementation-aligned evaluation flow is:

1. local gate evaluation,
2. fusion of gate-relevant signals,
2. validity enforcement,
4. projection enforcement,
5. kappa / hard veto enforcement,
6. final adaptive veto,
7. global stability policy application,
8. confirmation override layer,
9. normalization of reason codes,
10. deterministic trace projection.

Equivalent implementations are allowed, provided that:

- the final verdict is deterministic,
- all effective vetoes are preserved,
- confirmation overrides remain explicit and auditable.

---

## 7. Fusion Rules

Fusion MUST be monotonic with respect to the verdict lattice, except for explicit confirmation override.

### Rules:

- stricter partial verdicts dominate weaker ones,
- veto signals MUST propagate,
- fusion MUST NOT erase active veto semantics,
- confirmation override MUST be modeled as an explicit post-fusion override and not as an implicit fusion side effect.

---

## 8. Decision Trace

Every final gate decision MUST expose a deterministic decision trace.

### 8.1 Normative minimum

A trace step MUST support at least:

```yaml
GateDecisionTraceStep:
  stage: str
  reason_codes: list[str]
```

A full gate trace MUST support:

```yaml
GateDecisionTrace:
  steps: list[GateDecisionTraceStep]
```

### 8.2 Implementation-aligned extended trace

ARVIS v1 currently supports an extended deterministic trace model including:

- before
- after
- severity
- stability_impact

and aggregate observability metrics such as:

- total_severity
- max_severity
- instability_score

These fields are allowed as public deterministic extensions.

### 8.3 Trace requirements

The trace MUST:

- be deterministic,
- preserve verdict-relevant transitions,
- expose every effective downgrade or override,
- remain compatible with replay and audit,
- not depend on hidden runtime-only state.

---

## 9. Reason Codes

Reason codes are normative.

Requirements:

- MUST be non-empty on exposed gate output,
- MUST be normalized before IR exposure,
- MUST be deterministic,
- MUST remain consistent with the final verdict,
- MUST not contain contradictory active veto codes under final ALLOW, except when explicitly justified by a confirmation override mechanism propagated in context.

---

## 10. Required Properties

### 10.1 Determinism

Identical effective inputs MUST produce:

- identical verdict,
- identical normalized reason codes,
- identical trace projection.

### 10.2 Monotonic safety

Unsafe silent upgrades are forbidden.

### 10.3 Traceability

Every final verdict MUST be explainable through:

- reason codes,
- decision trace,
- explicit override context where applicable.

### 10.4 Replay compatibility

Gate output MUST remain compatible with canonical IR replay.

---

## 11. Forbidden Behaviors

The Gate MUST NOT:

- produce ALLOW while silently ignoring critical veto signals,
- expose contradictory verdict and reason code semantics,
- mutate reason codes non-deterministically,
- produce a verdict without traceable justification,
- depend on hidden non-replayable state,
- perform implicit override without explicit context propagation.

---

## 12. Compliance Requirements

An implementation is Gate-compliant if:

- the verdict lattice is respected,
- critical vetoes are enforced,
- reason codes are normalized,
- trace output is deterministic,
- confirmation overrides are explicit and auditable,
- exposed Gate IR remains consistent with final gate semantics.

---

## 13. Notes for Implementers

- The Gate SHOULD remain pure at the semantic level.
- Observability extensions are allowed only as additive deterministic layers.
- Confirmation override MUST remain separated from silent fusion.
- Public IR MUST reflect the final effective semantics of the gate.

---

## 14. Non-Claims

The Gate does NOT guarantee:

- full-system correctness,
- correctness outside the validated domain,
- completeness of upstream observability,
- correctness under corrupted or missing upstream artifacts.

---

## 15. Future Extensions (Non-Normative)

Possible future extensions include:

- richer policy-aware gate semantics,
- distributed or multi-agent gate coordination,
- stronger formal replay contracts,
- formally verified veto composition.