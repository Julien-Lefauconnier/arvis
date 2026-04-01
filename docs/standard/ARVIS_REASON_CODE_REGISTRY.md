# ARVIS Reason Code Registry v1 (Draft)

## Status
- Version: v1 (Draft)
- Scope: Normative (Core)
- Component: ARVIS Core / Compliance Layer

---

## 1. Purpose

The ARVIS Reason Code Registry defines the **canonical, versioned, and normative set of reason codes** used across the system.

Reason codes serve as:
- the **primary explanation mechanism** for decisions,
- a **machine-readable audit layer**,
- a **compliance anchor** for deterministic replay and certification.

Every reason code MUST be:
- stable,
- uniquely identifiable,
- semantically unambiguous.

---

## 2. Core Principles

### 2.1 Determinism
Given identical inputs, the same reason codes MUST be produced.

### 2.2 Canonical Form
Reason codes MUST follow a strict naming convention:

<layer><condition>[<qualifier>]


Examples:
- `projection_invalid`
- `kappa_violation`
- `adaptive_instability_veto`

---

### 2.3 One Meaning Rule
A reason code MUST have **exactly one meaning**.

No code may be reused for multiple interpretations.

---

### 2.4 Layer Attribution
Each reason code MUST belong to exactly one layer:

- `projection`
- `validity`
- `kappa`
- `stability`
- `adaptive`
- `fusion`
- `system`

---

### 2.5 Normative vs Informative

Each reason code MUST be classified as:

- `normative` → affects the verdict
- `informative` → does not affect the verdict

---

## 3. Severity Levels

Each reason code MUST define a severity:

| Severity | Meaning |
|----------|--------|
| `critical` | Forces ABSTAIN |
| `high` | Blocks ALLOW |
| `medium` | Requires confirmation |
| `low` | Informational |

---

## 4. Canonical Reason Codes (v1)

---

### 4.1 Projection Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `projection_missing` | high | normative | ≤ REQUIRE_CONFIRMATION |
| `projection_invalid` | critical | normative | ABSTAIN |
| `projection_boundary` | medium | normative | REQUIRE_CONFIRMATION |
| `projection_unsafe` | critical | normative | ABSTAIN |
| `projection_lyapunov_incompatible` | high | normative | no ALLOW |

---

### 4.2 Validity Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `validity_invalid` | critical | normative | ABSTAIN |
| `validity_degraded` | medium | normative | REQUIRE_CONFIRMATION |
| `validity_unknown` | high | normative | ≤ REQUIRE_CONFIRMATION |

---

### 4.3 Kappa Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `kappa_violation` | critical | normative | ABSTAIN |
| `kappa_boundary` | medium | normative | REQUIRE_CONFIRMATION |
| `kappa_unstable` | high | normative | no ALLOW |

---

### 4.4 Stability Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `global_instability_confirmed` | critical | normative | ABSTAIN |
| `global_instability_suspected` | high | normative | ≤ REQUIRE_CONFIRMATION |
| `local_instability_detected` | medium | normative | REQUIRE_CONFIRMATION |

---

### 4.5 Adaptive Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `adaptive_instability_veto` | critical | normative | ABSTAIN |
| `adaptive_band_critical` | high | normative | ≤ REQUIRE_CONFIRMATION |
| `adaptive_margin_warning` | medium | normative | REQUIRE_CONFIRMATION |
| `adaptive_unavailable` | low | informative | none |

---

### 4.6 Fusion Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `fusion_fallback` | medium | normative | downgrade |
| `fusion_override` | high | normative | downgrade |
| `fusion_consensus` | low | informative | none |

---

### 4.7 System Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `input_missing` | high | normative | ≤ REQUIRE_CONFIRMATION |
| `input_corrupted` | critical | normative | ABSTAIN |
| `state_inconsistent` | critical | normative | ABSTAIN |
| `unknown_error` | critical | normative | ABSTAIN |

---

## 5. Reason Code Semantics

Each reason code MUST define:

```yaml
ReasonCode:
  code: str
  layer: str
  severity: Enum
  type: Enum(normative, informative)
  description: str
  default_effect: str
```

---

## 6. Emission Rules

### 6.1 Mandatory Emission

A reason code MUST be emitted if:

- a normative constraint is triggered,
- a verdict downgrade occurs,
- a veto condition is applied.

### 6.2 No Silent Failures

The system MUST NOT:

- suppress a triggered reason,
- replace a reason with a generic label,
- emit ambiguous or free-text reasons.

### 6.3 Multiple Reasons

Multiple reason codes MAY be emitted.

Rules:

- order is not normative
- duplication is forbidden
- all relevant constraints MUST be included

---

## 7. Compatibility and Versioning

### 7.1 Stability Guarantee

Reason codes are part of the public contract.

Once released:

- they MUST NOT change meaning
- they MUST NOT be removed without deprecation

### 7.2 Deprecation Policy

A deprecated code MUST:

- remain supported for at least one version cycle
- be mapped to a replacement code

### 7.3 Version Tagging

The registry MUST include:

```text
reason_registry_version: v1
```

---

### 8. Compliance Requirements

An implementation is reason-compliant if:

- all emitted reasons belong to the registry
- no unknown code is emitted
- all triggered constraints produce a reason
- reason semantics match their defined effect

---

## 9. Forbidden Practices

The system MUST NOT:

- use free-text reasons
- mix multiple meanings into one code
- emit undocumented codes
- rely on implicit reasoning

---

## 10. Non-Claims

The registry does NOT guarantee:

- completeness of all possible failure modes
- correctness of upstream signals
- semantic interpretation beyond defined scope

---

## 11. Future Extensions (Non-Normative)

Planned additions:

- hierarchical reason codes
- probabilistic severity weighting
- cross-agent reason propagation
- domain-specific reason extensions