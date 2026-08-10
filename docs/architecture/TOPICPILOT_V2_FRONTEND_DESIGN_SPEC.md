# TopicPilot V2 Frontend Design Specification / UX-UI Blueprint

**Status:** `PM-FROZEN / VISUAL PROTOTYPE REVIEW PENDING`  
**Scope:** customer-facing desktop-first frontend design; documentation only  
**Authority:** constrained by the [Product Direction and Surfaces Contract](PRODUCT_SURFACES_AND_UX_CONTRACT.md). That contract remains authoritative for product positioning, semantic boundaries, and engine responsibilities.  
**No authorization:** this document does not authorize frontend implementation, API changes, schema changes, scoring changes, or production activation.

## 1. Executive summary

TopicPilot is a Taiwan market-theme intelligence workspace for retail investors with some investing experience. Its job is to make the market easier to read: what is happening today, which themes are strengthening or weakening, which stocks belong to those themes, and which items deserve further research.

The V2 customer flow is:

```text
市場 → 題材 → 股票 → 機會／收藏 → 深度研究
```

The first frontend blueprint is desktop-first, light-mode-first, intraday-first, and explanation-led. It should feel like a calm, durable research workspace: professional underneath, retail-friendly in expression. The home page is a market navigation surface, not a data dump or recommendation dashboard.

### Decision status legend

- **FROZEN / CURRENT DECISION** — record as the current product direction.
- **PROVISIONAL / TO REVIEW** — direction is useful for design, but PM may change it.
- **DEFERRED / FUTURE** — keep the concept visible without blocking V1.
- **API/data dependency to verify** — UI concept requires a currently unverified contract or field.

## 2. Product positioning

### FROZEN / CURRENT DECISION

- TopicPilot is not a generic stock screener, broker terminal, news homepage, or AI-showcase dashboard.
- Primary users are Taiwan retail investors with some investing experience, not professional institutional traders.
- Promise: help users quickly understand what the Taiwan market is trading today, which themes are strengthening or weakening, and where to continue research.
- Product flow: Market → Topic → Stock → Opportunity / Collection → Deep Research.
- Home principle: **首頁不是資料入口，而是市場導航。**
- Design principle: **專業 backend、散戶友善 expression.**
- Topic Intelligence is the product capability; Recommendation is downstream decision support, never an imperative trading instruction.

## 3. Information architecture and navigation

### FROZEN / CURRENT DECISION

Desktop V1 primary navigation:

```text
今日市場   題材   股票   收藏   機會   AI研究室
```

Top-right global utilities:

```text
全域搜尋   通知   帳號
```

Secondary or hidden surfaces:

- 研究中心、歷史回測、system/model transparency do not appear in ordinary-user main navigation.
- System policy, Leader Set, data-source, and model transparency details belong under settings, research, or admin-style secondary surfaces.
- The existing React customer UI remains the customer surface; this blueprint does not propose a replacement frontend.

### Global Header Information Architecture — FROZEN / PM-APPROVED / TASK-FE-HEADER-002

The V2 customer frontend uses one shared desktop App Shell header on every V2 customer route. The header is a single horizontal workspace bar divided into two information groups: a **Left Group** and a **Right Group**. It must not be split into a primary navigation row plus a second utility/search row.

Header layout, from left to right:

```text
[T] TopicPilot  今日市場  題材  股票  收藏  機會  AI研究室       搜尋股票、題材...  通知  帳號
```

- **Left Group:** contains the `TopicPilot` wordmark and the complete expanded primary navigation: `今日市場`, `題材`, `股票`, `收藏`, `機會`, `AI研究室`. Logo and navigation are one information group and stay naturally close to the left; navigation is not centered as a SaaS or marketing-site layout. The logo is weight 700, navigation is weight 500, and the active item is weight 600 with `#8A7462`.
- **Right Group:** contains Global Search, Notification, and Account; the group stays aligned to the right with the search control shortened to a balanced 260–300px range.
- **Global Search:** lives inside the Right Group, uses a white 260–300px field with placeholder `搜尋股票、題材...`, preserves `Ctrl+K`, and is a dummy shell only until a search API contract is approved. The shell is extensible to stocks, stock codes, and topics.
- **Notification:** the Bell remains in the header as an outline control. Its current panel is a placeholder for future topic warming/cooling, S/A/B, and favorite reminders; no notification API is connected.
- **Account:** the header uses an outline account control. Its placeholder dropdown contains `登入 / 建立帳號`, `會員方案`, `說明中心`, `意見回饋`, and `Settings`. Login and account APIs are deferred.
- **Removed:** the desktop hamburger is not part of the V2 customer header. Settings and help are integrated into the Account menu; duplicate search, notification, settings, and help bars below the header are removed.
- **Freshness boundary:** `盤中更新`, `尚未連接資料`, and other freshness/data-state presentation remains inside 今日市場 content. It is not promoted into a global header status.
- **Rhythm:** the header remains a consistent 72px desktop bar; logo-to-navigation spacing is compact and natural, navigation item spacing remains comfortable, and V2 page content begins with a compact vertical gap so the workspace reads like a financial tool rather than a landing page.
- **Style:** preserve the Modern Financial Workspace direction: light mode, warm off-white page, white surfaces, `#8A7462` brand, subtle borders, restrained hover, and no neon, gradient, glass, glow, or heavy shadow.

### DEFERRED / FUTURE

AI研究室 stays in the IA as a Phase 2 premium differentiator. It must not block the initial frontend launch.

## 4. Page purposes: one question per page

| Page | Primary question | V1 role |
|---|---|---|
| 今日市場 | 今天市場發生了什麼？ | Intraday market navigation |
| 題材 | 哪些題材值得研究？ | Theme exploration and state |
| 股票 | 資料庫有哪些股票、哪些符合條件？ | Full stock database |
| 收藏 | 我收藏的題材與股票，現在怎麼樣了？ | Saved items and quick access |
| 機會 | 系統辨識出哪些值得進一步研究的機會？ | Dedicated opportunity surface |
| AI研究室 | 我想針對一個市場／題材／股票問題深入討論？ | Phase 2 research workspace |

## 5. 今日市場 / Home blueprint

### FROZEN / CURRENT DECISION

Home is intraday-first. Pre-market and post-market variants are deferred. The fixed V2 hierarchy is:

```text
┌ 今日市場 ───────────────────────────────────────────────┐
│ 市場概況   加權指數／OTC／成交金額／漲跌家數／漲跌停／更新時間 │
├ 今日市場重點 ──────────────────────────────────────────┤
│ 一段 deterministic market reading                         │
├ 今日主線 TOP3 ──────────────────────────────────────────┤
│ 題材名稱／S-A-B-D 等級／可讀狀態 → 題材頁                  │
├ 盤中重要事件 ───────────────────────────────────────────┤
│ 有門檻的題材狀態轉換時間線                                 │
├ 快速升溫／快速退潮 ─────────────────────────────────────┤
│ 左右兩欄、各最多 3 個題材                                   │
├ 我的收藏（登入後） ─────────────────────────────────────┤
│ 登入後才顯示的收藏變化摘要                                  │
├ 今日機會 ─────────────────────────────────────────────┤
│ 研究候選 teaser → 機會頁                                    │
└───────────────────────────────────────────────────────┘
```

Sections, in order:

1. **市場概況** — 一張橫向 Summary Card，呈現加權指數、OTC 指數、成交金額、上漲／下跌／平盤家數、漲停／跌停家數與更新時間。
2. **今日市場重點** — 以 3–4 點條列呈現 concise deterministic summary，底部補一行低存在感的「今日一句話」。它不是新聞流，也不是 AI 對話或長文章。
3. **今日主線 TOP3** — 固定三張可點擊題材卡，顯示名稱、S/A/B/D 等級與一句可讀狀態；不放股票、新聞或 Leader Table。
4. **盤中重要事件** — 只記錄有意義的題材狀態轉換，例如升溫、分歧、退出主線；不記錄每分鐘流水帳。
5. **快速升溫／快速退潮** — 左右兩欄，各最多三個題材，回答資金目前正在移動的方向。
6. **我的收藏** — 僅登入後顯示的收藏變化摘要，不重建完整收藏頁。
7. **今日機會** — 受限的研究候選 teaser，點擊進入機會頁；Home 不完成推薦分析。

Explicit exclusions: no Home news feed, topic map/heatmap, long stock list, technical indicators as the primary visual, or AI branding as a visual gimmick. News belongs in Topic Detail and Stock Detail contexts.

**API/data dependency to verify:** market aggregates, freshness, event labels, deterministic summary source, topic-card fields, authenticated saved-item summary, and opportunity teaser fields must be confirmed against the existing API contracts before production data wiring. The first visual implementation may use a clearly documented fixed development snapshot.

### FROZEN / CURRENT DECISION

Home is not user-customizable in V1. The product team controls the hierarchy so the page consistently answers “today, what matters?”. Saved filters, stock columns, and watchlists may be customizable later.

## 6. 題材 page blueprint

### PROVISIONAL / TO REVIEW

Recommended views: `主線`、`升溫`、`退潮／降溫`、`全部`、`題材地圖`、`題材狀態分布`.

Capabilities:

- rank topics by strength, intraday warming/cooling, participation, leader drive, and persistence;
- show the topic map/heatmap here, never as the default Home composition;
- show a retail-readable state distribution corresponding to backend Breadth × Leadership logic: `全面走強`、`龍頭先行`、`題材擴散`、`動能轉弱`;
- topic cards lead with human-readable state and place numeric evidence second.

**API/data dependency to verify:** exact ranking dimensions, topic-map inputs, and state-distribution payloads must be verified; the browser must not calculate business scores.

## 7. Topic Detail blueprint

### FROZEN / CURRENT DECISION

Progressive disclosure is the default:

- Primary: topic name, current grade and strength score, human-readable state, short current summary.
- Secondary: 族群參與度, 龍頭帶動力, 龍頭一致性, 資料完整度／評分狀態, current representative stocks, CORE member count/list, intraday evolution, multi-day trend, and recent events.
- `龍頭一致性` is presented qualitatively first; raw `+10/+5` mechanics belong only in detailed explanation.
- News appears as a limited, relevant evidence/context list, not an endless generic feed.
- Drill-down routes: representative stocks, CORE members, opportunity candidates, stock detail.

The page must preserve the product-contract boundary: Topic Score is market strength, Grade is not a recommendation, Confidence is separate, News is context, and Recommendation is downstream.

**API/data dependency to verify:** summary copy, qualitative state, member counts, events, and curated news availability must be confirmed in the read contracts.

## 7A. 題材與 Topic Detail decision reconciliation (V1 authority)

### FROZEN / CURRENT DECISION — 題材 page

This section supersedes any earlier provisional card-first, time-scale-toggle, or list-level leader-sync wording in the 題材 blueprint. V1 is **LIST-FIRST**: a searchable/filterable topic ranking is the primary surface, followed below by a rectangular topic heatmap/treemap. The heatmap belongs on 題材, never Home, and clicking a topic routes to Topic Detail.

The list may show: 題材名稱, 題材強度, S/A/B/D, supported retail-readable state (`全面走強`、`龍頭先行`、`急升溫`、`高檔分歧`、`退潮`), an intraday change/event marker where supported, and an optional watch/star action. Do not expose `Breadth`、`Leadership`、`Consensus` technical names in the list. Do not show representative-stock synchronization or leader-confirmation state on the list; that belongs in Topic Detail. Do not add a V1 `盤中／近5日／近14日` toggle.

The heatmap communicates topic importance/market presence and current strength through restrained rectangles, labels, neutral fills, line weight, and status semantics. It follows the Modern Financial Workspace direction: light mode first, white/light surfaces, subtle borders/shadows, `#8A7462` warm-neutral brand, and Taiwan red/green reserved primarily for actual price direction. It must not become a saturated rainbow dashboard. Exact rectangle sizing remains an API/data dependency and PM-reviewable implementation detail; no new business score is defined here.

### FROZEN / PM-APPROVED DESIGN DIRECTION — 題材生命圖

Topic Detail reading order is frozen as: (1) identity + grade + 題材強度 + current state; (2) 題材生命圖; (3) 族群參與度、龍頭帶動力、龍頭一致性、資料完整度／評分狀態; (4) 代表股 / Leader Set; (5) 核心成員; (6) 全部相關股票; (7) recent topic events / intraday evolution; (8) limited relevant news/context; (9) opportunity candidates/downstream drill-down where appropriate.

Place the prominent 題材生命圖 immediately after the primary identity/strength summary and before member/news detail. Its retail-readable conceptual stages are `萌芽`、`發酵`、`主升`、`高檔整理`、`退潮`.

Each lifecycle segment or transition displays, or makes accessible through hover/progressive disclosure: stage name, stage start date, completed stage end date, number of **trading days** spent in the stage, and a clear current-stage marker. The default summary uses this pattern:

> 目前階段：主升｜8/6 進入｜已持續 4 個交易日

Preserve actual transition history. Lifecycle is not a permanently one-way state machine; a valid trajectory is `萌芽 → 發酵 → 主升 → 高檔整理 → 再度主升`, with repeated entries represented as separate segments.

