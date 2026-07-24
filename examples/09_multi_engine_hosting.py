# examples/09_multi_engine_hosting.py

"""Host-side parallelism: one engine per unit of work.

An ARVIS engine executes one governed run at a time and is not
thread-safe. Parallelism belongs to the host: create one engine per
unit of work (a request, a workload, a tenant). Engines living in the
same process are isolated by construction, so concurrent workers never
share cognitive state, tool surfaces or commitments.

This example screens three independent workstreams concurrently, each
worker creating its own engine, under the same three-band declared-risk
policy (low -> APPROVED, medium -> REVIEW, high -> BLOCKED).
"""

from concurrent.futures import ThreadPoolExecutor

from arvis import CognitiveOS

WORKSTREAMS: dict[str, list[float]] = {
    "compliance": [0.10, 0.50, 0.90],
    "payments": [0.10, 0.90],
    "trading": [0.50],
}


def screen_workstream(stream: str, risks: list[float]) -> list[tuple]:
    # One engine per unit of work, created inside the worker: the host
    # parallelizes by instantiation, never by sharing an engine.
    engine = CognitiveOS()
    rows = []
    for risk in risks:
        result = engine.run(f"host_{stream}", {"risk": risk})
        decision = result.to_dict()["decision"]

        allowed = "allowed=True" in decision
        needs_confirm = "requires_user_validation=True" in decision

        if allowed and not needs_confirm:
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
    print("Engines      :", len(WORKSTREAMS), "(one per workstream)")
    print("Decisions    :", len(rows))
    print("Traceability : PER ITEM")
    print()
    print("Takeaway     : Parallelism belongs to the host. One engine per")
    print("               unit of work; engines in one process are isolated")
    print("               by construction.")


if __name__ == "__main__":
    main()
