# tests/projection/test_domain.py

from arvis.kernel.projection.domain import NumericBounds, ProjectionDomain


def test_domain_valid():
    domain = ProjectionDomain(bounds={"x": NumericBounds(0, 10)})

    projected = {"x": 5}
    valid, checks = domain.validate(projected)

    assert valid is True
    assert checks["x_bounds"] is True


def test_domain_invalid():
    domain = ProjectionDomain(bounds={"x": NumericBounds(0, 10)})

    projected = {"x": 20}
    valid, checks = domain.validate(projected)

    assert valid is False
    assert checks["x_bounds"] is False
