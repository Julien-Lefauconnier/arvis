# arvis/adapters/__init__.py
"""ARVIS adapters package.

Campaign FINITION (audit #2 P2-4, 2026-09-02): the package used to
export ``get_llm_adapter``, a dead accessor reading adapters out of
``ctx.extra`` against the injection doctrine (F-001), called by
nothing. Deleted; the living adapter surfaces are the submodules
(``adapters.llm``, ``adapters.tools``, ``adapters.ir``).
"""
