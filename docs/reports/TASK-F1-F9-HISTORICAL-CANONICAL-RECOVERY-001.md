# TASK-F1-F9-HISTORICAL-CANONICAL-RECOVERY-001

## F1-F9 Historical Arc — Archaeology, Canonical Recovery, and Disposition Report

**Report status:** `COMPLETE` for repository archaeology and evidence mapping; no product implementation performed.
**Execution date:** 2026-09-15 (Asia/Taipei).
**Execution worktree:** `E:\topicpilot-platform-f1-f9-historical-recovery-001`.
**Execution branch:** `codex/task-f1-f9-historical-recovery-001`.
**Execution base:** `beb5b3d850bb8def248239f829abe39bcd24979b`.
**Canonical repository:** `C:\Users\acer\Desktop\題材領航\topicpilot-platform`.
**Owner checkout handling:** read-only evidence source; no owner-checkout edits.
**Production, push, merge, deploy, migration, Today, B2, A10, A9, Opportunity, Stock, FUND-001, and NEXT_TASK mutation:** `NONE`.

## 1. Executive conclusion

The F1-F9 historical arc is recoverable only in two different senses:

1. **F1-F3:** exhaustive repository archaeology found no recoverable report, path, commit subject, task identifier, or functional alias. Their existence, implementation, ownership, and canonical status cannot be proven from the currently available repository evidence. They are conservatively `UNKNOWN`; they are not reclassified as “never implemented,” and they are not reopened.
2. **F4-F9:** six formal reports and the corresponding aggregate implementation snapshot are recoverable from one historical Today release snapshot, `1501468da8b7b4d8338ae1c2da23996126ee918c`. The snapshot is reachable from two Today remote branches but is not an ancestor of the current governed mainline, the GOV-003 runtime tip, or the development integration base. F4-F8 contain historical PASS closure claims; F9 is explicitly BLOCKED. These are **branch-only historical artifacts**, not current canonical work.

The correct current disposition is therefore:

| Item | Disposition | Canonical reality |
|---|---|---|
| F1-F3 | `UNKNOWN` | no recoverable identity or equivalent proven |
| F4-F9 | `MERGE` candidates, not reopened tasks | functionality must be reconciled into current owning capabilities only through new owner-approved tasks |

No F-series item should be revived as a standalone frontend task. The labels are now provenance labels. The current architecture owns the recoverable concepts under Today/Home, shared V2 state, Stock formal read, WS2 Technical V0, V2 navigation, and Topic/B2.

## 2. Scope and explicit non-scope

### In scope

- F1-F9 identity, aliases, paths, reports, commits, branches, tags, remote refs, worktrees, reflog evidence, and reachable/unreachable object archaeology.
- Historical report content, stated before/after SHA claims, test claims, closure claims, blockers, write sets, and dependency order.
- Current canonical mapping against `origin/main`, current GOV-003 governance state, the development integration base, and later visible development refs.
- Provenance classification: governed artifact, provider/contract, persisted/live/Production, shadow, and fixture.
- Explicit `KEEP`, `PORT`, `MERGE`, `SUPERSEDE`, `DROP`, `OWNER_DECISION_REQUIRED`, and `UNKNOWN` dispositions, with portability notes for merge candidates.
- Governance registration, validation, and recovery-map creation.

### Out of scope

- Product code, API implementation, frontend implementation, generated-client changes, database changes, migrations, seed changes, Production mutation, deployment, push, merge, or operator promotion.
- Reopening F1-F9, creating F9.1/F10, changing Today, B2, A10/A9, Opportunity, Stock, FUND-001, `NEXT_TASK`, or the shared project context.
- Treating dirty-tree code, chat hints, report self-references, or branch presence as canonical completion.

## 3. Authority and repository boundary

The checked-in governance documents identify the nested platform repository as canonical:

```text
C:\Users\acer\Desktop\題材領航\topicpilot-platform
```

The outer workspace repository at `C:\Users\acer\Desktop\題材領航` is a separate, dirty historical workspace and is not the platform owner repository. It was inspected only for repository orientation. Its dirty state was not altered. The nested platform owner checkout was likewise treated as dirty/evidence-only. This task’s changes are isolated to the E worktree listed above.

The evidence anchors used in this report are:

| Anchor | SHA / path | Meaning |
|---|---|---|
| Governed baseline | `origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40` | current repository baseline recorded by project state |
| Development integration base | `a8357d46194f9669709f184949270e20a7a2546c` | main-derived development integration reference |
| GOV-003 runtime tip | `beb5b3d850bb8def248239f829abe39bcd24979b` | governance runtime used for this isolated task |
| Recovery task base | `beb5b3d850bb8def248239f829abe39bcd24979b` | exact base for this E worktree |
| Aggregate F4-F9 source | `1501468da8b7b4d8338ae1c2da23996126ee918c` | historical report and implementation snapshot |
| Today commercial branch tip | `569d2b4d5f4b94c2ab403a440e8b4b02c2fd2586` | branch containing the aggregate snapshot |
| Today production convergence tip | `bf68cc8bf0a4432d7623db43f42e9219c94d7b6b` | second branch containing the aggregate snapshot |
| Later Today development closeout | `5901437ba55661dfee726ea867286e2289541439` | later development ref based on `origin/main`; not itself canonical or Production |

The aggregate snapshot is not an ancestor of `origin/main`, `beb5b3d`, or `a8357d4`. It is not promoted merely because it is reachable from a remote ref.

## 4. Archaeology method and coverage

The nested repository was searched across all available local and remote refs, including named branches, remote branches, tags where present, and worktree-associated refs. The following evidence classes were used:

| Evidence class | Search / inspection | Result |
|---|---|---|
| Task identifiers | full-history subject searches for `TASK-F1` through `TASK-F9`, `TASK-FE-F1` through `TASK-FE-F9`, and report task forms | F4-F9 report evidence found; no F1-F3 hit |
| Functional aliases | Today official market fields, commercial state semantics, Stock formal read, technical evidence, commercial UX/navigation, read-only commercial beta | F4-F9 alias evidence found; no F1-F3 functional alias evidence |
| Paths | full-history path logs and all-ref path inventory | six F4-F9 report paths only; no F1-F3 report paths |
| Pickaxe | `TASK=F1`, `TASK=F2`, `TASK=F3`, `TASK-FE-F1`, `TASK-FE-F2`, `TASK-FE-F3`, and related report markers | no F1-F3 hits |
| Branch containment | `1501468` branch containment | both Today refs contain aggregate snapshot |
| Ancestor checks | aggregate vs mainline, GOV-003, development base | aggregate is not current-mainline ancestry |
| Reflog | all available reflog/worktree entries | recent Today and governance integration refs are visible; no F1-F3 identity recovered |
| Unreachable objects | `git fsck --full --no-reflogs --unreachable` | a large unreachable pool exists; object presence alone is not F identity evidence; no positive F1-F3 identity was established |

The reachable negative search is strong enough to set F1-F3 to `UNKNOWN`, not strong enough to assert deletion, non-implementation, or permanent loss. Unreachable object inventory is not treated as a canonical ref and was not converted into a speculative task lineage.

## 5. F1-F9 inventory

### 5.1 Inventory table

| Item | Identity / title | Evidence location | Best implementation SHA | Best governance SHA | Historical status | Current canonical status | Production status | Disposition |
|---|---|---|---|---|---|---|---|---|
| F1 | unknown | no report/path/alias found | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| F2 | unknown | no report/path/alias found | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| F3 | unknown | no report/path/alias found | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |
| F4 | Today Official Market Fields Consumer | aggregate snapshot report | `1501468...` aggregate only; individual SHA unrecoverable | `1501468...` historical report snapshot; current status governed by `beb5b3d...` | PASS closure claim, branch-only | partially present under Today/Home contracts; dedicated F4 consumer not canonical | development only; pending A10 | `MERGE` |
| F5 | Commercial State Semantics | aggregate snapshot report | `1501468...` aggregate only; individual SHA unrecoverable | `1501468...` historical report snapshot; current status governed by `beb5b3d...` | PASS closure claim, branch-only | partial V2 state surfaces; exact historical shared mapper not canonical | development only | `MERGE` |
| F6 | Stock Formal Read View Unification | aggregate snapshot report | `1501468...` aggregate only; individual SHA unrecoverable | `1501468...` historical report snapshot; current status governed by `beb5b3d...` | PASS closure claim, branch-only | partial current Stock formal EOD/history/read model | development only | `MERGE` |
| F7 | Stock Formal Technical Evidence Consumer | aggregate snapshot report | `1501468...` aggregate only; individual SHA unrecoverable | `1501468...` historical report snapshot; current status governed by `beb5b3d...` | PASS closure claim, branch-only | formal backend Technical V0 exists; historical frontend consumer not canonical | development only | `MERGE` |
| F8 | Commercial UX & Navigation Closure | aggregate snapshot report | `1501468...` aggregate only; individual SHA unrecoverable | `1501468...` historical report snapshot; current status governed by `beb5b3d...` | PASS closure claim, branch-only | current V2 navigation exists; exact F8 behavior not canonical | development only | `MERGE` |
| F9 | Truthful Read-only Commercial Beta Integration Closure | aggregate snapshot report | `1501468...` aggregate only; individual SHA unrecoverable | `1501468...` historical report snapshot; current status governed by `beb5b3d...` | BLOCKED artifact, branch-only | current provider exists; F9 frontend/B2 authority consumer not canonical | development only; blocked before Production | `MERGE` |

