# TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE

Date: 2026-08-15 (Asia/Taipei)

## 1. Executive Decision

FINAL_STATUS=RAW_BOUNDED_EXPORTS_VALIDATED_ENVELOPE_NORMALIZATION_REQUIRED

RESUME=YES
SOURCE_AUTHORITY_REAUDIT=NO_PRIOR_CLOSURE_REUSED

Owner-provided official bounded CSV exports are now present and were validated through the local import gate. The raw CSVs remain external and read-only. Their normalized envelopes, outside-universe audit rows, manifests, checkpoints, and the merged research-only dataset were generated locally without any network request.

Therefore:

- TPEX_ARTIFACT_PRESENT=YES
- TPEX_ARTIFACT_SOURCE=OWNER_PROVIDED_OFFICIAL_BOUNDED_CSV
- TPEX_COVERAGE=PARTIAL_NOT_COMPLETE
- TWSE_COVERAGE=PARTIAL_IMPROVED_NOT_COMPLETE
- OVERALL_RESEARCH_WINDOW_COVERAGE=PARTIAL_WITH_METHOD_GAPS
- DATASET_IMPLEMENTATION_AUTHORIZED=YES
- The implementation authorization was established by the predecessor task and the Owner export has now passed normalization/import validation; this task still does not authorize freeze.
- REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO_UNDER_CURRENT_FULL_COVERAGE_GATE
- REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO

The remaining blocker is full 507-identity and event-family coverage. The bounded exports do not cover capital reduction, split/par-value change, merger/share conversion, or lifecycle families as complete historical surfaces. Those gaps remain UNKNOWN/method gaps, not PASS_NO_EVENT.

## 2. Canonical Preflight

Canonical repository:

    C:\Users\acer\Desktop\題材領航\topicpilot-platform

Preflight state before this task's write set:

- CANONICAL_PRE_SHA=454a558bbc10f53576c652ff11144dd39159dacf
- BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
- ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
- WORKTREE_USED=NO
- WORKTREE_CREATED=NO
- ACTIVE_WORKTREES=15 observed at preflight
- DIRTY_FILES=171 observed at preflight

The repository was already shared with parallel work. The resume touched only the exact research readiness paths, derived owner-artifact outputs, the canonical research artifact, and this report. No unrelated dirty files, branches, or worktrees were reset, stashed, overwritten, or removed.

## 3. Prior Dataset Baseline

The predecessor implementation task produced the unchanged local artifact:

- DATASET_VERSION=REC-A1-CA-EVENTS-V0
- ARTIFACT_TYPE=NORMALIZED_SEMANTIC_DATASET
- DATASET_SCHEMA_VERSION=rec-a1-corporate-action-research-dataset.v0
- SEMANTIC_VERSION=CA-EVENT-SCHEMA-V0
- DATASET_ROWS=2
- TWSE_ROWS=2
- TPEX_ROWS=0
- COVERED_IDENTITIES=2
- COVERED_EVENTS=2
- UNKNOWN_ROWS=0
- DUPLICATES=0
- INVALID_IDENTITIES=0
- INVALID_EFFECTIVE_DATES=0
- MISSING_LINEAGE=0
- SEMANTIC_HASH_COLLISIONS=0

The two-row state above is the pre-resume baseline. It was replaced by the validated normalized import described in Sections 14 through 23; the original CSV bytes were not copied or modified.

## 4. Owner Decision and External Source Boundary

OWNER_DECISION=APPROVED_INTERNAL_RESEARCH_ONLY

OWNER_APPROVAL_STATUS=APPROVED_INTERNAL_RESEARCH_ONLY

The Owner approval covers internal research use of confirmed official TWSE/TPEx corporate-action data, local/research storage where the source terms and access method permit it, normalization, lineage, content/semantic hashing, checkpoint/idempotent replay, research datasets, backtest/walk-forward research, and EVENT_EXCLUDED_RAW_V0 episode exclusion.

It does not replace exchange permission, authorize prohibited automated extraction, authorize public download or redistribution, authorize raw-dataset publication, or authorize Production use.

For TPEx, AUTOMATED_EXTRACTION_TPEX=BLOCKED. A manual or bounded official export is the only current V0 path proposed for closure:

- MANUAL_BOUNDED_INGESTION=VALIDATED_OWNER_EXPORT
- RAW_REPRODUCTION_STATUS=NOT_APPROVED
- PUBLIC_REDISTRIBUTION_STATUS=NOT_APPROVED

## 5. Official Source and Terms Evidence

The official TPEx surfaces requested for the bounded handoff are:

1. Ex-right/ex-dividend announcements: https://www.tpex.org.tw/en-us/announce/market/ex/announce.html
2. Ex-right/ex-dividend calculation: https://www.tpex.org.tw/en-us/announce/market/ex/cal.html
3. Reduction reference-price information: https://www.tpex.org.tw/en-us/announce/market/reduction/reference.html
4. Reduction announcements: https://www.tpex.org.tw/en-us/announce/market/reduction-tdr.html

查證日期=2026-08-15.

The official TPEx E-Data Shop Terms of Use were reviewed at:

https://eshop.tpex.org.tw/en/useTerms/index

The terms state that software or data may not be downloaded through automated devices, scripts, automated programs, spiders, web crawlers, or extraction except by methods approved by TPEx or with TPEx consent. They also state that the content is protected by intellectual-property rights and may not be reproduced, distributed, published, or otherwise reused without the required consent. This is the reason the implementation does not make network requests and does not turn public page availability into automated-extraction permission.

The four market-information surfaces returned an official 403 response to the read-only browser check on 2026-08-15. That result is not treated as an empty result and does not create any event or no-event claim.

## 5.1 SOURCE_METHOD_AUTHORITY_MATRIX

