# tests/kernel/stages/test_projection_stage_pi_operator.py

from arvis.kernel.pipeline.stages.projection_stage import ProjectionStage
from arvis.kernel.projection.validator import ProjectionValidator


class DummyPiImpl:
    def project(self, ctx):
        class DummyState:
            def to_projection_view(self):
                return {
                    "state.system_tension": 5.0,
                    "risk.conflict_pressure": -3.0,
                }

        return DummyState()

    def project_previous(self, ctx):
        return None


class DummyValidator:
    def validate(self, projection_view, previous_projected=None, ctx=None):
        class Cert:
            domain_valid = True
            margin_to_boundary = 1.0
            certification_level = type("L", (), {"value": "FULL"})()
            lyapunov_compatibility_ok = True
            is_projection_safe = True

        return Cert()
    

def test_projection_stage_applies_pi_operator():
    stage = ProjectionStage()

    class Pipeline:
        pi_impl = DummyPiImpl()
        projection_validator = DummyValidator()

        # IMPORTANT : ajoute ton operator ici
        from arvis.math.projection.pi_operator import PiOperator
        pi_operator = PiOperator()

    class Ctx:
        projection_certificate = None
        extra = {}

    ctx = Ctx()

    stage.run(Pipeline(), ctx)

    assert abs(ctx.projection_view["state.system_tension"]) < 1.0
    assert abs(ctx.projection_view["risk.conflict_pressure"]) < 1.0
    assert ctx.projection_view_raw["state.system_tension"] == 5.0
    assert ctx.projection_view_raw["risk.conflict_pressure"] == -3.0


def test_projection_stage_fallback_still_applies():
    stage = ProjectionStage()

    class EmptyPiImpl:
        def project(self, ctx):
            class DummyState:
                def to_projection_view(self):
                    return {}

            return DummyState()

        def project_previous(self, ctx):
            return None

    class Pipeline:
        pi_impl = EmptyPiImpl()
        projection_validator = DummyValidator()

        from arvis.math.projection.pi_operator import PiOperator
        pi_operator = PiOperator()

    class Ctx:
        projection_certificate = None
        extra = {}

    ctx = Ctx()

    stage.run(Pipeline(), ctx)

    assert "state.system_tension" in ctx.projection_view
    assert "state.system_tension" in ctx.projection_view_raw



def test_projection_stage_passes_previous_projection():
    stage = ProjectionStage()

    class PiImplWithPrevious(DummyPiImpl):
        def project_previous(self, ctx):
            return {"state.system_tension": 0.5}

    class Pipeline:
        pi_impl = PiImplWithPrevious()
        projection_validator = DummyValidator()

        from arvis.math.projection.pi_operator import PiOperator
        pi_operator = PiOperator()

    class Ctx:
        projection_certificate = None
        extra = {}

    ctx = Ctx()

    stage.run(Pipeline(), ctx)

    assert ctx.projection_certificate is not None


def test_projection_validator_rejects_high_divergence():

    class DummyDomain:
        def validate(self, projected):
            return True, {}

        def margin_to_boundary(self, projected):
            return 1.0

    validator = ProjectionValidator(domain=DummyDomain())

    class Ctx:
        _dv = 0.5  # divergence forte

    cert = validator.validate({"x": 0.1}, ctx=Ctx())

    assert cert.lyapunov_compatibility_ok is False
    assert cert.certification_level.value != "LOCAL"


def test_projection_validator_accepts_stable():

    class DummyDomain:
        def validate(self, projected):
            return True, {}

        def margin_to_boundary(self, projected):
            return 1.0

    validator = ProjectionValidator(domain=DummyDomain())

    class Ctx:
        _dv = -0.1  # stabilisation

    cert = validator.validate({"x": 0.1}, ctx=Ctx())

    assert cert.lyapunov_compatibility_ok is True


def test_projection_validator_prefers_delta_w_over_dv():

    class DummyDomain:
        def validate(self, projected):
            return True, {}

        def margin_to_boundary(self, projected):
            return 1.0

    validator = ProjectionValidator(domain=DummyDomain())

    class Ctx:
        delta_w = 0.2
        _dv = -0.5

    cert = validator.validate({"x": 0.1}, ctx=Ctx())

    assert cert.lyapunov_compatibility_ok is False


def test_projection_validator_rejects_positive_delta_w():

    class DummyDomain:
        def validate(self, projected):
            return True, {}

        def margin_to_boundary(self, projected):
            return 1.0

    validator = ProjectionValidator(domain=DummyDomain())

    class Ctx:
        delta_w = 0.01

    cert = validator.validate({"x": 0.1}, ctx=Ctx())

    assert cert.lyapunov_compatibility_ok is False
    assert cert.certification_level.value == "BASIC"