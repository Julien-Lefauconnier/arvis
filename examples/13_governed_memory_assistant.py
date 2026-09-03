# examples/13_governed_memory_assistant.py
"""The full governance cycle of a memory assistant, end to end.

Every other example teaches one concept; this one runs the complete
cycle a real host lives through, on the generic memory-assistant
pattern of docs/architecture/REFERENCE_ASSISTANT_ARCHITECTURE.md
(the same pattern docs/integration/VERAMEM_INTEGRATION_PATTERN.md
projects into a production host):

1. declare a governed tool surface and freeze it;
2. govern a local, reversible act (remember a note): ALLOWED;
3. thread the scientific state and recall the note;
4. govern an externalizing act (share the note): the confirmation
   band and the tool policy each hold their own line;
5. keep threading routine turns and watch the measured regime
   graduate out of warmup;
6. read the audit trail back (commitment, fingerprints, trace).

The walkthrough narrative for this file is docs/GETTING_STARTED.md.
Like example 11, no tool effect runs through ``tool.execute`` here:
production effects go through the governed syscall path
(docs/architecture/EFFECT_PATH.md). The one write this file performs
is the host writing its OWN memory dict, after the verdict allowed
the act it stands for.
"""

from arvis import ArvisEngine, DecisionStatus
from arvis.host_api.tools import (
    AuthorizedEffectContext,
    BaseTool,
    ToolInvocation,
    ToolPolicyEvaluator,
    ToolSpec,
)

# ----------------------------------------------------------------- #
# 1. The host's memory and its governed tool surface                 #
# ----------------------------------------------------------------- #
# The memory itself belongs to the host (here: a dict). What ARVIS
# governs is every act touching it or leaving it.

HOST_MEMORY: dict[str, str] = {}


class RememberNoteTool(BaseTool):
    """Store a note in the host's memory: side-effectful but local,
    reversible, no third party involved."""

    name = "remember_note"
    spec = ToolSpec(
        name="remember_note",
        description="Store a note in the assistant's local memory.",
        side_effectful=True,
        reversible=True,
        max_risk=0.5,
        data_class="personal",
    )

    def execute(self, input_data):
        return {"stored": input_data["key"]}


class ShareNoteTool(BaseTool):
    """Send a stored note to an external recipient: egress of
    personal data, irreversible, consent declared. The manifest is
    the honest declaration governance reads."""

    name = "share_note"
    spec = ToolSpec(
        name="share_note",
        description="Send a stored note to an external recipient.",
        side_effectful=True,
        reversible=False,
        provider="mail",
        data_egress=True,
        data_class="personal",
        required_consent="recipient_consent",
        max_risk=0.4,
    )

    def execute(self, input_data):
        return {"sent": True}


def build_engine() -> tuple[ArvisEngine, str]:
    """Host factory: one configured engine per governed turn (the
    documented lifecycle); the frozen surface fingerprint is
    deterministic, so every turn commits to the same surface."""
    engine = ArvisEngine()
    engine.register_tool(RememberNoteTool())
    engine.register_tool(ShareNoteTool())
    return engine, engine.freeze_tools()


def governed_turn(declared_risk: float, state: dict | None):
    """Govern one host proposal under the explicit-risk input
    contract (the same contract example 11 uses), threading the
    scientific state per DM-S4."""
    engine, surface_fingerprint = build_engine()
    extra = {"scientific_state": state} if state is not None else {}
    result = engine.run("alice", {"risk": declared_risk}, extra=extra)
    return engine, surface_fingerprint, result


print("\nARVIS Example 13: a governed memory assistant, end to end")
print("=" * 60)

# ----------------------------------------------------------------- #
# 2. Remember a note: local, reversible, low declared risk           #
# ----------------------------------------------------------------- #
engine, surface, first = governed_turn(0.10, state=None)
state = first.next_scientific_state
print(f"\ntool surface frozen: {surface[:16]}...")

print("\n[turn 1] remember the note (first turn, unthreaded)")
print("  proposal :", "remember_note @ declared risk 0.10")
print("  status   :", first.status.value)
assert first.status is DecisionStatus.ALLOWED

