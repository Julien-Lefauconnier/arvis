# Format versions

ARVIS carries seventeen version constants. They are not variants of one number:
each governs a different artifact, changes for a different reason, and breaks a
different thing when it moves. This page is the map.

Nothing here is a public API version. For what the package promises and when it
may change, see [VERSIONING.md](../VERSIONING.md).

## Identity

| Constant | Value | What it names |
| --- | --- | --- |
| `PACKAGE_VERSION` | from installed metadata | the distribution on PyPI |
| `API_VERSION` | `0.1` | the shape of the public API surface |
| `STANDARD_VERSION` | `draft-v1` | the ARVIS standard the runtime implements |

`PACKAGE_VERSION` is read from the installed distribution and falls back to a
literal only when the package is not installed, which happens in a source
checkout.

## Intermediate representation

Two constants are called `IR_VERSION`, and they are not the same thing. This is
the confusion this page exists to end.

| Constant | Value | What it names |
| --- | --- | --- |
| `arvis.api.ir.IR_VERSION` | `arvis-ir.v1` | the **public** IR view, the one exposed to callers and hashed into commitments |
| `arvis.ir.version.IR_VERSION` | `1.0` | the **cognitive** IR, the internal representation the adapters build |
| `arvis.adapters.ir.state_adapter._IR_VERSION` | `1.0` | the state fragment of that cognitive IR |

The public IR version is the one that matters to a consumer: it is bound into
`commitment.py`, so changing it invalidates every previously issued commitment.
The cognitive IR version describes an internal structure and has no such reach.

They are deliberately left distinct rather than unified. Making them share a
value would suggest they move together, and they do not.

## Commitment and effect chain

These are the versions that invalidate stored material when they change. None
of them is deprecated: they are versioned, and the changelog says so
explicitly.

| Constant | Value | Moves when |
| --- | --- | --- |
| `CANONICALIZATION_VERSION` | `3` | canonical bytes change, invalidating every hash ever produced |
| `COMMITMENT_VERSION` | `5` | the commitment structure changes |
| `CONFIRMATION_FORMAT_VERSION` | `4` | a stored confirmation can no longer be read |
| `INVOCATION_FORMAT_VERSION` | `2` | the authorized invocation record changes |
| `CAPABILITY_FORMAT_VERSION` | `2` | the capability record changes |
| `CAPABILITY_ACTIVATION_FORMAT_VERSION` | `2` | the activation record changes |
| `EFFECT_CONTEXT_FORMAT_VERSION` | `1` | the sealed effect context changes |
| `REDACTION_POLICY_VERSION` | `5` | what is redacted from the journal changes |

A confirmation minted under an older format version is never silently
accepted. That is the point of versioning them rather than deprecating them.

## Schemas and tables

| Constant | Value | What it names |
| --- | --- | --- |
| `MANIFEST_SCHEMA_VERSION` | `1` | the tool manifest schema |
| `HARD_BLOCK_TABLE_VERSION` | `1` | the hard-block decision table |
| `_SELF_MODEL_VERSION` | `v0` | the self-model returned by the meta syscalls |

## Reading a mismatch

If two artifacts disagree on a version, the question is which of these moved.
A commitment that no longer verifies after an upgrade is expected behaviour if
`CANONICALIZATION_VERSION` or `COMMITMENT_VERSION` changed, and a defect
otherwise.
