# tests/kernel/mocks/dummy_core_model.py


class DummyCoreModel:
    def compute(self, bundle):
        return type(
            "CoreSnapshot",
            (),
            {
                "collapse_risk": 0.1,
                "drift_score": 0.05,
                "stable": True,
                "regime": "stable",
                "prev_lyap": 0.1,
                "cur_lyap": 0.09,
            },
        )()
