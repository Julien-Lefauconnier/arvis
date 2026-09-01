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
inside the projected domain**. Four conditions, in the order a host
meets them:

1. the host carries the trajectory across turns,
2. the switching guard has a dwell history,
3. the projected observation sits inside the domain, away from its
   dangerous bounds,
4. the composite energy actually decreases on that turn.

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

## 2. The switching guard needs a dwell history

The switching condition is `ln(J) / tau_d < kappa_eff`, where
`tau_d` is the dwell time: how long the system has stayed in one
regime. A fresh runtime has `tau_d = 0`, which makes the left-hand
side enormous and the guard unsafe, and adds
`switching_unsafe_monitoring` to the reasons.

**This is the honest v0 limit.** The dwell clock lives on a live
runtime object inside the pipeline, and the opaque blob of step 1
does not carry it, so a host driving ARVIS through `ArvisEngine`
cannot yet accumulate dwell time across calls. A host that owns the
pipeline directly (a deep integration) can, by carrying the
switching runtime across turns; the measured effect is `tau_d`
climbing 0 → 38 over 20 turns, after which the switching reason
disappears.

Carrying the dwell clock through the public contract is planned work,
not a configuration you are missing.

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

On the D-2.0 corpus, whose feedback family contracts on every turn
(`p_contraction = 1.000`), the gate's own pre-verdict is `ALLOW` on
102 of 192 turns: the energy criterion is reachable and reached.

## What 0.1.x does not let you reach

Being explicit, since the campaigns measured it: **`ALLOW` as a
final verdict was observed 0 times across the 3072 turns of both M10
campaigns.** Where the gate said `ALLOW` (102 turns), later layers
floored it: the local soft filter with `projection_unsafe` and
`projection_lyapunov_incompatible`, and the adaptive hard veto.

So today, a `0.1.x` host should design for a two-level ladder
(`REQUIRES_CONFIRMATION` and `ABSTAIN`) and treat `ALLOW` as a
capability under construction, not as the normal outcome of a
healthy run. The graded input-risk path is the one place where the
ladder is fully exercised today, with zero bleed between bands (see
M10 section 10.3).

If your integration needs `ALLOW` to be reachable, the open items
are the dwell clock of step 2 and the soft-filter conditions above.
Both are tracked; neither is a setting you can flip.

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
five.