The UX shape, current marker, dates, trading-day duration, transition history, and re-entry behavior are **FROZEN / PM-APPROVED DESIGN DIRECTION**. Lifecycle-stage derivation logic and its API/data contract remain an **API/data dependency to verify** unless a canonical backend contract already defines them. The browser must not infer lifecycle stages, heatmap sizing, or business scores.

Remaining topic/lifecycle dependencies include the list/read payload, supported human-readable states, optional intraday markers and watch action, heatmap sizing input, lifecycle history and trading-day durations, member/leader sets, events, curated news, and downstream opportunity links.

## 8. 股票 page blueprint — full database

### FROZEN / CURRENT DECISION

股票 is the complete TopicPilot stock database, not only the intraday observation pool. A stock remains visible even when it is not currently polled intraday, for example because price is below 60MA. The product role is **市場圖鑑**: quickly browse every stock and understand its current market identity. 題材頁像市場地圖，研究市場故事、題材強弱與輪動；股票頁像市場圖鑑，翻閱資料庫中的每一檔股票。

The default pre-selection state is a clean desktop-first stock-explorer/index surface, not a recommendation dashboard or card wall.

User-facing update states:

| State | Meaning | UI treatment |
|---|---|---|
| 盤中更新 | Included in intraday tracking; roughly every 5–10 minutes | Show current price and visible freshness |
| 盤後更新 | Intentionally not in intraday tracking; updated after close | Keep last valid price; explain status |
| 資料待更新 | Actual freshness or data problem | Distinguish as a data state |

Plain-language info text for 盤後更新:

> 目前股價低於 60 日均線，暫不納入盤中即時更新；價格將於盤後統一更新。

Do not gray out or disable the row. Make last valid price and as-of time transparent. Do not show `推薦／不推薦` in the base table because not every stock is evaluated by Recommendation.

Default layout before selecting a stock:

1. Page header/database summary: `股票`, `收錄 XXX 檔`, `盤中更新 XXX｜盤後更新 XXX`.
2. Search bar supporting stock name or code.
3. Compact horizontal first-level filters: `題材`, `強度等級 S/A/B/D`, `上市/上櫃`, `更新狀態`, `題材角色`, `60MA 狀態`, `自選`, and `更多篩選`. Do not expose dozens of filters at once; future technical filters belong under expanded filters.
4. Main stock table.

Default table columns prioritize:

`股票／股號 | 現價 | 漲跌幅 | 主要題材 | 題材角色 | 題材狀態 | 更新狀態`

`副題材` is not required in the first visual layer because it increases row clutter and variable density. Secondary topics remain available in the Stock Drawer and may later be an optional configurable column. Do not show Recommendation / 推薦不推薦 in the base table.

Table interaction and visual design: dense-but-readable financial table; sticky first column where appropriate; subtle horizontal separators rather than a full Excel-style grid; whole-row click opens the Stock Drawer; hover uses a very subtle warm-gray background; the selected row uses a restrained warm-neutral state. A small right chevron or `查看` affordance is optional and visually minor. Headers may sort valid fields such as price, change, topic strength, and update status where semantics are valid. Do not mix stale/post-close prices into an implied real-time ranking without freshness-aware rules; exact ranking/freshness behavior remains an API/implementation dependency.

### Stock Drawer — 個股圖鑑

A stock selection opens a right-side Drawer instead of navigating away by default. Preferred desktop width is roughly 35–40% of the viewport while preserving useful table context; this percentage is visual-prototype guidance, not business semantics. The Drawer is not a modal: the table remains visible, interactive, and scrollable, and clicking another row immediately replaces Drawer content without close/reopen repetition.

Drawer first-screen ordering is frozen as: identity → price/freshness → market identity/topic roles → main topic summary.

- Identity: stock code + name, with the single favorite star action at top-right only. `☆` tooltip: `加入自選`; `★` tooltip: `已加入自選，點擊移除`. Inactive is neutral gray; active is `#8A7462`. There is no duplicate bottom `加入自選` CTA.
- Price/freshness: current or last valid price, price change %, and a visible line such as `更新 10:35｜盤中更新`. Taiwan convention remains red up / green down only for actual price direction. Post-close-only stocks keep the last valid price with a plain-language explanation and must not look broken or disabled.
- Market identity: immediately after price, show all supported topic memberships with this stock's canonical role where available, for example `BBU｜核心股` and `儲能｜關聯股`. List the primary/main identity first with stronger hierarchy. Role chips: 代表股 deepest warm-neutral, 核心股 medium, 關聯股 light neutral.
- Main topic summary: show the main topic name, current topic grade/state, a short human-readable state, and lifecycle/current topic stage only when already available from the Topic Detail read model. Provide `查看 [題材] →` to route deeper research back to Topic Detail; do not duplicate full Topic Detail analytics here.

### Stock Drawer — secondary sections and dependencies

- **法人動向** is default-expanded if data exists, with `近5日 | 近20日 | 近60日`, 外資 net buy/sell, 投信 net buy/sell, 自營商 net buy/sell, and an optional restrained micro-trend. Do not invent data; verify the 5/20/60-day payload as an API/data dependency.
- **技術狀態** is compact and human-readable, showing only backend-supported facts such as `月線之上`, `趨勢偏強`, or `接近支撐區`. If deep technical evaluation has not run, show `尚未進入技術深度分析`. Do not expose recommendation status by default or infer technical conclusions in the browser.
- **〉個股走勢階段** is reserved as a collapsed accordion. Individual-stock lifecycle rules are not frozen and Topic lifecycle stages must not be copied automatically. Actual derivation/read model is an API/business-rule dependency; the browser must not infer it.
- **〉相關新聞 N** is collapsed by default and contains limited relevant, curated news rather than an endless generic feed. Stock-news payload/curation is an API/data dependency where not already supported.

V1 explicitly excludes a required K-line, a large fundamental terminal (PE/EPS/revenue/etc.) as the first-phase Drawer focus, a default recommendation field in the full database, a bottom duplicate favorite CTA, and a card-grid stock browser. K-line remains a future capability.

Apply the existing Modern Financial Workspace system: light mode first; warm off-white page background; `#8A7462` brand accent; white/light surfaces; subtle warm-gray 1px borders; little/no shadow; restrained 10–12px radius; data-dense but readable. In the Drawer use a clean white/light panel, strong identity and price hierarchy, whitespace and subtle separators instead of many colored nested cards, warm-neutral topic-role chips, and calm compact accordion labels. Update-state text/chips remain subdued and must not introduce unnecessary blue/orange categories.