| EXCHANGE | OFFICIAL_PRODUCT/SURFACE | EVENT_FAMILY | ACCESS_METHOD | HISTORICAL_RANGE | FIELDS | DATE_SEMANTICS | RATE/QUERY_LIMIT | AUTOMATION_LANGUAGE_IN_TERMS | LOCAL_RESEARCH_STORAGE_STATUS | NORMALIZATION_STATUS | HASH/LINEAGE_STATUS | REPLAY_STATUS | RAW_REPRODUCTION_STATUS | PUBLIC_REDISTRIBUTION_STATUS | EXTERNAL_SOURCE_USE_STATUS | EVIDENCE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TWSE | Previously reviewed official corporate-action/lifecycle source surfaces plus canonical reduced control records | All primary families and semantic-partial families, subject to prior closure scope | CANONICAL_REDUCED_OFFICIAL_RECORDS plus owner TWT49U manual export; no unattended bulk method authorized | 2026-02-02 to 2026-08-13 target; current materialization is partial | Required CA-EVENT-SCHEMA-V0 fields plus source lineage | Effective trading/discontinuity date is primary; announcement date is provenance | Source-specific limits remain applicable; no new rate claim made here | Must use only an approved official method; public availability is not automation permission | Allowed only within source terms for reduced research records | READY for normalized owner rows | COMPLETE for normalized owner rows | PASS for normalized owner rows | NOT_APPROVED | NOT_APPROVED | PARTIAL_IMPROVED_NOT_COMPLETE | Prior source-use closure plus owner TWT49U hash |
| TPEx | Ex-right/ex-dividend announcements and calculation; reduction reference and announcements | Primary and semantic-partial families explicitly scoped in the requested artifact | MANUAL_OR_BOUNDED_QUERY_ONLY | 2026-02-02 to 2026-08-13 exact bounded request | Required bounded envelope and event-row fields in Section 7 | Primary effective date required; announcement/record/reference dates preserved only if returned | Query/export scope and any official limit must be recorded in the artifact; no unattended rate assumption | TPEx Terms prohibit automated devices/scripts/spiders/crawlers/extraction except approved methods or consent | DERIVED_NORMALIZED_ONLY_RAW_EXTERNAL_READ_ONLY | VALIDATED_OWNER_EXPORT | PASS for normalized owner rows | PASS_BOUNDED_IMPORT | NOT_APPROVED | NOT_APPROVED | PARTIAL_NOT_COMPLETE | Official TPEx surfaces, TPEx Terms, owner CSV hash, and normalized envelope |

This matrix is a method boundary, not a claim that the public surfaces are complete or that an absent result means no event.

## 6. TPEX_BOUNDED_ARTIFACT_REQUIREMENTS

ARTIFACT_REQUIREMENTS_READY=YES

TPEX_ARTIFACT_FORMAT=JSON_OBJECT_OR_JSON_ARRAY_OR_CSV_UTF8_OR_CSV_UTF8_BOM

TPEX_ARTIFACT_QUERY_WINDOW=2026-02-02_TO_2026-08-13

TPEX_ARTIFACT_EVENT_SCOPE=PRIMARY_AND_SEMANTIC_PARTIAL_FAMILIES_EXPLICIT

The implementation defines TPEX_BOUNDED_ARTIFACT_REQUIREMENTS in:

services/api/src/topicpilot_api/research/corporate_action_dataset.py

The requirement object records:

- official surfaces;
- query date range 2026-02-02 through 2026-08-13;
- TWO security scope based on current tw-reference-v1 identities;
- explicit handling for rows outside the current 507 universe/lifecycle scope;
- primary and semantic-partial event families;
- required and optional fields;
- accepted file formats;
- explicit date/family scope semantics;
- manual operator steps;
- no raw bulk response retention unless the applicable terms permit it.

The code now accepts the owner CSV through a local read-only normalizer, emits the existing reduced normalized JSON envelope, preserves source row positions, and records raw file hashes without retaining raw bytes. There is no CSV network ingestion or unattended CSV crawler.

## 7. Owner Artifact Contract and Received Export

OWNER_ARTIFACT_REQUEST_REQUIRED=NO_CURRENT_ARTIFACT_PRESENT

The following contract was requested and is now fulfilled by the Owner-provided TWSE and TPEx exports. Its scope remains the validation boundary for future batches:

### Source and scope

- Use one or more of the four official TPEx surfaces listed above.
- Query exactly 2026-02-02 through 2026-08-13, or provide explicit bounded batches whose union covers that interval.
- Include the exact official surface, query/export date, date range, event-family scope, and security scope in the artifact envelope.
- Scope current TWO identities from tw-reference-v1. If the official export returns rows outside the current fixed 507 universe/lifecycle scope, retain them for classification or explicitly record them as outside-scope; do not silently discard them.
- Cover cash dividend/ex-dividend, stock dividend/ex-right, rights issue/capital increase reference-price reset, and capital reduction.
- Also explicitly scope split/reverse-split/par-value change, merger/share conversion/demerger, and listing/termination/resumption discontinuity. If a family is not available from the selected surface, record that fact as a bounded method gap rather than silently treating it as empty.

### Required record fields

Every event record must provide:

- source_name
- official_product_or_surface
- access_method
- source_url
- source_record_id_or_canonical_row_key
- market_code
- instrument_code
- canonical_identity
- event_type
- primary_effective_date
- retrieved_at
- semantic_version
- authority_state
- query_or_export_manifest_id
- checkpoint_id
- reason_code

The following may be null when the official surface does not return them:

- announcement_date_if_available
- reference_price_if_officially_returned
- source_as_of_if_available
- source_content_hash_if_storage_permitted

The primary effective date, TWO market code, instrument code, canonical identity, event type, source record key, authority state, manifest ID, checkpoint ID, and semantic version may not be missing. Missing critical fields fail closed.

### Artifact envelope

The preferred handoff is a reduced JSON object with:

- artifact_type=TPEX_BOUNDED_CORPORATE_ACTION_ARTIFACT
- source_name=TPEx
- official_surface
- source_url
- access_method=MANUAL_OR_BOUNDED_QUERY_ONLY
- query_window_start
- query_window_end
- event_family_scope
- security_scope
- retrieved_at
- manifest_id
- checkpoint_id
- records
- optional record_count
- optional source_as_of_if_available
- optional content_hash_if_allowed

