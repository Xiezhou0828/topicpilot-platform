"""Offline, price-free audit of the unchanged canonical daily ingestion path.

No HTTP client, database session, runner, or persistence entrypoint is invoked.
Inputs are retained official payloads and a canonical SELECT-only identity
projection. Normalization candidates are NOT persisted observations. Prior-close
presence is NOT a fabricated previousClose or proof of adjacent-session history.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Collection, Mapping
from datetime import date, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from topicpilot_api.corporate_action_authority import corporate_action_authorities_for
from topicpilot_api.daily_market import (
    assess_daily_coverage,
    build_unavailable_instruments,
)
from topicpilot_api.market_data.exchange import (
    TpexOfficialDailyProvider,
    TwseOfficialDailyProvider,
)
from topicpilot_api.market_data.history import HistoricalProviderError
from topicpilot_api.market_data.ingestion import (
    _bar_payload,
    _observed_at,
    _status_payload,
    classify_authoritative_no_trade_result,
)
from topicpilot_api.normalizer.contracts import (
    InputEnvelope,
    MappingPolicy,
    ReferenceContext,
)
from topicpilot_api.normalizer.historical import HistoricalDailyBarNormalizer
from topicpilot_api.previous_close_authority import (
    G2PriceEvidence,
    PreviousCloseEvidence,
    previous_session_date,
)
from topicpilot_api.provider_preflight import (
    G2MarketContext,
    G2MarketFetch,
    G2PreflightContext,
    evaluate_provider_preflight,
)
from topicpilot_api.trading_status_authority import (
    authority_from_official_daily_result,
    resolve_effective_trading_status,
)

ADAPTERS = {"TPE": TwseOfficialDailyProvider, "TWO": TpexOfficialDailyProvider}
STAGES = (
    "HTTP_REQUEST_SENT",
    "HTTP_RESPONSE_RECEIVED",
    "HTTP_STATUS_ACCEPTED",
    "PAYLOAD_NON_EMPTY",
    "JSON_DECODE",
    "PROVIDER_DATE_PARSED",
    "TARGET_DATE_MATCHED",
    "RAW_MARKET_ROWS_EXTRACTED",
    "INSTRUMENT_CODE_NORMALIZED",
    "TARGET_UNIVERSE_MATCHED",
    "CLOSE_EXTRACTED",
    "PREVIOUS_CLOSE_EXTRACTED",
    "PRICE_VALIDATION_PASSED",
    "TRADING_STATUS_LIFECYCLE_ACCEPTED",
    "CANONICAL_OBSERVATION_CREATED",
    "FORMAL_MARKET_READINESS_PASSED",
)


def replay_market(
    raw: bytes, targets: list[list], market: str, day: date, probe: dict | None = None,
    *, previous_closes: Mapping[str, PreviousCloseEvidence] | None = None,
    closed_dates: Collection[date] = (),
) -> dict:
    """Replay existing adapter -> ingestion classifier -> mapper -> status resolver.

    Target column order matches the documented protected readback projection:
    market, code, persisted id, effective lifecycle, eligibility reason,
    official provider, adapter, prior-close-present, prior date, current previousClose present.
    No stock list, missing-price exemption, or corporate-action policy is added here.
    """
    cls = ADAPTERS[market]
    codes = [r[1] for r in targets]
    ids = [UUID(r[2]) for r in targets]
    if not targets or len(codes) != len(set(codes)) or len(ids) != len(set(ids)):
        raise ValueError("INVALID_TARGET_IDENTITIES")
    if any(r[0] != market or r[4] != "ELIGIBLE" for r in targets):
        raise ValueError("INVALID_TARGET_ELIGIBILITY")
    if any(r[5:7] != [cls.source_code, cls.adapter_version] for r in targets):
        raise ValueError("TARGET_PROVIDER_IDENTITY_MISMATCH")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, ValueError):
        return {
            "market": market,
            "error": "JSON_DECODE_FAILED",
            "targets": len(targets),
        }
    if not isinstance(payload, dict):
        return {"market": market, "error": "INVALID_PAYLOAD", "targets": len(targets)}
    provider = cls(
        start_date=day,
        end_date=day,
        market_batch=True,
        transport=lambda _url, _timeout: raw,
        readiness_max_attempts=1,
        clock=lambda: datetime.fromisoformat(f"{day}T23:59:00+08:00"),
    )
    provenance = {
        "market": market,
        "targetDate": str(day),
        "responseDate": payload.get("date"),
        "payloadSha256": hashlib.sha256(raw).hexdigest(),
        "payloadBytes": len(raw),
        "adapterVersion": cls.adapter_version,
        "providerAuthority": cls.source_code,
        "providerRawStat": payload.get("stat"),
        "sourceEndpoint": provider.market_base_url,
    }
    try:
        _, bars = provider.fetch_market_day()
    except HistoricalProviderError as exc:
        # Preserve canonical failure ordering; never bypass non-OK stat or empty/date failures.
        return {
            **provenance,
            "error": exc.code,
            "targets": len(targets),
            "normalizationExecuted": False,
            "retryCount": provider.readiness_retry_count,
        }

    table = next(
        t
        for t in payload["tables"]
        if t.get("fields", [None])[0] == ("證券代號" if market == "TPE" else "代號")
    )
    matched = set(codes) & set(bars)
    missing = set(codes) - set(bars)
    close_codes = {c for c in matched if bars[c].close is not None}
    null_codes = matched - close_codes
    prior_codes = {
        r[1]
        for r in targets
        if r[7] is True and r[8] is not None and date.fromisoformat(r[8]) < day
    }
    mapper = HistoricalDailyBarNormalizer()
    reference = ReferenceContext(
        "audit-readback", "Asia/Taipei", "REGULAR", "TW_MARKET", "TWD", 2
    )
    decisions, rows, resolutions = [], [], {}
    qualities: Counter = Counter()
    accepted_price_codes = set()
    for target in targets:
        code, instrument_id = target[1], UUID(target[2])
        result = classify_authoritative_no_trade_result(
            provider.fetch_daily(code, market),
            lifecycle_status=target[3],
            trading_date=day,
        )
        bar = result.bars[0] if result.bars else None
        point = _bar_payload(result, bar) if bar else _status_payload(result, day)
        # Audit-only envelope identities are never source/canonical database records.
        audit_id = uuid5(NAMESPACE_URL, f"offline-not-persisted:{market}:{code}:{day}")
        observed = _observed_at(day, "Asia/Taipei")
        envelope = InputEnvelope(
            point,
            instrument_id,
            audit_id,
            audit_id,
            audit_id,
            observed,
            observed,
            observed,
            "offline-not-persisted",
        )
        normalized = mapper(envelope, reference, MappingPolicy())
        price = next(
            (c for c in normalized.candidates if c.family_code == "PRICE"), None
        )
        quality = price.quality_state if price else "REJECTED"
        qualities[quality] += 1
        if quality == "ACCEPTED" and bar is not None and bar.close is not None:
            accepted_price_codes.add(code)
        daily_authority = authority_from_official_daily_result(result, trading_date=day)
        authority = tuple(
            a.to_trading_status_record()
            for a in corporate_action_authorities_for(
                symbol=code,
                market=market,
                trading_date=day,
            )
        )
        if daily_authority is not None:
            authority += (daily_authority,)
        resolution = resolve_effective_trading_status(
            instrument_id,
            day,
            same_session_close=bar.close if bar else None,
            official_authority=authority,
            price_source=cls.source_code,
        )
        resolutions[instrument_id] = resolution
        rows.append(
            {
                "instrument_id": instrument_id,
                "symbol": code,
                "market": market,
                "close": bar.close if bar else None,
            }
        )
        decisions.append(
            {
                "market": market,
                "symbol": code,
                "instrumentId": str(instrument_id),
                "lifecycle": target[3],
                "eligibility": target[4],
                "providerAuthority": target[5],
                "adapterVersion": target[6],
                "providerRowMatched": code in matched,
                "closePresent": code in close_codes,
                "priorCanonicalClosePresent": code in prior_codes,
                "priorCanonicalCloseDate": target[8],
                "currentPreviousClosePresent": target[9],
                "normalizationPriceQuality": quality,
                "statusAuthorityOrigin": getattr(result, "status_authority_origin", None),
                "status": resolution.status,
                "reasonCode": resolution.reason_code,
                "authoritySource": resolution.authority_source,
                "legitimateUnavailable": resolution.is_legitimate_unavailable,
                "blocksPublication": resolution.blocks_publication,
                "normalizationFailureCodes": [f.code for f in normalized.failures],
            }
        )
    legitimate = [d for d in decisions if d["legitimateUnavailable"]]
    blocking = [d for d in decisions if d["blocksPublication"]]
    covered = len(accepted_price_codes) + len(legitimate)
    unavailable = build_unavailable_instruments(
        rows, trade_date=day, status_resolutions=resolutions
    )
    coverage = assess_daily_coverage(
        trade_date=day,
        expected_by_market={market: len(targets)},
        observed_by_market={market: len(targets)},
        priced_by_market={market: len(accepted_price_codes)},
        covered_by_market={market: covered},
        unavailable_instruments=unavailable,
    )
    context = G2MarketContext(
        market,
        cls.source_code,
        cls.adapter_version,
        "TWSE" if market == "TPE" else "TPEx",
        "Asia/Taipei",
        "TW_MARKET",
        tuple(codes),
        {r[1]: r[2] for r in targets},
    )
    g2 = evaluate_provider_preflight(
        G2PreflightContext(
            {"referenceLoadStatus": "READY"}, day, True, None, (context,),
            previous_session=previous_session_date(day, closed_dates),
        ),
        {
            market: G2MarketFetch(
                market,
                cls.source_code,
                cls.adapter_version,
                day,
                frozenset(bars),
                len(bars),
                prices={r[1]: G2PriceEvidence(
                    r[2], market, r[1], bars[r[1]].trading_date,
                    bars[r[1]].close, provenance["payloadSha256"],
                    provider_previous=PreviousCloseEvidence(
                        r[2], market, r[1], previous_session_date(day, closed_dates),
                        bars[r[1]].previous_close, cls.source_code,
                        "PROVIDER_EXPLICIT_PREVIOUS_CLOSE", provenance["payloadSha256"], day,
                    ) if bars[r[1]].previous_close is not None else None,
                    formal_previous=(previous_closes or {}).get(r[1]),
                ) for r in targets if r[1] in bars},
                statuses={r[2]: resolutions[UUID(r[2])] for r in targets},
            )
        },
    )["markets"][0]
    stages = []

    def stage(
        n, incoming, outgoing, unit, reason=None, symbols=(), status="OFFLINE_REPLAY"
    ):
        stages.append(
            {
                **provenance,
                "stage": n,
                "name": STAGES[n - 1],
                "unit": unit,
                "inputCount": incoming,
                "outputCount": outgoing,
                "rejectedCount": None if outgoing is None else incoming - outgoing,
                "rejectionReason": reason,
                "representativeSymbols": list(symbols)[:5],
                "status": status,
            }
        )

    http_proven = (
        probe is not None
        and probe.get("httpStatus") == 200
        and probe.get("payloadSha256") == provenance["payloadSha256"]
    )
    for n in range(1, 4):
        stage(
            n,
            1,
            1 if http_proven else None,
            "HTTP exchange",
            None if http_proven else "HTTP_EVIDENCE_NOT_SUPPLIED",
            status="RECORDED_SINGLE_PROBE_NOT_REISSUED"
            if http_proven
            else "NOT_PROVEN",
        )
    for n in range(4, 8):
        stage(n, 1, 1, "payload")
    stage(8, len(table["data"]), len(table["data"]), "provider row")
    stage(
        9,
        len(table["data"]),
        len(bars),
        "provider row",
        "BLANK_CODE" if len(table["data"]) != len(bars) else None,
    )
    stage(
        10,
        len(bars),
        len(matched),
        "provider row",
        "OUT_OF_TARGET_UNIVERSE",
        sorted(set(bars) - matched),
    )
    stage(
        11,
        len(matched),
        len(close_codes),
        "matched target",
        "NULL_PROVIDER_CLOSE" if null_codes else None,
        sorted(null_codes),
    )
    stage(
        12,
        len(close_codes),
        g2["previousCloseCoveredCount"],
        "priced target",
        "PREVIOUS_CLOSE_AUTHORITY_NOT_READY" if g2["previousCloseCoveredCount"] != len(close_codes) else None,
        [d["instrumentCode"] for d in g2["instrumentDecisions"] if d["closeValid"] and not d["previousCloseValid"]],
        status="AUTHORITY_VALIDATED_COMPARATOR_ONLY_NOT_PERSISTED",
    )
    stage(
        13,
        len(close_codes),
        len(accepted_price_codes),
        "priced target",
        "NORMALIZER_PRICE_REJECTED_OR_INCOMPLETE"
        if close_codes - accepted_price_codes
        else None,
        sorted(close_codes - accepted_price_codes),
    )
    stage(
        14,
        len(targets),
        len(targets) - len(blocking),
        "target identity",
        "BLOCKING_STATUS" if blocking else None,
        [d["symbol"] for d in blocking],
    )
    stage(
        15,
        len(targets),
        None,
        "persisted canonical observation",
        "PERSISTENCE_NOT_AUTHORIZED",
        status="NOT_EXECUTED",
    )
    stage(
        16,
        len(targets),
        covered,
        "target identity",
        "FORMAL_COVERAGE_INCOMPLETE" if not coverage.downstream_ready else None,
        status="PURE_COVERAGE_MODEL_ONLY_NOT_PUBLICATION",
    )
    return {
        **provenance,
        "targets": len(targets),
        "rawRows": len(bars),
        "rawCloseRows": sum(b.close is not None for b in bars.values()),
        "rawNullCloseRows": sum(b.close is None for b in bars.values()),
        "rawNullCloseExamples": [c for c, b in bars.items() if b.close is None][:5],
        "matchedTargets": len(matched),
        "missingTargets": sorted(missing),
        "targetCloseCount": len(close_codes),
        "nullCloseTargets": sorted(null_codes),
        "priorCanonicalCloseCount": len(prior_codes),
        "priorCanonicalDates": dict(
            Counter(r[8] for r in targets if r[1] in prior_codes)
        ),
        "currentPreviousCloseCount": sum(r[9] is True for r in targets),
        "normalizationPriceQualities": dict(qualities),
        "acceptedPriceCandidates": covered - len(legitimate),
        "legitimateUnavailableCount": len(legitimate),
        "formalCoverageModelReady": coverage.downstream_ready,
        "formalCoveredCount": covered,
        "blockingSymbols": [d["symbol"] for d in blocking],
        "priorComparatorPresenceComplete": close_codes <= prior_codes,
        "productionReadinessProven": False,
        "canonicalObservationCreated": False,
        "g2ProviderRowGateStatus": g2["status"],
        "g2Error": g2["errorCode"],
        "g2MissingCodes": g2["missingIdentityCodes"],
        "g2AuthorityEvidence": g2,
        "stages": stages,
        "decisions": decisions,
        "productionWriteSet": [],
        "retryCount": provider.readiness_retry_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--tpe-payload", type=Path, required=True)
    parser.add_argument("--two-payload", type=Path, required=True)
    parser.add_argument("--probes", type=Path, required=True)
    parser.add_argument("--implementation-label", choices=("BASELINE", "CANDIDATE"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    targets, context = (
        json.loads(args.targets.read_text()),
        json.loads(args.context.read_text()),
    )
    probes = json.loads(args.probes.read_text())
    day = date.fromisoformat(targets["targetDate"])
    ids = sorted(tuple(r[:3]) for r in targets["rows"])
    digest = hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest()
    if (
        not targets["readOnly"]
        or targets["productionWriteSet"]
        or not context["contextReady"]
        or targets["referenceVersion"] != context["referenceVersion"]
        or targets["targetDate"] != context["targetDate"]
        or digest != context["targetIdentitySha256"]
        or len(ids) != context["targetCount"]
    ):
        raise ValueError("CANONICAL_READBACK_CONTINUITY_INVALID")
    report = {
        "targetDate": str(day),
        "targetIdentitySha256": digest,
        "referenceVersion": targets["referenceVersion"],
        "readbackAt": context["recordedAt"],
        "canonicalBaselineSha": "3f2d4761c665931708517f0501c57f2be257b641",
        "implementationLabel": args.implementation_label,
        "implementationSourceSha256": {
            name: hashlib.sha256(Path(sys.modules[name].__file__).read_bytes()).hexdigest()
            for name in (
                "topicpilot_api.market_data.history",
                "topicpilot_api.market_data.ingestion",
                "topicpilot_api.normalizer.historical",
                "topicpilot_api.trading_status_authority",
                "topicpilot_api.daily_market",
                "topicpilot_api.provider_preflight",
                "topicpilot_api.previous_close_authority",
                "topicpilot_api.market_data.exchange",
            )
        },
        "productionWriteSet": [],
        "formalPublicationExecuted": False,
        "markets": {},
    }
    for market, path in (("TPE", args.tpe_payload), ("TWO", args.two_payload)):
        report["markets"][market] = replay_market(
            path.read_bytes(),
            [r for r in targets["rows"] if r[0] == market],
            market,
            day,
            probes[market],
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for market, result in report["markets"].items():
        print(
            json.dumps(
                {
                    "market": market,
                    **{
                        k: v
                        for k, v in result.items()
                        if k not in {"decisions", "stages", "g2AuthorityEvidence"}
                    },
                },
                ensure_ascii=True,
            )
        )


if __name__ == "__main__":
    main()
