# tests/kernel/projection/test_certificate_snapshot.py

"""ProjectionCertificate snapshots its detail map (audit a13, P1-04).

The certificate is an attestation: what it reports must be fixed at
emission. The producing validator builds ``checks_detail`` in a working
dict; the certificate snapshots that map at construction, so later
mutation of the validator's working dict can no longer rewrite an
already emitted attestation.
"""

from arvis.kernel.projection.certificate import (
    ProjectionCertificate,
    ProjectionCertificationLevel,
)


def _certificate(detail: dict[str, bool]) -> ProjectionCertificate:
    return ProjectionCertificate(
        domain_valid=True,
        boundedness_ok=True,
        lipschitz_ok=True,
        noise_robustness_ok=True,
        mode_stability_ok=True,
        lyapunov_compatibility_ok=True,
        margin_to_boundary=0.5,
        local_lipschitz_estimate=None,
        noise_gain_estimate=None,
        certification_level=ProjectionCertificationLevel.LOCAL,
        checks_detail=detail,
    )


def test_certificate_snapshots_its_detail_map_at_construction():
    working = {"boundedness_checked": True}
    certificate = _certificate(working)

    working["boundedness_checked"] = False
    working["injected_after_emission"] = True

    assert certificate.checks_detail == {"boundedness_checked": True}


def test_certificates_built_from_the_same_working_dict_are_independent():
    working = {"axis_assessed": True}
    first = _certificate(working)
    working["axis_assessed"] = False
    second = _certificate(working)

    assert first.checks_detail == {"axis_assessed": True}
    assert second.checks_detail == {"axis_assessed": False}
