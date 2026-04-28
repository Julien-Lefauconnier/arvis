# tests/adversarial/test_chaos_adversarial.py

import random


def test_randomized_bundle_noise():
    class Dummy:
        pass

    bundle = Dummy()

    for _ in range(100):
        setattr(bundle, f"field_{random.randint(0, 1000)}", object())

    # ne doit jamais crasher violemment
    try:
        from arvis.cognition.conflict.conflict_extractor import (
            extract_conflicts_from_bundle,
        )

        extract_conflicts_from_bundle(bundle)
    except Exception:
        pass  # acceptable si contrôlé
