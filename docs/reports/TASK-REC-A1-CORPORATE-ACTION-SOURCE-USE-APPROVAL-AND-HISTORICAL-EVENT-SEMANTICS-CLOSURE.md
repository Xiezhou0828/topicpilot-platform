# TASK-REC-A1-CORPORATE-ACTION-SOURCE-USE-APPROVAL-AND-HISTORICAL-EVENT-SEMANTICS-CLOSURE

**Review date:** `2026-08-15`

**Scope:** Owner-approved internal research use of official TWSE/TPEx
corporate-action sources, source-specific acquisition methods, historical
event-date semantics, identity/lifecycle alignment, and authorization of the
next minimal research-only dataset implementation.

**Evidence rule:** Official source and terms pages were reviewed on
`2026-08-15`. This report records source and governance evidence, not a legal
opinion. No official raw response, paid product file, or copied bulk source
content was stored in the repository.

## Executive Decision

The Owner approval gate is closed as requested:

```text
OWNER_DECISION=APPROVED_INTERNAL_RESEARCH_ONLY
OWNER_APPROVAL_STATUS=APPROVED_INTERNAL_RESEARCH_ONLY
```

The external source boundary is also closed sufficiently for the next,
bounded implementation, but only with a method split:

```text
TWSE documented OpenAPI endpoints       = automated use conditionally allowed
TWSE public HTML/CSV query surfaces     = manual or bounded only
TWSE paid E-Shop T48 product            = not authorized without subscription/consent
TPEx public HTML/CSV query surfaces     = manual or bounded only
TPEx automated extraction               = blocked without an approved method/consent
TPEx paid E-Shop products/API           = not authorized without subscription/consent
```

The covered core event families have deterministic effective-date semantics
for a research exclusion dataset. The remaining identity-discontinuity
families are explicitly `SEMANTIC_PARTIAL`; unresolved rows are not treated as
no-event and fail closed.

```text
DATASET_IMPLEMENTATION_AUTHORIZED=YES
AUTHORIZED_INGESTION_MODE=MANUAL_OR_BOUNDED_OFFICIAL_RESEARCH_V0
AUTOMATED_EXTRACTION_STATUS_TWSE=ALLOWED_ONLY_FOR_OFFICIAL_DOCUMENTED_OPENAPI_ENDPOINTS
AUTOMATED_EXTRACTION_STATUS_TPEX=AUTOMATED_EXTRACTION_BLOCKED
MANUAL_BOUNDED_INGESTION_STATUS=AUTHORIZED_FOR_RESEARCH_V0_WITH_LINEAGE_AND_FAIL_CLOSED_GAPS
```

This is authorization for the next dataset task, not implementation of the
dataset, not a Production data permission, and not a permission to reproduce
or redistribute official raw data.

```text
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO_UNTIL_DATASET_IMPLEMENTED_AND_VALIDATED
REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO
```

## Owner Decision Record

The Owner explicitly approved the following bounded use for REC-A1 and
TopicPilot internal research:

- use confirmed official TWSE/TPEx corporate-action sources;
- retrieve through a source-permitted method;
- retain a local/research semantic artifact and necessary provenance;
- normalize event records without changing historical OHLCV;
- retain content and semantic hashes, retrieval metadata, and replay
  checkpoints;
- use the resulting research dataset for `EVENT_EXCLUDED_RAW_V0` episode
  exclusion and future research replay only.

The approval does not grant exchange authorization. It does not authorize
public or external redistribution, raw-data downloads for public delivery,
website crawling, bypassing anti-bot or access controls, Production
publication, adjusted OHLC/total-return construction, or any method prohibited
by TWSE/TPEx terms.

The distinction used throughout this report is:

```text
OWNER_APPROVAL_STATUS       = project governance decision
EXTERNAL_SOURCE_USE_STATUS  = source/product/method-specific authority
```

The second status remains conditional where the official source requires an
approved method, paid subscription, written consent, or a particular delivery
channel.

## Canonical State

```text
CANONICAL_REPO=C:\Users\acer\Desktop\題材領航\topicpilot-platform
CANONICAL_PRE_SHA=c2a8b2e98f7c96499cce271b81c676b214183df0
CANONICAL_BRANCH=codex/task-ops-023a-p3c-runtime-sha-audit-20260813
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
DIRTY_STATE=YES_PRE_EXISTING_PARALLEL_CHANGES_PRESERVED
DIRTY_STATUS_COUNT_AT_AUDIT=160
ACTIVE_WORKTREE_COUNT_AT_AUDIT=15
WORKTREE_USED=NO
EXACT_TASK_WRITE_SET=docs/reports/TASK-REC-A1-CORPORATE-ACTION-SOURCE-USE-APPROVAL-AND-HISTORICAL-EVENT-SEMANTICS-CLOSURE.md
```

The canonical checkout was audited directly. Existing modified and untracked
files belong to parallel work and were not reset, stashed, cleaned, or
reconciled. The report path was absent before this task and does not collide
with the active Favorites, Today, Topic Detail, Stock, Historical, or owner
document write sets.

No new worktree was created. The active worktree list was inspected only to
confirm parallel state; no other worktree was treated as canonical authority.

## Prior Closure Baseline

The following prior REC-A1 conclusions are carried forward and are not
reopened:

```text
CORPORATE_ACTION_EVENT_SCHEMA_READY=YES
CORPORATE_ACTION_EVENT_SCHEMA_STATE=PROPOSAL_READY_NOT_IMPLEMENTED
EVENT_EXCLUDED_RAW_POLICY=READY
UNKNOWN_EVENT_AUTHORITY_FAIL_CLOSED=YES
TRADING_DECISION_LOOKAHEAD=NO
POST_HOC_OUTCOME_EXCLUSION_AUTHORIZED=YES
UNIVERSE_POLICY=LIFECYCLE_GATED_507
SURVIVORSHIP_DISCLOSURE_REQUIRED=YES
RS=OMITTED
TOPIC_CONTEXT=OMITTED
CORPORATE_ACTION_DATASET_IMPLEMENTED=NO
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO
REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO
```

The previous `PENDING_OWNER_SOURCE_USE_APPROVAL` value is historical evidence
from the predecessor closure. It is replaced here only by the explicit Owner
decision above; it is not reused as the current status.

### HIST-002B research window and universe

The canonical HIST-002B closure remains the data-window baseline:

| Attribute | Reconciled value |
|---|---:|
| Physical identities | 507 |
| TPE identities | 314 |
| TWO identities | 193 |
| Canonical OHLCV rows | 63,826 |
| Window start | 2026-02-02 |
| Window end | 2026-08-13 |
| Known lifecycle event | TPE:6806 effective termination 2026-06-23 |
| TPE:6806 last OHLCV bar | 2026-06-22 |
| TPE:6806 rows on/after effective date | 0 |

This is enough to align event records to the current physical identity
universe. It is not a claim that the current 507 identities are a
survivorship-safe historical universe.

## Official Source and Terms Evidence

The source review was performed on `2026-08-15`. Official pages are linked
directly; no third-party page is used as source authority.

### TWSE evidence

- [TWSE OpenAPI](https://openapi.twse.com.tw/) documents the official API
  catalog and lists `STOCK_DAY_ALL` for listed-stock daily trading
  information and `TWT48U_ALL` for listed-stock ex-right/ex-dividend
  announcements. The catalog states that it provides TWSE service APIs for
  integration. This is the only TWSE automation path treated as conditionally
  allowed in this closure.
- [TWSE Ex-right Announcement](https://www.twse.com.tw/en/announcement/ex-right/twt48u.html)
  exposes stock-dividend and cash-capital-increase ratio semantics.
- [TWSE Ex-right Price Data](https://www.twse.com.tw/en/announcement/ex-right/twt49u.html)
  states availability since `2003/05/05`, supports date queries, and defines
  ex-right and ex-dividend reference-price inputs and formulas.
- [TWSE Reference Price for Capital Reduction](https://www.twse.com.tw/en/announcement/reduction/twtauu.html)
  states availability since `2011/01/01`, is queried by resume-trading date,
  and distinguishes refund, loss-coverage, and cash-injection cases.
- [TWSE Change of Par Value Announcement](https://www.twse.com.tw/en/announcement/change/twtb7u.html)
  defines the old/new par-value ratio and share-count relationship.
- [TWSE T48 Ex-Right/Dividend and List/Delist product](https://eshop.twse.com.tw/en/product/detail/000000006e0bbe8d016f1842c12f0342)
  describes an official daily product with effective date, security code,
  pre-event close, opening reference price, ex-right/ex-dividend fields,
  dividends, stock-dividend ratios, and capital-increase fields. It is a paid
  subscription product beginning `2019-12-23`; no TopicPilot subscription or
  consent evidence exists in this repository.
- [TWSE Website Terms](https://www.twse.com.tw/en/terms/use.html) prohibit
  downloading software or data by crawler, scraper, instruction code, or
  other automated tool unless TWSE has agreed to the method or prior consent
  has been obtained. The terms also restrict reproduction and distribution of
  protected materials.
- [TWSE Data E-Shop Terms](https://eshop.twse.com.tw/en/home/terms) repeat the
  restriction on automation devices, scripts, spiders, crawlers, and other
  retrieval programs except approved methods or TWSE consent, and require
  respect for intellectual-property and reproduction limits.

### TPEx evidence

- [TPEx Ex-rights/Ex-dividend Announcements](https://www.tpex.org.tw/en-us/announce/market/ex/announce.html)
  provides date/code queries and CSV export, states availability since
  `2008/12/15`, and warns that issuer announcements take precedence for actual
  distribution details.
- [TPEx Ex-rights/Ex-dividend Calculation Result Sheet](https://www.tpex.org.tw/en-us/announce/market/ex/cal.html)
  provides date-range queries and CSV export, states availability since
  `2008/01/02`, and defines opening-reference-price/tick-size semantics.
- [TPEx Ex-rights/Ex-dividend Price Quotes](https://www.tpex.org.tw/en-us/announce/market/ex/announce/quotes.html)
  states that calculated quotes are reference information and that actual
  announcements take precedence.
- [TPEx Reference Price for Capital Reduction](https://www.tpex.org.tw/en-us/announce/market/reduction/reference.html)
  is the official capital-reduction reference-price surface. The previously
  reviewed official page records availability from `2013/01`; current direct
  fetch availability is not treated as a reason to infer or fill records.
- [TPEx Capital-Reduction Announcements](https://www.tpex.org.tw/en-us/announce/market/reduction-tdr.html)
  is the official announcement surface for reduction events. The previously
  reviewed official page records availability from `2015/12`.
- [TPEx Daily Stock Info](https://www.tpex.org.tw/en-us/mainboard/trading/info/stock-pricing.html?code=8433)
  provides code/date queries and CSV/UTF-8 export for daily stock information;
  the official page states availability since `1994/01`. This is raw-bar and
  identity evidence, not a corporate-action event authority.
- [TPEx Daily Stock Quotes](https://www.tpex.org.tw/en-us/mainboard/trading/info/pricing.html)
  provides date queries and CSV export for daily market information and
  states availability since `2007/01`.
- [TPEx E-Data Shop Terms](https://eshop.tpex.org.tw/en/useTerms/index) state
  that data or software may not be downloaded through automated devices,
  scripts, automated programs, spiders, web crawlers, or extraction other
  than TPEx-approved methods or with TPEx consent.
- [TPEx after-hours trading information subscription terms](https://eshop.tpex.org.tw/en/product/shoppingTerm)
  limit internal-use products to internal users and prohibit reproduction,
  transmission, distribution, or separate sampling for indices/derivatives
  without written TPEx authorization.

### Method interpretation

The review does not infer permission from the fact that a web page is public.
The method status is determined by the documented API/download surface and the
source terms:

| Source/method | Official evidence | Automation status | Local research status | External source-use status |
|---|---|---|---|---|
| TWSE documented OpenAPI catalog (`openapi.twse.com.tw/v1`) | Official Swagger/catalog lists documented GET endpoints including daily data and TWT48U_ALL | `OFFICIAL_API_AUTOMATED_ALLOWED` for listed documented endpoints only | Conditional; retain reduced semantics, source URL, attribution, hashes, and metadata | `CONDITIONALLY_AUTHORIZED_DOCUMENTED_OPENAPI_INTERNAL_RESEARCH` |
| TWSE public TWT49U / capital-reduction query/export | Official date-query and CSV/HTML surfaces; no separate automation permission in reviewed terms | `AUTOMATION_BLOCKED` for website scraping; user-operated query/export only | Conditional manual/bounded use | `MANUAL_OR_BOUNDED_QUERY_ONLY` |
| TWSE paid T48 E-Shop product | Official paid product, daily delivery/download, internal/external subscription modes | Not applicable without product access; no crawler/download automation | Not authorized absent subscription/terms confirmation | `NOT_AUTHORIZED_NO_SUBSCRIPTION_OR_CONSENT_EVIDENCE` |
| TPEx public ex-right, calculation, reduction, and daily-query pages | Official date/code query and CSV/UTF-8 export pages | `AUTOMATED_EXTRACTION_BLOCKED` unless TPEx approves the method or consents | Manual or bounded user-operated research export only | `MANUAL_OR_BOUNDED_QUERY_ONLY` |
| TPEx E-Data Shop products/API | Official subscription terms and product surface | Not authorized without an approved delivery method/consent | Not authorized absent subscription/terms confirmation | `NOT_AUTHORIZED_NO_SUBSCRIPTION_OR_CONSENT_EVIDENCE` |

## Source Method Authority Matrix

The following matrix is the V0 authority boundary. `HISTORICAL_RANGE`
describes the official surface's stated availability, not a claim that every
record is complete, immutable, or PIT-frozen.

| Exchange | Official product/surface | Event family | Access method | Historical range | Fields usable for V0 | Date semantics | Rate/query limit | Automation language in terms | Local storage | Normalization | Hash/lineage | Replay | Raw reproduction | Public redistribution | External source-use status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TWSE | OpenAPI `TWT48U_ALL` plus official ex-right surfaces | Cash dividend, stock dividend, rights/capital increase | Documented API for catalog-listed endpoint; public query fallback | API catalog does not state a complete historical range; public TWT49U range starts 2003-05-05 | Code, event/ex-date fields returned by the endpoint, dividend/rights fields when present, source response metadata | Event/ex-right date is the effective price-discontinuity date; announcement/publication date is separate provenance | Official limit not stated in reviewed catalog; repository `RateLimitedTransport` default is 60 requests/min with bounded retries, not an exchange permission | Website/E-Shop automation prohibited except approved method/consent; documented OpenAPI treated as the approved-method candidate | Conditional reduced semantic record; raw response only if method/terms permit | `CA-EVENT-SCHEMA-V0` mapper; nullable fields stay null | Source URL, method, retrieval time, source-as-of, content hash, semantic hash | Deterministic request key plus checkpoint/idempotent replay in next task | Retain only if method/terms permit; otherwise retain reduced semantic record | No public raw-data reproduction or redistribution | `CONDITIONALLY_AUTHORIZED_DOCUMENTED_OPENAPI_INTERNAL_RESEARCH` | [TWSE OpenAPI](https://openapi.twse.com.tw/); [TWT49U](https://www.twse.com.tw/en/announcement/ex-right/twt49u.html) |
| TWSE | TWT49U Ex-right Price Data | Cash dividend, stock dividend, rights/capital increase | Manual or bounded official date query/CSV export | Since 2003-05-05; covers 2026-02-02 through 2026-08-13 | Pre-event close, cash dividend, subscription price/ratio, stock-dividend ratio, opening/reference price when returned | Ex-dividend/ex-right date is primary effective date; source query/publication date is not the effective date | Query limit not stated; no automation claim | Website terms prohibit crawler/scraper/automation without agreement/consent | Conditional manual/bounded semantic capture | Same mapper; formula-only page cannot substitute for missing event row | Hash exported file/response if retained; always hash normalized row and record URL/retrieval | Manual export manifest and deterministic row key; no automated replay claim | Retain only when the bounded method/terms permit | No public raw-data reproduction or redistribution | `MANUAL_OR_BOUNDED_QUERY_ONLY` | [TWSE Ex-right Price Data](https://www.twse.com.tw/en/announcement/ex-right/twt49u.html) |
| TWSE | Capital-reduction reference-price page | Capital reduction | Manual or bounded official date query/CSV export | Since 2011-01-01; covers research window | Last-trading close, refund, post/original share ratio, subscription terms, reference price when returned | Resume-trading/reference-price effective date is primary; last trading date and announcement date remain separate | Query limit not stated | Website terms prohibit unapproved automation | Conditional manual/bounded semantic capture | Reduction subtype and ratio required; formula alone is not a row | Hash normalized event and source metadata | Manual checkpoint keyed by resume date/security | Retain only when the bounded method/terms permit | No public raw-data reproduction or redistribution | `MANUAL_OR_BOUNDED_QUERY_ONLY` | [TWSE Capital Reduction Reference Price](https://www.twse.com.tw/en/announcement/reduction/twtauu.html) |
| TWSE | T48 paid E-Shop product | Cash/stock dividend, rights, list/delist | Official subscription download/email delivery | Daily; start date 2019-12-23; covers window if subscribed | Effective date, code, pre-event close, opening reference price, ex-right/ex-dividend, dividend, ratios, capital-increase fields | Product `Effective Date` is primary event date; delivery/retrieval date is provenance | Product/subscription terms; no project entitlement observed | E-Shop automation prohibited except approved methods/consent | Not authorized yet | Future mapper only after product entitlement is documented | Future source/product hash if terms allow | Future replay only after entitlement and retention boundary close | Not authorized; no product file retained | No public raw-data reproduction or redistribution | `NOT_AUTHORIZED_NO_SUBSCRIPTION_OR_CONSENT_EVIDENCE` | [TWSE T48 product](https://eshop.twse.com.tw/en/product/detail/000000006e0bbe8d016f1842c12f0342) |
| TPEx | Ex-rights/Ex-dividend Announcements | Cash dividend, stock dividend, rights/capital increase | Manual or bounded official date/code query and CSV export | Since 2008-12-15; covers window | Code, ex-right/ex-dividend date, cash/stock dividend reference fields, subscription fields when returned | Ex-right/ex-dividend date is primary; issuer announcement/publication date is separate; issuer detail takes precedence | Query limit not stated; no automated rate claim | TPEx terms expressly block automated devices/scripts/spiders/crawlers unless approved/consented | Conditional manual/bounded semantic capture | Preserve reference-vs-issuer precedence and nullable fields | Hash normalized row, export/response when permitted, URL, retrieval, source-as-of | Manual bounded manifest; replay requires same export or approved re-query | Retain only when the bounded method/terms permit | No public raw-data reproduction or redistribution | `MANUAL_OR_BOUNDED_QUERY_ONLY_AUTOMATED_EXTRACTION_BLOCKED` | [TPEx Ex-right Announcements](https://www.tpex.org.tw/en-us/announce/market/ex/announce.html) |
| TPEx | Ex-rights/Ex-dividend Calculation Result Sheet | Cash dividend, stock dividend, rights/capital increase | Manual or bounded official date-range query and CSV export | Since 2008-01-02; covers window | Opening reference price, ex-right/ex-dividend calculation result, tick-size-adjusted value, source date/code fields | Opening-reference-price effective trading date is primary; calculation query date is provenance | Query limit not stated; no automated rate claim | Automated extraction blocked by TPEx terms | Conditional manual/bounded semantic capture | Never treat reference quote as issuer fact; actual announcement precedence | Hash normalized row/export metadata | Manual checkpoint keyed by date/code/method | Retain only when the bounded method/terms permit | No public raw-data reproduction or redistribution | `MANUAL_OR_BOUNDED_QUERY_ONLY_AUTOMATED_EXTRACTION_BLOCKED` | [TPEx Calculation Result](https://www.tpex.org.tw/en-us/announce/market/ex/cal.html) |
| TPEx | Capital-reduction reference/announcement surfaces | Capital reduction | Manual or bounded official query/export | Official pages previously reviewed as available from 2013/01 for reference and 2015/12 for announcement; covers window | Reduction subtype, last/resume date, refund/loss coverage, ratios, reference price, code | Resume/reference-price effective date primary; last trading and announcement dates separate | Query limit not stated | Automated extraction blocked by TPEx terms | Conditional manual/bounded semantic capture | Require subtype/ratio/reference fields; unknown fails closed | Hash semantic row and source metadata | Manual checkpoint; no crawler replay | Retain only when the bounded method/terms permit | No public raw-data reproduction or redistribution | `MANUAL_OR_BOUNDED_QUERY_ONLY_AUTOMATED_EXTRACTION_BLOCKED` | [TPEx Reduction Reference](https://www.tpex.org.tw/en-us/announce/market/reduction/reference.html); [TPEx Reduction Announcements](https://www.tpex.org.tw/en-us/announce/market/reduction-tdr.html) |
| TPEx | Daily Stock Info / Daily Stock Quotes | Raw OHLCV boundary and identity/date verification | Manual or bounded official code/date query and CSV/UTF-8 export | Stock Info since 1994/01; Daily Quotes since 2007/01; covers window | Code, trading date, raw OHLC fields, volume, source record/date | Trading date is bar effective date; it is not announcement or corporate-action date | Query limit not stated | Automated extraction blocked by TPEx terms | Conditional manual/bounded semantic capture | Existing V2 daily-bar normalizer; no adjusted OHLC | Existing source URL/retrieved-at/content-hash pattern; CA semantic hash next task | Bounded export manifest; no automated replay claim | Retain only when the bounded method/terms permit | No public raw-data reproduction or redistribution | `MANUAL_OR_BOUNDED_QUERY_ONLY_AUTOMATED_EXTRACTION_BLOCKED` | [TPEx Daily Stock Info](https://www.tpex.org.tw/en-us/mainboard/trading/info/stock-pricing.html?code=8433); [TPEx Daily Quotes](https://www.tpex.org.tw/en-us/mainboard/trading/info/pricing.html) |

## Event Family Coverage

Only events that can contaminate raw-price/volume continuity, trigger logic, or
outcome labels are in the V0 scope.

| Event family | Coverage status | Official semantic closure | V0 action |
|---|---|---|---|
| Cash dividend / ex-dividend | `COVERED` | TWSE/TPEx event and calculation surfaces expose the effective ex-dividend date and relevant reference-price inputs/results; issuer precedence is retained where TPEx states it | Include an authoritative semantic event; exclude affected episodes by effective date |
| Stock dividend / ex-right | `COVERED` | Ex-right date, stock-dividend ratio, and reference-price fields are available on the official ex-right surfaces when returned | Include when required fields are present; missing ratio/reference authority fails closed |
| Rights issue / cash capital-increase reference-price reset | `COVERED` | Subscription price/ratio and ex-right/reference-price semantics are documented by both exchanges | Include reset event when official row is available; do not derive missing inputs from price |
| Capital reduction | `COVERED` | Official TWSE/TPEx reference-price pages distinguish reduction subtype, last/resume dates, refund/share ratio, and reference-price semantics | Include when subtype, effective date, identity, and required ratio/reference fields are authoritative |
| Stock split / reverse split / par-value change | `SEMANTIC_PARTIAL` | TWSE defines par-value ratio semantics, but a complete historical common-stock event/result/identity feed for all 507 identities is not established | Capture only authoritative complete rows; otherwise `CA_AUTHORITY_UNKNOWN` and exclude |
| Merger / share conversion / demerger / identity discontinuity | `SEMANTIC_PARTIAL` | Official announcement categories exist, but a normalized old/new identity mapping and effective trading-date corpus is not established | No successor invention; unresolved mapping fails closed for both affected identities |
| Listing / termination / resumption-related discontinuity | `SEMANTIC_PARTIAL` | Canonical `tw-reference-v1` contains the known TPE:6806 lifecycle event; complete event history for all 507 identities is not established | Use canonical lifecycle rows; unknown lifecycle/event coverage fails closed |

`SEMANTIC_PARTIAL` is sufficient for the next manual/bounded dataset task only
because the V0 contract treats unresolved rows as unknown and excludes them. It
does not authorize a claim of complete corporate-action coverage.

## Event Semantic Closure Matrix

The event key is centered on the trading/effective date that changes raw
price, volume comparability, or identity. Announcement/publication timing is
provenance and PIT metadata, not a substitute effective date.

| Event type | Primary effective-date field | Announcement/publication field | Reference-price field | Ratio/par fields | Identity effect | Price continuity | Volume continuity | Official source | Semantic status | PIT status | V0 action |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Cash dividend / ex-dividend | `ex_dividend_date` / official ex-date | Exchange or issuer announcement/publication date when available | `opening_reference_price` or official ex-dividend reference price; formula-only pages are not event rows | Cash dividend; stock/rights ratio if present | Same canonical identity unless another event says otherwise | Mechanical ex-date gap/reset can contaminate features and outcomes | Usually comparable only with event awareness; do not assume share-count neutrality for every product | TWSE TWT49U/T48; TPEx ex-right announcement/calculation | `COVERED` | Not used for Gate/Rank/Trigger; event announcement may be retained for later audit | `CA_EX_DIVIDEND` and episode exclusion when overlap occurs |
| Stock dividend / ex-right | `ex_right_date` / official ex-right date | Exchange or issuer announcement/publication date when available | Official opening ex-right/reference price | Stock dividend ratio; subscription ratio/price | Usually same identity; identity change still checked | Reference-price and share-count reset | Share-count/volume comparability can change | TWSE TWT48U/T48; TPEx ex-right announcement/calculation | `COVERED` | Trading decision use forbidden; PIT provenance retained only | `CA_EX_RIGHT` |
| Rights issue / capital increase reset | `ex_right_date` or reference-price effective trading date | Announcement/publication date | Official opening/reference price | Subscription price and new-share ratio required | Usually same identity; new-share listing date can be separate | Reference-price reset | Issuance changes comparability | TWSE TWT48U/T48; TPEx ex-right/calculation | `COVERED` | No retroactive decision use | `CA_CAPITAL_INCREASE_REFERENCE_RESET` |
| Capital reduction | Resume-trading/effective reference-price date | Capital-reduction announcement date | Post-reduction/reference price | Reduction subtype, refund, post/original share ratio, cash-injection terms | May alter continuity; identity must be confirmed | Large mechanical reset likely | Share count and trading boundary can change | TWSE reduction; TPEx reduction reference/announcement | `COVERED` | Only post-hoc integrity use in Core V0 | `CA_CAPITAL_REDUCTION` |
| Split / reverse split / par-value change | Official effective/change/resumption trading date | Announcement/publication date | Official reference price if supplied | Old/new par value and share ratio required | Same code is not enough to prove continuity | Proportional reset | Proportional volume reset | TWSE par-value page plus exchange announcements; TPEx official announcements | `SEMANTIC_PARTIAL` | Not PIT-safe until complete row and mapping exist | `CA_SPLIT_REVERSE_SPLIT` / `CA_PAR_VALUE_CHANGE` or `CA_AUTHORITY_UNKNOWN` |
| Merger / share conversion / demerger | Legal/trading identity-effective date plus termination/new-listing date | Announcement/publication date | Often null; reference price is not identity mapping | Exchange ratio and old/new identity required | Identity discontinuity | Continuity breaks by definition if mapping unresolved | Continuity and tradability may change | TWSE/TPEx official market/issuer announcement categories | `SEMANTIC_PARTIAL` | No historical trading decision rewrite | `CA_SHARE_CONVERSION` / fail closed |
| Listing / termination / resumption | Lifecycle effective date / last or first tradable date | Exchange/lifecycle announcement date | Nullable | Lifecycle status and identity required | Eligibility/tradability boundary | May terminate or reset continuity | Bars outside lifecycle are invalid for identity | Canonical lifecycle bundle plus official exchange lifecycle source | `SEMANTIC_PARTIAL` | Known dated lifecycle rows can gate research universe; unknown rows fail closed | `CA_LISTING_TERMINATION` |

## PIT Semantics

The current REC-A1 policy remains unchanged:

```text
TRADING_DECISION_USE=FORBIDDEN
GATE_RANK_TRIGGER_USE=NO_CORPORATE_ACTION_LOOKAHEAD
POST_HOC_OUTCOME_INTEGRITY_EXCLUSION=ALLOWED
UNKNOWN_EVENT_AUTHORITY=FAIL_CLOSED
```

An event announcement available before a signal date is not silently added to
the Core V0 trading gate, rank, or trigger. That would be a new event-aware
strategy version and is outside this task. The future dataset may preserve
announcement/publication date for a PIT audit, but it cannot change the frozen
signal decision after the fact.

After signal/trigger/execution facts are frozen, an event may be used in the
outcome-integrity audit by its actual effective date:

```text
feature dependency overlap     -> PRE_SIGNAL_FEATURE_CONTAMINATION
trigger-window overlap         -> TRIGGER_WINDOW_CONTAMINATION
execution/open overlap         -> EXECUTION_CONTAMINATION
entry-through-T+10/MFE/MAE     -> OUTCOME_CONTAMINATION
unknown/incomplete authority   -> CA_AUTHORITY_UNKNOWN / fail closed
```

An excluded episode is not a loss, no-trigger, or zero return. It is excluded
from T+5, T+10, MFE, MAE, win-rate, expectancy, and related outcome
denominators, while the original Gate/Rank/Trigger/Entry facts remain
unchanged.

## Acquisition Modes

### TWSE

1. Use the documented OpenAPI catalog only for endpoints explicitly present in
   that catalog. Do not treat the current `rwd` HTML-adjacent adapter path as
   permission to automate a new corporate-action crawler.
2. For historical ex-right and capital-reduction records, use a bounded
   operator-controlled query/export path from the official page when the
   documented OpenAPI route does not provide a historical result set.
3. Do not use the paid T48 product until subscription, permitted use, delivery
   method, retention, and reproduction terms are separately evidenced.
4. Use source-specific request budgets and stop on source errors or access
   changes. The repository rate limiter is an implementation guard, not proof
   of an exchange-approved rate.

### TPEx

1. Keep the official ex-right, calculation, reduction, and daily-query
   surfaces in `MANUAL_OR_BOUNDED_QUERY_ONLY` mode.
2. A human/operator may perform a bounded official query/export and provide a
   research artifact to the next task; no unattended crawler, spider, script,
   browser automation, bulk extractor, or anti-bot bypass is authorized.
3. A TPEx documented/paid API or download method can be added only after the
   product entitlement and written/approved method are evidenced.
4. If a query cannot be completed or a source returns an ambiguous/no-data
   response, record `UNKNOWN`; do not fill dates or assert no event.

### Minimum next-task ingestion boundary

```text
INGESTION_MODE=MANUAL_OR_BOUNDED_OFFICIAL_RESEARCH_V0
SOURCE_SCOPE=TWSE/TPEx official source records only
RAW_RESPONSE_STORAGE=ONLY_IF_SOURCE_TERMS_AND_PRODUCT_ENTITLEMENT_ALLOW
DEFAULT_ARTIFACT=REDUCED_SEMANTIC_EVENT_RECORD_PLUS_LINEAGE_AND_HASH
AUTOMATED_PRODUCTION_PIPELINE=NOT_AUTHORIZED
SCHEDULER=NOT_AUTHORIZED
```

## Research Window Coverage

The date-range evidence is sufficient to authorize implementation in bounded
mode, with explicit coverage limitations:

| Coverage question | Result |
|---|---|
| Does the 2026-02-02 to 2026-08-13 window fall inside the stated TWSE ex-right historical range? | Yes; TWT49U states since 2003-05-05 |
| Does the window fall inside the stated TWSE capital-reduction range? | Yes; the official page states since 2011-01-01 |
| Does the window fall inside the stated TPEx ex-right announcement range? | Yes; the official page states since 2008-12-15 |
| Does the window fall inside the stated TPEx calculation range? | Yes; the official page states since 2008-01-02 |
| Does the window fall inside the reviewed TPEx capital-reduction ranges? | Yes; prior official review records 2013/01 reference and 2015/12 announcement availability |
| Can the repository prove a complete, immutable event row for every 507 identity and every event family? | No |
| Can an implementation represent query/export gaps deterministically? | Yes; `UNKNOWN` / `CA_AUTHORITY_UNKNOWN` fail closed |
| May an absent row be interpreted as no event? | No |

Precise gaps carried into the next implementation are:

1. Public interactive result surfaces are not a repository-held historical
   snapshot and may reflect later corrections.
2. The TWSE OpenAPI catalog documents `TWT48U_ALL`, but the reviewed catalog
   does not state a complete historical range for that endpoint.
3. The richer TWSE T48 product has useful fields and a historical start date,
   but no TopicPilot subscription/consent evidence is present.
4. TPEx public pages cover the date window but cannot be unattended-extracted
   under the reviewed terms.
5. Split/par-value, merger/conversion, and complete lifecycle identity
   histories are not normalized for the 507 identities.

These are deterministic fail-closed gaps, not claims that the window contains
no events.

```text
HISTORICAL_WINDOW_COVERAGE=DATE_RANGE_SURFACES_COVER_WINDOW_WITH_DETERMINISTIC_UNKNOWN_GAPS
HISTORICAL_WINDOW_COMPLETENESS=NOT_PROVEN
ABSENT_RESULT_MEANING=UNKNOWN_NOT_NO_EVENT
```

## Identity and Lifecycle Mapping

The canonical identity authority is the hashed `tw-reference-v1` bundle:

```text
IDENTITY_KEY=MARKET_CODE:INSTRUMENT_CODE
IDENTITY_UNIVERSE=507_PHYSICAL_EQUITY_IDENTITIES
REFERENCE_VERSION=tw-reference-v1
LIFECYCLE_POLICY=LIFECYCLE_GATED_507
KNOWN_LIFECYCLE=TPE:6806 effective_from 2026-06-23 status DELISTED
```

Mapping rules for the next task:

- A source security code is not accepted without the exchange/market context.
- Same-code events retain the canonical identity only after code, market, and
  effective date validate against the reference context.
- Merger, conversion, demerger, split, and par-value events require explicit
  old/new identity or ratio evidence. A successor is never inferred from a
  name, price, or nearest code.
- Unknown identity mapping excludes the affected episode and reports
  `CA_AUTHORITY_UNKNOWN` or `CA_SHARE_CONVERSION`.
- The known 6806 lifecycle boundary is reusable for research universe gating,
  but it is not evidence of complete corporate-action coverage.

```text
IDENTITY_MAPPING_STATE=CANONICAL_507_PLUS_KNOWN_6806_LIFECYCLE;DISCONTINUITY_FAMILIES_FAIL_CLOSED
SURVIVORSHIP_SAFE_CLAIM=NO
```

## Lineage, Hash, and Replay Boundary

Current repository patterns are sufficient for the next small research
artifact, but the corporate-action dataset itself is not implemented here.
The next task must retain at least:

```text
source_name
official_product_or_surface
access_method
source_url
source_record_id_or_canonical_row_key
security_identity
event_type
announcement_date_if_available
primary_effective_date
reference_price_if_officially_returned
source_as_of_if_available
retrieved_at
source_content_hash_if_storage_permitted
normalized_semantic_hash
semantic_version
authority_state
query_or_export_manifest_id
checkpoint_id
```

The existing V2 patterns are reusable as boundaries:

- `services/api/src/topicpilot_api/market_data/ingestion.py` already uses a
  deterministic request key, transaction-owned ingestion, raw/timeline hashes,
  and idempotent reuse.
- `services/api/src/topicpilot_api/market_data/lineage.py` provides
  secret-free official-provider lineage.
- `services/api/src/topicpilot_api/market_data/rate_limit.py` provides a
  bounded request budget and retry boundary, but it does not grant source
  permission.
- `services/api/src/topicpilot_api/normalizer/historical.py` preserves
  nullable fields and `adjustment_state=UNKNOWN`; it does not create adjusted
  OHLC or corporate-action rows.
- `tw-reference-v1` is versioned and hashed, with one canonical 6806 lifecycle
  event and an adjustment catalogue containing `ADJUSTED`, `UNADJUSTED`, and
  `UNKNOWN`; the catalogue does not assign an adjustment state to HIST-002B.

Replay is authorized only for the next bounded research artifact and only
when the same source method, export/manifest identity, semantic version, and
lineage inputs are available. A replay that cannot reproduce the source
record or source-as-of boundary must fail closed.

```text
HASH_LINEAGE_REPLAY_STATUS=READY_BOUNDARY_NOT_IMPLEMENTED
LOCAL_RESEARCH_STORAGE_STATUS=CONDITIONALLY_ALLOWED_SOURCE_TERMS_AND_METHOD_DEPENDENT
```

## Raw Reproduction and Redistribution Boundary

```text
RAW_REPRODUCTION_STATUS=NOT_APPROVED
PUBLIC_REDISTRIBUTION_STATUS=NOT_APPROVED
RAW_OFFICIAL_RESPONSE_STORED_IN_THIS_TASK=NO
PUBLIC_DOWNLOAD_ARTIFACT_CREATED=NO
```

The next implementation should default to a reduced semantic event artifact
with URL, retrieval/source-as-of metadata, hashes, and attribution. It must
not retain or publish a bulk raw response unless the exact official product
terms and delivery method permit that retention and use. Internal Owner
approval does not override TWSE/TPEx restrictions.

## Control Cases

### TWSE 2330 ex-dividend

The official [TWSE 2026-06-10 notice](https://wwwc.twse.com.tw/staticFiles/news/news/tsecnews/8a8216d69e6379f4019eb0d0cfa601e0.pdf)
identifies `2330` among the securities with an ex-dividend date of
`2026-06-11`. The canonical predecessor closure maps the source record to
`TPE:2330`, the effective date to the surrounding OHLCV boundary, and the
affected episode to `CA_EX_DIVIDEND` rather than a trading signal.

```text
SOURCE_RECORD=TWSE_OFFICIAL_NOTICE_2026-06-10
IDENTITY=TPE:2330
ANNOUNCEMENT_DATE=2026-06-10
PRIMARY_EFFECTIVE_DATE=2026-06-11
RAW_OHLC_BOUNDARY=CANONICAL_HIST_002B_READ_ONLY_EVIDENCE
REASON_CODE=CA_EX_DIVIDEND
EPISODE_RESULT=EVENT_EXCLUDED_RAW_V0
CONTROL_TWSE_2330_EX_DIVIDEND=PASS
```

### TPE 6806 termination

The canonical `tw-reference-v1` lifecycle row records `TPE:6806` as
`DELISTED` with `effective_from=2026-06-23` and the official TWSE lifecycle
source URL. The HIST-002B closure records the last OHLCV bar on `2026-06-22`
and zero rows on or after the effective date.

```text
SOURCE_RECORD=TWSE-DELISTED-6806-20260623
IDENTITY=TPE:6806
PRIMARY_EFFECTIVE_DATE=2026-06-23
LAST_RAW_OHLC_DATE=2026-06-22
POST_EFFECTIVE_OHLCV_ROWS=0
REASON_CODE=CA_LISTING_TERMINATION
EPISODE_RESULT=LIFECYCLE_BOUNDARY_EXCLUSION
CONTROL_TPE_6806_TERMINATION=PASS
```

### Semantic fixtures

The predecessor closure's six non-persisted semantic controls remain
reconciled:

```text
feature-window event       -> PRE_SIGNAL_FEATURE_CONTAMINATION
trigger-window event       -> TRIGGER_WINDOW_CONTAMINATION
execution-date event       -> EXECUTION_CONTAMINATION
outcome-window event       -> OUTCOME_CONTAMINATION
complete empty set         -> PASS_NO_EVENT
unknown/incomplete source  -> CA_AUTHORITY_UNKNOWN / fail closed
SEMANTIC_FIXTURE_ASSERTIONS=6_PASS
```

No new capital-reduction or split example was invented. A real example may be
added in the dataset implementation only when its official source row,
identity, effective date, and required ratio/reference fields are captured by
an approved method.

## Dataset Implementation Authorization Gate

| Gate | Decision | Evidence/boundary |
|---|---|---|
| 1. Owner internal research approval | `YES` | Explicit `OWNER_DECISION=APPROVED_INTERNAL_RESEARCH_ONLY` in this task input and record |
| 2. At least one source-specific path respects official limits | `YES` | TWSE documented OpenAPI candidate; TWSE/TPEx manual/bounded official query/export; TPEx automation remains blocked |
| 3. Historical coverage is sufficient or gaps are deterministic | `YES_WITH_FAIL_CLOSED_LIMITATION` | Official stated ranges cover the research window; completeness is not claimed; unresolved gaps are `UNKNOWN` and cannot be filled |
| 4. Effective-date semantics are deterministic | `YES_FOR_CORE_FAMILIES` | Ex-date, ex-right date, resume/reference-price effective date, and lifecycle effective date are separate fields; partial families fail closed |
| 5. Identity mapping aligns with canonical 507/lifecycle authority | `YES_WITH_DISCONTINUITY_LIMITATION` | `tw-reference-v1` and known 6806 lifecycle align; old/new identity mapping is required for conversion/split cases |
| 6. Lineage/hash/replay metadata can be preserved | `YES_FOR_NEXT_IMPLEMENTATION` | Existing V2 request-key, hash, lineage, normalization, and checkpoint patterns are reusable; no CA dataset exists yet |
| 7. Raw official data does not need external reproduction | `YES` | Next task can use reduced semantic records; public redistribution is not approved |

The combined result is:

```text
DATASET_IMPLEMENTATION_AUTHORIZED=YES
AUTHORIZED_INGESTION_MODE=MANUAL_OR_BOUNDED_OFFICIAL_RESEARCH_V0
```

The authorization is intentionally narrower than a fully automated or
complete event archive. If the next task requires unattended TPEx extraction,
paid T48/TPEX product use, or a full historical identity-continuity archive,
it must stop at the corresponding external method/entitlement gate.

## Remaining External Approval and Method Constraints

There is no remaining Owner-approval blocker for this bounded implementation.
The minimum remaining constraints are external/method-specific:

1. Do not automate TPEx public surfaces without a TPEx-approved method or
   consent.
2. Do not use TWSE T48 or TPEx E-Shop products without documented
   subscription/entitlement and retention/reproduction terms.
3. Do not treat the documented TWSE OpenAPI catalog as permission to automate
   undocumented website routes or to bypass request controls.
4. Do not claim complete historical event coverage from a public query page;
   store query/export manifests and mark unresolved records `UNKNOWN`.
5. Do not create adjusted OHLC, total-return, or price-rewritten series.

```text
REMAINING_BLOCKER_FOR_MANUAL_BOUNDED_DATASET=NONE
REMAINING_CONSTRAINT_FOR_AUTOMATED_TPEX=EXTERNAL_APPROVED_METHOD_OR_CONSENT_REQUIRED
REMAINING_CONSTRAINT_FOR_PAID_PRODUCTS=SUBSCRIPTION_AND_TERMS_EVIDENCE_REQUIRED
```

## Freeze Gate

Even though the implementation gate is `YES`, the downstream freeze gates remain
closed:

```text
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO_UNTIL_DATASET_IMPLEMENTED_AND_VALIDATED
REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO
```

The next task must build and validate the minimal research artifact first. It
must not run a full A1 backtest, walk-forward, parameter search, or Production
mutation in the same task.

## Impact Validation

This closure changed only the new report file. It did not modify application
code, database schema/data, historical OHLCV, recommendation logic, scheduler,
deployment, or protected gate inputs.

```text
OFFICIAL_EVIDENCE_REVIEW=PASS_2026-08-15
CANONICAL_REPO_STATE_INSPECTION=PASS
PRIOR_AUTHORITY_RECONCILIATION=PASS
SOURCE_METHOD_MATRIX_REVIEW=PASS
EVENT_SEMANTIC_MATRIX_REVIEW=PASS
CONTROL_2330=PASS_FROM_OFFICIAL_NOTICE_AND_CANONICAL_CLOSURE
CONTROL_6806=PASS_FROM_REFERENCE_BUNDLE_AND_HIST_002B_CLOSURE
SEMANTIC_FIXTURE_6=PASS_PRESERVED_FROM_PRIOR_CLOSURE
UNKNOWN_FAIL_CLOSED=PASS
DB_REQUERY=NOT_RUN_DATABASE_URL_UNSET; PRIOR_SELECT_ONLY_CANONICAL_EVIDENCE_RECONCILED
FULL_A1_BACKTEST=NOT_RUN
WALK_FORWARD=NOT_RUN
PARAMETER_SEARCH=NOT_RUN
G1=PRESERVED PASS
G2=PRESERVED PASS
G3=PRESERVED PASS
POST_CLOSE_CANARY=PRESERVED PASS
```

The protected gates were preserved because this report did not change the
reference registry, official historical OHLCV, provider runtime, market/no-
trade semantics, post-close writer, persistence, or Production state.

## Documentation Reconciliation

Only the exact report write set was used:

```text
REPORT_CREATED=YES
DAILY_PROGRESS_UPDATED=NO
PROJECT_CONTEXT_UPDATED=NO
ROADMAP_UPDATED=NO
PRODUCT_ROADMAP_UPDATED=NO
WORK_ORDERS_UPDATED=NO
DOCUMENTATION_INDEX_UPDATED=NO
OWNER_DOCUMENTS_UPDATED=NO
```

The owner documents were read as current authority but deliberately not
modified because parallel work already owns dirty sections and this task is a
governance closure, not a product-capability milestone.

## Final Handoff

```text
TASK_ID=TASK-REC-A1-CORPORATE-ACTION-SOURCE-USE-APPROVAL-AND-HISTORICAL-EVENT-SEMANTICS-CLOSURE
FINAL_STATUS=REC_A1_CORPORATE_ACTION_SOURCE_METHOD_AND_EVENT_SEMANTICS_READY_FOR_RESEARCH_DATASET_IMPLEMENTATION
CANONICAL_PRE_SHA=c2a8b2e98f7c96499cce271b81c676b214183df0
CANONICAL_POST_SHA=LOCAL_TASK_COMMIT_SHA_REPORTED_AT_HANDOFF
ORIGIN_MAIN=26f635b95d8d88fd7ed7e43949583347f3ab5feb
WORKTREE_USED=NO
OWNER_DECISION=APPROVED_INTERNAL_RESEARCH_ONLY
OWNER_APPROVAL_STATUS=APPROVED_INTERNAL_RESEARCH_ONLY
TWSE_SOURCE_METHOD_STATUS=CONDITIONALLY_CLOSED_DOCUMENTED_OPENAPI_PLUS_MANUAL_BOUNDED_QUERY;PAID_T48_NOT_AUTHORIZED
TPEX_SOURCE_METHOD_STATUS=MANUAL_BOUNDED_ONLY;PAID_PRODUCTS_NOT_AUTHORIZED
AUTOMATED_EXTRACTION_STATUS_TWSE=ALLOWED_ONLY_FOR_OFFICIAL_DOCUMENTED_OPENAPI_ENDPOINTS;WEBSITE_AND_ESHOP_AUTOMATION_BLOCKED
AUTOMATED_EXTRACTION_STATUS_TPEX=AUTOMATED_EXTRACTION_BLOCKED_UNLESS_APPROVED_METHOD_OR_CONSENT
MANUAL_BOUNDED_INGESTION_STATUS=AUTHORIZED_FOR_RESEARCH_V0_WITH_LINEAGE_AND_FAIL_CLOSED_GAPS
LOCAL_RESEARCH_STORAGE_STATUS=CONDITIONALLY_ALLOWED_SOURCE_TERMS_AND_METHOD_DEPENDENT
HASH_LINEAGE_REPLAY_STATUS=READY_BOUNDARY_NOT_IMPLEMENTED
RAW_REPRODUCTION_STATUS=NOT_APPROVED
PUBLIC_REDISTRIBUTION_STATUS=NOT_APPROVED
COVERED_EVENT_FAMILIES=CASH_DIVIDEND_EX_DIVIDEND;STOCK_DIVIDEND_EX_RIGHT;RIGHTS_ISSUE_CAPITAL_INCREASE_REFERENCE_RESET;CAPITAL_REDUCTION
SEMANTIC_PARTIAL_EVENT_FAMILIES=SPLIT_REVERSE_SPLIT_PAR_VALUE_CHANGE;MERGER_SHARE_CONVERSION_DEMERGER;LISTING_TERMINATION_RESUMPTION_DISCONTINUITY
HISTORICAL_WINDOW_COVERAGE=2026-02-02_TO_2026-08-13_DATE_RANGE_SURFACES_COVER_WITH_DETERMINISTIC_UNKNOWN_GAPS
EVENT_DATE_SEMANTICS=DETERMINISTIC_CORE_EFFECTIVE_DATE_SEPARATE_FROM_ANNOUNCEMENT_AND_REFERENCE_PRICE_DATE
PIT_SEMANTICS=TRADING_DECISION_USE_FORBIDDEN;POST_HOC_OUTCOME_INTEGRITY_EXCLUSION_ALLOWED
IDENTITY_MAPPING_STATE=CANONICAL_507_PLUS_KNOWN_6806_LIFECYCLE;DISCONTINUITY_FAMILIES_FAIL_CLOSED
REFERENCE_PRICE_AUTHORITY=DETERMINISTIC_FOR_CORE_EX_RIGHT_AND_CAPITAL_REDUCTION;PARTIAL_FOR_SPLIT_PAR_VALUE_IDENTITY_DISCONTINUITY
CONTROL_CASES=2330_EX_DIVIDEND_PASS;6806_TERMINATION_PASS;SEMANTIC_FIXTURE_6_PASS;UNKNOWN_FAIL_CLOSED_PASS
UNKNOWN_FAIL_CLOSED=YES
EVENT_EXCLUDED_RAW_POLICY=READY
TRADING_DECISION_USE=FORBIDDEN
POST_HOC_OUTCOME_INTEGRITY_EXCLUSION=ALLOWED
DATASET_IMPLEMENTATION_AUTHORIZED=YES
AUTHORIZED_INGESTION_MODE=MANUAL_OR_BOUNDED_OFFICIAL_RESEARCH_V0
NEXT_RECOMMENDED_TASK=TASK-REC-A1-CORPORATE-ACTION-RESEARCH-DATASET-IMPLEMENTATION
REC_A1_DATASET_PROTOCOL_FREEZE_AUTHORIZED=NO_UNTIL_DATASET_IMPLEMENTED_AND_VALIDATED
REC_A1_CORE_V0_WALK_FORWARD_AUTHORIZED=NO
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

The task stops here. It authorizes the next minimal research-only dataset
implementation and does not implement that dataset, freeze the protocol, or
run REC-A1.
