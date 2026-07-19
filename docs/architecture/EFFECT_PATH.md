# Governed effect path

Status: normative architecture note for `0.1.0a11`.

## Scope

ARVIS governs an external effect from the finalized action decision to the
journaled result. Persistence, authentication and the external adapter remain
host responsibilities; ARVIS enforces the contracts that must be satisfied
before dispatch.

## Transaction

```text
ActionDecision
  → ToolAuthorizationService
      freeze canonical payload
      validate tool and input schema
      snapshot AuthorizedEffectContext
      derive idempotency key
      evaluate ToolPolicy and host gates
  → ToolManager
      reserve confirmation
      mint registered MINTED capability
  → SyscallHandler(tool.execute)
      validate exact authorization outcome
      validate production identity
      compare current identity with sealed effect context
  → IntentOutboxService
      build committed intent
      persist through qualified sink
      validate exact receipt
      publish accepted intent
  → capability activation
  → EffectDispatcher
      atomically consume capability
      validate tool defense-in-depth
      dispatch frozen invocation
      classify effect boundary
  → ExecutionArtifact
  → exact intent/result journal pair
```

No public method on `ToolManager` or `ToolExecutor` can replace this sequence.
Possession of a capability is insufficient until its current identity matches
the sealed effect context and the exact outbox receipt has activated it.

## Typed ownership

| Component | Owns | Must not own |
|---|---|---|
| `ToolAuthorizationService` | immutable request preparation and policy material | confirmation state or mint authority |
| `ToolManager` | confirmation transaction and capability mint lifecycle | durable outbox or external effect body |
| `IntentOutboxService` | intent commitment, sink receipt and durable-position replay guard | policy evaluation or capability consumption |
| `SyscallHandler` | transaction ordering and mandatory result journal | business payload mutation |
| `EffectDispatcher` | single-use capability consumption and effect classification | policy, confirmation or outbox persistence |

The service classes are internal implementation details and are deliberately
absent from `arvis` and `arvis.api` exports.

## Capability lifecycle

```text
MINTED
  ├─ valid exact receipt → ACTIVATED
  │                         ├─ dispatch → CONSUMED
  │                         └─ abort before dispatch → REVOKED
  └─ invalid/missing receipt → REVOKED
```

All state transitions are atomic within one process. The current capability and
confirmation registries are process-local. Production hosts must use one ARVIS
instance per request/turn; a future shared multi-worker runtime requires an
external transactional registry.

## Frozen effect material

`ToolInvocation` contains exactly two effect-selection inputs:

- a canonical `FrozenEffectPayload` isolated from caller-owned containers;
- an immutable `AuthorizedEffectContext` containing principal, tenant,
  authentication provenance, service/session bindings, process/run identity and
  an optional host binding commitment.

It never retains the mutable pipeline context. A legacy adapter receives
`tool_payload`, `idempotency_key`, `invocation` and `effect_context`; it never
receives `context`. A structured adapter reads the same values from the exact
`ToolInvocation` authorized by policy.

The syscall handler reconstructs the current effect identity from the trusted
context channel and compares it by value with the sealed context before intent
creation. Principal, tenant, authentication source/strength, service, session,
process or run divergence produces `effect_context_mismatch`: the capability is
revoked, any confirmation is released, and no intent, receipt or effect exists.
`KERNEL_PRINCIPAL` is reserved for declared kernel-internal syscalls and is not
accepted for a user tool effect.

## Payload and identity binding

The intent commitment binds:

- canonical frozen payload hash;
- exact tool name;
- exact authorization snapshot;
- complete authorized effect context and its commitment;
- idempotency key;
- syscall and effect parameters.

The receipt binds the intent commitment, complete run ID, causal ID, durable
position and store fingerprint. The result binds the same intent commitment and
causal identity.

## Failure doctrine

Before the effect starts:

- refusal or exception releases a reserved confirmation;
- capability is revoked;
- no direct fallback route exists.

After the effect boundary is crossed:

- confirmation is conservatively consumed;
- failures are returned as effectful `ToolResult` states;
- result journaling is mandatory;
- a journaling failure marks the run audit-incomplete rather than pretending the
  effect did not happen.

## ARVIS / VeraMem boundary

ARVIS provides and enforces:

- `FrozenEffectPayload` and `AuthorizedEffectContext`;
- typed `ToolAuthorizationOutcome` and the single-use capability lifecycle;
- intent construction, receipt validation and result-to-intent binding;
- canonicalization, confirmation binding and composed commitments.

VeraMem, as production host, must provide:

- a real `AuthenticatedPrincipal` and tenant binding from its authentication
  layer;
- a transactional append-only `DurableAuditSink` with a DATABASE or
  DISTRIBUTED_LOG manifest and durable uniqueness constraints;
- persistent confirmation and idempotency state suitable for its worker model;
- tool business services, repositories and external clients injected when the
  tool is constructed;
- distributed locking, queues, retries and crash recovery when several workers
  share effects.

At minimum, VeraMem's durable schema must prevent duplicate receipt IDs,
duplicate `(store_fingerprint, durable_position)` pairs and duplicate
`(run_id, causal_id)` pairs. It should index `intent_sha256`, persist the
idempotency key, and model confirmation as an atomic lifecycle such as
`PENDING → RESERVED → CONSUMED` (or `EXPIRED`). These are host persistence
guarantees; ARVIS still validates every receipt and transition presented to
the kernel.

Credentials, database sessions, HTTP requests, connection pools and service
clients never belong in `AuthorizedEffectContext`. ARVIS commits identity and
provenance, not secrets or live host objects.

## Host obligations

A production host must provide:

- an `AuthenticatedPrincipal` on the trusted context channel;
- a qualified transactional append-only audit sink;
- durable persistence of the complete intent, including the idempotency key;
- forwarding of the idempotency key to the external system;
- storage fields large enough for the complete run-derived causal ID;
- one runtime instance per request/turn unless the host serializes access.

An ARVIS tool must never use mutable runtime context to select its target,
identity, tenant, credentials or services. VeraMem injects those services into
the tool or adapter constructor; the effect body uses only the frozen payload,
sealed effect context and persisted idempotency key.