Accepted handoff formats are JSON object, JSON array, UTF-8 CSV, or UTF-8-BOM CSV. A suggested filename is:

    tpex_corporate_action_bounded_2026-02-02_2026-08-13_v0.json

A proposed handoff location is:

    reports/TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE/owner-artifact/

The location is a request only; no empty or fabricated artifact directory was created.

### Empty-result rule

A zero-row export is acceptable as PASS_NO_EVENT only if:

1. the official query was completed;
2. the source, date range, event-family scope, and security scope are explicit;
3. the official response semantics establish that the result is complete for that scope;
4. the manifest and checkpoint identify the query/export;
5. the source record or export evidence is retained or referenced within permitted terms.

A zero-row artifact without those properties remains UNKNOWN.

## 8. Import Contract and Validation Readiness

The TPEx parser is in:

services/api/src/topicpilot_api/research/corporate_action_dataset.py

It:

- performs no network request;
- requires a bounded envelope;
- rejects unknown envelope fields and missing scope/lineage fields;
- requires MANUAL_OR_BOUNDED_QUERY_ONLY;
- validates an official TPEx host;
- restricts the market code to TWO;
- derives and validates the canonical identity as TWO:<instrument_code>;
- requires event type to be within the explicit artifact scope;
- requires primary_effective_date and checks it against the bounded query window;
- rejects raw_response and raw_rows shaped payloads;
- applies the existing CA-EVENT-SCHEMA-V0 normalization and semantic hash;
- rejects duplicate semantic events;
- returns zero records only as a parsed bounded artifact result, not as a coverage claim.

The dataset loader and validator validate the merged artifact against tw-reference-v1. Import remains an explicit local operation; no production or database path writes these records automatically.

## 9. Identity and Lifecycle Mapping

IDENTITY_MAPPING_STATE=VALIDATED_CANONICAL_507_WITH_OUTSIDE_AUDIT

Canonical identity rules are:

- TWSE rows use TPE:<instrument_code>.
- TPEx rows use TWO:<instrument_code>.
- TPEx records with a non-TWO market code fail closed.
- A supplied canonical_identity must equal the derived TWO identity or be absent and then derived.
- Current 507/lifecycle membership is validated against tw-reference-v1 by the dataset validator.
- Outside-current-507 or outside-lifecycle records must be classified explicitly and cannot silently expand the canonical universe.

The existing controls remain:

- TPE:2330 maps to the canonical identity TPE:2330.
- TPE:6806 maps to the canonical identity TPE:6806 and its lifecycle evidence.
- No new identity or PIT universe was created.

## 10. Event Family Coverage

The event-family authority boundary remains:

| Event family | TWSE current state | TPEx current state | V0 action |
| --- | --- | --- | --- |
| Cash dividend / ex-dividend | PARTIAL | PARTIAL | Imported where bounded rows exist; effective-date keyed |
| Stock dividend / ex-right | PARTIAL | PARTIAL | Imported; TPEx component fields support explicit semantics |
| Combined ex-right/ex-dividend semantic partial | PARTIAL | NOT_MATERIALIZED | TWSE 權息 retained as one non-authoritative split-safe record |
| Rights issue / capital increase reference-price reset | UNKNOWN | PARTIAL | TPEx imported; TWSE export lacks separated capital-increase fields |
| Capital reduction | UNKNOWN | UNKNOWN | Bounded method gap; not PASS_NO_EVENT |
| Split / reverse split / par value change | UNKNOWN | UNKNOWN | Bounded method gap; not PASS_NO_EVENT |
| Merger / share conversion / demerger | UNKNOWN | UNKNOWN | Bounded method gap; identity discontinuity required |
| Listing / termination / resumption discontinuity | PARTIAL for 6806 control | UNKNOWN | Lifecycle authority required; TPEx export does not cover it |

The matrix now reflects imported family rows and explicit method gaps. UNKNOWN means the bounded exports do not establish coverage for that family; it is not a no-event conclusion.

## 11. Effective-Date and Semantic Closure

### EVENT_SEMANTIC_CLOSURE_MATRIX

