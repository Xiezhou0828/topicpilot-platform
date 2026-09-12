# TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818

## Closure outcome

```text
TASK_FINAL_STATUS=PUBLICATION_CONTRACT_RECONCILED_WITH_BOUNDED_LIMITATIONS
PUBLICATION_CONTRACT_RECONCILED=YES
READY_FOR_WS2_NEXT_MAINLINE_STEP=YES_WITH_BOUNDED_LIMITATIONS
READY_FOR_WS2_PRODUCTION=NO
```

This task resumes the existing WS2 Technical V0 mainline. It closes the
publication contract and stock-level read surface after the prior full-universe
qualification. It does not reopen G2R-C, Shared-G3, exhaustive corporate-action
research, WS3 research, recommendation publication, migration, Production, or
deployment.

## Authority and provenance

| Item | Result |
|---|---|
| Canonical repository | `C:\Users\acer\Desktop\題材領航\topicpilot-platform` |
| Canonical branch | `codex/task-ops-023a-p3c-runtime-sha-audit-20260813` |
| Source canonical HEAD | `8bc9c8ec403e03aa104c6feac481e2d5e561e134` |
| Current WS2 contract before closure | `stock-technical-v0-policy.v3` / `stock-technical-publication.v2` |
| Contract after closure | `stock-technical-v0-policy.v4` / `stock-technical-publication.v3` |
| Known-event overlay | Present and connected; policy version `stock-technical-v0-known-event-aware.v2` |
| Full-universe qualification source | `YES`; prior task worktree `C:\Users\acer\Documents\Codex\ws2-full-universe-qualification-20260818`, source SHA `42f429518e9e0006811fb7c1076c79979a4254e1` |
| Concurrent reconciliation | WS3-only canonical advancement to `8bc9c8e`; unrelated owner dirty/untracked state preserved |
| Owner dirty state at audit | 18 tracked, 156 untracked; `WS2_STATUS=0` |
| `NEXT_TASK` | No repository `NEXT_TASK.md` is present in the canonical checkout; no roadmap/owner next-task file was modified |

The task worktree was created from the source canonical HEAD at
`C:\Users\acer\Documents\Codex\ws2-publication-contract-closure-20260818`.
No owner files were reset, cleaned, stashed, or overwritten. Active WS1/WS3/WS4
worktrees were enumerated and preserved.

## Reconciled publication contract

Technical V0 now exposes three independent dimensions:

| Dimension | States | Contract meaning |
|---|---|---|
| Technical result | `VALID`, `INELIGIBLE`, `UNAVAILABLE`, `ERROR` | Raw Technical V0 calculation plus the frozen `Close(T) >= MA60(T)` eligibility rule |
| Event authority | `KNOWN_EVENT`, `NO_KNOWN_EVENT_EVIDENCE`, `LOOKUP_UNAVAILABLE`, `NOT_APPLICABLE`, `ERROR` | What the known-event-aware overlay established; missing evidence is never no-event |
| Publication | `AVAILABLE`, `AVAILABLE_WITH_LIMITATION`, `BLOCKED`, `UNAVAILABLE`, `ERROR` | What a downstream consumer may use from the analytical read surface |

For a valid raw result with generic missing/timed-out event lookup, the overlay
keeps `publication_allowed=false` for ordinary formal clearance but permits the
explicit bounded surface. Values are serialized as
`FORMAL_WITH_LIMITATION`, with `EVENT_LOOKUP_UNAVAILABLE` in limitation/reason
codes and stock-level `AVAILABLE_WITH_LIMITATION`. This is not
`NO_EVENT`, `PASS_BOUNDED`, adjusted-price truth, or exchange-grade continuity.

Malformed lookup envelopes, invalid identity or lineage, corrupt input,
insufficient required history, known unresolved continuity-breaking events,
contract violations, and calculation errors remain hard unavailable/blocked or
error outcomes. Known events remain window-scoped; an event intersecting MA60
blocks the Technical V0 surface, while an event outside MA60 can produce an
explicit `KNOWN_EVENT_HANDLED` limitation for otherwise valid evidence.

MA60 policy, all fourteen Technical V0 algorithms, raw-observed price basis,
PIT/as-of binding, and the WS2 evidence-only boundary were unchanged. No BUY,
SELL, win rate, entry/target/stop-loss, strategy acceptance, Opportunity Grade,
or Recommendation score is emitted.

## Q1-Q10 closure answers

**Q1 — Why did the previous qualification produce 0/507 while eligible builder
success was 23/23?**

The prior `PUBLICATION_AVAILABLE` numerator meant strict ordinary publication:
the qualification required a successful bounded event disposition outside the
`KNOWN_EVENT_HANDLED` class. The 23 MA60-qualified instruments were therefore
counted as successful bounded known-event outcomes, not as ordinary available;
the other 166 identities had no valid event lookup envelope and remained
fail-closed. The prior builder also exposed only a single top-level
formal/unavailable view, so technical validity, event authority, and surface
availability were not separately machine-readable.

