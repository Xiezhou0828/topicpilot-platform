from .config import DetectorConfig
from .context import DetectorContext
from .contracts import BaseDetector, Generation, Lineage, Result, Status
from .exceptions import (
    DetectorCancelledError,
    DetectorFrameworkError,
    DetectorTimeoutError,
    InvalidConfigurationError,
    InvalidDetectorOutputError,
    MalformedInvocationError,
    RegistryAmbiguousError,
    RegistryNotFoundError,
    UnavailableInputError,
    UnexpectedDetectorFailure,
    UnsupportedCapabilityError,
)
from .range_detector import (
    CONTRACT_VERSION as RANGE_CONTRACT_VERSION,
)
from .range_detector import (
    DETECTOR_ID as RANGE_DETECTOR_ID,
)
from .range_detector import (
    DETECTOR_VERSION as RANGE_DETECTOR_VERSION,
)
from .range_detector import (
    RangeDetector,
    register_range_detector,
)
from .registry import DetectorEntry, DetectorRegistry
from .result import DetectorResult, Diagnostics, Evidence
from .runner import DetectorRunner

__all__ = [
    "RANGE_CONTRACT_VERSION",
    "RANGE_DETECTOR_ID",
    "RANGE_DETECTOR_VERSION",
    "BaseDetector",
    "DetectorCancelledError",
    "DetectorConfig",
    "DetectorContext",
    "DetectorEntry",
    "DetectorFrameworkError",
    "DetectorRegistry",
    "DetectorResult",
    "DetectorRunner",
    "DetectorTimeoutError",
    "Diagnostics",
    "Evidence",
    "Generation",
    "InvalidConfigurationError",
    "InvalidDetectorOutputError",
    "Lineage",
    "MalformedInvocationError",
    "RangeDetector",
    "RegistryAmbiguousError",
    "RegistryNotFoundError",
    "Result",
    "Status",
    "UnavailableInputError",
    "UnexpectedDetectorFailure",
    "UnsupportedCapabilityError",
    "register_range_detector",
]
