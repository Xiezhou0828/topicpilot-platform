# TASK-REC-A1-CORPORATE-ACTION-EVENT-EXCLUSION-CLOSURE

**Review date:** `2026-08-15`
**Scope:** research-only corporate-action event authority, point-in-time semantics, and deterministic event exclusion for the future REC-A1 Core V0 dataset freeze.

## Executive Decision

This closure establishes the minimum `EVENT_EXCLUDED_RAW_V0` contract and
confirms that the future research harness can separate trading-decision facts
from post-hoc outcome-integrity exclusions. It does **not** establish an
approved, batch-ingestable corporate-action dataset.

The exchange pages and formal terms establish source existence and several
field meanings, but the current repository still lacks a complete normalized
event history, point-in-time source snapshots, and owner approval for storing
or automating a new event dataset. The correct result is therefore a
contract-ready, source-authority-partial closure with ingestion blocked.

```text
TASK_ID=TASK-REC-A1-CORPORATE-ACTION-EVENT-EXCLUSION-CLOSURE
FINAL_STATUS=REC_A1_EVENT_AUTHORITY_PARTIAL_CONTRACT_READY_SOURCE_USE_APPROVAL_BLOCKED
CORPORATE_ACTION_EVENT_SOURCE_AUTHORITY=PARTIAL
HISTORICAL_EVENT_QUERY=PARTIAL
EVENT_DATE_SEMANTICS=PARTIAL
REFERENCE_PRICE_AUTHORITY=PARTIAL
EVENT_EXCLUDED_RAW_POLICY=READY
EVENT_EXCLUDED_RAW_POLICY_QUALIFIER=CONTRACT_ONLY_SOURCE_AUTHORITY_PARTIAL
CORPORATE_ACTION_DATASET_IMPLEMENTED=NO
UNKNOWN_EVENT_AUTHORITY_FAIL_CLOSED=YES
TRADING_DECISION_LOOKAHEAD=NO
POST_HOC_OUTCOME_EXCLUSION_AUTHORIZED=YES
POST_HOC_OUTCOME_EXCLUSION_QUALIFIER=CONTRACT_ONLY_NO_INGESTION_OR_RUN_AUTHORIZATION
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO
REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO
```

`POST_HOC_OUTCOME_EXCLUSION_AUTHORIZED=YES` is contract-only: a future
authorized event row may remove an affected episode from outcome evaluation.
It does not authorize source download, persistence, a run, a walk-forward, or
any production behavior.

## Canonical State

```text
CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
CANONICAL_PRE_SHA=88a4dcc897e986b0c5667f97cad27bb0f0131610
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
DIRTY_STATE=YES_PRE_EXISTING_USER_CHANGES_PRESERVED
WORKTREE_USED=NO
EXACT_TASK_WRITE_SET=docs/reports/TASK-REC-A1-CORPORATE-ACTION-EVENT-EXCLUSION-CLOSURE.md
```

The canonical worktree had pre-existing modified and untracked files,
including Topic Detail work. No reset, stash, blanket staging, cleanup, or
unrelated reconciliation was performed. The new report path did not collide
with the modified Topic Detail paths or the existing A/B/C report paths.

The local PostgreSQL instance was queried read-only. Its observed Historical
closure remains the approved fixed universe of 507 physical equity identities
and 63,826 OHLCV rows from `2026-02-02` through `2026-08-13`. The database is
still at Alembic `0017`, while repository migration head is `0029`; no
migration was run.

## Prior A/B/C Convergence

The three prerequisite audit reports were read as evidence and their current
conclusions are preserved:

| Prior audit | Reconciled conclusion | Boundary retained |
|---|---|---|
| Adjustment authority audit | Exchange adjustment/reference-price surfaces exist, but OHLC adjustment semantics and a persisted event authority remain unknown/partial. | Formal returns, MFE/MAE, expectancy, and affected episode claims remain blocked or preliminary until event authority is closed. |
| PIT universe / survivorship audit | `LIFECYCLE_GATED_507` is feasible for research-only use with explicit survivorship disclosure. | `SURVIVORSHIP_SAFE_CLAIM=NO`; a complete historical membership universe is not introduced here. |
| Research harness architecture audit | Existing deterministic replay, as-of boundaries, versioned policy, lineage/hash, and fail-closed patterns are reusable. | No new generic backtest framework, walk-forward, parameter search, or execution authorization is created here. |

The resulting policy input remains:

```text
UNIVERSE_POLICY_INPUT=LIFECYCLE_GATED_507
SURVIVORSHIP_DISCLOSURE_REQUIRED=YES
RS=OMITTED
TOPIC_CONTEXT=OMITTED
```

## Source Authority Audit

The audit separates five questions that must not be collapsed into one
`source exists` flag:

1. **Source existence:** an official exchange page, announcement, query, or
   formula surface exists.
2. **Field semantics:** the page identifies a date, security, event category,
   ratio, dividend, or reference-price field with a stable meaning.
3. **Historical availability:** the source can answer a historical date/code
   query and states its available period.
4. **Point-in-time availability:** the record preserves what was public by the
   signal date, including announcement/publication timing, rather than only a
   later corrected view.
5. **Use approval and reproduction:** current governance permits this project
   to retrieve, store, hash, replay, automate, and potentially expose the
   resulting artifact.

### Official TWSE evidence

