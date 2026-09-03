# Getting started: a governed memory assistant

This walkthrough builds the smallest integration that exercises every
part of ARVIS a real host touches: a memory assistant that remembers
notes, recalls them, and sometimes wants to send one outside. The
finished program is `examples/13_governed_memory_assistant.py`; every
snippet below comes from that file, and running it prints exactly the
output this page narrates.

The pattern is the generic one from the
[reference assistant architecture](architecture/REFERENCE_ASSISTANT_ARCHITECTURE.md);
the [VeraMem integration pattern](integration/VERAMEM_INTEGRATION_PATTERN.md)
shows the same pattern projected into a production host.

## Setup

```bash
pip install arvis
python examples/13_governed_memory_assistant.py
```

(For a source checkout: `pip install -e ".[dev]"` in a virtualenv, per
the README.)

## The mental model in one paragraph

ARVIS is not the assistant. The assistant, its memory, and its tools
belong to the host; ARVIS is the one-turn kernel the host consults
before acting, and the verdict comes back in one of three bands:
`ALLOWED`, `REQUIRES_CONFIRMATION`, or `BLOCKED`. The bands are
monotone (enforcement layers can harden a verdict, never relax it,
invariant F-001 in [docs/decisions/INVARIANTS.md](decisions/INVARIANTS.md)),
and the default is conservative: a bare, unstructured prompt lands in
`REQUIRES_CONFIRMATION` because nothing has been measured yet.
[PATH_TO_ALLOW.md](PATH_TO_ALLOW.md) is the honest map of what it
takes to earn an `ALLOW`; this walkthrough follows exactly that path.

## Step 1: declare the tool surface and freeze it

The assistant has two capabilities, and each declares what it really
does in its `ToolSpec` manifest:

```python
class RememberNoteTool(BaseTool):
    spec = ToolSpec(
        name="remember_note",
        side_effectful=True,
        reversible=True,        # a local write can be undone
        max_risk=0.5,
        data_class="personal",
        ...
    )

class ShareNoteTool(BaseTool):
    spec = ToolSpec(
        name="share_note",
        side_effectful=True,
        reversible=False,       # a sent mail cannot
        provider="mail",
        data_egress=True,       # personal data leaves the boundary
        required_consent="recipient_consent",
        max_risk=0.4,
        ...
    )
```

The contrast is the lesson: a local reversible write and an
irreversible egress of personal data are different acts, and the
manifest is where that difference is stated once, honestly, instead
of being rediscovered in every call site.
[tools/TOOL_AUTHORING_GUIDE.md](tools/TOOL_AUTHORING_GUIDE.md) covers
every field.

The host registers both tools and freezes the surface:

```python
engine = ArvisEngine()
engine.register_tool(RememberNoteTool())
engine.register_tool(ShareNoteTool())
surface_fingerprint = engine.freeze_tools()
```

After `freeze_tools()` the surface is pinned (invariant F-004): late
registration is refused, and the returned fingerprint names exactly
this set of manifests. The example rebuilds one engine per governed
turn, the documented lifecycle, and the fingerprint is deterministic,
so every turn commits to the same surface.

## Step 2: govern the first act

```python
result = engine.run("alice", {"risk": 0.10})
state = result.next_scientific_state
```

The `{"risk": ...}` payload is the explicit-risk input contract (the
one example 11 uses): the host has assessed the proposed act and
declares its risk. A low-risk local write is `ALLOWED`; the host then
applies the write to its own memory. In production that write is a
governed `remember_note` invocation through the syscall path
([architecture/EFFECT_PATH.md](architecture/EFFECT_PATH.md)); the
example never calls `tool.execute` directly, because that would
bypass everything this page teaches.

```text
[turn 1] remember the note (first turn, unthreaded)
  status   : ALLOWED
  effect   : host stored note 'friday'
```

## Step 3: thread the state

The kernel is one-turn by design; continuity belongs to the host. The
result view hands back an opaque, JSON-safe `next_scientific_state`,
and the host passes it into the next turn:

```python
result = engine.run("alice", {"risk": 0.05},
                    extra={"scientific_state": state})
```

That thread (contract DM-S4 in
[docs/decisions/DECISIONS.md](decisions/DECISIONS.md)) is what makes
the trajectory measurable at all. Drop it and every turn is a
conservative first turn again.

## Step 4: an externalizing act meets two independent locks

Turn 3 proposes sharing the note with an external recipient, at a
materially higher declared risk. Two locks act, and neither depends
on the other.

The first lock is the verdict band: 0.55 lands in the confirmation
band, so nothing happens without a bound user validation.

```text
[turn 3] share the note with bob@example.org (threaded)
  status   : REQUIRES_CONFIRMATION
  needs user validation: True
```

The second lock is the tool policy: even a confirmed turn cannot
invoke `share_note` above the risk budget its own manifest declares.
`ToolPolicyEvaluator` denies the invocation (`risk_exceeded`, 0.55
against a declared `max_risk` of 0.4), exactly as example 05 shows in
isolation.

The manifest also declares `required_consent` and `data_egress`.
Those gates belong to the host: in the PRODUCTION profile a tool
declaring either is denied by default when the matching host gate is
missing (invariants F-017 and F-018 in
[docs/decisions/INVARIANTS.md](decisions/INVARIANTS.md)); other
profiles leave the decision to the host. The example therefore prints
the manifest rather than simulating a denial it did not measure.

## Step 5: the trajectory comes alive

The assistant keeps working: seven more routine, low-risk recall
turns on the same thread. Nothing else changes, and the measured
regime graduates on its own:

```text
[turns 4..10] routine recalls, one thread
  turn 4:  regime=warmup     stability=0.85
  ...
  turn 10: regime=transition stability=0.85
```

This is the point of threading. The contraction monitor needs a
window of measured turns before it certifies anything about the
trajectory; the regime leaving `warmup` is the first visible sign of
that window filling. What stands between here and a measured `ALLOW`
on richer inputs is exactly the list in
[PATH_TO_ALLOW.md](PATH_TO_ALLOW.md).

## Step 6: read the audit trail back

Every turn commits to what governed it:

```text
[audit] the share turn's own record
  schema version    : 1.0
  api fingerprint   : 2425b5887aea8733...
  global commitment : 60bee5e15924c57f...
  trace / timeline  : True / True
```

The `global_commitment` composes the registry manifest fingerprint,
the effective configuration fingerprint, the active policy tables and
the redacted syscall journals (invariant F-007), so an auditor can
verify after the fact exactly which surface, configuration and
policies produced the verdict. Example 08 shows the hash-linked
timeline; example 02 shows deterministic replay of the same record;
[IR.md](IR.md) documents the exported form.

## Where to go next

Configuration that changes governed behavior is named, validated and
documented in [CONFIGURATION.md](CONFIGURATION.md), and the effective
values are part of the configuration fingerprint. Every decision
identifier cited in the code (`F-***`, `DM-**`, and the audit
findings) resolves in [docs/decisions/](decisions/README.md). The
example catalog in [examples/README.md](../examples/README.md) has
one focused example per concept this walkthrough composed; the
[reference assistant architecture](architecture/REFERENCE_ASSISTANT_ARCHITECTURE.md)
is the fuller version of the pattern, and
[CONTRIBUTING.md](../CONTRIBUTING.md) is the entry point for working
on ARVIS itself.
