# TASK-20261002 target universe replay and readiness gate resolution

TASK_TYPE=implementation (bounded provider-status provenance fix after read-only proof)
REQUIRED_TERMINAL_STATE=VALIDATED
TASK_STATUS=CANDIDATE_VALIDATED
FOLLOW_UP_REQUIRED=YES
FOLLOW_UP_AUTHORITY=Owner

## Outcome and limits

The same retained official target-date payloads, replayed against the actual 553 persisted
Production identities, prove **552 accepted price candidates + 1 independently evidenced
official suspension**. The canonical baseline rejects 2601 at status resolution after an
internally generated UNKNOWN is treated as a higher-precedence exchange status. The bounded
candidate preserves that diagnostic's origin and allows the unchanged corporate-action
authority to be reached. No price is created for 2601.

This is a local parser/classifier/mapper/status/coverage-model result, **not a persisted
canonical observation or formal publication**. Stage 15 is NOT_EXECUTED, not a zero-success
checkpoint. Stage 16 is a pure coverage model, not the entire formal market-facts,
institutional-flow, Topic, or Home gate. Production readiness and new-run authorization
remain NOT_PROVEN. The old failed run's historical raw response was not recovered in this
task; later successful payloads do not prove why its earlier requests failed.

## Exact lineage and scope

Canonical base and remote main verified: `3f2d4761c665931708517f0501c57f2be257b641`.
Worktree: `E:\TopicPilot\worktrees\TASK-20261002-TARGET-UNIVERSE-REPLAY-AND-READINESS-GATE-RESOLUTION`.
Branch: `codex/task-20261002-target-universe-replay-readiness`. Initial worktree was clean.
The local candidate commit and parent are verified in the final handoff. No push, PR, merge,
or deploy was performed. Candidates `22e668b9...` and `ec4edae...` were not imported or used
as runtime dependencies. No C-drive owner checkout operation was performed.

Changed runtime paths (only provider-status classification/provenance):

- `market_data/history.py`: typed optional `status_authority_origin` and exact tag predicate.
- `market_data/ingestion.py`: tag internally generated price-gap UNKNOWN; carry the tag in
  payloads; preserve genuine explicit UNKNOWN and idempotent classification.
- `normalizer/historical.py`: validate the origin and retain it in existing status JSON;
  null OHLC stays INCOMPLETE. Malformed origins or non-UNKNOWN origin tags are rejected.
- `daily_market.py`: project existing `status_context` and distinguish tagged diagnostics
  from official status events before calling the unchanged authority resolver.
- `trading_status_authority.py`: the same distinction at daily-result and operator-read
  boundaries. Authority priority, status vocabulary, and corporate-action policy unchanged.

Added offline audit script, two test files, this report, and three price-free evidence files.
No exchange parser, readiness retries, POST_CLOSE orchestration, schema, migration, frontend,
API contract, generated client, Topic formula, Score, Grade, Strength, Lifecycle formula,
Opportunity, or corporate-action catalogue was changed.

## Canonical universe and protected evidence

[Protected readback](TASK-20261002-TARGET-UNIVERSE-REPLAY-AND-READINESS-GATE-RESOLUTION/protected-readback-price-free.json)
was obtained through existing canonical `load_g2_preflight_context`, `read_daily_market_rows`,
and `build_unavailable_instruments` in the protected Worker shell. The database transaction
used PostgreSQL read-only, repeatable-read, autoflush=False, closed without commit.
No hand-written SQL or mutation entrypoint was executed. Worker revision readback was READY,
exact SHA `3f2d4761c665931708517f0501c57f2be257b641`; API SHA was not newly verified in this task.

Reference version: `tw-reference-v1-rollover-0578862f98914eb7`, reference READY, target date
2026-10-02 is an eligible session. Physical registry count 555 is **not** missing-data count.
Date-effective targets: TPE 347 + TWO 206 = 553. All 553 persisted IDs were resolved; no
missing or duplicate identities. Lifecycle selection and eligibility came from the canonical
loader, not a hard-coded stock list. The target matrix records each actual instrument ID,
eligibility, effective lifecycle, provider identity, parser match, price quality, and status.
Null effective lifecycle means no overriding lifecycle event, not UNKNOWN trading status.

Identity digest (sorted market/code/persisted UUID, compact JSON):
`62cbfc31f3689d239b91acadf7d6c4620d74a94c281b2e7d01b2450546ae4da7`.
Offline bundle UUID derivation did not match persisted IDs and was not substituted. The
canonical bundle is used only for deterministic date-effective count tests, not live identity
proof. Real price payloads remain in ignored `work/`; committed evidence contains no prices,
raw response bodies, secrets, credentials, or signed artifact URLs.

## Fresh official payload and rejection matrix

