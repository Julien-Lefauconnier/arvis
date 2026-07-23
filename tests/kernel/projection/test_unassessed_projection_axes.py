"""The certificate never attests an axis the validator did not measure.

Two of the six axes have no estimator: noise robustness reuses domain validity
as a conservative monotonic proxy, and mode stability examines nothing at all.
Both are still reported, so the certificate keeps a stable shape for its
consumers, but they are flagged unassessed in checks_detail and kept out of the
certification level.

That exclusion is the point. Certifying LOCAL on an axis that was never
evaluated would overstate what the certificate attests, and for a kernel that
advertises stability guarantees, an overstated guarantee is the failure that
matters most. These tests pin the honesty of that contract.
"""

from __future__ import annotations

from arvis.kernel.projection.certificate import ProjectionCertificationLevel
from arvis.kernel.projection.validator import ProjectionValidator


class _AlwaysValidDomain:
    def validate(self, projected):
        return True, {}

    def margin_to_boundary(self, projected):
        return 1.0


class _AlwaysInvalidDomain:
    def validate(self, projected):
        return False, {}

    def margin_to_boundary(self, projected):
        return -1.0


def test_the_unassessed_axes_are_flagged_as_such():
    certificate = ProjectionValidator(domain=_AlwaysValidDomain()).validate({"x": 0.1})

    assert certificate.checks_detail["noise_robustness_assessed"] is False
    assert certificate.checks_detail["mode_stability_assessed"] is False


def test_no_noise_gain_is_ever_reported():
    """The estimate stays None: a number would imply a measurement was made."""
    certificate = ProjectionValidator(domain=_AlwaysValidDomain()).validate({"x": 0.1})

    assert certificate.noise_gain_estimate is None


def test_a_measured_projection_still_certifies_local():
    """The exclusion does not weaken certification on the measured axes."""
    certificate = ProjectionValidator(domain=_AlwaysValidDomain()).validate({"x": 0.1})

    assert certificate.certification_level is ProjectionCertificationLevel.LOCAL


def test_an_invalid_domain_certifies_nothing():
    validator = ProjectionValidator(domain=_AlwaysInvalidDomain())
    certificate = validator.validate({"x": 0.1})

    assert certificate.certification_level is ProjectionCertificationLevel.NONE
