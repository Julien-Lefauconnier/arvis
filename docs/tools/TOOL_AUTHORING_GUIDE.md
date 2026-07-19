
# Tool Authoring Guide — ARVIS

## Position in ARVIS Architecture

Tools are NOT executed directly.

They are executed via the Syscall System:

Pipeline → Intent → Kernel → Syscall (tool.execute) → Tool


## Overview

A Tool is a capability exposed to the Cognitive OS.

It must:
- be deterministic when possible
- handle errors safely
- expose a clear contract

---

## Base Class

```python
from arvis.tools.base import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"

    def execute(self, input_data):
        ...
```

---

## Input Structure

```python
input_data = {
    "decision": ActionDecision,
    "context": CognitivePipelineContext,
    "tool_payload": dict,
    "syscall_context": dict  # optional runtime metadata
}
```

---

## Execution Constraints

Tools MUST:

- be callable via syscall only
- not be invoked directly by the pipeline
- not modify cognitive reasoning

---

## Example

```python
class EchoTool(BaseTool):
    name = "echo"

    def execute(self, input_data):
        payload = input_data["tool_payload"]
        return {"echo": payload}
```

---

## Validation (optional but recommended)

```python
def validate(self, input_data):
    if "tool_payload" not in input_data:
        raise ValueError("Missing payload")
```

---

## Best Practices

### 1. Pure vs Side Effects

Type	Example
Pure	compute, transform
Side-effect	API call, DB write

---

### 2. Idempotency

Declaring an operation idempotent is only the first step:

```python
ToolSpec(
    name="payments.capture",
    description="Capture one payment",
    idempotent=True,
)
```

Every effectful adapter MUST forward the exact key provided by ARVIS rather
than generating a new one:

```python
def execute_invocation(self, invocation: ToolInvocation):
    return provider.capture(
        payload=invocation.payload,
        idempotency_key=invocation.idempotency_key,
    )
```

Legacy adapters receive the same value under
`input_data["idempotency_key"]`. The key is stable for one logical action,
persisted in the pre-effect outbox and bound by the audit receipt through the
intent commitment. A retry or crash-recovery worker MUST reuse the persisted
key exactly. `idempotent=True` without forwarding the key is only a declaration
and does not make an external effect safely replayable.

---

### 3. Error Handling

Never swallow errors:

```python
raise Exception("clear message")
```

Executor will capture it.

---

### 4. Latency Awareness

Execution time is automatically tracked.

---

## Anti-patterns forbidden

- modifying ctx outside context.extra
- hidden global state
- non-deterministic behavior without reason
- blocking calls without timeout

---

## ToolSpec and the Capability Manifest

A `ToolSpec` describes a tool's contract, its execution semantics, and its
governance. Beyond the basic identity and schemas, the spec carries a
**capability manifest**: declarative metadata a host reads to govern
sovereignty, egress and consent uniformly across local tools and external
(e.g. MCP) tools.

```python
from arvis.tools.spec import ToolSpec

ToolSpec(
    name="my_tool",
    description="...",
    input_schema={...},
    output_schema={...},

    # execution semantics
    idempotent=False,
    retryable=True,
    side_effectful=True,
    timeout_seconds=None,

    # governance (enforced by ToolPolicyEvaluator, except where noted)
    max_risk=1.0,               # deny if the request risk exceeds this ceiling
    requires_confirmation=False,  # deny with a confirmation-required decision
    audit_required=False,       # declarative: tool.execute always journals
    reversible=True,            # False marks an effect that cannot be undone

    # capability manifest (opaque to ARVIS; the host interprets the labels)
    provider=None,              # third-party service ("google", "notion"), or None
    data_egress=False,          # True if it sends the caller's data outbound
    data_class="unspecified",   # host-defined sensitivity ("public", "personal", ...)
    required_consent=None,      # opaque consent key the host must have granted
)
```

### Sovereignty taxonomy

The manifest yields three tool classes, derived from `provider` and
`data_egress` (a host reads `spec.crosses_trust_boundary`, i.e.
`provider is not None`):

| Class | provider | data_egress | Meaning |
|-------|----------|-------------|---------|
| **sovereign** | `None` | `False` | No third party; stays in the local boundary. |
| **connected (read)** | set | `False` | Talks to a provider, inbound fetch only. |
| **connected (egress)** | set | `True` | Sends the caller's data outbound; maximal scrutiny. |

ARVIS does not interpret `provider`, `data_class` or `required_consent` -- they
are opaque labels. The host maps them onto its own consent system, data taxonomy
and egress policy (for example, denying egress of a `confidential` data class,
or gating a tool on a granted consent). Declaring a manifest is how a new tool,
local or external, becomes governable without bespoke policy code.

### Examples

```python
# Sovereign: reads a local encrypted store, no third party.
ToolSpec(name="calendar.read", description="Read the calendar.",
         side_effectful=False, required_consent="calendar_read")

# Connected (egress): publishes the caller's content to a third party.
ToolSpec(name="notion.create_page", description="Create a page in Notion.",
         side_effectful=True, reversible=False,
         provider="notion", data_egress=True, data_class="personal",
         required_consent="notion_access")
```

---

## Testing

Minimal test:

```python
def test_tool():
    tool = MyTool()
    result = tool.execute({"tool_payload": {...}})
    assert result is not None
```

---

## Summary

A good tool is:

- predictable
- observable
- bounded
- safe
