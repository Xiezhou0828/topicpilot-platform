# FUND-C Opportunity institutional-evidence canonical reconciliation

Task: `TASK-INT-FUND-C-OPPORTUNITY-INSTITUTIONAL-EVIDENCE-CANONICAL-RECONCILIATION-001`
Role: `INTEGRATION_OWNER`
Mode: `ONE_SHOT_FORWARD_CANONICAL_RECOVERY_FUND_C_RECONCILIATION_INTEGRATION_AND_CLOSEOUT`

## Result

`COMPLETE_WITH_EXTERNAL_GATE`

FUND-C is integrated into a forward development candidate as evidence
enrichment only. The formal Opportunity provider and Production release remain
separate external gates. No Production, database, migration, deployment,
replay, canary, push, C checkout, or `NEXT_TASK` mutation was performed.

## Canonical recovery and integration method

| Item | Recovered value |
| --- | --- |
| Reported canonical base | `18a0428af2988ff65becdf14b09f0fede8d81d0c` |
| Actual pre-integration canonical base | `b3094cec79c34052131e3bcfe0e8db1a895788a9` |
| Was `18a0428` still current? | No. It is the unified code head recorded by the previous closeout; `b3094ce` is the later governance closeout and current authoritative development tip. |
| FUND-C implementation source | `a0a553613983558b552e2a586bd7444187f3eb4e` |
| FUND-C scope-cleanup source | `05ae03fa937b73b85807acada7a82be54ef2caec` |
| FUND-C source governance | `817c78f1e98832aa892ff91a7f41d26b67b6e083` |
| Final approved FUND-C code state | `05ae03f` after removal of the out-of-scope package export; governance commit is provenance evidence, not code input. |
| Source base relation | FUND-C source parent is exactly `b3094ce`; no semantic rebase was required. |
| FUND-B contract compatibility | `IDENTICAL` |
| Integration method | `CLEAN_CHERRY_PICK`; source implementation and scope-cleanup commits were replayed onto a fresh worktree based on `b3094ce`. |
| Reconciled code commits | `f292530` (implementation), `c702518` (scope cleanup) |
| Canonical integration SHA | `c7025182349f93869eead2017d395b847744c9c9` |
| Post-integration code head | `c7025182349f93869eead2017d395b847744c9c9` |

The full SHA for the second integration commit is recorded after the clean
cherry-pick; its short form is shown above for readability. The final
governance closeout commit is intentionally reported in the machine-readable
packet using the non-self-referential marker `FINAL_CLOSEOUT_COMMIT`; the
actual commit SHA is the final commit containing this packet.

## Capability preservation

| Capability | Pre | Post |
| --- | --- | --- |
| FUND-A | canonical | canonical |
| FUND-B | canonical | canonical |
| FUND-C | completed source branch | canonically integrated in development candidate |
| Daily Close remediation | canonical | canonical |
| Opportunity Strategy | canonical | unchanged |
| Opportunity Selector | canonical | unchanged |
| C1-C5 | frozen | unchanged |
| S1-S2 | frozen | unchanged |
| Opportunity eligibility | frozen | unchanged |
| Opportunity ranking | frozen | unchanged |
| Institutional composite score | absent | absent |
| FUND-E | absent | absent |
| Alembic heads | 1 | 1 |

The current canonical FUND-B implementation/schema/API is consumed without
provider duplication. FUND-C adds no TWSE/TPEx I/O, normalization, persistence,
window, streak, reversal, price-flow, divergence, or liquidity-relative
calculation. It validates and copies the canonical FUND-B projection, binds it
to the Opportunity date, and exposes an optional read-model field.

## FUND-C V1 contract

FUND-C V1 is `OPPORTUNITY_INSTITUTIONAL_EVIDENCE_ENRICHMENT`. It is not scoring,
gating, ranking, or a selector dependency.

