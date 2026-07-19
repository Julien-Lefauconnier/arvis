# Governed effect path

Status: normative architecture note for `0.1.0a10`.

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
      derive principal, tenant and idempotency key
      evaluate ToolPolicy and host gates
  → ToolManager
      reserve confirmation
      mint registered MINTED capability
  → SyscallHandler(tool.execute)
      validate exact authorization outcome
      validate production identity
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
Possession of a capability is insufficient until the exact outbox receipt has
activated it.

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

## Payload and identity binding

The intent commitment binds:

- canonical frozen payload hash;
- exact tool name;
- exact authorization snapshot;
- principal and tenant;
- authentication provenance when present;
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

## Host obligations

A production host must provide:

- an `AuthenticatedPrincipal` on the trusted context channel;
- a qualified transactional append-only audit sink;
- durable persistence of the complete intent, including the idempotency key;
- forwarding of the idempotency key to the external system;
- storage fields large enough for the complete run-derived causal ID;
- one runtime instance per request/turn unless the host serializes access.
