# Today／今日市場 Commercial Investor Redesign

## Closure status

`TODAY_COMMERCIAL_REDESIGN_STATUS=BLOCKED`

The Today commercial investor-first redesign is implemented, tested, pushed, and the Sites frontend is live. The task cannot be marked closed because the protected Render API deploy hooks accepted the exact release revisions, while the public API continued serving the pre-existing runtime revision `51dbe48db203adb56e5fbc47da2f44b0e33997d2`. Production API/UI parity and production release readback therefore remain blocked. No fabricated production values were introduced.

## Exact source state

- `EXACT_SHA_BEFORE=08cd08a894859d1da03f434ed562b1740d4d6108`
- Commercial UI source commit: `8e0c0afc1d9c50d389c1a5c1ac931470c6f75f57`
- Mobile containment fix: `3d152a8bb48c2a8780f0721fe3a52a0226e9c3e8`
- Mobile highlights wrapping fix: `387490617ca8921ed4cb5cd40a98f9cdafbb9eee`
- API read normalization commit on the preserved working branch: `a7c88a4`
- Pushed clean API release revision: `f931593938c4190daf9ceb41043c46ef0511ae37`
- `EXACT_SHA_AFTER_SOURCE_RELEASE=f931593938c4190daf9ceb41043c46ef0511ae37`
- GitHub branch: `codex/today-commercial-investor-release-20260912`
- GitHub workflow run: `34708154987` — validation passed; API hook job `103591902900` passed.
- Render hook accepted deployment id: `dep-daiolt8ae00c73fc4a50`.

The working repository kept owner/parallel dirty changes out of the release snapshot. No reset, clean, stash, or checkout-overwrite operation was used.

## Capability matrix

| Capability | Authority result | Evidence / production behavior |
|---|---|---|
| TAIEX close, change points, change percent | `FORMAL_AVAILABLE` | Typed official index facts in `market_data/index_contract.py`; source exposes TPE close/change/change percent. |
| TPEx close, change points, change percent | `FORMAL_PARTIAL` | Typed official facts expose close/change; current formal row has `previousClose=null`, so change percent is truthfully unavailable. |
| TWSE / TPEx / total turnover | `FORMAL_PARTIAL` | Typed `MarketTurnoverFact` and official adapters; TPE and TWO values are exposed with units/scale. |
| Previous-session turnover comparison | `NOT_FORMAL` | No published previous-session comparison contract; UI omits it. |
| Advance / decline / unchanged | `FORMAL_AVAILABLE` | Server aggregation from active, date-effective EQUITY observations in `vw_daily_market_observations`; legal no-quote states are excluded from price direction. |
| EOD percent-change distribution | `FORMAL_AVAILABLE` | Server-owned mutually exclusive buckets, reconciliation and exclusion accounting in `home_v2_publication.py`; frontend does not aggregate. |
| Limit-up / limit-down semantics | `NOT_FORMAL` | No limit-status authority was found. Labels are percentage ranges with “未確認漲停／未確認跌停”; no threshold guessing. |
| Current Topic snapshot | `FORMAL_AVAILABLE` | Published `topic_snapshots` rows only; maximum three deterministic topic cards. |
| Topic historical comparison / rank delta | `FORMAL_PARTIAL` | Formal history supports deterministic 14-session rotation only; no rank arrows or historical delta are invented. |
| Heating / Cooling | `FORMAL_PARTIAL` | Uses the formal 14-trading-session contract; when history is insufficient the UI shows the existing concise unavailable state. |
| Today Opportunities | `NOT_FORMAL` | Opportunity authority remains unpublished; UI is a CTA with truthful unavailable state and no candidate counts or stock list. |

## Implemented information architecture

The source order is: market overview → EOD percent distribution and breadth → deterministic market highlights → formal Topic mainline cards → EOD Topic ticker → formal 14-session heating/cooling → Opportunity CTA. The redesign removes primary-view developer counters, provider/debug details, mockup counts, intraday curves, LLM market narration, and unsupported ranking arrows.

Backend changes are limited to the formal Today publication/read contract:

- `HomeMarketDistribution` schema and generated API client/OpenAPI parity.
- Canonical EOD aggregation with active/date-effective universe, eligible and excluded counts, no-quote handling, and bucket reconciliation.
- Deterministic market-highlight presenter based only on index, breadth and supported divergence facts.
- Read-time normalization that rebuilds persisted Daily Focus from stored market facts when an older V2 row still contains legacy narrative content.

Frontend changes are in `TodayMarketPage.tsx`, `today-market-fields.ts`, and the shared Today styles. The ticker is explicitly EOD, uses only current formal Topic facts, runs at approximately 42 seconds per cycle, pauses on hover/control, stops for reduced motion, and remains swipeable on mobile.

## Verification

