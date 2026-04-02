# ARVIS Decision Specification v1

## Status
- Version: v1
- Scope: Normative (Core Decision Layer)
- Component: ARVIS Core / Decision System

---

## 1. Purpose

The ARVIS Decision Layer defines how a cognitive execution produces a **final executable outcome**.

It extends the Gate layer into a full decision system composed of:

- Gate (admissibility)
- Confirmation (override / validation)
- Execution (action eligibility)

The Decision Layer is responsible for:

- transforming stability-constrained signals into actionable decisions
- enforcing safety constraints
- managing uncertainty and recovery
- ensuring deterministic and auditable outcomes

---

## 2. Decision Architecture

The ARVIS decision system is composed of three layers:

```text
Gate → Confirmation → Execution
```

### 2.1 Gate (Admissibility Layer)

Produces a canonical verdict:

```text
ABSTAIN > REQUIRE_CONFIRMATION > ALLOW
```

#### Role:

- enforce stability constraints
- enforce projection and validity constraints
- produce reason codes
- provide a deterministic baseline decision

---

### 2.2 Confirmation (Override Layer)

#### Handles:

- user validation
- recovery logic
- uncertainty resolution

#### Role:

- refine or override Gate verdict
- enforce explicit confirmation when required
- maintain traceability of overrides

---

### 2.3 Execution (Operational Layer)

Produces the final execution decision:

```yaml
ExecutionResult:
  can_execute: bool
  requires_confirmation: bool
  action_mode: Enum
```

#### Role:

- determine if the system can act
- enforce execution constraints
- map decision to action behavior

---

## 3. Canonical Decision Flow

The decision MUST follow a deterministic pipeline:

```text
1. Gate evaluation
2. Constraint enforcement (projection / validity / kappa / adaptive)
3. Recovery handling
4. Confirmation resolution
5. Execution mapping
6. IR projection
```

---

## 4. Decision Semantics

### 4.1 Gate Verdict Semantics

Verdict	Meaning
ALLOW	execution is permitted by constraints
REQUIRE_CONFIRMATION	execution requires explicit validation
ABSTAIN	execution is blocked

---

### 4.2 Execution Semantics

Execution is derived from the final decision state:

Gate / Confirmation	can_execute	requires_confirmation
ALLOW	True	False
REQUIRE_CONFIRMATION	False	True
ABSTAIN	False	False

---

## 5. Constraint System

The decision layer operates as a constraint system, not a rule system.

### 5.1 Core Principle

Constraints MUST:

- never allow unsafe execution
- degrade decisions when violated
- remain monotonic with respect to safety

---

### 5.2 Constraint Effects

Condition	Effect
Critical violation	ABSTAIN
Strong violation	REQUIRE_CONFIRMATION
Mild degradation	REQUIRE_CONFIRMATION
No violation	ALLOW

---

## 6. Recovery and Override

### 6.1 Recovery Detection

The system MAY detect recovery conditions:

```text
recovery_detected = True
```

This indicates:

- improving stability (ΔW < 0)
- decreasing risk
- potential safe re-entry

---

### 6.2 Recovery Rules

#### Case 1 — Valid Recovery

If:

- recovery_detected = True
- validity is True
- projection is valid

Then:

```text
final verdict MAY be promoted to ALLOV
```

#### Case 2 — Uncertain Recovery

If:

- recovery_detected = True
- but constraints are uncertain or degraded

Then:

```text
final verdict MUST be REQUIRE_CONFIRMATION
```

### Case 3 — Invalid Recovery

If:

- recovery_detected = True
- but validity or projection invalid

Then:

```text
final verdict MUST NOT be ALLOW
```

---

### 6.3 Override Requirements

All overrides MUST:

- be explicitly traceable
- emit reason codes
- be deterministic
- be replayable

---

## 7. Validity Interaction

### 7.1 Validity Rules

- validity = False → MUST NOT produce ALLOW
- validity MAY degrade to:
    - REQUIRE_CONFIRMATION
    - ABSTAIN (if critical)

---

### 7.2 Validity as Active Constraint

Validity:

- is not passive
- actively participates in decision filtering
- interacts with recovery and confirmation

---

## 8. Projection Interaction

### 8.1 Projection Rules

- projection invalid → MUST NOT produce ALLOW
- projection boundary → SHOULD produce REQUIRE_CONFIRMATION
- projection unavailable → ≤ REQUIRE_CONFIRMATION

---

### 8.2 Projection Semantics

Projection:

- informs decision
- does not decide directly
- constrains admissibility

---

## 9. Kappa and Stability Constraints

### 9.1 Kappa Violation

If:

```text
kappa_violation = True
```

Then:

```text
final verdict MUST be ABSTAIN
```

---

### 9.2 Adaptive Instability

If:

```text
adaptive_snapshot.is_unstable = True
```

Then:

```text
final verdict MUST be ABSTAIN
```

---

## 10. Confirmation Layer

### 10.1 Role

The confirmation layer determines whether:

- explicit user validation is required
- execution must be blocked pending confirmation

---

### 10.2 Confirmation Rules

- REQUIRE_CONFIRMATION → requires_confirmation = True
- ALLOW → requires_confirmation = False
- ABSTAIN → no execution possible

---

### 10.3 Conflict-Based Confirmation

If:

- conflict pressure is high
- structural risk is detected

Then:

```text
decision MAY be downgraded to REQUIRE_CONFIRMATION
```

---

## 11. Decision Trace

The system MUST produce a deterministic trace including:

```yaml
DecisionTrace:
  gate_verdict
  final_verdict
  reason_codes
  recovery_detected
  constraint_flags
```

---

## 12. Reason Codes

Reason codes MUST:

- follow the Reason Code Registry
- be deterministic
- reflect actual constraint activation

### 12.1 Recovery Codes

Examples:

- recovery_override
- uncertain_recovery

---

### 13. IR Mapping

The decision MUST be represented in IR as:

```yaml
CognitiveGateIR:
  verdict: Enum(ALLOW, REQUIRE_CONFIRMATION, ABSTAIN)
  reason_codes: list[str]
```

And execution fields:

```yaml
ExecutionIR:
  can_execute: bool
  requires_confirmation: bool
```

---

## 14. Determinism Requirements

The decision system MUST be:

- deterministic
- replayable
- traceable
- free of hidden state

---

## 15. Invariants

The system MUST guarantee:

- no unsafe execution
- no silent override
- no contradiction between layers
- consistent IR output

---

## 16. Forbidden Behaviors

The system MUST NOT:

- produce ALLOW under violated constraints
- silently override a veto
- emit inconsistent reason codes
- depend on non-deterministic signals

---

### 17. Compliance Requirements

An implementation is Decision-compliant if:

- Gate semantics are preserved
- Confirmation is explicit and traceable
- Execution mapping is correct
- recovery logic is deterministic
- all constraints are enforced
- IR output is consistent

---

## 18. Summary

The ARVIS Decision Layer transforms:

```text
stability signals → constrained decision → executable intent
```

It ensures that:

- decisions are safe
- decisions are explainable
- decisions are deterministic
- decisions are auditable

---

## One-Line Definition

ARVIS Decision Layer is a deterministic constraint-based system that transforms stability-aware signals into safe, executable outcomes.