# ARVIS Gate Specification v1 (Draft)

## Status
- Version: v1 (Draft)
- Scope: Normative (partial)
- Component: ARVIS Core

---

## 1. Purpose

The ARVIS Gate is the **central normative decision component** of the system.

Its responsibilities are to:
- Aggregate stability, validity, and projection constraints
- Produce a **canonical, traceable verdict**
- Prevent unsafe decisions within the declared domain of validity

The Gate is **not heuristic**. It is **deterministic, monotonic, and auditable**.

---

## 2. Normative Inputs

The Gate MUST receive a structured set of inputs.

### 2.1 Required Inputs

- `local_stability_metrics`
- `global_stability_metrics`
- `kappa_metrics`
- `projection_summary`
- `validity_envelope`
- `adaptive_snapshot` (if available)

### 2.2 Optional Inputs

- `disturbance_signals`
- `historical_context`
- `previous_verdict`

---

## 3. Normative Outputs

The Gate MUST produce the following structure:

```yaml
GateResult:
  verdict: Enum(ALLOW, REQUIRE_CONFIRMATION, ABSTAIN)
  reason_codes: list[str]
  decision_trace: DecisionTrace
```

---

## 4. Verdict Lattice

The Gate operates on a strict ordered lattice:

```text
ABSTAIN > REQUIRE_CONFIRMATION > ALLOW
```

Rules
- Verdicts may be downgraded, but never upgraded without explicit proof
- Any normative veto MUST propagate to the final verdict
- ALLOW is only reachable if no blocking condition exists

---

## 5. Normative Constraints

### 5.1 Projection Constraints

- If projection_available = False
  → final verdict MUST be ≤ REQUIRE_CONFIRMATION
- If projection_domain_valid = False
  → final verdict MUST be ABSTAIN
- If projection_lyapunov_compatible = False
  → final verdict MUST NOT be ALLOW

### 5.2 ValidityEnvelope Constraints

- If valid = False
  → final verdict MUST be ABSTAIN
- If kappa_safe = False
  → final verdict MUST NOT be ALLOW


### 5.3 Adaptive Constraints

- If adaptive_veto = True
  → final verdict MUST be ABSTAIN
- If adaptive_band = "critical"
  → final verdict MUST be ≤ REQUIRE_CONFIRMATION

### 5.4 Global Stability Constraints

- If global instability is confirmed
  → final verdict MUST be ABSTAIN

---

## 6. Evaluation Order (Mandatory)

The Gate MUST evaluate constraints in the following order:

1. Projection validation
2. ValidityEnvelope evaluation
3. Kappa constraints
4. Global stability
5. Adaptive constraints
6. Final fusion

Reordering is NOT allowed.

---

### 7. Fusion Rules

The final verdict MUST be computed using monotonic fusion:

```text
verdict_final = min(partial_verdicts, lattice_order)
```

Where:

- min is evaluated using the lattice ordering
- No override may violate monotonicity

---

### 8. Decision Trace (Mandatory)

Each decision MUST produce a full trace:

```yaml
DecisionTrace:
  steps:
    - stage: str
      input_snapshot: dict
      partial_verdict: Enum
      reason_codes: list[str]
```

Requirements

- Every stage affecting the verdict MUST be logged
- Every normative constraint MUST emit a reason code if triggered
- The trace MUST allow replay and audit

---

## 9. Required Properties

### 9.1 Monotonicity

The decision process MUST be monotonic:

- No unsafe upgrade is allowed
- All vetoes are final

### 9.2 Determinism

Given identical inputs, the Gate MUST produce:

- identical verdict
- identical reason codes

### 9.3 Traceability

Every decision MUST be explainable through:

- reason_codes
- decision_trace

---

## 10. Forbidden Behaviors

The Gate MUST NEVER:

- Produce ALLOW if any critical constraint is violated
- Ignore projection invalidity
- Produce a verdict without trace
- Depend on hidden or non-observable state
- Perform implicit heuristic overrides

---

### 11. Non-Claims

The Gate does NOT guarantee:

- Global stability outside its validated domain
- Completeness of projection coverage
- Mathematical proof of full-system correctness
- Correctness under missing or corrupted inputs

---

## 12. Compliance Requirements

An implementation is considered Gate-compliant if:

- All normative constraints are enforced
- The verdict lattice is respected
- Decision traces are complete and deterministic
- No forbidden behavior is observed

---

## 13. Notes for Implementers

- The Gate must remain pure and side-effect free
- Observability must be additive, never invasive
- Extensions must NOT alter normative semantics

---

## 14. Future Extensions (Non-Normative)

Planned additions include:

- Multi-agent gate coordination
- Distributed consensus gating
- Asynchronous evaluation models
- Formal verification of invariants