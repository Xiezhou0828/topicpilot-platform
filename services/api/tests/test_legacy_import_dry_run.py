from topicpilot_api.legacy_import import (
    DEFAULT_MAPPING_POLICY,
    ImportBatch,
    ImportEntity,
    ImportSource,
    canonical_record_hash,
    validate_batch,
    validate_dry_run,
)
from topicpilot_api.legacy_import.mapping import canonical_mapped_payload


def _batch(entity, *records):
    return ImportBatch(entity, tuple(records), (), ImportSource())


def test_warning_only_record_is_valid_and_counter_invariant():
    report = validate_dry_run(
        [_batch(ImportEntity.INSTRUMENT, {"market": "TPE", "code": "2330", "note": "x"})],
        DEFAULT_MAPPING_POLICY,
    )
    assert (report.records_read, report.valid, report.rejected, report.warnings) == (1, 1, 0, 1)
    assert report.valid + report.rejected == report.records_read


def test_instrument_stable_keys_include_market_and_full_code():
    report = validate_dry_run(
        [
            _batch(
                ImportEntity.INSTRUMENT,
                {"market": "TPE", "code": "2330"},
                {"market": "TPE", "code": "2454"},
                {"market": "TWO", "code": "6488"},
            )
        ],
        DEFAULT_MAPPING_POLICY,
    )
    assert report.conflicts == report.duplicate == 0
    assert report.valid == 3


def test_known_payload_lookup_uses_typed_composite_key_and_mapped_hash():
    record = {"market": "TPE", "code": "2330", "name": "TSMC"}
    rule = DEFAULT_MAPPING_POLICY.rule_for("instrument")
    key = ("instrument", ("TPE", "2330"))
    known = {key: canonical_record_hash(canonical_mapped_payload(record, rule))}
    assert (
        validate_dry_run(
            [_batch(ImportEntity.INSTRUMENT, {**record, "lineage_note": "one"})],
            DEFAULT_MAPPING_POLICY,
            known,
        ).conflicts
        == 0
    )
    assert (
        validate_dry_run(
            [_batch(ImportEntity.INSTRUMENT, {**record, "name": "changed"})],
            DEFAULT_MAPPING_POLICY,
            known,
        ).conflicts
        == 1
    )


def test_validate_batch_and_dry_run_agree_on_empty_required_values():
    record = {"market": "", "code": ""}
    batch_issues = validate_batch("instrument", [record], DEFAULT_MAPPING_POLICY)
    dry_run = validate_dry_run([_batch(ImportEntity.INSTRUMENT, record)], DEFAULT_MAPPING_POLICY)
    assert (
        sum(i.code == "REQUIRED_FIELD" for i in batch_issues)
        == sum(i.code == "REQUIRED_FIELD" for i in dry_run.issues)
        == 2
    )
    assert (
        sum(i.code == "STABLE_KEY" for i in batch_issues)
        == sum(i.code == "STABLE_KEY" for i in dry_run.issues)
        == 1
    )


def test_instrument_topic_composite_key_distinguishes_valid_from():
    records = [
        {
            "market": "TPE",
            "instrument": "2330",
            "topic": "ai",
            "relation_type": "PRIMARY",
            "valid_from": "2026-01-01",
        },
        {
            "market": "TPE",
            "instrument": "2330",
            "topic": "ai",
            "relation_type": "PRIMARY",
            "valid_from": "2026-02-01",
        },
    ]
    report = validate_dry_run(
        [_batch(ImportEntity.INSTRUMENT_TOPIC, *records)], DEFAULT_MAPPING_POLICY
    )
    assert report.valid == 2 and report.conflicts == 0 and report.duplicate == 0
