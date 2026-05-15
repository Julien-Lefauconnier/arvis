# ARVIS Errors

`arvis.errors` is the canonical error layer of ARVIS.

It provides a structured, deterministic, replay-aware, and redaction-safe error model for the cognitive kernel, pipeline, syscall layer, replay engine, runtime, API, and external adapters.

This layer is intentionally designed as a kernel-grade boundary system, not as a simple exception utility.

## Goals

The error layer guarantees:

- stable error taxonomy;
- deterministic fingerprints for audit and replay;
- runtime-specific policies;
- safe serialization;
- traceback preservation;
- redaction of sensitive payloads;
- context-based error aggregation;
- replay-safe export;
- explicit separation between declared policy and execution disposition.

## Core Concepts

### `ArvisError`

All ARVIS errors inherit from `ArvisError`.

Each error carries:

- `code`
- `domain`
- `category`
- `severity`
- `policy`
- `semantics`
- `retryable`
- `deterministic`
- `replay_safe`
- `degraded`
- `details`
- `origin`
- `cause`
- `fingerprint`
- `error_id`
- `traceback`

Example:

```python
from arvis.errors import ArvisRuntimeError

error = ArvisRuntimeError(
    "provider timeout",
    code="LLM_TIMEOUT",
    retryable=True,
    deterministic=False,
    replay_safe=False,
)
```

---

## Taxonomy

### Domains

ErrorDomain describes where the error happened.

Examples:

- core
- api
- kernel
- kernel.pipeline
- kernel.syscall
- kernel.replay
- memory
- vfs
- tool
- llm
- external

---

### Categories

ArvisErrorCategory describes the nature of the error.

Examples:

- runtime
- invariant
- domain
- external
- replay
- security
- kernel
- degraded

---

### Severity

ArvisErrorSeverity describes operational seriousness.

- info
- warning
- error
- fatal

---

### Policy

ErrorPolicy is the declared policy attached to the error.

- ignore
- retry
- degrade
- halt_process
- halt_pipeline
- fail_closed
- escalate

---

### Disposition

ErrorDisposition is the execution-oriented interpretation of the policy.

Use:

```python
from arvis.errors import decide_error_policy

decision = decide_error_policy(error)
```

---

## Deterministic Fingerprints vs Error IDs

Each error has two identifiers:

```text
fingerprint
```

A deterministic identifier derived from stable error properties.

Use it for:

- deduplication;
- replay analysis;
- audit grouping;
- deterministic comparison.

```text
error_id
```

A unique runtime occurrence identifier.

Use it for:

- tracing one concrete failure;
- logs;
- incident correlation.

Do not use error_id for replay equivalence.

---

## Serialization

Use:

```python
payload = error.to_dict()
```

For safe external/API exposure:

```python
payload = error.to_safe_dict()
```

Safe serialization removes or redacts sensitive fields such as:

- traceback;
- token;
- secret;
- password;
- authorization;
- cookie;
- api_key;
- private_key;
- access_key.

---

## Redaction

The redaction layer is recursive and key-based.

```python
from arvis.errors import redact_error_payload

safe = redact_error_payload(payload)
```

By default:

- traceback is removed;
- sensitive nested keys are redacted;
- fingerprint is preserved;
- error_id is preserved unless disabled.

```python
safe = redact_error_payload(
    payload,
    include_traceback=False,
    include_error_id=False,
)
```

---

## Normalization

normalize_error() converts arbitrary Python exceptions into ARVIS errors.

```python
from arvis.errors import normalize_error

error = normalize_error(exc)
```

Mapping examples:

```text
- TimeoutError → ArvisExternalError
- ConnectionError → ArvisExternalError
- json.JSONDecodeError → InvalidIRPayloadError
- AssertionError → ArvisInvariantViolation
- ValueError → ArvisInvariantViolation
- TypeError → ArvisRuntimeError
unknown exceptions → ArvisRuntimeError
```

The original exception cause and traceback are preserved.

---

## Error Context

The error layer expects a context-like object with a mutable extra mapping.

```python
from arvis.errors import ensure_error_extra

extra = ensure_error_extra(ctx)
```

A minimal compatible context is available:

```python
from arvis.errors.context import DefaultErrorContext

ctx = DefaultErrorContext()
```

