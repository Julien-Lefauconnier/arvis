# ARVIS Intermediate Representation Specification v1 (Draft)

## Status
- Version: v1 (Draft)
- Scope: Normative (Core)
- Component: ARVIS Core / Interface Layer

---

## 1. Purpose

The ARVIS Intermediate Representation (IR) defines the **canonical, structured, and versioned output** of a cognitive decision.

The IR serves as:
- the **primary interface** between ARVIS and external systems,
- the **basis for audit, replay, and compliance**,
- the **standardized representation of a cognitive episode**.

Every ARVIS-compliant system MUST produce a valid IR.

---

## 2. Core Principles

### 2.1 Determinism

Given identical inputs, the IR MUST be identical:
- same structure
- same values
- same ordering

---

### 2.2 Completeness

The IR MUST include all **normative outputs**:
- decision outcome
- reason codes
- validity information
- projection summary
- trace references

---

### 2.3 Canonical Structure

The IR MUST follow a fixed schema:
- no implicit fields
- no runtime-dependent fields
- no implementation-specific extensions (unless namespaced)

---

### 2.4 Replayability

The IR MUST allow:
- deterministic replay
- reconstruction of the decision path
- validation of constraints

---

## 3. IR Structure

```yaml
CognitiveIR:
  schema_version: str
  ir_version: str
  decision_id: str
  timestamp: str
  verdict: Enum(ALLOW, REQUIRE_CONFIRMATION, ABSTAIN)
  reason_codes: list[str]

  projection_summary: ProjectionCertificate
  validity_envelope: ValidityEnvelope
  stability_certificate: StabilityCertificate
  adaptive_snapshot: AdaptiveSnapshot | null

  decision_trace: DecisionTrace

  timeline_refs: list[str]

  metadata:
    system_version: str
    api_version: str
    execution_id: str
```

---

## 4. Field Definitions

### 4.1 schema_version
- Type: string
- Purpose: version of IR schema
- MUST follow semantic versioning

### 4.2 ir_version
- Type: string
- Purpose: identifies IR format version
- MUST remain stable across compatible implementations

### 4.3 decision_id
- Type: string (UUID or hash)
- MUST be unique per decision
- MUST be deterministic if replayed

### 4.4 timestamp
- Type: ISO 8601 string (UTC)
- MUST represent decision time
- MUST NOT depend on local timezone

### 4.5 verdict
- Type: Enum
- MUST match Gate output
- MUST respect verdict lattice

### 4.6 reason_codes
- Type: list[str]
- MUST match Reason Code Registry
- MUST include all normative triggers

### 4.7 projection_summary
- Type: ProjectionCertificate
- MUST reflect projection state at decision time

### 4.8 validity_envelope
- Type: ValidityEnvelope
- MUST match validity constraints used by Gate

### 4.9 stability_certificate
- Type: StabilityCertificate
- MUST be consistent with stability metrics

### 4.10 adaptive_snapshot
- Type: AdaptiveSnapshot or null
- MUST be null if adaptive layer unavailable

### 4.11 decision_trace
- Type: DecisionTrace
- MUST include all decision stages

### 4.12 timeline_refs
- Type: list[str]
- MUST reference timeline entries related to the decision

### 4.13 metadata

```yaml
metadata:
  system_version: str
  api_version: str
  execution_id: str
```

- MUST include system-level context
- MUST NOT contain sensitive or non-deterministic data

---

## 5. Invariants

The IR MUST satisfy:

- verdict is consistent with all constraints
- reason_codes reflect all triggered conditions
- decision_trace explains the verdict
- all referenced objects are valid public objects
- no contradiction between fields

---

## 6. Serialization Requirements

The IR MUST:

- be JSON serializable
- use canonical field ordering
- produce stable hash values
- avoid floating ambiguity

---

## 7. Deterministic Hashing

The IR MUST support canonical hashing:

```text
ir_hash = hash(canonical_json(CognitiveIR))
```

Rules:

- same IR → same hash
- ordering MUST be stable
- whitespace MUST be ignored

---

## 8. Replay Requirements

The IR MUST allow:

- re-execution of decision trace
- verification of verdict consistency
- validation of reason codes

Replay MUST produce:

- identical verdict
- identical reason codes

---

## 9. Compatibility Rules

### 9.1 Backward Compatibility
- New fields MAY be added
- Existing fields MUST NOT change meaning

### 9.2 Forward Compatibility
- Unknown fields MUST be ignored safely
- Missing optional fields MUST not break parsing

### 9.3 Version Evolution
- Breaking change → schema_version increment
- Non-breaking change → minor version increment

---

## 10. Compliance Requirements

An implementation is IR-compliant if:

- all required fields are present
- structure matches specification
- serialization is deterministic
- invariants are satisfied
- replay is consistent

---

## 11. Forbidden Practices

The system MUST NOT:

- omit required fields
- include undocumented fields
- produce non-deterministic IR
- embed internal-only data
- alter IR post-generation

---

## 12. Non-Claims

The IR does NOT guarantee:

- correctness of decision logic
- completeness of cognitive reasoning
- external system consistency

It guarantees only:

- structural validity
- traceability
- reproducibility

---

## 13. Future Extensions (Non-Normative)

Planned additions:

- multi-agent IR
- distributed IR linking
- probabilistic annotations
- extended audit metadata