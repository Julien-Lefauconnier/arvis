# Govern a real model call in fifteen minutes

This is the shortest honest path from `pip install` to a benefit you
can see: a dangerous action refused before it runs, and that refusal
replayed bit for bit for an auditor. It runs
`examples/14_govern_a_real_model_call.py`, first offline, then with
your own model.

The pattern matters more than the code: **the model proposes, your
policy prices, ARVIS decides.** ARVIS is not another model client
and does not sit between you and your provider SDK; your application
calls the model however it already does, and consults the kernel
before an act happens.

## Minute 0 to 3: install and run offline

```bash
pip install arvis
python examples/14_govern_a_real_model_call.py
```

No key, no network: a deterministic canned model stands in. You see
three proposals cross the three verdict bands:

```text
[step 1] model proposes: read_report      -> ALLOWED
[step 2] model proposes: email_summary    -> REQUIRES_CONFIRMATION
[step 3] model proposes: wire_transfer    -> BLOCKED
```

and then the part that distinguishes governance from filtering: the
blocked step is replayed from its exported record and authenticated
against the stored commitment.

## Minute 3 to 8: read the thirty lines that did it

Three pieces, all host-owned.

The risk policy is yours, a plain dict from action class to risk:

```python
RISK_POLICY = {
    "read_report": 0.05,
    "email_summary": 0.50,
    "wire_transfer": 0.95,
}
```

The model only ever proposes an action name. It never declares its
own risk: a model-declared risk would be untrusted input, and the
kernel lets a declared risk harden a verdict, never relax it
(invariant F-001-a5 in
[docs/decisions/INVARIANTS.md](decisions/INVARIANTS.md)).

The governed turn is three lines, one engine per turn (the
documented lifecycle):

```python
engine = ArvisEngine()
result = engine.run("ops", {"risk": RISK_POLICY[action]})
# result.status: ALLOWED / REQUIRES_CONFIRMATION / BLOCKED
```

And the audit trail is not an add-on: every turn already carries its
commitment, and the blocked turn replays from its exported IR
against the anchor you stored:

```python
replayed = ArvisEngine().os.replay_verified(
    blocked_run.to_ir(),
    expected_global_commitment=anchor,
)
```

## Minute 8 to 15: plug in your real model

```bash
export ANTHROPIC_API_KEY=...   # or OPENAI_API_KEY
python examples/14_govern_a_real_model_call.py --live
```

The example asks the model to pick the next action; everything
downstream is byte-for-byte the same path you just ran offline. Any
model failure falls back to the canned proposals, loudly, because
governance must not depend on the model being reachable.

To wire your own application instead of the example, replace the
`propose` function with your existing model call (any SDK, any
provider) and the `RISK_POLICY` dict with your action classes. That
is the whole integration for the explicit-risk contract. The example
calls your provider's SDK directly on the host side on purpose: the
bundled LLM adapters exist but are experimental, and the governed
verdict never depended on them.

## What you did and did not get

You got the governance loop: per-turn verdicts under your policy, a
dangerous act stopped before execution, human confirmation as a
first-class state, and a replayable, hash-committed record of every
decision.

You did not get content moderation (nothing here inspects what the
model says; run a content guardrail alongside if you need one), and
you did not yet get measured
stability: that needs the host to thread the scientific state across
turns and to feed structured signals, which is the next fifteen
minutes ([GETTING_STARTED.md](GETTING_STARTED.md), example 13, and
[PATH_TO_ALLOW.md](PATH_TO_ALLOW.md) for what separates a call from
an ALLOW).