# The verdict allowed the act, so the host applies it to its own
# memory. In production this write is a governed remember_note
# invocation through the effect path; ``tool.execute`` is never
# called directly.
HOST_MEMORY["friday"] = "the demo is on Friday"
print("  effect   : host stored note 'friday'")

# ----------------------------------------------------------------- #
# 3. Recall the note: threaded turn, read-only                       #
# ----------------------------------------------------------------- #
# The host stores the opaque scientific state and passes it back;
# that thread is what makes the trajectory measurable at all.
engine, _, second = governed_turn(0.05, state=state)
state = second.next_scientific_state

print("\n[turn 2] recall (threaded)")
print("  proposal :", "read-only recall @ declared risk 0.05")
print("  status   :", second.status.value)
print("  recalled :", HOST_MEMORY["friday"])
assert second.status is DecisionStatus.ALLOWED

# ----------------------------------------------------------------- #
# 4. Share externally: two independent locks                         #
# ----------------------------------------------------------------- #
# Lock one, the verdict band: an externalizing act at materially
# higher declared risk lands in the confirmation band, so nothing
# happens without a bound user validation.
engine, _, third = governed_turn(0.55, state=state)
state = third.next_scientific_state

decision = third.to_dict()["decision"]
print("\n[turn 3] share the note with bob@example.org (threaded)")
print("  proposal :", "share_note @ declared risk 0.55")
print("  status   :", decision["status"])
print("  needs user validation:", decision["requires_user_validation"])
assert third.status is DecisionStatus.REQUIRES_CONFIRMATION

# Lock two, the tool policy: even a confirmed turn cannot invoke
# share_note above the risk budget its own manifest declares.
invocation = ToolInvocation(
    tool_name="share_note",
    payload={"key": "friday", "recipient": "bob@example.org"},
    effect_context=AuthorizedEffectContext(
        principal="alice",
        tenant=None,
        authentication_source="example",
        authentication_strength="unattested",
        service_id=None,
        session_id_hash=None,
        process_id="demo",
        run_id=None,
    ),
    risk_score=0.55,
)
policy = ToolPolicyEvaluator.evaluate(invocation, engine.os.tool_registry)
verdict = "AUTHORIZED" if policy.allowed else f"DENIED ({policy.reason})"
print("  tool policy @ 0.55   :", verdict)
assert not policy.allowed

# The manifest also declares consent and egress. Those gates belong
# to the host: in the PRODUCTION profile a tool declaring
# required_consent or data_egress is denied by default when the
# matching host gate is missing (invariants F-017 and F-018,
# docs/decisions/INVARIANTS.md); this example profile leaves that
# decision to the host, which is why the manifest is printed rather
# than a denial simulated.
spec = engine.get_tool_spec("share_note")
print(
    "  manifest             :",
    f"provider={spec.provider},",
    f"egress={spec.data_egress}, irreversible={not spec.reversible},",
    f"consent={spec.required_consent}",
)

# ----------------------------------------------------------------- #
# 5. The trajectory comes alive: regime graduates out of warmup      #
# ----------------------------------------------------------------- #
print("\n[turns 4..10] routine recalls, one thread")
regimes: list[str] = []
for index in range(3, 10):
    engine, _, routine = governed_turn(0.05, state=state)
    state = routine.next_scientific_state
    view = routine.stability_view
    regimes.append(view.regime if view is not None else "none")
    print(
        f"  turn {index + 1}: regime={regimes[-1]:<10}"
        f" stability={view.stability_score:.2f}"
    )
assert "transition" in regimes, "the threaded regime should graduate"

# ----------------------------------------------------------------- #
# 6. The audit trail: what ran is what is committed                  #
# ----------------------------------------------------------------- #
payload = third.to_dict()
print("\n[audit] the share turn's own record")
print("  schema version    :", payload["schema_version"])
print("  api fingerprint   :", payload["fingerprint"][:16] + "...")
print("  global commitment :", (payload["global_commitment"] or "")[:16] + "...")
print("  trace / timeline  :", payload["has_trace"], "/", payload["has_timeline"])

print("\nTakeaway: the memory belongs to the host; every act touching it")
print("runs through the verdict bands, an externalizing act also has to")
print("clear the tool policy and the host's consent gates, and each turn")
print("is committed so an auditor can verify exactly what governed it.")
