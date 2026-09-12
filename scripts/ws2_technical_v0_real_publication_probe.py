"""Read-only deterministic WS2 Technical V0 real-publication probe.

This probe intentionally uses the canonical historical reader and a bounded,
fixed control set.  It never writes PostgreSQL, calls a provider, or changes
the canonical OHLCV dataset.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from topicpilot_api.config import Settings
from topicpilot_api.historical_read_model import read_historical_bars
from topicpilot_api.known_event_aware_publication import evaluate_known_event_lookup
from topicpilot_api.technical_publication import build_technical_publication

FROM = date(2026, 2, 2)
TO = date(2026, 8, 13)
TWT49U_SHA256 = "f610035f370ae2a9e9559625580daebb7d43a6198d1752a66387ee1869d6fd7b"


def _json_default(value: object) -> str:
    if isinstance(value, (date, Decimal)):
        return value.isoformat() if isinstance(value, date) else str(value)
    raise TypeError(type(value).__name__)


def _lookup(events: list[dict]) -> dict:
    return {
        "lookup_state": "SUCCESS",
        "query_completed": True,
        "response_parsed": True,
        "identity_binding_valid": True,
        "normalization_valid": True,
        "known_events": events,
        "source_lineage": {
            "lineage_state": "VERSIONED",
            "source": "TWSE_TWT49U_OFFICIAL",
            "query_window": [FROM.isoformat(), TO.isoformat()],
            "evidence_hash": TWT49U_SHA256,
        },
    }


def _compact(case_name: str, history: dict, publication: dict) -> dict:
    ma60 = [
        item
        for item in publication["technical_evidence"]
        if item["indicator_id"] == "MA60"
    ][-1]
    return {
        "case": case_name,
        "identity": f"{history['market']}:{history['code']}",
        "instrument_id": str(history["instrument_id"]),
        "rows": len(history["items"]),
        "date_range": [history["returned_from"], history["returned_to"]],
        "source_codes": sorted({item["source_code"] for item in history["items"]}),
        "status": publication["status"],
        "published_indicators": publication["published_indicators"],
        "ma60": {
            "session_date": ma60["session_date"],
            "value": ma60["value"],
            "publication_state": ma60["publication_state"],
            "availability_reason": ma60["availability_reason"],
            "continuity_state": ma60["continuity_state"],
            "event_lookup_state": ma60["event_lookup_state"],
            "required_observation_window": ma60["required_observation_window"],
            "actual_observation_window": ma60["actual_observation_window"],
            "algorithm_id": ma60["algorithm_id"],
            "algorithm_version": ma60["algorithm_version"],
            "source_lineage": ma60["source_lineage"],
            "as_of": ma60["as_of"],
        },
    }


def run() -> dict:
    engine = create_engine(Settings().database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        total_rows = connection.execute(text("""
            SELECT COUNT(*) FROM topicpilot.canonical_observations
            WHERE family_code='PRICE' AND quality_state='ACCEPTED'
        """)).scalar_one()
        distinct_instruments = connection.execute(text("""
            SELECT COUNT(DISTINCT instrument_id) FROM topicpilot.canonical_observations
            WHERE family_code='PRICE' AND quality_state='ACCEPTED'
        """)).scalar_one()
        min_date, max_date = connection.execute(text("""
            SELECT MIN((co.observed_at AT TIME ZONE m.timezone)::date),
                   MAX((co.observed_at AT TIME ZONE m.timezone)::date)
            FROM topicpilot.canonical_observations co
            JOIN topicpilot.instruments i ON i.id=co.instrument_id
            JOIN topicpilot.markets m ON m.id=i.market_id
            WHERE co.family_code='PRICE' AND co.quality_state='ACCEPTED'
        """)).one()
        lifecycle_rows = connection.execute(text(
            "SELECT COUNT(*) FROM topicpilot.reference_instrument_lifecycles"
        )).scalar_one()
        corporate_action_tables = connection.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema='topicpilot'
              AND (table_name ILIKE '%corporate%' OR table_name ILIKE '%action%')
        """)).scalar_one()

    with Session(engine) as session:
        def probe(case_name: str, code: str, limit: int, lookup: dict) -> dict:
            history = read_historical_bars(session, code, FROM, TO, "TPE", limit)
            history["known_event_lookup"] = lookup
            publication = build_technical_publication(history)
            return _compact(case_name, history, publication)

        probes = [
            probe("ordinary_no_match", "1314", 200, _lookup([])),
            probe(
                "known_event",
                "2330",
                200,
                _lookup([
                    {
                        "canonical_identity": "TPE:2330",
                        "effective_date": "2026-03-17",
                        "event_type": "CASH_DIVIDEND_EX_DIVIDEND",
                        "verified": True,
                        "handling": "EXCLUDE",
                    },
                    {
                        "canonical_identity": "TPE:2330",
                        "effective_date": "2026-06-11",
                        "event_type": "CASH_DIVIDEND_EX_DIVIDEND",
                        "verified": True,
                        "handling": "EXCLUDE",
                    },
                ]),
            ),
            probe("lookup_failure", "1314", 200, {"lookup_state": "TIMEOUT"}),
            probe("insufficient_history", "1314", 20, _lookup([])),
        ]

    external_controls = []
    for identity, effective_date, event_type in (
        ("TPE:2380", "2026-06-29", "CAPITAL_REDUCTION"),
        ("TWO:5904", "2026-08-10", "SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE"),
    ):
        market, code = identity.split(":")
        result = evaluate_known_event_lookup(
            {
                "market": market,
                "code": code,
                "known_event_lookup": _lookup([
                    {
                        "canonical_identity": identity,
                        "effective_date": effective_date,
                        "event_type": event_type,
                        "verified": True,
                        "handling": "EXCLUDE",
                    }
                ]),
            },
            required_window={"start_session": FROM, "end_session": TO},
        )
        external_controls.append(
            {
                "identity": identity,
                "state": result["state"],
                "publication_allowed": result["publication_allowed"],
            }
        )

    return {
        "dataset": {
            "total_instrument_count": int(distinct_instruments),
            "total_instrument_date_count": int(total_rows),
            "date_range": [min_date, max_date],
            "source_authority": ["TWSE_OFFICIAL_DAILY", "TPEX_OFFICIAL_DAILY"],
            "lifecycle_rows": int(lifecycle_rows),
            "corporate_action_table_count": int(corporate_action_tables),
        },
        "probe_mode": "DETERMINISTIC_FOUR_CASE_REAL_READER_BOUND",
        "probes": probes,
        "external_positive_controls": external_controls,
    }


if __name__ == "__main__":
    summary = run()
    canonical_json = json.dumps(summary, default=_json_default, sort_keys=True, separators=(",", ":"))
    print(json.dumps(summary, default=_json_default, indent=2, sort_keys=True))
    print(f"SUMMARY_SHA256={hashlib.sha256(canonical_json.encode()).hexdigest()}")
