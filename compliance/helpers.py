# compliance/helpers.py

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline


_pipeline = CognitivePipeline()


def run_ctx(ctx):
    return _pipeline.run(ctx)


def replay_from_ir(ir):
    return _pipeline.run_from_ir(ir)