| EVENT_TYPE | PRIMARY_EFFECTIVE_DATE_FIELD | ANNOUNCEMENT_DATE_FIELD | REFERENCE_PRICE_FIELD | RATIO/PAR_FIELDS | IDENTITY_EFFECT | PRICE_CONTINUITY_EFFECT | VOLUME_CONTINUITY_EFFECT | OFFICIAL_SOURCE | SEMANTIC_STATUS | PIT_STATUS | V0_ACTION |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CASH_DIVIDEND_EX_DIVIDEND | ex-dividend trading date | optional official announcement/publication date | optional official reference price | optional dividend value | continuous identity | discontinuity possible | continuity normally retained | TWSE/TPEx official corporate-action surface | COVERED_FOR_NORMALIZED_OWNER_ROWS | outcome exclusion only; trading use forbidden | imported when bounded effective date is deterministic |
| STOCK_DIVIDEND_EX_RIGHT | ex-right trading date | optional official announcement/publication date | optional official reference price | official ratio when returned | continuous identity | discontinuity possible | continuity normally retained | TWSE/TPEx official ex-right surface | COVERED_FOR_NORMALIZED_OWNER_ROWS; TWSE PARTIAL | outcome exclusion only; trading use forbidden | imported when ratio/date semantics are explicit |
| COMBINED_EX_RIGHT_EX_DIVIDEND_SEMANTIC_PARTIAL | ex-right/ex-dividend trading date | optional official announcement/publication date | official combined reference price when returned | combined 权值+息值 only | continuous identity | discontinuity likely | may be discontinuous | TWSE TWT49U bounded export | SEMANTIC_PARTIAL | outcome exclusion only; trading use forbidden | preserve one partial event; do not split |
| RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET | official reference-price effective trading date | optional announcement/publication date | official reference price when returned | issue ratio/par fields when returned | generally continuous; verify source | discontinuity possible | may be discontinuous | TWSE/TPEx official capital-increase/reference-price surface | SEMANTIC_PARTIAL | outcome exclusion only; trading use forbidden | import only with official reset semantics |
| CAPITAL_REDUCTION | official capital-reduction effective trading date | optional announcement/publication date | official reference price when returned | reduction ratio/par fields when returned | may be continuous or discontinuous; verify | discontinuity likely | may be discontinuous | TWSE/TPEx official reduction surface | SEMANTIC_PARTIAL | outcome exclusion only; trading use forbidden | import only with identity and reference semantics |
| SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE | official effective trading date | optional announcement/publication date | optional official reference price | split ratio/par value required when returned | continuous identity unless source says otherwise | discontinuity likely | may be discontinuous | TWSE/TPEx official event surface | SEMANTIC_PARTIAL | outcome exclusion only; trading use forbidden | import only when deterministic |
| MERGER_SHARE_CONVERSION_DEMERGER | official identity/effective date | optional announcement/publication date | optional official reference price | conversion ratio when returned | identity discontinuity possible | discontinuity likely | discontinuity likely | TWSE/TPEx official lifecycle/corporate-action surface | SEMANTIC_PARTIAL | outcome exclusion only; trading use forbidden | import only with canonical identity mapping |
| LISTING_TERMINATION_RESUMPTION_DISCONTINUITY | official listing/termination/resumption effective date | optional announcement/publication date | not required unless officially returned | not required unless officially returned | identity/lifecycle discontinuity | discontinuity likely | discontinuity likely | TWSE/TPEx official lifecycle source | COVERED_FOR_6806_CONTROL; TPEx METHOD_GAP | outcome exclusion only; trading use forbidden | import with lifecycle evidence |

The event key is based on the actual primary_effective_date that can create a trading price, volume, or identity discontinuity. Announcement/publication date is provenance only and must not substitute for the effective date.

The semantic fields required for an Owner artifact are:

| Semantic dimension | Required rule |
| --- | --- |
| announcement/publication date | Preserve when officially available; never substitute for effective date |
| record date | Preserve only when officially returned; not the V0 event key |
| ex-right/ex-dividend date | Use as primary effective date when it is the official discontinuity date |
| effective date | Required and must be in scope |
| reference-price effective trading date | Use when the official source identifies a separate trading-date reset |
| listing/termination date | Use for lifecycle identity discontinuity |
| reference price | Preserve only when officially returned |
| ratio/par value | Preserve when needed to explain the discontinuity |
| identity effect | Mark continuity or discontinuity explicitly |
| price/volume continuity | Drives EVENT_EXCLUDED_RAW_V0 mapping, not adjusted OHLCV |

V0 does not retroactively change a signal-date Gate, Rank, or Trigger. TRADING_DECISION_USE=FORBIDDEN. A post-hoc outcome integrity audit may exclude an episode based on the actual effective date.

## 12. Manifest, Hash, Checkpoint, and Replay

MANIFEST_IMPLEMENTED=YES

CHECKPOINT_IMPLEMENTED=YES

IDEMPOTENT=PASS

HASH_LINEAGE_REPLAY_STATUS=PASS_BOUNDED_IMPORT

HASH_LINEAGE_COMPLETE=YES_FOR_REDUCED_SEMANTIC_ROWS

Each accepted reduced row carries source lineage, source record identity, retrieval metadata, semantic version, manifest ID, checkpoint ID, normalized semantic hash, and a stable event key. Reordering the same event set does not change the dataset content hash or canonical export. Repeated semantic records are rejected rather than duplicated.

For the current unchanged artifact:

- 2330 normalized semantic hash is stable.
- 6806 normalized semantic hash is stable.
- no semantic hash collision exists.
- TPEx replay is validated against the normalized owner envelope; raw CSV replay remains external/read-only.

Raw official response retention remains bounded by source terms. Raw reproduction or public redistribution is not approved.

## 13. Idempotence and Empty Semantics

The parser and existing dataset contract preserve:

- deterministic stable event keys;
- deterministic normalized semantic hashes;
- duplicate rejection;
- manifest/checkpoint lineage;
- PASS_NO_EVENT only after explicit completed authoritative scope;
- UNKNOWN for absent or incomplete source scope;
- fail-closed validation for missing effective date, invalid identity, unsupported family, and ambiguous provenance.

For this task:

- PASS_NO_EVENT_CONTRACT=IMPLEMENTED_AND_TESTED
- COMPLETE_EMPTY_SET_VALIDATED=NO_FOR_UNREPRESENTED_EVENT_FAMILIES
- UNKNOWN_FAIL_CLOSED=YES

## 14. TPEx Coverage Result

The Owner-provided TPEx export passed the local validation/import gate:

- TPEX_FILE=C:\Users\acer\Desktop\Exright_1150202_1150813.csv
- TPEX_SHA256=566F4ACE3E8FED9E0D89C60D0F2471308B38A00C085A97E151E57BBBAC4DF316
- TPEX_RAW_EVENT_ROWS=853
- TPEX_CANONICAL_ROWS=131
- TPEX_CANONICAL_IDENTITIES=128
- TPEX_OUTSIDE_ROWS=722
- TPEX_OUTSIDE_IDENTITIES=493
- TPEX_NORMALIZED_EVENTS=138
- TPEX_COVERAGE=PARTIAL_NOT_COMPLETE
- TPEX_ARTIFACT_PRESENT=YES
- TPEX_ARTIFACT_SOURCE=OWNER_PROVIDED_OFFICIAL_BOUNDED_CSV
- AUTOMATED_EXTRACTION_TPEX=BLOCKED
- MANUAL_BOUNDED_INGESTION=VALIDATED_OWNER_EXPORT

The TPEx one-line footer was excluded from event-row parsing. The two 00970B name variants remain separate source-row audit/provenance records; no identity collapse is performed from the display name.