| Evidence dimension | Canonical source | TPE status | TWO status | Unit | Date semantics | Freshness semantics | Selection effect |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Current session flow | FUND-B `fund-b.stock-institutional-flow.v1` | complete | current snapshot only | SHARES, scale 0 | requested date must equal Opportunity `asOf` | copied `CURRENT`/`STALE`/`UNKNOWN` | NONE |
| Foreign, investment-trust, dealer, total legs | FUND-B canonical fact | complete | current snapshot when available | SHARES, scale 0 | canonical session date | canonical status/freshness preserved | NONE |
| 1D / 5D / 10D / 20D windows | FUND-B windows | complete when canonical history is complete | `PARTIAL` where current-only history is unavailable | SHARES, scale 0 | exchange-session windows only | explicit incomplete/unavailable state | NONE |
| Streaks | FUND-B streaks | available from canonical sessions | unavailable when history is absent | session count | no synthetic sessions | explicit `UNKNOWN`/unavailable | NONE |
| Reversal | FUND-B deterministic evidence | available when adjacent sessions exist | unavailable without history | N/A | adjacent canonical sessions | explicit unavailable state | NONE |
| Price-flow context | FUND-B evidence | available when inputs exist | unavailable when inputs are missing | SHARES for flow | aligned canonical date | canonical freshness | NONE |
| Divergence | FUND-B evidence | available when inputs exist | unavailable when inputs are missing | N/A | aligned canonical date | canonical freshness | NONE |
| Liquidity-relative flow | FUND-B evidence | valid positive-volume denominator only | unavailable when denominator/history is absent | shares/shares | aligned canonical date | canonical freshness | NONE |
| Source/provenance | FUND-B source and fact metadata | preserved | preserved when supplied | N/A | `sourceAsOf`, `fetchedAt`, session dates | explicit | NONE |
| Alignment classification | FUND-C boundary | `POLICY_DECISION_REQUIRED` | `POLICY_DECISION_REQUIRED` | N/A | Opportunity date binding | N/A | NONE |

TPE evidence is complete when the canonical FUND-B fact is complete. TWO remains
`PARTIAL` and current-snapshot-only; absent persisted history does not become
fabricated 5D/10D/20D windows, streaks, reversals, or divergence. Missing
evidence remains `null`/unavailable and is distinct from an explicit source
reported zero. SUPPORT/CONFLICT/NEUTRAL policy remains
`POLICY_DECISION_REQUIRED`; no threshold was invented.

## Opportunity boundary

The adapter is called only at the evidence/read-model boundary. It does not
feed Strategy, Selector, qualification, C1-C5, S1-S2, eligibility, ranking, or
publication policy. The optional `OpportunityReadModel.institutional_evidence`
field is projected to the shadow card; additive formal schema declarations do
not claim formal provider availability.

| Boundary | Result |
| --- | --- |
| Strategy changed | NO |
| Selector changed | NO |
| C1-C5 changed | NO |
| S1-S2 changed | NO |
| Eligibility changed | NO |
| Ranking changed | NO |
| Composite institutional score created | NO |
| FUND-C selection effect | NONE |
| Opportunity API readiness | READY_WITH_GAPS |
| Formal Opportunity provider | UNAVAILABLE_INCOMPLETE |
| Opportunity Daily Recommendation ready | NO |
| FUND-E implemented | NO |

The positive Opportunity fixture is test-only synthetic/deterministic evidence:
the candidate remains selected, its identity/rank/order/eligibility are
unchanged, and institutional evidence is attached to the shadow read model.
It is not a historical market claim.

## Frozen regression results

| Regression | Expected | Actual |
| --- | --- | --- |
| 2026-09-16 final candidates | 0 | 0, preserved from source authority and no candidate-selection path was changed |
| 2026-09-16 candidate-set change | NO | NO |
| TWO 6173 C5 | NO_BREAKOUT | NO_BREAKOUT; close 315 is not greater than frozen reference 321, despite high 323 |
| Strategy changed | NO | NO |
| Selector changed | NO | NO |
| C1-C5 changed | NO | NO |
| S1-S2 changed | NO | NO |
| Eligibility changed | NO | NO |
| Ranking changed | NO | NO |
| Composite score created | NO | NO |
| TWO fabricated history | NO | NO |
| Look-ahead violations | 0 | 0 |
| Positive fixture enrichment | selected/rank unchanged | PASS, test-only |
| Alembic head count | 1 | 1 |

The 2026-09-16 zero-candidate result is preserved from the completed shadow
reconstruction authority and FUND-C source replay. The committed FUND-C suite
also directly verifies the 6173 close-vs-reference C5 predicate and future-date
rejection.

## Validation and failure classification

- FUND-C / Opportunity / FUND-B focused backend: **87 passed**.
- Full backend: **770 passed, 14 failed, 59 skipped**.
- The 14 failures exactly match the current registered baseline registry:
  9 TOPIC_B2 lifecycle-contract/engine tests and 5 WS3 research-confirmatory
  tests. They are outside the FUND-C write set and reproduce the prior
  canonical baseline; they are not task-caused.
- PostgreSQL tests: **59 skipped** because no approved test database URL was
  configured. No migration was executed.
- API client: **6 passed**.
- OpenAPI drift: **PASS**.
- Generated client drift: **PASS** after governed generation.
- Web build: **PASS**.
- Web tests: **165 passed**.
- Web lint: **0 errors, 2 existing warnings**.
- Changed-file Ruff check: **PASS**.
- Ruff format: new FUND-C file and FUND-C test are formatted; existing
  formatting debt in shared `schemas.py` and pre-existing portions of
  `opportunity_contract.py` remains unchanged and is not task-caused.