`1501468...` is intentionally shown as an aggregate snapshot, never as six individual implementation commits. The six report-level `EXACT_SHA_BEFORE` values are preserved in the provenance JSON. Their corresponding after values are self-referential or absent from the reports and are not invented.

### 5.2 F1-F3: unknown recovery result

No F1, F2, or F3 formal report, named path, commit subject, exact task marker, or functional alias was found in reachable repository history. Current governance documents independently state that F1-F3 have no canonical closure or equivalent mainline evidence and must not be claimed complete. The result is:

```text
F1 = UNKNOWN
F2 = UNKNOWN
F3 = UNKNOWN
```

This means “not recoverable from the available repository evidence.” It does not mean “never existed,” “not implemented,” or “safe to delete.” No future work should use an inferred F1-F3 title or fabricate a lineage.

### 5.3 F4: Today official market fields

The recovered report claims a consumer for official index, turnover, as-of, trading date, unit, EOD/not-live, non-trading-day, null, partial, and unavailable semantics. It explicitly forbids fallback, blending, estimates, and static data. The historical write set included `TodayMarketPage`, `globals.css`, `today-market-fields.ts`, and tests. The report records frontend 182 tests, focused Today 17, backend Today 7 with one Postgres skip, API client 4, TypeScript/build/diff passes, and production pending A10.

Current `origin/main` has formal Home market index/turnover contract work and Today state scaffolding, but the dedicated F4 consumer is not current canonical code. Project context says source-use/persistence/Home/API/frontend rendering remains authority-gated. F4 is therefore a merge candidate into Today/Home after source authority and current Today reconciliation, not a branch revival.

### 5.4 F5: commercial state semantics

The recovered report defines a shared vocabulary: `LOADING`, `ERROR`, `AVAILABLE/PUBLISHED`, `EMPTY`, `PARTIAL`, `STALE`, `UNAVAILABLE`, and `NOT_APPLICABLE`, based on transport, authority, publication, row count, and freshness inputs. It states that Today zero rows are `EMPTY`, Topic leaf empty differs from authority failure, parent Topic can be `NOT_APPLICABLE`, Stock formal EOD can be partial/stale, and only transport failures should retry.

Current V2 pages have status surfaces, but the exact F5 shared mapper and historical presentation code are not canonical. Any future merge must preserve the accepted current state vocabulary and reason metadata; it must not replace current authority semantics with a historical UI helper by name alone.

### 5.5 F6: Stock formal read view

The recovered report converges Stock Explorer, the shared Drawer, and detail on a V2 Stock read model for identity, EOD, raw history, source/as-of/freshness, and published topic relations. It requires exact `(market, instrument_code)` identity and treats ambiguous code without market as unavailable. It forbids snapshot/trigger/recompute/legacy formal reads and forbids guessing a main topic from a relation.

Current Stock code includes formal EOD/history/read surfaces, but it also retains preview/legacy compatibility and does not exactly reproduce the historical market-aware consumer contract everywhere. F6 must merge only as a bounded Stock read-view reconciliation under Stock/WS2 ownership. No historical Stock route or data behavior is to be restored wholesale.

### 5.6 F7: Stock formal technical evidence consumer

The recovered report defines a formal, read-only technical evidence consumer with source, as-of, status, exact identity, and 14 fixed indicator IDs:

```text
MA5, MA10, MA20, MA60, DISTANCE_TO_MA20,
RAW_CLOSE_RETURN_5D, RAW_CLOSE_RETURN_20D,
VOLUME_MA5, VOLUME_MA20, VOLUME_RATIO_20,
RSI14, MACD_12_26_9, MACD_SIGNAL_12_26_9,
MACD_HISTOGRAM_12_26_9
```

It explicitly excludes technical scores, selectors, recommendations, institutional flow, news, fundamentals, Opportunity, Lifecycle, and advanced indicator families. The historical report records focused 52, clean frontend 195, dirty frontend 198, backend technical 33, API client 4, and clean-candidate validation.

Current backend Technical V0 publication and route exist, but current frontend Stock code still uses an older `technicalEvidence` shape and disables technical filters; the historical fixed-ID consumer is not canonical. F7 merges into WS2 Technical V0 only after the provider/consumer contract is accepted. No new indicators or strategy logic are authorized by this map.

### 5.7 F8: commercial UX/navigation

The recovered report closes commercial header/navigation around Today, Topic, Stock, and Favorites, while presenting Opportunity and AI Research as explicit unpublished boundaries. It removes unfinished search/notification/account controls from the commercial header, preserves Topic as-of, makes leaf-to-Stock links market-aware, and marks legacy Watchlist/Studio as Legacy Preview/DEMO. It records clean frontend 201, dirty frontend 204, TypeScript/build/diff pass, and no Production work.