Each endpoint received one fresh read-only probe, HTTP 200, no automatic retry. Dates both
`20261002`. TPE raw stat `OK`; TWO raw stat `ok`. TPE's `EXCHANGE_NOT_READY` error is an adapter
classification of a non-OK provider `stat`; it is not the raw stat value. The tested
contradictory fixture (non-OK stat with valid rows) remains fail-closed. No captured fresh
official payload exhibits that contradiction, so stat precedence was not relaxed.

| Evidence | TPE | TWO |
| --- | ---: | ---: |
| Official parsed rows | 1,380 | 11,928 |
| Non-null raw close | 1,373 | 6,443 |
| Null raw close | 7 | 5,485 |
| Date-effective targets | 347 | 206 |
| Target row matches | 346 | 206 |
| Target close extracted / price accepted | 346 | 206 |
| Target row absent | 1 (2601) | 0 |
| Matched target null close | 0 | 0 |
| Out-of-target rows | 1,034 | 11,722 |
| Out-of-target rows with close | 1,027 | 6,237 |
| Out-of-target null-close rows | 7 | 5,485 |
| Candidate legitimate unavailable | 1 (2601) | 0 |
| Candidate covered targets (pure model) | 347 | 206 |

The TWO difference 11,928 -> 6,443 is null provider close, not rows discarded by parsing.
All 206 target rows have valid close and OHLC. The 5,485 null-close rows are outside the
canonical target universe; no suspension/no-trade status is inferred for those securities.
Representative null-close codes are retained as metadata in the evidence. Neither target
mapping failure nor target post-parse zero coverage is reproduced by these payloads.

TPE source: `https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20261002&type=ALLBUT0999&response=json`.
Payload 247,435 bytes; SHA256 `cecf0d4e4ad34cf1c6068177ba5219afe88ec685e1c236f81ca5f56ea5d7a6ab`.
Adapter `twse-official-daily.v2`.

TWO source: `https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes?date=2026%2F10%2F02&response=json`.
Payload 1,796,554 bytes; SHA256 `1694fade3a2f98a433376b7a0410e5114aed2a4bf891bbc1036b142ba89888c1`.
Adapter `tpex-official-daily.v2`.

## Sixteen stages and baseline/candidate contrast

[Baseline matrix](TASK-20261002-TARGET-UNIVERSE-REPLAY-AND-READINESS-GATE-RESOLUTION/baseline-replay-price-free.json)
and [candidate matrix](TASK-20261002-TARGET-UNIVERSE-REPLAY-AND-READINESS-GATE-RESOLUTION/candidate-replay-price-free.json)
contain every stage's input/output/reject count, unit, reason, representative symbols,
endpoint, target/response date, response hash, adapter, and all 553 identities. The same
identity digest and payload hashes are used in both replays. Imported implementation source
hashes identify baseline versus candidate independently of the audit wrapper.

| Stage | Result / important distinction |
| --- | --- |
| 1-3 request/response/HTTP | Recorded single HTTP 200 probes, not additional replay requests |
| 4-7 bytes/JSON/date/date-match | Both payloads valid, non-empty, exact target date |
| 8-9 raw extraction/code normalization | TPE 1,380; TWO 11,928; no raw row rejected |
| 10 target match | 346 / 206; out-of-target rows counted separately from absent 2601 |
| 11 close extraction | 346 / 206; no matched target null close |
| 12 previousClose | Prior canonical source presence only, not extracted current-row previousClose |
| 13 price validation / mapper | 346 / 206 accepted PRICE candidates; 2601 INCOMPLETE, null |
| 14 status/lifecycle | Baseline 346 / 206; candidate 347 / 206 with evidenced suspension |
| 15 canonical observation creation | NOT_EXECUTED; output/rejected counts null, not fabricated zero |
| 16 formal market readiness | Pure daily-coverage model only; baseline TPE fails, candidate passes |

Exact reproducible root cause:

`missing 2601 provider row -> active no-price classifier -> UNKNOWN/status_explicit=True ->`
`normalizer ACCEPTED trading-status family with official daily source ->`
`read model creates OFFICIAL_EXCHANGE authority (priority 3) ->`
`approved CORPORATE_ACTION SUSPENDED (priority 2) masked ->`
`UNKNOWN / AMBIGUOUS_OR_UNSUPPORTED_AUTHORITY -> formal coverage blocked`.

The new marker `INTERNAL_MISSING_PRICE_CLASSIFICATION` distinguishes only that internal
diagnostic. It never grants eligibility by itself. Without independent date-effective
authority, the target remains MISSING_MARKET_DATA / blocking. Genuine explicit UNKNOWN,
ambiguous authority, malformed tags, untagged legacy UNKNOWN, provider/date/price failures
remain fail-closed. No existing observations are relabelled. The marker uses existing raw
payload and `canonical_trading_status_observations.status_context` JSON, requiring no migration.

