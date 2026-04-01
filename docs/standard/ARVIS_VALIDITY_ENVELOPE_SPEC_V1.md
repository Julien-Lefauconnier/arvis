# ARVIS Validity Envelope Specification v1 (Draft)

## Status
- Version: v1 (Draft)
- Scope: Normative (Core)
- Component: ARVIS Core

---

## 1. Purpose

The Validity Envelope defines the **domain of validity** in which a cognitive decision is considered acceptable.

It represents:
- the **bounded guarantees** of the system,
- the **constraints under which the Gate operates**,
- a **partial certification object**, not a proof of global correctness.

---

## 2. Core Principles

### 2.1 Bounded Validity

Validity is always **local and conditional**.

`valid = True` means:
- constraints are satisfied within a defined domain

It does NOT mean:
- global correctness
- universal stability

---

### 2.2 Monotonic Safety

If validity is lost:
- the system MUST degrade the verdict
- no unsafe decision may occur

---

### 2.3 Explicit Semantics

All validity conditions MUST be:
- observable
- explainable
- traceable

---

## 3. Structure

```yaml
ValidityEnvelope:
  schema_version: str
  valid: bool
  reason: str | null

  projection_available: bool
  switching_safe: bool
  exponential_safe: bool
  kappa_safe: bool

  adaptive_available: bool
  adaptive_band: str | null

  certification_scope: str
  ```

---

## 4. Field Definitions

### 4.1 valid
- Type: bool
- Indicates whether the system is within its validity domain

Rules:

- False MUST force Gate → ABSTAIN
- True MUST NOT imply ALLOW

### 4.2 reason
- Type: string | null
- MUST explain invalidity if valid = False

### 4.3 projection_available
- Indicates projection availability
- MUST be consistent with ProjectionCertificate

### 4.4 switching_safe
- Indicates switching stability condition
- MUST reflect switching constraint evaluation

### 4.5 exponential_safe
- Indicates exponential stability bounds
- MUST reflect Lyapunov-based guarantees

### 4.6 kappa_safe
- Indicates compliance with kappa constraints
- MUST align with Gate inputs

### 4.7 adaptive_available
- Indicates presence of adaptive layer

### 4.8 adaptive_band
- Type: string | null
- Possible values:
    - stable
    - warning
    - critical

### 4.9 certification_scope
- Type: string
- Describes the domain under which validity applies

Examples:

- "local_linear_region"
- "bounded_disturbance"
- "projection_domain_v1"

---

## 5. Invariants

The ValidityEnvelope MUST satisfy:

- If valid = False → Gate MUST ABSTAIN
- If any critical constraint fails → valid = False
- No contradiction between fields is allowed
- reason MUST exist when invalid

---

## 6. Reason Codes Mapping

Invalidity MUST map to reason codes:

Condition	Reason Code
projection unavailable	projection_missing
switching violation	switching_violation
exponential instability	exponential_bound_violation
kappa violation	kappa_violation
adaptive unavailable	adaptive_unavailable

---

7. Certification Semantics

The ValidityEnvelope acts as:

- a partial certificate
- a runtime validation snapshot

It does NOT guarantee:

- full-system correctness
- long-term stability

---

## 8. Interaction with Gate

The Gate MUST:

- consume ValidityEnvelope
- enforce validity constraints
- propagate invalidity to verdict

---

## 9. Compliance Requirements

An implementation is Validity-compliant if:

- all fields are present
- invariants are enforced
- mapping to reason codes is consistent
- behavior matches Gate rules

---

## 10. Forbidden Practices

The system MUST NOT:

- treat validity as optional
- ignore invalid states
- silently degrade validity
- infer validity implicitly

---

## 11. Non-Claims

The ValidityEnvelope does NOT guarantee:

- global system safety
- correctness outside its domain
- completeness of constraints

---

## 12. Future Extensions (Non-Normative)

Planned:

probabilistic validity bounds
multi-domain envelopes
hierarchical validity layers