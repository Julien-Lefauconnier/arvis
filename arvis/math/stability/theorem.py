# arvis/math/stability/theorem.py


from typing import Mapping


def is_globally_stable(cert: Mapping[str, bool]) -> bool:
    global_ok: bool = cert.get("global", False)
    switching_ok: bool = cert.get("switching", False)

    return global_ok and switching_ok