Current V2 surfaces provide a modern navigation foundation, but current `AppNav`/`V2Foundation` still expose placeholders and routes that do not equal the historical F8 contract. F8 is a merge candidate into the current V2 product surface, with serial UI ownership. It must preserve truthful unpublished boundaries and must not activate Opportunity or AI Studio.

### 5.8 F9: truthful read-only commercial beta integration

F9 is not a successful closure. The report says Today and Stock checks passed, but Topic commercial integration failed because the exact committed baseline lacked the `/api/v2/topic-catalog` routes required by the frontend. The apparent provider existed only in uncommitted dirty-tree files (`topic_catalog.py`, `topic_catalog_api.py`, schemas/tests/router changes). The Today-to-Topic journey therefore reached a 404. The report marks F9 blocked and explicitly says there should be no F9.1/F10 frontend task.

Current `origin/main` now contains a Topic catalog backend provider and generated route declarations, but that later availability does not canonize the old F9 frontend snapshot or resolve the B2 formal authority/publication gap. F9 is a merge candidate into a new Topic/B2 read-only consumer task after B2 authority is accepted. The dirty provider must not be treated as historical canonical evidence.

## 6. Commit, branch, and lineage reconstruction

### 6.1 What is recoverable

All six F4-F9 report paths have the same reachable path-history commit:

```text
1501468da8b7b4d8338ae1c2da23996126ee918c
parent 12b0c7c97031f223fe61c6ffe9de016852214fc5
2026-09-12T23:33:54+08:00
release(today): commercial investor market view
```

The commit contains the six formal reports and a large aggregate Today/Stock/UI snapshot. It is reachable from the two Today remote refs listed in Section 3. It is not the same thing as six task commits.

### 6.2 What is not recoverable

The reports state these historical before SHAs:

| Item | Reported before SHA | After SHA |
|---|---|---|
| F4 | `b8f854db08de379c6d9b6eba27575fc4afd5cc45` | self-referential / not recoverable |
| F5 | `1fec0260c2e0fa2b3e4b9592294dc5e34281d5f5` | self-referential / not recoverable |
| F6 | `09bc660e6a660afff2ac86076a0e42c6ea8e01c1` | self-referential / not recoverable |
| F7 | `1e8baf6d99c2c960eda7490de345a6b34d1393fc` | self-referential / not recoverable |
| F8 | `e814e78780fce303ab9d823ecc51dcf2bac9de0c` | self-referential / not recoverable |
| F9 | `909c7600001e43e17f216cd8fed51ebda94805b3` | self-referential / not recoverable |

The six before SHAs and their report messages do not resolve as current repository objects or `git log --all --grep` subjects. The reports describe their after values as “after commit” or a final-handoff self-reference. No after SHA is invented here.

### 6.3 Branch-only reality

F4-F9 report artifacts are retained on historical Today branches. Branch reachability is evidence of historical retention, not canonical promotion. Current governance documents classify F4-F9 as `SUPERSEDED` / `BRANCH_ONLY_CLOSED` for the current base; F9’s own blocked report makes the series-level result `PARTIAL`, not fully closed.

Later Today integration refs visible in the repository, including `5901437ba55661dfee726ea867286e2289541439` (`docs(integration): close Today canonical development series`), do not contain the old F1-F9 task labels as new canonical tasks. `origin/main` is an ancestor of that development ref, but the development ref is not `origin/main` and is not Production. It is separate current Today work and remains outside this task’s scope. Its existence reinforces the requirement to map capabilities by current owner rather than graft the old F labels onto new work.

## 7. Historical closure and test claims

### 7.1 Reported test evidence

| Item | Historical evidence reported | Interpretation |
|---|---|---|
| F1-F3 | none | `TESTS_EXIST=UNKNOWN`; no current claim |
| F4 | frontend 182; focused Today 17; backend Today 7 plus one skipped Postgres; API client 4; tsc/build/diff | historical isolated/candidate evidence only |
| F5 | frontend 193; focused 47; API client 4; tsc/build/diff | historical isolated/candidate evidence only |
| F6 | frontend 190; focused Stock 47; backend EOD 13 plus five skipped Postgres; API client 4; tsc/build/diff | historical isolated/candidate evidence only |
| F7 | dirty frontend 198; clean frontend 195; focused 52; backend technical 33; API client 4; tsc/build/diff | historical clean-candidate evidence; dirty owner overlay had a pre-existing Today error |
| F8 | dirty frontend 204; clean frontend 201; tsc/build/diff | historical clean-candidate evidence only |
| F9 | focused 76; clean frontend 202; shared frontend 205; backend Home/Stock 45; API client 4; tsc/build/diff; browser smoke preserved | historical blocked integration evidence only |