---

## ErrorManager

ErrorManager is the central orchestration layer.

It is responsible for:

- attaching normalized errors to context;
- maintaining counters;
- tracking degraded runtime state;
- exposing replay-safe errors;
- exposing escalation signals.

It does not:

- retry execution;
- control the pipeline;
- schedule runtime actions;
- perform IO.

Example:

```python
from arvis.errors import ErrorManager

payload = ErrorManager.attach(ctx, error)
```

---

## Statistics

```python
stats = ErrorManager.statistics(ctx)
```
Statistics include:

- total
- fatal
- error
- warning
- info
- degraded
- retryable
- replay_unsafe
- non_deterministic
- fail_closed

---

## Runtime Degradation

```python
state = ErrorManager.runtime_degradation_state(ctx)
```

Returned shape:

```python
{
    "active": bool,
    "count": int,
    "last_code": str | None,
    "domains": dict[str, int],
}
```

---

## Escalation

```python
should_escalate = ErrorManager.should_escalate(ctx)
```

Escalation is triggered by:

- any fatal error;
- degraded errors above threshold;
- error count above threshold;
- fail-closed errors.

---

## Replay-Safe Export

```python
should_escalate = ErrorManager.should_escalate(ctx)
```

Only errors with replay_safe=True are exported.

The exported payloads are redacted.

---

## Provenance

Errors can carry origin and cause metadata.

```python
from arvis.errors import ErrorOrigin, ErrorCause

origin = ErrorOrigin(
    component="pipeline",
    stage="gate",
)

cause = ErrorCause(
    code="TIMEOUT",
    error_type="TimeoutError",
)
```

--

## Clone

Errors can be cloned while preserving their operational semantics.

```python
cloned = error.clone(
    code="NEW_CODE",
    details={"stage": "gate"},
)
```

The clone preserves:

- domain;
- category;
- severity;
- policy;
- retryable;
- deterministic;
- replay safety;
- degradation state;
- fingerprint;
- timestamps;
- error id;
- traceback.

---

## Registry

The error registry validates uniqueness of declared error codes.

```python
from arvis.errors import error_code_registry

registry = error_code_registry()
```

Duplicate error codes raise at registry construction time.

---

## Built-in Error Families

**API**

- ArvisAPIError
- CognitiveStateRequiredError
- InvalidIRPayloadError

**Kernel** 

- KernelInvariantViolation
- KernelFailClosedError
- KernelDegradedWarning

**Pipeline**

- PipelineStageError
- PipelineStageDegradedError
- PipelineFailClosedError

**Replay**

- ReplayVerificationError
- ReplayGlobalCommitmentMissing
- ReplayGlobalCommitmentMismatch
- ReplayCognitiveStateMissing

**Runtime / Computation**

- RuntimeDegradationError
- CompositeComputationError
- AdaptiveComputationError
- ProjectionComputationError
- StabilityEvaluationError

**Syscall**

- SyscallExecutionError
- SyscallValidationError
- SyscallReplayError
- SyscallExternalDependencyError

---

## Design Rules

When adding a new error:

1. Prefer subclassing an existing family error.
2. Assign a stable default_code.
3. Choose the correct domain.
4. Choose the correct category.
5. Define retryable, deterministic, and replay_safe explicitly if behavior differs from the parent.
6. Use ErrorPolicy for declared behavior.
7. Do not perform runtime actions inside the error class.
8. Add tests for:
    - metadata;
    - serialization;
    - policy decision;
    - replay safety;
    - registry uniqueness.

---

## Production Invariants

The layer must preserve these invariants:

- every ARVIS error has a stable code;
- every serialized error is JSON-compatible;
- replay-safe export must never expose traceback by default;
- sensitive keys must be redacted recursively;
- external errors are non-deterministic and replay-unsafe by default;
- invariant violations are fatal and replay-unsafe by default;
- degraded errors update runtime degradation state;
- ErrorManager never performs retries, scheduling, IO, or pipeline control;
- fingerprint is for deterministic grouping;
- error_id is for runtime occurrence tracking.

---

## Test Status

Current error-layer test suite:

```bash
ruff check --fix
mypy arvis --strict
pytest tests/errors
```

Reference passing state:

```bash
113 passed
```