**Q2 — Root-cause classification.**

The 0/507 result was primarily `OVERLY_STRICT_LEGACY_PUBLICATION_GATE` plus a
`METRIC_NAMING / SURFACE_SEMANTICS_ISSUE`, not a Technical V0 algorithm defect.
The bounded implementation gap was the missing additive surface dimensions,
not a calculation error. The final full-universe run records
`IMPLEMENTATION_DEFECT_COUNT=0`.

**Q3 — Should technical validity and corporate-action authority be separate?**

Yes. The new contract separates `technical_result_status`,
`event_authority_status`, and `publication_status`; a technically valid result
can disclose incomplete event authority without claiming that authority exists.

**Q4 — Can lookup failure safely produce a bounded surface?**

Yes, but only through the known-event-aware path and only when raw observations,
identity, algorithms, lineage, and MA60 eligibility are valid. The result is
`VALID + LOOKUP_UNAVAILABLE + AVAILABLE_WITH_LIMITATION` with explicit
`EVENT_LOOKUP_UNAVAILABLE`. It never becomes a no-event claim. Invalid or
ambiguous event evidence does not receive this allowance.

**Q5 — What remains a hard blocker?**

Below-MA60 eligibility, insufficient MA60 or indicator history, missing/invalid
required OHLCV, invalid identity/lineage, explicit continuity conflict,
known unresolved continuity-breaking event intersecting the required window,
future-data/look-ahead violation, contract violation, and genuine calculation
error remain blocked, unavailable, or error according to the matrix.

**Q6 — Are known verified events still handled correctly?**

Yes. `TPE:2330` is a local MA60 blocking control; `TPE:2380` capital reduction
and `TWO:5904` par-value/share-basis change remain external positive controls
with `KNOWN_VERIFIED_BREAKING_EVENT_FOUND`, `publication_allowed=false`, and
`bounded_limitation_allowed=false`.

**Q7 — Is fail-safe behavior preserved without permanently blocking WS2?**

Yes. Ordinary formal clearance still fails closed on lookup failure, and known
events remain hard window gates. The bounded limited surface prevents missing
authority from being mistaken for either no event or a permanent system-wide
Technical V0 shutdown.

**Q8 — Can all 507 instruments be classified deterministically?**

Yes. The final read-only run classified `507/507` formal real instruments in
the `2026-02-02..2026-08-13` window and produced the same normalized surface
hash on both runs.

**Q9 — Does an implementation defect remain?**

No runtime/calculation defect remains in the scoped run. Focused tests passed,
independent Decimal reconciliation passed with zero mismatches, known-event
controls passed, and the full-universe runner recorded zero implementation
errors. The remaining limitations are bounded event-authority limitations.

**Q10 — What is next?**

The next WS2 mainline step is an Owner-authorized Technical V0 mainline
read-model consumer/surface integration that consumes these existing fields and
preserves the explicit limited/blocked/unavailable semantics. It is not a new
indicator family, strategy, recommendation, migration, or Production task.

## Full-universe surface result

The source was the canonical PostgreSQL historical read authority: 63,826 real
OHLCV rows across 507 real TPE/TWO instruments, as of 2026-08-13. The runner was
read-only and used REC-A1 bounded event evidence without fabricating empty event
lookups.

```text
TOTAL_FORMAL_INSTRUMENTS=507
TOTAL_CLASSIFIED_INSTRUMENTS=507
TECHNICAL_VALID_INSTRUMENTS=85
TECHNICAL_V0_ELIGIBLE_INSTRUMENTS=85
TECHNICAL_V0_INELIGIBLE_INSTRUMENTS=127
TECHNICAL_UNAVAILABLE_INSTRUMENTS=295
TECHNICAL_ERROR_INSTRUMENTS=0
EVENT_KNOWN_INSTRUMENTS=340
EVENT_NO_KNOWN_EVIDENCE_INSTRUMENTS=1
EVENT_LOOKUP_UNAVAILABLE_INSTRUMENTS=166
PUBLICATION_AVAILABLE_INSTRUMENTS=0
PUBLICATION_AVAILABLE_WITH_LIMITATION_INSTRUMENTS=85
PUBLICATION_BLOCKED_INSTRUMENTS=422
PUBLICATION_UNAVAILABLE_INSTRUMENTS=0
PUBLICATION_ERROR_INSTRUMENTS=0
ELIGIBLE_AVAILABLE_COUNT=0
ELIGIBLE_AVAILABLE_WITH_LIMITATION_COUNT=85
ELIGIBLE_BLOCKED_COUNT=0
ELIGIBLE_ERROR_COUNT=0
IMPLEMENTATION_DEFECT_COUNT=0
DATA_LIMITATION_COUNT=166
KNOWN_EVENT_HANDLED_COUNT=23
KNOWN_EVENT_BLOCKED_COUNT=317
TECHNICAL_VALUE_RECONCILIATION_PASS=YES
KNOWN_EVENT_CONTROL_VALIDATION_PASS=YES
LOOK_AHEAD_LEAKAGE_DETECTED=NO
FULL_UNIVERSE_REPRODUCIBLE=YES
NORMALIZED_SURFACE_SHA256=5d2aecd41bd171f395852be00f910d98953ceab672c0b915323656a2ca9fc692
```