### 7.2 Current test status

No current F-item implementation test suite was rerun for this archaeology task. The current code has diverged from the aggregate snapshot and the exact historical task commits are absent. Therefore:

```text
CURRENT_TESTS_PASS(F1..F9) = NOT_RUN
HISTORICAL_TEST_CLAIMS(F4..F9) = PRESERVED_AS_REPORTED
```

The historical counts are not promoted to current pass claims.

## 8. Current architecture mapping

### 8.1 F4 to Today/Home

Current Home publication has formal index/turnover fields and typed generated-client contracts; current Today rendering has market overview state and as-of/source displays. The dedicated F4 `today-market-fields.ts` consumer is absent from current canonical paths. The remaining gap is source-use/persistence/publication reconciliation under Today authority, not permission to copy the historical branch.

### 8.2 F5 to shared V2 state

Current V2 pages expose semantic state and backend reason metadata, but not the exact historical shared commercial state mapper. A future merge must be evaluated against current state vocabulary and authority/publication semantics. It must not downgrade authority failure to `EMPTY`, use transport retry for semantic failure, or treat stale/partial as available without disclosure.

### 8.3 F6 to Stock formal read

Current Stock surfaces include code/name search, formal EOD, detail, Explorer, Drawer, raw historical bars, source/as-of/freshness, and topic relations. Preview/legacy compatibility remains visible in current code. The historical F6 exact market-aware consumer is therefore a partial semantic predecessor, not a drop-in current implementation.

### 8.4 F7 to WS2 Technical V0

Current backend Technical V0 policy/publication and the generated technical route are the current authority boundary. The historical F7 frontend consumer is not present as an exact canonical surface. The correct future action is a bounded provider-consumer reconciliation against the current 14-ID policy, not a new technical indicator or selector project.

### 8.5 F8 to current V2 navigation

Current V2 foundation, page shell, and route components are the current navigation surface. The historical F8 report is useful as a behavior specification for truthful commercial boundaries and legacy disclosure, but its exact `AppNav`/page implementation is not canonical. Shared UI ownership makes this serial integration work.

### 8.6 F9 to Topic/B2

Current backend Topic catalog routes exist on `origin/main`, whereas the historical F9 baseline lacked them. Current Topic/B2 formal role/authority/publication remains governed separately and is not fully active. The correct future action is a new, bounded, read-only Topic/B2 consumer reconciliation after B2 acceptance. F9 itself stays branch-only blocked evidence.

## 9. Data authority and provenance classification

| Item | Historical input/output classification | What is not established |
|---|---|---|
| F1-F3 | `UNKNOWN` | no source, provider, persisted table, or Production status recoverable |
| F4 | governed typed contract/consumer artifact; test fixtures `SHADOW`/`FIXTURE`; provider/source use not proven persisted | no Production, no canonical persistence, no live writer |
| F5 | governed UI/state artifact; semantic metadata contract; tests `SHADOW`/`FIXTURE` | no authority/provider implementation and no Production |
| F6 | governed formal read contract/consumer; raw historical fixture data `SHADOW`/`FIXTURE` | no write path, snapshot trigger, recompute, or Production |
| F7 | governed Technical V0 contract/consumer artifact; historical technical responses `SHADOW`/`FIXTURE` unless supplied by formal provider | no technical score, selector, strategy, institutional-flow, or Production claim |
| F8 | governed UI/navigation artifact; browser/test surfaces `SHADOW`/`FIXTURE` | no product publication or Production promotion |
| F9 | historical UI artifact plus a dirty-tree provider appearance; provider at the exact F9 baseline `SHADOW`/uncommitted | no committed provider in F9 baseline, no canonical Topic publication, no Production |

No F4-F9 report supplies evidence of a Production database row, live scheduler, post-close writer, deployment digest, or operator readback. No F-series data should be labeled `PERSISTED`, `LIVE`, or `PRODUCTION_VERIFIED`.

## 10. Production, release, and migration status

Every recovered F4-F9 report explicitly records no push, merge, deploy, or Production mutation. F4/F5/F9 state production as pending A10 or otherwise blocked; F6/F7/F8 report no Production validation. Current project state further says the Production API reference diverges from the canonical baseline and exact Web/Worker/DB SHAs are not verified; the release gate remains operator-gated.

Accordingly:

```text
F1-F3 PRODUCTION_STATUS = UNKNOWN
F4-F9 PRODUCTION_STATUS = DEVELOPMENT_ONLY
F1-F9 PRODUCTION_VERIFIED = NO
MIGRATION_SCOPE = NONE
0040 / POST_CLOSE / A10 / A9 = untouched by this task
```