TPEx rows with explicit cash, stock, and capital-increase components were normalized without price inference. The 28 raw 除權息 rows were split only when the returned component fields supported the split. The normalized TPEx envelope and 493-identity outside audit are stored under the owner-artifact directory named in Section 22.

## 15. TWSE Coverage Reassessment

TWSE improved from the two-row pre-resume baseline but remains PARTIAL:

- TWSE_FILE=C:\Users\acer\Desktop\TWT49U (1).csv
- TWSE_SHA256=ED65E408FCD6223E875549E8CB853139B1379A73682CFB18CCA92E2109C0B90A
- TWSE_DOWNLOADS_FILE=C:\Users\acer\Downloads\TWT49U (1).csv
- TWSE_DOWNLOADS_SHA256=68759F7CD5FBA85FF2149513E649D3A4DB2E7B95AF05503A21398ADCB855303F
- TWSE_COPY_EQUIVALENCE=PASS_AFTER_ENCODING_NORMALIZATION
- MNT_DATA_TWT49U_PRESENT=NO_UNDER_WINDOWS_MOUNT
- TWSE_RAW_EVENT_ROWS=1035
- TWSE_CANONICAL_ROWS=233
- TWSE_CANONICAL_IDENTITIES=224
- TWSE_OUTSIDE_ROWS=802
- TWSE_OUTSIDE_IDENTITIES=632
- TWSE_NORMALIZED_EVENTS=233
- TWSE_DATASET_ROWS=234, including the 233 export events and the retained 6806 lifecycle event
- TWSE_DATASET_IDENTITIES=225
- TWSE_COVERAGE=PARTIAL_IMPROVED_NOT_COMPLETE

The 11 TWSE footer/explanatory rows were excluded from event-row parsing. Their exclusion is a structural CSV rule, not a no-event claim.

The 973 息 rows normalize to cash-dividend events, 27 權 rows to partial ex-right events, and 35 權息 rows to combined semantic-partial events. TWSE does not expose separated component fields in this export, so 權息 rows were not split into authoritative cash and stock events.

The current implementation does not claim full TWSE 507-identity coverage or full event-family completeness. Outside rows remain audit rows and do not enter the canonical dataset.

## 16. Research Window Coverage Matrix

Target window:

- HISTORICAL_WINDOW=2026-02-02_TO_2026-08-13
- UNIVERSE_POLICY=LIFECYCLE_GATED_507

Current coverage:

| Exchange | Materialized rows | Identity coverage | Event-family coverage | Window status |
| --- | ---: | ---: | --- | --- |
| TWSE | 234 dataset events; 233 export rows | 225 TPE identities of 314 | PARTIAL; method gaps remain | PARTIAL_IMPROVED_NOT_COMPLETE |
| TPEx | 138 normalized events; 131 export rows | 128 TWO identities of 193 | PARTIAL; method gaps remain | PARTIAL_NOT_COMPLETE |

OVERALL_RESEARCH_WINDOW_COVERAGE=PARTIAL_WITH_METHOD_GAPS

The code recomputes an exchange/family coverage matrix using explicit family_status values. Cash, stock, and rights families have materialized bounded rows; capital reduction, split/par-value change, merger/share conversion, and unrepresented lifecycle families remain UNKNOWN. Absence is never converted to PASS_NO_EVENT.

## 17. Complete Empty-Set Validation

COMPLETE_EMPTY_SET_VALIDATED=NO_FOR_UNREPRESENTED_EVENT_FAMILIES

The bounded exports establish populated results for the covered ex-right/ex-dividend families, but they do not establish complete empty sets for capital reduction, split/par-value change, merger/share conversion, or listing/termination/resumption. The implementation will not convert an unrepresented family into PASS_NO_EVENT. For every event family, the official response must make the query/export scope explicit and establish that the response is complete for that scope.

A future bounded artifact may close a family as complete-empty only if it meets the exact empty-result rule in Section 7.

## 18. EVENT_EXCLUDED_RAW_V0 Non-Regression

EVENT_EXCLUDED_RAW_POLICY=READY

EVENT_EXCLUDED_RAW_V0 remains an episode-integrity exclusion, not a loss, no-trigger, or trading signal. Excluded episodes do not enter T+5, T+10, MFE, MAE, win-rate, or expectancy denominators.

The current task does not:

- adjust OHLC;
- create total-return series;
- modify historical OHLCV;
- add an event-aware trading gate;
- change Gate, Rank, or Trigger;
- run a backtest or walk-forward.

The only accepted use is post-hoc outcome integrity exclusion by deterministic effective date.

## 19. Control Cases and Focused Validation

The preserved control cases remain:

- CONTROL_2330=PASS
  - TPE:2330
  - announcement date 2026-06-10
  - primary effective date 2026-06-11
  - reason CA_EX_DIVIDEND
  - canonical identity and lineage verified
- CONTROL_6806=PASS
  - TPE:6806
  - primary effective date 2026-06-23
  - reason CA_LISTING_TERMINATION
  - canonical lifecycle evidence verified
- SEMANTIC_FIXTURE_6=PASS

New focused tests cover:

- bounded TPEx requirement serialization;
- TPEx parser to TWO identity;
- effective-date scope;
- missing/invalid effective date fail-closed;
- duplicate semantic event rejection;
- manifest/checkpoint/hash/empty semantics;
- deterministic content hash;
- current TPEx PARTIAL coverage and unrepresented-family UNKNOWN states;
- freeze refusal when TWSE is PARTIAL even if TPEx is hypothetically COMPLETE;
- existing 2330/6806 behavior;
- no OHLCV or trading-decision path.
- read-only CSV decoding, ROC-date conversion, leading-zero and Excel-code cleanup;
- TWSE combined 權息 semantic-partial preservation;
- TPEx explicit cash/stock/capital-increase component splitting;
- canonical 507 mapping and OUTSIDE_CANONICAL_507 audit retention;
- owner envelope hash, manifest, checkpoint, and same-semantic replacement merge.

