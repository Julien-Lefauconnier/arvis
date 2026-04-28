# tests/projection/test_certificate.py

from arvis.kernel.projection.domain import ProjectionDomain, NumericBounds
from arvis.kernel.projection.validator import ProjectionValidator


def test_certificate_basic_valid():
    domain = ProjectionDomain(bounds={"x": NumericBounds(0, 10)})

    validator = ProjectionValidator(domain)

    projected = {"x": 5}
    cert = validator.validate(projected)

    assert cert.domain_valid is True
    assert cert.is_projection_safe is True


def test_certificate_invalid_domain():
    domain = ProjectionDomain(bounds={"x": NumericBounds(0, 10)})

    validator = ProjectionValidator(domain)

    projected = {"x": 100}
    cert = validator.validate(projected)

    assert cert.domain_valid is False
    assert cert.is_projection_safe is False
