# ARVIS Public Objects Registry v1 (Draft)

## Status
- Version: v1 (Draft)
- Scope: Normative (Core)
- Component: ARVIS Core / Standard Interface

---

## 1. Purpose

The ARVIS Public Objects Registry defines the **canonical set of public data structures** exposed by the system.

These objects form the **external contract** of ARVIS and are used for:
- interoperability between implementations,
- audit and replay,
- compliance verification,
- certification processes.

Any object not listed here MUST be considered **internal** and non-normative.

---

## 2. Core Principles

### 2.1 Explicit Contract
Every public object MUST:
- have a defined schema,
- define required and optional fields,
- declare invariants,
- be versioned.

---

### 2.2 Stability
Public objects are part of the **standard contract**.

- Breaking changes are forbidden without version bump
- Field semantics MUST NOT change silently

---

### 2.3 Deterministic Serialization
All public objects MUST be:
- serializable to a canonical format (e.g. JSON)
- deterministic in field ordering and hashing

---

### 2.4 Separation of Concerns

Public objects MUST NOT:
- embed runtime-only state
- contain hidden or implicit fields
- depend on implementation-specific structures

---

## 3. Object Classification

Each object MUST declare its status:

- `public` → part of the standard
- `internal` → implementation-specific
- `experimental` → unstable, non-normative

Only `public` objects appear in this registry.

---

## 4. Canonical Public Objects (v1)

---

### 4.1 GateResult

#### Role
Represents the final decision of the Gate.

```yaml
GateResult:
  schema_version: str
  verdict: Enum(ALLOW, REQUIRE_CONFIRMATION, ABSTAIN)
  reason_codes: list[str]
  decision_trace: DecisionTrace
```

Invariants

- verdict MUST follow the lattice rules
- reason_codes MUST belong to the registry
- decision_trace MUST be complete

### 4.2 DecisionTrace

Role

Provides a step-by-step trace of the Gate decision.

```yaml
DecisionTrace:
  schema_version: str
  steps:
    - stage: str
      input_snapshot: dict
      partial_verdict: Enum
      reason_codes: list[str]
```

Invariants
- All decision stages MUST be recorded
- No stage affecting the verdict may be omitted

Note:
Implementations MAY use an extended internal trace representation.
Only canonical fields are required for public exposure.

### 4.3 ValidityEnvelope

Role

Represents the validity domain of the current decision.

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

Invariants

- valid = False MUST imply ABSTAIN at Gate level
- reason MUST be present if valid = False

### 4.4 ProjectionCertificate

Role

Represents the certification status of projection.

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

Invariants
- If available = False, all other fields MUST be null
- warning_codes MUST follow reason registry

### 4.5 CognitiveIR

Role

Canonical intermediate representation of a cognitive decision.

```yaml
CognitiveIR:
  schema_version: str
  decision_id: str
  timestamp: str
  verdict: str
  reason_codes: list[str]
  projection_summary: dict
  validity_envelope: ValidityEnvelope
  stability_certificate: dict
  timeline_refs: list[str]
  metadata: dict
```

Invariants
- MUST be deterministic
- MUST be replayable
- MUST include all normative outputs

### 4.6 TimelineEntry

Role

Represents an event in the cognitive timeline.

```yaml
TimelineEntry:
  schema_version: str
  event_id: str
  timestamp: str
  lamport: int
  event_type: str
  payload_ref: str
  hash: str
  parent_hash: str
```

Invariants
- timestamps MUST be UTC
- hash MUST be deterministic
- parent_hash MUST form a chain

### 4.7 StabilityCertificate

Role

Represents stability guarantees at decision time.

```yaml
StabilityCertificate:
  schema_version: str
  local_stability: bool
  global_stability: bool
  kappa_safe: bool
  margin: float | null
  stability_domain: str
```

Invariants
- MUST align with Gate inputs
- MUST NOT contradict verdict

### 4.8 AdaptiveSnapshot

Role

Represents adaptive system state at decision time.

```yaml
AdaptiveSnapshot:
  schema_version: str
  available: bool
  stability_band: str
  veto: bool
  margin: float | null
```

Invariants

- If veto = True → Gate MUST ABSTAIN
- If available = False → no adaptive constraints applied

---

## 5. Object Versioning

Each object MUST include:

```text
schema_version: str
```

Rules:

- Version MUST follow semantic versioning
- Breaking change → version increment required
- Backward compatibility MUST be documented

---

## 6. Serialization Requirements

All public objects MUST:

- be JSON serializable
- use canonical field ordering
- avoid floating ambiguity (explicit precision rules)
- produce stable hashes when serialized

---

## 7. Compliance Requirements

An implementation is object-compliant if:

- all public objects match their schema
- invariants are enforced
- serialization is deterministic
- no undocumented fields are exposed

---

## 8. Forbidden Practices

The system MUST NOT:

- expose internal objects as public
- mutate public object schemas dynamically
- omit required fields
- introduce undocumented fields

---

## 9. Non-Claims

Public objects do NOT guarantee:

- correctness of upstream computations
- completeness of system observability
- global system validity

They only guarantee structural and semantic consistency.

---

## 10. Future Extensions (Non-Normative)

Planned additions:

- multi-agent object extensions
- distributed timeline objects
- resource governance objects
- cognitive scheduler objects