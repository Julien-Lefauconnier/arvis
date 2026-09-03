# F-*** doctrine invariants

Load-bearing rules the code keeps true and the tests pin. A comment
citing `F-xxx` is claiming this page's statement at that site. The
`-a5` suffix marks the audit-5 refinement of the base invariant.

## F-001

Verdict monotonicity. On the decision path, an enforcement layer may
only keep or harden the verdict (ALLOW < REQUIRE_CONFIRMATION <
ABSTAIN); relaxations exist only through the provenance-checked
override sites on a frozen allowlist. Enforced by `enforce_monotone`
(`trace_helpers.py`) around every layer of the gate decision stack,
and by the trace grammar test.

### F-001-a5

A caller-declared input risk is untrusted input: it may harden the
verdict or add a signal, never weaken anything. Enforced in
`kernel/gate/input_risk.py` and the input-risk gate (harden-only
outside the graded posture).

## F-002

Unknown switching safety fails closed: when the T1 condition cannot
be evaluated, the turn is treated as unsafe, never as safe. Enforced
in the gate switching layer; production invariants hold whatever the
constructor (`api/os.py`).

## F-003

The validity envelope's `hard_block` is a real, computed signal (it
used to be hardcoded False, leaving the enforcement machinery dead).
Enforced by `hard_block_policy.py` and its table version.

### F-003-a5

A configuration override that would relax a production invariant is
refused at construction, not silently accepted.

## F-004

The tool registry freezes after bootstrap: `freeze_tools()` pins the
surface and returns its fingerprint; later mutation is refused.

### F-004-a5

Production invariants hold whatever the constructor arguments; the
single enforcement point is `CognitiveOSConfig`/`CognitiveOS`.

## F-005

An envelope that could not be built is unknown validity, and unknown
validity gates nothing open: the verdict fails closed to ABSTAIN
(`decision_stack.py`).

## F-006

The input-risk policy never relaxes a real veto, and an exception
inside the gate forces ABSTAIN (fail-closed), never a pass-through.

## F-007

The composed run commitment: what arvis did is exactly what arvis can
prove it did (`api/commitment.py`).

### F-007-a5

The commitment inputs are exactly: registry manifest fingerprint,
effective config fingerprint, active policy tables fingerprint, and
the digest of the redacted syscall journals.

## F-008

The runtime mode set is closed: unknown mode strings are refused at
coercion instead of silently running with a permissive posture
(`api/runtime_mode.py`).

### F-008-a5

Every effect syscall journals a pre-effect audit intent through the
outbox; a missing intent reads as a ghost signal, never as silence.

## F-009

`force_tool` only selects the tool; execution authority is never
implied and requires `force_execution=True` explicitly
(`api/runtime_controls.py`).

### F-009-a5

An effect capability cannot exist without its governance: registering
an EFFECT syscall without an access resolver is refused at import
time (`syscall_registry.py`).

## F-012

REQUIRED audit commitment needs the trace machinery: combined with
`enable_trace=False` it is a configuration contradiction and is
refused (`api/os.py`).

## F-013

The audit artifact detaches at commitment time: the stored IR is
rebuilt from the exact hashed bytes, so no upstream alias can diverge
the payload from its committed digest (`cognitive_result_view.py`).

## F-014

A tool that runs past its declared timeout has its late result
REJECTED (deadline on result acceptance, not an interruption; the
effect may still have happened and the refusal says so)
(`errors/tool_runtime.py`).

## F-015

How a missing audit commitment is handled is an explicit policy
(`AuditCommitmentPolicy`), never an implicit default.

## F-016

Retry requires idempotence: a tool whose spec does not declare it is
never retried (`tools/retry_policy.py`).

## F-017 and F-018

Host-provided tool gates: in the PRODUCTION profile a tool declaring
`required_consent` or `data_egress` is denied when the matching gate
is missing (deny-by-default); other profiles leave the decision to
the host (`api/os.py`).

### F-018-a5

The redaction policy is part of the commitment composition: effect
parameters are redacted before hashing, and the redaction policy
itself is versioned.

## F-019

In the PRODUCTION profile the tool registry freezes automatically at
the first run; late registration is refused by the frozen registry
itself (`api/os.py`).

## F-020

A payload that violates the tool's declared `input_schema` never
reaches the tool (`errors/tool_runtime.py`).
