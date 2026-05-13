# tests/errors/test_error_domains.py

from __future__ import annotations

from arvis.errors.base import ErrorDomain


def test_pipeline_domain_is_hierarchical():
    assert ErrorDomain.PIPELINE == "kernel.pipeline"


def test_syscall_domain_is_hierarchical():
    assert ErrorDomain.SYSCALL == "kernel.syscall"


def test_projection_domain_is_hierarchical():
    assert ErrorDomain.PROJECTION == "kernel.projection"