The F arc does not authorize migration `0040`, Today promotion, B2 authority population, Opportunity publication, Stock provider changes, or FUND-001 initiation.

## 11. Obsolete and non-returnable historical designs

The following historical behaviors must not be returned merely because they existed in the aggregate snapshot:

| Area | Do not return |
|---|---|
| F4 / Today | index/turnover blending, estimates, static fallback data, non-official fallback, or treating not-live data as live |
| F5 / state | authority failure as empty, semantic failure as transport retry, partial/stale as silently available, or generic retry loops |
| F6 / Stock | first-match code identity, snapshot/trigger/recompute reads, legacy formal routes, frontend recomputation, or guessed main topic |
| F7 / technical | old boolean 20/60MA display as formal evidence, technical scores, selectors, recommendations, new indicators, or strategy logic |
| F8 / navigation | unfinished global controls in commercial header, Opportunity/AI Research as published, silent legacy fallback, or misleading route labels |
| F9 / integration | dirty-tree provider adoption, 404 treated as success, uncommitted schema/router assumptions, or formal data claimed without current authority |
| F1-F3 | any inferred title, implementation, owner, SHA, or “not implemented” conclusion |

## 12. Disposition rules

The allowed disposition vocabulary is interpreted as follows for this report:

- `KEEP`: exact artifact is current canonical and should remain unchanged.
- `PORT`: useful artifact has no sufficient current owning equivalent and may be transferred after owner approval.
- `MERGE`: useful capability maps into an existing current owning subsystem; do not revive the old task.
- `SUPERSEDE`: historical artifact is replaced by a current governed contract or design.
- `DROP`: artifact is proven obsolete and not reusable.
- `OWNER_DECISION_REQUIRED`: an owner must choose before execution; not silently inferred.
- `UNKNOWN`: evidence is insufficient to establish identity, status, or safe disposition.

### 12.1 Final dispositions

| Item | Final disposition | Rationale |
|---|---|---|
| F1-F3 | `UNKNOWN` | no recoverable identity or equivalent; no safe claim possible |
| F4 | `MERGE` | Today/Home contracts and consumer surface exist in part; exact F4 code is not canonical |
| F5 | `MERGE` | current V2 state surfaces exist; historical shared mapper is not canonical |
| F6 | `MERGE` | current Stock formal read surfaces exist; exact market-aware historical contract needs bounded reconciliation |
| F7 | `MERGE` | current Technical V0 provider exists; historical fixed-ID consumer needs WS2/Stock reconciliation |
| F8 | `MERGE` | current V2 navigation exists; historical truthful-boundary behavior should be reconciled into it |
| F9 | `MERGE` | current Topic provider exists, but consumer and B2 authority remain separate/currently incomplete |

There are no evidence-backed `KEEP`, `PORT`, or `DROP` candidates. There is no safe automatic `SUPERSEDE` for F1-F3. The old F4-F9 tasks are superseded as standalone task identities for the current base, but their capabilities are retained as merge evidence.

## 13. Portability assessment for F4-F9 merge candidates

### F4 portability

- **Source evidence:** TodayMarketPage, `today-market-fields.ts`, associated CSS/tests, aggregate snapshot `1501468...`.
- **Target owner:** Today / Integration.
- **Target surfaces:** current Today/Home publication contract, `TodayMarketPage`, generated client/shared schemas only through explicit reconciliation.
- **Dependencies:** official index/turnover source authority, date/as-of/unit contract, current Today integration status.
- **Collision risk:** high; current Today work and shared API/generated-client surfaces are active and diverged.
- **Migration/Production:** none.
- **Required tests:** official-field identity, unit/scale, EOD/not-live, null/partial/unavailable, no fallback, source/as-of parity.

### F5 portability

- **Source evidence:** commercial-state mapper files, Today/Topic/Stock F5 hunks, state tests, aggregate snapshot.
- **Target owner:** Frontend / Integration.
- **Target surfaces:** current V2 state vocabulary and reason metadata across Today, Topic, Stock.
- **Dependencies:** accepted authority/publication/freshness semantics.
- **Collision risk:** high; shared frontend behavior means one owner and explicit reconciliation.
- **Migration/Production:** none.
- **Required tests:** empty vs unavailable, partial/stale, semantic error vs transport retry, parent/leaf Topic states.

### F6 portability

- **Source evidence:** `stock-api.ts`, Stock Explorer, Drawer, detail route, history panel, F6 tests.
- **Target owner:** Stock / WS2.
- **Target surfaces:** current Stock formal EOD/history/read model and market-aware identity.
- **Dependencies:** formal Stock identity, EOD, raw history, topic relation publication.
- **Collision risk:** high; current Stock compatibility/preview code and F7 technical consumer overlap.
- **Migration/Production:** none.
- **Required tests:** exact market/code identity, ambiguous code unavailable, raw history, adjustment unknown, source/as-of/freshness, no recompute or guessed topic.

