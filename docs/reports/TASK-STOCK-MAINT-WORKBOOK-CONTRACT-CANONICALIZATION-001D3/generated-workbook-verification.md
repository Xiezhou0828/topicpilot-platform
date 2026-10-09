# Generated workbook verification

> **RETIRED / HISTORICAL ONLY — 2026-10-09.** The path below records a historical non-Production verification artifact and is preserved for audit traceability. The workbook is no longer a current, canonical, formal, Production, or daily maintenance source and must not be used for new work. Use `docs/operations/database-maintenance-excel.md` and `E:\topicpilot-artifacts\database-maintenance-excel\TopicPilot_Database_Maintenance.xlsx` for the current controlled workflow.

```text
GENERATED_WORKBOOK_PATH=E:\topicpilot-stock-maint-bootstrap-001\artifacts\TopicPilot_股票維護_001D3_驗證.xlsx
GENERATED_WORKBOOK_STATUS=PASS_FALLBACK_EXPORT_FROM_RECONCILED_GENERATOR_DATA
GENERATED_HEADERS_STATUS=PASS
GENERATED_MULTI_PRIMARY_ROW_STATUS=PASS
GENERATED_ZERO_TOPIC_ROW_STATUS=PASS
```

The artifact was generated on E: from the same canonical reference bundle,
Structural Role authority, Topic scope, mapping CSV, lifecycle bundle, and
workbook source used by `build_stock_maintenance_workbook.mjs`. The bundled
Node runtime does not contain `@oai/artifact-tool`, so direct JS export stopped
at dependency resolution without writing an output. The fallback exporter was
used only to create the non-production verification artifact; no Owner source
workbook was overwritten.

Inspection results:

```text
WORKSHEETS=8
CURRENT_STOCK_TOPICS_ROWS=556
CURRENT_STOCK_TOPICS_COLUMNS=11
MULTI_PRIMARY_ROWS=102
ZERO_TOPIC_ROWS=53
ARTIFACT_SIZE_BYTES=184013
ARTIFACT_SHA256=7F43383F9FD9BFEC5866030E58629E23A04B204360000B88558BD0DDFA603F2D
```

Representative generated rows include a multi-primary row for `1773` with a
pipe-separated PRIMARY list and a zero-topic row for `2414` with both relation
lists empty. Empty weights remain blank rather than being inferred.

```text
GENERATOR_SYNTAX_STATUS=PASS
GENERATOR_RUNTIME_STATUS=BLOCKED_MISSING_DEPENDENCY
FALLBACK_LIMITATION=Native artifact-tool render/export path unavailable in this runtime
```