Validation result:

- focused pytest: 20 passed;
- Ruff: passed;
- compileall: passed.

Actual owner-artifact validation also passed: raw SHA-256 checks, TWSE copy equivalence after CP950/UTF-8-BOM decoding, TPEx envelope parser validation, merged dataset loader validation, duplicate check, normalized hash/checkpoint generation, and freeze-gate refusal.

G1=PRESERVED_PASS
G2=PRESERVED_PASS
G3=PRESERVED_PASS
POST_CLOSE_CANARY=PRESERVED_PASS

## 20. Dataset Implementation Authorization Gate

The previous implementation authorization gate is recorded as follows:

| Gate | Decision | Evidence |
| --- | --- | --- |
| Owner internal research approval | YES | Owner decision record |
| At least one compliant source path | YES | TWSE reduced semantic control path; TPEx bounded manual path |
| Historical window coverage | NO for full closure | TWSE PARTIAL_IMPROVED_NOT_COMPLETE; TPEx PARTIAL_NOT_COMPLETE; method gaps remain |
| Deterministic effective-date semantics | YES for imported families; PARTIAL for TWSE combined rows | Parser requires primary effective date; TPEx component fields support explicit split |
| Identity/lifecycle alignment | YES for imported canonical rows | TPE 224/314 export identities plus 6806 lifecycle; TWO 128/193; outside rows audited |
| Lineage/hash/replay | PASS for normalized owner rows | Raw file hashes, source row positions, manifests, checkpoints, and semantic hashes |
| No public raw reproduction required | YES | Research-only reduced artifact boundary |

The dataset implementation was authorized and the owner exports were normalized/imported in this resumed task, but this task does not authorize protocol freeze. The remaining closure blocker is full 507-identity and full event-family coverage, including the bounded method gaps listed in Section 21. It is not Owner approval and it is not absence of a TPEx artifact.

## 21. Freeze Gate

REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO

REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO

The code-level freeze gate refuses authorization when any primary event-family coverage cell is not COMPLETE, when covered identities are below the current 507 universe, when complete empty-set validation is absent, when controls fail, or when dataset validation errors exist. Current validation is clean, but the gate returns unauthorized because primary cells remain PARTIAL/UNKNOWN, covered identities are 353 of 507, and complete empty-set validation is not established for method-gap families.

This means the validated TPEx artifact improves coverage but cannot by itself bypass the current TWSE PARTIAL state or the unrepresented-family UNKNOWN states. Freeze requires the full canonical coverage and validation conditions to be satisfied in a later task.

## 22. Changes and Documentation Reconciliation

APPLICATION_CODE_CHANGED=YES_RESEARCH_ONLY_IMPORT_READINESS

Changed exact task paths:

- services/api/src/topicpilot_api/research/corporate_action_dataset.py
- services/api/tests/test_corporate_action_dataset.py
- reports/TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION/REC-A1-CA-EVENTS-V0.json
- docs/reports/TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE.md
- reports/TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE/owner-artifact/TWSE-OWNER-BOUNDED-EXPORT-ENVELOPE-V0.json
- reports/TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE/owner-artifact/TPEX-OWNER-BOUNDED-EXPORT-ENVELOPE-V0.json
- reports/TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE/owner-artifact/REC-A1-OWNER-EXPORT-IMPORT-V0.json
- reports/TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE/owner-artifact/REC-A1-OWNER-EXPORT-OUTSIDE-CANONICAL-507-AUDIT-V0.json

The code change is limited to bounded CSV requirements, read-only local parsing/normalization, canonical 507 mapping, outside audit retention, coverage-matrix computation, dataset merge, and freeze-gate readiness. No production capability was enabled. The four derived JSON artifacts do not contain the raw CSV bytes.

Not changed or mutated:

- original Owner CSV files;
- database;
- historical OHLCV;
- recommendation engine;
- Today, Topic Detail, Favorites, or Stock active workstream code;
- PROJECT_CONTEXT.md;
- docs/ROADMAP.md;
- docs/DAILY_PROGRESS.md;
- docs/WORK_ORDERS.md;
- Production APIs, frontend, scheduler, or deployment configuration.

DAILY_PROGRESS_UPDATED=NO
PROJECT_CONTEXT_UPDATED=NO
ROADMAP_UPDATED=NO
WORK_ORDERS_UPDATED=NO
DATABASE_MUTATION=NO
HISTORICAL_OHLCV_CHANGED=NO
RECOMMENDATION_ENGINE_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO

## 23. Pre-Resume Handoff Snapshot

This section records the closed waiting state before the Owner supplied the exports. Section 24 is the current handoff and supersedes these values.