### PROVISIONAL / VISUAL PROTOTYPE REVIEW

Exact Drawer width (35–40% guidance), exact table density/row height, exact filter-bar wrapping behavior, and exact microcopy such as `市場身分` vs `題材身分` remain prototype-review items.

```text
股票／股號  | 現價 | 漲跌幅 | 主要題材 | 副題材 | 題材等級／狀態 | 更新狀態
───────────┼──────┼────────┼──────────┼────────┼────────────────┼──────────
sticky first column; subtle row hover; topic links; numeric alignment; freshness tooltip
```

### API/data dependency to verify

Complete stock universe counts; current/last valid price and freshness; canonical main topic and topic state; stock-topic role mapping; institutional flows for 5/20/60 days; simplified technical-state payload; stock lifecycle if ever implemented; curated stock news; 60MA relation; listing fields; and freshness-aware sort/ranking semantics must be supported or explicitly unavailable. Preserve the canonical states `盤中更新`, `盤後更新`, and `資料待更新`.

## 9. 我的收藏 page blueprint

### FROZEN / CURRENT DECISION

The product concept is **收藏／Saved Items**, not a recommendation surface. The page title is `我的收藏`; the exact primary-navigation copy `收藏` versus `自選` remains visual/copy reviewable. Its purpose is:

> 把我想持續關注、或只是想方便下次找到的題材與股票集中在一起，並告訴我它們目前發生了什麼。

It answers `我收藏的題材與股票，現在怎麼樣了？` It must not answer `我現在該買什麼／賣什麼／下一步該做什麼？`; that belongs to 機會 / Recommendation.

The page keeps two clearly separated entity types under one surface, using internal tabs or segmented navigation: `題材 | 股票`. Topics and stocks must not be mixed into one undifferentiated default list.

#### 收藏題材

Use a compact, dense-but-readable list/table rather than large cards. The first layer may show `題材名稱 | 題材強度 | S/A/B/D | 目前狀態 | 今日變化／meaningful event marker` where supported. Neutral factual examples include `今日首次升 S`、`快速升溫`、`開始高檔分歧`、`退出主線` and `題材角色變更`. Clicking a topic row routes to the existing Topic Detail page; do not reimplement lifecycle, members, events, or news detail inside 收藏.

#### 收藏股票

Use a compact stock list/table with `股票／股號 | 現價 | 漲跌幅 | 主要題材 | 題材角色 | 更新狀態`. Clicking a stock must reuse the exact shared `Stock Drawer — 個股圖鑑` already frozen for 股票. Do not create a 收藏-specific stock detail. Drawer hierarchy, favorite control, role chips, institution flows, technical state, collapsed lifecycle, and collapsed news remain shared.

#### Boundary with 機會 / Recommendation

`我的收藏 = state, changes, quick access`; `機會 = candidates, reasons, risk, conditions, timing / research priority`. Do not add a per-item `現在該怎麼辦？` field or generic recommendation labels such as `持續觀察`、`等待確認`、`留意風險`、`值得深入研究` in V1 收藏. If a saved item also appears in 機會, 收藏 may show only a restrained indicator such as `已列入今日機會 →`; it must not duplicate the explanation. 機會 may show `★ 已收藏`.

收藏 may surface **what changed, not what to do**: factual state changes, `盤中更新／盤後更新`, or `法人近5日轉買超` only when supplied by a canonical backend read model. The browser must not infer advice from these changes.

#### Layout, interaction, and states

Keep the page intentionally simple: page header `我的收藏`; quiet subtitle `快速查看你收藏的題材與股票`; `題材 | 股票` tabs; optional compact search/filter within the active tab; then the main list/table. No recommendation cards, opportunity ranking, heatmap, large news blocks, or redundant dashboard widgets. The surface should feel lighter than Home/Topic: personal organization plus fast re-entry.

Reuse the existing Topic row/detail routing, Stock Drawer, favorite star/bookmark primitive, grade chips, role chips, and update/freshness primitive. Empty states remain calm and concise: no saved topics links to 題材; no saved stocks links to 股票. Do not use illustration-heavy AI empty states.

收藏 must use the frozen Modern Financial Workspace system: desktop-first, light mode first, warm off-white background, white/light surfaces, subtle warm-gray 1px borders, little/no shadow, restrained 10–12px radius, and dense-but-readable rows. Tabs use `#8A7462` for the active state and neutral gray when inactive. Active saved-state star/bookmark uses `#8A7462`; inactive is neutral gray. Row hover is subtle warm-gray; a selected stock row while the Drawer is open uses a restrained warm-neutral state. Avoid colorful status cards, purple/blue AI gradients, glow, glassmorphism, neon, heavy shadows, colored icon walls, and dashboard tiles. Taiwan red/green remains reserved for actual price movement; S/A/B/D and role chips remain restrained warm-neutral hierarchy. Do not invent a separate visual identity for 收藏.

### PROVISIONAL / TO REVIEW

Exact navigation label `收藏` versus `自選`; exact subtitle; exact optional cross-link wording to 機會; exact row density; and search/filter placement.

### API/data dependency to verify

User-scoped persistence; saved topic list payload; saved stock list payload; factual event/change markers; optional opportunity cross-link status; and any institution-flow event marker must be supported by canonical contracts. The browser must not infer lifecycle, scores, advice, or events.

## 10. 機會 page blueprint

### FROZEN / CURRENT DECISION

Keep a dedicated Opportunity page. Recommendation logic is substantial, not every stock is evaluated, and Home should show only a teaser. Use language such as `今日機會`、`值得留意`、`研究候選`; do not frame the page as direct buy instructions.

### PROVISIONAL / TO REVIEW

Candidate groups may include `主線精選`、`龍頭先行`、`題材擴散`、`落後補漲`、`盤中急升溫`、`例外升溫`、`等待確認／觀察中`. Exact labels, ordering, and priority remain PM-reviewable.

Each candidate explains why it is surfaced. Evidence may include topic state, technical state, invalidation/risk, and timing/entry information only where backend data actually exists. A candidate should distinguish “not evaluated” from “not recommended”.

**API/data dependency to verify:** candidate reason taxonomy, evidence payloads, state/history, invalidation, and any entry-timing fields must be verified. No browser-side Recommendation logic.

## 11. AI研究室

### DEFERRED / FUTURE — Phase 2

Keep the IA entry but do not block V1. The intended experience is four stable investment-role agents: `短線派`、`趨勢派`、`風控派`、`逆向研究員`. They should provide independent views, exchange positions, conduct focused rebuttal/cross-examination, and finish with consensus, disagreement, and what to watch next. Product personas stay stable even if backend models change.