| Check | Result |
|---|---|
| Focused Home publication tests | `PASS` — 10 passed, including boundaries, reconciliation, no-quote exclusion, fail-closed transport behavior, deterministic focus, and persisted-read normalization. |
| Backend Ruff on touched source/tests | `PASS` — all checks passed. |
| Backend compile | `PASS` with bundled Python 3.12 runtime. |
| Full backend compatibility suite | `636 passed, 8 failed, 59 skipped, 84 deselected, 1 warning`; failures are pre-existing repository/database-baseline drift outside this write-set (migration head, instrument/topic fixture totals, compatibility path, and architecture-freeze expectations). PostgreSQL integration cases were skipped because no test database URL was available. |
| API client generation/check | `PASS`; OpenAPI, generated declarations and client parity checked. |
| API client tests | `PASS` — 4 passed. |
| Frontend focused lint | `PASS` for touched Today files. |
| Frontend TypeScript | `PASS` — `tsc --noEmit`. |
| Frontend production build | `PASS`. |
| Frontend focused/full tests | `PASS` — clean release tree 204 passed; the original working tree had 207 passed. |
| `git diff --check` | `PASS`; generated OpenAPI line-ending normalization was the only expected formatting note. |
| A10 schedule | `PASS` — no scheduler change; `POST_CLOSE` target remains 13:35 Asia/Taipei. Worker was not deployed. |
| C-drive artifacts | `C_DRIVE_ARTIFACTS_CREATED=0`; all workspace, temporary, build, test, browser, cache and report paths used were on E:. |

## Sites production evidence

- Project: `appgprj_6a6ce02bd75c81919ab3678ebf013c53`
- Live URL: https://topicpilot-platform.game0962046460.chatgpt.site
- Version: `46`
- Site source commit: `eab4b664bb8bba6039e47ae558ca90f1293b6b5d`
- Deployment: `appgdep_6aa57fda7ae08191b6d591991618b55f`
- Deployment status: `succeeded`
- Audience remained public.

Browser readback at 1280×800 and 390×844 confirmed the new page order, visible EOD labels, truthful unavailable states, working navigation links including `/opportunities`, no mockup values (`24,612.38`, `4,382`, `8 檔`), no developer flooding (`trackedStockCount`, `provider`, `debug`), and no page-level horizontal overflow. Measured widths were 1265px at the 1280px viewport and 375px at the 390px viewport.

Evidence files:

- `work/today-final-desktop-1280x800-20260913.png`
- `work/today-final-mobile-390x844-20260913.png`

The screenshots still show the old production API Daily Focus line because the Render API had not switched to the new backend revision at capture time. That is recorded as a blocker, not presented as a successful backend release.

## Production API readback and blocker

At the final readback, the public API returned:

- `/healthz`: `{"status":"ok","gitSha":"51dbe48db203adb56e5fbc47da2f44b0e33997d2"}`
- `/api/v2/home`: `contractVersion=v2.home-read-model.v2`, `asOf=2026-09-09`
- TAIEX: `47183.36`, change `+77.58`, `+0.16%`
- TPEx: `408.09`, change `+0.9`, change percent unavailable because `previousClose=null`
- Turnover: TPE `766870784582` TWD; TWO `217296892663` TWD
- Breadth: advance `999`, decline `742`, flat `196`
- Distribution: `null` / unavailable in the stale persisted payload
- Heating/cooling: unavailable with `INSUFFICIENT_ROTATION_HISTORY`
- Opportunities: unavailable with `OPTIONAL_SECTION_NOT_FORMAL`
- Daily Focus still included the legacy `目前主線為 網通。` line, proving the live service had not received `f931593938c4190daf9ceb41043c46ef0511ae37`.

Two protected API hook attempts were accepted and then read back without a live revision change:

1. workflow `34707477662`, release `34f16bcebed503d7284fd172005480abaa665fd8`, accepted deploy `dep-daiofjoae00c73fbee70`;
2. workflow `34708154987`, release `f931593938c4190daf9ceb41043c46ef0511ae37`, accepted deploy `dep-daiolt8ae00c73fc4a50`.

The exact external action required to continue is Render control-plane verification/reconciliation of the protected deploy hook/service. Until `/healthz` reports the release revision and `/api/v2/home` no longer returns the legacy Daily Focus content, the following gates remain blocked:

- `PRODUCTION_API_UI_PARITY`
- `NO_LEGACY_FORMAL_FALLBACK` in live production
- `PRODUCTION_RELEASE_READBACK`
- `TODAY_COMMERCIAL_REDESIGN_STATUS=CLOSED`

## Hard-gate ledger

