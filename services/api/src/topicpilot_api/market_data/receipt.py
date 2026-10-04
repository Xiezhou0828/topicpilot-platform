"""Sanitized official HTTP receipt; no retry, fallback, or price policy."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from hashlib import sha256
from typing import Any
from urllib.error import HTTPError

from .history import HistoricalProviderError


def _read_json_receipt(
    transport: Callable[[str, float], bytes],
    url: str,
    timeout: float,
    evidence: dict[str, Any],
) -> Any:
    evidence.clear()
    evidence.update(
        endpoint=url,
        stage="TRANSPORT",
        httpStatus=None,
        payloadSize=None,
        payloadHash=None,
        responseDate=None,
        rawStatus=None,
    )
    try:
        raw = transport(url, timeout)
    except Exception as exc:
        evidence.update(
            classification="PROVIDER_TRANSPORT_FAILURE", exceptionClass=type(exc).__name__
        )
        if isinstance(exc, HTTPError):
            evidence["httpStatus"] = exc.code
            body = exc.read()
            evidence.update(payloadSize=len(body), payloadHash=sha256(body).hexdigest())
        failure = HistoricalProviderError("PROVIDER_REQUEST_FAILED", "exchange transport failed")
        failure.evidence = dict(evidence)
        raise failure from exc
    evidence.update(
        httpStatus=getattr(raw, "http_status", None),
        payloadSize=len(raw),
        payloadHash=sha256(raw).hexdigest(),
        stage="JSON_DECODE",
    )
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        evidence.update(
            classification="PROVIDER_PAYLOAD_SCHEMA_CHANGE", exceptionClass=type(exc).__name__
        )
        failure = HistoricalProviderError("INVALID_PAYLOAD", "exchange JSON decode failed")
        failure.evidence = dict(evidence)
        raise failure from exc
    return payload


def read_json_receipt(
    transport: Callable[[str, float], bytes],
    url: str,
    timeout: float,
    evidence: dict[str, Any],
) -> Mapping[str, Any]:
    payload = _read_json_receipt(transport, url, timeout, evidence)
    if not isinstance(payload, Mapping):
        evidence["classification"] = "PROVIDER_PAYLOAD_SCHEMA_CHANGE"
        failure = HistoricalProviderError("INVALID_PAYLOAD", "exchange response must be an object")
        failure.evidence = dict(evidence)
        raise failure
    evidence.update(
        stage="DATASET_PARSE",
        responseDate=str(payload.get("date", "")),
        rawStatus=str(payload.get("stat", "")),
        classification=None,
    )
    return payload


def read_json_array_receipt(
    transport: Callable[[str, float], bytes],
    url: str,
    timeout: float,
    evidence: dict[str, Any],
) -> list[Any]:
    """Opt-in array boundary; object-based providers keep their strict contract."""
    payload = _read_json_receipt(transport, url, timeout, evidence)
    if not isinstance(payload, list):
        evidence["classification"] = "PROVIDER_PAYLOAD_SCHEMA_CHANGE"
        failure = HistoricalProviderError("INVALID_PAYLOAD", "exchange response must be an array")
        failure.evidence = dict(evidence)
        raise failure
    evidence.update(stage="DATASET_PARSE", classification=None)
    return payload


class ResponseBytes(bytes):
    """Retain actual status without changing the transport's bytes contract."""

    http_status: int | None
