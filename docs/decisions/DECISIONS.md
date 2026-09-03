# DM-** campaign decisions

One entry per decision identifier cited in the code, in campaign
order. Each says what was decided, why, and where it is enforced.
Dates are 2026; the full narratives live in `CHANGELOG.md` and the
commit messages of the campaign patches.

## MATH-B

### DM-B0

Adaptive observability reads are direct and typed: the estimator
snapshot carries its own fields, consumers stop duck-reading through
`ctx.extra` (`adaptive_runtime_observer.py`).

## FIX

### DM-F1

The global-stability duck default is fail-closed and identical in
both layers: a host context that never declared
`global_stability_action` confirms, in the math layer AND the kernel
layer. Pinned by `test_global_stability_duck_default.py`.

### DM-F2

A host that declared no LLM runtime is a quiet, expected
configuration: the missing-binding condition is downgraded from error
noise to a documented state (`pipeline_llm_service.py`).

### DM-F3

The projection margin measures only DANGEROUS bounds: absence of a
margin is a designed state meaning no dangerous bound is in play this
turn, not a sensor failure. Consumed by DM-H7 (typed absence in the
Pi layer).

## ALLOW / PROJ

### DM-P1

The projection operator's drift REACTION is removed: drift is
observed and journaled, it no longer mutates the operator mid-turn
(`math/projection/pi_operator.py`).

### DM-P2

Projection refresh is a post-hoc attestation, not a silent
re-projection: a refreshed view is distinguishable from the view the
decision was taken on (pinned by the projection tests).

## SEUIL and SURFACE (shared identifier)

### DM-S1

Two campaigns used this identifier; both meanings are load-bearing:

- SEUIL DM-S1: the weak-stability threshold is a REGISTERED rate rule
  (weak iff `|dW| < max(0.05*W, 0.005)`), registered by the owner
  before the campaign ran; constants live in
  `weak_stability_policy.py`; an explicit `delta_w_soft_threshold` on
  the context stays an absolute host override.
- SURFACE DM-S1: the public contract is exactly two surfaces, the
  root `arvis` (11 symbols) and `arvis.host_api`; `arvis.api` is the
  internal aggregator; the four dead `arvis.api` facades were
  deleted with their absence pinned.

### DM-S2

Production identity reaches both entrypoints: `ArvisEngine.run_as`
delegates to `CognitiveOS.run_as` with the exact-type stamp;
`host_api` exports `CognitiveOS`, `AuthenticatedPrincipal` and the
tool-policy objects; examples import only the two supported surfaces
(ratcheted).

### DM-S3

The host-side `CognitiveControlEngine` stays in the repository,
declared for what it is: a control runtime a host may run, never the
producer of the governed verdict. A structural ratchet
(`test_control_engine_isolation.py`) keeps the kernel from importing
it.

### DM-S4

One threading contract: the host reads the next scientific state from
`view.next_scientific_state`; the `extra["scientific_state_next"]`
echo is deprecated and kept only through the deprecation window.

### DM-S5

Vocabulary is typed without moving a serialized byte: verdict
conversions are total and fail-closed in one module per boundary
(`verdict_conversions.py`, `CognitiveGateVerdict.from_lyapunov`), the
gate postures are StrEnums with the historical wire values, the dead
duplicate `StabilityView` was deleted and `REFUS` became `REFUSAL`.

## GATE-SEM

### DM-G1

The adaptive layer fails CLOSED: the switching margin is computed on
the shared `DWELL_TIME_FLOOR`, so an empty dwell measures a violated
condition and vetoes instead of silently disappearing;
`adaptive_unavailable` is a normative reason with a
REQUIRE_CONFIRMATION floor.

### DM-G2

The validity envelope refuses `adaptive_available=False`, and (the
follow-up decision the M10 report records as DM-G2bis) the MEASURED
adaptive margin is what governs ALLOW; the assumed-constant T1
reading stays monitoring, disclosed through
`switching_safe_measured`.

### DM-G3

The gate-kernel acceptance shortcut is reserved for its declared
case, injected scalars without a Lyapunov quadruple (`cur_lyap is
None`), with the recovery floor applied; the live path always runs
the full `lyapunov_gate` guards (worst-axis, abstain threshold).

## INTEGRITY

### DM-I1

`api_fingerprint()` is computed lazily from the real surface
(sha256 of the sorted root `__all__`), never the bootstrap constant;
the module `__getattr__` keeps the legacy constant name working.

### DM-I2

ONE canonical JSON encoder (`ir/serialization/canonical_json.py`:
sorted keys, compact separators, ASCII, NaN refused) behind
`hash_ir`, the view's `ir_hash`, the decision-id mint and the replay
witness; the external-verifier recipe (hash the IR, recompose the
commitment) is pinned end to end.

### DM-I3

The stability view stops lying about risk: `risk_ucb` and
`risk_verdict` are exposed beside `collapse_risk` in the view, its
dict and the schema; the trace block separates regime from verdict.

## HARDEN

### DM-H1

The governed ZIP import never unlinks the host source archive;
`keep_zip` is an accepted no-op.

### DM-H2

`has_budget` checks the four deterministic dimensions `consume`
enforces; wall-clock time stays audit-only on both sides.

### DM-H3

The analyzer's `supported` verdict governs the content import: item
kept, content refused, skip recorded under the analyzer's reason.

### DM-H4

The interrupt bus's dead pub/sub half is deleted (subscribe half and
per-process subscription set had zero callers); `match` routes by
explicit target. Reintroducing pub/sub is a future design act.

### DM-H5

Governance fingerprints bind module + qualname (homonymous classes
cannot collide) and `config_fingerprint` includes
`confirmation_registry`; `host_context` (provenance, pinned doctrine)
and `telemetry_sink` (observe-only) are the two deliberate
exclusions, documented where they act.

### DM-H6

Ambient configuration is named (`ARVIS_`-prefixed), lazy, validated
(a malformed value is a typed error naming the variable, never an
import crash), documented in `docs/CONFIGURATION.md`, and ratcheted:
an environment read outside the registry fails the gate. The
effective ZIP limits are part of `config_fingerprint`.

### DM-H7

The Pi margin is `float | None`: absence is DM-F3's designed state
and stays neutral; a CERTIFIED 0.0 is the worst state and abstains;
the verdict is monotone over certified margins (the audit's
0.0-allows probe is pinned inverted).

### DM-H8

Recorded sensor degradations constrain the verdict: the escalation
predicate (`ErrorManager.should_escalate`) is consumed by a monotone
REQUIRE_CONFIRMATION floor (`sensor_degradation_floor`) at the end of
the decision stack. Sensors may fail open individually; the RECORD of
their failures may not fail silent.

### DM-H9

The decision constants live in one place, committed to: one kappa
band table (`kappa_bands.py`), one canonical
`DEFAULT_SWITCHING_PARAMS`, and `policies_fingerprint` covers both.

#### DM-H9c

The bootstrap small-gain check consumes the canonical switching
parameters instead of its own declared alpha.

#### DM-H9d

`theoretical_enforcement_mode` is a declared, typed, reachable
context posture (MONITOR default, STRICT reachable by a host).

#### DM-H9e

The three constants named `IR_VERSION` are renamed by meaning
(envelope, schema, state-adapter payload), wire values unchanged,
compatibility aliases kept on the internal surfaces.
