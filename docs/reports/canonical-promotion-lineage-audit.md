# Canonical promotion lineage audit

Task: `TASK-TOPIC-STRENGTH-LIFECYCLE-OWNER-SEEDED-V0-CANONICAL-PROMOTION-004`

The candidate was reconciled against the latest canonical `main` before
promotion. The original candidate ref was `eb358c10968a78772376020a605edd62253e6dc4`.
The reconciled promotion branch is
`codex/topic-strength-lifecycle-canonical-promotion-004`.

## Recomputed graph

```text
CURRENT_MAIN_SHA=7dee5f99e8127326b51c9672f3a01cab208a0f96
ORIGINAL_CANDIDATE_SHA=eb358c10968a78772376020a605edd62253e6dc4
ORIGINAL_MERGE_BASE_SHA=6cb88c0d7fceb45b244d295883636706f50ea0be
ORIGINAL_AHEAD_BY=16
ORIGINAL_BEHIND_BY=4
RECONCILED_MERGE_COMMIT=b8bce18a5a6f0ce3c00af436ab52a604c6c226e8
RECONCILED_MERGE_BASE=7dee5f99e8127326b51c9672f3a01cab208a0f96
RECONCILED_AHEAD_BY=17
RECONCILED_BEHIND_BY=0
```

`main` advanced with Today Market Signal v1. The only content conflict was
the end of `apps/web/app/globals.css`; the Topic detail styles and Today
signal styles were retained together. The generated API and backend schema
changes merged without semantic conflict.

## Ordered lineage

| Order | Commit | Title | Classification | Promotion disposition |
| ---: | --- | --- | --- | --- |
| 1 | `0a93217e589635e92dcd394402ea7e9edb7c8daf` | Reconcile topic role strength design freeze contracts | `RUNTIME_REQUIRED` | Preserve formal contracts, runtime projection, tests, and the un-applied 0047 migration artifact. |
| 2 | `7cbf00e8e630fc0e72e53267b3253a9fccb30ea7` | Record topic design freeze governance report | `GOVERNANCE_REQUIRED` | Preserve design-freeze evidence and authority boundaries. |
| 3 | `0ce187927885c9844709c95dd6e4cf0b556c462a` | Build bounded historical calibration candidate pipeline | `CALIBRATION_ARTIFACT_ONLY` | Preserve as diagnostic/research lineage; it is not runtime policy authority. |
| 4 | `b5903f8b8bdc8bea1eaa9d5305270a719cd2378d` | Record historical calibration governance limitation | `GOVERNANCE_REQUIRED` | Preserve the explicit calibration limitation and no-retrofill boundary. |
| 5 | `bde413235d5f9512956a6b6f9f9bc441fa971f2` | Complete historical calibration decision report | `CALIBRATION_ARTIFACT_ONLY` | Preserve the decision artifact; no historical seed becomes runtime authority. |
| 6 | `28752394bcccb4226d52516070e9b9cd2165f55f` | Close calibration data foundation with official benchmarks | `CALIBRATION_ARTIFACT_ONLY` | Preserve bounded PIT/benchmark evidence; do not activate it as policy. |
| 7 | `27ac01eff270bf35b49d7112646d3393cf6b39ad` | Close historical calibration and enter owner seeded v0 | `GOVERNANCE_REQUIRED` | Preserve the explicit transition to Owner-seeded V0 and the historical-calibration disposition. |
| 8 | `304eebd0d5c77f158e30adaa5502a62d02f03d4e` | Reconcile latest canonical main before owner seeded policy | `RUNTIME_REQUIRED` | Preserve the A10/Today compatibility reconciliation carried by the candidate lineage. |
| 9 | `1a140c63c703bfeb24327ff435115e4d9162f3f2` | Implement Owner-seeded V0 topic strength policy | `FORMAL_POLICY_REQUIRED` | Preserve the frozen curves, thresholds, guards, lifecycle rules, small-sample rule, tests, and policy hash. |
| 10 | `de594598fbc770620c638d0b3af71a1ba3f01b48` | Review Owner-seeded V0 and prepare forward observation | `FORWARD_OBSERVATION_REQUIRED` | Preserve Owner acceptance, observation contract, and diagnostic-only boundary. |
| 11 | `04f208a6e3465207652938e1229f41be122f63f9` | Record review branch handoff status | `GOVERNANCE_REQUIRED` | Preserve review provenance and accepted observation flags. |
| 12 | `e9cbe819ff24f6cfb3d484b54f4ffb52c564c402` | Merge canonical main into the activation branch | `RUNTIME_REQUIRED` | Preserve canonical post-close/A10 runtime compatibility and its governance evidence. |
| 13 | `897579b53ca933957367467c1219930f144df626` | Activate Owner-seeded V0 forward observation readback | `FORWARD_OBSERVATION_REQUIRED` | Preserve backend read model, capture contract, and Topic detail integration. |
| 14 | `2f93647fbf9742f27243ff7fbe86cf58bf8afeec` | Bind activation artifacts to implementation identity | `FORWARD_OBSERVATION_REQUIRED` | Preserve policy-hash and implementation-SHA binding. |
| 15 | `0e083d41bcce1aa89e5339025f4d1f9d3586dfbf` | Expose backend small-sample observation state | `FRONTEND_REQUIRED` | Preserve the fail-closed 1–2 member display boundary and regression coverage. |
| 16 | `eb358c10968a78772376020a605edd62253e6dc4` | Record activation validation status | `GOVERNANCE_REQUIRED` | Preserve exact 003 validation and activation status evidence. |
| 17 | `b8bce18a5a6f0ce3c00af436ab52a604c6c226e8` | Merge latest main into Topic Strength lifecycle promotion candidate | `RUNTIME_REQUIRED` | Preserve current canonical Today/OpenAPI/generated-client behavior while retaining the Topic lineage. |