**API/data dependency to verify:** orchestration, streaming/latency, conversation persistence, citation/evidence, and failure-state contracts.

## 12. Global UX capabilities

### 全站搜尋 — FROZEN / CURRENT DECISION

Desktop-first command-style search, optionally `Ctrl+K`, searches stocks and topics and routes quickly to detail pages. Search results must distinguish stock and topic entities.

### 通知中心 — PROVISIONAL / TO REVIEW

Use the bell notification center, not frequent intrusive popups. Prefer TopicPilot-native events: topic becomes main line, rapid warming, high-level divergence, main-line weakening, watched topic grade change, or material change in a watched stock’s topic. Only major events may justify a prominent banner. Do not freeze exact taxonomy or thresholds here.

**API/data dependency to verify:** notification read/unread, user scope, event payload, retention, and delivery contracts.

## 13. Data refresh and freshness UX

### FROZEN / CURRENT DECISION

The product should feel live without causing layout chaos. Use skeletons only for initial loading; afterward update values incrementally without whole-page spinners or reloads. Show freshness/as-of time wherever a number could be mistaken for current.

Ranking updates should balance liveness and visual stability. Do not invent a hard “sort every 15 minutes” rule. Exact reorder behavior is PM-reviewable. Do not over-emphasize yesterday-vs-today on Home; multi-day history belongs in topic/stock detail.

## 14. Visual direction and brand

### FROZEN / CURRENT DECISION

Brand personality: **Reliable, Clear, Calm, Insightful.** Concept: **Modern Financial Workspace / 現代金融工作桌**.

Avoid purple-blue AI gradients, glow/neon, glassmorphism, heavy shadows, excessive robot/AI icons, particle effects, futuristic monospace identity, and decorative color overload.

Primary brand color: `#8A7462` warm neutral taupe/brown. Use it for identity and interaction—logo/accent, selected tabs, buttons, links, small labels, focus states—not large background fills.

Base: warm/off-white background, white surfaces, dark neutral text, subdued warm-gray secondary text/borders. Light mode is the default first target; dark mode is fully supported eventually but timing is open.

Taiwan market convention is preserved: red = price up, green = price down. Reserve red/green primarily for actual price direction, not grade semantics. Warnings use restrained amber; error red is for true system errors and must remain distinguishable by context/style.

S/A/B/D uses restrained warm-neutral emphasis, never green/red or full-card fills: S deepest taupe, A medium taupe, B light warm gray-brown, D neutral gray.

## 15. Information density and component language

### FROZEN / CURRENT DECISION

Density is more compact than Apple/Notion, but less harsh than legacy broker/XQ screens. Home is breathable, Topic moderate, Stock table high-but-readable, AI Studio reading-oriented.

| Surface | Component language |
|---|---|
| Home | Editorial market summary cards |
| Topic | Cards plus selective visualizations |
| Stock | Table with subtle separators and sticky first column |
| Watchlist | List/status-oriented |
| AI Studio | Conversation |

Cards are white/light surfaces with subtle borders, little/no shadow, restrained radius, no glass/neon. Tables use subtle separators, aligned numerics, subtle hover, and visible but quiet freshness. Charts are few and meaningful; stock detail should have one primary K-line rather than competing panels.

Typography, spacing, radius, and shadow values below are implementation defaults, not PM business semantics:

```text
Proposed baseline: 8px spacing rhythm; 10–12px restrained radius; 1px warm-gray borders;
14px body / 12px metadata / 20–28px section titles; system sans-serif with Taiwan CJK fallback.
```

### RESPONSIVE STRATEGY — FROZEN / CURRENT DECISION

Desktop-first. Do not build a full mobile experience in parallel with desktop V1. Tablet may be tolerated where easy; mobile redesign is a later dedicated phase.

## 16. Interaction and motion

### FROZEN / CURRENT DECISION

V1 prioritizes layout and content correctness. Use subtle short transitions only when useful, no bounce, dramatic zoom, or decorative motion. Live values may update smoothly without whole-card re-entry animations.

## 17. Content and terminology map

| Backend/technical term | Retail-facing UI term |
|---|---|
| Topic Score | 題材強度 |
| Grade | 強度等級 |
| Breadth | 族群參與度 |
| Leadership | 龍頭帶動力 |
| Consensus | 龍頭一致性 |
| Confidence | 資料完整度／資料可信度 — PM review |
| Eligibility | 評分狀態 |
| CORE members | 核心成員 |
| Leader Set | 代表股／龍頭股 |
| Rotation | 題材輪動／升溫降溫 |

Raw formulas, scores, and system-policy details belong in progressive disclosure, not default cards. Any core metric should answer both “數字是多少” and “這代表什麼”.

## 18. Design manifesto

1. 少顏色：顏色代表狀態，不作裝飾。
2. 重層級：用版面、字級、留白表達重要性。
3. 先閱讀：像每天閱讀市場情報，不像拼貼 Dashboard。
4. 重解釋、不炫技：AI 是功能，不是視覺風格。
5. 預設平靜：只有真正重要的事件才突出。
6. 數字 + 意義：核心指標同時回答數字與含義。
7. 專業底層、散戶表達。
8. 首頁不是資料入口，而是市場導航。

## 19. Open PM review items

Only the following are intentionally unresolved:

- exact notification event taxonomy, content, and thresholds;
- exact live ranking/reordering stability behavior;
- exact Opportunity grouping labels, order, and priority;
- wording choice: `資料完整度` vs `資料可信度`;
- exact typography/font stack and token sizes;
- exact spacing/radius/border/shadow tokens, unless accepted as implementation defaults;
- Dark Mode visual-token timing;
- pre-market/post-market Home variants;
- mobile design phase;
- AI Research Studio orchestration and latency UX.

Already decided and not open here: full-database 股票 page, 盤中／盤後／待更新 distinction, desktop-first strategy, Home fixed hierarchy, no Home news feed, dedicated 機會 page, #8A7462 direction, Taiwan red/green price convention, and AI Studio Phase 2 deferral.

## 20. Recommended frontend implementation sequence

This is sequencing guidance, not an implementation authorization:

1. Confirm PM review items and verify API/data dependencies.
2. Establish shared shell, navigation, global search, freshness/status primitives, typography, and light-mode tokens.
3. Prototype 今日市場 hierarchy with deterministic/loading/stale states.
4. Implement 題材 list/detail and the retail terminology/progressive-disclosure pattern.
5. Implement full 股票 database table, filters, sticky column, and update-state explanations.
6. Implement 我的收藏 with separate 題材 and 股票 tabs, using shared detail components.
7. Implement 機會 after candidate reason/evidence contracts are verified.
8. Add notification center after event taxonomy review.
9. Treat AI研究室, dark mode, pre/post-market variants, and mobile as later phases.

