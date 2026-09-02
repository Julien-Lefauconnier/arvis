# The path to ALLOW

Every quickstart run of ARVIS ends in `REQUIRES_CONFIRMATION`. That
surprises integrators, who reasonably conclude the kernel blocks
everything. It does not: it certifies nothing it has not measured,
and a first turn has measured nothing.

This page is the honest map of what stands between a call and an
`ALLOW`, what a host can do about each item today, and what it
cannot do yet in 0.1.x. Every statement here was measured on the
current tree; the numbers come from the M10 campaigns
(`docs/math/M10_empirical_stability_validation_and_runtime_validation.md`).

## The short answer

`ALLOW` requires a **measured contraction on a threaded trajectory
inside the projected domain**. Five conditions, in the order a host
meets them:

1. the host carries the trajectory across turns,
2. the input carries structured signals, so there is an energy to
   measure at all,
3. the projected observation sits inside the domain, away from its
   dangerous bounds,
4. the composite energy actually decreases on that turn,
5. it decreases by more than the soft-filter threshold.

Miss any one and the verdict floors at `REQUIRES_CONFIRMATION`. That
is the monotone-hardening doctrine (F-001) doing its job: a floor is
never silently lifted.

## 1. Carry the trajectory (the host contract)

A single `ask()` measures one point. The stability monitor needs a
sequence, so it starts in the `warmup` regime and stays there until
it has enough samples (10 by default, `MonitorConfig.regime_min_samples`).

The contract is one opaque blob, in and out:

```python
from arvis import ArvisEngine

engine = ArvisEngine()
state = None

for question in questions:
    extra = {"scientific_state": state} if state is not None else None
    view = engine.ask(question, user_id="u1", extra=extra)
    state = view.next_scientific_state          # carry it forward
```

`next_scientific_state` is opaque on purpose: ARVIS never asks a host
to understand it, only to hand it back. It is deliberately absent
from `to_dict()`, which carries the decision contract, not host
plumbing.

Runnable version: `examples/07_session_threading.py`. Without
threading the regime stays `warmup` forever, however many calls the
host makes; with it, the regime moves at turn 9.

## 2. Give the kernel something to measure

A bare informational input, a plain text prompt with no structured
signals, does not produce a full cognitive projection. ARVIS attaches
the minimal certificate (see `arvis/kernel/projection/certificate.py`)
so the turn is still governed rather than surprisingly rejected, but
there is no composite energy on that path: `delta_w` stays `None`,
and a contraction that was never measured is never certified.

Measured on the public contract: 40 threaded turns of plain text
prompts return `REQUIRES_CONFIRMATION` throughout, `delta_w` `None`
on every one of them. Threading is necessary and it is not
sufficient.

If your integration only ever sends bare prompts, treat
`REQUIRES_CONFIRMATION` as the correct and permanent answer. `ALLOW`
is not withheld from you; it is undefined for that input.

## 3. Stay inside the domain, away from the dangerous bounds

The projected observation must be inside the certified domain, and
far enough from the bounds that matter. Two distinct things:

- **domain validity**: the five projected axes (`state.system_tension`,
  `state.coherence_score`, `risk.conflict_pressure`,
  `control.control_signal`, `trace.adaptive_kappa_eff`) must be
  present and in range. A missing axis is not certified.
- **boundary margin**: the distance to the nearest *dangerous* bound
  must exceed `projection_boundary_threshold` (0.1 by default).

Until campaign FIX, the margin measured the distance to the nearest
bound whatever it meant, so an axis at its *healthy* extreme counted
as boundary proximity. `risk.conflict_pressure` is fed by the
collapse risk, whose healthy value is exactly 0.0, its lower bound:
a system at zero collapse risk was read as sitting on the domain
edge and floored. The healthier the run, the closer to the "edge".
Bounds now declare which end means danger; the fix removed 909
spurious boundary flags on the D-2.0 corpus (1376 turns to 467)
without moving a single verdict.

Practical consequence for a host: supply the five axes, and keep
them off their dangerous ends (high tension, low coherence, high
conflict, saturated or absent control).

## 4. The energy has to actually decrease

