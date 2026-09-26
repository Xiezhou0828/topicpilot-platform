#!/usr/bin/env python3
"""Build the Owner-facing TopicPilot database-maintenance workbook.

The preferred engine is the bundled artifact-tool runtime.  A deliberately
compatible openpyxl fallback is retained for operators running the repository
outside the Codex artifact runtime; it produces the same contract and never
connects to a database.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from topicpilot_api.database_maintenance import (
    MAINTENANCE_ACTIONS,
    MARKET_CODES,
    TOPIC_ACTIVE_STATUSES,
)

SHEET_NAMES = (
    "README",
    "Instruments_Current",
    "Topics_Current",
    "Relations_Current",
    "Maintenance_Input",
    "Import_Preview",
    "Validation_Errors",
    "Lookups",
)
INPUT_HEADERS = [
    "ACTION",
    "STOCK_CODE",
    "NAME",
    "MARKET",
    "INSTRUMENT_TYPE",
    "CURRENCY",
    "ACTIVE/ENABLED",
    "PRIMARY_TOPICS",
    "PRIMARY_WEIGHTS",
    "SECONDARY_TOPICS",
    "SECONDARY_WEIGHTS",
    "AS_OF_DATE",
    "REPRESENTATIVE_TOPIC",
    "NOTES",
    "VALIDATION_STATUS",
    "VALIDATION_ERRORS",
]
PREVIEW_HEADERS = [
    "ROW_NUMBER",
    "RECORD_TYPE",
    "OPERATION",
    "ACTION",
    "MARKET",
    "STOCK_CODE",
    "INSTRUMENT_ID",
    "NAME",
    "INSTRUMENT_TYPE",
    "ACTIVE",
    "TOPIC_ID",
    "TOPIC_IDENTIFIER",
    "TOPIC_NAME",
    "RELATION_TYPE",
    "RELATION_WEIGHT",
    "EFFECTIVE_FROM",
    "EFFECTIVE_TO",
    "STATUS",
    "MESSAGE",
]
ERROR_HEADERS = [
    "ROW_NUMBER",
    "STOCK_CODE",
    "FIELD",
    "VALUE",
    "ERROR_CODE",
    "MESSAGE",
    "SEVERITY",
]

COLORS = {
    "navy": "#1F4E78",
    "blue": "#D9EAF7",
    "input": "#FFF2CC",
    "formula": "#E2F0D9",
    "error": "#FCE4D6",
    "muted": "#F2F2F2",
    "text": "#1F2937",
    "white": "#FFFFFF",
}


def _load_snapshot(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "source": "UNAVAILABLE",
            "environment": "UNAVAILABLE",
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "counts": {"instruments": 0, "topics": 0, "relations": 0},
            "markets": sorted(MARKET_CODES),
            "instruments": [],
            "topics": [],
            "relations": [],
            "snapshot_note": "No read-only database/API snapshot was available at build time.",
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _date_value(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (date, datetime)):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return str(value)


def _cell_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value
    if isinstance(value, bool | int | float):
        return value
    return str(value)


def _used_range_end(column_count: int, row_count: int) -> str:
    def col_name(number: int) -> str:
        result = ""
        while number:
            number, remainder = divmod(number - 1, 26)
            result = chr(65 + remainder) + result
        return result

    return f"{col_name(column_count)}{max(1, row_count)}"


def _table_name(sheet_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", sheet_name)[:20] + "Table"


def _current_sheet_rows(
    snapshot: dict[str, Any],
) -> dict[str, tuple[list[str], list[list[Any]]]]:
    instruments = [
        [
            item.get("id"),
            item.get("instrument_code"),
            item.get("name"),
            item.get("market"),
            item.get("instrument_type"),
            item.get("currency"),
            item.get("is_active"),
            _date_value(item.get("valid_from")),
            _date_value(item.get("valid_to")),
            item.get("created_at"),
            item.get("updated_at"),
            snapshot.get("source", "UNAVAILABLE"),
        ]
        for item in snapshot.get("instruments", [])
    ]
    topics = [
        [
            item.get("id"),
            item.get("slug"),
            item.get("name"),
            item.get("description"),
            item.get("status"),
            item.get("dictionary_version"),
            _date_value(item.get("valid_from")),
            _date_value(item.get("valid_to")),
            item.get("status") in TOPIC_ACTIVE_STATUSES,
            item.get("hierarchy"),
            snapshot.get("source", "UNAVAILABLE"),
        ]
        for item in snapshot.get("topics", [])
    ]
    relations = [
        [
            item.get("id"),
            item.get("instrument_code"),
            item.get("instrument_name"),
            item.get("market"),
            item.get("topic_id"),
            item.get("topic_slug"),
            item.get("topic_name"),
            item.get("relation_type"),
            item.get("relation_version"),
            item.get("relation_weight"),
            item.get("weight_approval_state"),
            _date_value(item.get("valid_from")),
            _date_value(item.get("valid_to")),
            item.get("structural_role"),
            item.get("approval_state"),
            item.get("source_artifact_id"),
            item.get("source_artifact_hash"),
            item.get("updated_at"),
            snapshot.get("source", "UNAVAILABLE"),
        ]
        for item in snapshot.get("relations", [])
    ]
    return {
        "Instruments_Current": (
            [
                "instrument_id",
                "instrument_code",
                "name",
                "market_code",
                "instrument_type",
                "currency",
                "is_active",
                "valid_from",
                "valid_to",
                "created_at",
                "updated_at",
                "snapshot_source",
            ],
            instruments,
        ),
        "Topics_Current": (
            [
                "topic_id",
                "slug",
                "name",
                "description",
                "status",
                "dictionary_version",
                "valid_from",
                "valid_to",
                "active_for_maintenance",
                "hierarchy",
                "snapshot_source",
            ],
            topics,
        ),
        "Relations_Current": (
            [
                "relation_id",
                "instrument_code",
                "instrument_name",
                "market_code",
                "topic_id",
                "topic_slug",
                "topic_name",
                "relation_type",
                "relation_version",
                "relation_weight",
                "weight_approval_state",
                "valid_from",
                "valid_to",
                "structural_role",
                "approval_state",
                "source_artifact_id",
                "source_artifact_hash",
                "updated_at",
                "snapshot_source",
            ],
            relations,
        ),
    }


def _readme_rows(snapshot: dict[str, Any]) -> list[list[Any]]:
    counts = snapshot.get("counts", {})
    source = snapshot.get("source", "UNAVAILABLE")
    note = snapshot.get("snapshot_note", "")
    rows = [
        ["TopicPilot Database Maintenance Workbook", None],
        [
            "Purpose",
            "Owner-facing maintenance interface for current instrument, topic, and relation data.",
        ],
        ["Snapshot source", source],
        ["Snapshot environment", snapshot.get("environment", "UNAVAILABLE")],
        ["Snapshot timestamp", f"ISO {snapshot.get('timestamp', '')}"],
        [
            "Snapshot counts",
            f"instruments={counts.get('instruments', 0)}; topics={counts.get('topics', 0)}; relations={counts.get('relations', 0)}",
        ],
        ["Snapshot note", note],
        ["Refresh", "python scripts/admin/export_database_maintenance_workbook.py"],
        [
            "Owner workflow",
            "Refresh → edit Maintenance_Input → run validate-only → review Import_Preview/Validation_Errors → run dry-run → apply only through controlled authority.",
        ],
        [
            "Database boundary",
            "Excel does not write PostgreSQL. The path is Excel → validated normalized TSV → controlled importer/API → DB.",
        ],
        [
            "ACTION values",
            "ADD_INSTRUMENT, UPDATE_INSTRUMENT, UPSERT_RELATIONS, REPLACE_RELATIONS, DEACTIVATE_INSTRUMENT.",
        ],
        [
            "Relation cardinality",
            "0..N PRIMARY and 0..N SECONDARY relations per instrument.",
        ],
        [
            "Relation weight",
            "Independent per-topic membership importance. PRIMARY 0.5..2.0 inclusive; SECONDARY 0.3..0.8 inclusive.",
        ],
        [
            "Delimiter",
            "Use literal |. Topic position N maps exactly to weight position N. Blank topic list and blank weight list means zero relations.",
        ],
        [
            "Validation",
            "Topics must resolve to current formal active status ACTIVE/ENABLED/PUBLISHED and be effective on AS_OF_DATE. Unknown or disabled topics are rejected; no topic auto-creation.",
        ],
        [
            "Representative Topic",
            "Optional and explicit. It is not inferred and has no automatic effect on relation cardinality or derived Topic metrics.",
        ],
        [
            "Relation Weight consumer boundary",
            "Relation Weight does not automatically change Topic Score, Heating/Cooling, Grade, Lifecycle, Leader, Today, or Opportunity.",
        ],
        [
            "Import commands",
            "python scripts/admin/database_maintenance_import.py --input <normalized.tsv> --validate-only; add --dry-run for DB-resolved operation plan; --apply requires explicit non-Production authorization.",
        ],
        [
            "What Excel is not allowed to do",
            "It must not directly write Production PostgreSQL, create unknown topics, silently clamp weights, infer representative topics, or partially apply a batch.",
        ],
    ]
    return rows


def _lookup_rows(snapshot: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [
        ["Actions", None, None, None],
        *[[item, None, None, None] for item in sorted(MAINTENANCE_ACTIONS)],
    ]
    rows += [
        ["Markets", None, None, None],
        *[
            [item, None, None, None]
            for item in sorted(snapshot.get("markets") or MARKET_CODES)
        ],
    ]
    rows += [
        ["Active/Enabled values", None, None, None],
        *[[item, None, None, None] for item in ["TRUE", "FALSE", "ACTIVE", "INACTIVE"]],
    ]
    rows += [
        ["Instrument types", None, None, None],
        *[[item, None, None, None] for item in ["EQUITY"]],
    ]
    rows += [["Topic names", "Topic slugs", "Topic status", "Active for maintenance"]]
    rows += [
        [
            item.get("name"),
            item.get("slug"),
            item.get("status"),
            item.get("status") in TOPIC_ACTIVE_STATUSES,
        ]
        for item in snapshot.get("topics", [])
    ]
    rows += [
        ["Weight ranges", None, None, None],
        ["PRIMARY", "0.5", "2.0", "inclusive"],
        ["SECONDARY", "0.3", "0.8", "inclusive"],
    ]
    return rows


def _formula_rows(row_count: int) -> tuple[list[list[Any]], list[list[Any]]]:
    status_rows: list[list[str]] = []
    error_rows: list[list[str]] = []
    for row in range(2, row_count + 2):
        status_rows.append(
            [
                f'=IF(COUNTA(A{row}:N{row})=0,"BLANK",IF(A{row}="","ERROR: UNKNOWN_ACTION",IF(B{row}="","ERROR: MISSING_STOCK_CODE",IF(D{row}="","ERROR: INVALID_MARKET",IF(AND(H{row}="",I{row}<>""),"ERROR: TOPIC_WEIGHT_COUNT_MISMATCH",IF(AND(H{row}<>"",(LEN(H{row})-LEN(SUBSTITUTE(H{row},"|",""))+1)<>(LEN(I{row})-LEN(SUBSTITUTE(I{row},"|",""))+1)),"ERROR: TOPIC_WEIGHT_COUNT_MISMATCH",IF(AND(J{row}="",K{row}<>""),"ERROR: TOPIC_WEIGHT_COUNT_MISMATCH",IF(AND(J{row}<>"",(LEN(J{row})-LEN(SUBSTITUTE(J{row},"|",""))+1)<>(LEN(K{row})-LEN(SUBSTITUTE(K{row},"|",""))+1)),"ERROR: TOPIC_WEIGHT_COUNT_MISMATCH","REVIEW_IMPORTER"))))))))',
            ]
        )
        error_rows.append(
            [
                f'=IF(O{row}="BLANK","",IF(O{row}="REVIEW_IMPORTER","Use validate-only importer for canonical topic/status/range checks",O{row}))',
            ]
        )
    return status_rows, error_rows


def _format_sheet(
    sheet: Any, headers: list[str], row_count: int, *, input_sheet: bool = False
) -> None:
    sheet.show_grid_lines = False
    sheet.freeze_panes.freeze_rows(1)
    if headers:
        header = sheet.get_range(f"A1:{_used_range_end(len(headers), 1)}")
        header.format.fill.color = COLORS["navy"]
        header.format.set_font(
            {"bold": True, "color": COLORS["white"], "name": "Arial", "size": 10}
        )
        header.format.horizontal_alignment = "center"
        header.format.vertical_alignment = "center"
        header.format.wrap_text = True
        if row_count:
            body = sheet.get_range(f"A2:{_used_range_end(len(headers), row_count + 1)}")
            body.format.set_font({"name": "Arial", "size": 10, "color": COLORS["text"]})
            body.format.vertical_alignment = "center"
            body.format.wrap_text = False
            if input_sheet:
                sheet.get_range(f"A2:N{row_count + 1}").format.fill.color = COLORS[
                    "input"
                ]
                sheet.get_range(f"O2:P{row_count + 1}").format.fill.color = COLORS[
                    "formula"
                ]
        sheet.get_range(
            f"A1:{_used_range_end(len(headers), row_count + 1)}"
        ).format.borders = {
            "preset": "inside",
            "style": "solid",
            "color": "#D9E2F3",
        }
        sheet.get_range(
            f"A:{_used_range_end(len(headers), 1).rstrip('1')}"
        ).format.autofit_columns()
        sheet.get_range(f"1:{row_count + 1}").format.autofit_rows()


def _add_table(sheet: Any, headers: list[str], row_count: int, name: str) -> None:
    # The table range includes the header and any reserved input rows so the
    # Owner can filter and extend the workbook without rebuilding it.
    end = _used_range_end(len(headers), max(1, row_count + 1))
    table = sheet.tables.add(f"A1:{end}", True, name)
    table.write_style("TableStyleMedium2")
    table.write_show_headers(True)
    table.write_show_banded_rows(True)


def _build_with_artifact_tool(
    snapshot: dict[str, Any], output_path: Path, render_dir: Path | None
) -> dict[str, Any]:
    from artifact_tool_v2.generated.interface.models import SpreadsheetFile, Workbook

    workbook = Workbook.create()
    for sheet_name in SHEET_NAMES:
        workbook.worksheets.add(sheet_name)
    readme = workbook.worksheets.get_item("README")
    readme.get_range(f"A1:B{len(_readme_rows(snapshot))}").values = [
        [_cell_value(value) for value in row] for row in _readme_rows(snapshot)
    ]
    readme.get_range("A1:B1").format.set_font(
        {"bold": True, "name": "Arial", "size": 14, "color": COLORS["navy"]}
    )
    readme.get_range(f"A2:A{len(_readme_rows(snapshot))}").format.set_font(
        {"bold": True, "name": "Arial", "size": 10, "color": COLORS["text"]}
    )
    readme.get_range(f"B2:B{len(_readme_rows(snapshot))}").format.set_font(
        {"name": "Arial", "size": 10, "color": COLORS["text"]}
    )
    readme.get_range(f"A1:B{len(_readme_rows(snapshot))}").format.wrap_text = True
    readme.get_range("A:A").format.column_width = 28
    readme.get_range("B:B").format.column_width = 100
    readme.show_grid_lines = False
    readme.tab_color = COLORS["navy"]

    current = _current_sheet_rows(snapshot)
    for sheet_name, (headers, rows) in current.items():
        sheet = workbook.worksheets.get_item(sheet_name)
        values = [headers] + [[_cell_value(value) for value in row] for row in rows]
        sheet.get_range(
            f"A1:{_used_range_end(len(headers), len(values))}"
        ).values = values
        _format_sheet(sheet, headers, len(rows))
        if rows:
            _add_table(sheet, headers, len(rows), _table_name(sheet_name))
        sheet.tab_color = COLORS["muted"]

    input_sheet = workbook.worksheets.get_item("Maintenance_Input")
    reserved_rows = 50
    input_values = [INPUT_HEADERS] + [
        [None] * len(INPUT_HEADERS) for _ in range(reserved_rows)
    ]
    input_sheet.get_range(
        f"A1:{_used_range_end(len(INPUT_HEADERS), reserved_rows + 1)}"
    ).values = input_values
    status_formulas, error_formulas = _formula_rows(reserved_rows)
    input_sheet.get_range(f"O2:O{reserved_rows + 1}").formulas = status_formulas
    input_sheet.get_range(f"P2:P{reserved_rows + 1}").formulas = error_formulas
    _format_sheet(input_sheet, INPUT_HEADERS, reserved_rows, input_sheet=True)
    _add_table(input_sheet, INPUT_HEADERS, reserved_rows, "MaintenanceInputTable")
    input_sheet.freeze_panes.freeze_columns(2)
    input_sheet.tab_color = COLORS["input"]
    input_sheet.get_range(
        f"L2:L{reserved_rows + 1}"
    ).format.number_format = "yyyy-mm-dd"
    input_sheet.get_range(f"O2:P{reserved_rows + 1}").conditional_formats.add_custom(
        '=OR(LEFT($O2,5)="ERROR",$O2="REVIEW_IMPORTER")',
        {"fill": COLORS["error"], "font": {"color": "#9C0006"}},
    )
    input_sheet.get_range(f"A2:A{reserved_rows + 1}").data_validation = {
        "allowBlank": True,
        "list": {"inCellDropDown": True, "source": sorted(MAINTENANCE_ACTIONS)},
    }
    input_sheet.get_range(f"D2:D{reserved_rows + 1}").data_validation = {
        "allowBlank": True,
        "list": {
            "inCellDropDown": True,
            "source": sorted(snapshot.get("markets") or MARKET_CODES),
        },
    }
    input_sheet.get_range(f"G2:G{reserved_rows + 1}").data_validation = {
        "allowBlank": True,
        "list": {
            "inCellDropDown": True,
            "source": ["TRUE", "FALSE", "ACTIVE", "INACTIVE"],
        },
    }
    input_sheet.get_range(f"E2:E{reserved_rows + 1}").data_validation = {
        "allowBlank": True,
        "list": {"inCellDropDown": True, "source": ["EQUITY"]},
    }

    preview = workbook.worksheets.get_item("Import_Preview")
    preview.get_range(f"A1:{_used_range_end(len(PREVIEW_HEADERS), 2)}").values = [
        PREVIEW_HEADERS,
        [
            None,
            "INFO",
            "NO_ACTIVE_INPUT_ROWS",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "INFO",
            "Edit Maintenance_Input, then run the controlled validator to populate normalized operations.",
        ],
    ]
    _format_sheet(preview, PREVIEW_HEADERS, 1)
    _add_table(preview, PREVIEW_HEADERS, 1, "ImportPreviewTable")
    preview.tab_color = COLORS["blue"]

    errors = workbook.worksheets.get_item("Validation_Errors")
    errors.get_range(f"A1:{_used_range_end(len(ERROR_HEADERS), 2)}").values = [
        ERROR_HEADERS,
        [
            None,
            None,
            None,
            None,
            "NO_VALIDATION_RUN",
            "Run database_maintenance_import.py --validate-only against this workbook's exported TSV.",
            "INFO",
        ],
    ]
    _format_sheet(errors, ERROR_HEADERS, 1)
    _add_table(errors, ERROR_HEADERS, 1, "ValidationErrorsTable")
    errors.tab_color = COLORS["error"]

    lookups = workbook.worksheets.get_item("Lookups")
    lookup_values = _lookup_rows(snapshot)
    lookup_headers = ["Lookup", "Value", "Value 2", "Notes"]
    lookups.get_range(f"A1:D{len(lookup_values) + 1}").values = [
        lookup_headers,
        *[[_cell_value(v) for v in row] for row in lookup_values],
    ]
    _format_sheet(lookups, ["Lookup", "Value", "Value 2", "Notes"], len(lookup_values))
    lookups.tab_color = COLORS["muted"]

    workbook.recalculate()
    if render_dir:
        render_dir.mkdir(parents=True, exist_ok=True)
        for sheet_name in SHEET_NAMES:
            preview_blob = workbook.render(
                {
                    "sheet_name": sheet_name,
                    "auto_crop": "all",
                    "scale": 1,
                    "format": "png",
                }
            )
            preview_blob.save(render_dir / f"{sheet_name}.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    blob = SpreadsheetFile.export_xlsx(workbook)
    blob.save(output_path)
    return {
        "engine": "artifact_tool_v2",
        "worksheets": list(SHEET_NAMES),
        "reserved_input_rows": reserved_rows,
        "rendered_sheets": bool(render_dir),
    }


def _build_with_openpyxl(snapshot: dict[str, Any], output_path: Path) -> dict[str, Any]:
    from openpyxl import Workbook
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Alignment, Font, PatternFill, Side
    from openpyxl.worksheet.datavalidation import DataValidation

    workbook = Workbook()
    workbook.remove(workbook.active)
    header_fill = PatternFill("solid", fgColor=COLORS["navy"].lstrip("#"))
    header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    thin = Side(style="thin", color="D9E2F3")
    for sheet_name in SHEET_NAMES:
        workbook.create_sheet(sheet_name)
    readme = workbook["README"]
    for row_idx, row in enumerate(_readme_rows(snapshot), start=1):
        for col_idx, value in enumerate(row, start=1):
            cell = readme.cell(row_idx, col_idx, _cell_value(value))
            cell.alignment = Alignment(wrap_text=True, vertical="center")
            cell.font = Font(
                name="Arial",
                size=10,
                bold=col_idx == 1,
                color=COLORS["text"].lstrip("#"),
            )
    readme["A1"].font = Font(
        name="Arial", size=14, bold=True, color=COLORS["navy"].lstrip("#")
    )
    readme.column_dimensions["A"].width = 28
    readme.column_dimensions["B"].width = 100
    readme.sheet_view.showGridLines = False
    current = _current_sheet_rows(snapshot)
    for sheet_name, (headers, rows) in current.items():
        ws = workbook[sheet_name]
        ws.append(headers)
        for row in rows:
            ws.append([_cell_value(value) for value in row])
        _style_openpyxl_sheet(ws, headers, header_fill, header_font, thin, len(rows))
    ws = workbook["Maintenance_Input"]
    ws.append(INPUT_HEADERS)
    for _ in range(50):
        ws.append([None] * len(INPUT_HEADERS))
    for row in range(2, 52):
        ws.cell(
            row,
            15,
            f'=IF(COUNTA(A{row}:N{row})=0,"BLANK",IF(A{row}="","ERROR: UNKNOWN_ACTION",IF(B{row}="","ERROR: MISSING_STOCK_CODE",IF(D{row}="","ERROR: INVALID_MARKET","REVIEW_IMPORTER"))))',
        )
        ws.cell(
            row,
            16,
            f'=IF(O{row}="BLANK","",IF(O{row}="REVIEW_IMPORTER","Use validate-only importer for canonical topic/status/range checks",O{row}))',
        )
        for col in range(1, 15):
            ws.cell(row, col).fill = PatternFill(
                "solid", fgColor=COLORS["input"].lstrip("#")
            )
        for col in range(15, 17):
            ws.cell(row, col).fill = PatternFill(
                "solid", fgColor=COLORS["formula"].lstrip("#")
            )
    _style_openpyxl_sheet(ws, INPUT_HEADERS, header_fill, header_font, thin, 50)
    ws.freeze_panes = "C2"
    ws.add_data_validation(
        DataValidation(
            type="list",
            formula1='"' + ",".join(sorted(MAINTENANCE_ACTIONS)) + '"',
            allow_blank=True,
        )
    )
    ws.data_validations.dataValidation[0].add("A2:A51")
    ws.add_data_validation(
        DataValidation(
            type="list",
            formula1='"'
            + ",".join(sorted(snapshot.get("markets") or MARKET_CODES))
            + '"',
            allow_blank=True,
        )
    )
    ws.data_validations.dataValidation[1].add("D2:D51")
    ws.add_data_validation(
        DataValidation(
            type="list", formula1='"TRUE,FALSE,ACTIVE,INACTIVE"', allow_blank=True
        )
    )
    ws.data_validations.dataValidation[2].add("G2:G51")
    ws.add_data_validation(
        DataValidation(type="list", formula1='"EQUITY"', allow_blank=True)
    )
    ws.data_validations.dataValidation[3].add("E2:E51")
    ws.conditional_formatting.add(
        "O2:P51",
        FormulaRule(
            formula=['OR(LEFT($O2,5)="ERROR",$O2="REVIEW_IMPORTER")'],
            fill=PatternFill("solid", fgColor=COLORS["error"].lstrip("#")),
        ),
    )
    for name, headers, row in (
        (
            "Import_Preview",
            PREVIEW_HEADERS,
            [
                None,
                "INFO",
                "NO_ACTIVE_INPUT_ROWS",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                "INFO",
                "Edit Maintenance_Input, then run the controlled validator to populate normalized operations.",
            ],
        ),
        (
            "Validation_Errors",
            ERROR_HEADERS,
            [
                None,
                None,
                None,
                None,
                "NO_VALIDATION_RUN",
                "Run the controlled validator against this workbook's exported TSV.",
                "INFO",
            ],
        ),
    ):
        ws = workbook[name]
        ws.append(headers)
        ws.append(row)
        _style_openpyxl_sheet(ws, headers, header_fill, header_font, thin, 1)
    ws = workbook["Lookups"]
    ws.append(["Lookup", "Value", "Value 2", "Notes"])
    for row in _lookup_rows(snapshot):
        ws.append(row)
    _style_openpyxl_sheet(
        ws,
        ["Lookup", "Value", "Value 2", "Notes"],
        header_fill,
        header_font,
        thin,
        len(_lookup_rows(snapshot)),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    return {
        "engine": "openpyxl_fallback",
        "worksheets": list(SHEET_NAMES),
        "reserved_input_rows": 50,
        "rendered_sheets": False,
    }


def _style_openpyxl_sheet(
    ws: Any,
    headers: list[str],
    header_fill: Any,
    header_font: Any,
    thin: Any,
    data_rows: int,
) -> None:
    from openpyxl.styles import Alignment, Border, Font
    from openpyxl.worksheet.table import Table, TableStyleInfo

    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A2"
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
    for row in ws.iter_rows(
        min_row=2, max_row=max(2, data_rows + 1), min_col=1, max_col=len(headers)
    ):
        for cell in row:
            cell.font = Font(name="Arial", size=10, color=COLORS["text"].lstrip("#"))
            cell.alignment = Alignment(vertical="center", wrap_text=False)
            cell.border = Border(bottom=thin)
    for index, header in enumerate(headers, start=1):
        ws.column_dimensions[chr(64 + index) if index <= 26 else "A"].width = min(
            max(len(header) + 2, 12), 28
        )
    if data_rows:
        ref = (
            f"A1:{chr(64 + len(headers)) if len(headers) <= 26 else 'Z'}{data_rows + 1}"
        )
        table = Table(
            displayName=re.sub(r"[^A-Za-z0-9]", "", ws.title)[:20] + "Table", ref=ref
        )
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        ws.add_table(table)


def build_workbook(
    snapshot_path: Path, output_path: Path, *, render_dir: Path | None = None
) -> dict[str, Any]:
    snapshot = _load_snapshot(snapshot_path)
    try:
        return _build_with_artifact_tool(snapshot, output_path, render_dir)
    except Exception as exc:  # noqa: BLE001 - fallback must handle missing artifact runtime APIs
        fallback = _build_with_openpyxl(snapshot, output_path)
        fallback["artifact_tool_error"] = f"{type(exc).__name__}: {exc}"
        return fallback


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--render-dir", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build_workbook(args.snapshot_json, args.output, render_dir=args.render_dir),
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