## 21. Repository and contract boundaries

- This is a frontend design specification only; no frontend code, API, backend, database, or scoring policy was changed by authoring it.
- Do not claim a UI field exists until the relevant API/read-model contract supports it.
- The Product Direction and Surfaces Contract remains the source of truth for product semantics; this document is the page and visual blueprint beneath it.
- Recommendation remains downstream, explainable, read-only, and fail-closed over unavailable/deferred Topic Intelligence according to the existing contracts.

## 22. PM freeze: 今日市場 (Home) V2

**Decision status:** `FROZEN / PM-FROZEN`  
**Review gate:** the fixed visual hierarchy is approved for the first V2 implementation. Backend data wiring remains a separate integration boundary.

### 22.1 Final section order

The Home page is a fixed market-navigation workspace. The final V2 order is:

1. **Shared App Shell header**
2. **Home hero** — no duplicate page H1; freshness/data state is presented inside the `市場概況` Card Header。
3. **市場概況** — 加權指數、OTC 指數、成交金額、上漲／下跌／平盤、漲停／跌停、更新時間。
4. **今日市場重點** — a concise deterministic market reading presented as 3–4 bullets, followed by a low-presence one-line research focus。
5. **今日主線 TOP3** — exactly three current themes, with grade and readable state; each routes to 題材。
6. **盤中重要事件 Timeline** — meaningful topic state transitions only。
7. **快速升溫／快速退潮** — two concise columns, at most three topics per side。
8. **我的收藏** — authenticated-only compact change summary; hidden while signed out。
9. **今日機會** — a restrained teaser linking to the dedicated 機會 page; Home does not complete recommendation analysis。

The hierarchy is fixed in V2 and is not user-customizable.

### 22.2 Home exclusions

Home V2 explicitly does **not** contain a stock ranking, long stock list, news feed, topic heatmap/topic map, K-line chart, technical analysis chart, or AI chat. These exclusions are intentional: TopicPilot is a market-navigation product, not a stock-ranking, charting, news, or AI showcase surface. Stocks remain concentrated on 股票; topic visualization belongs on 題材; recommendation analysis remains concentrated on 機會.

### 22.3 Intraday event timeline

The timeline records only significant, user-meaningful topic transitions. Supported examples include 首度升至 A、首度升至 S、開始高檔分歧、退出主線、快速升溫、快速降溫。 Do not emit an event for every small score, price, or rank movement. Each event should retain its timestamp, topic identity, transition label, and enough context for a user to understand what changed.

### 22.4 Home business boundary

Home is a market-navigation surface, not a stock-ranking surface. It must not contain `今日強勢股`、`今日弱勢股`、大量股票排行、完整股票列表、K 線、技術分析圖、完整題材地圖、新聞流或 AI 對話。股票資料集中於股票頁；推薦分析集中於機會頁；首頁的今日機會只負責提供下一步研究入口。

### 22.5 Frozen Home visual direction

Home uses the **Modern Financial Workspace** direction: light mode first; warm neutral primary brand color `#8A7462`; white cards with very restrained shadows; importance expressed through hierarchy, typography, and spacing rather than many colors; Taiwan market red/green reserved for actual price movement; and S/A/B/D shown with restrained warm-neutral chips, never bright saturated grade colors or full-card fills.

### 22.6 First implementation note

No Home product or information-architecture decision remains open for this phase. The first implementation uses a fixed development snapshot to complete layout, spacing, card hierarchy, and desktop rendering while market aggregates, freshness, event timeline, authenticated favorites summary, and opportunity teaser data remain integration dependencies. Pre-market/post-market variants, mobile redesign, and exact shared token values remain global or future-phase items.

### 22.7 TASK-FE-002C Home final UI freeze and data boundary

The Home hero no longer renders a duplicate `今日市場` H1 or a standalone freshness row. The global header identifies the current page. Freshness is shown only in the `市場概況` Card Header as one compact status treatment: `盤中更新`, `盤後更新`, or `資料待更新`, with a timestamp when available.

The first viewport should show the market summary and the beginning of `今日市場重點` without requiring a scroll at the approved desktop width. The Summary Card keeps the two-row structure: primary `加權指數／OTC 指數／成交金額`, followed by `上漲／下跌／平盤／漲停／跌停／更新時間`, with compressed vertical padding and no chart, heatmap, or additional visualization. `今日市場重點` keeps its four bullets and `今日一句話` while using a compressed reading rhythm.

`今日主線` keeps exactly three compact cards with their S/A/B/D grade chips, readable state, and `進入題材頁` action. The action link is the only clickable element for each card; the entire card is not a link. `盤中重要事件`, `快速升溫／快速退潮`, and `今日機會` retain their current design and information order. No hover preview, stock popup, tooltip, chart, or new business logic is introduced.

The frontend consumes the existing read-only `GET /api/v1/snapshot/latest` path when the returned snapshot contains the relevant fields. Market indices, market breadth, and freshness timestamps are live-backend candidates only when present and usable; fields absent from the current public read model remain formal-language mock values and are documented in the TASK-FE-002A implementation report. Today Focus, ranked Top 3, event timeline, rotation, authenticated favorites, and opportunity preview remain unchanged mock or deferred surfaces until their authoritative APIs are available.

**Freeze status:** Home is frozen after TASK-FE-002C. The next authorized surface is Topic Detail; no further Home layout changes are included in this phase.

## 23. PM freeze amendment: Topic Detail hierarchy, roles, and personal watch architecture

**Decision status:** `FROZEN / CURRENT DECISION`  
**Scope:** additive amendment to the existing V2 Frontend Design Specification. It does not authorize frontend, backend, API, schema, scoring, or production changes.

### 23.1 Topic Detail hierarchy breadcrumb

Freeze a compact breadcrumb immediately near the Topic Detail title. It explains where the current topic sits in the broader market story and allows navigation to parent groups. Examples are `電子 > AI > AI伺服器` and `電力 > 重電`. Ancestors are clickable; the current topic is emphasized. Ancestors use muted warm gray, while interactive/current emphasis uses `#8A7462`. Separators are compact and text-based; no decorative icon dependency is required.

The breadcrumb is the lowest-weight element in the Topic Detail hierarchy. The topic identity, grade, strength, and human-readable state remain the highest-weight elements.

### 23.2 Topic stock roles and unified list

Freeze the V1 topic stock roles as:

- `代表股`
- `核心股`
- `關聯股`

