# examples/00_quickstart_engine.py

import sys
from pprint import pformat

from arvis import ArvisEngine


def main():
    engine = ArvisEngine()

    result = engine.ask(
        "Should this high-risk wire transfer be approved?",
        user_id="demo",
    )

    print("=== ARVIS Quickstart ===")
    print()
    print(result.explain())

    if "--brief" in sys.argv:
        return

    if "--json" in sys.argv:
        print()
        print("JSON Output:")
        print(result.to_json())
        return

    if "--full" in sys.argv:
        print()
        print("Structured Output:")
        print(pformat(result.to_dict(), sort_dicts=False))
        return

    print()
    print("Structured Output:")
    print(result.quickstart_json())


if __name__ == "__main__":
    main()
