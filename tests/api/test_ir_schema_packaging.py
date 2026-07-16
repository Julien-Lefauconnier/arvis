# tests/api/test_ir_schema_packaging.py

"""Packaging contract for the IR schema (F-010).

The IR JSON schema must ship with the distribution: loadable through
importlib.resources (the canonical, location-independent access path)
and declared in both the wheel package-data and the sdist manifest so
the guarantee cannot silently regress. The CI build job additionally
verifies the schema inside the built wheel and reads it back from an
installed wheel.
"""

import json
import tomllib
from importlib import resources
from pathlib import Path


def test_ir_schema_loadable_via_importlib_resources():
    resource = resources.files("arvis.api").joinpath("schema/ir_schema.json")
    schema = json.loads(resource.read_text(encoding="utf-8"))
    assert schema.get("type") == "object"
    assert "properties" in schema
    assert "required" in schema


def test_wheel_package_data_declares_ir_schema():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]
    assert "schema/*.json" in package_data.get("arvis.api", [])


def test_sdist_manifest_declares_ir_schema():
    manifest = Path("MANIFEST.in").read_text(encoding="utf-8")
    assert "recursive-include arvis/api/schema *.json" in manifest
