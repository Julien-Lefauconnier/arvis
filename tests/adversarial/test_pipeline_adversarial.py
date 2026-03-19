# tests/adversarial/test_pipeline_adversarial.py

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline


def test_pipeline_resilience_to_failure(monkeypatch):
    pipeline = CognitivePipeline()

    def crash(*args, **kwargs):
        raise Exception("boom")


    # on casse une méthode réellement appelée dans le pipeline
    monkeypatch.setattr(
        "arvis.cognition.governance.governance_evaluator.GovernanceEvaluator.evaluate",
        crash,
    )

    result = pipeline.run_from_input({})

    # le pipeline doit survivre
    assert result is not None