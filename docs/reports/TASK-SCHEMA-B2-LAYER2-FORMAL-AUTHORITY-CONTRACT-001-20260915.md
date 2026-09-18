# TASK-SCHEMA-B2-LAYER2-FORMAL-AUTHORITY-CONTRACT-001

## 1. Governed closeout

| Field | Value |
|---|---|
| Role | `SCHEMA_OWNER_AND_INTEGRATION_OWNER` |
| Mode | `ONE_SHOT_FORMAL_AUTHORITY_CONTRACT_AND_GOVERNED_CLOSEOUT` |
| Result | `PARTIAL` |
| Stop reason | `FORMAL_OWNER_IDENTITY_DECISION_REQUIRED` |
| Worktree | `E:\\TopicPilot\\worktrees\\schema-b2-layer2-formal-authority-001-20260915` |
| Branch | `codex/schema-b2-layer2-formal-authority-contract-001-20260915` |
| Governed development base | `a8357d46194f9669709f184949270e20a7a2546c` |
| Canonical baseline | `origin/main@b2eaf33e0ec5f9bb72d936eb0165eb93dac3fa40` |
| C: | `UNTOUCHED` |
| Production | `UNTOUCHED` |
| Migration 0040 | `UNTOUCHED` |
| Push / merge / deploy | `NO` |
| `NEXT_TASK` | `NOT MODIFIED` |

The schema, validator, serializer, compatibility adapter, focused tests, and
governance artifacts were completed. The only genuine human stop is the lack
of a repository-authoritative stable Owner identity. No arbitrary name,
account, email, UUID, test fixture, or task-prompt label was promoted into the
formal record.

## 2. Recovered Owner policy decision

The prior governed closeout at final SHA
`57daa35d05491ef85e75287fb36aba0e037063c9` was recovered and verified from
the repository history. Its Owner decision is preserved:

```text
OWNER_POLICY_DECISION=APPROVE_EXISTING_LAYER2_POLICY_WITH_FAIL_CLOSED_ACTIVATION
OWNER_POLICY_REDESIGN_REQUIRED=NO
DAILY_STRENGTH_ARCHITECTURE=APPROVED
DAILY_STRENGTH_EXACT_POLICY=PARTIAL_BY_DESIGN
SCORE_GRADE_DETERMINISTIC_FOUNDATION=APPROVED_VERIFIED
FIVE_STAGE_LIFECYCLE=APPROVED
FORMAL_PUBLICATION_ACTIVE=NO
```

The recovered identity resolution is:

```text
policyBundleId=topic-b2-layer2-policy
policyBundleVersion=topic-b2-layer2-policy-v1
candidateId=TOPIC_B2_LAYER2_POLICY_V1
candidateVersion=v1
effectiveDate=2026-09-15
```

This is a bounded repository-compatible mapping of the Owner's supplied
conceptual identity. It does not answer the separate mandatory `ownerIdentity`
field.

## 3. Repository archaeology

The following existing contracts were inspected before mutation:

| Surface | Finding |
|---|---|
| `policy_approval.py` | Strict `topic-score-pm-approval.v1`; Score/Grade metadata only; no Lifecycle or typed partial scope |
| `production_policy.py` | Explicit caller-supplied candidate/policy/effective-date/Leader Set references; no defaults |
| `runtime_readiness.py` | Policy approval, Leader Set, as-of, freshness, and Eligibility Audit remain independent activation gates |
| `topic_score_formal.py` | Formal Score is `FORMAL / UNPUBLISHED`; authority requires exact policy, Leader Set, CORE, and as-of lineage |
| `structural_role_authority.py` | Repository-native `approvalReference` is an approval provenance reference, not an Owner identity |
| `score_projection.py` | Score projection is explicit and fails closed; it does not infer members or Owner identity |
| Lifecycle specification/engine | Five-stage product meaning exists; exact numeric transition parameters and formal publication remain bounded/partial |
| Governance reports/history | No later complete Layer 2 envelope exists; prior closeout explicitly identified schema insufficiency |
| Ownership/identity search | No `owner_id`, `approver_id`, `principal`, `approved_by`, or Owner identity registry was found |

The prompt's claim that 0040/A10/A9 engineering is complete is not stronger
than the repository handoff. Current repository authority remains
`MIGRATION_0040=BRANCH_ONLY / REVISION_COLLISION / NOT_EXECUTED` and
`A10_A9=PARTIAL / BRANCH_ONLY_CLOSURE / OPERATOR_GATED`. This task did not
reopen or modify that workstream.

## 4. Chosen formal contract

Created architecture authority:

`docs/architecture/TOPIC_B2_LAYER2_FORMAL_AUTHORITY_CONTRACT.md`

Created implementation:

`services/api/src/topicpilot_api/topic_engine/layer2_formal_authority.py`

Contract version:

```text
topic-layer2-formal-authority.v1
```

The strategy is composition, not replacement:

```text
topic-layer2-formal-authority.v1
├── DailyStrengthContract
├── ScoreGradeContract -> topic-score-pm-approval.v1
└── LifecycleContract
```

Legacy v1 remains readable and means Score/Grade subset only. It is never
reinterpreted as complete Layer 2 authority.

### Daily Strength

The contract records:

```text
status=PARTIAL_BY_DESIGN
verifiedComponents=[...]
unverifiedComponents=[...]
parameterProvenance=[...]
failClosed=true
```

Unknown parameters cannot be replaced by defaults or zeroes.

### Score/Grade

The contract references the recovered 003F PM approval artifact and its
SHA-256, retains the legacy schema version, and records whether the strict
legacy PolicyApprovalRecord is `PENDING_RECORD` or `CREATED` with a separate
record digest. The record is not created in this task because Owner identity is
unresolved.

### Lifecycle

The contract enforces the exact independent stages:

```text
SPROUTING, FERMENTING, MAIN_RISE, MATURE, DECLINING
```

It requires explicit independence from Daily Strength and Score/Grade, and
represents transition semantics as `VERIFIED_COMPONENTS_ONLY` or
`PARTIAL_BY_DESIGN` with fail-closed behavior. No unverified thresholds,
hysteresis, or duration was invented.

### Authority state separation

The envelope separates:

```text
authorityState:   POLICY_APPROVED | PRODUCTION_ACTIVE | BLOCKED
publicationState: UNPUBLISHED | READY | ACTIVE | BLOCKED
activationState:  NOT_ACTIVE | ACTIVE
```

The validator never authorizes Production activation. `003H` exposes the
distinction without granting authority.

## 5. Owner identity resolution

Repository evidence contains approval references such as
`OWNER-AUTHORIZED-B2-PROTECTED-TOPIC-AUTHORITY-20260910` and
`OWNER_APPROVAL_2026-09-11_A9_B2_FORMAL_CORRECTION`. These are provenance
references, not stable Owner identities.

The only repository-compatible candidate forms are:

1. `OWNER:<stable-id>` — explicit Owner namespace; requires a registered stable ID.
2. `GOVERNANCE_OWNER:<stable-id>` — explicit governance-owner namespace; requires the same registry.
3. `principal://<governance-domain>/<stable-id>` — URI principal; requires a repository governance domain and stable ID.

No candidate is selected because doing so would change governance identity
semantics without repository authority. The validator rejects null, display
name, test-fixture, email, account, and arbitrary alias values with:

```text
FORMAL_OWNER_IDENTITY_DECISION_REQUIRED
```

## 6. 003G / 003H implementation

The new 003G-compatible guard is `evaluate_layer2_authority()`.

It fails closed for unknown bundle/version/candidate, missing or invalid Owner
identity, invalid stages, collapsed outputs, non-fail-closed partial policy,
missing legacy Score/Grade record, and activation attempts.

The new 003H-compatible boundary is:

- `export_layer2_authority_artifact()`;
- `parse_layer2_authority_artifact()`; and
- `export_layer2_metadata()`.

Top-level and nested unknown/missing fields are rejected. Parsing does not
apply approval semantics. Metadata readback does not grant authority.

## 7. Compatibility matrix

| Consumer | Legacy v1 | New Layer 2 v1 | Disposition |
|---|---:|---:|---|
| Existing Score/Grade guard | Yes | Referenced | Preserved unchanged |
| Existing `ProductionV1PolicyBundle` | Yes | Composed through Score/Grade subset | No default identity introduced |
| Existing formal Score gate | Yes | Layer 2 envelope can reference it | Score remains separate and unpublished until its own gates pass |
| 003G | Yes | New Layer 2 guard | Additive, fail-closed |
| 003H | Yes | New strict artifact/readback | Additive, metadata-only |
| Daily Strength | No | Yes | `PARTIAL_BY_DESIGN`, fail-closed |
| Lifecycle | No | Yes | Independent five-stage contract |
| Historical v1 artifacts | Yes | Not reinterpreted | Backward-compatible |
| Production activation | No | No | Separate runtime/operator gate |

No migration, ORM persistence, API route, OpenAPI/generated artifact, or
frontend change was needed for the artifact-based contract.

## 8. Policy record and publication gate

