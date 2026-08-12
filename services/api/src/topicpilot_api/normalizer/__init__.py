"""Pure, provider-neutral observation normalization."""

from .contracts import (
    InputEnvelope,
    MappingPolicy,
    NormalizationCandidate,
    NormalizationFailure,
    NormalizationResult,
    ReferenceContext,
    ReferenceContextLoader,
    ReferenceContextRequest,
)
from .historical import HISTORICAL_MAPPING_POLICY_VERSION, HistoricalDailyBarNormalizer
from .registry import NormalizerKey, NormalizerRegistry
from .results import PersistedCanonicalReference, RuntimeResult
from .runtime import (
    DatabaseReferenceContextLoader,
    NormalizationRuntime,
    TimelineInputLoader,
)
from .synthetic import SyntheticReferenceNormalizer

__all__ = [
    "HISTORICAL_MAPPING_POLICY_VERSION",
    "DatabaseReferenceContextLoader",
    "HistoricalDailyBarNormalizer",
    "InputEnvelope",
    "MappingPolicy",
    "NormalizationCandidate",
    "NormalizationFailure",
    "NormalizationResult",
    "NormalizationRuntime",
    "NormalizerKey",
    "NormalizerRegistry",
    "PersistedCanonicalReference",
    "ReferenceContext",
    "ReferenceContextLoader",
    "ReferenceContextRequest",
    "RuntimeResult",
    "SyntheticReferenceNormalizer",
    "TimelineInputLoader",
]