Core principle: **題材 Detail 中，每一檔股票都應回答「它在這個題材中扮演什麼角色」，而不只是「它是否屬於這個題材」。**

The preferred presentation is one unified, dense-but-readable stock list/table ordered `代表股 → 核心股 → 關聯股`. Do not force three accordions by default. Columns are: 股票名稱/股號, 題材角色, 現價, 漲跌幅, 更新狀態, and optional freshness timestamp. Each row links to Stock Detail.

Role chips use warm-neutral hierarchy only: 代表股 uses the strongest taupe, 核心股 a medium taupe, and 關聯股 a light neutral. Role semantics must never use red/green, and production must not depend on emoji.

### 23.3 Topic Detail reading order amendment

The authoritative Topic Detail reading order is now:

1. hierarchy breadcrumb;
2. Topic title + grade + 題材強度 + human-readable state;
3. 收藏題材 / reminder entry action;
4. 題材生命圖;
5. 族群參與度 / 龍頭帶動力 / 龍頭一致性 / 資料完整度 / 評分狀態;
6. 題材內股票列表 with role chips;
7. recent topic events / intraday evolution;
8. relevant curated news/context;
9. downstream 機會 candidates where appropriate.

This amendment supersedes the earlier member-list ordering while preserving the already frozen lifecycle design. No other rejected sections are added.

### 23.4 Topic lifecycle preservation

The frozen lifecycle stages remain `萌芽 / 發酵 / 主升 / 高檔整理 / 退潮`. The lifecycle displays stage start date, end date when complete, trading-day duration, and a current-stage marker. Re-entry into prior stages is valid and must be represented as separate segments. The summary pattern is:

> 目前階段：主升｜8/6 進入｜已持續 4 個交易日

Lifecycle derivation remains an API/data/business-rule dependency unless already canonically defined by the backend. The browser must not infer it.

### 23.5 Watch architecture: 收藏題材 and 收藏個股

Freeze support for both entity types:

- `收藏題材`
- `收藏個股`

Both live under one top-level `我的收藏` page, visually separated with internal tabs or segmented navigation: `題材 | 股票`. Topic Detail exposes `☆ 加入自選 / 收藏題材`; Stock Detail exposes `☆ 加入自選 / 收藏股票`. Exact action copy remains prototype-reviewable, but entity separation is frozen. The page is a saved-item / quick-access surface, not a recommendation surface.

Topic alerts may later include `進入S / 快速升溫 / 開始退潮`; stock alerts may later include stock-specific events. Exact notification taxonomy and thresholds remain unresolved.

### 23.6 Home Freeze Amendment: compact personal watch summary

The prior Home freeze is preserved in full: Home remains a fixed market-navigation workspace; previous exclusions remain frozen, including no Home news feed, no Home heatmap/topic map, and no large K-line chart. Add one compact `我的關注 / 自選摘要` section that summarizes both 收藏題材 and 收藏股票. This is not a full Watchlist page.

Suggested content direction is two small counters or a segmented mini-summary such as `[收藏題材 3] [收藏股票 12]`, followed by one to three important change rows, for example:

- AI伺服器｜收藏題材｜首次升至 S
- BBU｜收藏題材｜開始高檔分歧
- 廣達｜收藏股票｜+3.2%｜所屬題材持續強勢

The summary links to `我的收藏`. Its preferred placement is after the major market/topic intelligence blocks and before or near `今日機會`. Existence and compact nature are frozen; exact placement and exact copy (`我的關注` vs `我的自選`) remain visual-prototype reviewable. Use a compact white editorial card/block, small counters, short rows, restrained spacing, and no colorful dashboard treatment.

### 23.7 Shared visual, layout, and color implementation guidance

All additions follow the frozen Modern Financial Workspace direction:

- desktop-first and light mode first;
- warm off-white page background, white/light cards, subtle warm-gray 1px borders, little or no shadow, and a 10–12px radius baseline;
- `#8A7462` as the warm-neutral brand and active favorite color;
- hierarchy expressed through spacing and typography, not decorative color;
- Taiwan red means price up and green means price down, only for actual price movement;
- S/A/B/D and role chips use restrained warm-neutral hierarchy;
- favorite controls are small star/bookmark controls, with neutral gray inactive state and `#8A7462` active state, never a huge CTA.

Topic Detail uses an editorial/calm lifecycle timeline as a key visual anchor, not a neon or futuristic graphic. Structural metrics use compact aligned cards/rows. The role-ordered stock list is moderately dense and readable. The Home watch summary is an editorial white block, not a dashboard.

### 23.8 Decision status and dependencies

**FROZEN / CURRENT DECISION:** hierarchy breadcrumb; roles 代表股/核心股/關聯股; unified role-ordered Topic Detail stock list; 收藏題材 + 收藏個股 as separate entity types; 我的收藏 split `題材 | 股票`; saved lists show factual state/change only; saved stocks open the shared Stock Drawer; no per-item recommendation field; restrained 機會 cross-link only; favorite actions on Topic/Stock Detail; compact Home watch summary exists; consistent Modern Financial Workspace visual system.

**PROVISIONAL / TO REVIEW:** exact navigation label `收藏` vs `自選`; exact Home placement of the watch summary; exact subtitle; exact optional 機會 cross-link wording; exact row density and search/filter placement; exact notification event taxonomy and thresholds.

**API/data dependency to verify:** user-scoped saved-item persistence; saved topic/stock payloads; watch counts and factual state changes; event history; optional opportunity cross-link status; institution-flow event markers; topic hierarchy breadcrumb read model; canonical instrument-topic role mapping if not explicit in backend; and lifecycle derivation if not already canonical.

This amendment does not change the product's scoring policy or define browser-side inference. It records presentation and product decisions only.

## 24. PM freeze amendment: Opportunity page / 機會

**Decision status:** `FROZEN / PM-APPROVED`  
**Scope:** customer-facing frontend page and interaction specification only. This amendment does not authorize frontend implementation, backend changes, API changes, schema changes, scoring changes, or production activation.

### 24.1 Product role and core question

The Opportunity page is a core TopicPilot value surface. It answers:

> 「今天有哪些題材值得研究，而其中哪些股票真正通過了我們的技術驗證。」

The page is **theme-first, stock-second**. It is not a generic stock recommendation list and must not imply that every displayed stock is a buy/sell recommendation. The canonical research flow is:

```text
Theme Opportunity
    → Technical Validation
    → Candidate Ranking
    → Stock Drawer
```

TopicPilot sorts research priority rather than hiding information. Technical validation helps users decide what to inspect first; it does not restrict exploration or remove non-priority members from view.

### 24.2 Page shell and sections

