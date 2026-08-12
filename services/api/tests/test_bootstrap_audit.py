from __future__ import annotations

import json

from topicpilot_api.live.bootstrap import audit_v1_stock_master


def test_stock_master_audit_reports_invalid_duplicate_and_limit_rows(tmp_path) -> None:
    path = tmp_path / "stock-master.json"
    path.write_text(
        json.dumps(
            [
                {"code": "2330", "name": "TSMC", "market": "TPE"},
                {"code": "2330", "name": "TSMC duplicate", "market": "TPE"},
                {"code": "6488", "name": "test", "market": "TWO"},
                {"code": "bad code", "name": "invalid", "market": "TPE"},
                {"code": "9999", "name": "unsupported", "market": "TEST"},
            ]
        ),
        encoding="utf-8",
    )

    audit = audit_v1_stock_master(path, limit=1, offset=1)

    assert audit.input_count == 5
    assert audit.accepted_count == 1
    assert audit.tpe_count == 0
    assert audit.two_count == 1
    assert audit.invalid_count == 2
    assert audit.duplicate_count == 1
    assert audit.skipped_count == 2
    assert [item.code for item in audit.records] == ["6488"]