TASK_ID=TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE
FINAL_STATUS=WAITING_OWNER_TPEX_BOUNDED_ARTIFACT
OWNER_APPROVAL_STATUS=APPROVED_INTERNAL_RESEARCH_ONLY
TPEX_ARTIFACT_PRESENT=NO
TPEX_ARTIFACT_SOURCE=NONE_PROVIDED_OWNER_ARTIFACT_REQUIRED
TPEX_ARTIFACT_FORMAT=JSON_OBJECT_OR_JSON_ARRAY_OR_CSV_UTF8_OR_CSV_UTF8_BOM
TPEX_ARTIFACT_QUERY_WINDOW=2026-02-02_TO_2026-08-13
TPEX_ARTIFACT_EVENT_SCOPE=PRIMARY_AND_SEMANTIC_PARTIAL_FAMILIES_EXPLICIT
ARTIFACT_REQUIREMENTS_READY=YES
OWNER_ARTIFACT_REQUEST_REQUIRED=YES
TWSE_SOURCE_METHOD_STATUS=PARTIAL_CANONICAL_REDUCED_ROWS_ONLY
TPEX_SOURCE_METHOD_STATUS=MANUAL_OR_BOUNDED_QUERY_ONLY_ARTIFACT_REQUIRED
AUTOMATED_EXTRACTION_STATUS_TWSE=NOT_AUTHORIZED_BY_DEFAULT_SOURCE_METHOD_REVIEW
AUTOMATED_EXTRACTION_STATUS_TPEX=BLOCKED
MANUAL_BOUNDED_INGESTION_STATUS=OWNER_ARTIFACT_REQUIRED
LOCAL_RESEARCH_STORAGE_STATUS=ALLOWED_ONLY_WITHIN_SOURCE_TERMS
HASH_LINEAGE_REPLAY_STATUS=READY_FOR_BOUNDED_ARTIFACT
RAW_REPRODUCTION_STATUS=NOT_APPROVED
PUBLIC_REDISTRIBUTION_STATUS=NOT_APPROVED
COVERED_EVENT_FAMILIES=PRIMARY_AND_SEMANTIC_PARTIAL_EXPLICIT
HISTORICAL_WINDOW_COVERAGE=PARTIAL_WITH_TPEX_UNKNOWN
EVENT_DATE_SEMANTICS=DETERMINISTIC_EFFECTIVE_DATE_REQUIRED
PIT_SEMANTICS=TRADING_DECISION_USE_FORBIDDEN_POST_HOC_EXCLUSION_ALLOWED
IDENTITY_MAPPING_STATE=READY_FOR_OWNER_ARTIFACT_VALIDATION
REFERENCE_PRICE_AUTHORITY=OFFICIAL_SOURCE_FIELD_ONLY
CONTROL_CASES=2330_PASS;6806_PASS;SEMANTIC_FIXTURE_6_PASS
UNKNOWN_FAIL_CLOSED=YES
EVENT_EXCLUDED_RAW_POLICY=READY
TRADING_DECISION_USE=FORBIDDEN
POST_HOC_OUTCOME_INTEGRITY_EXCLUSION=ALLOWED
DATASET_IMPLEMENTATION_AUTHORIZED=YES
AUTHORIZED_INGESTION_MODE=MANUAL_OR_BOUNDED_OFFICIAL_RESEARCH_V0
NEXT_RECOMMENDED_TASK=OWNER_PROVIDE_TPEX_BOUNDED_ARTIFACT_AND_RESUME_CLOSURE
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO_UNTIL_DATASET_IMPLEMENTED_AND_VALIDATED
REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO
REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
APPLICATION_CODE_CHANGED=YES_RESEARCH_ONLY_READINESS
DATABASE_MUTATION=NO
HISTORICAL_OHLCV_CHANGED=NO
ADJUSTED_OHLC_CREATED=NO
TOTAL_RETURN_CREATED=NO
RECOMMENDATION_ENGINE_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
G1=PRESERVED_PASS
G2=PRESERVED_PASS
G3=PRESERVED_PASS
POST_CLOSE_CANARY=PRESERVED_PASS

## 24. Resume Final Handoff

TASK_ID=TASK-REC-A1-CORPORATE-ACTION-TPEX-BOUNDED-ARTIFACT-COVERAGE-CLOSURE
RESUME=YES
RESUME_HANDOFF_TASK_ID=TASK-REC-A1-CORPORATE-ACTION-OWNER-EXPORT-RESUME-HANDOFF
FINAL_STATUS=RAW_BOUNDED_EXPORTS_VALIDATED_ENVELOPE_NORMALIZATION_REQUIRED
OWNER_APPROVAL_STATUS=APPROVED_INTERNAL_RESEARCH_ONLY
OWNER_DECISION=APPROVED_INTERNAL_RESEARCH_ONLY
SOURCE_AUTHORITY_REAUDIT=NO_PRIOR_CLOSURE_REUSED
RAW_ORIGINALS=READ_ONLY

CANONICAL_PRE_SHA=454a558bbc10f53576c652ff11144dd39159dacf
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_USED=NO
WORKTREE_CREATED=NO
WORKTREE_REMOVED=NOT_APPLICABLE

TWSE_FILE=C:\Users\acer\Desktop\TWT49U (1).csv
TWSE_SHA256=ED65E408FCD6223E875549E8CB853139B1379A73682CFB18CCA92E2109C0B90A
TWSE_DOWNLOADS_FILE=C:\Users\acer\Downloads\TWT49U (1).csv
TWSE_DOWNLOADS_SHA256=68759F7CD5FBA85FF2149513E649D3A4DB2E7B95AF05503A21398ADCB855303F
TWSE_COPY_EQUIVALENCE=PASS_AFTER_ENCODING_NORMALIZATION
MNT_DATA_TWT49U_PRESENT=NO_UNDER_WINDOWS_MOUNT
TWSE_MARKET=TPE
TWSE_RAW_EVENT_ROWS=1035
TWSE_FOOTER_ROWS=11
TWSE_CANONICAL_ROWS=233
TWSE_CANONICAL_IDENTITIES=224
TWSE_OUTSIDE_ROWS=802
TWSE_OUTSIDE_IDENTITIES=632
TWSE_NORMALIZED_EVENTS=233
TWSE_DATASET_ROWS=234
TWSE_DATASET_IDENTITIES=225
TWSE_COVERAGE=PARTIAL_IMPROVED_NOT_COMPLETE

TPEX_FILE=C:\Users\acer\Desktop\Exright_1150202_1150813.csv
TPEX_SHA256=566F4ACE3E8FED9E0D89C60D0F2471308B38A00C085A97E151E57BBBAC4DF316
TPEX_MARKET=TWO
TPEX_RAW_EVENT_ROWS=853
TPEX_FOOTER_ROWS=1
TPEX_CANONICAL_ROWS=131
TPEX_CANONICAL_IDENTITIES=128
TPEX_OUTSIDE_ROWS=722
TPEX_OUTSIDE_IDENTITIES=493
TPEX_NORMALIZED_EVENTS=138
TPEX_COVERAGE=PARTIAL_NOT_COMPLETE
TPEX_ARTIFACT_PRESENT=YES
TPEX_ARTIFACT_SOURCE=OWNER_PROVIDED_OFFICIAL_BOUNDED_CSV
TPEX_ENVELOPE_NORMALIZED=YES
TPEX_OUTSIDE_AUDIT_RETAINED=YES
TPEX_ARTIFACT_FORMAT=CSV_UTF8_BOM_TO_NORMALIZED_JSON_ENVELOPE
TPEX_ARTIFACT_QUERY_WINDOW=2026-02-02_TO_2026-08-13
TPEX_ARTIFACT_EVENT_SCOPE=PRIMARY_AND_SEMANTIC_PARTIAL_FAMILIES_EXPLICIT

