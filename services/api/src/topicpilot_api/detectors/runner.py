from __future__ import annotations

from collections.abc import Callable
from time import monotonic

from .config import DetectorConfig
from .exceptions import (
    DetectorCancelledError,
    DetectorTimeoutError,
    InvalidDetectorOutputError,
    UnexpectedDetectorFailure,
)
from .registry import DetectorRegistry
from .result import DetectorResult


class DetectorRunner:
    def __init__(
        self, registry: DetectorRegistry, *, clock: Callable[[], float] = monotonic
    ) -> None:
        self.registry = registry
        self.clock = clock

    def run(self, context, config: DetectorConfig) -> DetectorResult:
        entry = self.registry.lookup(context.detector_id, context.detector_version)
        self.registry.validate_capability(entry, context)
        if config.detector_id != context.detector_id:
            raise ValueError("configuration detector does not match context")
        if context.cancellation_requested:
            raise DetectorCancelledError("detector invocation was cancelled")
        started = self.clock()
        try:
            result = entry.detector.evaluate(context, config)
        except Exception as exc:
            raise UnexpectedDetectorFailure("detector invocation failed") from exc
        if not isinstance(result, DetectorResult):
            raise InvalidDetectorOutputError("detector must return DetectorResult")
        if context.timeout_seconds is not None and self.clock() - started > context.timeout_seconds:
            raise DetectorTimeoutError("detector invocation timed out")
        return result
