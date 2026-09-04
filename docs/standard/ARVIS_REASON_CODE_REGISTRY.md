# ARVIS Reason Code Registry v1 (Draft)

> The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL
> NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and
> **OPTIONAL** in this document are to be interpreted as described in
> [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and
> [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) when, and only
> when, they appear in all capitals, as shown here.

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

Reason codes are a **normative component of the CognitiveIR**.

They provide the **only authoritative explanation layer** for:

- Gate verdicts
- decision constraints
- stability violations

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

### 2.6 Gate Consistency

The set of emitted reason codes MUST be consistent with the final Gate verdict.

Rules:

- if a `critical` normative reason is present → verdict MUST be ABSTAIN
- if a `high` normative reason is present → verdict MUST NOT be ALLOW
- if a `medium` normative reason is present → verdict MUST be ≤ REQUIRE_CONFIRMATION

Violation of this rule invalidates the IR.

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

Three types appear in the tables below, and the normative/reserved
distinction is enforced by `tests/docs/test_reason_code_registry.py`:

- **normative**: the code is emitted by the current implementation and
  its documented effect binds that implementation.
- **informative**: emitted, observability only, no gating effect.
- **reserved**: registered for a documented purpose but emitted by no
  code path today. A reserved code carries no implemented guarantee;
  emitting one promotes it (and the ratchet test requires the table to
  say so).

Fifteen codes previously labeled normative or informative were emitted
by nothing (audit O3, 2026-08); they are now reserved.

---

### 4.1 Projection Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `projection_missing` | high | reserved | ≤ REQUIRE_CONFIRMATION |
| `projection_invalid` | critical | normative | ABSTAIN |
| `projection_boundary` | medium | normative | REQUIRE_CONFIRMATION |
| `projection_unsafe` | critical | normative | ABSTAIN |
| `projection_lyapunov_incompatible` | high | normative | no ALLOW |

---

### 4.2 Validity Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `validity_projection_unavailable` | high | normative | no ALLOW |
| `validity_switching_violation` | high | normative | no ALLOW |
| `validity_exponential_violation` | high | normative | no ALLOW |
| `validity_kappa_violation` | high | normative | no ALLOW |
| `validity_adaptive_unavailable` | high | normative | no ALLOW |
| `validity_unknown` | high | normative | no ALLOW |
| `validity_invalid` | critical | reserved | ABSTAIN |
| `validity_degraded` | medium | reserved | REQUIRE_CONFIRMATION |

The first five name which certification axis the envelope could not
establish; `validity_unknown` covers an envelope that refused for a reason
outside that closed set. Until campaign REASONS (2026-09-04) the gate built
these as `f"validity_{envelope.reason}"`, and a constructed string is not a
registered code: the normalizer replaced every one of them with
`unknown_reason`, so the IR named no cause for what is, under the default
posture, the most frequent refusal in the system. The emitted set is now
closed in `arvis/math/stability/validity_envelope.py`.

An invalid envelope blocks ALLOW; it does not by itself force ABSTAIN. On a
payload exclusively dedicated to a declared risk scalar the input-risk
policy supersedes projection-derived reasons (F-001-a5), which is how a
policy-governed ALLOW stays consistent with its own trace.

---

### 4.3 Kappa Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `kappa_violation` | critical | normative | ABSTAIN |
| `kappa_boundary` | medium | reserved | REQUIRE_CONFIRMATION |
| `kappa_unstable` | high | reserved | no ALLOW |

---

### 4.4 Stability Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `global_instability_confirmed` | critical | normative | ABSTAIN |
| `global_instability_abstained` | critical | normative | ABSTAIN |
| `switching_soft_warning` | low | informative | none |
| `switching_unsafe_monitoring` | medium | informative | none |
| `global_instability_suspected` | high | reserved | ≤ REQUIRE_CONFIRMATION |
| `local_instability_detected` | medium | reserved | REQUIRE_CONFIRMATION |

The two switching codes are informative because the switching axis is
monitor-only under the default posture: they are measured and disclosed on
every turn and act on the verdict only in the `enforce` posture. They are
emitted, and were reaching the IR as `unknown_reason`.

---

### 4.5 Adaptive Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `adaptive_instability_veto` | critical | normative | ABSTAIN |
| `adaptive_band_critical` | high | reserved | ≤ REQUIRE_CONFIRMATION |
| `adaptive_margin_warning` | medium | normative | REQUIRE_CONFIRMATION |
| `adaptive_unavailable` | high | normative | ≤ REQUIRE_CONFIRMATION |

---

### 4.6 Fusion Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `fusion_fallback` | medium | normative | downgrade |
| `fusion_override` | high | reserved | downgrade |
| `fusion_consensus` | low | reserved | none |
| `recovery_post_fusion_override` | medium | normative | downgrade |
| `gate_policy_adjustment` | medium | normative | downgrade |

---

### 4.7 Recovery / Override Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `recovery_override` | medium | normative | downgrade |


Recovery-related codes MAY promote or degrade decisions depending on policy and context.
They MUST remain consistent with the final verdict.

---

### 4.8 Declared Input Risk Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `input_risk_governed` | medium | normative | graded verdict |
| `input_risk_hardened` | medium | normative | harden only |
| `input_risk_relax_denied` | high | normative | verdict kept |

`input_risk_governed` is emitted when the three-band policy determines the
verdict, which requires both a payload exclusively dedicated to the risk
scalar and the `graded` posture. `input_risk_hardened` marks the harden-only
path (mixed payload, or the `production` posture) where an untrusted
declared risk may only make the verdict stricter. `input_risk_relax_denied`
records a relaxation refused because the verdict's provenance was a real
veto rather than a sparse-projection artifact (F-006).

---

### 4.9 System Layer

| Code | Severity | Type | Effect |
|------|----------|------|--------|
| `input_missing` | high | reserved | ≤ REQUIRE_CONFIRMATION |
| `input_corrupted` | critical | reserved | ABSTAIN |
| `state_inconsistent` | critical | reserved | ABSTAIN |
| `sensor_degradation_floor` | high | normative | ≤ REQUIRE_CONFIRMATION |
| `gate_fail_closed` | critical | normative | ABSTAIN |
| `unknown_error` | critical | normative | ABSTAIN |

`gate_fail_closed` is the code for an exception raised inside a gate layer:
a failing guarantee mechanism can never relax, so the verdict becomes
ABSTAIN and the record says which mechanism failed (F-002).

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

Additionally:

- all triggered constraints MUST produce at least one reason code
- absence of a required reason code invalidates the IR

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

Reason code ordering:

- MUST be deterministic after normalization
- MUST NOT carry semantic meaning

### 6.4 Separation from Interoperability Layers

Reason codes are independent from external canonical signal systems.

In particular:

- reason codes MUST NOT be derived from canonical signals
- reason codes MUST NOT be modified by projection layers
- reason codes MUST remain identical across IR → projection transformations

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

### 7.4 Normalization Requirement

Implementations MAY internally emit legacy or implementation-local reason codes,
but all public-facing outputs MUST be normalized to canonical registry codes
before exposure through public objects or IR.

---

### 8. Compliance Requirements

An implementation is reason-compliant if:

- all emitted reasons belong to the registry
- no unknown code is emitted
- all triggered constraints produce a reason
- reason semantics match their defined effect
- reason codes fully explain the Gate verdict (no missing causal reason)

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