| Gate | Result |
|---|---|
| `TODAY_INVESTOR_FIRST_IA` | `PASS` |
| `TAIEX_DISPLAY` | `PASS` |
| `OTC_DISPLAY` | `PASS_OR_TRUTHFUL_UNAVAILABLE` |
| `TURNOVER_DISPLAY` | `PASS_OR_TRUTHFUL_UNAVAILABLE` |
| `BREADTH_DISTRIBUTION_FORMAL` | `PASS` in source contract; live row truthful-unavailable pending API revision |
| `BREADTH_RECONCILIATION` | `PASS` |
| `SUSPENDED_NO_QUOTE_DOES_NOT_BLOCK_MARKET_PUBLICATION` | `PASS` |
| `NO_FAKE_LIMIT_UP_DOWN_CLASSIFICATION` | `PASS` |
| `MARKET_HIGHLIGHTS_DETERMINISTIC` | `PASS` in source; live API blocked on stale row |
| `NO_LLM_MARKET_NARRATIVE` | `PASS` in source; live API blocked on stale row |
| `TOPIC_MAINLINE_TRUTHFUL` | `PASS` |
| `TOPIC_TICKER_EOD_NOT_INTRADAY` | `PASS` |
| `HEATING_COOLING_TRUTHFUL` | `PASS_OR_TRUTHFUL_UNAVAILABLE` |
| `OPPORTUNITY_SUMMARY_TRUTHFUL` | `PASS_OR_TRUTHFUL_UNAVAILABLE` |
| `NO_MOCKUP_VALUES_IN_PRODUCTION` | `PASS` |
| `NO_LEGACY_FORMAL_FALLBACK` | `BLOCKED` — live API stale |
| `COMMERCIAL_STATE_SEMANTICS` | `PASS` in source; live API readback blocked |
| `DESKTOP_BROWSER_SMOKE` | `PASS_WITH_STALE_API_BLOCKER` |
| `MOBILE_BROWSER_SMOKE` | `PASS_WITH_STALE_API_BLOCKER` |
| `PRODUCTION_API_UI_PARITY` | `BLOCKED` |
| `PRODUCTION_RELEASE_READBACK` | `BLOCKED` |
| `A10_SCHEDULE_UNCHANGED_13_35` | `PASS` |
| `C_DRIVE_ARTIFACTS_CREATED` | `0` |
| `TODAY_COMMERCIAL_REDESIGN_STATUS` | `BLOCKED` |

## Preserved owner/parallel dirty state

The following state was intentionally not staged, rewritten, or absorbed. Hashes are the final working-tree blob hashes where applicable.

| Path | Hash / state |
|---|---|
| `apps/web/app/components/v2/TopicDetailPage.tsx` | `2e0b33d5c2ff45f2aa817ce04f6f10a1532b9aa2` |
| `apps/web/app/lib/today-mainlines.ts` | `364940e6578779ec3c806f345cd732409bc72ed0` |
| `apps/web/app/lib/topic-api.ts` | `0451eeaf76957a3482f6c344cf26b89937550f19` |
| `compose.yaml` | `b0ca993dbd2458647250288593b48c0bd3ceaece` |
| `docs/operations/deployment.md` | `89869ab38e93711c81356a827a3c37fe06f98995` |
| `packages/api-client/src/client.d.mts` | `913de3312cad3a884e05386f80ca80d0edf10697` |
| `packages/api-client/src/client.mjs` | `9990c2e4a625ab8a2a15428d4c30fc802d8ba01c` |
| `render.yaml` | `9890d4412f02919b0a890e581434efac69987898` |
| `services/api/.env.example` | `32883b5e26d35e659f3c77e87464d920c1ea3ef7` |
| `services/api/src/topicpilot_api/live/cli.py` | `22e1671c84ce5a5a1827457a5f42bb1f33cf154c` |
| `services/api/src/topicpilot_api/live/config.py` | `f17881b17802e955c12404fb15f3dca24074dad0` |
| `services/api/src/topicpilot_api/live/post_close.py` | `597014bda109ee18e02e0565d3bbe6fa4175c96c` |
| `services/api/src/topicpilot_api/live/scheduler.py` | `025386eeeaef44defe336f54a6f81088e370d8fd` |
| `services/api/tests/test_live_runtime.py` | `90320a4aaa499fee5e0a4dd87e1d183524e512d8` |
| `apps/web/app/lib/formal-topic-snapshot.ts` | `c7f4555abf55b73a9fe42f0eca133ea98625e308` |
| `apps/web/tests/formal-topic-snapshot.test.mjs` | `298a605b5c0a1683fc1379e9403d2f651b0775eb` |
| `services/api/src/topicpilot_api/live/daily_forward.py` | `2d8c1646dbb8a7260ba688ca0587cf647e67ec55` |
| `services/api/tests/test_daily_forward.py` | `6cc21c2ccc0f277b23301828fc5dadddd975fce0` |
| `tools/ws4_bounded_eod_catchup.py` | `dfd458d1fd73aee56f5b0692b4fe82b2fbff38a5` |
| `tools/ws4_formal_eod_publication.py` | `547e6d5b8db22168e2f4d9119288b011a31df162` |
| `reports/TASK-SOURCE-WORKSPACE-HYGIENE-DIRTY-STATE-CLASSIFICATION-CLOSURE-20260831/` | preserved directory; files remain untracked and unchanged |

The report itself is the final bounded-task artifact; work stops here pending external Render control-plane reconciliation.
