# ruff: noqa: RUF001

from __future__ import annotations

import json
from datetime import date

from topicpilot_api.financial_research.source_adapter import TwseOpenApiSnapshotAdapter


def test_twse_snapshot_adapter_parses_latest_ytd_and_balance_snapshot() -> None:
    payloads = {
        TwseOpenApiSnapshotAdapter.income_url: json.dumps(
            [
                {
                    "年度": "115",
                    "季別": "2",
                    "公司代號": "1303",
                    "營業收入": "152243276.00",
                    "基本每股盈餘（元）": "5.17",
                }
            ]
        ).encode(),
        TwseOpenApiSnapshotAdapter.balance_url: json.dumps(
            [
                {
                    "年度": "115",
                    "季別": "2",
                    "公司代號": "1303",
                    "資產總計": "723033450.00",
                    "權益總計": "497654350.00",
                }
            ]
        ).encode(),
    }

    result = TwseOpenApiSnapshotAdapter(payloads.__getitem__).retrieve("1303")

    assert result.status == "RIGHTS_UNVERIFIED"
    assert result.filing is not None
    assert result.filing.reporting_period_end == date(2026, 6, 30)
    assert {record.line_item_standard for record in result.records} == {
        "revenue",
        "basic_eps",
        "assets",
        "equity",
    }