- [TWSE Ex-right Announcement](https://www.twse.com.tw/en/announcement/ex-right/twt48u.html)
  exposes an official announcement surface and the stock-dividend and cash
  capital-increase ratio semantics.
- [TWSE Ex-right Price Data](https://www.twse.com.tw/en/announcement/ex-right/twt49u.html)
  states that the data is available since `2003-05-05` and defines the inputs
  for ex-right and ex-dividend reference-price calculations.
- [TWSE Reference Price for Capital Reduction](https://www.twse.com.tw/en/announcement/reduction/twtauu.html)
  states availability since `2011-01-01` and distinguishes cash refund, loss
  coverage, and capital-reduction/cash-injection formulas.
- [TWSE Change of Par Value Announcement](https://www.twse.com.tw/en/page/trading/exchange/TWTB7U.html)
  exposes the old/new par-value ratio semantics. A complete historical
  event-feed contract for the 507 research identities was not established.
- The [TWSE 2026-06-10 official notice](https://wwwc.twse.com.tw/staticFiles/news/news/tsecnews/8a8216d69e6379f4019eb0d0cfa601e0.pdf)
  identifies `2026-06-11` as the ex-dividend date for ten listed stocks,
  including `2330`, and directs users to the official Ex-right Announcement
  and Market Information System for related information.
- The [TWSE Data E-Shop product page](https://eshop.twse.com.tw/en/product/detail/000000006e0bbe8d016f1842c12f0342)
  describes a richer `T48` product with effective date, security code,
  pre-ex-right close, ex-dividend/ex-right fields, opening reference price,
  dividend, stock-dividend ratio, and cash-capital-increase fields. The page
  also labels internal/external use as subscription products with use
  restrictions; it is not evidence of an existing project subscription.

### Official TPEx evidence

- [TPEx Ex-rights/Ex-dividend Announcements](https://www.tpex.org.tw/en-us/announce/market/ex/announce.html)
  states historical availability since `2008-12-15`, exposes date/code
  queries, and warns that dividend and stock-dividend values are reference
  information whose actual issuer announcements take precedence.
- [TPEx Ex-rights/Ex-dividend Calculation Result Sheet](https://www.tpex.org.tw/en-us/announce/market/ex/cal.html)
  states availability since `2008-01-02` and defines opening-reference-price
  and tick-size semantics.
- [TPEx Reference Price for Capital Reduction](https://www.tpex.org.tw/en-us/announce/market/reduction/reference.html)
  states availability since `2013/01` and defines cash-refund, loss-coverage,
  and capital-reduction/cash-increase formulas.
- [TPEx capital-reduction announcements](https://www.tpex.org.tw/en-us/announce/market/reduction-tdr.html)
  provide a date/market/code-or-keyword query and state availability from
  `2015-12` for that announcement family.
- [TPEx market announcements](https://www.tpex.org.tw/en-us/service/pi/announce/market/retro.html)
  include capital reduction, merger, share transfer, acquisition, and
  demerger categories. This establishes source existence, not a normalized
  identity-continuity dataset.

### Terms and governance evidence

- [TPEx E-Data Shop subscription terms](https://eshop.tpex.org.tw/en/product/shoppingTerm)
  restrict internal-use products to internal users, require written consent
  for reproduction/transmission or derivatives, and separate external-use
  authorization from internal use.
- [TPEx E-Data Shop website terms](https://eshop.tpex.org.tw/en/useTerms/index)
  prohibit downloading software or data through automated devices, scripts,
  spiders, crawlers, or extraction other than approved methods or with TPEx
  consent.
- [TWSE Data E-Shop subscription terms](https://eshop.twse.com.tw/en/shopping/finishOrder/?show=true&showTIP=)
  state that TWSE products and databases are owned by TWSE, restrict internal
  products to internal use, require written consent for reproduction or
  transmission, and require approval for use in an index or derivative.
- [TWSE Regulations Governing the Use of Trading Information](https://www.twse.com.tw/downloads/en/products/regulation_use.pdf)
  and the [TWSE supply/use agreement](https://www.twse.com.tw/downloads/en/products/use_agreement.pdf)
  establish contract/approval boundaries for trading-information use and
  transmission.

These terms are recorded as governance evidence, not as a legal conclusion.
The current project authority does not show a TopicPilot subscription,
written consent, or owner approval that covers a new automated, persisted
corporate-action dataset. Therefore:

```text
SOURCE_USE_APPROVAL_STATUS=PENDING_OWNER_SOURCE_USE_APPROVAL
RESEARCH_ONLY_USE_STATUS=BLOCKED_PENDING_OWNER_SOURCE_USE_APPROVAL
RESEARCH_ONLY_AUTHORIZED=NO_CURRENT_EVIDENCE
AUTOMATED_BULK_INGESTION_STATUS=BLOCKED
AUTOMATED_BULK_INGESTION_APPROVAL=NOT_PROVEN
```

## Event Family Scope

Only events that can break the continuity or comparability of raw OHLC price,
resistance, moving averages, momentum, trigger, execution, or outcome labels
are in scope. Ordinary issuer news, routine shareholder-meeting notices, and
non-price corporate announcements are not automatically events for this
policy.

| Event family | A1 raw-price relevance | V0 treatment |
|---|---|---|
| Cash dividend / ex-dividend | Ex-date can create a mechanical price drop and distort gap, MAE, ATR, momentum, and breakout context. | Covered; exclude affected episode when authoritative. |
| Stock dividend / ex-right | Share-count and reference-price reset can break price and volume continuity. | Covered; exclude affected episode when authoritative. |
| Rights issue / cash capital increase reference-price reset | Subscription price/ratio and new-share issuance can reset the reference price. | Covered; exclude affected episode when authoritative. |
| Capital reduction | Cash refund, loss coverage, and share-ratio changes can create a discontinuity and may change identity continuity. | Covered; exclude affected episode when authoritative. |
| Stock split / reverse split / par-value change | Proportional price/share-count change invalidates raw-series continuity. | Covered; exclude unless old/new par or ratio semantics are authoritative. |
| Merger / share conversion / demerger | Identity and share-exchange continuity can terminate one security or map it to another. | Covered; exclude both affected identities when mapping is incomplete. |
| Listing / termination / resumption-related price discontinuity | Eligibility, tradability, and first/last bar boundaries can invalidate an episode even without a dividend-style reset. | Covered as a lifecycle/price discontinuity; use lifecycle authority where available, otherwise fail closed. |

The scope does not create an adjusted-price series, total-return series, or a
full corporate-action platform.

## CORPORATE_ACTION_EVENT_AUTHORITY_MATRIX

`POINT_IN_TIME_SAFE` refers to pre-signal eligibility/invalidation use. A
post-hoc event can still be usable for outcome integrity when its effective
date and source semantics are authoritative, even if the event was not known
on the signal date.

| EVENT_FAMILY | OFFICIAL_SOURCE | SOURCE_FIELD/IDENTIFIER | EVENT_DATE_SEMANTIC | REFERENCE_PRICE_AVAILABLE | HISTORICAL_QUERY_AVAILABLE | POINT_IN_TIME_SAFE | AUTOMATION_USE_STATUS | RESEARCH_AUTHORITY_STATE | RAW_PRICE_CONTAMINATION | PROPOSED_EXCLUSION_RULE | NOTES |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Cash dividend / ex-dividend | TWSE TWT48U/TWT49U; TPEx ex-right announcement/calculation pages | Security code; cash dividend; pre-event close; ex-dividend/ex-right flag; opening/reference price where returned | `ex_or_effective_date` is ex-dividend date; `announcement_date` is source publication/announcement date | Partial: direct result pages/products can expose it; formula page alone is not a per-security record | Partial: TWSE since 2003-05-05; TPEx announcement since 2008-12-15; query/archive completeness not proven | Partial: announcement/publication timing is not normalized into PIT snapshots | Blocked pending approved method/terms | Partial; pending owner source-use approval | Price gap, MA/momentum, ATR, resistance, outcome | Event in any applicable feature/trigger/execution/outcome window => `EXCLUDE_EPISODE` | Unknown absence is not `NO_EVENT`. |
| Stock dividend / ex-right | TWSE TWT48U/TWT49U; TPEx ex-right pages | Stock-dividend ratio; subscription ratio/price; security code; ex-right date; reference price | `ex_or_effective_date` is ex-right date, not announcement date | Partial; official formulas/results exist | Partial; page history exists for named periods, full reproducible archive not proven | Partial; only if announcement timing and versioned result are captured | Blocked pending approval | Partial; pending owner source-use approval | Price/share-count/volume discontinuity | `EXCLUDE_EPISODE` unless all required ratio/reference fields are authoritative | Do not infer missing ratio as zero. |
| Rights issue / capital increase reset | TWSE TWT48U/T48; TPEx ex-right/capital-reduction announcement surfaces | Subscription price; new-share ratio; issue/entitlement date; security code | `ex_or_effective_date` is price-reset/ex-right date; listing date may be separate | Partial | Partial; historical pages exist but coverage and identity mapping are not normalized | Partial | Blocked pending approval | Partial; pending owner source-use approval | Reference-price reset and volume comparability | `EXCLUDE_EPISODE` when reset overlaps episode; unknown ratio fails closed | A formula is not proof that the actual result was captured. |
| Capital reduction | TWSE reduction announcement/reference page; TPEx reduction announcement/reference page | Last trading date; resume/effective date; refund; post/pre share ratio; reference price; security code | `ex_or_effective_date` is resume/effective/reference-price date; `announcement_date` remains separate | Partial: formulas and some result surfaces | Partial: TWSE since 2011-01-01; TPEx reference since 2013/01; event archive completeness not proven | Partial | Blocked pending approval | Partial; pending owner source-use approval | Large mechanical reset; possible identity/volume discontinuity | `EXCLUDE_EPISODE`; unknown reduction type/ratio fails closed | Actual announcement takes precedence over preliminary calculation. |
| Split / reverse split / par-value change | TWSE TWTB7U and exchange announcements; TPEx market announcements/reference pages | Old/new par value; old/new share ratio; effective/listing/resumption date; security code | `ex_or_effective_date` is change/resumption date; announcement date is not substitute | Partial | Partial; query surfaces exist, complete common-stock history not proven | No for normalized 507 history | Blocked pending approval | Partial; pending owner source-use approval | Proportional raw-price and volume break | `EXCLUDE_EPISODE` unless old/new ratio and identity continuity are authoritative | Do not use ETF-specific split pages as common-stock coverage. |
| Merger / share conversion / demerger | TWSE/TPEx official market/issuer announcement categories | Old/new identity; effective date; exchange ratio; termination/new listing status | `ex_or_effective_date` is legal/trading identity-effective date; announcement date is PIT metadata | Usually nullable; reference price is not sufficient to prove mapping | Partial; announcement query exists, normalized historical mapping absent | No for the current 507 bundle | Blocked pending approval | Partial; pending owner source-use approval | Identity and price continuity break | `EXCLUDE_EPISODE` for both sides when mapping is incomplete | Must not invent a successor identity. |
| Listing / termination / resumption | TWSE/TPEx lifecycle and market announcements; canonical lifecycle table | Security code; lifecycle event type; effective date; last/first/resume trading date; source record | `ex_or_effective_date` is lifecycle/trading-effective date; announcement date separate | Nullable; price reset may be absent | Partial: canonical 6806 lifecycle is present; complete historical feed is absent | Partial for known canonical lifecycle rows only | Blocked pending approval for new event feed | Partial; lifecycle authority is not a complete CA authority | Eligibility boundary and possible price discontinuity | `EXCLUDE_EPISODE` or lifecycle exclusion; unknown status fails closed | This family is not evidence that all other corporate actions are covered. |

## Research Event Schema

This is a proposal, not an implemented table or API. Nullable fields remain
nullable when the official source does not provide them; they are never
backfilled from a formula, a later issuer announcement, or an inferred price
move.

```text
CorporateActionEventV0
  symbol: canonical source symbol/code, required when source provides it
  market: TPE | TWO, required when source provides it
  security_identity: canonical identity, e.g. TPE:2330, required
  event_type: governed event-family subtype, required
  announcement_date: date | null
  ex_or_effective_date: date | null
  reference_price: decimal | null
  old_par_value: decimal | null
  new_par_value: decimal | null
  old_share_ratio: decimal | null
  new_share_ratio: decimal | null
  source_name: TWSE | TPEX | canonical lifecycle source, required
  source_record_id: string | null
  source_url: string | null
  source_content_hash: sha256 | null
  source_as_of: timestamp/date | null
  retrieved_at: timestamp, required for an authorized artifact
  authority_state: AUTHORIZED | PARTIAL | UNKNOWN | REJECTED
  semantic_version: CA-EVENT-SCHEMA-V0
```

Additional fields may be added only when a reviewed official source exposes a
stable value and the field is included in a versioned contract. In particular,
the schema does not invent cash amount, issue ratio, old/new identity, or
announcement time when the source does not provide it.

`source_content_hash` is required for an authorized persisted raw/semantic
record according to the approved repository lineage pattern. Because source
use is not currently approved for this dataset, no official response or raw
fixture was stored in this task.

## Point-in-Time vs Post-Hoc Semantics

### Pre-signal use

At signal date `t`, any pre-signal eligibility or invalidation decision may use
only event information that was public by `t`:

```text
announcement_date <= signal_date
source_as_of <= signal_date
event facts are complete enough for the named rule
```

If `announcement_date`, `source_as_of`, the security identity, or the required
event date is missing, the event is not PIT-safe for pre-signal use. The
episode must be excluded or blocked; it must not be treated as no event.

### Trading-decision boundary

```text
TRADING_DECISION_USE=FORBIDDEN
```

The event resolver must not alter Gate, Rank, resistance thresholds, trigger
criteria, entry price, or next-day-open execution. A pre-signal event may only
serve the explicit data-quality/eligibility/invalidation boundary. It is not a
new alpha feature, threshold, or adjustment input.

### Post-hoc outcome integrity

```text
POST_HOC_OUTCOME_INTEGRITY_EXCLUSION=ALLOWED
```

After signal/trigger/execution facts are frozen, the audit may inspect the
whole actual episode window, including events that became known after the
signal date. It may mark the episode
`EXCLUDED_CORPORATE_ACTION` and retain the event reason. That exclusion does
not change the historical Gate/Rank/Trigger/Entry decision and is therefore
not look-ahead trading.

## Event-to-Episode Overlap Rules

The authoritative episode shape comes from the research-harness audit:

```text
signal observation date = t
feature lookback       = the actual dependency union for the configured raw features
trigger window          = five observed market-local trading days after t
execution               = next observed trading-day open after a confirmed trigger
outcome horizon         = entry through T+10, including MFE/MAE observation bars
```

The feature lookback is not automatically the entire 60-day history. A
feature is contaminated only when its actual raw-price/raw-volume dependency
intersects an event reset. The V0 episode rule is conservative at the episode
level, but the reason records the exact stage and event date.

| Stage | Event overlap | V0 result | Future refinement |
|---|---|---|---|
| `PRE_SIGNAL_FEATURE_CONTAMINATION` | Event effective date is inside the actual raw feature dependency window ending at `t`, including the signal bar when that bar is used. | Exclude the episode from strategy evaluation. | Restore only with verified event-aware reconstruction for each feature. |
| `TRIGGER_WINDOW_CONTAMINATION` | Event effective date falls on a bar in the five-trading-day candidate-to-trigger window. | Exclude the episode; do not count a mechanical close break as a strategy trigger. | A separate event-aware trigger study may be proposed later. |
| `EXECUTION_CONTAMINATION` | Event affects the confirmed trigger bar or the exact next-trading-day open used for execution. | Exclude the episode; never substitute trigger close or a later open. | Restore only with a verified execution/reference-price contract. |
| `OUTCOME_CONTAMINATION` | Event falls from valid entry through T+10 or any MFE/MAE observation bar. | Exclude the episode from all affected outcome denominators; retain frozen signal/trigger facts for audit. | Permit component-level outcome exclusion only after event-aware outcome semantics are approved. |

Deterministic ordering for multiple events is:

1. unknown or incomplete authority;
2. earliest contaminated stage;
3. event effective date;
4. governed event type;
5. source record identity.

The artifact may retain all matching events, but `primary_exclusion_reason`
must be stable under this order.

## Feature / Trigger / Execution / Outcome Contamination

| Contamination class | Examples of affected raw facts | Exclusion reason |
|---|---|---|
| `PRE_SIGNAL_FEATURE_CONTAMINATION` | Prior-20 resistance, MA, slope, momentum, ATR/range, volume comparison, structure or support features | `CA_EX_DIVIDEND`, `CA_EX_RIGHT`, `CA_CAPITAL_REDUCTION`, `CA_SPLIT_REVERSE_SPLIT`, `CA_PAR_VALUE_CHANGE`, `CA_SHARE_CONVERSION`, `CA_LISTING_TERMINATION`, or `CA_AUTHORITY_UNKNOWN` |
| `TRIGGER_WINDOW_CONTAMINATION` | Close-over-resistance, gap breakout, failed attempt, invalidation, trigger-window price/volume state | Same family reason with stage suffix `TRIGGER_WINDOW` in the exclusion record |
| `EXECUTION_CONTAMINATION` | Exact next-day open, tradability, successor-bar identity, entry price | Same family reason with stage suffix `EXECUTION` |
| `OUTCOME_CONTAMINATION` | T+5/T+10 close, high/low excursion, MFE/MAE, invalidation after entry | Same family reason with stage suffix `OUTCOME` |

All stage-specific records must include `episode_id`, `event_date`,
`event_type`, `source_record_id` when available, `authority_state`, and the
policy version. No affected event is converted into a loss, no-trigger, or
zero-valued metric.

## Reason Codes

The stable reason-code proposal is:

| Code | Meaning |
|---|---|
| `CA_EX_DIVIDEND` | Cash-dividend ex-date or equivalent cash distribution reset. |
| `CA_EX_RIGHT` | Stock dividend or ex-right event. |
| `CA_CAPITAL_INCREASE_REFERENCE_RESET` | Rights/cash-capital-increase reference-price reset not otherwise classified. |
| `CA_CAPITAL_REDUCTION` | Capital reduction, cash refund, loss coverage, or related resumption reset. |
| `CA_SPLIT_REVERSE_SPLIT` | Stock split or reverse split. |
| `CA_PAR_VALUE_CHANGE` | Old/new par-value change affecting price/share continuity. |
| `CA_SHARE_CONVERSION` | Merger, share conversion, demerger, successor/predecessor mapping, or identity discontinuity. |
| `CA_LISTING_TERMINATION` | Listing, termination, delisting, suspension/resumption, or first/last tradable-bar discontinuity. |
| `CA_OTHER_PRICE_RESET` | An authoritative price reset that does not fit the governed families. |
| `CA_AUTHORITY_UNKNOWN` | Event coverage, identity, date, source semantics, or use authority is unresolved. |

`CA_AUTHORITY_UNKNOWN` is fail-closed. It is not a no-event result and cannot
enter a formal performance denominator.

## EVENT_EXCLUDED_RAW_V0 Contract

```text
CorporateActionPolicy
  policy_id: EVENT_EXCLUDED_RAW
  policy_version: EVENT_EXCLUDED_RAW_V0
  covered_event_families:
    CASH_DIVIDEND_EX_DIVIDEND
    STOCK_DIVIDEND_EX_RIGHT
    RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET
    CAPITAL_REDUCTION
    SPLIT_REVERSE_SPLIT
    PAR_VALUE_CHANGE
    MERGER_SHARE_CONVERSION_DEMERGER
    LISTING_TERMINATION_RESUMPTION_DISCONTINUITY
  event_authority_version: CA-EVENT-SCHEMA-V0 / PARTIAL_PENDING_SOURCE_APPROVAL
  feature_contamination_window_rule: actual raw feature dependency union through signal date
  trigger_overlap_rule: any known event in the five observed trigger bars => EXCLUDE_EPISODE
  execution_overlap_rule: event on trigger or exact next-trading-day open => EXCLUDE_EPISODE
  outcome_overlap_rule: event from entry through T+10/MFE/MAE bars => EXCLUDE_EPISODE
  unknown_authority_behavior: FAIL_CLOSED / CA_AUTHORITY_UNKNOWN
  exclusion_reason_codes: governed CA_* list above
  trading_decision_use: FORBIDDEN
  post_hoc_outcome_integrity_exclusion: ALLOWED
  gross_metric_denominator: valid policy-eligible executed outcomes only
  net_metric_denominator: valid policy-eligible executed outcomes with authorized cost scenario
  excluded_episode_denominator: zero for loss/no-trigger/win-rate/expectancy/T+5/T+10/MFE/MAE
  aggregate_reporting: excluded_count and reason/stage distribution required
  current_authority_state: CONTRACT_READY / SOURCE_AUTHORITY_PARTIAL
```

`EVENT_EXCLUDED_RAW` retains official observed OHLCV and excludes affected
episodes. It does not mean the OHLCV is proven raw or adjusted, and it does
not mutate, back-adjust, forward-adjust, or replace any OHLCV row.

## Metric Denominator Rules

- `EXCLUDED_CORPORATE_ACTION` is not a loss.
- It is not `NO_TRIGGER` and is not an expired candidate.
- It is not included in win-rate or expectancy denominators.
- It is not included in T+5, T+10, MFE, or MAE denominators.
- It is not silently converted to a zero return, zero excursion, or missing
  loss.
- Candidate, trigger, execution, and outcome audit counts remain separate.
  Each aggregate must display excluded count, stage, and reason distribution.
- If authority status is unknown for the relevant window, the episode is
  excluded rather than included on the assumption that the raw series is safe.
- Gross and net metrics remain separate. Net metrics additionally require an
  explicit authorized cost/slippage scenario from the future protocol freeze.

## Dataset Implementation Decision

```text
CORPORATE_ACTION_DATASET_IMPLEMENTED=NO
CORPORATE_ACTION_DATASET_IDEMPOTENT=NA
DATASET_ROWS=0
DATASET_DATE_RANGE=NONE
LINEAGE_COMPLETE=NA_DATASET_NOT_IMPLEMENTED
SOURCE_RESPONSE_FIXTURE_STORED=NO
RAW_OHLCV_MODIFIED=NO
ADJUSTED_OHLC_CREATED=NO
TOTAL_RETURN_CREATED=NO
```

The source authority and use approval are not sufficient for a local
research-only ingestion artifact. Implementing a loader now would turn
public-page existence into an unauthorized automated persistence claim and
would create a second, unapproved persistence family. The future
implementation may reuse existing provider/lineage/checkpoint/idempotence
patterns only after owner source-use approval and field/coverage closure.

No code, table, migration, API, frontend, scheduler, or local source-response
fixture was added.

## Persistence / Lineage / Idempotence

No persistence capability was implemented, so idempotence is not claimed. The
future minimal artifact must meet these conditions before implementation:

1. a bounded research snapshot, never a Production read model;
2. deterministic security identity and event key;
3. source record identity plus source URL and authorized content/semantic hash;
4. retrieval and source-as-of metadata;
5. versioned semantic mapper and authority state;
6. checkpointed, transactional, idempotent replay using existing repository
   patterns rather than a generic second persistence architecture;
7. no raw official response fixture unless the approved terms allow it;
8. reduced semantic fixtures only, with no copied bulk official content.

## Control Cases

### TWSE ex-dividend control: 2330

The official TWSE notice identifies `2330` as one of the ten stocks with an
ex-dividend date of `2026-06-11`. The canonical local database contains
`2330` OHLCV rows on the surrounding dates. A read-only aggregate check found
four surrounding rows and a pre-event-close-to-ex-date-open movement of
`-0.6652%`; the pre-event-close-to-ex-date-close movement was `-0.2217%`.
The check is not a return-performance claim. It demonstrates that the event
date maps to an observed raw-bar boundary and that the conservative policy
must exclude the episode rather than interpret the move as a strategy signal.

```text
CONTROL_TWSE_2330_EX_DIVIDEND=PASS
EVENT_DATE=2026-06-11
EVENT_SOURCE=TWSE_OFFICIAL_NOTICE
RAW_BAR_BOUNDARY=OBSERVED_READ_ONLY
POLICY_RESULT=EXCLUDED_CORPORATE_ACTION / CA_EX_DIVIDEND
SOURCE_RESPONSE_PERSISTED=NO
```

### Lifecycle control: 6806

The canonical lifecycle table records `6806` as terminated on `2026-06-23`.
The read-only OHLCV check found the last bar on `2026-06-22` and zero bars on
or after the effective termination date. This validates the existing
lifecycle boundary but does not claim that lifecycle coverage is a complete
corporate-action feed.

```text
CONTROL_TWSE_6806_TERMINATION=PASS
EVENT_DATE=2026-06-23
LAST_BAR=2026-06-22
POST_EVENT_OHLCV_ROWS=0
POLICY_RESULT=LIFECYCLE_BOUNDARY_EXCLUSION
```

### Reduced semantic controls

The task-local non-persisted semantic fixture asserted six cases:

```text
known event in feature window       -> PRE_SIGNAL_FEATURE_CONTAMINATION
known event in trigger window       -> TRIGGER_WINDOW_CONTAMINATION
known event on execution date       -> EXECUTION_CONTAMINATION
known event in outcome horizon      -> OUTCOME_CONTAMINATION
empty event set                     -> PASS_NO_EVENT (only when authority is complete)
unknown/incomplete event authority  -> CA_AUTHORITY_UNKNOWN / fail closed
SEMANTIC_FIXTURE_ASSERTIONS=6 passed
```

The empty-event case is a contract control, not evidence that an entire
historical interval contains no corporate action. The task did not guess a
TPEx stock or batch-download a TPEx event result while source-use approval was
pending.

## Source-Use Governance

The governance state is deliberately split:

| Question | Current result |
|---|---|
| Do official TWSE/TPEx source pages exist? | Yes, for all scoped families at least as partial surfaces. |
| Do the pages expose useful field semantics? | Yes, for several date, ratio, dividend, and reference-price fields; incomplete for a full event authority. |
| Is historical query availability complete across the 507 identities and all families? | No; partial and not normalized. |
| Can the repository prove point-in-time event visibility? | No; announcement/publication timing is not persisted as an as-of event dataset. |
| Is automated download/retrieval approved? | No current project evidence; TPEx terms expressly require an approved method/consent for automated extraction. |
| Is storing/replaying a new event dataset approved? | Pending owner source-use approval. |
| Is external/public redistribution authorized? | Not established; current product terms distinguish internal/external use and written authorization. |

No legal interpretation is made here. The next authority decision must record
the approved source/product, permitted use, covered fields, retention and
hashing rules, automation method/rate limits, reproduction boundary, and
whether a research-only semantic artifact may be stored locally.

## Look-Ahead Safety

```text
TRADING_DECISION_LOOKAHEAD=NO
PRE_SIGNAL_RULE=only public-by-signal-date facts may affect eligibility/invalidation
GATE_RANK_TRIGGER_ENTRY=unchanged_by_event_resolver
POST_HOC_OUTCOME_EXCLUSION_AUTHORIZED=YES
POST_HOC_OUTCOME_EXCLUSION_QUALIFIER=CONTRACT_ONLY_NO_INGESTION_OR_RUN_AUTHORIZATION
FUTURE_EVENT_IN_OUTCOME_WINDOW=may exclude outcome; may not rewrite decision
UNKNOWN_EVENT_AUTHORITY=fail closed; never infer no event
```

The post-hoc rule is an integrity filter, not a trading signal. It prevents a
mechanical event from being counted as a loss, win, no-trigger, or return
observation while leaving the historical decision facts immutable.

## Remaining Blockers

1. Owner approval for research-only retrieval, local storage, hashing, replay,
   and automation of TWSE/TPEx event information.
2. A reviewed source list and field-level contract for each scoped event family.
3. A complete historical query/reproduction plan with stated coverage dates,
   corrections, and source-as-of semantics.
4. A point-in-time publication/announcement model that distinguishes event
   effective date from when the fact was public.
5. Identity mapping for merger, conversion, demerger, split, and par-value
   events across the fixed 507 identities.
6. Approval of the future local research artifact boundary and retention rules.

Because these blockers remain, the next task must close source authority,
approval, and historical semantics before any Dataset/Protocol Freeze. It must
not jump directly to performance evaluation.

## Dataset / Protocol Freeze Authorization Decision

The following can be carried forward as a proposed Freeze input:

```text
UniversePolicy=LIFECYCLE_GATED_507
CorporateActionPolicy=EVENT_EXCLUDED_RAW_V0
RS=OMITTED
TopicContext=OMITTED
```

The Freeze itself is not authorized because the policy's event authority
version is still partial and source-use approval is pending.

```text
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO
REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO
NEXT_RECOMMENDED_TASK=TASK-REC-A1-CORPORATE-ACTION-SOURCE-USE-APPROVAL-AND-HISTORICAL-EVENT-SEMANTICS-CLOSURE
NEXT_TASK_CHANGED=NO
```

When the blockers close, the recommended next task is
`TASK-REC-A1-RESEARCH-DATASET-PROTOCOL-FREEZE`. It must bind the approved
source/event snapshot and policy versions before any run authorization.

## Impact Validation

This task is contract/report-only. The control cases used read-only local
queries and non-persisted semantic assertions.

```text
FOCUSED_SEMANTIC_ASSERTIONS=6 passed
READ_ONLY_2330_EVENT_CONTROL=PASS
READ_ONLY_6806_LIFECYCLE_CONTROL=PASS
REPORT_LINK/SECTION_CHECK=to run after report creation
DIFF_CHECK=to run after report creation
SECRET_SCAN=to run after report creation
FIXTURE_SAFETY=PASS_NO_RAW_OFFICIAL_RESPONSE_STORED
G1=PRESERVED PASS
G2=PRESERVED PASS
G3=PRESERVED PASS
POST_CLOSE_CANARY=PRESERVED PASS
```

G1/G2/G3/Post-Close Canary were not rerun because no protected reference,
provider, market-semantics, post-close, application, database, or historical
OHLCV input changed.

## Documentation Reconciliation

Only this new report is in the exact task write set. `PROJECT_CONTEXT.md`,
`docs/ROADMAP.md`, `docs/product/TOPICPILOT_PRODUCT_ROADMAP.md`,
`docs/DOCUMENTATION_INDEX.md`, `docs/DAILY_PROGRESS.md`, and
`docs/WORK_ORDERS.md` were read but not edited. They had pre-existing changes
or active ownership/collision considerations; no duplicate status block was
added.

```text
REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
OWNER_DOCUMENTS_UPDATED=NO
```

The report is evidence for the next source-authority task, not a permanent
replacement for the current roadmap or project context.

## Final Handoff

```text
TASK_ID=TASK-REC-A1-CORPORATE-ACTION-EVENT-EXCLUSION-CLOSURE
FINAL_STATUS=REC_A1_EVENT_AUTHORITY_PARTIAL_CONTRACT_READY_SOURCE_USE_APPROVAL_BLOCKED
CANONICAL_PRE_SHA=88a4dcc897e986b0c5667f97cad27bb0f0131610
CANONICAL_POST_SHA=LOCAL_TASK_COMMIT_SHA_REPORTED_AT_HANDOFF
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_USED=NO
PRIOR_A_B_C_AUTHORITY_RECONCILED=YES
CORPORATE_ACTION_EVENT_SOURCE_AUTHORITY=PARTIAL
COVERED_EVENT_FAMILIES=CASH_DIVIDEND_EX_DIVIDEND;STOCK_DIVIDEND_EX_RIGHT;RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET;CAPITAL_REDUCTION;SPLIT_REVERSE_SPLIT;PAR_VALUE_CHANGE;MERGER_SHARE_CONVERSION_DEMERGER;LISTING_TERMINATION_RESUMPTION_DISCONTINUITY
HISTORICAL_EVENT_QUERY=PARTIAL
EVENT_DATE_SEMANTICS=PARTIAL
REFERENCE_PRICE_AUTHORITY=PARTIAL
SOURCE_USE_APPROVAL_STATUS=PENDING_OWNER_SOURCE_USE_APPROVAL
RESEARCH_ONLY_USE_STATUS=BLOCKED_PENDING_OWNER_SOURCE_USE_APPROVAL
AUTOMATED_BULK_INGESTION_STATUS=BLOCKED
CORPORATE_ACTION_EVENT_SCHEMA_READY=YES
CORPORATE_ACTION_EVENT_SCHEMA_QUALIFIER=PROPOSAL_NOT_IMPLEMENTED
CORPORATE_ACTION_DATASET_IMPLEMENTED=NO
CORPORATE_ACTION_DATASET_IDEMPOTENT=NA
DATASET_ROWS=0
DATASET_DATE_RANGE=NONE
LINEAGE_COMPLETE=NA_DATASET_NOT_IMPLEMENTED
IDEMPOTENT=NA
CONTROL_CASES=2330_EX_DIVIDEND_PASS;6806_TERMINATION_PASS;SEMANTIC_FIXTURE_6_PASS;UNKNOWN_FAIL_CLOSED_PASS
PRE_SIGNAL_FEATURE_CONTAMINATION_RULE=ACTUAL_RAW_FEATURE_DEPENDENCY_UNION_THROUGH_SIGNAL_DATE
TRIGGER_WINDOW_CONTAMINATION_RULE=ANY_KNOWN_EVENT_IN_FIVE_TRADING_DAY_WINDOW_EXCLUDE_EPISODE
EXECUTION_CONTAMINATION_RULE=EVENT_ON_TRIGGER_OR_EXACT_NEXT_OPEN_EXCLUDE_EPISODE
OUTCOME_CONTAMINATION_RULE=EVENT_FROM_ENTRY_THROUGH_T+10_OR_MFE_MAE_BARS_EXCLUDE_OUTCOME
UNKNOWN_EVENT_AUTHORITY_FAIL_CLOSED=YES
EVENT_EXCLUSION_REASON_CODES=CA_EX_DIVIDEND;CA_EX_RIGHT;CA_CAPITAL_INCREASE_REFERENCE_RESET;CA_CAPITAL_REDUCTION;CA_SPLIT_REVERSE_SPLIT;CA_PAR_VALUE_CHANGE;CA_SHARE_CONVERSION;CA_LISTING_TERMINATION;CA_OTHER_PRICE_RESET;CA_AUTHORITY_UNKNOWN
EVENT_EXCLUDED_RAW_POLICY=READY
EVENT_EXCLUDED_RAW_POLICY_QUALIFIER=CONTRACT_ONLY_SOURCE_AUTHORITY_PARTIAL
TRADING_DECISION_LOOKAHEAD=NO
POST_HOC_OUTCOME_EXCLUSION_AUTHORIZED=YES
POST_HOC_OUTCOME_EXCLUSION_QUALIFIER=CONTRACT_ONLY_NO_INGESTION_OR_RUN_AUTHORIZATION
METRIC_DENOMINATOR_RULES=EXCLUDED_NOT_LOSS_NOT_NO_TRIGGER_NOT_IN_WIN_RATE_EXPECTANCY_T+5_T+10_MFE_MAE_DENOMINATORS
UNIVERSE_POLICY_INPUT=LIFECYCLE_GATED_507
SURVIVORSHIP_DISCLOSURE_REQUIRED=YES
RS=OMITTED
TOPIC_CONTEXT=OMITTED
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO
REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO
NEXT_RECOMMENDED_TASK=TASK-REC-A1-CORPORATE-ACTION-SOURCE-USE-APPROVAL-AND-HISTORICAL-EVENT-SEMANTICS-CLOSURE
REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
APPLICATION_CODE_CHANGED=NO
DATABASE_MUTATION=NO
HISTORICAL_OHLCV_CHANGED=NO
RECOMMENDATION_ENGINE_CHANGED=NO
PRODUCTION_MUTATION=NO
PUSH_REMOTE=NO
MERGE_MAIN=NO
DEPLOY=NO
SCHEDULER=NO
NEXT_TASK_CHANGED=NO
G1=PRESERVED PASS
G2=PRESERVED PASS
G3=PRESERVED PASS
POST_CLOSE_CANARY=PRESERVED PASS
```

The task stops here. It does not execute Dataset/Protocol Freeze, walk-forward,
backtest, parameter search, or production work.
