from __future__ import annotations


class DetectorFrameworkError(Exception):
    code = "DETECTOR_FRAMEWORK_ERROR"
    retryable = False

    def __init__(
        self, message: str = "detector framework error", *, details: tuple[str, ...] = ()
    ) -> None:
        super().__init__(message)
        self.details = tuple(details)[:10]


class MalformedInvocationError(DetectorFrameworkError):
    code = "MALFORMED_INVOCATION"


class InvalidConfigurationError(DetectorFrameworkError):
    code = "INVALID_CONFIGURATION"


class UnsupportedCapabilityError(DetectorFrameworkError):
    code = "UNSUPPORTED_CAPABILITY"


class RegistryNotFoundError(DetectorFrameworkError):
    code = "REGISTRY_NOT_FOUND"


class RegistryAmbiguousError(DetectorFrameworkError):
    code = "REGISTRY_AMBIGUOUS"


class UnavailableInputError(DetectorFrameworkError):
    code = "UNAVAILABLE_INPUT"


class InvalidDetectorOutputError(DetectorFrameworkError):
    code = "INVALID_DETECTOR_OUTPUT"


class UnexpectedDetectorFailure(DetectorFrameworkError):
    code = "UNEXPECTED_DETECTOR_FAILURE"


class DetectorCancelledError(DetectorFrameworkError):
    code = "DETECTOR_CANCELLED"


class DetectorTimeoutError(DetectorFrameworkError):
    code = "DETECTOR_TIMED_OUT"
