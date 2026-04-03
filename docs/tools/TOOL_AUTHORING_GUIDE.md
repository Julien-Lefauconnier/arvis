# Tool Authoring Guide — ARVIS

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
    "tool_payload": dict
}
```

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

Prefer:

```python
idempotent = True
```

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

## ToolSpec (optional)

```python
ToolSpec(
    name="my_tool",
    description="...",
    input_schema={...},
    output_schema={...},
    retryable=True,
)
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

