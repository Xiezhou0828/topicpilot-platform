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

## G2 previousClose authority alignment follow-up (2026-10-03)

This section records the later Owner-approved implementation phase. Earlier sections and
the three original JSON artifacts remain historical evidence for candidate `5247393`;
their strict row-only G2 verdict and latest-earlier-price comparator description are not
the policy of this follow-up. No earlier Production evidence is reinterpreted as a new
readback or authorization.

TASK_TYPE=implementation
REQUIRED_TERMINAL_STATE=VALIDATED (Owner explicitly stops before canonical review)
TASK_ID=TASK-20261002-TARGET-UNIVERSE-REPLAY-AND-READINESS-GATE-RESOLUTION
AUTHORITY_BOUNDARY=Owner-approved G2 comparator/status coverage; local candidate only
CANONICAL_SHA=3f2d4761c665931708517f0501c57f2be257b641 (provided baseline, not live readback)
SOURCE_SHA=524739323befc2c3abcb0b48dbbc42b7ff54daf1 (verified clean starting candidate)
MIGRATION_HEAD=0048_task_checkpoint_provider_metric_applicability
SEMANTICS_CHANGED=G2 comparator and coverage only; no Topic/Score/Grade/Lifecycle policy change
PRODUCTION_DEPENDENCY=NOT_EXECUTED
FOLLOW_UP_REQUIRED=YES
FOLLOW_UP_REASON=Owner canonical review/integration and separately authorized runtime/data verification
WORKTREE_STATUS=ACTIVE; same existing branch; no second branch or PR
FILES_CHANGED=11 (5 backend source, 1 audit script, 4 test files, this report)
CANONICAL_RECONCILIATION_DISPOSITION=READY_FOR_CANONICAL_RECONCILIATION

### Decisions and affected paths

- `previous_close_authority.py`: typed comparator proof, positive finite numeric validation,
  exact instrument/market/code/date identity, official source, authority, and nonempty lineage.
  Provider evidence additionally binds target payload date and the same response hash.
  Comparator values are excluded from public diagnostic metadata. No global hash change.
- `provider_preflight.py`: G2 requires a target-date official positive close plus an accepted
  comparator for each priced target. Context now carries persisted instrument IDs and the
  previous session resolved using the existing governed TW_MARKET weekday/holiday/suspension
  calendar. Row presence alone cannot PASS. Price/status/comparator coverage are separate counts.
  Authority/version/date/transport/empty-payload failures still fail closed.
- `market_data/history.py` and `market_data/exchange.py`: additive optional `previous_close`
  in provider-neutral bars. Only explicitly named comparator fields (`previousClose`,
  `前收盤價`, `前一交易日收盤價`) are recognized. No close-minus-change calculation, inferred
  adjustment, month fallback, authority-version change, or additional request/retry behavior.
  This support does not assert that the retained production payloads contain such a field.
- `daily_market.py`: the comparator SELECT uses the exact previous governed session, same
  instrument, correct official market source, ACCEPTED quality, positive close and canonical
  observation lineage. It works independently of whether a target-date canonical price already
  exists. Missing prior-session data remains null; Sep30 cannot substitute for Oct1 on Oct2.
  The separate last-valid-price disclosure remains historical context, never a comparator fill.
- `replay_target_universe_readiness.py`: offline G2 uses typed proofs and existing status
  resolution. Prior-price presence booleans/dates alone never become invented numeric proofs.
  Stage 12 now reports accepted comparator proofs, not merely earlier source presence.

2601 still uses the unchanged corporate-action catalogue and TASK-024 resolver. Its existing
TWSE official reduction authority resolves SUSPENDED / LEGITIMATE_UNAVAILABLE. Only a resolved,
nonblocking, date-effective official/lifecycle status with lineage, keyed to the expected
instrument ID, can account for a missing price; it is never counted as a price/comparator row.
UNKNOWN, MISSING_MARKET_DATA, provider failure, expired authority and ungoverned/manual inputs
remain blocking. No run, recovery key, checkpoint, publication writer or formula was changed.

### Acceptance matrix and evidence boundary

| State | G2 result / evidence |
| --- | --- |
| Target official close + explicit valid provider comparator | PASS; prior session date, target payload date, official source and matching response hash retained |
| Target official close + same-instrument exact prior-session ACCEPTED official close | PASS; canonical observation lineage retained |
| Prior close missing, zero, null, empty or nonfinite | FAIL; no fabricated comparator |
| Wrong instrument, market, code, prior date, authority, quality or lineage | FAIL |
| Invalid explicit numeric comparator despite valid alternate history | FAIL; invalid explicit evidence is not hidden by fallback |
| Missing current close without formal no-trade authority | FAIL; history cannot replace current close |
| Existing official 2601 suspension, no price | STATUS accounted; no synthetic price; no comparator required |
| TPE 346 prices + 1 legitimate unavailable, TWO 206 prices, valid comparator proofs | Synthetic unit/parser fixture PASS; 552 priced + 1 status = 553 accounted |
| Retained real target payloads / identities but no Oct1 numeric authority/lineage proofs | Both G2 markets FAIL; PREVIOUS_CLOSE_AUTHORITY_NOT_READY |
| Weekend or Monday before new completed canonical session/publication | Existing Home read-model fixture selects Oct2 publication, not comparator date |
| Monday completed session with its completed Home envelope | Existing read-model fixture selects Monday; no publication is created by a read or comparator |