```text
POLICY_APPROVAL_RECORD=NOT_CREATED
POLICY_RECORD_SHA256=NOT_APPLICABLE
FORMAL_POLICY_AUTHORITY=PARTIAL
FORMAL_DB_PREREQUISITE=PENDING
A10_A9_PREREQUISITE=BLOCKED / OPERATOR_GATED
FORMAL_PUBLICATION_READINESS=BLOCKED
FORMAL_PUBLICATION_ACTIVE=NO
A9_FORMAL_WRITER_POLICY_PREREQUISITE=BLOCKED
OPPORTUNITY_B2_AUTHORITY_PREREQUISITE=BLOCKED
STOCK_B2_AUTHORITY_PREREQUISITE=BLOCKED
```

The contract is implemented and validatable, but formal authority cannot be
materialized until the Owner identity decision is resolved. Even after that,
formal publication remains independent of DB readback, Leader Set/Score
projection authority, A9/A10 runtime proof, and operator gates.

## 9. Validation

| Check | Result |
|---|---|
| New Layer 2 contract tests | `PASS` |
| Legacy policy approval tests | `PASS` |
| Production policy/runtime readiness/formal Score tests | `PASS` |
| Focused combined count | `53 passed` |
| Ruff | `PASS` |
| Ruff format | `PASS` |
| Python 3.12 compile | `PASS` |
| Strict artifact round-trip | `PASS` |
| Deterministic SHA-256 stability | `PASS` |
| 003G authoritative record validation | `NOT_RUN — record not created` |
| 003H authoritative record readback | `NOT_RUN — record not created` |
| PostgreSQL / DB readback | `PENDING / NOT RUN` |
| Production / scheduler / deployment | `NOT PERFORMED` |

No baseline failure was changed or masked. The focused implementation suite
reported `TASK_CAUSED_FAILURES=0` and `UNKNOWN_FAILURES=0`. The broader
regression selection reported `BASELINE_FAILURES=1`: the pre-existing
`tests/test_topic_lifecycle_contract_closure.py::test_frozen_stage_contract_has_one_owner_sequence_and_no_legacy_stage`
expects the frozen five-stage contract, while the baseline implementation
contains six mojibake stage values. This failure is outside the task diff and
was not repaired or masked.

## 10. Project Memory recovery test

Repository artifacts now answer without chat history:

1. Layer 2 contains Daily Strength, Score/Grade, and independent Lifecycle.
2. Daily Strength is current/day-level strength and is `PARTIAL_BY_DESIGN`.
3. Unverified Daily Strength parameters fail closed.
4. Score/Grade is the verified deterministic 003F foundation.
5. Lifecycle stages are SPROUTING, FERMENTING, MAIN_RISE, MATURE, DECLINING.
6. Lifecycle is not derived from Daily Strength or Score/Grade.
7. The formal schema is `topic-layer2-formal-authority.v1`.
8. Legacy `topic-score-pm-approval.v1` remains Score/Grade subset only.
9. 003G validates and blocks; it does not grant approval.
10. 003H reads metadata; it does not grant authority.
11. No formal PolicyApprovalRecord exists yet because Owner identity is unresolved.
12. Formal DB readback and A10/A9/operator gates remain independent blockers.
13. B2 is not active in Production; Opportunity and Stock remain downstream-gated.

`PROJECT_MEMORY_RECOVERY_TEST=PASS`.

## 11. Exact SHAs and safety

```text
CURRENT_GOVERNED_BASE_SHA=a8357d46194f9669709f184949270e20a7a2546c
TASK_EXECUTION_BASE_SHA=a8357d46194f9669709f184949270e20a7a2546c
IMPLEMENTATION_SHA=3011f00fe50e5c397635ef9a25ca3a9282bbd523
SCHEMA_SHA=b0a45d47b3ae5cc20a4e0e58d63a2daeff3ce5ec7d45c051aeac833994e136f9
GOVERNANCE_SHA=ee65c530058da5694741e4e5d7c5dcc1895ba9b0
REPORT_SHA256=REPORTED_IN_FINAL_CLOSEOUT
POLICY_RECORD_SHA256=NOT_APPLICABLE
C_DRIVE=UNTOUCHED
PRODUCTION=UNTOUCHED
PRODUCTION_MUTATION=NONE
MIGRATION_0040=UNTOUCHED
PUSH=NO
MERGE_MAIN=NO
DEPLOY=NO
NEXT_TASK_CHANGED=NO
```

The next governed action is a narrow Owner identity decision/registry
resolution. Do not automatically begin PolicyApprovalRecord creation,
Production publication, A9 writer activation, Opportunity implementation,
Stock frontend work, DB correction, migration, deployment, or scheduler work.