The page header contains:

- `機會`;
- a visible update/as-of time;
- a short, deterministic subtitle explaining the research-priority purpose.

Use four segmented sections in this order:

```text
新機會 | 持續追蹤 | 留意變化 | 已失效
```

Each section contains Opportunity Cards. Exact section counts, sorting thresholds, and grouping rules remain data/API dependencies unless already defined by a canonical backend contract.

### 24.3 Opportunity Card

Every Opportunity Card contains, in a calm editorial hierarchy:

1. topic name;
2. current topic grade/state;
3. opportunity age, expressed as `第 N 個交易日`;
4. a human-readable summary;
5. `為什麼值得研究` / why it became an opportunity;
6. technical validation summary in this form: `題材共 X 檔，目前 Y 檔通過技術條件`;
7. the top three priority candidates only, each showing stock name, technical score when available, and topic role;
8. CTA: `查看機會詳情`.

The card is a topic opportunity summary, not a stock wall. It must not expose a long member list or turn technical checks into unexplained recommendation language.

### 24.4 Opportunity Drawer

Clicking `查看機會詳情` opens a right-side Opportunity Drawer. Its interaction and visual language must be consistent with the canonical Stock Drawer: the underlying page remains visible, the drawer is not a separate full-page stock detail implementation, and selecting another item updates the drawer content predictably.

Drawer sections, in order:

1. **Topic identity** — topic name, grade/state, and opportunity age.
2. **Opportunity status** — current section/status and a short human-readable interpretation.
3. **Why included** — deterministic reasons/evidence for inclusion.
4. **Opportunity timeline** — relevant state changes and trading-day context when available.
5. **Technical validation overview** — total members, validated count, and the meaning of the supported statuses.
6. **Candidate tabs** — `優先候選 | 全部成員`.
7. **Risk / invalidation conditions** — concise, evidence-backed conditions that would weaken or invalidate the opportunity.
8. **CTA to Topic Detail** — routes to the existing Topic Detail surface.

### 24.5 Candidate tab A: 優先候選

`優先候選` shows the highest-priority technical candidates for the topic. Each candidate may display:

- technical score, if available;
- topic role;
- a technical checklist showing supported conditions and their status;
- a short risk note.

This is a research-priority ranking, not a mandatory recommendation field. Technical checks must be presented as explainable validation evidence; the browser must not derive or alter the score.

### 24.6 Candidate tab B: 全部成員

`全部成員` must display **all** members of the topic, including stocks that are not priority candidates. The minimum table columns are:

| 股票 | 題材角色 | 技術狀態 | 技術分（若有） | 漲跌幅 |
|---|---|---|---|---|

Non-priority stocks are never hidden. Explain their current state instead of labeling every non-priority row as `FAIL`. Preferred statuses are:

`通過` · `等待確認` · `條件未完整` · `技術偏弱` · `距理想位置偏遠` · `未進深度分析` · `資料不足`

Status wording must reflect the available evaluation state. Missing or deferred evaluation is not equivalent to a failed technical setup.

### 24.7 Stock interaction and component reuse

Clicking **any** stock from either `優先候選` or `全部成員` reuses the existing canonical Stock Drawer. There is no Opportunity-specific stock detail implementation and no second stock-detail interaction model.

The Opportunity page should explicitly reuse:

- Stock Drawer;
- Topic Detail;
- role chips;
- grade chips;
- favorite star;
- update-status/freshness primitives;
- table primitives.

Reuse preserves navigation, terminology, accessibility behavior, freshness treatment, and visual consistency across surfaces.

### 24.8 Opportunity visual direction

Opportunity follows the existing **Modern Financial Workspace** system:

- light mode first;
- warm off-white page background;
- white cards and drawer surfaces;
- `#8A7462` brand accent;
- warm-gray borders;
- low or no shadow;
- restrained 10–12px radius;
- calm editorial financial style;
- Taiwan red/green only for actual price movement.

Opportunity Cards use calm white surfaces, spacing and typography for hierarchy, and restrained warm-neutral status chips. Risk/invalidation uses a restrained amber accent only. Avoid neon, glassmorphism, AI gradients, glowing dashboards, saturated grade colors, and decorative color overload. The Drawer uses the same visual language as the Stock Drawer.

### 24.9 Explicit exclusions

The Opportunity page must not implement:

- a generic stock recommendation list;
- AI-generated freeform buy/sell advice;
- a mandatory recommendation field per stock;
- hidden topic members;
- a separate Opportunity Stock Detail surface.

### 24.10 API/data dependencies and provisional items

The following require verification against existing read models/contracts before implementation: opportunity section/status membership; opportunity age and trading-day timeline; deterministic inclusion reasons; topic member count and complete member list; technical validation statuses and score availability; candidate ranking; risk/invalidation evidence; update/as-of time; topic roles; and the Topic Detail route.

The following remain provisional unless an existing canonical contract already freezes them: exact section ordering rules within each segment; exact card density; exact status-chip copy beyond the preferred statuses above; exact technical checklist taxonomy; exact timeline event taxonomy; and exact drawer width/spacing tokens.

The browser must not calculate technical scores, infer validation status, rank candidates from raw fields, or invent risk conclusions. These are read-model/business-rule responsibilities.

## 25. Completion report for Opportunity amendment

- **Canonical file updated:** this existing canonical frontend design spec was updated in place.
- **Modified sections:** added the PM-approved Opportunity amendment in Section 24; it is the authoritative Opportunity page definition and supersedes earlier provisional Opportunity wording where inconsistent.
- **Frozen Opportunity decisions:** theme-first positioning; four segmented states; Opportunity Cards; right-side Opportunity Drawer; `優先候選 | 全部成員`; all members visible; explainable statuses; shared Stock Drawer interaction; Topic Detail CTA; research-priority philosophy; explicit exclusions.
- **Reused components:** Stock Drawer, Topic Detail, role chips, grade chips, favorite star, update-status/freshness primitives, and table primitives.
- **Remaining provisional items:** exact grouping/sorting thresholds, density, token values, checklist/event taxonomy, and drawer geometry.
- **API/data dependencies:** opportunity membership/age/timeline, inclusion reasons, complete members, validation state/score, ranking, risk evidence, freshness, roles, and Topic Detail routing.
- **Visual/style guidance added:** confirmed Modern Financial Workspace, light mode first, warm off-white/white surfaces, `#8A7462`, warm-gray borders, low shadow, 10–12px radius, restrained market colors, and no neon/glassmorphism/AI gradients.
- **Change boundary confirmed:** no backend, API, schema, scoring, or frontend code changes were made or authorized by this document update.