The retained Oct2 payload replay still accepts 346 TPE and 206 TWO price candidates; 2601
accounts for the remaining TPE status target. All 553 persisted identities are accounted for.
However, accepted comparator proof coverage is 0/346 and 0/206 with the preserved evidence.
The old readback has Sep30 closes (Sep22 for 2601), not the required Oct1 authority/lineage.
That proves an evidence gap, not the latest state of Production. No new provider HTTP request
or Production DB query was performed in this follow-up. Missing numeric proofs were not
filled using those date/presence flags. Both markets correctly remain FAIL, not readiness PASS.

Full per-instrument diagnostic replay remains private in the task-local diagnostic directory;
it is not part of this follow-up commit. No raw quote payload, price series, signed URL or
credentials were added. Replay output SHA256:
`5f04f68891e72d9390dfa6213acf3dc6b216b660c7fc2da27ab8d3e623dd3e35`.
Source SHA256 bindings in that output include:

- G2: `3f84dc2906b639cc1e2e5ab790f10aa46a55a3ae7ff246c0bf3d88899e38a4e0`
- Comparator: `f2a8eb938d6097b2a1781522df1f762435e59527de4ef2c8dca92ece6c9d28e7`
- Daily SELECT: `45be9028c41a66d987b457b4d2f98f22a8e3729ccbf13e8c4c6fcf1f0ae534c9`

### Validation and baseline attribution

Same task-local declared Python environment; isolated exact `5247393` baseline archive.
Tests run from repository root with explicit source paths. All database test URLs cleared.

- Baseline full backend: 1071 passed, 60 skipped.
- Follow-up full backend: 1117 passed, 60 skipped; +46 cases, zero new failures.
- Focused G2/provider/status/daily-market/Home/post-close: 170 passed, 1 skipped.
- New tests cover explicit provider/previous formal close, wrong identity/date/hash, missing
  comparator, zero/null/empty/nonfinite, unavailable status accounting, real bundle target
  counts with synthetic prices, runtime wiring before current ingestion, SELECT guard,
  unchanged weekend/Monday completed-publication date selection, and no price fill.
- Changed-scope Ruff PASS. Full-repository Ruff remains existing debt: 856 raw / 843 unique
  findings on baseline and follow-up, 843 unchanged, zero new and zero resolved. Not fixed.
- Compile PASS; OpenAPI drift PASS; generated client unchanged and client tests 4 passed.
- Migration graph: one unchanged head 0048, 49 revisions. No schema/migration changes or
  migration execution. Database-backed tests were skipped, not claimed PASS; SQL guard/runtime
  wiring tests are unit tests, not a persisted database or frontend E2E acceptance claim.
- Diff check PASS. Home reader/writer, frontend, corporate-action/status policies, post-close
  orchestration, migration graph and generated contracts unchanged from starting candidate.

Corrected diagnostic invocations: initial focus list referenced two nonexistent separate
post-close test filenames; collection stopped without tests. The existing combined contract
test file was used for the accepted focused result. A PowerShell hash invocation needed an
explicit path-array parameter; the corrected hashes above were read successfully. These are
invocation errors, not candidate regressions. An empty local disposable PostgreSQL container
was briefly initialized and removed with its own transient volume after exact ID/label
verification; no application schema, migration or database test was run against it.
The later raw Ruff-count summary also needed explicit UTF-8 decoding on Windows; the
attribution gate itself already used UTF-8 and was unaffected.

### Follow-up disposition

ACHIEVED_TERMINAL_STATE=VALIDATED
TASK_STATUS=CANDIDATE_COMMIT_READY
G2_POLICY=TARGET_OFFICIAL_CLOSE_AND_EXACT_PRIOR_FORMAL_COMPARATOR_OR_EXPLICIT_PROVIDER_PROOF
PREVIOUS_CLOSE_AUTHORITY=OFFICIAL_ONLY
PREVIOUS_CLOSE_LINEAGE=REQUIRED_AND_INSTRUMENT_DATE_BOUND
TPE_G2_STATUS=FIXTURE_PASS; RETAINED_REAL_EVIDENCE_FAIL_PREVIOUS_CLOSE_AUTHORITY_NOT_READY
TWO_G2_STATUS=FIXTURE_PASS; RETAINED_REAL_EVIDENCE_FAIL_PREVIOUS_CLOSE_AUTHORITY_NOT_READY
2601_STATUS=SUSPENDED / LEGITIMATE_UNAVAILABLE; UNCHANGED_AUTHORITY
TARGET_COVERAGE=552_PRICE_PLUS_1_UNAVAILABLE_EQUALS_553_ACCOUNTED; NOT_553_PRICES
HOME_DATE_SEMANTICS=UNCHANGED; COMPARATOR_DATE_NOT_HOME_DATE
WEEKEND_BEHAVIOR=READ_MODEL_FIXTURE_PASS
MONDAY_PRE_CLOSE_BEHAVIOR=READ_MODEL_FIXTURE_PASS
MONDAY_POST_CLOSE_BEHAVIOR=COMPLETED_MONDAY_PUBLICATION_READ_MODEL_FIXTURE_PASS
MIGRATION_REQUIRED=NO
PRODUCTION_DEPLOYED=NO
PRODUCTION_DB_MUTATED=NO
RECOVERY_EXECUTED=NO
POST_CLOSE_EXECUTED=NO
RUN_2284_TOUCHED=NO
UNAUTHORIZED_RETRY=NO
HISTORICAL_REPLAY=NO (offline parser/normalizer replay only, no historical run)
MANUAL_SQL=NO
PUSH=NO
CANONICAL_MERGE=NO
PR_CREATED=NO
NEXT_TASK_CHANGED=NO
TASK_COMPLETE=YES_FOR_IMPLEMENTATION_SCOPE_ONLY
NEXT_STEP=Owner canonical review and integration