The gate certifies a measured contraction, not a calm-looking
snapshot. With a perfectly static input the composite energy is
constant, `delta_w = 0.0`, and a zero delta is not a contraction:
the verdict floors at `REQUIRES_CONFIRMATION`. This is by design and
will not change: `ALLOW` means "the trajectory demonstrably
contracted", not "nothing bad was observed".

Until campaign ALLOW, this section described a condition the kernel
could not actually evaluate. The projection certificate assessed its
Lyapunov axis against `ctx._dv`, a private attribute holding the
drift score, which is clamped to [0, 1] and therefore never
negative. Any drift at all was published as a measured Lyapunov
incompatibility, which floored the verdict twice over
(`projection_unsafe` and `validity_projection_unavailable`). The
axis is now assessed against the composite energy delta or reported
unassessed, and the two reason codes went from 1270 occurrences on
the D-2.0 corpus to zero. M10 section 12 has the full account.

## 5. It has to decrease by enough

A contraction weaker than `delta_w_soft_threshold` (-0.05 by
default) is floored with reason `weak_stability`, in the local soft
filter of the decision stack. A turn whose energy fell by 0.04 is
contracting, and it will still land on `REQUIRES_CONFIRMATION`.

This is currently the dominant remaining floor. On the D-2.0 corpus
it accounts for 108 of the 113 turns where the gate's own pre-verdict
is `ALLOW` and the final verdict is not. The constant is
conventional, not calibrated; the M10 campaigns now publish the ΔW
scale a calibration would need, and that calibration is tracked as
its own change rather than tuned in place.

## What 0.1.x lets you reach

`ALLOW` is reachable. Measured on the current tree, across both M10
campaigns:

| | D-1.0 (1440 turns) | D-2.0 (1632 turns) |
|---|---|---|
| ALLOW | 22 (1.53%) | 6 (0.37%) |
| REQUIRES_CONFIRMATION | 185 | 349 |
| ABSTAIN | 1233 | 1277 |

Every one of those turns has a strictly negative composite delta,
and they occur only in the `nominal` and `long_horizon` families.
The `adversarial`, `conflicting`, `boundary`, `declared_risk`,
`switching_stress` and `nominal_feedback` distributions are
unchanged by the fix, and adversarial `ALLOW` remains 0.0.

Conditional on a turn that actually contracted, `ALLOW` reaches
3.8% overall on D-1.0 and 15.8% on its nominal family.

So a 0.1.x host should still design for the two-level ladder
(`REQUIRES_CONFIRMATION` and `ABSTAIN`) as the common case, and
treat `ALLOW` as an outcome that a well-instrumented, threaded,
genuinely contracting session can now reach rather than a capability
under construction.

## What 0.1.x still does not let you reach

The switching guard needs a dwell history. The switching condition is
`ln(J) / tau_d < kappa_eff`, where `tau_d` is how long the system has
stayed in one regime. A fresh runtime has `tau_d = 0`, which makes
the left-hand side enormous and adds `switching_unsafe_monitoring`
to the reasons.

The dwell clock lives on a live runtime object inside the pipeline,
and the opaque blob of step 1 does not carry it, so a host driving
ARVIS through `ArvisEngine` cannot yet accumulate dwell time across
calls. A host that owns the pipeline directly (a deep integration)
can, by carrying the switching runtime across turns; the measured
effect is `tau_d` climbing 0 to 38 over 20 turns, after which the
switching reason disappears.

Carrying the dwell clock through the public contract is planned work,
not a configuration you are missing.

## Debugging your own runs

The reasons are exported on every turn. With a host-supplied `extra`
dict you can read the whole journal back:

```python
bag = {}
view = engine.ask("...", user_id="u1", extra=bag)

bag["fusion_reasons"]            # why the verdict was floored
bag["projection_margin"]         # distance to the dangerous bounds
bag["projection_trace"]["view"]  # the five normalized axes
bag["switching_metrics"]         # tau_d and the switching decision
bag["verdict_transition_trace"]  # every tightening, with its stage
```

A verdict you did not expect is always explained by one of those
five. `delta_w` at `None` in the same bag is the signature of step 2:
nothing was measured, so nothing could be certified.
