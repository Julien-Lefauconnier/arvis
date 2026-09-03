# Audit finding identifiers and structural decisions

Identifiers cited by code comments that come from the audits rather
than from a campaign decision. The `-a5`/`-a6` suffixes name the
audit that raised or refined the finding (audit 5, audit 6); the
`A14-`/`A15-` prefixes come from the numbered beta audits.

## P0-1-a6

The intent/result bijection is verified where the journals are read,
before any commitment composition: an absent journal is
`audit_incomplete`, never a vacuous pass (`api/os.py`; the underlying
defect was fixed by campaign KERNEL and shipped in 0.1.0b6).

## P0-2

Audit finding: the gate-kernel acceptance shortcut fired on every
stable live turn, bypassing the worst-axis and abstain guards. Closed
by DM-G3 (campaign GATE-SEM).

## P0-2-a6

The `commitment_inputs` block is validated structurally; a malformed
block is a typed error (`CommitmentInputsValidationError`), not a
silently different commitment.

## P0-3-a6

Redaction primitives live at the kernel boundary
(`kernel_core/syscalls/engagement.py`): the syscall handler engages
effect parameters before the effect and cannot import the API layer;
the API re-exports them so the public surface is unchanged.

## P0-4

Audit finding: `API_FINGERPRINT` was computed eagerly during package
import and always carried the bootstrap fallback. Closed by DM-I1
(lazy computation from the real surface).

## P0-5

Audit finding: four divergent canonical JSON encoders; the public
`hash_ir` did not reproduce the engine's committed digest. Closed by
DM-I2 (one encoder).

## A14-BETA-01

A capability surface returned to a caller is caller-owned canonical
bytes, never the private capture itself: no reference obtained from
the registry can mutate what a later run relies on
(`tools/registry.py`).

## A14-BETA-02

Consumers never derive a verdict from the repr of an internal object:
the public decision contract is the typed `DecisionStatus` plus the
structured `decision` block of `to_dict()`
(`api/views/decision_status.py`).

## A15-BETA-02

The final public payload natively carries every parameter its
reflexive attestation needs: a consumer can verify without reaching
into internals (`reflexive/snapshot/reflexive_snapshot.py`).

## D-a

Replay decision: the non-cognitive commitment components ride in the
exported IR as a `commitment_inputs` block, outside the cognitively
hashed region, so replay can rebind them without disturbing the
cognitive digest (`api/commitment.py`). The same decision letters the
rule that replay reapplies the RECORDED runtime postures, never the
replayer's environment (`apply_runtime_postures`).

## DS3

Single-writer channel doctrine for `conflict_pressure`: the temporal
stage owns the write, the control stage consumes the clamped
modulation (`cognitive_pipeline_context.py`).
