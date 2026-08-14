from __future__ import annotations

from pathlib import Path

from topicpilot_api.market_identity_remediation import (
    CANONICAL_MARKET_METADATA,
    EXPECTED_MARKET_CODES,
    LEGACY_MARKET_METADATA,
    MARKET_IDENTITY_REMEDIATION_WRITE_SET,
    NON_MARKET_IDENTITY_WRITE_SET,
)


def test_market_identity_semantics_and_write_boundary_are_explicit():
    assert {"TPE", "TWO"} == EXPECTED_MARKET_CODES
    assert LEGACY_MARKET_METADATA == {
        "TPE": {"name": "Taiwan Stock Exchange", "exchange_code": "TPE"},
        "TWO": {"name": "Taipei Exchange", "exchange_code": "TWO"},
    }
    assert CANONICAL_MARKET_METADATA == {
        "TPE": {"name": "TWSE Listed", "exchange_code": "TWSE"},
        "TWO": {"name": "TPEx OTC", "exchange_code": "TPEx"},
    }
    assert {
        "markets.name",
        "markets.exchange_code",
    } == MARKET_IDENTITY_REMEDIATION_WRITE_SET
    assert frozenset() == NON_MARKET_IDENTITY_WRITE_SET


def test_remediation_does_not_expose_generic_or_non_market_mutation_paths():
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "topicpilot_api"
        / "market_identity_remediation.py"
    ).read_text(encoding="utf-8")
    assert "delete(" not in source
    assert "insert(" not in source
    assert "topicpilot_api.topic" not in source
    assert "canonical_observations" not in source
    assert "raw_market_observations" not in source
    assert "ReferenceRegistrySet" in source
