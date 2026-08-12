from __future__ import annotations

import pytest

from topicpilot_api.detectors import (
    BaseDetector,
    DetectorCancelledError,
    DetectorConfig,
    DetectorContext,
    DetectorEntry,
    DetectorRegistry,
    DetectorResult,
    DetectorRunner,
    DetectorTimeoutError,
    Generation,
    InvalidDetectorOutputError,
    Lineage,
    RegistryNotFoundError,
    Result,
    Status,
    UnsupportedCapabilityError,
)
from topicpilot_api.detectors.immutability import freeze


def context() -> DetectorContext:
    return DetectorContext(
        "inv-1", "run-1", "corr-1", Generation.NEXT_V2, "fixture", "1", "1",
        {"value": None}, "synthetic", "2026-01-01", Lineage("fixture"),
    )


class Double:
    detector_id = "fixture"
    detector_version = "1"

    def evaluate(self, context, config):
        return DetectorResult("fixture", "1", Result.UNKNOWN, Status.COMPLETED)


def registry() -> DetectorRegistry:
    value = DetectorRegistry()
    value.register(DetectorEntry("fixture", "1", Double(), input_profiles=frozenset({"synthetic"})))
    return value


def test_context_and_config_are_immutable_and_null_is_preserved():
    item = context()
    with pytest.raises((AttributeError, TypeError)):
        item.detector_id = "changed"
    config = DetectorConfig.resolve("fixture", "1", {"missing": None})
    assert config.values["missing"] is None
    with pytest.raises(TypeError):
        config.values["x"] = 1


def test_context_recursively_freezes_nested_containers():
    payload = {"nested": {"items": [{"value": 1}], "tags": {"a", "b"}}}
    item = DetectorContext(
        "inv-1", "run-1", "corr-1", Generation.NEXT_V2, "fixture", "1", "1",
        payload, "synthetic", "2026-01-01", Lineage("fixture"),
    )
    payload["nested"]["items"][0]["value"] = 99
    assert item.input_payload["nested"]["items"][0]["value"] == 1
    with pytest.raises(TypeError):
        item.input_payload["nested"]["items"][0]["value"] = 2
    with pytest.raises(AttributeError):
        item.input_payload["nested"]["tags"].add("c")


def test_shared_freeze_recursively_freezes_nested_containers():
    value = {"nested": [{"tags": {"a", "b"}}]}
    frozen = freeze(value)
    value["nested"][0]["tags"].add("c")
    assert frozen["nested"][0]["tags"] == frozenset({"a", "b"})
    with pytest.raises(TypeError):
        frozen["nested"][0]["tags"] = frozenset()


def test_result_metadata_recursively_freezes_nested_containers():
    metadata = {"nested": {"items": [{"value": 1}], "tags": {"a", "b"}}}
    result = DetectorResult("fixture", "1", Result.UNKNOWN, Status.COMPLETED, metadata=metadata)
    metadata["nested"]["items"][0]["value"] = 99
    assert result.metadata["nested"]["items"][0]["value"] == 1
    with pytest.raises(TypeError):
        result.metadata["nested"]["items"][0]["value"] = 2
    with pytest.raises(AttributeError):
        result.metadata["nested"]["tags"].add("c")


def test_unknown_is_distinct_from_failed_and_pass_fail_require_completed():
    unknown = DetectorResult("fixture", "1", Result.UNKNOWN, Status.COMPLETED)
    assert unknown.result is Result.UNKNOWN
    with pytest.raises(InvalidDetectorOutputError):
        DetectorResult("fixture", "1", Result.PASS, Status.FAILED)


def test_registry_fails_closed_and_runner_invokes_once():
    value = registry()
    with pytest.raises(RegistryNotFoundError):
        value.lookup("missing", "1")
    result = DetectorRunner(value).run(context(), DetectorConfig.resolve("fixture", "1"))
    assert result.result is Result.UNKNOWN


def test_registry_rejects_unsupported_and_missing_required_capabilities():
    value = DetectorRegistry()
    value.register(DetectorEntry("fixture", "1", Double(), timeframes=frozenset({"1d"})))
    with pytest.raises(UnsupportedCapabilityError):
        value.validate_capability(value.lookup("fixture", "1"), context())

    missing = context()
    missing = DetectorContext(
        missing.invocation_id, missing.run_id, missing.correlation_id, missing.generation,
        missing.detector_id, missing.detector_version, missing.contract_version,
        missing.input_payload, missing.input_profile, missing.as_of, missing.lineage,
        timeframe=None,
    )
    with pytest.raises(UnsupportedCapabilityError):
        value.validate_capability(value.lookup("fixture", "1"), missing)


def test_base_detector_protocol_accepts_typed_detector():
    detector: BaseDetector = Double()
    assert (
        detector.evaluate(context(), DetectorConfig.resolve("fixture", "1")).status
        is Status.COMPLETED
    )


def test_registry_entry_accepts_base_detector_compatible_instance():
    entry = DetectorEntry("fixture", "1", Double())
    assert entry.detector.detector_id == "fixture"
    assert entry.detector.detector_version == "1"


def test_runner_honors_cancellation_and_timeout():
    cancelled = DetectorContext(
        "inv-1", "run-1", "corr-1", Generation.NEXT_V2, "fixture", "1", "1",
        {"value": None}, "synthetic", "2026-01-01", Lineage("fixture"),
        cancellation_requested=True,
    )
    with pytest.raises(DetectorCancelledError):
        DetectorRunner(registry()).run(cancelled, DetectorConfig.resolve("fixture", "1"))

    class SlowDouble(Double):
        def evaluate(self, context, config):
            return super().evaluate(context, config)

    ticks = iter((10.0, 10.002))

    timed = DetectorRegistry()
    timed.register(
        DetectorEntry("fixture", "1", SlowDouble(), input_profiles=frozenset({"synthetic"}))
    )
    timed_context = DetectorContext(
        "inv-1", "run-1", "corr-1", Generation.NEXT_V2, "fixture", "1", "1",
        {"value": None}, "synthetic", "2026-01-01", Lineage("fixture"), timeout_seconds=0.001,
    )
    with pytest.raises(DetectorTimeoutError):
        DetectorRunner(timed, clock=lambda: next(ticks)).run(
            timed_context, DetectorConfig.resolve("fixture", "1")
        )