QUERY_WINDOW_START=2026-02-02
QUERY_WINDOW_END=2026-08-13
REFERENCE_VERSION=tw-reference-v1
UNIVERSE_POLICY=LIFECYCLE_GATED_507
CANONICAL_UNIVERSE_TPE=314
CANONICAL_UNIVERSE_TWO=193
CANONICAL_UNIVERSE_TOTAL=507
CANONICAL_INSTRUMENT_TYPE=EQUITY
OUTSIDE_CLASSIFICATION=EXACT_MARKET_CODE_AND_INSTRUMENT_LOOKUP_ONLY_NO_SUFFIX_HEURISTIC
ACCESS_METHOD=MANUAL_OR_BOUNDED_QUERY_ONLY
ARTIFACT_REQUIREMENTS_READY=YES
OWNER_ARTIFACT_REQUEST_REQUIRED=NO_CURRENT_ARTIFACT_PRESENT
MANUAL_BOUNDED_INGESTION=VALIDATED_OWNER_EXPORT
AUTOMATED_EXTRACTION_STATUS_TWSE=NOT_AUTHORIZED_BY_DEFAULT_SOURCE_METHOD_REVIEW
AUTOMATED_EXTRACTION_STATUS_TPEX=BLOCKED
TWSE_SOURCE_METHOD_STATUS=TWSE_TWT49U_MANUAL_BOUNDED_VALIDATED_PARTIAL
TPEX_SOURCE_METHOD_STATUS=MANUAL_OR_BOUNDED_QUERY_ONLY_VALIDATED
LOCAL_RESEARCH_STORAGE_STATUS=DERIVED_NORMALIZED_ONLY_RAW_EXTERNAL_READ_ONLY
HASH_LINEAGE_REPLAY_STATUS=PASS_BOUNDED_IMPORT
RAW_REPRODUCTION_STATUS=NOT_APPROVED
PUBLIC_REDISTRIBUTION_STATUS=NOT_APPROVED

DATASET_VERSION=REC-A1-CA-EVENTS-V0
DATASET_ROWS=372
TWSE_ROWS=234
TPEX_ROWS=138
COVERED_IDENTITIES=353
COVERED_EVENTS=372
UNKNOWN_ROWS=0
DUPLICATES=0
INVALID_IDENTITIES=0
INVALID_EFFECTIVE_DATES=0
MISSING_LINEAGE=0
SEMANTIC_HASH_COLLISIONS=0
MANIFEST_IMPLEMENTED=YES
CHECKPOINT_IMPLEMENTED=YES
IDEMPOTENT=PASS
HASH_LINEAGE_COMPLETE=YES_FOR_NORMALIZED_OWNER_ROWS
PASS_NO_EVENT_CONTRACT=IMPLEMENTED_AND_TESTED
COMPLETE_EMPTY_SET_VALIDATED=NO_FOR_UNREPRESENTED_EVENT_FAMILIES
UNKNOWN_FAIL_CLOSED=YES

COVERED_EVENT_FAMILIES=CASH_DIVIDEND;STOCK_DIVIDEND;RIGHTS_ISSUE_REFERENCE_RESET;TWSE_COMBINED_SEMANTIC_PARTIAL
EVENT_DATE_SEMANTICS=ROC_DATE_NORMALIZED_TO_ISO_EFFECTIVE_DATE
PIT_SEMANTICS=TRADING_DECISION_USE_FORBIDDEN_POST_HOC_EXCLUSION_ALLOWED
IDENTITY_MAPPING_STATE=CANONICAL_507_MATCHED_OUTSIDE_ROWS_AUDITED
REFERENCE_PRICE_AUTHORITY=OFFICIAL_EXPORTED_REFERENCE_FIELD_ONLY
CONTROL_CASES=2330_PASS;6806_PASS;SEMANTIC_FIXTURE_6_PASS
EVENT_EXCLUDED_RAW_POLICY=READY
TRADING_DECISION_USE=FORBIDDEN
POST_HOC_OUTCOME_INTEGRITY_EXCLUSION=ALLOWED

DATASET_IMPLEMENTATION_AUTHORIZED=YES
AUTHORIZED_INGESTION_MODE=MANUAL_OR_BOUNDED_OFFICIAL_RESEARCH_V0
OVERALL_RESEARCH_WINDOW_COVERAGE=PARTIAL_WITH_METHOD_GAPS
NEXT_RECOMMENDED_TASK=COMPLETE_RESEARCH_WINDOW_COVERAGE_AND_FREEZE_REASSESSMENT
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO_UNDER_CURRENT_FULL_COVERAGE_GATE
REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO

REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
PROJECT_CONTEXT_UPDATED=NO
ROADMAP_UPDATED=NO
WORK_ORDERS_UPDATED=NO
APPLICATION_CODE_CHANGED=YES_RESEARCH_ONLY_IMPORT_READINESS
DATABASE_MUTATION=NO
HISTORICAL_OHLCV_CHANGED=NO
ADJUSTED_OHLC_CREATED=NO
TOTAL_RETURN_CREATED=NO
RECOMMENDATION_ENGINE_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
G1=PRESERVED_PASS
G2=PRESERVED_PASS
G3=PRESERVED_PASS
POST_CLOSE_CANARY=PRESERVED_PASS

The resumed closure stops here. The Owner exports are validated and normalized, but Freeze and Core V0 walk-forward remain unauthorized until the full 507 identity/event-family coverage gate is satisfied.
