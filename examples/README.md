# ARVIS Examples

Production-ready examples showing how **ARVIS Cognitive OS** governs decisions, tools, memory, replayability, and auditability.

Run any example:

```bash
python examples/01_gate_refusal.py
```

---

## Quick Start

```python
from arvis import CognitiveOS

os = CognitiveOS()

result = os.run(
    "demo",
    {"risk": 0.92, "action": "wire_transfer"},
)

print(result.summary())
```

ARVIS evaluates the request, applies governance rules, and returns a traceable decision.

---

## Example Catalog

| File                            | What it demonstrates                         |
| ------------------------------- | -------------------------------------------- |
| `01_gate_refusal.py`            | Unsafe actions blocked before execution      |
| `02_deterministic_replay.py`    | Same input → same verified decision          |
| `03_ir_export.py`               | Portable IR records for replay & audit       |
| `04_human_confirmation.py`      | Human approval for sensitive actions         |
| `05_tool_authorization.py`      | External tools require authorization         |
| `06_finance_risk_screening.py`  | Trade / risk pre-execution controls          |
| `07_memory_governed_context.py` | Context-aware decisions with governed memory |
| `08_timeline_audit.py`          | Hash-linked timeline commitments             |
| `09_multi_run_batch.py`         | Batch decision processing at scale           |
| `10_runtime_inspection.py`      | Production observability & inspection        |

---

## Why These Examples Matter

ARVIS is built for systems that need:

* **Safe autonomous decisions**
* **Deterministic replay**
* **Human-in-the-loop controls**
* **Tool governance**
* **Audit trails**
* **Operational observability**

---

## Suggested Order

If you're new to ARVIS:

1. `01_gate_refusal.py`
2. `02_deterministic_replay.py`
3. `04_human_confirmation.py`
4. `08_timeline_audit.py`
5. `10_runtime_inspection.py`

---

## Output Style

Examples are intentionally concise and executive-readable:

```text
Status        : BLOCKED
Approval Need : YES
Commitment    : 8642d95cfdb73c16...
Takeaway      : Unsafe actions are stopped before execution.
```

---

## Next Step

Read the main documentation to integrate ARVIS into your own AI agents, copilots, or autonomous systems.