`UNEXPECTED_COMMIT_COUNT=0`. No unrelated feature branch was added to the
promotion candidate.

## Artifact authority boundary

### Runtime authority

- `services/api/src/topicpilot_api/topic_engine/owner_seeded_v0_policy.py`
- `services/api/src/topicpilot_api/topic_engine/forward_observation_activation.py`
- `services/api/src/topicpilot_api/topic_strength_lifecycle_read_model.py`
- `services/api/src/topicpilot_api/schemas.py`
- `services/api/src/topicpilot_api/production_read_model.py`
- `services/api/src/topicpilot_api/production_read_model_api.py`
- `apps/web/app/components/v2/TopicDetailPage.tsx`
- `apps/web/app/lib/topic-api.ts`
- `config/topic_strength_policy/topic-strength-lifecycle.owner-seeded-v0.json`

### Governance evidence

The TASK-001, TASK-002, TASK-003 reports, Owner acceptance, design-freeze
traceability, this audit, and the TASK-004 promotion report establish
provenance and boundaries. They do not override the runtime authority.

### Research-only and calibration-only

The historical calibration runners, calibration foundation, calibration
register versions, benchmark distributions, PIT audit outputs, replay
outputs, and historical-calibration reports remain evidence-only. They cannot
select thresholds, retrofill current roles, or publish formal Topic state.

The explicit boundary remains:

```text
HISTORICAL_CALIBRATION=NOT_AVAILABLE
CURRENT_ROLE_RETROFILL=FORBIDDEN
MANUAL_HISTORICAL_AUTHORITY_ASSEMBLY=FORBIDDEN
PIT_STANDARD_RELAXATION=FORBIDDEN
```

## Migration boundary

`0047_task_topic_role_strength_design_freeze.py` is present in the lineage
and is the repository graph head, but it was not applied by this task. The
canonical database maintenance source remains the prior applied head. No
Production database, migration state, or manual data was changed.
