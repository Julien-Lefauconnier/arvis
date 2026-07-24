# arvis/api/contracts/__init__.py

"""Serialized consumer contracts shipped with the package (beta, a16).

This package carries the versioned JSON Schema of the public result
serialization (CognitiveResultView.to_dict()). The schema file is the
contract an integrator can pin and validate against; its fingerprint is
frozen in the beta contract manifest, so any modification breaks the
golden and forces explicit versioning.
"""
