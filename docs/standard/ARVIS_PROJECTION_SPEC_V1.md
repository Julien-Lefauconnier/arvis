# ARVIS Projection Specification v1 (Draft)

## Status
- Version: v0.1 (Draft)
- Scope: Normative (Projection Layer)
- Component: ARVIS Projection Layer

---

## 1. Purpose

The Projection Layer defines how raw runtime observations are transformed into a **validated, bounded, and certifiable representation** usable by the Gate.

Projection is the **interface between observation and decision**.

It determines:
- whether the system operates within a valid domain,
- whether stability assumptions hold,
- whether the Gate can safely evaluate a decision.

---

## 2. Core Principles

### 2.1 Projection is a Certification Step

Projection MUST:
- validate domain assumptions,
- produce a structured certificate,
- expose all uncertainty explicitly.

Projection is NOT:
- a simple transformation,
- a hidden heuristic,
- a silent approximation.

---

### 2.2 Domain-Bounded Validity

Projection is only valid within a defined domain:

O_valid ⊂ Observation Space

Outside this domain:
- projection MUST be marked invalid
- the Gate MUST NOT produce ALLOW
- the system MUST degrade to REQUIRE_CONFIRMATION or ABSTAIN

---

### 2.3 Explicit Uncertainty

Projection MUST explicitly expose:

- domain validity,
- safety,
- compatibility with stability constraints,
- proximity to domain boundaries.

---

### 2.4 Separation from Decision

Projection MUST NOT:
- produce a verdict,
- apply decision logic,
- override Gate behavior.

Projection only **informs**, never **decides**.

---

## 3. ProjectionCertificate Structure

Projection MUST produce a `ProjectionCertificate` object:

```yaml
ProjectionCertificate:
  schema_version: str
  available: bool

  domain_valid: bool | null
  is_projection_safe: bool | null
  lyapunov_compatibility_ok: bool | null

  margin_to_boundary: float | null

  certification_level: str
  projection_domain: str | null

  proof_status: str
  warning_codes: list[str]
```

## 3.1 Projection Representation in IR

In ARVIS Core v1, the `projection` field in the Cognitive IR MUST represent the ProjectionCertificate.

No separate wrapper is required.

Therefore:

- `ir.projection` MUST be a ProjectionCertificate-compliant object
- no implicit transformation is allowed between projection and certificate
- the projection object MUST be directly serializable

---

## 4. Field Definitions

### 4.1 available

- Indicates whether projection is available
- If False:
    - all other fields MUST be null
    - Gate MUST degrade verdict (≤ REQUIRE_CONFIRMATION)

### 4.2 domain_valid
- Indicates whether the observation lies inside O_valid

Rules:
- False → Gate MUST ABSTAIN
- True → does NOT guarantee safety

### 4.3 is_projection_safe
- Indicates whether the projected state is safe for evaluation
- MUST reflect projection-level constraints

### 4.4 lyapunov_compatibility_ok
- Indicates compatibility with stability assumptions
- MUST align with Gate stability inputs

Rules:
- False → Gate MUST NOT ALLOW

### 4.5 margin_to_boundary
- Distance to domain boundary
- Used for early warning and degradation

Rules:
- Small margin SHOULD trigger warning_codes
- Zero or negative margin → domain_valid = False

### 4.6 certification_level

Allowed values:

- NONE
- BASIC
- CHECKED
- CERTIFIED
- RESTRICTED_DOMAIN

Semantics:

Level	Meaning
NONE	no projection available
BASIC	minimal projection
CHECKED	constraints verified
CERTIFIED	domain validated
RESTRICTED_DOMAIN	valid only in limited domain

### 4.7 projection_domain
Describes the domain where projection is valid

Examples:
- "local_linear_region"
- "bounded_disturbance"
- "projection_domain_v1"

### 4.8 proof_status

Allowed values:

- none
- partial
- validated
- formal

This field describes the level of formal validation.

### 4.9 warning_codes
- MUST follow Reason Code Registry
- MUST NOT directly affect verdict
- MUST reflect non-critical conditions

Examples:
- projection_boundary
- projection_low_margin

---

## 5. Projection Semantics

Projection MUST provide:

- domain membership (domain_valid)
- safety assessment (is_projection_safe)
- stability compatibility (lyapunov_compatibility_ok)

Projection MUST NOT:

- extrapolate silently outside domain
- hide invalid states
- merge multiple interpretations into one output

---

## 6. Interaction with Gate

The Gate MUST:

- consume projection_summary
- enforce projection constraints
- map projection failures to reason codes
- propagate invalidity to verdict

Examples:
- Condition	Gate Behavior
- projection_available = False	≤ REQUIRE_CONFIRMATION
- domain_valid = False	ABSTAIN
- lyapunov_compatibility_ok = False	no ALLOW

### Additional Gate Constraints

The Gate MUST enforce:

- is_projection_safe = False → verdict ≠ ALLOW
- domain_valid = False → verdict = ABSTAIN
- available = False → verdict ≤ REQUIRE_CONFIRMATION

---

## 7 Projection in IR (Normative Requirement)

Projection MUST be included in the Cognitive IR.

It MUST be:

- preserved through normalization,
- included in serialization,
- included in hashing,
- replayable without loss of information.

Projection omission is a compliance failure.

---

## 8. Interaction with ValidityEnvelope

Projection MUST be consistent with ValidityEnvelope:

- projection_available MUST match
- domain violations MUST propagate to validity
- no contradiction allowed

---

## 9. Invariants

The ProjectionCertificate MUST satisfy:

- If available = False → all other fields are null
- If domain_valid = False → margin_to_boundary ≤ 0 or null
- No contradictory flags allowed
- All warning_codes MUST be valid registry codes

---

## 10. Compliance Requirements

An implementation is Projection-compliant if:

- ProjectionCertificate is valid and complete
- domain validity is enforced
- invariants are respected
- Gate behavior matches projection output
- no silent fallback occurs

---

## 11. Forbidden Practices

The system MUST NOT:

- claim projection availability without validation
- omit domain invalidity
- overstate certification level
- mix projection and decision logic
- suppress projection errors

---

## 12. Non-Claims

Projection does NOT guarantee:

- full-system correctness
- global validity
- perfect representation of observation space
- absence of modeling error

Projection guarantees only:

- bounded validity within declared domain
- explicit uncertainty exposure

---

## 13. Future Extensions (Non-Normative)

Planned extensions:

- multi-domain projection support
- probabilistic projection confidence
- formal proof integration
- cross-agent projection consistency