### F7 portability

- **Source evidence:** historical technical consumer, Drawer/Explorer consumer changes, 14-ID tests, aggregate snapshot.
- **Target owner:** WS2 / Stock technical.
- **Target surfaces:** current Technical V0 publication, generated route, Stock technical read surface.
- **Dependencies:** formal provider status/source/as-of, 14-ID indicator policy, no selector/recommendation semantics.
- **Collision risk:** high; current Stock uses older `technicalEvidence` shape and disabled filters.
- **Migration/Production:** none.
- **Required tests:** all 14 IDs, exact identity/date/authority, source/as-of/status, partial/unavailable, Drawer/detail parity.

### F8 portability

- **Source evidence:** V2Foundation, V2Page, Topic/Stock routes, AppNav, legacy disclosure, UX tests.
- **Target owner:** Frontend / Integration.
- **Target surfaces:** current V2 navigation shell and route boundaries.
- **Dependencies:** accepted commercial route/publication contract and current Topic/Stock/Today state.
- **Collision risk:** high; active route and placeholder surfaces must be reconciled serially.
- **Migration/Production:** none.
- **Required tests:** route visibility, unpublished boundaries, legacy labels, Topic as-of, market-aware leaf-to-Stock, responsive/accessibility.

### F9 portability

- **Source evidence:** Topic catalog pages/routes, F9 cross-page tests, historical dirty-provider blocker.
- **Target owner:** Topic/B2 + Integration.
- **Target surfaces:** current Topic catalog provider, generated client, Topic list/detail/snapshot/history, Stock links.
- **Dependencies:** B2 formal role/authority/publication, current provider contract, truthful 404/unavailable behavior.
- **Collision risk:** high; current provider exists but the old consumer does not, and B2 remains authority-gated.
- **Migration/Production:** none.
- **Required tests:** list/detail/snapshot/history, 404/unavailable, no dirty provider assumptions, as-of/state/identity parity, Topic-to-Stock links.

## 14. Cross-task relationship matrix

| Current initiative | F4 | F5 | F6 | F7 | F8 | F9 |
|---|---:|---:|---:|---:|---:|---:|
| Today | direct predecessor/input | shared state consumer | downstream Stock link only | none | shared navigation | Today-to-Topic journey boundary |
| B2 | none | none | Topic relation boundary only | none | Topic route boundary | direct authority dependency |
| A10/A9 | read freshness/as-of boundary only | none | none | none | none | none |
| Opportunity | no | no | no | no | unpublished disclosure only | no |
| Stock | downstream target | shared state consumer | direct target | direct technical target | navigation target | leaf-link target |
| FUND-001 | no | no | no | explicitly unchanged | no | no |

`FUND001_REUSABLE_HISTORY=NO`. The F reports do not implement formal institutional-flow capability. F7 explicitly leaves institutional flow unchanged; F4-F9 treat it as separate/deferred. Incidental legacy fields do not create reusable provenance.

## 15. Dependency and parallelism map

### Historical sequence

The report baselines support:

```text
F4 -> F6 -> F5 -> F7 -> F8 -> F9
```

This sequence is historical evidence only. It is not an instruction to replay the old branch.

### Future execution sequence

```text
Current Today/Home authority
  -> F4 bounded consumer reconciliation
  -> F5 shared state reconciliation

Current Stock formal read authority
  -> F6 bounded read-view reconciliation
  -> F7 Technical V0 consumer reconciliation

Accepted V2 commercial surface
  -> F8 navigation reconciliation

Accepted B2 Topic authority + current Topic provider
  -> F9 Topic consumer reconciliation
```

The future tasks are serial where they touch shared frontend, generated client, API contracts, Topic routes, or Stock views. Only read-only archaeology and documentation can safely run now.

### Parallel buckets

```yaml
SAFE_TO_RUN_NOW:
  - TASK-F1-F9-HISTORICAL-CANONICAL-RECOVERY-001 (completed; archaeology/governance only)
WAIT_FOR_B2:
  - F9 merge candidate
  - any F6/F8 Topic-role extension
WAIT_FOR_A9:
  - none
WAIT_FOR_OPPORTUNITY:
  - none
SERIAL_INTEGRATION_REQUIRED:
  - F4 Today/Home
  - F5 shared V2 state
  - F6 Stock formal read
  - F7 WS2 Technical V0 consumer
  - F8 V2 commercial navigation
  - F9 Topic/B2 consumer
```

## 16. Governance artifacts created

