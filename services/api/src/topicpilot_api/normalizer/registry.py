from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .contracts import NormalizerMapper


@dataclass(frozen=True)
class NormalizerKey:
    source_code: str
    adapter_version: str
    normalization_contract_version: str
    mapping_policy_version: str


class NormalizerRegistry:
    """Explicit, immutable-after-resolution mapper registry.

    Registration is deterministic: duplicate keys and incomplete keys fail
    closed rather than silently replacing a mapper.
    """

    def __init__(self, registrations: Mapping[NormalizerKey, NormalizerMapper] | None = None):
        self._mappers: dict[NormalizerKey, NormalizerMapper] = dict(registrations or {})

    def register(self, key: NormalizerKey, mapper: NormalizerMapper) -> None:
        if not all(
            (
                key.source_code,
                key.adapter_version,
                key.normalization_contract_version,
                key.mapping_policy_version,
            )
        ):
            raise ValueError("normalizer registration key must be complete")
        if key in self._mappers:
            raise ValueError(f"normalizer already registered: {key}")
        self._mappers[key] = mapper

    def resolve(self, key: NormalizerKey) -> NormalizerMapper:
        try:
            return self._mappers[key]
        except KeyError as exc:
            raise LookupError(f"no normalizer registered for {key}") from exc

    def __len__(self) -> int:
        return len(self._mappers)