- Compileall: **PASS**.
- `git diff --check`: **PASS**.
- Conflict-marker scan: **PASS**.
- Alembic heads: **one**, `0042_task_fund_b_stock_institutional_flow_forward`.
- Migration execution: **NONE**.

The earlier 14-vs-9 difference is a validation-scope difference, not a new
regression. The current governed registry contains 14 entries: 9 TOPIC_B2 and
5 WS3. The FUND-C source closeout's 9-count was its scoped/source-run figure;
the current full-suite run is authoritative for this reconciliation and keeps
all 14 registry entries classified as `REGISTERED_BASELINE`. No registry entry
was edited to make this task pass. Task-caused failures are zero and unknown
failures are zero.

## Required questions

1. The actual authoritative canonical base was `b3094cec79c34052131e3bcfe0e8db1a895788a9`.
2. `18a0428` was not still current; it was the prior unified code head, while `b3094ce` was the later closeout tip.
3. C differs because it is the protected owner checkout on the separate runtime-audit branch with pre-existing dirty/untracked entries; it is not development canonical authority.
4. Full FUND-C source SHAs: implementation `a0a553613983558b552e2a586bd7444187f3eb4e`, scope cleanup `05ae03fa937b73b85807acada7a82be54ef2caec`, governance `817c78f1e98832aa892ff91a7f41d26b67b6e083`.
5. The final approved source code state was `05ae03f`, after scope cleanup removed the out-of-scope package export.
6. Integration method was `CLEAN_CHERRY_PICK` onto exact parent `b3094ce`.
7. Yes, FUND-C consumed the current canonical FUND-B contract identically.
8. No FUND-B provider logic was duplicated.
9. TPE institutional evidence is complete when canonical FUND-B history is complete.
10. TWO is partial/current-snapshot-only; unavailable historical windows and derived history are not synthesized.
11. Yes, missing evidence remains distinct from explicit zero.
12. Strategy: no.
13. Selector: no.
14. C1-C5: no.
15. S1-S2: no.
16. Eligibility: no.
17. Ranking: no.
18. Composite institutional score: no.
19. Yes, 2026-09-16 remains zero candidates.
20. Yes, 6173 remains C5 `NO_BREAKOUT`.
21. No look-ahead value violation occurred.
22. FUND-C added no migration.
23. Final Alembic head count is 1.
24. Final Alembic head is `0042_task_fund_b_stock_institutional_flow_forward`.
25. FUND-A and FUND-B were preserved: yes.
26. Daily Close remediation was preserved: yes.
27. B2/Topic policies changed: no.
28. FUND-E implemented: no.
29. Actual tests are recorded above: focused 87 passed; backend 770 passed / 14 registered baseline failures / 59 skipped; API client 6 passed; web 165 passed; build, OpenAPI, generated client, compileall, diff and conflict checks passed.
30. Current baseline is 14 because the current registry includes 9 TOPIC_B2 plus 5 WS3 entries; the source report's 9 was scoped validation evidence.
31. Task-caused failures are zero.
32. Unknown failures are zero.
33. Canonical integration SHA: `c7025182349f93869eead2017d395b847744c9c9`.
34. New unified development canonical code head: `c7025182349f93869eead2017d395b847744c9c9`.
35. FUND-C is canonically integrated in the forward development candidate: yes.
36. No. This does not make formal Opportunity Daily Recommendation Production-ready.
37. Production was not modified.
38. C was not modified.
39. Nothing was pushed.
40. Next governed action: resolve the formal Opportunity provider/publication gate and obtain owner policy decisions before any formal recommendation or institutional policy use; release/Production gates remain separate.

## Machine-readable pointers

- Final summary: `final-summary.json`
- Task manifest: `docs/governance/tasks/TASK-INT-FUND-C-OPPORTUNITY-INSTITUTIONAL-EVIDENCE-CANONICAL-RECONCILIATION-001.yaml`
- Provenance: `docs/governance/provenance/TASK-INT-FUND-C-OPPORTUNITY-INSTITUTIONAL-EVIDENCE-CANONICAL-RECONCILIATION-001.json`

## Closeout boundary

`FUND_C=CANONICALLY_INTEGRATED` for the development lineage.
`OPPORTUNITY_DAILY_RECOMMENDATION_READY=NO`.
`PRODUCTION_READY=EXTERNAL_GATE`.
`PRODUCTION_MUTATION=NONE`.
`MIGRATION_EXECUTION=NONE`.
`DEPLOYMENT=NONE`.
`REPLAY=NONE`.
`CANARY=NONE`.
`PUSH=NO`.
`NEXT_TASK_CHANGED=NO`.

C owner checkout before and after: HEAD `02d3086183d1c582bb6c66c4c316340ccce3fa97`,
status count `153` -> `153`; `C_DRIVE=UNTOUCHED`.
