# examples/09_multi_engine_hosting.py

"""Host-side parallelism: one engine per governed turn.

An ARVIS engine executes one governed run at a time and is not
thread-safe. The documented lifecycle (docs/architecture/
RUNTIME_LIFECYCLE.md) is one instance per governed turn, discarded
afterwards: a reused instance accumulates state without bound.
Parallelism belongs to the host, by instantiation: engines living in
the same process are isolated by construction, so concurrent workers
never share cognitive state, tool surfaces or commitments.

This example screens three independent workstreams concurrently. Each
worker builds a fresh engine for every decision (the recommended
host-side factory pattern), under the same three-band declared-risk
policy (low -> APPROVED, medium -> REVIEW, high -> BLOCKED).
"""

from concurrent.futures import ThreadPoolExecutor

from arvis import CognitiveOS

WORKSTREAMS: dict[str, list[float]] = {
    "compliance": [0.10, 0.50, 0.90],
    "payments": [0.10, 0.90],
    "trading": [0.50],
}


def build_engine() -> CognitiveOS:
    """Host-side factory: one place to configure, one instance per turn."""
    return CognitiveOS()


def screen_workstream(stream: str, risks: list[float]) -> list[tuple]:
    rows = []
    for risk in risks:
        # One engine per governed turn, built fresh inside the loop:
        # no state carries over between decisions, and nothing
        # accumulates (RUNTIME_LIFECYCLE doctrine).
        engine = build_engine()
        result = engine.run(f"host_{stream}", {"risk": risk})
        decision = result.to_dict()["decision"]  # structured block (a15)

        needs_confirm = bool(decision["requires_user_validation"])

        if decision["status"] == "ALLOWED":
            status = "APPROVED"
        elif needs_confirm:
            status = "REVIEW"
        else:
            status = "BLOCKED"

        rows.append((stream, risk, status, result.global_commitment[:10] + "..."))
    return rows


def main() -> None:
    with ThreadPoolExecutor(max_workers=len(WORKSTREAMS)) as pool:
        futures = [
            pool.submit(screen_workstream, stream, risks)
            for stream, risks in WORKSTREAMS.items()
        ]
        rows = [row for future in futures for row in future.result()]

    rows.sort(key=lambda r: (r[0], r[1]))

    print("\nARVIS Example 09: Multi-Engine Hosting")
    print("-" * 46)
    for stream, risk, status, commitment in rows:
        print(f"{stream:<11} Risk={risk:<4} {status:<9} {commitment}")

    print()
    print("Engines      :", len(rows), "(one per decision)")
    print("Decisions    :", len(rows))
    print("Traceability : PER ITEM")
    print()
    print("Takeaway     : Parallelism belongs to the host. One engine per")
    print("               governed turn, built by a host factory; engines in")
    print("               one process are isolated by construction.")


if __name__ == "__main__":
    main()
