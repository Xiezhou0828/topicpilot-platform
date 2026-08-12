import pytest

from topicpilot_api.normalizer import (
    NormalizerKey,
    NormalizerRegistry,
    SyntheticReferenceNormalizer,
)


def key():
    return NormalizerKey("synthetic", "v1", "normalization-contract-v1", "synthetic-mapping-v1")


def test_registry_resolves_and_rejects_duplicates_and_missing():
    registry = NormalizerRegistry()
    mapper = SyntheticReferenceNormalizer()
    registry.register(key(), mapper)
    assert registry.resolve(key()) is mapper
    with pytest.raises(ValueError):
        registry.register(key(), mapper)
    with pytest.raises(LookupError):
        registry.resolve(
            NormalizerKey("other", "v1", "normalization-contract-v1", "synthetic-mapping-v1")
        )
