"""Canonical hashing rules for append-only POST_CLOSE checkpoints.

The general normalizer intentionally rejects floats.  Checkpoint metadata has
one narrower boundary contract because runtime configuration can materialize a
whole-number duration as ``30.0``.  This module normalizes only the payload
used for checkpoint hashing; it does not change the global normalizer policy.

Numbers are represented as a tagged canonical decimal so that ``30``,
``Decimal("30.0")`` and ``30.0`` have the same checkpoint meaning, while the
string ``"30"`` remains a different JSON value.  Non-finite and unsupported
numeric values fail closed.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from decimal import Decimal
from hashlib import sha256
from typing import Any

_NUMBER_TAG = "$checkpointNumber"


def _canonical_number(value: int | float | Decimal) -> dict[str, str]:
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("checkpoint canonicalization requires finite numeric values")
        decimal_value = Decimal(str(value))
    elif isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("checkpoint canonicalization requires finite numeric values")
        decimal_value = value
    else:
        decimal_value = Decimal(value)

    normalized = decimal_value.normalize()
    canonical = "0" if normalized == 0 else format(normalized, "f")
    return {_NUMBER_TAG: canonical}


def canonicalize_checkpoint_payload(value: Any) -> Any:
    """Return the deterministic JSON-compatible checkpoint representation."""

    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, (int, float, Decimal)):
        return _canonical_number(value)
    if isinstance(value, Mapping):
        canonical_mapping: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("checkpoint mapping keys must be strings")
            canonical_mapping[key] = canonicalize_checkpoint_payload(item)
        return {key: canonical_mapping[key] for key in sorted(canonical_mapping)}
    if isinstance(value, (list, tuple)):
        return [canonicalize_checkpoint_payload(item) for item in value]
    if isinstance(value, (set, frozenset)):
        canonical_items = [canonicalize_checkpoint_payload(item) for item in value]
        return sorted(
            canonical_items,
            key=lambda item: json.dumps(
                item,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
                allow_nan=False,
            ),
        )
    raise TypeError(f"unsupported checkpoint canonical value: {type(value).__name__}")


def canonical_checkpoint_json(value: Any) -> str:
    """Serialize a checkpoint payload with fixed ordering, types, and nulls."""

    return json.dumps(
        canonicalize_checkpoint_payload(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def checkpoint_stable_hash(value: Any) -> str:
    """Hash the canonical representation used by checkpoint events only."""

    return sha256(canonical_checkpoint_json(value).encode("utf-8")).hexdigest()


__all__ = [
    "canonical_checkpoint_json",
    "canonicalize_checkpoint_payload",
    "checkpoint_stable_hash",
]
