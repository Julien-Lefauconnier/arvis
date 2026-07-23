# Versioning and guarantee scope

This document states what a version number means, what the public API is, and
exactly how far the formal guarantees reach. It is normative: where it
disagrees with a blog post, a slide or a docstring, this document wins.

## Version scheme

ARVIS follows [PEP 440](https://peps.python.org/pep-0440/). During the `0.x`
series the version carries three claims and no more:

- `0.1.0aN` (alpha) — the public surface may change without a deprecation
  window. Pin an exact version.
- `0.1.0bN` (beta) — the public surface is stable within the series. A removal
  from the public API goes through the deprecation window below.
- `0.1.0` and later `0.x` — stable within the minor version. Breaking changes
  raise the minor number, since `0.x` has no major-version budget.

A patch release never changes the public API, never changes canonical bytes,
and never relaxes a check on the effect path.

## The public API is `arvis.__all__`

The stable surface is exactly what `arvis.__all__` exports. Everything else,
including every submodule reachable by import, is internal and may change in
any release.

This is enforced, not asserted: continuous integration fails if a name leaves
`arvis.__all__` without a deliberate change to the frozen list, and the effect
path's internal services are deliberately absent from it.

Importing an internal module is allowed. Depending on its stability is not.

## Deprecation window

From beta onwards, a name in the public API is removed in two steps:

1. it emits `DeprecationWarning` for at least one minor release, with the
   replacement named in the message;
2. it is removed in the following minor release.

Anything that changes canonical bytes (canonicalization, redaction policy,
commitment or confirmation formats) is not deprecated: it is versioned. The
format version changes, old hashes and confirmations are explicitly
invalidated, and the change is called out in the changelog. A stored
confirmation from an older format is never silently accepted.

Which constant governs which artifact, and what breaks when each one moves, is
mapped in [docs/VERSIONS.md](docs/VERSIONS.md). Two of them are both called
`IR_VERSION` and are not the same thing, which is worth knowing before reading
a mismatch as a defect.

## Guarantee scope

The formal results in `docs/math/` (M1 to M15) hold **on the documented
projected domain**, not on arbitrary inputs. This section states where the
runtime actually measures, so a reader can tell a proof from a default.

### The projection certificate

`ProjectionValidator` reports six axes. They are not all evaluated, and the
certificate says which:

| Axis | Status |
| --- | --- |
| `domain_valid` | measured against the declared domain constraints |
| `boundedness_ok` | measured (follows domain validity) |
| `lipschitz_ok` | measured when a previous projection is supplied; otherwise not exercised |
| `lyapunov_compatibility_ok` | measured when the context carries a Lyapunov signal; otherwise not exercised |
| `noise_robustness_ok` | **not assessed**: no estimator exists; domain validity is reused as a conservative monotonic proxy |
| `mode_stability_ok` | **not assessed**: nothing examines a mode transition |

The two unassessed axes are recorded in `checks_detail` as
`noise_robustness_assessed = False` and `mode_stability_assessed = False`, and
they are **excluded from the certification level**. A `LOCAL` certificate
therefore attests only axes that were measured. It is not a claim about noise
robustness, and `noise_gain_estimate` is always `None` because no measurement
stands behind it.

Implementing a real noise estimator is open work. Until it lands, no ARVIS
release should be read as certifying robustness to input noise.

### Certification levels

The runtime produces exactly three: `NONE`, `BASIC` and `LOCAL`, plus `MINIMAL`
for a bare informational input, attached so the turn is still governed rather
than rejected. `MINIMAL` is explicitly not a full cognitive projection.

`CERTIFIED_RUNTIME` exists in the enum and **is never produced**. No code path
awards it, so no artifact carries it. It is reserved, not attainable, and must
not be read as a level ARVIS can currently reach.

### What is out of scope entirely

- **LLM behaviour.** ARVIS governs what a model is allowed to do and records
  what it did. It makes no claim about the content a model produces.
- **Language-level risk projection.** The risk gate operates on an explicit
  scalar. Deriving that scalar from natural language is the host's problem.
- **Host identity.** ARVIS does not authenticate anyone. It requires the host
  to stamp an authenticated principal and refuses production effects without
  one; the truth of that stamp is the host's responsibility.
- **Distribution.** Registries are process-local. Coordination across workers
  or hosts is not provided.
- **Timeouts.** A tool timeout bounds the wait, not the work: a running call is
  not interrupted.

### What holds regardless

These are properties of the effect path, and they are exercised by the
adversarial suite rather than argued:

- an effect payload is frozen at authorization and cannot be mutated afterwards;
- a capability is single-use and bound to its sealed identity context;
- a result is cryptographically bound to the intent that authorized it;
- a production effect requires an authenticated principal, a qualified durable
  sink, and bound runtime identity;
- a value with no injective canonical encoding is refused, never collapsed to a
  type marker.

## Reporting a mismatch

If the runtime claims more than this document allows, that is a defect worth
reporting, and a security-adjacent one. See [SECURITY.md](SECURITY.md).