The strict G2 provider-row gate **still fails** TPE with PARTIAL_PROVIDER_COVERAGE/2601;
TWO passes. This gate is provider-row coverage, not formal price-or-status coverage. POST_CLOSE
loads G2's reference/universe context but does not call `run_provider_preflight` or
`evaluate_provider_preflight`. No decision to change G2's contract is hidden in this candidate.

## previousClose / formal-history boundary

Readback has zero 10/2 current canonical close rows and zero current-row previousClose on both
markets. Existing prior canonical closes are present for all 553 targets: 552 dated 9/30,
2601 dated 9/22. The canonical read model obtains previousClose from the latest earlier
non-null formal observation after a current-day observation exists; it is not a field in
the daily provider-neutral bar. This task proves only that prior source presence, not its
numeric extraction into 10/2 readback, nor 10/1 formal continuity. Nothing is copied into a
current close; no zero/forward-fill or synthetic history is generated. Literally complete
553 target close/previousClose and Production publication cannot be claimed.

## Acceptance matrix

| Input / state | Expected candidate decision |
| --- | --- |
| Valid date, mapped target, complete valid OHLC | PRICE accepted; pure coverage eligible |
| Valid daily payload, absent 2601 + existing official date-effective action | Null price; SUSPENDED / LEGITIMATE_UNAVAILABLE |
| Internal gap marker with no independent authority | MISSING_MARKET_DATA; blocking |
| Genuine explicit UNKNOWN or untagged legacy UNKNOWN | UNKNOWN; blocking, even with lower-priority action |
| Invalid / inappropriate origin marker | Normalizer rejects; no price/status exemption |
| Empty/zero rows, non-OK stat, date mismatch, invalid prices | Canonical provider error; no normalization/retry |
| Raw extra row or raw null close outside targets | Evidence only; not 555 missing targets or inferred no-trade |
| Prior close absent or not earlier than target | Comparator source incomplete; no fabricated previousClose |
| Local coverage model PASS without persistence | Not formal publication; no recovery authorization |

## Validation and attribution

Fresh task-local Python 3.12 environment installed from declared backend dev dependencies.
Exact base archived locally on E and tested with identical interpreter/dependencies and
repository-root invocation. All test database environment variables cleared; 60 optional
database tests skipped, not passed. No Production URL used by tests.

- Baseline full backend: 1032 passed, 60 skipped.
- Candidate full backend: 1071 passed, 60 skipped; delta +39 tests, no new failure.
- Focused provider/no-trade/daily-market/status/post-close: 152 passed, 1 skipped.
- Changed-file Ruff PASS. Full tracked-Python roots: 843 unique findings / 856 raw findings
  on both base and candidate; 843 unchanged, zero new, zero resolved. Existing debt not fixed.
- Compile PASS; OpenAPI baseline and candidate PASS (same committed schema).
- Generated-client regeneration/check PASS, unchanged; client tests 4 passed.
- Migration graph single head `0048_task_checkpoint_provider_metric_applicability`, 49 revisions;
  migration files unchanged and no migration executed.
- Diff check PASS; no forbidden-scope changes.

Diagnostic invocations were corrected before acceptance: an API-subdirectory test invocation
caused five relative research-fixture path failures; root invocation passed on exact base.
An initial incomplete PYTHONPATH caused two import collection errors; it was corrected.
An attempted all-file Ruff argument list exceeded Windows command length, so both sides were
rerun against identical complete tracked Python roots (`services infra reports scripts tools`).
These are invocation errors, not attributed candidate or baseline code regressions. npm's
installation advisory reported four high-severity dependency findings; no dependency upgrade
or unrelated audit fix was made or claimed.

## Owner handoff and operations not performed

Owner must review/canonicalize the local candidate separately, decide whether the operational
provider gate intentionally remains strict row coverage or needs a separate bounded G2
alignment, and require exact-SHA/runtime and persisted previousClose/history readback before
any new history-run authorization. This task does not satisfy an authorization to run.
Do not reuse `3cf3e56f-494f-5db6-a32f-310685e0c2ce`, run 2284, or the old 10/1 failed run.

PRODUCTION_DB_MUTATED=NO
PRODUCTION_DEPLOYED=NO
MIGRATION_EXECUTED=NO
POST_CLOSE_EXECUTED=NO
RECOVERY_EXECUTED=NO
RETRY_EXECUTED=NO
RUN_2284_TOUCHED=NO
20261001_RUN_TOUCHED=NO
HISTORICAL_BACKFILL=NO
MANUAL_SQL=NO
SCHEDULER_ACTIVATED=NO
CANONICAL_MERGE=NO
PR_CREATED=NO
OWNER_DECISION_REQUIRED=YES
PRODUCTION_RECOVERY_PREREQUISITES=NOT_PROVEN
TASK_COMPLETE=YES (candidate implementation / analysis boundary only)