`PUBLICATION_AVAILABLE=0` remains an honest result: no eligible instrument in
this bounded input set had a successful ordinary no-match envelope. The new
surface makes the 85 valid-but-limited outcomes visible instead of collapsing
them into the old zero numerator. The 127 below-MA60 rows are expected
analytical ineligibility, not system failure; 295 known-event windows are hard
blocked by continuity handling.

## Evidence artifacts

- [Publication contract summary](../../reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818/ws2-technical-v0-publication-contract-summary.json)
- [Publication decision matrix](../../reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818/ws2-publication-decision-matrix.json)
- [Full-universe publication surface](../../reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818/ws2-full-universe-publication-surface.csv)
- [Full-universe summary](../../reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818/ws2-full-universe-publication-summary.json)
- [Known-event controls](../../reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818/ws2-known-event-control-validation.json)
- [Technical value reconciliation](../../reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818/ws2-technical-value-reconciliation.json)
- [Publication contract quality audit](../../reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818/ws2-publication-contract-quality-audit.json)
- [Next-mainline readiness](../../reports/TASK-WS2-TECHNICAL-V0-PUBLICATION-CONTRACT-AND-MAINLINE-SURFACE-CLOSURE-20260818/ws2-next-mainline-readiness.json)
- [Rerunnable full-universe validator](../../scripts/ws2_technical_v0_publication_contract_surface_closure.py)

## State ledger and safety boundaries

```text
IMPLEMENTATION_STATE=VALIDATED_BOUNDED_PUBLICATION_SURFACE
VALIDATION_STATE=PASS_FULL_UNIVERSE_TWO_RUNS_AND_FOCUSED_TESTS
CANONICAL_STATUS=PROMOTED_TO_CANONICAL; owner dirty state preserved; no conflicts
RELEASE_STATUS=NOT_RUN
PRODUCTION_VERIFICATION=NOT_RUN
DATABASE_WRITE_STATE=NOT_RUN
MIGRATION_STATE=NOT_RUN
PROVIDER_SCHEDULER_STATE=NOT_RUN
G1_G2_G3_STATE=NOT_RERUN; preserved prior evidence because write set is publication contract/read-only surface
G2R_C_EXECUTED=NO
SHARED_G3_EXECUTED=NO
PRODUCTION_MUTATION=NO
DEPLOY_EXECUTED=NO
PUSH_EXECUTED=NO
WS1_CHANGED=NO
WS3_CHANGED=NO
WS4_CHANGED=NO
NEXT_TASK_CHANGED=NO
TASK_SOURCE_COMMIT_SHA=606681daf883c8736dafd6968b337805b824ac60
CANONICAL_PROMOTION_COMMIT=5bb5ebf6912125fdd4dae5f744046ccbc679aaa9
CANONICAL_HEAD_AT_FIRST_PROMOTION=5bb5ebf6912125fdd4dae5f744046ccbc679aaa9
FINAL_CANONICAL_HEAD=RECORDED_IN_FINAL_HANDOFF_AFTER_PROVENANCE_UPDATE
```

## Validation record

```text
FOCUSED_WS2_TESTS=26 passed
KNOWN_EVENT_TESTS=PASS (included in focused run)
PY_COMPILE_COMPILEALL=PASS
RUFF_CHANGED_SCOPE=PASS
GIT_DIFF_CHECK=PASS
SECRET_SCAN_CHANGED_SCOPE=PASS
FULL_UNIVERSE_RUN_1=PASS; 507/507
FULL_UNIVERSE_RUN_2=PASS; identical normalized surface hash
TECHNICAL_VALUE_RECONCILIATION=PASS; mismatch_count=0
KNOWN_EVENT_CONTROLS=PASS
```

The isolated result was promoted by commit-preserving cherry-pick after a
conflict-free recheck against the owner dirty state and concurrent WS3
advancement. The provenance follow-up records the source implementation
commit and first canonical promotion commit; the final canonical head after
this follow-up is recorded in the final handoff. Unrelated files remain
preserved and `NEXT_TASK`, Production, and remote state remain unchanged.
