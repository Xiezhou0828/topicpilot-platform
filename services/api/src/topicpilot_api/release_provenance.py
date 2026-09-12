"""Secret-free runtime provenance helpers for release verification."""

from __future__ import annotations

import os
import re

_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
_UNKNOWN_SHA = "UNKNOWN"


def runtime_git_sha() -> str:
    """Return the deployed source SHA, or ``UNKNOWN`` when it is not provable."""

    for variable_name in ("RENDER_GIT_COMMIT", "GIT_SHA"):
        value = os.getenv(variable_name, "").strip()
        if not value:
            continue
        return value.lower() if _SHA_PATTERN.fullmatch(value) else _UNKNOWN_SHA
    return _UNKNOWN_SHA


__all__ = ["runtime_git_sha"]