- Formal report: `docs/reports/TASK-F1-F9-HISTORICAL-CANONICAL-RECOVERY-001.md`.
- Recovery map: `docs/reports/TASK-F1-F9-HISTORICAL-CANONICAL-RECOVERY-001/F1-F9-RECOVERY-MAP.md`.
- Provenance artifact: `docs/reports/TASK-F1-F9-HISTORICAL-CANONICAL-RECOVERY-001/f1-f9-provenance.json`.
- Task manifest: `docs/governance/tasks/TASK-F1-F9-HISTORICAL-CANONICAL-RECOVERY-001.yaml`.
- Ownership registration: `docs/governance/WORKSTREAM_OWNERSHIP.yaml` now recognizes this report/map namespace as GOVERNANCE-owned.

The manifest is `PARTIAL` because archaeology is complete but F1-F3 are conservatively unknown and F4-F9 require separate owner-approved merge work. `owner_decision_required=true` applies to future product execution, not to the evidence conclusions in this report. No product code or shared product contract was changed.

## 17. Validation and gate results

The following checks are required for this governance-only change and are recorded after the local commit in the final handoff:

| Check | Expected / actual interpretation |
|---|---|
| Governance self-test | must pass |
| Task manifest validation | must pass without implementation-commit check because this is archaeology-only |
| Worktree/branch/base validation | must pass on the isolated E worktree |
| Ownership validation | must pass for the report, map, provenance, manifest, and registry change |
| JSON/YAML parse validation | must pass |
| Diff whitespace/conflict scan | must pass |
| Governance Python compile/lint | run against unchanged governance tooling; failure is reported separately if environment lacks tool |
| Release gate | no release candidate is being promoted; migration boundary remains blocked/untouched |

## 18. Remaining owner decisions

No owner decision is required to accept this archaeology report. Owner decisions are required before any future implementation task:

1. whether to activate a bounded F4 Today/Home consumer reconciliation after the current Today/source-authority closeout;
2. whether to activate F5 as a shared V2 state reconciliation;
3. whether to activate F6/F7 under Stock/WS2;
4. whether to activate F8 under the accepted current V2 commercial surface;
5. whether to activate F9 under B2 formal Topic authority;
6. whether any external evidence should resolve F1-F3, or whether the owner explicitly retires them without claiming implementation history.

No decision may be inferred from this report, and no historical task is automatically reopened.

## 19. Final evidence-grade conclusion

The historical arc has been recovered as far as the repository allows. F4-F9 are preserved with exact report paths, aggregate snapshot provenance, branch locations, reported test evidence, blockers, and current capability mappings. F1-F3 are preserved as unknowns rather than erased or invented. The current architecture, not the historical F labels, is the canonical planning surface. Future work must be new, bounded, owner-approved, serially reconciled, and read-only unless a later task explicitly authorizes implementation.

## 20. Required final fields

```yaml
TASK_ID: TASK-F1-F9-HISTORICAL-CANONICAL-RECOVERY-001
EXECUTION_WORKTREE: E:\\topicpilot-platform-f1-f9-historical-recovery-001
EXECUTION_BRANCH: codex/task-f1-f9-historical-recovery-001
TASK_BASE_SHA: beb5b3d850bb8def248239f829abe39bcd24979b
GOVERNED_BASELINE: origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40
DEVELOPMENT_INTEGRATION_BASE: a8357d46194f9669709f184949270e20a7a2546c
HISTORICAL_F4_F9_SNAPSHOT: 1501468da8b7b4d8338ae1c2da23996126ee918c
F1_F3_RECOVERY: COMPLETE
F1_F3_STATUS: UNKNOWN / UNRECOVERABLE_FROM_AVAILABLE_REPOSITORY_EVIDENCE
F4_F9_BRANCH_ONLY_CLOSURE: PARTIAL
F4_F9_CANONICAL_STATUS: BRANCH_ONLY / NOT_CURRENT_CANONICAL
F4_F9_DISPOSITION: MERGE_CANDIDATES_INTO_CURRENT_OWNING_CAPABILITIES
PORT_CANDIDATES: NONE
KEEP_CANDIDATES: NONE
DROP_CANDIDATES: NONE
FUND001_REUSABLE_HISTORY: NO
A10_A9_OVERLAP: BOUNDARY_ONLY / NO_DUPLICATED_WRITER_SCHEDULER_MIGRATION
NEW_PRODUCT_CODE: NONE
PRODUCTION_MUTATION: NONE
PUSH_MERGE_DEPLOY: NONE
OWNER_DECISION_REQUIRED: NO_FOR_ARCHAEOLOGY / YES_FOR_ANY_FUTURE_PRODUCT_MERGE
GOVERNANCE_STATUS: REGISTERED_PENDING_OWNER_REVIEW
```

## 21. Handoff

The machine-readable provenance and compact map are colocated with this report. The task’s local governance commit SHA is recorded in the final response after validation. It is not pushed or merged. The owner checkout remains untouched.
